import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { login } from './http'

vi.stubGlobal('fetch', vi.fn())
const mockFetch = vi.mocked(globalThis.fetch)

const reloadMock = vi.fn()
const originalLocation = window.location

beforeEach(() => {
  localStorage.clear()
  mockFetch.mockReset()
  reloadMock.mockReset()
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { ...originalLocation, reload: reloadMock },
  })
})

afterEach(() => {
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: originalLocation,
  })
})

describe('http 401 handling', () => {
  it('throws with status and does not reload when no token is stored', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: () => Promise.resolve({ detail: 'Wrong credentials' }),
    } as Response)

    await expect(login('user', 'pass')).rejects.toMatchObject({
      message: 'Wrong credentials',
      status: 401,
    })

    expect(reloadMock).not.toHaveBeenCalled()
  })
})

describe('http error status', () => {
  it('exposes status on thrown errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: () => Promise.resolve({ detail: 'Unauthorized' }),
    } as Response)

    let caught: unknown
    try {
      await login('user', 'pass')
    } catch (e) {
      caught = e
    }

    expect(caught).toBeInstanceOf(Error)
    expect((caught as Error & { status: number }).status).toBe(401)
  })
})
