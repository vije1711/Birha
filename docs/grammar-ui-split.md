Title: Proper Split of Per-Word Grammar UI (Verse vs ABW)

Summary
- Extracted a shared builder `_build_user_input_grammar(win, *, word, translation, index, mode)` that constructs the complete grammar UI without starting a mainloop.
- Added two clean entry points:
  - `user_input_grammar(word, translation, index)` for Assess by Verse (unchanged behavior, modal, taskbar-safe maximize + F11).
  - `user_input_grammar_for_word(word, translation, index)` for Assess by Word (ABW) with modal behavior, taskbar-safe maximize + F11, and no reliance on Verse UI.
- Preserved bottom spacing via `BOTTOM_PAD` and kept WindowManager semantics consistent in both entry points.
- Removed unreachable ABW references in these functions and eliminated duplicated translation UI outside the builder.

Developer Notes
- Verse behavior is preserved: the wrapper sets the title and uses `_wm_apply(win, margin_px=BOTTOM_PAD)`, then calls the shared builder with `mode="verse"`, and runs the window modally.
- ABW entry creates a modal window, sets the ABW-specific title, applies the WindowManager, then calls the builder with `mode="word"`. It also installs a close protocol suited for modal usage.
- The shared builder wires up frames, the verse highlight, translation display, meanings canvas, grammar option radios, expert prompt, and the bottom action bar. It sets `self.current_word`, `self.meanings_canvas/inner_frame`, and `self.number_var/gender_var/pos_var` expected by existing callbacks.

Dead Code Cleanup
- Removed undefined references in the new ABW entry and ensured no unreachable blocks remain in the new functions.
- Note: The legacy implementation body was renamed to `_user_input_grammar_impl` for reference. If desired, it can be deleted once the new path is verified on all platforms.

Screenshots (placeholders)
- Add screenshots to these paths before final PR review:
  - docs/images/verse_grammar_ui_after.png
  - docs/images/abw_grammar_ui_after.png

PR Checklist
- [x] Both entry points call the shared builder and work end-to-end.
- [x] ABW path is self-contained and modal.
- [x] No undefined variable warnings in these functions.
- [x] Verse behavior unchanged; bottom spacing preserved.

Open PR
- Push branch: `refactor/grammar-ui-proper-split` (already pushed)
- Create PR: https://github.com/vije1711/Birha/pull/new/refactor/grammar-ui-proper-split
