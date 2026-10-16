import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Event } from '@/services/api'

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  new: 'outline',
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
  onAccept?: (id: string) => void
  onReject?: (id: string) => void
}

export function EventCard({ event, onAccept, onReject }: EventCardProps) {
  return (
    <Card data-testid={`event-card-${event.id}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-2">
          <span>{event.title}</span>
          <Badge variant={statusVariant[event.status]}>{event.status}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 text-sm">
        <p>
          <span className="font-medium">Date: </span>
          <span data-testid="event-datetime">{formatDateTime(event.dateTime)}</span>
        </p>
        <p>
          <span className="font-medium">Place: </span>
          {event.place}
        </p>
        <p>
          <span className="font-medium">Link: </span>
          <a
            href={event.link}
            target="_blank"
            rel="noopener noreferrer"
            className="underline text-primary"
          >
            {event.link}
          </a>
        </p>
        <p>
          <span className="font-medium">Score: </span>
          {event.score}
        </p>
        <p>
          <span className="font-medium">Reason: </span>
          {event.scoreReason}
        </p>
        {(onAccept || onReject) && (
          <div className="flex gap-2 pt-2">
            {onAccept && (
              <Button size="sm" onClick={() => onAccept(event.id)}>
                Accept
              </Button>
            )}
            {onReject && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => onReject(event.id)}
              >
                Reject
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
