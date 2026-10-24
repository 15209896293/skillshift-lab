"use strict";

import { createWorkspaceClient, errorStateFor, mapFilesToSubmissionDto, WorkspaceApiError } from "../workspace-client.mjs";

const files = {
  "main.py": {
    language: "Python",
    content: "import csv\n\n\ndef find_inconsistent_orders(path):\n    issues = []\n    with open(path, newline=\"\", encoding=\"utf-8\") as source:\n        for row in csv.DictReader(source):\n            quantity = int(row[\"quantity\"])\n            unit_price = float(row[\"unit_price\"])\n            amount = float(row[\"amount\"])\n            if amount != quantity * unit_price:\n                issues.append(row[\"order_id\"])\n    return issues\n\n\n# 固定合成示例：这里只展示代码，不会执行。\n",
  },
  "orders.csv": {
    language: "CSV · 固定合成数据",
    content: "order_id,quantity,unit_price,amount\nO-104,1,45.00,45.00\nO-105,2,89.00,160.00\nO-106,3,12.00,36.00\n",
  },
  "README.md": {
    language: "Markdown",
    content: "# 合成订单核对项目\n\n检查每条记录中的 amount 是否与 quantity × unit_price 一致。\n\n提交时请说明：\n- 你发现了什么；\n- 如何验证；\n- 哪些业务规则仍需确认。\n\n注意：这些文件只是页面内固定示例，不会运行或写入本机。\n",
  },
};

const editor = document.querySelector("#code-editor");
const lineNumbers = document.querySelector("#line-numbers");
const activeFileName = document.querySelector("#active-file-name");
const editorLanguage = document.querySelector("#editor-language");
const dirtyDot = document.querySelector("#dirty-dot");
const editStatus = document.querySelector("#edit-status");
const diffCard = document.querySelector("#diff-card");
const proposalStatus = document.querySelector("#proposal-status");
const agentMessages = document.querySelector("#agent-messages");
const agentInput = document.querySelector("#agent-input");
const submitDialog = document.querySelector("#submit-dialog");
const submissionForm = document.querySelector("#submission-form");
const submissionNote = document.querySelector("#submission-note");
const toast = document.querySelector("#toast");
const api = createWorkspaceClient("student");
let workspaceId = null;
let currentAssignmentId = null;
let workspaceRevision = null;
let workspaceState = null;
let pendingStartAttempt = null;
let workspaceInteractive = false;
let proposalId = null;
let proposalDiff = "";
let currentFile = "main.py";
let pendingSubmission = null;
let submissionInFlight = false;
let agentTurnAttempt = null;
let agentTurnInFlight = false;
let pauseAttempt = null;
let pauseReadInFlight = false;
let proposalAcceptAttempt = null;
let proposalDecisionAttempt = null;
let remediationReadGeneration = 0;
let latestSubmissionReadGeneration = 0;
let workspaceLoadGeneration = 0;
let workingContent = Object.fromEntries(Object.entries(files).map(([name, file]) => [name, file.content]));
let dirtyFiles = new Set();
const taskDrafts = new Map();
const initialAgentMessages = [...agentMessages.childNodes].map((node) => node.cloneNode(true));
let toastTimer = 0;

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { toast.hidden = true; }, 3000);
}

function setApiState(message) {
  document.querySelector("#api-state").textContent = message;
}

function renderStudentTaskReadFailure(message, selectedAssignmentId = null) {
  const region = document.querySelector("#api-state");
  region.replaceChildren(document.createTextNode(`任务读取失败，当前状态未知。${message} `));
  const retry = document.createElement("button");
  retry.type = "button";
  retry.textContent = "重新读取任务";
  retry.addEventListener("click", () => loadStudentWorkspace(selectedAssignmentId));
  region.append(retry);
}

function renderStudentActiveTaskConflict(message) {
  const region = document.querySelector("#api-state");
  region.replaceChildren(document.createTextNode(`所选任务没有开始：另一个任务正在进行。${message} 请重新读取目录并明确选择任务。 `));
  const retry = document.createElement("button");
  retry.type = "button";
  retry.textContent = "重新读取任务目录";
  retry.addEventListener("click", () => loadStudentWorkspace());
  region.append(retry);
}

function workspaceStateLabel(state) {
  const labels = {
    ASSIGNED: "已分配，准备开始",
    IN_PROGRESS: "进行中",
    PAUSED: "已暂停",
    REVIEW_REQUIRED: "等待教师复核",
    FEEDBACK_REQUIRED: "等待你补正",
    RESUBMITTED: "已补交，等待教师复核",
    CLOSED: "本轮已结束",
  };
  if (!state) return "未连接";
  return labels[state] || "状态未知";
}

function setWorkspaceState(state) {
  workspaceState = state;
  workspaceInteractive = ["IN_PROGRESS", "FEEDBACK_REQUIRED"].includes(state);
  const canSubmit = proposalAcceptAttempt === null && proposalDecisionAttempt === null
    && (pendingSubmission !== null || ["IN_PROGRESS", "FEEDBACK_REQUIRED"].includes(state));
  document.querySelector("[data-action='open-submit']").disabled = !canSubmit;
  document.querySelector("#task-picker-state").textContent = workspaceStateLabel(state);
  const pauseButton = document.querySelector("#pause-task");
  if (pauseButton) pauseButton.disabled = state !== "IN_PROGRESS";
  document.querySelector("#task-state").lastChild.textContent = ` ${workspaceStateLabel(state)} · 合成`;
  setSubmissionContentFrozen(!workspaceInteractive || submissionInFlight || pendingSubmission !== null);
  syncAgentTurnControls();
}

