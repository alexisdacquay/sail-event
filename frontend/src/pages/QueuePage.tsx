import { useEffect, useState } from 'react'
import { listEvents, decideEvent } from '@/services/api'
import type { Event } from '@/services/api'
import { EventCard } from '@/components/EventCard'
import { Button } from '@/components/ui/button'

type QueuePageProps = {
  onQueueChange?: () => void
}

export function QueuePage({ onQueueChange }: QueuePageProps) {
  const [queuedEvents, setQueuedEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)

  async function fetchQueue() {
    setLoading(true)
    setFetchError(false)
    try {
      const events = await listEvents('queued')
      events.sort(
        (a, b) =>
          new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime(),
      )
      setQueuedEvents(events)
    } catch {
      setFetchError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchQueue()
  }, [])

  async function handleDecide(
    id: string,
    decision: 'accepted' | 'rejected',
  ) {
    await decideEvent(id, decision)
    setQueuedEvents((prev) => prev.filter((e) => e.id !== id))
    onQueueChange?.()
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="font-heading text-2xl font-bold tracking-tight">Queue</h2>
      {loading && (
        <p className="text-muted-foreground">Loading…</p>
      )}
      {fetchError && (
        <>
          <p className="text-destructive">
            Couldn&apos;t load your queue. Try again.
          </p>
          <Button variant="outline" onClick={fetchQueue}>
            Try again
          </Button>
        </>
      )}
      {!loading && !fetchError && queuedEvents.length === 0 && (
        <>
          <p className="font-medium">Nothing to decide right now.</p>
          <p className="text-sm text-muted-foreground">
            Events that clearly match go straight to your calendar. Events that
            clearly don&apos;t are rejected. When the app isn&apos;t sure, they
            appear here.
          </p>
        </>
      )}
      {!loading &&
        !fetchError &&
        queuedEvents.map((event) => (
          <EventCard
            key={event.id}
            event={event}
            variant="queue"
            onDecide={handleDecide}
          />
        ))}
    </div>
  )
}
