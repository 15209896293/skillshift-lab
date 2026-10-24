# P0-A Audit Record: SQL aggregation and abnormal result diagnosis

## Record Metadata

- **Task ID:** P0A-PUB-002
- **Record status:** Design-stage audit record; no agent-assisted execution has been run.
- **Task type:** Public-source candidate, not a verified local historical school task.
- **Source basis:** `SRC-PUB-003` in the public-source register. The public Xiamen University website-user-analysis case publishes aggregate analysis questions and SQL/Hive query examples, including day-level user behavior proportions: <https://dblab.xmu.edu.cn/blog/1005/>. It supports the task pattern only; it is not the original task statement for this record.
- **Recorded date:** 2026-09-21

## Original Task

### Original Task Summary

Given a fixed transactional or behavior table and a stated business question, write aggregate SQL and diagnose an abnormal result such as a count that is unexpectedly large, zero, duplicated, or inconsistent with a known total. Submit corrected SQL, result tables, and a reasoned diagnosis.

### Skill Area

- SQL
- MySQL
- Aggregation and joins
- Data-quality and anomaly diagnosis

### Traditional Expected Output

- Aggregate query or queries using `GROUP BY`, `HAVING`, conditional aggregation, joins, and date filters as applicable.
- A result table with expected totals or anomaly flags.
- A written diagnosis identifying the suspected cause and the correction.
- Evidence that the corrected query changes the anomalous result for the stated reason.

### Original Learning Goal

Measure whether a learner can define denominator and grouping grain, detect join multiplication or filter errors, and use evidence to distinguish a syntactically valid query from a valid answer.

### Environment

- Required software: MySQL-compatible server and SQL client.
- Required data: a fixed fixture with a data dictionary and expected aggregate semantics.
- Network requirement: not required after setup.
- Can run locally: yes, with a supplied environment; managed school access remains a valid alternative.

## Agent Impact Audit

### Possible Agent Completion Path

1. Convert the natural-language business question into an explicit metric definition: grain, population, numerator, denominator, time window, and null/duplicate policy.
2. Inspect table schemas and sample rows before proposing SQL.
3. Draft a baseline query, then run diagnostic queries for counts by key, unmatched joins, nulls, duplicate IDs, and totals before and after joins.
4. Compare query output with hidden expected aggregates and explain deviations.
5. Ask a human to resolve ambiguous business semantics; record any correction rather than silently changing definitions.

This path is a test design, not a completed agent run.

### Agent Used and Result

- Agent name/model/date/prompt: not tested.
- Result classification: **Not tested**.
- Timing fields: unknown; no comparison is claimed.

### Human Intervention Required

- Define the intended business metric and correct aggregation grain.
- Decide whether a discrepancy is a data incident, an expected edge case, or a query defect.
- Verify assumptions about time zones, inclusive boundaries, status values, cancelled records, and one-to-many relationships.
- Reject a plausible natural-language explanation when the database evidence does not support it.

### Likely Agent Failure Modes

- Aggregates after a one-to-many join and inflates totals.
- Uses `COUNT(column)` where `COUNT(*)` or `COUNT(DISTINCT ...)` is required, or vice versa.
- Moves a filter from `ON` to `WHERE` and unintentionally turns an outer join into an inner join.
- Selects non-grouped columns under permissive SQL mode or relies on nondeterministic values.
- Explains the anomaly confidently without running diagnostic subqueries.

### Verification Plan

Use deterministic fixtures and a hidden SQL verifier:

1. Provide normal, duplicate, null, unmatched, boundary-date, and one-to-many join cases.
2. Execute submitted SQL in an isolated read-only database with a controlled SQL mode.
3. Compare ordered, normalized result sets against canonical outputs for several hidden fixtures.
4. Check diagnostic evidence: the submission must identify the actual injected abnormality and support the diagnosis with a relevant count or reconciliation query.
5. Use metamorphic checks: duplicating an irrelevant dimension row must not alter an intended transaction count; shifting a record across a stated boundary must affect only the declared time bucket.

- Verification result: not executed.
- Future evidence location: `artifacts/P0-A/runs/P0A-PUB-002/`.

## Assessment Value

### What the Original Task Still Measures

- Metric definition, grain awareness, and database reasoning.
- Ability to inspect intermediate results and reconcile totals.
- Skepticism toward a runnable query or a fluent agent explanation.
- Communication of a bounded, evidence-backed diagnosis.

### What the Original Task No Longer Measures Well

- Recall of common aggregation syntax with unrestricted agent assistance.
- The ability to recognize a familiar query pattern without an adversarial fixture.
- A single expected-output screenshot that cannot reveal wrong logic on nearby data.

### Foundation Track Direction

Give a small database and an intentionally abnormal report. Restrict agents. Require students to write a metric definition, diagnostic query sequence, corrected SQL, and a short proof using reconciliation counts. Use multiple fixtures to avoid answer memorization.

### Agent Track Direction

Allow an agent to propose queries against a larger and messier database, but require the student to log requirements given to the agent, test the first answer on hidden cases, identify a seeded logical defect, correct or override it, and submit a diagnosis packet. The task should assess delegation, falsification, and takeover.

### Candidate for Dual Track / P0-C Recommendation

**Strong candidate, conditional on a real task statement and hidden fixtures.** Its value is high only if verification checks semantic correctness rather than accepting a plausible query string.

## Evidence Limitations

- No local historical task, original marking rule, data set, agent run, or human observation is available.
- Public examples establish that aggregate behavior-analysis queries are taught publicly; they do not establish what a local course assesses.
- All stated agent effects are test hypotheses, not measured results.

## Reviewer Notes / Next Evidence Needed

Build a small fixture generator with known join traps and obtain teacher confirmation of the intended metric definitions before any P0-C selection.
