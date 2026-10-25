import { useCallback, useEffect, useLayoutEffect, useRef, useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScoreScale } from '@/components/ScoreScale'
import { ConfirmAction } from '@/components/ConfirmAction'
import { COL, EventRow, ROW_GRID, formatDay } from '@/components/EventCard'
import { EventDetail } from '@/components/EventDetail'
import { EarlierRuns, fmtStamp } from '@/components/EarlierRuns'
import { Funnel, funnelNumbers } from '@/components/Funnel'
import { MonthCalendar } from '@/components/MonthCalendar'
import {
  getCriteria,
  saveCriteria,
  getThresholds,
  saveThresholds,
  runSearch,
  getLastRun,
  getRuns,
  listEvents,
  decideEvent,
  deleteAllEvents,
  getCalendarUrl,
  rotateCalendarUrl,
} from '@/services/api'
import type { Event, RunSummary, SearchResult } from '@/services/api'

const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone

/** [done, total] of the live stage when it counts items; the text and the hairline both read it. */
function stageProgress(run: SearchResult): [number, number] | null {
  const c = run.stageCounts ?? {}
  switch (run.currentStage) {
    // the extractor iterates results after known-page removal
    case 'extract': return [c.pages_content_pass ?? 0, (c.results_fetched ?? 0) - (c.results_known ?? 0)]
    case 'detail_hop': return [c.detail_pages_done ?? 0, c.detail_pages_to_open ?? 0]
    // events_to_judge is in stageCounts during the live run; eventsNew only after finalise
    case 'judge': return [c.events_judged ?? 0, c.events_to_judge ?? run.eventsNew ?? 0]
    default: return null
  }
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

  const p = stageProgress(run)
  const counted = (what: string) => (p && p[1] > 0 ? `${what} ${p[0]} / ${p[1]}…` : `${what}…`)
  switch (stage) {
    case 'adapters':
    case 'criteria':
    case 'window':
      return 'Starting up…'
    case 'search':
      return 'Searching the web…'
    case 'extract':
      return counted('Reading pages')
    case 'detail_hop':
      return counted('Opening event pages')
    case 'filter':
      return 'Filtering events…'
    case 'judge':
      return counted('Judging events')
    default:
      return 'Working…'
  }
}

/** 0–1 fraction of the live stage, or null when the total is unknown. */
export function stageFraction(run: SearchResult): number | null {
  const p = stageProgress(run)
  return p && p[1] > 0 ? p[0] / p[1] : null
}

const STAGES = ['search', 'extract', 'detail_hop', 'filter', 'judge']

/** The chronology lines: finished stages, then the live line or the stop line. */
export function stageLines(run: SearchResult): string[] {
  const c = run.stageCounts ?? {}
  const n = funnelNumbers(c)
  const opened = n.pagesDetailFetched + n.detailFetchErrors // = the live line's total, detail_pages_to_open
  // one entry per stage; found = screened out + judged, non-events are pages, not events
  // shortcut: new = fetched - known ignores duplicate URLs removed in between; upgrade if the backend ever counts them
  const done = [
    [n.pagesKnown > 0
      ? `Searched the web: ${n.pages} pages, ${n.pagesKnown} already known from earlier runs, ${n.pages - n.pagesKnown} new`
      : `Searched the web, ${n.pages} pages`],
    [`Read ${n.pages - n.pagesKnown} pages, found ${n.found} events`, ...(n.nonEvent > 0 ? [`Skipped ${n.nonEvent} pages that were not events`] : [])],
    // a failed fetch keeps the listing's record for the screen: a count of pages, never a screening reason
    [...(opened > 0 ? [`Opened ${opened} event pages${n.detailFetchErrors > 0 ? `, ${n.detailFetchErrors} failed` : ''}`] : [])],
    [`Screened out: ${n.notJudged}`],
    [`Judged ${n.judged} · ${n.accepted} in calendar, ${n.queued} to review, ${n.rejected} rejected${n.judgeErrors > 0 ? `, ${n.judgeErrors} not scored yet` : ''}`],
  ]
  const stage = run.currentStage ?? run.stoppedAtStage
  const at = stage ? STAGES.indexOf(stage) : run.finishedAt ? STAGES.length : 0
  const lines = done.slice(0, Math.max(0, at)).flat()
  if (run.currentStage) lines.push(stageText(run))
  if (run.stoppedAtStage) lines.push(`Stopped at ${run.stoppedAtStage}${run.error ? `: ${run.error}` : ''}.`)
  return lines
}

