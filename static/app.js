const state = {
  ratio: "9:16",
  duration: 10,
  quantity: 1,
  defaultModel: "doubao-seedance-2-0-260128",
  model: "doubao-seedance-2-0-260128",
  taskId: "",
  taskIds: [],
  taskMap: {},
  pollTimer: null,
  lastRequest: null,
  lastTask: null,
  lastVideoUrl: "",
  lastErrors: [],
  lastSkillPrompt: "",
  skillPrompts: [],
  taskPromptMap: {},
  taskPromptTextMap: {},
  taskPayloadMap: {},
  assetRoles: {},
  assetBatches: null,
  lastPromptQualityScore: 0,
  promptReview: null,
  promptReviewPrompt: "",
  promptReviewSkill: null,
  workspaceView: "create",
  templateReplaceMode: false,
  lightboxUrl: "",
  videoLightboxUrl: "",
  mentionRange: null,
  mentionIndex: 0,
};

const BUILT_IN_MODEL = "doubao-seedance-2-0-260128";
const MODEL_ALIASES = {
  "seed2.0": BUILT_IN_MODEL,
  "seed-2.0": BUILT_IN_MODEL,
  "seedance2.0": BUILT_IN_MODEL,
  "seedance-2.0": BUILT_IN_MODEL,
  seedance2: BUILT_IN_MODEL,
  "seedance-2": BUILT_IN_MODEL,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const PROMPT_HISTORY_KEY = "seedancePromptHistory";
const CREATIVE_BRIEF_KEY = "seedanceCreativeBriefV1";
const MATERIAL_REVERSE_PROMPT_DRAFT_KEY = "seedanceMaterialReversePromptDraftV1";
const ASSET_ROLE_KEY = "seedanceAssetRoles";
const ASSET_BATCH_KEY = "seedanceAssetBatches";
const WORKSPACE_VIEW_KEY = "seedanceWorkspaceViewV1";
const MARKET_LOCALIZATION = {
  日本: { language: "日语", direction: "日本本地电商、Reels 和 TikTok 的自然表达" },
  Japan: { language: "日语", direction: "日本本地电商、Reels 和 TikTok 的自然表达" },
  美国: { language: "美式英语", direction: "美国 TikTok UGC 和 Meta 广告的直接自然表达" },
  "United States": { language: "美式英语", direction: "美国 TikTok UGC 和 Meta 广告的直接自然表达" },
  英国: { language: "英式英语", direction: "英国本地生活方式与电商口语" },
  "United Kingdom": { language: "英式英语", direction: "英国本地生活方式与电商口语" },
  韩国: { language: "韩语", direction: "韩国本地电商与短视频口语" },
  法国: { language: "法语", direction: "法国本地生活方式与电商表达" },
  德国: { language: "德语", direction: "德国本地清晰、可信的电商表达" },
  西班牙: { language: "西班牙语", direction: "西班牙本地自然口语与生活场景" },
  墨西哥: { language: "西班牙语", direction: "墨西哥本地西班牙语与短视频表达" },
  意大利: { language: "意大利语", direction: "意大利本地生活方式与电商表达" },
  巴西: { language: "巴西葡萄牙语", direction: "巴西本地短视频与电商口语" },
  加拿大: { language: "美式英语", direction: "加拿大本地生活方式与电商表达" },
  澳大利亚: { language: "英式英语", direction: "澳大利亚本地生活方式与短视频表达" },
  泰国: { language: "泰语", direction: "泰国本地电商与短视频口语" },
  越南: { language: "越南语", direction: "越南本地电商与短视频口语" },
  印度尼西亚: { language: "印度尼西亚语", direction: "印度尼西亚本地电商与短视频口语" },
  沙特阿拉伯: { language: "阿拉伯语", direction: "沙特本地文化语境与电商表达" },
  阿联酋: { language: "阿拉伯语", direction: "阿联酋本地文化语境与电商表达" },
};
const DEFAULT_ASSET_TAGS = ["待剪辑", "已选", "上身", "细节", "动作", "首帧", "尾帧", "BGM", "广告", "返修"];
const ASSET_ACCENTS = [
  { color: "#1677ff", soft: "#eef5ff", rgb: "22, 119, 255" },
  { color: "#d9483b", soft: "#fff0ed", rgb: "217, 72, 59" },
  { color: "#16b981", soft: "#effcf6", rgb: "22, 185, 129" },
  { color: "#f59f24", soft: "#fff8e8", rgb: "245, 159, 36" },
  { color: "#7c5cff", soft: "#f1edff", rgb: "124, 92, 255" },
  { color: "#0f9aa8", soft: "#eafcff", rgb: "15, 154, 168" },
  { color: "#c43d8f", soft: "#fff0f8", rgb: "196, 61, 143" },
  { color: "#5166d6", soft: "#eef1ff", rgb: "81, 102, 214" },
  { color: "#77820f", soft: "#fbfde8", rgb: "119, 130, 15" },
  { color: "#a55018", soft: "#fff3e8", rgb: "165, 80, 24" },
];

const ASSET_ROLE_OPTIONS = {
  image: [
    { value: "reference_image", label: "参考图", route: "提交", hint: "服装、产品或画面风格参考" },
    { value: "first_frame", label: "首帧图", route: "提交", hint: "作为开场画面参考" },
    { value: "end_frame", label: "尾帧图", route: "提交", hint: "作为结束定格参考" },
    { value: "product_detail", label: "细节图", route: "提交", hint: "突出面料、纹理、版型细节" },
    { value: "workspace_only", label: "仅工作台参考", route: "参考", hint: "只在页面查看和 @ 引用，不提交" },
  ],
  video: [
    { value: "reference_video", label: "动作参考", route: "提交", hint: "参考动作、构图和镜头节奏" },
    { value: "composition_reference", label: "构图参考", route: "提交", hint: "参考景别、机位和运镜" },
    { value: "no_face_motion", label: "无脸动作版", route: "提交", hint: "适合规避清晰人脸失败" },
    { value: "workspace_only", label: "仅工作台参考", route: "参考", hint: "只在页面查看和 @ 引用，不提交" },
  ],
  audio: [
    { value: "reference_audio", label: "背景音乐", route: "提交", hint: "作为参考音频提交" },
    { value: "voice_reference", label: "声音参考", route: "提交", hint: "参考声音质感或节奏" },
    { value: "workspace_only", label: "仅工作台参考", route: "参考", hint: "只在页面试听，不提交" },
  ],
  face: [
    { value: "avatar_reference", label: "AI头像参考", route: "参考", hint: "无脸安全模式下仅作文字描述参考" },
    { value: "workspace_only", label: "仅工作台参考", route: "参考", hint: "不提交给 Seedance" },
  ],
};

const PROMPT_TEMPLATES = [
  {
    title: "女装穿搭展示",
    tag: "OOTD",
    prompt:
      "生成一条 SOSOVE 女装穿搭展示短视频。参考@图片1中的服装版型、颜色、面料纹理和细节设计，模特在日系自然光场景中完成正面、侧面、背面展示。0-2秒展示整体上身效果，2-5秒慢走和转身，5-8秒近景展示领口、袖口、腰线、下摆和面料纹理，最后定格为自然穿搭氛围。画面真实、干净、像买家实拍，不要夸张广告感。",
  },
  {
    title: "商品细节特写",
    tag: "DETAIL",
    prompt:
      "生成一条商品细节特写视频。全程围绕@图片1中的商品，镜头从整体轮廓推进到局部细节，依次展示面料纹理、走线、边缘处理、层次结构和穿着垂感。动作轻柔自然，手部整理衣摆或面料，光线为室内自然光。不要改变商品设计，不要添加价格牌、夸张字幕或无关道具。",
  },
  {
    title: "AI虚拟模特无脸",
    tag: "SAFE",
    prompt:
      "参考@视频1的动作、构图、镜头节奏和身体姿态，重新生成一个新的 AI 虚拟角色穿搭视频。参考视频只用于动作和运镜，不复刻人物身份或面部。角色以文字设定为准，画面尽量使用背影、侧身、头部裁切或不清晰面部构图，突出服装上身效果、版型、面料和整体搭配氛围。",
  },
  {
    title: "第一视角广告",
    tag: "POV",
    prompt:
      "生成一条第一人称视角的 SOSOVE 商品短视频。开场用手拿起@图片1中的商品或包装，随后切到穿搭/使用场景，镜头贴近商品细节，节奏轻快。0-2秒建立场景，2-5秒展示核心卖点，5-8秒展示真实使用或穿着效果，最后镜头拉近商品并自然定格。声音和画面保持真实生活感。",
  },
  {
    title: "首尾帧图生视频",
    tag: "FRAME",
    prompt:
      "以@图片1作为首帧画面，以@图片2作为尾帧目标画面，生成一条连贯的商品展示视频。中间镜头自然过渡，保持商品颜色、结构、材质和细节一致。用轻微推拉、转场和手部整理动作连接首尾帧，画面真实、稳定、没有明显变形。",
  },
  {
    title: "参考视频动作重生成",
    tag: "R2V",
    prompt:
      "全程参考@视频1的动作节奏、构图、镜头语言和身体姿态，重新生成一条新的 SOSOVE 商品展示视频。商品以@图片1为准，严格保持版型、颜色、长度、面料纹理和关键细节。不要复刻参考视频中的人物身份或面部，只保留动作、场景节奏和镜头结构。",
  },
];

const elements = {
  apiKeyState: $("#api-key-state"),
  aiApiState: $("#ai-api-state"),
  modelState: $("#model-state"),
  healthBtn: $("#health-btn"),
  navButtons: $$("[data-scroll-target]"),
  composerForm: $("#composer-form"),
  workspaceViewButtons: $$("[data-workspace-view]"),
  workspacePanes: $$("[data-workspace-pane]"),
  prompt: $("#prompt-input"),
  promptCount: $("#prompt-count"),
  promptMarket: $("#prompt-market-input"),
  promptCustomMarket: $("#prompt-custom-market-input"),
  promptLanguage: $("#prompt-language-select"),
  promptMarketLockState: $("#prompt-market-lock-state"),
  creativeProduct: $("#creative-product-input"),
  creativeMarket: $("#creative-market-input"),
  creativeCustomMarket: $("#creative-custom-market-input"),
  creativeLanguage: $("#creative-language-select"),
  creativeMarketNote: $("#creative-market-note"),
  creativeAudience: $("#creative-audience-input"),
  creativeStyle: $("#creative-style-select"),
  creativeSellingPoints: $("#creative-selling-points-input"),
  creativeScript: $("#creative-script-input"),
  creativeBriefState: $("#creative-brief-state"),
  creativeAiBtn: $("#creative-ai-btn"),
  creativeSkillBtn: $("#creative-skill-btn"),
  generateReadySummary: $("#generate-ready-summary"),
  assetMentionPopover: $("#asset-mention-popover"),
  opsApiState: $("#ops-api-state"),
  opsAiState: $("#ops-ai-state"),
  opsModelState: $("#ops-model-state"),
  opsRatioState: $("#ops-ratio-state"),
  opsAssetState: $("#ops-asset-state"),
  opsWorkspaceState: $("#ops-workspace-state"),
  opsPromptState: $("#ops-prompt-state"),
  opsQualityState: $("#ops-quality-state"),
  opsTaskState: $("#ops-task-state"),
  opsTaskDetailState: $("#ops-task-detail-state"),
  promptTemplateList: $("#prompt-template-list"),
  clearTemplateInsertBtn: $("#clear-template-insert-btn"),
  promptQualityScore: $("#prompt-quality-score"),
  promptQualityList: $("#prompt-quality-list"),
  strengthenPromptBtn: $("#strengthen-prompt-btn"),
  skillReviewPromptBtn: $("#skill-review-prompt-btn"),
  promptSkillReview: $("#prompt-skill-review"),
  promptSkillReviewTitle: $("#prompt-skill-review-title"),
  promptSkillReviewScore: $("#prompt-skill-review-score"),
  promptSkillReviewSummary: $("#prompt-skill-review-summary"),
  promptSkillReviewPreserved: $("#prompt-skill-review-preserved"),
  promptSkillReviewChanges: $("#prompt-skill-review-changes"),
  promptSkillReviewIssues: $("#prompt-skill-review-issues"),
  promptSkillReviewOutput: $("#prompt-skill-review-output"),
  applyPromptSkillReviewBtn: $("#apply-prompt-skill-review-btn"),
  copyPromptSkillReviewBtn: $("#copy-prompt-skill-review-btn"),
  aiBrief: $("#ai-brief-input"),
  skillPromptCount: $("#skill-prompt-count-input"),
  skillGenerateBtn: $("#skill-generate-btn"),
  aiGenerateBtn: $("#ai-generate-btn"),
  skillOutputPanel: $("#skill-output-panel"),
  skillPromptQueue: $("#skill-prompt-queue"),
  skillOutput: $("#skill-output-input"),
  useSkillPromptBtn: $("#use-skill-prompt-btn"),
  submitSkillQueueBtn: $("#submit-skill-queue-btn"),
  copySkillOutputBtn: $("#copy-skill-output-btn"),
  clearPromptHistoryBtn: $("#clear-prompt-history-btn"),
  promptHistoryList: $("#prompt-history-list"),
  arkApiKey: $("#ark-api-key-input"),
  arkEndpoint: $("#ark-endpoint-input"),
  arkConfigState: $("#ark-config-state"),
  clearArkKeyBtn: $("#clear-ark-key-btn"),
  aiApiKey: $("#ai-api-key-input"),
  aiBaseUrl: $("#ai-base-url-input"),
  aiModel: $("#ai-model-input"),
  aiTemperature: $("#ai-temperature-input"),
  aiMaxTokens: $("#ai-max-tokens-input"),
  aiConfigState: $("#ai-config-state"),
  imageApiKey: $("#image-api-key-input"),
  imageBaseUrl: $("#image-base-url-input"),
  imageModel: $("#image-model-input"),
  imageConfigState: $("#image-config-state"),
  imageConfigDetail: $("#image-config-detail"),
  apiConfigPanel: $("#api-config-panel"),
  apiConfigBody: $("#api-config-body"),
  toggleConfigBtn: $("#toggle-config-btn"),
  arkSummaryState: $("#ark-summary-state"),
  aiSummaryState: $("#ai-summary-state"),
  imageSummaryState: $("#image-summary-state"),
  clearAiKeyBtn: $("#clear-ai-key-btn"),
  clearImageKeyBtn: $("#clear-image-key-btn"),
  saveConfigBtn: $("#save-config-btn"),
  testArkConfigBtn: $("#test-ark-config-btn"),
  invokeArkConfigBtn: $("#invoke-ark-config-btn"),
  arkConfigTestDetail: $("#ark-config-test-detail"),
  testAiConfigBtn: $("#test-ai-config-btn"),
  invokeAiConfigBtn: $("#invoke-ai-config-btn"),
  aiConfigTestDetail: $("#ai-config-test-detail"),
  model: $("#model-input"),
  modelHelper: $("#model-helper"),
  modelPresetButtons: $$("[data-model-preset]"),
  workflowConfigState: $("#workflow-config-state"),
  workflowAssetsState: $("#workflow-assets-state"),
  workflowPromptState: $("#workflow-prompt-state"),
  workflowSubmitState: $("#workflow-submit-state"),
  promptHighlightLayer: $("#prompt-highlight-layer"),
  images: $("#images-input"),
  imageUploadZone: $("#image-upload-zone"),
  imageUploadBtn: $("#image-upload-btn"),
  imageUploadInput: $("#image-upload-input"),
  imagePreviewGrid: $("#image-preview-grid"),
  uploadedImageList: $("#uploaded-image-list"),
  uploadHelper: $("#upload-helper"),
  videos: $("#videos-input"),
  videoUploadZone: $("#video-upload-zone"),
  videoUploadBtn: $("#video-upload-btn"),
  videoUploadInput: $("#video-upload-input"),
  videoPreviewGrid: $("#video-preview-grid"),
  uploadedVideoList: $("#uploaded-video-list"),
  videoUploadHelper: $("#video-upload-helper"),
  audios: $("#audios-input"),
  audioUploadZone: $("#audio-upload-zone"),
  audioUploadBtn: $("#audio-upload-btn"),
  audioUploadInput: $("#audio-upload-input"),
  audioPreviewList: $("#audio-preview-list"),
  uploadedAudioList: $("#uploaded-audio-list"),
  audioUploadHelper: $("#audio-upload-helper"),
  faceSwapState: $("#face-swap-state"),
  faceSwapRefs: $("#face-swap-refs-input"),
  faceSwapPreviewGrid: $("#face-swap-preview-grid"),
  faceSwapUploadZone: $("#face-swap-upload-zone"),
  faceSwapUploadBtn: $("#face-swap-upload-btn"),
  faceSwapUploadInput: $("#face-swap-upload-input"),
  uploadedFaceSwapList: $("#uploaded-face-swap-list"),
  faceSwapHelper: $("#face-swap-helper"),
  faceSwapConsent: $("#face-swap-consent"),
  faceSwapVirtual: $("#face-swap-virtual-input"),
  faceSwapSubmit: $("#face-swap-submit-input"),
  faceSwapPrompt: $("#face-swap-prompt-input"),
  applyFaceSwapBtn: $("#apply-face-swap-btn"),
  urlInputs: $$(".url-input"),
  assetImageCount: $("#asset-image-count"),
  assetVideoCount: $("#asset-video-count"),
  assetAudioCount: $("#asset-audio-count"),
  submittedAssetSummary: $("#submitted-asset-summary"),
  submittedAssetList: $("#submitted-asset-list"),
  workspaceAssetSummary: $("#workspace-asset-summary"),
  workspaceAssetList: $("#workspace-asset-list"),
  assetRoleList: $("#asset-role-list"),
  assetRoleNote: $("#asset-role-note"),
  assetCurrentBatchSelect: $("#asset-current-batch-select"),
  assetNewBatchBtn: $("#asset-new-batch-btn"),
  assetBatchNameInput: $("#asset-batch-name-input"),
  assetRenameBatchBtn: $("#asset-rename-batch-btn"),
  assetAssignBatchBtn: $("#asset-assign-batch-btn"),
  assetTagInput: $("#asset-tag-input"),
  assetQuickTags: $("#asset-quick-tags"),
  assetApplyTagsBtn: $("#asset-apply-tags-btn"),
  assetClearFilterBtn: $("#asset-clear-filter-btn"),
  assetCurrentBatchCount: $("#asset-current-batch-count"),
  assetTaggedCount: $("#asset-tagged-count"),
  assetUnbatchedCount: $("#asset-unbatched-count"),
  assetBatchList: $("#asset-batch-list"),
  assetBatchFilterSelect: $("#asset-batch-filter-select"),
  assetTagFilterSelect: $("#asset-tag-filter-select"),
  assetFilterCount: $("#asset-filter-count"),
  assetBatchAssetList: $("#asset-batch-asset-list"),
  preflightSummary: $("#preflight-summary"),
  preflightList: $("#preflight-list"),
  audioToggle: $("#audio-toggle"),
  watermarkToggle: $("#watermark-toggle"),
  quantityInput: $("#quantity-input"),
  quantityMinus: $("#quantity-minus"),
  quantityPlus: $("#quantity-plus"),
  chatInput: $("#chat-input"),
  buildBtn: $("#build-btn"),
  submitBtn: $("#submit-btn"),
  sampleBtn: $("#sample-btn"),
  clearBtn: $("#clear-btn"),
  repairPromptBtn: $("#repair-prompt-btn"),
  parseChatBtn: $("#parse-chat-btn"),
  pollBtn: $("#poll-btn"),
  retryFailedBtn: $("#retry-failed-btn"),
  copyTaskBtn: $("#copy-task-btn"),
  copyJsonBtn: $("#copy-json-btn"),
  clearHistoryBtn: $("#clear-history-btn"),
  taskId: $("#task-id"),
  taskStatus: $("#task-status"),
  taskCountLabel: $("#task-count-label"),
  pollState: $("#poll-state"),
  taskProgress: $("#task-progress"),
  taskProgressBar: $("#task-progress-bar"),
  taskQueueNote: $("#task-queue-note"),
  resultVideoState: $("#result-video-state"),
  copyVideoBtn: $("#copy-video-btn"),
  downloadVideoLink: $("#download-video-link"),
  taskErrorBox: $("#task-error-box"),
  imageLightbox: $("#image-lightbox"),
  imageLightboxImg: $("#image-lightbox-img"),
  imageLightboxTitle: $("#image-lightbox-title"),
  imageLightboxUrl: $("#image-lightbox-url"),
  closeLightboxBtn: $("#close-lightbox-btn"),
  copyLightboxUrlBtn: $("#copy-lightbox-url-btn"),
  videoLightbox: $("#video-lightbox"),
  videoLightboxPlayer: $("#video-lightbox-player"),
  videoLightboxTitle: $("#video-lightbox-title"),
  videoLightboxUrl: $("#video-lightbox-url"),
  closeVideoLightboxBtn: $("#close-video-lightbox-btn"),
  copyVideoLightboxUrlBtn: $("#copy-video-lightbox-url-btn"),
  backToTopBtn: $("#back-to-top-btn"),
  jsonPreview: $("#json-preview"),
  videoStage: $("#video-stage"),
  batchList: $("#batch-list"),
  historyList: $("#history-list"),
  toast: $("#toast"),
};

const sample = {
  brief:
    "白色网纱百褶裙，日系温柔通勤感，突出网纱层次、刺绣花纹、裙摆边缘细节和轻盈垂坠。模特 23-30 岁，日本街头自然走动、慢转身、小幅旋转，画面干净真实，适合 SOSOVE 女装种草短视频。",
  prompt:
    "A 10-second vertical fashion video in 9:16 aspect ratio. A Japanese woman aged 23-30 with an Instagram fashion blogger aesthetic walks naturally through Japanese street scenes. She is wearing the exact same white mesh pleated midi skirt from the reference images. The skirt must replicate the silhouette, white color tone, mesh texture, embroidered floral details, ruffled layered hem, folded edge details, and length proportion. Natural walking, light turning, small twirl, close-up shots of hands brushing the skirt fabric, soft daylight, clean realistic influencer outfit showcase.",
  images:
    "https://img.xn--ohqu9y07ujpb.dpdns.org/file/1775543337530_O1CN01Ix6l7t1ScKwWzFQWh_!!2056652267-0-cib.jpg\nhttps://img.xn--ohqu9y07ujpb.dpdns.org/file/1775543335993_O1CN01WVPNOF1ScKwXfV5qH_!!2056652267-0-cib.jpg",
  videos: "",
  audios: "",
};

function normalizeModelAlias(value) {
  return value.toLowerCase().replace(/\s+/g, "").replace(/_/g, "-");
}

function resolveModel(value) {
  const raw = String(value || "").trim();
  if (!raw) return state.defaultModel || BUILT_IN_MODEL;
  return MODEL_ALIASES[normalizeModelAlias(raw)] || raw;
}

function currentModel() {
  return resolveModel(elements.model.value);
}

function setModel(value) {
  const model = resolveModel(value);
  elements.model.value = model;
  state.model = model;
  updateModelDisplay();
}

function updateModelDisplay() {
  const model = currentModel();
  state.model = model;
  elements.modelState.textContent = model;
  if (elements.modelHelper) {
    elements.modelHelper.textContent = `提交视频时使用：${model}`;
  }
  const rawModel = String(elements.model.value || "").trim();
  elements.modelPresetButtons.forEach((button) => {
    button.classList.toggle("active", String(button.dataset.modelPreset || "").trim() === rawModel);
  });
}

function uniqueUrls(urls) {
  return [...new Set(urls.filter(Boolean))];
}

function assetAccent(index) {
  return ASSET_ACCENTS[index % ASSET_ACCENTS.length];
}

function assetAccentStyle(index) {
  const accent = assetAccent(index);
  return `--asset-color:${accent.color};--asset-soft:${accent.soft};--asset-rgb:${accent.rgb};`;
}

function setAssetAccent(element, index) {
  const accent = assetAccent(index);
  element.style.setProperty("--asset-color", accent.color);
  element.style.setProperty("--asset-soft", accent.soft);
  element.style.setProperty("--asset-rgb", accent.rgb);
}

function loadAssetRoles() {
  try {
    const roles = JSON.parse(window.localStorage.getItem(ASSET_ROLE_KEY) || "{}");
    return roles && typeof roles === "object" && !Array.isArray(roles) ? roles : {};
  } catch {
    return {};
  }
}

function saveAssetRoles() {
  window.localStorage.setItem(ASSET_ROLE_KEY, JSON.stringify(state.assetRoles || {}));
}

function assetRoleKey(kind, url) {
  return `${kind}:${url}`;
}

function defaultAssetRole(kind) {
  return ASSET_ROLE_OPTIONS[kind]?.[0]?.value || "reference";
}

function getAssetRole(kind, url) {
  return state.assetRoles[assetRoleKey(kind, url)] || defaultAssetRole(kind);
}

function setAssetRole(kind, url, role) {
  const options = ASSET_ROLE_OPTIONS[kind] || [];
  const validRole = options.some((item) => item.value === role) ? role : defaultAssetRole(kind);
  const key = assetRoleKey(kind, url);
  if (validRole === defaultAssetRole(kind)) {
    delete state.assetRoles[key];
  } else {
    state.assetRoles[key] = validRole;
  }
  saveAssetRoles();
  displayJson(payloadFromForm());
  showToast("素材角色已更新");
}

function assetRoleMeta(kind, url) {
  const role = getAssetRole(kind, url);
  const options = ASSET_ROLE_OPTIONS[kind] || [];
  return options.find((item) => item.value === role) || options[0] || { value: role, label: role, route: "提交", hint: "" };
}

function shouldSubmitAsset(kind, url) {
  return assetRoleMeta(kind, url).value !== "workspace_only";
}

function roleKindLabel(kind) {
  return {
    image: "图片",
    video: "视频",
    audio: "音频",
    face: "人像",
  }[kind] || "素材";
}

function assetSourceType(kind, url) {
  if (kind === "image" || kind === "face") return imageSourceType(url);
  if (kind === "video") return videoSourceType(url);
  if (kind === "audio") return audioSourceType(url);
  return { label: "素材", className: "external" };
}

function assetToken(kind, index) {
  if (kind === "image") return `图片${index + 1}`;
  if (kind === "video") return `视频${index + 1}`;
  if (kind === "audio") return `音频${index + 1}`;
  return `人像${index + 1}`;
}

function rawAssetEntries() {
  const imageUrls = splitLines(elements.images.value);
  const videoUrls = splitLines(elements.videos.value);
  const audioUrls = splitLines(elements.audios.value);
  const faceUrls = faceSwapRefsFromForm();
  return [
    ...imageUrls.map((url, index) => ({ kind: "image", index, url, token: assetToken("image", index), colorIndex: index })),
    ...videoUrls.map((url, index) => ({ kind: "video", index, url, token: assetToken("video", index), colorIndex: imageUrls.length + index })),
    ...audioUrls.map((url, index) => ({ kind: "audio", index, url, token: assetToken("audio", index), colorIndex: imageUrls.length + videoUrls.length + index })),
    ...faceUrls.map((url, index) => ({ kind: "face", index, url, token: assetToken("face", index), colorIndex: imageUrls.length + videoUrls.length + audioUrls.length + index })),
  ];
}

function defaultAssetBatchName(date = new Date()) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `素材批次 ${month}/${day} ${hour}:${minute}`;
}

