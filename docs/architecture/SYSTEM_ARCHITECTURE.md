# SkillShift Lab System Architecture

## Status

Historical long-term proposal. It does not define the current R0 baseline; see `TECHNICAL_SPEC.md`.

## Architecture Principle

Use a unified web experience with decoupled execution.

The student should enter through a browser or PWA. The task may run in a Managed Sandbox, School Node, or optional Personal Node.

## Proposed Planes

| Plane | Responsibility |
| --- | --- |
| Client Layer | Student workspace, teacher web, admin console |
| Control Plane | auth, courses, assignments, task engine, sessions, scheduling |
| Agent Plane | model/provider adapters, agent gateway, policy, quota, standardized trace |
| Execution Plane | managed sandbox, school node, personal node, terminal/editor/runtime |
| Evaluation Plane | evidence collector, hidden verifier, report engine |
| Data Plane | operational database, event store, artifact store, research export |

## Current Boundary

This is a long-term architecture reference. R0 is a general AI Agent Workspace with a non-Docker local restricted-process provider and a Python + CSV Golden Path; teacher, evaluation, research, and multi-node planes are not R0 implementation scope.
