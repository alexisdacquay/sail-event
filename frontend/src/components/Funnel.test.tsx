import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Funnel, funnelNumbers } from './Funnel'

const counts = {
  results_fetched: 31, events_extracted: 12,
  filtered_no_date: 1, filtered_past: 2, filtered_place: 1, filtered_duplicate: 1, filtered_non_event: 2,
  events_judged: 7, accepted: 2, queued: 3, rejected: 2, rejected_date_place: 1, rejected_off_topic: 1, rejected_other: 0,
}
const pagesWithEvents = 8

const noDate = { results_fetched: 4, events_extracted: 5, filtered_no_date: 2, accepted: 1, queued: 1, rejected: 1 }

function stageHeights(container: HTMLElement, stage: number) {
  const [bar, ...squares] = Array.from(container.querySelectorAll(`[data-testid="funnel-stage-${stage}"] rect`))
  return { bar: Number(bar.getAttribute('height')), sum: squares.reduce((a, r) => a + Number(r.getAttribute('height')), 0) }
}

function expectStagesSum(container: HTMLElement) {
  for (const stage of [1, 2, 3]) {
    const { bar, sum } = stageHeights(container, stage)
    expect(bar).toBe(124)
    expect(sum).toBeCloseTo(124, 6)
  }
}

describe('funnelNumbers', () => {
  it('partitions pages, found and rejected', () => {
    const n = funnelNumbers(counts, pagesWithEvents)
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
  it.each([1, 2, 3])('stage %i squares sum to its bar height', (stage) => {
    const { container } = render(<Funnel counts={counts} pagesWithEvents={pagesWithEvents} />)
    const { bar, sum } = stageHeights(container, stage)
    expect(bar).toBe(124)
    expect(sum).toBeCloseTo(124, 6)
  })

  it('every stage sums when events lack a date', () => {
    const { container } = render(<Funnel counts={noDate} pagesWithEvents={3} />)
    expectStagesSum(container)
    expect(screen.getByText('2 not judged')).toBeInTheDocument()
  })

  it('renders every label', () => {
    render(<Funnel counts={counts} pagesWithEvents={pagesWithEvents} />)
    for (const t of [
      '31 pages read', '12 events from 8 pages', '23 pages: no events',
      '12 found', '7 judged', '5 not judged', '1 no date', '2 past', '1 duplicate', '1 place',
      '2 in calendar', '3 to review', '2 out', '1 date or place', '1 topic',
    ]) expect(screen.getAllByText(t).length).toBeGreaterThan(0)
    expect(screen.queryByText(/other/)).not.toBeInTheDocument()
  })

  it('never says set aside or rejected', () => {
    const { container } = render(<Funnel counts={counts} pagesWithEvents={pagesWithEvents} />)
    expect(container.textContent).not.toMatch(/set aside|rejected/)
    expect(screen.getByTestId('funnel').getAttribute('aria-label')).not.toMatch(/set aside|rejected/)
  })

  it('never overlaps labels within a stage', () => {
    const { container } = render(<Funnel counts={counts} pagesWithEvents={pagesWithEvents} />)
    for (const stage of [1, 2, 3]) {
      const ys = Array.from(
        container.querySelectorAll(`[data-testid="funnel-stage-${stage}"] text[x="${(stage - 1) * 240 + 100}"]`),
        (t) => Number(t.getAttribute('y')),
      ).sort((a, b) => a - b)
      expect(ys.length).toBeGreaterThan(1)
      for (let i = 1; i < ys.length; i++) expect(ys[i] - ys[i - 1]).toBeGreaterThanOrEqual(10)
    }
  })

  it('renders nothing with no events', () => {
    const { container } = render(<Funnel counts={{ events_extracted: 0, results_fetched: 5 }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('has no side ribbon without pagesWithEvents and stage 1 still sums', () => {
    const { container } = render(<Funnel counts={counts} />)
    expect(screen.queryByText(/no events/)).not.toBeInTheDocument()
    expect(screen.getByText('12 events from 31 pages')).toBeInTheDocument()
    expectStagesSum(container)
  })
})
