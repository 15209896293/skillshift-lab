import type { AllowedArtifact } from './types'

// ---------------------------------------------------------------------------
// 领域类型定义（与 workspace-client.mjs 的 DTO 验证一一对应）
// ---------------------------------------------------------------------------

export type WorkspaceState =
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'PAUSED'
  | 'REVIEW_REQUIRED'
  | 'FEEDBACK_REQUIRED'
  | 'RESUBMITTED'
  | 'CLOSED'

export type ArtifactMediaType = 'text/x-python' | 'text/csv' | 'text/markdown'

export interface ArtifactReference {
  id: string
  logical_name: AllowedArtifact
  media_type: ArtifactMediaType
  source: 'FIXED_SYNTHETIC'
  integrity_status: 'NOT_COMPUTED'
}

export interface ArtifactSnapshot {
  logical_name: AllowedArtifact
  media_type: ArtifactMediaType
  size_bytes: number
  content: string
  sha256: string
}

export interface Workspace {
  id: string
  assignment_id: string
  assignment_version: number
  state: WorkspaceState
  revision: number
  execution_enabled: false
  artifact_refs: ArtifactReference[]
}

export type CollaborationMode = 'QA_ONLY' | 'PROPOSE_WITH_STUDENT_CONFIRMATION'

export interface CreateAssignmentRequest {
  title: string
  goal: string
  student_responsibility: string
  submission_requirement: string
  starter_project_id: 'orders-audit-v1'
  collaboration_mode: CollaborationMode
}

export interface Task {
  id: string
  task_id: string
  version: number
  title: string
  goal: string
  collaboration_mode: CollaborationMode
  student_responsibility: string
  submission_requirements: string[]
  starter_project_id: string
  execution_enabled: false
}

export type AssignmentState = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'

export interface Assignment {
  id: string
  version: number
  state: AssignmentState
  revision: number
  task: Task
  workspace: Workspace | null
  demo_notice: string
}

export type SubmissionState =
  | 'SUBMITTED'
  | 'RESUBMITTED'
  | 'FEEDBACK_REQUIRED'
  | 'ACCEPTED'

export interface Submission {
  id: string
  workspace_id: string
  workspace_revision: number
  assignment_version: number
  version: number
  artifact_refs: ArtifactReference[]
  artifact_snapshots: ArtifactSnapshot[]
  student_explanation: string
  created_event_sequence: number
  state: SubmissionState
}

export type EvidenceActorRole = 'teacher' | 'student'

export interface EvidenceEvent {
  event_id: string
  sequence: number
  schema_version: string
  workspace_id: string
  actor_role: EvidenceActorRole
  event_type: string
  resource_ref: string
  request_id: string
  occurred_at: string
}

export type RemediationAction =
  | 'REQUEST_EXPLANATION'
  | 'REQUEST_EVIDENCE'
  | 'REQUEST_REMEDIATION'
  | 'ENVIRONMENT_ISSUE'

export type RemediationState = 'OPEN' | 'RESPONDED' | 'CLOSED'

export interface Remediation {
  id: string
  review_action_id: string
  submission_id: string
  requested_action: RemediationAction
  reason: string
  state: RemediationState
  response_submission_id?: string
}

export type ReviewActionKind =
  | 'ACKNOWLEDGE'
  | 'REQUEST_EXPLANATION'
  | 'REQUEST_EVIDENCE'
  | 'REQUEST_REMEDIATION'
  | 'ENVIRONMENT_ISSUE'

export interface ReviewHistoryAction {
  id: string
  submission_id: string
  submission_version: number
  kind: ReviewActionKind
  reason: string
  created_event_sequence: number
}

export interface ReviewHistoryPage {
  review_actions: ReviewHistoryAction[]
  next_sequence: number
  has_more: boolean
}

// Agent turn 相关
export type AgentAvailability = 'AVAILABLE' | 'UNAVAILABLE'

export interface AgentTurn {
  id: string
  provider_mode: string
  response_text: string
  availability: AgentAvailability
  event_sequence: number
}

export type ProposalStatus = 'PROPOSED' | 'ACCEPTED' | 'REJECTED'

export interface ProposedAction {
  id: string
  kind: 'FILE_PATCH_PREVIEW'
  target_artifact_ref: string
  status: ProposalStatus
  diff: string
  decision_event_sequence?: number
}

// API 响应信封
export interface ApiEnvelope<T> {
  schema_version: string
  request_id: string
  data: T
  revision?: number
}

export interface ApiResult<T> {
  data: T
  revision?: number
  requestId: string
}
