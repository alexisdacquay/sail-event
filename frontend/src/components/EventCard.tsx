import { useState } from 'react'
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

const badgeText: Record<string, string> = {
  accepted: 'On your calendar',
  rejected: 'Rejected',
  queued: 'Waiting for you',
}

const badgeVariant: Record<string, 'default' | 'secondary' | 'destructive'> = {
  accepted: 'default',
  rejected: 'destructive',
  queued: 'secondary',
}

function formatDateTime(iso: string): string {
  const date = new Date(iso)
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
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
  const [error, setError] = useState('')

  async function handleDecide(decision: 'accepted' | 'rejected') {
    setDeciding(decision)
    setError('')
    try {
      await onDecide?.(event.id, decision)
    } catch {
      setError("Couldn't save your decision. Try again.")
      setDeciding(null)
    }
  }

  const fields = (
    <>
      <p>
        <span className="font-medium text-muted-foreground">Match: </span>
        <span className="font-semibold tabular-nums">{event.score} / 100</span>
      </p>
      <p>
        <span className="font-medium text-muted-foreground">When: </span>
        <span data-testid="event-datetime">
          {formatDateTime(event.dateTime)}
        </span>
      </p>
      <p>
        <span className="font-medium text-muted-foreground">Where: </span>
        {event.place}
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
      <Card data-testid={`event-card-${event.id}`}>
        <CardHeader>
          <p className="text-base leading-relaxed">
            <span className="font-semibold text-accent-foreground">Why: </span>
            {event.scoreReason}
          </p>
          <CardTitle>{event.title}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-1.5 text-sm">
          {fields}
          {onDecide && (
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
          <CardTitle>{event.title}</CardTitle>
          {badgeText[event.status] && (
            <Badge variant={badgeVariant[event.status]}>
              {badgeText[event.status]}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-1.5 text-sm">
        <p>
          <span className="font-semibold text-accent-foreground">Why: </span>
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
              onConfirm={() => onDecide(event.id, 'rejected')}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
