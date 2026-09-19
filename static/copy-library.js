const COPY_LIBRARY_DRAFT_KEY = "seedanceCopyLibraryDraft";

const $ = (selector) => document.querySelector(selector);

const copyElements = {
  form: $("#copy-library-form"),
  formKicker: $("#copy-library-form-kicker"),
  formTitle: $("#copy-library-form-title"),
  resetBtn: $("#copy-library-reset-btn"),
  templateBtn: $("#copy-library-template-btn"),
  title: $("#copy-library-title-input"),
  product: $("#copy-library-product-input"),
  market: $("#copy-library-market-select"),
  language: $("#copy-library-language-select"),
  stage: $("#copy-library-stage-select"),
  style: $("#copy-library-style-select"),
  duration: $("#copy-library-duration-select"),
  script: $("#copy-library-script-input"),
  sentenceCount: $("#copy-library-sentence-count"),
  characterCount: $("#copy-library-character-count"),
  readingTime: $("#copy-library-reading-time"),
  durationFit: $("#copy-library-duration-fit"),
  analyzeBtn: $("#copy-library-analyze-btn"),
  analysisPanel: $("#copy-library-analysis-panel"),
  analysisScore: $("#copy-library-analysis-score"),
  hookScore: $("#copy-library-hook-score"),
  pacingScore: $("#copy-library-pacing-score"),
  matchScore: $("#copy-library-match-score"),
  analysisSummary: $("#copy-library-analysis-summary"),
  analysisSegments: $("#copy-library-analysis-segments"),
  analysisAdvice: $("#copy-library-analysis-advice"),
  tags: $("#copy-library-tags-input"),
  source: $("#copy-library-source-input"),
  status: $("#copy-library-status-select"),
  views: $("#copy-library-views-input"),
  saves: $("#copy-library-saves-input"),
  orders: $("#copy-library-orders-input"),
  notes: $("#copy-library-notes-input"),
  saveBtn: $("#copy-library-save-btn"),
  message: $("#copy-library-form-message"),
  refreshBtn: $("#copy-library-refresh-btn"),
  search: $("#copy-library-search-input"),
  filterStage: $("#copy-library-filter-stage"),
  filterStatus: $("#copy-library-filter-status"),
  sort: $("#copy-library-sort-select"),
  list: $("#copy-library-list"),
  count: $("#copy-library-count"),
  verifiedCount: $("#copy-library-verified-count"),
  hookCount: $("#copy-library-hook-count"),
  readyCount: $("#copy-library-ready-count"),
  toast: $("#copy-library-toast"),
};

const copyState = {
  library: { items: [], stageLabels: {}, statusLabels: {} },
  editingId: "",
  search: "",
  stage: "all",
  status: "all",
  sort: "recommended",
  analysis: {},
  analyzing: false,
  toastTimer: null,
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function showToast(message) {
  copyElements.toast.textContent = message;
  copyElements.toast.classList.add("show");
  window.clearTimeout(copyState.toastTimer);
  copyState.toastTimer = window.setTimeout(() => copyElements.toast.classList.remove("show"), 2800);
}

function setMessage(message = "", tone = "") {
  copyElements.message.textContent = message;
  copyElements.message.dataset.tone = tone;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) throw new Error(payload.error || `请求失败：${response.status}`);
  return payload;
}

function stageLabel(value) {
  return copyState.library.stageLabels?.[value] || value || "完整脚本";
}

function statusLabel(value) {
  return copyState.library.statusLabels?.[value] || value || "已收藏";
}

