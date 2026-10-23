import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Funnel, GAP, HEIGHT, TOP, X, funnelNumbers } from './Funnel'

const counts = {
  results_fetched: 31, pages_with_events: 8, events_extracted: 12,
  filtered_no_date: 1, filtered_past: 2, filtered_place: 1, filtered_duplicate: 1, filtered_non_event: 2,
  events_judged: 7, accepted: 2, queued: 3, rejected: 2, rejected_date_place: 1, rejected_off_topic: 1, rejected_other: 0,
}

const noDate = { results_fetched: 4, pages_with_events: 3, events_extracted: 5, filtered_no_date: 2, accepted: 1, queued: 1, rejected: 1 }

// a run stored before the reject bands and filtered_no_date: 24 found, 8 judged, 4 past, 12 nowhere
const v1 = { results_fetched: 20, events_extracted: 24, filtered_past: 4, accepted: 2, queued: 1, rejected: 5 }

type Edge = { x0: number; yL0: number; yL1: number; x1: number; yR0: number; yR1: number }

/** The ribbon's two vertical edges, read back from its path: M x0 yL0 C … x1 yR0 L x1 yR1 C … x0 yL1 Z */
function edges(path: Element): Edge {
  const m = path.getAttribute('d')!.match(/^M(\S+) (\S+) C\S+ \S+ \S+ \S+ (\S+) (\S+) L\S+ (\S+) C\S+ \S+ \S+ \S+ \S+ (\S+) Z$/)!
  const [x0, yL0, x1, yR0, yR1, yL1] = m.slice(1).map(Number)
  return { x0, yL0, yL1, x1, yR0, yR1 }
}

type Box = { key: string; x: number; w: number; y: number; h: number }

function nodes(container: HTMLElement): Box[] {
  return Array.from(container.querySelectorAll('rect'), (r) => ({
    key: r.getAttribute('data-testid')!.replace('funnel-node-', ''),
    x: Number(r.getAttribute('x')), w: Number(r.getAttribute('width')), y: Number(r.getAttribute('y')), h: Number(r.getAttribute('height')),
  }))
}

function ribbons(container: HTMLElement) {
  return Array.from(container.querySelectorAll('path'), (p) => ({ key: p.getAttribute('data-testid')!.replace('funnel-ribbon-', ''), ...edges(p) }))
}

/** Text boxes at 6 px per character, 8 px tall (10 px mono). */
function labels(container: HTMLElement) {
  return Array.from(container.querySelectorAll('text'), (t) => {
    const x = Number(t.getAttribute('x')), y = Number(t.getAttribute('y'))
    return { text: t.textContent!, x0: x, x1: x + t.textContent!.length * 6, y0: y - 8, y1: y }
  })
}

/** The issue's structure: one scale, constant-thickness ribbons, columns stacked GAP apart and centred, zero nodes absent. */
function expectStructure(container: HTMLElement, c: Record<string, number>, extra: Record<string, number> = {}) {
  const n = { ...funnelNumbers(c), ...extra }
  const s = HEIGHT / n.found
  const ns = nodes(container)
  const by = Object.fromEntries(ns.map((b) => [b.key, b]))
  const expected: Record<string, number> = {
    found: n.found, judged: n.judged, notJudged: n.notJudged, notAccounted: extra.notAccounted ?? 0,
    accepted: n.accepted, queued: n.queued, rejected: n.rejected,
  }
  // every node is its count × scale tall; a count of 0 has no node
  expect(ns.map((b) => b.key).sort()).toEqual(Object.keys(expected).filter((k) => expected[k] > 0).sort())
  for (const b of ns) expect(b.h, b.key).toBeCloseTo(expected[b.key] * s, 6)
  // every ribbon is as thick as its target node at both ends and spans the two columns
  const rs = ribbons(container)
  expect(rs.map((r) => r.key).sort()).toEqual(ns.map((b) => b.key).filter((k) => k !== 'found').sort())
  for (const r of rs) {
    const t = by[r.key]
    expect(r.yL1 - r.yL0, r.key).toBeCloseTo(t.h, 6)
    expect([r.yR0, r.yR1], r.key).toEqual([t.y, t.y + t.h])
    expect(r.x1).toBe(t.x)
    const from = ['judged', 'notJudged', 'notAccounted'].includes(r.key) ? by.found : by.judged
    expect(r.x0).toBe(from.x + from.w)
    expect(r.yL0).toBeGreaterThanOrEqual(from.y)
    expect(r.yL1).toBeLessThanOrEqual(from.y + from.h + 1e-6)
  }
  // columns at the drawing's x; nodes GAP apart; column 2 centred on found, column 3 on judged
  expect(by.found).toMatchObject({ x: X[0], y: TOP, h: HEIGHT })
  const col = (x: number) => ns.filter((b) => b.x === x).sort((a, b) => a.y - b.y)
  const centred = (c: Box[], centre: number) => {
    for (let i = 1; i < c.length; i++) expect(c[i].y - (c[i - 1].y + c[i - 1].h)).toBeCloseTo(GAP, 6)
    expect((c[0].y + c[c.length - 1].y + c[c.length - 1].h) / 2).toBeCloseTo(centre, 6)
  }
  centred(col(X[1]), TOP + HEIGHT / 2)
  if (by.judged) centred(col(X[2]), by.judged.y + by.judged.h / 2)
}

