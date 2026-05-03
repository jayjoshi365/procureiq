---
name: ProcureIQ
colors:
  # ── Page & surface depth (navy-black, five layers) ──
  background: "#03080f"
  surface: "#060d1a"
  surface-dim: "#03080f"
  surface-bright: "#0f1f38"
  surface-container-lowest: "#040b16"
  surface-container-low: "#060d1a"
  surface-container: "#0a1628"
  surface-container-high: "#0f1f38"
  surface-container-highest: "#162236"
  surface-hover: "#0d1e35"
  on-surface: "#f1f5f9"
  on-surface-variant: "#94a3b8"
  inverse-surface: "#f1f5f9"
  inverse-on-surface: "#03080f"
  outline: "#334155"
  outline-variant: "rgba(96,165,250,0.08)"
  surface-tint: "#3b82f6"

  # ── Primary — electric blue (single dominant accent) ──
  primary: "#3b82f6"
  primary-bright: "#60a5fa"
  primary-dim: "#1d4ed8"
  on-primary: "#ffffff"
  primary-container: "rgba(29,78,216,0.06)"
  on-primary-container: "#60a5fa"
  inverse-primary: "#60a5fa"
  primary-fixed: "rgba(96,165,250,0.08)"
  primary-fixed-dim: "rgba(96,165,250,0.35)"
  on-primary-fixed: "#60a5fa"
  on-primary-fixed-variant: "rgba(96,165,250,0.18)"

  # ── Secondary — signal green (positive outcomes, awards) ──
  secondary: "#4ade80"
  on-secondary: "#03080f"
  secondary-container: "rgba(74,222,128,0.07)"
  on-secondary-container: "#4ade80"

  # ── Tertiary — violet (AI intelligence, predictive signals) ──
  tertiary: "#a78bfa"
  on-tertiary: "#ffffff"
  tertiary-container: "rgba(167,139,250,0.07)"
  on-tertiary-container: "#a78bfa"

  # ── Semantic status (traffic-light set, used sparingly) ──
  error: "#f87171"
  on-error: "#03080f"
  error-container: "rgba(248,113,113,0.07)"
  on-error-container: "#f87171"
  warning: "#fcd34d"
  warning-container: "rgba(252,211,77,0.07)"
  on-warning: "#03080f"
  success: "#4ade80"
  success-container: "rgba(74,222,128,0.07)"
  cyan: "#22d3ee"

  # ── Kraljic posture palette (strategic procurement quadrants) ──
  kraljic-strategic: "#dc2626"
  kraljic-leverage: "#16a34a"
  kraljic-bottleneck: "#d97706"
  kraljic-non-critical: "#64748b"

  # ── Phase / timeline palette ──
  phase-foundation: "#1d4ed8"
  phase-execution: "#d97706"
  phase-optimization: "#16a34a"

  # ── Border states ──
  border-structural: "rgba(96,165,250,0.08)"
  border-active: "rgba(96,165,250,0.18)"
  border-selected: "rgba(96,165,250,0.35)"
  border-focus: "rgba(59,130,246,0.60)"

typography:
  # Display — DM Serif Display only, for hero wordmark & large score numerals
  display:
    fontFamily: "DM Serif Display, Georgia, serif"
    fontSize: "3rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "-0.02em"

  hero-title:
    fontFamily: "DM Serif Display, Georgia, serif"
    fontSize: "2.6rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "-0.02em"

  section-heading:
    fontFamily: "DM Serif Display, Georgia, serif"
    fontSize: "1.1rem"
    fontWeight: "400"
    lineHeight: "1.3"
    letterSpacing: "-0.01em"

  # Body — Inter for all descriptive prose
  body-lg:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.9rem"
    fontWeight: "400"
    lineHeight: "1.6"

  body-md:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: "400"
    lineHeight: "1.5"

  body-sm:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: "400"
    lineHeight: "1.62"

  # Data — JetBrains Mono for all labels, numbers, metadata, eyebrows
  metric-num:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: "1.9rem"
    fontWeight: "700"
    lineHeight: "1.1"
    letterSpacing: "-0.02em"

  label-lg:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: "0.75rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.08em"

  label-md:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: "0.68rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.12em"

  label-sm:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: "0.62rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.16em"

  eyebrow:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: "0.6rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.2em"
    textTransform: "uppercase"

  badge:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: "0.58rem"
    fontWeight: "700"
    lineHeight: "1"
    letterSpacing: "0.14em"
    textTransform: "uppercase"

rounded:
  sm: 6px
  DEFAULT: 6px
  md: 10px
  lg: 14px
  xl: 20px
  full: 9999px