/** "18 Oct 10:00 · your run · 1 min 30 s" */
export function runHeader(run: SearchResult): string {
  const parts: string[] = []
  if (run.startedAt) parts.push(fmtStamp(run.startedAt))
  if (run.trigger) parts.push(run.trigger === 'scheduled' ? 'automatic run' : 'your run')
  const raw = run.durationSeconds
    ?? (run.startedAt && run.finishedAt ? (Date.parse(run.finishedAt) - Date.parse(run.startedAt)) / 1000 : null)
  if (raw == null) parts.push('running…')
  else {
    const secs = Math.round(raw)
    parts.push(secs >= 60 ? `${Math.floor(secs / 60)} min ${secs % 60} s` : `${secs} s`)
  }
  return parts.join(' · ')
}

/** The most common rejected_* reason, or '' when the counts are missing. */
export function mostlyReason(c: Record<string, number>): string {
  const n = funnelNumbers(c)
  const top = Math.max(n.rejectedDatePlace, n.rejectedOffTopic, n.rejectedOther)
  if (top === 0) return ''
  if (top === n.rejectedDatePlace) return 'wrong date or place'
  return top === n.rejectedOffTopic ? 'off topic' : 'below your threshold'
}

/** Events in date order, grouped by day label ("Tue 21 Oct"). */
export function groupByDay(events: Event[]): [string, Event[]][] {
  const sorted = [...events].sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
  const groups = new Map<string, Event[]>()
  for (const e of sorted) {
    const k = formatDay(e)
    groups.set(k, [...(groups.get(k) ?? []), e])
  }
  return [...groups]
}

const tlLine = "relative mb-1.5 before:absolute before:-left-[19px] before:top-1.5 before:size-2 before:rounded-full before:bg-input before:content-['']"
const tlLive = `${tlLine} before:!bg-primary`

/** True when the user prefers reduced motion (respects live changes). */
function useReducedMotion() {
  const mql = typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)') : null
  const [reduced, setReduced] = useState(mql?.matches ?? false)
  useEffect(() => {
    if (!mql) return
    const h = (e: MediaQueryListEvent) => setReduced(e.matches)
    mql.addEventListener('change', h)
    return () => mql.removeEventListener('change', h)
  }, [mql])
  return reduced
}

/** Hairline track + breathing dot. With a fraction: 2 px filled track. Without: dot only. */
function ProgressHairline({ fraction }: { fraction: number | null }) {
  const noMotion = useReducedMotion()
  const cls = noMotion ? ' progress-no-motion' : ''
  if (fraction != null) {
    const pct = `${Math.min(100, Math.max(0, fraction * 100))}%`
    return (
      <span data-testid="progress-hairline" className={`progress-hairline${cls}`} aria-hidden="true">
        <span className="progress-hairline-fill" style={{ width: pct }} />
      </span>
    )
  }
  return <span data-testid="progress-hairline" className={`progress-hairline-dot${cls}`} aria-hidden="true" />
}
const label = 'mb-1.5 text-[11px] font-semibold uppercase tracking-[.08em] text-muted-foreground'
// same contour as the login and register boxes
const PANEL = 'rounded-xl border-2 border-ring/50 bg-card p-4 shadow-sm'

