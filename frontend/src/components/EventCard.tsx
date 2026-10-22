import type { Ref } from 'react'
import type { Event } from '@/services/api'

/** Exported for testing — mock this to simulate a different browser zone. */
export function getBrowserTz(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/** Format date without year, stripping the en-GB comma after weekday. */
function fmtDate(date: Date, tz: string | undefined): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone: tz,
  }).formatToParts(date)
  let out = ''
  let afterWeekday = false
  for (const p of parts) {
    if (p.type === 'weekday') {
      out += p.value
      afterWeekday = true
    } else if (afterWeekday && p.type === 'literal') {
      out += ' '
      afterWeekday = false
    } else {
      out += p.value
      afterWeekday = false
    }
  }
  return out
}

export function formatDay(event: Event): string {
  const { dateTime, startTz } = event
  // Date-only: no T in the string — use midday UTC to avoid date rollover
  if (!dateTime.includes('T')) {
    const [y, m, d] = dateTime.split('-').map(Number)
    return fmtDate(new Date(Date.UTC(y, m - 1, d, 12, 0, 0)), 'UTC')
  }
  return fmtDate(new Date(dateTime), startTz || undefined)
}

/** "20:00", or "20:00 CEST" / "20:00 GMT+9" when the event zone differs from the viewer's. */
export function formatTime(event: Event, viewerTz?: string): string {
  const { dateTime, startTz } = event
  if (!dateTime.includes('T')) return 'no time'
  const parts = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit', minute: '2-digit', hour12: false, timeZone: startTz || undefined, timeZoneName: 'short',
  }).formatToParts(new Date(dateTime))
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? ''
  const time = `${get('hour')}:${get('minute')}`
  return startTz && startTz !== (viewerTz ?? getBrowserTz()) ? `${time} ${get('timeZoneName')}` : time
}

export function formatWhere(event: Event): string {
  if (event.country === 'ZZ') return 'place unknown'
  const parts: string[] = []
  if (event.place) parts.push(event.place)
  if (event.city && !event.place.includes(event.city)) parts.push(event.city)
  // the API's place is "venue, city, country" since search v2; do not print the country twice
  if (event.country && !event.place.endsWith(event.country)) parts.push(event.country)
  return parts.join(', ') || 'place unknown'
}

const STATUS_PILL = {
  accepted: ['In calendar', 'bg-zone-calendar/30'],
  queued: ['Review', 'bg-zone-decide'],
  rejected: ['Out', 'bg-zone-rejected/60'],
  new: ['New', 'bg-muted'],
} as const

/** Shared by the rows and the column-header row above them, so the columns line up. */
export const ROW_GRID = 'grid grid-cols-[minmax(0,1fr)_auto_auto_auto] md:grid-cols-[minmax(0,1fr)_auto_auto_auto_auto] items-center gap-2 md:gap-3.5 px-2.5 whitespace-nowrap'
export const COL = {
  time: 'w-20 md:w-[6.5rem] truncate',
  place: 'hidden md:block w-44 truncate',
  score: 'w-10 text-right',
  status: 'w-[72px] md:w-[86px] text-center',
}

export function EventRow({
  event,
  selected,
  onSelect,
  rowRef,
}: {
  event: Event
  selected: boolean
  onSelect: (id: string) => void
  rowRef?: Ref<HTMLDivElement>
}) {
  const [pillText, pillColor] = STATUS_PILL[event.status]
  return (
    <div
      ref={rowRef}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      data-testid={`event-row-${event.id}`}
      onClick={() => onSelect(event.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect(event.id)
        }
      }}
      className={`${ROW_GRID} rounded-lg border py-2 text-sm cursor-pointer outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
        selected ? 'border-ring bg-accent/40' : 'border-border bg-card hover:bg-muted/50'
      }`}
    >
      <a
        href={event.link}
        target="_blank"
        rel="noopener noreferrer"
        className="font-semibold truncate hover:underline"
      >
        {event.title}
      </a>
      <span data-testid="row-time" className={`${COL.time} text-xs text-muted-foreground tabular-nums`}>
        {formatTime(event)}
      </span>
      <span data-testid="row-place" className={`${COL.place} text-xs text-muted-foreground`}>
        {formatWhere(event)}
      </span>
      <span data-testid="row-score" className={`${COL.score} font-mono text-xs text-muted-foreground tabular-nums`}>
        {event.score}%
      </span>
      <span
        data-testid="row-status"
        className={`${COL.status} rounded-full px-2 py-px text-[11px] font-medium ${pillColor}`}
      >
        {pillText}
      </span>
    </div>
  )
}
