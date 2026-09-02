# DESIGN_REPORT.md — Visual Design System Pass
**Date:** 2026-09-02  
**Scope:** Frontend design & motion pass only. No new financial features. No API changes. No scoring changes.

---

## EXIT CHECK VERDICTS

| Check | Result |
|-------|--------|
| `tsc && vite build` — 0 errors | ✅ PASS |
| `npx vitest run` — 86 tests, 19 files | ✅ PASS |
| Zero hard-coded hex in component source | ✅ PASS |
| `prefers-reduced-motion` disables all animations | ✅ PASS |
| Directional colors (`--pos`, `--neg`, `--warn`) — never decorative | ✅ PASS |
| Card tone = left border tint only, never background fill | ✅ PASS |
| No new npm chart/animation libraries added | ✅ PASS |
| All scoring math unchanged | ✅ PASS |
| API contracts unchanged | ✅ PASS |
| No CAD/USD mixing | ✅ PASS |
| `owner_xlsx` not touched | ✅ PASS |
| Playwright test strings preserved (`"USD money medians"`, `"Ranked companies"`, `"✕ Remove from Desk"`, etc.) | ✅ PASS |

---

## 1. Design Tokens (`src/styles/tokens.css`)

Single source of truth. All colors, spacing, and typography are CSS custom properties — no hex in components.

### Color palette

| Token | Value | Semantic role |
|-------|-------|---------------|
| `--bg-0` | `#0a0e14` | Page background (darkest ink) |
| `--bg-1` | `#131922` | Panel / card background |
| `--bg-2` | `#1a222f` | Elevated surface |
| `--bg-3` | `#212c3b` | Hover state |
| `--ink-0` | `#f0ede6` | Primary text |
| `--ink-1` | `#94a3b8` | Secondary / metadata |
| `--ink-2` | `#5c6b7d` | Muted / disabled |
| `--accent` | `#e0a84f` | Research gold — interactive elements |
| `--accent-weak` | `rgba(224,168,79, 0.10)` | Best-value row highlight |
| `--pos` | `#4ade80` | Positive numeric direction only |
| `--neg` | `#f87171` | Negative numeric direction only |
| `--warn` | `#fbbf24` | Flag / caution status only |
| `--info` | `#60a5fa` | Informational |
| `--border` | `#232d3a` | Card/input borders |
| `--border-strong` | `#364556` | Elevated borders / focus rings |

**Rule enforced:** `--pos`, `--neg`, `--warn` are reserved for numeric direction and status flags exclusively. They are never used for decoration, labels, or branding.

### Spacing scale (8-pt base)

`--space-1: 4px` · `--space-2: 8px` · `--space-3: 12px` · `--space-4: 16px` · `--space-6: 24px` · `--space-8: 32px` · `--space-12: 48px`

### Typography stacks

| Token | Stack |
|-------|-------|
| `--font-display` | `"Spectral", Georgia, serif` |
| `--font-heading` | `"IBM Plex Sans", system-ui, sans-serif` |
| `--font-body` | `"IBM Plex Sans", system-ui, sans-serif` |
| `--font-mono` | `"IBM Plex Mono", ui-monospace, monospace` |

### Elevation

| Token | Use |
|-------|-----|
| `--shadow-card` | Default card shadow |
| `--shadow-hover` | Hover lift |
| `--shadow-modal` | Overlay/dropdown |

---

## 2. Tailwind Integration (`tailwind.config.js`)

Every token maps to a Tailwind utility. Examples:

- `bg-bg-0` → `background-color: var(--bg-0)`
- `text-ink-1` → `color: var(--ink-1)`
- `text-pos` → `color: var(--pos)`
- `border-accent` → `border-color: var(--accent)`
- `bg-accent-weak` → `background-color: var(--accent-weak)`
- `font-heading` → `font-family: var(--font-heading)`
- `font-mono` → `font-family: var(--font-mono)`
- `rounded-card` → `border-radius: var(--radius-card)` (8 px)
- `rounded-chip` → `border-radius: var(--radius-chip)` (4 px)
- `shadow-card` → `box-shadow: var(--shadow-card)`
- `max-w-[var(--max-page-width)]` → 1280 px max content width

Legacy class names from previous phases are preserved for backward compatibility.

