const $ = (selector) => document.querySelector(selector);

const elements = {
  activeState: $("#operations-active-state"),
  alertState: $("#operations-alert-state"),
  navRefreshBtn: $("#operations-nav-refresh-btn"),
  refreshBtn: $("#operations-refresh-btn"),
  updatedAt: $("#operations-updated-at"),
  activeCount: $("#operations-active-count"),
  attentionCount: $("#operations-attention-count"),
  completedCount: $("#operations-completed-count"),
  readyCount: $("#operations-ready-count"),
  draftCount: $("#operations-draft-count"),
  jobSummary: $("#operations-job-summary"),
  searchInput: $("#operations-search-input"),
  categoryFilter: $("#operations-category-filter"),
  statusFilter: $("#operations-status-filter"),
  jobList: $("#operations-job-list"),
  executorChip: $("#operations-executor-chip"),
  executorLabel: $("#operations-executor-label"),
  executorDetail: $("#operations-executor-detail"),
  alertCount: $("#operations-alert-count"),
  alertList: $("#operations-alert-list"),
  dataHealth: $("#operations-data-health"),
  coverageList: $("#operations-coverage-list"),
  toast: $("#operations-toast"),
};

const state = {
  operations: { metrics: {}, jobs: [], alerts: [], coverage: [], dataHealth: [], executor: {} },
  loading: false,
  toastTimer: null,
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 2400);
}

async function requestJson(url) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json" } });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) throw new Error(payload.error || `请求失败：${response.status}`);
  return payload;
}

