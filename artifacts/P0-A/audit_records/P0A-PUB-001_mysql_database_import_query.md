# P0-A Audit Record: MySQL database creation, table design, data import, and basic query

## Record Metadata

- **Task ID:** P0A-PUB-001
- **Record status:** Design-stage audit record; no agent-assisted execution has been run.
- **Task type:** Public-source candidate, not a verified local historical school task.
- **Source basis:** `SRC-PUB-003` in the public-source register. The precise assignment sheet has not yet been obtained. The task pattern is additionally consistent with the public Xiamen University user-behavior teaching case, which includes relational-database and MySQL use in an end-to-end data workflow: <https://dblab.xmu.edu.cn/post/useranalysis/>.
- **Recorded date:** 2026-09-21

## Original Task

### Original Task Summary

Create a MySQL database for a small business or behavior-data scenario; design one or more related tables; import a supplied CSV or SQL data file; then write basic `SELECT`, filter, sort, and join queries. This is a reconstructed public task pattern, not a transcription of a local assignment.

### Skill Area

- SQL
- MySQL
- Relational schema design
- Data import and encoding diagnosis

### Traditional Expected Output

- A runnable database and table-definition SQL file.
- Imported rows with an accountable row count.
- Required query SQL and result screenshots or exported result tables.
- A short explanation of primary keys, foreign keys, field types, and import choices.

### Original Learning Goal

Measure whether a learner can translate a stated data scenario into an executable relational schema, operate the database environment, load data correctly, and inspect query results rather than merely write SQL text.

### Environment

- Required software: MySQL-compatible server and client.
- Required data: a fixed, licensed teaching data set plus its data dictionary.
- Network requirement: not required once the environment and data set are provided.
- Can run locally: yes, subject to a provided environment; this must not be assumed to mean every student has a personal computer.

## Agent Impact Audit

### Possible Agent Completion Path

1. Read the task statement and draft DDL, import commands, and requested queries.
2. Ask the human for the real file delimiter, encoding, header convention, server version, and supplied data dictionary when they are absent.
3. Generate an execution checklist and run only in an approved MySQL environment.
4. Compare post-import row counts, null counts, duplicate keys, constraints, and sample query outputs with the task contract.
5. Record each correction and the final evidence bundle.

This is a proposed evaluation path, not evidence that an agent has completed the task.

### Agent Used and Result

- Agent name/model/date/prompt: not tested.
- Result classification: **Not tested**.
- Human baseline, agent-assisted, and intervention time: unknown; no timing claim is made.

### Human Intervention Required

- Confirm the intended business entities, key relationships, and allowed simplifying assumptions.
- Decide whether a column should be text, numeric, date/time, nullable, unique, or constrained.
- Resolve real import failures such as encoding, delimiter, header, path, permissions, duplicate rows, and server-specific SQL differences.
- Judge whether an apparently valid query answers the stated question and whether a schema is maintainable enough for the task.

### Likely Agent Failure Modes

- Invents column meanings or key relationships that the data dictionary does not support.
- Uses a permissive type or omits a constraint so invalid data is silently accepted.
- Treats `LOAD DATA` syntax, file paths, or encoding as portable across MySQL installations.
- Produces queries that run but double-count after joins or filter the wrong date/value representation.
- Stops after SQL text generation without checking database state or result cardinality.

### Verification Plan

Use a real database-state verifier, not LLM judgment:

1. Load a fixed fixture data set into a fresh database.
2. Inspect `information_schema` for required tables, columns, types, nullability, indexes, and declared constraints.
3. Check expected row counts, rejected-row log, key uniqueness, referential integrity, and agreed encoding samples.
4. Run canonical hidden queries against the submitted database and compare normalized results with expected result sets.
5. Add adversarial fixtures (duplicate key, malformed date, quoted delimiter, non-ASCII text) to distinguish a robust import from a screenshot-only submission.

- Verification result: not executed.
- Evidence location for a future run: `artifacts/P0-A/runs/P0A-PUB-001/` (must contain task version, fixture hash, SQL, database-state export, verifier output, and intervention notes).

## Assessment Value

### What the Original Task Still Measures

- Reading data semantics and translating them into a defensible schema.
- Operating a real database and diagnosing environment-specific import failures.
- Inspecting result counts and constraints instead of trusting generated code.
- Explaining trade-offs and taking responsibility for a submitted database state.

### What the Original Task No Longer Measures Well

- Recall of routine DDL and basic query syntax when unrestricted agent assistance is allowed.
- Typing speed or memorization of client-specific import commands.
- A bare SQL file without executable environment evidence.

### Foundation Track Direction

Provide a small offline fixture, data dictionary, and explicit entities. Restrict agent use. Require the learner to draw the schema, write selected DDL/query parts, import in a managed lab environment, and explain row-count or constraint discrepancies. Grade with database state plus a short oral or written rationale.

### Agent Track Direction

Provide an incomplete, messy import package and a changing business question. Allow an agent, but require a delegation plan, prompt/run log, explicit assumptions, a correction after a seeded import defect, and a verifier-backed final database. Assess verification behavior and takeover decisions rather than generated SQL alone.

### Candidate for Dual Track / P0-C Recommendation

**Strong candidate, conditional on a real local task and an executable MySQL fixture.** It aligns with the proposed first SQL/MySQL slice, but this record alone is not sufficient to select it for P0-C.

## Evidence Limitations

- The registered source is a public-source theme and the linked public case is not a local high-vocational assignment.
- No original rubric, fixed data set, agent run, human observation, timing, output, or verifier result is attached.
- The failure modes and redesign directions are hypotheses to test; they are not outcome claims or a measure of any broader educational effect.

## Reviewer Notes / Next Evidence Needed

Obtain a licensed local assignment sheet or a public assignment with explicit requirements, then freeze a fixture and data dictionary before conducting comparable human-assisted runs.
