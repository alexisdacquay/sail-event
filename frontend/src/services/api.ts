export type AuthResponse = { token: string; username: string }
export type Criteria = { text: string; updatedAt: string }
export type Thresholds = { lowerThreshold: number; upperThreshold: number }
export type SearchResult = {
  runId: string
  eventsFound: number
  eventsNew: number
}

export type EventStatus = 'new' | 'accepted' | 'rejected' | 'queued'

export type Event = {
  id: string
  title: string
  dateTime: string
  place: string
  link: string
  description: string
  score: number
  scoreReason: string
  status: EventStatus
}

const useHttp = import.meta.env.VITE_API_URL !== undefined

const mod = useHttp
  ? await import('./http')
  : await import('./mock')

export const register = mod.register
export const login = mod.login
export const getCriteria = mod.getCriteria
export const saveCriteria = mod.saveCriteria
export const getThresholds = mod.getThresholds
export const saveThresholds = mod.saveThresholds
export const runSearch = mod.runSearch
export const listEvents = mod.listEvents
export const decideEvent = mod.decideEvent
export const getCalendarUrl = mod.getCalendarUrl
export const rotateCalendarUrl = mod.rotateCalendarUrl
