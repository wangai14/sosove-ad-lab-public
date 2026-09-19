const CHATCUT_PROJECT_URL_KEY = "seedanceChatCutProjectUrl";
const CHATCUT_BATCH_KEY = "seedanceChatCutBatchId";
const CHATCUT_PRODUCT_KEYS_KEY = "seedanceChatCutProductKeys";
const CHATCUT_PROJECT_ID_PATTERN = /([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/i;
const CHATCUT_SYNC_CHUNK_SIZE = 30;

const CHATCUT_STATUS_META = {
  queued: { label: "待 Codex 执行", tone: "queued" },
  syncing: { label: "上传中", tone: "running" },
  partial: { label: "部分完成", tone: "partial" },
  complete: { label: "已完成", tone: "done" },
  failed: { label: "失败", tone: "failed" },
  blocked: { label: "需处理", tone: "blocked" },
};

const CHATCUT_ITEM_STATUS_META = {
  pending: { label: "待上传", tone: "queued" },
  syncing: { label: "上传中", tone: "running" },
  imported: { label: "已导入", tone: "done" },
  already_imported: { label: "项目已有", tone: "done" },
  failed: { label: "失败", tone: "failed" },
  unresolved: { label: "无法处理", tone: "blocked" },
  skipped: { label: "已跳过", tone: "idle" },
};

const $ = (selector) => document.querySelector(selector);

const elements = {
  projectUrlInput: $("#material-chatcut-project-url-input"),
  productKeyInput: $("#material-chatcut-product-key-input"),
  batchSelect: $("#material-chatcut-batch-select"),
  scopeSelect: $("#material-chatcut-sync-scope-select"),
  syncRefreshBtn: $("#material-chatcut-sync-refresh-btn"),
  syncSubmitBtn: $("#material-chatcut-sync-submit-btn"),
  scopeCount: $("#material-chatcut-scope-count"),
  readyCount: $("#material-chatcut-ready-count"),
  importableCount: $("#chatcut-importable-count"),
  existingCount: $("#chatcut-existing-count"),
  problemCount: $("#chatcut-problem-count"),
  requestCount: $("#material-chatcut-request-count"),
  lastStatus: $("#material-chatcut-last-status"),
  syncStatus: $("#material-chatcut-sync-status"),
  preflightResult: $("#chatcut-preflight-result"),
  projectHealth: $("#chatcut-project-health"),
  projectId: $("#chatcut-project-id"),
  queueSummary: $("#chatcut-queue-summary"),
  latestProgressWrap: $(".chatcut-latest-progress"),
  latestTitle: $("#chatcut-latest-title"),
  latestPercent: $("#chatcut-latest-percent"),
  latestProgress: $("#chatcut-latest-progress"),
  latestDetail: $("#chatcut-latest-detail"),
  executorState: $("#chatcut-executor-state"),
  executorLabel: $("#chatcut-executor-label"),
  executorDetail: $("#chatcut-executor-detail"),
  copyTaskBtn: $("#chatcut-copy-task-btn"),
  syncList: $("#material-chatcut-sync-list"),
  requestState: $("#chatcut-request-state"),
  readyState: $("#chatcut-ready-state"),
  refreshBtn: $("#chatcut-refresh-btn"),
  queueRefreshBtn: $("#chatcut-queue-refresh-btn"),
  embedFrame: $("#material-chatcut-embed-frame"),
  embedStatus: $("#material-chatcut-embed-status"),
  embedReloadBtn: $("#material-chatcut-embed-reload-btn"),
  openWindowBtn: $("#material-chatcut-open-window-btn"),
  hyperframesStatus: $("#chatcut-hyperframes-status"),
  hyperframesOptions: $(".chatcut-hyperframes-options"),
  hyperframesOfferInput: $("#chatcut-hyperframes-offer-input"),
  copyHyperframesBtn: $("#chatcut-copy-hyperframes-btn"),
  toast: $("#chatcut-toast"),
};

const state = {
  library: { activeId: "", batches: [], items: {} },
  sync: { version: 1, requests: [], assets: [] },
  operations: { executor: {} },
  preview: null,
  previewError: "",
  previewing: false,
  submitting: false,
  suggestedProductKey: "",
  previewTimer: null,
  previewToken: 0,
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
  if (!elements.toast) return;
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 2800);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) throw new Error(payload.error || `请求失败：${response.status}`);
  return payload;
}

