# SkillShift Studio UI assets

## Current R0.5 teacher references

- `../apps/studio-web/public/concepts/teacher-course-overview.html`: teacher task workbench reference.
- `../apps/studio-web/public/concepts/teacher-authoring-and-model-settings.html`: three-column task authoring reference (teacher navigation, planned assistant area, API-backed task form).
- Runtime implementation: `../apps/studio-web/src/pages/teacher/` and `../apps/studio-web/src/components/layout/AppLayout.tsx`.

The React application and its API DTOs are the implementation source of truth. The standalone HTML files are visual references and do not call the API.

## Preserved earlier designs

`pages/teacher-designer.html` and `pages/teacher-review.html` are earlier static explorations. They include concepts such as course management and AI scoring that are outside the current active R0 workflow; do not treat those interactions or values as implemented product behavior. They are retained as prior design assets and are not synchronized with the React application.

## API and product boundary

The current teacher UI uses only the local synthetic API rooted at `/api/v1/demo`: assignment listing, creation, publication, and per-assignment review queues. It does not provide authentication, course/class membership, due dates, document upload or parsing, teacher-side AI drafting, model credentials, grading, or student counts.

The composer in the authoring reference is intentionally marked unavailable until a separately approved and implemented teacher authoring API exists. ADR-006 also keeps student API keys out of student clients; teacher BYOK, if later authorized and implemented, must use a server-side credential reference. No credential form in these UI references stores or sends a key.
