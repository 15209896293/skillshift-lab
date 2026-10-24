import { API_VERSION, ALLOWED_ARTIFACTS } from './types'
import type { AllowedArtifact } from './types'

// ---------------------------------------------------------------------------
// 表单 → DTO 映射
// ---------------------------------------------------------------------------

export type TaskFormMode = 'qa' | 'propose'

export interface TaskFormData {
  title: string
  goal: string
  responsibility: string
  deliverable: string
  mode: TaskFormMode
}

export function mapTaskFormToCreateDto(task: TaskFormData) {
  const collaborationMode =
    task.mode === 'qa' ? 'QA_ONLY' : 'PROPOSE_WITH_STUDENT_CONFIRMATION'
  return {
    schema_version: API_VERSION,
    title: String(task.title || '').trim(),
    goal: String(task.goal || '').trim(),
    student_responsibility: String(task.responsibility || '').trim(),
    submission_requirement: String(task.deliverable || '').trim(),
    starter_project_id: 'orders-audit-v1',
    collaboration_mode: collaborationMode,
  }
}

// --- 复核动作映射 ---
export type ReviewActionType =
  | 'approve'
  | 'explanation'
  | 'evidence'
  | 'remediation'
  | 'environment'

const REVIEW_KIND_MAP: Record<ReviewActionType, string> = {
  approve: 'ACKNOWLEDGE',
  explanation: 'REQUEST_EXPLANATION',
  evidence: 'REQUEST_EVIDENCE',
  remediation: 'REQUEST_REMEDIATION',
  environment: 'ENVIRONMENT_ISSUE',
}

export function mapReviewActionToDto(
  action: ReviewActionType,
  reason: string,
) {
  const kind = REVIEW_KIND_MAP[action]
  if (!kind) throw new TypeError('unknown review action')
  return {
    schema_version: API_VERSION,
    kind,
    reason: String(reason || '').trim(),
  }
}

// --- 提交文件映射 ---
export function mapFilesToSubmissionDto(
  files: Partial<Record<AllowedArtifact, string>>,
  explanation: string,
) {
  const names = Object.keys(files).filter(
    (name) => ALLOWED_ARTIFACTS.includes(name as AllowedArtifact),
  ) as AllowedArtifact[]
  if (!names.length) {
    throw new TypeError('提交必须至少包含一个工件文件。')
  }
  const artifactContents = Object.fromEntries(
    names.map((name) => [name, String(files[name] ?? '')]),
  ) as Record<string, string>
  return {
    schema_version: API_VERSION,
    artifact_refs: names,
    artifact_contents: artifactContents,
    student_explanation: String(explanation || '').trim(),
  }
}

// ---------------------------------------------------------------------------
// 复核结果确认（写后读回验证）
// ---------------------------------------------------------------------------

import type { WorkspaceClient } from './client'
import type { Submission } from './models'

export async function confirmReviewOutcome(
  client: WorkspaceClient,
  submission: Submission | null | undefined,
  reviewDto: { kind: string; reason: string },
): Promise<boolean> {
  if (!submission || !submission.workspace_id || !submission.id) return false
  const workspace = (await client.getWorkspace(submission.workspace_id)).data
  if (workspace.id !== submission.workspace_id) return false
  // ACKNOWLEDGE 不改变 workspace 状态，无法通过状态验证
  if (reviewDto.kind === 'ACKNOWLEDGE') return false
  if (workspace.state !== 'FEEDBACK_REQUIRED') return false
  const remediations = (await client.remediations(submission.workspace_id)).data
    .remediations
  return remediations.some(
    (item) =>
      item.state === 'OPEN' &&
      item.submission_id === submission.id &&
      item.requested_action === reviewDto.kind &&
      item.reason === reviewDto.reason,
  )
}
