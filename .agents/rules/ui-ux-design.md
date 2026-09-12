# UI/UX & Apple Design System Rules

These guidelines are mandatory for all AI agents working on the frontend, styles, and interface components of the Local Document Signer application.

---

## 1. Core Design Philosophy: Apple Design Principles

Interfaces must feel like a natural, physical extension of the user—responsive, calm, predictable, and crafted with restraint.

- **Simplicity over flashiness**: Avoid unnecessary decorative embellishments.
- **Physicality**: Elements should behave like physical objects with direct feedback, elevation, and realistic inertia.
- **Translucent Materials**: Use subtle frosted glass materials (`backdrop-filter`) to establish visual hierarchy without clutter.
- **Restraint & Craft**: Every pixel, margin, border-radius, and font weight must be deliberate and purposeful.

---

## 2. Gradient Policy & Color Palette (STRICT)

### ⛔ Prohibition of Purple / Neon Gradients
- **NEVER introduce purple gradients, neon gradients, or artificial decorative background glows.**
- Backgrounds must remain clean, calm, and solid.
- Do not use decorative dot grids or pattern overlays across the document canvas.

### Color Tokens

#### Light Mode (`:root`)
- **Canvas Background**: `#f5f5f7` (Apple Studio clean neutral)
- **Translucent Chrome (Header/Toolbars)**: `rgba(255, 255, 255, 0.82)` with `backdrop-filter: blur(20px) saturate(180%)`
- **Sidebar Background**: `rgba(250, 250, 252, 0.94)` with `backdrop-filter: blur(24px)`
- **Card / Surface Background**: `#ffffff`
- **Primary Text**: `#1d1d1f`
- **Secondary Text**: `#6e6e73`
- **Tertiary / Muted Text**: `#86868b`
- **Hairline Borders**: `rgba(0, 0, 0, 0.08)` (subtle) to `rgba(0, 0, 0, 0.14)` (medium)
- **Accent Blue**: `#0071e3` (Apple San Francisco Blue)
- **Success Green**: `#34c759`
- **Alert / Error Red**: `#ff3b30`
- **Inks**: `#18181b` (Midnight Black), `#0066cc` (Royal Blue)

#### Dark Mode (`:root[data-theme="dark"]`)
- **Canvas Background**: `#121214`
- **Translucent Chrome**: `rgba(28, 28, 30, 0.85)` with `backdrop-filter: blur(20px) saturate(180%)`
- **Sidebar Background**: `rgba(22, 22, 24, 0.94)` with `backdrop-filter: blur(24px)`
- **Card / Surface Background**: `#1c1c1e`
- **Primary Text**: `#f5f5f7`
- **Secondary Text**: `#a1a1a6`
- **Hairline Borders**: `rgba(255, 255, 255, 0.1)` (subtle) to `rgba(255, 255, 255, 0.16)` (medium)
- **Accent Blue**: `#0a84ff`
- **Success Green**: `#30d158`
- **Alert / Error Red**: `#ff453a`

---

## 3. Typography & Optical Sizing

- **Font Family**:
  ```css
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, system-ui, -system-ui, sans-serif;
  ```
- **Optical Tracking (Letter Spacing)**:
  - Large display and headings: tight negative tracking (`-0.015em` to `-0.02em`).
  - Body text: neutral tracking (`-0.005em` to `0`).
  - Microcopy, labels, and badges: relaxed positive tracking (`+0.01em` to `+0.02em`).
- **Tabular Numerals**: Always apply `font-variant-numeric: tabular-nums` to outputs, zoom percentages, page counters, and widths to prevent layout jitter during updates.

---

## 4. Direct Manipulation & Physical Feedback

- **Instant Pointer-Down Response**:
  All clickable buttons must give immediate tactile feedback upon press:
  ```css
  button:active:not(:disabled) {
    transform: scale(0.96);
    transition: transform 60ms ease-out;
  }
  ```
- **Physical Signature Dragging**:
  - When dragging starts, add `.dragging` and capture pointer events with `setPointerCapture`.
  - Apply physical lift with slight scale and deep drop shadow:
    ```css
    .placed-signature:active,
    .placed-signature.dragging {
      cursor: grabbing;
      transform: scale(1.025);
      filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.2));
      z-index: 25;
    }
    ```
- **Paper Depth**:
  Documents on the stage must have realistic multi-layered physical paper shadows:
  ```css
  --shadow-paper: 0 1px 3px rgba(0, 0, 0, 0.03), 0 8px 24px rgba(0, 0, 0, 0.07), 0 16px 40px rgba(0, 0, 0, 0.04);
  ```

---

## 5. Component Patterns

- **Segmented Controls**:
  - Outer container: recessed pill container (`border-radius: 9px; padding: 3px; background: var(--bg-subtle);`).
  - Active segment: crisp white floating card with subtle shadow (`box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 0.5px 1px rgba(0, 0, 0, 0.06); border-radius: 7px;`).
- **Buttons**:
  - Squircle rounded corners (`border-radius: 8px` to `10px`).
  - Primary button: Apple blue with subtle top inner highlight (`inset 0 1px 0 rgba(255, 255, 255, 0.2)`).
- **Sliders**:
  - Thin clean track (`height: 4px; border-radius: 2px;`).
  - Crisp round white thumb (`width: 20px; height: 20px; border-radius: 50%`) with soft drop shadow.

---

## 6. Accessibility & System Overrides

- **Reduced Motion**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
    button:active:not(:disabled),
    .placed-signature:active,
    .placed-signature.dragging {
      transform: none !important;
    }
  }
  ```
- **Reduced Transparency**:
  ```css
  @media (prefers-reduced-transparency: reduce) {
    .app-header, .sidebar, .document-heading, .document-toolbar, .document-footer {
      backdrop-filter: none !important;
      background: var(--bg-card) !important;
    }
  }
  ```