function makeAssetBatch(name = "") {
  return {
    id: `batch-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    name: name.trim() || defaultAssetBatchName(),
    createdAt: new Date().toISOString(),
  };
}

function normalizeAssetTag(tag) {
  return String(tag || "").replace(/^#+/, "").trim().slice(0, 18);
}

function splitAssetTags(value) {
  const source = Array.isArray(value) ? value.join(",") : String(value || "");
  return [...new Set(source.split(/[\s,，、#]+/).map(normalizeAssetTag).filter(Boolean))].slice(0, 12);
}

function normalizeAssetBatchState(value) {
  const rawBatches = Array.isArray(value?.batches) ? value.batches : [];
  const batches = rawBatches
    .map((batch) => ({
      id: String(batch?.id || "").trim(),
      name: String(batch?.name || "").trim().slice(0, 40),
      createdAt: String(batch?.createdAt || new Date().toISOString()),
    }))
    .filter((batch) => batch.id && batch.name);
  if (!batches.length) batches.push(makeAssetBatch("默认批次"));

  const rawItems = value?.items && typeof value.items === "object" && !Array.isArray(value.items) ? value.items : {};
  const items = Object.fromEntries(
    Object.entries(rawItems).map(([url, item]) => [
      url,
      {
        batchId: String(item?.batchId || ""),
        tags: splitAssetTags(item?.tags || []),
        kind: String(item?.kind || ""),
        name: String(item?.name || ""),
        size: Number(item?.size || 0),
        contentType: String(item?.contentType || ""),
        addedAt: String(item?.addedAt || item?.uploadedAt || new Date().toISOString()),
      },
    ])
  );

  const activeId = batches.some((batch) => batch.id === value?.activeId) ? value.activeId : batches[0].id;
  const filterBatchId = ["all", "current", "unbatched"].includes(value?.filterBatchId) || batches.some((batch) => batch.id === value?.filterBatchId)
    ? value.filterBatchId
    : "all";
  return {
    activeId,
    filterBatchId,
    filterTag: String(value?.filterTag || "all"),
    batches,
    items,
  };
}

function loadAssetBatches() {
  try {
    return normalizeAssetBatchState(JSON.parse(window.localStorage.getItem(ASSET_BATCH_KEY) || "{}"));
  } catch {
    return normalizeAssetBatchState({});
  }
}

function ensureAssetBatchState() {
  if (!state.assetBatches) state.assetBatches = loadAssetBatches();
  return state.assetBatches;
}

function saveAssetBatches() {
  window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(ensureAssetBatchState()));
}

function activeAssetBatch() {
  const batchState = ensureAssetBatchState();
  return batchState.batches.find((batch) => batch.id === batchState.activeId) || batchState.batches[0];
}

function uploadedKindForBatch(kind) {
  return kind === "face-swap" ? "face" : kind;
}

function assetBatchItem(url) {
  return ensureAssetBatchState().items[url] || null;
}

function assetEntryBatchId(entry) {
  const batchId = assetBatchItem(entry.url)?.batchId || "";
  return ensureAssetBatchState().batches.some((batch) => batch.id === batchId) ? batchId : "";
}

function assetEntryTags(entry) {
  return splitAssetTags(assetBatchItem(entry.url)?.tags || []);
}

function enrichedAssetEntries() {
  return rawAssetEntries().map((entry) => ({
    ...entry,
    batchId: assetEntryBatchId(entry),
    tags: assetEntryTags(entry),
  }));
}

function upsertAssetBatchItem(entry, patch = {}) {
  const batchState = ensureAssetBatchState();
  const previous = batchState.items[entry.url] || {};
  const tags = patch.tags === undefined ? splitAssetTags(previous.tags || []) : splitAssetTags(patch.tags || []);
  batchState.items[entry.url] = {
    ...previous,
    kind: patch.kind || previous.kind || entry.kind,
    name: patch.name || previous.name || materialDisplayName(entry.url),
    size: Number(patch.size ?? previous.size ?? 0),
    contentType: patch.contentType || previous.contentType || "",
    batchId: patch.batchId === undefined ? String(previous.batchId || "") : String(patch.batchId || ""),
    tags,
    addedAt: previous.addedAt || patch.addedAt || new Date().toISOString(),
  };
}

function registerUploadedMaterials(materials, options) {
  const uploaded = Array.isArray(materials) ? materials.filter((material) => material?.url) : [];
  if (!uploaded.length) return;
  const batch = activeAssetBatch();
  uploaded.forEach((material) => {
    upsertAssetBatchItem(
      { kind: uploadedKindForBatch(options.kind), url: material.url },
      {
        kind: uploadedKindForBatch(options.kind),
        batchId: batch.id,
        name: material.name || "",
        size: material.size,
        contentType: material.contentType,
        addedAt: new Date().toISOString(),
      }
    );
  });
  saveAssetBatches();
  renderAssetBatchPanel();
}

function uniqueBatchTags(entries = enrichedAssetEntries()) {
  return [...new Set(entries.flatMap((entry) => entry.tags || []))].sort((a, b) => a.localeCompare(b, "zh-CN"));
}

function getAssetBatchName(batchId) {
  return ensureAssetBatchState().batches.find((batch) => batch.id === batchId)?.name || "未分批";
}

function renderBatchSelect(select, options, selectedValue) {
  if (!select) return;
  select.innerHTML = options
    .map((option) => `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`)
    .join("");
  select.value = selectedValue;
}

function tagInputTags() {
  return splitAssetTags(elements.assetTagInput?.value || "");
}

function setTagInputTags(tags) {
  if (!elements.assetTagInput) return;
  elements.assetTagInput.value = splitAssetTags(tags).join("、");
}

function addTagsToEntry(entry, tags) {
  const nextTags = [...new Set([...(entry.tags || []), ...splitAssetTags(tags)])];
  upsertAssetBatchItem(entry, { tags: nextTags, batchId: entry.batchId || activeAssetBatch().id });
}

function assignCurrentAssetsToActiveBatch() {
  const batch = activeAssetBatch();
  const entries = enrichedAssetEntries();
  if (!entries.length) {
    showToast("当前没有可归档素材");
    return;
  }
  entries.forEach((entry) => upsertAssetBatchItem(entry, { batchId: batch.id, tags: entry.tags }));
  ensureAssetBatchState().filterBatchId = batch.id;
  saveAssetBatches();
  displayJson(payloadFromForm());
  showToast(`已归入「${batch.name}」`);
}

function applyTagsToActiveBatch(tags = tagInputTags()) {
  const nextTags = splitAssetTags(tags);
  if (!nextTags.length) {
    showToast("先输入标签");
    return;
  }
  const batch = activeAssetBatch();
  const entries = enrichedAssetEntries();
  let targets = entries.filter((entry) => entry.batchId === batch.id);
  if (!targets.length && entries.length) {
    targets = entries;
    targets.forEach((entry) => upsertAssetBatchItem(entry, { batchId: batch.id, tags: entry.tags }));
  }
  if (!targets.length) {
    setTagInputTags(nextTags);
    showToast("当前批次暂无素材");
    return;
  }
  targets.forEach((entry) => addTagsToEntry({ ...entry, batchId: batch.id }, nextTags));
  saveAssetBatches();
  displayJson(payloadFromForm());
  showToast(`已给 ${targets.length} 个素材打标签`);
}

function createAssetBatchFromInput() {
  const batchState = ensureAssetBatchState();
  const batch = makeAssetBatch(elements.assetBatchNameInput?.value || "");
  batchState.batches.unshift(batch);
  batchState.activeId = batch.id;
  batchState.filterBatchId = batch.id;
  saveAssetBatches();
  displayJson(payloadFromForm());
  showToast(`已新建「${batch.name}」`);
}

function renameActiveAssetBatch() {
  const batch = activeAssetBatch();
  const name = String(elements.assetBatchNameInput?.value || "").trim().slice(0, 40);
  if (!name) {
    showToast("批次名称不能为空");
    return;
  }
  batch.name = name;
  saveAssetBatches();
  displayJson(payloadFromForm());
  showToast("批次名称已保存");
}

function setActiveAssetBatch(batchId) {
  const batchState = ensureAssetBatchState();
  if (!batchState.batches.some((batch) => batch.id === batchId)) return;
  batchState.activeId = batchId;
  batchState.filterBatchId = batchId;
  saveAssetBatches();
  displayJson(payloadFromForm());
}

function filterAssetBatchEntries(entries) {
  const batchState = ensureAssetBatchState();
  let result = entries;
  if (batchState.filterBatchId === "current") {
    result = result.filter((entry) => entry.batchId === batchState.activeId);
  } else if (batchState.filterBatchId === "unbatched") {
    result = result.filter((entry) => !entry.batchId);
  } else if (batchState.filterBatchId !== "all") {
    result = result.filter((entry) => entry.batchId === batchState.filterBatchId);
  }

  if (batchState.filterTag === "untagged") {
    result = result.filter((entry) => !entry.tags.length);
  } else if (batchState.filterTag !== "all") {
    result = result.filter((entry) => entry.tags.includes(batchState.filterTag));
  }
  return result;
}

function renderAssetBatchPanel() {
  if (!elements.assetBatchAssetList) return;
  const batchState = ensureAssetBatchState();
  const batches = batchState.batches;
  const active = activeAssetBatch();
  const entries = enrichedAssetEntries();
  const activeEntries = entries.filter((entry) => entry.batchId === active.id);
  const taggedEntries = entries.filter((entry) => entry.tags.length);
  const unbatchedEntries = entries.filter((entry) => !entry.batchId);
  const allTags = uniqueBatchTags(entries);
  const selectedFilterTag = allTags.includes(batchState.filterTag) || ["all", "untagged"].includes(batchState.filterTag) ? batchState.filterTag : "all";
  batchState.filterTag = selectedFilterTag;

  renderBatchSelect(
    elements.assetCurrentBatchSelect,
    batches.map((batch) => ({ value: batch.id, label: batch.name })),
    active.id
  );
  renderBatchSelect(
    elements.assetBatchFilterSelect,
    [
      { value: "all", label: "全部素材" },
      { value: "current", label: "当前批次" },
      { value: "unbatched", label: "未分批" },
      ...batches.map((batch) => ({ value: batch.id, label: batch.name })),
    ],
    batchState.filterBatchId
  );
  renderBatchSelect(
    elements.assetTagFilterSelect,
    [
      { value: "all", label: "全部标签" },
      { value: "untagged", label: "未打标签" },
      ...allTags.map((tag) => ({ value: tag, label: `#${tag}` })),
    ],
    selectedFilterTag
  );

  if (elements.assetBatchNameInput && document.activeElement !== elements.assetBatchNameInput) {
    elements.assetBatchNameInput.value = active.name;
  }
  if (elements.assetCurrentBatchCount) elements.assetCurrentBatchCount.textContent = String(activeEntries.length);
  if (elements.assetTaggedCount) elements.assetTaggedCount.textContent = String(taggedEntries.length);
  if (elements.assetUnbatchedCount) elements.assetUnbatchedCount.textContent = String(unbatchedEntries.length);

  renderAssetQuickTags(activeEntries);
  renderAssetBatchList(entries);
  renderAssetBatchAssetList(filterAssetBatchEntries(entries), entries.length);
}

function renderAssetQuickTags(activeEntries) {
  if (!elements.assetQuickTags) return;
  elements.assetQuickTags.innerHTML = "";
  DEFAULT_ASSET_TAGS.forEach((tag) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `#${tag}`;
    button.addEventListener("click", () => {
      if (!activeEntries.length) {
        setTagInputTags([...tagInputTags(), tag]);
        showToast(`#${tag} 已加入标签框`);
        return;
      }
      applyTagsToActiveBatch([tag]);
    });
    elements.assetQuickTags.appendChild(button);
  });
}

function renderAssetBatchList(entries) {
  if (!elements.assetBatchList) return;
  const batchState = ensureAssetBatchState();
  elements.assetBatchList.innerHTML = "";
  batchState.batches.forEach((batch) => {
    const batchEntries = entries.filter((entry) => entry.batchId === batch.id);
    const tagCount = uniqueBatchTags(batchEntries).length;
    const item = document.createElement("article");
    item.className = `asset-batch-item ${batch.id === batchState.activeId ? "active" : ""}`;
    item.innerHTML = `
      <button type="button" data-batch-id="${escapeHtml(batch.id)}">
        <strong>${escapeHtml(batch.name)}</strong>
        <small>${batchEntries.length} 个素材 · ${tagCount} 个标签</small>
      </button>
    `;
    item.querySelector("button").addEventListener("click", () => setActiveAssetBatch(batch.id));
    elements.assetBatchList.appendChild(item);
  });
}

function renderAssetBatchAssetList(entries, totalCount) {
  if (!elements.assetBatchAssetList) return;
  if (elements.assetFilterCount) elements.assetFilterCount.textContent = `${entries.length}/${totalCount} 个素材`;
  if (!totalCount) {
    elements.assetBatchAssetList.innerHTML = `
      <article class="asset-batch-empty">
        <strong>暂无素材</strong>
        <small>上传或粘贴素材 URL 后，这里会显示批次和标签。</small>
      </article>
    `;
    return;
  }
  if (!entries.length) {
    elements.assetBatchAssetList.innerHTML = `
      <article class="asset-batch-empty">
        <strong>没有匹配素材</strong>
        <small>调整批次或标签筛选。</small>
      </article>
    `;
    return;
  }

  const batches = ensureAssetBatchState().batches;
  elements.assetBatchAssetList.innerHTML = "";
  entries.forEach((entry) => {
    const source = assetSourceType(entry.kind, entry.url);
    const row = document.createElement("article");
    row.className = `asset-batch-asset ${entry.batchId ? "batched" : "unbatched"}`;
    setAssetAccent(row, entry.colorIndex);
    row.innerHTML = `
      <span class="asset-batch-token">${escapeHtml(entry.token)}</span>
      <div class="asset-batch-asset-main">
        <strong>${escapeHtml(materialDisplayName(entry.url))}</strong>
        <small>${escapeHtml(roleKindLabel(entry.kind))} · ${escapeHtml(source.label)} · ${escapeHtml(getAssetBatchName(entry.batchId))}</small>
        <div class="asset-batch-tags">
          ${entry.tags.length ? entry.tags.map((tag) => `<button type="button" data-action="remove-tag" data-tag="${escapeHtml(tag)}">#${escapeHtml(tag)}</button>`).join("") : "<span>未打标签</span>"}
        </div>
      </div>
      <select aria-label="${escapeHtml(entry.token)}所属批次">
        <option value="">未分批</option>
        ${batches.map((batch) => `<option value="${escapeHtml(batch.id)}" ${batch.id === entry.batchId ? "selected" : ""}>${escapeHtml(batch.name)}</option>`).join("")}
      </select>
      <div class="asset-batch-row-actions">
        <button type="button" data-action="tag">打标签</button>
        <button type="button" data-action="copy">复制</button>
      </div>
    `;
    row.querySelector("select").addEventListener("change", (event) => {
      upsertAssetBatchItem(entry, { batchId: event.target.value, tags: entry.tags });
      saveAssetBatches();
      displayJson(payloadFromForm());
      showToast(event.target.value ? "素材批次已更新" : "素材已设为未分批");
    });
    row.querySelector('[data-action="tag"]').addEventListener("click", () => {
      const tags = tagInputTags();
      if (!tags.length) {
        showToast("先输入标签");
        return;
      }
      addTagsToEntry(entry, tags);
      saveAssetBatches();
      displayJson(payloadFromForm());
      showToast(`${entry.token} 已打标签`);
    });
    row.querySelector('[data-action="copy"]').addEventListener("click", async () => {
      await navigator.clipboard.writeText(entry.url);
      showToast("素材 URL 已复制");
    });
    row.querySelectorAll('[data-action="remove-tag"]').forEach((button) => {
      button.addEventListener("click", () => {
        const nextTags = entry.tags.filter((tag) => tag !== button.dataset.tag);
        upsertAssetBatchItem(entry, { tags: nextTags, batchId: entry.batchId });
        saveAssetBatches();
        displayJson(payloadFromForm());
        showToast(`#${button.dataset.tag} 已移除`);
      });
    });
    elements.assetBatchAssetList.appendChild(row);
  });
}

function faceSwapRefsFromForm() {
  return splitLines(elements.faceSwapRefs.value);
}

function faceSwapInstructionFromForm() {
  const refs = faceSwapRefsFromForm();
  if (!refs.length || !elements.faceSwapConsent.checked) return "";
  const virtualMode = Boolean(elements.faceSwapVirtual?.checked);
  const submittingFaces = Boolean(elements.faceSwapSubmit?.checked);
  const fallback = virtualMode
    ? "AI 虚拟角色，使用文字描述定义头像特征；参考视频只用于动作、构图、镜头节奏和身体姿态，重新生成一个新视频。"
    : "使用授权人像作为已授权人物外观参考，请尽量保持人物气质、发型、妆容和面部风格的一致性；不要承诺精准身份替换，若模型限制真人人脸参考，则优先保持服装、动作、镜头和品牌风格一致。";
  const detail = elements.faceSwapPrompt.value.trim() || fallback;
  const labels = refs.map((_, index) => `授权人像${index + 1}`).join("、");
  return virtualMode && !submittingFaces
    ? `AI 虚拟角色无脸安全模式：头像图片仅作为工作台参考，不提交给模型。请根据以下文字设定生成虚拟角色：${detail} 原视频或参考视频只用于动作、构图、镜头节奏和身体姿态。`
    : virtualMode
      ? `AI 虚拟角色重生成要求：使用${labels}作为豆包/AI 生成的虚拟角色外观参考。${detail}`
      : `授权人像参考要求：使用${labels}作为已授权人像参考。${detail}`;
}

function marketLocalizationInstruction() {
  const market = creativeMarketValue();
  const language = resolvedCreativeLanguage();
  return `生成市场锁定（最高优先级）：目标国家/市场为${market}。人物、日常场景、服装搭配和内容节奏必须符合${market}真实本地语境，避免国家刻板印象；忽略原提示词中与该国家冲突的旧地区描述。如有口播、对白或字幕，使用${language}和当地自然口语，不要翻译腔。不得改变用户提供的商品事实和参考素材职责。`;
}

function promptWithMarketLocalization(basePrompt) {
  if (!basePrompt) return "";
  if (basePrompt.includes("生成市场锁定（最高优先级）")) return basePrompt;
  return `${marketLocalizationInstruction()}\n\n${basePrompt}`;
}

function promptFromForm() {
  const virtualMode = Boolean(elements.faceSwapVirtual?.checked);
  const basePrompt = virtualMode ? normalizeVirtualAvatarPrompt(elements.prompt.value.trim()) : elements.prompt.value.trim();
  return promptWithFaceSwapInstruction(promptWithMarketLocalization(basePrompt));
}

function promptWithFaceSwapInstruction(basePrompt) {
  const faceSwapInstruction = faceSwapInstructionFromForm();
  if (!faceSwapInstruction || basePrompt.includes(faceSwapInstruction)) return basePrompt;
  return [basePrompt, faceSwapInstruction].filter(Boolean).join("\n\n");
}

function payloadFromForm() {
  const faceSwapRefs = faceSwapRefsFromForm();
  const faceSwapSubmit = Boolean(elements.faceSwapSubmit?.checked);
  const faceSwapVirtual = Boolean(elements.faceSwapVirtual?.checked);
  const refImages = uniqueUrls([
    ...splitLines(elements.images.value).filter((url) => shouldSubmitAsset("image", url)),
    ...(faceSwapSubmit ? faceSwapRefs : []),
  ]);
  return {
    prompt: promptFromForm(),
    targetMarket: creativeMarketValue(),
    contentLanguage: resolvedCreativeLanguage(),
    ratio: state.ratio,
    duration: state.duration,
    model: currentModel(),
    refImages,
    refVideos: splitLines(elements.videos.value).filter((url) => shouldSubmitAsset("video", url)),
    refAudios: splitLines(elements.audios.value).filter((url) => shouldSubmitAsset("audio", url)),
    faceSwapRefs,
    faceSwapConsent: elements.faceSwapConsent.checked,
    faceSwapVirtual,
    faceSwapSubmit,
    faceSwapPrompt: elements.faceSwapPrompt.value.trim(),
    generateAudio: elements.audioToggle.checked,
    watermark: elements.watermarkToggle.checked,
    quantity: state.quantity,
  };
}