spacing:
  unit: 8px
  xs: 0.3rem
  sm: 0.6rem
  md: 1rem
  lg: 1.4rem
  xl: 2rem
  container-x: 1.6rem
  container-y: 0.8rem
  card-padding: 1.1rem
  card-padding-lg: 1.4rem
  hero-padding-x: 2.2rem
  hero-padding-y: 2rem
  section-gap: 1rem
  component-gap: 0.6rem

elevation:
  sm: "0 1px 4px rgba(0,0,0,0.50)"
  md: "0 4px 16px rgba(0,0,0,0.60)"
  lg: "0 12px 40px rgba(0,0,0,0.70)"
  glow: "0 0 0 3px rgba(96,165,250,0.18)"
  focus-ring: "0 0 0 3px rgba(59,130,246,0.12)"
  hover-lift: "0 20px 40px rgba(0,0,0,0.50), 0 0 30px rgba(96,165,250,0.05)"
  blue-halo: "0 0 24px rgba(59,130,246,0.35)"
  slider-thumb: "0 0 8px rgba(59,130,246,0.40)"

motion:
  fast: "150ms ease"
  med: "250ms ease"
  slow: "400ms ease"
  x-slow: "700ms ease"
  easing-out: "ease-out"
  fade-up: "opacity 0→1 + translateY(14px→0), 0.4s ease"
  fade-in: "opacity 0→1, 0.3s ease"
  assemble-in: "scale(0.97)+translateY(8px) → scale(1)+translateY(0), 0.7s ease"
  pulse-green: "box-shadow pulse, 2s infinite"
  pulse-blue: "glow pulse, 2s infinite"
  draw-bar: "width 0→target, 0.5–0.8s ease-out"

components:
  metric-card:
    backgroundColor: "{colors.surface-container-low}"
    borderColor: "{colors.border-structural}"
    rounded: "{rounded.md}"
    padding: "{spacing.card-padding}"
    transition: "{motion.fast}"

  metric-card-hover:
    borderColor: "{colors.border-active}"
    backgroundColor: "{colors.surface-container}"

  exec-card:
    backgroundColor: "{colors.surface-container-low}"
    borderColor: "{colors.border-structural}"
    rounded: "{rounded.md}"
    padding: "1.2rem"
    transition: "{motion.fast}"

  hero:
    background: "linear-gradient(135deg, #04090f 0%, #060f1a 60%, #091828 100%)"
    borderColor: "{colors.border-structural}"
    rounded: "{rounded.lg}"
    padding: "{spacing.hero-padding-y} {spacing.hero-padding-x}"

  control-panel:
    backgroundColor: "{colors.surface-container-lowest}"
    borderColor: "{colors.border-structural}"
    rounded: "{rounded.lg}"
    padding: "1rem 0.9rem"

  pillar-card:
    backgroundColor: "{colors.surface-container-low}"
    borderColor: "{colors.border-structural}"
    rounded: "{rounded.lg}"
    padding: "1.2rem 1.4rem"
    transition: "{motion.med}"

  pillar-card-hover:
    borderColor: "{colors.border-active}"
    boxShadow: "{elevation.hover-lift}"

  button-primary:
    backgroundColor: "{colors.primary-dim}"
    borderColor: "{colors.primary}"
    textColor: "#ffffff"
    typography: "{typography.label-lg}"
    rounded: "{rounded.sm}"
    transition: "{motion.fast}"

  button-primary-hover:
    backgroundColor: "{colors.primary}"
    boxShadow: "{elevation.blue-halo}"

  input-field:
    backgroundColor: "#060f20"
    borderColor: "rgba(96,165,250,0.18)"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"

  input-focus:
    borderColor: "{colors.primary}"
    boxShadow: "{elevation.focus-ring}"

  badge-pill:
    backgroundColor: "{colors.primary-fixed}"
    borderColor: "rgba(96,165,250,0.22)"
    textColor: "{colors.primary-bright}"
    typography: "{typography.badge}"
    rounded: "{rounded.full}"
    padding: "0.1rem 0.45rem"

  stakeholder-pill:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.border-active}"
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.full}"
    padding: "0.25rem 0.6rem"
    fontSize: "0.76rem"

  ai-governance-banner:
    backgroundColor: "rgba(59,130,246,0.08)"
    borderLeft: "4px solid #3b82f6"
    rounded: "0 {rounded.sm} {rounded.sm} 0"
    labelColor: "{colors.primary}"
    labelTypography: "{typography.eyebrow}"
    bodyColor: "{colors.on-surface-variant}"
    bodyTypography: "{typography.body-sm}"

  sync-badge-green:
    backgroundColor: "{colors.success-container}"
    borderColor: "rgba(74,222,128,0.25)"
    textColor: "{colors.success}"
    typography: "{typography.badge}"
    rounded: "{rounded.sm}"
    animation: "{motion.pulse-green}"

  sync-badge-amber:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    typography: "{typography.badge}"
    rounded: "{rounded.sm}"

  cover-cta:
    backgroundColor: "rgba(29,78,216,0.15)"
    borderColor: "rgba(96,165,250,0.25)"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    transition: "{motion.med}"

  cover-cta-hover:
    backgroundColor: "{colors.primary-dim}"
    borderColor: "{colors.primary-bright}"
    boxShadow: "0 0 28px rgba(59,130,246,0.35)"
    textColor: "#ffffff"
