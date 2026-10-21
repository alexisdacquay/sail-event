import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Funnel, funnelNumbers } from './Funnel'

const counts = {
  results_fetched: 20, events_extracted: 31, accepted: 2, queued: 1, rejected: 19,
  rejected_date_place: 16, rejected_off_topic: 3, rejected_other: 0,
  filtered_past: 4, filtered_place: 2, filtered_duplicate: 3,
}

describe('funnelNumbers', () => {
  it('partitions found and rejected', () => {
    const n = funnelNumbers(counts)
    expect(n.accepted + n.queued + n.rejected + n.setAside).toBe(n.found)
    expect(n.rejectedDatePlace + n.rejectedOffTopic + n.rejectedOther).toBe(n.rejected)
  })
})

describe('Funnel', () => {
  it('renders every label', () => {
    render(<Funnel counts={counts} />)
    for (const t of [
      '31 found', 'on 20 pages', '2 in calendar', '1 to review', '19 rejected',
      '16 wrong date or place', '3 off topic', '9 set aside', '4 past · 2 place · 3 dup',
    ]) expect(screen.getByText(t)).toBeInTheDocument()
  })

  it('right-side squares sum to the left bar height', () => {
    const { container } = render(<Funnel counts={counts} />)
    const [bar, ...squares] = Array.from(container.querySelectorAll('rect'))
    expect(bar.getAttribute('height')).toBe('124')
    expect(squares).toHaveLength(4)
    const sum = squares.reduce((a, r) => a + Number(r.getAttribute('height')), 0)
    expect(sum).toBeCloseTo(124, 2)
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