function hasVisualReference(payload = payloadFromForm()) {
  return Boolean(payload.refImages.length || payload.refVideos.length);
}

function hasUsableSkillPromptQueue() {
  return state.skillPrompts.some((item) => String(item?.prompt || "").trim());
}

function skillQueueGateReason(payload = payloadFromForm()) {
  if (!state.skillPrompts.length) return "请先生成 Prompt 队列";
  if (!hasUsableSkillPromptQueue()) return "请先填写至少一条可生成的 Prompt";
  if (!hasVisualReference(payload)) return "请先上传/填写至少一张参考图或一条参考视频";
  return "";
}

function updateSkillQueueSubmitState(payload = payloadFromForm()) {
  if (!elements.submitSkillQueueBtn) return;
  const reason = skillQueueGateReason(payload);
  const hasReference = hasVisualReference(payload);
  elements.submitSkillQueueBtn.disabled = Boolean(reason);
  elements.submitSkillQueueBtn.title = reason || "按 Prompt 队列依次提交视频生成";
  updateSkillPromptQueueVisualState(hasReference);
}

function createSkillPromptGate() {
  const gate = document.createElement("article");
  gate.className = "skill-prompt-empty skill-prompt-gate";
  gate.innerHTML = `
    <strong>队列已准备，先上传参考图/视频</strong>
    <small>上传或填写至少一张参考图，或一条参考视频后，才能按队列生成素材。</small>
  `;
  return gate;
}

function updateSkillPromptQueueVisualState(hasReference) {
  if (!elements.skillPromptQueue) return;
  elements.skillPromptQueue.querySelectorAll('[data-action="submit-one"]').forEach((button) => {
    const index = Number(button.dataset.promptIndex || -1);
    const hasPrompt = Boolean(String(state.skillPrompts[index]?.prompt || "").trim());
    button.disabled = !hasReference || !hasPrompt;
    button.title = !hasPrompt ? "请先填写这条 Prompt" : hasReference ? "生成此条 Prompt" : "请先上传/填写参考图或参考视频";
  });

  const existingGate = elements.skillPromptQueue.querySelector(".skill-prompt-gate");
  if (!state.skillPrompts.length) {
    existingGate?.remove();
    return;
  }
  if (!hasReference && !existingGate) {
    elements.skillPromptQueue.prepend(createSkillPromptGate());
    return;
  }
  if (existingGate) existingGate.hidden = hasReference;
}

function requireSkillQueueVisualReference(payload = payloadFromForm()) {
  if (hasVisualReference(payload)) return true;
  showToast("请先上传/填写至少一张参考图或一条参考视频，再队列生成素材");
  renderPreflight(payload);
  updateSkillQueueSubmitState(payload);
  scrollToWorkspaceSection("#reference-panel-section");
  return false;
}

function configPayload(options = {}) {
  return {
    arkApiKey: elements.arkApiKey.value.trim(),
    arkEndpoint: elements.arkEndpoint.value.trim(),
    seedanceModel: currentModel(),
    aiApiKey: elements.aiApiKey.value.trim(),
    aiBaseUrl: elements.aiBaseUrl.value.trim(),
    aiModel: elements.aiModel.value.trim(),
    aiTemperature: elements.aiTemperature.value,
    aiMaxTokens: elements.aiMaxTokens.value,
    imageGenerationApiKey: elements.imageApiKey.value.trim(),
    imageGenerationBaseUrl: elements.imageBaseUrl.value.trim(),
    imageGenerationModel: elements.imageModel.value.trim(),
    clearArkApiKey: Boolean(options.clearArkApiKey),
    clearAiApiKey: Boolean(options.clearAiApiKey),
    clearImageGenerationApiKey: Boolean(options.clearImageGenerationApiKey),
  };
}

function applyConfig(config) {
  if (!config) return;
  const ark = config.ark || {};
  const ai = config.ai || {};
  const image = config.imageGeneration || {};

  elements.arkEndpoint.value = ark.endpoint || elements.arkEndpoint.value;
  state.defaultModel = ark.model || state.defaultModel || BUILT_IN_MODEL;
  setModel(ark.model || state.defaultModel);
  elements.arkConfigState.textContent = ark.hasApiKey ? `已配置 ${ark.apiKeyPreview || "Ark Key"}` : "未配置 Ark Key";
  elements.arkConfigState.classList.toggle("ok", Boolean(ark.hasApiKey));
  elements.arkSummaryState.textContent = ark.hasApiKey ? "已配置" : "未配置";
  elements.arkSummaryState.classList.toggle("ok", Boolean(ark.hasApiKey));
  elements.apiKeyState.textContent = ark.hasApiKey ? "已配置 ARK_API_KEY" : "未配置 ARK_API_KEY";
  elements.apiKeyState.style.color = ark.hasApiKey ? "var(--blue)" : "var(--cinnabar)";

  elements.aiBaseUrl.value = ai.baseUrl || elements.aiBaseUrl.value;
  elements.aiModel.value = ai.model || elements.aiModel.value;
  elements.aiTemperature.value = ai.temperature ?? elements.aiTemperature.value;
  elements.aiMaxTokens.value = ai.maxTokens ?? elements.aiMaxTokens.value;
  elements.aiConfigState.textContent = ai.hasApiKey ? `已配置 ${ai.apiKeyPreview || "AI Key"}` : "未配置 AI Key";
  elements.aiConfigState.classList.toggle("ok", Boolean(ai.hasApiKey));
  elements.aiSummaryState.textContent = ai.hasApiKey ? ai.model || "已配置" : "未配置";
  elements.aiSummaryState.classList.toggle("ok", Boolean(ai.hasApiKey));
  elements.aiApiState.textContent = ai.hasApiKey ? ai.model || "已配置" : "未配置";
  elements.aiApiState.style.color = ai.hasApiKey ? "var(--blue)" : "var(--cinnabar)";
  elements.aiGenerateBtn.disabled = !ai.hasApiKey;
  elements.aiGenerateBtn.title = ai.hasApiKey ? `使用 ${ai.model}` : "请先配置 AI API Key";
  elements.skillGenerateBtn.disabled = !ai.hasApiKey;
  elements.skillGenerateBtn.title = ai.hasApiKey ? `使用 ${ai.model} 和本地 skill` : "请先配置 AI API Key";

  elements.imageBaseUrl.value = image.baseUrl || elements.imageBaseUrl.value;
  elements.imageModel.value = image.model || elements.imageModel.value;
  elements.imageConfigState.textContent = image.hasApiKey ? `已配置 ${image.apiKeyPreview || "图片 Key"}` : "未配置图片 Key";
  elements.imageConfigState.classList.toggle("ok", Boolean(image.hasApiKey));
  elements.imageSummaryState.textContent = image.hasApiKey ? image.model || "已配置" : "未配置";
  elements.imageSummaryState.classList.toggle("ok", Boolean(image.hasApiKey));
  elements.imageConfigDetail.dataset.tone = image.hasApiKey ? "ok" : "idle";
  elements.imageConfigDetail.querySelector("strong").textContent = image.hasApiKey
    ? `${image.model || "图片模型"} · ${image.baseUrl || "图片接口已配置"}`
    : "用于关键帧图片生成；保存后 Ad Lab 自动读取";
  elements.imageConfigDetail.title = [image.baseUrl, image.model].filter(Boolean).join("\n");
  elements.arkApiKey.value = "";
  elements.aiApiKey.value = "";
  elements.imageApiKey.value = "";
  displayJson(payloadFromForm());
}

async function loadConfig() {
  const result = await requestJson("/api/config");
  applyConfig(result.config);
  return result.config;
}

async function saveConfig(options = {}) {
  const originalText = elements.saveConfigBtn.textContent;
  elements.saveConfigBtn.disabled = true;
  elements.saveConfigBtn.textContent = "保存中";
  try {
    const result = await requestJson("/api/config", {
      method: "POST",
      body: JSON.stringify(configPayload(options)),
    });
    applyConfig(result.config);
    showToast("模型接口配置已保存");
  } finally {
    elements.saveConfigBtn.disabled = false;
    elements.saveConfigBtn.textContent = originalText;
  }
}

function renderConfigTestResult(kind, mode, item) {
  const isArk = kind === "ark";
  const stateNode = isArk ? elements.arkConfigState : elements.aiConfigState;
  const detail = isArk ? elements.arkConfigTestDetail : elements.aiConfigTestDetail;
  if (!item || !stateNode || !detail) return;
  const latency = Number(item.latencyMs || 0) > 0 ? ` · ${Number(item.latencyMs)}ms` : "";
  const status = item.httpStatus ? ` · HTTP ${item.httpStatus}` : "";
  const prefix = item.ok ? (mode === "invoke" ? "模型可调用" : "节点已连通") : item.networkOk ? "节点已响应，需处理" : "连接失败";
  stateNode.textContent = `${prefix}${latency}`;
  stateNode.classList.toggle("ok", Boolean(item.ok));
  stateNode.classList.toggle("warn", Boolean(!item.ok && item.networkOk));
  const tone = item.ok ? "ok" : item.networkOk ? "warn" : "error";
  detail.dataset.tone = tone;
  detail.querySelector("span").textContent = mode === "invoke" ? "MODEL" : "NETWORK";
  detail.querySelector("strong").textContent = [item.message || "状态待检查", status, item.reply ? `回复：${item.reply}` : "", item.taskId ? `测试任务：${item.taskId}` : ""].filter(Boolean).join(" · ");
  detail.title = [item.endpoint, item.model, item.message].filter(Boolean).join("\n");
}

async function testConfig(kind, mode = "connectivity") {
  const isArk = kind === "ark";
  const button = mode === "invoke"
    ? (isArk ? elements.invokeArkConfigBtn : elements.invokeAiConfigBtn)
    : (isArk ? elements.testArkConfigBtn : elements.testAiConfigBtn);
  const label = isArk ? "视频接口" : "AI 接口";
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = mode === "invoke" ? "试调用中" : "检测中";
  try {
    const result = await requestJson(`/api/config/test/${kind}`, {
      method: "POST",
      body: JSON.stringify({ ...configPayload(), testMode: mode }),
    });
    const item = result.result?.[kind];
    renderConfigTestResult(kind, mode, item);
    showToast(item?.message || `${label}待检查`);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function splitLines(value) {
  return value
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function appendMaterialUrls(textarea, urls) {
  const existing = splitLines(textarea.value);
  const next = [...new Set([...existing, ...urls.filter(Boolean)])];
  textarea.value = next.join("\n");
  autoResizeTextarea(textarea);
  displayJson(payloadFromForm());
}

function appendImageUrls(urls) {
  appendMaterialUrls(elements.images, urls);
}

function renderUploadedMaterials(items, options) {
  if (!items.length || !options.list) return;
  const fragment = document.createDocumentFragment();
  items.forEach((material) => {
    const item = document.createElement("article");
    item.className = `uploaded-material-item uploaded-${options.kind}-item`;
    item.dataset.url = material.url;
    const preview = options.preview === "image"
      ? `<img src="${escapeHtml(material.url)}" alt="${escapeHtml(material.name || "uploaded material")}">`
      : `<div class="material-file-icon" aria-hidden="true">${escapeHtml(options.icon || "+")}</div>`;
    item.innerHTML = `
      ${preview}
      <div>
        <strong>${escapeHtml(material.name || options.fallbackName)}</strong>
        <small>${formatBytes(material.size)} · ${material.isPublic ? "公网 URL" : "本地 URL"}</small>
      </div>
      <div class="material-actions">
        <button type="button" data-action="copy" data-url="${escapeHtml(material.url)}">复制</button>
        <button type="button" data-action="remove" data-url="${escapeHtml(material.url)}">移除</button>
      </div>
    `;
    item.querySelector('[data-action="copy"]').addEventListener("click", async () => {
      await navigator.clipboard.writeText(material.url);
      showToast(options.copiedMessage);
    });
    item.querySelector('[data-action="remove"]').addEventListener("click", () => {
      removeMaterialUrl(options.textarea, material.url);
      item.remove();
      showToast(`${options.fallbackName}已移除`);
    });
    fragment.appendChild(item);
  });
  options.list.prepend(fragment);
}

function removeMaterialUrl(textarea, url) {
  const next = splitLines(textarea.value).filter((item) => item !== url);
  textarea.value = next.join("\n");
  removeUploadedMaterialItem(textarea, url);
  autoResizeTextarea(textarea);
  displayJson(payloadFromForm());
}

function removeUploadedMaterialItem(textarea, url) {
  const list =
    textarea === elements.images
      ? elements.uploadedImageList
      : textarea === elements.videos
        ? elements.uploadedVideoList
      : textarea === elements.audios
        ? elements.uploadedAudioList
        : textarea === elements.faceSwapRefs
          ? elements.uploadedFaceSwapList
          : null;
  if (!list) return;
  list.querySelectorAll(".uploaded-material-item").forEach((item) => {
    if (item.dataset.url === url) item.remove();
  });
}

function renderUploadedImages(images) {
  renderUploadedMaterials(images, {
    kind: "image",
    preview: "image",
    fallbackName: "图片素材",
    copiedMessage: "图片 URL 已复制",
    list: elements.uploadedImageList,
    textarea: elements.images,
  });
}

function formatBytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function filterUploadFiles(fileList, fileTypePrefix, extensions) {
  return [...(fileList || [])].filter((file) => {
    if (!file) return false;
    const type = String(file.type || "").toLowerCase();
    const name = String(file.name || "").toLowerCase();
    return type.startsWith(fileTypePrefix) || extensions.some((extension) => name.endsWith(extension));
  });
}

async function uploadMaterialFiles(fileList, options) {
  const files = filterUploadFiles(fileList, options.fileTypePrefix, options.extensions);
  if (!files.length) {
    showToast(options.emptyMessage);
    return;
  }

  const originalText = options.button.textContent;
  options.button.disabled = true;
  options.button.textContent = "上传中";
  options.zone.classList.add("uploading");

  try {
    const formData = new FormData();
    files.forEach((file) => formData.append(options.fieldName, file));
    const response = await fetch(options.endpoint, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `上传失败：${response.status}`);
    }
    const materials = Array.isArray(payload[options.responseKey]) ? payload[options.responseKey] : Array.isArray(payload.items) ? payload.items : [];
    appendMaterialUrls(options.textarea, materials.map((material) => material.url));
    registerUploadedMaterials(materials, options);
    renderUploadedMaterials(materials, options);
    if (options.helper) {
      options.helper.textContent = payload.warning || options.helperMessage;
    }
    showToast(options.doneMessage(materials.length));
  } catch (error) {
    showToast(error.message);
  } finally {
    options.button.disabled = false;
    options.button.textContent = originalText;
    options.zone.classList.remove("uploading", "drag-over");
    options.input.value = "";
  }
}

async function uploadImageFiles(fileList) {
  await uploadMaterialFiles(fileList, {
    kind: "image",
    preview: "image",
    fileTypePrefix: "image/",
    extensions: [".jpg", ".jpeg", ".png", ".webp", ".gif"],
    fieldName: "images",
    endpoint: "/api/uploads/images",
    responseKey: "images",
    textarea: elements.images,
    zone: elements.imageUploadZone,
    button: elements.imageUploadBtn,
    input: elements.imageUploadInput,
    list: elements.uploadedImageList,
    helper: elements.uploadHelper,
    fallbackName: "图片素材",
    copiedMessage: "图片 URL 已复制",
    emptyMessage: "请选择图片文件",
    helperMessage: "图片已上传并写入参考图 URL。",
    doneMessage: (count) => `已上传 ${count} 张图片素材`,
  });
}

async function uploadFaceSwapFiles(fileList) {
  await uploadMaterialFiles(fileList, {
    kind: "face-swap",
    preview: "image",
    fileTypePrefix: "image/",
    extensions: [".jpg", ".jpeg", ".png", ".webp", ".gif"],
    fieldName: "images",
    endpoint: "/api/uploads/images",
    responseKey: "images",
    textarea: elements.faceSwapRefs,
    zone: elements.faceSwapUploadZone,
    button: elements.faceSwapUploadBtn,
    input: elements.faceSwapUploadInput,
    list: elements.uploadedFaceSwapList,
    helper: elements.faceSwapHelper,
    fallbackName: "授权人像素材",
    copiedMessage: "授权人像 URL 已复制",
    emptyMessage: "请选择授权人像图片文件",
    helperMessage: "授权人像已上传并写入人像参考素材 URL。",
    doneMessage: (count) => `已上传 ${count} 张授权人像素材`,
  });
}

async function uploadVideoFiles(fileList) {
  await uploadMaterialFiles(fileList, {
    kind: "video",
    icon: "▶",
    fileTypePrefix: "video/",
    extensions: [".mp4", ".mov", ".webm", ".m4v"],
    fieldName: "videos",
    endpoint: "/api/uploads/videos",
    responseKey: "videos",
    textarea: elements.videos,
    zone: elements.videoUploadZone,
    button: elements.videoUploadBtn,
    input: elements.videoUploadInput,
    list: elements.uploadedVideoList,
    helper: elements.videoUploadHelper,
    fallbackName: "视频素材",
    copiedMessage: "视频 URL 已复制",
    emptyMessage: "请选择视频文件",
    helperMessage: "视频已上传并写入参考视频 URL。",
    doneMessage: (count) => `已上传 ${count} 个视频素材`,
  });
}

async function uploadAudioFiles(fileList) {
  await uploadMaterialFiles(fileList, {
    kind: "audio",
    icon: "♪",
    fileTypePrefix: "audio/",
    extensions: [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm", ".flac"],
    fieldName: "audios",
    endpoint: "/api/uploads/audios",
    responseKey: "audios",
    textarea: elements.audios,
    zone: elements.audioUploadZone,
    button: elements.audioUploadBtn,
    input: elements.audioUploadInput,
    list: elements.uploadedAudioList,
    helper: elements.audioUploadHelper,
    fallbackName: "音频素材",
    copiedMessage: "音频 URL 已复制",
    emptyMessage: "请选择音频文件",
    helperMessage: "音频已上传并写入参考音频 URL。",
    doneMessage: (count) => `已上传 ${count} 个音频素材`,
  });
}

function setSegment(buttons, attr, value) {
  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset[attr] === String(value));
  });
}

function clampQuantity(value) {
  const max = Number(elements.quantityInput.max || 4);
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) return 1;
  return Math.min(max, Math.max(1, parsed));
}

function clampSkillPromptCount(value) {
  const max = Number(elements.skillPromptCount?.max || 4);
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) return 2;
  return Math.min(max, Math.max(1, parsed));
}

function setQuantity(value) {
  state.quantity = clampQuantity(value);
  elements.quantityInput.value = String(state.quantity);
}

function setSkillPromptCount(value) {
  if (!elements.skillPromptCount) return;
  elements.skillPromptCount.value = String(clampSkillPromptCount(value));
}

function displayJson(value) {
  elements.jsonPreview.textContent = JSON.stringify(value || {}, null, 2);
  renderPromptHighlights();
  renderPreflight(payloadFromForm());
  renderPromptQuality(payloadFromForm());
  updateSkillQueueSubmitState();
  updateAssetSummary();
  renderAssetBatchPanel();
  renderAssetRoleList();
  renderReferenceImagePreviews();
  renderReferenceVideoPreviews();
  renderReferenceAudioPreviews();
  renderFaceSwapPreviews();
  updateWorkflowGuide();
  updateOpsSummary();
  refreshAssetMentionPopover();
}

function updateAssetSummary() {
  const payload = payloadFromForm();
  elements.assetImageCount.textContent = String(splitLines(elements.images.value).length);
  elements.assetVideoCount.textContent = String(splitLines(elements.videos.value).length);
  elements.assetAudioCount.textContent = String(splitLines(elements.audios.value).length);
  renderAssetRoutes(payload);
}

function renderAssetRoutes(payload) {
  const entries = rawAssetEntries();
  const submitted = entries
    .filter((entry) => entry.kind !== "face" && shouldSubmitAsset(entry.kind, entry.url))
    .map((entry) => ({ kind: roleKindLabel(entry.kind), name: entry.token, role: assetRoleMeta(entry.kind, entry.url).label, url: entry.url }));
  const workspaceOnly = [
    ...entries
      .filter((entry) => entry.kind !== "face" && !shouldSubmitAsset(entry.kind, entry.url))
      .map((entry) => ({ kind: roleKindLabel(entry.kind), name: entry.token, role: assetRoleMeta(entry.kind, entry.url).label, url: entry.url })),
    ...payload.faceSwapRefs
      .filter((url) => !payload.faceSwapSubmit || !payload.refImages.includes(url))
      .map((url, index) => ({ kind: payload.faceSwapVirtual ? "AI头像" : "人像", name: `人像${index + 1}`, role: "工作台参考", url })),
  ];

  elements.submittedAssetSummary.textContent = `${submitted.length} 个素材`;
  elements.workspaceAssetSummary.textContent = `${workspaceOnly.length} 个素材`;
  elements.submittedAssetList.innerHTML = renderAssetRouteItems(submitted, "暂无提交素材");
  elements.workspaceAssetList.innerHTML = renderAssetRouteItems(workspaceOnly, "暂无工作台参考素材");
}

function renderAssetRouteItems(items, emptyText) {
  if (!items.length) return `<p>${emptyText}</p>`;
  return items
    .slice(0, 5)
    .map((item) => `<span title="${escapeHtml(item.url)}"><b>${escapeHtml(item.kind)}</b> ${escapeHtml(item.name)} · ${escapeHtml(item.role || "")}</span>`)
    .join("");
}

function renderAssetRoleList() {
  if (!elements.assetRoleList) return;
  const entries = rawAssetEntries();
  const roleEntries = entries.filter((entry) => entry.kind !== "face");
  if (!roleEntries.length) {
    elements.assetRoleList.innerHTML = `
      <article class="asset-role-empty">
        <strong>暂无可标记素材</strong>
        <small>上传图片、视频或音频后，可以在这里设置首帧、动作参考、背景音乐或仅工作台参考。</small>
      </article>
    `;
    if (elements.assetRoleNote) elements.assetRoleNote.textContent = "给每个素材标记用途；选择“仅工作台参考”后不会提交给 Seedance。";
    return;
  }

  const submittedCount = roleEntries.filter((entry) => shouldSubmitAsset(entry.kind, entry.url)).length;
  const workspaceCount = roleEntries.length - submittedCount;
  if (elements.assetRoleNote) {
    elements.assetRoleNote.textContent = `${submittedCount} 个会提交，${workspaceCount} 个仅工作台参考。角色标记会同步到素材路由和 @ 引用。`;
  }

  elements.assetRoleList.innerHTML = "";
  roleEntries.forEach((entry) => {
    const role = assetRoleMeta(entry.kind, entry.url);
    const source = assetSourceType(entry.kind, entry.url);
    const item = document.createElement("article");
    item.className = `asset-role-item ${shouldSubmitAsset(entry.kind, entry.url) ? "will-submit" : "workspace-only"}`;
    setAssetAccent(item, entry.colorIndex);
    item.innerHTML = `
      <span class="asset-role-badge">${escapeHtml(entry.token)}</span>
      <div class="asset-role-main">
        <strong>${escapeHtml(materialDisplayName(entry.url))}</strong>
        <small>${escapeHtml(source.label)} · ${escapeHtml(role.hint || role.label)}</small>
      </div>
      <select aria-label="${escapeHtml(entry.token)}素材角色">
        ${(ASSET_ROLE_OPTIONS[entry.kind] || [])
          .map((option) => `<option value="${escapeHtml(option.value)}" ${option.value === role.value ? "selected" : ""}>${escapeHtml(option.label)}</option>`)
          .join("")}
      </select>
      <button class="asset-role-mention" type="button">插入@</button>
    `;
    item.querySelector("select").addEventListener("change", (event) => {
      setAssetRole(entry.kind, entry.url, event.target.value);
    });
    item.querySelector(".asset-role-mention").addEventListener("click", () => {
      insertPromptTextAtCursor(`@${entry.token}`);
      showToast(`${entry.token} 已插入提示词`);
    });
    elements.assetRoleList.appendChild(item);
  });
}

