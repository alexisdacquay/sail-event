import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Funnel, funnelNumbers } from './Funnel'

const counts = {
  results_fetched: 31, pages_with_events: 8, events_extracted: 12,
  filtered_no_date: 1, filtered_past: 2, filtered_place: 1, filtered_duplicate: 1, filtered_non_event: 2,
  events_judged: 7, accepted: 2, queued: 3, rejected: 2, rejected_date_place: 1, rejected_off_topic: 1, rejected_other: 0,
}

const noDate = { results_fetched: 4, pages_with_events: 3, events_extracted: 5, filtered_no_date: 2, accepted: 1, queued: 1, rejected: 1 }

type Edge = { x0: number; yL0: number; yL1: number; x1: number; yR0: number; yR1: number }

/** The ribbon's two vertical edges, read back from its path: M x0 yL0 C … x1 yR0 L x1 yR1 C … x0 yL1 Z */
function edges(path: Element): Edge {
  const m = path.getAttribute('d')!.match(/^M(\S+) (\S+) C\S+ \S+ \S+ \S+ (\S+) (\S+) L\S+ (\S+) C\S+ \S+ \S+ \S+ \S+ (\S+) Z$/)!
  const [x0, yL0, x1, yR0, yR1, yL1] = m.slice(1).map(Number)
  return { x0, yL0, yL1, x1, yR0, yR1 }
}

function stage(container: HTMLElement, i: number) {
  const g = container.querySelector(`[data-testid="funnel-stage-${i}"]`)!
  const bar = g.querySelector('rect')!
  const box = { x: Number(bar.getAttribute('x')), w: Number(bar.getAttribute('width')), h: Number(bar.getAttribute('height')) }
  return { bar: box, ribbons: Array.from(g.querySelectorAll('path'), edges), ends: Array.from(g.querySelectorAll('rect')).slice(1) }
}

function expectStructure(container: HTMLElement) {
  const [s1, s2, s3] = [1, 2, 3].map((i) => stage(container, i))
  for (const s of [s1, s2, s3]) {
    // every ribbon leaves from the bar's right edge, and the left edges sum to the bar
    for (const r of s.ribbons) expect(r.x0).toBe(s.bar.x + s.bar.w)
    expect(s.ribbons.reduce((a, r) => a + (r.yL1 - r.yL0), 0)).toBeCloseTo(s.bar.h, 6)
  }
  // the main ribbon of stages 1 and 2 ends exactly at the next bar, as tall as it
  expect(s1.ribbons[0].x1).toBe(s2.bar.x)
  expect(s1.ribbons[0].yR1 - s1.ribbons[0].yR0).toBeCloseTo(s2.bar.h, 6)
  expect(s2.ribbons[0].x1).toBe(s3.bar.x)
  expect(s2.ribbons[0].yR1 - s2.ribbons[0].yR0).toBeCloseTo(s3.bar.h, 6)
  // the verdict end bars sum to the judged bar
  expect(s3.ends.reduce((a, r) => a + Number(r.getAttribute('height')), 0)).toBeCloseTo(s3.bar.h, 6)
}

describe('funnelNumbers', () => {
  it('partitions pages, found and rejected', () => {
    const n = funnelNumbers(counts)
    expect(n.notJudged + n.judged).toBe(n.found)
    expect(n.pagesWithEvents + n.pagesNoEvents).toBe(n.pages)
    expect(n.rejectedDatePlace + n.rejectedOffTopic + n.rejectedOther).toBe(n.rejected)
    expect(n.nonEvent).toBe(2)
  })

  it('treats missing counts as 0 and pagesWithEvents as every page', () => {
    const n = funnelNumbers({ events_extracted: 3, accepted: 3, results_fetched: 5 })
    expect([n.rejected, n.rejectedDatePlace, n.notJudged, n.pagesNoEvents]).toEqual([0, 0, 0, 0])
    expect(n.pagesWithEvents).toBe(5)
  })
})

describe('Funnel', () => {
  it('is one continuous flow: ribbons leave the bars, feed the next bar, and sum per stage', () => {
    const { container } = render(<Funnel counts={counts} />)
    expectStructure(container)
    const [s1, s2, s3] = [1, 2, 3].map((i) => stage(container, i))
    expect([s1.bar.x, s2.bar.x, s3.bar.x]).toEqual([10, 200, 400])
    expect(s1.ribbons).toHaveLength(2)
    expect(s2.ribbons).toHaveLength(2)
    expect(s3.ribbons).toHaveLength(3)
    // the not-judged ribbon ends short, under the judged bar
    expect(s2.ribbons[1].yR0).toBeGreaterThan(10 + s3.bar.h)
  })

  it('every stage sums when events lack a date', () => {
    const { container } = render(<Funnel counts={noDate} />)
    expectStructure(container)
    expect(screen.getByText('2 no date · 0 past · 0 dup')).toBeInTheDocument()
  })

  it('renders every label where the drawing puts it', () => {
    render(<Funnel counts={counts} />)
    for (const t of [
      '31 pages read', '12 events', 'from 8 pages', '23 pages: no events',
      '12 found', '7 judged', '1 no date · 2 past · 1 dup · 1 place',
      '2 in', '3 review', '2 out', '1 date/place', '1 topic',
    ]) expect(screen.getByText(t)).toBeInTheDocument()
    expect(screen.queryByText(/other/)).not.toBeInTheDocument()
    // labels inside the ribbons for stages 1 and 2, verdict labels right of the end bars
    expect(Number(screen.getByText('12 events').getAttribute('x'))).toBe(34)
    expect(Number(screen.getByText('7 judged').getAttribute('x'))).toBe(224)
    expect(Number(screen.getByText('2 out').getAttribute('x'))).toBe(592)
  })

  it('never says set aside or rejected', () => {
    const { container } = render(<Funnel counts={counts} />)
    expect(container.textContent).not.toMatch(/set aside|rejected/)
    expect(screen.getByTestId('funnel').getAttribute('aria-label')).not.toMatch(/set aside|rejected/)
  })

  it('never overlaps the verdict labels', () => {
    const { container } = render(<Funnel counts={counts} />)
    const ys = Array.from(container.querySelectorAll('[data-testid="funnel-stage-3"] text'), (t) => Number(t.getAttribute('y'))).sort((a, b) => a - b)
    expect(ys.length).toBeGreaterThan(1)
    for (let i = 1; i < ys.length; i++) expect(ys[i] - ys[i - 1]).toBeGreaterThanOrEqual(10)
  })

  it('renders nothing with no events', () => {
    const { container } = render(<Funnel counts={{ events_extracted: 0, results_fetched: 5 }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('is one piece from every page for a run from before pages_with_events', () => {
    const { pages_with_events: _, ...before } = counts
    const { container } = render(<Funnel counts={before} />)
    expect(screen.queryByText(/no events/)).not.toBeInTheDocument()
    expect(screen.getByText('from 31 pages')).toBeInTheDocument()
    expect(stage(container, 1).ribbons).toHaveLength(1)
    expectStructure(container)
  })
})
