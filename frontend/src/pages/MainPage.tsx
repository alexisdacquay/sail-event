import { useCallback, useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { ScoreScale } from '@/components/ScoreScale'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ConfirmAction } from '@/components/ConfirmAction'
import { EventCard } from '@/components/EventCard'
import {
  getCriteria,
  saveCriteria,
  getThresholds,
  saveThresholds,
  runSearch,
  getLastRun,
  listEvents,
  decideEvent,
  deleteAllEvents,
  getCalendarUrl,
  rotateCalendarUrl,
} from '@/services/api'
import type { Event, SearchResult } from '@/services/api'

const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone

type MainPageProps = {
  onSearchComplete: () => Promise<number>
  queuedEvents: Event[]
  onNavigateQueue: () => void
}

/** Human-readable progress text from a run's currentStage and stageCounts. */
export function stageText(run: SearchResult): string {
  const stage = run.currentStage
  const c = run.stageCounts ?? {}

  if (!stage && run.finishedAt) {
    const accepted = c.accepted ?? 0
    const queued = c.queued ?? 0
    const rejected = c.rejected ?? 0
    return `Done: ${accepted} added to your calendar, ${queued} to review, ${rejected} rejected`
  }

  switch (stage) {
    case 'adapters':
    case 'criteria':
    case 'window':
      return 'Starting up…'
    case 'search':
      return 'Searching the web…'
    case 'extract': {
      const done = c.pages_content_pass ?? 0
      const total = c.results_fetched ?? 0
      return total > 0
        ? `Reading pages ${done} of ${total}…`
        : 'Reading pages…'
    }
    case 'filter':
      return 'Filtering events…'
    case 'judge': {
      const judged = c.events_judged ?? 0
      const total = run.eventsNew || 0
      return total > 0
        ? `Judging ${judged} of ${total} events…`
        : 'Judging events…'
    }
    default:
      return 'Working…'
  }
}

/** Build the run-report lines from a SearchResult (spec §8). */
function buildRunReport(result: SearchResult): string[] {
  const lines: string[] = []
  const c = result.stageCounts
  if (!c) {
    if (result.eventsFound === 0) {
      return ['Found no events. Try broader criteria.']
    }
    lines.push(`Found ${result.eventsFound} events, ${result.eventsNew} new.`)
    return lines
  }

  const queries = c.queries_planned ?? 0
  const results = c.results_fetched ?? 0
  const events = c.events_extracted ?? 0
  const judged = c.events_judged ?? 0
  const accepted = c.accepted ?? 0
  const queued = c.queued ?? 0
  const rejected = c.rejected ?? 0

  const filterKeys = [
    'filtered_incomplete', 'filtered_past', 'filtered_date',
    'filtered_place', 'filtered_non_event', 'filtered_duplicate',
  ] as const
  const totalFiltered = filterKeys.reduce((sum, k) => sum + (c[k] ?? 0), 0)
  const passed = Math.max(0, events - totalFiltered)

  lines.push(
    `${queries} queries → ${results} results → ${events} events → ${passed} passed filters → ${judged} judged → ${accepted} accepted, ${queued} queued, ${rejected} rejected`,
  )

  const filterLabels: Record<string, string> = {
    filtered_past: 'past',
    filtered_date: 'outside date window',
    filtered_place: 'wrong place',
    filtered_non_event: 'non-event',
    filtered_duplicate: 'duplicate',
    filtered_incomplete: 'incomplete',
  }
  const details = filterKeys
    .filter(k => (c[k] ?? 0) > 0)
    .map(k => `${c[k]} ${filterLabels[k]}`)
  if (details.length > 0) {
    lines.push(`Filtered: ${details.join(', ')}.`)
  }

  if (result.stoppedAtStage) {
    lines.push(
      `Stopped at ${result.stoppedAtStage}${result.error ? `: ${result.error}` : ''}.`,
    )
  }

  return lines
}

