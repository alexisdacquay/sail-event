import { useEffect, useState } from 'react'
import { listEvents, decideEvent } from '@/services/api'
import type { Event } from '@/services/api'
import { EventCard } from '@/components/EventCard'

type QueuePageProps = {
  onQueueChange?: () => void
}

export function QueuePage({ onQueueChange }: QueuePageProps) {
  const [queuedEvents, setQueuedEvents] = useState<Event[]>([])

  useEffect(() => {
    listEvents('queued').then(setQueuedEvents)
  }, [])

  async function handleAccept(id: string) {
    await decideEvent(id, 'accepted')
    setQueuedEvents((prev) => prev.filter((e) => e.id !== id))
    onQueueChange?.()
  }

  async function handleReject(id: string) {
    await decideEvent(id, 'rejected')
    setQueuedEvents((prev) => prev.filter((e) => e.id !== id))
    onQueueChange?.()
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Queue</h2>
      {queuedEvents.length === 0 && <p>No events in the queue.</p>}
      {queuedEvents.map((event) => (
        <EventCard
          key={event.id}
          event={event}
          onAccept={handleAccept}
          onReject={handleReject}
        />
      ))}
    </div>
  )
}
