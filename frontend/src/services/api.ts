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

export {
  register,
  login,
  getCriteria,
  saveCriteria,
  getThresholds,
  saveThresholds,
  runSearch,
  listEvents,
  decideEvent,
} from './mock'
