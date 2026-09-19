const EDITING_TASK_STATUS_OPTIONS = [
  { value: "assigned", label: "待接单" },
  { value: "in_progress", label: "制作中" },
  { value: "review", label: "待审核" },
  { value: "revision", label: "需修改" },
  { value: "done", label: "已完成" },
  { value: "paused", label: "已暂停" },
];

const PRIORITY_OPTIONS = [
  { value: "high", label: "高优先" },
  { value: "normal", label: "普通" },
  { value: "low", label: "低优先" },
];

const ORDER_TEMPLATES = {
  ja15: {
    title: "15 秒日本带货视频",
    priority: "high",
    brief: "成片 15 秒，竖屏 9:16。节奏要快，开头 2 秒必须有钩子；中段突出上身效果、细节设计和显瘦显腿长；结尾给购买理由。优先调用素材库高分片段生成可编辑剪映草稿。",
    script: "こちらが当店で人気のアイテムです。\nシルエットがきれいで、脚長効果もばっちり。\n今の季節に合わせやすく、毎日のコーデに使いやすいです。",
  },
  ja30: {
    title: "30 秒产品混剪",
    priority: "normal",
    brief: "成片 30 秒，适合日本电商投放。结构：开头钩子、上身展示、细节特写、动作展示、卖点证明、结尾召回。画面和文案必须一一对应。",
    script: "今日はおすすめの新作をご紹介します。\nまず見てほしいのは、このきれいなシルエット。\n細部のデザインも可愛くて、普段使いしやすいです。\nトップスとも合わせやすく、スタイルアップして見えます。",
  },
  detail: {
    title: "细节展示视频",
    priority: "normal",
    brief: "突出面料、纽扣、口袋、腰头、版型等细节。需要多用特写镜头，剪辑不要太跳，适合产品页展示。",
    script: "細部までこだわったデザインです。\n生地感もきれいで、毎日使いやすい一枚。\nシンプルだけど、しっかりおしゃれに見えます。",
  },
  tryon: {
    title: "上身试穿视频",
    priority: "high",
    brief: "重点展示模特上身效果、走动效果、正侧背多角度。优先选择清晰、稳定、完整的上身素材。",
    script: "実際に着てみると、ラインがとてもきれいです。\n動きやすくて、普段のお出かけにもぴったり。\n自然にスタイルアップして見えるのがポイントです。",
  },
  draft: {
    title: "剪映草稿交付",
    priority: "normal",
    brief: "先生成可编辑剪映草稿，字幕、配音、素材片段都需要可后期修改。请保留素材轨道和配音轨道，方便二次调整。",
    script: "こちらの商品を、短い広告動画として分かりやすく紹介します。\n画面に合わせて、自然な日本語ナレーションを入れてください。",
  },
};

const REQUIRED_EDIT_ROLES = ["hook", "try_on", "detail", "motion", "proof", "ending"];
const ROLE_LABELS = {
  hook: "开头钩子",
  try_on: "上身展示",
  detail: "细节特写",
  motion: "动作镜头",
  transition: "转场氛围",
  proof: "卖点证明",
  ending: "结尾召回",
  unassigned: "待判断",
};

const $ = (selector) => document.querySelector(selector);

const elements = {
  totalState: $("#editing-task-total-state"),
  roleState: $("#editing-task-role-state"),
  refreshBtn: $("#editing-task-refresh-btn"),
  boardRefreshBtn: $("#editing-task-board-refresh-btn"),
  summary: $("#editing-task-summary"),
  createForm: $("#editing-task-create-form"),
  formKicker: $("#editing-task-form-kicker"),
  formTitle: $("#editing-task-form-title"),
  assigneeField: $("#editing-task-assignee-field"),
  assigneeSelect: $("#editing-task-assignee-select"),
  templateSelect: $("#editing-task-template-select"),
  titleInput: $("#editing-task-title-input"),
  productInput: $("#editing-task-product-input"),
  prioritySelect: $("#editing-task-priority-select"),
  dueInput: $("#editing-task-due-input"),
  scopeSelect: $("#editing-task-scope-select"),
  briefInput: $("#editing-task-brief-input"),
  scriptInput: $("#editing-task-script-input"),
  readiness: $("#editing-task-readiness"),
  createBtn: $("#editing-task-create-btn"),
  metrics: $("#editing-task-metrics"),
  list: $("#editing-task-list"),
  status: $("#editing-task-status"),
  toast: $("#editing-task-toast"),
};

