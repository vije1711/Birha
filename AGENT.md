# AGENT Playbook

## Roles & handoff
- **SME (Assistant)** – Provides authoritative guidance, celebrates wins, and requests minimal targeted diffs until we converge.
- **Orchestrator (You)** – Bridges intent and execution, coordinating SME insights and Codex outputs, and merging when the DoD is met.
- **Engine (Codex)** – Generates code and diffs exactly per the Preferred submission format and acceptance criteria.

## Preferred submission format
Use the following sections in every review:

- **Context**
- **Objective**
- **KEEP**
- **IMPROVE #1**  
  - Severity (P1/P2/P3)  
  - Rationale  
  - Codex, please …  
  - Acceptance criteria  
    - [ ] …  
- **IMPROVE #N** blocks may be repeated.
- **Global checks**  
  - [ ] Definition of Done  
  - [ ] No P1/P2  
  - [ ] No regressions  
  - [ ] Stability Guards  
  - [ ] Idempotency  
  - [ ] Verification evidence attached  
  - [ ] Ready to CONVERGE
- **Assumptions** (optional)
- **Verification**
- **Exit (CONVERGED)**

## Convergence & Stop Rules
- **Definition of Done**: all acceptance criteria pass, no P1/P2, no regressions, performance/UX targets met.
- **Scope & Change Budget**: minimal diffs, avoid out‑of‑scope refactors.
- **Stability Guards**: preserve inputs, outputs, file paths, and user-visible messages.
- **Idempotency**: re-running should propose zero further changes.
- **Verification**: outline quick-check commands.

Tone: kind, specific, actionable.

## Code Style
AGENT.md governs workflow, review, and convergence only.
Follow PEP8 and any repo-specific configs (ruff, flake8, pyproject.toml).
Codex must respect those external settings for formatting and linting; do not mirror rules here.
