"use strict";

import { confirmReviewOutcome, createWorkspaceClient, errorStateFor, mapReviewActionToDto, mapTaskFormToCreateDto, WorkspaceApiError } from "../workspace-client.mjs";

const form = document.querySelector("#task-form");
const toast = document.querySelector("#toast");
const createdTasks = document.querySelector("#created-tasks");
const viewIds = ["tasks-view", "editor-view", "reviews-view"];
let toastTimer = 0;
let draftState = null;
let reviewContext = null;
let selectedReviewAssignmentId = null;
let reviewWriteAttempt = null;
let reviewHistoryPages = [];
let reviewHistoryGeneration = 0;
let reviewHistoryDirectoryError = "";
let reviewLoadGeneration = 0;
let reviewEventGeneration = 0;
let reviewEventWorkspaceId = null;
let reviewQueueResults = new Map();
let reviewQueueRetryGenerations = new Map();
let reviewDetailResults = new Map();
let reviewDetailRetryGenerations = new Map();
let remediationReadResults = new Map();
let remediationRetryGenerations = new Map();
let taskWritePending = false;
let taskWriteAttempt = null;
let assignmentListReadGeneration = 0;
const api = createWorkspaceClient("teacher");

async function readReviewQueueForAssignment(assignment) {
  if (!assignment.workspace || assignment.workspace.assignment_id !== assignment.id) {
    throw new WorkspaceApiError({ status: 200, code: "invalid_response", message: "任务与工作区绑定不一致。", retryable: false });
  }
  return (await api.reviewQueue(assignment.id, assignment.workspace.id, assignment.version)).data.submissions;
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { toast.hidden = true; }, 3200);
}

