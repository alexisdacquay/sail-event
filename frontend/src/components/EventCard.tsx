import { useEffect, useState } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/ConfirmAction'
import type { Event } from '@/services/api'

function badgeText(event: Event): string {
  if (event.status === 'accepted') {
    return event.decidedBy === 'user' ? 'Accepted by you' : 'Auto-accepted'
  }
  if (event.status === 'rejected') {
    return event.decidedBy === 'user' ? 'Rejected by you' : 'Auto-rejected'
  }
  return 'To review'
}

const badgeVariant: Record<string, 'default' | 'secondary' | 'destructive'> = {
  accepted: 'default',
  rejected: 'destructive',
  queued: 'secondary',
}

/** Exported for testing — mock this to simulate a different browser zone. */
export function getBrowserTz(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/** Format date-time parts without the comma after weekday that en-GB adds. */
function fmtParts(date: Date, tz: string | undefined, includeTime: boolean): string {
  const opts: Intl.DateTimeFormatOptions = {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    ...(includeTime ? { hour: '2-digit', minute: '2-digit', hour12: false } : {}),
    timeZone: tz,
  }
  const parts = new Intl.DateTimeFormat('en-GB', opts).formatToParts(date)
  let out = ''
  let afterWeekday = false
  for (const p of parts) {
    if (p.type === 'weekday') {
      out += p.value
      afterWeekday = true
    } else if (afterWeekday && p.type === 'literal') {
      out += ' ' // replace ", " with " "
      afterWeekday = false
    } else {
      out += p.value
      afterWeekday = false
    }
  }
  return out
}

export function formatWhen(event: Event, viewerTz?: string): string {
  const { dateTime, startTz } = event
  const browserTz = viewerTz ?? getBrowserTz()

  // Missing date entirely
  if (!dateTime) return 'time unknown'

  // Date-only: no T in the string — show "all day" label
  if (!dateTime.includes('T')) {
    const [y, m, d] = dateTime.split('-').map(Number)
    if (!y || !m || !d) return 'time unknown'
    const midday = new Date(Date.UTC(y, m - 1, d, 12, 0, 0))
    return `${fmtParts(midday, 'UTC', false)} (all day)`
  }

  const date = new Date(dateTime)
  if (isNaN(date.getTime())) return 'time unknown'

  const tz = startTz || undefined
  const tzLabel = startTz || 'local time'

  let result = `${fmtParts(date, tz, true)} (${tzLabel})`

  // Show browser time only when event tz differs from browser tz
  if (startTz && startTz !== browserTz) {
    const browserTime = new Intl.DateTimeFormat('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: browserTz,
    }).format(date)
    result += ` · your time: ${browserTime} (${browserTz})`
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
  onDecide?: (id: string, decision: 'accepted' | 'rejected' | 'queued') => Promise<void>
}

export function EventCard({ event, variant, onDecide }: EventCardProps) {
  const [deciding, setDeciding] = useState<'accepted' | 'rejected' | null>(
    null,
  )
  const [leaving, setLeaving] = useState(false)
  const [error, setError] = useState('')

  // 5-second inline undo after accept/reject in queue variant
  const [undoDecision, setUndoDecision] = useState<'accepted' | 'rejected' | null>(null)
  const [undoTimer, setUndoTimer] = useState<ReturnType<typeof setTimeout> | null>(null)

  // Clean up timer on unmount
  useEffect(() => {
    return () => { if (undoTimer) clearTimeout(undoTimer) }
  }, [undoTimer])

  async function handleDecide(decision: 'accepted' | 'rejected') {
    setDeciding(decision)
    setError('')
    try {
      await onDecide?.(event.id, decision)
      if (variant === 'queue') {
        // Show undo for 5 seconds before removing the card
        setUndoDecision(decision)
        setDeciding(null)
        const timer = setTimeout(() => {
          setLeaving(true)
        }, 5000)
        setUndoTimer(timer)
      }
    } catch {
      setError("Couldn't save your decision. Try again.")
      setDeciding(null)
    }
  }

  async function handleUndo() {
    if (undoTimer) clearTimeout(undoTimer)
    setUndoTimer(null)
    setUndoDecision(null)
    setError('')
    try {
      await onDecide?.(event.id, 'queued')
    } catch {
      setError("Couldn't undo. Try again.")
    }
  }

  const fields = (
    <>
      <p>
        <span className="font-semibold tabular-nums">Score {event.score}%</span>
        {event.band && <span className="text-muted-foreground"> · {event.band}</span>}
      </p>
      <p>
        <span className="font-medium text-muted-foreground">When: </span>
        <span data-testid="event-datetime">
          {formatWhen(event)}
        </span>
      </p>
      <p>
        <span className="font-medium text-muted-foreground">Where: </span>
        {formatWhere(event)}
      </p>
      <p>
        <span className="font-medium text-muted-foreground">Link: </span>
        <a
          href={event.link}
          target="_blank"
          rel="noopener noreferrer"
          className="underline break-all text-primary decoration-primary/40 underline-offset-2 hover:decoration-primary"
        >
          {event.link}
        </a>
      </p>
    </>
  )

  if (variant === 'queue') {
    return (
      <Card data-testid={`event-card-${event.id}`} className={leaving ? 'animate-out fade-out-0 slide-out-to-right-2 fill-mode-forwards duration-200' : undefined}>
        <CardHeader>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {event.scoreReason}
          </p>
          <CardTitle>
            <a
              href={event.link}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline underline-offset-2"
            >
              {event.title}
            </a>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-1.5 text-sm">
          {fields}
          {undoDecision ? (
            <div className="flex items-center gap-2 pt-3" data-testid="undo-bar">
              <span className="text-sm">
                {undoDecision === 'accepted' ? 'Accepted.' : 'Rejected.'}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={handleUndo}
              >
                Undo
              </Button>
            </div>
          ) : onDecide && (
            <div className="flex gap-2 pt-3">
              <Button
                size="sm"
                disabled={deciding !== null}
                onClick={() => handleDecide('accepted')}
              >
                {deciding === 'accepted' ? 'Accepting…' : 'Accept'}
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
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
    )
  }

  // all variant
  return (
    <Card data-testid={`event-card-${event.id}`}>
      <CardHeader>
        <div className="flex flex-wrap-reverse items-start justify-between gap-2">
          <CardTitle>
            <a
              href={event.link}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline underline-offset-2"
            >
              {event.title}
            </a>
          </CardTitle>
          <Badge variant={badgeVariant[event.status]}>
            {badgeText(event)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-1.5 text-sm">
        <p className="text-muted-foreground">
          {event.scoreReason}
        </p>
        {fields}
        {event.status === 'accepted' && onDecide && (
          <div className="pt-2">
            <ConfirmAction
              label="Remove from calendar"
              prompt="Remove this event from your calendar?"
              confirmLabel="Remove"
              confirmingLabel="Removing…"
              errorText="Couldn't remove it. Try again."
              onConfirm={() => onDecide(event.id, 'queued')}
            />
          </div>
        )}
        {event.status === 'rejected' && onDecide && (
          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                try {
                  await onDecide(event.id, 'queued')
                } catch {
                  // handled by parent
                }
              }}
            >
              Put back to review
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