function normalizeLibrary(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const batches = Array.isArray(source.batches)
    ? source.batches.filter((item) => item && typeof item === "object" && item.id).map((item) => ({
      id: String(item.id),
      name: String(item.name || "未命名批次"),
    }))
    : [];
  const activeId = batches.some((batch) => batch.id === source.activeId) ? String(source.activeId) : (batches[0]?.id || "");
  return {
    activeId,
    batches,
    items: source.items && typeof source.items === "object" && !Array.isArray(source.items) ? source.items : {},
  };
}

function normalizeSync(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  return {
    version: Number(source.version || 1) || 1,
    updatedAt: String(source.updatedAt || ""),
    requests: Array.isArray(source.requests) ? source.requests.filter((item) => item && typeof item === "object").slice(-100) : [],
    assets: Array.isArray(source.assets) ? source.assets.filter((item) => item && typeof item === "object").slice(-5000) : [],
  };
}

function inferVideo(value) {
  return /\.(mp4|mov|m4v|webm|avi|mkv|mts|m2ts)(?:$|[?#])/i.test(String(value || ""));
}

function videoItems() {
  return Object.entries(state.library.items).flatMap(([url, raw]) => {
    const item = raw && typeof raw === "object" ? raw : {};
    const kind = String(item.kind || "").toLowerCase();
    const sourceName = item.name || item.sourcePath || item.externalPath || item.localPath || url;
    if (kind && kind !== "video") return [];
    if (!kind && !inferVideo(sourceName)) return [];
    return [{
      ...item,
      url,
      batchId: String(item.batchId || ""),
      analysisStatus: String(item.analysisStatus || item.status || "queued").toLowerCase(),
    }];
  });
}

function selectedBatchId() {
  return String(elements.batchSelect?.value || state.library.activeId || "");
}

function scopedItems() {
  const batchId = selectedBatchId();
  return videoItems().filter((item) => item.url && item.batchId === batchId);
}

function readyItems(items = scopedItems()) {
  return items.filter((item) => item.analysisStatus === "ready");
}

function batchStats(batchId) {
  const items = videoItems().filter((item) => item.batchId === batchId);
  return { total: items.length, ready: readyItems(items).length };
}

function selectedBatch() {
  return state.library.batches.find((batch) => batch.id === selectedBatchId()) || null;
}

function sourceProductLabel(item) {
  const path = String(item?.sourcePath || item?.externalPath || item?.localPath || "").trim();
  const parts = path.split(/[\\/]+/).filter(Boolean);
  const markerIndex = parts.lastIndexOf("打标签");
  return markerIndex >= 0 && markerIndex + 1 < parts.length ? parts[markerIndex + 1] : "";
}

function suggestedProductKey(items) {
  const labels = [...new Set(items.map(sourceProductLabel).filter(Boolean))];
  return labels.length === 1 ? labels[0] : "";
}

function projectIdFromInput() {
  return String(elements.projectUrlInput?.value || "").trim().match(CHATCUT_PROJECT_ID_PATTERN)?.[1]?.toLowerCase() || "";
}

function normalizedProjectUrl() {
  const raw = String(elements.projectUrlInput?.value || "").trim();
  const projectId = projectIdFromInput();
  if (!raw || !projectId) return "";
  try {
    const url = new URL(raw);
    if (!["app.chatcut.io", "chatcut.io"].includes(url.hostname)) return "";
  } catch {
    return "";
  }
  return `https://app.chatcut.io/zh/editor/${projectId}`;
}

function statusMeta(status) {
  return CHATCUT_STATUS_META[String(status || "")] || { label: "未知", tone: "queued" };
}

function itemStatusMeta(status) {
  return CHATCUT_ITEM_STATUS_META[String(status || "")] || { label: "未知", tone: "idle" };
}

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function requestProblemCount(request) {
  const summary = request?.summary || {};
  return Number(summary.failed || 0) + Number(summary.unresolved || 0);
}

function requestImportedCount(request) {
  const summary = request?.summary || {};
  return Number(summary.imported || 0) + Number(summary.alreadyImported || 0);
}

function requestProgress(request) {
  const summary = request?.summary || {};
  const total = Number(summary.total || 0);
  if (!total) return 0;
  const unfinished = Number(summary.pending || 0) + Number(summary.syncing || 0);
  return Math.max(0, Math.min(100, Math.round(((total - unfinished) / total) * 100)));
}

function requestSummary(request) {
  const summary = request?.summary || {};
  const parts = [
    `共 ${Number(summary.total || 0)}`,
    `待上传 ${Number(summary.pending || 0)}`,
    `已进入项目 ${requestImportedCount(request)}`,
  ];
  const problemCount = requestProblemCount(request);
  if (problemCount) parts.push(`需处理 ${problemCount}`);
  return parts.join(" · ");
}

function readProductPreferences() {
  try {
    const value = JSON.parse(window.localStorage.getItem(CHATCUT_PRODUCT_KEYS_KEY) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

function savePreferences() {
  window.localStorage.setItem(CHATCUT_PROJECT_URL_KEY, String(elements.projectUrlInput?.value || "").trim());
  window.localStorage.setItem(CHATCUT_BATCH_KEY, selectedBatchId());
  const productKeys = readProductPreferences();
  if (selectedBatchId()) productKeys[selectedBatchId()] = String(elements.productKeyInput?.value || "").trim();
  window.localStorage.setItem(CHATCUT_PRODUCT_KEYS_KEY, JSON.stringify(productKeys));
}

function loadPreferences() {
  elements.projectUrlInput.value = window.localStorage.getItem(CHATCUT_PROJECT_URL_KEY) || "";
}

function loadProductPreference({ allowSuggestion = true } = {}) {
  const stored = String(readProductPreferences()[selectedBatchId()] || "").trim();
  const suggestion = suggestedProductKey(readyItems());
  state.suggestedProductKey = suggestion;
  elements.productKeyInput.value = stored || (allowSuggestion ? suggestion : "");
}

function renderBatchOptions() {
  const savedBatchId = window.localStorage.getItem(CHATCUT_BATCH_KEY) || "";
  const previousSelection = elements.batchSelect.value;
  const previous = previousSelection || savedBatchId || state.library.activeId;
  const stats = new Map(state.library.batches.map((batch) => [batch.id, batchStats(batch.id)]));
  elements.batchSelect.innerHTML = state.library.batches.length
    ? state.library.batches.map((batch) => {
      const batchCount = stats.get(batch.id) || { total: 0, ready: 0 };
      return `<option value="${escapeHtml(batch.id)}">${escapeHtml(batch.name)} · ${batchCount.ready}/${batchCount.total} 可用</option>`;
    }).join("")
    : '<option value="">暂无素材批次</option>';
  const previousStats = stats.get(previous);
  const fallback = state.library.batches.find((batch) => (stats.get(batch.id)?.ready || 0) > 0)
    || state.library.batches.find((batch) => (stats.get(batch.id)?.total || 0) > 0)
    || state.library.batches[0];
  const nextSelection = previousStats?.total ? previous : (fallback?.id || "");
  elements.batchSelect.value = nextSelection;
  if (!previousSelection || previousSelection !== nextSelection || !String(elements.productKeyInput.value || "").trim()) {
    loadProductPreference();
  }
}

function renderProjectHealth() {
  const projectId = projectIdFromInput();
  const validUrl = normalizedProjectUrl();
  if (!String(elements.projectUrlInput.value || "").trim()) {
    elements.projectHealth.textContent = "未绑定项目";
    elements.projectHealth.dataset.tone = "idle";
    elements.projectId.textContent = "粘贴 ChatCut 编辑器地址后自动检查。";
    return;
  }
  if (!validUrl) {
    elements.projectHealth.textContent = "链接无效";
    elements.projectHealth.dataset.tone = "failed";
    elements.projectId.textContent = "需要完整的 app.chatcut.io 编辑器链接。";
    return;
  }
  elements.projectHealth.textContent = "项目已识别";
  elements.projectHealth.dataset.tone = "done";
  elements.projectId.textContent = `Project ID · ${projectId}`;
}

function setFlowState() {
  const scopeReady = scopedItems().length > 0;
  const projectReady = Boolean(normalizedProjectUrl());
  const latest = state.sync.requests[state.sync.requests.length - 1];
  const syncReady = Boolean(latest?.status === "complete" || requestImportedCount(latest) > 0);
  const canEdit = syncReady;
  const states = { source: scopeReady, project: projectReady, sync: syncReady, edit: canEdit };
  let activeAssigned = false;
  document.querySelectorAll("[data-chatcut-step]").forEach((step) => {
    const key = step.dataset.chatcutStep;
    step.classList.toggle("done", Boolean(states[key]));
    step.classList.remove("active");
    if (!activeAssigned && !states[key]) {
      step.classList.add("active");
      activeAssigned = true;
    }
  });
  if (!activeAssigned) document.querySelector('[data-chatcut-step="edit"]')?.classList.add("active");
}

function aggregatePreviews(previews) {
  const summaryKeys = ["total", "pending", "syncing", "imported", "alreadyImported", "failed", "unresolved", "skipped"];
  const summary = Object.fromEntries(summaryKeys.map((key) => [key, 0]));
  const items = [];
  previews.forEach((preview) => {
    summaryKeys.forEach((key) => { summary[key] += Number(preview?.summary?.[key] || 0); });
    items.push(...(Array.isArray(preview?.items) ? preview.items : []));
  });
  return { summary, items, chunks: previews.length };
}

function renderPreflight() {
  const scope = scopedItems();
  const ready = readyItems(scope);
  const summary = state.preview?.summary || {};
  const pending = Number(summary.pending || 0);
  const existing = Number(summary.alreadyImported || 0) + Number(summary.imported || 0);
  const problems = Number(summary.failed || 0) + Number(summary.unresolved || 0);

  elements.scopeCount.textContent = String(scope.length);
  elements.readyCount.textContent = String(ready.length);
  elements.importableCount.textContent = String(pending);
  elements.existingCount.textContent = String(existing);
  elements.problemCount.textContent = String(problems);
  elements.readyState.textContent = `${ready.length} 个视频`;

  let tone = "idle";
  let title = "等待预检";
  let message = "请选择批次并填写 ChatCut 项目链接。";
  if (state.previewing) {
    tone = "running";
    title = "正在检查素材";
    message = "正在核对文件路径、产品目录和项目内重复素材。";
  } else if (state.previewError) {
    tone = "failed";
    title = "预检未通过";
    message = state.previewError;
  } else if (state.preview) {
    if (problems && pending) {
      tone = "warning";
      title = `${pending} 个可上传，${problems} 个需处理`;
      message = `可用素材仍可提交；路径不可读的素材会保留在任务明细中。${state.preview.chunks > 1 ? ` 将自动拆成 ${state.preview.chunks} 个任务。` : ""}`;
    } else if (problems) {
      tone = "failed";
      title = "没有可上传素材";
      message = `${problems} 个素材路径不可读，请回到素材库重新登记 NAS 或本地路径。`;
    } else if (pending) {
      tone = "done";
      title = `预检通过，可上传 ${pending} 个素材`;
      message = `${existing ? `${existing} 个重复素材会自动跳过；` : ""}${state.preview.chunks > 1 ? `将按每组 ${CHATCUT_SYNC_CHUNK_SIZE} 个自动分批。` : "产品、批次与文件路径均已通过检查。"}`;
    } else {
      tone = "done";
      title = "当前素材已全部在项目中";
      message = `${existing} 个素材无需重复上传，可以直接进入下方时间线混剪。`;
    }
  } else if (!scope.length) {
    message = "当前批次没有视频，请返回视频素材库导入或登记素材。";
  } else if (!ready.length) {
    message = "当前批次没有分析完成的视频，请先在视频素材库运行分析 Skill。";
  } else if (!normalizedProjectUrl()) {
    message = "请填写有效的 ChatCut 项目链接。";
  } else if (!String(elements.productKeyInput.value || "").trim()) {
    message = "请填写与素材目录一致的产品名或 SKU。";
  }

  elements.preflightResult.dataset.tone = tone;
  elements.preflightResult.querySelector("strong").textContent = title;
  elements.syncStatus.textContent = message;

  const busy = state.previewing || state.submitting;
  elements.syncRefreshBtn.disabled = busy || !ready.length || !normalizedProjectUrl();
  elements.refreshBtn.disabled = state.submitting;
  elements.queueRefreshBtn.disabled = state.submitting;
  elements.syncSubmitBtn.disabled = busy || !state.preview || pending < 1;
  elements.syncSubmitBtn.textContent = state.submitting
    ? "正在登记任务..."
    : pending > 0
      ? `同步 ${pending} 个可用素材`
      : state.preview && existing > 0
        ? "无需重复同步"
        : "同步可用素材";
  renderProjectHealth();
  setFlowState();
}

function renderLatestProgress(latest) {
  if (!latest) {
    elements.lastStatus.textContent = "未提交";
    elements.lastStatus.dataset.tone = "idle";
    elements.latestProgressWrap.dataset.tone = "idle";
    elements.latestTitle.textContent = "等待创建同步任务";
    elements.latestPercent.textContent = "0%";
    elements.latestProgress.value = 0;
    elements.latestProgress.textContent = "0%";
    elements.latestDetail.textContent = "提交后会在这里显示真实上传进度。";
    elements.copyTaskBtn.disabled = true;
    return;
  }
  const meta = statusMeta(latest.status);
  const progress = requestProgress(latest);
  elements.lastStatus.textContent = meta.label;
  elements.lastStatus.dataset.tone = meta.tone;
  elements.latestProgressWrap.dataset.tone = meta.tone;
  elements.latestTitle.textContent = latest.productKey || "未命名产品";
  elements.latestPercent.textContent = `${progress}%`;
  elements.latestProgress.value = progress;
  elements.latestProgress.textContent = `${progress}%`;
  elements.latestDetail.textContent = latest.status === "queued"
    ? `${requestSummary(latest)}。尚未上传，请复制执行指令并在启用 ChatCut 插件的 Codex 中运行。`
    : latest.status === "syncing"
      ? `${requestSummary(latest)}。正在上传，请保持 NAS 路径可访问。`
      : latest.status === "complete"
        ? `${requestSummary(latest)}。素材已进入目标项目。`
        : `${requestSummary(latest)}。展开任务查看具体原因。`;
  elements.copyTaskBtn.disabled = !latest.id;
}

function renderRequestItems(request) {
  const items = Array.isArray(request.items) ? request.items : [];
  if (!items.length) return '<div class="chatcut-task-empty">暂无逐素材明细</div>';
  return items.slice(0, 12).map((item) => {
    const meta = itemStatusMeta(item.status);
    return `
      <div class="chatcut-task-material">
        <span data-tone="${escapeHtml(meta.tone)}">${escapeHtml(meta.label)}</span>
        <div>
          <strong title="${escapeHtml(item.name || "未命名素材")}">${escapeHtml(item.name || "未命名素材")}</strong>
          <small>${escapeHtml(item.error || [item.role && `角色 ${item.role}`, Array.isArray(item.tags) && item.tags.slice(0, 3).join(" / ")].filter(Boolean).join(" · ") || "等待处理")}</small>
        </div>
      </div>
    `;
  }).join("") + (items.length > 12 ? `<small class="chatcut-task-more">其余 ${items.length - 12} 个素材未展开</small>` : "");
}

function renderQueue() {
  const requests = state.sync.requests || [];
  const latest = requests[requests.length - 1] || null;
  const activeCount = requests.filter((request) => ["queued", "syncing", "partial"].includes(String(request.status || ""))).length;
  elements.requestCount.textContent = String(requests.length);
  elements.requestState.textContent = `${activeCount} 个进行中`;
  elements.queueSummary.textContent = requests.length ? `${activeCount} 个进行中 · ${requests.length} 条历史记录` : "暂无同步任务";
  renderLatestProgress(latest);

  if (!requests.length) {
    elements.syncList.innerHTML = `
      <div class="chatcut-queue-empty">
        <strong>队列还是空的</strong>
        <small>左侧预检通过后即可提交素材。</small>
      </div>`;
    return;
  }

  elements.syncList.innerHTML = requests.slice(-8).reverse().map((request, index) => {
    const meta = statusMeta(request.status);
    const progress = requestProgress(request);
    const errorCount = requestProblemCount(request);
    return `
      <details class="material-chatcut-sync-item ${escapeHtml(meta.tone)}" ${index === 0 ? "open" : ""}>
        <summary>
          <span>${escapeHtml(meta.label)}</span>
          <div>
            <strong>${escapeHtml(request.productKey || "未命名产品")}</strong>
            <small>${escapeHtml([request.batchName, formatTime(request.updatedAt || request.createdAt), requestSummary(request)].filter(Boolean).join(" · "))}</small>
          </div>
          <em>${progress}%</em>
        </summary>
        <div class="chatcut-task-progress"><i style="width:${progress}%"></i></div>
        ${errorCount ? `<p class="material-chatcut-sync-error">${errorCount} 个素材需要处理，请检查下方路径或上传错误。</p>` : ""}
        <div class="chatcut-task-materials">${renderRequestItems(request)}</div>
        <div class="chatcut-task-actions">
          <button type="button" class="mini-action" data-copy-task="${escapeHtml(request.id || "")}">复制 Codex 指令</button>
          <a class="mini-action link-action" href="${escapeHtml(request.projectUrl || "https://app.chatcut.io/zh/")}" target="_blank" rel="noopener">打开项目</a>
        </div>
      </details>
    `;
  }).join("");
}

function renderExecutorState() {
  if (!elements.executorState) return;
  const requests = state.sync.requests || [];
  const active = [...requests].reverse().find((request) => ["queued", "syncing", "partial"].includes(String(request.status || "")));
  const executor = state.operations?.executor || {};
  let tone = "idle";
  let label = "当前没有待执行任务";
  let detail = "创建上传任务后，Codex 中的 ChatCut 插件会接管原始视频导入。";
  if (active && executor.health === "online") {
    tone = "running";
    label = active.status === "syncing" ? "Codex 正在上传素材" : "ChatCut 执行器已连接";
    detail = `${active.id || "当前任务"} · ${requestSummary(active)}`;
  } else if (active) {
    tone = "blocked";
    label = "ChatCut 插件尚未接管任务";
    detail = `${active.id || "当前任务"} · ${requestSummary(active)} · 请复制 Codex 执行指令。`;
  } else if (executor.health === "online") {
    tone = "done";
    label = "ChatCut 执行器在线";
    detail = "当前队列已处理完毕。";
  }
  elements.executorState.dataset.tone = tone;
  elements.executorLabel.textContent = label;
  elements.executorDetail.textContent = detail;
}

function selectedHyperframesModules() {
  if (!elements.hyperframesOptions) return [];
  return [...elements.hyperframesOptions.querySelectorAll('input[type="checkbox"]:checked')].map((input) => input.value);
}

function hyperframesExecutionPrompt() {
  const latest = state.sync.requests[state.sync.requests.length - 1] || null;
  const projectUrl = normalizedProjectUrl() || latest?.projectUrl || "";
  if (!projectUrl) return "";
  const product = String(elements.productKeyInput.value || latest?.productKey || selectedBatch()?.name || "未命名产品").trim();
  const moduleLabels = {
    hook: "0-3秒目标人群/问题动态钩子",
    "selling-point": "斜扣腰头、版型与穿着效果卖点强调",
    cta: "品牌与单一CTA片尾",
    offer: "价格与优惠卡",
  };
  const modules = selectedHyperframesModules();
  const offer = modules.includes("offer") ? String(elements.hyperframesOfferInput?.value || "").trim() : "";
  return [
    "@HyperFrames 请为当前电商短视频生成独立视觉增强素材，并交给 @ChatCut 放入可编辑时间线。",
    `项目：${projectUrl}`,
    `产品：${product}`,
    latest?.id ? `素材同步任务：${latest.id}` : "",
    `增强模块：${modules.map((item) => moduleLabels[item]).filter(Boolean).join("；")}`,
    offer ? `已确认优惠信息：${offer}` : "未提供优惠信息，不得生成价格、库存、折扣或虚假稀缺表达。",
    "开始前读取当前工作区的剪辑配置与素材库规则。",
    "规格为9:16、1080x1920、30fps；字幕以日语为主，普通文字白色，核心词黄色或橙色，底部预留15%平台安全区。",
    "HyperFrames只生成钩子、卖点强调、优惠卡和CTA等独立上层素材；主视频选片、配音、字幕和音频继续保留在ChatCut独立轨道。",
    "优先使用透明背景；如果当前渲染格式不支持透明，只生成全屏钩子或片尾，不得用黑底覆盖主视频。",
    "不得把主时间线渲染成单个扁平视频。完成后将每个增强素材导入ChatCut上层轨道，并保持源素材连续块可编辑。",
  ].filter(Boolean).join("\n");
}

function renderHyperframesState() {
  if (!elements.copyHyperframesBtn) return;
  const latest = state.sync.requests[state.sync.requests.length - 1] || null;
  const projectUrl = normalizedProjectUrl() || latest?.projectUrl || "";
  const modules = selectedHyperframesModules();
  const offerSelected = modules.includes("offer");
  const offer = String(elements.hyperframesOfferInput?.value || "").trim();
  const ready = Boolean(projectUrl && modules.length && (!offerSelected || offer));
  elements.copyHyperframesBtn.disabled = !ready;
  if (!projectUrl) {
    elements.hyperframesStatus.textContent = "先绑定目标 ChatCut 项目。";
  } else if (!modules.length) {
    elements.hyperframesStatus.textContent = "至少选择一个视觉增强模块。";
  } else if (offerSelected && !offer) {
    elements.hyperframesStatus.textContent = "价格卡必须填写已确认的优惠信息。";
  } else {
    elements.hyperframesStatus.textContent = `已选择 ${modules.length} 个增强模块 · 主时间线保持可编辑。`;
  }
}

function renderAll() {
  renderPreflight();
  renderQueue();
  renderExecutorState();
  renderHyperframesState();
}

function chunkItems(items, size = CHATCUT_SYNC_CHUNK_SIZE) {
  const chunks = [];
  for (let index = 0; index < items.length; index += size) chunks.push(items.slice(index, index + size));
  return chunks;
}

function syncPayload(items) {
  const batch = selectedBatch();
  return {
    projectUrl: normalizedProjectUrl(),
    productKey: String(elements.productKeyInput.value || "").trim(),
    scope: "batch",
    statuses: ["ready"],
    urls: items.map((item) => item.url),
    filterSnapshot: {
      scope: "batch",
      activeBatchId: selectedBatchId(),
      filterBatchId: selectedBatchId(),
      batchName: batch?.name || "",
      filterTag: "all",
      kind: "video",
      status: "ready",
      role: "all",
      search: "",
      requestedCount: items.length,
      capturedAt: new Date().toISOString(),
    },
  };
}

function codexExecutionPrompt(request) {
  if (!request?.id) return "";
  const product = request.productKey || "未命名产品";
  const batch = request.batchName || "未分批";
  const project = request.projectUrl || request.projectId || "目标 ChatCut 项目";
  return [
    "@ChatCut 请使用 chatcut-material-sync Skill 执行素材同步任务。",
    `任务 ID：${request.id}`,
    `产品：${product}`,
    `批次：${batch}`,
    `目标项目：${project}`,
    "请从 Obsidian 的 chatcut-sync.json 读取该任务，只导入任务内 analysisStatus=ready 且路径可读的视频。",
    "上传后把每个 ChatCut assetId 和成功/失败状态回写到原任务，不要创建重复任务，也不要改传到其他项目。",
  ].join("\n");
}

function resetPreview() {
  state.preview = null;
  state.previewError = "";
  state.previewToken += 1;
  renderPreflight();
}

function schedulePreflight(delay = 450) {
  window.clearTimeout(state.previewTimer);
  resetPreview();
  state.previewTimer = window.setTimeout(() => runPreflight({ silent: true }), delay);
}

async function runPreflight({ silent = false } = {}) {
  const ready = readyItems();
  const projectUrl = normalizedProjectUrl();
  const productKey = String(elements.productKeyInput.value || "").trim();
  if (!ready.length || !projectUrl || !productKey || state.submitting) {
    renderPreflight();
    return;
  }
  const token = ++state.previewToken;
  state.previewing = true;
  state.previewError = "";
  renderPreflight();
  try {
    const previews = await Promise.all(chunkItems(ready).map(async (items) => {
      const payload = await requestJson("/api/material-library/chatcut-sync/preview", {
        method: "POST",
        body: JSON.stringify(syncPayload(items)),
      });
      return payload.preview || {};
    }));
    if (token !== state.previewToken) return;
    state.preview = aggregatePreviews(previews);
    if (!silent) showToast("同步预检已完成");
  } catch (error) {
    if (token !== state.previewToken) return;
    state.preview = null;
    state.previewError = error.message;
    if (!silent) showToast(error.message);
  } finally {
    if (token === state.previewToken) {
      state.previewing = false;
      renderPreflight();
    }
  }
}

function embedUrl() {
  return normalizedProjectUrl() || "https://app.chatcut.io/zh/";
}

function updateEmbed({ force = false } = {}) {
  const url = embedUrl();
  elements.openWindowBtn.href = url;
  if (force || elements.embedFrame.src !== url) {
    elements.embedFrame.src = url;
    elements.embedStatus.textContent = url.includes("/editor/") ? "正在加载当前 ChatCut 项目" : "填写项目链接后加载对应编辑器";
  }
}

async function loadData({ silent = false, runPreviewAfter = false } = {}) {
  try {
    const [libraryPayload, syncPayloadValue, operationsPayload] = await Promise.all([
      requestJson("/api/material-library"),
      requestJson("/api/material-library/chatcut-sync"),
      requestJson("/api/operations-center").catch(() => ({ operations: { executor: {} } })),
    ]);
    state.library = normalizeLibrary(libraryPayload.library || {});
    state.sync = normalizeSync(syncPayloadValue.sync || {});
    state.operations = operationsPayload.operations || { executor: {} };
    renderBatchOptions();
    renderAll();
    if (runPreviewAfter) await runPreflight({ silent: true });
    if (!silent) showToast("ChatCut 工作区已刷新");
  } catch (error) {
    state.previewError = `数据读取失败：${error.message}`;
    renderAll();
    if (!silent) showToast(error.message);
  }
}

async function submitSyncRequest() {
  if (state.submitting || !state.preview) return;
  const ready = readyItems();
  if (!ready.length || Number(state.preview.summary?.pending || 0) < 1) return;
  const pendingUrls = new Set(
    (state.preview.items || [])
      .filter((item) => String(item?.status || "") === "pending")
      .map((item) => String(item?.panelUrl || ""))
      .filter(Boolean),
  );
  const uploadable = ready.filter((item) => pendingUrls.has(item.url));
  if (!uploadable.length) return;

  state.submitting = true;
  savePreferences();
  renderPreflight();
  try {
    const chunks = chunkItems(uploadable);
    let pendingTotal = 0;
    for (let index = 0; index < chunks.length; index += 1) {
      elements.syncSubmitBtn.textContent = chunks.length > 1 ? `正在登记 ${index + 1}/${chunks.length}` : "正在登记任务...";
      const payload = await requestJson("/api/material-library/chatcut-sync/request", {
        method: "POST",
        body: JSON.stringify(syncPayload(chunks[index])),
      });
      state.sync = normalizeSync(payload.sync || {});
      pendingTotal += Number(payload.request?.summary?.pending || 0);
      renderQueue();
    }
    showToast(`已登记 ${pendingTotal} 个待上传素材，请复制 Codex 执行指令`);
    await loadData({ silent: true, runPreviewAfter: true });
  } catch (error) {
    state.previewError = `提交失败：${error.message}`;
    showToast(error.message);
  } finally {
    state.submitting = false;
    renderAll();
  }
}

async function copyText(value, successMessage = "已复制") {
  const text = String(value || "").trim();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    showToast(successMessage);
  } catch {
    showToast("复制失败，请手动选择文本");
  }
}

function bindEvents() {
  elements.syncSubmitBtn.addEventListener("click", submitSyncRequest);
  elements.syncRefreshBtn.addEventListener("click", () => runPreflight());
  elements.refreshBtn.addEventListener("click", () => loadData({ runPreviewAfter: true }));
  elements.queueRefreshBtn.addEventListener("click", () => loadData({ runPreviewAfter: true }));
  elements.batchSelect.addEventListener("change", () => {
    savePreferences();
    loadProductPreference();
    schedulePreflight(120);
  });
  elements.projectUrlInput.addEventListener("input", () => {
    renderProjectHealth();
    renderHyperframesState();
    schedulePreflight();
  });
  elements.projectUrlInput.addEventListener("change", () => {
    savePreferences();
    updateEmbed({ force: true });
  });
  elements.productKeyInput.addEventListener("input", () => schedulePreflight());
  elements.productKeyInput.addEventListener("change", savePreferences);
  elements.embedReloadBtn.addEventListener("click", () => updateEmbed({ force: true }));
  elements.embedFrame.addEventListener("load", () => {
    elements.embedStatus.textContent = normalizedProjectUrl()
      ? "项目页面已请求加载；如浏览器阻止嵌入，请打开完整编辑器"
      : "ChatCut 首页已请求加载";
  });
  elements.copyTaskBtn.addEventListener("click", () => {
    const latest = state.sync.requests[state.sync.requests.length - 1];
    copyText(codexExecutionPrompt(latest), "Codex 执行指令已复制");
  });
  elements.syncList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-copy-task]");
    if (!button) return;
    const request = state.sync.requests.find((item) => item.id === button.dataset.copyTask);
    copyText(codexExecutionPrompt(request), "Codex 执行指令已复制");
  });
  elements.hyperframesOptions?.addEventListener("change", renderHyperframesState);
  elements.hyperframesOfferInput?.addEventListener("input", renderHyperframesState);
  elements.copyHyperframesBtn?.addEventListener("click", () => {
    copyText(hyperframesExecutionPrompt(), "HyperFrames 视觉增强指令已复制");
  });
}

loadPreferences();
bindEvents();
renderProjectHealth();
updateEmbed({ force: true });
loadData({ silent: true, runPreviewAfter: true });

window.setInterval(() => {
  if (document.hidden || state.submitting || state.previewing) return;
  const active = (state.sync.requests || []).some((request) => ["queued", "syncing", "partial"].includes(String(request?.status || "")));
  if (active) loadData({ silent: true });
}, 10000);