function renderPromptTemplates() {
  if (!elements.promptTemplateList) return;
  elements.promptTemplateList.innerHTML = "";
  PROMPT_TEMPLATES.forEach((template, index) => {
    const card = document.createElement("button");
    card.className = "prompt-template-card";
    card.type = "button";
    card.innerHTML = `
      <span>${escapeHtml(template.tag)}</span>
      <strong>${escapeHtml(template.title)}</strong>
      <small>${escapeHtml(template.prompt.slice(0, 58))}...</small>
    `;
    card.addEventListener("click", () => applyPromptTemplate(index));
    elements.promptTemplateList.appendChild(card);
  });
}

function applyPromptTemplate(index) {
  const template = PROMPT_TEMPLATES[index];
  if (!template) return;
  const current = elements.prompt.value.trim();
  elements.prompt.value = !current || state.templateReplaceMode ? template.prompt : `${current}\n\n${template.prompt}`;
  updatePromptCount();
  displayJson(payloadFromForm());
  elements.prompt.focus();
  showToast(state.templateReplaceMode ? `已替换为「${template.title}」模板` : `已追加「${template.title}」模板`);
}

function toggleTemplateReplaceMode() {
  state.templateReplaceMode = !state.templateReplaceMode;
  if (elements.clearTemplateInsertBtn) {
    elements.clearTemplateInsertBtn.classList.toggle("active", state.templateReplaceMode);
    elements.clearTemplateInsertBtn.textContent = state.templateReplaceMode ? "模板将替换" : "只保留模板";
  }
  showToast(state.templateReplaceMode ? "选择模板时会替换当前提示词" : "选择模板时会追加到当前提示词");
}

function readMarketControl(select, customInput) {
  const selected = String(select?.value || "").trim();
  if (selected === "__custom__") return String(customInput?.value || "").trim();
  return selected;
}

function writeMarketControl(select, customInput, market) {
  if (!select) return;
  const normalizedMarket = String(market || "").trim();
  const hasPreset = [...select.options].some((option) => option.value === normalizedMarket && option.value !== "__custom__");
  select.value = hasPreset ? normalizedMarket : "__custom__";
  if (customInput) {
    customInput.hidden = hasPreset;
    customInput.value = hasPreset ? "" : normalizedMarket;
  }
}

function creativeMarketValue() {
  if (elements.promptMarket) return readMarketControl(elements.promptMarket, elements.promptCustomMarket) || "未指定国家";
  return readMarketControl(elements.creativeMarket, elements.creativeCustomMarket) || "日本";
}

function resolvedCreativeLanguage() {
  const selectedLanguage = elements.promptLanguage?.value || elements.creativeLanguage?.value || "auto";
  if (selectedLanguage !== "auto") return selectedLanguage;
  return MARKET_LOCALIZATION[creativeMarketValue()]?.language || "目标市场当地主要语言";
}

function syncLocalizationControls(source = "prompt") {
  const fromPrompt = source === "prompt";
  const sourceSelect = fromPrompt ? elements.promptMarket : elements.creativeMarket;
  const sourceCustom = fromPrompt ? elements.promptCustomMarket : elements.creativeCustomMarket;
  const market = readMarketControl(sourceSelect, sourceCustom);
  const language = (fromPrompt ? elements.promptLanguage?.value : elements.creativeLanguage?.value) || "auto";
  writeMarketControl(elements.promptMarket, elements.promptCustomMarket, market);
  writeMarketControl(elements.creativeMarket, elements.creativeCustomMarket, market);
  if (elements.promptLanguage) elements.promptLanguage.value = language;
  if (elements.creativeLanguage) elements.creativeLanguage.value = language;
  updateCreativeBriefState();
  displayJson(payloadFromForm());
}

function updateCreativeMarketNote() {
  if (!elements.creativeMarketNote) return;
  const market = creativeMarketValue();
  const preset = MARKET_LOCALIZATION[market];
  const direction = preset?.direction || "使用该市场真实人物、日常场景和当地自然口语，避免刻板印象";
  elements.creativeMarketNote.textContent = `${market}市场 · ${resolvedCreativeLanguage()} · ${direction}`;
  if (elements.promptMarketLockState) {
    elements.promptMarketLockState.textContent = `${market} · ${resolvedCreativeLanguage()} · 提交时锁定`;
  }
}

function creativeBriefText() {
  const product = elements.creativeProduct?.value.trim() || "";
  const market = creativeMarketValue();
  const language = resolvedCreativeLanguage();
  const audience = elements.creativeAudience?.value.trim() || "";
  const style = elements.creativeStyle?.selectedOptions?.[0]?.textContent?.trim() || "";
  const sellingPoints = elements.creativeSellingPoints?.value.trim() || "";
  const script = elements.creativeScript?.value.trim() || "";
  return [
    product && `产品：${product}`,
    market && `目标市场 / 国家：${market}`,
    language && `内容语言：${language}，使用当地人自然口语，不要翻译腔`,
    audience && `目标人群：${audience}`,
    style && `视频方向：${style}`,
    sellingPoints && `核心卖点：${sellingPoints}`,
    script && `口播文案 / 分镜要求：${script}`,
  ].filter(Boolean).join("\n");
}

function saveCreativeBriefDraft() {
  try {
    window.localStorage.setItem(CREATIVE_BRIEF_KEY, JSON.stringify({
      product: elements.creativeProduct?.value || "",
      market: creativeMarketValue(),
      language: elements.creativeLanguage?.value || "auto",
      audience: elements.creativeAudience?.value || "",
      style: elements.creativeStyle?.value || "",
      sellingPoints: elements.creativeSellingPoints?.value || "",
      script: elements.creativeScript?.value || "",
    }));
  } catch {
    // 本地草稿保存失败时不影响当前生成流程。
  }
}

function loadCreativeBriefDraft() {
  try {
    const draft = JSON.parse(window.localStorage.getItem(CREATIVE_BRIEF_KEY) || "{}");
    const savedMarket = String(draft.market || "日本") === "__custom__" ? "日本" : String(draft.market || "日本");
    if (elements.creativeProduct) elements.creativeProduct.value = String(draft.product || "");
    writeMarketControl(elements.creativeMarket, elements.creativeCustomMarket, savedMarket);
    if (elements.creativeLanguage) elements.creativeLanguage.value = String(draft.language || "auto");
    writeMarketControl(elements.promptMarket, elements.promptCustomMarket, savedMarket);
    if (elements.promptLanguage) elements.promptLanguage.value = String(draft.language || "auto");
    if (elements.creativeAudience) elements.creativeAudience.value = String(draft.audience || "");
    if (elements.creativeStyle && draft.style) {
      elements.creativeStyle.value = String(draft.style) === "日系电商商品广告" ? "当地电商商品广告" : String(draft.style);
    }
    if (elements.creativeSellingPoints) elements.creativeSellingPoints.value = String(draft.sellingPoints || "");
    if (elements.creativeScript) elements.creativeScript.value = String(draft.script || "");
  } catch {
    // 本地草稿属于增强功能，读取失败时使用空白表单。
  }
}

function applyMaterialReversePromptDraft() {
  try {
    const raw = window.localStorage.getItem(MATERIAL_REVERSE_PROMPT_DRAFT_KEY);
    if (!raw) return false;
    const draft = JSON.parse(raw);
    const prompt = String(draft.prompt || "").trim();
    if (!prompt) {
      window.localStorage.removeItem(MATERIAL_REVERSE_PROMPT_DRAFT_KEY);
      return false;
    }
    elements.prompt.value = prompt;
    if (elements.aiBrief) {
      elements.aiBrief.value = String(draft.brief || "").trim();
      autoResizeTextarea(elements.aiBrief);
    }
    const market = String(draft.targetMarket || "日本").trim() || "日本";
    const language = String(draft.contentLanguage || "auto").trim() || "auto";
    writeMarketControl(elements.promptMarket, elements.promptCustomMarket, market);
    writeMarketControl(elements.creativeMarket, elements.creativeCustomMarket, market);
    if (elements.promptLanguage && [...elements.promptLanguage.options].some((option) => option.value === language)) {
      elements.promptLanguage.value = language;
    }
    if (elements.creativeLanguage && [...elements.creativeLanguage.options].some((option) => option.value === language)) {
      elements.creativeLanguage.value = language;
    }
    const duration = Number(draft.duration || 0) || 10;
    if ([5, 10, 11, 15].includes(duration)) {
      state.duration = duration;
      setSegment($$("[data-duration]"), "duration", duration);
    }
    const ratio = String(draft.ratio || "9:16");
    if (["9:16", "16:9", "1:1"].includes(ratio)) {
      state.ratio = ratio;
      setSegment($$("[data-ratio]"), "ratio", ratio);
    }
    const refVideo = String(draft.refVideo || "").trim();
    if (refVideo && elements.videos) {
      elements.videos.value = [...new Set([refVideo, ...splitLines(elements.videos.value)])].join("\n");
      autoResizeTextarea(elements.videos);
    }
    state.workspaceView = "create";
    window.localStorage.setItem(WORKSPACE_VIEW_KEY, "create");
    window.localStorage.removeItem(MATERIAL_REVERSE_PROMPT_DRAFT_KEY);
    return true;
  } catch {
    return false;
  }
}

function updateCreativeBriefState() {
  const values = [
    elements.creativeProduct?.value,
    elements.creativeAudience?.value,
    elements.creativeSellingPoints?.value,
    elements.creativeScript?.value,
  ].map((value) => String(value || "").trim()).filter(Boolean);
  if (elements.creativeBriefState) {
    elements.creativeBriefState.textContent = `${creativeMarketValue()} · 已填写 ${values.length}/4 项`;
  }
  updateCreativeMarketNote();
  saveCreativeBriefDraft();
  updateOpsSummary();
}

function syncCreativeBriefToAssistant() {
  const text = creativeBriefText();
  if (!text) {
    showToast("请先填写产品、卖点或口播文案");
    return false;
  }
  elements.aiBrief.value = text;
  autoResizeTextarea(elements.aiBrief);
  return true;
}

function includesAny(text, words) {
  return words.some((word) => text.includes(word));
}

function promptReferencesAssets(text) {
  const assets = getMentionAssets();
  return assets.filter((asset) => text.includes(`@${asset.token}`) || text.includes(asset.token));
}

function analyzePromptQuality(payload) {
  const rawPrompt = elements.prompt.value.trim();
  const prompt = payload.prompt || rawPrompt;
  const text = prompt.toLowerCase();
  const referencedAssets = promptReferencesAssets(prompt);
  const items = [
    {
      level: rawPrompt.length >= 60 ? "ok" : rawPrompt ? "warn" : "error",
      text: rawPrompt.length >= 60 ? "提示词长度足够，可表达完整镜头" : rawPrompt ? "提示词偏短，建议补充镜头和商品细节" : "还没有填写提示词",
    },
    {
      level: includesAny(prompt, ["0-", "1-", "2-", "3-", "秒", "开场", "最后", "尾帧", "定格"]) ? "ok" : "warn",
      text: includesAny(prompt, ["0-", "1-", "2-", "3-", "秒", "开场", "最后", "尾帧", "定格"]) ? "包含时长/分镜结构" : "建议写清 0-2秒、2-5秒、最后画面",
    },
    {
      level: includesAny(prompt, ["镜头", "构图", "特写", "近景", "推近", "拉近", "运镜", "第一人称", "视角"]) ? "ok" : "warn",
      text: includesAny(prompt, ["镜头", "构图", "特写", "近景", "推近", "拉近", "运镜", "第一人称", "视角"]) ? "镜头语言明确" : "建议补充镜头语言：近景、特写、推拉、构图",
    },
    {
      level: includesAny(prompt, ["面料", "纹理", "版型", "颜色", "领口", "袖口", "腰线", "下摆", "细节", "层次", "商品"]) ? "ok" : "warn",
      text: includesAny(prompt, ["面料", "纹理", "版型", "颜色", "领口", "袖口", "腰线", "下摆", "细节", "层次", "商品"]) ? "商品细节描述较完整" : "建议补充商品颜色、版型、面料、边缘和结构细节",
    },
    {
      level: includesAny(prompt, ["走", "转身", "展示", "整理", "拿起", "倒入", "递到", "摇晃", "手持", "动作"]) ? "ok" : "warn",
      text: includesAny(prompt, ["走", "转身", "展示", "整理", "拿起", "倒入", "递到", "摇晃", "手持", "动作"]) ? "动作描述可执行" : "建议补充主体动作，避免只写静态画面",
    },
    {
      level: referencedAssets.length ? "ok" : getMentionAssets().length ? "warn" : "ok",
      text: referencedAssets.length
        ? `已引用 ${referencedAssets.map((asset) => `@${asset.token}`).slice(0, 4).join("、")}`
        : getMentionAssets().length
          ? "已上传素材，建议在提示词里用 @图片1 / @视频1 精确引用"
          : "暂无可 @ 引用素材",
    },
    {
      level: hasIdentityRiskPrompt(rawPrompt) ? "error" : "ok",
      text: hasIdentityRiskPrompt(rawPrompt) ? "检测到换脸/身份替换风险词，建议点击合规修复" : "未检测到换脸/身份替换高风险表达",
    },
  ];
  const score = Math.max(0, 100 - items.reduce((total, item) => total + (item.level === "error" ? 28 : item.level === "warn" ? 12 : 0), 0));
  return { score, items };
}

function renderPromptQuality(payload) {
  if (!elements.promptQualityList || !elements.promptQualityScore) return;
  const analysis = analyzePromptQuality(payload);
  state.lastPromptQualityScore = analysis.score;
  const hasError = analysis.items.some((item) => item.level === "error");
  const hasWarn = analysis.items.some((item) => item.level === "warn");
  elements.promptQualityScore.textContent = payload.prompt ? `${analysis.score}分` : "待检查";
  elements.promptQualityScore.className = `prompt-quality-score ${payload.prompt ? hasError ? "status-error" : hasWarn ? "status-warn" : "status-success" : "status-idle"}`;
  elements.promptQualityList.innerHTML = analysis.items
    .map((item) => `<article class="prompt-quality-item quality-${item.level}"><span>${item.level === "ok" ? "OK" : item.level === "warn" ? "!" : "X"}</span><strong>${escapeHtml(item.text)}</strong></article>`)
    .join("");
  updatePromptSkillReviewFreshness(payload);
}

function promptReviewVerdictMeta(verdict) {
  if (verdict === "pass") return { label: "优化后可生成", tone: "status-success" };
  if (verdict === "block") return { label: "存在风险，已给出安全替代", tone: "status-error" };
  return { label: "优化完成，建议确认", tone: "status-warn" };
}