function splitTags(value) {
  return String(value || "").split(/[，,、\n\r]+/).map((tag) => tag.trim().replace(/^#/, "")).filter(Boolean);
}

function numericValue(input) {
  return Math.max(0, Number(input.value || 0) || 0);
}

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN", { notation: "compact", maximumFractionDigits: 1 }).format(Number(value || 0));
}

function formatDate(value) {
  if (!value) return "刚刚";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function scriptLines(text = copyElements.script.value) {
  return String(text || "").split(/\r?\n+/).map((line) => line.trim()).filter(Boolean);
}

function estimatedReadingSeconds(text = copyElements.script.value) {
  const clean = String(text || "").replace(/\d+(?:\.\d+)?\s*[-—~至到]\s*\d+(?:\.\d+)?\s*秒?[｜|:：]?/g, " ").trim();
  if (!clean) return 0;
  if (copyElements.language.value === "en-US") {
    return Math.max(1, Math.round(clean.split(/\s+/).filter(Boolean).length / 2.5));
  }
  const characters = clean.replace(/[\s\p{P}\p{S}]/gu, "").length;
  const rate = copyElements.language.value === "ja-JP" ? 6.2 : 4.5;
  return Math.max(1, Math.round(characters / rate));
}

function updateScriptHealth() {
  const text = copyElements.script.value.trim();
  const sentenceCount = scriptLines(text).length;
  const characterCount = text.length;
  const estimated = estimatedReadingSeconds(text);
  const target = Number(copyElements.duration.value || 15);
  copyElements.sentenceCount.textContent = `${sentenceCount} 句`;
  copyElements.characterCount.textContent = `${characterCount} 字`;
  copyElements.readingTime.textContent = `预计 ${estimated} 秒`;
  if (!text) {
    copyElements.durationFit.textContent = "等待文案";
    copyElements.durationFit.dataset.tone = "idle";
    return;
  }
  const difference = estimated - target;
  if (Math.abs(difference) <= 2) {
    copyElements.durationFit.textContent = `适配 ${target} 秒`;
    copyElements.durationFit.dataset.tone = "ok";
  } else if (difference > 2) {
    copyElements.durationFit.textContent = `预计超出 ${difference} 秒`;
    copyElements.durationFit.dataset.tone = "warn";
  } else {
    copyElements.durationFit.textContent = `还可补约 ${Math.abs(difference)} 秒`;
    copyElements.durationFit.dataset.tone = "warn";
  }
}

function renderAnalysis(analysis = {}) {
  copyState.analysis = analysis && typeof analysis === "object" ? analysis : {};
  const segments = Array.isArray(copyState.analysis.segments) ? copyState.analysis.segments : [];
  const hasAnalysis = segments.length > 0;
  copyElements.analysisPanel.hidden = !hasAnalysis;
  if (!hasAnalysis) return;
  copyElements.analysisScore.textContent = `${Number(copyState.analysis.score || 0)} 分`;
  copyElements.hookScore.textContent = String(Number(copyState.analysis.hookScore || 0));
  copyElements.pacingScore.textContent = String(Number(copyState.analysis.pacingScore || 0));
  copyElements.matchScore.textContent = String(Number(copyState.analysis.materialMatchScore || 0));
  copyElements.analysisSummary.textContent = copyState.analysis.summary || "已完成逐句分镜拆解。";
  copyElements.analysisSegments.innerHTML = segments.map((segment, index) => `
    <article>
      <div><b>${escapeHtml(index + 1)}</b><span>${escapeHtml(Number(segment.startSec || 0).toFixed(1))}-${escapeHtml(Number(segment.endSec || 0).toFixed(1))}s</span></div>
      <strong>${escapeHtml(segment.text || "")}</strong>
      <small>${escapeHtml(stageLabel(segment.role))} · ${escapeHtml(segment.shotType || "产品相关画面")}</small>
      <div class="copy-library-analysis-tags">${(segment.materialTags || []).map((tag) => `<span>#${escapeHtml(tag)}</span>`).join("")}</div>
      ${segment.reason ? `<p>${escapeHtml(segment.reason)}</p>` : ""}
    </article>
  `).join("");
  const missing = Array.isArray(copyState.analysis.missingShots) ? copyState.analysis.missingShots : [];
  const suggestions = Array.isArray(copyState.analysis.suggestions) ? copyState.analysis.suggestions : [];
  copyElements.analysisAdvice.innerHTML = [
    ...missing.map((item) => `<span class="is-missing">素材缺口：${escapeHtml(item)}</span>`),
    ...suggestions.map((item) => `<span>优化建议：${escapeHtml(item)}</span>`),
  ].join("");
}

function updateSelectOptions() {
  const stageValue = copyElements.filterStage.value || copyState.stage;
  const statusValue = copyElements.filterStatus.value || copyState.status;
  const stageOptions = Object.entries(copyState.library.stageLabels || {}).map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join("");
  const statusOptions = Object.entries(copyState.library.statusLabels || {}).map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join("");
  copyElements.filterStage.innerHTML = `<option value="all">全部阶段</option>${stageOptions}`;
  copyElements.filterStatus.innerHTML = `<option value="all">全部状态</option>${statusOptions}`;
  copyElements.filterStage.value = stageValue;
  copyElements.filterStatus.value = statusValue;
}

function renderMetrics() {
  const items = Array.isArray(copyState.library.items) ? copyState.library.items : [];
  copyElements.count.textContent = String(items.length);
  copyElements.verifiedCount.textContent = String(items.filter((item) => item.status === "verified").length);
  copyElements.hookCount.textContent = String(items.filter((item) => item.stage === "hook").length);
  copyElements.readyCount.textContent = String(items.filter((item) => ["verified", "testing", "template"].includes(item.status)).length);
}

function filteredItems() {
  const search = copyState.search.trim().toLowerCase();
  const items = (copyState.library.items || []).filter((item) => {
    if (copyState.stage !== "all" && item.stage !== copyState.stage) return false;
    if (copyState.status !== "all" && item.status !== copyState.status) return false;
    if (!search) return true;
    return [item.title, item.product, item.market, item.style, item.source, item.script, ...(item.tags || [])]
      .join(" ").toLowerCase().includes(search);
  });
  const number = (value) => Number(value || 0) || 0;
  const recommended = (item) => {
    const statusWeight = { verified: 5000000, testing: 2000000, template: 1000000, collected: 0 }[item.status] || 0;
    return statusWeight
      + number(item.performance?.orders) * 1000
      + number(item.performance?.saves) * 10
      + number(item.performance?.views) * 0.01
      + number(item.analysis?.score) * 100;
  };
  return items.sort((left, right) => {
    if (copyState.sort === "verified") return Number(right.status === "verified") - Number(left.status === "verified") || recommended(right) - recommended(left);
    if (copyState.sort === "orders") return number(right.performance?.orders) - number(left.performance?.orders);
    if (copyState.sort === "views") return number(right.performance?.views) - number(left.performance?.views);
    if (copyState.sort === "score") return number(right.analysis?.score) - number(left.analysis?.score);
    if (copyState.sort === "updated") return String(right.updatedAt || "").localeCompare(String(left.updatedAt || ""));
    return recommended(right) - recommended(left);
  });
}

function setFormMode(editing = false) {
  copyElements.formKicker.textContent = editing ? "EDIT SCRIPT" : "ADD SCRIPT";
  copyElements.formTitle.textContent = editing ? "编辑视频文案" : "新增视频文案";
  copyElements.saveBtn.textContent = editing ? "保存修改" : "保存到文案库";
  copyElements.resetBtn.hidden = !editing;
}

function clearForm() {
  copyState.editingId = "";
  copyElements.form.reset();
  copyElements.market.value = "日本";
  copyElements.language.value = "ja-JP";
  copyElements.stage.value = "full_script";
  copyElements.style.value = "自然种草";
  copyElements.duration.value = "15";
  copyElements.status.value = "collected";
  copyElements.views.value = "0";
  copyElements.saves.value = "0";
  copyElements.orders.value = "0";
  renderAnalysis({});
  updateScriptHealth();
  setFormMode(false);
  setMessage();
}

function fillForm(item, { asTemplate = false } = {}) {
  copyState.editingId = asTemplate ? "" : String(item.id || "");
  copyElements.title.value = asTemplate ? `${item.title || "视频文案"} · 副本` : (item.title || "");
  copyElements.product.value = item.product || "";
  copyElements.market.value = item.market || "日本";
  copyElements.language.value = item.language || "ja-JP";
  copyElements.stage.value = item.stage || "full_script";
  copyElements.style.value = item.style || "自然种草";
  copyElements.duration.value = String(item.duration || 15);
  copyElements.script.value = item.script || "";
  copyElements.tags.value = Array.isArray(item.tags) ? item.tags.join("、") : "";
  copyElements.source.value = item.source || "";
  copyElements.status.value = asTemplate ? "collected" : (item.status || "collected");
  copyElements.views.value = String(item.performance?.views || 0);
  copyElements.saves.value = String(item.performance?.saves || 0);
  copyElements.orders.value = String(item.performance?.orders || 0);
  copyElements.notes.value = item.notes || "";
  renderAnalysis(item.analysis || {});
  updateScriptHealth();
  setFormMode(!asTemplate);
  setMessage(asTemplate ? "已带入结构模板，请按产品和素材情况改写后保存。" : "正在编辑这条文案。", "success");
  copyElements.title.focus();
}

function payloadFromForm() {
  return {
    title: copyElements.title.value.trim(),
    product: copyElements.product.value.trim(),
    market: copyElements.market.value,
    language: copyElements.language.value,
    stage: copyElements.stage.value,
    style: copyElements.style.value,
    duration: Number(copyElements.duration.value || 15),
    script: copyElements.script.value.trim(),
    tags: splitTags(copyElements.tags.value),
    source: copyElements.source.value.trim(),
    status: copyElements.status.value,
    notes: copyElements.notes.value.trim(),
    performance: {
      views: numericValue(copyElements.views),
      saves: numericValue(copyElements.saves),
      orders: numericValue(copyElements.orders),
    },
    analysis: copyState.analysis || {},
  };
}

function copyCardMarkup(item) {
  const performance = item.performance || {};
  const analysis = item.analysis || {};
  const segmentCount = Array.isArray(analysis.segments) ? analysis.segments.length : 0;
  const excerpt = String(item.script || "").split(/\r?\n/).slice(0, 4).join("\n");
  return `
    <article class="copy-library-card status-${escapeHtml(item.status || "collected")}" data-id="${escapeHtml(item.id)}">
      <div class="copy-library-card-head">
        <div>
          <span class="copy-library-stage-chip">${escapeHtml(stageLabel(item.stage))}</span>
          <strong>${escapeHtml(item.title)}</strong>
          <small>${escapeHtml(item.product || "未分类")} · ${escapeHtml(item.market || "")} · ${escapeHtml(item.language || "")} · ${escapeHtml(item.duration || 15)} 秒</small>
        </div>
        <div class="copy-library-card-badges">
          ${analysis.score ? `<span class="copy-library-score-chip">AI ${escapeHtml(analysis.score)} 分 · ${escapeHtml(segmentCount)} 分镜</span>` : ""}
          <span class="copy-library-status-chip status-${escapeHtml(item.status || "collected")}">${escapeHtml(statusLabel(item.status))}</span>
        </div>
      </div>
      <pre>${escapeHtml(excerpt)}</pre>
      <div class="copy-library-tags">${(item.tags || []).length ? item.tags.map((tag) => `<span>#${escapeHtml(tag)}</span>`).join("") : "<span>未打标签</span>"}</div>
      <div class="copy-library-card-foot">
        <span>播放 ${escapeHtml(formatNumber(performance.views))} · 收藏 ${escapeHtml(formatNumber(performance.saves))} · 订单 ${escapeHtml(formatNumber(performance.orders))}</span>
        <span>${escapeHtml(formatDate(item.updatedAt))}</span>
      </div>
      <div class="copy-library-card-actions">
        <button class="mini-action primary" type="button" data-action="use">用于素材混剪</button>
        <button class="mini-action" type="button" data-action="analyze">AI 拆解</button>
        <button class="mini-action" type="button" data-action="edit">编辑</button>
        <button class="mini-action" type="button" data-action="copy">复制文案</button>
        <button class="ghost-link danger" type="button" data-action="delete">删除</button>
      </div>
    </article>
  `;
}

function renderList() {
  const items = filteredItems();
  if (!items.length) {
    copyElements.list.innerHTML = `
      <article class="copy-library-empty">
        <strong>还没有匹配的文案</strong>
        <small>可载入右上角的结构模板，或把已验证的爆款文案保存进来。</small>
      </article>
    `;
    return;
  }
  copyElements.list.innerHTML = items.map(copyCardMarkup).join("");
  copyElements.list.querySelectorAll("[data-id]").forEach((card) => {
    const item = (copyState.library.items || []).find((entry) => entry.id === card.dataset.id);
    if (!item) return;
    card.querySelector('[data-action="use"]').addEventListener("click", () => useForMix(item));
    card.querySelector('[data-action="analyze"]').addEventListener("click", () => analyzeEntry(item));
    card.querySelector('[data-action="edit"]').addEventListener("click", () => fillForm(item));
    card.querySelector('[data-action="copy"]').addEventListener("click", () => navigator.clipboard.writeText(item.script || "").then(() => showToast("视频文案已复制")));
    card.querySelector('[data-action="delete"]').addEventListener("click", () => deleteEntry(item));
  });
}

function render() {
  updateSelectOptions();
  renderMetrics();
  renderList();
}

async function loadLibrary({ silent = false } = {}) {
  try {
    const response = await requestJson("/api/copy-library");
    copyState.library = response.library || copyState.library;
    render();
    if (!silent) showToast("已从 Obsidian 刷新视频文案库");
  } catch (error) {
    copyElements.list.innerHTML = `<article class="copy-library-empty"><strong>文案库读取失败</strong><small>${escapeHtml(error.message)}</small></article>`;
  }
}

async function saveEntry(event) {
  event.preventDefault();
  const payload = payloadFromForm();
  if (!payload.title || !payload.script) {
    setMessage("请填写文案标题和完整文案。", "error");
    return;
  }
  const editing = Boolean(copyState.editingId);
  const original = copyElements.saveBtn.textContent;
  copyElements.saveBtn.disabled = true;
  copyElements.saveBtn.textContent = editing ? "保存中…" : "入库中…";
  try {
    const response = await requestJson(editing ? "/api/copy-library/update" : "/api/copy-library", {
      method: "POST",
      body: JSON.stringify(editing ? { ...payload, id: copyState.editingId } : payload),
    });
    copyState.library = response.library || copyState.library;
    const entry = response.entry || null;
    clearForm();
    render();
    setMessage(editing ? "文案已更新并同步到 Obsidian。" : "文案已保存并同步到 Obsidian。", "success");
    showToast(entry ? `已保存「${entry.title}」` : "文案已保存");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    copyElements.saveBtn.disabled = false;
    copyElements.saveBtn.textContent = original;
  }
}

async function analyzeCurrentCopy() {
  if (copyState.analyzing) return;
  const payload = payloadFromForm();
  if (!payload.script) {
    setMessage("请先填写需要拆解的完整文案。", "error");
    copyElements.script.focus();
    return;
  }
  copyState.analyzing = true;
  const original = copyElements.analyzeBtn.textContent;
  copyElements.analyzeBtn.disabled = true;
  copyElements.analyzeBtn.textContent = "导演拆解中…";
  setMessage("正在按每句文案生成秒级分镜、镜头类型和素材搜索标签…");
  try {
    const response = await requestJson("/api/copy-library/analyze", {
      method: "POST",
      body: JSON.stringify(copyState.editingId ? { ...payload, id: copyState.editingId } : payload),
    });
    if (response.library) copyState.library = response.library;
    renderAnalysis(response.analysis || {});
    renderMetrics();
    renderList();
    const count = response.analysis?.segments?.length || 0;
    setMessage(`AI 已拆解 ${count} 个分镜，可按标签去素材库匹配视频片段。`, "success");
    showToast(`文案拆解完成：${count} 个分镜`);
  } catch (error) {
    setMessage(error.message, "error");
    showToast(error.message);
  } finally {
    copyState.analyzing = false;
    copyElements.analyzeBtn.disabled = false;
    copyElements.analyzeBtn.textContent = original;
  }
}

function analyzeEntry(item) {
  fillForm(item);
  analyzeCurrentCopy();
}

async function deleteEntry(item) {
  if (!window.confirm(`确定删除「${item.title}」吗？`)) return;
  try {
    const response = await requestJson("/api/copy-library/delete", {
      method: "POST",
      body: JSON.stringify({ id: item.id }),
    });
    copyState.library = response.library || copyState.library;
    if (copyState.editingId === item.id) clearForm();
    render();
    showToast("视频文案已删除");
  } catch (error) {
    showToast(error.message);
  }
}

function useForMix(item) {
  const draft = {
    id: item.id,
    title: item.title,
    product: item.product,
    script: item.script,
    tags: item.tags || [],
    duration: item.duration || 15,
    stage: item.stage,
    source: item.source,
    analysis: item.analysis || {},
  };
  window.sessionStorage.setItem(COPY_LIBRARY_DRAFT_KEY, JSON.stringify(draft));
  window.location.href = "/materials.html#material-auto-pool-section";
}

function loadTemplate() {
  const template = (copyState.library.items || []).find((item) => item.status === "template") || copyState.library.items?.[0];
  if (!template) {
    showToast("文案库中暂未找到结构模板");
    return;
  }
  fillForm(template, { asTemplate: true });
}

function bindEvents() {
  copyElements.form.addEventListener("submit", saveEntry);
  copyElements.resetBtn.addEventListener("click", clearForm);
  copyElements.templateBtn.addEventListener("click", loadTemplate);
  copyElements.refreshBtn.addEventListener("click", () => loadLibrary());
  copyElements.script.addEventListener("input", () => {
    updateScriptHealth();
    if (copyState.analysis?.segments?.length) renderAnalysis({});
  });
  copyElements.language.addEventListener("change", updateScriptHealth);
  copyElements.duration.addEventListener("change", updateScriptHealth);
  copyElements.analyzeBtn.addEventListener("click", analyzeCurrentCopy);
  copyElements.search.addEventListener("input", () => {
    copyState.search = copyElements.search.value;
    renderList();
  });
  copyElements.filterStage.addEventListener("change", () => {
    copyState.stage = copyElements.filterStage.value;
    renderList();
  });
  copyElements.filterStatus.addEventListener("change", () => {
    copyState.status = copyElements.filterStatus.value;
    renderList();
  });
  copyElements.sort.addEventListener("change", () => {
    copyState.sort = copyElements.sort.value;
    renderList();
  });
}

bindEvents();
clearForm();
loadLibrary({ silent: true });
