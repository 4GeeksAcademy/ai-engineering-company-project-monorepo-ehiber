# AGENTS.md

## Startup Context

Before making any change in this repository, every coding agent must read these files in order:

1. `CONTEXT.md`
2. `memory-bank/projectbrief.md`
3. `memory-bank/techContext.md`
4. `memory-bank/progress.md`

If any of these files is missing or outdated, update them before making product changes.

## Required Delivery Workflow

Before every commit, the agent must complete these steps in order:

1. Read the startup context files and confirm the requested task matches the company context.
2. Inspect the target folders `README.md` files and reuse existing code instead of duplicating business logic.
3. Implement the smallest safe change, keeping business logic in its original module whenever it is already present in the monorepo.
4. Run the relevant verification commands for the touched area and review the visible output for regressions.
5. Update the memory bank with any new architectural decision, milestone progress, or pending risk discovered during the work.
6. Prepare a concise delivery note with changed areas, verification status, and any blockers that still require human confirmation.

## Protected Areas

The agent must not modify these files or folders without explicit developer confirmation:

- `CONTEXT.md`
- `company-choice.md`
- `apps/trackflow-coding-fundamentals/src/`
- `apps/talent-pipeline-tracker/`
- `data/raw/`
- `data/eval/`

## Guardrails

- Do not duplicate business logic that already exists in `apps/trackflow-coding-fundamentals`.
- Do not create new top-level folders until the corresponding directory README has been reviewed.
- Ask for confirmation before deleting files, renaming existing apps, or changing public copy that affects TrackFlow positioning.
