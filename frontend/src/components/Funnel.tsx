import { cn } from 'cn'

/** One definition shared with the chronology and the backend: found = judged + notJudged,
 *  judged = accepted + queued + rejected; filtered_non_event are pages, not events. */
export function funnelNumbers(counts: Record<string, number>) {
  const c = (k: string) => counts[k] ?? 0
  const pages = c('results_fetched')
  // pages_with_events arrived with #112; a run from before it has no side ribbon
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
const RING = { color: 'var(--ring)', opacity: 0.45 }
const GREY = { color: 'var(--muted-foreground)', opacity: 0.3 }

type Ribbon = { count: number; color: string; opacity: number; label: string; subs?: string[] }

/** Ribbons of one stage: curves from the bar to a square, labels to the right, 11 px per line, never overlapping. */
function layout(bar: number, ribbons: Ribbon[]) {
  const live = ribbons.filter((r) => r.count > 0)
  // the ribbons never overrun the bar, even when the backend's parts do not sum to it
  const s = 124 / (Math.max(bar, live.reduce((a, r) => a + r.count, 0)) || 1)
  let yL = 10
  let yR = 6
  let lastY = -Infinity
  const parts = live.map((r) => {
    const h = r.count * s
    const [yL0, yL1, yR0, yR1] = [yL, yL + h, yR, yR + h]
    yL = yL1
    yR = yR1 + 6
    let y = Math.max(yR0 + h / 2 + 3, lastY + 11)
    const lines = [{ y, text: r.label, main: true }]
    for (const sub of r.subs ?? []) lines.push({ y: (y += 11), text: sub, main: false })
    lastY = y
    return { ...r, yL0, yL1, yR0, yR1, h, lines }
  })
  return { parts, lastY }
}

export function Funnel({ counts, className }: { counts: Record<string, number>; className?: string }) {
  const n = funnelNumbers(counts)
  if (n.found === 0) return null
  const nz = (count: number, word: string) => (count > 0 ? [`${count} ${word}`] : [])
  const stages = [
    {
      bar: n.pages, caption: `${n.pages} pages read`,
      ribbons: [
        { count: n.pagesWithEvents, ...RING, label: `${n.found} events from ${n.pagesWithEvents} pages` },
        { count: n.pagesNoEvents, ...GREY, label: `${n.pagesNoEvents} pages: no events` },
      ],
    },
    {
      bar: n.found, caption: `${n.found} found`,
      ribbons: [
        { count: n.judged, ...RING, label: `${n.judged} judged` },
        {
          count: n.notJudged, ...GREY, label: `${n.notJudged} not judged`,
          subs: [
            `${n.noDate} no date`, `${n.past} past`, `${n.duplicate} duplicate`,
            ...nz(n.date, 'date'), ...nz(n.place, 'place'), ...nz(n.incomplete, 'incomplete'),
            ...nz(n.capped, 'capped'), ...nz(n.judgeErrors, 'errors'),
          ],
        },
      ],
    },
    {
      bar: n.judged, caption: `${n.judged} judged`,
      ribbons: [
        { count: n.accepted, color: 'var(--zone-calendar)', opacity: 0.55, label: `${n.accepted} in calendar` },
        { count: n.queued, color: 'var(--zone-decide)', opacity: 0.9, label: `${n.queued} to review` },
        {
          count: n.rejected, color: 'var(--zone-rejected)', opacity: 0.6, label: `${n.rejected} out`,
          subs: [`${n.rejectedDatePlace} date or place`, `${n.rejectedOffTopic} topic`, ...nz(n.rejectedOther, 'other')],
        },
      ],
    },
  ].map((st) => ({ ...st, ...layout(st.bar, st.ribbons) }))
  const height = Math.max(172, ...stages.map((st) => st.lastY + 10))

  return (
    <svg
      data-testid="funnel"
      role="img"
      aria-label={`Funnel: ${n.pages} pages read, ${n.found} events found, ${n.judged} judged: ${n.accepted} in calendar, ${n.queued} to review, ${n.rejected} out`}
      viewBox={`0 0 720 ${height}`}
      className={cn('w-full max-w-[720px] font-mono text-[10px]', className)}
    >
      <title>Where the {n.found} events went</title>
      {stages.map((st, i) => {
        const ox = i * 240
        return (
          <g key={st.caption} data-testid={`funnel-stage-${i + 1}`}>
            <rect x={ox} y={10} width={14} height={124} fill="var(--border)" />
            <text x={ox} y={150} style={MAIN}>{st.caption}</text>
            {st.parts.map((p) => (
              <g key={p.label}>
                <path
                  d={`M${ox + 14} ${p.yL0} C${ox + 50} ${p.yL0} ${ox + 50} ${p.yR0} ${ox + 88} ${p.yR0} L${ox + 88} ${p.yR1} C${ox + 50} ${p.yR1} ${ox + 50} ${p.yL1} ${ox + 14} ${p.yL1} Z`}
                  fill={p.color}
                  opacity={p.opacity}
                />
                <rect x={ox + 88} y={p.yR0} width={6} height={p.h} fill={p.color} />
                {p.lines.map((l) => (
                  <text key={l.text} x={ox + 100} y={l.y} style={l.main ? MAIN : SUB}>{l.text}</text>
                ))}
              </g>
            ))}
          </g>
        )
      })}
    </svg>
  )
}
