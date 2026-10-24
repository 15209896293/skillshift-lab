const API_ROOT = "/api/v1/demo";
const API_VERSION = "skillshift-api/v1";
export const ALLOWED_ARTIFACTS = Object.freeze(["main.py", "orders.csv", "README.md"]);

export class WorkspaceApiError extends Error {
  constructor({ status = 0, code = "service_unavailable", message, retryable = true, idempotencyKey, definitiveRejection = false } = {}) {
    super(message || "本机合成服务暂不可用，请稍后重试。", { cause: undefined });
    this.name = "WorkspaceApiError";
    this.status = status;
    this.code = code;
    this.retryable = retryable;
    this.idempotencyKey = idempotencyKey;
    this.definitiveRejection = definitiveRejection;
  }
}

export function mapTaskFormToCreateDto(task) {
  const collaborationMode = task.mode === "qa" ? "QA_ONLY" : "PROPOSE_WITH_STUDENT_CONFIRMATION";
  return {
    schema_version: API_VERSION,
    title: String(task.title || "").trim(),
    goal: String(task.goal || "").trim(),
    student_responsibility: String(task.responsibility || "").trim(),
    submission_requirement: String(task.deliverable || "").trim(),
    starter_project_id: "orders-audit-v1",
    collaboration_mode: collaborationMode,
  };
}

export function mapReviewActionToDto(action, reason) {
  const kinds = {
    approve: "ACKNOWLEDGE",
    explanation: "REQUEST_EXPLANATION",
    evidence: "REQUEST_EVIDENCE",
    remediation: "REQUEST_REMEDIATION",
    environment: "ENVIRONMENT_ISSUE",
  };
  const kind = kinds[action];
  if (!kind) throw new TypeError("unknown review action");
  return { schema_version: API_VERSION, kind, reason: String(reason || "").trim() };
}

export function mapFilesToSubmissionDto(files, explanation) {
  const names = Object.keys(files || {});
  if (!names.length || names.some((name) => !ALLOWED_ARTIFACTS.includes(name))) {
    throw new TypeError("提交只能包含固定合成项目 allowlist 文件。");
  }
  const artifactContents = Object.fromEntries(names.map((name) => [name, String(files[name])]));
  return {
    schema_version: API_VERSION,
    artifact_refs: names,
    artifact_contents: artifactContents,
    student_explanation: String(explanation || "").trim(),
  };
}

export function errorStateFor(error, operation = "请求") {
  if (!(error instanceof WorkspaceApiError)) {
    return { kind: "error", message: `${operation}没有收到成功回执；状态未确认，请刷新核对。` };
  }
  if (error.status === 0 || error.status >= 500 || ["service_unavailable", "invalid_response"].includes(error.code)) {
    return { kind: "unavailable", message: `${operation}没有收到 API 成功回执；请求状态未确认，请刷新核对后再操作。` };
  }
  if (error.code === "stale_revision" || error.code === "stale_submission") {
    return { kind: "conflict", message: `${operation}遇到版本冲突，请刷新后核对当前状态；没有覆盖已有内容。` };
  }
  if (error.code === "idempotency_conflict") {
    return { kind: "conflict", message: `${operation}请求编号与先前内容不一致，请刷新状态后再操作。` };
  }
  if (error.status === 409) {
    return { kind: "conflict", message: `${operation}遇到状态冲突，请刷新并核对当前状态后再操作。` };
  }
  return { kind: "rejected", message: `${operation}未通过校验：${error.message} 没有记录成功。` };
}

export async function confirmReviewOutcome(client, submission, reviewDto) {
  if (!submission || !hasText(submission.workspace_id) || !hasText(submission.id) || !isRecord(reviewDto)) return false;
  const workspace = (await client.getWorkspace(submission.workspace_id)).data;
  if (workspace.id !== submission.workspace_id) return false;
  // A closed workspace does not identify which submission/action caused the transition.
  if (reviewDto.kind === "ACKNOWLEDGE") return false;
  if (workspace.state !== "FEEDBACK_REQUIRED") return false;
  const remediations = (await client.remediations(submission.workspace_id)).data.remediations;
  return remediations.some((item) => item.state === "OPEN"
    && item.submission_id === submission.id
    && item.requested_action === reviewDto.kind
    && item.reason === reviewDto.reason);
}