function renderPromptSkillList(element, items, emptyText) {
  if (!element) return;
  const normalizedItems = Array.isArray(items) ? items.filter((item) => String(item || "").trim()) : [];
  element.innerHTML = normalizedItems.length
    ? `<ul>${normalizedItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
    : `<p class="prompt-skill-review-list-empty">${escapeHtml(emptyText)}</p>`;
}

function renderPromptSkillReview(result, applied = false) {
  if (!elements.promptSkillReview) return;
  const review = result?.review || {};
  const skill = result?.skill || {};
  const meta = promptReviewVerdictMeta(review.verdict);
  const clampScore = (value, fallback = 0) => Number.isFinite(Number(value)) ? Math.max(0, Math.min(100, Number(value))) : fallback;
  const scoreAfter = clampScore(review.scoreAfter ?? review.score);
  const scoreBefore = clampScore(review.scoreBefore, scoreAfter);
  const preservedContent = Array.isArray(review.preservedContent) ? review.preservedContent : review.strengths;
  const changeSummary = Array.isArray(review.changeSummary) ? review.changeSummary : [];
  const issues = Array.isArray(review.issues) ? review.issues : [];

  elements.promptSkillReview.hidden = false;
  elements.promptSkillReviewTitle.textContent = `${meta.label}${review.mode ? ` · ${review.mode}` : ""}${skill.version ? ` · v${skill.version}` : ""}${applied ? " · 已应用" : ""}`;
  elements.promptSkillReviewScore.textContent = `${scoreBefore} → ${scoreAfter}分`;
  elements.promptSkillReviewScore.className = `prompt-quality-score ${meta.tone}`;
  elements.promptSkillReviewSummary.textContent = review.summary || "已按 Seedance 2.0 Skill 完成提示词优化。";
  renderPromptSkillList(elements.promptSkillReviewPreserved, preservedContent, "原提示词没有可单独提取的事实或引用。");
  renderPromptSkillList(elements.promptSkillReviewChanges, changeSummary, "已完成结构精炼，没有额外改写说明。");
  elements.promptSkillReviewIssues.innerHTML = issues.length
    ? issues
        .map((item) => {
          const severity = ["error", "warning", "info"].includes(item.severity) ? item.severity : "warning";
          const marker = severity === "error" ? "X" : severity === "warning" ? "!" : "OK";
          const suggestion = item.suggestion ? `<small>${escapeHtml(item.suggestion)}</small>` : "";
          return `<article class="prompt-skill-review-issue review-${severity}"><span>${marker}</span><div><strong>${escapeHtml(item.category || "提示词质量")}</strong><p>${escapeHtml(item.finding || "建议调整当前表达。")}</p>${suggestion}</div></article>`;
        })
        .join("")
    : '<article class="prompt-skill-review-empty"><strong>没有发现阻断问题</strong><small>确认优化结果后即可应用到提示词。</small></article>';
  elements.promptSkillReviewOutput.value = review.improvedPrompt || "";
  elements.applyPromptSkillReviewBtn.disabled = !review.improvedPrompt;
  elements.copyPromptSkillReviewBtn.disabled = !review.improvedPrompt;
}

function updatePromptSkillReviewFreshness(payload = payloadFromForm()) {
  if (!state.promptReview || !elements.promptSkillReview || elements.promptSkillReview.hidden) return;
  if (String(payload.prompt || "").trim() === state.promptReviewPrompt) return;
  elements.promptSkillReviewTitle.textContent = "原提示词已改动，需要重新优化";
  elements.promptSkillReviewScore.textContent = "待重优化";
  elements.promptSkillReviewScore.className = "prompt-quality-score status-warn";
}

async function optimizePromptWithSeedanceSkill() {
  const payload = payloadFromForm();
  if (!payload.prompt) {
    showToast("请先填写需要优化的视频生成提示词");
    return;
  }
  const originalText = elements.skillReviewPromptBtn.textContent;
  elements.skillReviewPromptBtn.disabled = true;
  elements.skillReviewPromptBtn.textContent = "Skill 优化中";
  try {
    const result = await requestJson("/api/skill/optimize-prompt", {
      method: "POST",
      body: JSON.stringify({
        ...payload,
        brief: creativeBriefText() || elements.aiBrief.value.trim(),
      }),
    });
    state.promptReview = result;
    state.promptReviewPrompt = payload.prompt;
    renderPromptSkillReview(result);
    displayJson({ promptOptimization: result.review, skill: result.skill, optimizedAt: result.optimizedAt });
    showToast(`Seedance Skill 优化完成：${result.review?.scoreBefore ?? 0} → ${result.review?.scoreAfter ?? result.review?.score ?? 0}分`);
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.skillReviewPromptBtn.disabled = state.promptReviewSkill?.exists === false;
    elements.skillReviewPromptBtn.textContent = originalText;
  }
}

function applyPromptSkillReview() {
  const improvedPrompt = String(state.promptReview?.review?.improvedPrompt || "").trim();
  if (!improvedPrompt) {
    showToast("当前没有可应用的优化 Prompt");
    return;
  }
  elements.prompt.value = improvedPrompt;
  state.promptReviewPrompt = promptFromForm();
  addPromptHistory(improvedPrompt, {
    brief: creativeBriefText() || elements.aiBrief.value.trim(),
    model: state.promptReview?.model || "seedance-20",
    ratio: state.ratio,
    duration: state.duration,
    quantity: state.quantity,
  });
  updatePromptCount();
  displayJson(payloadFromForm());
  renderPromptSkillReview(state.promptReview, true);
  elements.prompt.focus();
  showToast("已应用 Seedance Skill 优化 Prompt");
}

async function copyPromptSkillReview() {
  const improvedPrompt = String(state.promptReview?.review?.improvedPrompt || "").trim();
  if (!improvedPrompt) {
    showToast("当前没有可复制的优化 Prompt");
    return;
  }
  await navigator.clipboard.writeText(improvedPrompt);
  showToast("优化 Prompt 已复制");
}

function strengthenPromptStructure() {
  const prompt = elements.prompt.value.trim();
  const additions = [];
  if (!prompt) {
    elements.prompt.value = PROMPT_TEMPLATES[0].prompt;
    updatePromptCount();
    displayJson(payloadFromForm());
    showToast("已填入基础穿搭展示结构");
    return;
  }
  if (!includesAny(prompt, ["0-", "1-", "2-", "3-", "秒", "开场", "最后", "定格"])) {
    additions.push("分镜结构：0-2秒展示整体画面，2-5秒展示动作和场景，5-8秒推进到商品细节，最后自然定格。");
  }
  if (!includesAny(prompt, ["镜头", "构图", "特写", "近景", "推近", "拉近", "运镜"])) {
    additions.push("镜头语言：使用自然手持镜头、近景特写、轻微推拉和干净构图，画面真实稳定。");
  }
  if (!includesAny(prompt, ["面料", "纹理", "版型", "颜色", "领口", "袖口", "腰线", "下摆", "细节"])) {
    additions.push("商品细节：严格保持参考图中的颜色、版型、面料纹理、长度比例、边缘处理和关键设计。");
  }
  if (!includesAny(prompt, ["走", "转身", "展示", "整理", "拿起", "动作"])) {
    additions.push("动作要求：主体动作自然连贯，可加入慢走、转身、手部整理商品或递近镜头的动作。");
  }
  if (getMentionAssets().length && !promptReferencesAssets(prompt).length) {
    additions.push(`素材引用：重点参考@${getMentionAssets()[0].token}，如有动作素材则参考@视频1的动作、构图和镜头节奏。`);
  }
  if (!additions.length) {
    showToast("提示词结构已经比较完整");
    return;
  }
  elements.prompt.value = `${prompt}\n\n${additions.join("\n")}`;
  updatePromptCount();
  displayJson(payloadFromForm());
  showToast("已补强提示词结构");
}

function materialDisplayName(url) {
  try {
    const parsed = new URL(url);
    const name = decodeURIComponent(parsed.pathname.split("/").filter(Boolean).pop() || "");
    return name || parsed.hostname;
  } catch {
    return url;
  }
}

function getMentionAssets() {
  const imageUrls = splitLines(elements.images.value);
  const videoUrls = splitLines(elements.videos.value);
  const audioUrls = splitLines(elements.audios.value);
  const faceUrls = faceSwapRefsFromForm();
  const images = imageUrls.map((url, index) => {
    const source = imageSourceType(url);
    const role = assetRoleMeta("image", url);
    return {
      kind: "image",
      token: `图片${index + 1}`,
      label: `图片 ${index + 1}`,
      colorIndex: index,
      source,
      role,
      url,
      name: materialDisplayName(url),
    };
  });
  const videos = videoUrls.map((url, index) => {
    const source = videoSourceType(url);
    const role = assetRoleMeta("video", url);
    return {
      kind: "video",
      token: `视频${index + 1}`,
      label: `视频 ${index + 1}`,
      colorIndex: imageUrls.length + index,
      source,
      role,
      url,
      name: materialDisplayName(url),
    };
  });
  const audios = audioUrls.map((url, index) => {
    const source = audioSourceType(url);
    const role = assetRoleMeta("audio", url);
    return {
      kind: "audio",
      token: `音频${index + 1}`,
      label: `音频 ${index + 1}`,
      colorIndex: imageUrls.length + videoUrls.length + index,
      source,
      role,
      url,
      name: materialDisplayName(url),
    };
  });
  const faces = faceUrls.map((url, index) => {
    const source = imageSourceType(url);
    const role = assetRoleMeta("face", url);
    return {
      kind: "face",
      token: `人像${index + 1}`,
      label: `授权人像 ${index + 1}`,
      colorIndex: imageUrls.length + videoUrls.length + audioUrls.length + index,
      source,
      role,
      url,
      name: materialDisplayName(url),
    };
  });
  return [...images, ...videos, ...audios, ...faces];
}

function promptMentionRange() {
  const cursor = elements.prompt.selectionStart ?? elements.prompt.value.length;
  const beforeCursor = elements.prompt.value.slice(0, cursor);
  const atIndex = beforeCursor.lastIndexOf("@");
  if (atIndex < 0) return null;
  const query = beforeCursor.slice(atIndex + 1);
  if (query.length > 24 || /[\s\r\n，。；、,.!?！？:：]/.test(query)) return null;
  return { start: atIndex, end: cursor, query };
}

function filteredMentionAssets(range) {
  const query = String(range?.query || "").trim().toLowerCase();
  const assets = getMentionAssets();
  if (!query) return assets;
  return assets.filter((asset) => {
    const haystack = `${asset.kind} ${asset.token} ${asset.label} ${asset.source.label} ${asset.name} ${asset.url}`.toLowerCase();
    return haystack.includes(query);
  });
}

function renderPromptHighlights() {
  if (!elements.promptHighlightLayer) return;
  const text = elements.prompt.value;
  if (!text) {
    elements.promptHighlightLayer.innerHTML = "";
    return;
  }

  const assets = getMentionAssets().sort((a, b) => b.token.length - a.token.length);
  let html = "";
  let index = 0;
  while (index < text.length) {
    const asset = assets.find((item) => text.startsWith(`@${item.token}`, index) || text.startsWith(item.token, index));
    if (asset) {
      const rawToken = text.startsWith("@", index) ? `@${asset.token}` : asset.token;
      html += `<span class="prompt-highlight-mention" style="${assetAccentStyle(asset.colorIndex)}">${escapeHtml(rawToken)}</span>`;
      index += rawToken.length;
      continue;
    }
    html += escapeHtml(text[index]);
    index += 1;
  }

  if (text.endsWith("\n")) html += "\n";
  elements.promptHighlightLayer.innerHTML = html;
  syncPromptHighlightScroll();
}

function syncPromptHighlightScroll() {
  if (!elements.promptHighlightLayer) return;
  elements.promptHighlightLayer.scrollTop = elements.prompt.scrollTop;
  elements.promptHighlightLayer.scrollLeft = elements.prompt.scrollLeft;
}

function renderAssetMentionPopover() {
  if (!elements.assetMentionPopover || !state.mentionRange) return;
  const allAssets = getMentionAssets();
  const assets = filteredMentionAssets(state.mentionRange);

  if (!allAssets.length) {
    elements.assetMentionPopover.innerHTML = `
      <div class="asset-mention-empty">
        <strong>暂无可引用素材</strong>
        <small>先在下面添加图片或视频素材。</small>
      </div>
    `;
    elements.assetMentionPopover.hidden = false;
    return;
  }

  if (!assets.length) {
    elements.assetMentionPopover.innerHTML = `
      <div class="asset-mention-empty">
        <strong>没有匹配素材</strong>
        <small>换一个 @ 关键词试试。</small>
      </div>
    `;
    elements.assetMentionPopover.hidden = false;
    return;
  }

  state.mentionIndex = Math.min(Math.max(0, state.mentionIndex), assets.length - 1);
  elements.assetMentionPopover.innerHTML = `
    <div class="asset-mention-list">
      ${assets
        .map((asset, index) => {
          const isVideo = asset.kind === "video";
          const isAudio = asset.kind === "audio";
          const media = isAudio
            ? `<span class="asset-audio-glyph">♪</span>`
            : !isVideo
            ? `<img src="${escapeHtml(asset.url)}" alt="${escapeHtml(asset.label)}" loading="lazy">`
            : `<video src="${escapeHtml(asset.url)}" muted playsinline preload="metadata"></video>`;
          const kindLabel = asset.kind === "video" ? "VIDEO" : asset.kind === "audio" ? "AUDIO" : asset.kind === "face" ? "FACE" : "IMAGE";
          return `
            <button class="asset-mention-item ${index === state.mentionIndex ? "active" : ""}" type="button" role="option" aria-selected="${index === state.mentionIndex}" data-mention-index="${index}" style="${assetAccentStyle(asset.colorIndex)}">
              <span class="asset-mention-thumb ${escapeHtml(asset.kind)}">
                ${media}
                <span class="asset-color-badge">${escapeHtml(asset.token)}</span>
              </span>
              <span class="asset-mention-body">
                <strong>${escapeHtml(asset.token)}</strong>
                <small>${escapeHtml(asset.role?.label || asset.source.label)} · ${escapeHtml(asset.name)}</small>
              </span>
              <span class="asset-mention-kind">${kindLabel}</span>
            </button>
          `;
        })
        .join("")}
    </div>
  `;

  elements.assetMentionPopover.querySelectorAll("[data-mention-index]").forEach((button) => {
    button.addEventListener("mousedown", (event) => event.preventDefault());
    button.addEventListener("click", () => insertMentionAsset(Number(button.dataset.mentionIndex)));
  });
  elements.assetMentionPopover.querySelector(".asset-mention-item.active")?.scrollIntoView({ block: "nearest" });
  elements.assetMentionPopover.hidden = false;
}

function updateAssetMentionPopover() {
  if (!elements.assetMentionPopover) return;
  const range = promptMentionRange();
  if (!range) {
    closeAssetMentionPopover();
    return;
  }
  state.mentionRange = range;
  renderAssetMentionPopover();
}

function refreshAssetMentionPopover() {
  if (!elements.assetMentionPopover || elements.assetMentionPopover.hidden) return;
  const range = promptMentionRange();
  if (!range) {
    closeAssetMentionPopover();
    return;
  }
  state.mentionRange = range;
  renderAssetMentionPopover();
}

function closeAssetMentionPopover() {
  if (!elements.assetMentionPopover) return;
  elements.assetMentionPopover.hidden = true;
  elements.assetMentionPopover.innerHTML = "";
  state.mentionRange = null;
  state.mentionIndex = 0;
}

function insertPromptTextAtCursor(text) {
  const insertText = String(text || "");
  if (!insertText) return;
  const value = elements.prompt.value;
  const start = elements.prompt.selectionStart ?? value.length;
  const end = elements.prompt.selectionEnd ?? start;
  const needsLeadingSpace = start > 0 && !/[\s\n]$/.test(value.slice(0, start));
  const needsTrailingSpace = end < value.length && !/^[\s\n]/.test(value.slice(end));
  const nextText = `${needsLeadingSpace ? " " : ""}${insertText}${needsTrailingSpace ? " " : ""}`;
  elements.prompt.value = `${value.slice(0, start)}${nextText}${value.slice(end)}`;
  const cursor = start + nextText.length;
  elements.prompt.setSelectionRange(cursor, cursor);
  elements.prompt.focus();
  updatePromptCount();
  displayJson(payloadFromForm());
}

function insertMentionAsset(index = state.mentionIndex) {
  if (!state.mentionRange) return;
  const assets = filteredMentionAssets(state.mentionRange);
  const asset = assets[index];
  if (!asset) return;

  const value = elements.prompt.value;
  const before = value.slice(0, state.mentionRange.start);
  const after = value.slice(state.mentionRange.end);
  const mentionToken = `@${asset.token}`;
  const nextValue = `${before}${mentionToken}${after}`;
  const cursor = before.length + mentionToken.length;
  elements.prompt.value = nextValue;
  elements.prompt.setSelectionRange(cursor, cursor);
  updatePromptCount();
  closeAssetMentionPopover();
  displayJson(payloadFromForm());
  elements.prompt.focus();
}

function handleMentionKeydown(event) {
  if (!elements.assetMentionPopover || elements.assetMentionPopover.hidden) return;
  const assets = filteredMentionAssets(state.mentionRange);
  if (event.key === "Escape") {
    event.preventDefault();
    closeAssetMentionPopover();
    return;
  }
  if (!assets.length) return;
  if (event.key === "ArrowDown") {
    event.preventDefault();
    state.mentionIndex = (state.mentionIndex + 1) % assets.length;
    renderAssetMentionPopover();
    return;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    state.mentionIndex = (state.mentionIndex - 1 + assets.length) % assets.length;
    renderAssetMentionPopover();
    return;
  }
  if (event.key === "Enter" || event.key === "Tab") {
    event.preventDefault();
    insertMentionAsset();
  }
}

function imageSourceType(url) {
  if (!isHttpUrl(url)) return { label: "无效 URL", className: "invalid" };
  try {
    const parsed = new URL(url);
    const sameHost = parsed.host === window.location.host;
    if (sameHost && parsed.pathname.startsWith("/uploads/images/")) {
      return { label: "本站上传", className: "site" };
    }
  } catch {
    return { label: "无效 URL", className: "invalid" };
  }
  if (isLocalOrPrivateUrl(url)) return { label: "本地 URL", className: "local" };
  return { label: "外部 URL", className: "external" };
}

function videoSourceType(url) {
  if (!isHttpUrl(url)) return { label: "无效 URL", className: "invalid" };
  try {
    const parsed = new URL(url);
    const sameHost = parsed.host === window.location.host;
    if (sameHost && parsed.pathname.startsWith("/uploads/videos/")) {
      return { label: "本站上传", className: "site" };
    }
  } catch {
    return { label: "无效 URL", className: "invalid" };
  }
  if (isLocalOrPrivateUrl(url)) return { label: "本地 URL", className: "local" };
  return { label: "外部 URL", className: "external" };
}

function audioSourceType(url) {
  if (!isHttpUrl(url)) return { label: "无效 URL", className: "invalid" };
  try {
    const parsed = new URL(url);
    const sameHost = parsed.host === window.location.host;
    if (sameHost && parsed.pathname.startsWith("/uploads/audios/")) {
      return { label: "本站上传", className: "site" };
    }
  } catch {
    return { label: "无效 URL", className: "invalid" };
  }
  if (isLocalOrPrivateUrl(url)) return { label: "本地 URL", className: "local" };
  return { label: "外部 URL", className: "external" };
}

function renderReferenceImagePreviews() {
  if (!elements.imagePreviewGrid) return;
  const urls = splitLines(elements.images.value);
  if (!urls.length) {
    elements.imagePreviewGrid.innerHTML = `
      <article class="image-preview-empty">
        <strong>暂无参考图</strong>
        <small>上传图片或粘贴图片 URL 后，会在这里展示缩略图。</small>
      </article>
    `;
    return;
  }

  elements.imagePreviewGrid.innerHTML = "";
  urls.forEach((url, index) => {
    const source = imageSourceType(url);
    const role = assetRoleMeta("image", url);
    const item = document.createElement("article");
    item.className = `image-preview-item ${source.className}`;
    setAssetAccent(item, index);
    item.innerHTML = `
      <button class="image-preview-frame" type="button" aria-label="放大查看参考图 ${index + 1}">
        <img src="${escapeHtml(url)}" alt="参考图 ${index + 1}" loading="lazy">
        <span class="asset-color-badge">图片${index + 1}</span>
      </button>
      <div class="image-preview-meta">
        <span>${escapeHtml(role.label)} · ${escapeHtml(source.label)}</span>
        <button class="image-preview-remove" type="button">移除</button>
      </div>
    `;
    item.querySelector("img").addEventListener("error", () => {
      item.classList.add("broken");
      item.querySelector(".image-preview-frame").innerHTML = `<strong>图片无法预览</strong><span class="asset-color-badge">图片${index + 1}</span>`;
    });
    item.querySelector(".image-preview-frame").addEventListener("click", () => {
      openImageLightbox(url, `参考图 ${index + 1} · ${source.label}`);
    });
    item.querySelector(".image-preview-remove").addEventListener("click", () => {
      removeMaterialUrl(elements.images, url);
      showToast("参考图已移除");
    });
    elements.imagePreviewGrid.appendChild(item);
  });
}

function renderReferenceVideoPreviews() {
  if (!elements.videoPreviewGrid) return;
  const urls = splitLines(elements.videos.value);
  if (!urls.length) {
    elements.videoPreviewGrid.innerHTML = `
      <article class="video-preview-empty">
        <strong>暂无参考视频</strong>
        <small>上传视频或粘贴视频 URL 后，会在这里展示预览。</small>
      </article>
    `;
    return;
  }

  elements.videoPreviewGrid.innerHTML = "";
  const imageCount = splitLines(elements.images.value).length;
  urls.forEach((url, index) => {
    const source = videoSourceType(url);
    const role = assetRoleMeta("video", url);
    const item = document.createElement("article");
    item.className = `video-preview-item ${source.className}`;
    setAssetAccent(item, imageCount + index);
    item.innerHTML = `
      <button class="video-preview-frame" type="button" aria-label="播放参考视频 ${index + 1}">
        <video src="${escapeHtml(url)}" muted playsinline preload="metadata"></video>
        <span class="asset-color-badge">视频${index + 1}</span>
        <span class="video-play-mark">播放</span>
      </button>
      <div class="video-preview-meta">
        <span>${escapeHtml(role.label)} · ${escapeHtml(source.label)}</span>
        <button class="video-preview-remove" type="button">移除</button>
      </div>
    `;
    item.querySelector("video").addEventListener("error", () => {
      item.classList.add("broken");
      item.querySelector(".video-preview-frame").innerHTML = `<strong>视频无法预览</strong><span class="asset-color-badge">视频${index + 1}</span>`;
    });
    item.querySelector(".video-preview-frame").addEventListener("click", () => {
      openVideoLightbox(url, `参考视频 ${index + 1} · ${source.label}`);
    });
    item.querySelector(".video-preview-remove").addEventListener("click", () => {
      removeMaterialUrl(elements.videos, url);
      showToast("参考视频已移除");
    });
    elements.videoPreviewGrid.appendChild(item);
  });
}

function renderReferenceAudioPreviews() {
  if (!elements.audioPreviewList) return;
  const urls = splitLines(elements.audios.value);
  if (!urls.length) {
    elements.audioPreviewList.innerHTML = `
      <article class="audio-preview-empty">
        <strong>暂无参考音频</strong>
        <small>上传音频或粘贴音频 URL 后，可以在这里在线试听。</small>
      </article>
    `;
    return;
  }

  elements.audioPreviewList.innerHTML = "";
  urls.forEach((url, index) => {
    const source = audioSourceType(url);
    const role = assetRoleMeta("audio", url);
    const item = document.createElement("article");
    item.className = `audio-preview-item ${source.className}`;
    item.innerHTML = `
      <div class="audio-preview-head">
        <div>
          <strong>音频 ${index + 1}</strong>
          <small>${escapeHtml(materialDisplayName(url))}</small>
        </div>
        <span>${escapeHtml(role.label)} · ${escapeHtml(source.label)}</span>
      </div>
      <audio class="audio-preview-player" src="${escapeHtml(url)}" controls preload="metadata"></audio>
      <div class="audio-preview-actions">
        <button class="audio-preview-copy" type="button">复制 URL</button>
        <button class="audio-preview-remove" type="button">移除</button>
      </div>
    `;
    item.querySelector("audio").addEventListener("error", () => {
      item.classList.add("broken");
      item.querySelector(".audio-preview-head small").textContent = "音频无法预览，请检查 URL 是否可访问";
    });
    item.querySelector(".audio-preview-copy").addEventListener("click", async () => {
      await navigator.clipboard.writeText(url);
      showToast("音频 URL 已复制");
    });
    item.querySelector(".audio-preview-remove").addEventListener("click", () => {
      removeMaterialUrl(elements.audios, url);
      showToast("参考音频已移除");
    });
    elements.audioPreviewList.appendChild(item);
  });
}

function renderFaceSwapPreviews() {
  if (!elements.faceSwapPreviewGrid) return;
  const urls = faceSwapRefsFromForm();
  const enabled = urls.length && elements.faceSwapConsent.checked;
  const submittingFaces = enabled && elements.faceSwapSubmit.checked;
  const virtualMode = Boolean(elements.faceSwapVirtual?.checked);
  elements.faceSwapState.textContent = urls.length ? (enabled ? (submittingFaces ? "强制提交" : virtualMode ? "无脸安全" : "安全参考") : "待授权确认") : "未启用";
  elements.faceSwapState.className = `face-swap-state ${enabled && !submittingFaces ? "enabled" : urls.length ? "pending" : ""}`;

  if (!urls.length) {
    elements.faceSwapPreviewGrid.innerHTML = `
      <article class="face-swap-empty">
        <strong>暂无授权人像</strong>
        <small>上传或粘贴已授权人像图片 URL 后，会在这里展示预览。</small>
      </article>
    `;
    return;
  }

  elements.faceSwapPreviewGrid.innerHTML = "";
  const imageCount = splitLines(elements.images.value).length;
  const videoCount = splitLines(elements.videos.value).length;
  urls.forEach((url, index) => {
    const source = imageSourceType(url);
    const item = document.createElement("article");
    item.className = `face-swap-item ${source.className}`;
    setAssetAccent(item, imageCount + videoCount + index);
    item.innerHTML = `
      <button class="face-swap-frame" type="button" aria-label="放大查看授权人像 ${index + 1}">
        <img src="${escapeHtml(url)}" alt="授权人像 ${index + 1}" loading="lazy">
        <span class="asset-color-badge">人像${index + 1}</span>
      </button>
      <div class="face-swap-meta">
        <span>${escapeHtml(source.label)}</span>
        <button class="face-swap-remove" type="button">移除</button>
      </div>
    `;
    item.querySelector("img").addEventListener("error", () => {
      item.classList.add("broken");
      item.querySelector(".face-swap-frame").innerHTML = `<strong>人像无法预览</strong><span class="asset-color-badge">人像${index + 1}</span>`;
    });
    item.querySelector(".face-swap-frame").addEventListener("click", () => {
      openImageLightbox(url, `授权人像 ${index + 1} · ${source.label}`);
    });
    item.querySelector(".face-swap-remove").addEventListener("click", () => {
      removeMaterialUrl(elements.faceSwapRefs, url);
      showToast("授权人像已移除");
    });
    elements.faceSwapPreviewGrid.appendChild(item);
  });
}

function openImageLightbox(url, title) {
  closeVideoLightbox();
  state.lightboxUrl = url;
  elements.imageLightboxImg.src = url;
  elements.imageLightboxTitle.textContent = title || "参考图预览";
  elements.imageLightboxUrl.textContent = url;
  elements.imageLightbox.hidden = false;
  document.body.classList.add("lightbox-open");
  elements.closeLightboxBtn.focus();
}

function closeImageLightbox() {
  if (elements.imageLightbox.hidden) return;
  elements.imageLightbox.hidden = true;
  elements.imageLightboxImg.removeAttribute("src");
  elements.imageLightboxUrl.textContent = "";
  state.lightboxUrl = "";
  document.body.classList.remove("lightbox-open");
}

async function copyLightboxUrl() {
  if (!state.lightboxUrl) {
    showToast("还没有可复制的图片 URL");
    return;
  }
  await navigator.clipboard.writeText(state.lightboxUrl);
  showToast("图片 URL 已复制");
}

function openVideoLightbox(url, title) {
  closeImageLightbox();
  state.videoLightboxUrl = url;
  elements.videoLightboxPlayer.src = url;
  elements.videoLightboxTitle.textContent = title || "参考视频预览";
  elements.videoLightboxUrl.textContent = url;
  elements.videoLightbox.hidden = false;
  elements.videoLightboxPlayer.load();
  document.body.classList.add("lightbox-open");
  elements.closeVideoLightboxBtn.focus();
}

function closeVideoLightbox() {
  if (elements.videoLightbox.hidden) return;
  elements.videoLightbox.hidden = true;
  elements.videoLightboxPlayer.pause();
  elements.videoLightboxPlayer.removeAttribute("src");
  elements.videoLightboxPlayer.load();
  elements.videoLightboxUrl.textContent = "";
  state.videoLightboxUrl = "";
  document.body.classList.remove("lightbox-open");
}

async function copyVideoLightboxUrl() {
  if (!state.videoLightboxUrl) {
    showToast("还没有可复制的视频 URL");
    return;
  }
  await navigator.clipboard.writeText(state.videoLightboxUrl);
  showToast("视频 URL 已复制");
}

function hasVideoApiConfig() {
  return Boolean(
    elements.arkApiKey.value.trim() ||
      elements.arkConfigState.classList.contains("ok") ||
      elements.apiKeyState.textContent.includes("已配置")
  );
}

function isHttpUrl(value) {
  return /^https?:\/\//i.test(String(value || "").trim());
}

function isLocalOrPrivateUrl(value) {
  if (!isHttpUrl(value)) return false;
  try {
    const host = new URL(value).hostname.replace(/^\[|\]$/g, "").toLowerCase();
    return (
      host === "localhost" ||
      host === "::1" ||
      host.startsWith("127.") ||
      host.startsWith("10.") ||
      host.startsWith("192.168.") ||
      /^172\.(1[6-9]|2\d|3[0-1])\./.test(host)
    );
  } catch {
    return false;
  }
}

function buildPreflightChecks(payload) {
  const refs = [...payload.refImages, ...payload.refVideos, ...payload.refAudios];
  const nonHttpRefs = refs.filter((url) => !isHttpUrl(url));
  const localRefs = refs.filter(isLocalOrPrivateUrl);
  const hasVisualRef = payload.refImages.length || payload.refVideos.length;
  const endpoint = elements.arkEndpoint.value.trim();
  const rawIdentityRisk = hasIdentityRiskPrompt(`${elements.prompt.value}\n${elements.faceSwapPrompt.value}`);
  const identityRisk = hasIdentityRiskPrompt(payload.prompt);
  const hasAvatarDescription = Boolean(elements.faceSwapPrompt.value.trim());

  return [
    {
      level: payload.prompt ? "ok" : "error",
      text: payload.prompt ? "Prompt 已填写" : "请先填写视频生成 Prompt",
    },
    {
      level: payload.targetMarket && payload.targetMarket !== "未指定国家" ? "ok" : "error",
      text: payload.targetMarket && payload.targetMarket !== "未指定国家"
        ? `生成国家已锁定：${payload.targetMarket} · ${payload.contentLanguage}`
        : "选择其他国家后，请填写具体国家或地区",
    },
    {
      level: hasVideoApiConfig() ? "ok" : "error",
      text: hasVideoApiConfig() ? "视频生成接口已配置" : "请先配置火山/CPA 视频接口 Key",
    },
    {
      level: isHttpUrl(endpoint) ? "ok" : "error",
      text: isHttpUrl(endpoint) ? "视频 Endpoint 可用" : "视频 Endpoint 需要是 http/https 地址",
    },
    {
      level: currentModel() ? "ok" : "error",
      text: currentModel() ? `模型：${currentModel()}` : "请填写 Seedance 模型 ID",
    },
    {
      level: nonHttpRefs.length ? "error" : localRefs.length ? "error" : refs.length ? "ok" : "warn",
      text: nonHttpRefs.length
        ? `参考素材含非 http/https 地址：${nonHttpRefs[0]}`
        : localRefs.length
          ? "参考素材是本地/内网 URL，火山远端无法访问；请换成公网素材地址"
          : refs.length
            ? `已加入 ${refs.length} 个参考素材`
            : "未加入参考素材，服装复刻稳定性会下降",
    },
    {
      level: hasVisualRef ? "ok" : "warn",
      text: hasVisualRef ? "已有参考图/参考视频" : "建议至少加入一张参考图或一条参考视频",
    },
    {
      level: payload.faceSwapRefs.length
        ? payload.faceSwapConsent
          ? payload.faceSwapVirtual && !payload.faceSwapSubmit && !hasAvatarDescription
            ? "warn"
            : payload.faceSwapSubmit
            ? "error"
            : "ok"
          : "error"
        : "ok",
      text: payload.faceSwapRefs.length
        ? payload.faceSwapConsent
          ? payload.faceSwapVirtual && !payload.faceSwapSubmit && !hasAvatarDescription
            ? "无脸安全模式已启用：请在“头像文字描述 / 角色要求”里写清发型、脸型、妆容和风格"
            : payload.faceSwapSubmit
              ? `强制提交人像图：${payload.faceSwapRefs.length} 张，当前策略下只要检测到人脸就可能失败`
              : payload.faceSwapVirtual
                ? `无脸安全模式：${payload.faceSwapRefs.length} 张头像仅作工作台参考，不提交给 Seedance`
              : `安全模式：${payload.faceSwapRefs.length} 张人像仅作工作台参考，不提交给 Seedance`
          : "已添加人像参考素材，请先确认已获得该人像素材授权"
        : "授权人像参考未启用",
    },
    {
      level: rawIdentityRisk ? "warn" : "ok",
      text: rawIdentityRisk
        ? payload.faceSwapVirtual
          ? "已启用无脸安全模式，提交时会改写为“AI 虚拟角色重生成”表达"
          : "提示词含换脸/身份替换类表达，建议改成“AI 虚拟角色、参考视频动作构图、重新生成新视频”"
        : identityRisk
          ? "生成请求仍含身份替换高风险表达，建议检查人像参考要求"
          : "提示词未检测到身份替换高风险表达",
    },
    {
      level: payload.faceSwapVirtual ? "warn" : "ok",
      text: payload.faceSwapVirtual
        ? payload.refVideos.length
          ? "无脸安全提醒：参考视频如含清晰人脸，也可能触发审核；建议先裁掉头部、遮脸或使用背影/动作版视频"
          : "AI 虚拟头像套视频时，建议把无清晰人脸的动作参考视频加入参考视频 URL"
        : "虚拟头像视频参考设置正常",
    },
    {
      level: payload.refAudios.length && payload.generateAudio ? "warn" : "ok",
      text: payload.refAudios.length && payload.generateAudio ? "参考音频和有声生成可能互斥，建议二选一" : "音频设置正常",
    },
  ];
}

function renderPreflight(payload) {
  if (!elements.preflightList || !elements.preflightSummary) return;
  const checks = buildPreflightChecks(payload);
  const errors = checks.filter((item) => item.level === "error");
  const warnings = checks.filter((item) => item.level === "warn");
  elements.preflightSummary.textContent = errors.length
    ? `${errors.length} 项需处理`
    : warnings.length
      ? `${warnings.length} 项提醒`
      : "可以提交";
  elements.preflightSummary.className = `preflight-summary ${errors.length ? "status-error" : warnings.length ? "status-warn" : "status-success"}`;
  const visibleChecks = [...errors, ...warnings];
  const compactChecks = visibleChecks.length
    ? visibleChecks
    : [{ level: "ok", text: "接口、Prompt、素材和生成参数均已通过检查" }];
  elements.preflightList.innerHTML = compactChecks
    .map((item) => `<article class="preflight-item preflight-${item.level}"><span>${item.level === "ok" ? "OK" : item.level === "warn" ? "!" : "X"}</span><strong>${escapeHtml(item.text)}</strong></article>`)
    .join("");
}

function runPreflight() {
  const payload = payloadFromForm();
  const checks = buildPreflightChecks(payload);
  renderPreflight(payload);
  const firstError = checks.find((item) => item.level === "error");
  if (firstError) {
    showToast(firstError.text);
    return false;
  }
  return true;
}

function updateWorkflowGuide() {
  const payload = payloadFromForm();
  const checks = buildPreflightChecks(payload);
  const hasAssets = payload.refImages.length || payload.refVideos.length || payload.refAudios.length || payload.faceSwapRefs.length;
  const hasErrors = checks.some((item) => item.level === "error");
  const hasWarnings = checks.some((item) => item.level === "warn");
  setWorkflowState(elements.workflowConfigState, hasVideoApiConfig() ? "已配置" : "待配置", hasVideoApiConfig() ? "ok" : "warn");
  setWorkflowState(elements.workflowAssetsState, hasAssets ? `${payload.refImages.length + payload.refVideos.length + payload.refAudios.length} 提交 / ${payload.faceSwapRefs.length} 参考` : "等待素材", hasAssets ? "ok" : "warn");
  setWorkflowState(elements.workflowPromptState, payload.prompt ? (hasIdentityRiskPrompt(payload.prompt) ? "需修复" : "已填写") : "等待输入", payload.prompt ? (hasIdentityRiskPrompt(payload.prompt) ? "warn" : "ok") : "warn");
  setWorkflowState(elements.workflowSubmitState, hasErrors ? "需处理" : hasWarnings ? "可检查" : "可提交", hasErrors ? "error" : hasWarnings ? "warn" : "ok");
}

function updateOpsSummary() {
  if (!elements.opsApiState) return;
  const payload = payloadFromForm();
  const rawAssets = rawAssetEntries();
  const submittedAssets = payload.refImages.length + payload.refVideos.length + payload.refAudios.length;
  const workspaceAssets = rawAssets.filter((entry) => entry.kind === "face" || !shouldSubmitAsset(entry.kind, entry.url)).length;
  const total = state.taskIds.length;
  const statuses = state.taskIds.map((taskId) => getTaskStatus(state.taskMap[taskId]));
  const finished = statuses.filter(isTerminalStatus).length;
  const failed = statuses.filter(isFailedStatus).length;
  const succeeded = statuses.filter(isSuccessStatus).length;
  const hasPrompt = Boolean(payload.prompt);

  elements.opsApiState.textContent = hasVideoApiConfig() ? "视频已配置" : "视频未配置";
  elements.opsApiState.className = hasVideoApiConfig() ? "ops-ok" : "ops-warn";
  elements.opsAiState.textContent = elements.aiConfigState?.classList.contains("ok") || elements.aiApiState?.textContent.includes("已配置") ? "AI 已配置" : "AI 未配置";
  elements.opsModelState.textContent = currentModel();
  elements.opsRatioState.textContent = `${creativeMarketValue()} · ${state.ratio} · ${state.duration}s · ${state.quantity}条`;
  elements.opsAssetState.textContent = `${submittedAssets} 个提交`;
  elements.opsWorkspaceState.textContent = `${workspaceAssets} 个参考`;
  elements.opsPromptState.textContent = hasPrompt ? `${elements.prompt.value.trim().length} 字` : "未填写";
  elements.opsQualityState.textContent = hasPrompt ? `质量 ${state.lastPromptQualityScore}分` : "待检查";
  elements.opsTaskState.textContent = total ? `${finished}/${total}` : "0/0";
  elements.opsTaskDetailState.textContent = total ? `${succeeded} 成功 · ${failed} 失败` : "等待提交";
  if (elements.generateReadySummary) {
    const checks = buildPreflightChecks(payload);
    const errors = checks.filter((item) => item.level === "error").length;
    const warnings = checks.filter((item) => item.level === "warn").length;
    elements.generateReadySummary.textContent = errors
      ? `${errors} 项需处理 · ${creativeMarketValue()} · ${state.ratio} · ${state.duration}s · ${state.quantity}条`
      : warnings
        ? `${warnings} 项提醒 · ${creativeMarketValue()} · ${state.ratio} · ${state.duration}s · ${state.quantity}条`
        : `${creativeMarketValue()} · ${state.ratio} · ${state.duration}s · ${state.quantity}条 · 可以生成`;
  }
}

function setWorkflowState(element, text, level) {
  if (!element) return;
  element.textContent = text;
  element.className = `workflow-state-${level}`;
}

function hasIdentityRiskPrompt(prompt) {
  return /换脸|换头像|换头|替换[^，。,.!?！？\n]{0,8}(脸|面部|人脸|头像|头部)|脸部替换|面部替换|头像替换|头部替换|人脸生成|身份替换|复刻真人|精准复刻|克隆[^，。,.!?！？\n]{0,8}(脸|面部|人脸|头像)|变成[^，。,.!?！？\n]{0,8}(某人|本人|明星)/i.test(prompt || "");
}

function normalizeVirtualAvatarPrompt(prompt) {
  return String(prompt || "")
    .replace(/(人物|角色|主角|模特)?\s*(换脸|换头像|换头|替换头像|替换头部|替换人脸|替换面部)\s*(成|为)\s*(@?(授权人像|人像|图片)\d+)/gi, (_match, subject, _action, _link, target) => {
      return `${subject || "主角"}以${target}作为 AI 虚拟角色外观参考重新生成`;
    })
    .replace(/(换脸|换头像|换头|替换头像|替换头部|替换人脸|替换面部|脸部替换|面部替换|头像替换|头部替换)\s*(成|为)?/gi, "改为以 AI 虚拟角色外观重新生成")
    .replace(/身份替换|复刻真人|精准复刻|克隆人脸|克隆头像/gi, "保持 AI 虚拟角色风格一致")
    .replace(/真人/g, "虚拟角色")
    .trim();
}

function repairPromptCompliance() {
  const hasFaceRefs = faceSwapRefsFromForm().length > 0;
  const beforePrompt = elements.prompt.value.trim();
  const beforeFacePrompt = elements.faceSwapPrompt.value.trim();
  let changed = false;

  if (hasFaceRefs) {
    elements.faceSwapConsent.checked = true;
    elements.faceSwapVirtual.checked = true;
    elements.faceSwapSubmit.checked = false;
    changed = true;
    if (!beforeFacePrompt) {
      elements.faceSwapPrompt.value = "AI虚拟角色，按工作台头像参考图填写发型、脸型、妆容和风格气质；参考视频只用于动作、构图、镜头节奏和身体姿态。";
    }
  }

  const normalizedPrompt = normalizeVirtualAvatarPrompt(beforePrompt);
  if (normalizedPrompt && normalizedPrompt !== beforePrompt) {
    elements.prompt.value = normalizedPrompt;
    changed = true;
  }

  if (!elements.prompt.value.trim()) {
    elements.prompt.value = hasFaceRefs
      ? "参考视频1的动作、构图、镜头节奏和身体姿态，重新生成一个新的 AI 虚拟角色视频。"
      : "重新生成一个新的 AI 虚拟角色视频，画面自然，动作连贯，镜头节奏清晰。";
    changed = true;
  }

  updatePromptCount();
  autoResizeTextarea(elements.faceSwapPrompt);
  closeAssetMentionPopover();
  displayJson(payloadFromForm());
  showToast(changed ? "已修复为无脸安全生成表达" : "当前提示词已接近合规表达");
}

function updatePromptCount() {
  if (!elements.promptCount) return;
  const length = elements.prompt.value.length;
  elements.promptCount.textContent = `${length} / 10000`;
}

function autoResizeTextarea(textarea) {
  if (!textarea) return;
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight + 2}px`;
}