function expectLabelsClear(container: HTMLElement) {
  const boxes = labels(container)
  for (const a of boxes) for (const b of boxes) {
    if (a === b) continue
    const overlap = a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1
    expect(overlap, `${a.text} / ${b.text}`).toBe(false)
  }
  const [width, height] = container.querySelector('svg')!.getAttribute('viewBox')!.split(' ').slice(2).map(Number)
  for (const b of [...boxes, ...nodes(container).map((n) => ({ text: n.key, x1: n.x + n.w, y0: n.y, y1: n.y + n.h }))]) {
    expect(b.y0, b.text).toBeGreaterThanOrEqual(0)
    expect(b.y1, b.text).toBeLessThanOrEqual(height)
    expect(b.x1, b.text).toBeLessThanOrEqual(width)
  }
}

describe('funnelNumbers', () => {
  it('partitions pages, found and rejected', () => {
    const n = funnelNumbers(counts)
    expect(n.notJudged + n.judged).toBe(n.found)
    expect(n.pagesWithEvents + n.pagesNoEvents).toBe(n.pages)
    expect(n.rejectedDatePlace + n.rejectedOffTopic + n.rejectedOther).toBe(n.rejected)
    expect(n.nonEvent).toBe(2)
  })

  it('treats missing counts as 0 and pagesWithEvents as every page', () => {
    const n = funnelNumbers({ events_extracted: 3, accepted: 3, results_fetched: 5 })
    expect([n.rejected, n.rejectedDatePlace, n.notJudged, n.pagesNoEvents, n.pagesKnown]).toEqual([0, 0, 0, 0, 0])
    expect(n.pagesWithEvents).toBe(5)
  })
})

// The owner's drawing, _docs/ui/05-funnel-sankey.svg, read as numbers: 24 found, 8 judged, 16 not judged, 2 / 1 / 5.
const DRAWING = {
  counts: { results_fetched: 20, pages_with_events: 8, events_extracted: 24, filtered_no_date: 5, filtered_duplicate: 9, judge_errors: 2, accepted: 2, queued: 1, rejected: 5, rejected_date_place: 4, rejected_off_topic: 1 },
  viewBox: [640, 200],
  rects: {
    found: { x: 10, y: 40, w: 14, h: 120 },
    judged: { x: 260, y: 20, w: 14, h: 40 },
    notJudged: { x: 260, y: 88, w: 14, h: 80 },
    accepted: { x: 520, y: 8, w: 6, h: 10 },
    queued: { x: 520, y: 34, w: 6, h: 5 },
    rejected: { x: 520, y: 55, w: 6, h: 25 },
  },
  texts: {
    '24 found': [10, 176], 'from 8 of 20 pages read': [10, 187],
    '8 judged': [280, 33], '16 not judged': [280, 124], '5 no date · 9 duplicate · 2 errors': [280, 135],
    '2 in calendar': [532, 16], '1 to review': [532, 40], '5 out': [532, 66], '4 date or place · 1 topic': [532, 77],
  },
  ribbons: { judged: ['var(--border)', '0.9'], notJudged: ['var(--muted-foreground)', '0.3'], accepted: ['var(--zone-calendar)', '0.6'], queued: ['var(--zone-decide)', '0.7'], rejected: ['var(--zone-rejected)', '0.4'] },
}
// Where the hand-made drawing departs from its own rule (nodes GAP apart, centred on their source): its column-2 gap is
// 28 and its judged node sits 12 px higher than a centred stack puts it, which moves column 3 and "8 judged" with it.
const HAND_PLACED = { judged: 12, accepted: 8, queued: 8, rejected: 8, '8 judged': 22, '2 in calendar': 8, '1 to review': 8, '5 out': 8, '4 date or place · 1 topic': 8 }