export function MainPage() {
  const [criteriaText, setCriteriaText] = useState('')
  const [draft, setDraft] = useState('')
  const [criteriaError, setCriteriaError] = useState('')
  // a Search while a run is in progress saves the text for the next run
  const [queued, setQueued] = useState(false)

  const [lower, setLower] = useState(0)
  const [upper, setUpper] = useState(100)
  const [scoringSaved, setScoringSaved] = useState(false)
  const [scoringError, setScoringError] = useState('')
  const [scoringSaving, setScoringSaving] = useState(false)

  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [lastRun, setLastRun] = useState<SearchResult | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])

  const [calendarUrl, setCalendarUrl] = useState('')
  const [copied, setCopied] = useState(false)

  const [events, setEvents] = useState<Event[]>([])
  const [showRejected, setShowRejected] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const screenRef = useRef<HTMLDivElement>(null)
  const rowRef = useRef<HTMLDivElement>(null)
  const detailRef = useRef<HTMLDivElement>(null)
  const tieRef = useRef<SVGSVGElement>(null)

  const thresholdInvalid = !(lower >= 0 && lower < upper && upper <= 100)

  const refreshEvents = useCallback(async () => {
    try {
      setEvents(await listEvents())
    } catch {
      // the list is supplementary; the next poll or action refreshes it
    }
  }, [])

  const refreshRuns = useCallback(async () => {
    try {
      setRuns((await getRuns()).runs)
    } catch {
      // the backend may predate /api/search/runs; the page works without it
    }
  }, [])

  useEffect(() => {
    getCriteria().then((c) => {
      setCriteriaText(c.text)
      // a slow load must not wipe what the user has typed meanwhile
      setDraft((d) => d || c.text)
    })
    getThresholds().then((t) => {
      setLower(t.lowerThreshold)
      setUpper(t.upperThreshold)
    })
    getCalendarUrl().then((r) => setCalendarUrl(r.url))
    refreshEvents()
    refreshRuns()
    // Reload persistence: resume the live view when a run is in progress
    getLastRun().then((resp) => {
      if (!resp.run) return
      setLastRun(resp.run)
      if (resp.run.currentStage) {
        setSearching(true)
        startPolling(null)
      }
    }).catch(() => { /* no-op */ })
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function stopPolling() {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = null
  }

  async function finishRun(run: SearchResult) {
    stopPolling()
    setSearching(false)
    setQueued(false)
    setLastRun(run)
    refreshEvents()
    refreshRuns()
  }

  /** Polls last-run; `previousRunId` is skipped until the new run has replaced it. */
  function startPolling(previousRunId: string | null) {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const resp = await getLastRun()
        if (!resp.run || resp.run.runId === previousRunId) return
        setLastRun(resp.run)
        refreshEvents()
        if (!resp.run.currentStage && resp.run.finishedAt) finishRun(resp.run)
      } catch {
        // polling error — the next tick retries
      }
    }, 3000)
  }

  async function handleSaveScoring() {
    if (thresholdInvalid) return
    setScoringSaving(true)
    setScoringSaved(false)
    setScoringError('')
    try {
      const saved = await saveThresholds({ lowerThreshold: lower, upperThreshold: upper })
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

  /** One action: save what is in the box (PUT), then start the run (POST). While a run goes, only save. */
  async function handleSearch(e?: FormEvent) {
    e?.preventDefault()
    if (!draft.trim()) return
    setCriteriaError('')
    setSearchError('')
    const wasSearching = searching
    setSearching(true)
    try {
      const saved = await saveCriteria(draft, browserTz)
      setCriteriaText(saved.text)
      setDraft(saved.text)
    } catch {
      setCriteriaError("Couldn't save. Try again.")
      setSearching(wasSearching)
      return
    }
    if (wasSearching) {
      setQueued(true)
      return
    }
    const previousRunId = lastRun?.runId ?? null
    setLastRun({
      runId: '', eventsFound: 0, eventsNew: 0, stageCounts: null, currentStage: 'adapters',
      stoppedAtStage: null, error: null, startedAt: new Date().toISOString(), finishedAt: null, trigger: 'manual',
    })
    startPolling(previousRunId)
    try {
      await finishRun(await runSearch())
    } catch (err: unknown) {
      stopPolling()
      setSearching(false)
      const e = err as Error & { status?: number; retryAfter?: number }
      if (e.status === 429) {
        const minutes = e.retryAfter ? Math.ceil(e.retryAfter / 60) : 60
        setSearchError(`Search limit reached, try again in ${minutes} minutes`)
      } else {
        setSearchError('Search failed. Try again.')
      }
      getLastRun().then((r) => setLastRun(r.run)).catch(() => { /* keep the placeholder */ })
    }
  }

  async function handleDecide(id: string, decision: 'accepted' | 'rejected') {
    await decideEvent(id, decision)
    refreshEvents()
  }

  async function handleClearAll() {
    await deleteAllEvents()
    setEvents([])
    setSelectedId(null)
    setShowRejected(false)
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

  // Dotted tie from the selected row's right edge to the detail's left edge, from real positions
  const drawTie = useCallback(() => {
    const s = screenRef.current, c = rowRef.current, d = detailRef.current, svg = tieRef.current
    if (!s || !svg) return
    if (!c || !d) {
      // no selected row on screen: erase the line rather than leave it pointing at the old spot
      svg.querySelector('path')!.setAttribute('d', '')
      svg.querySelectorAll('circle').forEach((k) => k.removeAttribute('cx'))
      return
    }
    const S = s.getBoundingClientRect(), C = c.getBoundingClientRect(), D = d.getBoundingClientRect()
    const x1 = C.right - S.left, y1 = C.top - S.top + C.height / 2
    const x2 = D.left - S.left, y2 = D.top - S.top + D.height / 2
    const xm = x1 + (x2 - x1) / 2
    svg.querySelector('path')!.setAttribute('d', `M${x1} ${y1} H${xm} V${y2} H${x2}`)
    const [c1, c2] = svg.querySelectorAll('circle')
    c1.setAttribute('cx', `${x1}`); c1.setAttribute('cy', `${y1}`)
    c2.setAttribute('cx', `${x2}`); c2.setAttribute('cy', `${y2}`)
  }, [])
  useLayoutEffect(drawTie)
  useEffect(() => {
    window.addEventListener('resize', drawTie)
    const ro = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(drawTie)
    if (screenRef.current) ro?.observe(screenRef.current)
    return () => { window.removeEventListener('resize', drawTie); ro?.disconnect() }
  }, [drawTie])

  const accepted = events.filter((e) => e.status === 'accepted')
  const rejected = events.filter((e) => e.status === 'rejected')
  const shown = events.filter((e) => e.status === 'accepted' || e.status === 'queued' || (showRejected && e.status === 'rejected'))
  // the selection follows the rows on screen: a row that leaves (decided, cleared, folded) deselects
  const selectedEvent = shown.find((e) => e.id === selectedId) ?? null
  useEffect(() => {
    if (selectedId && !selectedEvent) setSelectedId(null)
  }, [selectedId, selectedEvent])
  const todayKey = formatDay({ dateTime: new Date().toISOString(), startTz: null } as Event)
  const reason = lastRun?.stageCounts ? mostlyReason(lastRun.stageCounts) : ''
  const earlier = runs.filter((r) => r.runId !== lastRun?.runId)

  return (
    <div ref={screenRef} className="relative grid grid-cols-1 gap-6 md:grid-cols-[1fr_260px] md:gap-8 items-start">
      <div className="min-w-0">
        {/* Search box: one form, Search takes whatever is in the box */}
        <form data-testid="search-box" className={`${PANEL} text-sm`} onSubmit={handleSearch}>
          <label htmlFor="criteria" className="sr-only">What are you looking for?</label>
          <textarea
            id="criteria"
            data-testid="criteria-text"
            placeholder="e.g. jazz or folk concerts near Paris on weekends"
            value={draft}
            rows={1}
            className="field-sizing-content max-h-24 w-full resize-none rounded-lg border border-input bg-background px-3 py-2 text-base font-medium leading-snug text-foreground outline-none placeholder:font-normal placeholder:italic placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 md:text-lg"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSearch() }
              if (e.key === 'Escape') setDraft(criteriaText)
            }}
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Button
              type="submit"
              size="sm"
              disabled={!draft.trim() || searching}
              aria-busy={searching ? true : undefined}
            >
              {searching ? 'Searching…' : lastRun ? 'Search again' : 'Search now'}
            </Button>
            {queued && <span role="status" className="text-muted-foreground">Saved for the next search</span>}
            {criteriaError && <span className="text-destructive">{criteriaError}</span>}
          </div>
          {searchError && (
            <p data-testid="search-error" role="status" className="mt-2 text-destructive">{searchError}</p>
          )}
        </form>

        {/* Run chronology and funnel */}
        {lastRun && (
          <div data-testid="run" className="mt-3.5 grid gap-4">
            <div data-testid="run-chronology" className="border-l-2 border-border pl-3.5 text-sm">
              <p className={`${tlLine} font-mono text-xs text-muted-foreground`}>{runHeader(lastRun)}</p>
              {stageLines(lastRun).map((line, i) => {
                const isLive = line === stageText(lastRun) && !!lastRun.currentStage
                return (
                  <p
                    key={i}
                    className={isLive ? tlLive : tlLine}
                    data-testid={isLive ? 'search-progress' : undefined}
                    role={isLive ? 'status' : undefined}
                  >
                    {isLive ? (
                      <span className="flex flex-wrap items-center gap-x-3.5 gap-y-1">
                        <span className="whitespace-nowrap">{line}</span>
                        <ProgressHairline fraction={stageFraction(lastRun)} />
                      </span>
                    ) : line}
                  </p>
                )
              })}
            </div>
            {lastRun.stageCounts && <Funnel counts={lastRun.stageCounts} countsVersion={lastRun.countsVersion ?? 1} className="hidden md:block" />}
          </div>
        )}
        <EarlierRuns runs={earlier} />

        {/* Results */}
        {events.length > 0 && (
          <section data-testid="results-section" className="mt-4">
            <div className="flex items-center justify-between">
              <h2 className="font-heading text-xl font-bold tracking-tight">Results</h2>
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
            <div data-testid="row-header" className={`${ROW_GRID} mt-3 border border-transparent ${label} mb-0`}>
              <span>Event</span>
              <span className={COL.time}>Start</span>
              <span className={COL.place}>Where</span>
              <span className={COL.score}>Score</span>
              <span className={COL.status}>Status</span>
            </div>
            {groupByDay(shown).map(([day, dayEvents]) => (
              <div key={day}>
                <p data-testid="day-heading" className={`mt-2.5 ${label}`}>{day === todayKey ? `Tonight · ${day}` : day}</p>
                <div className="grid gap-1.5">
                  {dayEvents.map((evt) => (
                    <EventRow
                      key={evt.id}
                      event={evt}
                      selected={evt.id === selectedId}
                      onSelect={(id) => setSelectedId(id === selectedId ? null : id)}
                      rowRef={evt.id === selectedId ? rowRef : undefined}
                    />
                  ))}
                </div>
              </div>
            ))}
            {rejected.length > 0 && (
              <p className="mt-2 text-sm text-muted-foreground">
                {rejected.length} out{reason ? `, mostly ${reason}` : ''} ·{' '}
                <button
                  data-testid="rejected-toggle"
                  className="underline underline-offset-2 hover:text-foreground"
                  onClick={() => setShowRejected(!showRejected)}
                >
                  {showRejected ? 'hide' : 'show'}
                </button>
              </p>
            )}
          </section>
        )}
      </div>

      {/* Rail */}
      <aside className="grid content-start gap-4 md:border-l md:pl-4">
        <MonthCalendar dates={accepted.map((e) => e.dateTime)} />
        {calendarUrl && (
          <div>
            <p className={label}>Calendar feed</p>
            <div className="flex flex-wrap gap-2">
              <Input
                readOnly
                value={calendarUrl}
                data-testid="calendar-url"
                aria-label="Calendar feed URL"
                className="w-full min-w-0 font-mono text-xs bg-muted/50"
              />
              <Button size="sm" variant="outline" onClick={handleCopyCalendarUrl} data-testid="copy-calendar-url">
                {copied ? 'Copied' : 'Copy'}
              </Button>
              <ConfirmAction
                label="Reset link"
                prompt="This will break any existing subscription. Reset?"
                confirmLabel="Reset"
                errorText="Couldn't reset the link. Try again."
                onConfirm={async () => setCalendarUrl((await rotateCalendarUrl()).url)}
                testId="rotate-calendar-url"
                confirmTestId="rotate-confirm"
              />
            </div>
          </div>
        )}
        <div data-testid="searches">
          <p className={label}>Searches</p>
          <p className="text-sm">{criteriaText || <span className="text-muted-foreground">no search yet</span>}</p>
          <button disabled title="coming later" className="mt-1 text-sm text-muted-foreground disabled:opacity-60">+ new search</button>
        </div>
        <details data-testid="scoring-card" className="text-sm">
          <summary className={`cursor-pointer ${label}`}>Scoring</summary>
          <div className="mt-2 grid gap-3">
            <ScoreScale lower={lower} upper={upper} onChange={(l, u) => { setLower(l); setUpper(u) }} />
            <div className="flex items-center gap-2">
              <Button size="sm" aria-label="Save scoring" disabled={thresholdInvalid || scoringSaving} onClick={handleSaveScoring}>
                Save
              </Button>
              {scoringSaved && <span role="status" className="font-medium text-accent-foreground">Saved.</span>}
              {scoringError && <span className="text-destructive">{scoringError}</span>}
            </div>
          </div>
        </details>
        {selectedEvent && (
          <div className="fixed inset-x-0 bottom-0 z-20 max-h-[70vh] overflow-y-auto border-t bg-background p-3 shadow-lg md:static md:max-h-none md:overflow-visible md:border-0 md:bg-transparent md:p-0 md:shadow-none">
            <EventDetail
              event={selectedEvent}
              onDecide={handleDecide}
              onClose={() => setSelectedId(null)}
              detailRef={detailRef}
            />
          </div>
        )}
      </aside>
      <svg ref={tieRef} data-testid="tie" aria-hidden="true" className="pointer-events-none absolute inset-0 hidden h-full w-full overflow-visible md:block">
        <path d="" fill="none" stroke="var(--ring)" strokeWidth="1.5" strokeDasharray="3 4" />
        <circle r="2.5" fill="var(--ring)" />
        <circle r="2.5" fill="var(--ring)" />
      </svg>
    </div>
  )
}
