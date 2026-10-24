import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import {
  createWorkspaceClient,
  confirmReviewOutcome,
  errorStateFor,
  mapFilesToSubmissionDto,
  mapReviewActionToDto,
  mapTaskFormToCreateDto,
  WorkspaceApiError,
} from "../apps/workspace-client.mjs";

const requestSchema = JSON.parse(readFileSync(new URL("../specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json", import.meta.url), "utf8"));

function assertRequestDtoMatchesSchema(dto, definitionName) {
  const definition = requestSchema.$defs[definitionName];
  assert.ok(definition, `missing schema definition ${definitionName}`);
  assert.equal(definition.additionalProperties, false);
  assert.deepEqual(Object.keys(dto).sort(), [...definition.required].sort());
  for (const [key, value] of Object.entries(dto)) {
    const property = definition.properties[key];
    if (property.const !== undefined) assert.equal(value, property.const);
    if (property.enum) assert.ok(property.enum.includes(value), `${key} is outside its schema enum`);
    if (property.type === "string") {
      assert.equal(typeof value, "string", `${key} must be text`);
      if (property.maxLength !== undefined) assert.ok(value.length <= property.maxLength, `${key} exceeds its schema character limit`);
    }
  }
  if (definitionName === "SubmissionCreateRequest") {
    const refs = definition.properties.artifact_refs.items.enum;
    assert.ok(dto.artifact_refs.every((name) => refs.includes(name)));
    const contentSchema = definition.properties.artifact_contents;
    assert.ok(Object.keys(dto.artifact_contents).every((name) => contentSchema.propertyNames.enum.includes(name)));
    assert.ok(Object.values(dto.artifact_contents).every((content) => typeof content === "string" && content.length <= contentSchema.additionalProperties.maxLength));
  }
}

function eventReceipt(workspaceId = "workspace-1", sequence = 2, actorRole = "student") {
  return {
    event_id: `event-${sequence}`,
    sequence,
    schema_version: "evidence-event/v1",
    workspace_id: workspaceId,
    actor_role: actorRole,
    event_type: "synthetic.test_event",
    resource_ref: `resource-${sequence}`,
    request_id: `req-event-${sequence}`,
    occurred_at: "2026-09-25T00:00:00Z",
  };
}

function workspaceReceipt({ id = "workspace-1", assignmentId = "assignment-1", state = "IN_PROGRESS", revision = 3 } = {}) {
  return {
    id,
    assignment_id: assignmentId,
    assignment_version: 1,
    state,
    revision,
    execution_enabled: false,
    artifact_refs: [],
  };
}

function assignmentReceipt({ id = "assignment-1", state = "DRAFT", revision = 1, workspace = null } = {}) {
  return {
    id,
    version: 1,
    state,
    revision,
    task: {
      id: "task-1",
      task_id: "synthetic-task-1-v1",
      version: 1,
      title: "核对合成订单",
      goal: "核对订单数量、单价与金额是否一致。",
      collaboration_mode: "PROPOSE_WITH_STUDENT_CONFIRMATION",
      student_responsibility: "说明异常记录和验证步骤。",
      submission_requirements: ["提交 allowlist 文件快照和验证说明。"],
      starter_project_id: "orders-audit-v1",
      execution_enabled: false,
    },
    workspace,
    demo_notice: "仅限固定合成本机演示；服务重启后清空。",
  };
}

function submissionRequestDto({ content = "abc", explanation = "我检查了合成记录并记录了仍需确认的验证依据。" } = {}) {
  return {
    schema_version: "skillshift-api/v1",
    artifact_refs: ["main.py"],
    artifact_contents: { "main.py": content },
    student_explanation: explanation,
  };
}

function submissionReceipt(dto, { id = "submission-1", workspaceId = "workspace-1", version = 1, state = "SUBMITTED" } = {}) {
  const content = dto.artifact_contents["main.py"];
  const contentHash = createHash("sha256").update(content, "utf8").digest("hex");
  return {
    id,
    workspace_id: workspaceId,
    assignment_version: 1,
    version,
    artifact_refs: [{
      id: "artifact-main-py-v1", logical_name: "main.py", media_type: "text/x-python",
      source: "FIXED_SYNTHETIC", integrity_status: "NOT_COMPUTED",
    }],
    artifact_snapshots: [{
      logical_name: "main.py", media_type: "text/x-python", size_bytes: new TextEncoder().encode(content).length,
      sha256: contentHash, content,
    }],
    student_explanation: dto.student_explanation,
    state,
    created_event_sequence: 4,
  };
}

function reviewReceipt({ id = "review-1", submissionId = "submission-1", submissionVersion = 1, kind = "REQUEST_EVIDENCE", reason = "请补充核验依据。", sequence = 5 } = {}) {
  return {
    review_action: {
      id, submission_id: submissionId, submission_version: submissionVersion,
      kind, reason, created_event_sequence: sequence,
    },
    workspace_revision: sequence,
  };
}

test("teacher task form maps to strict assignment DTO", () => {
  assert.deepEqual(mapTaskFormToCreateDto({
    title: " 标题 ", goal: "目标", responsibility: "学生责任", deliverable: "提交物", mode: "qa",
  }), {
    schema_version: "skillshift-api/v1",
    title: "标题", goal: "目标", student_responsibility: "学生责任", submission_requirement: "提交物",
    starter_project_id: "orders-audit-v1", collaboration_mode: "QA_ONLY",
  });
  assert.equal(mapTaskFormToCreateDto({ mode: "confirm" }).collaboration_mode, "PROPOSE_WITH_STUDENT_CONFIRMATION");
});

test("review actions map to API enums and retain required reason", () => {
  assert.deepEqual(mapReviewActionToDto("approve", "已核对提交依据"), { schema_version: "skillshift-api/v1", kind: "ACKNOWLEDGE", reason: "已核对提交依据" });
  assert.equal(mapReviewActionToDto("evidence", "请补充一次验证步骤").kind, "REQUEST_EVIDENCE");
  assert.equal(mapReviewActionToDto("remediation", "请修正金额核对说明").kind, "REQUEST_REMEDIATION");
  assert.throws(() => mapReviewActionToDto("unknown", "理由"), TypeError);
});

test("student submission DTO includes only allowlisted text snapshots", () => {
  const dto = mapFilesToSubmissionDto({ "main.py": "print('synthetic')", "orders.csv": "id,amount\n" }, "我检查了数据并记录了仍不确定的规则。");
  assert.equal(dto.schema_version, "skillshift-api/v1");
  assert.deepEqual(dto.artifact_refs, ["main.py", "orders.csv"]);
  assert.deepEqual(dto.artifact_contents, { "main.py": "print('synthetic')", "orders.csv": "id,amount\n" });
  assert.equal(dto.student_explanation, "我检查了数据并记录了仍不确定的规则。");
  assert.throws(() => mapFilesToSubmissionDto({ "../private.txt": "x" }, "说明"), TypeError);
});

test("mapped write DTOs match their strict request schema definitions", () => {
  assertRequestDtoMatchesSchema(mapTaskFormToCreateDto({
    title: "核对订单", goal: "检查字段关系并说明验证方法。", responsibility: "说明异常和验证。", deliverable: "提交结果。", mode: "qa",
  }), "AssignmentCreateRequest");
  assertRequestDtoMatchesSchema(mapReviewActionToDto("evidence", "请补充一次验证步骤"), "ReviewActionRequest");
  assertRequestDtoMatchesSchema(mapFilesToSubmissionDto({ "main.py": "print('synthetic')", "orders.csv": "id,amount\n" }, "我检查了数据并记录了仍不确定的规则。"), "SubmissionCreateRequest");
});

