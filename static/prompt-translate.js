const TRANSLATION_HISTORY_KEY = "seedancePromptTranslationHistory";

const $ = (selector) => document.querySelector(selector);

const elements = {
  modelState: $("#translate-model-state"),
  runtimeState: $("#translate-runtime-state"),
  refreshBtn: $("#translate-refresh-btn"),
  configToggleBtn: $("#translate-config-toggle-btn"),
  configBody: $("#translate-config-body"),
  configSaveBtn: $("#translate-config-save-btn"),
  apiKeyInput: $("#translate-api-key-input"),
  baseUrlInput: $("#translate-base-url-input"),
  modelInput: $("#translate-model-input"),
  temperatureInput: $("#translate-temperature-input"),
  maxTokensInput: $("#translate-max-tokens-input"),
  connectivityBtn: $("#translate-connectivity-btn"),
  invokeBtn: $("#translate-invoke-btn"),
  clearKeyBtn: $("#translate-clear-key-btn"),
  testDetail: $("#translate-config-test-detail"),
  sourceLanguage: $("#translate-source-language-select"),
  targetLanguage: $("#translate-target-language-select"),
  market: $("#translate-market-select"),
  scene: $("#translate-scene-select"),
  tone: $("#translate-tone-select"),
  sourceInput: $("#translate-source-input"),
  sourceCount: $("#translate-source-count"),
  backCheck: $("#translate-back-check"),
  dualCheck: $("#translate-dual-check"),
  complianceCheck: $("#translate-compliance-check"),
  formatCheck: $("#translate-format-check"),
  sampleBtn: $("#translate-sample-btn"),
  clearBtn: $("#translate-clear-btn"),
  submitBtn: $("#translate-submit-btn"),
  copyMainBtn: $("#translate-copy-main-btn"),
  mainOutput: $("#translate-main-output"),
  altOutput: $("#translate-alt-output"),
  backOutput: $("#translate-back-output"),
  consistencyScore: $("#translate-consistency-score"),
  consistencyList: $("#translate-consistency-list"),
  riskState: $("#translate-risk-state"),
  riskList: $("#translate-risk-list"),
  complianceInput: $("#translate-compliance-input"),
  complianceCheckBtn: $("#translate-compliance-check-btn"),
  complianceCopyPromptBtn: $("#translate-compliance-copy-prompt-btn"),
  complianceSummary: $("#translate-compliance-summary"),
  historyClearBtn: $("#translate-history-clear-btn"),
  historyList: $("#translate-history-list"),
  toast: $("#translate-toast"),
};

let toastTimer = null;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 2800);
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

function configPayload(options = {}) {
  return {
    translationApiKey: elements.apiKeyInput.value.trim(),
    translationBaseUrl: elements.baseUrlInput.value.trim(),
    translationModel: elements.modelInput.value.trim(),
    translationTemperature: elements.temperatureInput.value,
    translationMaxTokens: elements.maxTokensInput.value,
    clearTranslationApiKey: Boolean(options.clearTranslationApiKey),
  };
}

function applyConfig(config) {
  const translation = config?.translation || {};
  elements.baseUrlInput.value = translation.baseUrl || "";
  elements.modelInput.value = translation.model || "";
  elements.temperatureInput.value = translation.temperature ?? 0.3;
  elements.maxTokensInput.value = translation.maxTokens ?? 2200;
  elements.apiKeyInput.value = "";
  elements.modelState.textContent = translation.model || "待配置";
  elements.modelState.style.color = translation.hasApiKey ? "var(--blue)" : "var(--cinnabar)";
  elements.runtimeState.textContent = translation.hasApiKey ? "模型已配置" : "等待配置";
}

async function loadConfig({ silent = false } = {}) {
  try {
    const result = await requestJson("/api/config");
    applyConfig(result.config);
    if (!silent) showToast("翻译模型配置已刷新");
  } catch (error) {
    elements.runtimeState.textContent = "配置读取失败";
    if (!silent) showToast(error.message);
  }
}

async function saveConfig(options = {}) {
  const original = elements.configSaveBtn.textContent;
  elements.configSaveBtn.disabled = true;
  elements.configSaveBtn.textContent = "保存中";
  try {
    const result = await requestJson("/api/config", {
      method: "POST",
      body: JSON.stringify(configPayload(options)),
    });
    applyConfig(result.config);
    showToast(options.clearTranslationApiKey ? "翻译 Key 已清除" : "翻译模型配置已保存");
  } finally {
    elements.configSaveBtn.disabled = false;
    elements.configSaveBtn.textContent = original;
  }
}