---

## Brand & Style

ProcureIQ is a dark-mode-only enterprise procurement intelligence tool. Its visual language reads as a **command-center terminal** — not a consumer app. Every surface is a deep navy-black; the single accent color is electric blue. The emotional register is precision, authority, and controlled urgency: the same feeling as a Bloomberg terminal or a mission-operations dashboard.

The design achieves its identity through extreme restraint: one accent color (blue), three semantic colors used only for status signals (green/amber/red), and a three-font stack where each typeface has a strict, non-overlapping role. Decorative chrome is minimal. Animation is fast and purposeful. Whitespace is tight because the app is data-dense.

The intended audience is procurement professionals (CPOs, category managers, sourcing analysts) who judge software by how quickly it surfaces the right number. Aesthetic warmth is deprioritized in favor of legibility, data density, and professional credibility.

## Colors

The palette is built on a five-stop depth ramp of near-black navy blues (`#03080f` → `#162236`). No surface is pure black; every layer carries a faint blue tint that ties the entire depth stack to the primary accent. This creates cohesion — the page feels monochromatic and intentional rather than arbitrary.

**Blue is the only accent.** It appears in three intensities:
- `#1d4ed8` (dim) — active button fills, progress gradients
- `#3b82f6` (base) — borders on focus, slider tracks, eyebrow labels
- `#60a5fa` (glow) — metric numbers, interactive highlights, hover borders

**Traffic-light semantics** are used strictly and sparingly:
- Green (`#4ade80`) — positive recommendation, award, ESG pass
- Amber (`#fcd34d`) — bottleneck risk, caution, pending
- Red (`#f87171`) — execution risk, error, Strategic (high-stakes) posture

**Kraljic posture** colors map directly to the four strategic procurement quadrants: Strategic (red), Leverage (green), Bottleneck (amber), Non-Critical (slate). These appear as border accents and badges on supplier scorecards and never as background fills.

The **AI governance banner** always renders as a blue left-border card with a monospaced "AI-Generated Analysis" eyebrow. This is a deliberate design choice — blue signals information, not warning, maintaining trust without creating alarm.

## Typography

Three typefaces, strictly partitioned by role:

**DM Serif Display** — used exclusively for hero wordmarks, section display headings, and large score numerals that need editorial weight. It signals gravitas and differentiates ProcureIQ's brand voice from the data layer. It is never used for labels, body copy, or anything below ~1rem.

**Inter** — the invisible workhorse for all descriptive prose, explanatory text, and AI-generated narrative. Neutral and functional. Used at `0.82–0.9rem` with `1.5–1.62` line height for comfortable reading density.

**JetBrains Mono** — the dominant interface typeface for everything that is *data*: all eyebrows, all card labels, all widget labels (selectbox, slider, input), all metric numbers, all badges, tab labels, and the right control panel. Mono creates a consistent "instrument readout" feel across every data surface. Letter spacing is pushed wide (0.12–0.22em) on uppercase labels to maximize legibility at tiny sizes.

Widget labels (Streamlit inputs) are overridden to monospace + uppercase + wide letter-spacing. This means the form UI reads as a cockpit panel, not a standard web form — consistent with the command-center metaphor.

## Layout & Spacing

The layout uses a **two-column split**: a wide main content area (~76%) and a narrow right control panel (~24%) that is always visible. There is no sidebar. The right panel contains all Kraljic/category/supplier controls and stays sticky while the user navigates tabs in the main area.

Content is organized into **10 sequential tabs** (Overview → Intake → Suppliers → Market → Stakeholders → Strategy → Negotiate → Award Brief → Comms → Spend Intel). The tab strip uses monospace labels styled as terminal commands.

Spacing rhythm is tight-but-breathable:
- Container padding: `0.8rem` vertical, `1.6rem` horizontal (max-width 100%)
- Cards: `1rem–1.2rem` padding, `0.6rem` gap between siblings
- Hero sections: `2rem × 2.2rem` padding — the only generous breathing room
- Section gaps: `1rem` — deliberately compact to maximize visible data

An 8px base unit underlies all spacing decisions.

## Elevation & Depth

Depth is not achieved through shadows alone — it is achieved through the **surface color ramp**. Moving from `#03080f` (page) → `#060d1a` (surface) → `#0a1628` (container) → `#0f1f38` (raised) creates a perceivable Z-axis entirely through color.

