const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const STATUS_LABELS = {
  draft: "草稿",
  ready: "待生成",
  queued: "已排队",
  generating: "生成中",
  completed: "已完成",
  failed: "失败",
};

const ROLE_LABELS = {
  hook: "开头钩子",
  problem: "痛点证据",
  reveal: "产品揭晓",
  detail: "结构细节",
  proof: "上身证明",
  cta: "行动召回",
};

const STEP_ACTIONS = {
  1: "生成分镜",
  2: "审核提示词",
  3: "进入视频生成",
  4: "查看时间线",
  5: "合成最终草稿",
};

const state = {
  projects: [],
  project: null,
  selectedShotId: "",
  activeStep: 1,
  capabilities: {},
  filter: "active",
  query: "",
  saveTimer: null,
  polling: new Map(),
  busy: new Set(),
  imageRequests: new Map(),
  serviceProbes: { ai: null, image: null, ark: null },
  videoPlayerReturnFocus: null,
  inspectorOverride: null,
};

const elements = {
  projectCrumb: $("#project-crumb"),
  serviceStatus: $("#service-status"),
  projectRail: $("#project-rail"),
  projectList: $("#project-list"),
  projectSearch: $("#project-search"),
  emptyProject: $("#empty-project"),
  stageContent: $("#stage-content"),
  workflowSteps: $$(".workflow-step"),
  previousStep: $("#previous-step-button"),
  nextStep: $("#next-step-button"),
  projectName: $("#project-name-input"),
  productName: $("#product-name-input"),
  productDescription: $("#product-description-input"),
  promptSkill: $("#prompt-skill-select"),
  generateSkillPrompts: $("#generate-skill-prompts-button"),
  promptSkillState: $("#prompt-skill-state"),
  promptModelState: $("#prompt-model-state"),
  imageModelState: $("#image-model-state"),
  videoModelState: $("#video-model-state"),
  serviceNodePanel: $("#service-node-panel"),
  serviceNodeModels: $("#service-node-models"),
  serviceNodeSummary: $("#service-node-summary"),
  briefSummary: $("#brief-summary-input"),
  briefAudience: $("#brief-audience-input"),
  sellingPointInput: $("#selling-point-input"),
  sellingPointList: $("#selling-point-list"),
  market: $("#market-select"),
  language: $("#language-select"),
  platform: $("#platform-select"),
  ratio: $("#ratio-select"),
  imageSize: $("#image-size-select"),
  shotCount: $("#shot-count-select"),
  totalDuration: $("#duration-select"),
  style: $("#style-select"),
  bgm: $("#bgm-toggle"),
  onScreenText: $("#text-toggle"),
  capabilityNote: $("#capability-note"),
  generateAllImages: $("#generate-all-images-button"),
  storyboardGrid: $("#storyboard-grid"),
  storyboardSource: $("#storyboard-source"),
  referenceQuickbar: $("#reference-quickbar"),
  quickReferenceShot: $("#quick-reference-shot"),
  quickReferenceImageCount: $("#quick-reference-image-count"),
  quickReferenceVideoCount: $("#quick-reference-video-count"),
  quickUploadReference: $("#quick-upload-reference-button"),
  quickUploadReferenceVideo: $("#quick-upload-reference-video-button"),
  manageReference: $("#manage-reference-button"),
  directionLedger: $("#direction-ledger"),
  generationBoard: $("#generation-board"),
  finalPreview: $("#final-preview"),
  inspectorEmpty: $("#inspector-empty"),
  inspectorContent: $("#inspector-content"),
  inspectorShotLabel: $("#inspector-shot-label"),
  inspectorStatus: $("#inspector-status"),
  inspectorPreview: $("#inspector-preview"),
  inspectorCollapse: $("#inspector-collapse-button"),
  inspectorReopen: $("#inspector-reopen-button"),
  shotTitle: $("#shot-title-input"),
  shotRole: $("#shot-role-select"),
  shotDuration: $("#shot-duration-select"),
  shotScene: $("#shot-scene-input"),
  shotCamera: $("#shot-camera-input"),
  shotImagePrompt: $("#shot-image-prompt-input"),
  imageGenerationMode: $("#image-generation-mode-select"),
  imageGenerationReferenceState: $("#image-generation-reference-state"),
  shotPrompt: $("#shot-prompt-input"),
  shotCopy: $("#shot-copy-input"),
  generationMode: $("#generation-mode-select"),
  referencePrivacyMode: $("#reference-privacy-mode-select"),
  shotReferenceInput: $("#shot-reference-input"),
  shotReferenceVideoInput: $("#shot-reference-video-input"),
  referenceOverview: $("#reference-overview"),
  referenceImageCount: $("#reference-image-count"),
  referenceVideoCount: $("#reference-video-count"),
  referenceImageList: $("#reference-image-list"),
  referenceVideoList: $("#reference-video-list"),
  referenceState: $("#reference-state"),
  referenceWorkbench: $("#reference-workbench"),
  generateImage: $("#generate-image-button"),
  shotError: $("#shot-error"),
  timelineTrack: $("#timeline-track"),
  overallProgressBar: $("#overall-progress-bar"),
  overallProgressText: $("#overall-progress-text"),
  saveState: $("#save-state"),
  primaryAction: $("#primary-action-button"),
  toastStack: $("#toast-stack"),
  backdrop: $("#modal-backdrop"),
  taskConfirmDialog: $("#task-confirm-dialog"),
  taskConfirmEyebrow: $("#task-confirm-eyebrow"),
  taskConfirmTitle: $("#task-confirm-title"),
  taskConfirmMessage: $("#task-confirm-message"),
  taskConfirmFacts: $("#task-confirm-facts"),
  taskConfirmAccept: $("#task-confirm-accept"),
  videoPlayerModal: $("#video-player-modal"),
  videoPlayerVideo: $("#video-player-video"),
  videoPlayerShot: $("#video-player-shot"),
  videoPlayerTitle: $("#video-player-title"),
  videoPlayerError: $("#video-player-error"),
  videoPlayerClose: $("#video-player-close"),
  videoPlayerOpen: $("#video-player-open"),
  videoPlayerDownload: $("#video-player-download"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toast(message, tone = "info") {
  const item = document.createElement("div");
  item.className = `toast ${tone}`;
  item.textContent = String(message || "操作完成");
  elements.toastStack.append(item);
  window.setTimeout(() => item.remove(), 4200);
}

function confirmTaskBatch({ eyebrow = "TASK REVIEW", title, message, facts = [], confirmText = "确认继续" }) {
  if (!elements.taskConfirmDialog?.showModal) return Promise.resolve(window.confirm(`${title}\n\n${message}`));
  if (elements.taskConfirmDialog.open) elements.taskConfirmDialog.close("cancel");
  elements.taskConfirmEyebrow.textContent = eyebrow;
  elements.taskConfirmTitle.textContent = title;
  elements.taskConfirmMessage.textContent = message;
  elements.taskConfirmFacts.innerHTML = facts.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>`).join("");
  elements.taskConfirmAccept.textContent = confirmText;
  return new Promise((resolve) => {
    elements.taskConfirmDialog.addEventListener("close", () => resolve(elements.taskConfirmDialog.returnValue === "confirm"), { once: true });
    elements.taskConfirmDialog.showModal();
  });
}

async function requestJson(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(url, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401) {
    window.location.replace(`/login.html?next=${encodeURIComponent(window.location.pathname)}`);
    throw new Error("登录状态已失效。");
  }
  if (!response.ok || payload.ok === false) throw new Error(payload.error || `请求失败：${response.status}`);
  return payload;
}

function setBusy(key, busy) {
  if (busy) state.busy.add(key);
  else state.busy.delete(key);
  renderPrimaryAction();
}

function createImageRequestId() {
  const randomPart = typeof globalThis.crypto?.randomUUID === "function"
    ? globalThis.crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `img-${randomPart}`;
}

function taskIdFrom(task) {
  return task?.id || task?.task_id || task?.taskId || task?.data?.id || task?.data?.task_id || "";
}

function taskStatus(task) {
  return String(task?.status || task?.data?.status || "submitted").toLowerCase();
}

function taskError(task) {
  const queue = [task];
  const seen = new Set();
  while (queue.length) {
    const current = queue.shift();
    if (!current || seen.has(current)) continue;
    if (typeof current === "object") seen.add(current);
    if (Array.isArray(current)) { queue.push(...current); continue; }
    if (typeof current === "object") {
      for (const [key, value] of Object.entries(current)) {
        if (/error|message|reason|detail|msg/i.test(key) && typeof value === "string" && value.trim()) return value.trim();
        if (value && typeof value === "object") queue.push(value);
      }
    }
  }
  return "视频生成失败。";
}

function findVideoUrl(value) {
  const queue = [value];
  const seen = new Set();
  while (queue.length) {
    const current = queue.shift();
    if (!current || seen.has(current)) continue;
    if (typeof current === "object") seen.add(current);
    if (typeof current === "string") {
      if (/^https?:\/\//i.test(current) && /\.(mp4|mov|webm|m4v)(\?|$)/i.test(current)) return current;
      continue;
    }
    if (Array.isArray(current)) { queue.push(...current); continue; }
    if (typeof current === "object") {
      for (const [key, item] of Object.entries(current)) {
        if (/video|output|url/i.test(key) && typeof item === "string" && /^https?:\/\//i.test(item)) return item;
        if (item && typeof item === "object") queue.push(item);
      }
    }
  }
  return "";
}

function selectedShot() {
  return state.project?.shots?.find((shot) => shot.id === state.selectedShotId) || state.project?.shots?.[0] || null;
}

function replaceProject(project, projects = null) {
  state.project = project;
  if (projects) state.projects = projects;
  else {
    const index = state.projects.findIndex((item) => item.id === project.id);
    if (index >= 0) state.projects[index] = project;
    else state.projects.unshift(project);
  }
  if (!project.shots?.some((shot) => shot.id === state.selectedShotId)) state.selectedShotId = project.shots?.[0]?.id || "";
  state.activeStep = Number(project.currentStep || state.activeStep || 1);
  render();
  resumePolling();
}

async function loadProjects(includeArchived = false) {
  const payload = await requestJson(`/api/ad-forge/projects${includeArchived ? "?archived=1" : ""}`);
  state.projects = payload.projects || [];
  state.capabilities = payload.capabilities || {};
  const remembered = window.sessionStorage.getItem("sosove-ad-lab-project");
  state.project = state.projects.find((item) => item.id === remembered) || state.projects[0] || null;
  state.activeStep = Number(state.project?.currentStep || 1);
  state.selectedShotId = state.project?.shots?.[0]?.id || "";
  render();
  resumePolling();
}

async function createProject() {
  setBusy("create", true);
  try {
    const payload = await requestJson("/api/ad-forge/projects", {
      method: "POST",
      body: JSON.stringify({ name: "新广告项目", shotCount: 4, totalDuration: 20 }),
    });
    state.filter = "active";
    replaceProject(payload.project, payload.projects);
    window.sessionStorage.setItem("sosove-ad-lab-project", payload.project.id);
    setStep(1, false);
    toast("项目已创建，先填写真实商品信息。", "success");
    window.setTimeout(() => elements.projectName.focus(), 100);
  } catch (error) {
    toast(error.message, "error");
  } finally {
    setBusy("create", false);
  }
}

function projectChangesFromForm() {
  return {
    name: elements.projectName.value,
    productName: elements.productName.value,
    productDescription: elements.productDescription.value,
    brief: {
      summary: elements.briefSummary.value,
      audience: elements.briefAudience.value,
      sellingPoints: state.project?.brief?.sellingPoints || [],
    },
    settings: {
      ...(state.project?.settings || {}),
      market: elements.market.value,
      language: elements.language.value,
      platform: elements.platform.value,
      ratio: elements.ratio.value,
      imageSize: elements.imageSize.value,
      shotCount: Number(elements.shotCount.value),
      totalDuration: Number(elements.totalDuration.value),
      style: elements.style.value,
      bgm: elements.bgm.checked,
      onScreenText: elements.onScreenText.checked,
    },
  };
}

async function saveProject(changes = null, quiet = false) {
  if (!state.project) return null;
  elements.saveState.textContent = "保存中";
  try {
    const payload = await requestJson("/api/ad-forge/projects/update", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id, changes: changes || projectChangesFromForm() }),
    });
    replaceProject(payload.project, payload.projects);
    elements.saveState.textContent = "已同步";
    if (!quiet) toast("项目已保存。", "success");
    return payload.project;
  } catch (error) {
    elements.saveState.textContent = "保存失败";
    if (!quiet) toast(error.message, "error");
    throw error;
  }
}

function queueProjectSave() {
  if (!state.project) return;
  elements.saveState.textContent = "待保存";
  window.clearTimeout(state.saveTimer);
  state.saveTimer = window.setTimeout(() => saveProject(null, true).catch(() => {}), 650);
}

function bindFormToState() {
  if (!state.project) return;
  const requestedShotCount = Number(elements.shotCount.value);
  const minimumDuration = requestedShotCount * 5;
  if (Number(elements.totalDuration.value) < minimumDuration) {
    if (![...elements.totalDuration.options].some((option) => Number(option.value) === minimumDuration)) {
      elements.totalDuration.add(new Option(`${minimumDuration} 秒`, String(minimumDuration)));
    }
    elements.totalDuration.value = String(minimumDuration);
    toast(`${requestedShotCount} 个镜头至少需要 ${minimumDuration} 秒，已自动调整。`, "info");
  }
  state.project.name = elements.projectName.value;
  state.project.productName = elements.productName.value;
  state.project.productDescription = elements.productDescription.value;
  state.project.brief.summary = elements.briefSummary.value;
  state.project.brief.audience = elements.briefAudience.value;
  Object.assign(state.project.settings, {
    market: elements.market.value,
    language: elements.language.value,
    platform: elements.platform.value,
    ratio: elements.ratio.value,
    imageSize: elements.imageSize.value,
    shotCount: requestedShotCount,
    totalDuration: Number(elements.totalDuration.value),
    style: elements.style.value,
    bgm: elements.bgm.checked,
    onScreenText: elements.onScreenText.checked,
  });
  elements.projectCrumb.textContent = state.project.name || "未命名广告项目";
  queueProjectSave();
}

function addSellingPoint() {
  if (!state.project) return;
  const value = elements.sellingPointInput.value.trim();
  if (!value) return;
  const points = state.project.brief.sellingPoints || [];
  if (!points.includes(value)) points.push(value);
  state.project.brief.sellingPoints = points.slice(0, 10);
  elements.sellingPointInput.value = "";
  renderSellingPoints();
  queueProjectSave();
}

function removeSellingPoint(index) {
  state.project.brief.sellingPoints.splice(index, 1);
  renderSellingPoints();
  queueProjectSave();
}

function stepCompletionState(step) {
  const project = state.project;
  if (!project) return "pending";
  const shots = (project.shots || []).filter((shot) => !shot.excluded);
  const hasFacts = Boolean(project.productName?.trim() || project.productDescription?.trim() || project.brief?.summary?.trim());
  if (step === 1) return hasFacts && shots.length ? "done" : "pending";
  if (step === 2) return shots.length && shots.every((shot) => shot.imagePrompt?.trim() || shot.referenceImage) ? "done" : "pending";
  if (step === 3) return shots.length && shots.every((shot) => shot.prompt?.trim()) ? "done" : "pending";
  if (step === 4) {
    if (shots.length && shots.every((shot) => shot.videoUrl)) return "done";
    if (shots.some((shot) => shot.videoUrl || shot.status === "failed" || shot.status === "generating" || shot.status === "queued")) return "warning";
    return "pending";
  }
  if (step === 5) return project.finalVideoUrl ? "done" : shots.some((shot) => shot.videoUrl) ? "warning" : "pending";
  return "pending";
}

function syncInspectorContext(step = state.activeStep) {
  const contextualCollapse = Number(step) === 1 || Number(step) === 5;
  if (window.innerWidth <= 1080) {
    document.body.classList.remove("inspector-collapsed");
    if (state.inspectorOverride !== "open" && contextualCollapse) document.body.classList.remove("inspector-open");
    return;
  }
  const collapsed = state.inspectorOverride === "collapsed" || (state.inspectorOverride !== "open" && contextualCollapse);
  document.body.classList.toggle("inspector-collapsed", collapsed);
  document.body.classList.remove("inspector-open");
}

function setStep(step, persist = true) {
  const next = Math.max(1, Math.min(5, Number(step || 1)));
  if (!state.project) return;
  const changed = next !== state.activeStep;
  if (changed) state.inspectorOverride = null;
  state.activeStep = next;
  state.project.currentStep = next;
  $$(".stage-panel").forEach((panel) => panel.classList.toggle("is-active", Number(panel.dataset.stagePanel) === next));
  elements.workflowSteps.forEach((button) => {
    const number = Number(button.dataset.step);
    const completion = stepCompletionState(number);
    button.classList.toggle("is-active", number === next);
    button.classList.toggle("is-done", completion === "done");
    button.classList.toggle("is-warning", completion === "warning");
  });
  elements.previousStep.disabled = next === 1;
  elements.nextStep.disabled = next === 5;
  if (changed && elements.stageContent) elements.stageContent.scrollTop = 0;
  syncInspectorContext(next);
  renderPrimaryAction();
  if (persist) saveProject({ currentStep: next }, true).catch(() => {});
}

async function generateStoryboard(forceFallback = false) {
  if (!state.project) return;
  if (!elements.productName.value.trim() && !elements.briefSummary.value.trim()) {
    setStep(1, false);
    toast("至少填写商品名称或广告简述。", "error");
    return;
  }
  setBusy("storyboard", true);
  try {
    await saveProject(null, true);
    const payload = await requestJson("/api/ad-forge/storyboard", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id, forceFallback }),
    });
    replaceProject(payload.project, payload.projects);
    setStep(2, false);
    toast(payload.project.warning || "分镜已生成，可以逐镜审核。", payload.project.warning ? "info" : "success");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    setBusy("storyboard", false);
  }
}

async function generateSkillPrompts() {
  if (!state.project || state.busy.has("skill-prompts")) return;
  if (!elements.productDescription.value.trim()) {
    setStep(1, false);
    elements.productDescription.focus();
    toast("请先填写产品描述，再交给 Seedance Skill 生成提示词。", "error");
    return;
  }
  const skill = state.capabilities.promptSkill || {};
  if (!skill.exists || !state.capabilities.ai) {
    toast(!skill.exists ? "本机 Seedance Skill 未安装。" : "AI 提示词模型尚未配置。", "error");
    return;
  }
  setBusy("skill-prompts", true);
  elements.generateSkillPrompts.disabled = true;
  elements.generateSkillPrompts.textContent = "⚡ Skill 正在编排…";
  elements.promptSkillState.textContent = "正在生成每镜图片提示词与视频提示词";
  try {
    await saveProject(null, true);
    const payload = await requestJson("/api/ad-forge/skill/generate-prompts", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id, skill: elements.promptSkill.value }),
    });
    replaceProject(payload.project, payload.projects);
    state.selectedShotId = payload.project.shots?.[0]?.id || "";
    setStep(2, false);
    toast(`Seedance Skill 已生成 ${payload.project.shots?.length || 0} 组图片与视频提示词。`, "success");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    setBusy("skill-prompts", false);
    elements.generateSkillPrompts.textContent = "⚡ Skill 生成双提示词";
    renderBrief();
  }
}

function chooseShot(shotId, openInspector = false) {
  state.selectedShotId = shotId;
  renderStoryboard();
  renderDirectionLedger();
  renderGenerationBoard();
  renderTimeline();
  renderInspector();
  if (openInspector || window.innerWidth <= 1080) openInspectorDrawer();
}

function readInspectorChanges() {
  return {
    title: elements.shotTitle.value,
    role: elements.shotRole.value,
    duration: Number(elements.shotDuration.value),
    scene: elements.shotScene.value,
    camera: elements.shotCamera.value,
    imagePrompt: elements.shotImagePrompt.value,
    imageGenerationMode: elements.imageGenerationMode.value,
    prompt: elements.shotPrompt.value,
    copy: elements.shotCopy.value,
    generationMode: elements.generationMode.value,
    referencePrivacyMode: elements.referencePrivacyMode.value,
  };
}

async function saveShot(changes = null, quiet = false) {
  const shot = selectedShot();
  if (!shot || !state.project) return null;
  try {
    const payload = await requestJson("/api/ad-forge/shots/update", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id, shotId: shot.id, changes: changes || readInspectorChanges() }),
    });
    replaceProject(payload.project, payload.projects);
    if (!quiet) toast("镜头已保存。", "success");
    return payload.project.shots.find((item) => item.id === shot.id);
  } catch (error) {
    if (!quiet) toast(error.message, "error");
    throw error;
  }
}

function referenceImageUrls(shot) {
  return [...new Set([shot?.referenceImage, ...(shot?.referenceAssets || [])].filter(Boolean))].slice(0, 9);
}

function projectReferenceImageUrls() {
  return [...new Set((state.project?.referenceAssets || []).filter(Boolean))].slice(0, 12);
}

function effectiveReferenceImageUrls(shot) {
  return [...new Set([...referenceImageUrls(shot), ...projectReferenceImageUrls()])];
}

function videoReferenceImageUrls(shot) {
  return [...new Set([...sourceReferenceImageUrls(shot), ...effectiveReferenceImageUrls(shot)])].slice(0, 9);
}

function isGeneratedReferenceImage(url) {
  try {
    return new URL(url, window.location.origin).pathname.includes("/ad-forge-images/");
  } catch (_error) {
    return false;
  }
}

function imageEditReferenceUrls(shot) {
  const references = effectiveReferenceImageUrls(shot);
  const sourceReferences = sourceReferenceImageUrls(shot);
  return (sourceReferences.length ? sourceReferences : references).slice(0, 4);
}

function sourceReferenceImageUrls(shot) {
  return effectiveReferenceImageUrls(shot).filter((url) => !isGeneratedReferenceImage(url)).slice(0, 4);
}

async function toggleProjectReferenceImage(url) {
  if (!state.project || isGeneratedReferenceImage(url)) return;
  const current = projectReferenceImageUrls();
  const isGlobal = current.includes(url);
  const referenceAssets = isGlobal ? current.filter((item) => item !== url) : [...current, url].slice(0, 12);
  const changes = { referenceAssets };
  if (!isGlobal) {
    changes.shots = (state.project.shots || []).map((shot) => ({ ...shot, imageGenerationMode: "reference" }));
  }
  await saveProject(changes, true);
  toast(isGlobal ? "已取消全片商品参考；镜头仍保持强制参考，缺图时会阻止生成。" : "已设为全片商品参考，并为所有镜头启用强制参考。", "success");
}

function referenceVideoDurationMs(shot) {
  return (shot?.referenceVideos || []).reduce((total, item) => total + Math.max(0, Number(item?.durationMs || 0)), 0);
}

function formatReferenceDuration(durationMs) {
  const seconds = Math.max(0, Number(durationMs || 0)) / 1000;
  return Number.isInteger(seconds) ? `${seconds}s` : `${seconds.toFixed(1)}s`;
}

function friendlyShotError(value) {
  const text = String(value || "");
  const lower = text.toLowerCase();
  if (lower.includes("inputimagesensitivecontentdetected.privacyinformation") || lower.includes("may contain real person")) {
    return "Seedance 拒绝了含真人脸的普通参考图。当前已启用商品隐私模式，请点击“修复后重试”；需要保留真人身份时，必须使用火山方舟已授权的 Asset ID。";
  }
  if (lower.includes("resource download failed") && lower.includes("image_url")) {
    return "Seedance 无法下载旧的本机参考图。当前已改为服务端自动内嵌，请点击“修复后重试”。";
  }
  return text;
}

async function uploadReferenceImages() {
  const shot = selectedShot();
  const current = referenceImageUrls(shot);
  const remaining = Math.max(0, 9 - current.length);
  const files = Array.from(elements.shotReferenceInput.files || []).slice(0, remaining);
  if (!shot || !files.length) {
    if (shot && remaining === 0) toast("当前镜头已经有 9 张参考图。", "info");
    elements.shotReferenceInput.value = "";
    return;
  }
  const formData = new FormData();
  files.forEach((file) => formData.append("images", file));
  elements.referenceState.textContent = `正在上传 ${files.length} 张参考图……`;
  try {
    const payload = await requestJson("/api/uploads/images", { method: "POST", body: formData });
    const materials = payload.images || payload.items || [];
    const urls = materials.map((material) => material?.url && new URL(material.url, window.location.origin).href).filter(Boolean);
    if (!urls.length) throw new Error("上传成功但没有返回图片 URL。");
    const referenceAssets = [...new Set([...current, ...urls])].slice(0, 9);
    const hasPrimary = Boolean(shot.referenceImage);
    await saveShot({
      referenceImage: shot.referenceImage || urls[0],
      referenceAssets,
      imageGenerationMode: "reference",
      referenceImageSource: hasPrimary ? shot.referenceImageSource : "uploaded",
      imageModel: hasPrimary ? shot.imageModel : "",
      imageGeneratedAt: hasPrimary ? shot.imageGeneratedAt : "",
      imageError: "",
    }, true);
    toast(`已添加 ${urls.length} 张参考图，当前镜头已启用强制商品参考。${payload.warning ? ` ${payload.warning}` : ""}`, payload.warning ? "info" : "success");
  } catch (error) {
    elements.referenceState.textContent = "参考图上传失败";
    toast(error.message, "error");
  } finally {
    elements.shotReferenceInput.value = "";
  }
}

async function uploadReferenceVideos() {
  const shot = selectedShot();
  const current = shot?.referenceVideos || [];
  const remaining = Math.max(0, 3 - current.length);
  const files = Array.from(elements.shotReferenceVideoInput.files || []).slice(0, remaining);
  if (!shot || !files.length) {
    if (shot && remaining === 0) toast("当前镜头已经有 3 个参考视频。", "info");
    elements.shotReferenceVideoInput.value = "";
    return;
  }
  const formData = new FormData();
  files.forEach((file) => formData.append("videos", file));
  elements.referenceState.textContent = `正在上传 ${files.length} 个参考视频……`;
  try {
    const payload = await requestJson("/api/uploads/videos", { method: "POST", body: formData });
    const materials = payload.videos || payload.items || [];
    const uploaded = materials.map((material) => ({
      url: material?.url ? new URL(material.url, window.location.origin).href : "",
      name: material?.name || "参考视频",
      durationMs: Number(material?.technical?.durationMs || 0),
      contentType: material?.contentType || "",
    })).filter((item) => item.url);
    if (!uploaded.length) throw new Error("上传成功但没有返回视频 URL。");
    if (uploaded.some((item) => item.durationMs <= 0)) throw new Error("无法读取参考视频时长，请转换为 MP4 后重试。");
    const referenceVideos = [...current, ...uploaded].slice(0, 3);
    const totalDurationMs = referenceVideos.reduce((total, item) => total + Number(item.durationMs || 0), 0);
    if (totalDurationMs > 15000) throw new Error(`参考视频总时长为 ${formatReferenceDuration(totalDurationMs)}，最多允许 15s。`);
    await saveShot({ referenceVideos }, true);
    toast(`已添加 ${uploaded.length} 个参考视频。${payload.warning ? ` ${payload.warning}` : ""}`, payload.warning ? "info" : "success");
  } catch (error) {
    elements.referenceState.textContent = "参考视频上传失败";
    toast(error.message, "error");
  } finally {
    elements.shotReferenceVideoInput.value = "";
  }
}

async function removeReferenceImage(url) {
  const shot = selectedShot();
  if (!shot) return;
  const referenceAssets = referenceImageUrls(shot).filter((item) => item !== url);
  const changes = { referenceAssets };
  if (shot.referenceImage === url) {
    changes.referenceImage = referenceAssets[0] || "";
    changes.referenceImageSource = referenceAssets.length ? "uploaded" : "";
    changes.imageModel = "";
    changes.imageGeneratedAt = "";
    changes.imageGenerationRoute = "";
    changes.imageReferenceCount = 0;
    changes.imageReferenceAssets = [];
    changes.imageError = "";
  }
  await saveShot(changes, true);
  toast(projectReferenceImageUrls().includes(url) ? "已从当前镜头移除；全片商品参考仍然保留。" : "已从当前镜头移除参考图。", "success");
}

async function removeReferenceVideo(url) {
  const shot = selectedShot();
  if (!shot) return;
  await saveShot({ referenceVideos: (shot.referenceVideos || []).filter((item) => item.url !== url) }, true);
  toast("参考视频已移除。", "success");
}

async function generateImage(shotId, { quiet = false } = {}) {
  const shot = state.project?.shots?.find((item) => item.id === shotId);
  const busyKey = `image:${shotId}`;
  if (!shot || state.busy.has(busyKey)) return false;
  if (!state.capabilities.imageGeneration) {
    if (!quiet) toast("生图服务尚未配置。", "error");
    return false;
  }
  if (shot.imageGenerationMode === "reference" && sourceReferenceImageUrls(shot).length === 0) {
    chooseShot(shot.id, true);
    if (!quiet) toast("当前镜头启用了强制参考，但没有原始商品图。请先上传或设为全片参考。", "error");
    return false;
  }
  if (!shot.imagePrompt?.trim() && !shot.prompt?.trim() && !shot.scene?.trim()) {
    chooseShot(shot.id, true);
    if (!quiet) toast("请先生成分镜或填写场景描述。", "error");
    return false;
  }
  if (shot.id === state.selectedShotId) {
    try {
      await saveShot(null, true);
    } catch (error) {
      if (!quiet) toast(error.message, "error");
      return false;
    }
  }
  const requestState = {
    requestId: createImageRequestId(),
    projectId: state.project.id,
    controller: new AbortController(),
    cancelled: false,
    cancelling: false,
  };
  state.imageRequests.set(shotId, requestState);
  setBusy(busyKey, true);
  renderStoryboard();
  renderInspector();
  try {
    const payload = await requestJson("/api/ad-forge/images/generate", {
      method: "POST",
      signal: requestState.controller.signal,
      body: JSON.stringify({
        projectId: requestState.projectId,
        shotId: shot.id,
        requestId: requestState.requestId,
      }),
    });
    replaceProject(payload.project, payload.projects);
    if (!quiet) toast(`SHOT ${String(shot.order).padStart(2, "0")} 关键帧已生成。`, "success");
    return true;
  } catch (error) {
    if (requestState.cancelled) return false;
    if (!quiet) toast(error.message, "error");
    await loadProjects(false).catch(() => {});
    return false;
  } finally {
    if (state.imageRequests.get(shotId) === requestState) state.imageRequests.delete(shotId);
    setBusy(busyKey, false);
    renderStoryboard();
    renderInspector();
  }
}

async function cancelImage(shotId) {
  const requestState = state.imageRequests.get(shotId);
  if (!requestState || requestState.cancelling) return false;
  requestState.cancelling = true;
  renderStoryboard();
  renderInspector();
  try {
    const payload = await requestJson("/api/ad-forge/images/cancel", {
      method: "POST",
      body: JSON.stringify({
        projectId: requestState.projectId,
        shotId,
        requestId: requestState.requestId,
      }),
    });
    if (!payload.cancelled) {
      requestState.cancelling = false;
      renderStoryboard();
      renderInspector();
      toast("这次生图已经结束，无法再取消。", "info");
      return false;
    }
    requestState.cancelled = true;
    requestState.controller.abort();
    toast("已取消等待；服务商已开始的计算可能仍会产生费用，但结果不会保存。", "info");
    return true;
  } catch (error) {
    requestState.cancelling = false;
    renderStoryboard();
    renderInspector();
    toast(`取消失败：${error.message}`, "error");
    return false;
  }
}

async function generateAllImages() {
  if (state.busy.has("generate-all-images")) return;
  if (!state.capabilities.imageGeneration) {
    toast("生图服务尚未配置。", "error");
    return;
  }
  const shots = state.project?.shots?.filter((shot) => !shot.excluded && shot.referenceImageSource !== "generated" && (shot.imagePrompt?.trim() || shot.prompt?.trim() || shot.scene?.trim())) || [];
  if (!shots.length) {
    toast("没有待生成的关键帧；已有图片可在单镜中选择重绘。", "info");
    return;
  }
  const imageSizeLabel = elements.imageSize?.options[elements.imageSize.selectedIndex]?.text || "跟随项目画幅";
  const confirmed = await confirmTaskBatch({
    eyebrow: "IMAGE BATCH",
    title: `生成 ${shots.length} 张关键帧？`,
    message: "系统会逐镜提交图片任务。每个模型请求可能产生费用，已有 AI 关键帧不会重复生成。",
    facts: [["任务数量", `${shots.length} 张`], ["图片尺寸", imageSizeLabel], ["参考策略", "按每镜当前设置"]],
    confirmText: `确认生成 ${shots.length} 张`,
  });
  if (!confirmed) return;
  setBusy("generate-all-images", true);
  renderStoryboard();
  let completed = 0;
  try {
    for (const shot of shots) {
      if (await generateImage(shot.id, { quiet: true })) completed += 1;
    }
    toast(`关键帧批量生成完成：${completed}/${shots.length}。`, completed === shots.length ? "success" : "info");
  } finally {
    setBusy("generate-all-images", false);
    renderStoryboard();
    renderInspector();
  }
}

async function reorderShots(ids) {
  if (!state.project) return;
  try {
    const payload = await requestJson("/api/ad-forge/shots/reorder", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id, shotIds: ids }),
    });
    replaceProject(payload.project, payload.projects);
    toast("分镜顺序已更新。", "success");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function generateShot(shotId) {
  const shot = state.project?.shots?.find((item) => item.id === shotId);
  if (!shot || state.busy.has(`shot:${shot.id}`)) return;
  if (!shot.prompt?.trim()) {
    chooseShot(shot.id, true);
    toast("请先填写这一镜的视频提示词。", "error");
    return;
  }
  setBusy(`shot:${shot.id}`, true);
  try {
    if (shot.id === state.selectedShotId) await saveShot(null, true);
    const refreshed = state.project.shots.find((item) => item.id === shot.id) || shot;
    const useReferences = refreshed.generationMode !== "prompt-only";
    const refs = useReferences ? videoReferenceImageUrls(refreshed) : [];
    const referencePrivacyMode = ["product-only", "direct"].includes(refreshed.referencePrivacyMode)
      ? refreshed.referencePrivacyMode
      : "product-only";
    const submissionPrompt = useReferences && refs.length && referencePrivacyMode === "product-only"
      ? `The reference images control only the garment, product construction, material, color and silhouette. Faces are intentionally removed for privacy. Generate a new original adult model identity; do not reproduce any referenced person and do not show a privacy mask in the output.\n\n${refreshed.prompt}`
      : refreshed.prompt;
    const videoReferences = useReferences ? (refreshed.referenceVideos || []).slice(0, 3) : [];
    const duration = [5, 10, 11, 15].includes(Number(refreshed.duration)) ? Number(refreshed.duration) : 5;
    const result = await requestJson("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        projectId: state.project.id,
        prompt: submissionPrompt,
        ratio: state.project.settings.ratio,
        duration,
        quantity: 1,
        model: state.project.settings.model,
        refImages: refs,
        referencePrivacyMode,
        refVideos: videoReferences.map((item) => item.url),
        refVideoDurationsMs: videoReferences.map((item) => Number(item.durationMs || 0)),
        refAudios: [],
        generateAudio: Boolean(state.project.settings.generateAudio),
        watermark: false,
      }),
    });
    const task = result.task || result.tasks?.[0];
    const taskId = taskIdFrom(task);
    if (!taskId) throw new Error("视频服务没有返回任务 ID。");
    await saveShot({ taskId, status: "generating", error: "", videoUrl: "" }, true);
    toast(`SHOT ${String(refreshed.order).padStart(2, "0")} 已提交。`, "success");
    startPollingShot(refreshed.id, taskId);
  } catch (error) {
    await saveShot({ status: "failed", error: error.message }, true).catch(() => {});
    toast(error.message, "error");
  } finally {
    setBusy(`shot:${shot.id}`, false);
  }
}

async function generateAll() {
  const shots = state.project?.shots?.filter((shot) => !shot.excluded && shot.prompt && !shot.videoUrl && !["queued", "generating"].includes(shot.status)) || [];
  if (!shots.length) {
    toast("没有待提交的镜头。", "info");
    return;
  }
  const requestedDuration = shots.reduce((total, shot) => total + Math.max(0, Number(shot.duration || 0)), 0);
  const confirmed = await confirmTaskBatch({
    eyebrow: "VIDEO BATCH",
    title: `提交 ${shots.length} 个视频任务？`,
    message: "视频任务会逐镜提交到 Seedance，并可能产生模型费用。失败镜头不会阻塞其他镜头。",
    facts: [["任务数量", `${shots.length} 镜`], ["请求总时长", `${requestedDuration} 秒`], ["提交方式", "逐镜独立任务"]],
    confirmText: `确认提交 ${shots.length} 镜`,
  });
  if (!confirmed) return;
  setBusy("generate-all", true);
  try {
    for (const shot of shots) await generateShot(shot.id);
  } finally {
    setBusy("generate-all", false);
  }
}

function startPollingShot(shotId, taskId) {
  const key = `${state.project?.id}:${shotId}`;
  if (state.polling.has(key)) window.clearInterval(state.polling.get(key));
  const poll = () => pollShot(shotId, taskId, key);
  const timer = window.setInterval(poll, 8000);
  state.polling.set(key, timer);
  poll();
}

async function pollShot(shotId, taskId, key) {
  if (!state.project?.shots?.some((shot) => shot.id === shotId)) return;
  try {
    const payload = await requestJson(`/api/tasks/${encodeURIComponent(taskId)}`);
    const status = taskStatus(payload.task);
    const videoUrl = findVideoUrl(payload.task);
    if (videoUrl || status === "succeeded") {
      if (!videoUrl) return;
      stopPollingKey(key);
      await saveShot({ status: "completed", videoUrl, error: "" }, true);
      toast("一个镜头已生成完成。", "success");
      return;
    }
    if (["failed", "canceled", "cancelled"].includes(status)) {
      stopPollingKey(key);
      await saveShot({ status: "failed", error: taskError(payload.task) }, true);
      toast("一个镜头生成失败，已保留错误信息。", "error");
      return;
    }
    const shot = state.project.shots.find((item) => item.id === shotId);
    if (shot && shot.status !== "generating") await saveShot({ status: "generating" }, true);
  } catch (error) {
    console.warn("Ad Lab poll failed", error);
  }
}

function stopPollingKey(key) {
  if (!state.polling.has(key)) return;
  window.clearInterval(state.polling.get(key));
  state.polling.delete(key);
}

function resumePolling() {
  if (!state.project) return;
  state.project.shots.forEach((shot) => {
    if (shot.taskId && ["queued", "generating"].includes(shot.status)) startPollingShot(shot.id, shot.taskId);
  });
}

async function composeProject() {
  if (!state.project) return;
  const eligibleShots = state.project.shots.filter((shot) => !shot.excluded);
  const availableShots = eligibleShots.filter((shot) => shot.videoUrl);
  if (!availableShots.length) {
    toast("至少需要一个已生成的视频片段。", "error");
    return;
  }
  if (availableShots.length < eligibleShots.length) {
    const confirmed = await confirmTaskBatch({
      eyebrow: "PARTIAL TIMELINE",
      title: `仅合成 ${availableShots.length}/${eligibleShots.length} 个片段？`,
      message: "尚未成功的镜头不会进入本次草稿。它们会继续保留，可以稍后修复并重新合成。",
      facts: [["可用片段", `${availableShots.length} 个`], ["暂不包含", `${eligibleShots.length - availableShots.length} 个`], ["成片时长", `${availableShots.reduce((total, shot) => total + Number(shot.duration || 0), 0)} 秒`]],
      confirmText: "确认合成可用片段",
    });
    if (!confirmed) return;
  }
  setBusy("compose", true);
  try {
    const payload = await requestJson("/api/ad-forge/compose", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id }),
    });
    replaceProject(payload.project, payload.projects);
    setStep(5, false);
    toast("草稿已合成，可以预览和下载。", "success");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    setBusy("compose", false);
  }
}

async function archiveCurrentProject() {
  if (!state.project) return;
  try {
    const payload = await requestJson("/api/ad-forge/projects/archive", {
      method: "POST",
      body: JSON.stringify({ projectId: state.project.id, archived: true }),
    });
    state.projects = payload.projects || [];
    state.project = state.projects[0] || null;
    state.selectedShotId = state.project?.shots?.[0]?.id || "";
    render();
    toast("项目已归档。", "success");
  } catch (error) {
    toast(error.message, "error");
  }
}

function render() {
  renderCapabilities();
  renderProjectList();
  const hasProject = Boolean(state.project);
  elements.emptyProject.hidden = hasProject;
  elements.stageContent.hidden = !hasProject;
  elements.projectCrumb.textContent = state.project?.name || "未选择项目";
  if (!hasProject) {
    elements.timelineTrack.innerHTML = "";
    elements.overallProgressBar.style.width = "0%";
    elements.overallProgressText.textContent = "0%";
    renderPrimaryAction();
    return;
  }
  window.sessionStorage.setItem("sosove-ad-lab-project", state.project.id);
  renderBrief();
  renderSellingPoints();
  renderStoryboard();
  renderDirectionLedger();
  renderGenerationBoard();
  renderInspector();
  renderTimeline();
  renderFinal();
  setStep(state.activeStep, false);
}

function renderCapabilities() {
  const labels = [];
  const promptSkill = state.capabilities.promptSkill || {};
  if (state.capabilities.ai) labels.push(`${state.capabilities.aiModel || "AI"} 提示词已连接`);
  else labels.push("AI 未配置 · 使用本地导演模板");
  labels.push(state.capabilities.imageGeneration ? `${state.capabilities.imageModel || "GPT-Image-2"} 生图已连接` : "生图未配置");
  labels.push(state.capabilities.seedance ? "Seedance 已连接" : "Seedance 未配置");
  labels.push(state.capabilities.ffmpeg ? "FFmpeg 可合成" : "FFmpeg 不可用");
  if (elements.promptSkill) {
    const option = elements.promptSkill.options[0];
    option.textContent = promptSkill.exists
      ? `Seedance 2.0${promptSkill.version ? ` · v${promptSkill.version}` : ""}`
      : "Seedance 2.0 · 未安装";
    elements.promptSkill.disabled = !promptSkill.exists;
    elements.generateSkillPrompts.disabled = state.busy.size > 0 || !state.capabilities.ai || !promptSkill.exists;
  }
  ["ai", "image", "ark"].forEach((kind) => renderServiceNode(kind, state.serviceProbes[kind]));
  renderServiceNodeSummary();
  elements.capabilityNote.textContent = labels.join(" · ");
  elements.serviceStatus.classList.toggle("is-ready", Boolean(state.capabilities.seedance));
  elements.serviceStatus.lastChild.textContent = state.capabilities.seedance ? " 视频服务就绪" : " 待配置视频服务";
}

function formatServiceNodeCheckedAt(value) {
  if (!value) return "尚未检测";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function serviceNodeDefinition(kind) {
  const definitions = {
    ai: {
      configured: Boolean(state.capabilities.ai),
      model: state.capabilities.aiModel || "未配置模型",
      url: state.capabilities.aiBaseUrl || "未配置接口地址",
      purpose: "提示词",
      protocol: "Chat Completions",
      description: "用于产品描述分析以及图片、视频双提示词生成。",
    },
    image: {
      configured: Boolean(state.capabilities.imageGeneration),
      model: state.capabilities.imageModel || "未配置模型",
      url: state.capabilities.imageBaseUrl || "未配置接口地址",
      purpose: "生图",
      protocol: "Images Generations + Edits",
      description: "用于文生图与参考图编辑，支持独立尺寸选择。",
    },
    ark: {
      configured: Boolean(state.capabilities.seedance),
      model: state.capabilities.seedanceModel || "未配置模型",
      url: state.capabilities.seedanceEndpoint || "未配置任务地址",
      purpose: "视频",
      protocol: "异步视频任务",
      description: "用于文本、图片和视频参考驱动的逐镜视频生成。",
    },
  };
  return definitions[kind];
}

function renderServiceNode(kind, probe = null) {
  const card = $(`[data-service-node="${kind}"]`);
  const definition = serviceNodeDefinition(kind);
  if (!card || !definition) return;
  const field = (name) => $(`[data-node-field="${name}"]`, card);
  const button = $("[data-node-test]", card);
  const configured = definition.configured;
  const testing = state.busy.has(`service-node-probe:${kind}`);
  const hasProbe = Boolean(probe);
  const ready = hasProbe ? Boolean(probe.ok) : configured;
  const failed = hasProbe && !probe.ok;

  field("title").textContent = `${definition.model} ${definition.purpose}节点`;
  field("url").textContent = definition.url;
  field("url").title = definition.url;
  field("key").textContent = configured ? "密钥已配置" : "密钥未配置";
  field("model").textContent = `模型 ${definition.model}`;
  field("protocol").textContent = definition.protocol;
  field("status").textContent = testing
    ? "检测中"
    : hasProbe
      ? probe.ok ? "已连接" : probe.networkOk ? "接口异常" : "连接异常"
      : configured ? "已配置" : "未配置";
  field("diagnostics").textContent = testing
    ? `正在检测${definition.purpose}节点网络、鉴权与模型……`
    : hasProbe
      ? `HTTP ${probe.httpStatus ?? "--"} · ${probe.latencyMs ?? "--"}ms · ${formatServiceNodeCheckedAt(probe.checkedAt)}`
      : "等待检测 · 点击右侧按钮验证连通性";
  field("message").textContent = hasProbe
    ? probe.message || "节点检测完成。"
    : configured
      ? definition.description
      : `请先在接口配置中填写${definition.purpose}服务地址、模型和密钥。`;
  button.textContent = testing ? "检测中…" : "检测节点";
  button.disabled = testing;
  card.classList.toggle("is-ready", ready && !testing);
  card.classList.toggle("is-error", failed);
  card.classList.toggle("is-testing", testing);
}

function renderServiceNodeSummary() {
  if (!elements.serviceNodeSummary) return;
  const kinds = ["ai", "image", "ark"];
  const definitions = kinds.map((kind) => serviceNodeDefinition(kind));
  const configured = kinds.filter((kind) => serviceNodeDefinition(kind).configured).length;
  const checked = kinds.filter((kind) => state.serviceProbes[kind]);
  const connected = checked.filter((kind) => state.serviceProbes[kind]?.ok).length;
  const testing = kinds.filter((kind) => state.busy.has(`service-node-probe:${kind}`)).length;
  if (elements.serviceNodeModels) {
    elements.serviceNodeModels.textContent = definitions.map((definition) => definition.model).join(" · ");
    elements.serviceNodeModels.title = definitions.map((definition) => `${definition.purpose}: ${definition.model}`).join("\n");
  }
  elements.serviceNodeSummary.textContent = testing
    ? `${kinds.length} 个节点 · ${testing} 个检测中`
    : checked.length
      ? `${kinds.length} 个节点 · ${connected} 个已连接 · ${checked.length - connected} 个异常`
      : `${kinds.length} 个节点 · ${configured} 个已配置`;
  const hasProblem = definitions.some((definition) => !definition.configured) || kinds.some((kind) => state.serviceProbes[kind] && !state.serviceProbes[kind].ok);
  if (hasProblem && elements.serviceNodePanel) elements.serviceNodePanel.open = true;
}

async function testServiceNode(kind) {
  const definition = serviceNodeDefinition(kind);
  const busyKey = `service-node-probe:${kind}`;
  if (!definition || state.busy.has(busyKey)) return;
  setBusy(busyKey, true);
  renderServiceNode(kind, state.serviceProbes[kind]);
  renderServiceNodeSummary();
  try {
    const payload = await requestJson(`/api/config/test/${kind}`, {
      method: "POST",
      body: JSON.stringify({ testMode: "connectivity" }),
    });
    state.serviceProbes[kind] = payload.result?.[kind] || null;
    renderServiceNode(kind, state.serviceProbes[kind]);
    toast(state.serviceProbes[kind]?.message || `${definition.purpose}节点检测完成。`, state.serviceProbes[kind]?.ok ? "success" : "error");
  } catch (error) {
    state.serviceProbes[kind] = {
      ok: false,
      networkOk: false,
      httpStatus: null,
      latencyMs: null,
      checkedAt: new Date().toISOString(),
      message: error.message,
    };
    renderServiceNode(kind, state.serviceProbes[kind]);
    toast(error.message, "error");
  } finally {
    setBusy(busyKey, false);
    renderServiceNode(kind, state.serviceProbes[kind]);
    renderServiceNodeSummary();
  }
}

function renderProjectList() {
  const query = state.query.toLowerCase();
  const projects = state.projects.filter((project) => {
    if (state.filter === "archived" && !project.archived) return false;
    if (state.filter === "active" && project.archived) return false;
    return !query || `${project.name} ${project.productName}`.toLowerCase().includes(query);
  });
  elements.projectList.innerHTML = "";
  if (!projects.length) {
    const empty = document.createElement("div");
    empty.className = "project-empty";
    empty.textContent = state.filter === "archived" ? "还没有归档项目。" : "没有匹配项目。\n从一条清楚的 Brief 开始。";
    elements.projectList.append(empty);
    return;
  }
  projects.forEach((project) => {
    const item = document.createElement("article");
    item.className = `project-item ${project.id === state.project?.id ? "is-active" : ""}`;
    item.dataset.projectId = project.id;
    const thumb = project.shots?.find((shot) => shot.referenceImage)?.referenceImage || "";
    item.innerHTML = `
      <div class="project-thumb">${thumb ? `<img src="${escapeHtml(thumb)}" alt="">` : escapeHtml((project.productName || project.name || "AD").slice(0, 2))}</div>
      <div><strong></strong><p></p><div class="project-meta"><span></span><span></span></div></div>`;
    $("strong", item).textContent = project.name || "未命名广告项目";
    $("p", item).textContent = project.productName || "等待商品信息";
    const meta = $$(".project-meta span", item);
    meta[0].textContent = `${project.progress?.videosReady || 0}/${project.progress?.shotsTotal || 0} 视频`;
    meta[1].textContent = `${project.progress?.percent || 0}%`;
    item.addEventListener("click", () => {
      state.project = project;
      state.activeStep = Number(project.currentStep || 1);
      state.selectedShotId = project.shots?.[0]?.id || "";
      render();
      document.body.classList.remove("rail-open");
      elements.backdrop.hidden = true;
      resumePolling();
    });
    elements.projectList.append(item);
  });
}

function renderBrief() {
  const project = state.project;
  elements.projectName.value = project.name || "";
  elements.productName.value = project.productName || "";
  elements.productDescription.value = project.productDescription || "";
  elements.briefSummary.value = project.brief?.summary || "";
  elements.briefAudience.value = project.brief?.audience || "";
  elements.market.value = project.settings?.market || "日本";
  elements.language.value = project.settings?.language || "日语";
  elements.platform.value = project.settings?.platform || "TikTok";
  elements.ratio.value = project.settings?.ratio || "9:16";
  elements.imageSize.value = project.settings?.imageSize || "auto";
  elements.shotCount.value = String(project.settings?.shotCount || 4);
  if (![...elements.totalDuration.options].some((option) => Number(option.value) === Number(project.settings?.totalDuration))) {
    const option = new Option(`${project.settings.totalDuration} 秒`, String(project.settings.totalDuration));
    elements.totalDuration.add(option);
  }
  elements.totalDuration.value = String(project.settings?.totalDuration || 20);
  elements.style.value = project.settings?.style || "editorial-natural";
  elements.bgm.checked = Boolean(project.settings?.bgm);
  elements.onScreenText.checked = Boolean(project.settings?.onScreenText);
  const promptSkill = state.capabilities.promptSkill || {};
  elements.promptSkillState.textContent = project.promptGeneratedAt
    ? `已用 ${project.promptSkill || "seedance-20"}${project.promptSkillVersion ? ` v${project.promptSkillVersion}` : ""} 生成 · ${project.shots?.length || 0} 组双提示词`
    : promptSkill.exists
      ? `本机 ${promptSkill.name || "seedance-20"}${promptSkill.version ? ` v${promptSkill.version}` : ""} 已就绪`
      : "本机 Seedance Skill 未安装";
}

function renderSellingPoints() {
  elements.sellingPointList.innerHTML = "";
  (state.project?.brief?.sellingPoints || []).forEach((point, index) => {
    const chip = document.createElement("span");
    chip.className = "point-chip";
    const text = document.createElement("span");
    text.textContent = point;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `删除卖点 ${point}`);
    remove.addEventListener("click", () => removeSellingPoint(index));
    chip.append(text, remove);
    elements.sellingPointList.append(chip);
  });
}

function resolvedImageSize(shot) {
  const requested = shot?.imageSize || state.project?.settings?.imageSize || "auto";
  if (["1024x1536", "1536x1024", "1024x1024"].includes(requested)) return requested;
  return { "9:16": "1024x1536", "16:9": "1536x1024", "1:1": "1024x1024" }[state.project?.settings?.ratio] || "1024x1536";
}

function imageFrameClass(shot) {
  return {
    "1024x1536": "frame-portrait",
    "1536x1024": "frame-landscape",
    "1024x1024": "frame-square",
  }[resolvedImageSize(shot)] || "frame-portrait";
}

function shotArtMarkup(shot, portrait = false) {
  const imageBusy = state.busy.has(`image:${shot.id}`);
  const imageCancelling = Boolean(state.imageRequests.get(shot.id)?.cancelling);
  const art = shot.videoUrl
    ? `<video src="${escapeHtml(shot.videoUrl)}" controls playsinline preload="metadata"></video><button class="shot-play-overlay" type="button" data-action="play-video" aria-label="播放 ${escapeHtml(shot.title || `SHOT ${shot.order}`)}"><span>▶</span><b>播放视频</b></button>`
    : shot.referenceImage
      ? `<img src="${escapeHtml(shot.referenceImage)}" alt="${escapeHtml(shot.title)}">`
      : `<div class="shot-placeholder" data-order="${String(shot.order).padStart(2, "0")}"><b>${escapeHtml(shot.title)}</b><small>${escapeHtml(shot.scene || shot.imagePrompt || shot.prompt || "等待分镜描述")}</small></div>`;
  const stateClass = imageBusy ? "generating" : shot.status;
  const stateLabel = imageCancelling ? "正在取消" : imageBusy ? "正在生图" : shot.referenceImage && !shot.videoUrl && !["queued", "generating", "completed"].includes(shot.status) ? "关键帧就绪" : STATUS_LABELS[shot.status] || shot.status;
  return `<div class="shot-art ${portrait ? "portrait" : ""} ${imageFrameClass(shot)}"><span class="shot-badge">SHOT ${String(shot.order).padStart(2, "0")}</span><span class="shot-size">${escapeHtml(resolvedImageSize(shot).replace("x", " × "))}</span>${art}<span class="shot-state ${escapeHtml(stateClass)}">${escapeHtml(stateLabel)}</span></div>`;
}

function createShotCard(shot, generation = false) {
  const imageBusy = state.busy.has(`image:${shot.id}`);
  const imageCancelling = Boolean(state.imageRequests.get(shot.id)?.cancelling);
  const imageOrigin = shot.referenceImageSource === "generated" ? "AI 关键帧" : shot.referenceImage ? "上传参考" : "无关键帧";
  const imageTrace = shot.imageGenerationRoute === "edits"
    ? `原图驱动 ${Number(shot.imageReferenceCount || 0)}张`
    : shot.imageGenerationRoute === "generations"
      ? "纯提示词生图"
      : "未记录生图来源";
  const promptPair = shot.imagePrompt && shot.prompt ? "双提示词" : shot.prompt ? "视频提示词" : "待提示词";
  const cardError = friendlyShotError(shot.imageError || shot.error || "");
  const cardErrorMarkup = cardError
    ? `<div class="shot-card-error"><b>需要处理</b><span title="${escapeHtml(cardError)}">${escapeHtml(cardError)}</span><button type="button" data-action="inspect">查看并修复</button></div>`
    : "";
  const actions = generation
    ? shot.videoUrl
      ? `<button type="button" data-action="play-video" class="play-video-action">播放视频</button><button type="button" data-action="inspect">编辑</button><button type="button" data-action="generate">重新生成</button>`
      : `<button type="button" data-action="inspect">编辑</button><button type="button" data-action="generate">${shot.status === "failed" ? "重试" : "生成视频"}</button>`
    : `<button type="button" data-action="inspect">编辑</button><button type="button" data-action="${imageBusy ? "cancel-image" : "generate-image"}" class="${imageBusy ? "cancel-action" : ""}" ${imageCancelling ? "disabled" : ""}>${imageCancelling ? "正在取消…" : imageBusy ? "取消生成" : shot.referenceImage ? "重绘关键帧" : "生成关键帧"}</button>`;
  const card = document.createElement("article");
  card.className = `shot-card ${shot.id === state.selectedShotId ? "is-selected" : ""}`;
  card.dataset.shotId = shot.id;
  card.innerHTML = `
    ${shotArtMarkup(shot, !generation)}
    <div class="shot-card-body">
      <div class="shot-card-head"><h3></h3><span>${shot.duration}s</span></div>
      <p></p>
      <div class="shot-card-meta"><span>${escapeHtml(ROLE_LABELS[shot.role] || shot.role)}</span><span>${escapeHtml(imageOrigin)}</span><span>${escapeHtml(imageTrace)}</span><span>${escapeHtml(promptPair)}</span><span>图 ${referenceImageUrls(shot).length} · 视 ${shot.referenceVideos?.length || 0}</span>${shot.taskId ? "<span>任务已绑定</span>" : ""}</div>
      ${cardErrorMarkup}
      <div class="shot-card-actions">
        ${actions}
      </div>
    </div>`;
  $("h3", card).textContent = shot.title;
  $(".shot-card-body > p", card).textContent = shot.prompt || shot.scene || "等待提示词";
  card.addEventListener("click", (event) => {
    const action = event.target.closest("button")?.dataset.action;
    if (action === "play-video") { event.stopPropagation(); openVideoPlayer(shot); return; }
    if (action === "generate") { event.stopPropagation(); generateShot(shot.id); return; }
    if (action === "generate-image") { event.stopPropagation(); generateImage(shot.id); return; }
    if (action === "cancel-image") { event.stopPropagation(); cancelImage(shot.id); return; }
    if (event.target.closest("video")) { event.stopPropagation(); return; }
    chooseShot(shot.id, action === "inspect");
  });
  return card;
}

function renderStoryboard() {
  elements.storyboardGrid.innerHTML = "";
  if (!state.project?.shots?.length) return;
  state.project.shots.forEach((shot) => elements.storyboardGrid.append(createShotCard(shot)));
  const source = state.project.storyboardSource === "seedance-skill"
    ? `Seedance Skill${state.project.promptSkillVersion ? ` v${state.project.promptSkillVersion}` : ""} 双提示词`
    : state.project.storyboardSource === "ai"
      ? "AI 导演分镜"
      : state.project.storyboardSource === "fallback"
        ? "本地导演模板"
        : "等待生成";
  elements.storyboardSource.textContent = `${source} · ${state.project.shots.length} 镜 · ${state.project.settings.totalDuration}s`;
  elements.generateAllImages.disabled = state.busy.size > 0 || !state.capabilities.imageGeneration;
}

function renderDirectionLedger() {
  elements.directionLedger.innerHTML = "";
  (state.project?.shots || []).forEach((shot) => {
    const row = document.createElement("article");
    row.className = `direction-row ${shot.id === state.selectedShotId ? "is-selected" : ""}`;
    row.innerHTML = `<span>SHOT ${String(shot.order).padStart(2, "0")}</span><strong></strong><p></p><small>图 ${shot.imagePrompt?.length || 0} · 视 ${shot.prompt?.length || 0}</small>`;
    $("strong", row).textContent = shot.title;
    $("p", row).textContent = shot.prompt || "等待提示词";
    row.addEventListener("click", () => chooseShot(shot.id, true));
    elements.directionLedger.append(row);
  });
}

function renderGenerationBoard() {
  elements.generationBoard.innerHTML = "";
  (state.project?.shots || []).forEach((shot) => elements.generationBoard.append(createShotCard(shot, true)));
}

function renderReferenceWorkbench(shot) {
  const images = referenceImageUrls(shot);
  const globalImages = projectReferenceImageUrls();
  const visibleImages = effectiveReferenceImageUrls(shot);
  const videos = shot.referenceVideos || [];
  const videoDurationMs = referenceVideoDurationMs(shot);
  const promptOnly = shot.generationMode === "prompt-only";
  const privacyMode = ["product-only", "direct"].includes(shot.referencePrivacyMode) ? shot.referencePrivacyMode : "product-only";
  const imageMode = ["auto", "reference", "prompt"].includes(shot.imageGenerationMode) ? shot.imageGenerationMode : "auto";
  const editReferences = imageEditReferenceUrls(shot);
  const sourceReferences = sourceReferenceImageUrls(shot);
  const sourceReferenceCount = sourceReferences.length;
  elements.generationMode.value = promptOnly ? "prompt-only" : "multimodal";
  elements.referencePrivacyMode.value = privacyMode;
  elements.imageGenerationMode.value = imageMode;
  elements.referenceOverview.textContent = `本镜 ${images.length} 图 · 全片 ${globalImages.length} 图 · ${videos.length} 视${promptOnly ? " · 视频不传参考" : privacyMode === "product-only" ? " · 人脸遮蔽" : " · 原图直传"}`;
  elements.referenceImageCount.textContent = `${images.length}/9 · 全片 ${globalImages.length}`;
  elements.referenceVideoCount.textContent = `${videos.length}/3 · ${formatReferenceDuration(videoDurationMs)}/15s`;
  elements.referenceImageList.innerHTML = "";
  elements.referenceVideoList.innerHTML = "";

  elements.imageGenerationReferenceState.classList.toggle("is-warning", imageMode === "reference" && sourceReferences.length === 0);
  let currentImageReferenceState = "";
  if (imageMode === "prompt") {
    currentImageReferenceState = "本次调用 /images/generations，不发送参考图。";
  } else if (sourceReferences.length) {
    const sourceNote = sourceReferenceCount ? "原始商品参考" : "现有 AI 关键帧";
    currentImageReferenceState = `将发送 ${sourceReferences.length} 张${sourceNote}到 /images/edits（最多 4 张）。`;
  } else if (imageMode === "reference") {
    currentImageReferenceState = "缺少原始商品图：强制参考不会退回纯提示词，也不会用 AI 图冒充原图。";
  } else if (editReferences.length) {
    currentImageReferenceState = `当前只有 AI 关键帧，将用它继续编辑；建议上传原始商品图。`;
  } else {
    currentImageReferenceState = "当前没有参考图，将自动使用纯提示词生图。";
  }
  const lastImageReferenceState = shot.imageGenerationRoute === "edits"
    ? `上次：原图驱动 ${Number(shot.imageReferenceCount || 0)} 张`
    : shot.imageGenerationRoute === "generations"
      ? "上次：纯提示词生图"
      : "";
  elements.imageGenerationReferenceState.textContent = `${currentImageReferenceState}${lastImageReferenceState ? ` · ${lastImageReferenceState}` : ""}`;

  visibleImages.forEach((url, index) => {
    const item = document.createElement("figure");
    item.className = "reference-media-item image-reference-item";
    const image = document.createElement("img");
    image.src = url;
    image.alt = `参考图 ${index + 1}`;
    image.loading = "lazy";
    const badge = document.createElement("figcaption");
    const isGenerated = isGeneratedReferenceImage(url);
    const isGlobal = globalImages.includes(url);
    const isLocal = images.includes(url);
    badge.textContent = isGenerated ? "AI 关键帧" : isGlobal ? `商品参考 ${index + 1} · 全片` : `商品参考 ${index + 1}`;
    if (!isGenerated) {
      const globalButton = document.createElement("button");
      globalButton.type = "button";
      globalButton.className = `reference-global-button ${isGlobal ? "is-active" : ""}`;
      globalButton.textContent = isGlobal ? "全片 ✓" : "设为全片";
      globalButton.title = isGlobal ? "取消全片商品参考" : "设为全片商品参考";
      globalButton.setAttribute("aria-label", `${globalButton.title}：参考图 ${index + 1}`);
      globalButton.addEventListener("click", () => toggleProjectReferenceImage(url).catch((error) => toast(error.message, "error")));
      item.append(globalButton);
    }
    item.append(image, badge);
    if (isLocal) {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "reference-remove-button";
      remove.textContent = "×";
      remove.title = isGlobal ? "仅从当前镜头移除；全片参考仍保留" : "从当前镜头移除参考图";
      remove.setAttribute("aria-label", `${remove.title} ${index + 1}`);
      remove.addEventListener("click", () => removeReferenceImage(url).catch((error) => toast(error.message, "error")));
      item.append(remove);
    }
    elements.referenceImageList.append(item);
  });

  videos.forEach((reference, index) => {
    const item = document.createElement("figure");
    item.className = "reference-media-item video-reference-item";
    const video = document.createElement("video");
    video.src = reference.url;
    video.muted = true;
    video.playsInline = true;
    video.preload = "metadata";
    video.controls = true;
    const badge = document.createElement("figcaption");
    badge.textContent = `视频 ${index + 1} · ${formatReferenceDuration(reference.durationMs)}`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "reference-remove-button";
    remove.textContent = "×";
    remove.title = "移除参考视频";
    remove.setAttribute("aria-label", `移除参考视频 ${index + 1}`);
    remove.addEventListener("click", () => removeReferenceVideo(reference.url).catch((error) => toast(error.message, "error")));
    item.append(video, badge, remove);
    elements.referenceVideoList.append(item);
  });

  $("#upload-reference-button").disabled = images.length >= 9;
  $("#upload-reference-video-button").disabled = videos.length >= 3 || videoDurationMs >= 15000;
  $(".reference-workbench").classList.toggle("is-prompt-only", promptOnly);
  const localImagesCanInline = Boolean(state.capabilities.inlineLocalImages);
  const localVideoNeedsPublicUrl = !state.capabilities.publicAssets && videos.length > 0;
  const localImageNeedsPublicUrl = !state.capabilities.publicAssets && visibleImages.length > 0 && !localImagesCanInline;
  const directFaceRisk = privacyMode === "direct" && visibleImages.length > 0;
  elements.referenceState.textContent = promptOnly
    ? "参考素材会继续保留，但纯提示词模式不会把它们发送给视频模型。"
    : localVideoNeedsPublicUrl
      ? "本机参考图会自动安全内嵌；参考视频仍需公网可访问地址，请配置公网素材地址或先移除本机参考视频。"
    : privacyMode === "product-only" && visibleImages.length > 0
      ? "商品隐私模式：原始商品图优先，提交前会遮蔽真人脸，只让参考图控制服装、材质和轮廓。"
    : directFaceRisk
      ? "无人脸原图直传：图片中只要出现完整或部分真人脸，Seedance 都可能拒绝；真人素材需使用方舟授权 Asset ID。"
    : localImageNeedsPublicUrl
      ? "当前参考图仅本机可访问，提交远端 Seedance 前需要配置公网素材地址。"
    : !state.capabilities.publicAssets && visibleImages.length > 0 && localImagesCanInline
      ? "本机参考图会由服务端自动安全内嵌到 Seedance 请求，无需配置公网图片地址。"
      : "图片锁定商品与主体；视频只参考动作、运镜和节奏，不继承人物、服装、场景或标识。";
  elements.referenceState.classList.toggle("is-warning", Boolean(!promptOnly && (localVideoNeedsPublicUrl || localImageNeedsPublicUrl || directFaceRisk)));
}

function renderReferenceQuickbar(shot = selectedShot()) {
  const images = shot ? referenceImageUrls(shot) : [];
  const globalImages = projectReferenceImageUrls();
  const videos = shot?.referenceVideos || [];
  const videoDurationMs = shot ? referenceVideoDurationMs(shot) : 0;
  const hasShot = Boolean(shot);
  elements.quickReferenceShot.textContent = hasShot
    ? `SHOT ${String(shot.order).padStart(2, "0")} · ${shot.title || "未命名镜头"}`
    : "请先选择一个分镜";
  elements.quickReferenceImageCount.textContent = `${images.length}/9 · 全片 ${globalImages.length}`;
  elements.quickReferenceVideoCount.textContent = `${videos.length}/3 · ${formatReferenceDuration(videoDurationMs)}/15s`;
  elements.quickUploadReference.disabled = !hasShot || images.length >= 9;
  elements.quickUploadReferenceVideo.disabled = !hasShot || videos.length >= 3 || videoDurationMs >= 15000;
  elements.manageReference.disabled = !hasShot;
  elements.referenceQuickbar.classList.toggle("has-material", images.length + videos.length > 0);
}

function renderInspector() {
  const shot = selectedShot();
  renderReferenceQuickbar(shot);
  elements.inspectorEmpty.hidden = Boolean(shot);
  elements.inspectorContent.hidden = !shot;
  if (!shot) return;
  elements.inspectorShotLabel.textContent = `SHOT ${String(shot.order).padStart(2, "0")}`;
  elements.inspectorStatus.textContent = STATUS_LABELS[shot.status] || shot.status;
  elements.inspectorStatus.className = `status-pill ${shot.status}`;
  elements.inspectorPreview.innerHTML = shotArtMarkup(shot);
  elements.shotTitle.value = shot.title || "";
  elements.shotRole.value = shot.role || "detail";
  if (![...elements.shotDuration.options].some((option) => Number(option.value) === Number(shot.duration))) {
    elements.shotDuration.add(new Option(`${shot.duration} 秒`, String(shot.duration)));
  }
  elements.shotDuration.value = String(shot.duration || 5);
  elements.shotScene.value = shot.scene || "";
  elements.shotCamera.value = shot.camera || "";
  elements.shotImagePrompt.value = shot.imagePrompt || "";
  elements.shotPrompt.value = shot.prompt || "";
  elements.shotCopy.value = shot.copy || "";
  renderReferenceWorkbench(shot);
  const visibleError = friendlyShotError(shot.imageError || shot.error || "");
  elements.shotError.hidden = !visibleError;
  elements.shotError.textContent = visibleError;
  const imageBusy = state.busy.has(`image:${shot.id}`);
  const imageCancelling = Boolean(state.imageRequests.get(shot.id)?.cancelling);
  const missingForcedReference = shot.imageGenerationMode === "reference" && sourceReferenceImageUrls(shot).length === 0;
  elements.generateImage.disabled = imageCancelling || (!imageBusy && (!state.capabilities.imageGeneration || missingForcedReference));
  elements.generateImage.classList.toggle("cancel-action", imageBusy);
  elements.generateImage.textContent = imageCancelling
    ? "正在取消…"
    : imageBusy
      ? "取消生成"
      : shot.referenceImageSource === "generated"
        ? "重绘关键帧"
        : imageEditReferenceUrls(shot).length
          ? "按参考图生成"
          : "生成关键帧";
  $("#generate-shot-button").textContent = shot.videoUrl ? "重新生成这一镜" : shot.status === "failed" ? "修复后重试" : "生成这一镜";
}

function renderTimeline() {
  elements.timelineTrack.innerHTML = "";
  (state.project?.shots || []).forEach((shot) => {
    const clip = document.createElement("button");
    clip.type = "button";
    clip.className = `timeline-clip ${shot.status} ${shot.id === state.selectedShotId ? "is-selected" : ""}`;
    clip.innerHTML = `<b>${String(shot.order).padStart(2, "0")} · ${escapeHtml(shot.title)}</b><small>${shot.duration}s · ${escapeHtml(STATUS_LABELS[shot.status] || shot.status)}</small>`;
    clip.addEventListener("click", () => chooseShot(shot.id, true));
    elements.timelineTrack.append(clip);
  });
  const progress = state.project?.progress?.percent || 0;
  elements.overallProgressBar.style.width = `${progress}%`;
  elements.overallProgressText.textContent = `${progress}%`;
}

function renderFinal() {
  if (state.project?.finalVideoUrl) {
    elements.finalPreview.innerHTML = "";
    const video = document.createElement("video");
    video.src = state.project.finalVideoUrl;
    video.controls = true;
    video.playsInline = true;
    elements.finalPreview.append(video);
    const link = document.createElement("a");
    link.className = "primary-button";
    link.href = state.project.finalVideoUrl;
    link.download = "";
    link.textContent = "下载合成草稿";
    link.style.position = "absolute";
    link.style.right = "18px";
    link.style.bottom = "18px";
    elements.finalPreview.style.position = "relative";
    elements.finalPreview.append(link);
  } else {
    elements.finalPreview.innerHTML = '<div class="final-empty"><span>FINAL</span><p>所有可用片段会在这里形成可下载草稿。</p></div>';
  }
}

function openVideoPlayer(shot) {
  if (!shot?.videoUrl) {
    toast("这个镜头还没有可播放的视频。", "error");
    return;
  }
  state.videoPlayerReturnFocus = document.activeElement;
  document.body.classList.remove("rail-open", "inspector-open");
  document.body.classList.add("video-player-open");
  elements.videoPlayerShot.textContent = `SHOT ${String(shot.order || 0).padStart(2, "0")} · ${Number(shot.duration || 0)} 秒`;
  elements.videoPlayerTitle.textContent = shot.title || "生成视频预览";
  elements.videoPlayerError.hidden = true;
  elements.videoPlayerOpen.href = shot.videoUrl;
  elements.videoPlayerDownload.href = shot.videoUrl;
  elements.videoPlayerDownload.download = `${shot.title || `shot-${shot.order || "video"}`}.mp4`;
  elements.videoPlayerVideo.src = shot.videoUrl;
  elements.videoPlayerModal.hidden = false;
  elements.backdrop.hidden = false;
  elements.videoPlayerVideo.load();
  const playRequest = elements.videoPlayerVideo.play();
  if (playRequest?.catch) playRequest.catch(() => {});
  window.requestAnimationFrame(() => elements.videoPlayerClose.focus());
}

function closeVideoPlayer() {
  const wasOpen = !elements.videoPlayerModal.hidden;
  elements.videoPlayerVideo.pause();
  elements.videoPlayerVideo.removeAttribute("src");
  elements.videoPlayerVideo.load();
  elements.videoPlayerModal.hidden = true;
  elements.videoPlayerError.hidden = true;
  document.body.classList.remove("video-player-open");
  if (!document.body.classList.contains("rail-open") && !document.body.classList.contains("inspector-open")) {
    elements.backdrop.hidden = true;
  }
  if (wasOpen && state.videoPlayerReturnFocus instanceof HTMLElement) state.videoPlayerReturnFocus.focus();
  state.videoPlayerReturnFocus = null;
}

function renderPrimaryAction() {
  const button = elements.primaryAction;
  if (!state.project) {
    button.textContent = "新建项目";
    button.disabled = state.busy.has("create");
    return;
  }
  const eligibleShots = (state.project.shots || []).filter((shot) => !shot.excluded);
  const completedShots = eligibleShots.filter((shot) => shot.videoUrl);
  const actionLabels = {
    ...STEP_ACTIONS,
    2: `审核 ${eligibleShots.length} 组提示词`,
    4: `查看时间线（${completedShots.length}/${eligibleShots.length}）`,
    5: `合成 ${completedShots.length} 个片段`,
  };
  button.textContent = actionLabels[state.activeStep] || "继续";
  button.disabled = state.busy.size > 0 || (state.activeStep === 5 && completedShots.length === 0);
}

function openInspectorDrawer() {
  state.inspectorOverride = "open";
  document.body.classList.remove("inspector-collapsed");
  if (window.innerWidth <= 1080) {
    document.body.classList.add("inspector-open");
    elements.backdrop.hidden = false;
  } else {
    document.body.classList.remove("inspector-open");
  }
}

function collapseInspectorPanel() {
  state.inspectorOverride = "collapsed";
  document.body.classList.remove("inspector-open");
  if (!document.body.classList.contains("rail-open") && !document.body.classList.contains("video-player-open")) {
    elements.backdrop.hidden = true;
  }
  syncInspectorContext();
}

function openReferenceManager() {
  if (!selectedShot()) return;
  openInspectorDrawer();
  window.requestAnimationFrame(() => {
    elements.referenceWorkbench.scrollIntoView({ behavior: "smooth", block: "center" });
    elements.referenceWorkbench.classList.remove("is-focus-target");
    window.requestAnimationFrame(() => elements.referenceWorkbench.classList.add("is-focus-target"));
  });
}

function closeDrawers() {
  document.body.classList.remove("rail-open", "inspector-open");
  closeVideoPlayer();
}

function runPrimaryAction() {
  if (!state.project) return createProject();
  if (state.activeStep === 1) return generateStoryboard(false);
  if (state.activeStep === 2) return setStep(3);
  if (state.activeStep === 3) return setStep(4);
  if (state.activeStep === 4) return setStep(5);
  return composeProject();
}

function bindEvents() {
  $("#new-project-button").addEventListener("click", createProject);
  $("#empty-create-button").addEventListener("click", createProject);
  elements.projectSearch.addEventListener("input", () => { state.query = elements.projectSearch.value.trim(); renderProjectList(); });
  $$("[data-project-filter]").forEach((button) => button.addEventListener("click", async () => {
    state.filter = button.dataset.projectFilter;
    $$("[data-project-filter]").forEach((item) => item.classList.toggle("is-active", item === button));
    if (state.filter === "archived") await loadProjects(true);
    else await loadProjects(false);
  }));
  elements.workflowSteps.forEach((button) => button.addEventListener("click", () => setStep(button.dataset.step)));
  elements.previousStep.addEventListener("click", () => setStep(state.activeStep - 1));
  elements.nextStep.addEventListener("click", () => setStep(state.activeStep + 1));
  $$("#brief-form input, #brief-form textarea, #brief-form select").forEach((control) => {
    control.addEventListener(control.type === "checkbox" ? "change" : "input", bindFormToState);
    if (control.tagName === "SELECT") control.addEventListener("change", bindFormToState);
  });
  $("#add-selling-point-button").addEventListener("click", addSellingPoint);
  elements.sellingPointInput.addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); addSellingPoint(); } });
  $("#generate-storyboard-button").addEventListener("click", () => generateStoryboard(false));
  elements.generateSkillPrompts.addEventListener("click", generateSkillPrompts);
  $$('[data-node-test]').forEach((button) => button.addEventListener("click", () => testServiceNode(button.dataset.nodeTest)));
  elements.generateAllImages.addEventListener("click", generateAllImages);
  elements.imageSize.addEventListener("change", () => {
    if (!state.project) return;
    state.project.settings.imageSize = elements.imageSize.value;
    renderStoryboard();
    renderGenerationBoard();
    renderInspector();
    queueProjectSave();
    toast(`生图尺寸已设为：${elements.imageSize.options[elements.imageSize.selectedIndex].text}。`, "success");
  });
  $("#reset-storyboard-button").addEventListener("click", () => generateStoryboard(true));
  $("#reverse-shots-button").addEventListener("click", () => reorderShots([...state.project.shots].reverse().map((shot) => shot.id)));
  $("#save-shot-button").addEventListener("click", () => saveShot());
  elements.generateImage.addEventListener("click", () => {
    const shot = selectedShot();
    if (!shot) return;
    if (state.busy.has(`image:${shot.id}`)) cancelImage(shot.id);
    else generateImage(shot.id);
  });
  $("#generate-shot-button").addEventListener("click", () => selectedShot() && generateShot(selectedShot().id));
  $("#upload-reference-button").addEventListener("click", () => elements.shotReferenceInput.click());
  elements.quickUploadReference.addEventListener("click", () => elements.shotReferenceInput.click());
  elements.shotReferenceInput.addEventListener("change", uploadReferenceImages);
  $("#upload-reference-video-button").addEventListener("click", () => elements.shotReferenceVideoInput.click());
  elements.quickUploadReferenceVideo.addEventListener("click", () => elements.shotReferenceVideoInput.click());
  elements.shotReferenceVideoInput.addEventListener("change", uploadReferenceVideos);
  elements.manageReference.addEventListener("click", openReferenceManager);
  elements.inspectorPreview.addEventListener("click", (event) => {
    if (event.target.closest('[data-action="play-video"]')) openVideoPlayer(selectedShot());
  });
  elements.generationMode.addEventListener("change", () => {
    saveShot({ generationMode: elements.generationMode.value }, true)
      .then(() => toast(elements.generationMode.value === "multimodal" ? "已启用多模态参考。" : "已切换为纯提示词模式。", "success"))
      .catch((error) => toast(error.message, "error"));
  });
  elements.referencePrivacyMode.addEventListener("change", () => {
    const mode = elements.referencePrivacyMode.value;
    saveShot({ referencePrivacyMode: mode }, true)
      .then(() => toast(mode === "product-only" ? "已启用商品隐私模式：提交前遮蔽真人脸。" : "已切换为无人脸原图直传。", "success"))
      .catch((error) => toast(error.message, "error"));
  });
  elements.imageGenerationMode.addEventListener("change", () => {
    const mode = elements.imageGenerationMode.value;
    saveShot({ imageGenerationMode: mode }, true)
      .then(() => toast(mode === "prompt" ? "关键帧已切换为纯提示词生图。" : mode === "reference" ? "关键帧将强制使用参考图。" : "关键帧已切换为自动参考模式。", "success"))
      .catch((error) => toast(error.message, "error"));
  });
  $("#generate-all-button").addEventListener("click", generateAll);
  $("#compose-button").addEventListener("click", composeProject);
  $("#archive-project-button").addEventListener("click", archiveCurrentProject);
  elements.primaryAction.addEventListener("click", runPrimaryAction);
  $("#theme-density-button").addEventListener("click", () => document.body.classList.toggle("is-compact"));
  $("#mobile-rail-button").addEventListener("click", () => { document.body.classList.add("rail-open"); elements.backdrop.hidden = false; });
  $("#rail-close").addEventListener("click", closeDrawers);
  $("#mobile-inspector-button").addEventListener("click", openInspectorDrawer);
  elements.inspectorCollapse.addEventListener("click", collapseInspectorPanel);
  elements.inspectorReopen.addEventListener("click", openInspectorDrawer);
  elements.videoPlayerClose.addEventListener("click", closeVideoPlayer);
  elements.videoPlayerVideo.addEventListener("loadeddata", () => { elements.videoPlayerError.hidden = true; });
  elements.videoPlayerVideo.addEventListener("error", () => {
    if (!elements.videoPlayerModal.hidden) elements.videoPlayerError.hidden = false;
  });
  elements.backdrop.addEventListener("click", closeDrawers);
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeDrawers(); });
  window.addEventListener("resize", () => syncInspectorContext());
  window.addEventListener("beforeunload", () => state.polling.forEach((timer) => window.clearInterval(timer)));
  window.addEventListener("ad-lab:archive-current", archiveCurrentProject);
}

async function init() {
  bindEvents();
  try {
    await loadProjects(false);
  } catch (error) {
    toast(error.message, "error");
  }
}

init();