function setSubmissionContentFrozen(frozen) {
  const editorFrozen = frozen || !workspaceInteractive || proposalAcceptAttempt !== null;
  editor.disabled = editorFrozen;
  document.querySelectorAll(".file-item").forEach((button) => { button.disabled = editorFrozen; });
  submissionNote.disabled = frozen;
}

function syncAgentTurnControls() {
  const pending = !workspaceInteractive || agentTurnInFlight || proposalAcceptAttempt !== null || proposalDecisionAttempt !== null;
  document.querySelector("#send-agent").disabled = pending;
  document.querySelectorAll("[data-prompt]").forEach((button) => { button.disabled = pending; });
}

function renderRemediationStatus(message, workspaceIdForRetry = null, readState = "unknown") {
  const region = document.querySelector("#remediation-state");
  region.replaceChildren(document.createTextNode(message));
  region.dataset.readState = readState;
  region.removeAttribute("aria-busy");
  if (workspaceIdForRetry) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "重新读取补正状态";
    retry.addEventListener("click", () => loadRemediations(workspaceIdForRetry));
    region.append(document.createTextNode(" "), retry);
  }
  region.hidden = false;
}

async function loadRemediations(workspaceIdToRead) {
  const requestGeneration = ++remediationReadGeneration;
  const region = document.querySelector("#remediation-state");
  const preserveLastSuccess = region.dataset.readState === "confirmed" || region.dataset.readState === "confirmed-with-error";
  const retryButton = region.querySelector("button");
  if (retryButton) retryButton.disabled = true;
  if (preserveLastSuccess) {
    region.querySelectorAll("[data-read-refresh], [data-read-failure]").forEach((node) => node.remove());
    region.querySelector("button")?.remove();
    const refresh = document.createElement("span");
    refresh.dataset.readRefresh = "true";
    refresh.textContent = "正在重新读取补正状态……";
    region.append(document.createTextNode(" "), refresh);
    region.setAttribute("aria-busy", "true");
  } else {
    renderRemediationStatus("正在从本机合成 API 读取补正状态……", null, "loading");
  }
  try {
    const remediations = (await api.remediations(workspaceIdToRead)).data.remediations;
    if (requestGeneration !== remediationReadGeneration || workspaceIdToRead !== workspaceId) return;
    const openRemediation = remediations.find((item) => item.state === "OPEN");
    if (openRemediation) {
      renderRemediationStatus(`教师补正请求（${openRemediation.requested_action}）：${openRemediation.reason}`, null, "confirmed");
    } else {
      renderRemediationStatus("本机合成 API 已确认：当前没有待补正请求。", null, "confirmed");
    }
  } catch (error) {
    if (requestGeneration !== remediationReadGeneration || workspaceIdToRead !== workspaceId) return;
    const state = errorStateFor(error, "读取补正状态");
    if (preserveLastSuccess) {
      region.querySelector("[data-read-refresh]")?.remove();
      const notice = document.createElement("span");
      notice.dataset.readFailure = "true";
      notice.textContent = `本次重读失败，补正状态未知；以下保留上次成功记录。${state.message}`;
      const retry = document.createElement("button");
      retry.type = "button";
      retry.textContent = "重新读取补正状态";
      retry.addEventListener("click", () => loadRemediations(workspaceIdToRead));
      region.append(document.createTextNode(" "), notice, document.createTextNode(" "), retry);
      region.dataset.readState = "confirmed-with-error";
      region.setAttribute("aria-busy", "false");
    } else {
      renderRemediationStatus(`补正状态未知，API 读取失败。${state.message}`, workspaceIdToRead);
    }
  } finally {
    if (requestGeneration === remediationReadGeneration) {
      const retry = document.querySelector("#remediation-state button");
      if (retry) retry.disabled = false;
    }
  }
}

function renderLatestSubmissionState(message, workspaceIdForRetry = null) {
  const region = document.querySelector("#latest-submission-state");
  region.replaceChildren(document.createTextNode(message));
  region.dataset.readState = "unknown";
  region.removeAttribute("aria-busy");
  if (workspaceIdForRetry) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "重新读取提交记录";
    retry.addEventListener("click", () => loadLatestSubmission(workspaceIdForRetry));
    region.append(document.createTextNode(" "), retry);
  }
  region.hidden = false;
}

function renderLatestSubmission(submission) {
  const region = document.querySelector("#latest-submission-state");
  region.replaceChildren();
  region.dataset.readState = "confirmed";
  region.removeAttribute("aria-busy");
  if (submission === null) {
    region.append(document.createTextNode("本机合成 API 当前没有提交记录。"));
    region.hidden = false;
    return;
  }

  const heading = document.createElement("strong");
  heading.textContent = `本机 API 最近提交：${submission.id} · 第 ${submission.version} 版 · ${submission.state}`;
  const explanation = document.createElement("p");
  explanation.textContent = `学生说明：${submission.student_explanation}`;
  const list = document.createElement("ul");
  for (const snapshot of submission.artifact_snapshots) {
    const item = document.createElement("li");
    const details = document.createElement("div");
    details.textContent = `${snapshot.logical_name} · ${snapshot.size_bytes} UTF-8 字节 · SHA-256 ${snapshot.sha256}`;
    const content = document.createElement("pre");
    content.textContent = snapshot.content;
    item.append(details, content);
    list.append(item);
  }
  const boundary = document.createElement("p");
  boundary.textContent = "记录来自当前服务进程的内存暂存；重启后清空，非生产。它只表示 API 当前返回的最近记录，不能证明某次回执未知的提交请求就是这条记录。";
  region.append(heading, explanation, list, boundary);
  region.hidden = false;
}

