# Theme design review — `_docs/theme-design.md`

Reviewer: fresh, no part in the design. Checked against the code on `main` (e1e1c70), `node_modules`, Google Fonts, and an own oklch→sRGB conversion.

## Verified claims (no action)

| Claim | How verified | Result |
|---|---|---|
| Tailwind v4 `dark:` defaults to `prefers-color-scheme` once `@custom-variant dark` is removed | `tailwindcss/dist/lib.js`: `r("dark",["@media (prefers-color-scheme: dark)"])`; no other `@custom-variant dark` in `shadcn/dist/tailwind.css`, `tw-animate.css`, `tailwindcss/index.css` | holds |
| `tw-animate-css` 1.4.0 provides `animate-in`, `animate-out`, `fade-in-*`, `fade-out-*`, `slide-in-from-top-*`, `slide-out-to-right-*`, `fill-mode-*` | `node_modules/tw-animate-css/dist/tw-animate.css` defines each as `@utility`; `duration-200` feeds `--tw-duration`, which `--animate-in/out` read | holds, no plain-keyframe fallback needed |
| `@theme inline { --color-zone-*: var(--zone-*) }` gives `bg-zone-*` / `fill-zone-*` | same pattern as the 20 existing `--color-*` lines in `index.css` | holds |
| Bricolage Grotesque on Google Fonts, weights 600/700 | `curl` of the exact css2 URL returns `font-weight: 600` and `700` `@font-face` blocks, `font-display: swap` | holds |
| Contrast table §2 | own conversion (oklch→linear sRGB→WCAG), 21 pairs spot-checked incl. fg/bg 16.59, primary/bg 12.66, accent-fg/accent 7.42, destructive/card 5.38, ring/card 3.71, zone-cal/card 3.39, dark primary/bg 9.88, dark destructive on 20 % tint 3.0 | every value matches the doc to one decimal |
| Test selectors, ARIA names, `data-testid`, copy strings survive | read all 8 `*.test.tsx` and `e2e/journeys.spec.ts`; `getByText(/85 \/ 100/)` matches the new single span (own-text-node matcher); Playwright `getByText(/Match: \d+ \/ 100/)` still matches the `<p>`; `aria-hidden` SVG leaves the h1 name `Sail Event` | no regression found |
| Dark mode by OS only | Decision 2 names the way back (`@custom-variant dark (&:where(.dark, .dark *))`) | acceptable for now |

## Findings

| id | severity | what is wrong | exact change | section |
|---|---|---|---|---|
| F1 | should | `rounded-2xl` is not 16 px here: `index.css` overrides `--radius-2xl: calc(var(--radius) * 1.8)`, so with `--radius: 0.75rem` cards get 21.6 px (`rounded-xl` = 16.8 px). The doc's pixel claim and Decision 10 are off by a third | either write `rounded-xl` (16.8 px) everywhere `rounded-2xl` appears (cards, empty-state panel), or keep `rounded-2xl` and state 22 px; pick one | §4, §5 Cards, §5 Empty states, §9 #10 |
| F2 | should | "metric-compatible fallback (Geist)" is false: Bricolage Grotesque and Geist share no metrics; a `swap` repaints headings with a width change | delete "metric-compatible"; keep "no layout depends on the web font being present" | §7 checklist line 8, §3 Faces |
| F3 | should | T3 card exit depends on an ordering the text does not state: `EventCard` sets `leaving` when `onDecide` resolves, and `QueuePage.handleDecide` removes the card 200 ms after `decideEvent` resolves. If `handleDecide` awaits that timer, `onDecide` resolves after unmount and no animation ever plays | add to T3 and §6: "`handleDecide` returns right after `decideEvent` resolves; the `setTimeout` is fire-and-forget; `onQueueChange` is called before the timer" | §6 row 4, §8 T3 bullet 2 |
| F4 | should | T1's goal says "no component edited yet" but its criteria edit `App.tsx` (h1 + mark), `LoginPage`, `RegisterPage` (mark, `font-heading`), and the `Queue` / `All events` h2s | move the h1 mark, sign-in mark and h2 `font-heading` bullets to T2, or reword the T1 goal to "tokens, fonts, favicon, mark; four small markup edits" | §8 T1 |
| F5 | should | Taste: in light mode the brand teal appears only in the badge, the scale zone and the focus ring; primary buttons and the active tab are navy. Decision 6 itself calls the solid pill "the most template-like element left". The owner asked for "sexy/cool/modern/tech"; "harbour at dusk — calm" delivers modern, not tech | reverse Decision 6: active tab `bg-accent text-accent-foreground` (one `App.tsx` variant change); state in §1 which element carries the "tech" note in light mode | §1, §5 Header, §9 #6 |
| F6 | nice | All-events variant `Why:` span (`EventCard.tsx:141`, `font-medium`) is not covered: §5 restyles only the queue first line and the field labels | add a row: all variant `Why:` → same `font-semibold text-accent-foreground` as the queue | §5 Event card |
| F7 | nice | `--input` edge 1.5:1 (light) / 1.6:1 (dark) on a `bg-card` input inside a `bg-card` card: the border is the only boundary cue | accept as P1 carry-over (current shadcn default is ≈1.2:1), or raise `--input` to `oklch(0.80 0.015 240)` (≈2.2:1) as a middle step | §2 `--input` |
| F8 | nice | `SailMark` inlines `b-sail-mark.svg` which carries `fill="#00A8CC"` and `stroke="#0F3057"` attributes; the class / `currentColor` win in CSS, but the dead attributes invite a dark-mode bug on the next edit | T1 criterion: "the three paths carry no `fill` / `stroke` colour attributes" | §5 Header `SailMark`, §8 T1 |

## Issue sizing and order

- T1 → T2 → T3 order is right: tokens first, components second, motion last. T1 is the widest (9 files) but each edit is small; T2 is the real session (7 components + e2e run); T3 is half a session. No re-split needed once F4 is settled.

## Verdict

**APPROVE WITH CHANGES** — F1–F5 are text fixes to the design, none changes a selector, a name or a dependency; every implementability claim checked holds.

Strongest fact against: F5 is a taste call the owner may reject, and without it the light theme is the current shadcn layout with a navy/teal tint plus a new display face — "modern", arguably not "sexy/cool/tech". The verdict rests on the owner having ranked prettiness below UX and on dark mode (deep navy, teal primary) carrying the character.
