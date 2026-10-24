import { cn } from 'cn'

/** One definition shared with the chronology and the backend: found = judged + notJudged,
 *  judged = accepted + queued + rejected; filtered_non_event are pages, not events. */
export function funnelNumbers(counts: Record<string, number>) {
  const c = (k: string) => counts[k] ?? 0
  const pages = c('results_fetched')
  // pages_with_events arrived with #112; a run from before it has no "no events" part
  const withEvents = counts.pages_with_events ?? pages
  const [accepted, queued, rejected] = [c('accepted'), c('queued'), c('rejected')]
  const [noDate, noTime, past, duplicate, date] = [c('filtered_no_date'), c('filtered_no_time'), c('filtered_past'), c('filtered_duplicate'), c('filtered_date')]
  const [place, incomplete, capped, judgeErrors] = [c('filtered_place'), c('filtered_incomplete'), c('events_capped'), c('judge_errors')]
  return {
    pages,
    pagesKnown: c('results_known'),
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
    noTime,
    past,
    duplicate,
    date,
    place,
    incomplete,
    capped,
    judgeErrors,
    notJudged: noDate + noTime + past + duplicate + date + place + incomplete + capped + judgeErrors,
  }
}

const MAIN = { fill: 'var(--foreground)', fontWeight: 500 }
const SUB = { fill: 'var(--muted-foreground)' }

// Sankey with the numbers of _docs/ui/05-funnel-sankey.svg: 120 px for the events found (5 px per event for 24),
// columns at x 10 / 260 / 520, nodes stacked GAP apart and centred, labels beside their own node. The viewBox
// only grows for labels, never by scaling. shortcut: the drawing's column gaps are 28 and 16, not one value;
// 16 reproduces its column 3 and its not-judged node, upgrade if the owner wants column 2 wider apart.
export const GAP = 16
export const TOP = 40
export const HEIGHT = 120
export const X = [10, 260, 520]
export const WIDTH = 640
const BAR = [14, 14, 6]
const LINE = 11
const CHARS = [0, 40, 26] // a breakdown line wraps here per column (6 px per character)

// Hardcoded colours: same in light and dark, per mockup 06-progress-and-colour.html
type Node = { key: string; count: number; fill: string; ribbonFill?: string; ribbonOpacity?: number; label: string; subs: string[] }
type Placed = Node & { x: number; w: number; y: number; h: number; lines: { y: number; text: string; main: boolean }[] }

/** A ribbon from the span [yL0, yL1] at x0 to [yR0, yR1] at x1, curved like the approved drawing. */
function ribbon(x0: number, yL0: number, yL1: number, x1: number, yR0: number, yR1: number) {
  const cx = (x0 + x1) / 2
  return `M${x0} ${yL0} C${cx} ${yL0} ${cx} ${yR0} ${x1} ${yR0} L${x1} ${yR1} C${cx} ${yR1} ${cx} ${yL1} ${x0} ${yL1} Z`
}

/** "5 no date · 9 duplicate · …" cut into lines no wider than the gap between two columns. */
function wrap(parts: string[], chars: number): string[] {
  const lines: string[] = []
  for (const p of parts) {
    const last = lines[lines.length - 1]
    if (last !== undefined && `${last} · ${p}`.length <= chars) lines[lines.length - 1] = `${last} · ${p}`
    else lines.push(p)
  }
  return lines
}

/** Nodes with a count, stacked GAP apart and centred on `centre`; labels to the right, pushed down so none overlap. */
function stack(nodes: Node[], col: number, s: number, centre: number): Placed[] {
  const drawn = nodes.filter((n) => n.count > 0)
  const total = drawn.reduce((a, n) => a + n.count * s, 0) + GAP * (drawn.length - 1)
  let y = centre - total / 2
  let lastY = -Infinity
  return drawn.map((n) => {
    const h = n.count * s
    const texts = [n.label, ...n.subs]
    // the label block is centred on its node, or starts one line under the previous label when the node is thinner
    const first = Math.max(y + h / 2 + 3 - (LINE * (texts.length - 1)) / 2, lastY + LINE)
    const lines = texts.map((text, i) => ({ text, main: i === 0, y: first + i * LINE }))
    lastY = lines[lines.length - 1].y
    const placed = { ...n, x: X[col], w: BAR[col], y, h, lines }
    y += h + GAP
    return placed
  })
}

