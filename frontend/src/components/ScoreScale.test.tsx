import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ScoreScale } from './ScoreScale'

function renderScale(lower = 30, upper = 70, onChange = vi.fn()) {
  return { ...render(<ScoreScale lower={lower} upper={upper} onChange={onChange} />), onChange }
}

describe('ScoreScale', () => {
  it('renders thumbs at initial 30/70 with correct accessible names', () => {
    renderScale()
    const thumb0 = screen.getByRole('slider', { name: 'Auto-reject below' })
    const thumb1 = screen.getByRole('slider', { name: 'Auto-accept above' })
    expect(thumb0).toHaveValue('30')
    expect(thumb1).toHaveValue('70')
  })

  it('renders number inputs at initial 30/70', () => {
    renderScale()
    const lower = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upper = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    expect(lower).toHaveValue(30)
    expect(upper).toHaveValue(70)
  })

  it('has aria-valuetext on thumbs', () => {
    renderScale()
    expect(screen.getByRole('slider', { name: 'Auto-reject below' }))
      .toHaveAttribute('aria-valuetext', '30 out of 100')
    expect(screen.getByRole('slider', { name: 'Auto-accept above' }))
      .toHaveAttribute('aria-valuetext', '70 out of 100')
  })

  it('calls onChange when a number input changes', () => {
    const { onChange } = renderScale()
    fireEvent.change(
      screen.getByRole('spinbutton', { name: 'Auto-reject below' }),
      { target: { value: '40' } },
    )
    expect(onChange).toHaveBeenCalledWith(40, 70)
  })

  it('calls onChange with upper when upper input changes', () => {
    const { onChange } = renderScale()
    fireEvent.change(
      screen.getByRole('spinbutton', { name: 'Auto-accept above' }),
      { target: { value: '80' } },
    )
    expect(onChange).toHaveBeenCalledWith(30, 80)
  })

  // jsdom does not drive native range-input keyboard behaviour, so we test
  // via a change event on the hidden input — the same event Base UI listens to
  it('calls onChange when slider thumb value changes via change event', () => {
    const { onChange } = renderScale()
    const thumb = screen.getByRole('slider', { name: 'Auto-reject below' })
    fireEvent.change(thumb, { target: { value: '25' } })
    expect(onChange).toHaveBeenCalledWith(25, 70)
  })

  it('shows validation error when lower >= upper', () => {
    render(<ScoreScale lower={80} upper={50} onChange={vi.fn()} />)
    expect(
      screen.getByText(
        'The auto-accept line must be higher than the auto-reject line.',
      ),
    ).toBeInTheDocument()
  })

  it('shows validation error when lower equals upper', () => {
    render(<ScoreScale lower={50} upper={50} onChange={vi.fn()} />)
    expect(
      screen.getByRole('alert'),
    ).toBeInTheDocument()
  })

  it('does not show validation when values are valid', () => {
    renderScale()
    expect(
      screen.queryByText(
        'The auto-accept line must be higher than the auto-reject line.',
      ),
    ).not.toBeInTheDocument()
  })

  it('wraps in fieldset with sr-only legend "Score cut-offs"', () => {
    renderScale()
    expect(screen.getByText('Score cut-offs')).toBeInTheDocument()
  })

  it('shows all three zone labels', () => {
    renderScale()
    expect(screen.getAllByText('Rejected').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('You decide').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('On your calendar').length).toBeGreaterThanOrEqual(1)
  })
})