async function loadLatestSubmission(workspaceIdToRead) {
  const requestGeneration = ++latestSubmissionReadGeneration;
  const region = document.querySelector("#latest-submission-state");
  const preserveLastSuccess = region.dataset.readState === "confirmed" || region.dataset.readState === "confirmed-with-error";
  const retryButton = region.querySelector("button");
  if (retryButton) retryButton.disabled = true;
  if (preserveLastSuccess) {
    region.querySelectorAll("[data-read-refresh], [data-read-failure]").forEach((node) => node.remove());
    region.querySelector("button")?.remove();
    const refresh = document.createElement("span");
    refresh.dataset.readRefresh = "true";
    refresh.textContent = "正在重新读取最近提交……";
    region.append(document.createTextNode(" "), refresh);
    region.setAttribute("aria-busy", "true");
  } else {
    renderLatestSubmissionState("正在从本机合成 API 读取最近提交……");
  }
  try {
    const submission = (await api.latestSubmission(workspaceIdToRead)).data.submission;
    if (requestGeneration !== latestSubmissionReadGeneration || workspaceIdToRead !== workspaceId) return;
    renderLatestSubmission(submission);
  } catch (error) {
    if (requestGeneration !== latestSubmissionReadGeneration || workspaceIdToRead !== workspaceId) return;
    const state = errorStateFor(error, "读取最近提交");
    if (preserveLastSuccess) {
      region.querySelector("[data-read-refresh]")?.remove();
      const notice = document.createElement("p");
      notice.dataset.readFailure = "true";
      notice.textContent = `本次重读失败，最近提交状态未知；以下保留上次成功记录。${state.message}`;
      const retry = document.createElement("button");
      retry.type = "button";
      retry.textContent = "重新读取提交记录";
      retry.addEventListener("click", () => loadLatestSubmission(workspaceIdToRead));
      region.append(notice, retry);
      region.dataset.readState = "confirmed-with-error";
      region.setAttribute("aria-busy", "false");
    } else {
      renderLatestSubmissionState(`最近提交读取失败，当前状态未知。${state.message}`, workspaceIdToRead);
    }
  } finally {
    if (requestGeneration === latestSubmissionReadGeneration) {
      const retry = region.querySelector("button");
      if (retry) retry.disabled = false;
    }
  }
}

function saveTaskDraft() {
  if (!currentAssignmentId) return;
  taskDrafts.set(currentAssignmentId, {
    workingContent: { ...workingContent },
    dirtyFiles: [...dirtyFiles],
    currentFile,
    proposalId,
    proposalDiff,
    proposalStatus: proposalStatus.textContent,
    diffHidden: diffCard.hidden,
    agentQuestion: agentInput.value,
    agentMessages: [...agentMessages.childNodes].map((node) => node.cloneNode(true)),
  });
}