export function Funnel({ counts, countsVersion = 3, className }: { counts: Record<string, number>; countsVersion?: number; className?: string }) {
  const n = funnelNumbers(counts)
  if (n.found === 0) return null
  const nz = (count: number, word: string) => (count > 0 ? [`${count} ${word}`] : [])
  const s = HEIGHT / n.found
  const centre = TOP + HEIGHT / 2
  // an older run stored fewer counters: the events they would have counted are drawn, not dropped or shown as 0
  const notAccounted = countsVersion < 3 ? Math.max(0, n.found - n.judged - n.notJudged) : 0

  const found: Placed = {
    key: 'found', count: n.found, fill: '#5b6472', label: `${n.found} found`, x: X[0], w: BAR[0], y: TOP, h: HEIGHT,
    subs: [], lines: [
      { y: TOP + HEIGHT + 16, text: `${n.found} found`, main: true },
      { y: TOP + HEIGHT + 16 + LINE, main: false, text: 'pages_with_events' in counts ? `from ${n.pagesWithEvents} of ${n.pages - n.pagesKnown} pages read` : `on ${n.pages - n.pagesKnown} pages read` },
    ],
  }
  const col2 = stack([
    { key: 'judged', count: n.judged, fill: '#2563eb', ribbonFill: '#3b82f6', ribbonOpacity: 0.55, label: `${n.judged} judged`, subs: [] },
    {
      key: 'notJudged', count: n.notJudged, fill: '#64748b', ribbonFill: '#94a3b8', ribbonOpacity: 0.4, label: `${n.notJudged} not judged`,
      subs: wrap([
        ...nz(n.noDate, 'no date'), ...nz(n.noTime, 'no time'), ...nz(n.past, 'past'), ...nz(n.duplicate, 'duplicate'), ...nz(n.date, 'date'),
        ...nz(n.place, 'place'), ...nz(n.incomplete, 'incomplete'), ...nz(n.capped, 'capped'), ...nz(n.judgeErrors, 'errors'),
      ], CHARS[1]),
    },
    { key: 'notAccounted', count: notAccounted, fill: '#64748b', ribbonFill: '#94a3b8', ribbonOpacity: 0.4, label: `${notAccounted} not accounted`, subs: ['run before 22 Oct, counters added later'] },
  ], 1, s, centre)
  const judged = col2.find((p) => p.key === 'judged')
  const col3 = stack([
    { key: 'accepted', count: n.accepted, fill: '#059669', ribbonFill: '#10b981', ribbonOpacity: 0.75, label: `${n.accepted} in calendar`, subs: [] },
    { key: 'queued', count: n.queued, fill: '#d97706', ribbonFill: '#f59e0b', ribbonOpacity: 0.85, label: `${n.queued} to review`, subs: [] },
    {
      key: 'rejected', count: n.rejected, fill: '#dc2626', ribbonFill: '#ef4444', ribbonOpacity: 0.6, label: `${n.rejected} out`,
      subs: wrap([...nz(n.rejectedDatePlace, 'date or place'), ...nz(n.rejectedOffTopic, 'topic'), ...nz(n.rejectedOther, 'other')], CHARS[2]),
    },
  ], 2, s, judged ? judged.y + judged.h / 2 : centre)

  // ribbons leave their source node top to bottom in the order of the target column
  const flows = (from: Placed, to: Placed[]) => {
    let y = from.y
    return to.map((t) => {
      const d = ribbon(from.x + from.w, y, y + t.h, t.x, t.y, t.y + t.h)
      y += t.h
      return { key: t.key, d, style: { fill: t.ribbonFill, opacity: t.ribbonOpacity } }
    })
  }
  const ribbons = [...flows(found, col2), ...(judged ? flows(judged, col3) : [])]
  const all = [found, ...col2, ...col3]
  const labelX = (p: Placed) => (p.key === 'found' ? p.x : p.x + p.w + 6)
  // the drawing's frame; it only grows to keep a long label line inside, never shrinking the nodes' scale
  const height = Math.max(...all.flatMap((p) => [p.y + p.h, ...p.lines.map((l) => l.y)])) + 6
  const width = Math.max(WIDTH, ...all.flatMap((p) => p.lines.map((l) => labelX(p) + l.text.length * 6 + 6)))

  return (
    <svg
      data-testid="funnel"
      role="img"
      aria-label={`Funnel: ${n.found} events found, ${n.judged} judged: ${n.accepted} in calendar, ${n.queued} to review, ${n.rejected} out`}
      viewBox={`0 0 ${width} ${height}`}
      className={cn('w-full font-mono text-[10px]', className)}
    >
      <title>Where the {n.found} events went</title>
      {ribbons.map((r) => <path key={r.key} data-testid={`funnel-ribbon-${r.key}`} d={r.d} {...r.style} />)}
      {all.map((p) => (
        <g key={p.key}>
          <rect data-testid={`funnel-node-${p.key}`} x={p.x} y={p.y} width={p.w} height={p.h} fill={p.fill} />
          {p.lines.map((l) => (
            <text key={l.text} x={labelX(p)} y={l.y} style={l.main ? MAIN : SUB}>{l.text}</text>
          ))}
        </g>
      ))}
    </svg>
  )
}
