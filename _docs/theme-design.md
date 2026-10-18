# Theme design — Sail-event visual theme (roadmap P2)

Scope: look only. Copy, selectors, behaviour and layout order stay as `_docs/ux-design.md` defines them. Tailwind v4 tokens, the six shadcn primitives present, `tw-animate-css` (installed), Geist (installed). No new dependency.

Facts this design relies on (checked in code):

| Fact | Where |
|---|---|
| Body font is already Geist Variable via `@fontsource-variable/geist`; `--font-heading` aliases `--font-sans` | `frontend/src/index.css:9-10`, `package.json:15` |
| `CardTitle` already uses `font-heading`; changing that token restyles every card title | `components/ui/card.tsx:40` |
| Dark mode is class-based (`@custom-variant dark (&:is(.dark *))`) and nothing ever adds `.dark` | `index.css:6`, grep of `src/` |
| `tw-animate-css` is imported (`animate-in`, `animate-out`, `fade-*`, `slide-*` utilities available) | `index.css:2` |
| `lucide-react` installed, unused by the app | `package.json:19` |
| Zone fills use only `--destructive`, `--muted`, `--primary` tokens | `components/ScoreScale.tsx:55-74` |
| Tests match the score line as `getByText(/85 \/ 100/)` on one element, and the Why label as the literal `Why:` | `EventCard.test.tsx:25,36` |
| Queue tests wait for card removal with `waitFor` (default 1 s timeout) | `QueuePage.test.tsx:41,60,80` |
| e2e asserts `getByRole("heading", { name: "Sail Event" })` after sign-in | `e2e/journeys.spec.ts:22,46,108,131` |
| Current favicon is the Vite default | `frontend/public/favicon.svg` |


## 1. Direction

- Mood: **harbour at dusk** — modern, calm, a nautical hint, not a template.
- Two brand colours from the chosen mark: navy `#0F3057` (ink, primary) and ocean teal `#00A8CC` (the sail, the "on your calendar" zone, focus).
- Light mode is a pale cool paper with white cards; dark mode is deep navy, not grey.
- One display face for the wordmark, page titles and card titles; Geist for everything else. Numbers are tabular.
- Colour means one thing each: teal = accepted / good, coral = rejected, sand = undecided. Nothing else is coloured.
- The "tech" note in light mode is carried by the teal: the sail in the mark, the active tab (`bg-accent text-accent-foreground`), the `Why:` label, the focus ring and the calendar zone. Primary buttons stay navy in light mode because teal at 0.62 L gives only 3.4:1 under white text (fails 4.5:1) and teal with dark text reads weak; in dark mode the primary buttons are teal.


## 2. Colour

### Light palette (`:root`)

Contrast = WCAG 2.x ratio, computed from the oklch values (sRGB, D65). Hex is the nearest sRGB, for reference only; the CSS uses oklch.

| Variable | Value | ≈ hex | Used for | Contrast |
|---|---|---|---|---|
| `--background` | `oklch(0.985 0.004 240)` | `#F8FAFD` | page | — |
| `--foreground` | `oklch(0.22 0.04 255)` | `#0D1B2D` | text | 16.6:1 on background, 17.3:1 on card |
| `--card` | `oklch(1 0 0)` | `#FFFFFF` | cards, header | — |
| `--card-foreground` | `oklch(0.22 0.04 255)` | `#0D1B2D` | text on cards | 17.3:1 |
| `--popover` / `--popover-foreground` | same as card / card-foreground | | unused today | |
| `--primary` | `oklch(0.31 0.085 255)` | `#0D305A` | primary buttons, active tab, links | 12.7:1 on background |
| `--primary-foreground` | `oklch(0.985 0.004 240)` | `#F8FAFD` | text on primary | 12.7:1 on primary |
| `--secondary` | `oklch(0.95 0.01 240)` | `#E9F0F5` | secondary surfaces | |
| `--secondary-foreground` | `oklch(0.22 0.04 255)` | `#0D1B2D` | | 15:1 |
| `--muted` | `oklch(0.955 0.008 240)` | `#ECF1F5` | empty-state panel, hover fills | |
| `--muted-foreground` | `oklch(0.48 0.03 250)` | `#515F6E` | descriptions, field labels | 6.3:1 on background, 6.5:1 on card |
| `--accent` | `oklch(0.94 0.045 215)` | `#CAF4FE` | "On your calendar" badge, Saved. tint | |
| `--accent-foreground` | `oklch(0.40 0.09 220)` | `#005269` | text on accent, `Why:` label, Saved. | 7.4:1 on accent, 8.7:1 on card |
| `--destructive` | `oklch(0.55 0.20 25)` | `#CC272E` | Reject text, errors, Rejected badge | 5.4:1 on card, 5.2:1 on background |
| `--border` | `oklch(0.90 0.01 240)` | `#D8DFE4` | card and header borders | 1.35:1 (decorative) |
| `--input` | `oklch(0.86 0.015 240)` | — | input borders | 1.5:1 on card (field edge only; label and focus ring carry the field) |
| `--ring` | `oklch(0.60 0.12 215)` | `#0091AD` | focus ring | 3.7:1 on card, 3.6:1 on background |
| `--zone-rejected` | `oklch(0.88 0.07 25)` | `#FFC6C0` | scale zone 0 → lower | fill; text label beside it |
| `--zone-decide` | `oklch(0.93 0.02 80)` | `#EFE7D9` | scale zone lower → upper | fill; hatched with `foreground/10` |
| `--zone-calendar` | `oklch(0.62 0.13 215)` | `#0098B7` | scale zone upper → 100, sail in the mark | 3.4:1 on card |
| `--radius` | `0.75rem` | | 12 px base; `rounded-lg` = 12 px, `rounded-xl` = 16.8 px (`--radius-xl: calc(var(--radius) * 1.4)` in `index.css`); cards use `rounded-xl` | |