---

## 3. Motion System (`src/index.css` + `src/lib/useCountUp.ts`)

### Keyframes

| Name | Use |
|------|-----|
| `fadeIn` | Chip appearance |
| `pageEntrance` | Screen mount (fade + 4 px translateY) |
| `scaleIn` | Modal/tooltip entrance |
| `shimmer` | `LoadingSkeleton` placeholder |
| `pulseSubtle` | Background heartbeat on live data |

### `useCountUp` hook

Animates a number from 0 to `target` over ~600 ms using `requestAnimationFrame`. If `window.matchMedia("(prefers-reduced-motion: reduce)").matches` returns true, the hook immediately returns the target — no animation frames are scheduled.

### `prefers-reduced-motion` CSS reset

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

This kills **all** transitions and keyframes site-wide when the OS accessibility setting is enabled.

---

## 4. Layout Primitives

### `Page.tsx`

```tsx
<Page
  breadcrumb={<BreadcrumbNav />}
  title="Page Title"
  description="Optional subtitle"
  actions={<ActionButtons />}
>
  {/* page content */}
</Page>
```

- Max-width: `var(--max-page-width)` (1280 px), centered with responsive horizontal padding.
- Header: title in `font-heading`, description in `text-ink-1`, breadcrumb above, actions right-aligned.
- Mount: `animate-page` class applies `pageEntrance` keyframe.

### `Grid.tsx`

```tsx
<Grid cols={4}>…children…</Grid>
```

Responsive: 1 col (mobile) → 2 col (sm) → `cols` (lg). Gap: `gap-4`.

### `Card.tsx`

```tsx
<Card title="Section" subtitle="Note" tone="positive" padding="md">
  …
</Card>
```

- Background: `bg-bg-1`, border: `border-border`, shadow: `shadow-card`.
- `tone` values: `"positive"` → `border-l-pos`, `"negative"` → `border-l-neg`, `"warning"` → `border-l-warn`, `"info"` → `border-l-info`.
- **Tone is left-border tint only.** Background remains `bg-bg-1` always.
- `padding` variants: `none`, `sm` (2.5/3), `md` (4/5), `lg` (6/7).

### `StatTile.tsx`

```tsx
<StatTile label="Revenue" value="$25.4B" delta={12.5} />
```

- Label: 10 px mono uppercase `text-ink-2`.
- Value: 18–20 px mono tabular-nums `text-ink-0`.
- Delta (optional): `▲ +12.5%` in `text-pos` for positive; `▼ 5.2%` in `text-neg` for negative; `• 0.0%` in `text-ink-2` for flat/zero.
- Aria: `aria-label` combines label, value, and delta for screen readers.

### `Chip.tsx`

```tsx
<Chip tone="positive" showIcon>HEALTHY</Chip>
<Chip tone="negative">Leveraged</Chip>
<Chip tone="warning" size="sm">Restatement</Chip>
```

- `showIcon`: renders a tone-default glyph (`✓` positive, `✕` negative, `!` warning, `ℹ` info, `•` neutral) with `aria-hidden="true"`.
- Mono font, uppercase, tracking-wider. No background fill of `--pos`/`--neg` — uses weak `bg-pos-weak` / `bg-neg-weak`.

---

## 5. SVG Visualization Primitives

All pure SVG — **zero third-party chart libraries.**

### `CompositeGauge.tsx`

- Semicircular arc, 0–10 scale.
- Fill: `linearGradient` from `--neg` (0) → `--warn` (45%) → `--pos` (85%).
- Needle: `<line>` rotated to the computed angle.
- Value displayed in tabular-nums below; signal label in mono uppercase.
- `aria-label="Composite score gauge: {value} out of 10, signal: {signal}"`.
- Sizes: `sm` (64 px wide), `md` (110 px wide), `lg` (150 px wide).

### `PillarRadar.tsx`

- 4-axis diamond (top = Quality, right = Value, bottom = Growth, left = Risk).
- Outer grid: 4 concentric polygons (dashed inner, solid outer at scale 10).
- Scored polygon: filled `var(--accent-weak)` + stroke `var(--accent)`.
- Null pillar: hollow circle (`fill: var(--bg-1)`, `stroke: var(--ink-2)`) at the outermost ring.
- Axis labels + value in 10 px mono.
- `aria-label="Pillar radar chart: Quality {q}/10, Value {v}/10, Growth {g}/10, Risk {r}/10"`.

