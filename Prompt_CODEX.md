---

# Prompt: Axioms T4 — Prompt Builder Preview (additive only)

**Context & constraints**

* Target file: `1.1.0_birha.py` only. Do **not** touch `1.1.0_birha_pre_Axiom.py`.
* **Additive-only**: no edits/renames to pre-Axiom functions; wrap where needed.
* Build on T0–T3 already merged:

  * `AxiomsDashboard` (T1), `AxiomsVerseInputFlow` (T2),
  * `AxiomsTranslationChoiceView` (T3) with `_placeholder_continue` wrapper in place.

**Goal**

After the T3 screen, show a **Prompt Builder** view that composes a structured, copyable prompt for ChatGPT based on:

* The reviewed verse selection (primary verse, related suggestions, consecutive verses),
* The user’s **translation choice**:

  * Use predefined **Darpan** translation (preview was shown in T3), or
  * Use **own literal translation** typed in T3.

Provide working buttons:

* **Copy Prompt**: copies the generated prompt to clipboard (best-effort).
* **Save Draft**: stores an in-memory draft (UI phase only; persistence arrives in T5).
* **Back**: returns to T3.
* **Cancel**: closes the Axioms dashboard window.

---

## What to implement (all additive)

### 1) New class: `AxiomsPromptBuilderView` (tk.Frame)

Insert under a new header:

```python
# === Axioms T4: Prompt Builder Preview (additive only) ===
```

**Responsibilities & UI:**

* Header: “Prompt Builder (Preview)”.
* Summary panel (read-only labels) showing:

  * Primary verse (one line wraplength ~760),
  * Related verses (use the existing review bullet text string from T2; show as label with wrap),
  * Consecutive verses choice (string from T2 review).
  * Translation mode: “Darpan” or “Own literal”.
* Prompt preview area:

  * A `tk.Text` (read-only state) containing the final prompt string.
  * “Regenerate” button to rebuild text if upstream state is ever refreshed.
* Action bar:

  * **Back** → show the T3 view again.
  * **Cancel** → call the same cancel as other flows (close dashboard).
  * **Copy Prompt** → tries `pyperclip.copy()`, else selects text and shows info message.
  * **Save Draft** → append a dict to `dashboard._axioms_drafts` (create list lazily). Each draft dict should include:

    * `created_at` (datetime.now())
    * `verse`, `related_summ`, `consecutive_summ`, `translation_mode` (“darpan”|“own”)
    * `own_text` (if any)
    * `prompt_text` (the generated text)

**Public API:**

* `prepare(flow, verse, related_summary, consecutive_summary, translation_mode, own_text, darpan_preview_text)`

  * Stores params and calls `_regenerate_prompt()`.
* `_regenerate_prompt()` builds the preview string using the template below and inserts it into the Text widget (read-only afterwards).

**Prompt template (exact sections, friendly but deterministic):**

```
Title: Derive a SGGS Axiom from the provided verse(s)

Primary verse:
<the verse>

Related verses (if any):
<bullet lines as received from T2 review; otherwise "None">

Consecutive verses:
<e.g., "Including 2 consecutive verse(s)" or "Not including consecutive verses.">

Translation source:
<"Darpan (predefined)" or "Own literal analysis">

Translation text:
<if "darpan": use the Darpan preview text passed from T3; if "own": use user's own text from T3>

Task:
Using only the translation text above, identify a single precise Axiom (short, declarative), and explain briefly (2–4 sentences) how the verse supports this Axiom. Avoid paraphrasing the verse; focus on the core principle.

Output format:
AXIOM: <one-line axiom>
RATIONALE: <2–4 sentences>

Notes:
- If multiple principles are present, pick the primary one most strongly supported by the verse.
- Keep neutral tone; avoid sectarian claims or historical speculation.
```

### 2) Wire from T3 → T4 (safe wrapper; no edits)

* In T3, `AxiomsTranslationChoiceView._proceed_choice` currently shows an info box.
* Add an **additive wrapper** (like T3 did for T2) to capture:

  * Review strings on `flow`: `review_verse_var`, `review_suggestions_var`, `review_consecutive_var`.
  * The selected mode: `choice_var.get()` ∈ {`"darpan"`, `"own"`}
  * The user’s own translation: `own_text.get("1.0", tk.END)` when mode is `"own"`.
  * The Darpan preview text used in T3: pull from the T3 view instance if available; if not, pass the static sample already stored there.
* Create or reuse a single `AxiomsPromptBuilderView` instance stored on `flow` as `_axioms_t4_builder_view`.
* Call `.prepare(...)` with gathered values, then show it (swap frame like T2/T3 do).
* **Back** from T4 should display the T3 view again (no new instances needed).

### 3) In-memory Drafts container (UI-only)

* On the `AxiomsDashboard` or on the `flow` (prefer `dashboard`): attach `dashboard._axioms_drafts: list` lazily (if not present).
* “Save Draft” should:

  * Append the dict described above.
  * Show `messagebox.showinfo("Draft Saved", "...")`.
* No file I/O in T4 (persistence is T5).

### 4) Robustness requirements

* Every UI callback (`copy`, `save`, `back`, `cancel`) must be `try/except` protected to prevent crashes.
* The preview Text must be set to `state=tk.NORMAL` to insert, then restored to `state=tk.DISABLED`.
* Clipboard copy:

  * Prefer `pyperclip.copy(prompt)`.
  * On failure, select all text in the Text box and show a message like “Couldn’t access clipboard; the prompt is highlighted—press Ctrl+C to copy.”

---

## Acceptance criteria (mirror the contract)

* From T3, pressing **Proceed** shows **Prompt Builder (Preview)**.
* Prompt contains all sections and reflects the translation choice (Darpan vs Own).
* **Copy Prompt** works (pyperclip or fallback).
* **Save Draft** stores an in-memory draft without errors.
* **Back** returns to T3; **Cancel** closes the Axioms dashboard.
* `python -m py_compile 1.1.0_birha.py` passes.

---

## Implementation notes / anchors

* Header tag: `# === Axioms T4: Prompt Builder Preview (additive only) ===`
* New class: `AxiomsPromptBuilderView(tk.Frame)`
* Additive wrapper that replaces `AxiomsTranslationChoiceView._proceed_choice` similar to how T3 wrapped T2:

  * Gather data from `flow` vars: `review_verse_var`, `review_suggestions_var`, `review_consecutive_var`.
  * Gather choice from `self.choice_var` and own text via `_get_own_translation()` (already present).
  * Darpan preview text: read from the T3 view’s `self.darpan_text` (via `"1.0","end-1c"` while temporarily enabling) or reuse its `_DARPAN_SAMPLE`.

**Do not** modify existing pre-Axiom functions or any non-Axioms modules.

---

## Quick test script (manual)

1. Launch app → Welcome → **Axioms (beta)**.
2. Verse Analysis → enter any verse → Find Related → pick 2–3 → Include consecutive verses = 2 → Next.
3. Review → Continue → Translation Choice.
4. Pick **Darpan**, then **Proceed** → Prompt Builder appears with sections & Darpan text.

   * Click **Copy Prompt** (expect success or fallback message).
   * Click **Save Draft** (expect “Draft Saved”).
   * Click **Back** (returns to T3), then pick **Own**, type some text, **Proceed** → preview shows own text.
5. **Cancel** closes the Axioms window.

---

## Commit format

Commit subject:
`[Axioms T4] Add Prompt Builder Preview (copy + save draft, additive only)`

Branch: `task/t4-axioms-prompt-builder`

---
