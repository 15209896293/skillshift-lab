# SkillShift Lab Agent Rules

## PROJECT

SkillShift Lab is a vocational digital skill transition platform for the Agent era.
The project connects school-based foundation training with realistic human-agent work.

The current stage is not full platform development. The current priority is:

1. Build a minimal Agent Native Development OS.
2. Run P0 research and planning work.
3. Verify whether real traditional training tasks are changed by modern agents.
4. Only then move into MVP engineering.

## CURRENT DEVELOPMENT PHILOSOPHY

Keep the project simple, traceable, verifiable, recoverable, agent-friendly, and understandable to a non-technical product owner.

Do not build processes for appearance. Add a workflow only when it reduces more confusion than it creates.

## NON-NEGOTIABLE RULES

- Do not treat chat history as the formal project state.
- Do not claim a feature is Done without objective evidence.
- Do not expand task scope without explicit approval.
- Do not rewrite architecture during an implementation task.
- Do not delete historical documents.
- Do not overwrite project plans in `wenben/`.
- Do not use an LLM's own judgment as a Hidden Verifier.
- Do not assume every student owns a personal computer.
- Do not use unverified research metrics for student grades.
- Do not send student personal information to third-party models by default.
- Do not bypass tests or checks and claim completion.
- Do not push automatically.
- Do not close major issues automatically.
- Do not perform large refactors unless the task explicitly authorizes them.

## SOURCE OF TRUTH

Use this hierarchy:

1. Project plan documents in `wenben/`: long-term strategy and research knowledge.
2. `docs/PROJECT_BRIEF.md`: stable facts every agent must know.
3. `AGENTS.md`: agent operating rules.
4. `docs/architecture/`: current effective architecture.
5. `docs/adr/`: architecture decisions and reasons.
6. `specs/`: feature, research, bug, and documentation specs.
7. GitHub Issues / Project: current work state, once GitHub is configured.
8. Git: actual code history, once the repository is initialized.
9. CI / Tests: machine evidence that work still functions.
10. Release notes: current usable product state.

If two sources conflict, stop and report the conflict. Do not silently choose the convenient version.

## BEFORE CODING

Before changing code or project structure:

1. Identify the task type: FEATURE, BUG, RESEARCH, REFACTOR, DOC, or DEV_OS.
2. Check whether a spec or issue exists for significant work.
3. Read only the necessary project context, starting from `docs/PROJECT_BRIEF.md`.
4. Define allowed scope and forbidden scope.
5. Identify acceptance criteria and verification evidence.
6. Check whether the work should happen in a separate branch or worktree.

## IMPLEMENTATION RULES

- Make the smallest useful change.
- Prefer current project patterns over new abstractions.
- Keep historical assets intact.
- Do not move unknown files.
- Do not create duplicate sources of truth.
- Keep long-term architecture ideas separate from current implementation.
- Mark uncertain architecture as Proposed, not Accepted.
- For student-facing or research-facing behavior, preserve privacy and evidence boundaries.

## TESTING

Every meaningful task must state what was checked.

If tests exist, run the relevant tests.
If tests do not exist, explain the current limitation and provide the best available verification.

For development tasks, prefer this order:

1. Static checks.
2. Unit tests.
3. Integration tests.
4. Build.
5. Runtime or demo verification.
6. Acceptance criteria review.

## AFTER CODING

Every agent completion report must include:

- Task ID
- Files changed
- Why the files changed
- Test commands
- Test results
- Acceptance criteria PASS / FAIL
- Known limitations
- New risks
- Follow-up
- Git diff summary
- Commit, or `NONE` if no commit was made

Forbidden completion phrases when used alone:

- Done
- Fixed
- Optimized
- No problem
- Completed successfully

## GIT RULES

This project is not yet initialized as a Git repository at the time this file was created.

When Git is initialized:

- Do not work directly on `main` for significant changes.
- Use one issue, one branch, one worktree for parallel agent work.
- Do not reset, clean, force-push, or discard user changes without explicit approval.
- Do not auto-commit unless the user requested a commit.
- Do not auto-push.
- Review the final diff before reporting completion.

## SECURITY / PRIVACY

- Student personal data is sensitive by default.
- Research data must be separated from operational data.
- API keys must not be stored in student clients or Personal Nodes.
- Personal Node must use task-scoped permissions and workspace allowlists.
- Do not collect full desktop, private folders, real credentials, or unrelated applications.
- Use minimum necessary telemetry.

## RESEARCH BOUNDARIES

- Do not output "AI replacement rate".
- Do not treat a pilot result as a general education conclusion.
- Distinguish implemented, planned, simulated, and unverified claims.
- Keep raw data, analysis scripts, evidence, limitations, and decisions connected.
- Research findings must affect product decisions only through documented evidence.

## FORBIDDEN ACTIONS

- `git reset --hard`
- `git clean`
- Deleting or moving unknown historical assets
- Automatic commit or push
- Deploying without explicit approval
- Large-scale refactoring without a spec
- Hidden architecture changes inside feature work
- Claiming Done without verification evidence