function autoResizeUrlInputs() {
  elements.urlInputs.forEach(autoResizeTextarea);
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => elements.toast.classList.remove("show"), 2800);
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
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `请求失败：${response.status}`);
  }
  return payload;
}

async function loadHealth() {
  try {
    const health = await requestJson("/api/health");
    state.defaultModel = health.defaultModel || health.model || BUILT_IN_MODEL;
    state.promptReviewSkill = health.promptReviewSkill || null;
    if (elements.skillReviewPromptBtn && state.promptReviewSkill) {
      elements.skillReviewPromptBtn.disabled = !state.promptReviewSkill.exists;
      elements.skillReviewPromptBtn.title = state.promptReviewSkill.exists
        ? `使用 seedance-20${state.promptReviewSkill.version ? ` v${state.promptReviewSkill.version}` : ""} 优化当前提示词`
        : "未检测到 seedance-20 Skill";
    }
    await loadConfig();
    if (health.maxQuantity) {
      elements.quantityInput.max = String(health.maxQuantity);
    }
    if (health.minQuantity) {
      elements.quantityInput.min = String(health.minQuantity);
    }
    if (health.maxPromptCount && elements.skillPromptCount) {
      elements.skillPromptCount.max = String(health.maxPromptCount);
    }
    if (health.minPromptCount && elements.skillPromptCount) {
      elements.skillPromptCount.min = String(health.minPromptCount);
    }
    setQuantity(elements.quantityInput.value || state.quantity || 1);
    setSkillPromptCount(elements.skillPromptCount?.value || 2);
  } catch (error) {
    elements.apiKeyState.textContent = "检测失败";
    showToast(error.message);
  }
}