Shadows are high-opacity and dark:
- Small: `0 1px 4px rgba(0,0,0,0.50)` — subtle card lift
- Medium: `0 4px 16px rgba(0,0,0,0.60)` — modal tray
- Large: `0 12px 40px rgba(0,0,0,0.70)` — fullscreen overlays

The **blue glow shadow** (`0 0 0 3px rgba(96,165,250,0.18)`) is used for focus rings and the "recommended supplier" highlight state. It is the only shadow with color — everything else is dark. This makes focus states feel electric without being garish.

Borders serve as the primary depth separator: structural borders are `rgba(96,165,250,0.08)` (barely visible, just enough to separate layers), active/hover borders are `rgba(96,165,250,0.18)`, and selected states use `rgba(96,165,250,0.35)`.

## Shapes

The radius scale is conservative and professional:
- `6px` (sm) — form inputs, buttons, small badges. Just enough to avoid harsh corners.
- `10px` (md) — metric cards, exec-summary cards, data panels. The default card radius.
- `14px` (lg) — hero containers, control panel, pillar cards. Larger grouping containers.
- `20px` (xl) — onboarding modal, cover screen. Prominent featured surfaces.
- `9999px` (full) — weight-recommendation pills, stakeholder pills, sync status badges.

The shape language is deliberate restraint: cards feel solid and rectilinear, not bubbly. Pills are reserved for small inline badges and status indicators — they never appear on primary CTAs.

## Motion

All animation durations and purposes are strictly defined:

| Token | Value | Use |
|---|---|---|
| fast | 150ms ease | Tab hover, button hover state changes |
| med | 250ms ease | Pillar card hover, expander open |
| slow | 400ms ease | Metric card fade-up on mount |
| x-slow | 700ms ease | Cover screen assemble-in, modal entrance |

Entry animations use `fadeUp` (opacity + translateY 14px) universally. This gives the page a sense of assembling from a data stream, consistent with the terminal metaphor. The cover splash screen uses `assembleIn` (scale from 0.97) for a more cinematic reveal.

`pulseGreen` and `pulseBlue` are looping keyframe animations used only on live-sync status indicators — they signal that data is actively streaming, not static. They are never used decoratively.

Progress bars use `drawBar` (width 0 → target value) with a staggered delay so bars "fill in" sequentially, making the scoring comparison feel like a calculation completing in real time.

## Components

### Hero Section
The hero is a `linear-gradient(135deg)` from near-black to slightly less dark navy, with a `320×320px` radial blue glow orb top-right (via `::before` pseudo-element). This orb is always `rgba(59,130,246,0.08)` — barely perceptible — and reinforces the blue-tinted brand without competing with content. The DM Serif Display headline sits over a monospace eyebrow set in blue.

### Control Panel
The right panel uses `#040b16` (darkest surface), creating maximum contrast against the main content area. The panel header is monospaced, uppercase, with wide letter-spacing. All widget labels inside the panel are monospace uppercase — turning a Streamlit form into a procurement instrument panel.

### Metric Cards
Five-metric executive strips appear in the Overview tab. Each card has a monospace number in `#60a5fa` (blue-glow) and an uppercase monospace label in `#334155` (dim). On hover, the border brightens from structural to active. Cards animate in with staggered `fadeUp`.

### Score Badges & Pills
Weight-recommendation badges are blue pills (`rgba(96,165,250,0.08)` fill, `rgba(96,165,250,0.22)` border). Supplier status badges (sync, diversity, ESG) use the semantic color set with matching background fills at 7–8% opacity. Stakeholder pills use the active border to make them feel interactive even when read-only.

### AI Governance Banner
Every AI-generated output is preceded by a blue left-border banner. The eyebrow text reads "AI-Generated Analysis" in JetBrains Mono, uppercase, at 0.65rem. This is a non-negotiable component — it appears on all Claude-streamed responses across all tabs. The blue color is deliberate: informational, not alarming.

### Buttons
Primary buttons use `#1d4ed8` fill with `#3b82f6` border. On hover, the fill steps up to `#3b82f6` and a blue halo shadow (`0 0 24px rgba(59,130,246,0.35)`) pulses out. Button labels are always JetBrains Mono, uppercase, `0.72rem`, `0.1em` letter-spacing. Secondary/ghost buttons use transparent fills with structural borders.

### Data Tables (Print / Export)
The executive one-pager HTML export uses a separate light-mode design: `#1e293b` body text on white, `#1d4ed8` section headers, `#f1f5f9` table headers, and the same Kraljic badge colors expressed as `{color}22` background fills (8% opacity tint of the posture color). This is the only surface in the product that is not dark-mode.
