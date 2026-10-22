export type AuthResponse = { token: string; username: string }
export type ConfigResponse = { registrationCodeRequired: boolean }
export type Criteria = { text: string; updatedAt: string; timeZone: string }
export type Thresholds = { lowerThreshold: number; upperThreshold: number }
export type SearchResult = {
  runId: string
  eventsFound: number
  eventsNew: number
  stageCounts: Record<string, number> | null
  currentStage: string | null
  stoppedAtStage: string | null
  error: string | null
  startedAt: string | null
  finishedAt: string | null
  // #108: always sent by the backend; optional so existing test literals in MainPage.test.tsx still type-check
  durationSeconds?: number | null
  trigger?: RunTrigger
}

export type LastRunResponse = { run: SearchResult | null }

export type RunTrigger = 'manual' | 'scheduled'

export type RunSummary = {
  runId: string
  startedAt: string
  finishedAt: string | null
  durationSeconds: number | null
  trigger: RunTrigger
  eventsFound: number // events_extracted; accepted + queued + rejected + setAside == eventsFound
  accepted: number
  queued: number
  rejected: number
  setAside: number // extracted events with no verdict: filtered_incomplete/past/date/place/duplicate + events_capped + judge_errors
  pagesRead: number // results_fetched
  pagesSkipped: number // filtered_non_event
  error: string | null
}

export type RunsResponse = { runs: RunSummary[] }

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
export const getLastRun = mod.getLastRun
export const deleteAllEvents = mod.deleteAllEvents
export const getCalendarUrl = mod.getCalendarUrl
export const rotateCalendarUrl = mod.rotateCalendarUrl
