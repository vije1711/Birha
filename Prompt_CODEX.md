Task: Compare 1.1.0_birha_pre_Axiom.py and 1.1.0_birha.py, and ensure that any functionality used inside the new Axioms code in 1.1.0_birha.py is implemented via fresh, dedicated functions rather than calling the old ones from 1.1.0_birha_pre_Axiom.py.

Repository context:

* You are working inside the Birha project.
* Two key files:

  * 1.1.0_birha_pre_Axiom.py  (legacy / pre-Axioms implementation)
  * 1.1.0_birha.py            (current main app with Axioms framework added)

High-level goal:

* Detect any direct reuse of functions from 1.1.0_birha_pre_Axiom.py inside the Axioms-related code in 1.1.0_birha.py.
* For every such reused function, create a new, Axioms-specific implementation inside 1.1.0_birha.py (or an appropriate new Axioms module) that does not call back into 1.1.0_birha_pre_Axiom.py.
* Update the Axioms code to use these new implementations.
* Preserve existing behavior for Axioms flows as they are today.

Definition: “Axioms code”

* In this task, “Axioms code” means any classes, functions, or modules in 1.1.0_birha.py that are clearly part of the Axioms framework/feature (for example:

  * Any sections explicitly marked in comments as Axioms or Axioms Framework.
  * Classes or functions whose names include “Axiom”, “Axioms”, or are clearly grouped under Axioms-related comments/regions.
* If needed, infer the Axioms boundary by reading surrounding comments and structure in 1.1.0_birha.py.

Constraints:

1. Do not remove or break any non-Axioms features that already exist.
2. Do not make Axioms code call functions from 1.1.0_birha_pre_Axiom.py.
3. For Axioms usage:

   * “Developed from scratch” means: implement fresh functions in 1.1.0_birha.py (or an Axioms-specific helper module) whose logic is self-contained.
   * You may use the old implementation as a reference to understand behavior, but the new Axioms-specific functions must not simply wrap or directly call the old functions.
4. Outside Axioms code:

   * It is acceptable for non-Axioms parts of the app to continue using 1.1.0_birha_pre_Axiom.py as they currently do.
5. Preserve public behavior:

   * From the user’s perspective, Axioms-related flows must behave the same as before this refactor (same inputs, outputs, and side effects).

Step-by-step instructions:

Step 1: Map legacy functions

* Open 1.1.0_birha_pre_Axiom.py.
* Build a list of all top-level functions and any key helper methods that could plausibly be reused (name, signature, and a one-line summary of what they do).
* Keep this mapping in your reasoning only; do not print it to the user.

Step 2: Find Axioms code in 1.1.0_birha.py

* Open 1.1.0_birha.py.
* Identify the Axioms-related region(s) as per the definition above (comments, class names, function names, etc.).
* Treat everything clearly inside those regions as “Axioms code” for this task.

Step 3: Detect reuse from pre-Axiom file

* Within the Axioms code in 1.1.0_birha.py, find all places that:

  * Import from 1.1.0_birha_pre_Axiom.py, OR
  * Call functions whose original definition is in 1.1.0_birha_pre_Axiom.py, whether via:

    * direct calls (e.g. some_legacy_fn(...)),
    * imported aliases,
    * or attribute-style calls if that file is imported as a module.
* Make an internal list of “Axioms → reused function” pairs.

Step 4: Create new Axioms-specific implementations
For each reused function from 1.1.0_birha_pre_Axiom.py that is called from Axioms code:

* Design a new function that lives in 1.1.0_birha.py (preferably:

  * near the Axioms code,
  * or in a clearly-named Axioms helper section/module).
* The new function should:

  * Have a clear, descriptive name that fits the Axioms context (e.g. prefix/suffix with axiom_ or similar, if consistent with existing style).
  * Accept parameters that make sense for the Axioms call sites.
  * Reimplement the necessary logic directly, without delegating to 1.1.0_birha_pre_Axiom.py.
* It is OK to:

  * Reuse existing utility helpers already defined inside 1.1.0_birha.py (such as general-purpose CSV/Excel helpers, normalization helpers, etc.), as long as they are not Axioms-specific and are not imported from 1.1.0_birha_pre_Axiom.py.
  * Slightly improve clarity and safety (e.g. better variable names, small error checks) as long as behavior stays the same.

Step 5: Wire Axioms code to new functions

* For every Axioms call to an old function:

  * Replace the call so that it uses the new Axioms-specific implementation you created.
* Remove any now-unneeded imports from 1.1.0_birha_pre_Axiom.py that are only used inside Axioms code.
* Do not touch imports or usage in non-Axioms areas.

Step 6: Sanity checks and light tests

* If the repository has an existing test suite, run it and ensure it passes.
* If there is no formal test suite for this part, add minimal local checks such as:

  * Small, self-contained test functions or script snippets (for example, guarded by if **name** == "**main**":) that exercise:

    * One or two representative Axioms flows that previously used the legacy functions.
    * Confirm the Axioms outputs (or side effects) match the current behavior.
* Keep these tests light and do not introduce heavy new dependencies.

Step 7: Code style and structure

* Follow the existing style of 1.1.0_birha.py:

  * Naming, comments, logging approach, and error handling.
* Document the new functions with concise docstrings explaining:

  * What they do.
  * That they are Axioms-specific replacements for previously reused logic from 1.1.0_birha_pre_Axiom.py.

Definition of Done:

1. All Axioms-related code in 1.1.0_birha.py no longer calls any functions from 1.1.0_birha_pre_Axiom.py directly or via imports.
2. New Axioms-specific helper functions exist in 1.1.0_birha.py (or a dedicated Axioms helper module) implementing the needed behavior from scratch.
3. Non-Axioms code continues to work and may still use 1.1.0_birha_pre_Axiom.py unchanged.
4. Axioms behavior is preserved (manual smoke tests or existing tests confirm the same outputs for typical flows).
5. Imports are clean:

   * No unused imports from 1.1.0_birha_pre_Axiom.py.
   * No circular or broken imports introduced by this refactor.
