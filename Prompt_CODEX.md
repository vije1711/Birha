
---

### Prompt text for **Prompt_CODEX.md**

> **Task – Fix Translation Choice view vertical overflow (Axioms T3)**
>
> Context:
>
> * Repo: **Birha**.
> * Main file: `1.1.0_birha.py`.
> * Axioms flows are implemented as additive tasks T0–T13.
> * The **Translation Choice** screen lives in `AxiomsTranslationChoiceView` (Task T3) and is reached via:
>
>   1. Launch **Axioms (beta)** from the Welcome dashboard
>   2. Click **Axiom via Verse Analysis**
>   3. Enter a verse → **Find Related** → **Next** → Translation Choice.
>
> **Problem statement**
> On a typical laptop resolution (1366×768), with the Axioms Dashboard window maximized, the **Translation Choice** view is **too tall**:
>
> * The main header, “Primary verse / Related verses / Consecutive verses” summary, and the “Use predefined Darpan translation” block consume most of the vertical space.
> * The bottom section (“Perform own literal translation” + its text area) and especially the **Back / Cancel / Proceed** button bar are **partially or completely off-screen**.
> * Because the Toplevel uses static `pack` layout with no scroll container, the user cannot reach those controls without manually resizing the window, which violates the usability expectation in the Axioms engineering contract (all primary actions must be reachable on 1366×768 when maximized).
>
> **What to change**
>
> * Work only inside **`AxiomsTranslationChoiceView`** in `1.1.0_birha.py` and make **minimal, layout-focused changes** to:
>
>   * Ensure the entire Translation Choice view (including the “Perform own literal translation” area and the Back/Cancel/Proceed buttons) fits comfortably within a maximized 1366×768 window.
>   * Prefer reducing vertical spacing and widget heights to adding scrollbars, unless a simple scrollable container is clearly safer.
> * Examples of acceptable adjustments (use your judgment and test visually):
>
>   * Reduce `pady` for the header and summary sections.
>   * Reduce `height` of the Darpan and own-translation `Text` widgets (e.g., from 8 lines down to 5–6).
>   * Slightly tighten padding around option frames and button bar.
> * Do **not**:
>
>   * Change WindowManager behavior for the Axioms window globally.
>   * Change fonts or colors.
>   * Break existing logic for radio buttons, enabling/disabling the Proceed button, or how the choice is sent to downstream tasks (T4+).
>
> **Constraints**
>
> * Keep the work fully **additive / layout-safe**: only modify Axioms T3 view; no changes to pre-Axioms code paths.
> * Respect the intentions and style described in
>   **`0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`** (especially around Axioms screens being readable and usable on standard laptop resolutions).
> * Run `python -m py_compile 1.1.0_birha.py` after changes.
>
> **Definition of Done**
>
> * On a 1366×768 test window (maximized), the Translation Choice view:
>
>   * Shows the **entire** summary section, both translation options, and the **Back / Cancel / Proceed** buttons without clipping.
>   * Still looks visually balanced and consistent with the rest of the Axioms UI.
> * No regressions to T2, T4, or later Axioms tasks.

---