function navigate(viewName) {
  const viewId = `${viewName}-view`;
  for (const id of viewIds) {
    document.getElementById(id).hidden = id !== viewId;
  }
  document.querySelectorAll(".nav-item[data-view]").forEach((button) => {
    const active = button.dataset.view === viewName;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function readTask() {
  const data = new FormData(form);
  return {
    title: String(data.get("title") || "").trim(),
    goal: String(data.get("goal") || "").trim(),
    responsibility: String(data.get("responsibility") || "").trim(),
    deliverable: String(data.get("deliverable") || "").trim(),
    mode: String(data.get("mode") || "confirm"),
  };
}

function updatePreview() {
  const task = readTask();
  const titleInput = document.querySelector("#task-title");
  const titleBytes = new TextEncoder().encode(task.title).length;
  titleInput.setCustomValidity(titleBytes > 128
    ? `任务名称 UTF-8 编码为 ${titleBytes} 字节，接口上限为 128 字节。请缩短后再保存或发布。`
    : "");
  document.querySelector("#preview-title").textContent = task.title || "任务名称预览";
  document.querySelector("#preview-goal").textContent = task.goal || "任务目标会显示在这里。";
  document.querySelector("#preview-responsibility").textContent = task.responsibility || "请说明学生要亲自验证、解释或补正什么。";
  document.querySelector("#preview-deliverable").textContent = task.deliverable || "请说明学生需要提交的项目结果和说明。";
  const modeLabel = task.mode === "qa" ? "仅问答" : "协作需确认";
  document.querySelector(".preview-mode").textContent = modeLabel;
  document.querySelectorAll(".mode-option:not(.is-disabled)").forEach((label) => {
    const input = label.querySelector("input");
    label.classList.toggle("is-selected", input.checked);
  });
  const goalCount = document.querySelector("#goal-count");
  goalCount.textContent = `${task.goal.length} / 800`;
}

function renderAssignment(assignment) {
  const card = document.createElement("article");
  card.className = `created-task-card${assignment.state === "PUBLISHED" ? " is-published" : ""}`;
  const dot = document.createElement("span");
  dot.className = "created-task-status";
  dot.setAttribute("aria-hidden", "true");
  const copy = document.createElement("div");
  copy.className = "created-task-copy";
  const title = document.createElement("strong");
  title.textContent = assignment.task.title;
  const meta = document.createElement("small");
  meta.textContent = `Python + CSV · ${assignment.state === "PUBLISHED" ? "本机合成 API 已发布" : "本机合成草稿"} · 服务重启后清空`;
  copy.append(title, meta);
  const statusTag = document.createElement("span");
  statusTag.className = `tag ${assignment.state === "PUBLISHED" ? "tag-teal" : "tag-muted"}`;
  statusTag.textContent = assignment.state === "PUBLISHED" ? "已发布 · 合成" : "草稿 · 合成";
  card.append(dot, copy, statusTag);
  createdTasks.prepend(card);
}

function renderAssignmentListReadFailure(message, writeStatus = "") {
  const region = document.querySelector("#assignment-list-state");
  region.hidden = false;
  const prefix = writeStatus ? `${writeStatus}；` : "";
  region.replaceChildren(document.createTextNode(`${prefix}任务目录读取失败，当前目录状态未知。${message} `));
  const retry = document.createElement("button");
  retry.type = "button";
  retry.textContent = "重试读取任务目录";
  retry.addEventListener("click", async () => {
    retry.disabled = true;
    try {
      const result = await refreshAssignments();
      if (!result.stale && result.generation === assignmentListReadGeneration) {
        region.hidden = false;
        region.textContent = "任务目录已重新读取。";
      }
    } catch { /* refreshAssignments keeps the current failure visible with a new retry control. */ }
  });
  region.append(retry);
}

async function refreshAssignments() {
  const generation = ++assignmentListReadGeneration;
  const status = document.querySelector("#assignment-list-state");
  status.hidden = false;
  status.textContent = "正在读取任务目录。";
  let response;
  try {
    response = await api.listAssignments();
  } catch (error) {
    if (generation === assignmentListReadGeneration) {
      renderAssignmentListReadFailure(errorStateFor(error, "读取任务目录").message);
    }
    throw error;
  }
  if (generation !== assignmentListReadGeneration) {
    return { assignments: response.data.assignments, generation, stale: true };
  }
  createdTasks.replaceChildren();
  response.data.assignments.forEach(renderAssignment);
  status.hidden = true;
  status.replaceChildren();
  return { assignments: response.data.assignments, generation, stale: false };
}

function isUnknownWriteOutcome(error) {
  return !(error instanceof WorkspaceApiError)
    || error.status === 0
    || error.status >= 500
    || error.code === "invalid_response";
}

function syncTaskWriteButtons() {
  const hasPendingAttempt = taskWriteAttempt !== null;
  form.querySelectorAll("input, textarea, select, button").forEach((control) => {
    control.disabled = taskWritePending || hasPendingAttempt;
  });
  document.querySelectorAll("[data-action='new-task'], [data-action='use-template']")
    .forEach((button) => { button.disabled = taskWritePending || hasPendingAttempt; });
  document.querySelectorAll("[data-action='save-draft'], [data-action='simulate-publish']")
    .forEach((button) => {
      const isPublish = button.dataset.action === "simulate-publish";
      button.disabled = taskWritePending || (taskWriteAttempt !== null && isPublish !== taskWriteAttempt.publish);
      if (taskWriteAttempt && isPublish === taskWriteAttempt.publish) {
        button.setAttribute("aria-label", taskWriteAttempt.publish ? "重试原发布请求" : "重试原保存请求");
        button.dataset.retryPending = "true";
      } else {
        button.removeAttribute("aria-label");
        delete button.dataset.retryPending;
      }
    });
}

function isPublishedAttemptAssignment(assignment, attempt) {
  return assignment?.id === attempt.assignment?.id
    && assignment.state === "PUBLISHED"
    && assignment.workspace?.assignment_id === assignment.id
    && assignment.workspace.execution_enabled === false;
}

function setPublishRecoveryStatus(message) {
  const title = taskWriteAttempt?.dto?.title || "未命名任务";
  document.querySelector("#api-state").textContent = `待处理原任务“${title}”：${message} 当前任务内容与新建入口已冻结；仅可继续处理原任务。`;
}

async function saveTask(publish) {
  if (taskWritePending) return false;
  if (taskWriteAttempt && taskWriteAttempt.publish !== publish) {
    const originalAction = taskWriteAttempt.publish ? "发布" : "保存草稿";
    showToast(`任务“${taskWriteAttempt.dto.title}”的${originalAction}请求仍待处理；请用原操作处理，不能替换任务内容或动作。`);
    return false;
  }
  if (!taskWriteAttempt) {
    if (!form.reportValidity()) return false;
    draftState = readTask();
    taskWriteAttempt = {
      dto: Object.freeze(mapTaskFormToCreateDto(draftState)),
      publish,
      phase: "CREATE",
      assignment: null,
    };
  }
  const attempt = taskWriteAttempt;
  taskWritePending = true;
  syncTaskWriteButtons();
  document.querySelector("#api-state").textContent = `正在处理原任务“${attempt.dto.title}”的${attempt.phase === "CREATE" ? "创建" : "发布"}步骤；内容与新建入口暂时冻结。`;
  if (attempt.phase === "PUBLISH_READBACK_REQUIRED") {
    try {
      const latest = (await api.getAssignment(attempt.assignment.id)).data;
      if (isPublishedAttemptAssignment(latest, attempt)) {
        taskWriteAttempt = null;
        document.querySelector("#api-state").textContent = "本机合成 API 按原任务 ID 读回已发布状态及其 Workspace；当前发布状态已确认。非生产，数据仅在当前进程内存。";
        showToast("已按原任务读取确认发布状态；没有创建新任务。");
        try { await refreshAssignments(); } catch { /* The publish postcondition is already confirmed. */ }
        navigate("tasks");
        return true;
      }
      if (latest.id === attempt.assignment.id && latest.state === "DRAFT") {
        attempt.assignment = latest;
        attempt.phase = "PUBLISH_RETRY_READY";
        setPublishRecoveryStatus("已按原任务 ID 读回确认它仍是草稿。再次点击原发布操作，将以 API 最新版本发起新的明确发布请求；本次只读回，没有自动重发。 ");
        showToast("原任务仍是草稿；请明确再次点击发布以按最新版本重试。");
      } else {
        setPublishRecoveryStatus("已读回原任务，但状态不符合草稿或已发布的确认条件；发布未确认，未自动重发。");
      }
    } catch (error) {
      const state = errorStateFor(error, "读取原任务发布状态");
      setPublishRecoveryStatus(`原任务发布状态仍无法读取；重试只会再次读取，不会创建任务或重发旧版本。${state.message}`);
    } finally {
      taskWritePending = false;
      syncTaskWriteButtons();
    }
    return false;
  }
  try {
    if (attempt.phase === "PUBLISH_RETRY_READY") attempt.phase = "PUBLISH";
    if (attempt.phase === "CREATE") {
      const created = await api.createAssignment(attempt.dto);
      attempt.assignment = created.data;
      attempt.phase = attempt.publish ? "PUBLISH" : "COMPLETE";
    }
    if (attempt.phase === "PUBLISH") {
      await api.publishAssignment(attempt.assignment.id, attempt.assignment.revision);
      attempt.phase = "COMPLETE";
    }
  } catch (error) {
    const state = errorStateFor(error, attempt.phase === "CREATE"
      ? "创建任务"
      : attempt.publish ? "发布任务" : "保存草稿");
    if (!isUnknownWriteOutcome(error)) {
      if (attempt.phase === "PUBLISH" && attempt.assignment) {
        try {
          const latest = (await api.getAssignment(attempt.assignment.id)).data;
          if (isPublishedAttemptAssignment(latest, attempt)) {
            taskWriteAttempt = null;
            document.querySelector("#api-state").textContent = "发布请求收到明确冲突/拒绝，但按原任务 ID 读回确认其已发布且已创建 Workspace；当前状态已确认，不会重建任务。非生产。";
            showToast("已按原任务读取确认发布状态；没有创建新任务。");
            try { await refreshAssignments(); } catch { /* The publish postcondition is already confirmed. */ }
            navigate("tasks");
            return true;
          }
          if (latest.id === attempt.assignment.id && latest.state === "DRAFT") {
            attempt.assignment = latest;
            attempt.phase = "PUBLISH_RETRY_READY";
            setPublishRecoveryStatus(`API 明确拒绝了发布请求，读回确认原任务仍是草稿。${state.message} 再次点击原发布操作才会使用最新版本发起新请求；不会重新创建草稿。`);
          } else {
            attempt.phase = "PUBLISH_READBACK_REQUIRED";
            setPublishRecoveryStatus(`API 明确拒绝了发布请求，但读回状态不符合可确认条件。${state.message} 请点击原发布操作重新读取状态；不会自动重发。`);
          }
        } catch (readError) {
          attempt.phase = "PUBLISH_READBACK_REQUIRED";
          const readState = errorStateFor(readError, "读取原任务发布状态");
          setPublishRecoveryStatus(`发布请求被 API 明确拒绝，但无法读回原任务状态。${state.message} ${readState.message}`);
        }
      } else {
        taskWriteAttempt = null;
        document.querySelector("#api-state").textContent = `任务创建被本机合成 API 明确拒绝。 ${state.message}`;
      }
      showToast(state.message);
      return false;
    }
    const pendingAction = attempt.phase === "CREATE"
      ? "创建回执未确认；重试将原样发送同一任务 DTO。"
      : "发布回执未确认；重试将使用同一任务和版本，不会再次创建任务。";
    document.querySelector("#api-state").textContent = `待处理原任务“${attempt.dto.title}”：${pendingAction} 当前尝试 DTO 与任务入口已冻结。 ${state.message}`;
    showToast(`${pendingAction} ${state.message}`);
    return false;
  } finally {
    taskWritePending = false;
    syncTaskWriteButtons();
  }

  // A confirmed write must not become an apparent retry just because list refresh fails.
  taskWriteAttempt = null;
  syncTaskWriteButtons();
  const completedPublish = attempt.publish;
  let listRefreshError = null;
  let listRefreshResult = null;
  try {
    listRefreshResult = await refreshAssignments();
  } catch (error) {
    listRefreshError = error;
  }
  if (listRefreshError) {
    const state = errorStateFor(listRefreshError, "刷新任务列表");
    const writeStatus = completedPublish ? "发布回执已确认" : "草稿保存回执已确认";
    renderAssignmentListReadFailure(`${state.message} 写入状态不会重试。`, writeStatus);
    document.querySelector("#api-state").textContent = `${writeStatus}；任务目录读取失败，写入状态已确认且不会重试。`;
    showToast(`${writeStatus}，但任务列表刷新失败。`);
    navigate("tasks");
    return true;
  }
  if (listRefreshResult.stale || listRefreshResult.generation !== assignmentListReadGeneration) {
    navigate("tasks");
    return true;
  }
  document.querySelector("#api-state").textContent = completedPublish
      ? "本机合成 API 已发布任务；固定学生演示角色可在当前进程内读取。非生产，服务重启后清空。"
      : "本机合成 API 已保存草稿；尚未向学生目录发布。服务重启后清空，非生产。";
  showToast(completedPublish ? "任务已由本机合成 API 发布。" : "草稿已由本机合成 API 保存。");
  navigate("tasks");
  return true;
}

function renderSnapshot(snapshot) {
  const item = document.createElement("section");
  item.className = "snapshot-item";
  item.dataset.logicalName = snapshot.logical_name;
  const heading = document.createElement("strong");
  heading.textContent = `${snapshot.logical_name} · ${snapshot.size_bytes} UTF-8 bytes · SHA-256 ${snapshot.sha256}`;
  const content = document.createElement("pre");
  content.textContent = snapshot.content;
  item.append(heading, content);
  return item;
}

function renderEvent(event) {
  const item = document.createElement("li");
  const dot = document.createElement("span");
  dot.className = "timeline-dot dot-student";
  dot.textContent = String(event.sequence);
  const copy = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = event.event_type;
  const detail = document.createElement("p");
  detail.textContent = `${event.actor_role} · ${event.resource_ref}`;
  const kind = document.createElement("span");
  kind.className = "timeline-kind";
  kind.textContent = `服务端顺序 ${event.sequence} · ${event.occurred_at}`;
  copy.append(title, detail, kind);
  item.append(dot, copy);
  return item;
}

function renderRemediationStatus(entries, errors = []) {
  const container = document.querySelector("#remediation-status");
  container.style.display = "block";
  container.style.whiteSpace = "normal";
  container.setAttribute("aria-live", "polite");
  if (!entries.length && !errors.length) {
    container.textContent = "暂无补正记录。";
    return;
  }
  const actionLabels = {
    REQUEST_EXPLANATION: "请求说明",
    REQUEST_EVIDENCE: "请求补证",
    REQUEST_REMEDIATION: "请求补正",
    ENVIRONMENT_ISSUE: "标记环境问题",
  };
  const stateLabels = {
    OPEN: "等待学生回应",
    RESPONDED: "已收到学生回应",
    CLOSED: "API 记录为已关闭",
  };
  const rendered = entries.map(({ assignment, remediation }) => {
    const item = document.createElement("span");
    item.style.display = "block";
    const responseRef = remediation.response_submission_id
      ? `；回应提交 ${remediation.response_submission_id}`
      : "";
    item.textContent = `${assignment.task.title} · ${stateLabels[remediation.state] || remediation.state} · ${actionLabels[remediation.requested_action] || remediation.requested_action} · 原提交 ${remediation.submission_id}${responseRef} · 要求：${remediation.reason}`;
    return item;
  });
  errors.forEach(({ assignment, error }) => {
    const item = document.createElement("span");
    item.style.display = "block";
    const isLoading = Boolean(remediationReadResults.get(assignment.id)?.loading);
    const status = document.createElement("span");
    status.textContent = isLoading
      ? `${assignment.task.title} · 正在重读补正状态。`
      : `${assignment.task.title} · 补正读取失败，状态未知：${error} `;
    const retry = document.createElement("button");
    retry.type = "button";
    retry.dataset.remediationRetry = assignment.id;
    retry.textContent = "重试此任务补正状态";
    retry.disabled = isLoading;
    item.append(status, retry);
    rendered.push(item);
  });
  container.replaceChildren(...rendered);
}

function renderTeacherRemediationResults() {
  const results = [...remediationReadResults.values()];
  renderRemediationStatus(
    results.flatMap(({ assignment, remediations }) => remediations.map((remediation) => ({ assignment, remediation }))),
    results.filter((item) => item.error),
  );
}

async function retryTeacherRemediation(assignmentId) {
  const previous = remediationReadResults.get(assignmentId);
  if (!previous || !previous.error || previous.loading) return;
  const viewGeneration = reviewLoadGeneration;
  const requestGeneration = (remediationRetryGenerations.get(assignmentId) || 0) + 1;
  remediationRetryGenerations.set(assignmentId, requestGeneration);
  remediationReadResults.set(assignmentId, { ...previous, loading: true, error: "正在重读此任务的补正状态。" });
  renderTeacherRemediationResults();
  try {
    const remediations = (await api.remediations(previous.assignment.workspace.id)).data.remediations;
    if (viewGeneration !== reviewLoadGeneration || requestGeneration !== remediationRetryGenerations.get(assignmentId)) return;
    remediationReadResults.set(assignmentId, { assignment: previous.assignment, remediations, error: "", loading: false });
  } catch (error) {
    if (viewGeneration !== reviewLoadGeneration || requestGeneration !== remediationRetryGenerations.get(assignmentId)) return;
    remediationReadResults.set(assignmentId, { ...previous, loading: false, error: errorStateFor(error, "读取补正状态").message });
  }
  renderTeacherRemediationResults();
}

document.querySelector("#remediation-status").addEventListener("click", (event) => {
  const button = event.target.closest("[data-remediation-retry]");
  if (button) void retryTeacherRemediation(button.dataset.remediationRetry);
});

function markRemediationStatusUnknown(error) {
  const state = errorStateFor(error, "读取补正状态");
  const container = document.querySelector("#remediation-status");
  container.style.display = "block";
  container.style.whiteSpace = "normal";
  container.setAttribute("aria-live", "polite");
  container.textContent = `补正状态未知，API 读取失败：${state.message}`;
}

function renderReviewHistory(entries) {
  const list = document.querySelector("#review-history-list");
  const status = document.querySelector("#review-history-state");
  const retry = document.querySelector("#review-history-retry");
  const more = document.querySelector("#review-history-more");
  const actionLabels = {
    ACKNOWLEDGE: "认可并关闭",
    REQUEST_EXPLANATION: "请求说明",
    REQUEST_EVIDENCE: "请求补证",
    REQUEST_REMEDIATION: "请求补正",
    ENVIRONMENT_ISSUE: "标记环境问题",
  };
  list.replaceChildren();
  retry.hidden = true;
  if (!reviewHistoryPages.length && !reviewHistoryDirectoryError) {
    const empty = document.createElement("li");
    empty.textContent = "当前没有已发布任务可读取复核历史。";
    list.append(empty);
    more.hidden = true;
    status.textContent = "任务目录读取成功；没有已发布任务，未请求历史 API。";
    return;
  }
  more.hidden = !reviewHistoryPages.some((page) => page.hasMore && !page.error);
  if (!entries.length && !reviewHistoryPages.some((page) => page.error) && !reviewHistoryDirectoryError) {
    const empty = document.createElement("li");
    empty.textContent = "API 返回：当前没有复核动作记录。";
    list.append(empty);
    status.textContent = "历史读取成功；空记录不代表某次待确认操作成功或失败。";
    return;
  }
  entries.forEach(({ assignment, action }) => {
    const item = document.createElement("li");
    item.textContent = `${assignment.task.title} · 动作记录：${actionLabels[action.kind] || action.kind} · 目标提交 ${action.submission_id} 第 ${action.submission_version} 版 · 理由：${action.reason} · 事件序号 ${action.created_event_sequence}`;
    list.append(item);
  });
  reviewHistoryPages.filter((page) => page.error).forEach((page) => {
    const item = document.createElement("li");
    item.textContent = `${page.assignment.task.title} · 复核历史读取失败，状态未知：${page.error}`;
    list.append(item);
  });
  const moreAssignments = reviewHistoryPages.filter((page) => page.hasMore && !page.error).length;
  const failedAssignments = reviewHistoryPages.filter((page) => page.error).length;
  status.textContent = `${reviewHistoryDirectoryError ? `任务目录刷新失败，目录状态未知；${reviewHistoryDirectoryError}；保留已成功读取的历史记录。` : ""}${failedAssignments ? `${failedAssignments} 个任务读取失败，历史状态未知；` : ""}${moreAssignments ? `${moreAssignments} 个任务还有后续页；` : ""}以下仅为 API 返回的复核历史记录；记录本身不能确认页面中某次回执未知的请求。`;
  retry.hidden = !failedAssignments && !reviewHistoryDirectoryError;
}

function markReviewHistoryUnknown(error) {
  reviewHistoryGeneration += 1;
  const state = errorStateFor(error, "读取复核历史");
  reviewHistoryDirectoryError = state.message;
  document.querySelector("#review-history-more").disabled = false;
  renderReviewHistory(reviewHistoryPages.flatMap((page) =>
    page.actions.map((action) => ({ assignment: page.assignment, action }))));
}

async function loadReviewHistory(published, requestId = reviewHistoryGeneration + 1) {
  reviewHistoryGeneration = Math.max(reviewHistoryGeneration, requestId);
  const generation = requestId;
  const status = document.querySelector("#review-history-state");
  reviewHistoryDirectoryError = "";
  document.querySelector("#review-history-retry").hidden = true;
  const more = document.querySelector("#review-history-more");
  more.hidden = true;
  more.disabled = false;
  const previousPagesByAssignment = new Map(reviewHistoryPages.map((page) => [page.assignment.id, page]));
  const pages = published.map((assignment) => {
    const previous = previousPagesByAssignment.get(assignment.id);
    return {
      assignment,
      actions: [...(previous?.actions || [])],
      nextSequence: previous?.nextSequence || 0,
      hasMore: previous?.hasMore || false,
      error: "",
      inFlight: false,
    };
  });
  reviewHistoryPages = pages;
  status.textContent = "正在读取已发布任务的复核历史；本机合成、内存暂存、非生产。";
  await Promise.all(pages.map(async (page) => {
    try {
      const result = (await api.reviewHistory(page.assignment.id, 0, 50)).data;
      page.actions = result.review_actions;
      page.nextSequence = result.next_sequence;
      page.hasMore = result.has_more;
      if (page.hasMore && (!Number.isInteger(page.nextSequence) || page.nextSequence < 0)) {
        throw new TypeError("分页响应缺少有效 next_sequence");
      }
    } catch (error) {
      page.error = errorStateFor(error, "读取复核历史").message;
    }
  }));
  if (generation !== reviewHistoryGeneration) return;
  renderReviewHistory(pages.flatMap((page) =>
    page.actions.map((action) => ({ assignment: page.assignment, action }))));
}

async function loadMoreReviewHistory() {
  const generation = reviewHistoryGeneration;
  const button = document.querySelector("#review-history-more");
  button.disabled = true;
  const pages = reviewHistoryPages;
  const pendingPages = pages.filter((page) => page.hasMore && !page.error && !page.inFlight);
  await Promise.all(pendingPages.map(async (page) => {
    page.inFlight = true;
    try {
      const result = (await api.reviewHistory(page.assignment.id, page.nextSequence, 50)).data;
      if (generation !== reviewHistoryGeneration) return;
      page.actions.push(...result.review_actions);
      page.nextSequence = result.next_sequence;
      page.hasMore = result.has_more;
      if (page.hasMore && (!Number.isInteger(page.nextSequence) || page.nextSequence < 0)) {
        throw new TypeError("分页响应缺少有效 next_sequence");
      }
      page.error = "";
    } catch (error) {
      page.error = errorStateFor(error, "加载复核历史后续页").message;
    } finally {
      page.inFlight = false;
    }
  }));
  if (generation !== reviewHistoryGeneration) return;
  button.disabled = false;
  renderReviewHistory(pages.flatMap((page) =>
    page.actions.map((action) => ({ assignment: page.assignment, action }))));
}

async function retryReviewHistory() {
  const generation = ++reviewHistoryGeneration;
  document.querySelector("#review-history-state").textContent = "正在刷新已发布任务目录；保留当前历史记录。";
  try {
    const assignments = (await api.listAssignments()).data.assignments;
    if (generation !== reviewHistoryGeneration) return;
    await loadReviewHistory(assignments.filter((item) => item.state === "PUBLISHED" && item.workspace), generation);
  } catch (error) {
    if (generation === reviewHistoryGeneration) markReviewHistoryUnknown(error);
  }
}

document.querySelector("#review-history-retry").addEventListener("click", retryReviewHistory);
document.querySelector("#review-history-more").addEventListener("click", loadMoreReviewHistory);

function validateReviewReasonBytes() {
  const field = document.querySelector("#feedback-reason");
  const byteLength = new TextEncoder().encode(field.value.trim()).length;
  field.setCustomValidity(byteLength > 1024
    ? `反馈理由 UTF-8 编码为 ${byteLength} 字节，接口上限为 1024 字节。请缩短后再提交。`
    : "");
  return byteLength <= 1024;
}

document.querySelector("#feedback-reason").addEventListener("input", validateReviewReasonBytes);

function syncReviewAttemptControls() {
  const attempt = reviewWriteAttempt;
  document.querySelector("#feedback-reason").disabled = Boolean(attempt);
  document.querySelectorAll(".submission-tab").forEach((tab) => { tab.disabled = Boolean(attempt); });
  document.querySelectorAll("[data-review]").forEach((button) => {
    button.disabled = attempt
      ? attempt.inFlight || button.dataset.review !== attempt.action
      : !reviewContext;
  });
}

function markReviewAttemptUnknown(attempt, message) {
  attempt.inFlight = false;
  attempt.phase = "UNKNOWN";
  const actionButton = [...document.querySelectorAll("[data-review]")]
    .find((button) => button.dataset.review === attempt.action);
  const actionLabel = actionButton?.querySelector("strong")?.textContent || actionButton?.textContent.trim() || "原复核动作";
  const text = `${message} 目标为“${attempt.context.assignment.task.title}”第 ${attempt.context.submission.version} 版提交，动作“${actionLabel}”，理由已固定。当前只能点击同一动作，使用原 DTO、修订号和幂等键重试；不要编辑或改选动作。`;
  const result = document.querySelector("#review-result");
  result.textContent = text;
  result.hidden = false;
  document.querySelector("#api-state").textContent = `${text} 状态仅限本机合成 API，内存暂存，非生产。`;
  showToast("复核回执未确认；仅可重试原复核写入。");
  syncReviewAttemptControls();
}

function renderReviewTaskChoices(items) {
  const region = document.querySelector("#review-task-list");
  region.replaceChildren();
  region.hidden = items.length === 0;
  const heading = document.createElement("strong");
  heading.textContent = "选择要查看的任务";
  region.append(heading);
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "review-task-choice";
    const label = document.createElement("span");
    const count = item.loading ? "正在读取复核队列" : item.error ? "待复核数量未知" : `待复核 ${item.submissions.length} 项`;
    const error = item.error && !item.loading ? ` · 读取失败：${item.error}` : "";
    label.textContent = `${item.assignment.task.title} · ${item.assignment.state} · ${count}${error}`;
    const button = document.createElement("button");
    button.type = "button";
    const taskTitle = item.assignment.task.title;
    const detail = reviewDetailResults.get(item.assignment.id);
    if (item.error || item.loading) {
      button.dataset.reviewQueueRetry = item.assignment.id;
      button.textContent = item.loading ? "正在重试" : "重试此任务";
      button.setAttribute("aria-label", `重试“${taskTitle}”的复核队列`);
      button.disabled = Boolean(item.loading);
    } else if (detail?.error || detail?.loading) {
      button.dataset.reviewDetailRetry = item.assignment.id;
      button.textContent = detail.loading ? "正在重试详情" : "重试详情读取";
      button.setAttribute("aria-label", `重试“${taskTitle}”的复核详情读取`);
      button.disabled = Boolean(detail.loading);
    } else {
      button.dataset.reviewAssignment = item.assignment.id;
      button.textContent = "查看此任务";
      button.setAttribute("aria-label", `查看“${taskTitle}”的复核详情`);
    }
    row.append(label, button);
    region.append(row);
  }
}

function updateTeacherReviewCount() {
  const results = [...reviewQueueResults.values()];
  const count = results.some((item) => item.error || item.loading)
    ? "?"
    : String(results.reduce((total, item) => total + item.submissions.length, 0));
  document.querySelector("#review-count").textContent = count;
}

function collaborationModeLabel(mode) {
  if (mode === "QA_ONLY") return "仅问答";
  if (mode === "PROPOSE_WITH_STUDENT_CONFIRMATION") return "协作需确认";
  return "协作方式未知";
}

async function loadReviewEvents(workspaceId) {
  const requestId = ++reviewEventGeneration;
  const state = document.querySelector("#evidence-state");
  const retry = document.querySelector("#evidence-retry");
  const timeline = document.querySelector("#evidence-timeline");
  state.textContent = "正在读取此任务的事件记录。";
  const preserveSameWorkspaceEvents = reviewEventWorkspaceId === workspaceId;
  if (!preserveSameWorkspaceEvents) timeline.replaceChildren();
  retry.hidden = true;
  try {
    const events = await api.events(workspaceId, 0, 50);
    if (requestId !== reviewEventGeneration || reviewContext?.submission?.workspace_id !== workspaceId) return;
    timeline.replaceChildren(...events.data.events.map(renderEvent));
    reviewEventWorkspaceId = workspaceId;
    if (!events.data.events.length) {
      const emptyEvent = document.createElement("li");
      emptyEvent.textContent = "当前没有可显示的合成事件。";
      timeline.append(emptyEvent);
    }
    state.textContent = "事件读取成功。";
  } catch (error) {
    if (requestId !== reviewEventGeneration || reviewContext?.submission?.workspace_id !== workspaceId) return;
    const message = errorStateFor(error, "读取事件").message;
    state.textContent = `事件状态未知，读取失败：${message}${preserveSameWorkspaceEvents ? "；保留此工作区上次成功读取的事件。" : ""}`;
    retry.hidden = false;
  }
}

document.querySelector("#evidence-retry").addEventListener("click", () => {
  if (reviewContext?.submission?.workspace_id) void loadReviewEvents(reviewContext.submission.workspace_id);
});

document.querySelector("#review-task-list").addEventListener("click", (event) => {
  const retry = event.target.closest("[data-review-queue-retry]");
  if (retry) {
    void retryTeacherReviewQueue(retry.dataset.reviewQueueRetry);
    return;
  }
  const detailRetry = event.target.closest("[data-review-detail-retry]");
  if (detailRetry) {
    void retryTeacherWorkspaceDetail(detailRetry.dataset.reviewDetailRetry);
    return;
  }
  const button = event.target.closest("[data-review-assignment]");
  if (!button) return;
  selectedReviewAssignmentId = button.dataset.reviewAssignment;
  void loadReviewQueue();
});

async function retryTeacherWorkspaceDetail(assignmentId) {
  const previous = reviewDetailResults.get(assignmentId);
  if (!previous?.error || previous.loading || selectedReviewAssignmentId !== assignmentId) return;
  const viewGeneration = reviewLoadGeneration;
  const requestGeneration = (reviewDetailRetryGenerations.get(assignmentId) || 0) + 1;
  reviewDetailRetryGenerations.set(assignmentId, requestGeneration);
  reviewDetailResults.set(assignmentId, { ...previous, loading: true });
  renderReviewTaskChoices([...reviewQueueResults.values()]);
  let retryStage = "review queue";
  try {
    const submissions = await readReviewQueueForAssignment(previous.assignment);
    if (viewGeneration !== reviewLoadGeneration
      || requestGeneration !== reviewDetailRetryGenerations.get(assignmentId)
      || selectedReviewAssignmentId !== assignmentId
      || reviewDetailResults.get(assignmentId)?.submission.id !== previous.submission.id) return;
    reviewQueueResults.set(assignmentId, { assignment: previous.assignment, submissions, error: "", loading: false });
    updateTeacherReviewCount();
    renderReviewTaskChoices([...reviewQueueResults.values()]);
    const submission = submissions.find((item) => item.id === previous.submission.id
      && item.version === previous.submission.version
      && item.workspace_id === previous.submission.workspace_id
      && ["SUBMITTED", "RESUBMITTED"].includes(item.state));
    if (!submission) {
      reviewDetailResults.delete(assignmentId);
      reviewContext = null;
      document.querySelector("#review-details").hidden = true;
      document.querySelector("#review-empty").hidden = false;
      document.querySelector("#review-empty").textContent = "此提交已不在当前待复核队列中。已刷新队列；请明确选择当前待复核任务。";
      syncReviewAttemptControls();
      renderReviewTaskChoices([...reviewQueueResults.values()]);
      return;
    }
    retryStage = "workspace detail";
    const workspace = await api.getWorkspace(submission.workspace_id);
    if (viewGeneration !== reviewLoadGeneration
      || requestGeneration !== reviewDetailRetryGenerations.get(assignmentId)
      || selectedReviewAssignmentId !== assignmentId
      || reviewDetailResults.get(assignmentId)?.submission.id !== previous.submission.id) return;
    if (workspace.data.assignment_id !== previous.assignment.id) {
      throw new WorkspaceApiError({ status: 200, code: "invalid_response", message: "工作区不属于当前所选任务。", retryable: false });
    }
    if (!["REVIEW_REQUIRED", "RESUBMITTED"].includes(workspace.data.state)) {
      reviewDetailResults.delete(assignmentId);
      reviewContext = null;
      document.querySelector("#review-details").hidden = true;
      document.querySelector("#review-empty").hidden = false;
      document.querySelector("#review-empty").textContent = `待复核队列与工作区状态不一致（当前 ${workspace.data.state}）；详情保持不可操作，请重新读取任务复核状态。`;
      syncReviewAttemptControls();
      renderReviewTaskChoices([...reviewQueueResults.values()]);
      return;
    }
    reviewDetailResults.set(assignmentId, { ...previous, submission, error: "", loading: false });
    reviewContext = { assignment: previous.assignment, submission, revision: workspace.data.revision };
    await showReviewSubmissionDetails(reviewContext, viewGeneration);
    if (viewGeneration !== reviewLoadGeneration || selectedReviewAssignmentId !== assignmentId) return;
    const queueErrors = [...reviewQueueResults.values()].filter((item) => item.error).length;
    document.querySelector("#review-details").hidden = false;
    document.querySelector("#review-empty").hidden = false;
    document.querySelector("#review-empty").textContent = queueErrors
      ? `所选任务详情已加载；另有 ${queueErrors} 个任务读取失败，仍以未知状态保留在任务概览中。`
      : "已载入所选任务详情。可从上方任务概览切换任务。";
    document.querySelector("#api-state").textContent = "已连接本机合成 API；复核目录和所选任务详情已读取。";
    syncReviewAttemptControls();
    renderReviewTaskChoices([...reviewQueueResults.values()]);
  } catch (error) {
    if (viewGeneration !== reviewLoadGeneration
      || requestGeneration !== reviewDetailRetryGenerations.get(assignmentId)
      || selectedReviewAssignmentId !== assignmentId) return;
    const failedRead = retryStage === "review queue" ? "读取复核队列" : "读取工作区详情";
    const message = errorStateFor(error, failedRead).message;
    if (retryStage === "review queue") {
      const queue = reviewQueueResults.get(assignmentId);
      if (queue) reviewQueueResults.set(assignmentId, { ...queue, loading: false, error: message });
      reviewDetailResults.delete(assignmentId);
      reviewContext = null;
      document.querySelector("#review-details").hidden = true;
      document.querySelector("#review-empty").hidden = false;
      document.querySelector("#review-empty").textContent = `所选任务复核队列读取失败，待复核数量与提交状态未知：${message}。请重试此任务。`;
      syncReviewAttemptControls();
      updateTeacherReviewCount();
      renderReviewTaskChoices([...reviewQueueResults.values()]);
      document.querySelector("#api-state").textContent = message;
      return;
    }
    reviewDetailResults.set(assignmentId, { ...previous, loading: false, error: message });
    document.querySelector("#review-empty").hidden = false;
    document.querySelector("#review-empty").textContent = `所选任务详情读取失败，状态未知：${message}。请重试该任务。`;
    document.querySelector("#api-state").textContent = message;
    renderReviewTaskChoices([...reviewQueueResults.values()]);
  }
}

async function showReviewSubmissionDetails(context, viewGeneration) {
  const { assignment, submission } = context;
  document.querySelector("#review-assignment-title").textContent = assignment.task.title;
  document.querySelector("#review-task-goal").textContent = assignment.task.goal;
  document.querySelector("#review-collaboration-mode").textContent = collaborationModeLabel(assignment.task.collaboration_mode);
  document.querySelector("#review-student-explanation").textContent = submission.student_explanation;
  document.querySelector("#review-submission-state").textContent = `第 ${submission.version} 版 · ${submission.state}`;
  document.querySelector("#review-snapshots").replaceChildren(...submission.artifact_snapshots.map(renderSnapshot));
  await loadReviewEvents(submission.workspace_id);
  if (viewGeneration !== reviewLoadGeneration || reviewContext?.submission?.id !== submission.id) return;
}

async function retryTeacherReviewQueue(assignmentId) {
  const previous = reviewQueueResults.get(assignmentId);
  if (!previous || !previous.error || previous.loading) return;
  const viewGeneration = reviewLoadGeneration;
  const requestGeneration = (reviewQueueRetryGenerations.get(assignmentId) || 0) + 1;
  reviewQueueRetryGenerations.set(assignmentId, requestGeneration);
  reviewQueueResults.set(assignmentId, { ...previous, loading: true });
  renderReviewTaskChoices([...reviewQueueResults.values()]);
  try {
    const submissions = await readReviewQueueForAssignment(previous.assignment);
    if (viewGeneration !== reviewLoadGeneration || requestGeneration !== reviewQueueRetryGenerations.get(assignmentId)) return;
    reviewQueueResults.set(assignmentId, { assignment: previous.assignment, submissions, error: "", loading: false });
    renderReviewTaskChoices([...reviewQueueResults.values()]);
    updateTeacherReviewCount();
    if (document.querySelector("#review-details").hidden) {
      const remainingErrors = [...reviewQueueResults.values()].filter((item) => item.error).length;
      document.querySelector("#review-empty").textContent = selectedReviewAssignmentId === assignmentId
        ? "此任务复核队列已恢复；请明确选择此任务查看提交详情。"
        : remainingErrors
        ? `${remainingErrors} 个任务读取失败，状态未知；其他任务结果仍保留在任务概览中。`
        : "已读取任务复核概览。请选择一个任务后查看提交详情；系统不会自动选择任务。";
    }
  } catch (error) {
    if (viewGeneration !== reviewLoadGeneration || requestGeneration !== reviewQueueRetryGenerations.get(assignmentId)) return;
    reviewQueueResults.set(assignmentId, { ...previous, loading: false, error: errorStateFor(error, "读取复核队列").message });
    renderReviewTaskChoices([...reviewQueueResults.values()]);
  }
}

async function loadReviewQueue() {
  const historyRequestId = ++reviewLoadGeneration;
  reviewEventGeneration += 1;
  reviewQueueResults = new Map();
  reviewQueueRetryGenerations = new Map();
  document.querySelector("#review-count").textContent = "?";
  reviewDetailResults = new Map();
  reviewDetailRetryGenerations = new Map();
  remediationReadResults = new Map();
  remediationRetryGenerations = new Map();
  const empty = document.querySelector("#review-empty");
  const directoryRetry = document.querySelector("#review-directory-retry");
  directoryRetry.hidden = true;
  document.querySelector("#review-task-list").hidden = true;
  const details = document.querySelector("#review-details");
  const resultMessage = document.querySelector("#review-result");
  resultMessage.hidden = true;
  resultMessage.textContent = "";
  if (reviewWriteAttempt) {
    reviewContext = reviewWriteAttempt.context;
    details.hidden = false;
    empty.hidden = true;
    void retryReviewHistory();
    syncReviewAttemptControls();
    return;
  }
  reviewContext = null;
  details.hidden = true;
  empty.hidden = false;
  empty.textContent = "正在刷新所选任务的复核、补正和事件状态。";
  syncReviewAttemptControls();
  document.querySelector("#remediation-status").textContent = "正在从本机合成 API 读取补正状态。";
  let remediationReadComplete = false;
  let reviewHistoryLoaded = false;
  let failureStage = "读取复核队列";
  try {
    failureStage = "读取任务目录";
    const assignments = (await api.listAssignments()).data.assignments;
    if (historyRequestId !== reviewLoadGeneration) return;
    document.querySelector("#api-state").textContent = "教师任务目录读取成功；其他复核区域状态分别显示。";
    const published = assignments.filter((item) => item.state === "PUBLISHED" && item.workspace);
    await loadReviewHistory(published);
    if (historyRequestId !== reviewLoadGeneration) return;
    reviewHistoryLoaded = true;
    failureStage = "读取补正状态";
    const remediationResults = await Promise.all(published.map(async (assignment) => {
      try {
        return { assignment, remediations: (await api.remediations(assignment.workspace.id)).data.remediations, error: "" };
      } catch (error) {
        return { assignment, remediations: [], error: errorStateFor(error, "读取补正状态").message };
      }
    }));
    if (historyRequestId !== reviewLoadGeneration) return;
    remediationReadResults = new Map(remediationResults.map((item) => [item.assignment.id, item]));
    const remediationEntries = remediationResults.flatMap(({ assignment, remediations }) =>
      remediations.map((remediation) => ({ assignment, remediation })));
    renderTeacherRemediationResults();
    remediationReadComplete = true;
    failureStage = "读取复核队列";
    const loadedAssignments = await Promise.all(published.map(async (assignment) => {
      try {
        return { assignment, submissions: await readReviewQueueForAssignment(assignment), error: "" };
      } catch (error) {
        return { assignment, submissions: [], error: errorStateFor(error, "读取复核队列").message };
      }
    }));
    if (historyRequestId !== reviewLoadGeneration) return;
    reviewQueueResults = new Map(loadedAssignments.map((item) => [item.assignment.id, item]));
    const queueErrors = loadedAssignments.filter((item) => item.error);
    renderReviewTaskChoices(loadedAssignments);
    updateTeacherReviewCount();
    if (!published.length) {
      selectedReviewAssignmentId = null;
      reviewContext = null;
      details.hidden = true;
      empty.hidden = false;
      empty.textContent = "当前没有已发布任务，因此没有可复核队列。";
      updateTeacherReviewCount();
      syncReviewAttemptControls();
      return;
    }
    if (!selectedReviewAssignmentId) {
      reviewContext = null;
      details.hidden = true;
      empty.hidden = false;
      empty.textContent = "已读取任务复核概览。请选择一个任务后查看提交详情；失败任务显示为状态未知并可单独重试。";
      updateTeacherReviewCount();
      syncReviewAttemptControls();
      return;
    }
    const selectedResult = loadedAssignments.find((item) => item.assignment.id === selectedReviewAssignmentId);
    if (!selectedResult || selectedResult.error) {
      reviewContext = null;
      details.hidden = true;
      empty.hidden = false;
      empty.textContent = selectedResult?.error
        ? `${selectedResult.assignment.task.title} 的复核队列读取失败，状态未知：${selectedResult.error}`
        : "所选任务不在当前复核目录中，状态未知。请重新读取。";
      updateTeacherReviewCount();
      syncReviewAttemptControls();
      return;
    }
    const pendingAssignment = selectedResult.submissions.length ? selectedResult : null;
    if (pendingAssignment) {
      const submission = pendingAssignment.submissions[pendingAssignment.submissions.length - 1];
      reviewDetailResults.set(pendingAssignment.assignment.id, {
        assignment: pendingAssignment.assignment,
        submission,
        error: "",
        loading: false,
      });
      failureStage = "读取工作区详情";
      const workspace = await api.getWorkspace(submission.workspace_id);
      if (historyRequestId !== reviewLoadGeneration) return;
      if (workspace.data.assignment_id !== pendingAssignment.assignment.id) {
        throw new WorkspaceApiError({ status: 200, code: "invalid_response", message: "工作区不属于当前所选任务。", retryable: false });
      }
      reviewContext = { assignment: pendingAssignment.assignment, submission, revision: workspace.data.revision };
    }
    if (!reviewContext) {
      details.hidden = true;
      empty.hidden = false;
      empty.textContent = queueErrors.length
        ? `${queueErrors.length} 个任务读取失败，状态未知；其他任务结果仍保留在任务概览中。${remediationEntries.length ? "下方仍显示已读取的补正记录。" : ""}`
        : remediationEntries.length
        ? `${selectedResult.assignment.task.title} 当前没有待复核的提交；下方仍显示已发布任务的补正记录及状态。`
        : `${selectedResult.assignment.task.title} 当前没有待复核的提交，也没有补正记录。`;
      updateTeacherReviewCount();
      syncReviewAttemptControls();
      return;
    }
    const { assignment, submission } = reviewContext;
    await showReviewSubmissionDetails(reviewContext, historyRequestId);
    if (historyRequestId !== reviewLoadGeneration) return;
    failureStage = "读取复核队列";
    details.hidden = false;
    empty.hidden = false;
    empty.textContent = queueErrors.length
      ? `所选任务详情已加载；另有 ${queueErrors.length} 个任务读取失败，仍以未知状态保留在任务概览中。`
      : "已载入所选任务详情。可从上方任务概览切换任务。";
    document.querySelector("#api-state").textContent = "已连接本机合成 API；复核目录和所选任务详情已读取。";
    syncReviewAttemptControls();
  } catch (error) {
    if (historyRequestId !== reviewLoadGeneration) return;
    const state = errorStateFor(error, failureStage);
    if (!reviewHistoryLoaded) {
      markReviewHistoryUnknown(error);
      details.hidden = true;
      empty.hidden = false;
      if (failureStage === "读取任务目录") {
        empty.textContent = `任务目录刷新失败，复核任务列表状态未知：${state.message}`;
        directoryRetry.hidden = false;
      } else {
        empty.textContent = state.message;
        directoryRetry.hidden = true;
      }
    } else if (details.hidden) {
      empty.hidden = false;
      empty.textContent = `所选任务详情读取失败，状态未知：${state.message}。请重试该任务。`;
      const selected = reviewQueueResults.get(selectedReviewAssignmentId);
      const submission = selected?.submissions?.[selected.submissions.length - 1];
      if (submission) {
        reviewDetailResults.set(selectedReviewAssignmentId, {
          assignment: selected.assignment,
          submission,
          error: state.message,
          loading: false,
        });
        renderReviewTaskChoices([...reviewQueueResults.values()]);
      }
    } else {
      const result = document.querySelector("#review-result");
      result.textContent = `当前提交详情读取失败，状态未知：${state.message}`;
      result.hidden = false;
    }
    document.querySelector("#api-state").textContent = failureStage === "读取任务目录"
      ? `任务目录刷新失败，复核任务列表状态未知：${state.message}`
      : state.message;
    if (!remediationReadComplete) markRemediationStatusUnknown(error);
    syncReviewAttemptControls();
  }
}

document.querySelector("#review-directory-retry").addEventListener("click", () => loadReviewQueue());

document.querySelectorAll("[data-action='new-task'], [data-action='use-template']").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.action === "use-template") {
      form.reset();
      document.querySelector("#task-title").value = "检查订单数据中的不一致记录";
      document.querySelector("#task-goal").value = "检查合成订单数据中的金额与数量、单价关系，找出一条不一致记录，并说明你如何验证判断。";
      document.querySelector("#task-responsibility").value = "指出异常记录，写出至少一个可检查的验证步骤，并说明仍不确定的地方。";
      document.querySelector("#task-deliverable").value = "提交代码或处理结果，并用一段简短说明写明异常记录、验证依据和不确定之处。";
      document.querySelector("input[name='mode'][value='confirm']").checked = true;
      updatePreview();
    }
    navigate("editor");
  });
});

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    navigate(button.dataset.view);
    if (button.dataset.view === "reviews") loadReviewQueue();
  });
});

