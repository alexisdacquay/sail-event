export type AuthResponse = { token: string; username: string }
export type ConfigResponse = { registrationCodeRequired: boolean }
export type Criteria = { text: string; updatedAt: string; timeZone: string }
export type Thresholds = { lowerThreshold: number; upperThreshold: number }
export type SearchResult = {
  runId: string
  eventsFound: number
  eventsNew: number
  stageCounts: Record<string, number> | null
  stoppedAtStage: string | null
  error: string | null
}

export type EventStatus = 'new' | 'accepted' | 'rejected' | 'queued'

export type Event = {
  id: string
  title: string
  dateTime: string
  place: string
  link: string
  description: string
  startTz: string | null
  endTime: string | null
  city: string
  country: string
  priceAmount: number | null
  priceCurrency: string | null
  sourceUrl: string | null
  band: string | null
  score: number
  scoreReason: string
  status: EventStatus
  decidedBy: 'auto' | 'user' | null
}

const useHttp = import.meta.env.VITE_API_URL !== undefined

const mod = useHttp
  ? await import('./http')
  : await import('./mock')

export const getConfig = mod.getConfig
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
