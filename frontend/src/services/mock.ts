import type {
  AuthResponse,
  Criteria,
  Thresholds,
  SearchResult,
  Event,
  EventStatus,
} from './api'

const INITIAL_EVENTS: Event[] = [
  {
    id: 'evt-1',
    title: 'React London Meetup',
    dateTime: '2026-07-10T18:30:00Z',
    place: 'WeWork Moorgate, London',
    link: 'https://meetup.com/react-london/july-2026',
    description: 'Monthly React meetup with talks on server components and signals.',
    score: 82,
    scoreReason: 'Strong match: tech meetup, aligns with frontend interest.',
    status: 'accepted',
  },
  {
    id: 'evt-2',
    title: 'Jazz in the Park',
    dateTime: '2026-07-15T20:00:00Z',
    place: 'Hyde Park, London',
    link: 'https://jazzpark.co.uk/summer-2026',
    description: 'Open-air jazz concert featuring international artists.',
    score: 45,
    scoreReason: 'Moderate match: entertainment, but not a tech or professional event.',
    status: 'queued',
  },
  {
    id: 'evt-3',
    title: 'AWS re:Invent Watch Party',
    dateTime: '2026-12-02T09:00:00Z',
    place: 'TechHub Manchester',
    link: 'https://techhub.com/reinvent-watch-2026',
    description: 'Live stream of AWS re:Invent keynotes with local networking.',
    score: 75,
    scoreReason: 'Good match: cloud computing event, professional networking.',
    status: 'queued',
  },
  {
    id: 'evt-4',
    title: 'Pottery Workshop for Beginners',
    dateTime: '2026-08-20T14:00:00Z',
    place: 'Clay Studio, Brighton',
    link: 'https://claystudio.co.uk/workshops/beginner',
    description: 'Hands-on pottery session, no experience needed.',
    score: 12,
    scoreReason: 'Low relevance: arts and crafts, no professional or tech angle.',
    status: 'rejected',
  },
  {
    id: 'evt-5',
    title: 'TypeScript Conference 2026',
    dateTime: '2026-09-18T09:00:00Z',
    place: 'QEII Centre, London',
    link: 'https://tsconf.eu/2026',
    description: 'Two-day conference on TypeScript, type systems, and tooling.',
    score: 91,
    scoreReason: 'Excellent match: core technology conference.',
    status: 'new',
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
}

let mockThresholds: Thresholds = {
  lowerThreshold: 30,
  upperThreshold: 70,
}

export async function register(
  username: string,
  _password: string,
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

export async function saveCriteria(text: string): Promise<Criteria> {
  mockCriteria = { text, updatedAt: new Date().toISOString() }
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
  return { runId: 'run-001', eventsFound: 12, eventsNew: 4 }
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
  return { ...event }
}

export async function getCalendarUrl(): Promise<{ url: string }> {
  return { url: 'http://localhost:8000/api/calendar/mock-ics-token' }
}
