import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'

// CI runners are several times slower than a laptop; 1 s default waits flake there.
configure({ asyncUtilTimeout: 5000 })

// jsdom lacks matchMedia; provide a stub so components that check prefers-reduced-motion work
if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })
}
