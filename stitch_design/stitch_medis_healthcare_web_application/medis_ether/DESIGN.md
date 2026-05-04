```markdown
# Design System Document

## 1. Creative North Star: "The Clinical Sanctuary"

This design system transcends the typical "hospital portal" aesthetic. Our North Star is **The Clinical Sanctuary**—a digital environment that balances the rigorous precision of modern Vietnamese healthcare with a sense of serene, editorial calm. 

We move away from the rigid, boxed-in layouts of the past. Instead, we use **Tonal Layering** and **Asymmetric Breathing Room** to guide the eye. We treat the interface not as a series of containers, but as a sequence of high-end editorial surfaces. This approach reduces cognitive load for elderly users while maintaining a premium, authoritative presence that builds immediate trust.

---

## 2. Color & Surface Philosophy

While the core palette is rooted in medical blues, the application of these colors must be sophisticated. We prioritize tonal shifts over structural lines.

### The "No-Line" Rule
Standard 1px borders are strictly prohibited for sectioning. To create separation, use the **Surface Hierarchy**:
- **Background (`#f9f9ff`):** The base canvas.
- **Surface-Container-Low (`#f0f3ff`):** Use for large secondary content areas.
- **Surface-Container-Lowest (`#ffffff`):** Reserved for primary interactive cards, creating a "lifted" effect against the background without needing a stroke.

### Signature Textures & Glass
- **The Gradient Soul:** For hero sections or primary CTAs, use a subtle linear gradient from `primary` (#006193) to `primary_container` (#007bb9) at a 135-degree angle. This adds depth and "medical-grade" polish.
- **Clinical Glass:** For floating navigation or modal overlays, use `surface_container_lowest` at 80% opacity with a `24px` backdrop blur. This ensures the UI feels integrated and airy, rather than heavy and static.

---

## 3. Typography: Editorial Authority

We use a dual-font strategy to balance character with legibility.

- **Display & Headlines (Manrope):** A modern geometric sans-serif with a high x-height. This provides a "designed" feel for large headings.
- **Body & Labels (Inter):** Chosen for its exceptional readability at small sizes and high legibility for elderly users (minimum 14px/`body-md`).

| Token | Font | Size | Intent |
| :--- | :--- | :--- | :--- |
| `display-lg` | Manrope | 3.5rem | Hero statements / Key metrics |
| `headline-md`| Manrope | 1.75rem| Section headers |
| `title-lg`   | Inter | 1.375rem| Card titles / Patient names |
| `body-lg`    | Inter | 1.0rem  | Primary reading text (16px equivalent) |
| `label-md`   | Inter | 0.75rem | Metadata / Captions |

---

## 4. Elevation & Depth: Tonal Layering

Traditional shadows and borders are replaced by **Ambient Depth**.

*   **Layering Principle:** Stack `surface_container_lowest` (White) elements on top of `surface_container_low` (Light Blue-Grey) backgrounds. This "natural lift" is more accessible for aging eyes than low-contrast grey borders.
*   **Ambient Shadows:** For high-priority elements (e.g., a "Book Appointment" floating button), use an extra-diffused shadow: `0px 20px 40px rgba(0, 28, 59, 0.08)`. The tint uses the `on_surface` color rather than black to keep the look clean.
*   **The Ghost Border:** If a boundary is required for accessibility in forms, use `outline_variant` (#bfc7d2) at **20% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons
*   **Primary:** Uses the `primary` to `primary_container` gradient. 
*   **Secondary:** Ghost style using `primary` text on a `primary_fixed` background.
*   **Shape:** `xl` (1.5rem) rounded corners.
*   **Sizing:** All interactive targets must maintain a minimum height of **48px** to ensure accessibility for users with limited motor precision.

### Clinical Cards
*   **Structure:** No borders. Use `surface_container_lowest` background.
*   **Separation:** Use `40px` (or `xl` spacing) of vertical whitespace instead of divider lines.
*   **Nesting:** Small "data chips" inside cards should use `surface_container_high` to create a "recessed" look.

### Input Fields
*   **State:** Default state uses a `surface_container_low` fill. 
*   **Focus:** Transitions to a 2px `surface_tint` bottom-border only, maintaining an editorial, "form-like" feel rather than a boxed-in appearance.
*   **Error:** Use `error` (#ba1a1a) text with a `error_container` soft background fill behind the input.

### Specialized Components: The "Health Timeline"
For patient history, avoid a vertical line. Use a series of `surface_container_highest` vertical blocks of varying widths to create an **intentional asymmetry**, signaling different types of medical events through weight and color rather than a "list" format.

---

## 6. Do’s and Don’ts

### Do:
*   **Use Generous White Space:** Treat space as a functional tool to separate complex medical data.
*   **Layer Surfaces:** Use the `surface` tokens to create depth hierarchy (Lowest > High).
*   **Prioritize Contrast:** Ensure all `on_surface` text meets WCAG AAA standards for the elderly demographic.
*   **Verticality:** Let the content breathe; scrollable layouts are preferred over cramped, "above the fold" thinking.

### Don’t:
*   **Don't Use Dividers:** Never use 1px horizontal lines to separate list items; use background shifts or `24px` spacing.
*   **Don't Use Sharp Corners:** Avoid the `none` or `sm` roundedness tokens; medical environments should feel "soft" and approachable.
*   **Don't Use Pure Black:** Use `on_surface` (#001c3b) for all primary text to maintain a high-end, soft-contrast feel.
*   **Don't Over-Animate:** Use subtle 200ms fades. Avoid jarring "pop" animations that may confuse elderly users. 

---
*This design system is a living document intended to ensure every touchpoint of the platform feels like a premium, clinical, yet human-centric experience.*```