const state = {
  auth: null,
  tasks: [],
  users: [],
  statusLabels: {},
  library: null,
  obsidian: null,
  loading: false,
  draftRunningTaskId: "",
  toastTimer: null,
};

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `请求失败：${response.status}`);
  }
  return payload;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function optionLabel(options, value) {
  return options.find((option) => option.value === value)?.label || value;
}

function optionsMarkup(options, selected) {
  return options.map((option) => `<option value="${escapeHtml(option.value)}"${option.value === String(selected) ? " selected" : ""}>${escapeHtml(option.label)}</option>`).join("");
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function taskDateLabel(value) {
  if (!value) return "";
  return /^\d{4}-\d{2}-\d{2}$/.test(String(value)) ? String(value) : (formatDate(value) || String(value));
}

function roleLabel(role) {
  return role === "admin" ? "管理员" : "客户";
}

function isAdmin() {
  return Boolean(state.auth?.canManageUsers || state.auth?.role === "admin");
}

function setStatus(message, tone = "") {
  if (!elements.status) return;
  elements.status.textContent = message || "";
  elements.status.dataset.tone = tone;
}

function showToast(message) {
  if (!elements.toast) return;
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 2600);
}

function updateTaskState(payload = {}) {
  state.auth = payload.auth || state.auth;
  state.tasks = Array.isArray(payload.tasks) ? payload.tasks : state.tasks;
  state.users = Array.isArray(payload.users) ? payload.users : state.users;
  state.statusLabels = payload.statusLabels || state.statusLabels || {};
  state.obsidian = payload.obsidian || state.obsidian;
}

function materialBatches() {
  return Array.isArray(state.library?.batches) ? state.library.batches : [];
}

function materialEntries() {
  const items = state.library?.items && typeof state.library.items === "object" ? state.library.items : {};
  return Object.entries(items)
    .map(([url, item]) => ({
      url,
      ...(item || {}),
      batchId: String(item?.batchId || ""),
      editRole: String(item?.editRole || "unassigned"),
      analysisStatus: String(item?.analysisStatus || item?.status || "queued"),
      priority: String(item?.priority || "normal"),
      qualityScore: Number(item?.qualityScore || 0) || 0,
      technical: item?.technical && typeof item.technical === "object" ? item.technical : {},
      analysis: item?.analysis && typeof item.analysis === "object" ? item.analysis : {},
    }))
    .filter((item) => String(item.kind || "video") === "video");
}

function scopeItems(scopeValue) {
  if (!scopeValue || scopeValue === "all") return materialEntries();
  return materialEntries().filter((item) => item.batchId === scopeValue);
}

function taskScopeItems(task) {
  if (task?.batchId) return scopeItems(task.batchId);
  return materialEntries();
}

async function loadMaterialLibrary() {
  try {
    const payload = await requestJson("/api/material-library");
    state.library = payload.library || null;
  } catch {
    state.library = null;
  }
}

async function loadTasks(options = {}) {
  if (state.loading) return;
  state.loading = true;
  if (!options.silent) setStatus("正在从 Obsidian 读取剪辑任务...");
  try {
    const [taskPayload] = await Promise.all([
      requestJson("/api/editing-tasks"),
      loadMaterialLibrary(),
    ]);
    updateTaskState(taskPayload);
    render();
    setStatus(taskPayload.obsidian?.root ? `任务数据已同步到 Obsidian：${taskPayload.obsidian.root}` : "任务数据已刷新", "success");
  } catch (error) {
    setStatus(`读取剪辑任务失败：${error.message}`, "error");
    render();
  } finally {
    state.loading = false;
  }
}

