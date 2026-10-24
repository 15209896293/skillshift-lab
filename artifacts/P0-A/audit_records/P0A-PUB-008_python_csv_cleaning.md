# P0-A Audit Record: Python CSV cleaning with missing values and type conversion

## Record Metadata

- **Task ID:** P0A-PUB-008
- **Record status:** Design-stage audit record; no agent-assisted execution has been run.
- **Task type:** Public-source candidate, not a verified local historical school task.
- **Source basis:** `SRC-PUB-006` in the public-source register. Public teaching examples from the Xiamen University Database Lab explicitly demonstrate CSV/data-frame cleaning, missing-value handling, duplicate handling, and conversion of age from floating point to integer: <https://dblab.xmu.edu.cn/blog/5419/>. This source supports the pattern, not a local task provenance.
- **Recorded date:** 2026-09-21

## Original Task

### Original Task Summary

Read a supplied CSV in Python, identify missing or malformed values, apply stated cleaning rules, convert selected fields to intended types, export a cleaned CSV, and report before/after quality statistics. This is a reconstructed public task pattern.

### Skill Area

- Python data processing
- Data cleaning
- CSV parsing
- Missing-value and type-conversion handling

### Traditional Expected Output

- Reproducible Python script or notebook.
- Cleaned CSV with a defined schema.
- Before/after row count, missing-value count, duplicate count, and type summary.
- Brief rationale for each cleaning rule and any dropped or imputed records.

### Original Learning Goal

Measure whether a learner can inspect an input data contract, distinguish missing values from valid sentinel values, choose a defensible conversion policy, and validate the resulting data rather than merely call a library function.

### Environment

- Required software: supported Python runtime and approved data libraries such as pandas.
- Required data: versioned CSV fixture, data dictionary, and stated cleaning policy.
- Network requirement: not required after dependency provisioning.
- Can run locally: yes, but a managed notebook/lab environment should be available for learners without personal computers.

## Agent Impact Audit

### Possible Agent Completion Path

1. Inspect the CSV bytes, delimiter, encoding, header, sample values, and data dictionary.
2. Propose an explicit input/output schema and cleaning decision table rather than immediately dropping rows.
3. Generate a script with parsing, normalization, missing-value policy, conversion, quality summary, and export steps.
4. Run it on public and hidden fixtures; compare outputs, reject rows with reasons, and schema checks.
5. Escalate ambiguous values (for example `0`, `N/A`, blank, locale-specific dates, or decimal commas) to the human.

This is a possible audit runbook, not evidence of agent completion.

### Agent Used and Result

- Agent name/model/date/prompt: not tested.
- Result classification: **Not tested**.
- Timing fields: unknown; no timing or productivity inference is made.

### Human Intervention Required

- Confirm the meaning of missing, unknown, zero, and out-of-range values.
- Select which fields are identifiers, categories, dates, numeric measures, or free text.
- Decide whether to drop, impute, retain, or quarantine invalid rows and document the impact.
- Inspect outliers and confirm that a successful `astype` did not silently lose precision or coerce values incorrectly.

### Likely Agent Failure Modes

- Applies `dropna()` globally and removes valid or recoverable observations.
- Converts IDs such as `00123` to integers and loses leading zeros.
- Treats locale-specific numbers, dates, or encoding as universal.
- Uses coercion that turns malformed values into nulls but does not report them.
- Produces a cleaned file without preserving row lineage or quality statistics.

### Verification Plan

Use fixture-based checks that inspect the real output:

1. Freeze public and hidden input CSVs with a data dictionary and expected output schema.
2. Check output encoding, header, column order, row count, types, null policy, duplicate policy, and allowed value ranges.
3. Compare normalized output rows to a canonical result where the rule is deterministic.
4. Include edge cases: BOM/encoding variation, quoted delimiter, blank string, `N/A`, decimal comma, invalid date, leading-zero ID, duplicate, and unexpected category.
5. Require a machine-readable rejection/imputation report so row loss and conversions are auditable.

- Verification result: not executed.
- Future evidence location: `artifacts/P0-A/runs/P0A-PUB-008/`.

## Assessment Value

### What the Original Task Still Measures

- Data-contract reading and cleaning-policy judgment.
- Ability to validate a generated script on real edge cases.
- Explanation of data loss, type semantics, and remaining uncertainty.
- Reproducibility and evidence preservation.

### What the Original Task No Longer Measures Well

- Memorization of pandas method names or boilerplate code when unrestricted agent assistance is allowed.
- A happy-path cleaning run on a single well-formed CSV.
- A notebook screenshot without input/output integrity checks.

### Foundation Track Direction

Provide a small, documented CSV and require students to inspect it, create a cleaning decision table, implement core operations with restricted agent use, and account for every changed or excluded row. Grade scripts and outputs against fixtures plus an explanation.

### Agent Track Direction

Allow an agent on a larger, ambiguous CSV package. Require the student to specify a data contract, audit agent-proposed transformations on hidden edge cases, preserve lineage, respond to a seeded schema/encoding change, and submit a verifier-backed quality report.

### Candidate for Dual Track / P0-C Recommendation

**Strong candidate, conditional on a precise data policy and hidden fixtures.** It is especially suitable for observing verification and correction behavior, not for scoring unverified generated code.

## Evidence Limitations

- The linked material is public and does not prove a local course used this exact assignment.
- No original rubric, frozen fixture, agent transcript, output, verifier run, or human intervention observation is present.
- Assertions about agent failure modes are prospective test cases rather than observed frequencies.

## Reviewer Notes / Next Evidence Needed

Create a licensed fixture and decision table before testing. Ensure the task never requires a learner to upload private or real student data to an external model.