function renderTestResult(item, mode) {
  const latency = item?.latencyMs ? ` · ${item.latencyMs}ms` : "";
  const status = item?.httpStatus ? ` · HTTP ${item.httpStatus}` : "";
  elements.testDetail.dataset.tone = item?.ok ? "ok" : item?.networkOk ? "warn" : "error";
  elements.testDetail.querySelector("span").textContent = mode === "invoke" ? "MODEL" : "NETWORK";
  elements.testDetail.querySelector("strong").textContent = [item?.message || "状态待检查", status, item?.reply ? `回复：${item.reply}` : ""].filter(Boolean).join(" · ");
  elements.testDetail.title = [item?.endpoint, item?.model].filter(Boolean).join("\n");
  elements.runtimeState.textContent = item?.ok ? `${mode === "invoke" ? "模型可用" : "节点已连通"}${latency}` : "检测需处理";
}

async function testConfig(mode) {
  const button = mode === "invoke" ? elements.invokeBtn : elements.connectivityBtn;
  const original = button.textContent;
  button.disabled = true;
  button.textContent = mode === "invoke" ? "试调用中" : "检测中";
  try {
    const result = await requestJson("/api/config/test/translation", {
      method: "POST",
      body: JSON.stringify({ ...configPayload(), testMode: mode }),
    });
    const item = result.result?.translation;
    renderTestResult(item, mode);
    showToast(item?.message || "检测完成");
  } catch (error) {
    const item = {
      ok: false,
      networkOk: false,
      message: error?.message || "翻译模型测试失败",
    };
    renderTestResult(item, mode);
    showToast(item.message);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function translationPayload() {
  return {
    text: elements.sourceInput.value.trim(),
    sourceLanguage: elements.sourceLanguage.value,
    targetLanguage: elements.targetLanguage.value,
    market: elements.market.value,
    scene: elements.scene.value,
    tone: elements.tone.value,
    backTranslation: elements.backCheck.checked,
    dualPass: elements.dualCheck.checked,
    complianceAudit: elements.complianceCheck.checked,
    preserveFormat: elements.formatCheck.checked,
  };
}

function renderList(container, items, emptyText) {
  const values = Array.isArray(items) ? items.filter(Boolean) : [];
  container.innerHTML = values.length
    ? values.map((item) => `<article><span>•</span><strong>${escapeHtml(typeof item === "string" ? item : item.text || JSON.stringify(item))}</strong></article>`).join("")
    : `<p>${escapeHtml(emptyText)}</p>`;
}

function reviewEntryText(item) {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return String(item || "");
  const term = item.term || item.phrase || "风险表达";
  const category = item.category ? `【${item.category}】` : "";
  const reason = item.reason || "建议调整表达";
  const suggestion = item.suggestion || item.replacement;
  return `${category}${term}：${reason}${suggestion ? ` 建议：${suggestion}` : ""}`;
}

function renderComplianceReview(review = {}, { manual = false } = {}) {
  const risk = String(review.riskLevel || "low").toLowerCase();
  elements.riskState.textContent = { low: "低风险", medium: "需检查", high: "高风险" }[risk] || "已审核";
  elements.riskState.dataset.tone = risk === "low" ? "ok" : risk === "medium" ? "warn" : "error";
  const riskItems = [
    ...(Array.isArray(review.flaggedTerms) ? review.flaggedTerms.map(reviewEntryText) : []),
    ...(Array.isArray(review.suggestions) ? review.suggestions : []),
  ];
  renderList(elements.riskList, riskItems, "未发现明显的 Facebook / TikTok 广告违禁表达。");
  elements.complianceSummary.textContent = review.summary || (manual
    ? "AI 违规检测已完成。"
    : "翻译完成时已自动进行首次违禁词审核。可修改下方文本后再次检测。");
}

function updateComplianceActions() {
  const hasText = Boolean(elements.complianceInput.value.trim());
  elements.complianceCheckBtn.disabled = !hasText;
  elements.complianceCopyPromptBtn.disabled = !hasText;
}

function buildExternalCompliancePrompt() {
  const text = elements.complianceInput.value.trim();
  const languageName = {
    "en-US": "英文",
    "ja-JP": "日文",
    "ko-KR": "韩文",
    "zh-CN": "中文",
  }[elements.targetLanguage.value] || "翻译后的";
  return [
    `请检查以下${languageName}文案是否包含Facebook/TikTok广告违禁词（医疗功效类、绝对化用语、虚假承诺类），标出问题词汇并给出修改建议。`,
    "",
    "文案：",
    text,
  ].join("\n");
}

function renderResult(result) {
  elements.mainOutput.value = result.translation || "";
  elements.altOutput.value = result.alternateTranslation || "";
  elements.backOutput.value = result.backTranslation || "";
  elements.consistencyScore.textContent = Number.isFinite(Number(result.consistencyScore)) ? `${Math.round(Number(result.consistencyScore))}分` : "已检查";
  elements.consistencyScore.dataset.tone = Number(result.consistencyScore || 0) >= 85 ? "ok" : "warn";
  renderList(elements.consistencyList, result.consistencyNotes, "主译文与第二版本语义一致，未发现明显偏移。");
  const review = result.compliance || {};
  elements.complianceInput.value = result.translation || "";
  renderComplianceReview(review);
  updateComplianceActions();
  elements.copyMainBtn.disabled = !elements.mainOutput.value.trim();
  elements.runtimeState.textContent = `翻译完成 · ${result.model || elements.modelInput.value}`;
}

function historyItems() {
  try {
    const items = JSON.parse(window.localStorage.getItem(TRANSLATION_HISTORY_KEY) || "[]");
    return Array.isArray(items) ? items : [];
  } catch {
    return [];
  }
}

function saveHistory(source, result) {
  const items = historyItems();
  items.unshift({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    source,
    translation: result.translation || "",
    targetLanguage: elements.targetLanguage.value,
    createdAt: new Date().toLocaleString(),
  });
  window.localStorage.setItem(TRANSLATION_HISTORY_KEY, JSON.stringify(items.slice(0, 20)));
  renderHistory();
}

function renderHistory() {
  const items = historyItems();
  elements.historyClearBtn.disabled = !items.length;
  if (!items.length) {
    elements.historyList.innerHTML = '<article class="translation-history-empty"><strong>暂无翻译记录</strong><small>完成翻译后会自动保存最近 20 条。</small></article>';
    return;
  }
  elements.historyList.innerHTML = items.map((item) => `
    <article class="translation-history-item" data-id="${escapeHtml(item.id)}">
      <div><strong>${escapeHtml(item.targetLanguage || "目标语言")}</strong><small>${escapeHtml(item.createdAt || "")}</small></div>
      <p>${escapeHtml(item.translation || "")}</p>
      <div class="material-panel-actions"><button class="mini-action" type="button" data-action="use">回填</button><button class="mini-action" type="button" data-action="copy">复制</button></div>
    </article>
  `).join("");
  elements.historyList.querySelectorAll("[data-id]").forEach((card) => {
    const item = items.find((entry) => entry.id === card.dataset.id);
    card.querySelector('[data-action="use"]').addEventListener("click", () => {
      elements.sourceInput.value = item?.source || "";
      elements.mainOutput.value = item?.translation || "";
      elements.complianceInput.value = item?.translation || "";
      updateComplianceActions();
      updateSourceCount();
      elements.sourceInput.focus();
    });
    card.querySelector('[data-action="copy"]').addEventListener("click", () => navigator.clipboard.writeText(item?.translation || "").then(() => showToast("译文已复制")));
  });
}

async function translatePrompt() {
  const payload = translationPayload();
  if (!payload.text) {
    showToast("请先填写需要翻译的提示词或文案");
    elements.sourceInput.focus();
    return;
  }
  const original = elements.submitBtn.innerHTML;
  elements.submitBtn.disabled = true;
  elements.submitBtn.innerHTML = "翻译中…";
  elements.runtimeState.textContent = "正在翻译与校验";
  try {
    const response = await requestJson("/api/prompt/translate", { method: "POST", body: JSON.stringify(payload) });
    renderResult(response.result || {});
    saveHistory(payload.text, response.result || {});
    showToast("翻译、反译和用词审核已完成");
  } catch (error) {
    elements.runtimeState.textContent = "翻译失败";
    showToast(error.message);
  } finally {
    elements.submitBtn.disabled = false;
    elements.submitBtn.innerHTML = original;
  }
}

async function checkCompliance() {
  const text = elements.complianceInput.value.trim();
  if (!text) {
    showToast("请先填写需要核查的翻译文案");
    elements.complianceInput.focus();
    return;
  }
  const original = elements.complianceCheckBtn.textContent;
  elements.complianceCheckBtn.disabled = true;
  elements.complianceCheckBtn.textContent = "检测中…";
  elements.complianceSummary.textContent = "正在使用 AI 检测 Facebook / TikTok 广告违禁表达…";
  try {
    const response = await requestJson("/api/prompt/compliance-check", {
      method: "POST",
      body: JSON.stringify({
        text,
        targetLanguage: elements.targetLanguage.value,
        market: elements.market.value,
        scene: elements.scene.value,
      }),
    });
    renderComplianceReview(response.result?.compliance || {}, { manual: true });
    showToast("提示词违规检测已完成");
  } catch (error) {
    elements.riskState.textContent = "检测失败";
    elements.riskState.dataset.tone = "error";
    elements.complianceSummary.textContent = error.message || "违规检测失败，请稍后重试。";
    showToast(error.message);
  } finally {
    elements.complianceCheckBtn.textContent = original;
    updateComplianceActions();
  }
}

function updateSourceCount() {
  elements.sourceCount.textContent = `${elements.sourceInput.value.length} / 12000`;
}

function clearWorkspace() {
  elements.sourceInput.value = "";
  elements.mainOutput.value = "";
  elements.altOutput.value = "";
  elements.backOutput.value = "";
  elements.complianceInput.value = "";
  elements.consistencyScore.textContent = "待检查";
  elements.riskState.textContent = "待审核";
  elements.consistencyList.innerHTML = "";
  elements.riskList.innerHTML = "";
  elements.complianceSummary.textContent = "完成翻译后将自动进行首次审核。";
  elements.copyMainBtn.disabled = true;
  updateComplianceActions();
  elements.runtimeState.textContent = "等待翻译";
  updateSourceCount();
}

function fillSample() {
  elements.sourceLanguage.value = "zh-CN";
  elements.targetLanguage.value = "ja-JP";
  elements.market.value = "Japan";
  elements.scene.value = "voiceover";
  elements.tone.value = "natural";
  elements.sourceInput.value = "这款不规则斜扣阔腿牛仔裤是我们店里最受欢迎的款式。高腰设计特别显腿长，宽松裤腿也很遮肉，日常通勤和休闲搭配都很好看。0-3秒展示整体上身效果，3-8秒展示腰头斜扣、口袋和面料细节，最后展示走动时的垂坠感。";
  updateSourceCount();
}

function bindEvents() {
  elements.refreshBtn.addEventListener("click", () => loadConfig());
  elements.configToggleBtn.addEventListener("click", () => {
    const collapsed = elements.configBody.hidden;
    elements.configBody.hidden = !collapsed;
    elements.configToggleBtn.textContent = collapsed ? "收起配置" : "展开配置";
    elements.configToggleBtn.setAttribute("aria-expanded", collapsed ? "true" : "false");
  });
  elements.configSaveBtn.addEventListener("click", () => saveConfig().catch((error) => showToast(error.message)));
  elements.clearKeyBtn.addEventListener("click", () => saveConfig({ clearTranslationApiKey: true }).catch((error) => showToast(error.message)));
  elements.connectivityBtn.addEventListener("click", () => testConfig("connectivity").catch((error) => showToast(error.message)));
  elements.invokeBtn.addEventListener("click", () => testConfig("invoke").catch((error) => showToast(error.message)));
  elements.sourceInput.addEventListener("input", updateSourceCount);
  elements.complianceInput.addEventListener("input", updateComplianceActions);
  elements.sampleBtn.addEventListener("click", fillSample);
  elements.clearBtn.addEventListener("click", clearWorkspace);
  elements.submitBtn.addEventListener("click", translatePrompt);
  elements.complianceCheckBtn.addEventListener("click", checkCompliance);
  elements.complianceCopyPromptBtn.addEventListener("click", () => navigator.clipboard.writeText(buildExternalCompliancePrompt()).then(() => showToast("ChatGPT / Claude 核查指令已复制")));
  elements.copyMainBtn.addEventListener("click", () => navigator.clipboard.writeText(elements.mainOutput.value).then(() => showToast("主译文已复制")));
  elements.historyClearBtn.addEventListener("click", () => {
    window.localStorage.removeItem(TRANSLATION_HISTORY_KEY);
    renderHistory();
    showToast("翻译记录已清空");
  });
}

bindEvents();
updateSourceCount();
updateComplianceActions();
renderHistory();
loadConfig({ silent: true });