Thumb on the scale (light): body `--card`, border `--foreground`. Border vs zone-rejected 11.6:1, vs zone-decide 14.1:1, vs zone-calendar 5.1:1.

### Dark palette (`@media (prefers-color-scheme: dark) { :root { … } }`)

| Variable | Value | ≈ hex | Contrast |
|---|---|---|---|
| `--background` | `oklch(0.17 0.025 255)` | `#08101A` | — |
| `--foreground` | `oklch(0.95 0.01 240)` | `#E9F0F5` | 16.6:1 on background, 15:1 on card |
| `--card` | `oklch(0.22 0.03 255)` | `#111B28` | — |
| `--card-foreground` | `oklch(0.95 0.01 240)` | `#E9F0F5` | 15:1 |
| `--popover` / `--popover-foreground` | same as card / card-foreground | | |
| `--primary` | `oklch(0.78 0.11 215)` | `#54C9E3` | 9.9:1 on background |
| `--primary-foreground` | `oklch(0.17 0.025 255)` | `#08101A` | 9.9:1 on primary |
| `--secondary` | `oklch(0.28 0.03 255)` | `#1F2A38` | |
| `--secondary-foreground` | `oklch(0.95 0.01 240)` | `#E9F0F5` | 11:1 |
| `--muted` | `oklch(0.28 0.03 255)` | `#1F2A38` | |
| `--muted-foreground` | `oklch(0.72 0.02 240)` | `#9AA7B0` | 7.7:1 on background, 7.0:1 on card |
| `--accent` | `oklch(0.30 0.05 220)` | `#07333F` | |
| `--accent-foreground` | `oklch(0.85 0.10 210)` | `#77E0F2` | 8.8:1 on accent, 11.3:1 on card |
| `--destructive` | `oklch(0.70 0.17 22)` | `#F66C6D` | 6.0:1 on card, 6.6:1 on background |
| `--border` | `oklch(0.32 0.03 255)` | `#293442` | decorative |
| `--input` | `oklch(0.36 0.03 255)` | — | 1.6:1 on card (field edge only) |
| `--ring` | `oklch(0.78 0.11 215)` | `#54C9E3` | 9.0:1 on card |
| `--zone-rejected` | `oklch(0.40 0.10 25)` | `#742E2B` | fill |
| `--zone-decide` | `oklch(0.32 0.02 80)` | `#383227` | fill |
| `--zone-calendar` | `oklch(0.72 0.12 215)` | `#26B7D3` | 7.3:1 on card |

Thumb on the scale (dark): body `--card` vs zone-calendar 7.3:1; border `--foreground` vs zone-rejected 8.4:1, vs zone-decide 11:1. Every zone has either the thumb body or its border at ≥ 3:1 (border vs zone-calendar alone is 2.1:1; the body carries it).

### Wiring in `index.css`

| Change | Detail |
|---|---|
| Delete `@custom-variant dark (&:is(.dark *));` | Tailwind v4's default `dark:` variant is `prefers-color-scheme: dark`; the `dark:` classes already in `button`, `badge`, `input`, `textarea` start working with no edit |
| Replace the `.dark { … }` block | `@media (prefers-color-scheme: dark) { :root { … } }` with the dark table above |
| `:root { color-scheme: light }`, dark block `color-scheme: dark` | native scrollbars, number spinners and autofill follow the theme |
| Add to `@theme inline` | `--color-zone-rejected: var(--zone-rejected)`, `--color-zone-decide: var(--zone-decide)`, `--color-zone-calendar: var(--zone-calendar)` → utilities `bg-zone-*`, `fill-zone-*` |
| Drop unused tokens | `--chart-*`, `--sidebar-*` and their `@theme` lines; nothing references them (grep) |
| `index.html` | `<meta name="theme-color" content="#F8FAFD" media="(prefers-color-scheme: light)">` and `content="#08101A" media="(prefers-color-scheme: dark)"` |

