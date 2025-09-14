Title: Taskbar-safe bottom action bars; deferred exact maximize; consistent padding

Summary
- Anchor action button frames at the bottom across key dialogs and remove excess bottom padding so buttons remain fully visible above the Windows taskbar.
- Switch to deferred, exact per-monitor work-area maximize via WindowManager to avoid 1×1 restore glitches and ensure the client area matches the monitor work area (no fullscreen overlap).
- Ensure the main content uses fill=BOTH, expand=True so content grows instead of pushing buttons off-screen. Scroll areas still fill correctly.

Dialogs updated
- Verse
  - `show_translation_input`
  - `user_input_grammar` (implementation `_user_input_grammar_impl`)
  - `open_final_grammar_dropdown` (common: `_open_final_grammar_dropdown_common`)
- Assess by Word (ABW)
  - `show_word_translation_input`
  - `show_word_search_modal`
  - `show_word_verse_hits_modal`

Window sizing changes
- Use `self._wm_apply(win, margin_px=0, defer=True)` so:
  - Per-monitor WORK AREA is used (excludes taskbar).
  - Sizing is deferred with `after_idle` to avoid 1×1 restores when toggling or reopening.
  - On Windows, `state('zoomed')` is used after moving to the monitor’s `rcWork` origin. Fallback computes client size via `AdjustWindowRectEx` accounting for the title bar and frame.

Layout changes
- Bottom action bars now consistently: `pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))`.
- Remove hard-coded bottom gaps (e.g., 46) and rely on exact maximize instead of bottom padding.
- Main content frames use `fill=tk.BOTH, expand=True`; scrollable canvases/Text widgets fill vertically.

Acceptance
- ≤1px gap to taskbar; bottom buttons never obscured (fixed the regression shown in the 3rd screenshot case).
- Scroll areas still fill; behaves at 100–200% DPI and on multi-monitor setups.

Before/After (placeholders)
- Verse
  - show_translation_input: docs/screenshots/verse_show_translation_before.png → docs/screenshots/verse_show_translation_after.png
  - user_input_grammar: docs/screenshots/verse_user_input_grammar_before.png → docs/screenshots/verse_user_input_grammar_after.png
  - final_grammar_dropdown: docs/screenshots/verse_final_grammar_before.png → docs/screenshots/verse_final_grammar_after.png
- ABW
  - translation input: docs/screenshots/abw_word_translation_before.png → docs/screenshots/abw_word_translation_after.png
  - word search: docs/screenshots/abw_word_search_before.png → docs/screenshots/abw_word_search_after.png
  - verse hits: docs/screenshots/abw_verse_hits_before.png → docs/screenshots/abw_verse_hits_after.png

Notes
- F11 still toggles maximize/restore via WindowManager.
- Exact work-area maximize ensures the client matches WORK AREA within OS frame metrics, avoiding taskbar overlap.
