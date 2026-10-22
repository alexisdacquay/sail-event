import type {
  AuthResponse,
  ConfigResponse,
  Criteria,
  Thresholds,
  SearchResult,
  LastRunResponse,
  RunSummary,
  RunsResponse,
  Event,
  EventStatus,
} from './api'

const INITIAL_EVENTS: Event[] = [
  {
    id: 'evt-1',
    title: 'React London Meetup',
    dateTime: '2026-07-10T18:30:00Z',
    place: 'WeWork Moorgate',
    link: 'https://meetup.com/react-london/july-2026',
    description: 'Monthly React meetup with talks on server components and signals.',
    startTz: 'Europe/London',
    endTime: null,
    city: 'London',
    country: 'GB',

    sourceUrl: 'https://meetup.com/react-london/july-2026',
    band: 'mostly fits',
    score: 82,
    scoreReason: 'Strong match: tech meetup, aligns with frontend interest.',
    status: 'accepted',
    decidedBy: 'auto',
  },
  {
    id: 'evt-2',
    title: 'Jazz in the Park',
    dateTime: '2026-07-15T19:00:00Z',
    place: 'Hyde Park',
    link: 'https://jazzpark.co.uk/summer-2026',
    description: 'Open-air jazz concert featuring international artists.',
    startTz: 'Europe/London',
    endTime: null,
    city: 'London',
    country: 'GB',

    sourceUrl: 'https://jazzpark.co.uk/summer-2026',
    band: 'open question',
    score: 45,
    scoreReason: 'Entertainment event, but not a tech or professional event.',
    status: 'queued',
    decidedBy: null,
  },
  {
    id: 'evt-3',
    title: 'AWS re:Invent Watch Party',
    dateTime: '2026-12-02T09:00:00Z',
    place: 'TechHub',
    link: 'https://techhub.com/reinvent-watch-2026',
    description: 'Live stream of AWS re:Invent keynotes with local networking.',
    startTz: 'Europe/London',
    endTime: null,
    city: 'Manchester',
    country: 'GB',

    sourceUrl: 'https://techhub.com/reinvent-watch-2026',
    band: 'mostly fits',
    score: 75,
    scoreReason: 'Cloud computing event with professional networking.',
    status: 'queued',
    decidedBy: null,
  },
  {
    id: 'evt-4',
    title: 'Pottery Workshop for Beginners',
    dateTime: '2026-08-20T14:00:00Z',
    place: 'Clay Studio',
    link: 'https://claystudio.co.uk/workshops/beginner',
    description: 'Hands-on pottery session, no experience needed.',
    startTz: 'Europe/London',
    endTime: null,
    city: 'Brighton',
    country: 'GB',

    sourceUrl: 'https://claystudio.co.uk/workshops/beginner',
    band: 'off topic',
    score: 12,
    scoreReason: 'Arts and crafts, no professional or tech angle.',
    status: 'rejected',
    decidedBy: 'auto',
  },
  {
    id: 'evt-5',
    title: 'TypeScript Conference 2026',
    dateTime: '2026-09-18T09:00:00Z',
    place: 'QEII Centre',
    link: 'https://tsconf.eu/2026',
    description: 'Two-day conference on TypeScript, type systems, and tooling.',
    startTz: 'Europe/London',
    endTime: null,
    city: 'London',
    country: 'GB',

    sourceUrl: 'https://tsconf.eu/2026',
    band: 'fits',
    score: 91,
    scoreReason: 'Core technology conference, excellent match.',
    status: 'new',
    decidedBy: null,
  },
]

let mockEvents: Event[] = INITIAL_EVENTS.map((e) => ({ ...e }))

/** Reset mock events to initial state. Test-only. */
export function _resetMockEvents() {
  mockEvents = INITIAL_EVENTS.map((e) => ({ ...e }))
}

let mockCriteria: Criteria = {
  text: 'sailing regattas in the Mediterranean, July 2026',
  updatedAt: '2026-01-15T10:00:00Z',
  timeZone: 'UTC',
}

let mockThresholds: Thresholds = {
  lowerThreshold: 30,
  upperThreshold: 70,
}

export async function getConfig(): Promise<ConfigResponse> {
  return { registrationCodeRequired: false }
}

export async function register(
  username: string,
  _password: string,
  _registrationCode?: string,
): Promise<AuthResponse> {
  return { token: 'mock-token-' + username, username }
}

export async function login(
  username: string,
  _password: string,
): Promise<AuthResponse> {
  return { token: 'mock-token-' + username, username }
}