test("client uses fixed role path, idempotency and If-Match headers", async () => {
  const calls = [];
  const client = createWorkspaceClient("teacher", {
    idempotencyKeyFactory: () => "test-key-1",
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      const workspace = workspaceReceipt({ id: "workspace-1", assignmentId: "assignment-1", state: "ASSIGNED", revision: 1 });
      return { ok: true, status: 201, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-test", revision: 4, data: {
        assignment: assignmentReceipt({ id: "assignment-1", state: "PUBLISHED", revision: 4, workspace }),
        workspace,
        event: eventReceipt("workspace-1", 2, "teacher"),
      } }) };
    },
  });
  const result = await client.publishAssignment("assignment-1", 3);
  assert.match(calls[0].url, /\/api\/v1\/demo\/teacher\/assignments\/assignment-1\/publish$/);
  assert.equal(calls[0].options.headers["Idempotency-Key"], "test-key-1");
  assert.equal(calls[0].options.headers["If-Match"], "3");
  assert.deepEqual(JSON.parse(calls[0].options.body), { schema_version: "skillshift-api/v1" });
  assert.equal(calls[0].options.credentials, "omit");
  assert.equal(result.revision, 4);
});

test("every mutating client request declares the wire schema version", async () => {
  const requestBodies = [];
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => `schema-key-${requestBodies.length}`,
    fetchImpl: async (url, options) => {
      requestBodies.push(JSON.parse(options.body));
      const body = JSON.parse(options.body);
      let data;
      if (url.endsWith("/start")) data = { workspace: workspaceReceipt({ revision: 3 }), event: eventReceipt("workspace-1", 2) };
      else if (url.endsWith("/agent-turns")) data = {
        turn: { id: "turn-1", provider_mode: "scripted-demo", response_text: "固定合成回复。", availability: "AVAILABLE", event_sequence: 2 },
        workspace_revision: 3,
      };
      else if (url.endsWith("/decision")) data = {
        proposed_action: { id: "proposal-1", kind: "FILE_PATCH_PREVIEW", target_artifact_ref: "artifact-main-py-v1", status: body.decision, diff: "fixed preview", decision_event_sequence: 2 },
        workspace_revision: 3,
      };
      else data = { submission: submissionReceipt(body), workspace_revision: 3 };
      return { ok: true, status: 200, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-test", revision: 3, data }) };
    },
  });
  await client.startWorkspace("workspace-1", 1);
  await client.agentTurn("workspace-1", "如何核验？", 2);
  await client.decideProposal("workspace-1", "proposal-1", "ACCEPTED", 2);
  await client.submit("workspace-1", submissionRequestDto(), 2);
  assert.equal(requestBodies.length, 4);
  assert.ok(requestBodies.every((body) => body.schema_version === "skillshift-api/v1"));
});

test("definitively rejected student submission clears its retry key", async () => {
  const calls = [];
  let keyNumber = 0;
  const dto = submissionRequestDto();
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => `submit-${++keyNumber}`,
    fetchImpl: async (url, options) => {
      calls.push({ url, key: options.headers["Idempotency-Key"], revision: options.headers["If-Match"], body: options.body });
      if (calls.length === 1) return { ok: false, status: 409, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-submit-rejected",
        error: { code: "stale_submission", message: "当前修订冲突。", retryable: false },
      }) };
      return { ok: true, status: 201, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-submit-retried-after-rejection", revision: 3,
        data: { submission: submissionReceipt(dto), workspace_revision: 3 },
      }) };
    },
  });

  await assert.rejects(client.submit("workspace-1", dto, 2), (error) => {
    assert.equal(error.code, "stale_submission");
    assert.equal(error.definitiveRejection, true);
    assert.equal(errorStateFor(error, "提交成果").kind, "conflict");
    return true;
  });
  await client.submit("workspace-1", dto, 2);
  assert.equal(calls.length, 2);
  assert.notEqual(calls[0].key, calls[1].key);
  assert.equal(calls[0].revision, "2");
  assert.deepEqual(JSON.parse(calls[0].body), dto);
});

test("teacher write receipts must match create, publish and review DTOs", async () => {
  const client = createWorkspaceClient("teacher", {
    idempotencyKeyFactory: () => "teacher-key",
    fetchImpl: async (url, options) => {
      const body = JSON.parse(options.body);
      let data;
      if (url.endsWith("/assignments")) data = assignmentReceipt({ id: "assignment-2" });
      else if (url.endsWith("/publish")) data = {
          assignment: assignmentReceipt({
            id: "assignment-2", state: "PUBLISHED", revision: 2,
            workspace: workspaceReceipt({ id: "workspace-2", assignmentId: "assignment-2", state: "ASSIGNED", revision: 1 }),
        }),
        workspace: workspaceReceipt({ id: "workspace-2", assignmentId: "assignment-2", state: "ASSIGNED", revision: 1 }),
        event: eventReceipt("workspace-2", 1, "teacher"),
      };
      else data = reviewReceipt({ submissionId: "submission-2", submissionVersion: 1, kind: body.kind, reason: body.reason, sequence: 4 });
      return { ok: true, status: 201, json: async () => {
        const envelope = { schema_version: "skillshift-api/v1", request_id: "req-test", data };
        // Assignment creation follows the API contract: the draft has its own
        // revision in data, while the SuccessEnvelope revision is optional.
        if (url.endsWith("/publish")) envelope.revision = 2;
        else if (!url.endsWith("/assignments")) envelope.revision = 4;
        return envelope;
      } };
    },
  });
  const created = await client.createAssignment(mapTaskFormToCreateDto({
    title: "核对订单", goal: "goal", responsibility: "responsibility", deliverable: "deliverable", mode: "qa",
  }));
  assert.equal(created.data.state, "DRAFT");
  assert.equal((await client.publishAssignment("assignment-2", created.data.revision)).data.assignment.state, "PUBLISHED");
  const reviewed = await client.review("submission-2", mapReviewActionToDto("evidence", "请补充一次验证步骤"), 3, 1);
  assert.equal(reviewed.data.review_action.kind, "REQUEST_EVIDENCE");
});