async function buildRequest() {
  if (!runPreflight()) return null;
  const payload = payloadFromForm();
  const result = await requestJson("/api/build", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.lastRequest = result.request;
  displayJson({ quantity: result.quantity, request: result.request });
  showToast(`请求 JSON 已生成，将提交 ${result.quantity} 条任务`);
  return result.request;
}

async function submitTask() {
  if (!runPreflight()) return;
  stopPolling();
  elements.submitBtn.disabled = true;
  elements.submitSkillQueueBtn.disabled = true;
  elements.taskStatus.textContent = "提交中";
  elements.resultVideoState.textContent = "生成中";
  updateTaskOverview();

  try {
    const payload = payloadFromForm();
    const result = await requestJson("/api/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.lastRequest = result.request;
    state.lastErrors = [];
    state.taskPromptMap = {};
    state.taskPromptTextMap = {};
    state.taskPayloadMap = {};
    renderTaskErrors([]);
    const tasks = Array.isArray(result.tasks) && result.tasks.length ? result.tasks : result.task ? [result.task] : [];
    state.lastTask = tasks[0] || null;
    displayJson({ quantity: result.quantity || payload.quantity, tasks, errors: result.errors || [], request: result.request });

    const taskIds = tasks.map(readTaskId).filter(Boolean);
    if (!taskIds.length) {
      elements.taskStatus.textContent = "已提交，无任务 ID";
      updateTaskOverview();
      showToast("已提交，但响应里没有找到任务 ID");
      return;
    }

    setTasks(taskIds, tasks);
    taskIds.forEach((taskId, index) => {
      state.taskPromptMap[taskId] = `直接生成 #${index + 1}`;
      state.taskPromptTextMap[taskId] = payload.prompt;
      state.taskPayloadMap[taskId] = { ...payload, quantity: 1 };
      addHistory(taskId, tasks[index]?.status || "submitted", `${payload.prompt} #${index + 1}`);
    });
    showToast(taskIds.length === 1 ? "任务已提交，开始轮询状态" : `已提交 ${taskIds.length} 条任务，开始轮询状态`);
    startPolling();
  } catch (error) {
    elements.taskStatus.textContent = "提交失败";
    elements.resultVideoState.textContent = "未生成";
    renderTaskErrors([{ message: error.message }]);
    updateTaskOverview();
    showToast(error.message);
  } finally {
    elements.submitBtn.disabled = false;
    updateSkillQueueSubmitState();
  }
}

async function submitSkillPromptQueue(items = state.skillPrompts) {
  const promptItems = items.filter((item) => String(item?.prompt || "").trim());
  if (!promptItems.length) {
    showToast("暂无可生成的视频 Prompt 队列");
    return;
  }
  const basePayload = payloadFromForm();
  if (!requireSkillQueueVisualReference(basePayload)) return;

  stopPolling();
  elements.submitBtn.disabled = true;
  elements.submitSkillQueueBtn.disabled = true;
  elements.taskStatus.textContent = "队列提交中";
  elements.resultVideoState.textContent = "生成中";
  renderTaskErrors([]);
  updateTaskOverview();

  const allTasks = [];
  const allTaskIds = [];
  const allErrors = [];
  const requests = [];
  state.taskPromptMap = {};
  state.taskPromptTextMap = {};
  state.taskPayloadMap = {};

  try {
    for (const [index, item] of promptItems.entries()) {
      const payload = {
        ...basePayload,
        prompt: promptWithFaceSwapInstruction(item.prompt),
        quantity: state.quantity,
      };
      const checks = buildPreflightChecks(payload);
      const firstError = checks.find((check) => check.level === "error");
      renderPreflight(payload);
      if (firstError) {
        throw new Error(firstError.text);
      }

      elements.taskStatus.textContent = `提交 ${index + 1}/${promptItems.length}`;
      const result = await requestJson("/api/tasks", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      requests.push({ prompt: item.prompt, title: item.title, angle: item.angle, request: result.request });
      const tasks = Array.isArray(result.tasks) && result.tasks.length ? result.tasks : result.task ? [result.task] : [];
      allTasks.push(...tasks);
      if (Array.isArray(result.errors) && result.errors.length) {
        allErrors.push(...result.errors.map((error) => ({ ...error, prompt: item.title || `Prompt ${index + 1}` })));
      }

      const taskIds = tasks.map(readTaskId).filter(Boolean);
      taskIds.forEach((taskId, taskIndex) => {
        allTaskIds.push(taskId);
        state.taskPromptMap[taskId] = `${item.title || `Prompt ${index + 1}`} · ${item.angle || "Skill Prompt"}`;
        state.taskPromptTextMap[taskId] = item.prompt;
        state.taskPayloadMap[taskId] = { ...payload, quantity: 1 };
        addHistory(taskId, tasks[taskIndex]?.status || "submitted", `${item.title || `Prompt ${index + 1}`} · ${item.prompt}`);
      });
      setTasks(allTaskIds, allTasks);
      displayJson({
        mode: "skillPromptQueue",
        submittedPrompts: index + 1,
        totalPrompts: promptItems.length,
        tasks: allTasks,
        errors: allErrors,
        requests,
      });
    }

    state.lastRequest = { mode: "skillPromptQueue", requests };
    state.lastTask = allTasks[0] || null;
    state.lastErrors = allErrors;
    renderTaskErrors(allErrors);
    if (!allTaskIds.length) {
      elements.taskStatus.textContent = "已提交，无任务 ID";
      showToast("队列已提交，但响应里没有找到任务 ID");
      updateTaskOverview();
      return;
    }
    setTasks(allTaskIds, allTasks);
    showToast(`已按 ${promptItems.length} 个 Prompt 依次提交 ${allTaskIds.length} 条视频任务`);
    startPolling();
  } catch (error) {
    elements.taskStatus.textContent = "队列提交失败";
    elements.resultVideoState.textContent = "未生成";
    renderTaskErrors([{ message: error.message }]);
    updateTaskOverview();
    showToast(error.message);
  } finally {
    elements.submitBtn.disabled = false;
    updateSkillQueueSubmitState();
  }
}

function readTaskId(task) {
  if (!task || typeof task !== "object") return "";
  return task.id || task.task_id || task.taskId || task.data?.id || task.data?.task_id || "";
}

function setTask(taskId, status) {
  setTasks([taskId], [{ id: taskId, status }]);
}

function setTasks(taskIds, tasks = []) {
  state.taskIds = taskIds.slice();
  state.taskMap = {};
  taskIds.forEach((taskId, index) => {
    state.taskMap[taskId] = tasks[index] || { id: taskId, status: "submitted" };
  });
  state.taskId = taskIds[0] || "";
  elements.taskId.textContent = taskIds.length > 1 ? `${taskIds.length} 个任务` : taskIds[0] || "未提交";
  elements.taskStatus.textContent = summarizeTaskStatus();
  elements.pollBtn.disabled = !taskIds.length;
  renderBatchList();
  updateTaskOverview();
}

function getTaskStatus(task) {
  return String(task?.status || task?.data?.status || "submitted");
}

function isTerminalStatus(status) {
  return ["succeeded", "failed", "canceled", "cancelled"].includes(String(status).toLowerCase());
}

function isSuccessStatus(status) {
  return String(status).toLowerCase() === "succeeded";
}

function isFailedStatus(status) {
  return ["failed", "canceled", "cancelled"].includes(String(status).toLowerCase());
}

function statusClassFor(status) {
  const value = String(status || "").toLowerCase();
  if (value.includes("succeeded") || value.includes("完成")) return "status-success";
  if (value.includes("failed") || value.includes("fail") || value.includes("失败") || value.includes("canceled") || value.includes("cancelled")) return "status-error";
  if (value.includes("submit") || value.includes("running") || value.includes("progress") || value.includes("queued") || value.includes("处理中") || value.includes("提交中")) return "status-running";
  if (value.includes("/")) return "status-running";
  return "status-idle";
}

function findTaskError(value) {
  const seen = new Set();
  const queue = [value];
  while (queue.length) {
    const current = queue.shift();
    if (!current || seen.has(current)) continue;
    if (typeof current === "object") seen.add(current);
    if (typeof current === "string") return current;
    if (Array.isArray(current)) {
      queue.push(...current);
      continue;
    }
    if (typeof current === "object") {
      for (const [key, item] of Object.entries(current)) {
        if (/error|message|reason|detail|msg/i.test(key) && typeof item === "string" && item.trim()) {
          return item.trim();
        }
        if (typeof item === "object") queue.push(item);
      }
    }
  }
  return "";
}

function renderTaskErrors(errors = []) {
  const failedTasks = state.taskIds
    .map((taskId) => {
      const task = state.taskMap[taskId];
      const status = getTaskStatus(task);
      if (!isFailedStatus(status)) return null;
      return { taskId, message: findTaskError(task) || status };
    })
    .filter(Boolean);
  state.lastErrors = [...failedTasks, ...errors].filter((item) => item.message);
  if (!state.lastErrors.length) {
    elements.taskErrorBox.hidden = true;
    elements.taskErrorBox.innerHTML = "";
    return;
  }
  const policyBlocked = state.lastErrors.some((item) => isPolicyViolationMessage(item.message));
  elements.taskErrorBox.hidden = false;
  elements.taskErrorBox.innerHTML = `
    <strong>失败原因</strong>
    ${state.lastErrors
      .slice(0, 4)
      .map((item) => `<p>${item.taskId ? `<b>${escapeHtml(item.taskId)}</b> · ` : ""}${escapeHtml(item.message)}</p>`)
      .join("")}
    ${
      policyBlocked
        ? '<div class="task-error-tip"><b>合规处理建议</b><span>如果当前策略只要检测到人脸就失败，请不要强制提交头像图或带脸视频。开启无脸安全模式，用文字描述头像特征，并把参考视频处理成背影、遮脸、裁掉头部或只保留动作构图的版本。</span></div>'
        : ""
    }
  `;
}

function isPolicyViolationMessage(message) {
  return /违规|安全|审核|敏感|风控|policy|violation|violat|safety|moderation|risk|blocked|content/i.test(message || "");
}

function updateTaskOverview() {
  const total = state.taskIds.length;
  const statuses = state.taskIds.map((taskId) => getTaskStatus(state.taskMap[taskId]));
  const finished = statuses.filter(isTerminalStatus).length;
  const succeeded = statuses.filter(isSuccessStatus).length;
  const failed = statuses.filter(isFailedStatus).length;
  const progress = total ? Math.round((finished / total) * 100) : 0;
  const statusText = elements.taskStatus.textContent || summarizeTaskStatus();

  elements.taskCountLabel.textContent = total ? (total === 1 ? "单任务生成" : `批量 ${total} 条`) : "等待提交";
  elements.taskProgress.textContent = total ? `${finished}/${total}` : "0/0";
  elements.taskProgressBar.style.width = `${progress}%`;
  elements.pollState.textContent = state.pollTimer ? "自动轮询中" : total ? "可手动查询" : "轮询未启动";
  elements.taskQueueNote.textContent = total
    ? `${succeeded} 条成功，${failed} 条失败，点击任务 ID 可切换预览`
    : "提交后显示每条任务状态";
  elements.taskStatus.className = `status-badge ${statusClassFor(statusText)}`;
  if (elements.retryFailedBtn) {
    elements.retryFailedBtn.disabled = !failed;
    elements.retryFailedBtn.title = failed ? `修复并重试 ${failed} 条失败任务` : "当前没有失败任务";
  }
  updateOpsSummary();
}

function summarizeTaskStatus() {
  if (!state.taskIds.length) return "待命";
  const statuses = state.taskIds.map((taskId) => getTaskStatus(state.taskMap[taskId]));
  if (statuses.length === 1) return statuses[0];
  const finished = statuses.filter(isTerminalStatus).length;
  return `${finished}/${statuses.length} 已完成`;
}

async function pollStatus(manual = false) {
  const taskIds = state.taskIds.length ? state.taskIds : state.taskId ? [state.taskId] : [];
  if (!taskIds.length) {
    showToast("还没有可查询的任务 ID");
    return;
  }

  const errors = [];
  let renderedVideo = false;

  for (const taskId of taskIds) {
    try {
      const result = await requestJson(`/api/tasks/${encodeURIComponent(taskId)}`);
      state.taskMap[taskId] = result.task;
      if (taskId === state.taskId) {
        state.lastTask = result.task;
      }
      const status = getTaskStatus(result.task);
      updateHistoryStatus(taskId, status);

      const videoUrl = findVideoUrl(result.task);
      if (videoUrl && (!renderedVideo || taskId === state.taskId)) {
        renderVideo(videoUrl);
        renderedVideo = true;
      }
    } catch (error) {
      errors.push({ taskId, message: error.message });
    }
  }

  renderBatchList();
  renderTaskErrors(errors);
  elements.taskStatus.textContent = summarizeTaskStatus();
  updateTaskOverview();
  displayJson({
    quantity: taskIds.length,
    tasks: taskIds.map((taskId) => state.taskMap[taskId]),
    request: state.lastRequest,
    errors,
  });

  const statuses = taskIds.map((taskId) => getTaskStatus(state.taskMap[taskId]));
  const done = statuses.every(isTerminalStatus);
  if (done) {
    stopPolling();
    const succeeded = statuses.filter((status) => status.toLowerCase() === "succeeded").length;
    showToast(succeeded ? `${succeeded}/${taskIds.length} 条视频生成完成` : "任务已结束");
  } else if (manual) {
    showToast(errors.length ? `部分查询失败：${errors[0].message}` : `当前状态：${summarizeTaskStatus()}`);
  }
}

function startPolling() {
  elements.pollBtn.disabled = false;
  stopPolling();
  state.pollTimer = window.setInterval(() => pollStatus(false), 8000);
  updateTaskOverview();
  pollStatus(false);
}

function stopPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  updateTaskOverview();
}

function findVideoUrl(value) {
  const seen = new Set();
  const queue = [value];
  while (queue.length) {
    const current = queue.shift();
    if (!current || seen.has(current)) continue;
    if (typeof current === "object") seen.add(current);

    if (typeof current === "string") {
      if (/^https?:\/\/.+\.(mp4|mov|webm|m4v)(\?|$)/i.test(current)) return current;
      continue;
    }

    if (Array.isArray(current)) {
      queue.push(...current);
      continue;
    }

    if (typeof current === "object") {
      for (const [key, item] of Object.entries(current)) {
        if (/video|output|url/i.test(key) && typeof item === "string" && /^https?:\/\//.test(item)) {
          return item;
        }
        queue.push(item);
      }
    }
  }
  return "";
}

function renderVideo(url) {
  elements.videoStage.innerHTML = "";
  const video = document.createElement("video");
  video.controls = true;
  video.playsInline = true;
  video.src = url;
  elements.videoStage.appendChild(video);
  elements.resultVideoState.textContent = "已生成，可预览";
  state.lastVideoUrl = url;
  elements.copyVideoBtn.disabled = false;
  elements.downloadVideoLink.hidden = false;
  elements.downloadVideoLink.href = url;
}

async function copyVideoUrl() {
  if (!state.lastVideoUrl) {
    showToast("还没有可复制的视频 URL");
    return;
  }
  await navigator.clipboard.writeText(state.lastVideoUrl);
  showToast("视频 URL 已复制");
}

async function copyTaskIds() {
  const taskIds = state.taskIds.length ? state.taskIds : state.taskId ? [state.taskId] : [];
  if (!taskIds.length) {
    showToast("还没有可复制的任务 ID");
    return;
  }
  await navigator.clipboard.writeText(taskIds.join("\n"));
  showToast(taskIds.length === 1 ? "任务 ID 已复制" : `${taskIds.length} 个任务 ID 已复制`);
}

function renderBatchList() {
  elements.batchList.innerHTML = "";
  if (!state.taskIds.length) {
    elements.batchList.innerHTML = `
      <article class="batch-empty">
        <strong>还没有任务</strong>
        <small>点击右侧提交按钮后，这里会显示每条生成任务。</small>
      </article>
    `;
    return;
  }

  state.taskIds.forEach((taskId, index) => {
    const task = state.taskMap[taskId] || { status: "submitted" };
    const status = getTaskStatus(task);
    const taskError = isFailedStatus(status) ? findTaskError(task) : "";
    const promptLabel = state.taskPromptMap?.[taskId] || "";
    const videoUrl = findVideoUrl(task);
    const row = document.createElement("article");
    row.className = `batch-item ${taskId === state.taskId ? "active" : ""}`;
    row.innerHTML = `
      <span class="batch-index">${index + 1}</span>
      <div class="batch-copy">
        <button type="button" data-task-id="${escapeHtml(taskId)}">${escapeHtml(taskId)}</button>
        <small>${escapeHtml(taskError || promptLabel || (taskId === state.taskId ? "当前预览任务" : "点击查看这一条任务"))}</small>
      </div>
      <span class="batch-status ${statusClassFor(status)}">${escapeHtml(status)}</span>
      <div class="batch-actions">
        <button type="button" data-action="copy-prompt">复制Prompt</button>
        ${isFailedStatus(status) ? '<button type="button" data-action="retry-task">修复重试</button>' : ""}
        ${videoUrl ? '<button type="button" data-action="preview-video">预览</button>' : ""}
      </div>
    `;
    row.querySelector("button").addEventListener("click", () => {
      state.taskId = taskId;
      elements.taskId.textContent = taskId;
      elements.taskStatus.textContent = status;
      if (videoUrl) renderVideo(videoUrl);
      renderBatchList();
      updateTaskOverview();
      pollStatus(true);
    });
    row.querySelector('[data-action="copy-prompt"]')?.addEventListener("click", async () => {
      await copyTaskPrompt(taskId);
    });
    row.querySelector('[data-action="retry-task"]')?.addEventListener("click", () => {
      retryTask(taskId).catch((error) => showToast(error.message));
    });
    row.querySelector('[data-action="preview-video"]')?.addEventListener("click", () => {
      if (videoUrl) {
        state.taskId = taskId;
        renderVideo(videoUrl);
        renderBatchList();
        updateTaskOverview();
      }
    });
    elements.batchList.appendChild(row);
  });
}

async function copyTaskPrompt(taskId) {
  const prompt = state.taskPromptTextMap[taskId] || state.taskPayloadMap[taskId]?.prompt || "";
  if (!prompt) {
    showToast("这条任务没有保存完整 Prompt");
    return;
  }
  await navigator.clipboard.writeText(prompt);
  showToast("这条任务的 Prompt 已复制");
}

function repairRetryPayload(payload, taskId) {
  const source = payload || {};
  const prompt = state.taskPromptTextMap[taskId] || source.prompt || elements.prompt.value.trim();
  const hasRisk = hasIdentityRiskPrompt(prompt) || source.faceSwapSubmit;
  const repairedPrompt = hasRisk
    ? normalizeVirtualAvatarPrompt(prompt).replace(/换脸|换头像|换头|替换人脸|替换面部|脸部替换|面部替换|身份替换|复刻真人|精准复刻/gi, "AI 虚拟角色外观参考重新生成")
    : prompt;
  return {
    ...source,
    prompt: repairedPrompt,
    quantity: 1,
    faceSwapSubmit: false,
    faceSwapVirtual: source.faceSwapVirtual || hasRisk,
    generateAudio: Boolean(source.generateAudio),
    watermark: Boolean(source.watermark),
  };
}

async function retryTask(taskId) {
  const sourcePayload = state.taskPayloadMap[taskId];
  if (!sourcePayload) {
    showToast("这条任务没有保存请求参数，请回填 Prompt 后重新提交");
    return;
  }
  const retryPayload = repairRetryPayload(sourcePayload, taskId);
  const refs = [...(retryPayload.refImages || []), ...(retryPayload.refVideos || []), ...(retryPayload.refAudios || [])];
  const nonHttpRef = refs.find((url) => !isHttpUrl(url) || isLocalOrPrivateUrl(url));
  if (nonHttpRef) {
    showToast("重试失败：素材 URL 需要公网可访问");
    return;
  }

  elements.retryFailedBtn.disabled = true;
  elements.taskStatus.textContent = "重试提交中";
  renderTaskErrors([]);
  updateTaskOverview();

  try {
    const result = await requestJson("/api/tasks", {
      method: "POST",
      body: JSON.stringify(retryPayload),
    });
    const tasks = Array.isArray(result.tasks) && result.tasks.length ? result.tasks : result.task ? [result.task] : [];
    const taskIds = tasks.map(readTaskId).filter(Boolean);
    if (!taskIds.length) {
      renderTaskErrors([{ message: "重试已提交，但响应中没有任务 ID" }]);
      updateTaskOverview();
      return;
    }

    state.lastRequest = result.request;
    state.lastErrors = [];
    taskIds.forEach((newTaskId, index) => {
      state.taskMap[newTaskId] = tasks[index] || { id: newTaskId, status: "submitted" };
      state.taskPromptMap[newTaskId] = `重试 ${taskId}`;
      state.taskPromptTextMap[newTaskId] = retryPayload.prompt;
      state.taskPayloadMap[newTaskId] = { ...retryPayload, quantity: 1 };
      addHistory(newTaskId, tasks[index]?.status || "submitted", `重试 ${taskId} · ${retryPayload.prompt}`);
    });
    state.taskIds = uniqueUrls([...state.taskIds, ...taskIds]);
    state.taskId = taskIds[0];
    elements.taskId.textContent = state.taskId;
    elements.taskStatus.textContent = summarizeTaskStatus();
    elements.pollBtn.disabled = false;
    displayJson({ retryFrom: taskId, tasks, errors: result.errors || [], request: result.request });
    renderBatchList();
    updateTaskOverview();
    showToast(`已修复并重试 ${taskIds.length} 条任务`);
    startPolling();
  } catch (error) {
    elements.taskStatus.textContent = "重试失败";
    renderTaskErrors([{ taskId, message: error.message }]);
    updateTaskOverview();
    throw error;
  } finally {
    updateTaskOverview();
  }
}

async function retryFailedTasks() {
  const failedTaskIds = state.taskIds.filter((taskId) => isFailedStatus(getTaskStatus(state.taskMap[taskId])));
  if (!failedTaskIds.length) {
    showToast("当前没有失败任务");
    return;
  }
  for (const taskId of failedTaskIds) {
    await retryTask(taskId);
  }
}

function getPromptHistory() {
  try {
    const items = JSON.parse(window.localStorage.getItem(PROMPT_HISTORY_KEY) || "[]");
    return Array.isArray(items) ? items : [];
  } catch {
    return [];
  }
}

function setPromptHistory(items) {
  window.localStorage.setItem(PROMPT_HISTORY_KEY, JSON.stringify(items.slice(0, 20)));
  renderPromptHistory();
}

function addPromptHistory(prompt, meta = {}) {
  const text = String(prompt || "").trim();
  if (!text) return;
  const items = getPromptHistory().filter((item) => item.prompt !== text);
  items.unshift({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    prompt: text,
    brief: String(meta.brief || "").trim(),
    model: String(meta.model || "").trim(),
    ratio: meta.ratio || state.ratio,
    duration: meta.duration || state.duration,
    quantity: meta.quantity || state.quantity,
    createdAt: new Date().toLocaleString(),
  });
  setPromptHistory(items);
}

function renderPromptHistory() {
  if (!elements.promptHistoryList) return;
  const items = getPromptHistory();
  const panel = elements.promptHistoryList.closest(".top-prompt-history");
  panel?.classList.toggle("is-empty", !items.length);
  if (elements.clearPromptHistoryBtn) elements.clearPromptHistoryBtn.disabled = !items.length;
  elements.promptHistoryList.innerHTML = "";
  if (!items.length) {
    elements.promptHistoryList.innerHTML = `
      <article class="prompt-history-empty">
        <strong>暂无生成记录</strong>
        <small>点击 AI智能体 生成提示词后，会自动保存到这里。</small>
      </article>
    `;
    return;
  }

  items.forEach((item, index) => {
    const row = document.createElement("article");
    row.className = "prompt-history-item";
    row.innerHTML = `
      <div class="prompt-history-meta">
        <strong>提示词 ${items.length - index}</strong>
        <small>${escapeHtml(item.createdAt || "")} · ${escapeHtml(item.model || "AI")} · ${escapeHtml(item.ratio || state.ratio)} · ${escapeHtml(item.duration || state.duration)}s · ${escapeHtml(item.quantity || 1)}条</small>
      </div>
      <p>${escapeHtml(item.prompt || "")}</p>
      <div class="prompt-history-actions">
        <button type="button" data-action="use">回填</button>
        <button type="button" data-action="copy">复制</button>
        <button type="button" data-action="remove">删除</button>
      </div>
    `;
    row.querySelector('[data-action="use"]').addEventListener("click", () => {
      elements.prompt.value = item.prompt || "";
      updatePromptCount();
      displayJson(payloadFromForm());
      elements.prompt.focus();
      showToast("提示词已回填");
    });
    row.querySelector('[data-action="copy"]').addEventListener("click", async () => {
      await navigator.clipboard.writeText(item.prompt || "");
      showToast("提示词已复制");
    });
    row.querySelector('[data-action="remove"]').addEventListener("click", () => {
      setPromptHistory(getPromptHistory().filter((entry) => entry.id !== item.id));
      showToast("提示词记录已删除");
    });
    elements.promptHistoryList.appendChild(row);
  });
}

async function generatePromptWithAi() {
  const brief = elements.aiBrief.value.trim();
  const draftPrompt = elements.prompt.value.trim();
  if (!brief && !draftPrompt) {
    showToast("先写一点产品卖点或已有 Prompt");
    return;
  }

  const originalText = elements.aiGenerateBtn.textContent;
  elements.aiGenerateBtn.disabled = true;
  elements.aiGenerateBtn.textContent = "生成中";

  try {
    const payload = {
      brief,
      draftPrompt,
      targetMarket: creativeMarketValue(),
      contentLanguage: resolvedCreativeLanguage(),
      ratio: state.ratio,
      duration: state.duration,
      quantity: state.quantity,
      refImages: splitLines(elements.images.value),
      refVideos: splitLines(elements.videos.value),
      refAudios: splitLines(elements.audios.value),
      generateAudio: elements.audioToggle.checked,
      watermark: elements.watermarkToggle.checked,
    };
    const result = await requestJson("/api/prompt/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    elements.prompt.value = result.prompt || "";
    addPromptHistory(result.prompt, {
      brief,
      model: result.model,
      ratio: state.ratio,
      duration: state.duration,
      quantity: state.quantity,
    });
    updatePromptCount();
    displayJson({ aiModel: result.model, generatedPrompt: result.prompt });
    showToast("AI 提示词已生成");
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.aiGenerateBtn.disabled = false;
    elements.aiGenerateBtn.textContent = originalText;
  }
}

async function generatePlanWithSkill() {
  const brief = elements.aiBrief.value.trim();
  const draftPrompt = elements.prompt.value.trim();
  if (!brief && !draftPrompt) {
    showToast("先写商品资料、落地页卖点或已有 Prompt");
    return;
  }

  const originalText = elements.skillGenerateBtn.textContent;
  elements.skillGenerateBtn.disabled = true;
  elements.aiGenerateBtn.disabled = true;
  elements.skillGenerateBtn.textContent = "Skill生成中";

  try {
    const payload = {
      brief,
      draftPrompt,
      targetMarket: creativeMarketValue(),
      contentLanguage: resolvedCreativeLanguage(),
      ratio: state.ratio,
      duration: state.duration,
      quantity: state.quantity,
      promptCount: clampSkillPromptCount(elements.skillPromptCount?.value),
      refImages: splitLines(elements.images.value),
      refVideos: splitLines(elements.videos.value),
      refAudios: splitLines(elements.audios.value),
      generateAudio: elements.audioToggle.checked,
      watermark: elements.watermarkToggle.checked,
    };
    const result = await requestJson("/api/skill/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const skillContent = result.content || "";
    const seedancePrompt = result.seedancePrompt || result.prompt || "";
    state.skillPrompts = normalizeSkillPromptItems(result, seedancePrompt);
    state.lastSkillPrompt = seedancePrompt;
    elements.skillOutput.value = skillContent;
    elements.skillOutputPanel.hidden = false;
    autoResizeTextarea(elements.skillOutput);
    renderSkillPromptQueue();
    if (seedancePrompt) {
      elements.prompt.value = seedancePrompt;
      updatePromptCount();
      addPromptHistory(seedancePrompt, {
        brief,
        model: `${result.model || "AI"} · Skill`,
        ratio: state.ratio,
        duration: state.duration,
        quantity: state.quantity,
      });
    }
    displayJson({
      skillModel: result.model,
      skillFiles: result.skillFiles,
      productType: result.productType,
      seedancePrompt,
      prompts: state.skillPrompts,
      missingMaterials: result.missingMaterials,
    });
    showToast(state.skillPrompts.length > 1 ? `Skill 已生成 ${state.skillPrompts.length} 个 Prompt，首条已回填` : "Skill 方案已生成，Prompt 已回填");
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.skillGenerateBtn.disabled = false;
    elements.aiGenerateBtn.disabled = false;
    elements.skillGenerateBtn.textContent = originalText;
  }
}

function normalizeSkillPromptItems(result, fallbackPrompt) {
  const rawItems = Array.isArray(result.prompts) ? result.prompts : [];
  const items = rawItems
    .map((item, index) => {
      const prompt = String(item?.seedancePrompt || item?.seedance_prompt || item?.prompt || item || "").trim();
      if (!prompt) return null;
      return {
        id: `${Date.now()}-${index}-${Math.random().toString(16).slice(2)}`,
        title: String(item?.title || `Prompt ${index + 1}`).trim(),
        angle: String(item?.angle || "").trim(),
        prompt,
        negativePrompt: String(item?.negativePrompt || item?.negative_prompt || result.negativePrompt || "").trim(),
      };
    })
    .filter(Boolean);

  if (!items.length && fallbackPrompt) {
    items.push({
      id: `${Date.now()}-0-${Math.random().toString(16).slice(2)}`,
      title: "Prompt 1",
      angle: "Skill 默认提示词",
      prompt: fallbackPrompt,
      negativePrompt: String(result.negativePrompt || "").trim(),
    });
  }
  return items;
}

function renderSkillPromptQueue() {
  if (!elements.skillPromptQueue) return;
  elements.skillPromptQueue.innerHTML = "";
  const payload = payloadFromForm();
  const hasReference = hasVisualReference(payload);
  if (!state.skillPrompts.length) {
    elements.skillPromptQueue.innerHTML = `
      <article class="skill-prompt-empty">
        <strong>暂无 Prompt 队列</strong>
        <small>设置 Prompt 数量后点击 Skill生成方案。</small>
      </article>
    `;
    updateSkillQueueSubmitState(payload);
    return;
  }
  updateSkillQueueSubmitState(payload);
  state.skillPrompts.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "skill-prompt-card";
    card.innerHTML = `
      <div class="skill-prompt-card-head">
        <span>${index + 1}</span>
      <div>
        <strong>${escapeHtml(item.title || `Prompt ${index + 1}`)}</strong>
        <small>${escapeHtml(item.angle || "Seedance 视频提示词")}</small>
      </div>
    </div>
      <textarea rows="4" data-role="skill-prompt-text" data-prompt-index="${index}" aria-label="Prompt ${index + 1}">${escapeHtml(item.prompt)}</textarea>
      <div class="skill-prompt-card-actions">
        <button type="button" data-action="use">回填</button>
        <button type="button" data-action="copy">复制</button>
        <button type="button" data-action="submit-one" data-prompt-index="${index}">生成此条</button>
      </div>
    `;
    const promptTextarea = card.querySelector('[data-role="skill-prompt-text"]');
    promptTextarea.addEventListener("input", () => {
      item.prompt = promptTextarea.value;
      if (index === 0) state.lastSkillPrompt = promptTextarea.value.trim();
      autoResizeTextarea(promptTextarea);
      updateSkillQueueSubmitState(payloadFromForm());
    });
    autoResizeTextarea(promptTextarea);
    card.querySelector('[data-action="use"]').addEventListener("click", () => {
      useSkillPromptItem(index);
    });
    card.querySelector('[data-action="copy"]').addEventListener("click", async () => {
      await navigator.clipboard.writeText(item.prompt);
      showToast(`Prompt ${index + 1} 已复制`);
    });
    const submitOneButton = card.querySelector('[data-action="submit-one"]');
    submitOneButton.disabled = !hasReference || !String(item.prompt || "").trim();
    submitOneButton.title = !String(item.prompt || "").trim() ? "请先填写这条 Prompt" : hasReference ? "生成此条 Prompt" : "请先上传/填写参考图或参考视频";
    submitOneButton.addEventListener("click", () => {
      submitSkillPromptQueue([item]).catch((error) => showToast(error.message));
    });
    elements.skillPromptQueue.appendChild(card);
  });
}

function useSkillPromptItem(index = 0) {
  const item = state.skillPrompts[index];
  const prompt = String(item?.prompt || state.lastSkillPrompt || "").trim();
  if (!prompt) {
    showToast("暂无可回填的 Skill Prompt");
    return;
  }
  state.lastSkillPrompt = prompt;
  elements.prompt.value = prompt;
  updatePromptCount();
  displayJson(payloadFromForm());
  elements.prompt.focus();
  showToast(`${item?.title || "Skill Prompt"} 已回填`);
}

function useSkillPrompt() {
  useSkillPromptItem(0);
}

async function copySkillOutput() {
  const text = String(elements.skillOutput.value || "").trim();
  if (!text) {
    showToast("暂无 Skill 输出方案");
    return;
  }
  await navigator.clipboard.writeText(text);
  showToast("Skill 输出方案已复制");
}

function parseChatText() {
  const text = elements.chatInput.value.trim();
  if (!text) {
    showToast("先贴一段聊天文本");
    return;
  }

  const urls = [...new Set([...text.matchAll(/https?:\/\/\S+/g)].map((match) => cleanUrl(match[0])))];
  const fields = readFields(text);
  const classified = classifyUrls(urls);

  elements.prompt.value = fields.prompt || removeUrlsAndFieldLabels(text);
  updatePromptCount();
  elements.images.value = classified.images.join("\n");
  elements.videos.value = classified.videos.join("\n");
  elements.audios.value = classified.audios.join("\n");
  autoResizeUrlInputs();

  if (fields.ratio) {
    state.ratio = fields.ratio;
    setSegment($$("[data-ratio]"), "ratio", state.ratio);
  }
  if (fields.duration) {
    state.duration = Number(fields.duration);
    setSegment($$("[data-duration]"), "duration", state.duration);
  }
  if (fields.quantity) {
    setQuantity(fields.quantity);
  }
  if (fields.audio) {
    elements.audioToggle.checked = /^(true|yes|y|1|on|开|开启|需要|生成)$/i.test(fields.audio);
  }

  showToast("已解析到表单");
}

function cleanUrl(url) {
  return url.replace(/[.,;)\]，。；）】]+$/g, "");
}