No toggle. The OS setting decides.


## 3. Type

### Faces

| Role | Stack | Source |
|---|---|---|
| Display (`--font-heading`) | `'Bricolage Grotesque', 'Geist Variable', system-ui, sans-serif` | one `<link>` in `index.html`: `https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700&display=swap`, with the two `preconnect` links Google prescribes. Fallback is the installed Geist: an offline load renders headings in Geist; the two faces share no metrics, so a `swap` repaints headings with a width change, which nothing depends on |
| Body (`--font-sans`) | `'Geist Variable', system-ui, sans-serif` | installed (`@fontsource-variable/geist`), unchanged |
| Mono | `ui-monospace, 'SF Mono', Menlo, monospace` | calendar URL only (`font-mono` already on the input) |

### Scale

| Element | Face | Size / line | Weight | Extras |
|---|---|---|---|---|
| Wordmark `Sail Event` (header h1) | display | 20 px / 1.2 (phone 18 px) | 700 | `tracking-tight` |
| App name on Sign in / Create account | display | 28 px / 1.2 | 700 | `tracking-tight`, mark 40 px above it |
| Page h2 (`Queue`, `All events`) | display | 24 px / 1.2 | 700 | `tracking-tight` |
| Card title (`CardTitle`, event title) | display | 18 px / 1.3 | 600 | via `font-heading` token, no per-card class |
| Card description, explainers | Geist | 14 px / 1.5 | 400 | `text-muted-foreground` |
| Body, event fields | Geist | 14 px / 1.5 | 400 | labels (`When:` etc.) `text-muted-foreground`, values `text-foreground` |
| `Why:` line (queue) | Geist | 16 px / 1.5 | 400 | the `Why:` span 600 `text-accent-foreground` |
| `Match: 72 / 100` | Geist | 14 px | value span 600 | `tabular-nums`; the span wraps the whole `72 / 100` so `getByText(/85 \/ 100/)` still matches one element |
| Field labels (`Label`) | Geist | 14 px / 1 | 500 | unchanged |
| Buttons | Geist | 14 px (sm 13 px) | 500 | unchanged weights |
| Badges | Geist | 12 px | 500 | `tracking-wide` (0.01em) |
| Scale ends `0` / `100` | Geist | 12 px | 500 | `tabular-nums text-muted-foreground` |
| Thumb values (`30`, `70`) | Geist | 12 px | 600 | `tabular-nums text-foreground` (currently muted) |
| Zone legend labels | Geist | 13 px | 500 | `text-foreground` |
| Inline status (`Saved.`, `Copied`) | Geist | 14 px | 500 | `text-accent-foreground` |
| Errors | Geist | 14 px | 400 | `text-destructive`, unchanged |


## 4. Layout and spacing

| Item | Desktop (≥ 640 px) | Phone (< 640 px) |
|---|---|---|
| Page max width | `max-w-2xl` (672 px), centred | full width |
| Main padding | `p-8` | `p-4` (App currently `p-8` everywhere; becomes `p-4 sm:p-8`) |
| Header | `h-14` (56 px), `sticky top-0 z-10`, `bg-card/80 backdrop-blur border-b`, `px-8` | two rows (existing `flex-wrap`): row 1 name + Sign out, row 2 tabs; `px-4`; ≈ 96 px total |
| Card padding (`--card-spacing`) | 20 px (`--spacing(5)`) | 16 px (`--spacing(4)`, current) |
| Card radius | `rounded-xl` (16.8 px with `--radius: 0.75rem`) | same |
| Gap between cards | `gap-6` (24 px, current) | `gap-4` (16 px) |
| Gap inside a card (header → content) | `gap-4` (current) | same |
| Field stack (label → input) | `gap-2` (current) | same |
| Button row | `gap-2` (current) | same |
| Sign in / Create account card | `max-w-sm` (384 px), vertically centred (current) | full width minus `p-4` |
| Event list | one column | one column |
| Scale legend | one row under the bar (current) | vertical with swatches (current) |
| Number inputs on the scale | side by side (current) | stacked (current) |
| Copy / Reset link | one row with the URL | wrap under the URL (current) |

Breakpoint: only `sm` (640 px). Nothing else changes with width.


## 5. Components

### Header