test("malformed create or cross-assignment publish receipts stay unknown and retry with the same request identity", async () => {
  const calls = [];
  let createAttempts = 0;
  let publishAttempts = 0;
  const client = createWorkspaceClient("teacher", {
    idempotencyKeyFactory: (() => {
      let next = 0;
      return () => `teacher-guard-${++next}`;
    })(),
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/assignments")) {
        createAttempts += 1;
        const data = createAttempts === 1
          ? { id: "assignment-guard", state: "DRAFT", revision: 1 }
          : assignmentReceipt({ id: "assignment-guard" });
        return { ok: true, status: createAttempts === 1 ? 201 : 201, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-create-guard", data,
        }) };
      }

      publishAttempts += 1;
      const acceptedWorkspace = workspaceReceipt({
        id: publishAttempts === 1 ? "workspace-foreign" : "workspace-guard",
        assignmentId: publishAttempts === 1 ? "assignment-foreign" : "assignment-guard",
        state: "ASSIGNED",
        revision: 1,
      });
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1",
        request_id: "req-publish-guard",
        revision: 2,
        data: {
          assignment: assignmentReceipt({ id: "assignment-guard", state: "PUBLISHED", revision: 2, workspace: acceptedWorkspace }),
          workspace: acceptedWorkspace,
          event: eventReceipt(acceptedWorkspace.id, 1, "teacher"),
        },
      }) };
    },
  });
  const dto = mapTaskFormToCreateDto({ title: "核对订单", goal: "goal", responsibility: "responsibility", deliverable: "deliverable", mode: "qa" });

  await assert.rejects(client.createAssignment(dto), (error) => {
    assert.equal(error.code, "invalid_response");
    assert.equal(errorStateFor(error, "创建任务").kind, "unavailable");
    return true;
  });
  const created = await client.createAssignment(dto);
  assert.equal(created.data.id, "assignment-guard");
  assert.equal(calls[0].options.headers["Idempotency-Key"], calls[1].options.headers["Idempotency-Key"]);
  assert.equal(calls[0].options.body, calls[1].options.body);

  await assert.rejects(client.publishAssignment(created.data.id, created.data.revision), (error) => {
    assert.equal(error.code, "invalid_response");
    assert.equal(errorStateFor(error, "发布任务").kind, "unavailable");
    return true;
  });
  const published = await client.publishAssignment(created.data.id, created.data.revision);
  assert.equal(published.data.workspace.assignment_id, created.data.id);
  assert.equal(calls[2].options.headers["Idempotency-Key"], calls[3].options.headers["Idempotency-Key"]);
  assert.equal(calls[2].options.headers["If-Match"], calls[3].options.headers["If-Match"]);
  assert.equal(calls[2].options.body, calls[3].options.body);
});

test("student resubmission and teacher acknowledgement require matching write receipts", async () => {
  const dto = submissionRequestDto({ explanation: "我重新检查了合成记录并记录了仍需确认的验证依据。" });
  const studentClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 201, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-test", revision: 6,
      data: { submission: submissionReceipt(dto, { id: "submission-2", version: 2, state: "RESUBMITTED" }), workspace_revision: 6 },
    }) }),
  });
  const resubmitted = await studentClient.submit("workspace-1", dto, 5);
  assert.equal(resubmitted.data.submission.state, "RESUBMITTED");
  assert.equal(resubmitted.data.submission.version, 2);

  const teacherClient = createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: true, status: 201, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-test", revision: 7,
      data: reviewReceipt({ id: "review-2", submissionId: "submission-2", submissionVersion: 2, kind: "ACKNOWLEDGE", reason: "已核对补正结果。", sequence: 7 }),
    }) }),
  });
  const acknowledged = await teacherClient.review("submission-2", { kind: "ACKNOWLEDGE", reason: "已核对补正结果。" }, 6, 2);
  assert.equal(acknowledged.data.review_action.kind, "ACKNOWLEDGE");
});

test("API validation and conflict errors become visible non-success UI states", async () => {
  const client = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: false, status: 409, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-test", error: { code: "stale_revision", message: "private path must not be shown", retryable: false } }) }),
  });
  await assert.rejects(client.startWorkspace("workspace-1", 1), (error) => {
    const state = errorStateFor(error, "开始工作");
    assert.equal(state.kind, "conflict");
    assert.match(state.message, /没有覆盖已有内容/);
    assert.doesNotMatch(state.message, /private path/);
    return error instanceof WorkspaceApiError && error.code === "stale_revision";
  });
});

test("all API 409 responses are shown as state or idempotency conflicts", () => {
  for (const code of ["stale_submission", "state_conflict", "cursor_expired"]) {
    const state = errorStateFor(new WorkspaceApiError({ status: 409, code, message: "internal path must not be surfaced" }), "刷新复核");
    assert.equal(state.kind, "conflict", code);
    assert.match(state.message, /冲突/);
    assert.doesNotMatch(state.message, /internal path/);
  }
  const replayConflict = errorStateFor(new WorkspaceApiError({ status: 409, code: "idempotency_conflict", message: "internal path" }), "提交成果");
  assert.equal(replayConflict.kind, "conflict");
  assert.match(replayConflict.message, /请求编号/);
  assert.doesNotMatch(replayConflict.message, /internal path/);
});

test("network failure and validation rejection never become success states", async () => {
  const unavailable = createWorkspaceClient("teacher", { fetchImpl: async () => { throw new Error("connection refused"); } });
  await assert.rejects(unavailable.listAssignments(), (error) => {
    const state = errorStateFor(error, "读取任务");
    assert.equal(state.kind, "unavailable");
    assert.match(state.message, /状态未确认/);
    return true;
  });

  const rejected = createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: false, status: 422, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-test", error: { code: "reason_too_short", message: "理由不足。", retryable: false } }) }),
  });
  await assert.rejects(rejected.listAssignments(), (error) => errorStateFor(error, "提交复核意见").kind === "rejected");
});

test("malformed success envelopes cannot be mistaken for API DTO acknowledgements", async () => {
  for (const data of [[], { proposed_action: { id: "proposal-1", status: "REJECTED" }, workspace_revision: 3 }]) {
    const client = createWorkspaceClient("student", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-test", revision: 3, data,
      }) }),
    });
    await assert.rejects(client.decideProposal("workspace-1", "proposal-1", "ACCEPTED", 2), (error) => {
      assert.equal(error.code, "invalid_response");
      assert.equal(errorStateFor(error, "接受修改建议").kind, "unavailable");
      return true;
    });
  }
});