function readFields(text) {
  const aliases = {
    prompt: ["要求", "需求", "描述", "prompt", "Prompt", "request", "Request", "description", "Description"],
    ratio: ["比例", "ratio", "Ratio"],
    duration: ["时长", "秒数", "duration", "Duration"],
    quantity: ["数量", "生成数量", "条数", "quantity", "Quantity"],
    audio: ["音频", "声音", "audio", "Audio"],
  };
  const result = {};
  const lines = text.split(/\r?\n/);

  for (const line of lines) {
    for (const [field, names] of Object.entries(aliases)) {
      const escaped = names.map((name) => escapeRegExp(name)).join("|");
      const match = line.match(new RegExp(`^\\s*(?:${escaped})\\s*[:=：]\\s*(.+?)\\s*$`));
      if (match) result[field] = match[1].trim();
    }
  }

  if (result.duration) {
    const match = result.duration.match(/\d+/);
    result.duration = match ? match[0] : "";
  }
  if (result.quantity) {
    const match = result.quantity.match(/\d+/);
    result.quantity = match ? match[0] : "";
  }
  return result;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function removeUrlsAndFieldLabels(text) {
  return text
    .replace(/https?:\/\/\S+/g, "")
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*(图\d*|图片\d*|视频\d*|音频\d*|比例|时长|数量|生成数量|条数)\s*[:=：]\s*/i, ""))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function classifyUrls(urls) {
  return urls.reduce(
    (result, url) => {
      if (/\.(mp4|mov|webm|m4v)(\?|$)/i.test(url)) result.videos.push(url);
      else if (/\.(mp3|wav|m4a|aac)(\?|$)/i.test(url)) result.audios.push(url);
      else result.images.push(url);
      return result;
    },
    { images: [], videos: [], audios: [] }
  );
}

function fillSample() {
  elements.aiBrief.value = sample.brief;
  if (elements.creativeProduct) elements.creativeProduct.value = "白色网纱百褶裙";
  writeMarketControl(elements.creativeMarket, elements.creativeCustomMarket, "日本");
  if (elements.creativeLanguage) elements.creativeLanguage.value = "auto";
  writeMarketControl(elements.promptMarket, elements.promptCustomMarket, "日本");
  if (elements.promptLanguage) elements.promptLanguage.value = "auto";
  if (elements.creativeAudience) elements.creativeAudience.value = "日本 25-40 岁通勤女性";
  if (elements.creativeStyle) elements.creativeStyle.value = "当地电商商品广告";
  if (elements.creativeSellingPoints) elements.creativeSellingPoints.value = "网纱层次、刺绣花纹、裙摆垂感、轻盈通勤";
  if (elements.creativeScript) elements.creativeScript.value = "0-2 秒展示整体上身；2-6 秒展示裙摆和面料细节；6-10 秒完成自然转身与通勤搭配收尾。";
  updateCreativeBriefState();
  elements.prompt.value = sample.prompt;
  updatePromptCount();
  elements.images.value = sample.images;
  elements.videos.value = sample.videos;
  elements.audios.value = sample.audios;
  elements.faceSwapRefs.value = "";
  elements.faceSwapPrompt.value = "";
  elements.faceSwapConsent.checked = false;
  elements.faceSwapVirtual.checked = false;
  elements.faceSwapSubmit.checked = false;
  autoResizeUrlInputs();
  state.ratio = "9:16";
  state.duration = 10;
  setQuantity(1);
  setSegment($$("[data-ratio]"), "ratio", state.ratio);
  setSegment($$("[data-duration]"), "duration", state.duration);
  displayJson(payloadFromForm());
  showToast("示例已填入");
}

function clearForm() {
  stopPolling();
  closeImageLightbox();
  closeVideoLightbox();
  closeAssetMentionPopover();
  elements.prompt.value = "";
  updatePromptCount();
  elements.images.value = "";
  elements.videos.value = "";
  elements.audios.value = "";
  elements.faceSwapRefs.value = "";
  elements.faceSwapPrompt.value = "";
  elements.faceSwapConsent.checked = false;
  elements.faceSwapVirtual.checked = false;
  elements.faceSwapSubmit.checked = false;
  autoResizeUrlInputs();
  elements.aiBrief.value = "";
  if (elements.creativeProduct) elements.creativeProduct.value = "";
  writeMarketControl(elements.creativeMarket, elements.creativeCustomMarket, "日本");
  if (elements.creativeLanguage) elements.creativeLanguage.value = "auto";
  writeMarketControl(elements.promptMarket, elements.promptCustomMarket, "日本");
  if (elements.promptLanguage) elements.promptLanguage.value = "auto";
  if (elements.creativeAudience) elements.creativeAudience.value = "";
  if (elements.creativeStyle) elements.creativeStyle.value = "当地电商商品广告";
  if (elements.creativeSellingPoints) elements.creativeSellingPoints.value = "";
  if (elements.creativeScript) elements.creativeScript.value = "";
  updateCreativeBriefState();
  elements.chatInput.value = "";
  elements.audioToggle.checked = false;
  elements.watermarkToggle.checked = false;
  setQuantity(1);
  state.taskId = "";
  state.taskIds = [];
  state.taskMap = {};
  state.taskPromptMap = {};
  state.lastRequest = null;
  state.lastTask = null;
  state.lastVideoUrl = "";
  state.lastErrors = [];
  state.lastSkillPrompt = "";
  state.skillPrompts = [];
  state.promptReview = null;
  state.promptReviewPrompt = "";
  if (elements.promptSkillReview) elements.promptSkillReview.hidden = true;
  if (elements.promptSkillReviewOutput) elements.promptSkillReviewOutput.value = "";
  elements.skillOutput.value = "";
  elements.skillOutputPanel.hidden = true;
  renderSkillPromptQueue();
  elements.taskId.textContent = "未提交";
  elements.taskStatus.textContent = "待命";
  elements.pollBtn.disabled = true;
  renderBatchList();
  displayJson({});
  elements.resultVideoState.textContent = "等待生成";
  elements.copyVideoBtn.disabled = true;
  elements.downloadVideoLink.hidden = true;
  elements.downloadVideoLink.href = "#";
  renderTaskErrors([]);
  elements.videoStage.innerHTML = '<div class="empty-state"><span aria-hidden="true">◇</span><p>生成成功后，视频会显示在这里。</p></div>';
  updateTaskOverview();
}

function getHistory() {
  return JSON.parse(window.localStorage.getItem("seedanceHistory") || "[]");
}

function setHistory(items) {
  window.localStorage.setItem("seedanceHistory", JSON.stringify(items.slice(0, 12)));
  renderHistory();
}

function addHistory(taskId, status, prompt) {
  const items = getHistory().filter((item) => item.taskId !== taskId);
  items.unshift({
    taskId,
    status,
    prompt: prompt.slice(0, 120),
    createdAt: new Date().toLocaleString(),
  });
  setHistory(items);
}

function updateHistoryStatus(taskId, status) {
  const items = getHistory();
  const item = items.find((entry) => entry.taskId === taskId);
  if (!item) return;
  item.status = status;
  setHistory(items);
}

function renderHistory() {
  const items = getHistory();
  elements.historyList.innerHTML = "";
  if (!items.length) {
    elements.historyList.innerHTML = '<p class="label">暂无历史任务</p>';
    return;
  }
  for (const item of items) {
    const row = document.createElement("article");
    row.className = "history-item";
    row.innerHTML = `
      <button type="button" data-task-id="${escapeHtml(item.taskId)}">${escapeHtml(item.taskId)}</button>
      <small>${escapeHtml(item.status)} · ${escapeHtml(item.createdAt)}</small>
      <small>${escapeHtml(item.prompt || "")}</small>
    `;
    row.querySelector("button").addEventListener("click", () => {
      setTask(item.taskId, item.status);
      pollStatus(true);
    });
    elements.historyList.appendChild(row);
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
  });
}

function bindUploadZone({ zone, button, input, upload }) {
  if (!zone || !button || !input) return;

  button.addEventListener("click", (event) => {
    event.stopPropagation();
    input.click();
  });
  zone.addEventListener("click", () => input.click());
  zone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.click();
    }
  });
  input.addEventListener("change", () => upload(input.files));
  ["dragenter", "dragover"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("drag-over");
    });
  });
  zone.addEventListener("drop", (event) => upload(event.dataTransfer.files));
}

function setConfigExpanded(expanded) {
  elements.apiConfigPanel.classList.toggle("is-collapsed", !expanded);
  elements.toggleConfigBtn.textContent = expanded ? "收起配置" : "展开配置";
  elements.toggleConfigBtn.setAttribute("aria-expanded", String(expanded));
}

function setWorkspaceView(view, options = {}) {
  const allowedViews = new Set(elements.workspaceViewButtons.map((button) => button.dataset.workspaceView));
  const nextView = allowedViews.has(view) ? view : "create";
  state.workspaceView = nextView;
  if (elements.composerForm) elements.composerForm.dataset.workspaceView = nextView;
  elements.workspacePanes.forEach((pane) => {
    pane.hidden = pane.dataset.workspacePane !== nextView;
  });
  elements.workspaceViewButtons.forEach((button) => {
    const active = button.dataset.workspaceView === nextView;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  try {
    window.localStorage.setItem(WORKSPACE_VIEW_KEY, nextView);
  } catch {
    // The active view still works when browser storage is unavailable.
  }
  if (options.scroll !== false) {
    elements.composerForm?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function initialWorkspaceView() {
  try {
    const queryView = new URLSearchParams(window.location.search).get("workspace");
    if (queryView) return queryView;
    return window.localStorage.getItem(WORKSPACE_VIEW_KEY) || "create";
  } catch {
    return "create";
  }
}

function scrollToWorkspaceSection(targetSelector) {
  const target = document.querySelector(targetSelector);
  if (!target) return;
  const workspacePane = target.closest("[data-workspace-pane]");
  if (workspacePane?.dataset.workspacePane) {
    setWorkspaceView(workspacePane.dataset.workspacePane, { scroll: false });
  }
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  elements.navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.scrollTarget === targetSelector);
  });
}

function updateBackToTopButton() {
  elements.backToTopBtn.classList.toggle("show", window.scrollY > 520);
}

function scrollToPageTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
  elements.navButtons.forEach((button) => button.classList.remove("active"));
}

function bindEvents() {
  elements.workspaceViewButtons.forEach((button) => {
    button.addEventListener("click", () => setWorkspaceView(button.dataset.workspaceView));
  });
  elements.navButtons.forEach((button) => {
    button.addEventListener("click", () => scrollToWorkspaceSection(button.dataset.scrollTarget));
  });
  elements.backToTopBtn.addEventListener("click", scrollToPageTop);
  window.addEventListener("scroll", updateBackToTopButton, { passive: true });

  $$("[data-ratio]").forEach((button) => {
    button.addEventListener("click", () => {
      state.ratio = button.dataset.ratio;
      setSegment($$("[data-ratio]"), "ratio", state.ratio);
      displayJson(payloadFromForm());
    });
  });

  $$("[data-duration]").forEach((button) => {
    button.addEventListener("click", () => {
      state.duration = Number(button.dataset.duration);
      setSegment($$("[data-duration]"), "duration", state.duration);
      displayJson(payloadFromForm());
    });
  });

  elements.healthBtn.addEventListener("click", loadHealth);
  elements.toggleConfigBtn.addEventListener("click", () => {
    setConfigExpanded(elements.apiConfigPanel.classList.contains("is-collapsed"));
  });
  elements.modelPresetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setModel(button.dataset.modelPreset);
      displayJson(payloadFromForm());
    });
  });
  elements.model.addEventListener("input", () => {
    updateModelDisplay();
    displayJson(payloadFromForm());
  });
  elements.model.addEventListener("change", () => {
    setModel(elements.model.value);
    displayJson(payloadFromForm());
  });
  elements.saveConfigBtn.addEventListener("click", () => saveConfig().catch((error) => showToast(error.message)));
  elements.testArkConfigBtn.addEventListener("click", () => testConfig("ark", "connectivity").catch((error) => showToast(error.message)));
  elements.invokeArkConfigBtn?.addEventListener("click", () => testConfig("ark", "invoke").catch((error) => showToast(error.message)));
  elements.testAiConfigBtn.addEventListener("click", () => testConfig("ai", "connectivity").catch((error) => showToast(error.message)));
  elements.invokeAiConfigBtn?.addEventListener("click", () => testConfig("ai", "invoke").catch((error) => showToast(error.message)));
  elements.clearArkKeyBtn.addEventListener("click", () => saveConfig({ clearArkApiKey: true }).catch((error) => showToast(error.message)));
  elements.clearAiKeyBtn.addEventListener("click", () => saveConfig({ clearAiApiKey: true }).catch((error) => showToast(error.message)));
  elements.clearImageKeyBtn.addEventListener("click", () => saveConfig({ clearImageGenerationApiKey: true }).catch((error) => showToast(error.message)));
  elements.arkEndpoint.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.aiBaseUrl.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.aiModel.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.imageBaseUrl.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.imageModel.addEventListener("change", () => displayJson(payloadFromForm()));
  bindUploadZone({
    zone: elements.imageUploadZone,
    button: elements.imageUploadBtn,
    input: elements.imageUploadInput,
    upload: uploadImageFiles,
  });
  bindUploadZone({
    zone: elements.videoUploadZone,
    button: elements.videoUploadBtn,
    input: elements.videoUploadInput,
    upload: uploadVideoFiles,
  });
  bindUploadZone({
    zone: elements.audioUploadZone,
    button: elements.audioUploadBtn,
    input: elements.audioUploadInput,
    upload: uploadAudioFiles,
  });
  bindUploadZone({
    zone: elements.faceSwapUploadZone,
    button: elements.faceSwapUploadBtn,
    input: elements.faceSwapUploadInput,
    upload: uploadFaceSwapFiles,
  });
  elements.prompt.addEventListener("input", () => {
    updatePromptCount();
    updateAssetMentionPopover();
    displayJson(payloadFromForm());
  });
  elements.prompt.addEventListener("scroll", syncPromptHighlightScroll);
  elements.faceSwapConsent.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.faceSwapVirtual.addEventListener("change", () => {
    if (elements.faceSwapVirtual.checked) {
      elements.faceSwapConsent.checked = true;
      elements.faceSwapSubmit.checked = false;
    }
    displayJson(payloadFromForm());
  });
  elements.faceSwapSubmit.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.faceSwapPrompt.addEventListener("input", () => displayJson(payloadFromForm()));
  elements.applyFaceSwapBtn.addEventListener("click", () => {
    const instruction = faceSwapInstructionFromForm();
    if (!faceSwapRefsFromForm().length) {
      showToast("请先添加授权人像素材");
      return;
    }
    if (!elements.faceSwapConsent.checked) {
      showToast("请先确认已获得人像素材授权");
      return;
    }
    if (!elements.prompt.value.includes(instruction)) {
      elements.prompt.value = [elements.prompt.value.trim(), instruction].filter(Boolean).join("\n\n");
      updatePromptCount();
    }
    displayJson(payloadFromForm());
    showToast("人像参考要求已写入提示词");
  });
  elements.prompt.addEventListener("keydown", handleMentionKeydown);
  elements.prompt.addEventListener("click", updateAssetMentionPopover);
  elements.prompt.addEventListener("keyup", (event) => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) updateAssetMentionPopover();
  });
  elements.prompt.addEventListener("blur", () => {
    window.setTimeout(closeAssetMentionPopover, 120);
  });
  elements.urlInputs.forEach((textarea) => {
    textarea.addEventListener("input", () => {
      autoResizeTextarea(textarea);
      displayJson(payloadFromForm());
    });
  });
  elements.assetCurrentBatchSelect?.addEventListener("change", () => setActiveAssetBatch(elements.assetCurrentBatchSelect.value));
  elements.assetNewBatchBtn?.addEventListener("click", createAssetBatchFromInput);
  elements.assetRenameBatchBtn?.addEventListener("click", renameActiveAssetBatch);
  elements.assetAssignBatchBtn?.addEventListener("click", assignCurrentAssetsToActiveBatch);
  elements.assetApplyTagsBtn?.addEventListener("click", () => applyTagsToActiveBatch());
  elements.assetTagInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applyTagsToActiveBatch();
    }
  });
  elements.assetBatchFilterSelect?.addEventListener("change", () => {
    ensureAssetBatchState().filterBatchId = elements.assetBatchFilterSelect.value;
    saveAssetBatches();
    displayJson(payloadFromForm());
  });
  elements.assetTagFilterSelect?.addEventListener("change", () => {
    ensureAssetBatchState().filterTag = elements.assetTagFilterSelect.value;
    saveAssetBatches();
    displayJson(payloadFromForm());
  });
  elements.assetClearFilterBtn?.addEventListener("click", () => {
    const batchState = ensureAssetBatchState();
    batchState.filterBatchId = "all";
    batchState.filterTag = "all";
    saveAssetBatches();
    displayJson(payloadFromForm());
    showToast("筛选已清除");
  });
  elements.buildBtn.addEventListener("click", () => buildRequest().catch((error) => showToast(error.message)));
  elements.clearTemplateInsertBtn.addEventListener("click", toggleTemplateReplaceMode);
  elements.strengthenPromptBtn.addEventListener("click", strengthenPromptStructure);
  elements.skillReviewPromptBtn?.addEventListener("click", () => optimizePromptWithSeedanceSkill().catch((error) => showToast(error.message)));
  elements.applyPromptSkillReviewBtn?.addEventListener("click", applyPromptSkillReview);
  elements.copyPromptSkillReviewBtn?.addEventListener("click", () => copyPromptSkillReview().catch((error) => showToast(error.message)));
  elements.aiGenerateBtn.addEventListener("click", generatePromptWithAi);
  elements.skillGenerateBtn.addEventListener("click", generatePlanWithSkill);
  elements.promptMarket?.addEventListener("change", () => {
    syncLocalizationControls("prompt");
    if (elements.promptMarket.value === "__custom__") elements.promptCustomMarket?.focus();
  });
  elements.promptCustomMarket?.addEventListener("input", () => syncLocalizationControls("prompt"));
  elements.promptCustomMarket?.addEventListener("change", () => syncLocalizationControls("prompt"));
  elements.promptLanguage?.addEventListener("change", () => syncLocalizationControls("prompt"));
  elements.creativeMarket?.addEventListener("change", () => {
    syncLocalizationControls("creative");
    if (elements.creativeMarket.value === "__custom__") elements.creativeCustomMarket?.focus();
  });
  elements.creativeCustomMarket?.addEventListener("input", () => syncLocalizationControls("creative"));
  elements.creativeCustomMarket?.addEventListener("change", () => syncLocalizationControls("creative"));
  elements.creativeLanguage?.addEventListener("change", () => syncLocalizationControls("creative"));
  [
    elements.creativeProduct,
    elements.creativeAudience,
    elements.creativeStyle,
    elements.creativeSellingPoints,
    elements.creativeScript,
  ].filter(Boolean).forEach((field) => {
    field.addEventListener("input", updateCreativeBriefState);
    field.addEventListener("change", updateCreativeBriefState);
  });
  elements.creativeAiBtn?.addEventListener("click", () => {
    if (syncCreativeBriefToAssistant()) generatePromptWithAi();
  });
  elements.creativeSkillBtn?.addEventListener("click", () => {
    if (syncCreativeBriefToAssistant()) generatePlanWithSkill();
  });
  elements.skillPromptCount.addEventListener("change", () => setSkillPromptCount(elements.skillPromptCount.value));
  elements.skillPromptCount.addEventListener("input", () => setSkillPromptCount(elements.skillPromptCount.value));
  elements.useSkillPromptBtn.addEventListener("click", useSkillPrompt);
  elements.submitSkillQueueBtn.addEventListener("click", () => submitSkillPromptQueue().catch((error) => showToast(error.message)));
  elements.copySkillOutputBtn.addEventListener("click", () => copySkillOutput().catch((error) => showToast(error.message)));
  elements.submitBtn.addEventListener("click", submitTask);
  elements.sampleBtn.addEventListener("click", fillSample);
  elements.clearBtn.addEventListener("click", clearForm);
  elements.repairPromptBtn.addEventListener("click", repairPromptCompliance);
  elements.quantityMinus.addEventListener("click", () => {
    setQuantity(state.quantity - 1);
    displayJson(payloadFromForm());
  });
  elements.quantityPlus.addEventListener("click", () => {
    setQuantity(state.quantity + 1);
    displayJson(payloadFromForm());
  });
  elements.quantityInput.addEventListener("change", () => {
    setQuantity(elements.quantityInput.value);
    displayJson(payloadFromForm());
  });
  elements.quantityInput.addEventListener("input", () => {
    state.quantity = clampQuantity(elements.quantityInput.value);
    displayJson(payloadFromForm());
  });
  elements.audioToggle.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.watermarkToggle.addEventListener("change", () => displayJson(payloadFromForm()));
  elements.parseChatBtn.addEventListener("click", parseChatText);
  elements.pollBtn.addEventListener("click", () => pollStatus(true));
  elements.retryFailedBtn.addEventListener("click", () => retryFailedTasks().catch((error) => showToast(error.message)));
  elements.copyTaskBtn.addEventListener("click", () => copyTaskIds().catch((error) => showToast(error.message)));
  elements.copyVideoBtn.addEventListener("click", () => copyVideoUrl().catch((error) => showToast(error.message)));
  elements.copyJsonBtn.addEventListener("click", async () => {
    await navigator.clipboard.writeText(elements.jsonPreview.textContent);
    showToast("JSON 已复制");
  });
  elements.clearHistoryBtn.addEventListener("click", () => setHistory([]));
  elements.clearPromptHistoryBtn.addEventListener("click", () => {
    setPromptHistory([]);
    showToast("提示词生成记录已清空");
  });
  elements.closeLightboxBtn.addEventListener("click", closeImageLightbox);
  elements.copyLightboxUrlBtn.addEventListener("click", () => copyLightboxUrl().catch((error) => showToast(error.message)));
  elements.imageLightbox.addEventListener("click", (event) => {
    if (event.target?.dataset?.lightboxClose !== undefined) closeImageLightbox();
  });
  elements.closeVideoLightboxBtn.addEventListener("click", closeVideoLightbox);
  elements.copyVideoLightboxUrlBtn.addEventListener("click", () => copyVideoLightboxUrl().catch((error) => showToast(error.message)));
  elements.videoLightbox.addEventListener("click", (event) => {
    if (event.target?.dataset?.videoLightboxClose !== undefined) closeVideoLightbox();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeImageLightbox();
      closeVideoLightbox();
    }
  });
}

loadCreativeBriefDraft();
const importedMaterialReversePrompt = applyMaterialReversePromptDraft();
bindEvents();
setWorkspaceView(initialWorkspaceView(), { scroll: false });
state.assetRoles = loadAssetRoles();
state.assetBatches = loadAssetBatches();
updateModelDisplay();
loadHealth();
renderPromptTemplates();
renderBatchList();
renderHistory();
renderPromptHistory();
renderSkillPromptQueue();
displayJson(payloadFromForm());
updateCreativeBriefState();
updatePromptCount();
updateTaskOverview();
autoResizeUrlInputs();
updateBackToTopButton();
if (importedMaterialReversePrompt) showToast("已从优秀素材片段回填 Seedance Prompt");
