## Summary
- embed the `AxiomsVerseInputFlow` frame so the “Axiom via Verse Analysis” button swaps the dashboard buttons for an in-pane verse-input workflow with mock suggestions and consecutive-verse controls (1.1.0_birha.py:15242)
- keep a single reusable flow instance, restore the button deck on Back/Cancel, and enforce verse/consecutive validation before revealing the review placeholder (1.1.0_birha.py:15679)
- surface a review summary (primary verse, selected suggestions, consecutive choice) and gate “Continue” behind the mandated placeholder message (1.1.0_birha.py:15525)

## Testing
- python -m py_compile 1.1.0_birha.py
