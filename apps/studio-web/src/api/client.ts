import {
  WorkspaceApiError,
  API_VERSION,
  API_ROOT,
  ALLOWED_ARTIFACTS,
} from './types'
import type {
  ApiResult,
  Assignment,
  CreateAssignmentRequest,
  AgentTurn,
  EvidenceEvent,
  ProposedAction,
  Remediation,
  ReviewHistoryPage,
  Submission,
  Workspace,
} from './models'

// ---------------------------------------------------------------------------
// 类型守卫（DTO 验证）
// ---------------------------------------------------------------------------

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function hasText(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
}

function hasRevision(value: unknown): value is number {
  return Number.isInteger(value) && (value as number) >= 1
}

function hasOneOf<T extends string>(
  value: unknown,
  choices: readonly T[],
): value is T {
  return choices.includes(value as T)
}

function isArtifactReference(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    hasText(value.id) &&
    hasOneOf(value.logical_name, ALLOWED_ARTIFACTS as unknown as string[]) &&
    hasOneOf(value.media_type, [
      'text/x-python',
      'text/csv',
      'text/markdown',
    ]) &&
    value.source === 'FIXED_SYNTHETIC' &&
    value.integrity_status === 'NOT_COMPUTED'
  )
}

function isWorkspace(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    hasText(value.id) &&
    hasText(value.assignment_id) &&
    hasRevision(value.assignment_version) &&
    hasOneOf(value.state, [
      'ASSIGNED',
      'IN_PROGRESS',
      'PAUSED',
      'REVIEW_REQUIRED',
      'FEEDBACK_REQUIRED',
      'RESUBMITTED',
      'CLOSED',
    ]) &&
    hasRevision(value.revision) &&
    value.execution_enabled === false &&
    Array.isArray(value.artifact_refs) &&
    value.artifact_refs.every(isArtifactReference)
  )
}

function isTask(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    hasText(value.id) &&
    hasText(value.task_id) &&
    hasRevision(value.version) &&
    hasText(value.title) &&
    hasText(value.goal) &&
    hasOneOf(value.collaboration_mode, [
      'QA_ONLY',
      'PROPOSE_WITH_STUDENT_CONFIRMATION',
    ]) &&
    hasText(value.student_responsibility) &&
    Array.isArray(value.submission_requirements) &&
    value.submission_requirements.length > 0 &&
    value.submission_requirements.every(hasText) &&
    value.starter_project_id === 'orders-audit-v1' &&
    value.execution_enabled === false
  )
}

function isAssignment(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    hasText(value.id) &&
    hasRevision(value.version) &&
    hasOneOf(value.state, ['DRAFT', 'PUBLISHED', 'ARCHIVED']) &&
    hasRevision(value.revision) &&
    isTask(value.task) &&
    (value.workspace === null || isWorkspace(value.workspace)) &&
    hasText(value.demo_notice)
  )
}

async function isArtifactSnapshot(value: unknown): Promise<boolean> {
  if (!isRecord(value)) return false
  if (
    !hasOneOf(
      value.logical_name,
      ALLOWED_ARTIFACTS as unknown as string[],
    ) ||
    !hasOneOf(value.media_type, ['text/x-python', 'text/csv', 'text/markdown'])
  )
    return false
  if (
    !Number.isInteger(value.size_bytes) ||
    (value.size_bytes as number) < 0 ||
    (value.size_bytes as number) > 8192
  )
    return false
  if (typeof value.content !== 'string') return false
  if (
    new TextEncoder().encode(value.content).length !==
    (value.size_bytes as number)
  )
    return false
  if (typeof value.sha256 !== 'string') return false
  if (!/^[0-9a-f]{64}$/.test(value.sha256)) return false
  if (typeof globalThis.crypto?.subtle?.digest !== 'function') return false
  const digest = await globalThis.crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(value.content),
  )
  const actualSha256 = Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('')
  return actualSha256 === value.sha256
}