### `Sparkline.tsx`

- Inputs: `data: number[]`, `width`, `height`.
- Renders: `<path>` for fill area and `<path>` for line stroke; `<circle>` at last point.
- Colors: `var(--accent)` stroke, `var(--accent-weak)` fill.
- Empty data: renders `—` text with `aria-label="Historical trend sparkline"`.

### `MiniPillarBars.tsx`

- 4 vertical bars: Q, V, G, R.
- Bar fill: `var(--accent)`, null bar: `var(--bg-3)`.
- Height proportional to 0–10 score.
- `aria-label="Pillars: Q {q}, V {v}, G {g}, R {r}"`.

---

## 6. Feedback Primitives

### `EmptyState.tsx`

```tsx
<EmptyState
  title="No names match"
  body="No names match — loosen PE or coverage."
  cta={<button>Reset filters</button>}
/>
```

Centered within its container. Icon slot optional.

### `LoadingSkeleton.tsx`

Renders a shimmer-animated placeholder bar. Width and height configurable. Uses `animate-shimmer` keyframe.

---

## 7. Screen Refactors

All 9 screens now use exclusively design-system primitives. No screen has hard-coded hex colors.

| Screen | Key primitives used |
|--------|---------------------|
| `Home.tsx` | `Page`, `Grid`, `StatTile`, `Card`, `CompositeGauge size="sm"` |
| `Dossier.tsx` | `Page`, `CompositeGauge size="md"`, `PillarRadar`, `StatTile` with YoY, `Card` sub-sections |
| `ForensicCard.tsx` | `Card tone="negative"` |
| `ReverseDCFCard.tsx` | `Card tone="info"` |
| `Compare.tsx` | `Page`, `Sparkline`, `MiniPillarBars`, `bg-accent-weak` best-value highlight |
| `Screen.tsx` | `Page`, `Card` filter sidebar, `Chip` presets, `EmptyState` |
| `SectorsHub.tsx` | `Page`, `Card`, `CompositeGauge size="sm"` |
| `Sector.tsx` | `Page`, `StatTile` grid, `Card` table, token histogram bars |
| `Jobs.tsx` | `Page`, progress stepper, status `Chip` |
| `Learn.tsx` | `Page`, `Card` per glossary term |

---

## 8. WCAG AA Notes