function statusLabel(status) {
  return state.statusLabels?.[status] || optionLabel(EDITING_TASK_STATUS_OPTIONS, status || "assigned");
}

function priorityLabel(priority) {
  return optionLabel(PRIORITY_OPTIONS, priority || "normal");
}

function scopeOptions() {
  return [
    { value: "all", label: "全部素材库" },
    ...materialBatches().map((batch) => ({ value: batch.id, label: `批次：${batch.name}` })),
  ];
}

function clipRole(item, segment = null) {
  return String(segment?.role || item?.editRole || "unassigned");
}

function roleCounts(items) {
  const counts = {};
  items.forEach((item) => {
    const segments = Array.isArray(item.analysis?.segments) ? item.analysis.segments : [];
    if (segments.length) {
      segments.forEach((segment) => {
        const role = clipRole(item, segment);
        counts[role] = (counts[role] || 0) + 1;
      });
    } else {
      const role = clipRole(item);
      counts[role] = (counts[role] || 0) + 1;
    }
  });
  return counts;
}

function readinessForItems(items) {
  const analyzed = items.filter((item) => ["analyzed", "ready"].includes(item.analysisStatus));
  const ready = items.filter((item) => item.analysisStatus === "ready");
  const counts = roleCounts(analyzed);
  const missing = REQUIRED_EDIT_ROLES.filter((role) => !counts[role]);
  const segmentCount = analyzed.reduce((sum, item) => sum + (Array.isArray(item.analysis?.segments) ? item.analysis.segments.length : 0), 0);
  let score = 0;
  if (items.length) score += 20;
  score += Math.min(25, analyzed.length * 5);
  score += Math.min(20, ready.length * 5);
  score += Math.min(25, (REQUIRED_EDIT_ROLES.length - missing.length) * 5);
  score += Math.min(10, segmentCount);
  return {
    score: Math.max(0, Math.min(100, score)),
    total: items.length,
    analyzed: analyzed.length,
    ready: ready.length,
    segmentCount,
    counts,
    missing,
  };
}

function readinessTone(readiness) {
  if (readiness.score >= 80) return "good";
  if (readiness.score >= 55) return "warn";
  return "bad";
}

function readinessMarkup(readiness, compact = false) {
  const tone = readinessTone(readiness);
  const missingText = readiness.missing.length
    ? `缺少：${readiness.missing.map((role) => ROLE_LABELS[role] || role).join("、")}`
    : "关键镜头齐全";
  const roleLine = REQUIRED_EDIT_ROLES.map((role) => {
    const count = readiness.counts[role] || 0;
    return `<span class="${count ? "ok" : "missing"}">${escapeHtml(ROLE_LABELS[role] || role)} ${escapeHtml(count)}</span>`;
  }).join("");
  return `
    <div class="editing-order-readiness-card ${escapeHtml(tone)}">
      <div>
        <strong>${escapeHtml(readiness.score)}%</strong>
        <small>${escapeHtml(readiness.total)} 个视频 · 已分析 ${escapeHtml(readiness.analyzed)} · 可剪辑 ${escapeHtml(readiness.ready)} · 智能片段 ${escapeHtml(readiness.segmentCount)}</small>
      </div>
      <em>${escapeHtml(missingText)}</em>
      ${compact ? "" : `<div class="editing-order-role-grid">${roleLine}</div>`}
    </div>
  `;
}

function renderFormReadiness() {
  if (!elements.readiness) return;
  const value = elements.scopeSelect?.value || "all";
  const readiness = readinessForItems(scopeItems(value));
  elements.readiness.innerHTML = readinessMarkup(readiness);
}

