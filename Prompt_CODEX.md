Nice drop. The stub does what we asked: opens a scrollable SGGS list, Back/Cancel behave, and selecting a verse routes you back into the Verse Input flow with the field prefilled. A few small, high-impact fixes to tighten it up:

1. Cast the Listbox index to int
   Tkinter returns string indices; you’re using `selection[0]` directly. That’ll trip comparisons and indexing in some spots (we’ve been burnt by this before).

```python
selection = self.listbox.curselection()
if not selection:
    ...
idx = int(selection[0])            # <-- cast
verse = self.listbox.get(idx)
```

2. Make “Next” enable immediately after routing
   Right now we set the verse and show the input frame, but the **Next** button may still be disabled until the user types. Nudge the flow to recalc:

```python
flow.verse_var.set(verse)
flow._display(flow.input_frame)
try:
    flow._update_next_state()      # T2 helper already present
except Exception:
    pass
```

(Optionally `verse_entry.focus_set()` if you expose the widget, but not required.)

3. Simplify the home re-pack logic
   You’re doing `pack_forget()` then `pack()` twice in `_select_verse`. One is enough—keep the `pack_forget()` where you hide the reader, and re-pack the button holder once using the cached `pack_info` like you already do in `_go_back`.

4. Idempotent wiring is good; guard reader creation once
   You already cache `_axioms_t7_reader_view`. Keep that as is—prevents multiple readers on repeated clicks.

5. Error handling is very forgiving—good for UI—but log if you can
   If you have a lightweight logger in the file, consider logging inside those `except Exception:` blocks so we don’t swallow actionable errors during dev. If not, fine for now.

6. Header/placement looks clean
   All code is under `# === Axioms T7: SGGS Reading Mode (stub, additive only) ===` and wraps T1/T2 constructs without editing them. ✅
