import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { RunSummary } from '@/services/api'
import { EarlierRuns } from './EarlierRuns'

function run(i: number): RunSummary {
  return {
    runId: `r${i}`,
    startedAt: `2026-10-21T${19 - i}:07:00Z`,
    finishedAt: null,
    durationSeconds: 100,
    trigger: 'scheduled',
    eventsFound: 29,
    accepted: 2,
    queued: 0,
    rejected: 19,
    setAside: 8,
    pagesRead: 20,
    pagesWithEvents: 12,
    pagesSkipped: 3,
    error: null,
  }
}

describe('EarlierRuns', () => {
  it('shows three rows and expands on click', () => {
    render(<EarlierRuns runs={[run(0), run(1), run(2), run(3)]} />)
    expect(screen.getAllByTestId('earlier-run')).toHaveLength(3)
    // the count is the hidden runs, not the three shown
    expect(screen.getByText('1 more')).toBeInTheDocument()
    expect(screen.getAllByTestId('earlier-run')[0]).toHaveTextContent('29 found')
    fireEvent.click(screen.getByTestId('earlier-runs-more'))
    expect(screen.getAllByTestId('earlier-run')).toHaveLength(4)
    expect(screen.queryByTestId('earlier-runs-more')).not.toBeInTheDocument()
  })

  it('has no button with three runs', () => {
    render(<EarlierRuns runs={[run(0), run(1), run(2)]} />)
    expect(screen.queryByTestId('earlier-runs-more')).not.toBeInTheDocument()
  })

  it('renders nothing when empty', () => {
    const { container } = render(<EarlierRuns runs={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})
