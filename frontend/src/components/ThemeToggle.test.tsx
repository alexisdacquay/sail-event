import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ThemeToggle } from './ThemeToggle'

const KEY = 'sail-event-theme'
const isDark = () => document.documentElement.classList.contains('dark')

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })
  afterEach(() => vi.unstubAllGlobals())

  it('is light with empty storage and no matchMedia', () => {
    render(<ThemeToggle />)
    expect(isDark()).toBe(false)
    expect(screen.getByTestId('theme-toggle')).toHaveAttribute(
      'aria-label',
      'Switch to dark theme',
    )
  })

  it('toggle adds the class, writes localStorage, and persists on a fresh render', () => {
    const { unmount } = render(<ThemeToggle />)
    fireEvent.click(screen.getByTestId('theme-toggle'))
    expect(isDark()).toBe(true)
    expect(localStorage.getItem(KEY)).toBe('dark')
    expect(screen.getByTestId('theme-toggle')).toHaveAttribute(
      'aria-label',
      'Switch to light theme',
    )
    unmount()
    document.documentElement.classList.remove('dark')
    render(<ThemeToggle />)
    expect(isDark()).toBe(true)
  })

  it('stored light beats a dark system preference', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    localStorage.setItem(KEY, 'light')
    render(<ThemeToggle />)
    expect(isDark()).toBe(false)
  })
})