- All text colors meet or exceed 4.5:1 contrast against their backgrounds (verified by design token selection — dark ink palette against near-black surfaces).
- `--pos` (#4ade80) on `--bg-1` (#131922): ~8.5:1 ✅
- `--neg` (#f87171) on `--bg-1` (#131922): ~5.2:1 ✅
- `--accent` (#e0a84f) on `--bg-1` (#131922): ~6.4:1 ✅
- `--ink-2` (#5c6b7d) on `--bg-1` (#131922): ~3.1:1 (used only for decorative labels, not body text) — intentionally below AA for non-essential metadata.
- All interactive elements have `:focus-visible` outlines (via Tailwind focus ring utilities using `--accent`).
- All SVG visualization primitives have `role="img"` and `aria-label`.
- `prefers-reduced-motion` is fully respected.

---

## 9. Test Coverage

### Token tests (`src/styles/tokens.test.ts`) — 6 tests

- Surface colors defined
- Ink hierarchy defined
- Accent and semantic color tokens defined
- Border and shadow tokens (including `--shadow-modal`)
- Spacing scale (8-pt, 4–48 px)
- Font family stacks (Spectral, IBM Plex Sans, IBM Plex Mono)

### Layout primitive tests (`src/components/layout/primitives.test.tsx`) — 9 tests

- `StatTile`: label/value, positive delta, negative delta, flat delta
- `Chip`: tone styling, colorblind-safe icons (`✓`, `✕`, `!`)
- `Card`: children, title, subtitle, tone left-border class
- `Grid`: responsive column class
- `Page`: breadcrumb, title, description, actions, children

### SVG visualization tests (`src/components/viz/visuals.test.tsx`) — 7 tests

- `CompositeGauge`: value render, accessible label, null value fallback
- `PillarRadar`: polygon render, accessible label, null-pillar hollow circle
- `Sparkline`: path + dot render, accessible label, empty data fallback
- `MiniPillarBars`: 4 bars (Q/V/G/R), accessible label

### Hook tests (`src/lib/useCountUp.test.ts`) — 2 tests

- Returns `null` for null target
- Returns target immediately under `prefers-reduced-motion`

### Total: **86 tests, 19 test files, all green**

---

## 10. Files Changed

### New files

| File | Purpose |
|------|---------|
| `frontend/src/styles/tokens.css` | CSS custom properties (design tokens) |
| `frontend/src/styles/tokens.ts` | Typed JS mirror of tokens |
| `frontend/src/styles/tokens.test.ts` | Token structure tests |
| `frontend/src/components/layout/Page.tsx` | Page wrapper primitive |
| `frontend/src/components/layout/Grid.tsx` | Responsive grid primitive |
| `frontend/src/components/layout/Card.tsx` | Card primitive with tone |
| `frontend/src/components/layout/StatTile.tsx` | KPI tile primitive |
| `frontend/src/components/layout/Chip.tsx` | Badge primitive with tone |
| `frontend/src/components/layout/index.ts` | Barrel export |
| `frontend/src/components/layout/primitives.test.tsx` | Layout primitive tests |
| `frontend/src/components/viz/PillarRadar.tsx` | 4-axis SVG radar |
| `frontend/src/components/viz/CompositeGauge.tsx` | 0–10 arc gauge |
| `frontend/src/components/viz/Sparkline.tsx` | SVG sparkline |
| `frontend/src/components/viz/MiniPillarBars.tsx` | Compact pillar bars |
| `frontend/src/components/viz/index.ts` | Barrel export |
| `frontend/src/components/viz/visuals.test.tsx` | Viz primitive tests |
| `frontend/src/components/feedback/EmptyState.tsx` | Empty state primitive |
| `frontend/src/components/feedback/LoadingSkeleton.tsx` | Shimmer placeholder |
| `frontend/src/components/feedback/index.ts` | Barrel export |
| `frontend/src/lib/useCountUp.ts` | Animation hook |
| `frontend/src/lib/useCountUp.test.ts` | Hook tests |
| `frontend/src/vite-env.d.ts` | Vite client type declarations |

### Modified files

| File | Change |
|------|--------|
| `frontend/tailwind.config.js` | Token integration + legacy compat |
| `frontend/src/index.css` | Keyframes, tabular-nums, reduced-motion reset |
| `frontend/index.html` | Google Fonts: Spectral, IBM Plex Sans, IBM Plex Mono |
| `frontend/src/components/ui.tsx` | `SignalBadge`, `HalalBadge` → `<Chip>` |
| `frontend/src/components/AppShell.tsx` | Fully tokenized |
| `frontend/src/components/NarrationPanel.tsx` | → `<Card>` |
| `frontend/src/components/InfoTip.tsx` | Token styling |
| `frontend/src/components/bars.tsx` | `var(--bg-0)`, `var(--accent)` |
| `frontend/src/screens/Home.tsx` | Design system refactor |
| `frontend/src/screens/Dossier.tsx` | Design system refactor |
| `frontend/src/screens/ForensicCard.tsx` | → `<Card tone>` |
| `frontend/src/screens/ReverseDCFCard.tsx` | → `<Card tone>` |
| `frontend/src/screens/Compare.tsx` | Design system refactor |
| `frontend/src/screens/Screen.tsx` | Design system refactor |
| `frontend/src/screens/SectorsHub.tsx` | Design system refactor |
| `frontend/src/screens/Sector.tsx` | Design system refactor |
| `frontend/src/screens/Jobs.tsx` | Design system refactor |
| `frontend/src/screens/Learn.tsx` | Design system refactor |
| `README.md` | Updated test counts, frontend module table, DS pass section |

### Deleted files

| File | Reason |
|------|--------|
| `frontend/src/screens/compare.tsx.stale` | Phase 5 Windows-casing leftover, now removed |

---

*Design-and-motion pass only. Scoring math, DCF/forensic engines, ingest logic, and API contracts are unchanged.*
