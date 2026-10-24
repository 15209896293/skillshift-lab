# SkillShift Lab Current State

## Date

2026-09-24

## Current Stage

R0 product-prototype specification and project-structure organization.

## Current Status

The project has strategic planning documents, an initial Dev OS skeleton, and an approved R0 product direction. SkillShift is research-led; Studio is a productized research infrastructure for AI-enabled tasks, minimal process evidence and teacher intervention. R0 uses Python only as the first Code Workspace Evidence Adapter, not as the permanent task boundary.

The local folder is a Git repository on branch `main`. The Dev OS baseline, the P0-A public-source task seed, and the project stage long plan are committed.

Five design-stage audit records for the first public-source P0-A candidates have been added. They are explicitly not local historical tasks and have not yet been executed as agent-assisted experiments.

## Current Priority

The R0 requirements, technical and quality specifications have been unified; the A+B research-task-evidence contract, three ADRs and the Foundation Spike specification have been added. A synthetic local reference Node has been implemented and tested. Its evidence is PARTIAL: path/timeout/Manifest basics pass, while OS-level network isolation, child-process-tree stopping and actual symbolic-link testing remain unresolved. Research-track expansion remains paused; no deployment, real student use or research execution has occurred.

## Next Concrete Actions

1. Close the PARTIAL/FAIL items in `artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md` before expanding scope.
2. Keep the Spike limited to synthetic or project-owner-authorized example projects.
3. Do not add real models, student data, deployment or teacher Web while ADR-002 remains Proposed.
4. After all Foundation Spike gates have objective PASS evidence, create a separately authorized teacher-task-to-review vertical-slice specification.

## Not Yet Started

- teacher Web, platform API, model integration and real Agent Runtime,
- GitHub Project,
- GitHub Issues,
- releases,
- deployments.

CI exists only as a minimal draft workflow and has not run on GitHub yet.

## Important Boundary

Do not build the full SkillShift platform, a production sandbox, full LMS/gradebook, external-AI detection or research-data pipeline. The Foundation Spike is a non-Docker local restricted-process prototype; it does not access host private directories, credentials, other Workspaces, student real privacy data, arbitrary networks or arbitrary dependencies. Teacher workflow is specified for the later R0 vertical slice, not implemented in the Foundation Spike.
