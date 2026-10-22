import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Funnel, funnelNumbers } from './Funnel'

const counts = {
  results_fetched: 31, pages_with_events: 8, events_extracted: 12,
  filtered_no_date: 1, filtered_past: 2, filtered_place: 1, filtered_duplicate: 1, filtered_non_event: 2,
  events_judged: 7, accepted: 2, queued: 3, rejected: 2, rejected_date_place: 1, rejected_off_topic: 1, rejected_other: 0,
}

const noDate = { results_fetched: 4, pages_with_events: 3, events_extracted: 5, filtered_no_date: 2, accepted: 1, queued: 1, rejected: 1 }

const SCALE = 140 // px of bar for all the events found

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

/** Structure the issue asks for: ribbons leave the bar's right edge, the judged ribbon ends at the judged bar,
 *  every ribbon is its count × scale thick at both ends, and each stage's parts sum to its bar. */
function expectStructure(container: HTMLElement, c: Record<string, number>) {
  const n = funnelNumbers(c)
  const s = SCALE / n.found
  const [s1, s2] = [1, 2].map((i) => stage(container, i))
  const expected = [
    [n.judged, n.notJudged].filter((k) => k > 0),
    [n.accepted, n.queued, n.rejected].filter((k) => k > 0),
  ]
  for (const [i, st] of [s1, s2].entries()) {
    expect(st.ribbons).toHaveLength(expected[i].length)
    for (const [j, r] of st.ribbons.entries()) {
      expect(r.x0).toBe(st.bar.x + st.bar.w)
      expect(r.yL1 - r.yL0).toBeCloseTo(expected[i][j] * s, 6)
      expect(r.yR1 - r.yR0).toBeCloseTo(expected[i][j] * s, 6)
    }
    expect(st.ribbons.reduce((a, r) => a + (r.yL1 - r.yL0), 0)).toBeCloseTo(st.bar.h, 6)
  }
  expect(s1.bar.h).toBe(SCALE)
  expect(s2.bar.h).toBeCloseTo(n.judged * s, 6)
  // the judged ribbon feeds the judged bar exactly; the not-judged one ends short of it
  expect(s1.ribbons[0].x1).toBe(s2.bar.x)
  expect(s1.ribbons[0].yR0).toBe(10)
  if (s1.ribbons[1]) expect(s1.ribbons[1].x1).toBeLessThan(s2.bar.x)
  // the verdict end bars sum to the judged bar
  expect(s2.ends.reduce((a, r) => a + Number(r.getAttribute('height')), 0)).toBeCloseTo(s2.bar.h, 6)
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
  it('is one continuous flow at one scale: constant-thickness ribbons that sum per stage', () => {
    const { container } = render(<Funnel counts={counts} />)
    expectStructure(container, counts)
  })

  it('every stage sums when events lack a date', () => {
    const { container } = render(<Funnel counts={noDate} />)
    expectStructure(container, noDate)
    expect(screen.getByText('2 no date · 0 past · 0 dup')).toBeInTheDocument()
  })

  it('renders every label anchored to its own element', () => {
    const { container } = render(<Funnel counts={counts} />)
    for (const t of [
      '12 found', 'from 8 of 31 pages read', '5 not judged', '1 no date · 2 past · 1 dup', '1 place',
      '2 in', '3 review', '2 out', '1 date/place', '1 topic',
    ]) expect(screen.getByText(t)).toBeInTheDocument()
    expect(screen.queryByText(/other/)).not.toBeInTheDocument()
    const x = (el: Element) => Number(el.getAttribute('x'))
    // the pages line is part of "found": flush with the found bar
    const bar = stage(container, 1).bar
    expect(x(screen.getByText('12 found'))).toBe(bar.x)
    expect(x(screen.getByText('from 8 of 31 pages read'))).toBe(bar.x)
    // "judged" inside its ribbon and under its bar; "not judged" under the grey ribbon's end; verdicts right of the end bars
    expect(screen.getAllByText('7 judged').map(x)).toEqual([34, 400])
    expect(x(screen.getByText('5 not judged'))).toBe(200)
    expect(x(screen.getByText('1 no date · 2 past · 1 dup'))).toBe(200)
    expect(x(screen.getByText('2 out'))).toBe(592)
  })

  it('no two labels overlap, and nothing is clipped', () => {
    const many = { ...counts, filtered_date: 1, filtered_incomplete: 1, events_capped: 1, judge_errors: 1, events_extracted: 16 }
    const { container } = render(<Funnel counts={many} />)
    const boxes = Array.from(container.querySelectorAll('text'), (t) => {
      const x = Number(t.getAttribute('x')), y = Number(t.getAttribute('y'))
      return { text: t.textContent, x0: x, x1: x + t.textContent!.length * 6, y0: y - 8, y1: y }
    })
    for (const a of boxes) for (const b of boxes) {
      if (a === b) continue
      const overlap = a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1
      expect(overlap, `${a.text} / ${b.text}`).toBe(false)
    }
    const [width, height] = screen.getByTestId('funnel').getAttribute('viewBox')!.split(' ').slice(2).map(Number)
    for (const b of boxes) {
      expect(b.y1).toBeLessThanOrEqual(height)
      expect(b.x1, b.text!).toBeLessThanOrEqual(width)
    }
  })

  it('never says set aside or rejected', () => {
    const { container } = render(<Funnel counts={counts} />)
    expect(container.textContent).not.toMatch(/set aside|rejected|pages: no events/)
    expect(screen.getByTestId('funnel').getAttribute('aria-label')).not.toMatch(/set aside|rejected/)
  })

  it('never overlaps the verdict labels', () => {
    const { container } = render(<Funnel counts={{ ...counts, events_extracted: 40, rejected: 30, rejected_date_place: 29 }} />)
    const ys = Array.from(container.querySelectorAll('[data-testid="funnel-stage-2"] text'), (t) => Number(t.getAttribute('y'))).sort((a, b) => a - b)
    expect(ys.length).toBeGreaterThan(1)
    for (let i = 1; i < ys.length; i++) expect(ys[i] - ys[i - 1]).toBeGreaterThanOrEqual(10)
  })

  it('renders nothing with no events', () => {
    const { container } = render(<Funnel counts={{ events_extracted: 0, results_fetched: 5 }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('says "on P pages read" for a run from before pages_with_events', () => {
    const { pages_with_events: _, ...before } = counts
    const { container } = render(<Funnel counts={before} />)
    expect(screen.getByText('on 31 pages read')).toBeInTheDocument()
    expectStructure(container, before)
  })
})
