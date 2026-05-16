---
name: Medis Ether Design
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#3d4946'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f0f1f1'
  outline: '#6d7a77'
  outline-variant: '#bcc9c5'
  surface-tint: '#006b5f'
  primary: '#00685d'
  on-primary: '#ffffff'
  primary-container: '#008376'
  on-primary-container: '#f4fffb'
  inverse-primary: '#70d8c8'
  secondary: '#4555b7'
  on-secondary: '#ffffff'
  secondary-container: '#8999ff'
  on-secondary-container: '#182a8e'
  tertiary: '#8a30b0'
  on-tertiary: '#ffffff'
  tertiary-container: '#a54dcc'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#8df5e4'
  primary-fixed-dim: '#70d8c8'
  on-primary-fixed: '#00201c'
  on-primary-fixed-variant: '#005048'
  secondary-fixed: '#dee0ff'
  secondary-fixed-dim: '#bbc3ff'
  on-secondary-fixed: '#000e5e'
  on-secondary-fixed-variant: '#2c3c9e'
  tertiary-fixed: '#f8d8ff'
  tertiary-fixed-dim: '#ebb2ff'
  on-tertiary-fixed: '#320047'
  on-tertiary-fixed-variant: '#721199'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
  active-green: '#43A047'
  completed-gray: '#9E9E9E'
  error-red: '#B00020'
  warning-orange: '#E65100'
  glass-surface: rgba(255, 255, 255, 0.7)
  glass-border: rgba(255, 255, 255, 0.4)
typography:
  display-hero:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-page: 40px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
  container-padding: 24px
---

## Brand & Style
The design system for this health management platform is built on the philosophy of **"Luminous Clarity."** It aims to transform the often clinical and stressful experience of medical management into one of calm, ethereal precision. The brand personality is empathetic yet authoritative, combining the trustworthiness of a medical professional with the modern ease of a high-end consumer lifestyle app.

The primary aesthetic is **Glassmorphism**, utilized not just for visual flair but to create a sense of depth and focus within a complex data environment. By using frosted glass effects and soft blurred backgrounds, the UI achieves a "light-as-air" feel that prevents information density from becoming overwhelming. This is paired with **Minimalism** to ensure that critical health data remains the focal point, using generous negative space and a refined typographic hierarchy to guide the user’s eye.

## Colors
This design system utilizes a sophisticated palette centered around medical and technological cues.

- **Primary (Teal):** Used for main actions, active navigation states, and core health-related branding. It evokes cleanliness and professional care.
- **Secondary (Indigo):** Reserved for secondary actions and structural elements, providing a grounded contrast to the teal.
- **Tertiary (Purple):** Specifically designated for AI-driven insights, machine-generated suggestions, and advanced metrics to distinguish them from user-entered data.
- **Status Colors:** These are functionally rigid. **Green** is exclusively for active statuses, **Gray** for completed tasks, and **Red** for expired or urgent medical alerts.

The color system relies heavily on **translucency**. Surface containers should utilize the `glass-surface` token with a backdrop-filter blur of 12px to 20px, ensuring the underlying brand gradients softly peak through without compromising readability.

## Typography
The typography system uses **Inter** to deliver a modern, neutral, and highly legible experience across all data densities. 

- **Weight Usage:** Use Bold (700) for primary headers to establish strong anchoring. Semi-bold (600) is used for component-level headers and buttons to maintain visibility against frosted backgrounds.
- **Readability:** For data tables and medical lists, `body-sm` is the standard to allow for high information density while maintaining a clean look.
- **Letter Spacing:** Headlines utilize slight negative tracking to feel more "designed" and tight, while labels use expanded tracking (0.05em) for clarity at small sizes.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid Grid**. On desktop, a 280px sidebar remains fixed, while the main dashboard area utilizes a fluid 12-column grid with 24px gutters.

- **Modular Dashboard:** Content is organized into "Ether Tiles"—glassmorphic containers that group related health data.
- **Rhythm:** A strict 4px base unit governs all dimensions. Internal component padding should default to 16px (`stack-md`), while section-level spacing should use 32px (`stack-lg`) to maintain the "spacious" requirement.
- **Breakpoints:**
  - **Desktop (1440px+):** Full 12-column grid, expanded sidebar.
  - **Tablet (768px - 1439px):** 8-column grid, sidebar collapses into an icon-only rail.
  - **Mobile (<767px):** 4-column grid, single-column stack, sidebar moves to a bottom navigation bar or hamburger menu.

## Elevation & Depth
Depth in this design system is achieved through **Backdrop Refraction** rather than traditional heavy shadows.

- **Layer 0 (Background):** Soft, organic brand gradients (Teal/Purple) with high Gaussian blur.
- **Layer 1 (Tiles/Cards):** Frosted glass surfaces with a `1px` white border at 40% opacity (`glass-border`). These use a very soft, diffused ambient shadow (Blur 16px, Opacity 4%) to lift them slightly from the background.
- **Layer 2 (Modals/Popovers):** Higher opacity frosted glass with a more pronounced shadow (Blur 32px, Opacity 10%) to indicate immediate priority.
- **Layer 3 (Active Elements):** Elements like active "Quick Action Tiles" use a slight inner glow and a vibrant primary border to signal interaction.

## Shapes
The shape language is defined by **Soft Continuity**. 

- **Standard Containers:** Use `rounded-2xl` (16px) for cards and tiles to evoke a friendly, modern feel.
- **Interactive Elements:** Buttons and Input fields use `rounded-lg` (8px) for a more structured, functional appearance.
- **Status Elements:** Chips and pill-style buttons use `rounded-full` to maximize the "tactile" and "friendly" aesthetic.
- **Modals:** Use `rounded-xl` (24px) for large containers to emphasize their role as distinct, temporary surfaces.

## Components

### Navigation
- **Sidebar:** Uses a semi-transparent blur. Active links are indicated by a solid Teal left-accent and a subtle white-glass background tint.
- **Breadcrumbs:** Small-caps `label-md` style for secondary navigation within deep health records.

### Quick Action Tiles
- Square tiles with `rounded-2xl` corners.
- Icons are centered, utilizing the `color-primary` with a 10% opacity background circle of the same color.
- Hover state: The background blur increases, and the border opacity rises to 80%.

### Health Stats & Data Tables
- **Stats:** Large numeric displays using `headline-lg` with a supporting `label-md` descriptor underneath.
- **Tables:** No vertical borders. Horizontal dividers are `1px` white at 10% opacity. Row headers use `headline-sm` for drug names or metric titles.

### Buttons & Inputs
- **Primary Button:** Solid Teal (`color-primary`) with white text. High-contrast and shadowless to maintain the flat glass look.
- **Input Fields:** Ghost-style with a `glass-border` and a soft background blur. On focus, the border transitions to a `2px` solid Teal.

### AI Badges
- Utilizing the Tertiary Purple, these badges indicate machine-learned health trends. They should feature a subtle "shimmer" animation to denote active processing or intelligence.