function renderAssignees() {
  const users = state.users || [];
  const previous = elements.assigneeSelect?.value || "";
  if (!elements.assigneeSelect) return;
  elements.assigneeSelect.innerHTML = users.length
    ? users.map((user) => `<option value="${escapeHtml(user.username)}">${escapeHtml(user.username)}</option>`).join("")
    : `<option value="">先在账号管理里添加客户</option>`;
  elements.assigneeSelect.value = users.some((user) => user.username === previous) ? previous : (users[0]?.username || "");
}

function renderScopeSelect() {
  if (!elements.scopeSelect) return;
  const previous = elements.scopeSelect.value || "all";
  const options = scopeOptions();
  elements.scopeSelect.innerHTML = optionsMarkup(options, options.some((item) => item.value === previous) ? previous : "all");
  renderFormReadiness();
}

function taskMetrics(tasks) {
  const counts = Object.fromEntries(EDITING_TASK_STATUS_OPTIONS.map((option) => [option.value, 0]));
  tasks.forEach((task) => {
    const status = task.status || "assigned";
    counts[status] = (counts[status] || 0) + 1;
  });
  return counts;
}

function renderMetrics(tasks) {
  if (!elements.metrics) return;
  const counts = taskMetrics(tasks);
  elements.metrics.innerHTML = EDITING_TASK_STATUS_OPTIONS.map((option) => `
    <span class="status-${escapeHtml(option.value)}">
      <b>${escapeHtml(counts[option.value] || 0)}</b>
      <em>${escapeHtml(option.label)}</em>
    </span>
  `).join("");
}

function renderTaskList(tasks) {
  if (!elements.list) return;
  const admin = isAdmin();
  if (!tasks.length) {
    elements.list.innerHTML = `<div class="material-workbench-empty good"><strong>${admin ? "还没有剪辑任务" : "暂无分配给你的任务"}</strong><small>${admin ? "选择客户账号、批次和剪辑要求后即可下发。" : "管理员下发后会显示在这里。"}</small></div>`;
    return;
  }
  elements.list.innerHTML = tasks.map((task) => {
    const scope = task.batchName || (task.materialScope === "all" ? "全部素材库" : "未指定素材范围");
    const due = task.dueAt ? ` · 截止 ${taskDateLabel(task.dueAt)}` : "";
    const updated = task.updatedAt ? ` · 更新 ${formatDate(task.updatedAt)}` : "";
    const readiness = readinessForItems(taskScopeItems(task));
    const canGenerate = readiness.analyzed > 0 && readiness.total > 0;
    const isDraftRunning = state.draftRunningTaskId === task.id;
    return `
      <article class="material-task-card status-${escapeHtml(task.status || "assigned")}" data-task-id="${escapeHtml(task.id)}">
        <div class="material-task-card-head">
          <div>
            <strong>${escapeHtml(task.title || "未命名剪辑任务")}</strong>
            <small>${escapeHtml(task.productName || "未填写产品名")} · ${escapeHtml(scope)}${escapeHtml(due)}${escapeHtml(updated)}</small>
          </div>
          <div class="material-task-chip-row">
            <span class="material-task-status-chip status-${escapeHtml(task.status || "assigned")}">${escapeHtml(statusLabel(task.status))}</span>
            <span>${escapeHtml(priorityLabel(task.priority))}</span>
            ${admin ? `<span>@${escapeHtml(task.assignee || "")}</span>` : ""}
          </div>
        </div>
        ${task.brief ? `<div class="material-task-copy"><b>剪辑要求</b><p>${escapeHtml(task.brief)}</p></div>` : ""}
        ${task.script ? `<div class="material-task-copy"><b>脚本文案</b><p>${escapeHtml(task.script)}</p></div>` : ""}
        <div class="editing-task-card-readiness">${readinessMarkup(readiness, true)}</div>
        <div class="material-task-update-grid">
          <label>
            <span>状态</span>
            <select data-task-field="status">${optionsMarkup(EDITING_TASK_STATUS_OPTIONS, task.status || "assigned")}</select>
          </label>
          <label>
            <span>成片链接</span>
            <input data-task-field="resultUrl" type="url" maxlength="1000" placeholder="剪映导出链接/云盘地址" value="${escapeHtml(task.resultUrl || "")}">
          </label>
          <label class="wide">
            <span>交付备注</span>
            <textarea data-task-field="deliveryNote" rows="2" maxlength="3000" placeholder="客户提交说明，或管理员复核意见">${escapeHtml(task.deliveryNote || "")}</textarea>
          </label>
          <button class="mini-action primary" type="button" data-action="save-task">保存进度</button>
        </div>
        <div class="editing-task-card-actions">
          <button class="mini-action primary" type="button" data-action="generate-draft" ${canGenerate && !isDraftRunning ? "" : "disabled"}>
            ${isDraftRunning ? "生成中..." : "按此订单生成剪映草稿"}
          </button>
          <small>${canGenerate ? "会优先使用该订单素材范围里的高分智能片段。" : "请先导入并分析该订单对应素材。"}</small>
        </div>
      </article>
    `;
  }).join("");
  bindTaskCards();
}