const isRecord = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const hasText = (value) => typeof value === "string" && value.length > 0;
const hasRevision = (value) => Number.isInteger(value) && value >= 1;
const hasOneOf = (value, choices) => choices.includes(value);

function isWorkspace(value) {
  return isRecord(value)
    && hasText(value.id)
    && hasText(value.assignment_id)
    && hasRevision(value.assignment_version)
    && hasOneOf(value.state, ["ASSIGNED", "IN_PROGRESS", "PAUSED", "REVIEW_REQUIRED", "FEEDBACK_REQUIRED", "RESUBMITTED", "CLOSED"])
    && hasRevision(value.revision)
    && value.execution_enabled === false
    && Array.isArray(value.artifact_refs)
    && value.artifact_refs.every(isArtifactReference);
}

function isTask(value) {
  return isRecord(value)
    && hasText(value.id)
    && hasText(value.task_id)
    && hasRevision(value.version)
    && hasText(value.title)
    && hasText(value.goal)
    && hasOneOf(value.collaboration_mode, ["QA_ONLY", "PROPOSE_WITH_STUDENT_CONFIRMATION"])
    && hasText(value.student_responsibility)
    && Array.isArray(value.submission_requirements)
    && value.submission_requirements.length > 0
    && value.submission_requirements.every(hasText)
    && value.starter_project_id === "orders-audit-v1"
    && value.execution_enabled === false;
}

function isAssignment(value) {
  return isRecord(value)
    && hasText(value.id)
    && hasRevision(value.version)
    && hasOneOf(value.state, ["DRAFT", "PUBLISHED", "ARCHIVED"])
    && hasRevision(value.revision)
    && isTask(value.task)
    && (value.workspace === null || isWorkspace(value.workspace))
    && hasText(value.demo_notice);
}

function isArtifactReference(value) {
  return isRecord(value)
    && hasText(value.id)
    && hasOneOf(value.logical_name, ALLOWED_ARTIFACTS)
    && hasOneOf(value.media_type, ["text/x-python", "text/csv", "text/markdown"])
    && value.source === "FIXED_SYNTHETIC"
    && value.integrity_status === "NOT_COMPUTED";
}

async function isArtifactSnapshot(value) {
  if (!isRecord(value)
    || !hasOneOf(value.logical_name, ALLOWED_ARTIFACTS)
    || !hasOneOf(value.media_type, ["text/x-python", "text/csv", "text/markdown"])
    || !Number.isInteger(value.size_bytes)
    || value.size_bytes < 0
    || value.size_bytes > 8192
    || typeof value.content !== "string"
    || new TextEncoder().encode(value.content).length !== value.size_bytes
    || typeof value.sha256 !== "string"
    || !/^[0-9a-f]{64}$/.test(value.sha256)
    || typeof globalThis.crypto?.subtle?.digest !== "function") return false;
  const digest = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(value.content));
  const actualSha256 = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  return actualSha256 === value.sha256;
}

async function isSubmission(value) {
  return isRecord(value)
    && hasText(value.id)
    && hasText(value.workspace_id)
    && hasRevision(value.assignment_version)
    && hasRevision(value.version)
    && Array.isArray(value.artifact_refs)
    && value.artifact_refs.length > 0
    && value.artifact_refs.length <= ALLOWED_ARTIFACTS.length
    && value.artifact_refs.every(isArtifactReference)
    && Array.isArray(value.artifact_snapshots)
    && value.artifact_snapshots.length > 0
    && value.artifact_snapshots.length <= ALLOWED_ARTIFACTS.length
    && (await Promise.all(value.artifact_snapshots.map(isArtifactSnapshot))).every(Boolean)
    && hasText(value.student_explanation)
    && hasRevision(value.created_event_sequence)
    && hasOneOf(value.state, ["SUBMITTED", "RESUBMITTED", "FEEDBACK_REQUIRED", "ACCEPTED"]);
}