async function loadStudentWorkspace(selectedAssignmentId = null) {
  const picker = document.querySelector("#task-picker");
  const pickerState = document.querySelector("#task-picker-state");
  if (selectedAssignmentId && selectedAssignmentId !== currentAssignmentId && workspaceState === "IN_PROGRESS") {
    picker.value = currentAssignmentId || "";
    pickerState.textContent = "请先暂停当前任务，再切换。";
    setApiState("请先暂停当前任务，再切换到另一个任务。");
    return;
  }
  const loadGeneration = ++workspaceLoadGeneration;
  remediationReadGeneration += 1;
  latestSubmissionReadGeneration += 1;
  const workArea = document.querySelector(".work-area");
  const taskRail = document.querySelector(".task-rail");
  picker.disabled = true;
  workArea.hidden = true;
  taskRail.hidden = true;
  document.querySelector("#latest-submission-state").hidden = true;
  document.querySelector("#remediation-state").hidden = true;
  document.querySelector("#latest-submission-state").dataset.readState = "loading";
  document.querySelector("#remediation-state").dataset.readState = "loading";
  setApiState("正在读取所选任务；任务详情在确认对应工作区前会保持隐藏。");
  setWorkspaceState(null);
  workspaceId = null;
  currentAssignmentId = null;
  try {
    const assignments = (await api.listAssignments()).data.assignments;
    if (loadGeneration !== workspaceLoadGeneration) return;
    const publishedAssignments = assignments.filter((item) => item.state === "PUBLISHED" && item.workspace);
    picker.replaceChildren(new Option("请选择任务", ""), ...publishedAssignments.map((item) => new Option(item.task.title, item.id)));
    picker.disabled = publishedAssignments.length === 0;
    if (selectedAssignmentId && publishedAssignments.some((item) => item.id === selectedAssignmentId)) {
      picker.value = selectedAssignmentId;
    }
    if (!publishedAssignments.length) {
      picker.replaceChildren(new Option("当前没有可用任务", ""));
      pickerState.textContent = "暂无可用任务";
      setApiState("当前没有已发布的本机合成任务。页面文件只是固定合成示例；不会报告 Agent 协作或提交成功。");
      return;
    }
    if (!selectedAssignmentId) {
      setWorkspaceState(null);
      picker.value = "";
      pickerState.textContent = "请选择任务";
      setApiState("请选择一个任务。系统不会按目录顺序或更新时间替你选择；如有任务正在进行，请先暂停后再切换。");
      return;
    }
    const assignment = publishedAssignments.find((item) => item.id === selectedAssignmentId);
    if (!assignment) {
      setApiState("所选任务不在当前可用目录中，任务状态未知。请重新读取任务目录。");
      return;
    }
    const current = (await api.getAssignment(assignment.id)).data;
    if (loadGeneration !== workspaceLoadGeneration) return;
    const workspaceIdFromAssignment = current.workspace?.id;
    if (!workspaceIdFromAssignment) {
      setApiState("任务已发布，但 API 尚未提供工作区；没有开始或提交任务。");
      return;
    }
    if (current.workspace.assignment_id !== assignment.id) {
      throw new WorkspaceApiError({ status: 200, code: "invalid_response", message: "所选任务与其工作区绑定不一致。", retryable: false });
    }
    let workspace = (await api.getWorkspace(workspaceIdFromAssignment)).data;
    if (loadGeneration !== workspaceLoadGeneration) return;
    if (workspace.assignment_id !== assignment.id) {
      throw new WorkspaceApiError({ status: 200, code: "invalid_response", message: "读取到的工作区不属于所选任务。", retryable: false });
    }
    if (workspace.state === "ASSIGNED" || workspace.state === "PAUSED") {
      if (loadGeneration !== workspaceLoadGeneration) return;
      pendingStartAttempt = { assignmentId: assignment.id, workspaceId: workspace.id, revision: workspace.revision };
      let started;
      try {
        started = await api.startWorkspace(workspace.id, workspace.revision, assignment.id);
      } catch (error) {
        const outcome = errorStateFor(error, "开始任务");
        if (outcome.kind !== "unavailable" && outcome.kind !== "error") pendingStartAttempt = null;
        throw error;
      }
      if (loadGeneration !== workspaceLoadGeneration) return;
      if (started.data.workspace.assignment_id !== assignment.id) {
        throw new WorkspaceApiError({ status: 200, code: "invalid_response", message: "开始回执中的工作区不属于所选任务。", retryable: false });
      }
      workspace = started.data.workspace;
      workspaceRevision = started.revision ?? workspace.revision;
    } else {
      workspaceRevision = workspace.revision;
    }
    workspaceId = workspace.id;
    currentAssignmentId = assignment.id;
    const savedDraft = taskDrafts.get(currentAssignmentId);
    workingContent = savedDraft ? { ...savedDraft.workingContent } : Object.fromEntries(Object.entries(files).map(([name, file]) => [name, file.content]));
    dirtyFiles = new Set(savedDraft?.dirtyFiles || []);
    proposalId = savedDraft?.proposalId || null;
    proposalDiff = savedDraft?.proposalDiff || "";
    proposalStatus.textContent = savedDraft?.proposalStatus || "API 只记录你的决定；页面内存中的演示编辑不会写回服务端，也不会运行。";
    diffCard.hidden = savedDraft?.diffHidden ?? true;
    agentInput.value = savedDraft?.agentQuestion || "";
    agentMessages.replaceChildren(...(savedDraft?.agentMessages || initialAgentMessages).map((node) => node.cloneNode(true)));
    loadFile(savedDraft?.currentFile && files[savedDraft.currentFile] ? savedDraft.currentFile : "main.py");
    picker.value = assignment.id;
    pickerState.textContent = workspaceStateLabel(workspace.state);
    setWorkspaceState(workspace.state);
    if (pendingStartAttempt?.assignmentId === assignment.id && pendingStartAttempt.workspaceId === workspace.id
      && workspace.state === "IN_PROGRESS") pendingStartAttempt = null;
    document.querySelector("#task-title").textContent = current.task.title;
    document.querySelector("#rail-task-title").textContent = current.task.title;
    document.querySelector(".task-summary > p").textContent = current.task.goal;
    const modeLabel = current.task.collaboration_mode === "QA_ONLY" ? "仅问答" : "先看建议，再由你决定";
    const modeFooter = document.querySelector(".task-footer > span:nth-child(2)");
    const modeTitle = modeFooter.querySelector("b");
    modeFooter.replaceChildren(modeTitle, document.createTextNode(` ${modeLabel}`));
    const details = document.querySelector("#task-details");
    details.textContent = `学生责任：${current.task.student_responsibility} 提交要求：${current.task.submission_requirements.join("；")} 执行状态：未开放。`;
    workArea.hidden = false;
    taskRail.hidden = false;
    setApiState("已连接本机合成 API。固定学生演示角色；任务、Agent 回合和提交快照仅在当前服务进程内存，非生产。代码执行未开放。");
    await loadRemediations(workspace.id);
    if (loadGeneration !== workspaceLoadGeneration) return;
    await loadLatestSubmission(workspace.id);
  } catch (error) {
    if (loadGeneration !== workspaceLoadGeneration) return;
    const state = errorStateFor(error, "读取任务");
    if (error?.code === "active_task_exists") {
      renderStudentActiveTaskConflict(state.message);
      pickerState.textContent = "启动冲突 · 需重新选择";
    } else {
      renderStudentTaskReadFailure(state.message, selectedAssignmentId);
      pickerState.textContent = "读取失败 · 未知";
    }
  } finally {
    if (loadGeneration === workspaceLoadGeneration) picker.disabled = picker.options.length <= 1 || pendingStartAttempt !== null;
  }
}

document.querySelector("#task-picker").addEventListener("change", async (event) => {
  const nextAssignmentId = event.target.value;
  if (!nextAssignmentId) return;
  if (pendingStartAttempt && nextAssignmentId !== pendingStartAttempt.assignmentId) {
    event.target.value = pendingStartAttempt.assignmentId;
    document.querySelector("#task-picker-state").textContent = "开始请求结果尚未确认；请重新读取原任务状态后再切换。";
    return;
  }
  if (workspaceState === "IN_PROGRESS" && nextAssignmentId !== currentAssignmentId) {
    event.target.value = currentAssignmentId;
    document.querySelector("#task-picker-state").textContent = "请先暂停当前任务，再切换。";
    return;
  }
  if (pauseAttempt) {
    event.target.value = currentAssignmentId || "";
    showToast("暂停结果尚未确认；请先重读当前任务状态。");
    return;
  }
  if (pendingSubmission || submissionInFlight || agentTurnInFlight || agentTurnAttempt || proposalAcceptAttempt || proposalDecisionAttempt) {
    event.target.value = currentAssignmentId || "";
    document.querySelector("#task-picker-state").textContent = "有请求尚未确认；请先完成同一请求的重试或等待明确结果。";
    return;
  }
  saveTaskDraft();
  await loadStudentWorkspace(nextAssignmentId);
});