test("read receipts enforce the DTO shapes consumed by both demo pages", async () => {
  const task = {
    id: "task-1", task_id: "synthetic-task-1-v1", version: 1, title: "核对订单", goal: "检查记录。",
    collaboration_mode: "QA_ONLY", student_responsibility: "说明验证。", submission_requirements: ["提交说明。"],
    starter_project_id: "orders-audit-v1", execution_enabled: false,
  };
  const assignment = {
    id: "assignment-1", version: 1, state: "PUBLISHED", revision: 2, task, workspace: {
      id: "workspace-1", assignment_id: "assignment-1", assignment_version: 1, state: "ASSIGNED", revision: 1,
      execution_enabled: false, artifact_refs: [],
    }, demo_notice: "本机合成演示。",
  };
  const workspace = assignment.workspace;
  const submission = {
    id: "submission-1", workspace_id: workspace.id, assignment_version: 1, version: 1,
    artifact_refs: [{ id: "artifact-1", logical_name: "main.py", media_type: "text/x-python", source: "FIXED_SYNTHETIC", integrity_status: "NOT_COMPUTED" }],
    artifact_snapshots: [{ logical_name: "main.py", media_type: "text/x-python", size_bytes: 3, sha256: "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", content: "abc" }],
    student_explanation: "我按字段关系检查并记录了仍需确认的规则。", state: "SUBMITTED", created_event_sequence: 4,
  };
  const client = createWorkspaceClient("student", {
    fetchImpl: async (url) => {
      const path = new URL(url, "http://localhost").pathname;
      let data;
      if (path.endsWith("/assignments")) data = { assignments: [assignment] };
      else if (path.endsWith("/review-queue")) data = { submissions: [submission] };
      else if (path.endsWith("/remediation")) data = { remediations: [] };
      else if (path.endsWith("/events")) data = { events: [], next_sequence: 0, has_more: false };
      else if (path.includes("/assignments/")) data = assignment;
      else data = workspace;
      return { ok: true, status: 200, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-test", data }) };
    },
  });
  assert.equal((await client.listAssignments()).data.assignments[0].id, assignment.id);
  assert.equal((await client.getAssignment(assignment.id)).data.id, assignment.id);
  assert.equal((await client.reviewQueue(assignment.id)).data.submissions[0].artifact_snapshots[0].size_bytes, 3);
  assert.equal((await client.reviewQueue(assignment.id, workspace.id, assignment.version)).data.submissions[0].workspace_id, workspace.id);
  await assert.rejects(client.reviewQueue(assignment.id, "workspace-other", assignment.version), (error) => error.code === "invalid_response");
  await assert.rejects(client.reviewQueue(assignment.id, workspace.id, assignment.version + 1), (error) => error.code === "invalid_response");
  const closedQueueClient = createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-test", data: { submissions: [{ ...submission, state: "ACCEPTED" }] },
    }) }),
  });
  await assert.rejects(closedQueueClient.reviewQueue(assignment.id, workspace.id, assignment.version), (error) => error.code === "invalid_response");
  assert.equal((await client.getWorkspace(workspace.id)).data.id, workspace.id);
  assert.deepEqual((await client.remediations(workspace.id)).data.remediations, []);
  assert.deepEqual((await client.events(workspace.id)).data.events, []);

  const malformedClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-test", data: {},
    }) }),
  });
  const malformedReads = [
    () => malformedClient.listAssignments(),
    () => malformedClient.getAssignment(assignment.id),
    () => malformedClient.reviewQueue(assignment.id),
    () => malformedClient.getWorkspace(workspace.id),
    () => malformedClient.remediations(workspace.id),
    () => malformedClient.events(workspace.id),
  ];
  for (const read of malformedReads) {
    await assert.rejects(read(), (error) => error.code === "invalid_response");
  }

  for (const snapshot of [
    { ...submission.artifact_snapshots[0], size_bytes: 4 },
    { ...submission.artifact_snapshots[0], sha256: "0".repeat(64) },
  ]) {
    const invalidSnapshotClient = createWorkspaceClient("teacher", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-test", data: {
          submissions: [{ ...submission, artifact_snapshots: [snapshot] }],
        },
      }) }),
    });
    await assert.rejects(invalidSnapshotClient.reviewQueue(assignment.id), (error) => error.code === "invalid_response");
  }
});

test("assignment directory rejects duplicate IDs instead of exposing ambiguous choices", async () => {
  const assignment = assignmentReceipt();
  const client = createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-duplicate-assignments",
      data: { assignments: [assignment, { ...assignment, revision: assignment.revision + 1 }] },
    }) }),
  });
  await assert.rejects(client.listAssignments(), (error) => error.code === "invalid_response");
});

test("teacher review history uses an encoded bounded page and validates empty and action receipts", async () => {
  const calls = [];
  const action = {
    id: "review-history-1", submission_id: "submission-7", submission_version: 2,
    kind: "REQUEST_REMEDIATION", reason: "请补充字段关系的可复核依据。", created_event_sequence: 8,
  };
  const pages = [
    { review_actions: [], next_sequence: 0, has_more: false },
    { review_actions: [action], next_sequence: 8, has_more: false },
  ];
  const client = createWorkspaceClient("teacher", {
    fetchImpl: async (url, options) => {
      calls.push({ url, method: options.method });
      const data = pages.shift();
      return { ok: true, status: 200, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-history", data }) };
    },
  });

  const empty = await client.reviewHistory("assignment/one ?");
  assert.deepEqual(empty.data.review_actions, []);
  const history = await client.reviewHistory("assignment/one ?", 4, 3);
  assert.deepEqual(history.data.review_actions, [action]);
  assert.equal(calls[0].url, "/api/v1/demo/teacher/assignments/assignment%2Fone%20%3F/review-history?after_sequence=0&limit=50");
  assert.equal(calls[1].url, "/api/v1/demo/teacher/assignments/assignment%2Fone%20%3F/review-history?after_sequence=4&limit=3");
  assert.equal(calls[0].method, "GET");
});

test("review history rejects wrong roles, unbounded cursors, malformed pages, and non-review payloads", async () => {
  const roleClient = createWorkspaceClient("student", { fetchImpl: async () => { throw new Error("must not call API"); } });
  assert.throws(() => roleClient.reviewHistory("assignment-1"), TypeError);
  const teacher = createWorkspaceClient("teacher", { fetchImpl: async () => { throw new Error("must not call API"); } });
  for (const [afterSequence, limit] of [
    [-1, 50], [1.5, 50], [Number.MAX_SAFE_INTEGER + 1, 50],
    [0, 0], [0, 51], [0, 1.5],
  ]) assert.throws(() => teacher.reviewHistory("assignment-1", afterSequence, limit), TypeError);
  assert.throws(() => teacher.reviewHistory(""), TypeError);

  const goodAction = {
    id: "review-1", submission_id: "submission-1", submission_version: 1,
    kind: "ACKNOWLEDGE", reason: "已核对提交中的验证依据。", created_event_sequence: 5,
  };
  const invalidPages = [
    {},
    { review_actions: [goodAction], next_sequence: 5, has_more: false, snapshots: [] },
    { review_actions: [{ ...goodAction, kind: "AUTO_SCORE" }], next_sequence: 5, has_more: false },
    { review_actions: [{ ...goodAction, created_event_sequence: 0 }], next_sequence: 0, has_more: false },
    { review_actions: [{ ...goodAction, student_explanation: "不应出现学生说明" }], next_sequence: 5, has_more: false },
    { review_actions: [{ ...goodAction, artifact_snapshots: [] }], next_sequence: 5, has_more: false },
    { review_actions: [{ ...goodAction, assignment_id: "assignment-other" }], next_sequence: 5, has_more: false },
    { review_actions: [goodAction], next_sequence: 4, has_more: false },
    { review_actions: [], next_sequence: 0, has_more: true },
  ];
  for (const data of invalidPages) {
    const client = createWorkspaceClient("teacher", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-history-invalid", data }) }),
    });
    await assert.rejects(client.reviewHistory("assignment-1", 0, 1), (error) => error.code === "invalid_response");
  }
});

test("review history preserves HTTP and network failures as non-success", async () => {
  const httpClient = createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: false, status: 503, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-history-http-failure",
      error: { code: "service_unavailable", message: "暂不可用", retryable: true },
    }) }),
  });
  await assert.rejects(httpClient.reviewHistory("assignment-1"), (error) => error.status === 503 && error.code === "service_unavailable");
  const networkClient = createWorkspaceClient("teacher", { fetchImpl: async () => { throw new Error("offline"); } });
  await assert.rejects(networkClient.reviewHistory("assignment-1"), (error) => error.status === 0 && error.code === "service_unavailable");
});