async function isSubmissionForRequest(value, workspaceId, dto) {
  if (!(await isSubmission(value))
    || value.workspace_id !== workspaceId
    || value.student_explanation !== dto.student_explanation
    || value.artifact_refs.length !== dto.artifact_refs.length
    || value.artifact_snapshots.length !== dto.artifact_refs.length
    || value.artifact_refs.some((item) => !dto.artifact_refs.includes(item.logical_name))
    || value.artifact_snapshots.some((item) => dto.artifact_contents[item.logical_name] !== item.content)) return false;
  return value.artifact_refs.every((item) => value.artifact_snapshots.some((snapshot) => snapshot.logical_name === item.logical_name))
    && value.state === (value.version === 1 ? "SUBMITTED" : "RESUBMITTED");
}

async function isLatestSubmission(value, workspaceId) {
  if (value === null) return true;
  if (!(await isSubmission(value)) || value.workspace_id !== workspaceId) return false;
  const referenceNames = value.artifact_refs.map((item) => item.logical_name);
  const snapshotNames = value.artifact_snapshots.map((item) => item.logical_name);
  const referenceSet = new Set(referenceNames);
  const snapshotSet = new Set(snapshotNames);
  const referenceMediaTypes = new Map(value.artifact_refs.map((item) => [item.logical_name, item.media_type]));
  const snapshotMediaTypes = new Map(value.artifact_snapshots.map((item) => [item.logical_name, item.media_type]));
  return referenceSet.size === referenceNames.length
    && snapshotSet.size === snapshotNames.length
    && referenceSet.size === snapshotSet.size
    && [...referenceSet].every((name) => snapshotSet.has(name)
      && referenceMediaTypes.get(name) === snapshotMediaTypes.get(name));
}

function isEvidenceEvent(value) {
  return isRecord(value)
    && hasText(value.event_id)
    && hasRevision(value.sequence)
    && value.schema_version === "evidence-event/v1"
    && hasText(value.workspace_id)
    && hasOneOf(value.actor_role, ["teacher", "student"])
    && hasText(value.event_type)
    && hasText(value.resource_ref)
    && hasText(value.request_id)
    && hasText(value.occurred_at);
}

function isRemediation(value) {
  return isRecord(value)
    && hasText(value.id)
    && hasText(value.review_action_id)
    && hasText(value.submission_id)
    && hasOneOf(value.requested_action, ["REQUEST_EXPLANATION", "REQUEST_EVIDENCE", "REQUEST_REMEDIATION", "ENVIRONMENT_ISSUE"])
    && hasText(value.reason)
    && hasOneOf(value.state, ["OPEN", "RESPONDED", "CLOSED"])
    && (value.response_submission_id === undefined || hasText(value.response_submission_id))
    && (value.state !== "RESPONDED" || hasText(value.response_submission_id));
}

const REVIEW_ACTION_KINDS = Object.freeze([
  "ACKNOWLEDGE",
  "REQUEST_EXPLANATION",
  "REQUEST_EVIDENCE",
  "REQUEST_REMEDIATION",
  "ENVIRONMENT_ISSUE",
]);

function hasExactKeys(value, keys) {
  return isRecord(value)
    && Object.keys(value).length === keys.length
    && keys.every((key) => Object.hasOwn(value, key));
}

function isReviewHistoryAction(value) {
  return hasExactKeys(value, ["id", "submission_id", "submission_version", "kind", "reason", "created_event_sequence"])
    && hasText(value.id)
    && hasText(value.submission_id)
    && hasRevision(value.submission_version)
    && hasOneOf(value.kind, REVIEW_ACTION_KINDS)
    && hasText(value.reason)
    && value.reason.length <= 1024
    && (value.reason.match(/\S/g) || []).length >= 8
    && hasRevision(value.created_event_sequence);
}