document.querySelector("#pause-task").addEventListener("click", async () => {
  if (!workspaceId || workspaceState !== "IN_PROGRESS" || pauseAttempt) return;
  if (pendingSubmission || submissionInFlight || agentTurnInFlight || agentTurnAttempt || proposalAcceptAttempt || proposalDecisionAttempt) {
    document.querySelector("#task-picker-state").textContent = "有请求尚未确认，暂不能暂停或切换。";
    return;
  }
  saveTaskDraft();
  const button = document.querySelector("#pause-task");
  button.disabled = true;
  try {
    const result = await api.pauseWorkspace(workspaceId, workspaceRevision, currentAssignmentId);
    workspaceRevision = result.revision ?? result.data.workspace.revision;
    setWorkspaceState("PAUSED");
    document.querySelector("#task-picker-state").textContent = "任务已暂停；现在可以选择另一个任务。";
  } catch (error) {
    const state = errorStateFor(error, "暂停任务");
    pauseAttempt = {
      workspaceId,
      assignmentId: currentAssignmentId,
      revision: workspaceRevision,
      phase: error?.definitiveRejection === true ? "REJECTED_READBACK" : "UNKNOWN_WRITE",
    };
    setWorkspaceState(null);
    renderPauseRecoveryAction(`暂停结果未知；切换已锁定。${state.message}`, readPauseAttemptState, "重读任务状态");
  } finally {
    button.disabled = workspaceState !== "IN_PROGRESS" || pauseAttempt !== null;
  }
});

function renderPauseRecoveryAction(message, action, label) {
  const region = document.querySelector("#task-picker-state");
  region.replaceChildren(document.createTextNode(`${message} `));
  const retry = document.createElement("button");
  retry.type = "button";
  retry.textContent = label;
  retry.addEventListener("click", action);
  region.append(retry);
}

async function retryPauseAttempt(attempt) {
  if (!pauseAttempt || pauseAttempt !== attempt || pauseReadInFlight) return;
  pauseReadInFlight = true;
  document.querySelector("#task-picker-state").textContent = "正在用原修订号和幂等请求重试暂停；不能切换任务。";
  try {
    const result = await api.pauseWorkspace(attempt.workspaceId, attempt.revision, attempt.assignmentId);
    if (pauseAttempt !== attempt || workspaceId !== attempt.workspaceId) return;
    workspaceRevision = result.revision ?? result.data.workspace.revision;
    pauseAttempt = null;
    setWorkspaceState("PAUSED");
    document.querySelector("#task-picker-state").textContent = "暂停回执已确认；现在可以选择另一个任务。";
  } catch (error) {
    if (pauseAttempt !== attempt || workspaceId !== attempt.workspaceId) return;
    const state = errorStateFor(error, "重试原暂停请求");
    if (error?.status > 0 && error.status < 500) attempt.phase = "REJECTED_READBACK";
    renderPauseRecoveryAction(`原暂停请求尚未确认。${state.message}`, readPauseAttemptState, "重读任务状态");
  } finally {
    pauseReadInFlight = false;
    if (pauseAttempt) document.querySelector("#pause-task").disabled = true;
  }
}

async function readPauseAttemptState() {
  if (!pauseAttempt || pauseReadInFlight) return;
  pauseReadInFlight = true;
  const attempt = pauseAttempt;
  const region = document.querySelector("#task-picker-state");
  region.textContent = "正在重读当前任务状态；读取完成前不能切换。";
  try {
    const result = await api.getWorkspace(attempt.workspaceId, attempt.assignmentId);
    if (pauseAttempt !== attempt || workspaceId !== attempt.workspaceId) return;
    if (!["IN_PROGRESS", "PAUSED"].includes(result.data.state)) {
      throw new Error("当前任务状态无法安全用于暂停或切换");
    }
    if (result.data.state === "PAUSED") {
      workspaceRevision = result.data.revision;
      pauseAttempt = null;
      setWorkspaceState("PAUSED");
      region.textContent = "任务已暂停；现在可以选择另一个任务。";
    } else if (attempt.phase === "REJECTED_READBACK") {
      workspaceRevision = result.data.revision;
      pauseAttempt = null;
      setWorkspaceState("IN_PROGRESS");
      region.textContent = "原暂停请求已明确被拒绝；任务仍在进行，修订号已同步。需要暂停时请重新确认。";
    } else {
      setWorkspaceState(null);
      renderPauseRecoveryAction(
        "任务仍在进行；为确认原请求结果，请使用原修订号和幂等请求重试。",
        () => retryPauseAttempt(attempt),
        "重试原暂停请求",
      );
    }
  } catch (error) {
    if (pauseAttempt !== attempt) return;
    const state = errorStateFor(error, "重读任务状态");
    renderPauseRecoveryAction(`任务状态仍未知；切换保持锁定。${state.message}`, readPauseAttemptState, "重读任务状态");
  } finally {
    pauseReadInFlight = false;
    if (pauseAttempt) document.querySelector("#pause-task").disabled = true;
  }
}

function renderLineNumbers() {
  const count = editor.value.split("\n").length;
  lineNumbers.textContent = Array.from({ length: count }, (_, index) => index + 1).join("\n");
}

