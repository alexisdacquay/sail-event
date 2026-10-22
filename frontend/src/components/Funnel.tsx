import { cn } from 'cn'

/** One definition shared with the chronology and the backend (PR 110): found = accepted + queued +
 *  rejected + setAside, setAside = the seven counts below; filtered_non_event are pages, not events. */
export function funnelNumbers(counts: Record<string, number>) {
  const past = counts.filtered_past ?? 0
  const date = counts.filtered_date ?? 0
  const place = counts.filtered_place ?? 0
  const duplicate = counts.filtered_duplicate ?? 0
  const incomplete = counts.filtered_incomplete ?? 0
  const capped = counts.events_capped ?? 0
  const judgeErrors = counts.judge_errors ?? 0
  return {
    found: counts.events_extracted ?? 0,
    pages: counts.results_fetched ?? 0,
    nonEvent: counts.filtered_non_event ?? 0,
    accepted: counts.accepted ?? 0,
    queued: counts.queued ?? 0,
    rejected: counts.rejected ?? 0,
    rejectedDatePlace: counts.rejected_date_place ?? 0,
    rejectedOffTopic: counts.rejected_off_topic ?? 0,
    rejectedOther: counts.rejected_other ?? 0,
    past,
    date,
    place,
    duplicate,
    incomplete,
    capped,
    judgeErrors,
    setAside: incomplete + past + date + place + duplicate + capped + judgeErrors,
  }
}

const MAIN = { fill: 'var(--foreground)', fontWeight: 500 }
const SUB = { fill: 'var(--muted-foreground)' }

export function Funnel({ counts, className }: { counts: Record<string, number>; className?: string }) {
  const n = funnelNumbers(counts)
  if (n.found === 0) return null
  // the ribbons never overrun the bar, even when the backend's parts do not sum to found
  const s = 124 / Math.max(n.found, n.accepted + n.queued + n.rejected + n.setAside)
  const ribbons = [
    { count: n.accepted, color: 'var(--zone-calendar)', opacity: 0.55, label: `${n.accepted} in calendar`, subs: [] as string[] },
    { count: n.queued, color: 'var(--zone-decide)', opacity: 0.9, label: `${n.queued} to review`, subs: [] },
    {
      count: n.rejected, color: 'var(--zone-rejected)', opacity: 0.6, label: `${n.rejected} rejected`,
      subs: [
        `${n.rejectedDatePlace} wrong date or place`,
        `${n.rejectedOffTopic} off topic`,
        ...(n.rejectedOther > 0 ? [`${n.rejectedOther} other`] : []),
      ],
    },
    {
      count: n.setAside, color: 'var(--muted-foreground)', opacity: 0.35, label: `${n.setAside} set aside`,
      // only the non-zero parts: the full list overflows the 352 px viewBox
      subs: [[[n.past, 'past'], [n.date, 'date'], [n.place, 'place'], [n.duplicate, 'dup'],
        [n.incomplete, 'incomplete'], [n.capped, 'capped'], [n.judgeErrors, 'errors']]
        .filter(([c]) => (c as number) > 0).map(([c, w]) => `${c} ${w}`).join(' · ')],
    },
  ].filter((r) => r.count > 0)

  let yL = 10
  let yR = 6
  let lastY = -Infinity
  const parts = ribbons.map((r) => {
    const h = r.count * s
    const [yL0, yL1, yR0, yR1] = [yL, yL + h, yR, yR + h]
    yL = yL1
    yR = yR1 + 6
    const lines: { y: number; text: string; main: boolean }[] = []
    let y = Math.max(yR0 + h / 2 + 3, lastY + 11)
    lines.push({ y, text: r.label, main: true })
    for (const sub of r.subs) {
      y += 11
      lines.push({ y, text: sub, main: false })
    }
    lastY = y
    return { ...r, yL0, yL1, yR0, yR1, h, lines }
  })
  const height = Math.max(172, lastY + 10)

  return (
    <svg
      data-testid="funnel"
      role="img"
      aria-label={`Funnel of the ${n.found} events found: ${n.accepted} in calendar, ${n.queued} to review, ${n.rejected} rejected, ${n.setAside} set aside`}
      viewBox={`0 0 352 ${height}`}
      className={cn('w-[352px] max-w-full font-mono text-[10px]', className)}
    >
      <title>Where the {n.found} events went</title>
      <rect x={12} y={10} width={18} height={124} fill="var(--border)" />
      <text x={12} y={150} style={MAIN}>{n.found} found</text>
      <text x={12} y={162} style={SUB}>on {n.pages} pages read</text>
      {parts.map((p) => (
        <g key={p.label}>
          <path
            d={`M30 ${p.yL0} C140 ${p.yL0} 140 ${p.yR0} 212 ${p.yR0} L212 ${p.yR1} C140 ${p.yR1} 140 ${p.yL1} 30 ${p.yL1} Z`}
            fill={p.color}
            opacity={p.opacity}
          />
          <rect x={212} y={p.yR0} width={8} height={p.h} fill={p.color} />
          {p.lines.map((l) => (
            <text key={l.text} x={226} y={l.y} style={l.main ? MAIN : SUB}>{l.text}</text>
          ))}
        </g>
      ))}
    </svg>
  )
}
