# Skill: TrackFlow Release Check

## Objective

Run a consistent pre-delivery review for TrackFlow milestone work before creating the final commit or pull request update.

## When To Use

Use this skill after implementing a feature in the TrackFlow monorepo and before final delivery.

## Inputs

- The list of changed files.
- The milestone requirement being fulfilled.
- The verification commands relevant to the touched code.

## Procedure

1. Confirm the task still matches `CONTEXT.md` and the memory bank.
2. Check whether any business logic was duplicated instead of imported from its original module.
3. Run the relevant verification commands.
4. Compare the result against the milestone acceptance criteria.
5. Summarize pass/fail status and any remaining blockers.

## Acceptance Criteria

- `CONTEXT.md` and the memory bank were consulted for the task.
- Changed files stay within the intended scope.
- Existing TrackFlow business logic was reused instead of copied when applicable.
- At least one verification command was run and its outcome is recorded.
- The final summary clearly states what is complete, what is unverified, and what still needs human follow-up.