| Part | Current | New |
|---|---|---|
| Wordmark | `<h1 class="text-lg sm:text-xl font-bold">Sail Event</h1>` | `<h1 class="flex items-center gap-2 font-heading text-lg sm:text-xl font-bold tracking-tight"><SailMark class="size-6" aria-hidden="true" />Sail Event</h1>`; accessible name stays `Sail Event` |
| `SailMark` | — | new `frontend/src/components/SailMark.tsx`: inline SVG of `_docs/icon-proposals/b-sail-mark.svg` (`viewBox 0 0 256 256`, three paths). Sail `className="fill-zone-calendar"`; mast and hull `stroke="currentColor"` so they follow `text-foreground` in both themes. Props: `className`, `aria-hidden` default true |
| Favicon | Vite default | `frontend/public/favicon.svg` = `b-sail-mark.svg` verbatim plus one `<style>@media (prefers-color-scheme: dark){.ink{stroke:#E9F0F5}}</style>` with `class="ink"` on mast and hull, so the navy strokes read on dark tab bars |
| Bar | `border-b px-4 sm:px-8 py-3` | `sticky top-0 z-10 h-auto sm:h-14 border-b bg-card/80 backdrop-blur px-4 sm:px-8` |
| Tabs | `Button size=sm`, active `default`, others `ghost` | active becomes `secondary` (one word in `App.tsx`: `variant={page === tab.page ? 'secondary' : 'ghost'}`), restyled as `bg-accent text-accent-foreground` (light 7.4:1, dark 8.8:1); inactive `ghost` unchanged; `aria-current` unchanged. `gap-1` stays |
| Queue count | `text-xs` in the active/ghost button | unchanged markup; `tabular-nums` |
| Username | `text-sm text-muted-foreground` | unchanged |
| Sign out | `outline sm` | unchanged variant |

### Buttons (`components/ui/button.tsx`)

| Variant | Current | New |
|---|---|---|
| base | `rounded-lg … transition-all … focus-visible:ring-3 ring-ring/50` | `rounded-lg transition-colors duration-150 focus-visible:ring-3 focus-visible:ring-ring/40 focus-visible:border-ring`; keep `active:translate-y-px` |
| `default` (Accept, Save, Search now, Sign in) | `bg-primary text-primary-foreground hover:bg-primary/80` | `bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs` |
| `outline` (Sign out, Remove from calendar, Cancel, Try again) | `border-border bg-background hover:bg-muted …` | `border-border bg-card hover:bg-muted dark:bg-card dark:border-input dark:hover:bg-muted` |
| `secondary` (active tab) | tint of secondary, unused today | `bg-accent text-accent-foreground hover:bg-accent/80 aria-expanded:bg-accent` |
| `ghost` (inactive tabs) | `hover:bg-muted` | unchanged |
| `destructive` (Reject, Reset, Remove) | `bg-destructive/10 text-destructive hover:bg-destructive/20` | destructive-ghost: `bg-transparent text-destructive hover:bg-destructive/10 focus-visible:ring-destructive/30 dark:hover:bg-destructive/15`; same variant name, so no call site changes |
| sizes | `default h-8`, `sm h-7` | `default h-9 px-3.5`, `sm h-8 px-3`; `xs`, `lg`, `icon*` unchanged |
| disabled | `opacity-50` | unchanged |

### Cards (`components/ui/card.tsx`)

| Part | Current | New |
|---|---|---|
| Surface | `rounded-xl bg-card ring-1 ring-foreground/10` | `rounded-xl bg-card border border-border shadow-xs` (dark: `shadow-none`); the radius class stays, the base `--radius` grows from 10 px to 12 px so `rounded-xl` goes from 14 px to 16.8 px |
| Spacing | `[--card-spacing:--spacing(4)]` | `[--card-spacing:--spacing(4)] sm:[--card-spacing:--spacing(5)]` |
| Title | `font-heading text-base font-medium` | `font-heading text-lg font-semibold tracking-tight leading-snug` |
| Description | `text-sm text-muted-foreground` | unchanged, `leading-relaxed` |
| Footer | unused | unchanged |

### Badges (`components/ui/badge.tsx`) — icon-free

| Status → variant | Current | New |
|---|---|---|
| base | `h-5 rounded-4xl px-2 text-xs font-medium` | `h-6 rounded-full px-2.5 text-xs font-medium tracking-wide` |
| `On your calendar` → `default` | `bg-primary text-primary-foreground` | `bg-accent text-accent-foreground` (light 7.4:1, dark 8.8:1) |
| `Rejected` → `destructive` | `bg-destructive/10 text-destructive dark:bg-destructive/20` | light unchanged (`bg-destructive/10`, text on the tint 4.9:1); dark becomes `dark:bg-transparent dark:border-destructive/40` (text on card 6.0:1 — on the 20 % tint it is only 3.0:1, on 10 % 4.0:1, both fail) |
| `Waiting for you` → `secondary` | `bg-secondary text-secondary-foreground` | `bg-muted text-foreground border-border` |
| `outline`, `ghost`, `link` | — | unchanged (unused) |