test("remediation read receipts require a response submission link for RESPONDED records", async () => {
  const open = {
    id: "remediation-open-1", review_action_id: "review-1", submission_id: "submission-1",
    requested_action: "REQUEST_EVIDENCE", reason: "请补充可复核的验证依据。", state: "OPEN",
  };
  const responded = {
    ...open, id: "remediation-responded-1", state: "RESPONDED", response_submission_id: "submission-2",
  };
  const validClient = createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-remediation-states",
      data: { remediations: [open, responded] },
    }) }),
  });
  const result = await validClient.remediations("workspace-1");
  assert.deepEqual(result.data.remediations.map((item) => item.state), ["OPEN", "RESPONDED"]);
  assert.equal(result.data.remediations[1].response_submission_id, "submission-2");

  for (const malformed of [
    { ...responded, response_submission_id: undefined },
    { ...responded, response_submission_id: "" },
  ]) {
    const invalidClient = createWorkspaceClient("teacher", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-remediation-invalid",
        data: { remediations: [malformed] },
      }) }),
    });
    await assert.rejects(invalidClient.remediations("workspace-1"), (error) => error.code === "invalid_response");
  }
});

test("latest submission read validates empty and complete workspace-scoped snapshots", async () => {
  const dto = submissionRequestDto();
  const submission = submissionReceipt(dto, { workspaceId: "workspace/with space" });
  const calls = [];
  let currentSubmission = null;
  const client = createWorkspaceClient("student", {
    fetchImpl: async (url) => {
      calls.push(String(url));
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-latest-submission",
        data: { submission: currentSubmission },
      }) };
    },
  });

  const empty = await client.latestSubmission("workspace/with space");
  assert.equal(empty.data.submission, null);
  currentSubmission = submission;
  const populated = await client.latestSubmission("workspace/with space");
  assert.equal(populated.data.submission.id, "submission-1");
  assert.equal(populated.data.submission.artifact_snapshots[0].content, "abc");
  assert.deepEqual(calls, [
    "/api/v1/demo/student/workspaces/workspace%2Fwith%20space/submissions/latest",
    "/api/v1/demo/student/workspaces/workspace%2Fwith%20space/submissions/latest",
  ]);
});

test("workspace reads reject malformed artifact references and missing request ids", async () => {
  const validWorkspace = workspaceReceipt();
  const malformedWorkspace = { ...validWorkspace, artifact_refs: [{ unexpected: true }] };
  const malformedClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-workspace-malformed",
      data: malformedWorkspace,
    }) }),
  });
  await assert.rejects(malformedClient.getWorkspace("workspace-1"), (error) => error.code === "invalid_response");

  const missingRequestIdClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", data: validWorkspace,
    }) }),
  });
  await assert.rejects(missingRequestIdClient.getWorkspace("workspace-1"), (error) => error.code === "invalid_response");
});

test("latest submission read accepts post-review states while rejecting unknown states", async () => {
  const dto = submissionRequestDto();
  const receipts = [
    submissionReceipt(dto, { version: 1, state: "ACCEPTED" }),
    submissionReceipt(dto, { id: "submission-2", version: 2, state: "FEEDBACK_REQUIRED" }),
    submissionReceipt(dto, { id: "submission-2", version: 2, state: "RESUBMITTED" }),
  ];
  for (const submission of receipts) {
    const client = createWorkspaceClient("student", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-latest-reviewed",
        data: { submission },
      }) }),
    });
    const result = await client.latestSubmission("workspace-1");
    assert.equal(result.data.submission.state, submission.state);
  }

  const invalidStateClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-latest-invalid-state",
      data: { submission: { ...receipts[0], state: "PENDING" } },
    }) }),
  });
  await assert.rejects(invalidStateClient.latestSubmission("workspace-1"), (error) => error.code === "invalid_response");
});

test("latest submission read rejects malformed, cross-workspace, and mismatched snapshot receipts", async () => {
  const dto = submissionRequestDto();
  const valid = submissionReceipt(dto);
  const malformedData = [
    {},
    { submission: null, unexpected: true },
    { submission: {} },
    { submission: { ...valid, workspace_id: "workspace-other" } },
    { submission: { ...valid, version: 0 } },
    { submission: { ...valid, artifact_refs: [{ ...valid.artifact_refs[0], logical_name: "private.txt" }] } },
    { submission: { ...valid, artifact_snapshots: [{ ...valid.artifact_snapshots[0], sha256: "0".repeat(64) }] } },
    { submission: { ...valid, artifact_snapshots: [{ ...valid.artifact_snapshots[0], logical_name: "README.md" }] } },
    { submission: { ...valid, artifact_snapshots: [{ ...valid.artifact_snapshots[0], media_type: "text/csv" }] } },
  ];
  for (const data of malformedData) {
    const client = createWorkspaceClient("student", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-latest-invalid", data,
      }) }),
    });
    await assert.rejects(client.latestSubmission("workspace-1"), (error) => error.code === "invalid_response");
  }
});

test("latest submission read preserves HTTP and network failures", async () => {
  const httpClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: false, status: 503, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-latest-unavailable",
      error: { code: "service_unavailable", message: "暂不可用", retryable: true },
    }) }),
  });
  await assert.rejects(httpClient.latestSubmission("workspace-1"), (error) => error.status === 503 && error.code === "service_unavailable");

  const networkClient = createWorkspaceClient("student", { fetchImpl: async () => { throw new Error("offline"); } });
  await assert.rejects(networkClient.latestSubmission("workspace-1"), (error) => error.status === 0 && error.code === "service_unavailable");
});

test("uncertain teacher review writes are confirmed only by matching API readback", async () => {
  const submission = { id: "submission-7", workspace_id: "workspace-4" };
  const remediationDto = { kind: "REQUEST_REMEDIATION", reason: "请补充字段关系的核对依据。" };
  const remediationApi = {
    getWorkspace: async () => ({ data: { id: submission.workspace_id, state: "FEEDBACK_REQUIRED" } }),
    remediations: async () => ({ data: { remediations: [
      { state: "OPEN", submission_id: submission.id, requested_action: remediationDto.kind, reason: remediationDto.reason },
    ] } }),
  };
  assert.equal(await confirmReviewOutcome(remediationApi, submission, remediationDto), true);
  assert.equal(await confirmReviewOutcome(remediationApi, submission, { ...remediationDto, reason: "different reason" }), false);
  assert.equal(await confirmReviewOutcome(remediationApi, { ...submission, id: "submission-other" }, remediationDto), false);

  const closedApi = {
    getWorkspace: async () => ({ data: { id: submission.workspace_id, state: "CLOSED" } }),
    remediations: async () => { throw new Error("acknowledgement readback should only require the closed workspace"); },
  };
  assert.equal(await confirmReviewOutcome(closedApi, submission, { kind: "ACKNOWLEDGE", reason: "复核理由已满足八个字符。" }), false);
  const notClosedApi = { ...closedApi, getWorkspace: async () => ({ data: { id: submission.workspace_id, state: "FEEDBACK_REQUIRED" } }) };
  assert.equal(await confirmReviewOutcome(notClosedApi, submission, { kind: "ACKNOWLEDGE", reason: "复核理由已满足八个字符。" }), false);
});

test("an uncertain write reuses its idempotency key on an identical retry", async () => {
  const sentKeys = [];
  let attempt = 0;
  const dto = submissionRequestDto();
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => "stable-write-key",
    fetchImpl: async (_url, options) => {
      sentKeys.push(options.headers["Idempotency-Key"]);
      attempt += 1;
      if (attempt === 1) throw new Error("response lost");
      return { ok: true, status: 201, json: async () => ({ schema_version: "skillshift-api/v1", request_id: "req-replay", revision: 3, data: {
        submission: submissionReceipt(dto), workspace_revision: 3,
      } }) };
    },
  });
  await assert.rejects(client.submit("workspace-1", dto, 2));
  await client.submit("workspace-1", dto, 2);
  assert.deepEqual(sentKeys, ["stable-write-key", "stable-write-key"]);
});

