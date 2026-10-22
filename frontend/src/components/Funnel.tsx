import { cn } from 'cn'

/** One definition shared with the chronology and the backend: found = judged + notJudged,
 *  judged = accepted + queued + rejected; filtered_non_event are pages, not events. */
export function funnelNumbers(counts: Record<string, number>) {
  const c = (k: string) => counts[k] ?? 0
  const pages = c('results_fetched')
  // pages_with_events arrived with #112; a run from before it has no "no events" part
  const withEvents = counts.pages_with_events ?? pages
  const [accepted, queued, rejected] = [c('accepted'), c('queued'), c('rejected')]
  const [noDate, past, duplicate, date] = [c('filtered_no_date'), c('filtered_past'), c('filtered_duplicate'), c('filtered_date')]
  const [place, incomplete, capped, judgeErrors] = [c('filtered_place'), c('filtered_incomplete'), c('events_capped'), c('judge_errors')]
  return {
    pages,
    pagesWithEvents: withEvents,
    pagesNoEvents: pages - withEvents,
    found: c('events_extracted'),
    nonEvent: c('filtered_non_event'),
    judged: accepted + queued + rejected,
    accepted,
    queued,
    rejected,
    rejectedDatePlace: c('rejected_date_place'),
    rejectedOffTopic: c('rejected_off_topic'),
    rejectedOther: c('rejected_other'),
    noDate,
    past,
    duplicate,
    date,
    place,
    incomplete,
    capped,
    judgeErrors,
    notJudged: noDate + past + duplicate + date + place + incomplete + capped + judgeErrors,
  }
}

const MAIN = { fill: 'var(--foreground)', fontWeight: 500 }
const SUB = { fill: 'var(--muted-foreground)' }
const RING = { fill: 'var(--ring)', opacity: 0.45 }
const GREY = { fill: 'var(--muted-foreground)', opacity: 0.3 }

// One scale for the whole drawing (px per event), so a count is the same thickness everywhere:
// bar "N found" → ribbon "J judged" into bar "J judged" + grey "K not judged" ending short → verdict ribbons to end bars.
const BAR = 16
const TOP = 10
const HEIGHT = 140
const X_FOUND = 10
const X_JUDGED = 400
const X_SHORT = 200
const X_END = 580
const LINE = 11

/** A ribbon from the span [yL0, yL1] at x0 to [yR0, yR1] at x1, curved like the approved drawing. */
function ribbon(x0: number, yL0: number, yL1: number, x1: number, yR0: number, yR1: number) {
  const cx = (x0 + x1) / 2
  return `M${x0} ${yL0} C${cx} ${yL0} ${cx} ${yR0} ${x1} ${yR0} L${x1} ${yR1} C${cx} ${yR1} ${cx} ${yL1} ${x0} ${yL1} Z`
}

export function Funnel({ counts, className }: { counts: Record<string, number>; className?: string }) {
  const n = funnelNumbers(counts)
  if (n.found === 0) return null
  const nz = (count: number, word: string) => (count > 0 ? [`${count} ${word}`] : [])
  const s = HEIGHT / n.found
  const judgedH = n.judged * s

  // every label sits under (or inside) the one element it belongs to, its detail lines beneath it
  const judgedLabelY = TOP + judgedH + 15
  const notJudgedLines = [
    `${n.notJudged} not judged`,
    `${n.noDate} no date · ${n.past} past · ${n.duplicate} dup`,
    ...nz(n.date, 'date'), ...nz(n.place, 'place'), ...nz(n.incomplete, 'incomplete'), ...nz(n.capped, 'capped'), ...nz(n.judgeErrors, 'errors'),
  ].map((text, i) => ({ text, y: TOP + HEIGHT + 14 + i * LINE }))
  const height = Math.max(185, (n.notJudged > 0 ? notJudgedLines[notJudgedLines.length - 1].y : 0) + 8, judgedLabelY + 8)

  // verdict ribbons leave the judged bar in order; the end bars sit 6 px apart
  let yL = TOP
  let yR = 6
  let lastY = -Infinity
  const verdicts = [
    { count: n.accepted, fill: 'var(--zone-calendar)', opacity: 0.6, label: `${n.accepted} in`, subs: [] as string[] },
    { count: n.queued, fill: 'var(--zone-decide)', opacity: 0.7, label: `${n.queued} review`, subs: [] },
    {
      count: n.rejected, fill: 'var(--zone-rejected)', opacity: 0.35, label: `${n.rejected} out`,
      subs: [`${n.rejectedDatePlace} date/place`, `${n.rejectedOffTopic} topic`, ...nz(n.rejectedOther, 'other')],
    },
  ].filter((r) => r.count > 0).map((r) => {
    const h = r.count * s
    const d = ribbon(X_JUDGED + BAR, yL, yL + h, X_END, yR, yR + h)
    let y = Math.max(yR + h / 2 + 3, lastY + 11)
    const lines = [{ y, text: r.label, main: true }]
    for (const sub of r.subs) lines.push({ y: (y += 11), text: sub, main: false })
    lastY = y
    const part = { ...r, h, yR0: yR, d, lines }
    yL += h
    yR += h + 6
    return part
  })

  return (
    <svg
      data-testid="funnel"
      role="img"
      aria-label={`Funnel: ${n.found} events found, ${n.judged} judged: ${n.accepted} in calendar, ${n.queued} to review, ${n.rejected} out`}
      viewBox={`0 0 700 ${height}`}
      className={cn('w-full font-mono text-[10px]', className)}
    >
      <title>Where the {n.found} events went</title>
      <g data-testid="funnel-stage-1">
        <rect x={X_FOUND} y={TOP} width={BAR} height={HEIGHT} fill="var(--border)" />
        <text x={X_FOUND} y={165} style={MAIN}>{n.found} found</text>
        <text x={X_FOUND} y={177} style={SUB}>
          {'pages_with_events' in counts ? `from ${n.pagesWithEvents} of ${n.pages} pages read` : `on ${n.pages} pages read`}
        </text>
        {n.judged > 0 && <path d={ribbon(X_FOUND + BAR, TOP, TOP + judgedH, X_JUDGED, TOP, TOP + judgedH)} {...RING} />}
        {n.notJudged > 0 && (
          <path d={ribbon(X_FOUND + BAR, TOP + judgedH, TOP + HEIGHT, X_SHORT, TOP + judgedH, TOP + HEIGHT)} {...GREY} />
        )}
        {n.judged > 0 && <text x={X_FOUND + BAR + 8} y={TOP + judgedH / 2 + 3} style={MAIN}>{n.judged} judged</text>}
        {n.notJudged > 0 && notJudgedLines.map((l, i) => (
          <text key={l.text} x={X_SHORT} y={l.y} style={i === 0 ? MAIN : SUB}>{l.text}</text>
        ))}
      </g>
      <g data-testid="funnel-stage-2">
        <rect x={X_JUDGED} y={TOP} width={BAR} height={judgedH} fill="var(--border)" />
        {n.judged > 0 && <text x={X_JUDGED} y={judgedLabelY} style={MAIN}>{n.judged} judged</text>}
        {verdicts.map((p) => (
          <g key={p.label}>
            <path d={p.d} fill={p.fill} opacity={p.opacity} />
            <rect x={X_END} y={p.yR0} width={6} height={p.h} fill={p.fill} />
            {p.lines.map((l) => (
              <text key={l.text} x={X_END + 12} y={l.y} style={l.main ? MAIN : SUB}>{l.text}</text>
            ))}
          </g>
        ))}
      </g>
    </svg>
  )
}