async function isSubmission(value: unknown): Promise<boolean> {
  if (!isRecord(value)) return false
  if (
    !hasText(value.id) ||
    !hasText(value.workspace_id) ||
    !hasRevision(value.workspace_revision) ||
    !hasRevision(value.assignment_version) ||
    !hasRevision(value.version)
  )
    return false
  if (
    !Array.isArray(value.artifact_refs) ||
    value.artifact_refs.length === 0 ||
    value.artifact_refs.length > ALLOWED_ARTIFACTS.length ||
    !value.artifact_refs.every(isArtifactReference)
  )
    return false
  if (
    !Array.isArray(value.artifact_snapshots) ||
    value.artifact_snapshots.length === 0 ||
    value.artifact_snapshots.length > ALLOWED_ARTIFACTS.length
  )
    return false
  const snapshotsValid = await Promise.all(
    value.artifact_snapshots.map(isArtifactSnapshot),
  )
  if (!snapshotsValid.every(Boolean)) return false
  if (!hasText(value.student_explanation)) return false
  if (!hasRevision(value.created_event_sequence)) return false
  return hasOneOf(value.state, [
    'SUBMITTED',
    'RESUBMITTED',
    'FEEDBACK_REQUIRED',
    'ACCEPTED',
  ])
}

function isEvidenceEvent(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    hasText(value.event_id) &&
    hasRevision(value.sequence) &&
    value.schema_version === 'evidence-event/v1' &&
    hasText(value.workspace_id) &&
    hasOneOf(value.actor_role, ['teacher', 'student']) &&
    hasText(value.event_type) &&
    hasText(value.resource_ref) &&
    hasText(value.request_id) &&
    hasText(value.occurred_at)
  )
}

function isRemediation(value: unknown): boolean {
  if (!isRecord(value)) return false
  if (
    !hasText(value.id) ||
    !hasText(value.review_action_id) ||
    !hasText(value.submission_id)
  )
    return false
  if (
    !hasOneOf(value.requested_action, [
      'REQUEST_EXPLANATION',
      'REQUEST_EVIDENCE',
      'REQUEST_REMEDIATION',
      'ENVIRONMENT_ISSUE',
    ])
  )
    return false
  if (!hasText(value.reason)) return false
  if (!hasOneOf(value.state, ['OPEN', 'RESPONDED', 'CLOSED'])) return false
  if (
    value.response_submission_id !== undefined &&
    !hasText(value.response_submission_id)
  )
    return false
  if (value.state === 'RESPONDED' && !hasText(value.response_submission_id))
    return false
  return true
}

function hasExactKeys(
  value: unknown,
  keys: string[],
): value is Record<string, unknown> {
  if (!isRecord(value)) return false
  return (
    Object.keys(value).length === keys.length &&
    keys.every((key) => Object.hasOwn(value, key))
  )
}

const REVIEW_ACTION_KINDS = Object.freeze([
  'ACKNOWLEDGE',
  'REQUEST_EXPLANATION',
  'REQUEST_EVIDENCE',
  'REQUEST_REMEDIATION',
  'ENVIRONMENT_ISSUE',
])

function isReviewHistoryAction(value: unknown): boolean {
  if (
    !hasExactKeys(value, [
      'id',
      'submission_id',
      'submission_version',
      'kind',
      'reason',
      'created_event_sequence',
    ])
  )
    return false
  if (!hasText(value.id) || !hasText(value.submission_id)) return false
  if (!hasRevision(value.submission_version)) return false
  if (!hasOneOf(value.kind, REVIEW_ACTION_KINDS)) return false
  if (!hasText(value.reason)) return false
  if (value.reason.length > 1024) return false
  if ((value.reason.match(/\S/g) || []).length < 8) return false
  return hasRevision(value.created_event_sequence)
}

