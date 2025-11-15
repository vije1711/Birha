
---

### Task – Translation Choice: compact verse summary card (height-friendly)

**Context**

We’re working in `1.1.0_birha.py` inside the Axioms framework. The “Translation Choice” screen is implemented by `AxiomsTranslationChoiceView`. At the top of this view there is a summary block that shows:

* Primary verse (label bound to `self.verse_label_var`)
* Related verses (label bound to `self.suggestions_var`)
* Consecutive verses (label bound to `self.consecutive_var`)

Below that, we show the two translation options and their text areas, and at the bottom the Back / Cancel / Proceed buttons.

**Problem**

On a typical laptop resolution (for example 1366×768, maximized window), this layout is too tall. The combination of:

* three separate summary rows with generous padding, plus
* Darpan translation text box, plus
* “own literal translation” text box

means the bottom part of the UI (especially the “Perform own literal translation” area and the buttons) is partially or fully off-screen. Users have to resize or move the window to reach the controls, which is not ideal.

**Goal**

Refactor the summary area of `AxiomsTranslationChoiceView` into a **single compact verse-summary card** that:

1. Shows all three pieces of information (primary verse, related verses, consecutive verses) inside one bordered card.
2. Uses less vertical space than the current three-row layout, so that on a 1366×768-style screen the **bottom buttons stay visible** without needing to resize the window.
3. Keeps all existing data flow intact: values still come from `self.verse_label_var`, `self.suggestions_var`, and `self.consecutive_var`.
4. Does **not** change window geometry globally – only layout within this view.

**Requirements**

* Work only in `1.1.0_birha.py`, inside `AxiomsTranslationChoiceView` (and any private helpers for it). Do not touch `1.1.0_birha_pre_Axiom.py` and do not call functions from it.
* Preserve the existing header bar (“Translation Choice”) and the rest of the view (radio buttons, text areas, buttons). Only replace/rework the block that currently builds the three summary labels.
* Implement a new card-like `tk.Frame` (for example: `card = tk.Frame(body, bg="light gray", highlightthickness=1, highlightbackground="#999999")` or similar) that:

  * Shows the **primary verse** on the first line, slightly emphasized (e.g., bold or slightly larger font, or a darker foreground color).
  * Shows **related verses** on the next line, prefixed with a short label like “Related:” but keeping things compact.
  * Shows **consecutive verses info** on a third line if non-empty (otherwise omit or show a short “Not including consecutive verses” text).
  * Uses `wraplength` and small vertical paddings (e.g., `pady=(2, 2)` per label) to minimise height.
* The width of the card should visually align with the translation sections below (i.e., fill the same horizontal region).
* Long text should wrap; if it would still get very tall, you may abbreviate with an ellipsis (e.g., show only the first N characters or first line and append “…”) but keep this logic simple and local.
* Ensure the layout works reasonably at ~1200×700 window size: the verse card, Darpan box, own-translation box, and the buttons should all be reachable without hidden controls.
* Keep styles consistent with the rest of Axioms (fonts, colors already used in this view). No new third-party libraries.

**Contract & references**

* Before coding, **read** the engineering contract file in the workspace named
  `0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`
  and respect all relevant constraints (additive-only behavior, no cross-module reuse, beta labeling, etc.).
* Do not rely on `@filename` shorthand inside this `.md` file – open the `.docx` and `.py` directly from the workspace.
* After changes, run at least `python -m py_compile 1.1.0_birha.py` to ensure there are no syntax errors.

If you need to adjust small paddings (`padx/pady`) in this view to get a clean fit, do so conservatively and only within `AxiomsTranslationChoiceView`.

---