`EventCard`'s `badgeVariant` map stays as is.

### Inputs and textarea

| Part | Current | New |
|---|---|---|
| Input height | `h-8` | `h-9` |
| Surface | `bg-transparent border-input dark:bg-input/30` | `bg-card border-input dark:bg-background` |
| Radius | `rounded-lg` | unchanged |
| Placeholder | `text-muted-foreground` | unchanged |
| Focus | `border-ring ring-3 ring-ring/50` | `border-ring ring-3 ring-ring/30` |
| Textarea | `min-h-16 py-2` | `min-h-24 py-2.5 leading-relaxed`; `rows=4` on Home unchanged |
| Number inputs on the scale | `w-20` | `w-24 tabular-nums text-base sm:text-sm` |
| Calendar URL | `font-mono text-xs` | unchanged, `bg-muted/50` since it is read-only |
| Label | unchanged | unchanged |

### Score scale (`components/ScoreScale.tsx`)

| Part | Current | New |
|---|---|---|
| Track | `h-3 rounded-full overflow-hidden` | `h-3 rounded-full overflow-hidden ring-1 ring-foreground/10` |
| Rejected zone | `bg-destructive/20` | `bg-zone-rejected` |
| You decide zone | `bg-muted` + 45° hatch `opacity-10 currentColor` | `bg-zone-decide` + same hatch |
| On your calendar zone | `bg-primary` | `bg-zone-calendar` |
| Thumbs | `size-6 bg-background border-2 border-primary shadow` | `size-7 bg-card border-2 border-foreground shadow-md hover:ring-4 hover:ring-ring/20 focus-within:ring-4 focus-within:ring-ring/40 transition-shadow duration-150`; control strip `h-7` |
| Thumb values | `text-xs text-muted-foreground` | `text-xs font-semibold tabular-nums text-foreground` |
| Scale ends `0` / `100` | `text-xs text-muted-foreground` | `text-xs font-medium tabular-nums text-muted-foreground` |
| Desktop legend | plain text, centred per zone | same, `text-[13px] font-medium`; each label prefixed by a `size-2 rounded-full` dot in its zone colour (`bg-zone-*`), `aria-hidden` |
| Phone legend swatches | `bg-destructive/20`, `bg-muted`, `bg-primary` | `bg-zone-rejected`, `bg-zone-decide border-foreground/10`, `bg-zone-calendar`; `rounded-full` |
| Validation line | `text-sm text-destructive` | unchanged |

Roles, names, `aria-valuetext`, fieldset and legend: unchanged.

### Event card hierarchy (`components/EventCard.tsx`)

| Part | Current | New |
|---|---|---|
| `Why:` label (queue, first line) | `font-bold` | `font-semibold text-accent-foreground`; literal text `Why:` kept |
| `Why:` label (all variant, `EventCard.tsx:141`) | `font-medium` | same `font-semibold text-accent-foreground` |
| Why sentence | `text-base` | `text-base leading-relaxed` |
| Title | `CardTitle` | `CardTitle` (now display 18 px 600) |
| Field labels `Match:` `When:` `Where:` `Link:` | `font-medium` | `font-medium text-muted-foreground` |
| Match value | plain text | `<span class="font-semibold tabular-nums">{score} / 100</span>` |
| Link | `underline break-all` | `underline break-all text-primary decoration-primary/40 underline-offset-2 hover:decoration-primary` |
| Fields block | `gap-2 text-sm` | `gap-1.5 text-sm` |
| Buttons row | `gap-2 pt-2` | `gap-2 pt-3` |
| Badge (all variant) | top-right | unchanged position |
| Status error line | `text-sm text-destructive` | unchanged |

### Empty states (Queue, All events) — illustration-free

| Part | Current | New |
|---|---|---|
| Container | two bare `<p>` | `<div class="rounded-xl border border-dashed border-border bg-muted/40 px-6 py-10 text-center">` wrapping the same two `<p>` |
| First line | `font-medium` | `font-heading text-lg font-semibold` |
| Second line | `text-sm text-muted-foreground` | same, `max-w-sm mx-auto mt-2 leading-relaxed` |
| Loading `Loading…` | `text-muted-foreground` | unchanged |

Copy unchanged: `Nothing to decide right now.` / `No events yet.` and their second lines.

### Saved. / Searching… / Copied feedback