test("teacher create and publish retries preserve request identity after lost responses", async () => {
  const calls = [];
  let requestNumber = 0;
  const client = createWorkspaceClient("teacher", {
    idempotencyKeyFactory: () => `teacher-write-${++requestNumber}`,
    fetchImpl: async (url, options) => {
      calls.push({
        url,
        method: options.method,
        idempotencyKey: options.headers["Idempotency-Key"],
        ifMatch: options.headers["If-Match"],
        body: options.body,
      });
      if (calls.length === 1 || calls.length === 3) throw new Error("response lost");

      const workspace = workspaceReceipt({ id: "workspace-retry-1", assignmentId: "assignment-retry-1", state: "ASSIGNED", revision: 1 });
      const data = url.endsWith("/publish")
        ? {
          assignment: assignmentReceipt({ id: "assignment-retry-1", state: "PUBLISHED", revision: 8, workspace }),
          workspace,
          event: eventReceipt("workspace-retry-1", 2, "teacher"),
        }
        : assignmentReceipt({ id: "assignment-retry-1", revision: 7 });
      return {
        ok: true,
        status: 201,
        json: async () => ({
          schema_version: "skillshift-api/v1",
          request_id: `req-${calls.length}`,
          ...(url.endsWith("/publish") ? { revision: 8 } : {}),
          data,
        }),
      };
    },
  });
  const createDto = mapTaskFormToCreateDto({
    title: "核对合成订单",
    goal: "检查字段关系并说明验证方法。",
    responsibility: "说明异常和验证。",
    deliverable: "提交结果与核验说明。",
    mode: "qa",
  });

  await assert.rejects(client.createAssignment(createDto));
  const created = await client.createAssignment(createDto);
  assert.equal(created.data.id, "assignment-retry-1");
  assert.equal(calls[0].url, "/api/v1/demo/teacher/assignments");
  assert.equal(calls[1].url, calls[0].url);
  assert.equal(calls[0].method, "POST");
  assert.equal(calls[1].method, calls[0].method);
  assert.equal(calls[1].idempotencyKey, calls[0].idempotencyKey);
  assert.deepEqual(JSON.parse(calls[1].body), JSON.parse(calls[0].body));
  assert.deepEqual(JSON.parse(calls[0].body), createDto);

  await assert.rejects(client.publishAssignment(created.data.id, created.data.revision));
  const published = await client.publishAssignment(created.data.id, created.data.revision);
  assert.equal(published.data.assignment.state, "PUBLISHED");
  assert.equal(calls[2].url, "/api/v1/demo/teacher/assignments/assignment-retry-1/publish");
  assert.equal(calls[3].url, calls[2].url);
  assert.equal(calls[2].method, "POST");
  assert.equal(calls[3].method, calls[2].method);
  assert.equal(calls[3].idempotencyKey, calls[2].idempotencyKey);
  assert.equal(calls[2].ifMatch, "7");
  assert.equal(calls[3].ifMatch, calls[2].ifMatch);
  assert.deepEqual(JSON.parse(calls[3].body), JSON.parse(calls[2].body));
  assert.deepEqual(JSON.parse(calls[2].body), { schema_version: "skillshift-api/v1" });
});

test("an uncertain proposal decision retries with the same idempotency key and receipt", async () => {
  const keys = [];
  let attempt = 0;
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => "proposal-decision-key",
    fetchImpl: async (_url, options) => {
      keys.push(options.headers["Idempotency-Key"]);
      attempt += 1;
      if (attempt === 1) throw new Error("response lost after proposal decision");
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-proposal-replay", revision: 4,
        data: { proposed_action: {
          id: "proposal-3", kind: "FILE_PATCH_PREVIEW", target_artifact_ref: "artifact-main-py-v1",
          status: "ACCEPTED", diff: "fixed preview", decision_event_sequence: 4,
        }, workspace_revision: 4 },
      }) };
    },
  });
  await assert.rejects(client.decideProposal("workspace-2", "proposal-3", "ACCEPTED", 3));
  const replay = await client.decideProposal("workspace-2", "proposal-3", "ACCEPTED", 3);
  assert.deepEqual(keys, ["proposal-decision-key", "proposal-decision-key"]);
  assert.equal(replay.data.proposed_action.status, "ACCEPTED");
});

test("unavailable Agent turns and proposal decisions can omit the envelope revision", async () => {
  const calls = [];
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => "optional-envelope-revision",
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      const data = url.endsWith("/agent-turns")
        ? {
          turn: { id: "turn-unavailable", provider_mode: "scripted-demo", response_text: "", availability: "UNAVAILABLE", event_sequence: 3 },
          workspace_revision: 3,
        }
        : {
          proposed_action: {
            id: "proposal-1", kind: "FILE_PATCH_PREVIEW", target_artifact_ref: "artifact-main-py-v1",
            status: "REJECTED", diff: "固定文本差异", decision_event_sequence: 4,
          },
          workspace_revision: 4,
        };
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-optional-revision", data,
      }) };
    },
  });

  const unavailable = await client.agentTurn("workspace-1", "请核对金额", 2);
  assert.equal(unavailable.data.turn.availability, "UNAVAILABLE");
  assert.equal(unavailable.revision, undefined);
  const decision = await client.decideProposal("workspace-1", "proposal-1", "REJECTED", unavailable.data.workspace_revision);
  assert.equal(decision.data.workspace_revision, 4);
  assert.equal(decision.revision, undefined);
  assert.equal(calls[1].options.headers["If-Match"], "3");
});

test("uncertain student Agent turns retry the exact question, revision, and idempotency key", async () => {
  const calls = [];
  let keyNumber = 0;
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => `agent-turn-${++keyNumber}`,
    fetchImpl: async (url, options) => {
      calls.push({ url, method: options.method, key: options.headers["Idempotency-Key"], revision: options.headers["If-Match"], body: options.body });
      if (calls.length === 1) throw new Error("response lost after scripted Agent turn");
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-agent-replay", revision: 5,
        data: {
          turn: { id: "turn-5", provider_mode: "scripted-demo", response_text: "固定合成提示。", availability: "AVAILABLE", event_sequence: 5 },
          workspace_revision: 5,
        },
      }) };
    },
  });
  const question = "请解释怎样核验数量与金额关系。";
  await assert.rejects(client.agentTurn("workspace-agent-1", question, 4));
  const replay = await client.agentTurn("workspace-agent-1", question, 4);

  assert.equal(replay.data.turn.provider_mode, "scripted-demo");
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[1], calls[0]);
  assert.equal(calls[0].url, "/api/v1/demo/student/workspaces/workspace-agent-1/agent-turns");
  assert.equal(calls[0].method, "POST");
  assert.equal(calls[0].revision, "4");
  assert.deepEqual(JSON.parse(calls[0].body), { question, schema_version: "skillshift-api/v1" });
});

