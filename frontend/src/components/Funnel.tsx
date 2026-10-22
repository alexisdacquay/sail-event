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

// the approved drawing, _docs/ui/04-funnel-three-stages.svg: bars at x=10, 200, 400 (16 wide), end bars at 580
const BAR = 16
const X = [10, 200, 400, 580]
const S1 = { y: 20, h: 100 } // pages bar
const S2 = { y: 10, h: 140 } // found bar; stages 2 and 3 share its scale

/** A ribbon from the span [yL0, yL1] at x0 to [yR0, yR1] at x1, curved like the drawing. */
function ribbon(x0: number, yL0: number, yL1: number, x1: number, yR0: number, yR1: number) {
  const cx = (x0 + x1) / 2
  return `M${x0} ${yL0} C${cx} ${yL0} ${cx} ${yR0} ${x1} ${yR0} L${x1} ${yR1} C${cx} ${yR1} ${cx} ${yL1} ${x0} ${yL1} Z`
}

export function Funnel({ counts, className }: { counts: Record<string, number>; className?: string }) {
  const n = funnelNumbers(counts)
  if (n.found === 0) return null
  const nz = (count: number, word: string) => (count > 0 ? [`${count} ${word}`] : [])
  const s = S2.h / n.found
  const judgedH = n.judged * s
  const [x1, x2, x3, x4] = X

  // stage 1: the pages bar flows into the found bar; the pages with no events taper to nothing
  const withEventsH = (n.pagesWithEvents / (n.pages || 1)) * S1.h
  const stage1 = [
    { d: ribbon(x1 + BAR, S1.y, S1.y + withEventsH, x2, S2.y, S2.y + S2.h), ...RING },
    ...(n.pagesNoEvents > 0
      ? [{ d: ribbon(x1 + BAR, S1.y + withEventsH, S1.y + S1.h, x2, S2.y + S2.h, S2.y + S2.h), ...GREY }]
      : []),
  ]

  // stage 2: judged flows straight into the judged bar; not judged ends short, under it
  const notJudgedTop = S2.y + judgedH
  const stage2 = [
    { d: ribbon(x2 + BAR, S2.y, notJudgedTop, x3, S2.y, notJudgedTop), ...RING },
    ...(n.notJudged > 0
      ? [{ d: ribbon(x2 + BAR, notJudgedTop, S2.y + S2.h, x3, Math.min(notJudgedTop + 7, S2.y + S2.h), S2.y + S2.h), ...GREY }]
      : []),
  ]
  const breakdown = [
    `${n.noDate} no date`, `${n.past} past`, `${n.duplicate} dup`,
    ...nz(n.date, 'date'), ...nz(n.place, 'place'), ...nz(n.incomplete, 'incomplete'), ...nz(n.capped, 'capped'), ...nz(n.judgeErrors, 'errors'),
  ].join(' · ')

  // stage 3: verdict ribbons to small end bars, 6 px apart, labels at the right
  let yL = S2.y
  let yR = 6
  let lastY = -Infinity
  const stage3 = [
    { count: n.accepted, fill: 'var(--zone-calendar)', opacity: 0.6, label: `${n.accepted} in`, subs: [] as string[] },
    { count: n.queued, fill: 'var(--zone-decide)', opacity: 0.7, label: `${n.queued} review`, subs: [] },
    {
      count: n.rejected, fill: 'var(--zone-rejected)', opacity: 0.35, label: `${n.rejected} out`,
      subs: [`${n.rejectedDatePlace} date/place`, `${n.rejectedOffTopic} topic`, ...nz(n.rejectedOther, 'other')],
    },
  ].filter((r) => r.count > 0).map((r) => {
    const h = r.count * s
    const part = { ...r, h, yR0: yR, d: ribbon(x3 + BAR, yL, yL + h, x4, yR, yR + h) }
    let y = Math.max(yR + h / 2 + 3, lastY + 11)
    const lines = [{ y, text: r.label, main: true }]
    for (const sub of r.subs) lines.push({ y: (y += 11), text: sub, main: false })
    lastY = y
    yL += h
    yR += h + 6
    return { ...part, lines }
  })

  return (
    <svg
      data-testid="funnel"
      role="img"
      aria-label={`Funnel: ${n.pages} pages read, ${n.found} events found, ${n.judged} judged: ${n.accepted} in calendar, ${n.queued} to review, ${n.rejected} out`}
      viewBox="0 0 640 170"
      className={cn('w-full font-mono text-[10px]', className)}
    >
      <title>Where the {n.found} events went</title>
      <g data-testid="funnel-stage-1">
        <rect x={x1} y={S1.y} width={BAR} height={S1.h} fill="var(--border)" />
        <text x={x1} y={135} style={MAIN}>{n.pages} pages read</text>
        {stage1.map((p) => <path key={p.d} d={p.d} fill={p.fill} opacity={p.opacity} />)}
        <text x={x1 + BAR + 8} y={66} style={MAIN}>{n.found} events</text>
        <text x={x1 + BAR + 8} y={78} style={SUB}>from {n.pagesWithEvents} pages</text>
        {n.pagesNoEvents > 0 && <text x={x1 + BAR + 8} y={108} style={SUB}>{n.pagesNoEvents} pages: no events</text>}
      </g>
      <g data-testid="funnel-stage-2">
        <rect x={x2} y={S2.y} width={BAR} height={S2.h} fill="var(--border)" />
        <text x={x2} y={165} style={MAIN}>{n.found} found</text>
        {stage2.map((p) => <path key={p.d} d={p.d} fill={p.fill} opacity={p.opacity} />)}
        <text x={x2 + BAR + 8} y={S2.y + judgedH / 2 + 3} style={MAIN}>{n.judged} judged</text>
        {/* shortcut: a thin not-judged band gets its text over it rather than beside; fine while the counts are small */}
        {n.notJudged > 0 && <text x={x2 + BAR + 8} y={(notJudgedTop + S2.y + S2.h) / 2 + 3} style={SUB}>{breakdown}</text>}
      </g>
      <g data-testid="funnel-stage-3">
        <rect x={x3} y={S2.y} width={BAR} height={judgedH} fill="var(--border)" />
        {stage3.map((p) => (
          <g key={p.label}>
            <path d={p.d} fill={p.fill} opacity={p.opacity} />
            <rect x={x4} y={p.yR0} width={6} height={p.h} fill={p.fill} />
            {p.lines.map((l) => (
              <text key={l.text} x={x4 + 12} y={l.y} style={l.main ? MAIN : SUB}>{l.text}</text>
            ))}
          </g>
        ))}
      </g>
    </svg>
  )
}