form.addEventListener("input", updatePreview);
form.addEventListener("change", updatePreview);

document.querySelector("[data-action='save-draft']").addEventListener("click", () => {
  saveTask(false);
});

document.querySelector("[data-action='simulate-publish']").addEventListener("click", () => {
  saveTask(true);
});

document.querySelectorAll("[data-review]").forEach((button) => {
  button.addEventListener("click", async () => {
    let attempt = reviewWriteAttempt;
    if (attempt) {
      if (attempt.inFlight || attempt.phase !== "UNKNOWN" || button.dataset.review !== attempt.action) return;
    } else {
      const reason = document.querySelector("#feedback-reason").value.trim();
      if (!reviewContext) return;
      if (!validateReviewReasonBytes()) {
        document.querySelector("#feedback-reason").reportValidity();
        return;
      }
      if ([...reason].filter((character) => !/\s/u.test(character)).length < 8) {
        document.querySelector("#feedback-reason").setCustomValidity("所有复核动作都需要至少 8 个非空白字符的理由。");
        document.querySelector("#feedback-reason").reportValidity();
        return;
      }
      document.querySelector("#feedback-reason").setCustomValidity("");
      attempt = {
        action: button.dataset.review,
        context: Object.freeze({ ...reviewContext }),
        targetSubmissionId: reviewContext.submission.id,
        revision: reviewContext.revision,
        dto: Object.freeze(mapReviewActionToDto(button.dataset.review, reason)),
        inFlight: false,
        phase: "READY",
      };
      reviewWriteAttempt = attempt;
    }
    attempt.inFlight = true;
    attempt.phase = "IN_FLIGHT";
    syncReviewAttemptControls();
    const { context, dto: reviewDto } = attempt;
    try {
      const result = await api.review(attempt.targetSubmissionId, reviewDto, attempt.revision, context.submission.version);
      reviewWriteAttempt = null;
      reviewContext = context;
      syncReviewAttemptControls();
      const requested = result.data.review_action.kind === "ACKNOWLEDGE"
        ? `本轮已在本机合成 API 关闭。教师理由：${result.data.review_action.reason}`
        : `补正要求已记录；学生将看到：${result.data.review_action.reason}`;
      document.querySelector("#remediation-status").textContent = requested;
      document.querySelector("#api-state").textContent = `${requested} 仅当前服务进程内存，非生产。`;
      showToast("教师复核回执已写入本机合成 API。");
      await loadReviewQueue();
    } catch (error) {
      const state = errorStateFor(error, "提交复核意见");
      if (state.kind === "unavailable") {
        let confirmed = false;
        if (reviewDto.kind !== "ACKNOWLEDGE") {
          try { confirmed = await confirmReviewOutcome(api, context.submission, reviewDto); } catch { /* Keep the write outcome unknown when readback is unavailable. */ }
        }
        if (confirmed) {
          reviewWriteAttempt = null;
          reviewContext = context;
          syncReviewAttemptControls();
          const requested = `本机合成 API 读回确认补正要求已记录。学生将看到：${reviewDto.reason}`;
          document.querySelector("#review-result").textContent = requested;
          document.querySelector("#review-result").hidden = false;
          document.querySelector("#remediation-status").textContent = requested;
          document.querySelector("#api-state").textContent = `${requested} 仅当前服务进程内存，非生产。`;
          showToast("已从本机合成 API 读回确认复核状态。");
          await loadReviewQueue();
          return;
        }
        markReviewAttemptUnknown(attempt, state.message);
        return;
      }
      // A 409 or validation rejection is an explicit API refusal, not an unknown receipt.
      reviewWriteAttempt = null;
      reviewContext = null;
      syncReviewAttemptControls();
      document.querySelector("#review-result").textContent = state.message;
      document.querySelector("#review-result").hidden = false;
      document.querySelector("#api-state").textContent = state.message;
      showToast(state.message);
      await loadReviewQueue();
    }
  });
});

document.querySelectorAll(".submission-tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".submission-tab").forEach((tab) => tab.classList.remove("is-active"));
    button.classList.add("is-active");
    if (button.textContent.trim() === "结果文件") {
      const snapshot = document.querySelector(".snapshot-item[data-logical-name='orders.csv']");
      if (snapshot) snapshot.scrollIntoView({ block: "nearest", behavior: "smooth" });
      else showToast("当前提交没有包含 orders.csv。");
    } else if (button.textContent.trim() === "代码差异") {
      showToast("API 返回的是提交文本快照；起始文件仍未绑定到唯一权威来源，因此这里不计算代码差异。");
    }
  });
});

updatePreview();
refreshAssignments().then((result) => {
  if (!result.stale && result.generation === assignmentListReadGeneration) {
    document.querySelector("#api-state").textContent = "已连接本机合成 API。固定教师演示角色；任务与提交仅保存在当前服务进程内存，非生产。";
  }
}).catch(() => {
  // The list-local renderer preserves failure as unknown and offers an independent retry.
});