test("uncertain teacher review retries the exact submission, DTO, revision and idempotency key", async () => {
  const calls = [];
  let keyNumber = 0;
  const client = createWorkspaceClient("teacher", {
    idempotencyKeyFactory: () => `review-${++keyNumber}`,
    fetchImpl: async (url, options) => {
      calls.push({ url, method: options.method, key: options.headers["Idempotency-Key"], revision: options.headers["If-Match"], body: options.body });
      if (calls.length === 1) throw new Error("response lost after review write");
      const body = JSON.parse(options.body);
      return { ok: true, status: 201, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-review-replay", revision: 8,
        data: { review_action: {
          id: "review-replay-1", submission_id: "submission-9", submission_version: 2,
          kind: body.kind, reason: body.reason, created_event_sequence: 8,
        }, workspace_revision: 8 },
      }) };
    },
  });
  const dto = mapReviewActionToDto("remediation", "请补充字段关系的可复核依据。");
  await assert.rejects(client.review("submission-9", dto, 7, 2));
  const replay = await client.review("submission-9", dto, 7, 2);

  assert.equal(replay.data.review_action.submission_id, "submission-9");
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[1], calls[0]);
  assert.equal(calls[0].url, "/api/v1/demo/teacher/submissions/submission-9/review-actions");
  assert.equal(calls[0].method, "POST");
  assert.equal(calls[0].revision, "7");
  assert.deepEqual(JSON.parse(calls[0].body), dto);
});

test("malformed strict write DTO receipts fail closed for Agent turn, proposal decision, and review", async () => {
  const malformedReplies = [
    {
      role: "student",
      run: (client) => client.agentTurn("workspace-1", "如何核验？", 2),
      data: { turn: {
        id: "turn-1", provider_mode: "real-model", response_text: "错误来源", availability: "AVAILABLE", event_sequence: 3,
      }, workspace_revision: 3 },
    },
    {
      role: "student",
      run: (client) => client.decideProposal("workspace-1", "proposal-1", "ACCEPTED", 2),
      data: { proposed_action: { id: "proposal-1", status: "REJECTED" }, workspace_revision: 3 },
    },
    {
      role: "teacher",
      run: (client) => client.review("submission-1", { kind: "REQUEST_EVIDENCE", reason: "请补充核验依据。" }, 2, 1),
      data: { review_action: {
        id: "review-1", submission_id: "other-submission", submission_version: 1,
        kind: "REQUEST_EVIDENCE", reason: "请补充核验依据。", created_event_sequence: 3,
      }, workspace_revision: 3 },
    },
  ];
  for (const malformed of malformedReplies) {
    const client = createWorkspaceClient(malformed.role, {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-malformed", revision: 3, data: malformed.data,
      }) }),
    });
    await assert.rejects(malformed.run(client), (error) => {
      assert.equal(error.code, "invalid_response");
      const state = errorStateFor(error, "写入合成状态");
      assert.equal(state.kind, "unavailable");
      assert.match(state.message, /没有收到 API 成功回执/);
      assert.doesNotMatch(state.message, /已记录/);
      return true;
    });
  }
});

test("remediation read HTTP failures map to visible non-success states", async () => {
  const client = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: false, status: 503, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-remediation-unavailable",
      error: { code: "service_unavailable", message: "server detail must not be surfaced", retryable: true },
    }) }),
  });
  await assert.rejects(client.remediations("workspace-1"), (error) => {
    const state = errorStateFor(error, "读取教师补正状态");
    assert.equal(state.kind, "unavailable");
    assert.match(state.message, /状态未确认/);
    assert.doesNotMatch(state.message, /server detail/);
    return true;
  });
});

test("start workspace accepts a full DTO without optional envelope revision", async () => {
  const validClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-start", revision: 3,
      data: { workspace: workspaceReceipt({ revision: 3 }), event: eventReceipt("workspace-1", 2) },
    }) }),
  });
  const started = await validClient.startWorkspace("workspace-1", 2);
  assert.equal(started.data.workspace.state, "IN_PROGRESS");
  assert.equal(started.revision, 3);

  const incompleteClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-start-incomplete",
      data: { workspace: { id: "workspace-1", state: "IN_PROGRESS" }, event: eventReceipt("workspace-1", 2) },
    }) }),
  });
  await assert.rejects(incompleteClient.startWorkspace("workspace-1", 2), (error) => error.code === "invalid_response");

  const noRevisionClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-start-no-revision",
      data: { workspace: workspaceReceipt({ revision: 3 }), event: eventReceipt("workspace-1", 2) },
    }) }),
  });
  const startedWithoutEnvelopeRevision = await noRevisionClient.startWorkspace("workspace-1", 2);
  assert.equal(startedWithoutEnvelopeRevision.data.workspace.revision, 3);

  const crossAssignmentClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-start-cross-assignment", revision: 3,
      data: { workspace: workspaceReceipt({ assignmentId: "assignment-other", revision: 3 }), event: eventReceipt("workspace-1", 2) },
    }) }),
  });
  await assert.rejects(
    crossAssignmentClient.startWorkspace("workspace-1", 2, "assignment-1"),
    (error) => error.code === "invalid_response",
  );
});

test("authoritative IN_PROGRESS readback retires an uncertain start key before a later resume", async () => {
  const startCalls = [];
  const pauseCalls = [];
  let keySequence = 0;
  const client = createWorkspaceClient("student", {
    idempotencyKeyFactory: () => `start-readback-key-${++keySequence}`,
    fetchImpl: async (url, options) => {
      if (url.endsWith("/start")) {
        startCalls.push(options);
        if (startCalls.length === 1) return { ok: false, status: 503, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-start-lost",
          error: { code: "service_unavailable", message: "synthetic response lost", retryable: true },
        }) };
        return { ok: true, status: 200, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-start-resume", revision: 5,
          data: { workspace: workspaceReceipt({ state: "IN_PROGRESS", revision: 5 }), event: eventReceipt("workspace-1", 4) },
        }) };
      }
      if (url.endsWith("/pause")) {
        pauseCalls.push(options);
        return { ok: true, status: 200, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-pause-after-readback", revision: 4,
          data: { workspace: workspaceReceipt({ state: "PAUSED", revision: 4 }), event: eventReceipt("workspace-1", 3) },
        }) };
      }
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-start-readback",
        data: workspaceReceipt({ state: "IN_PROGRESS", revision: 3 }),
      }) };
    },
  });

  await assert.rejects(client.startWorkspace("workspace-1", 1), (error) => error.status === 503);
  const readback = await client.getWorkspace("workspace-1");
  assert.equal(readback.data.state, "IN_PROGRESS");
  await client.pauseWorkspace("workspace-1", 3);
  await client.startWorkspace("workspace-1", 4);
  assert.equal(startCalls[0].headers["Idempotency-Key"], "start-readback-key-1");
  assert.equal(pauseCalls[0].headers["Idempotency-Key"], "start-readback-key-2");
  assert.equal(startCalls[1].headers["Idempotency-Key"], "start-readback-key-3");
});

test("pause workspace accepts only a confirmed PAUSED workspace DTO", async () => {
  let requestUrl = "";
  const client = createWorkspaceClient("student", {
    fetchImpl: async (url) => {
      requestUrl = url;
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-pause", revision: 4,
        data: { workspace: workspaceReceipt({ state: "PAUSED", revision: 4 }), event: eventReceipt("workspace-1", 3) },
      }) };
    },
  });
  const paused = await client.pauseWorkspace("workspace-1", 3);
  assert.match(requestUrl, /\/workspaces\/workspace-1\/pause$/);
  assert.equal(paused.data.workspace.state, "PAUSED");
  assert.equal(paused.revision, 4);
});

