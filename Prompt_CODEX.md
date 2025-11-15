
---

# **Problem Statement for Codex CLI — Verse Summary Bug**

Codex, something interesting is happening inside `1.1.0_birha.py`.

When the user selects a verse → chooses consecutive verses → reaches the **Summary Dialog (Task 13)**, the *Verse Summary* textbox shows *correct Gurmukhi text*, but individual verse fragments are joined using **slashes (`/`)**, creating duplicates and breaking readability. The user wants **one continuous clean line** containing all consecutive fragments, *without inserting slashes or separators unless they originally existed in the SGGS database*.

Here is the unexpected output pattern:

```
ਬਿਨੁ ਗੁਰ ਗਿਆਨੁ ... ਹੋਇ ॥ / ਤਰਤਿ ਵਰਤਣੁ ... ਹੋਇ ॥ / ਨਾਨਕ ਸਭਦੇ ... ਹੋਇ ॥
```

But the desired output is:

```
ਬਿਨੁ ਗੁਰ ਗਿਆਨੁ ... ਹੋਇ ॥ ਤਰਤਿ ਵਰਤਣੁ ... ਹੋਇ ॥ ਨਾਨਕ ਸਭਦੇ ... ਹੋਇ ॥
```

So the UI is correct; the database is correct; the issue is that **some helper inside Tasks 11–12 is artificially stitching consecutive verses using “ / ” instead of natural concatenation**.

Your objective:

1. **Locate EXACTLY which helper builds the combined Verse Summary string** (likely the T12 builder `_axioms_t12_build_verse_summary(...)` or another join helper in the T11/T12 pipeline).
2. **Understand why it injects “ / ” even though the SGGS source lines are independent and already end with a `॥` delimiter.**
3. **Refactor so consecutive fragments join naturally** – preserving original SGGS punctuation, spacing, and Gurmukhi structure — with *no artificial slash separators*.
4. Ensure the fix is fully **Unicode-safe**, **Tkinter-safe**, and **compatible with both WSL and Windows fonts**.

---

## **The intriguing question for you, Codex:**

**Why is the UI showing correct Gurmukhi rendering everywhere else,
but only the internal string-builder for Axioms Summary insists on adding slashes —
even though no other part of the system uses `/` as a verse delimiter?**

Find the hidden cause, fix it cleanly, and rewrite the summary builder in the correct SGGS-aware way.

---

## **Final instruction**

**Study both files directly:**

* `1.1.0_birha.py`
* `1.1.0_birha_pre_Axiom.py`

and update the main file so that the Axioms Verse Summary is built correctly without slashes.
Do not modify any Literal Translation or Word Analysis modules.
Do not break any existing Axioms UI flows (Tasks 1–13).
Ensure the change is strictly additive or localized.

**Codex — do the rest.**
