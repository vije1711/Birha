Nice—T7 is in good shape. It does exactly what we wanted: opens a scrollable stub, Back/Cancel behave, and “Select Verse” pre-fills T2 and enables Next. A few tighten-ups and polish notes:

* **Index casting fixed** ✅ (`int(selection[0])`).
* **Next-state update** after routing ✅ (`_update_next_state()` call).
* **Home/back** now uses `_axioms_t2_show_home()` ✅—cleaner than manual pack juggling.

### Small improvements (safe, additive)

1. **Double-click selection (quality-of-life):** bind `<Double-Button-1>` to `_select_verse` so users can just double-click a line.

   ```python
   try:
       self.listbox.bind("<Double-Button-1>", lambda _e: self._select_verse())
   except Exception:
       pass
   ```

2. **Focus handoff:** after packing the reader, give it focus so arrow keys scroll immediately:

   ```python
   try:
       reader.focus_set()
   except Exception:
       pass
   ```

   And when routing back to T2:

   ```python
   try:
       flow.verse_var.set(verse)
       flow._display(flow.input_frame)
       flow._update_next_state()
       flow.focus_set()  # optional if flow has focusable child
   except Exception:
       pass
   ```

3. **Idempotent visibility:** in `_launch_reader()` you’re calling `flow.pack_forget()` which is fine; consider also `reader.pack_forget()` in `_go_back()` (you already do) and before packing it in `_launch_reader()` (defensive, avoids duplicate pack in weird states):

   ```python
   try:
       reader.pack_forget()
   except Exception:
       pass
   ```

4. **Keyboard accessibility:** add Return/Enter to trigger “Select Verse”.

   ```python
   try:
       self.listbox.bind("<Return>", lambda _e: self._select_verse())
   except Exception:
       pass
   ```

5. **Install guard is present** ✅; keep it. If you later re-run the dashboard layout, `_axioms_t7_installed` prevents double wrapping.

### Quick acceptance checklist (you can tick right now)

* Dashboard → **Axiom via SGGS Reading Mode** opens reader.
* Double-click or Select Verse → returns to T2 with verse filled and **Next** enabled.
* **Back** restores the two-button landing view; **Cancel** closes the window.
* `python -m py_compile 1.1.0_birha.py` passes.