test("pause receipts and workspace readbacks can be bound to the expected assignment", async () => {
  const mismatchedPauseClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-pause-wrong-assignment", revision: 4,
      data: { workspace: workspaceReceipt({ state: "PAUSED", revision: 4, assignmentId: "assignment-2" }), event: eventReceipt("workspace-1", 3) },
    }) }),
  });
  await assert.rejects(mismatchedPauseClient.pauseWorkspace("workspace-1", 3, "assignment-1"), (error) => error.code === "invalid_response");

  const mismatchedReadbackClient = createWorkspaceClient("student", {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-workspace-wrong-assignment",
      data: workspaceReceipt({ state: "PAUSED", revision: 4, assignmentId: "assignment-2" }),
    }) }),
  });
  await assert.rejects(mismatchedReadbackClient.getWorkspace("workspace-1", "assignment-1"), (error) => error.code === "invalid_response");
});

test("pause transport failure keeps its exact idempotency key across workspace readback and retry", async () => {
  const pauseCalls = [];
  let pauseAttempts = 0;
  const client = createWorkspaceClient("student", {
    fetchImpl: async (url, options) => {
      if (url.endsWith("/pause")) {
        pauseCalls.push(options);
        pauseAttempts += 1;
        if (pauseAttempts === 1) throw new Error("synthetic response dropped");
        return { ok: true, status: 200, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-pause-replay", revision: 4,
          data: { workspace: workspaceReceipt({ state: "PAUSED", revision: 4 }), event: eventReceipt("workspace-1", 3) },
        }) };
      }
      assert.match(url, /\/workspaces\/workspace-1$/);
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-pause-readback",
        data: workspaceReceipt({ state: "IN_PROGRESS", revision: 4 }),
      }) };
    },
  });

  await assert.rejects(client.pauseWorkspace("workspace-1", 3), (error) => error.code === "service_unavailable");
  const state = await client.getWorkspace("workspace-1");
  assert.equal(state.data.state, "IN_PROGRESS");
  assert.equal(state.data.revision, 4);
  await client.pauseWorkspace("workspace-1", 3);
  assert.equal(pauseCalls[0].headers["Idempotency-Key"], pauseCalls[1].headers["Idempotency-Key"]);
  assert.equal(pauseCalls[0].headers["If-Match"], pauseCalls[1].headers["If-Match"]);
  assert.equal(pauseCalls[1].headers["If-Match"], "3");
});

test("malformed 2xx pause receipt remains uncertain and retry keeps the original revision and key", async () => {
  const pauseCalls = [];
  let pauseAttempts = 0;
  const client = createWorkspaceClient("student", {
    fetchImpl: async (url, options) => {
      if (url.endsWith("/pause")) {
        pauseCalls.push(options);
        pauseAttempts += 1;
        if (pauseAttempts === 1) return { ok: true, status: 200, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-pause-malformed",
          data: { workspace: { id: "workspace-1", state: "PAUSED" } },
        }) };
        return { ok: true, status: 200, json: async () => ({
          schema_version: "skillshift-api/v1", request_id: "req-pause-exact-replay", revision: 4,
          data: { workspace: workspaceReceipt({ state: "PAUSED", revision: 4 }), event: eventReceipt("workspace-1", 3) },
        }) };
      }
      assert.match(url, /\/workspaces\/workspace-1$/);
      return { ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-pause-readback-newer-revision",
        data: workspaceReceipt({ state: "IN_PROGRESS", revision: 4 }),
      }) };
    },
  });

  await assert.rejects(client.pauseWorkspace("workspace-1", 3), (error) => {
    assert.equal(error.code, "invalid_response");
    assert.equal(error.status, 200);
    assert.equal(error.definitiveRejection, false);
    return true;
  });
  const state = await client.getWorkspace("workspace-1");
  assert.equal(state.data.state, "IN_PROGRESS");
  assert.equal(state.data.revision, 4);
  const paused = await client.pauseWorkspace("workspace-1", 3);
  assert.equal(paused.data.workspace.state, "PAUSED");
  assert.equal(pauseCalls[0].headers["Idempotency-Key"], pauseCalls[1].headers["Idempotency-Key"]);
  assert.equal(pauseCalls[0].headers["If-Match"], pauseCalls[1].headers["If-Match"]);
  assert.equal(pauseCalls[1].headers["If-Match"], "3");
});

test("provided mutation envelope revisions must be valid and agree with workspace revision", async () => {
  const fixtures = [
    { envelopeRevision: 0, workspaceRevision: 3 },
    { envelopeRevision: 4, workspaceRevision: 3 },
  ];
  for (const fixture of fixtures) {
    const client = createWorkspaceClient("student", {
      fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-invalid-write-revision", revision: fixture.envelopeRevision,
        data: {
          turn: { id: "turn-1", provider_mode: "scripted-demo", response_text: "固定合成回复。", availability: "AVAILABLE", event_sequence: 2 },
          workspace_revision: fixture.workspaceRevision,
        },
      }) }),
    });
    await assert.rejects(client.agentTurn("workspace-1", "如何核验？", 1), (error) => error.code === "invalid_response");
  }
});

test("review receipt must match the selected submission version", async () => {
  const dto = mapReviewActionToDto("evidence", "请补充一次验证步骤");
  const makeClient = (submissionVersion) => createWorkspaceClient("teacher", {
    fetchImpl: async () => ({ ok: true, status: 201, json: async () => ({
      schema_version: "skillshift-api/v1", request_id: "req-review-version", revision: 4,
      data: reviewReceipt({ submissionId: "submission-versioned", submissionVersion, kind: dto.kind, reason: dto.reason, sequence: 4 }),
    }) }),
  });

  const matching = await makeClient(3).review("submission-versioned", dto, 3, 3);
  assert.equal(matching.data.review_action.submission_version, 3);
  await assert.rejects(makeClient(2).review("submission-versioned", dto, 3, 3), (error) => error.code === "invalid_response");
});

test("submission write rejects receipts whose workspace, explanation, or snapshots differ from request", async () => {
  const dto = submissionRequestDto();
  const valid = submissionReceipt(dto);
  const mismatches = [
    { ...valid, workspace_id: "workspace-other" },
    { ...valid, student_explanation: "另一条说明文本足够长但不是本次提交内容。" },
    { ...valid, artifact_snapshots: [{ ...valid.artifact_snapshots[0], content: "abd", size_bytes: 3, sha256: createHash("sha256").update("abd").digest("hex") }] },
    { ...valid, artifact_refs: [{ ...valid.artifact_refs[0], logical_name: "README.md", media_type: "text/markdown", id: "artifact-README-md-v1" }] },
  ];
  for (const submission of mismatches) {
    const client = createWorkspaceClient("student", {
      fetchImpl: async () => ({ ok: true, status: 201, json: async () => ({
        schema_version: "skillshift-api/v1", request_id: "req-submit-mismatch", revision: 3,
        data: { submission, workspace_revision: 3 },
      }) }),
    });
    await assert.rejects(client.submit("workspace-1", dto, 2), (error) => error.code === "invalid_response");
  }
});
