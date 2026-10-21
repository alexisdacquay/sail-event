function dayKey(s: string): string {
  return s.includes('T') ? new Date(s).toLocaleDateString('en-CA') : s.slice(0, 10)
}

export function MonthCalendar({ dates, today = new Date() }: { dates: string[]; today?: Date }) {
  const has = new Set(dates.map(dayKey))
  const todayKey = today.toLocaleDateString('en-CA')
  const year = today.getFullYear()
  const month = today.getMonth()
  const first = new Date(year, month, 1)
  const offset = (first.getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const prefix = todayKey.slice(0, 8)

  return (
    <div data-testid="month-calendar">
      <p className="text-[11px] font-semibold uppercase tracking-[.08em] text-muted-foreground mb-1.5">
        {today.toLocaleDateString('en-GB', { month: 'long' })}
      </p>
      <div className="grid grid-cols-7 gap-[3px] font-mono text-[10px] text-center">
        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
          <span key={i} className="text-muted-foreground">{d}</span>
        ))}
        {Array.from({ length: offset }, (_, i) => (
          <span key={`b${i}`} data-blank />
        ))}
        {Array.from({ length: daysInMonth }, (_, i) => {
          const key = prefix + String(i + 1).padStart(2, '0')
          const isToday = key === todayKey
          return (
            <span
              key={key}
              data-has-event={has.has(key) || undefined}
              aria-current={isToday ? 'date' : undefined}
              className={`py-[3px] rounded text-muted-foreground ${
                has.has(key) ? 'bg-accent text-accent-foreground font-medium' : ''
              } ${isToday ? 'outline outline-1 outline-foreground text-foreground' : ''}`}
            >
              {i + 1}
            </span>
          )
        })}
      </div>
    </div>
  )
}
