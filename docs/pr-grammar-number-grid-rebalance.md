Title: Grammar UI: Number grid 2x2 + Translation height rebalance

- Changes the “Number” group from a 3×1 stack to a 2×2 grid:
  - Row 0: Singular (c0), Plural (c1)
  - Row 1: Unknown (c0), spacer (c1)
  - Two columns with weights (0..1), radios left-aligned.
- Reclaims ~10% height from the Meanings box and gives it to the Darpan Translation box:
  - Meanings: ≥8 “lines” equivalent, with guard for small windows (if ≤10 lines, keep at least m-1).
  - Translation: increased by the reclaimed amount, clamped to a reasonable max.
- Keeps main content area expanding and the bottom action bar non-expanding, taskbar-safe via `BOTTOM_PAD`.

Verification checklist

- Number group shows a 2×2 layout, radios left-aligned.
- Translation box visibly taller; Meanings box ~10% shorter (but ≥8 lines).
- No overlaps at 100–200% DPI; bottom buttons remain taskbar-safe with WindowManager/F11 logic.

Screenshots

- Before: docs/screenshots/verse_user_input_grammar_before.png
- After:  docs/screenshots/verse_user_input_grammar_after.png

Notes

- If the existing “after” screenshot predates this change, replace it with a fresh capture:
  1) Build and launch the app.
  2) Open the Grammar modal (verse or ABW mode).
  3) Capture the visible window (ensure 100–200% DPI looks good).
  4) Save as the paths above and commit to this branch.