| State | Current | New |
|---|---|---|
| `Saved.` (criteria, scoring) | `text-sm` | `text-sm font-medium text-accent-foreground animate-in fade-in-0 duration-200`; still `role=status`, still 2 s |
| `Copied` | button label swap | unchanged |
| `Searching…` | button label swap, button disabled | unchanged; add `aria-busy="true"` on the button while in flight. No spinner |
| Search result line | `text-sm` | `text-sm animate-in fade-in-0 slide-in-from-top-1 duration-200`; error state unchanged |
| In-flight labels `Accepting…` etc. | label swap | unchanged |

### Focus rings

| Element | Current | New |
|---|---|---|
| Buttons, inputs, textarea | `border-ring ring-3 ring-ring/50` | `border-ring ring-3 ring-ring/40`; `--ring` is now teal (light 3.7:1, dark 9:1 against the card) |
| Slider thumbs | `focus-within:ring-3 ring-ring/50` | `focus-within:ring-4 ring-ring/40` |
| Text links (`Create one`, `Sign in`, event links) | browser default | `rounded-sm focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2` |
| Global `outline-ring/50` on `*` | present | unchanged |


## 6. Motion

| Where | Transition | Duration / easing |
|---|---|---|
| Button, badge, input hover / colour change | `transition-colors` (replaces `transition-all`) | 150 ms, `ease-out` |
| Slider thumb hover ring | `transition-shadow` | 150 ms |
| `Saved.`, `Copied`, search result line appear | `animate-in fade-in-0` (+ `slide-in-from-top-1` for the result line) | 200 ms; no exit animation, the 2 s timer unmounts |
| Queue card after Accept / Reject succeeds | `animate-out fade-out-0 slide-out-to-right-2 fill-mode-forwards` on the card, then unmount | 200 ms. Ordering: `QueuePage.handleDecide` awaits `decideEvent`, calls `onQueueChange`, starts a fire-and-forget `setTimeout(remove, 200)` and returns at once; `EventCard` sets its `leaving` flag when `onDecide` resolves, so the exit classes apply while the card is still mounted; the timer unmounts it. `handleDecide` must not await the timer. Tests already `waitFor` removal |
| All events: badge flips to `Rejected` | none (text swap) | — |
| Tab switch, page load, card mount | none | — |
| `prefers-reduced-motion: reduce` | `@layer base { @media (prefers-reduced-motion: reduce) { *, ::before, ::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; } } }` in `index.css` | the 200 ms removal delay stays (imperceptible, no motion) |

Nothing else moves. No parallax, no skeletons, no spinners.


## 7. Accessibility checklist

- [ ] Text contrast ≥ 4.5:1 everywhere text sits on its surface, both themes (table §2; lowest: light `destructive` on the 10 % tint 4.9:1, dark `destructive` on card 6.0:1; the dark Rejected badge is outlined, not tinted, for this reason). Hover tints (`hover:bg-destructive/10`) are transient and not counted
- [ ] Non-text contrast ≥ 3:1: focus ring on card (light 3.7:1, dark 9:1); zone-calendar on card (light 3.4:1, dark 7.3:1); thumb body or border vs every zone ≥ 3:1 (§2)
- [ ] Colour never the only carrier: zone labels, thumb numbers, badge text, error text all present (unchanged from P1)
- [ ] Focus visible on every interactive element including the text links on Sign in / Create account and the event links (§5 Focus rings)
- [ ] Hit sizes: buttons ≥ 32 px tall (`sm`) / 36 px (`default`); slider thumbs 28 px; inputs 36 px; number inputs 96 px wide
- [ ] Reduced motion honoured globally (§6); no content depends on an animation finishing
- [ ] Dark mode follows the OS; `color-scheme` set so native controls match
- [ ] Display font loads with `display=swap` and a fallback (Geist); no layout depends on the web font being present
- [ ] `SailMark` is `aria-hidden`; the h1 accessible name is still `Sail Event`
- [ ] Zoom to 200 %: single column, no horizontal scroll (phone layout already handles 320–640 px)


## 8. Implementation plan

Three issues, in order. Each is one engineer session. Label: `theme`. Every existing test selector, `data-testid`, ARIA name and copy string stays unchanged; only classes, tokens and two new files (`SailMark.tsx`, `favicon.svg`) are added.

### Issue T1 — Tokens, fonts, favicon and mark, dark mode

Goal: tokens, fonts, favicon and the mark component exist and the app renders in the new palette in both themes; no component or page is edited yet (the mark is wired into the pages in T2).

