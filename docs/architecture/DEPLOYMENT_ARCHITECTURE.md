# SkillShift Lab Deployment Architecture

## Status

Historical multi-environment proposal. It does not select the current R0 provider; see `TECHNICAL_SPEC.md`.

## Deployment Principle

The interface should be unified, but execution backends may differ.

SkillShift should support students in different real equipment conditions:

- school computer room,
- student personal computer,
- no personal computer.

## Proposed Execution Options

| Option | Purpose | Notes |
| --- | --- | --- |
| Managed Sandbox | shared remote execution for students without personal computers | preferred for consistency and control |
| School Node | school-provided execution resource | useful for local teaching environments |
| Personal Node | optional local execution agent on a student's computer | must be explicitly authorized and task-scoped |

## Security Boundary

Personal Node is an execution agent, not a full desktop remote-control product.

It should use:

- device binding,
- session-scoped tokens,
- workspace allowlists,
- minimum permissions,
- revocable authorization.

## Current Boundary

R0 uses a non-Docker local restricted-process provider for synthetic or project-owner-authorized examples only. Managed Sandbox, School Node, and Personal Node remain later proposals.
