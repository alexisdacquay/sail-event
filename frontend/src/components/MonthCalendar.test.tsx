import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MonthCalendar } from './MonthCalendar'

describe('MonthCalendar', () => {
  it('renders October 2026 with event days and today marked', () => {
    render(
      <MonthCalendar
        dates={['2026-10-24', '2026-10-27T20:00:00+02:00']}
        today={new Date(2026, 9, 21, 12)}
      />,
    )
    expect(screen.getByText('October')).toBeInTheDocument()
    const cells = screen.getByTestId('month-calendar').querySelectorAll('.grid > span')
    // 7 headers + 3 blanks (1 Oct 2026 is a Thursday) + 31 days
    expect(cells).toHaveLength(7 + 3 + 31)
    expect(cells[7 + 3].textContent).toBe('1')
    expect(screen.getByText('24')).toHaveAttribute('data-has-event', 'true')
    expect(screen.getByText('27')).toHaveAttribute('data-has-event', 'true')
    expect(screen.getByText('21')).toHaveAttribute('aria-current', 'date')
    expect(screen.getByText('22')).not.toHaveAttribute('data-has-event')
  })
})
