### 🧩 **Prompt Title**

Implement Axioms T5 — Local Draft Save/Load (JSON Mock)

---

### 🧠 **Prompt Text (for Prompt_Codex.md)**

Implement **Task T5** of the Axioms Framework in **`1.1.0_birha.py`** under a new section header:
`# === Axioms T5: Local Draft Save/Load (JSON Mock) ===`

#### **Reference**

All behavior, method signatures, and data-handling details must comply with the official engineering document:
📄 **“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx.”**

---

### **Objective**

Extend the `AxiomsPromptBuilderView` (from T4) so that user-saved drafts now persist between sessions by using a lightweight local JSON file (`axioms_drafts.json`) stored in the same directory as `1.1.0_birha.py`.

---

### **Implementation Scope**

#### **1️⃣ Draft Persistence Adapter**

Add helper functions:

* `_axioms_t5_get_draft_path()` → returns the absolute JSON path (same folder as `1.1.0_birha.py`).
* `_axioms_t5_load_drafts()` → loads and returns a list of draft dicts; if file missing/corrupt, returns `[]`.
* `_axioms_t5_save_drafts(drafts)` → writes drafts as JSON (UTF-8, indent 2).
  Guard all file I/O operations with `try/except` so that no UI crashes occur.

---

#### **2️⃣ Dashboard Integration**

Update `AxiomsDashboard` (additively):

* On startup (`__init__`), call `_axioms_t5_load_drafts()` and assign the result to `self._axioms_drafts`.
* Add `save_all_axiom_drafts()` method → calls `_axioms_t5_save_drafts(self._axioms_drafts)` to persist data.
* Ensure drafts auto-save on window close via the existing `WM_DELETE_WINDOW` callback.

---

#### **3️⃣ Prompt Builder Enhancement**

Modify `AxiomsPromptBuilderView._save_draft()`:

* After appending the draft to memory, also write it immediately to disk using `_axioms_t5_save_drafts()`.
* On launch, previously saved drafts should load silently into memory (`dashboard._axioms_drafts`) even if UI list display is not yet implemented.

---

#### **4️⃣ Data Format**

Each draft dict must contain:

```json
{
  "created_at": "2025-10-19T07:45:00",
  "verse": "text…",
  "related_summ": "text…",
  "consecutive_summ": "2",
  "translation_mode": "own|darpan",
  "own_text": "string",
  "prompt_text": "string"
}
```

Use `datetime.now().isoformat(timespec="seconds")` for timestamps.

---

#### **5️⃣ Acceptance Criteria**

* “Save Draft” creates `axioms_drafts.json` if missing and updates it on every save.
* Reopening the app retains previous drafts in memory.
* No exception crashes even if the file is absent or corrupted (reset to empty list gracefully).
* `python -m py_compile 1.1.0_birha.py` must pass.

---

### **Additive Requirements**

* All code must be placed under its own `# === Axioms T5:` header.
* **Do not modify or rename any pre-Axiom code, functions, or strings.**
* Maintain the Axioms Framework’s non-intrusive, wrapper-based architecture.

---

### **Testing Checklist**

1. Launch app → enter Verse Analysis → reach Prompt Builder.
2. Click **Save Draft** → close and relaunch app.
3. Verify `axioms_drafts.json` exists and contains the entry.
4. Confirm previous drafts reload without manual import or error.

---

### **Note**

All naming, method structure, and draft I/O rules must adhere to the **“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx.”**