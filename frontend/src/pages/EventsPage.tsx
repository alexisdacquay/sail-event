import { useEffect, useState } from 'react'
import { listEvents } from '@/services/api'
import type { Event } from '@/services/api'
import { EventCard } from '@/components/EventCard'

export function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])

  useEffect(() => {
    listEvents().then(setEvents)
  }, [])

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Events</h2>
      {events.length === 0 && <p>No events yet.</p>}
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  )
}
