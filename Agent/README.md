# SYNTAX V2 Agent Guidelines

This directory contains the autonomous agent that plans, edits, and tests gameplay features. The following practices keep the agent reliable when extending the game (especially for complex weapon behaviours):

## Core Responsibilities
- Always refresh the project structure before working so file paths remain accurate.
- Read the relevant documentation (`Game/README.md`) and source files in full before attempting modifications.
- Plan the work into explicit steps (analysis → edit → validation). Do not guess behaviour—derive it from the codebase or observed failures.

## Editing Workflow
1. Gather context using `read_file(..., line_count=True)` for any file that will be touched.
2. Use `write_into_file` for targeted edits. The helper now guarantees trailing newlines for inserted blocks, preventing the previous "same-line" bug.
3. After editing a file involved in a failing check, rerun that phase's tests. When a later phase passes, immediately re-run earlier failing checks to ensure there are no regressions.
4. Continue iterating until all validations succeed. The agent should only pause for explicit confirmation (such as the 10-call safety prompt) and must resume immediately afterwards.

## Testing Expectations
- Run syntax/static validation after each substantial change.
- Execute the full simulation/test suite before concluding the workflow.
- Do not mark a task complete until all tests are green and no unresolved issues remain.

These rules mirror the updated instructions in `Agent/Prompts/agents.md` and should be kept in sync whenever the agent's behaviour is adjusted.