describe('Funnel', () => {
  it("matches the owner's drawing numerically: frame, scale, columns, widths, labels, fills", () => {
    const { container } = render(<Funnel counts={DRAWING.counts} />)
    const [width, height] = container.querySelector('svg')!.getAttribute('viewBox')!.split(' ').slice(2).map(Number)
    // the drawing's own "4 date or place · 1 topic" runs to x 682, past its 640 frame: the frame grows just enough for it
    expect(width).toBeGreaterThanOrEqual(DRAWING.viewBox[0])
    expect(width).toBeLessThanOrEqual(690)
    expect(Math.abs(height - DRAWING.viewBox[1])).toBeLessThanOrEqual(7) // the frame ends 6 px under the last label
    const within = (got: number, want: number, slack: number, what: string) => expect(Math.abs(got - want), what).toBeLessThanOrEqual(slack)
    const by = Object.fromEntries(nodes(container).map((b) => [b.key, b]))
    for (const [key, r] of Object.entries(DRAWING.rects)) {
      expect(by[key], key).toBeDefined()
      within(by[key].x, r.x, 0, `${key} x`)
      within(by[key].w, r.w, 0, `${key} width`)
      within(by[key].h, r.h, 2, `${key} height`)
      within(by[key].y, r.y, 2 + (HAND_PLACED[key as keyof typeof HAND_PLACED] ?? 0), `${key} y`)
    }
    for (const [text, [x, y]] of Object.entries(DRAWING.texts)) {
      const t = screen.getByText(text)
      within(Number(t.getAttribute('x')), x, 0, `${text} x`)
      within(Number(t.getAttribute('y')), y, 2 + (HAND_PLACED[text as keyof typeof HAND_PLACED] ?? 0), `${text} y`)
    }
    for (const [key, [fill, opacity]] of Object.entries(DRAWING.ribbons)) {
      const p = screen.getByTestId(`funnel-ribbon-${key}`)
      expect([p.getAttribute('fill'), p.getAttribute('opacity')], key).toEqual([fill, opacity])
    }
    // the rule itself, exactly: nodes GAP apart, column 2 centred on found, column 3 on judged
    expectStructure(container, DRAWING.counts)
  })

  it('is a Sankey at one scale: ribbons as thick as their node at both ends, columns stacked GAP apart and centred', () => {
    const { container } = render(<Funnel counts={counts} />)
    expectStructure(container, counts)
    expectLabelsClear(container)
  })

  it('keeps the structure when events lack a date', () => {
    const { container } = render(<Funnel counts={noDate} />)
    expectStructure(container, noDate)
    expectLabelsClear(container)
    expect(screen.getByText('2 no date')).toBeInTheDocument()
  })

  it('labels every node beside it: under found, right of the others', () => {
    const { container } = render(<Funnel counts={counts} />)
    for (const t of [
      '12 found', 'from 8 of 31 pages read', '7 judged', '5 not judged', '1 no date · 2 past · 1 duplicate', '1 place',
      '2 in calendar', '3 to review', '2 out', '1 date or place · 1 topic',
    ]) expect(screen.getByText(t)).toBeInTheDocument()
    expect(screen.queryByText(/other/)).not.toBeInTheDocument()
    const x = (el: Element) => Number(el.getAttribute('x'))
    const y = (el: Element) => Number(el.getAttribute('y'))
    const by = Object.fromEntries(nodes(container).map((b) => [b.key, b]))
    expect(x(screen.getByText('12 found'))).toBe(by.found.x)
    expect(y(screen.getByText('12 found'))).toBeGreaterThan(by.found.y + by.found.h)
    expect(x(screen.getByText('from 8 of 31 pages read'))).toBe(by.found.x)
    for (const [text, key] of [['7 judged', 'judged'], ['5 not judged', 'notJudged'], ['2 in calendar', 'accepted'], ['2 out', 'rejected']]) {
      expect(x(screen.getByText(text)), text).toBe(by[key].x + by[key].w + 6)
      expect(y(screen.getByText(text)), text).toBeGreaterThan(by[key].y)
      expect(y(screen.getByText(text)) - 8, text).toBeLessThan(by[key].y + by[key].h)
    }
    // the breakdown line sits right under its count line
    expect(y(screen.getByText('1 date or place · 1 topic')) - y(screen.getByText('2 out'))).toBe(11)
  })

  it('no two labels overlap and nothing is clipped, with every breakdown and thin nodes', () => {
    const many = { ...counts, filtered_date: 1, filtered_incomplete: 1, events_capped: 1, judge_errors: 1, rejected_other: 1, rejected: 3, events_extracted: 17 }
    const { container } = render(<Funnel counts={many} />)
    expectStructure(container, many)
    expectLabelsClear(container)
    const thin = { results_fetched: 9, events_extracted: 60, filtered_past: 56, accepted: 1, queued: 1, rejected: 2, rejected_date_place: 1, rejected_other: 1 }
    const { container: c2 } = render(<Funnel counts={thin} />)
    expectStructure(c2, thin)
    expectLabelsClear(c2)
  })

  it('draws a version-1 run with the events its counters missed as "not accounted"', () => {
    const { container } = render(<Funnel counts={v1} countsVersion={1} />)
    expectStructure(container, v1, { notAccounted: 12 })
    expectLabelsClear(container)
    expect(screen.getByText('12 not accounted')).toBeInTheDocument()
    expect(screen.getByText('run before 22 Oct, counters added later')).toBeInTheDocument()
    expect(screen.queryByTestId('funnel-node-notJudged')).toHaveTextContent('')
    expect(screen.getByTestId('funnel-node-notAccounted')).toBeInTheDocument()
  })

  it('never draws "not accounted" for a version-3 run', () => {
    render(<Funnel counts={v1} countsVersion={3} />)
    expect(screen.queryByText(/not accounted/)).not.toBeInTheDocument()
    expect(screen.queryByTestId('funnel-node-notAccounted')).not.toBeInTheDocument()
  })

  it('draws no node, ribbon or label for a count of 0', () => {
    const allJudged = { results_fetched: 5, events_extracted: 6, accepted: 4, rejected: 2, rejected_other: 2 }
    const { container } = render(<Funnel counts={allJudged} />)
    expectStructure(container, allJudged)
    expect(nodes(container).map((b) => b.key)).toEqual(['found', 'judged', 'accepted', 'rejected'])
    expect(container.textContent).not.toMatch(/not judged|to review|0 /)
  })

  it('never says set aside or rejected', () => {
    const { container } = render(<Funnel counts={counts} />)
    expect(container.textContent).not.toMatch(/set aside|rejected|pages: no events/)
    expect(screen.getByTestId('funnel').getAttribute('aria-label')).not.toMatch(/set aside|rejected/)
  })

  it('renders nothing with no events', () => {
    const { container } = render(<Funnel counts={{ events_extracted: 0, results_fetched: 5 }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('says "on P pages read" for a run from before pages_with_events', () => {
    const { pages_with_events: _, ...before } = counts
    const { container } = render(<Funnel counts={before} />)
    expect(screen.getByText('on 31 pages read')).toBeInTheDocument()
    expectStructure(container, before)
  })
})