export async function getCriteria(): Promise<Criteria> {
  return { ...mockCriteria }
}

export async function saveCriteria(text: string, timeZone?: string): Promise<Criteria> {
  mockCriteria = { text, updatedAt: new Date().toISOString(), timeZone: timeZone || mockCriteria.timeZone }
  return { ...mockCriteria }
}

export async function getThresholds(): Promise<Thresholds> {
  return { ...mockThresholds }
}

export async function saveThresholds(
  thresholds: Thresholds,
): Promise<Thresholds> {
  mockThresholds = { ...thresholds }
  return { ...mockThresholds }
}

export async function runSearch(): Promise<SearchResult> {
  return {
    runId: 'run-001',
    eventsFound: 12,
    eventsNew: 4,
    stageCounts: {
      queries_planned: 6,
      results_fetched: 31,
      events_extracted: 12,
      // judged 7 + not judged 5 = 12 found (#112 invariant), with a no-date case
      filtered_no_date: 1,
      filtered_past: 2,
      filtered_place: 1,
      filtered_duplicate: 1,
      filtered_non_event: 2,
      events_judged: 7,
      accepted: 2,
      queued: 3,
      rejected: 2,
      rejected_date_place: 1,
      rejected_off_topic: 1,
      rejected_other: 0,
    },
    currentStage: null,
    stoppedAtStage: null,
    error: null,
    startedAt: '2026-10-18T10:00:00+00:00',
    finishedAt: '2026-10-18T10:01:30+00:00',
    durationSeconds: 90,
    trigger: 'manual',
  }
}

export async function getLastRun(): Promise<LastRunResponse> {
  // the Stream page renders the chronology and funnel from this run
  return { run: await runSearch() }
}

const mockRuns: RunSummary[] = [
  {
    runId: 'run-001',
    startedAt: '2026-10-18T10:00:00+00:00',
    finishedAt: '2026-10-18T10:01:30+00:00',
    durationSeconds: 90,
    trigger: 'manual',
    eventsFound: 12,
    accepted: 2,
    queued: 3,
    rejected: 2,
    setAside: 5,
    pagesRead: 31,
    pagesWithEvents: 8,
    pagesSkipped: 2,
    error: null,
  },
  {
    runId: 'run-003',
    startedAt: '2026-10-18T09:00:00+00:00',
    finishedAt: '2026-10-18T09:00:42+00:00',
    durationSeconds: 42,
    trigger: 'scheduled',
    eventsFound: 9,
    accepted: 0,
    queued: 1,
    rejected: 4,
    setAside: 4,
    pagesRead: 20,
    pagesWithEvents: 6,
    pagesSkipped: 9,
    error: null,
  },
  {
    runId: 'run-002',
    startedAt: '2026-10-18T08:00:00+00:00',
    finishedAt: '2026-10-18T08:00:03+00:00',
    durationSeconds: 3,
    trigger: 'scheduled',
    eventsFound: 0,
    accepted: 0,
    queued: 0,
    rejected: 0,
    setAside: 0,
    pagesRead: 0,
    pagesWithEvents: 0,
    pagesSkipped: 0,
    error: 'TimeoutError: search provider timed out',
  },
]

export async function getRuns(limit = 20): Promise<RunsResponse> {
  return { runs: mockRuns.slice(0, limit).map((r) => ({ ...r })) }
}

export async function deleteAllEvents(): Promise<{ deleted: number }> {
  const count = mockEvents.length
  mockEvents = []
  return { deleted: count }
}

export async function listEvents(status?: EventStatus): Promise<Event[]> {
  if (status) {
    return mockEvents.filter((e) => e.status === status).map((e) => ({ ...e }))
  }
  return mockEvents.map((e) => ({ ...e }))
}

export async function decideEvent(
  id: string,
  decision: 'accepted' | 'rejected',
): Promise<Event> {
  const event = mockEvents.find((e) => e.id === id)
  if (!event) throw new Error(`Event not found: ${id}`)
  event.status = decision
  event.decidedBy = 'user'
  return { ...event }
}

let mockIcsToken = 'mock-ics-token'

export async function getCalendarUrl(): Promise<{ url: string }> {
  return { url: `http://localhost:8000/api/calendar/${mockIcsToken}` }
}

export async function rotateCalendarUrl(): Promise<{ url: string }> {
  mockIcsToken = 'mock-ics-token-' + Date.now()
  return { url: `http://localhost:8000/api/calendar/${mockIcsToken}` }
}