function isReviewHistoryPage(
  value: unknown,
  opts: { afterSequence: number; limit: number },
): boolean {
  if (
    !hasExactKeys(value, ['review_actions', 'next_sequence', 'has_more'])
  )
    return false
  if (!Array.isArray(value.review_actions)) return false
  if (value.review_actions.length > opts.limit) return false
  if (!Number.isSafeInteger(value.next_sequence)) return false
  if ((value.next_sequence as number) < opts.afterSequence) return false
  if (typeof value.has_more !== 'boolean') return false
  if (!value.review_actions.every(isReviewHistoryAction)) return false
  const sequences = value.review_actions.map(
    (a: { created_event_sequence: number }) => a.created_event_sequence,
  )
  for (let i = 0; i < sequences.length; i++) {
    if (sequences[i] <= opts.afterSequence) return false
    if (i > 0 && sequences[i] <= sequences[i - 1]) return false
  }
  const expectedNext = sequences.length
    ? sequences[sequences.length - 1]
    : opts.afterSequence
  if (value.next_sequence !== expectedNext) return false
  if (value.has_more && value.review_actions.length !== opts.limit) return false
  return true
}

async function isLatestSubmission(
  value: unknown,
  workspaceId: string,
): Promise<boolean> {
  if (value === null) return true
  if (!(await isSubmission(value))) return false
  const sub = value as Submission
  if (sub.workspace_id !== workspaceId) return false
  const refNames = sub.artifact_refs.map((a) => a.logical_name)
  const snapNames = sub.artifact_snapshots.map((a) => a.logical_name)
  const refSet = new Set(refNames)
  const snapSet = new Set(snapNames)
  if (refSet.size !== refNames.length) return false
  if (snapSet.size !== snapNames.length) return false
  if (refSet.size !== snapSet.size) return false
  const refMedia = new Map(
    sub.artifact_refs.map((a) => [a.logical_name, a.media_type]),
  )
  const snapMedia = new Map(
    sub.artifact_snapshots.map((a) => [a.logical_name, a.media_type]),
  )
  for (const name of refSet) {
    if (!snapSet.has(name)) return false
    if (refMedia.get(name) !== snapMedia.get(name)) return false
  }
  return true
}

async function isSubmissionForRequest(
  value: unknown,
  workspaceId: string,
  dto: {
    artifact_refs: string[]
    artifact_contents: Record<string, string>
    student_explanation: string
  },
): Promise<boolean> {
  if (!(await isSubmission(value))) return false
  const sub = value as Submission
  if (sub.workspace_id !== workspaceId) return false
  if (sub.student_explanation !== dto.student_explanation) return false
  if (sub.artifact_refs.length !== dto.artifact_refs.length) return false
  if (sub.artifact_snapshots.length !== dto.artifact_refs.length) return false
  if (
    sub.artifact_refs.some(
      (item) => !dto.artifact_refs.includes(item.logical_name),
    )
  )
    return false
  if (
    sub.artifact_snapshots.some(
      (snapshot) => dto.artifact_contents[snapshot.logical_name] !== snapshot.content,
    )
  )
    return false
  const refNames = new Set(sub.artifact_refs.map((a) => a.logical_name))
  const snapNames = new Set(sub.artifact_snapshots.map((a) => a.logical_name))
  for (const name of refNames) {
    if (!snapNames.has(name)) return false
  }
  const expectedState = sub.version === 1 ? 'SUBMITTED' : 'RESUBMITTED'
  return sub.state === expectedState
}

// ---------------------------------------------------------------------------
// 幂等键工厂
// ---------------------------------------------------------------------------

