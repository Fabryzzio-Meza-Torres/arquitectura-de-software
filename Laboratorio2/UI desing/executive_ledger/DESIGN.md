---
name: Executive Ledger
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45464d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#5c5e68'
  on-secondary: '#ffffff'
  secondary-container: '#dedfeb'
  on-secondary-container: '#60626c'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#e1e2ed'
  secondary-fixed-dim: '#c4c6d1'
  on-secondary-fixed: '#191b24'
  on-secondary-fixed-variant: '#444650'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  data-tabular:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-label:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  grid_columns: '12'
  gutter: 24px
  margin_desktop: 40px
  margin_mobile: 16px
  container_max_width: 1440px
---

## Brand & Style
The design system is engineered for high-stakes B2B financial environments where clarity, speed of data ingestion, and perceived authority are paramount. The brand personality is institutional yet technologically advanced—evoking the reliability of a traditional bank with the efficiency of a modern SaaS platform.

The visual style follows a **Corporate / Modern** aesthetic with elements of **Minimalism**. It prioritizes high information density without sacrificing legibility. The interface utilizes a rigorous alignment system, subtle tonal layering, and high-contrast action states to guide users through complex fiscal workflows. The emotional response should be one of absolute control, precision, and financial security.

## Colors
The palette is anchored by **Deep Navy (#0F172A)**, used for primary navigation and structural headers to establish institutional authority. **Emerald Green (#10B981)** is reserved strictly for positive financial growth, "Success" states, and primary calls to action, creating a psychological link between the platform's tools and capital appreciation.

**Slate Grays** handle the heavy lifting of secondary information and metadata to prevent visual fatigue in data-dense environments. A refined **4-color status system** is implemented to indicate delinquency and risk:
- **Green:** Current / Paid
- **Yellow:** Grace Period / Pending
- **Orange:** Late (1-30 days)
- **Red:** Default / Critical

Use white backgrounds (#FFFFFF) for primary work surfaces and subtle cool grays (#F8FAFC) for secondary containers to maintain a sterile, professional atmosphere.

## Typography
This design system utilizes **Inter** as its primary typeface due to its exceptional legibility in UI and specialized features for numerical data. 

For financial figures and currency callouts, always enable `tnum` (tabular figures) and `lnum` (lining numbers) to ensure that columns of numbers align perfectly for easy scanning. **JetBrains Mono** is used sparingly for technical identifiers, transaction IDs, or code-adjacent data to distinguish them from standard prose.

On mobile devices, `display` and `headline-lg` styles should scale down by 20% to maintain visual hierarchy without overwhelming the viewport.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy on desktop to ensure data tables remain predictable and readable. A 12-column system is used, with 24px gutters providing ample breathing room between dense information blocks.

**Spacing Rhythm:**
- Use a 4px baseline grid.
- **Compact (8px-12px):** Used within components (e.g., label to input field).
- **Default (16px-24px):** Used for padding within cards and between standard elements.
- **Sectional (48px-64px):** Used to separate major functional areas of a page.

On mobile, the grid collapses to 4 columns with 16px margins. Tables should transition to a horizontal scroll or card-stacking model depending on the criticality of the horizontal data comparison.

## Elevation & Depth
Depth is conveyed through **Tonal Layers** and extremely subtle **Ambient Shadows**. This keeps the interface feeling "flat" and efficient rather than decorative.

- **Level 0 (Background):** #F8FAFC (Cool Gray) - The canvas.
- **Level 1 (Cards/Surface):** #FFFFFF (White) - Standard containers for data. These use a 1px border (#E2E8F0) and no shadow.
- **Level 2 (Active/Hover):** #FFFFFF (White) - Elements being interacted with. Apply a soft, diffused shadow: `0 4px 6px -1px rgba(15, 23, 42, 0.1)`.
- **Level 3 (Overlay/Modals):** These use a stronger shadow for separation and a 40% opacity Deep Navy backdrop blur to maintain focus.

Avoid heavy skeuomorphism. Depth should strictly follow the "paper on table" metaphor, where the most important interactive elements sit slightly above the data grid.

## Shapes
The shape language is **Soft** and professional. A standard radius of 4px (0.25rem) is applied to most UI components, including buttons, inputs, and card containers. This provides a modern touch while maintaining the "architectural" feel of a financial tool.

- **Standard Radius:** 4px (Inputs, Buttons, Cards)
- **Large Radius:** 8px (Modals, Large Dashboard Containers)
- **Full Radius:** Used only for status badges and pill-shaped tags to distinguish them from interactive buttons.

## Components
**Data Tables:**
The core of the platform. Use a "Zebra-stripe" alternative or 1px horizontal dividers. Header rows must be fixed (sticky) with a subtle bottom shadow on scroll. Cell padding should be 12px vertical and 16px horizontal for "Comfortable" density, or 8px vertical for "Compact" views.

**Buttons:**
- **Primary:** Deep Navy background, White text.
- **Action/Success:** Emerald Green background, White text.
- **Ghost:** No background, Slate Gray border. Use for secondary actions like "Export" or "Cancel."

**Status Badges:**
Small, pill-shaped indicators using 10% opacity of the status color for the background and 100% opacity for the text. Example: A "Late" badge uses a light orange background with dark orange text.

**Input Fields:**
1px border (#CBD5E1) with a 4px radius. On focus, the border transitions to Deep Navy with a 2px outer "glow" in a light blue tint.

**Progress Indicators:**
For multi-step lease applications, use a "Stepper" component. Completed steps are Emerald Green with a checkmark; the active step is Deep Navy; future steps are Slate Gray.

**Currency Callouts:**
Always include the ISO code (e.g., USD, EUR). Positive values should use Emerald Green; negative values or "amount due" should use Deep Navy or Red depending on the context of the workflow.