function formatDate(value) {
  if (!value) return "未记录时间";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未记录时间";
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function relativeTime(value) {
  if (!value) return "暂无心跳";
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return "暂无心跳";
  const seconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
  if (seconds < 60) return `${seconds} 秒前`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

function statusGroup(status) {
  if (["queued", "running", "review"].includes(status)) return "active";
  if (["warning", "blocked", "failed"].includes(status)) return "attention";
  return status === "done" ? "done" : "active";
}

function renderMetrics() {
  const metrics = state.operations.metrics || {};
  elements.activeCount.textContent = String(Number(metrics.active || 0));
  elements.attentionCount.textContent = String(Number(metrics.attention || 0));
  elements.completedCount.textContent = String(Number(metrics.completed || 0));
  elements.readyCount.textContent = String(Number(metrics.materialsReady || 0));
  elements.draftCount.textContent = String(Number(metrics.drafts || 0));
  elements.activeState.textContent = String(Number(metrics.active || 0));
  elements.alertState.textContent = String((state.operations.alerts || []).length);
}

function filteredJobs() {
  const search = String(elements.searchInput.value || "").trim().toLowerCase();
  const category = String(elements.categoryFilter.value || "all");
  const status = String(elements.statusFilter.value || "all");
  return (state.operations.jobs || []).filter((job) => {
    if (category !== "all" && job.category !== category) return false;
    if (status !== "all" && statusGroup(job.status) !== status) return false;
    if (!search) return true;
    return [job.title, job.detail, job.id, job.categoryLabel].some((value) => String(value || "").toLowerCase().includes(search));
  });
}

function renderJobs() {
  const jobs = filteredJobs();
  const total = (state.operations.jobs || []).length;
  elements.jobSummary.textContent = `${jobs.length} 条当前结果 · ${total} 条汇总记录`;
  if (!jobs.length) {
    elements.jobList.innerHTML = `
      <div class="operations-empty">
        <strong>没有符合条件的任务</strong>
        <small>调整类型、状态或搜索关键词。</small>
      </div>`;
    return;
  }
  elements.jobList.innerHTML = jobs.map((job) => `
    <a class="operations-job-row" data-status="${escapeHtml(job.status)}" href="${escapeHtml(job.href || "#")}">
      <span class="operations-job-type" data-category="${escapeHtml(job.category)}">${escapeHtml(job.categoryLabel)}</span>
      <div>
        <strong>${escapeHtml(job.title)}</strong>
        <small>${escapeHtml(job.detail || job.id || "暂无任务明细")}</small>
      </div>
      <time>${escapeHtml(formatDate(job.updatedAt))}</time>
      <em>${escapeHtml(job.statusLabel)}</em>
    </a>
  `).join("");
}

function renderExecutor() {
  const executor = state.operations.executor || {};
  const tone = executor.health || "idle";
  elements.executorChip.dataset.tone = tone;
  elements.executorChip.textContent = executor.label || "状态未知";
  elements.executorLabel.textContent = executor.health === "offline"
    ? `${Number(executor.activeRequestCount || 0)} 个任务等待执行`
    : executor.state === "syncing"
      ? `正在处理 ${executor.requestId || "同步任务"}`
      : executor.label || "当前无活动任务";
  const heartbeat = executor.lastSeenAt ? `最后心跳 ${relativeTime(executor.lastSeenAt)}` : "尚未收到执行器心跳";
  const host = executor.host ? ` · ${executor.host}` : "";
  elements.executorDetail.textContent = `${heartbeat}${host}`;
}

function renderAlerts() {
  const alerts = state.operations.alerts || [];
  elements.alertCount.textContent = String(alerts.length);
  if (!alerts.length) {
    elements.alertList.innerHTML = `
      <div class="operations-empty compact">
        <strong>当前没有告警</strong>
        <small>关键流程状态正常。</small>
      </div>`;
    return;
  }
  elements.alertList.innerHTML = alerts.map((alert) => `
    <a class="operations-alert-row" data-tone="${escapeHtml(alert.tone || "info")}" href="${escapeHtml(alert.href || "#")}">
      <i></i>
      <div>
        <strong>${escapeHtml(alert.title)}</strong>
        <small>${escapeHtml(alert.detail)}</small>
      </div>
    </a>
  `).join("");
}

function renderDataHealth() {
  const files = state.operations.dataHealth || [];
  elements.dataHealth.innerHTML = files.map((file) => `
    <div class="operations-data-row" data-status="${escapeHtml(file.status || "ok")}">
      <span></span>
      <div>
        <strong>${escapeHtml(file.label)}</strong>
        <small title="${escapeHtml(file.path)}">${escapeHtml(file.path)}</small>
      </div>
      <b>${Number(file.sizeMb || 0).toFixed(1)} MB</b>
    </div>
  `).join("");
}

function renderCoverage() {
  const batches = state.operations.coverage || [];
  if (!batches.length) {
    elements.coverageList.innerHTML = '<div class="operations-empty"><strong>暂无素材批次</strong></div>';
    return;
  }
  elements.coverageList.innerHTML = batches.map((batch) => {
    const roles = Array.isArray(batch.roles) ? batch.roles : [];
    return `
      <article class="operations-coverage-row">
        <div class="operations-coverage-batch">
          <strong>${escapeHtml(batch.batchName)}</strong>
          <small>可剪辑 ${Number(batch.ready || 0)}/${Number(batch.total || 0)}${batch.queued ? ` · 待分析 ${Number(batch.queued)}` : ""}</small>
        </div>
        ${roles.map((role) => `
          <span class="operations-role-cell" data-status="${escapeHtml(role.status)}" title="${escapeHtml(role.label)} ${Number(role.count || 0)}">
            <b>${Number(role.count || 0)}</b><em>${escapeHtml(role.label)}</em>
          </span>
        `).join("")}
        <div class="operations-coverage-score" data-tone="${batch.coverageScore >= 80 ? "good" : batch.coverageScore >= 50 ? "warning" : "critical"}">
          <b>${Number(batch.coverageScore || 0)}%</b>
          <small>${batch.missingLabels?.length ? `缺 ${batch.missingLabels.length} 类` : "覆盖完整"}</small>
        </div>
      </article>
    `;
  }).join("");
}

function renderAll() {
  renderMetrics();
  renderJobs();
  renderExecutor();
  renderAlerts();
  renderDataHealth();
  renderCoverage();
}

async function loadOperations({ silent = false } = {}) {
  if (state.loading) return;
  state.loading = true;
  elements.refreshBtn.disabled = true;
  elements.navRefreshBtn.disabled = true;
  try {
    const payload = await requestJson("/api/operations-center");
    state.operations = payload.operations || state.operations;
    elements.updatedAt.textContent = `Obsidian 已同步 · ${formatDate(state.operations.updatedAt)}`;
    renderAll();
    if (!silent) showToast("运行中心已刷新");
  } catch (error) {
    elements.updatedAt.textContent = `数据读取失败：${error.message}`;
    if (!silent) showToast(error.message);
  } finally {
    state.loading = false;
    elements.refreshBtn.disabled = false;
    elements.navRefreshBtn.disabled = false;
  }
}

elements.refreshBtn.addEventListener("click", () => loadOperations());
elements.navRefreshBtn.addEventListener("click", () => loadOperations());
elements.searchInput.addEventListener("input", renderJobs);
elements.categoryFilter.addEventListener("change", renderJobs);
elements.statusFilter.addEventListener("change", renderJobs);

loadOperations({ silent: true });
window.setInterval(() => {
  if (!document.hidden) loadOperations({ silent: true });
}, 60000);