export function MainPage({ onSearchComplete, queuedEvents, onNavigateQueue }: MainPageProps) {
  const [criteriaText, setCriteriaText] = useState('')
  const [criteriaSaved, setCriteriaSaved] = useState(false)
  const [criteriaError, setCriteriaError] = useState('')
  const [criteriaSaving, setCriteriaSaving] = useState(false)

  const [lower, setLower] = useState(0)
  const [upper, setUpper] = useState(100)
  const [scoringSaved, setScoringSaved] = useState(false)
  const [scoringError, setScoringError] = useState('')
  const [scoringSaving, setScoringSaving] = useState(false)

  const [searching, setSearching] = useState(false)
  const [progressText, setProgressText] = useState('')
  const [searchReport, setSearchReport] = useState<{ lines: string[]; queued: number } | null>(null)
  const [searchIsError, setSearchIsError] = useState(false)
  const [searchErrorText, setSearchErrorText] = useState('')

  const [calendarUrl, setCalendarUrl] = useState('')
  const [copied, setCopied] = useState(false)

  const [userTimeZone, setUserTimeZone] = useState('UTC')

  // Results section state
  const [acceptedEvents, setAcceptedEvents] = useState<Event[]>([])
  const [queuedResultEvents, setQueuedResultEvents] = useState<Event[]>([])
  const [rejectedEvents, setRejectedEvents] = useState<Event[]>([])
  const [showRejected, setShowRejected] = useState(false)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const thresholdInvalid = !(lower >= 0 && lower < upper && upper <= 100)

  const refreshResults = useCallback(async () => {
    try {
      const [accepted, queued, rejected] = await Promise.all([
        listEvents('accepted'),
        listEvents('queued'),
        listEvents('rejected'),
      ])
      accepted.sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
      queued.sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
      rejected.sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
      setAcceptedEvents(accepted)
      setQueuedResultEvents(queued)
      setRejectedEvents(rejected)
    } catch {
      // silent — results section is supplementary
    }
  }, [])

  useEffect(() => {
    getCriteria().then((c) => {
      setCriteriaText((current) => (current === '' ? c.text : current))
      setUserTimeZone(c.timeZone)
    })
    getThresholds().then((t) => {
      setLower(t.lowerThreshold)
      setUpper(t.upperThreshold)
    })
    getCalendarUrl().then((r) => setCalendarUrl(r.url))
    refreshResults()

    // Reload persistence: check if a run is in progress
    getLastRun().then((resp) => {
      if (resp.run && resp.run.currentStage) {
        // Run is in progress — show progress and start polling
        setSearching(true)
        setProgressText(stageText(resp.run))
        startPolling()
      }
    }).catch(() => { /* no-op */ })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  function startPolling() {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const resp = await getLastRun()
        if (!resp.run) return
        setProgressText(stageText(resp.run))
        // Refresh results during the run to show events as they appear
        refreshResults()
        if (!resp.run.currentStage && resp.run.finishedAt) {
          // Run finished — stop polling
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          setSearching(false)
          const queueCount = await onSearchComplete()
          setSearchReport({ lines: buildRunReport(resp.run), queued: queueCount })
          setProgressText('')
          refreshResults()
        }
      } catch {
        // polling error — ignore
      }
    }, 3000)
  }

  function showCriteriaSaved() {
    setCriteriaSaved(true)
    setTimeout(() => setCriteriaSaved(false), 2000)
  }

  async function handleSaveCriteria() {
    setCriteriaSaving(true)
    setCriteriaSaved(false)
    setCriteriaError('')
    try {
      const saved = await saveCriteria(criteriaText, browserTz)
      setCriteriaText(saved.text)
      setUserTimeZone(saved.timeZone)
      showCriteriaSaved()
    } catch {
      setCriteriaError("Couldn't save. Try again.")
    } finally {
      setCriteriaSaving(false)
    }
  }

  async function handleSaveScoring() {
    if (thresholdInvalid) return
    setScoringSaving(true)
    setScoringSaved(false)
    setScoringError('')
    try {
      const saved = await saveThresholds({
        lowerThreshold: lower,
        upperThreshold: upper,
      })
      setLower(saved.lowerThreshold)
      setUpper(saved.upperThreshold)
      setScoringSaved(true)
      setTimeout(() => setScoringSaved(false), 2000)
    } catch {
      setScoringError("Couldn't save. Try again.")
    } finally {
      setScoringSaving(false)
    }
  }

  async function handleSearch() {
    setSearching(true)
    setSearchReport(null)
    setSearchIsError(false)
    setSearchErrorText('')
    setProgressText('Starting up…')

    // Save criteria draft first (decision 11)
    setCriteriaSaved(false)
    setCriteriaError('')
    try {
      const saved = await saveCriteria(criteriaText, browserTz)
      setCriteriaText(saved.text)
      setUserTimeZone(saved.timeZone)
      showCriteriaSaved()
    } catch {
      setCriteriaError("Couldn't save. Try again.")
      setSearching(false)
      setProgressText('')
      return
    }

    // Start polling for live progress
    startPolling()

    try {
      const result = await runSearch()
      // Stop polling — we have the final result
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
      setProgressText('')
      const queueCount = await onSearchComplete()

      if (result.eventsFound === 0 && !result.stageCounts) {
        setSearchErrorText('Found no events. Try broader criteria.')
      } else {
        setSearchReport({ lines: buildRunReport(result), queued: queueCount })
      }
      await refreshResults()
    } catch (err: unknown) {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
      setProgressText('')
      const e = err as Error & { status?: number; retryAfter?: number }
      if (e.status === 429) {
        const minutes = e.retryAfter ? Math.ceil(e.retryAfter / 60) : 60
        setSearchErrorText(`Search limit reached, try again in ${minutes} minutes`)
      } else {
        setSearchErrorText('Search failed. Try again.')
        setSearchIsError(true)
      }
    } finally {
      setSearching(false)
    }
  }

  async function handleDecide(id: string, decision: 'accepted' | 'rejected') {
    await decideEvent(id, decision)
    onSearchComplete()
    refreshResults()
  }

  async function handleClearAll() {
    await deleteAllEvents()
    setAcceptedEvents([])
    setQueuedResultEvents([])
    setRejectedEvents([])
    setShowRejected(false)
    onSearchComplete()
  }

  async function handleCopyCalendarUrl() {
    try {
      await navigator.clipboard.writeText(calendarUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard API unavailable (e.g. test environments)
    }
  }

  const hasResults = acceptedEvents.length > 0 || queuedResultEvents.length > 0 || rejectedEvents.length > 0

  const cards = (
    <div className="flex flex-col gap-4 sm:gap-6 max-w-2xl">
      {/* Criteria card */}
      <Card data-testid="criteria-card">
        <CardHeader>
          <CardTitle as="h2">What I&apos;m looking for</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Textarea
            aria-label="What I'm looking for"
            placeholder="e.g. jazz or folk concerts near Paris on weekends, under 40 EUR"
            value={criteriaText}
            onChange={(e) => setCriteriaText(e.target.value)}
            rows={4}
          />
          <div className="flex items-center gap-2">
            <Button
              aria-label="Save criteria"
              disabled={criteriaSaving}
              onClick={handleSaveCriteria}
            >
              Save
            </Button>
            {criteriaSaved && (
              <span role="status" className="text-sm font-medium text-accent-foreground animate-in fade-in-0 duration-200">Saved.</span>
            )}
            {criteriaError && (
              <span className="text-sm text-destructive">{criteriaError}</span>
            )}
          </div>
          {userTimeZone === 'UTC' && (
            <p data-testid="utc-notice" className="text-sm text-muted-foreground">
              Times shown in UTC until you save your criteria.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Scoring card */}
      <Card data-testid="scoring-card">
        <CardHeader>
          <CardTitle as="h2">How scoring works</CardTitle>
          <CardDescription>
            <p>Score 0 to 100.</p>
            <p>Below {lower}: rejected.</p>
            <p>Above {upper}: accepted.</p>
            <p>In between: you review.</p>
            <p className="mt-2 text-xs">Score bands: 90+ fits, 70–89 mostly fits, 40–69 open question, 10–39 off topic. Recommended thresholds: 90 / 40.</p>
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <ScoreScale
            lower={lower}
            upper={upper}
            onChange={(l, u) => { setLower(l); setUpper(u) }}
          />
          <div className="flex items-center gap-2">
            <Button
              aria-label="Save scoring"
              disabled={thresholdInvalid || scoringSaving}
              onClick={handleSaveScoring}
            >
              Save
            </Button>
            {scoringSaved && (
              <span role="status" className="text-sm font-medium text-accent-foreground animate-in fade-in-0 duration-200">Saved.</span>
            )}
            {scoringError && (
              <span className="text-sm text-destructive">{scoringError}</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Search card */}
      <Card data-testid="search-card">
        <CardHeader>
          <CardTitle as="h2">Search now</CardTitle>
          <CardDescription>
            The app also searches automatically every hour.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {!criteriaText.trim() && (
            <p className="text-sm text-muted-foreground">
              Write what you&apos;re looking for, then press Search now.
            </p>
          )}
          <Button
            disabled={!criteriaText.trim() || searching}
            aria-busy={searching ? true : undefined}
            onClick={handleSearch}
          >
            {searching ? 'Searching…' : 'Search now'}
          </Button>
          {searching && progressText && (
            <p data-testid="search-progress" role="status" className="text-sm text-muted-foreground animate-in fade-in-0 duration-200">
              {progressText}
            </p>
          )}
          {searchReport && (
            <div data-testid="search-result" role="status" className="text-sm animate-in fade-in-0 slide-in-from-top-1 duration-200">
              {searchReport.lines.map((line, i) => (
                <p key={i}>{line}</p>
              ))}
              {searchReport.queued > 0 && (
                <Button
                  variant="default"
                  size="sm"
                  className="mt-2"
                  onClick={onNavigateQueue}
                >
                  Review {searchReport.queued} events →
                </Button>
              )}
            </div>
          )}
          {searchErrorText && (
            <p
              data-testid="search-result"
              role="status"
              className={searchIsError ? 'text-sm text-destructive' : 'text-sm'}
            >
              {searchErrorText}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Results section */}
      {hasResults && (
        <section data-testid="results-section">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-heading text-2xl font-bold tracking-tight">Results</h2>
            <ConfirmAction
              label="Clear all"
              prompt="Delete all your events? This cannot be undone."
              confirmLabel="Delete all"
              confirmingLabel="Deleting…"
              errorText="Couldn't delete events. Try again."
              onConfirm={handleClearAll}
              testId="clear-all"
              confirmTestId="clear-all-confirm"
            />
          </div>
          <p data-testid="results-summary" className="text-sm text-muted-foreground mb-4">
            {acceptedEvents.length} in your calendar · {queuedResultEvents.length} to review · {rejectedEvents.length} rejected
          </p>
          {acceptedEvents.length > 0 && (
            <div data-testid="results-accepted" className="mb-4">
              <h3 className="font-heading text-lg font-semibold tracking-tight mb-2">
                In your calendar ({acceptedEvents.length})
              </h3>
              <div className="flex flex-col gap-3">
                {acceptedEvents.map((evt) => (
                  <EventCard
                    key={evt.id}
                    event={evt}
                    variant="all"
                    onDecide={handleDecide}
                  />
                ))}
              </div>
            </div>
          )}
          {queuedResultEvents.length > 0 && (
            <div data-testid="results-queued" className="mb-4">
              <h3 className="font-heading text-lg font-semibold tracking-tight mb-2">
                To review ({queuedResultEvents.length})
              </h3>
              <div className="flex flex-col gap-3">
                {queuedResultEvents.map((evt) => (
                  <EventCard
                    key={evt.id}
                    event={evt}
                    variant="queue"
                    onDecide={handleDecide}
                  />
                ))}
              </div>
            </div>
          )}
          {rejectedEvents.length > 0 && (
            <div data-testid="results-rejected" className="mb-4">
              <h3 className="font-heading text-lg font-semibold tracking-tight mb-2">
                Rejected ({rejectedEvents.length})
                {' · '}
                <button
                  className="text-sm font-normal text-muted-foreground underline underline-offset-2 hover:text-foreground"
                  onClick={() => setShowRejected(!showRejected)}
                  data-testid="rejected-toggle"
                >
                  {showRejected ? 'hide' : 'show all'}
                </button>
              </h3>
              {showRejected && (
                <div className="flex flex-col gap-3">
                  {rejectedEvents.map((evt) => (
                    <EventCard
                      key={evt.id}
                      event={evt}
                      variant="all"
                      onDecide={handleDecide}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Calendar card */}
      {calendarUrl && (
        <Card data-testid="calendar-card">
          <CardHeader>
            <CardTitle as="h2">Your calendar feed</CardTitle>
            <CardDescription>
              Paste this link into your calendar app. Accepted events will appear
              there.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Input
                readOnly
                value={calendarUrl}
                data-testid="calendar-url"
                aria-label="Calendar feed URL"
                className="flex-1 min-w-0 font-mono text-xs bg-muted/50"
              />
              <Button onClick={handleCopyCalendarUrl} data-testid="copy-calendar-url">
                {copied ? 'Copied' : 'Copy'}
              </Button>
              <ConfirmAction
                label="Reset link"
                prompt="This will break any existing subscription. Reset?"
                confirmLabel="Reset"
                errorText="Couldn't reset the link. Try again."
                onConfirm={async () => {
                  const r = await rotateCalendarUrl()
                  setCalendarUrl(r.url)
                }}
                testId="rotate-calendar-url"
                confirmTestId="rotate-confirm"
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )

  const sidebar = queuedEvents.length > 0 ? (
    <aside data-testid="review-sidebar" className="flex flex-col gap-3">
      <h3 className="font-heading text-lg font-semibold tracking-tight">To review</h3>
      <div className="flex flex-col gap-2">
        {queuedEvents.slice(0, 5).map((evt) => (
          <button
            key={evt.id}
            className="text-left rounded-lg border bg-card p-3 hover:bg-accent/50 transition-colors"
            onClick={onNavigateQueue}
          >
            <p className="text-sm font-medium leading-snug">{evt.title}</p>
            <p className="text-xs font-semibold tabular-nums text-muted-foreground mt-0.5">Score {evt.score}%</p>
          </button>
        ))}
      </div>
      {queuedEvents.length > 5 && (
        <Button variant="ghost" size="sm" onClick={onNavigateQueue}>
          See all {queuedEvents.length} →
        </Button>
      )}
    </aside>
  ) : null

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 lg:gap-8 items-start">
      {cards}
      {sidebar}
    </div>
  )
}
