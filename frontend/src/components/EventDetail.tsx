import { useState, type Ref } from 'react'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/ConfirmAction'
import { formatDay, formatTime, formatWhere } from '@/components/EventCard'
import type { Event } from '@/services/api'

function sourceHost(url: string): string {
  try {
    const u = new URL(url)
    return u.hostname.replace(/^www\./, '') + (u.pathname === '/' ? '' : u.pathname)
  } catch {
    return url
  }
}

export function EventDetail({
  event,
  onDecide,
  onClose,
  detailRef,
}: {
  event: Event
  onDecide: (id: string, decision: 'accepted' | 'rejected') => Promise<void>
  onClose: () => void
  detailRef?: Ref<HTMLDivElement>
}) {
  const [deciding, setDeciding] = useState<'accepted' | 'rejected' | null>(null)
  const [error, setError] = useState('')

  async function handleDecide(decision: 'accepted' | 'rejected') {
    setDeciding(decision)
    setError('')
    try {
      await onDecide(event.id, decision)
    } catch {
      setError("Couldn't save your decision. Try again.")
    } finally {
      setDeciding(null)
    }
  }

  const source = event.sourceUrl ?? event.link
  return (
    <div
      ref={detailRef}
      data-testid="event-detail"
      className="grid gap-1.5 rounded-lg border border-ring bg-accent/40 p-3 text-sm"
    >
      <p className="font-heading font-bold">{event.title}</p>
      <p className="text-muted-foreground">
        {formatDay(event)} · {formatTime(event)} · {formatWhere(event)}
      </p>

      {event.status === 'accepted' && (
        <div>
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
      {event.status === 'queued' && (
        <div className="flex gap-2">
          <Button size="sm" disabled={deciding !== null} onClick={() => handleDecide('accepted')}>
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
      {event.status === 'rejected' && (
        <div>
          <Button size="sm" disabled={deciding !== null} onClick={() => handleDecide('accepted')}>
            {deciding === 'accepted' ? 'Adding…' : 'Add to calendar'}
          </Button>
        </div>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <p className="text-muted-foreground">Score {event.score}%</p>
      <div className="h-1.5 rounded bg-card overflow-hidden" aria-hidden>
        <div className="h-full bg-zone-calendar" style={{ width: `${event.score}%` }} />
      </div>
      <p>{event.scoreReason}</p>
      <a
        href={source}
        target="_blank"
        rel="noopener noreferrer"
        className="text-muted-foreground text-xs hover:underline"
      >
        Source · {sourceHost(source)} ↗
      </a>
      <Button variant="ghost" size="sm" className="md:hidden justify-self-start" onClick={onClose}>
        Close
      </Button>
    </div>
  )
}