- [ ] `index.css`: light `:root` and `@media (prefers-color-scheme: dark) { :root }` blocks carry exactly the values in §2; `.dark` block and `@custom-variant dark` line removed; `color-scheme` set in both blocks; `--chart-*` and `--sidebar-*` tokens and their `@theme` lines removed
- [ ] `@theme inline` exposes `--color-zone-rejected`, `--color-zone-decide`, `--color-zone-calendar`; `bg-zone-calendar` compiles (used by T2)
- [ ] `--font-heading` is `'Bricolage Grotesque', 'Geist Variable', system-ui, sans-serif`; `index.html` has the single Google Fonts `<link>` (weights 600, 700, `display=swap`) plus the two `preconnect` links; with the network blocked the page renders in Geist with no error
- [ ] `index.html` carries the two `theme-color` meta tags; `frontend/public/favicon.svg` is `b-sail-mark.svg` with the dark-scheme `<style>` rule; the Vite default favicon is gone
- [ ] `frontend/src/components/SailMark.tsx` exists, renders the three paths with `fill-zone-calendar` sail and `currentColor` mast and hull, `aria-hidden="true"` by default; the three paths carry no `fill` / `stroke` colour attributes (colour comes from classes only); not yet imported anywhere
- [ ] Reduced-motion rule from §6 present in `index.css`
- [ ] With the OS in dark mode the page background is `#08101A`-ish navy, primary buttons are teal with dark text, and no element keeps a light-theme colour (manual check of the four screens); `npm test` and `make test` green

### Issue T2 — Component restyle and the scale

Goal: every component matches §5; the scale uses the zone tokens.

- [ ] `button.tsx`: sizes `default h-9`, `sm h-8`; `transition-colors`; `destructive` is the ghost treatment (transparent at rest, tint on hover); `outline` uses `bg-card`; `secondary` is `bg-accent text-accent-foreground hover:bg-accent/80`; focus ring `ring-ring/40`
- [ ] `card.tsx`: `rounded-xl border border-border shadow-xs`, `--card-spacing` 16 px phone / 20 px desktop, title `text-lg font-semibold tracking-tight`
- [ ] `badge.tsx`: `h-6 rounded-full px-2.5 tracking-wide`; `default` = `bg-accent text-accent-foreground`, `secondary` = `bg-muted text-foreground border-border`, `destructive` dark = `dark:bg-transparent dark:border-destructive/40`; `EventCard` badge map untouched; `getByText('On your calendar' | 'Rejected' | 'Waiting for you')` pass
- [ ] `input.tsx` / `textarea.tsx`: `h-9`, `bg-card`, focus `ring-ring/30`; textarea `min-h-24 leading-relaxed`
- [ ] `ScoreScale.tsx`: zone fills `bg-zone-*`, thumbs `size-7 bg-card border-foreground` with hover and focus rings, thumb values `font-semibold tabular-nums text-foreground`, legend dots and swatches in zone colours; `ScoreScale.test.tsx` green with no selector change
- [ ] `EventCard.tsx`: `Why:` span `font-semibold text-accent-foreground`, field labels muted, score wrapped as one span `font-semibold tabular-nums` containing `{score} / 100`, link classes per §5; `EventCard.test.tsx` green (`/85 \/ 100/` and `Why:` still match)
- [ ] `App.tsx`: h1 shows `<SailMark class="size-6" />` before the text `Sail Event` and uses `font-heading`; active tab variant is `secondary` (`variant={page === tab.page ? 'secondary' : 'ghost'}`), `aria-current` unchanged; header `sticky top-0 bg-card/80 backdrop-blur sm:h-14`; main `p-4 sm:p-8`; `App.test.tsx` and e2e `getByRole("heading", { name: "Sail Event" })` pass unchanged
- [ ] `LoginPage.tsx` / `RegisterPage.tsx`: the mark (40 px) above the app name; app name `font-heading text-[28px] font-bold tracking-tight`; text links `Create one` / `Sign in` carry the focus classes
- [ ] `QueuePage.tsx` / `EventsPage.tsx` h2s `font-heading text-2xl font-bold tracking-tight`
- [ ] `MainPage.tsx`: card gap `gap-4 sm:gap-6`; `Saved.` spans `font-medium text-accent-foreground`
- [ ] `npm test`, `make test`, `make test-e2e` green

### Issue T3 — Motion and empty states

Goal: the few transitions in §6 and the empty-state panel in §5.

- [ ] `QueuePage.tsx` and `EventsPage.tsx` empty states wrapped in the dashed `rounded-xl` panel; first line `font-heading text-lg font-semibold`; copy unchanged; `QueuePage.test.tsx` / `EventsPage.test.tsx` green
- [ ] `EventCard` queue variant: when `onDecide` resolves the card sets `leaving` and gets `animate-out fade-out-0 slide-out-to-right-2 fill-mode-forwards duration-200`; `QueuePage.handleDecide` awaits `decideEvent`, calls `onQueueChange`, starts a fire-and-forget `setTimeout` (200 ms) that removes the card from state, and returns at once — it never awaits the timer, so `onDecide` resolves while the card is still mounted; `QueuePage.test.tsx` `waitFor` assertions green; e2e Journey 1 green
- [ ] `Saved.` and the search result line carry `animate-in fade-in-0 duration-200` (result line also `slide-in-from-top-1`); `role=status` kept
- [ ] `Search now` button has `aria-busy="true"` while `searching`
- [ ] With `prefers-reduced-motion: reduce` emulated in devtools, accepting a queue card shows no slide and the card disappears within 250 ms
- [ ] `npm test`, `make test`, `make test-e2e` green; `docs/images/*.png` re-captured on the new theme (same four screens, light mode)