function render() {
  const tasks = Array.isArray(state.tasks) ? state.tasks : [];
  const admin = isAdmin();
  if (elements.createForm) elements.createForm.hidden = false;
  if (elements.assigneeField) elements.assigneeField.hidden = !admin;
  if (elements.formKicker) elements.formKicker.textContent = admin ? "ASSIGN" : "ORDER";
  if (elements.formTitle) elements.formTitle.textContent = admin ? "下发剪辑任务" : "提交视频订单";
  if (elements.createBtn) elements.createBtn.textContent = admin ? "下发剪辑任务" : "提交视频订单";
  if (elements.totalState) elements.totalState.textContent = `${tasks.length} 个任务`;
  if (elements.roleState) elements.roleState.textContent = roleLabel(state.auth?.role);
  if (elements.summary) {
    elements.summary.textContent = admin
      ? `当前 ${tasks.length} 个剪辑任务 · 可派单客户 ${state.users.length} 个 · 数据写入 Obsidian`
      : `我的视频订单 ${tasks.length} 个 · 可自助提交需求，也可以接收管理员派单`;
  }
  renderAssignees();
  renderScopeSelect();
  if (elements.createBtn) elements.createBtn.disabled = admin && !state.users.length;
  renderMetrics(tasks);
  renderTaskList(tasks);
}

function selectedScopePayload() {
  const value = elements.scopeSelect?.value || "all";
  if (value === "all") {
    return { materialScope: "all", batchId: "", batchName: "" };
  }
  const batch = materialBatches().find((item) => item.id === value);
  return {
    materialScope: "batch",
    batchId: batch?.id || "",
    batchName: batch?.name || "",
  };
}

function applyOrderTemplate() {
  const key = elements.templateSelect?.value || "custom";
  const template = ORDER_TEMPLATES[key];
  if (!template) return;
  if (elements.titleInput && !elements.titleInput.value.trim()) elements.titleInput.value = template.title;
  if (elements.prioritySelect) elements.prioritySelect.value = template.priority || "normal";
  if (elements.briefInput) {
    elements.briefInput.value = elements.briefInput.value.trim()
      ? `${elements.briefInput.value.trim()}\n${template.brief}`
      : template.brief;
  }
  if (elements.scriptInput && !elements.scriptInput.value.trim()) elements.scriptInput.value = template.script;
  showToast("下单模板已填入");
}

