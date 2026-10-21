import { useEffect, useState } from 'react'
import { listEvents, decideEvent } from '@/services/api'
import type { Event } from '@/services/api'
import { EventCard } from '@/components/EventCard'
import { Button } from '@/components/ui/button'

export function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)

  async function fetchEvents() {
    setLoading(true)
    setFetchError(false)
    try {
      const all = await listEvents()
      const filtered = all
        .filter((e) => e.status !== 'new')
        .sort(
          (a, b) =>
            new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime(),
        )
      setEvents(filtered)
    } catch {
      setFetchError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents()
  }, [])

  async function handleDecide(
    id: string,
    decision: 'accepted' | 'rejected' | 'queued',
  ) {
    const updated = await decideEvent(id, decision)
    setEvents((prev) => prev.map((e) => (e.id === id ? updated : e)))
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="font-heading text-2xl font-bold tracking-tight">All events</h2>
      {loading && (
        <p className="text-muted-foreground">Loading…</p>
      )}
      {fetchError && (
        <>
          <p className="text-destructive">
            Couldn&apos;t load your events. Try again.
          </p>
          <Button variant="outline" onClick={fetchEvents}>
            Try again
          </Button>
        </>
      )}
      {!loading && !fetchError && events.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-muted/40 px-6 py-10 text-center">
          <p className="font-heading text-lg font-semibold">No events yet.</p>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-2 leading-relaxed">
            Write what you&apos;re looking for on the Home tab, then press
            Search now.
          </p>
        </div>
      )}
      {!loading &&
        !fetchError &&
        events.map((event) => (
          <EventCard
            key={event.id}
            event={event}
            variant="all"
            onDecide={handleDecide}
          />
        ))}
    </div>
  )
}