function loadFile(name) {
  currentFile = name;
  editor.value = workingContent[name];
  activeFileName.textContent = name;
  editorLanguage.textContent = files[name].language;
  document.querySelectorAll(".file-item").forEach((button) => {
    const active = button.dataset.file === name;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  dirtyDot.hidden = !dirtyFiles.has(name);
  editStatus.textContent = dirtyFiles.has(name) ? "未保存的页面演示编辑" : "演示文件";
  diffCard.hidden = true;
  renderLineNumbers();
}

function addUserMessage(question) {
  const bubble = document.createElement("div");
  bubble.className = "user-message";
  bubble.textContent = question;
  agentMessages.append(bubble);
}

function addApiReply(responseText, proposal) {
  document.querySelector("#agent-empty")?.remove();
  const article = document.createElement("article");
  article.className = "agent-message";
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "✳";
  const content = document.createElement("div");
  const author = document.createElement("span");
  author.className = "message-author";
  author.textContent = "项目 Agent · 固定演示内容";
  const text = document.createElement("p");
  text.textContent = responseText;
  content.append(author, text);
  if (proposal?.status === "PROPOSED") {
    const tools = document.createElement("div");
    tools.className = "message-tools";
    const suggestionButton = document.createElement("button");
    suggestionButton.type = "button";
    suggestionButton.dataset.action = "show-diff";
    suggestionButton.textContent = "查看本机合成修改建议";
    tools.append(suggestionButton);
    content.append(tools);
  }
  article.append(avatar, content);
  agentMessages.append(article);
  article.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function showDiff() {
  if (!proposalId) {
    showToast("当前没有 API 返回的修改建议；页面没有显示成功操作。");
    return;
  }
  if (currentFile !== "main.py") {
    showToast("先打开 main.py，再查看这条针对代码文件的合成建议；当前编辑没有被切换。");
    return;
  }
  document.querySelector("#proposal-summary").textContent = proposalDiff || "本机合成 API 未返回建议摘要。";
  proposalStatus.textContent = "API 只记录你的决定；页面内存中的演示编辑不会写回服务端，也不会运行。";
  diffCard.hidden = false;
  diffCard.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function setProposalDecisionPending(pending, retryAction = null) {
  document.querySelectorAll("[data-action='accept'], [data-action='reject'], [data-action='takeover']")
    .forEach((button) => {
      button.disabled = pending || !proposalId || (retryAction !== null && button.dataset.action !== retryAction);
    });
}

async function sendQuestion(value) {
  const question = String(value === undefined ? agentInput.value : value).trim();
  if (!question) {
    agentInput.focus();
    return;
  }
  if (proposalAcceptAttempt !== null) {
    showToast("当前建议的接受结果尚未确认；请先完成同一接受操作，再发送新问题。");
    return;
  }
  if (proposalDecisionAttempt !== null) {
    showToast("当前提案决定仍待确认；请先重试同一决定，再发送新问题。");
    return;
  }
  if (agentTurnInFlight) return;
  if (agentTurnAttempt !== null && question !== agentTurnAttempt.question) {
    const message = "上一问题的回执尚未确认；请将原问题放回输入框后重试。当前新输入已保留。";
    setApiState(message);
    showToast(message);
    return;
  }
  if (!workspaceId || workspaceRevision === null) {
    setApiState("没有已连接的本机合成工作区；问题未发送。");
    return;
  }
  const inputBeforeRequest = agentInput.value;
  const attempt = agentTurnAttempt || { workspaceId, revision: workspaceRevision, question };
  agentTurnAttempt = attempt;
  agentTurnInFlight = true;
  syncAgentTurnControls();
  try {
    const result = await api.agentTurn(attempt.workspaceId, attempt.question, attempt.revision);
    workspaceRevision = result.data.workspace_revision ?? result.revision ?? workspaceRevision;
    if (result.data.turn.availability === "UNAVAILABLE") {
      agentTurnAttempt = null;
      setApiState("本机 scripted-demo Agent 当前不可用；本回合没有提供回复。问题仍保留在输入框中，可调整后再次发送。没有收到成功引导。");
      showToast("本机演示 Agent 当前不可用；没有生成回复。");
      return;
    }
    proposalId = result.data.proposed_action?.id || null;
    proposalDiff = result.data.proposed_action?.diff || "";
    setApiState("本机合成 API 已确认上一 Agent 回合；当前回复来自固定 scripted-demo 内容，没有调用真实模型。");
    agentTurnAttempt = null;
    setProposalDecisionPending(false);
    addUserMessage(attempt.question);
    addApiReply(result.data.turn.response_text, result.data.proposed_action);
    if (agentInput.value === inputBeforeRequest && inputBeforeRequest.trim() === attempt.question) agentInput.value = "";
    showToast("收到本机 scripted-demo 固定回复；没有调用真实模型。");
  } catch (error) {
    const state = errorStateFor(error, "发送问题");
    if (state.kind === "conflict" || state.kind === "rejected") agentTurnAttempt = null;
    const message = ["unavailable", "error", "unknown"].includes(state.kind)
      ? "上一问题的回执尚未确认。请留在当前页面，把原问题放回输入框后重试；刷新会丢失本页重试信息。"
      : state.message;
    setApiState(message);
    showToast(message);
  } finally {
    agentTurnInFlight = false;
    syncAgentTurnControls();
  }
}

document.querySelectorAll(".file-item").forEach((button) => {
  button.addEventListener("click", () => loadFile(button.dataset.file));
});

editor.addEventListener("input", () => {
  workingContent[currentFile] = editor.value;
  dirtyFiles.add(currentFile);
  dirtyDot.hidden = false;
  editStatus.textContent = "未保存的页面演示编辑";
  renderLineNumbers();
});

document.querySelector("[data-action='task-details']").addEventListener("click", (event) => {
  const details = document.querySelector("#task-details");
  details.hidden = !details.hidden;
  event.currentTarget.querySelector("span").textContent = details.hidden ? "⌄" : "⌃";
});

document.querySelector("#send-agent").addEventListener("click", () => sendQuestion());
agentInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendQuestion();
  }
});

agentMessages.addEventListener("click", (event) => {
  const prompt = event.target.closest("[data-prompt]");
  if (prompt) {
    void sendQuestion(prompt.dataset.prompt);
    return;
  }
  const button = event.target.closest("[data-action='show-diff']");
  if (button) showDiff();
});

document.querySelector(".editor-tab").addEventListener("click", () => {
  if (proposalAcceptAttempt !== null) return;
  if (currentFile !== "main.py") loadFile("main.py");
});

document.querySelector("[data-action='open-submit']").addEventListener("click", () => {
  if (!pendingSubmission) submissionNote.value = "";
  submitDialog.showModal();
});

document.querySelector("[data-action='close-diff']").addEventListener("click", () => {
  diffCard.hidden = true;
});

document.querySelector("[data-action='accept']").addEventListener("click", async () => {
  if (proposalDecisionAttempt !== null) return;
  const oldCheck = '            if amount != quantity * unit_price:\n                issues.append(row["order_id"])';
  const replacement = '            expected = quantity * unit_price\n            if amount != expected:\n                print("需要核对", row["order_id"], expected)\n                issues.append(row["order_id"])';
  if (currentFile !== "main.py" || !editor.value.includes(oldCheck)) {
    proposalStatus.textContent = "当前编辑内容与固定建议的适用位置不一致，没有覆盖你的修改；你可以手动参考差异。";
    return;
  }
  if (!workspaceId || !proposalId) {
    proposalStatus.textContent = "没有可记录的本机合成建议；未修改项目内容。";
    return;
  }
  const attempt = proposalAcceptAttempt || {
    proposalId,
    workspaceId,
    revision: workspaceRevision,
    targetFile: currentFile,
    targetContent: editor.value,
  };
  proposalAcceptAttempt = attempt;
  syncAgentTurnControls();
  setSubmissionContentFrozen(pendingSubmission !== null || submissionInFlight);
  setWorkspaceState(workspaceState);
  setProposalDecisionPending(true);
  try {
    const result = await api.decideProposal(attempt.workspaceId, attempt.proposalId, "ACCEPTED", attempt.revision);
    workspaceRevision = result.data.workspace_revision ?? result.revision ?? workspaceRevision;
  } catch (error) {
    const state = errorStateFor(error, "接受修改建议");
    const message = ["unavailable", "error", "unknown"].includes(state.kind)
      ? "接受建议仍未确认。请留在当前页面，使用“接受并查看修改”重试同一请求；刷新会丢失本页重试信息。"
      : state.message;
    setProposalDecisionPending(false, proposalAcceptAttempt !== null ? "accept" : null);
    proposalStatus.textContent = message;
    setApiState(message);
    if (state.kind !== "unavailable" && state.kind !== "error" && state.kind !== "unknown") {
      proposalAcceptAttempt = null;
      syncAgentTurnControls();
      setSubmissionContentFrozen(pendingSubmission !== null || submissionInFlight);
      setWorkspaceState(workspaceState);
    }
    return;
  }
  const targetContent = attempt.targetContent;
  if (workingContent[attempt.targetFile] === targetContent) {
    const updatedContent = targetContent.replace(oldCheck, replacement);
    workingContent[attempt.targetFile] = updatedContent;
    if (currentFile === attempt.targetFile) editor.value = updatedContent;
    dirtyFiles.add(attempt.targetFile);
    if (currentFile === attempt.targetFile) {
      dirtyDot.hidden = false;
      editStatus.textContent = "已接受建议 · 仅页面演示编辑";
    }
    proposalStatus.textContent = "建议已写入捕获的页面内存编辑上下文；未运行，也未保存到本机。你仍可继续修改或撤销编辑。";
  } else {
    proposalStatus.textContent = "建议决定已由本机合成 API 记录，但本地目标内容已变化；为避免覆盖编辑，没有自动应用修改。";
  }
  proposalAcceptAttempt = null;
  proposalId = null;
  proposalDiff = "";
  setProposalDecisionPending(false);
  setApiState("本机合成 API 已确认接受建议；页面内存中的编辑不会写回文件，也不会运行代码。");
  syncAgentTurnControls();
  setSubmissionContentFrozen(pendingSubmission !== null || submissionInFlight);
  setWorkspaceState(workspaceState);
  if (currentFile === attempt.targetFile) renderLineNumbers();
});

async function decideProposal(decision, action) {
  if (proposalAcceptAttempt !== null) return;
  if (proposalDecisionAttempt && proposalDecisionAttempt.decision !== decision) return;
  if (!proposalDecisionAttempt && (!workspaceId || !proposalId)) return;
  const attempt = proposalDecisionAttempt || {
    proposalId,
    workspaceId,
    revision: workspaceRevision,
    decision,
  };
  proposalDecisionAttempt = attempt;
  syncAgentTurnControls();
  setWorkspaceState(workspaceState);
  setProposalDecisionPending(true);
  try {
    const result = await api.decideProposal(attempt.workspaceId, attempt.proposalId, attempt.decision, attempt.revision);
    workspaceRevision = result.data.workspace_revision ?? result.revision ?? workspaceRevision;
    if (proposalId === attempt.proposalId) proposalId = null;
    proposalDiff = "";
    proposalDecisionAttempt = null;
    setProposalDecisionPending(false);
    setWorkspaceState(workspaceState);
    setApiState("本机合成 API 已确认提案决定；下面显示的是本机合成记录。页面内存演示不会写回文件，也不会运行代码。");
    if (attempt.decision === "REJECTED") {
      proposalStatus.textContent = "拒绝决定已记录到本机合成 API；项目文件没有变化。";
      showToast("本机合成 API 已记录拒绝决定。");
    } else {
      diffCard.hidden = true;
      if (currentFile !== "main.py") loadFile("main.py");
      editor.focus();
      proposalStatus.textContent = "接管决定已记录到本机合成 API；你可以继续在页面内存中编辑，不会运行代码。";
      showToast("已记录学生接管；不会运行代码。");
    }
  } catch (error) {
    const label = attempt.decision === "REJECTED" ? "拒绝修改建议" : "接管修改建议";
    const state = errorStateFor(error, label);
    const message = ["unavailable", "error", "unknown"].includes(state.kind)
      ? `${attempt.decision === "REJECTED" ? "拒绝建议" : "接管建议"}仍未确认。请留在当前页面，使用原按钮重试同一请求；刷新会丢失本页重试信息。`
      : state.message;
    setProposalDecisionPending(false, state.kind === "unavailable" ? action : null);
    proposalStatus.textContent = message;
    setApiState(message);
    if (!['unavailable', 'error', 'unknown'].includes(state.kind)) {
      proposalDecisionAttempt = null;
      syncAgentTurnControls();
      setWorkspaceState(workspaceState);
    }
  } finally {
    setProposalDecisionPending(false, proposalDecisionAttempt ? action : null);
    syncAgentTurnControls();
  }
}

document.querySelector("[data-action='reject']").addEventListener("click", () => decideProposal("REJECTED", "reject"));
document.querySelector("[data-action='takeover']").addEventListener("click", () => decideProposal("STUDENT_TAKEOVER", "takeover"));

submissionForm.addEventListener("submit", async (event) => {
  if (event.submitter?.id !== "confirm-submit") return;
  event.preventDefault();
  if (submissionInFlight) return;
  if (!submissionNote.value.trim()) {
    event.preventDefault();
    submissionNote.setCustomValidity("请写明至少一项验证或仍不确定之处。");
    submissionNote.reportValidity();
    return;
  }
  submissionNote.setCustomValidity("");
  if (proposalAcceptAttempt !== null) {
    setApiState("当前建议的接受结果尚未确认；先完成同一接受操作，再提交成果。");
    return;
  }
  if (!workspaceId || workspaceRevision === null) {
    setApiState("没有本机合成工作区；提交未发送，也未报告成功。");
    return;
  }
  const retryingUnknownSubmission = pendingSubmission !== null;
  const attempt = pendingSubmission || {
    workspaceId,
    revision: workspaceRevision,
    dto: mapFilesToSubmissionDto(workingContent, submissionNote.value),
  };
  pendingSubmission = attempt;
  submissionInFlight = true;
  const confirmButton = document.querySelector("#confirm-submit");
  confirmButton.dataset.idleText ||= confirmButton.textContent;
  confirmButton.disabled = true;
  confirmButton.textContent = retryingUnknownSubmission ? "正在重试…" : "正在提交…";
  setSubmissionContentFrozen(true);
  try {
    const result = await api.submit(attempt.workspaceId, attempt.dto, attempt.revision);
    pendingSubmission = null;
    workspaceRevision = result.data.workspace_revision ?? result.revision ?? workspaceRevision;
    setWorkspaceState(result.data.submission.version === 1 ? "REVIEW_REQUIRED" : "RESUBMITTED");
    submitDialog.close();
    document.querySelector("#edit-status").textContent = "已由本机合成 API 接收 · 服务重启后清空";
    setApiState("提交已由本机合成 API 接收；allowlist 文本快照、字节数和 SHA-256 仅暂存在当前服务进程内存，非生产。");
    await loadLatestSubmission(attempt.workspaceId);
    showToast("本机合成 API 已接收提交。");
  } catch (error) {
    let state = errorStateFor(error, "提交成果");
    if (attempt.workspaceId) {
      try {
        const latest = (await api.getWorkspace(attempt.workspaceId)).data;
        workspaceRevision = latest.revision;
        setWorkspaceState(latest.state);
        if (error?.definitiveRejection !== true && ["REVIEW_REQUIRED", "RESUBMITTED"].includes(latest.state)) {
          state = { kind: "unknown", message: `工作区当前状态为 ${latest.state}；提交请求的回执未确认，请让教师核对队列后再操作。` };
        }
      } catch { /* Keep the original request error when readback is also unavailable. */ }
    }
    if (state.kind === "unavailable" || state.kind === "error" || state.kind === "unknown") {
      state = {
        kind: "unknown",
        message: "提交结果暂未确认；页面已冻结本次提交内容。可重试同一提交以读取原回执，请勿修改后当作新提交。",
      };
    } else {
      pendingSubmission = null;
      setSubmissionContentFrozen(false);
      setWorkspaceState(workspaceState);
    }
    setApiState(state.message);
    if (state.kind === "unknown") await loadLatestSubmission(attempt.workspaceId);
    showToast(state.message);
  } finally {
    submissionInFlight = false;
    confirmButton.disabled = false;
    if (pendingSubmission === null) {
      confirmButton.textContent = confirmButton.dataset.idleText;
      setSubmissionContentFrozen(false);
    } else {
      confirmButton.textContent = "重试同一提交";
    }
  }
});

submissionNote.addEventListener("input", () => submissionNote.setCustomValidity(""));

loadFile("main.py");
loadStudentWorkspace();
