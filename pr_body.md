## Summary
- Refined **Task T13 — Integration Validation & Final Polishing** by replacing the tall dashboard checklist with a compact status row plus “View details…” dialog to keep navigation buttons visible.
- Preserved the reusable integration helpers and structured report; the modal reuses them to display the full checklist on demand.
- Ensured the summary row stays anchored beneath the navigation buttons even after entering and exiting verse/SGGS flows.
- Added refresh hooks for both the summary row and dialog so QA can re-run integration checks without leaving the dashboard.

## How to Verify
- Launch `Axioms (beta)` and confirm the **Integration Checklist** row shows the pass/fail count and offers `Refresh` + `View details…`.
- Click `View details…` to open the modal; use `Refresh` inside the dialog to confirm the checklist updates without resizing the dashboard.
- (Optional) Run the harness programmatically: `python - <<'PY' ... get_axioms_integration_report()`.
- `python -m py_compile 1.1.0_birha.py`

## Risks
- Low risk of focus/stacking quirks if multiple dialogs are opened simultaneously; mitigated by reusing a single modal instance.
- Status checks still depend on existing monkey patches; breaking changes upstream will surface as warnings until addressed.

## Additive Changes
- All updates remain additive within `# === Axioms T13: Integration Validation & Final Polishing ===` in `1.1.0_birha.py`; legacy code paths untouched.
