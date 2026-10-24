# P0-A Audit Record: Multi-source data merge and consistency check

## Record Metadata

- **Task ID:** P0A-PUB-009
- **Record status:** Design-stage audit record; no agent-assisted execution has been run.
- **Task type:** Public-source candidate, not a verified local historical school task.
- **Source basis:** `SRC-PUB-006` in the public-source register. The register provides only a public search-derived data-cleaning theme; no exact public assignment sheet for a multi-source merge has yet been verified. Related public teaching material demonstrates CSV-oriented preprocessing and field conversion: <https://dblab.xmu.edu.cn/blog/5419/>. This record therefore carries an explicit source-gap limitation.
- **Recorded date:** 2026-09-21

## Original Task

### Original Task Summary

Given two or more supplied sources such as customer master data, transactions, and reference codes, reconcile field definitions, standardize keys, merge the data, identify duplicates/unmatched/conflicting records, and submit a merged data set with a consistency report. This is an unverified public-source candidate pattern.

### Skill Area

- Python data processing
- SQL
- Data integration
- Data quality and consistency checking

### Traditional Expected Output

- Reproducible merge script or SQL.
- A merged data set with declared grain and join keys.
- A reconciliation report covering source row counts, match/unmatch counts, duplicate keys, conflicts, and resolution rules.
- Samples or identifiers for rejected and unresolved records.

### Original Learning Goal

Measure whether a learner can establish a data contract across sources, choose keys and join cardinality deliberately, detect data loss or multiplication, and communicate unresolved consistency problems.

### Environment

- Required software: supported Python and/or SQL environment.
- Required data: versioned source files, field dictionaries, explicit data-ownership boundary, and a defined output schema.
- Network requirement: not required after data provisioning.
- Can run locally: yes; a school-managed workspace should also be supported.

## Agent Impact Audit

### Possible Agent Completion Path

1. Profile every source independently: schema, row count, candidate keys, nulls, duplicates, formats, and value domains.
2. Draft a source-to-target mapping and declare target grain, join order, key normalization, precedence, and conflict policy.
3. Generate merge code only after the human confirms unresolved semantic assumptions.
4. Run reconciliation checks before and after each merge, preserving unmatched and conflict records.
5. Test with hidden duplicate, missing-key, formatting, and many-to-many cases; revise the pipeline with a change log.

This is a proposed path, not a record of an agent run.

### Agent Used and Result

- Agent name/model/date/prompt: not tested.
- Result classification: **Not tested**.
- Timing fields: unknown.

### Human Intervention Required

- Decide whether similarly named fields have the same business meaning and grain.
- Approve normalization and entity-matching rules; determine when uncertain matches must remain unresolved.
- Set source precedence and conflict-resolution policy.
- Review privacy, licensing, and minimum-necessary-data boundaries before sharing source extracts with an agent.

### Likely Agent Failure Modes

- Chooses a convenient but non-unique key and silently creates many-to-many row multiplication.
- Normalizes values too aggressively and merges distinct entities.
- Drops unmatched records or duplicate evidence to make reconciliation totals look clean.
- Treats a same-named field as semantically identical without checking units, period, or source grain.
- Writes a merge that runs successfully but cannot explain source-to-target lineage.

### Verification Plan

Use an evidence contract and deterministic reconciliation verifier:

1. Freeze each source fixture, expected target grain, key rules, and permitted transformations.
2. Check source and output hashes, schemas, lineage columns, row counts, match/unmatch counts, duplicate-key counts, and conflict counts.
3. Verify conservation/invariant rules where applicable (for example, transaction totals must reconcile before and after a one-to-one enrichment).
4. Run hidden fixtures containing key-format drift, duplicate keys, missing references, conflicting attributes, and deliberately ambiguous records.
5. Reject submissions that suppress unresolved records without an approved resolution code and audit trail.

- Verification result: not executed.
- Future evidence location: `artifacts/P0-A/runs/P0A-PUB-009/`.

## Assessment Value

### What the Original Task Still Measures

- Understanding of data grain, entity identity, and semantic compatibility.
- Use of reconciliation evidence to detect silent loss or duplication.
- Judgment about unresolved ambiguity and communication of data-quality limits.
- Privacy-aware handling of multiple data sources.

### What the Original Task No Longer Measures Well

- Boilerplate syntax for `merge`, joins, or string normalization when unrestricted agent assistance is allowed.
- A single successful merge on clean, one-to-one source files.
- Cosmetic reports that lack reconciled counts and lineage.

### Foundation Track Direction

Provide two or three small, documented source files. Restrict agent use. Require students to define target grain and key mapping before coding, execute a merge, retain all exception rows, and reconcile counts using a provided report template.

### Agent Track Direction

Allow an agent on a larger source package with hidden traps. Require a student-authored mapping/assumption register, agent delegation record, automated reconciliation, response to a seeded source-schema change, and a decision about an ambiguous match. Score verified outcome plus human oversight.

### Candidate for Dual Track / P0-C Recommendation

**Possible candidate, conditional on source provenance, privacy-safe fixtures, and a deterministic reconciliation contract.** It should not enter P0-C until an exact assignment or a carefully reconstructed task specification is evidence-backed.

## Evidence Limitations

- Unlike the other four records, no exact public task sheet has yet been verified for this candidate; the register names a search-derived theme only.
- No local assignment, original scoring rule, run evidence, agent transcript, output, or observed intervention exists.
- Proposed validation is a design recommendation, not a demonstrated verifier.

## Reviewer Notes / Next Evidence Needed

Prioritize locating an attributable public assignment or obtaining a local task. Do not use sensitive school, student, or enterprise data as an audit fixture.