## 9. Decisions

| # | Decision | Strongest fact against it |
|---|---|---|
| 1 | Display face via one Google Fonts link (`Bricolage Grotesque`), Geist stays for body | Adds a third-party request on every load; the fallback makes it optional but the first paint can swap |
| 2 | Dark mode by `prefers-color-scheme` only, `.dark` class removed | A future toggle needs the class variant back (`@custom-variant dark (&:where(.dark, .dark *))`) and a small script |
| 3 | Zone colours are three new tokens, not reuse of `destructive` / `muted` / `primary` | Three more variables to maintain; the P1 risk table expected token reuse |
| 4 | Thumb border is `--foreground`, not `--primary` | In dark mode primary and the calendar zone are both teal; the thumb body (card colour) carries the 3:1, not the border |
| 5 | `destructive` button variant becomes a ghost (transparent at rest) instead of a new variant name | Reset / Remove confirm buttons lose their tint at rest; they sit next to a prompt sentence, so context carries them |
| 6 | Active tab is the `secondary` variant restyled as `bg-accent text-accent-foreground` (teal tint); primary actions stay navy in light mode (reversed after review F5) | The active tab and the `On your calendar` badge now share the same tint; a tab and a status reading alike is a small ambiguity, accepted because they never sit side by side |
| 7 | Badges stay icon-free; `lucide-react` stays unused | Three statuses without icons rely on wording plus tint; wording is already distinct |
| 8 | No spinner on `Searching…` / `Accepting…`; label swap plus `aria-busy` | A long search (real provider) shows only a disabled button with an ellipsis |
| 9 | Card removal delay implemented in `QueuePage` with a 200 ms `setTimeout`, not an animation-end listener | A test that asserts removal synchronously after `await` would fail; the existing ones use `waitFor` |
| 10 | `--radius` 10 px → 12 px; cards and the empty-state panel use `rounded-xl` (16.8 px, not `rounded-2xl` = 21.6 px under this file's `--radius-2xl: calc(var(--radius) * 1.8)`) | Larger radii on small `sm` buttons look soft; `sm` keeps its capped radius from shadcn |
| 11 | Empty state is a dashed panel, no illustration | Dashed borders can read as a drop target; the copy says otherwise |
| 12 | Unused `--chart-*` / `--sidebar-*` tokens deleted | Future shadcn `add` of sidebar or chart would need them back; one `npx shadcn add` regenerates them |
| 13 | `README` screenshots re-captured in T3, light mode only | Dark mode has no screenshot in the README |
| 14 | `--input` edge stays at 1.5:1 light / 1.6:1 dark (review F7 accepted as P1 carry-over, current shadcn default ≈ 1.2:1) | On a `bg-card` input inside a `bg-card` card the border is the only boundary cue; the label and the focus ring carry the field |

### Review applied (`_docs/theme-design-review.md`)

| Finding | What changed |
|---|---|
| F1 | `rounded-2xl` → `rounded-xl` (16.8 px) in §2 `--radius` row, §4, §5 Cards, §5 Empty states, T2 and T3 bullets; decision 10 states the 21.6 px trap |
| F2 | "metric-compatible" deleted from §7; §3 Faces says the faces share no metrics and `swap` repaints headings |
| F3 | §6 row 4 and T3 bullet 2 state the ordering: `handleDecide` awaits `decideEvent`, calls `onQueueChange`, starts a fire-and-forget `setTimeout`, returns; never awaits the timer |
| F4 | T1 goal reworded; h1 mark, sign-in mark and h2 `font-heading` bullets moved to T2 (`App.tsx`, `LoginPage` / `RegisterPage`, `QueuePage` / `EventsPage` bullets); T1 creates `SailMark.tsx` unimported |
| F5 | decision 6 reversed: active tab `secondary` = `bg-accent text-accent-foreground` (§5 Header, §5 Buttons, T2); §1 names what carries the "tech" note in light mode; primary buttons stay navy in light (teal fails 4.5:1 under white text), teal in dark |
| F6 | §5 Event card: all-variant `Why:` row added |
| F7 | not raised; decision 14 records the carry-over |
| F8 | T1 `SailMark` criterion: no `fill` / `stroke` colour attributes on the paths |
