# SkillShift Lab Data Architecture

## Status

Long-term data-governance reference. The active R0 entity and event model is in `TECHNICAL_SPEC.md`.

## Core Rule

Separate operational data from research data.

Operational data supports teaching, task execution, submissions, reports, accounts, and system operation.

Research data must be exported through a governed process with minimization, de-identification or pseudonymization, versioning, and authorization records.

## Data Categories

| Category | Examples | Boundary |
| --- | --- | --- |
| Operational Data | accounts, assignments, sessions, submissions, reports | used for product operation |
| Task Evidence | files, database states, command outputs, verifier results | task-scoped only |
| Telemetry Events | human decisions, agent suggestions, checkpoints, timestamps | minimum necessary collection |
| Research Export | de-identified datasets, analysis scripts, evidence packages | not direct teaching identity data |

## Privacy Rules

- Do not collect unrelated desktop activity.
- Do not collect private folders.
- Do not store real credentials in task evidence.
- Do not send student personal information to third-party models by default.
- Do not use unverified research metrics for grading.

## Current Boundary

This document defines direction only.

Concrete schemas must be created inside feature specs when implementation begins.
