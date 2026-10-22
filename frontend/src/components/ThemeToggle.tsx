import { useState } from 'react'

const KEY = 'sail-event-theme'

/** Applies the stored theme (or the system one) via the `dark` class; returns whether dark. */
export function applyTheme(): boolean {
  const stored = localStorage.getItem(KEY)
  const dark =
    stored === 'dark' ||
    (stored !== 'light' &&
      !!window.matchMedia?.('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark)
  return dark
}

export function ThemeToggle() {
  const [dark, setDark] = useState(applyTheme)
  const next = dark ? 'light' : 'dark'
  return (
    <button
      type="button"
      data-testid="theme-toggle"
      aria-label={`Switch to ${next} theme`}
      className="rounded-md p-1.5 hover:bg-muted focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2"
      onClick={() => {
        localStorage.setItem(KEY, next)
        setDark(applyTheme())
      }}
    >
      <svg
        viewBox="0 0 24 24"
        className="size-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        {dark ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M4.9 19.1l1.4-1.4m11.4-11.4 1.4-1.4" />
          </>
        ) : (
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        )}
      </svg>
    </button>
  )
}