function isReviewHistoryPage(value, { afterSequence, limit }) {
  if (!hasExactKeys(value, ["review_actions", "next_sequence", "has_more"])
    || !Array.isArray(value.review_actions)
    || value.review_actions.length > limit
    || !Number.isSafeInteger(value.next_sequence)
    || value.next_sequence < afterSequence
    || typeof value.has_more !== "boolean"
    || !value.review_actions.every(isReviewHistoryAction)) return false;
  const sequences = value.review_actions.map((action) => action.created_event_sequence);
  if (sequences.some((sequence, index) => sequence <= afterSequence || (index > 0 && sequence <= sequences[index - 1]))) return false;
  const expectedNextSequence = sequences.length ? sequences[sequences.length - 1] : afterSequence;
  return value.next_sequence === expectedNextSequence
    && (!value.has_more || value.review_actions.length === limit);
}

function defaultIdempotencyKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `demo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function createWorkspaceClient(role, {
  fetchImpl = globalThis.fetch,
  idempotencyKeyFactory = defaultIdempotencyKey,
  apiRoot = API_ROOT,
} = {}) {
  if (!["teacher", "student"].includes(role)) throw new TypeError("unsupported demo role");
  if (typeof fetchImpl !== "function") throw new TypeError("fetch is unavailable");
  const root = `${apiRoot}/${role}`;
  const pendingKeys = new Map();

  async function request(path, { method = "GET", body, revision, key, validateData } = {}) {
    const operationKey = `${method}:${path}`;
    const requestKey = method === "GET" ? undefined : (key || pendingKeys.get(operationKey) || idempotencyKeyFactory());
    const headers = { Accept: "application/json" };
    const options = { method, headers, cache: "no-store", credentials: "omit" };
    if (method !== "GET") {
      headers["Content-Type"] = "application/json; charset=utf-8";
      headers["Idempotency-Key"] = requestKey;
      pendingKeys.set(operationKey, requestKey);
      if (revision !== undefined && revision !== null) headers["If-Match"] = String(revision);
      options.body = JSON.stringify({ ...(body || {}), schema_version: API_VERSION });
    }
    let response;
    try {
      response = await fetchImpl(`${root}${path}`, options);
    } catch {
      throw new WorkspaceApiError({ idempotencyKey: requestKey });
    }
    let envelope;
    try {
      envelope = await response.json();
    } catch {
      throw new WorkspaceApiError({ status: response.status, code: "invalid_response", message: "服务返回了无法读取的响应。", retryable: false, idempotencyKey: requestKey });
    }
    if (!response.ok || envelope?.error) {
      const apiError = envelope?.error || {};
      if (response.status < 500) pendingKeys.delete(operationKey);
      throw new WorkspaceApiError({
        status: response.status,
        code: apiError.code || "http_error",
        message: apiError.message || "服务拒绝了本次请求。",
        retryable: Boolean(apiError.retryable),
        idempotencyKey: requestKey,
        definitiveRejection: response.status >= 400 && response.status < 500,
      });
    }
    let validData = isRecord(envelope?.data);
    if (validData && validateData) {
      try {
        validData = await validateData(envelope.data);
      } catch {
        validData = false;
      }
    }
    if (!envelope || envelope.schema_version !== "skillshift-api/v1" || !hasText(envelope.request_id) || !validData) {
      throw new WorkspaceApiError({ status: response.status, code: "invalid_response", message: "服务响应格式不符合本机合成 DTO。", retryable: false, idempotencyKey: requestKey });
    }
    const responseRevisionMismatch = envelope.revision !== undefined && (
      !hasRevision(envelope.revision)
      || (hasRevision(envelope.data?.workspace_revision) && envelope.data.workspace_revision !== envelope.revision)
      || (hasRevision(envelope.data?.assignment?.revision) && envelope.data.assignment.revision !== envelope.revision)
      || (!envelope.data?.assignment && hasRevision(envelope.data?.workspace?.revision) && envelope.data.workspace.revision !== envelope.revision)
    );
    if (method !== "GET" && responseRevisionMismatch) {
      throw new WorkspaceApiError({ status: response.status, code: "invalid_response", message: "服务写入回执中的修订号无效或不一致；请求状态未确认。", retryable: false, idempotencyKey: requestKey });
    }
    pendingKeys.delete(operationKey);
    return { data: envelope.data, revision: envelope.revision, requestId: envelope.request_id };
  }

  return Object.freeze({
    listAssignments: () => request("/assignments", {
      validateData: (data) => Array.isArray(data.assignments)
        && data.assignments.every(isAssignment)
        && new Set(data.assignments.map((assignment) => assignment.id)).size === data.assignments.length,
    }),
    getAssignment: (assignmentId) => request(`/assignments/${encodeURIComponent(assignmentId)}`, {
      validateData: (data) => isAssignment(data) && data.id === assignmentId,
    }),
    createAssignment: (dto) => request("/assignments", {
      method: "POST", body: dto,
      validateData: (data) => isAssignment(data) && data.state === "DRAFT" && data.workspace === null,
    }),
    publishAssignment: (assignmentId, revision) => request(`/assignments/${encodeURIComponent(assignmentId)}/publish`, {
      method: "POST", body: { schema_version: API_VERSION }, revision,
      validateData: (data) => isAssignment(data.assignment)
        && data.assignment.id === assignmentId
        && data.assignment.state === "PUBLISHED"
        && isWorkspace(data.workspace)
        && data.workspace.assignment_id === assignmentId
        && data.workspace.state === "ASSIGNED"
        && data.assignment.workspace.id === data.workspace.id
        && isRecord(data.event)
        && hasRevision(data.event.sequence),
    }),
    reviewQueue: (assignmentId, expectedWorkspaceId = null, expectedAssignmentVersion = null) => request(`/assignments/${encodeURIComponent(assignmentId)}/review-queue`, {
      validateData: async (data) => Array.isArray(data.submissions)
        && (await Promise.all(data.submissions.map(isSubmission))).every(Boolean)
        && data.submissions.every((submission) =>
          ["SUBMITTED", "RESUBMITTED"].includes(submission.state)
          && (!expectedWorkspaceId || submission.workspace_id === expectedWorkspaceId)
          && (expectedAssignmentVersion === null || submission.assignment_version === expectedAssignmentVersion)),
    }),
    reviewHistory: (assignmentId, afterSequence = 0, limit = 50) => {
      if (role !== "teacher") throw new TypeError("review history is available only to the fixed teacher demo client");
      if (!hasText(assignmentId)) throw new TypeError("assignmentId must be non-empty text");
      if (!Number.isSafeInteger(afterSequence) || afterSequence < 0) throw new TypeError("afterSequence must be a non-negative safe integer");
      if (!Number.isInteger(limit) || limit < 1 || limit > 50) throw new TypeError("limit must be an integer from 1 to 50");
      const query = `after_sequence=${encodeURIComponent(afterSequence)}&limit=${encodeURIComponent(limit)}`;
      return request(`/assignments/${encodeURIComponent(assignmentId)}/review-history?${query}`, {
        validateData: (data) => isReviewHistoryPage(data, { afterSequence, limit }),
      });
    },
    getWorkspace: async (workspaceId, expectedAssignmentId = null) => {
      const result = await request(`/workspaces/${encodeURIComponent(workspaceId)}`, {
        validateData: (data) => isWorkspace(data) && data.id === workspaceId
          && (!expectedAssignmentId || data.assignment_id === expectedAssignmentId),
      });
      if (result.data.state === "IN_PROGRESS") {
        // A successful state read resolves an uncertain start; do not replay that key after a later pause.
        pendingKeys.delete(`POST:/workspaces/${encodeURIComponent(workspaceId)}/start`);
      }
      return result;
    },
    latestSubmission: (workspaceId) => request(`/workspaces/${encodeURIComponent(workspaceId)}/submissions/latest`, {
      validateData: async (data) => hasExactKeys(data, ["submission"]) && await isLatestSubmission(data.submission, workspaceId),
    }),
    startWorkspace: (workspaceId, revision, expectedAssignmentId = null) => request(`/workspaces/${encodeURIComponent(workspaceId)}/start`, {
      method: "POST", body: { schema_version: API_VERSION }, revision,
      validateData: (data) => isWorkspace(data.workspace) && data.workspace.id === workspaceId
        && (!expectedAssignmentId || data.workspace.assignment_id === expectedAssignmentId)
        && data.workspace.state === "IN_PROGRESS" && isEvidenceEvent(data.event),
    }),
    pauseWorkspace: (workspaceId, revision, expectedAssignmentId = null) => request(`/workspaces/${encodeURIComponent(workspaceId)}/pause`, {
      method: "POST", body: { schema_version: API_VERSION }, revision,
      validateData: (data) => isWorkspace(data.workspace) && data.workspace.id === workspaceId
        && (!expectedAssignmentId || data.workspace.assignment_id === expectedAssignmentId)
        && data.workspace.state === "PAUSED" && isEvidenceEvent(data.event),
    }),
    agentTurn: (workspaceId, question, revision) => request(`/workspaces/${encodeURIComponent(workspaceId)}/agent-turns`, {
      method: "POST", body: { question, schema_version: API_VERSION }, revision,
      validateData: (data) => isRecord(data.turn) && hasText(data.turn.id) && data.turn.provider_mode === "scripted-demo"
        && typeof data.turn.response_text === "string" && hasOneOf(data.turn.availability, ["AVAILABLE", "UNAVAILABLE"])
        && hasRevision(data.turn.event_sequence) && hasRevision(data.workspace_revision)
        && (data.proposed_action === undefined || (isRecord(data.proposed_action)
          && hasText(data.proposed_action.id) && data.proposed_action.kind === "FILE_PATCH_PREVIEW"
          && hasText(data.proposed_action.target_artifact_ref) && data.proposed_action.status === "PROPOSED"
          && typeof data.proposed_action.diff === "string" && data.proposed_action.diff.length <= 4096)),
    }),
    decideProposal: (workspaceId, proposalId, decision, revision) => request(`/workspaces/${encodeURIComponent(workspaceId)}/proposed-actions/${encodeURIComponent(proposalId)}/decision`, {
      method: "POST", body: { decision, schema_version: API_VERSION }, revision,
      validateData: (data) => isRecord(data.proposed_action) && data.proposed_action.id === proposalId
        && data.proposed_action.kind === "FILE_PATCH_PREVIEW" && data.proposed_action.status === decision
        && hasText(data.proposed_action.target_artifact_ref) && typeof data.proposed_action.diff === "string"
        && hasRevision(data.proposed_action.decision_event_sequence) && hasRevision(data.workspace_revision),
    }),
    submit: (workspaceId, dto, revision) => request(`/workspaces/${encodeURIComponent(workspaceId)}/submissions`, {
      method: "POST", body: dto, revision,
      validateData: async (data) => await isSubmissionForRequest(data.submission, workspaceId, dto) && hasRevision(data.workspace_revision),
    }),
    remediations: (workspaceId) => request(`/workspaces/${encodeURIComponent(workspaceId)}/remediation`, {
      validateData: (data) => Array.isArray(data.remediations) && data.remediations.every(isRemediation),
    }),
    events: (workspaceId, afterSequence = 0, limit = 50) => request(`/workspaces/${encodeURIComponent(workspaceId)}/events?after_sequence=${encodeURIComponent(afterSequence)}&limit=${encodeURIComponent(limit)}`, {
      validateData: (data) => Array.isArray(data.events) && data.events.length <= 50 && data.events.every(isEvidenceEvent)
        && Number.isInteger(data.next_sequence) && data.next_sequence >= 0 && typeof data.has_more === "boolean",
    }),
    review: (submissionId, dto, revision, expectedSubmissionVersion) => request(`/submissions/${encodeURIComponent(submissionId)}/review-actions`, {
      method: "POST", body: dto, revision,
      validateData: (data) => isRecord(data.review_action) && hasText(data.review_action.id)
        && data.review_action.submission_id === submissionId && hasRevision(expectedSubmissionVersion)
        && data.review_action.submission_version === expectedSubmissionVersion
        && data.review_action.kind === dto.kind && data.review_action.reason === dto.reason
        && hasRevision(data.review_action.created_event_sequence) && hasRevision(data.workspace_revision),
    }),
  });
}