function defaultIdempotencyKey(): string {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `demo-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

// ---------------------------------------------------------------------------
// 客户端工厂
// ---------------------------------------------------------------------------

export type ClientRole = 'teacher' | 'student'

export interface ClientOptions {
  fetchImpl?: typeof globalThis.fetch
  idempotencyKeyFactory?: () => string
  apiRoot?: string
}

export interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: Record<string, unknown>
  revision?: number
  key?: string
  validateData?: (data: unknown) => boolean | Promise<boolean>
}

export function createWorkspaceClient(
  role: ClientRole,
  options: ClientOptions = {},
) {
  const {
    fetchImpl = globalThis.fetch,
    idempotencyKeyFactory = defaultIdempotencyKey,
    apiRoot = API_ROOT,
  } = options

  if (!['teacher', 'student'].includes(role)) {
    throw new TypeError('unsupported demo role')
  }
  if (typeof fetchImpl !== 'function') {
    throw new TypeError('fetch is unavailable')
  }

  const root = `${apiRoot}/${role}`
  const pendingKeys = new Map<string, string>()

  async function request<T = unknown>(
    path: string,
    opts: RequestOptions = {},
  ): Promise<ApiResult<T>> {
    const { method = 'GET', body, revision, key, validateData } = opts
    const operationKey = `${method}:${path}`
    const requestKey =
      method === 'GET'
        ? undefined
        : (key ?? pendingKeys.get(operationKey) ?? idempotencyKeyFactory())

    const headers: Record<string, string> = { Accept: 'application/json' }
    const init: RequestInit = { method, headers, cache: 'no-store', credentials: 'omit' }

    if (method !== 'GET') {
      headers['Content-Type'] = 'application/json; charset=utf-8'
      headers['Idempotency-Key'] = requestKey!
      pendingKeys.set(operationKey, requestKey!)
      if (revision !== undefined && revision !== null) {
        headers['If-Match'] = String(revision)
      }
      init.body = JSON.stringify({
        ...(body ?? {}),
        schema_version: API_VERSION,
      })
    }

    let response: Response
    try {
      response = await fetchImpl(`${root}${path}`, init)
    } catch {
      throw new WorkspaceApiError({ idempotencyKey: requestKey })
    }

    let envelope: {
      schema_version?: string
      request_id?: string
      data?: unknown
      revision?: number
      error?: { code?: string; message?: string; retryable?: boolean }
    }
    try {
      envelope = (await response.json()) as typeof envelope
    } catch {
      throw new WorkspaceApiError({
        status: response.status,
        code: 'invalid_response',
        message: '服务返回了无法读取的响应。',
        retryable: false,
        idempotencyKey: requestKey,
      })
    }

    if (!response.ok || envelope?.error) {
      const apiError = envelope?.error ?? {}
      if (response.status < 500) pendingKeys.delete(operationKey)
      throw new WorkspaceApiError({
        status: response.status,
        code: apiError.code ?? 'http_error',
        message: apiError.message ?? '服务拒绝了本次请求。',
        retryable: Boolean(apiError.retryable),
        idempotencyKey: requestKey,
        definitiveRejection: response.status >= 400 && response.status < 500,
      })
    }

    let validData = isRecord(envelope?.data)
    if (validData && validateData) {
      try {
        validData = Boolean(await validateData(envelope.data))
      } catch {
        validData = false
      }
    }

    if (
      !envelope ||
      envelope.schema_version !== 'skillshift-api/v1' ||
      !hasText(envelope.request_id) ||
      !validData
    ) {
      throw new WorkspaceApiError({
        status: response.status,
        code: 'invalid_response',
        message: '服务响应格式不符合本机合成 DTO。',
        retryable: false,
        idempotencyKey: requestKey,
      })
    }

    // 修订号一致性检查（仅写操作）
    const data = envelope.data as Record<string, unknown>
    const responseRevisionMismatch =
      envelope.revision !== undefined &&
      (!hasRevision(envelope.revision) ||
        (hasRevision(data.workspace_revision) &&
          data.workspace_revision !== envelope.revision) ||
        (isRecord(data.assignment) &&
          hasRevision(data.assignment.revision) &&
          data.assignment.revision !== envelope.revision) ||
        (!data.assignment &&
          isRecord(data.workspace) &&
          hasRevision(data.workspace.revision) &&
          data.workspace.revision !== envelope.revision))

    if (method !== 'GET' && responseRevisionMismatch) {
      throw new WorkspaceApiError({
        status: response.status,
        code: 'invalid_response',
        message: '服务写入回执中的修订号无效或不一致；请求状态未确认。',
        retryable: false,
        idempotencyKey: requestKey,
      })
    }

    pendingKeys.delete(operationKey)
    return {
      data: envelope.data as T,
      revision: envelope.revision,
      requestId: envelope.request_id,
    }
  }

  // -------------------------------------------------------------------------
  // 公共 API
  // -------------------------------------------------------------------------

  return Object.freeze({
    // --- 任务 / 作业 ---
    listAssignments: () =>
      request<{ assignments: Assignment[] }>('/assignments', {
        validateData: (data) => {
          const d = data as { assignments: unknown[] }
          return (
            Array.isArray(d.assignments) &&
            d.assignments.every(isAssignment) &&
            new Set(d.assignments.map((a) => (a as Assignment).id)).size ===
              d.assignments.length
          )
        },
      }),

    getAssignment: (assignmentId: string) =>
      request<Assignment>(`/assignments/${encodeURIComponent(assignmentId)}`, {
        validateData: (data) => isAssignment(data) && (data as Assignment).id === assignmentId,
      }),

    createAssignment: (dto: CreateAssignmentRequest) =>
      request<Assignment>('/assignments', {
        method: 'POST',
        body: { ...dto },
        validateData: (data) =>
          isAssignment(data) &&
          (data as Assignment).state === 'DRAFT' &&
          (data as Assignment).workspace === null,
      }),

    publishAssignment: (assignmentId: string, revision: number) =>
      request<{ assignment: Assignment; workspace: Workspace; event: { sequence: number } }>(
        `/assignments/${encodeURIComponent(assignmentId)}/publish`,
        {
          method: 'POST',
          body: { schema_version: API_VERSION },
          revision,
          validateData: (data) => {
            const d = data as {
              assignment: Assignment
              workspace: Workspace
              event: { sequence: number }
            }
            return (
              isAssignment(d.assignment) &&
              d.assignment.id === assignmentId &&
              d.assignment.state === 'PUBLISHED' &&
              isWorkspace(d.workspace) &&
              d.workspace.assignment_id === assignmentId &&
              d.workspace.state === 'ASSIGNED' &&
              d.assignment.workspace?.id === d.workspace.id &&
              isRecord(d.event) &&
              hasRevision(d.event.sequence)
            )
          },
        },
      ),

    // --- 复核 ---
    reviewQueue: (
      assignmentId: string,
      expectedWorkspaceId: string | null = null,
      expectedAssignmentVersion: number | null = null,
    ) =>
      request<{ submissions: Submission[] }>(
        `/assignments/${encodeURIComponent(assignmentId)}/review-queue`,
        {
          validateData: async (data) => {
            const d = data as { submissions: Submission[] }
            if (!Array.isArray(d.submissions)) return false
            const allValid = await Promise.all(d.submissions.map(isSubmission))
            if (!allValid.every(Boolean)) return false
            return d.submissions.every((sub) => {
              if (!['SUBMITTED', 'RESUBMITTED'].includes(sub.state))
                return false
              if (expectedWorkspaceId && sub.workspace_id !== expectedWorkspaceId)
                return false
              if (
                expectedAssignmentVersion !== null &&
                sub.assignment_version !== expectedAssignmentVersion
              )
                return false
              return true
            })
          },
        },
      ),

    reviewHistory: (
      assignmentId: string,
      afterSequence = 0,
      limit = 50,
    ) => {
      if (role !== 'teacher') {
        throw new TypeError(
          'review history is available only to the fixed teacher demo client',
        )
      }
      if (!hasText(assignmentId)) {
        throw new TypeError('assignmentId must be non-empty text')
      }
      if (!Number.isSafeInteger(afterSequence) || afterSequence < 0) {
        throw new TypeError('afterSequence must be a non-negative safe integer')
      }
      if (!Number.isInteger(limit) || limit < 1 || limit > 50) {
        throw new TypeError('limit must be an integer from 1 to 50')
      }
      const query = `after_sequence=${encodeURIComponent(afterSequence)}&limit=${encodeURIComponent(limit)}`
      return request<ReviewHistoryPage>(
        `/assignments/${encodeURIComponent(assignmentId)}/review-history?${query}`,
        {
          validateData: (data) =>
            isReviewHistoryPage(data, { afterSequence, limit }),
        },
      )
    },

    // --- Workspace ---
    getWorkspace: async (
      workspaceId: string,
      expectedAssignmentId: string | null = null,
    ) => {
      const result = await request<Workspace>(
        `/workspaces/${encodeURIComponent(workspaceId)}`,
        {
          validateData: (data) =>
            isWorkspace(data) &&
            (data as Workspace).id === workspaceId &&
            (!expectedAssignmentId ||
              (data as Workspace).assignment_id === expectedAssignmentId),
        },
      )
      if (result.data.state === 'IN_PROGRESS') {
        pendingKeys.delete(
          `POST:/workspaces/${encodeURIComponent(workspaceId)}/start`,
        )
      }
      return result
    },

    latestSubmission: (workspaceId: string) =>
      request<{ submission: Submission | null }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/submissions/latest`,
        {
          validateData: async (data) => {
            const d = data as { submission: Submission | null }
            if (!hasExactKeys(d, ['submission'])) return false
            return isLatestSubmission(d.submission, workspaceId)
          },
        },
      ),

    startWorkspace: (
      workspaceId: string,
      revision: number,
      expectedAssignmentId: string | null = null,
    ) =>
      request<{ workspace: Workspace; event: EvidenceEvent }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/start`,
        {
          method: 'POST',
          body: { schema_version: API_VERSION },
          revision,
          validateData: (data) => {
            const d = data as { workspace: Workspace; event: EvidenceEvent }
            return (
              isWorkspace(d.workspace) &&
              d.workspace.id === workspaceId &&
              (!expectedAssignmentId ||
                d.workspace.assignment_id === expectedAssignmentId) &&
              d.workspace.state === 'IN_PROGRESS' &&
              isEvidenceEvent(d.event)
            )
          },
        },
      ),

    pauseWorkspace: (
      workspaceId: string,
      revision: number,
      expectedAssignmentId: string | null = null,
    ) =>
      request<{ workspace: Workspace; event: EvidenceEvent }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/pause`,
        {
          method: 'POST',
          body: { schema_version: API_VERSION },
          revision,
          validateData: (data) => {
            const d = data as { workspace: Workspace; event: EvidenceEvent }
            return (
              isWorkspace(d.workspace) &&
              d.workspace.id === workspaceId &&
              (!expectedAssignmentId ||
                d.workspace.assignment_id === expectedAssignmentId) &&
              d.workspace.state === 'PAUSED' &&
              isEvidenceEvent(d.event)
            )
          },
        },
      ),

    // --- Agent ---
    agentTurn: (workspaceId: string, question: string, revision: number) =>
      request<{
        turn: AgentTurn
        workspace_revision: number
        proposed_action?: ProposedAction
      }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/agent-turns`,
        {
          method: 'POST',
          body: { question, schema_version: API_VERSION },
          revision,
          validateData: (data) => {
            const d = data as {
              turn: AgentTurn
              workspace_revision: number
              proposed_action?: ProposedAction
            }
            if (!isRecord(d.turn)) return false
            if (!hasText(d.turn.id)) return false
            if (d.turn.provider_mode !== 'scripted-demo') return false
            if (typeof d.turn.response_text !== 'string') return false
            if (!['AVAILABLE', 'UNAVAILABLE'].includes(d.turn.availability))
              return false
            if (!hasRevision(d.turn.event_sequence)) return false
            if (!hasRevision(d.workspace_revision)) return false
            if (d.proposed_action !== undefined) {
              const pa = d.proposed_action
              if (!isRecord(pa)) return false
              if (!hasText(pa.id)) return false
              if (pa.kind !== 'FILE_PATCH_PREVIEW') return false
              if (!hasText(pa.target_artifact_ref)) return false
              if (pa.status !== 'PROPOSED') return false
              if (typeof pa.diff !== 'string') return false
              if (pa.diff.length > 4096) return false
            }
            return true
          },
        },
      ),

    decideProposal: (
      workspaceId: string,
      proposalId: string,
      decision: 'ACCEPTED' | 'REJECTED',
      revision: number,
    ) =>
      request<{ proposed_action: ProposedAction; workspace_revision: number }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/proposed-actions/${encodeURIComponent(proposalId)}/decision`,
        {
          method: 'POST',
          body: { decision, schema_version: API_VERSION },
          revision,
          validateData: (data) => {
            const d = data as {
              proposed_action: ProposedAction
              workspace_revision: number
            }
            if (!isRecord(d.proposed_action)) return false
            if (d.proposed_action.id !== proposalId) return false
            if (d.proposed_action.kind !== 'FILE_PATCH_PREVIEW') return false
            if (d.proposed_action.status !== decision) return false
            if (!hasText(d.proposed_action.target_artifact_ref)) return false
            if (typeof d.proposed_action.diff !== 'string') return false
            if (!hasRevision(d.proposed_action.decision_event_sequence))
              return false
            if (!hasRevision(d.workspace_revision)) return false
            return true
          },
        },
      ),

    // --- 提交 ---
    submit: (
      workspaceId: string,
      dto: {
        schema_version: string
        artifact_refs: string[]
        artifact_contents: Record<string, string>
        student_explanation: string
      },
      revision: number,
    ) =>
      request<{ submission: Submission; workspace_revision: number }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/submissions`,
        {
          method: 'POST',
          body: dto,
          revision,
          validateData: async (data) => {
            const d = data as {
              submission: Submission
              workspace_revision: number
            }
            const subOk = await isSubmissionForRequest(
              d.submission,
              workspaceId,
              dto,
            )
            return subOk && hasRevision(d.workspace_revision)
          },
        },
      ),

    // --- 补正 ---
    remediations: (workspaceId: string) =>
      request<{ remediations: Remediation[] }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/remediation`,
        {
          validateData: (data) => {
            const d = data as { remediations: Remediation[] }
            return (
              Array.isArray(d.remediations) &&
              d.remediations.every(isRemediation)
            )
          },
        },
      ),

    // --- 事件 ---
    events: (workspaceId: string, afterSequence = 0, limit = 50) =>
      request<{ events: EvidenceEvent[]; next_sequence: number; has_more: boolean }>(
        `/workspaces/${encodeURIComponent(workspaceId)}/events?after_sequence=${encodeURIComponent(afterSequence)}&limit=${encodeURIComponent(limit)}`,
        {
          validateData: (data) => {
            const d = data as {
              events: EvidenceEvent[]
              next_sequence: number
              has_more: boolean
            }
            if (!Array.isArray(d.events)) return false
            if (d.events.length > 50) return false
            if (!d.events.every(isEvidenceEvent)) return false
            if (!Number.isInteger(d.next_sequence)) return false
            if (d.next_sequence < 0) return false
            if (typeof d.has_more !== 'boolean') return false
            return true
          },
        },
      ),

    // --- 教师复核 ---
    review: (
      submissionId: string,
      dto: { schema_version: string; kind: string; reason: string },
      revision: number,
      expectedSubmissionVersion: number,
    ) =>
      request<{
        review_action: {
          id: string
          submission_id: string
          submission_version: number
          kind: string
          reason: string
          created_event_sequence: number
        }
        workspace_revision: number
      }>(
        `/submissions/${encodeURIComponent(submissionId)}/review-actions`,
        {
          method: 'POST',
          body: dto,
          revision,
          validateData: (data) => {
            const d = data as {
              review_action: {
                id: string
                submission_id: string
                submission_version: number
                kind: string
                reason: string
                created_event_sequence: number
              }
              workspace_revision: number
            }
            if (!isRecord(d.review_action)) return false
            if (!hasText(d.review_action.id)) return false
            if (d.review_action.submission_id !== submissionId) return false
            if (!hasRevision(expectedSubmissionVersion)) return false
            if (d.review_action.submission_version !== expectedSubmissionVersion)
              return false
            if (d.review_action.kind !== dto.kind) return false
            if (d.review_action.reason !== dto.reason) return false
            if (!hasRevision(d.review_action.created_event_sequence))
              return false
            if (!hasRevision(d.workspace_revision)) return false
            return true
          },
        },
      ),
  })
}

export type WorkspaceClient = ReturnType<typeof createWorkspaceClient>
