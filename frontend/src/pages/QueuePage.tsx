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
    onQueueChange?.()
    setTimeout(() => setQueuedEvents((prev) => prev.filter((e) => e.id !== id)), 200)
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="font-heading text-2xl font-bold tracking-tight">To review</h2>
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
        <div className="rounded-xl border border-dashed border-border bg-muted/40 px-6 py-10 text-center">
          <p className="font-heading text-lg font-semibold">Nothing to decide right now.</p>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-2 leading-relaxed">
            Events that clearly match go straight to your calendar. Events that
            clearly don&apos;t are rejected. When the app isn&apos;t sure, they
            appear here.
          </p>
        </div>
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
