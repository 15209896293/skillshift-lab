const teacherId = "teacher-demo";
const studentId = "student-demo";
let assignmentId = null;

const result = document.querySelector("#result");
const teacherStatus = document.querySelector("#teacher-status");
const studentStatus = document.querySelector("#student-status");

function show(value) {
  result.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    "\"": "&quot;",
  })[character]);
}

async function request(path, method = "GET", payload = null) {
  const response = await fetch(path, {
    method,
    headers: payload ? { "Content-Type": "application/json" } : {},
    body: payload ? JSON.stringify(payload) : null,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error?.message || "本机演示请求未完成。");
  }
  return data;
}

function renderAssignment(assignment) {
  assignmentId = assignment.assignment_id;
  const task = assignment.task;
  const feedback = assignment.teacher_feedback
    ? `<p><strong>教师反馈：</strong>${escapeHtml(assignment.teacher_feedback.kind)} — ${escapeHtml(assignment.teacher_feedback.reason)}</p>`
    : "<p>尚无教师反馈。</p>";
  const response = assignment.student_response
    ? `<p><strong>学生最新提交：</strong>${escapeHtml(assignment.student_response.text)}</p>`
    : "<p>学生尚未提交。</p>";
  const summary = `<p><strong>${escapeHtml(task.title)}</strong></p><p>${escapeHtml(task.goal)}</p><p><strong>学生责任：</strong>${escapeHtml(task.student_responsibility)}</p><p><strong>提交要求：</strong>${escapeHtml(task.submission_requirement)}</p><p>状态：<code>${escapeHtml(assignment.status)}</code></p>${response}${feedback}`;
  teacherStatus.innerHTML = summary;
  studentStatus.innerHTML = `${summary}<p class="small">${assignment.demo_notice}</p>`;
}

function requireAssignment() {
  if (!assignmentId) {
    throw new Error("请先由教师创建任务。");
  }
}

async function restoreLatestAssignment() {
  try {
    const data = await request("/api/assignments");
    const assignments = data.assignments || [];
    if (assignments.length > 0) {
      renderAssignment(assignments[assignments.length - 1]);
      show("已重新载入最近的本机合成任务。");
    }
  } catch (error) {
    show(error.message);
  }
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab, .panel").forEach((node) => node.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.panel}`).classList.add("active");
  });
});

document.querySelector("#create-assignment").addEventListener("click", async () => {
  try {
    const assignment = await request("/api/assignments", "POST", {
      actor_id: teacherId,
      title: document.querySelector("#task-title").value,
      goal: document.querySelector("#task-goal").value,
      student_responsibility: document.querySelector("#task-responsibility").value,
      submission_requirement: document.querySelector("#task-submission").value,
    });
    renderAssignment(assignment);
    show({ message: "合成任务已创建并发布。", assignment_id: assignment.assignment_id });
  } catch (error) {
    show(error.message);
  }
});

document.querySelector("#start-work").addEventListener("click", async () => {
  try {
    requireAssignment();
    const assignment = await request(`/api/assignments/${assignmentId}/start`, "POST", { actor_id: studentId });
    renderAssignment(assignment);
    show("学生已开始任务。现在可以提问或提交任务关联响应。");
  } catch (error) {
    show(error.message);
  }
});

document.querySelector("#ask-guidance").addEventListener("click", async () => {
  try {
    requireAssignment();
    const question = document.querySelector("#question").value;
    const guidance = await request(`/api/assignments/${assignmentId}/guidance`, "POST", { actor_id: studentId, question });
    document.querySelector("#guidance-result").textContent = guidance.text;
    show({ adapter: guidance.adapter_version, availability: guidance.availability });
  } catch (error) {
    show(error.message);
  }
});

document.querySelector("#submit-response").addEventListener("click", async () => {
  try {
    requireAssignment();
    const submission = await request(`/api/assignments/${assignmentId}/submissions`, "POST", {
      actor_id: studentId,
      responsibility_kind: document.querySelector("#responsibility-kind").value,
      response_text: document.querySelector("#response-text").value,
    });
    renderAssignment(submission.assignment);
    show({ message: "学生任务响应已提交。", revision: submission.response.revision });
  } catch (error) {
    show(error.message);
  }
});

document.querySelector("#send-review").addEventListener("click", async () => {
  try {
    requireAssignment();
    const review = await request(`/api/assignments/${assignmentId}/reviews`, "POST", {
      actor_id: teacherId,
      kind: document.querySelector("#review-kind").value,
      reason: document.querySelector("#review-reason").value,
    });
    renderAssignment(review.assignment);
    show({ message: "教师反馈已记录。", kind: review.review.kind });
  } catch (error) {
    show(error.message);
  }
});

document.querySelector("#view-manifest").addEventListener("click", async () => {
  try {
    requireAssignment();
    show(await request(`/api/assignments/${assignmentId}/manifest`));
  } catch (error) {
    show(error.message);
  }
});

restoreLatestAssignment();
