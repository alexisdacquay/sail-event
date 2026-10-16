export type AuthResponse = { token: string; username: string }
export type Criteria = { text: string; updatedAt: string }
export type Thresholds = { lowerThreshold: number; upperThreshold: number }
export type SearchResult = {
  runId: string
  eventsFound: number
  eventsNew: number
}

export {
  register,
  login,
  getCriteria,
  saveCriteria,
  getThresholds,
  saveThresholds,
  runSearch,
} from './mock'
