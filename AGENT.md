# AGENT Playbook

Practical guidelines for fast, safe convergence when collaborating with the Codex CLI agent.

## Roles & Handoff
- SME (Assistant/User): Provides domain guidance, clarifies intent, and requests minimal, targeted diffs until we converge.
- Orchestrator (Maintainer/You): Bridges intent and execution, coordinates SME input and agent outputs, and merges when the Definition of Done is met.
- Engine (Codex Agent): Produces code and diffs exactly per the submission template and acceptance criteria.

## Submission Template
Use the following template for each change request or review:

- Context: Brief background and current behavior.
- Objective: Desired behavior and scope (1–2 sentences).
- KEEP: Behaviors/APIs/paths that must not change.
- IMPROVE #1
  - Severity: P1/P2/P3
  - Rationale: Why this matters now.
  - Codex, please: Specific, actionable request (what to change/add/remove).
  - Acceptance criteria:
    - [ ] Concrete, verifiable checks
- Repeat additional IMPROVE blocks as needed.
- Global checks
  - [ ] Definition of Done
  - [ ] No P1/P2 outstanding
  - [ ] No regressions in existing flows
  - [ ] Stability guards intact (inputs/outputs/paths/messages)
  - [ ] Idempotent: rerun yields no new diffs
  - [ ] Verification evidence attached
  - [ ] Ready to CONVERGE
- Assumptions (optional): Constraints or non‑goals.
- Verification: Exact commands, sample inputs, and expected outputs.
- Exit (CONVERGED): Short note when merged and released.

## Severity Levels
- P1 (Blocker): Crashes, data loss, security risk, or core workflow broken.
- P2 (Major): Wrong results, degraded UX, or substantial inconsistency.
- P3 (Minor): Nits, polish, small refactors that can wait.

## Convergence & Stop Rules
- Definition of Done: All acceptance criteria pass; no P1/P2; no regressions; performance/UX targets met.
- Scope & Change Budget: Keep diffs minimal; avoid out‑of‑scope refactors.
- Stability Guards: Preserve inputs, outputs, file paths, CLI/GUI labels, and user‑visible messages unless explicitly requested.
- Idempotency: Re‑running the agent after acceptance should propose zero further changes.
- Verification: Provide quick‑check commands and sample data to validate the change.
- Escalation: If blocked on environment or data, request the smallest viable artifact (input sample, log, screenshot) and pause.

## Review Standards
- Diff etiquette: Change only what’s necessary; keep naming and file layout stable.
- Tests/QA: Prefer targeted checks first. In this repo:
  - Compile: `python -m py_compile 1.1.0_birha.py`
  - Optional: `bash scripts/qa.sh` (if Bash is available)
- Data safety: The app reads/writes CSV/XLSX in place; call out backup implications in PRs touching data paths.
- Compatibility: Keep Windows support in mind (PowerShell, UTF‑8 codepage, file locks with Excel).

## Code Style
- Workflow and review live here; language style follows project configs.
- Follow PEP 8 and any repo tooling (ruff/flake8/pyproject). Respect external settings; don’t restate them here.

## Communication
- Tone: kind, specific, actionable, and concise.
- Prefer short summaries with exact commands and expected results.
- Surface risks and assumptions early; propose the smallest next step to unblock.

