Description

- Injects a new Axioms (beta) button onto the welcome dashboard via an additive wrapper around GrammarApp.show_dashboard, positioning it before the disabled “Upcoming Feature” tile and reusing existing styling. (1.1.0_birha.py:14995)
- Hooks the button to open the additive AxiomsDashboard shell when available, reusing any existing instance and falling back to the required “next build” info popup if the class is missing. (1.1.0_birha.py:15029)
- Introduces the AxiomsDashboard beta window itself as an additive tk.Toplevel, leveraging WindowManager, offering the two placeholder navigation buttons, and ensuring clean teardown via an on_close callback. (1.1.0_birha.py:15150)

Testing

- python -m py_compile 1.1.0_birha.py
