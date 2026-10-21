import { useState } from 'react'
import {
  Card,
  CardContent,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/ConfirmAction'
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

function fmtTime(date: Date, tz: string | undefined): string {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: tz,
  }).format(date)
}

export function formatWhen(event: Event, viewerTz?: string): string {
  const { dateTime, startTz } = event
  const browserTz = viewerTz ?? getBrowserTz()

  // Date-only: no T in the string — use midday UTC to avoid date rollover
  if (!dateTime.includes('T')) {
    const [y, m, d] = dateTime.split('-').map(Number)
    const midday = new Date(Date.UTC(y, m - 1, d, 12, 0, 0))
    return fmtDate(midday, 'UTC')
  }

  const date = new Date(dateTime)
  const tz = startTz || undefined
  let result = `${fmtDate(date, tz)} · ${fmtTime(date, tz)}`

  // Tz suffix only when event zone ≠ viewer zone
  if (startTz && startTz !== browserTz) {
    result += ` (${startTz})`
  }

  return result
}

function formatWhere(event: Event): string {
  if (event.country === 'ZZ') return 'place unknown'
  const parts: string[] = []
  if (event.place) parts.push(event.place)
  if (event.city && !event.place.includes(event.city)) parts.push(event.city)
  // the API's place is "venue, city, country" since search v2; do not print the country twice
  if (event.country && !event.place.endsWith(event.country)) parts.push(event.country)
  return parts.join(', ') || 'place unknown'
}

type EventCardProps = {
  event: Event
  variant: 'queue' | 'all'
  onDecide?: (id: string, decision: 'accepted' | 'rejected') => Promise<void>
}

export function EventCard({ event, variant, onDecide }: EventCardProps) {
  const [deciding, setDeciding] = useState<'accepted' | 'rejected' | null>(
    null,
  )
  const [leaving, setLeaving] = useState(false)
  const [error, setError] = useState('')
  const [detailsOpen, setDetailsOpen] = useState(event.status === 'rejected')

  async function handleDecide(decision: 'accepted' | 'rejected') {
    setDeciding(decision)
    setError('')
    try {
      await onDecide?.(event.id, decision)
      if (variant === 'queue') setLeaving(true)
    } catch {
      setError("Couldn't save your decision. Try again.")
      setDeciding(null)
    }
  }

  const infoLine = [
    formatWhen(event),
    formatWhere(event),
    `Score: ${event.score}%`,
  ].join(' · ')

  return (
    <Card
      data-testid={`event-card-${event.id}`}
      className={leaving ? 'animate-out fade-out-0 slide-out-to-right-2 fill-mode-forwards duration-200' : undefined}
    >
      <CardContent className="flex flex-col gap-2 pt-5 text-sm">
        {/* 1. Title — links to event page */}
        <a
          href={event.link}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold leading-snug hover:underline"
        >
          {event.title}
        </a>

        {/* 2. Muted info line: when · where · Score: N% */}
        <p className="text-muted-foreground" data-testid="event-info-line">
          {infoLine}
        </p>

        {/* 3. Action buttons per status */}
        {event.status === 'accepted' && onDecide && (
          <div className="pt-1">
            <ConfirmAction
              label="Remove from calendar"
              prompt="Remove this event from your calendar?"
              confirmLabel="Remove"
              confirmingLabel="Removing…"
              errorText="Couldn't remove it. Try again."
              onConfirm={() => onDecide(event.id, 'rejected')}
            />
          </div>
        )}
        {event.status === 'queued' && onDecide && (
          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              disabled={deciding !== null}
              onClick={() => handleDecide('accepted')}
            >
              {deciding === 'accepted' ? 'Adding…' : 'Add to calendar'}
            </Button>
            <Button
              size="sm"
              variant="destructive"
              disabled={deciding !== null}
              onClick={() => handleDecide('rejected')}
            >
              {deciding === 'rejected' ? 'Rejecting…' : 'Reject'}
            </Button>
          </div>
        )}
        {event.status === 'rejected' && onDecide && (
          <div className="pt-1">
            <Button
              size="sm"
              disabled={deciding !== null}
              onClick={() => handleDecide('accepted')}
            >
              {deciding === 'accepted' ? 'Adding…' : 'Add to calendar'}
            </Button>
          </div>
        )}

        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}

        {/* 4. Details toggle — quietest element on the card */}
        <div>
          <button
            className="text-muted-foreground hover:text-foreground transition-colors"
            style={{ fontSize: '12px' }}
            onClick={() => setDetailsOpen(!detailsOpen)}
            aria-expanded={detailsOpen}
          >
            Details {detailsOpen ? '‹' : '›'}
          </button>
          {detailsOpen && (
            <p className="text-muted-foreground mt-1" style={{ fontSize: '13px' }}>
              {event.scoreReason}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
