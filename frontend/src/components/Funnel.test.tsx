import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Funnel, funnelNumbers } from './Funnel'

const counts = {
  results_fetched: 20, pages_content_pass: 20, events_extracted: 31, accepted: 2, queued: 1, rejected: 19,
  rejected_date_place: 16, rejected_off_topic: 3, rejected_other: 0,
  filtered_past: 4, filtered_place: 2, filtered_duplicate: 3,
}

// What the backend sends after a fixture run: pages that were not events are counted
// in filtered_non_event and are not part of the 10 events found.
const real = {
  queries_planned: 1, results_fetched: 22, pages_content_pass: 22, events_extracted: 10,
  filtered_non_event: 12, filtered_past: 0, filtered_date: 0, filtered_place: 0, filtered_duplicate: 0,
  events_judged: 10, accepted: 3, queued: 1, rejected: 6, rejected_date_place: 4, rejected_off_topic: 2, rejected_other: 0,
}

function squareHeights(container: HTMLElement) {
  const [bar, ...squares] = Array.from(container.querySelectorAll('rect'))
  return { bar: Number(bar.getAttribute('height')), sum: squares.reduce((a, r) => a + Number(r.getAttribute('height')), 0) }
}

describe('funnelNumbers', () => {
  it('partitions found and rejected', () => {
    const n = funnelNumbers(counts)
    expect(n.accepted + n.queued + n.rejected + n.setAside).toBe(n.found)
    expect(n.rejectedDatePlace + n.rejectedOffTopic + n.rejectedOther).toBe(n.rejected)
  })

  it('keeps pages that were not events out of the four parts', () => {
    const n = funnelNumbers(real)
    expect(n.setAside).toBe(0)
    expect(n.nonEvent).toBe(12)
    expect(n.accepted + n.queued + n.rejected + n.setAside).toBe(n.found)
  })

  it('treats missing rejected_* and filtered_* counts as 0', () => {
    const n = funnelNumbers({ events_extracted: 3, accepted: 3 })
    expect([n.rejected, n.rejectedDatePlace, n.rejectedOffTopic, n.rejectedOther, n.setAside]).toEqual([0, 0, 0, 0, 0])
  })
})

describe('Funnel', () => {
  it('renders every label', () => {
    render(<Funnel counts={counts} />)
    for (const t of [
      '31 found', 'on 20 pages read', '2 in calendar', '1 to review', '19 rejected',
      '16 wrong date or place', '3 off topic', '9 set aside', '4 past · 2 place · 3 dup',
    ]) expect(screen.getByText(t)).toBeInTheDocument()
  })

  it('right-side squares sum to the left bar height', () => {
    const { container } = render(<Funnel counts={counts} />)
    const { bar, sum } = squareHeights(container)
    expect(bar).toBe(124)
    expect(sum).toBeCloseTo(124, 2)
  })

  it('is to scale against real backend counts: ribbons equal the bar, non-events excluded', () => {
    const { container } = render(<Funnel counts={real} />)
    const { bar, sum } = squareHeights(container)
    expect(sum).toBeCloseTo(bar, 2)
    expect(screen.getByText('10 found')).toBeInTheDocument()
    expect(screen.getByText('on 22 pages read')).toBeInTheDocument()
    expect(screen.queryByText(/set aside/)).not.toBeInTheDocument()
    expect(screen.queryByText(/non-event/)).not.toBeInTheDocument()
  })

  it('counts incomplete and judge errors as set aside: ribbons equal the bar exactly', () => {
    const { container } = render(
      <Funnel counts={{ events_extracted: 10, accepted: 3, queued: 1, rejected: 4, filtered_incomplete: 1, judge_errors: 1 }} />,
    )
    const { bar, sum } = squareHeights(container)
    expect(bar).toBe(124)
    expect(sum).toBeCloseTo(124, 6)
    expect(screen.getByText('2 set aside')).toBeInTheDocument()
    expect(screen.getByText('1 incomplete · 1 errors')).toBeInTheDocument()
  })

  it('renders nothing with no events', () => {
    const { container } = render(<Funnel counts={{ events_extracted: 0 }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('never overlaps labels', () => {
    const { container } = render(
      <Funnel counts={{ events_extracted: 4, accepted: 1, queued: 1, rejected: 1, filtered_past: 1 }} />,
    )
    const ys = Array.from(container.querySelectorAll('text[x="226"]'), (t) => Number(t.getAttribute('y'))).sort((a, b) => a - b)
    for (let i = 1; i < ys.length; i++) expect(ys[i] - ys[i - 1]).toBeGreaterThanOrEqual(10)
  })

  it('skips a zero ribbon', () => {
    render(<Funnel counts={{ ...counts, queued: 0 }} />)
    expect(screen.queryByText(/to review/)).not.toBeInTheDocument()
  })
})