async function createTask(event) {
  event.preventDefault();
  const admin = isAdmin();
  const assignee = admin ? (elements.assigneeSelect?.value || "") : (state.auth?.username || "");
  if (!assignee) {
    setStatus(admin ? "请先在账号管理里添加客户账号。" : "请先登录客户账号。", "error");
    showToast(admin ? "请先添加客户账号" : "请先登录");
    return;
  }
  const payload = {
    assignee,
    title: elements.titleInput?.value || "",
    productName: elements.productInput?.value || "",
    priority: elements.prioritySelect?.value || "normal",
    dueAt: elements.dueInput?.value || "",
    ...selectedScopePayload(),
    brief: elements.briefInput?.value || "",
    script: elements.scriptInput?.value || "",
  };
  if (elements.createBtn) elements.createBtn.disabled = true;
  setStatus(admin ? "正在下发剪辑任务，并写入 Obsidian..." : "正在提交视频订单，并写入 Obsidian...");
  try {
    const response = await requestJson("/api/editing-tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    updateTaskState(response);
    elements.createForm?.reset();
    if (elements.prioritySelect) elements.prioritySelect.value = "normal";
    if (elements.templateSelect) elements.templateSelect.value = "custom";
    render();
    setStatus(admin ? "剪辑任务已下发，客户登录后即可看到。" : "视频订单已提交，管理员可以直接看到。", "success");
    showToast(admin ? "剪辑任务已下发" : "视频订单已提交");
  } catch (error) {
    setStatus(`${admin ? "下发" : "提交"}失败：${error.message}`, "error");
    showToast(error.message);
  } finally {
    if (elements.createBtn) elements.createBtn.disabled = isAdmin() && !state.users.length;
  }
}

async function updateTask(taskId, patch) {
  setStatus("正在保存任务进度...");
  try {
    const response = await requestJson("/api/editing-tasks/update", {
      method: "POST",
      body: JSON.stringify({ id: taskId, ...patch }),
    });
    updateTaskState(response);
    render();
    setStatus("任务进度已保存，并同步到 Obsidian。", "success");
    showToast("任务进度已保存");
  } catch (error) {
    setStatus(`保存失败：${error.message}`, "error");
    showToast(error.message);
  }
}

function clipDurationMs(item, segment = null) {
  if (segment) return Math.max(0, Number(segment.endMs || 0) - Number(segment.startMs || 0));
  const duration = Number(item.technical?.durationMs || item.technical?.duration || 0) || 0;
  return duration || 6000;
}

function clipScore(item, segment = null) {
  const priorityBonus = item.priority === "high" ? 12 : item.priority === "low" ? -6 : 4;
  const statusBonus = item.analysisStatus === "ready" ? 12 : item.analysisStatus === "analyzed" ? 8 : 0;
  const qualityBonus = (Number(item.qualityScore || 0) || 0) * 8;
  const segmentScore = Number(segment?.score || 0) || 0;
  return segmentScore + priorityBonus + statusBonus + qualityBonus;
}

function selectedClipsForTask(task) {
  const rolePlan = ["hook", "try_on", "detail", "motion", "proof", "detail", "transition", "ending"];
  const scoped = taskScopeItems(task).filter((item) => ["ready", "analyzed"].includes(item.analysisStatus));
  const candidates = [];
  scoped.forEach((item) => {
    const segments = Array.isArray(item.analysis?.segments) ? item.analysis.segments : [];
    if (segments.length) {
      segments.forEach((segment) => {
        const duration = clipDurationMs(item, segment);
        if (duration < 1200) return;
        candidates.push({
          url: item.url,
          segmentId: String(segment.id || ""),
          startMs: Number(segment.startMs || 0) || 0,
          endMs: Number(segment.endMs || 0) || 0,
          role: clipRole(item, segment),
          segmentScore: Number(segment.score || 0) || 0,
          note: segment.reason || task.title || "",
          sortScore: clipScore(item, segment),
        });
      });
      return;
    }
    const total = clipDurationMs(item);
    if (total < 1200) return;
    candidates.push({
      url: item.url,
      startMs: 0,
      endMs: Math.min(total, 6000),
      role: clipRole(item),
      segmentScore: 0,
      note: task.title || "",
      sortScore: clipScore(item),
    });
  });
  const selected = [];
  rolePlan.forEach((role) => {
    const match = candidates
      .filter((clip) => clip.role === role && !selected.some((item) => item.url === clip.url && item.startMs === clip.startMs))
      .sort((a, b) => b.sortScore - a.sortScore)[0];
    if (match) selected.push(match);
  });
  candidates
    .sort((a, b) => b.sortScore - a.sortScore)
    .forEach((clip) => {
      if (selected.length >= 12) return;
      if (!selected.some((item) => item.url === clip.url && item.startMs === clip.startMs)) selected.push(clip);
    });
  return selected.slice(0, 12).map(({ sortScore, ...clip }) => clip);
}

function draftStatusNote(result) {
  const record = result?.record || {};
  const duration = record.totalDurationMs ? `${Math.round(record.totalDurationMs / 1000)}s` : "";
  return [
    record.draftName ? `草稿：${record.draftName}` : "已生成剪映草稿",
    record.clipCount ? `${record.clipCount} 个片段` : "",
    duration,
    record.obsidianReportPath || "",
  ].filter(Boolean).join(" · ");
}

async function generateDraftForTask(taskId) {
  const task = state.tasks.find((item) => item.id === taskId);
  if (!task) return;
  const selectedClips = selectedClipsForTask(task);
  if (!selectedClips.length) {
    showToast("该订单还没有可生成草稿的已分析素材");
    return;
  }
  state.draftRunningTaskId = taskId;
  render();
  setStatus("正在按订单生成可编辑剪映草稿...");
  try {
    const payload = await requestJson("/api/material-library/jianying-draft", {
      method: "POST",
      body: JSON.stringify({
        maxClips: Math.min(12, selectedClips.length),
        maxDuration: 60,
        targetRatio: "auto",
        selectedClips,
        voiceoverText: task.script || task.brief || "",
        copyLanguage: "ja",
        voiceProvider: "edge",
        speaker: "ja-JP-NanamiNeural",
        generateVoiceover: true,
        draftName: `${task.productName || task.title || "视频订单"}-${task.id}`,
      }),
    });
    const note = draftStatusNote(payload.result);
    await updateTask(taskId, {
      status: "review",
      deliveryNote: [task.deliveryNote || "", note].filter(Boolean).join("\n"),
    });
    setStatus(`剪映草稿已生成：${note}`, "success");
    showToast("剪映草稿已生成");
  } catch (error) {
    setStatus(`生成剪映草稿失败：${error.message}`, "error");
    showToast(error.message);
  } finally {
    state.draftRunningTaskId = "";
    render();
  }
}

function bindTaskCards() {
  elements.list?.querySelectorAll(".material-task-card").forEach((card) => {
    const button = card.querySelector("[data-action='save-task']");
    button?.addEventListener("click", async () => {
      const taskId = card.dataset.taskId || "";
      const patch = {
        status: card.querySelector("[data-task-field='status']")?.value || "assigned",
        resultUrl: card.querySelector("[data-task-field='resultUrl']")?.value || "",
        deliveryNote: card.querySelector("[data-task-field='deliveryNote']")?.value || "",
      };
      button.disabled = true;
      await updateTask(taskId, patch);
      button.disabled = false;
    });
    card.querySelector("[data-action='generate-draft']")?.addEventListener("click", async (event) => {
      event.currentTarget.disabled = true;
      await generateDraftForTask(card.dataset.taskId || "");
    });
  });
}

function bindEvents() {
  elements.refreshBtn?.addEventListener("click", () => loadTasks().then(() => showToast("剪辑任务已刷新")));
  elements.boardRefreshBtn?.addEventListener("click", () => loadTasks().then(() => showToast("剪辑任务已刷新")));
  elements.templateSelect?.addEventListener("change", applyOrderTemplate);
  elements.scopeSelect?.addEventListener("change", renderFormReadiness);
  elements.createForm?.addEventListener("submit", createTask);
}

bindEvents();
render();
loadTasks();
