const ASSET_BATCH_KEY = "seedanceAssetBatches";
const MANUAL_CLIP_SELECTION_KEY = "seedanceMaterialManualClips";
const MATERIAL_ANALYSIS_QUEUE_KEY = "seedanceMaterialAnalysisQueue";
const MATERIAL_REVERSE_PROMPT_DRAFT_KEY = "seedanceMaterialReversePromptDraftV1";
const MATERIAL_PRODUCT_DRAFT_KEY = "seedanceMaterialProductDraftV2";
const CHATCUT_PROJECT_URL_KEY = "seedanceChatCutProjectUrl";
const CHATCUT_SYNC_SCOPE_KEY = "seedanceChatCutSyncScope";
const MANUAL_CLIP_DEFAULT_MS = 6000;
const MANUAL_CLIP_MIN_MS = 1200;
const REVERSE_PROMPT_DURATIONS = [5, 10, 11, 15];
const REVERSE_PROMPT_MARKET_LANGUAGES = {
  日本: "日语",
  美国: "美式英语",
  英国: "英式英语",
  韩国: "韩语",
  法国: "法语",
  德国: "德语",
  西班牙: "西班牙语",
  意大利: "意大利语",
  巴西: "巴西葡萄牙语",
};
const PRODUCT_FILM_MAX_CLIPS = 24;
const PRODUCT_FILM_MIN_SCORE = 55;
const PRODUCT_FILM_MAX_CLIPS_PER_SOURCE = 2;
const PRODUCT_FILM_ROLE_PLANS = {
  ecommerce: ["hook", "try_on", "detail", "motion", "proof", "detail", "transition", "ending"],
  tryon: ["hook", "try_on", "motion", "try_on", "detail", "proof", "transition", "ending"],
  detail: ["hook", "detail", "proof", "detail", "motion", "try_on", "transition", "ending"],
};
const PRODUCT_FILM_ROLE_REQUIREMENTS = {
  ecommerce: ["hook", "try_on", "detail", "proof", "ending"],
  tryon: ["hook", "try_on", "motion", "detail", "ending"],
  detail: ["hook", "detail", "proof", "motion", "ending"],
};
const CHATCUT_SYNC_STATUS_META = {
  queued: { label: "待同步", tone: "queued" },
  syncing: { label: "同步中", tone: "running" },
  partial: { label: "部分完成", tone: "partial" },
  complete: { label: "已完成", tone: "done" },
  failed: { label: "失败", tone: "failed" },
  blocked: { label: "需处理", tone: "blocked" },
};
const PRODUCT_FILM_ROLE_DURATION_MS = {
  hook: [1200, 2400],
  try_on: [2200, 3800],
  detail: [1600, 3200],
  motion: [1800, 3400],
  transition: [1200, 2200],
  proof: [1800, 3200],
  ending: [1800, 3200],
  unassigned: [1500, 3000],
};
const MATERIAL_EDITING_TAG_GROUPS = [
  {
    label: "\u526a\u8f91\u7528\u9014",
    tags: [
      "\u5f00\u5934\u94a9\u5b50",
      "\u4e0a\u8eab\u5c55\u793a",
      "\u7ec6\u8282\u7279\u5199",
      "\u5356\u70b9\u8bc1\u660e",
      "\u52a8\u4f5c\u955c\u5934",
      "\u8f6c\u573a\u8fc7\u6e21",
      "\u7ed3\u5c3e\u6536\u53e3",
    ],
  },
  {
    label: "\u753b\u9762\u5185\u5bb9",
    tags: [
      "\u6574\u4f53\u7248\u578b",
      "\u6b63\u9762",
      "\u4fa7\u9762",
      "\u80cc\u9762",
      "\u8170\u5934",
      "\u659c\u6263",
      "\u7ebd\u6263",
      "\u53e3\u888b",
      "\u9762\u6599",
      "\u88e4\u811a",
    ],
  },
  {
    label: "\u5356\u70b9\u4fe1\u53f7",
    tags: [
      "\u663e\u7626",
      "\u663e\u817f\u957f",
      "\u906e\u8089",
      "\u9ad8\u8170",
      "\u9614\u817f",
      "\u767e\u642d",
      "\u8212\u9002",
      "\u5782\u611f",
      "\u901a\u52e4",
      "\u4f11\u95f2",
    ],
  },
  {
    label: "\u6df7\u526a\u51b3\u7b56",
    tags: [
      "\u9ad8\u5206\u4f18\u9009",
      "\u6e05\u6670\u7a33\u5b9a",
      "\u5149\u7ebf\u597d",
      "\u8282\u594f\u5207\u70b9",
      "\u53ef\u6df7\u526a",
      "\u5f85\u590d\u6838",
      "\u77ed\u7528\u907f\u5f00",
      "\u4e0d\u8fdb\u4e3b\u526a",
    ],
  },
];
const MATERIAL_TAG_GROUPS = [
  { label: "剪辑通道", tags: ["成品", "定制", "高光镜", "营销", "进阶剪辑", "AI建议", "废片"] },
  { label: "素材来源", tags: ["单品图展示", "通用片段", "网图", "达人素材", "数字人试穿"] },
  { label: "镜头用途", tags: ["待AI分析", "可剪辑", "开头钩子", "上身", "细节", "动作", "转场", "卖点"] },
];

const ANALYSIS_STATUS_OPTIONS = [
  { value: "queued", label: "待 AI 分析" },
  { value: "analyzing", label: "分析中" },
  { value: "analyzed", label: "已分析" },
  { value: "ready", label: "可剪辑" },
  { value: "hold", label: "待补拍" },
  { value: "rejected", label: "废弃" },
];

const EDIT_ROLE_OPTIONS = [
  { value: "unassigned", label: "待判断" },
  { value: "hook", label: "开头钩子" },
  { value: "try_on", label: "上身展示" },
  { value: "detail", label: "细节特写" },
  { value: "motion", label: "动作镜头" },
  { value: "transition", label: "转场氛围" },
  { value: "proof", label: "卖点证明" },
  { value: "ending", label: "结尾召回" },
];

const PRODUCT_COPY_ROLE_KEYWORDS = {
  hook: [
    "\u5f00\u5934", "\u94a9\u5b50", "\u7b2c\u4e00\u773c", "\u5438\u5f15", "\u4e3b\u63a8", "\u70ed\u5356", "\u4eba\u6c14",
    "\u30d5\u30c3\u30af", "\u6ce8\u76ee", "\u4eba\u6c17", "\u4e00\u756a", "\u30b7\u30eb\u30a8\u30c3\u30c8",
  ],
  try_on: [
    "\u4e0a\u8eab", "\u8bd5\u7a7f", "\u7248\u578b", "\u7a7f\u642d", "\u642d\u914d", "\u6574\u4f53", "\u6b63\u9762", "\u4fa7\u9762", "\u80cc\u9762",
    "\u7740\u7528", "\u30b3\u30fc\u30c7", "\u30b7\u30eb\u30a8\u30c3\u30c8", "\u30c8\u30c3\u30d7\u30b9",
  ],
  detail: [
    "\u8170", "\u8170\u5934", "\u659c\u6263", "\u6263", "\u7ebd\u6263", "\u53e3\u888b", "\u9762\u6599", "\u7ec6\u8282", "\u7279\u5199", "\u88e4\u811a", "\u8d70\u7ebf", "\u8d28\u611f",
    "\u30a6\u30a8\u30b9\u30c8", "\u30dc\u30bf\u30f3", "\u30dd\u30b1\u30c3\u30c8", "\u7d20\u6750", "\u30c7\u30a3\u30c6\u30fc\u30eb",
  ],
  motion: [
    "\u8d70", "\u884c\u8d70", "\u8d70\u8def", "\u8f6c\u8eab", "\u52a8\u4f5c", "\u6446\u52a8", "\u5782\u611f", "\u5750\u4e0b", "\u8d77\u8eab",
    "\u6b69\u304f", "\u52d5\u304f", "\u30bf\u30fc\u30f3", "\u63fa\u308c", "\u843d\u3061\u611f",
  ],
  proof: [
    "\u663e\u7626", "\u663e\u817f\u957f", "\u906e\u8089", "\u4fee\u9970", "\u8212\u670d", "\u8212\u9002", "\u767e\u642d", "\u4e0d\u6311\u4eba", "\u817f\u578b", "\u4f53\u578b",
    "\u7d30\u898b\u3048", "\u30ab\u30d0\u30fc", "\u697d", "\u811a\u9577", "\u30b9\u30bf\u30a4\u30eb",
  ],
  transition: [
    "\u8f6c\u573a", "\u8fc7\u6e21", "\u8282\u594f", "\u5207\u70b9", "\u5feb\u5207", "\u89d2\u5ea6\u5207\u6362",
    "\u30c6\u30f3\u30dd", "\u5207\u308a\u66ff\u3048",
  ],
  ending: [
    "\u7ed3\u5c3e", "\u6700\u540e", "\u540c\u6b3e", "\u8be6\u60c5", "\u4e0b\u5355", "\u5546\u54c1\u9875", "\u6536\u5c3e", "\u8d2d\u4e70",
    "\u30c1\u30a7\u30c3\u30af", "\u6c17\u306b\u306a\u308b", "\u30b5\u30a4\u30ba",
  ],
};

const PRIORITY_OPTIONS = [
  { value: "high", label: "高优先" },
  { value: "normal", label: "普通" },
  { value: "low", label: "低优先" },
];

const QUALITY_SCORE_OPTIONS = [
  { value: "0", label: "未评分" },
  { value: "5", label: "5 分" },
  { value: "4", label: "4 分" },
  { value: "3", label: "3 分" },
  { value: "2", label: "2 分" },
  { value: "1", label: "1 分" },
];

const UPLOAD_CONFIGS = {
  video: {
    endpoint: "/api/uploads/videos",
    fieldName: "videos",
    responseKey: "videos",
    fileTypePrefix: "video/",
    extensions: [".mp4", ".mov", ".webm", ".m4v"],
    emptyMessage: "请选择视频文件",
    uploadingText: "上传中",
    doneText: (count) => `已上传 ${count} 个视频`,
  },
};

const $ = (selector) => document.querySelector(selector);

const elements = {
  workflowNextDetail: $("#material-workflow-next-detail"),
  workflowNextBtn: $("#material-workflow-next-btn"),
  workflowBatchCount: $("#material-workflow-batch-count"),
  workflowPendingCount: $("#material-workflow-pending-count"),
  workflowReadyCount: $("#material-workflow-ready-count"),
  workflowMatchScore: $("#material-workflow-match-score"),
  workflowSteps: $("#material-workflow-steps"),
  totalState: $("#material-total-state"),
  activeState: $("#material-active-state"),
  refreshBtn: $("#material-refresh-btn"),
  currentBatchSelect: $("#material-current-batch-select"),
  newBatchBtn: $("#material-new-batch-btn"),
  batchNameInput: $("#material-batch-name-input"),
  renameBatchBtn: $("#material-rename-batch-btn"),
  deleteEmptyBatchBtn: $("#material-delete-empty-batch-btn"),
  tagInput: $("#material-tag-input"),
  applyCurrentTagsBtn: $("#material-apply-current-tags-btn"),
  quickTags: $("#material-quick-tags"),
  selectedTags: $("#material-selected-tags"),
  bulkStatusSelect: $("#material-bulk-status-select"),
  bulkRoleSelect: $("#material-bulk-role-select"),
  bulkPrioritySelect: $("#material-bulk-priority-select"),
  applyWorkflowBtn: $("#material-apply-workflow-btn"),
  syncUploadsBtn: $("#material-sync-uploads-btn"),
  analyzeQueuedBtn: $("#material-analyze-queued-btn"),
  analyzeForceBtn: $("#material-analyze-force-btn"),
  analysisStatus: $("#material-analysis-status"),
  analysisQueueSummary: $("#material-analysis-queue-summary"),
  analysisQueueList: $("#material-analysis-queue-list"),
  clearAnalysisQueueBtn: $("#material-clear-analysis-queue-btn"),
  urlImportInput: $("#material-url-import-input"),
  importUrlsBtn: $("#material-import-urls-btn"),
  localFolderInput: $("#material-local-folder-input"),
  importFolderBtn: $("#material-import-folder-btn"),
  allUploadZone: $("#material-all-upload-zone"),
  allUploadBtn: $("#material-all-upload-btn"),
  allUploadInput: $("#material-all-upload-input"),
  uploadQueueTitle: $("#material-upload-queue-title"),
  uploadQueueDetail: $("#material-upload-queue-detail"),
  uploadVideoCount: $("#material-upload-video-count"),
  totalCount: $("#material-total-count"),
  currentBatchCount: $("#material-current-batch-count"),
  taggedCount: $("#material-tagged-count"),
  queuedCount: $("#material-queued-count"),
  readyCount: $("#material-ready-count"),
  analyzedCount: $("#material-analyzed-count"),
  videoCount: $("#material-video-count"),
  holdCount: $("#material-hold-count"),
  unbatchedCount: $("#material-unbatched-count"),
  clearLibraryBtn: $("#material-clear-library-btn"),
  clearLibraryStatus: $("#material-clear-library-status"),
  autoPoolCount: $("#material-auto-pool-count"),
  autoPoolDuration: $("#material-auto-pool-duration"),
  autoPoolHighCount: $("#material-auto-pool-high-count"),
  autoPoolUpdated: $("#material-auto-pool-updated"),
  autoPoolRoles: $("#material-auto-pool-roles"),
  showAutoPoolBtn: $("#material-show-auto-pool-btn"),
  generateJianyingDraftBtn: $("#material-generate-jianying-draft-btn"),
  chatcutProjectUrlInput: $("#material-chatcut-project-url-input"),
  chatcutProductKeyInput: $("#material-chatcut-product-key-input"),
  chatcutSyncScopeSelect: $("#material-chatcut-sync-scope-select"),
  chatcutSyncRefreshBtn: $("#material-chatcut-sync-refresh-btn"),
  chatcutSyncSubmitBtn: $("#material-chatcut-sync-submit-btn"),
  chatcutScopeCount: $("#material-chatcut-scope-count"),
  chatcutReadyCount: $("#material-chatcut-ready-count"),
  chatcutRequestCount: $("#material-chatcut-request-count"),
  chatcutLastStatus: $("#material-chatcut-last-status"),
  chatcutSyncStatus: $("#material-chatcut-sync-status"),
  chatcutSyncList: $("#material-chatcut-sync-list"),
  chatcutEmbedFrame: $("#material-chatcut-embed-frame"),
  chatcutEmbedStatus: $("#material-chatcut-embed-status"),
  chatcutEmbedReloadBtn: $("#material-chatcut-embed-reload-btn"),
  chatcutOpenWindowBtn: $("#material-chatcut-open-window-btn"),
  productNameInput: $("#material-product-name-input"),
  productDurationSelect: $("#material-product-duration-select"),
  productScopeSelect: $("#material-product-scope-select"),
  productStyleSelect: $("#material-product-style-select"),
  editPaceSelect: $("#material-edit-pace-select"),
  transitionStyleSelect: $("#material-transition-style-select"),
  captionStyleSelect: $("#material-caption-style-select"),
  productSellingPointsInput: $("#material-product-selling-points-input"),
  productDraftSaveState: $("#material-product-draft-save-state"),
  restoreProductDraftBtn: $("#material-restore-product-draft-btn"),
  clearProductDraftBtn: $("#material-clear-product-draft-btn"),
  copyAutofitBtn: $("#material-copy-autofit-btn"),
  matchPrecutBtn: $("#material-match-precut-btn"),
  productFilmClipCount: $("#material-product-film-clip-count"),
  productFilmDuration: $("#material-product-film-duration"),
  productFilmStatus: $("#material-product-film-status"),
  productQualityGate: $("#material-product-quality-gate"),
  productQualityLabel: $("#material-product-quality-label"),
  productQualityScore: $("#material-product-quality-score"),
  productQualityProgress: $("#material-product-quality-progress"),
  productQualityDetail: $("#material-product-quality-detail"),
  productQualityChecks: $("#material-product-quality-checks"),
  directionScore: $("#material-direction-score"),
  directionStatus: $("#material-direction-status"),
  directionUpdated: $("#material-direction-updated"),
  directionRoles: $("#material-direction-roles"),
  directionActions: $("#material-direction-actions"),
  refreshDirectionMonitorBtn: $("#material-refresh-direction-monitor-btn"),
  applyDirectionPlanBtn: $("#material-apply-direction-plan-btn"),
  productPreviewSummary: $("#material-product-preview-summary"),
  productPreviewList: $("#material-product-preview-list"),
  exportRoughCutBtn: $("#material-export-rough-cut-btn"),
  roughCutResult: $("#material-rough-cut-result"),
  generateProductFilmBtn: $("#material-generate-product-film-btn"),
  manualClipCount: $("#material-manual-clip-count"),
  manualClipDuration: $("#material-manual-clip-duration"),
  manualClipList: $("#material-manual-clip-list"),
  clearManualClipsBtn: $("#material-clear-manual-clips-btn"),
  manualSourceSelect: $("#material-manual-source-select"),
  manualSourcePlayer: $("#material-manual-source-player"),
  manualSourceStatus: $("#material-manual-source-status"),
  manualInInput: $("#material-manual-in-input"),
  manualOutInput: $("#material-manual-out-input"),
  manualRangeDuration: $("#material-manual-range-duration"),
  manualSetInBtn: $("#material-manual-set-in-btn"),
  manualSetOutBtn: $("#material-manual-set-out-btn"),
  manualAddRangeBtn: $("#material-manual-add-range-btn"),
  manualTimelineRuler: $("#material-manual-timeline-ruler"),
  manualTimelineTrack: $("#material-manual-timeline-track"),
  manualTimelineStatus: $("#material-manual-timeline-status"),
  manualSelectedEditor: $("#material-manual-selected-editor"),
  manualSelectedLabel: $("#material-manual-selected-label"),
  manualSelectedPreviewBtn: $("#material-manual-selected-preview-btn"),
  manualSelectedRemoveBtn: $("#material-manual-selected-remove-btn"),
  manualSelectedRole: $("#material-manual-selected-role"),
  manualSelectedTagInput: $("#material-manual-selected-tag-input"),
  manualApplyTagBtn: $("#material-manual-apply-tag-btn"),
  manualQuickTags: $("#material-manual-quick-tags"),
  manualSelectedTags: $("#material-manual-selected-tags"),
  draftCopyInput: $("#material-draft-copy-input"),
  draftVoiceProviderSelect: $("#material-draft-voice-provider-select"),
  draftSpeakerSelect: $("#material-draft-speaker-select"),
  draftVoiceoverToggle: $("#material-draft-voiceover-toggle"),
  elevenLabsFields: $("#material-elevenlabs-fields"),
  elevenLabsApiKeyInput: $("#material-elevenlabs-api-key-input"),
  elevenLabsVoiceIdInput: $("#material-elevenlabs-voice-id-input"),
  elevenLabsModelInput: $("#material-elevenlabs-model-input"),
  elevenLabsStatus: $("#material-elevenlabs-status"),
  jianyingDraftStatus: $("#material-jianying-draft-status"),
  invalidCount: $("#material-invalid-count"),
  invalidList: $("#material-invalid-list"),
  showInvalidBtn: $("#material-show-invalid-btn"),
  batchList: $("#material-batch-list"),
  showReadyBtn: $("#material-show-ready-btn"),
  showHoldBtn: $("#material-show-hold-btn"),
  priorityList: $("#material-priority-list"),
  workbenchAlerts: $("#material-workbench-alerts"),
  batchFilterSelect: $("#material-batch-filter-select"),
  tagFilterSelect: $("#material-tag-filter-select"),
  statusFilterSelect: $("#material-status-filter-select"),
  roleFilterSelect: $("#material-role-filter-select"),
  searchInput: $("#material-search-input"),
  clearFilterBtn: $("#material-clear-filter-btn"),
  filterCount: $("#material-filter-count"),
  assetList: $("#material-asset-list"),
  videoLightbox: $("#material-video-lightbox"),
  videoLightboxPlayer: $("#material-video-lightbox-player"),
  videoLightboxTitle: $("#material-video-lightbox-title"),
  videoLightboxUrl: $("#material-video-lightbox-url"),
  closeVideoLightboxBtn: $("#material-close-video-lightbox-btn"),
  copyVideoLightboxUrlBtn: $("#material-copy-video-lightbox-url-btn"),
  rewindVideoBtn: $("#material-rewind-video-btn"),
  forwardVideoBtn: $("#material-forward-video-btn"),
  reversePromptDialog: $("#material-reverse-prompt-dialog"),
  reversePromptSource: $("#material-reverse-prompt-source"),
  reversePromptMeta: $("#material-reverse-prompt-meta"),
  reversePromptModes: [...document.querySelectorAll('input[name="material-reverse-prompt-mode"]')],
  reversePromptSubject: $("#material-reverse-prompt-subject"),
  reversePromptMarket: $("#material-reverse-prompt-market"),
  reversePromptLanguage: $("#material-reverse-prompt-language"),
  reversePromptEvidence: $("#material-reverse-prompt-evidence"),
  reversePromptOutput: $("#material-reverse-prompt-output"),
  reversePromptStatus: $("#material-reverse-prompt-status"),
  closeReversePromptBtn: $("#material-close-reverse-prompt-btn"),
  rebuildReversePromptBtn: $("#material-rebuild-reverse-prompt-btn"),
  skillReversePromptBtn: $("#material-skill-reverse-prompt-btn"),
  copyReversePromptBtn: $("#material-copy-reverse-prompt-btn"),
  sendReversePromptBtn: $("#material-send-reverse-prompt-btn"),
  backToTopBtn: $("#material-back-to-top-btn"),
  toast: $("#material-toast"),
};

const state = {
  library: normalizeLibrary({}),
  libraryLoaded: false,
  obsidian: null,
  directionMonitor: null,
  directionMonitorRunning: false,
  chatcutSync: { version: 1, requests: [], assets: [] },
  chatcutSyncRunning: false,
  chatcutSuggestedProductKey: "",
  kindFilter: "video",
  statusFilter: "all",
  roleFilter: "all",
  search: "",
  manualClips: loadManualClipSelection(),
  manualSourceUrl: "",
  selectedManualClipId: "",
  manualClipSaveTimer: null,
  manualClipSyncError: "",
  productFilmEdits: {},
  productFilmCopyMisses: [],
  productFilmCopyPlan: null,
  productPrecutSignature: "",
  productDraftSaveTimer: null,
  directorClipLimit: 0,
  analysisQueue: loadAnalysisQueue(),
  analysisRunning: false,
  draftRunning: false,
  roughCutRunning: false,
  roughCutRecord: null,
  clearLibraryRunning: false,
  remoteImportRunning: false,
  folderImportRunning: false,
  config: null,
  videoLightboxUrl: "",
  reversePromptItem: null,
  reversePromptSegment: null,
  reversePromptRunning: false,
  saveTimer: null,
  toastTimer: null,
};

function defaultBatchName(date = new Date()) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `素材批次 ${month}/${day} ${hour}:${minute}`;
}

function makeBatch(name = "") {
  return {
    id: `batch-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    name: name.trim() || defaultBatchName(),
    createdAt: new Date().toISOString(),
  };
}

function splitTags(value) {
  const source = Array.isArray(value) ? value.join(",") : String(value || "");
  return [...new Set(source.split(/[\s,，、#]+/).map((tag) => tag.trim().replace(/^#+/, "").slice(0, 18)).filter(Boolean))].slice(0, 12);
}

function optionValue(value, options, fallback) {
  const current = String(value || "").trim();
  return options.some((option) => option.value === current) ? current : fallback;
}

function optionLabel(options, value) {
  return options.find((option) => option.value === value)?.label || value;
}

function defaultEditRoleForKind(kind) {
  return normalizeKind(kind) === "audio" ? "bgm" : "unassigned";
}

function normalizeAnalysisStatus(value) {
  return optionValue(value, ANALYSIS_STATUS_OPTIONS, "queued");
}

function normalizeEditRole(value, kind = "image") {
  return optionValue(value, EDIT_ROLE_OPTIONS, defaultEditRoleForKind(kind));
}

function normalizePriority(value) {
  return optionValue(value, PRIORITY_OPTIONS, "normal");
}

function normalizeQualityScore(value) {
  const score = Number(value);
  return Number.isInteger(score) && score >= 0 && score <= 5 ? score : 0;
}

function normalizeSecondMark(mark) {
  const source = mark && typeof mark === "object" && !Array.isArray(mark) ? mark : {};
  return {
    second: Number(source.second || 0) || 0,
    startMs: Number(source.startMs || 0) || 0,
    endMs: Number(source.endMs || 0) || 0,
    frameCount: Number(source.frameCount || 0) || 0,
    keyFrames: Number(source.keyFrames || 0) || 0,
    avgPacketSize: Number(source.avgPacketSize || 0) || 0,
    relativePacket: Number(source.relativePacket || 0) || 0,
    motionDelta: Number(source.motionDelta || 0) || 0,
    timelineZone: String(source.timelineZone || "").slice(0, 40),
    brightness: Number(source.brightness || 0) || 0,
    contrast: Number(source.contrast || 0) || 0,
    sharpness: Number(source.sharpness || 0) || 0,
    visualMotion: Number(source.visualMotion || 0) || 0,
    visualNote: String(source.visualNote || "").slice(0, 120),
    score: Math.max(0, Math.min(100, Number(source.score || 0) || 0)),
    note: String(source.note || "").slice(0, 120),
    pros: Array.isArray(source.pros) ? source.pros.map((item) => String(item).trim()).filter(Boolean).slice(0, 4) : [],
    cons: Array.isArray(source.cons) ? source.cons.map((item) => String(item).trim()).filter(Boolean).slice(0, 4) : [],
    cutAdvice: String(source.cutAdvice || "").slice(0, 220),
    tone: ["good", "ok", "warn", "bad"].includes(String(source.tone || "")) ? String(source.tone || "") : "ok",
  };
}

function normalizeAdProfile(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const cleanList = (items, limit = 8) => Array.isArray(items) ? items.map((item) => String(item).trim()).filter(Boolean).slice(0, limit) : [];
  return {
    adScore: Math.max(0, Math.min(100, Number(source.adScore || 0) || 0)),
    qualityTier: String(source.qualityTier || "").slice(0, 8),
    primaryStage: String(source.primaryStage || "").slice(0, 40),
    primaryStageLabel: String(source.primaryStageLabel || "").slice(0, 40),
    contentSummary: String(source.contentSummary || "").slice(0, 420),
    productSignals: cleanList(source.productSignals, 12),
    strengths: cleanList(source.strengths, 8),
    risks: cleanList(source.risks, 8),
    recommendedTags: cleanList(source.recommendedTags, 12),
    bestSegmentIds: cleanList(source.bestSegmentIds, 12),
    stageCoverage: source.stageCoverage && typeof source.stageCoverage === "object" && !Array.isArray(source.stageCoverage) ? source.stageCoverage : {},
    stageBestScores: source.stageBestScores && typeof source.stageBestScores === "object" && !Array.isArray(source.stageBestScores) ? source.stageBestScores : {},
  };
}

function normalizeAnalysis(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const keyframes = Array.isArray(source.keyframes) ? source.keyframes.slice(0, 120) : [];
  const suggestions = Array.isArray(source.suggestions) ? source.suggestions.map((item) => String(item).trim()).filter(Boolean).slice(0, 40) : [];
  const autoTags = splitTags(source.autoTags || []);
  const secondMarks = Array.isArray(source.secondMarks) ? source.secondMarks.slice(0, 600).map(normalizeSecondMark) : [];
  const frameIndexSource = source.frameIndex && typeof source.frameIndex === "object" && !Array.isArray(source.frameIndex) ? source.frameIndex : {};
  const cutHints = Array.isArray(source.cutHints)
    ? source.cutHints.filter((item) => item && typeof item === "object").slice(0, 24).map((item) => ({
      startMs: Number(item.startMs || 0) || 0,
      endMs: Number(item.endMs || 0) || 0,
      role: String(item.role || "").slice(0, 40),
      confidence: Number(item.confidence || 0) || 0,
      reason: String(item.reason || "").slice(0, 220),
    }))
    : [];
  const segments = Array.isArray(source.segments)
    ? source.segments.filter((item) => item && typeof item === "object").slice(0, 120).map((item, index) => ({
      id: String(item.id || `seg-${index + 1}`).slice(0, 80),
      startMs: Number(item.startMs || 0) || 0,
      endMs: Number(item.endMs || 0) || 0,
      durationMs: Number(item.durationMs || 0) || 0,
      role: String(item.role || "").slice(0, 40),
      adStage: String(item.adStage || "").slice(0, 40),
      adStageLabel: String(item.adStageLabel || "").slice(0, 40),
      score: Math.max(0, Math.min(100, Number(item.score || 0) || 0)),
      confidence: Number(item.confidence || 0) || 0,
      reason: String(item.reason || "").slice(0, 260),
      contentDescription: String(item.contentDescription || "").slice(0, 420),
      strengths: Array.isArray(item.strengths) ? item.strengths.map((value) => String(value).trim()).filter(Boolean).slice(0, 8) : [],
      risks: Array.isArray(item.risks) ? item.risks.map((value) => String(value).trim()).filter(Boolean).slice(0, 8) : [],
      copyAngle: String(item.copyAngle || "").slice(0, 260),
      secondMarks: Array.isArray(item.secondMarks) ? item.secondMarks.slice(0, 12).map(normalizeSecondMark) : [],
      tags: splitTags(item.tags || []),
    }))
    : [];
  return {
    status: normalizeAnalysisStatus(source.status),
    frameCount: Number(source.frameCount || 0) || 0,
    keyframes,
    summary: String(source.summary || "").slice(0, 1200),
    suggestions,
    autoTags,
    secondMarks,
    frameIndex: {
      path: String(frameIndexSource.path || "").slice(0, 260),
      mode: String(frameIndexSource.mode || "").slice(0, 80),
      totalFrames: Number(frameIndexSource.totalFrames || 0) || 0,
      indexedFrames: Number(frameIndexSource.indexedFrames || 0) || 0,
      complete: Boolean(frameIndexSource.complete),
      maxRecords: Number(frameIndexSource.maxRecords || 0) || 0,
    },
    adProfile: normalizeAdProfile(source.adProfile),
    cutHints,
    segments,
    updatedAt: String(source.updatedAt || ""),
  };
}

function normalizeTechnical(value, kind = "image") {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const width = Number(source.width || 0) || 0;
  const height = Number(source.height || 0) || 0;
  const fps = Number(source.fps || 0) || 0;
  const durationMs = Number(source.durationMs || source.duration || 0) || 0;
  const bitrateKbps = Number(source.bitrateKbps || source.bitrate || 0) || 0;
  const orientation = ["portrait", "landscape", "square", "audio", "unknown"].includes(String(source.orientation || ""))
    ? String(source.orientation || "")
    : kind === "audio"
      ? "audio"
      : width && height
        ? width === height
          ? "square"
          : width > height
            ? "landscape"
            : "portrait"
        : "unknown";
  return {
    width,
    height,
    durationMs,
    fps: fps > 0 ? Number(fps.toFixed(3)) : 0,
    bitrateKbps: bitrateKbps > 0 ? Math.round(bitrateKbps) : 0,
    orientation,
    hasAudio: kind === "audio" ? true : Boolean(source.hasAudio),
    videoCodec: String(source.videoCodec || "").slice(0, 80),
    audioCodec: String(source.audioCodec || "").slice(0, 80),
  };
}

function normalizeLibrary(value) {
  const batches = (Array.isArray(value?.batches) ? value.batches : [])
    .map((batch) => ({
      id: String(batch?.id || "").trim(),
      name: String(batch?.name || "").trim().slice(0, 40),
      createdAt: String(batch?.createdAt || new Date().toISOString()),
    }))
    .filter((batch) => batch.id && batch.name);
  if (!batches.length) batches.push(makeBatch("默认批次"));

  const rawItems = value?.items && typeof value.items === "object" && !Array.isArray(value.items) ? value.items : {};
  const items = Object.fromEntries(
    Object.entries(rawItems).map(([url, item]) => {
      const kind = normalizeKind(item?.kind || inferKindFromUrl(url));
      const analysis = normalizeAnalysis(item?.analysis);
      const technical = normalizeTechnical(item?.technical, kind);
      return [
        url,
        {
          batchId: String(item?.batchId || ""),
          tags: splitTags(item?.tags || []),
          aiTags: splitTags(item?.aiTags || analysis.autoTags || []),
          kind,
          name: String(item?.name || ""),
          size: Number(item?.size || 0),
          contentType: String(item?.contentType || ""),
          localPath: String(item?.localPath || ""),
          obsidianPath: String(item?.obsidianPath || ""),
          sourcePath: String(item?.sourcePath || ""),
          externalPath: String(item?.externalPath || ""),
          sourceUrl: String(item?.sourceUrl || ""),
          importMethod: String(item?.importMethod || ""),
          importedAt: String(item?.importedAt || ""),
          analysisStatus: normalizeAnalysisStatus(item?.analysisStatus || item?.status),
          editRole: normalizeEditRole(item?.editRole || item?.clipRole || item?.role, kind),
          priority: normalizePriority(item?.priority),
          qualityScore: normalizeQualityScore(item?.qualityScore),
          notes: String(item?.notes || "").slice(0, 500),
          analysis,
          technical,
          addedAt: String(item?.addedAt || item?.uploadedAt || new Date().toISOString()),
        },
      ];
    })
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

function normalizeChatCutSync(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  return {
    version: Number(source.version || 1) || 1,
    updatedAt: String(source.updatedAt || ""),
    requests: Array.isArray(source.requests) ? source.requests.filter((item) => item && typeof item === "object").slice(-100) : [],
    assets: Array.isArray(source.assets) ? source.assets.filter((item) => item && typeof item === "object").slice(-5000) : [],
  };
}

function loadChatCutSyncPreferences() {
  try {
    if (elements.chatcutProjectUrlInput) elements.chatcutProjectUrlInput.value = window.localStorage.getItem(CHATCUT_PROJECT_URL_KEY) || "";
    const scope = window.localStorage.getItem(CHATCUT_SYNC_SCOPE_KEY) || "filtered";
    if (elements.chatcutSyncScopeSelect) elements.chatcutSyncScopeSelect.value = ["filtered", "batch"].includes(scope) ? scope : "filtered";
  } catch {
    // Preferences are optional; the server ledger remains authoritative.
  }
}

function saveChatCutSyncPreferences() {
  try {
    window.localStorage.setItem(CHATCUT_PROJECT_URL_KEY, String(elements.chatcutProjectUrlInput?.value || "").trim());
    window.localStorage.setItem(CHATCUT_SYNC_SCOPE_KEY, String(elements.chatcutSyncScopeSelect?.value || "filtered"));
  } catch {
    // Preferences are optional; submitting a request does not depend on localStorage.
  }
}

function chatCutEmbedUrl() {
  const raw = String(elements.chatcutProjectUrlInput?.value || "").trim();
  if (!raw) return "https://app.chatcut.io/zh/";
  try {
    const url = new URL(raw);
    if (!["app.chatcut.io", "chatcut.io"].includes(url.hostname)) return "https://app.chatcut.io/zh/";
    return url.href;
  } catch {
    return "https://app.chatcut.io/zh/";
  }
}

function updateChatCutEmbed({ force = false } = {}) {
  const url = chatCutEmbedUrl();
  if (elements.chatcutOpenWindowBtn) elements.chatcutOpenWindowBtn.href = url;
  if (!elements.chatcutEmbedFrame) return;
  if (force || elements.chatcutEmbedFrame.src !== url) {
    elements.chatcutEmbedFrame.src = url;
    if (elements.chatcutEmbedStatus) elements.chatcutEmbedStatus.textContent = url.includes("/editor/") ? "正在加载当前 ChatCut 项目" : "正在加载 ChatCut 素材库首页";
  }
}

function loadLocalLibraryFallback() {
  try {
    return normalizeLibrary(JSON.parse(window.localStorage.getItem(ASSET_BATCH_KEY) || "{}"));
  } catch {
    return normalizeLibrary({});
  }
}

function loadAnalysisQueue() {
  try {
    const raw = JSON.parse(window.localStorage.getItem(MATERIAL_ANALYSIS_QUEUE_KEY) || "[]");
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((job) => job && typeof job === "object" && job.id)
      .slice(0, 16)
      .map((job) => ({
        id: String(job.id),
        label: String(job.label || "素材分析"),
        scope: String(job.scope || ""),
        status: ["queued", "running", "done", "failed"].includes(job.status) ? job.status : "queued",
        createdAt: String(job.createdAt || new Date().toISOString()),
        startedAt: String(job.startedAt || ""),
        completedAt: String(job.completedAt || ""),
        resultText: String(job.resultText || ""),
        error: String(job.error || ""),
      }));
  } catch {
    return [];
  }
}

function saveAnalysisQueue() {
  try {
    window.localStorage.setItem(MATERIAL_ANALYSIS_QUEUE_KEY, JSON.stringify((state.analysisQueue || []).slice(0, 16)));
  } catch {
    // Local queue history is helpful but not critical.
  }
}

function materialAnalysisActionName(options = {}) {
  if (options.syncOnly) return "同步 uploads";
  if (options.force) return "重跑视频分析";
  return "Skill 分析素材";
}

function materialAnalysisScopeText(options = {}) {
  const allItems = entries();
  const queued = allItems.filter((item) => ["queued", "analyzing"].includes(item.analysisStatus)).length;
  if (options.syncOnly) return "扫描 uploads 并登记新视频";
  if (options.force) return allItems.length ? `全量重跑 ${allItems.length} 个视频` : "等待素材导入";
  if (queued) return `待分析 ${queued} 个视频`;
  return allItems.length ? `检查素材库 ${allItems.length} 个视频` : "等待素材导入";
}

function materialAnalysisResultText(result = {}) {
  const synced = Array.isArray(result.synced) ? result.synced.length : 0;
  const analyzedItems = Array.isArray(result.analyzed) ? result.analyzed : [];
  const analyzed = analyzedItems.length;
  const segments = analyzedItems.reduce((sum, item) => sum + (Number(item?.segments || 0) || 0), 0);
  const failures = Array.isArray(result.failures) ? result.failures.length : 0;
  return [`新增 ${synced}`, `分析 ${analyzed}`, `片段 ${segments}`, `待复核 ${failures}`].join(" · ");
}

function addAnalysisQueueJob(options = {}) {
  const job = {
    id: `analysis-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    label: materialAnalysisActionName(options),
    scope: materialAnalysisScopeText(options),
    status: "queued",
    createdAt: new Date().toISOString(),
    startedAt: "",
    completedAt: "",
    resultText: "",
    error: "",
  };
  state.analysisQueue = [job, ...(state.analysisQueue || [])].slice(0, 16);
  saveAnalysisQueue();
  renderAnalysisQueue();
  return job.id;
}

function updateAnalysisQueueJob(id, patch = {}) {
  if (!id) return;
  state.analysisQueue = (state.analysisQueue || []).map((job) => (job.id === id ? { ...job, ...patch } : job));
  saveAnalysisQueue();
  renderAnalysisQueue();
}

function formatAnalysisQueueTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function analysisQueueStatusMeta(status) {
  const map = {
    queued: { tone: "queued", label: "排队" },
    running: { tone: "running", label: "运行中" },
    done: { tone: "done", label: "完成" },
    failed: { tone: "failed", label: "失败" },
  };
  return map[status] || map.queued;
}

function renderAnalysisQueue() {
  if (!elements.analysisQueueList || !elements.analysisQueueSummary) return;
  const jobs = state.analysisQueue || [];
  const running = jobs.filter((job) => job.status === "running").length;
  const done = jobs.filter((job) => job.status === "done").length;
  const failed = jobs.filter((job) => job.status === "failed").length;
  elements.analysisQueueSummary.textContent = jobs.length
    ? `最近 ${jobs.length} 个任务 · 运行中 ${running} · 完成 ${done} · 失败 ${failed}`
    : "暂无分析任务";
  if (!jobs.length) {
    elements.analysisQueueList.innerHTML = "";
    return;
  }
  elements.analysisQueueList.innerHTML = jobs.slice(0, 6).map((job) => {
    const meta = analysisQueueStatusMeta(job.status);
    const time = formatAnalysisQueueTime(job.completedAt || job.startedAt || job.createdAt);
    const detail = job.status === "failed" ? job.error : job.resultText || job.scope;
    return `
      <article class="material-analysis-queue-item ${meta.tone}">
        <span>${escapeHtml(meta.label)}</span>
        <div>
          <strong>${escapeHtml(job.label)}</strong>
          <small>${escapeHtml([time, detail].filter(Boolean).join(" · "))}</small>
        </div>
      </article>
    `;
  }).join("");
}

function hasLibraryContent(library) {
  const normalized = normalizeLibrary(library || {});
  return Object.keys(normalized.items || {}).length > 0 || normalized.batches.length > 1;
}

function saveLibrary() {
  window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(state.library));
  window.clearTimeout(state.saveTimer);
  state.saveTimer = window.setTimeout(() => persistLibrary().catch((error) => showToast(error.message)), 120);
}

async function loadLibrary() {
  try {
    const payload = await requestJson("/api/material-library");
    const remoteLibrary = normalizeLibrary(payload.library || {});
    const localLibrary = loadLocalLibraryFallback();
    state.library = !hasLibraryContent(remoteLibrary) && hasLibraryContent(localLibrary) ? localLibrary : remoteLibrary;
    state.obsidian = payload.obsidian || null;
    try {
      const monitorPayload = await requestJson("/api/material-library/director-monitor");
      state.directionMonitor = monitorPayload.monitor || null;
    } catch (monitorError) {
      state.directionMonitor = null;
    }
    try {
      const manualDraftPayload = await requestJson("/api/material-library/manual-cut-draft");
      const manualDraft = manualDraftPayload.draft || {};
      const remoteClips = normalizeManualClipSelection(manualDraft.clips || []);
      if (manualDraft.updatedAt || remoteClips.length || !state.manualClips.length) {
        state.manualClips = remoteClips;
        state.selectedManualClipId = remoteClips.some((clip) => clip.id === manualDraft.selectedClipId)
          ? String(manualDraft.selectedClipId || "")
          : remoteClips[0]?.id || "";
        window.localStorage.setItem(MANUAL_CLIP_SELECTION_KEY, JSON.stringify(state.manualClips));
      } else {
        persistManualCutDraft().catch(() => {});
      }
    } catch (manualDraftError) {
      state.manualClipSyncError = manualDraftError.message;
    }
    try {
      const syncPayload = await requestJson("/api/material-library/chatcut-sync");
      state.chatcutSync = normalizeChatCutSync(syncPayload.sync || {});
    } catch (syncError) {
      state.chatcutSync = normalizeChatCutSync({});
    }
    if (state.library === localLibrary) {
      await persistLibrary();
      showToast("Synced browser material cache to Obsidian");
    }
  } catch (error) {
    state.library = loadLocalLibraryFallback();
    showToast(`Obsidian 素材库读取失败，已使用浏览器缓存：${error.message}`);
  }
  state.libraryLoaded = true;
  render();
}

async function loadChatCutSync({ silent = false } = {}) {
  try {
    const payload = await requestJson("/api/material-library/chatcut-sync");
    state.chatcutSync = normalizeChatCutSync(payload.sync || {});
    renderChatCutSyncPanel(entries(), filterEntries(entries()));
    if (!silent) showToast("ChatCut 同步状态已刷新");
  } catch (error) {
    if (!silent) showToast(`ChatCut 同步状态读取失败：${error.message}`);
  }
}

function directionMonitorPayload(allItems = entries(), filteredItems = null) {
  const scope = String(elements.productScopeSelect?.value || "current");
  const scopedItems = productFilmScopeItems(allItems, filteredItems);
  return {
    scope,
    batchId: activeBatch()?.id || "",
    style: productFilmStyle(),
    urls: scopedItems.map((item) => item.url).filter(Boolean),
  };
}

async function refreshDirectionMonitor({ silent = false } = {}) {
  if (state.directionMonitorRunning) return;
  state.directionMonitorRunning = true;
  if (elements.refreshDirectionMonitorBtn) elements.refreshDirectionMonitorBtn.disabled = true;
  if (elements.applyDirectionPlanBtn) elements.applyDirectionPlanBtn.disabled = true;
  if (elements.directionStatus && !silent) elements.directionStatus.textContent = "日本剪辑导演正在判断素材方向...";
  try {
    const allItems = entries();
    const filtered = filterEntries(allItems);
    const payload = await requestJson("/api/material-library/director-monitor", {
      method: "POST",
      body: JSON.stringify(directionMonitorPayload(allItems, filtered)),
    });
    state.directionMonitor = payload.monitor || null;
    state.obsidian = payload.obsidian || state.obsidian;
    render();
    if (!silent) showToast("剪辑方向监控已写入 Obsidian");
  } catch (error) {
    if (elements.directionStatus) elements.directionStatus.textContent = `方向监控失败：${error.message}`;
    if (!silent) showToast(error.message);
  } finally {
    state.directionMonitorRunning = false;
    if (elements.refreshDirectionMonitorBtn) elements.refreshDirectionMonitorBtn.disabled = false;
    if (elements.applyDirectionPlanBtn) elements.applyDirectionPlanBtn.disabled = false;
  }
}

function directorSafeCopyRewrite(part, index, missingRoles) {
  if (!part?.role || !missingRoles.includes(part.role)) return String(part?.text || "").trim();
  const japanese = /[\u3040-\u30ff]/.test(String(part.text || ""));
  const variants = {
    motion: japanese
      ? ["別角度からシルエットをチェック。", "着用ラインをゆっくり見てみましょう。"]
      : ["换个角度看整体版型。", "这里继续看上身轮廓。"],
    proof: japanese
      ? ["着用シルエットを自然に見せます。", "全体のラインをチェック。"]
      : ["这里展示整体上身版型。", "画面重点看整体轮廓。"],
    detail: japanese
      ? ["全体のデザインを別角度から。", "シルエットを近めにチェック。"]
      : ["换个角度看整体设计。", "这里用近一点的画面看版型。"],
    ending: japanese
      ? ["最後に全体シルエットをチェック。"]
      : ["最后再看一次整体版型。"],
    hook: japanese
      ? ["まずは全体シルエットから。"]
      : ["开头先看整体版型。"],
  };
  const options = variants[part.role] || (japanese ? ["全体のシルエットをチェック。"] : ["这里展示整体版型。"]);
  return options[index % options.length];
}

async function applyDirectionPlan() {
  if (!state.directionMonitor) await refreshDirectionMonitor({ silent: true });
  const monitor = state.directionMonitor && typeof state.directionMonitor === "object" ? state.directionMonitor : null;
  const plan = monitor?.editingPlan && typeof monitor.editingPlan === "object" ? monitor.editingPlan : null;
  if (!monitor || !plan) {
    showToast("导演方案暂不可用，请先刷新监控");
    return;
  }

  const durationSeconds = String(Math.round(Number(plan.recommendedDurationSeconds || 15) || 15));
  const durationOption = elements.productDurationSelect
    ? [...elements.productDurationSelect.options].find((option) => option.value === durationSeconds)
    : null;
  if (elements.productDurationSelect && durationOption) elements.productDurationSelect.value = durationSeconds;
  state.directorClipLimit = Math.max(4, Math.round(Number(plan.recommendedClipCount || 6) || 6));

  const missingRoles = Array.isArray(monitor.missingRoles) ? monitor.missingRoles.filter(Boolean) : [];
  const rawText = productManualCopyText();
  let rewrittenCount = 0;
  if (rawText && elements.productSellingPointsInput) {
    const rewrittenParts = rawProductCopyParts(rawText).map((part, index) => {
      const text = directorSafeCopyRewrite(part, index, missingRoles);
      if (text && text !== part.text) rewrittenCount += 1;
      return { ...part, text, originalText: part.text };
    });
    const uniqueParts = rewrittenParts.filter((part, index, all) => {
      const key = normalizedProductCopyKey(part.text);
      return key && all.findIndex((candidate) => normalizedProductCopyKey(candidate.text) === key) === index;
    });
    const paced = paceProductCopyParts(uniqueParts, {
      targetDurationMs: productFilmTargetMs(),
      maxLines: state.directorClipLimit,
      style: productFilmStyle(),
    });
    elements.productSellingPointsInput.value = paced.parts.map((part) => part.text).filter(Boolean).join("\n");
    state.productFilmCopyPlan = paced.plan;
  }

  clearProductFilmCopyOverrides();
  render();
  elements.productPreviewList?.closest(".material-product-preview-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  showToast(`已应用导演方案：${durationSeconds}s · ${state.directorClipLimit} 段${rewrittenCount ? ` · 改写 ${rewrittenCount} 句` : ""}`);
}

function toggleVoiceProviderFields() {
  const provider = elements.draftVoiceProviderSelect?.value || "edge";
  if (elements.elevenLabsFields) {
    elements.elevenLabsFields.hidden = provider !== "elevenlabs";
  }
  if (elements.draftSpeakerSelect) {
    elements.draftSpeakerSelect.disabled = provider === "elevenlabs";
  }
}

function applyRuntimeConfig(config) {
  state.config = config || null;
  const elevenlabs = config?.elevenlabs || {};
  if (elements.elevenLabsVoiceIdInput && elevenlabs.voiceId) {
    elements.elevenLabsVoiceIdInput.value = elevenlabs.voiceId;
  }
  if (elements.elevenLabsModelInput && elevenlabs.model) {
    elements.elevenLabsModelInput.value = elevenlabs.model;
  }
  if (elements.elevenLabsStatus) {
    const voice = elevenlabs.voiceId ? ` · Voice ${elevenlabs.voiceId.slice(0, 8)}...` : "";
    elements.elevenLabsStatus.textContent = elevenlabs.hasApiKey
      ? `ElevenLabs Key 已配置${voice}`
      : "ElevenLabs Key 未配置；日语配音不需要 Key，选择 ElevenLabs 时才需要。";
  }
}

async function loadRuntimeConfig() {
  try {
    const payload = await requestJson("/api/config");
    applyRuntimeConfig(payload.config || null);
  } catch {
    applyRuntimeConfig(null);
  }
  toggleVoiceProviderFields();
}

async function persistLibrary() {
  const payload = await requestJson("/api/material-library", {
    method: "POST",
    body: JSON.stringify({ library: state.library }),
  });
  state.library = normalizeLibrary(payload.library || state.library);
  state.obsidian = payload.obsidian || state.obsidian;
  window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(state.library));
}

function setClearLibraryBusy(isBusy) {
  state.clearLibraryRunning = isBusy;
  if (elements.clearLibraryBtn) {
    elements.clearLibraryBtn.disabled = isBusy;
    elements.clearLibraryBtn.textContent = isBusy ? "清空中..." : "清空素材库";
  }
}

async function clearMaterialLibrary() {
  if (state.clearLibraryRunning) return;
  const count = entries().length;
  const message = count
    ? `确定清空当前 ${count} 个素材记录吗？\n\n只会清空面板记录和自动混剪候选池，不会删除 NAS 原文件、上传视频文件、分析报告或剪映草稿。`
    : "当前素材库已经是空的，是否仍然重置素材库索引？";
  if (!window.confirm(message)) return;

  setClearLibraryBusy(true);
  if (elements.clearLibraryStatus) elements.clearLibraryStatus.textContent = "正在清空素材库索引，并同步写入 Obsidian...";
  try {
    window.clearTimeout(state.saveTimer);
    const payload = await requestJson("/api/material-library/clear", { method: "POST", body: JSON.stringify({}) });
    state.library = normalizeLibrary(payload.library || {});
    state.obsidian = payload.obsidian || state.obsidian;
    state.manualClips = [];
    state.selectedManualClipId = "";
    window.localStorage.removeItem(MANUAL_CLIP_SELECTION_KEY);
    window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(state.library));
    clearFilters({ persist: false, toast: false });
    const clearedCount = Number(payload.clearedCount || 0) || 0;
    const clearedPool = Number(payload.clearedAutoPoolCount || 0) || 0;
    const ignoredUploadCount = Number(payload.ignoredUploadCount || 0) || 0;
    if (elements.clearLibraryStatus) {
      const ignoreText = ignoredUploadCount ? `，${ignoredUploadCount} 个历史上传文件已加入不同步清单` : "";
      elements.clearLibraryStatus.textContent = `已清空 ${clearedCount} 个素材记录，自动混剪候选池 ${clearedPool} 条已归零${ignoreText}。原视频文件没有删除。`;
    }
    showToast("素材库已清空");
  } catch (error) {
    if (elements.clearLibraryStatus) elements.clearLibraryStatus.textContent = `清空失败：${error.message}`;
    showToast(error.message);
  } finally {
    setClearLibraryBusy(false);
  }
}

function setAnalysisControlsBusy(isBusy) {
  state.analysisRunning = isBusy;
  [elements.syncUploadsBtn, elements.analyzeQueuedBtn, elements.analyzeForceBtn].forEach((button) => {
    if (button) button.disabled = isBusy;
  });
}

async function runMaterialAnalysis(options = {}) {
  if (state.analysisRunning) return;
  const actionName = materialAnalysisActionName(options);
  const queueJobId = addAnalysisQueueJob(options);
  setAnalysisControlsBusy(true);
  updateAnalysisQueueJob(queueJobId, { status: "running", startedAt: new Date().toISOString(), error: "" });
  elements.analysisStatus.textContent = `${actionName}进行中，分析结果会写入 Obsidian...`;
  try {
    const payload = await requestJson("/api/material-library/analyze", {
      method: "POST",
      body: JSON.stringify(options),
    });
    state.library = normalizeLibrary(payload.library || state.library);
    state.obsidian = payload.obsidian || state.obsidian;
    window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(state.library));
    render();
    refreshDirectionMonitor({ silent: true });
    const result = payload.result || {};
    const synced = Array.isArray(result.synced) ? result.synced.length : 0;
    const analyzedItems = Array.isArray(result.analyzed) ? result.analyzed : [];
    const analyzed = analyzedItems.length;
    const segments = analyzedItems.reduce((sum, item) => sum + (Number(item?.segments || 0) || 0), 0);
    const failures = Array.isArray(result.failures) ? result.failures.length : 0;
    const parts = [`新增登记 ${synced}`, `分析视频 ${analyzed}`, `智能片段 ${segments}`, `待复核 ${failures}`];
    elements.analysisStatus.textContent = `${actionName}完成：${parts.join(" · ")}`;
    updateAnalysisQueueJob(queueJobId, {
      status: failures ? "failed" : "done",
      completedAt: new Date().toISOString(),
      resultText: materialAnalysisResultText(result),
      error: failures ? `有 ${failures} 个素材需要复核` : "",
    });
    showToast(`${actionName}完成，素材库已刷新`);
  } catch (error) {
    elements.analysisStatus.textContent = `${actionName}失败：${error.message}`;
    updateAnalysisQueueJob(queueJobId, { status: "failed", completedAt: new Date().toISOString(), error: error.message });
    showToast(error.message);
  } finally {
    setAnalysisControlsBusy(false);
  }
}

function setJianyingDraftBusy(isBusy) {
  state.draftRunning = isBusy;
  if (elements.generateJianyingDraftBtn) {
    const hasCandidates = autoEditPoolStats(entries()).poolCandidates.length > 0;
    const hasManualClips = manualClipPayload(entries()).length > 0;
    elements.generateJianyingDraftBtn.disabled = isBusy || (!hasManualClips && !hasCandidates);
  }
  if (elements.generateProductFilmBtn) {
    const productBaseClips = buildProductFilmClips(productFilmScopeItems(entries()), productFilmTargetMs(), {
      style: productFilmStyle(),
      notePrefix: productFilmName(),
    });
    elements.generateProductFilmBtn.disabled = isBusy || state.roughCutRunning || !enabledProductFilmClips(productBaseClips).length;
  }
  if (elements.exportRoughCutBtn) {
    elements.exportRoughCutBtn.disabled = isBusy || state.roughCutRunning;
  }
}

function setRoughCutBusy(isBusy) {
  state.roughCutRunning = isBusy;
  if (elements.exportRoughCutBtn) {
    elements.exportRoughCutBtn.disabled = isBusy || state.draftRunning;
    elements.exportRoughCutBtn.textContent = isBusy ? "正在导出预剪" : "导出预剪素材";
  }
  if (elements.generateProductFilmBtn) {
    elements.generateProductFilmBtn.disabled = isBusy || state.draftRunning;
  }
  if (elements.generateJianyingDraftBtn) {
    elements.generateJianyingDraftBtn.disabled = isBusy || state.draftRunning;
  }
}

async function generateJianyingDraft() {
  if (state.draftRunning || state.roughCutRunning) return;
  const allEntries = entries();
  const stats = autoEditPoolStats(allEntries);
  const selectedClips = manualClipPayload(allEntries);
  if (!selectedClips.length && !stats.poolCandidates.length) {
    showToast("没有可生成草稿的素材，请先选择片段或运行 Skill 分析素材");
    return;
  }

  setJianyingDraftBusy(true);
  elements.jianyingDraftStatus.textContent = selectedClips.length
    ? "正在生成手动片段草稿：按你选择的顺序剪辑，并写入日语字幕和配音..."
    : "正在生成可编辑草稿：自动写日语脚本，并把日本配音写入独立音频轨...";
  try {
    const editSettings = draftEditSettings();
    const payload = await requestJson("/api/material-library/jianying-draft", {
      method: "POST",
      body: JSON.stringify({
        maxClips: selectedClips.length ? Math.min(30, selectedClips.length) : Math.min(8, stats.poolCandidates.length || stats.candidates.length),
        maxDuration: 60,
        targetRatio: "auto",
        selectedClips,
        ...editSettings,
        voiceoverText: elements.draftCopyInput?.value || "",
        copyLanguage: "ja",
        voiceProvider: elements.draftVoiceProviderSelect?.value || "edge",
        speaker: elements.draftSpeakerSelect?.value || "ja-JP-NanamiNeural",
        generateVoiceover: elements.draftVoiceoverToggle?.checked ?? true,
        elevenLabsApiKey: elements.elevenLabsApiKeyInput?.value || "",
        elevenLabsVoiceId: elements.elevenLabsVoiceIdInput?.value || "",
        elevenLabsModel: elements.elevenLabsModelInput?.value || "eleven_multilingual_v2",
      }),
    });
    state.obsidian = payload.obsidian || state.obsidian;
    const result = payload.result || {};
    const record = result.record || {};
    const copy = result.copy || {};
    const duration = record.totalDurationMs ? formatDurationMs(record.totalDurationMs) : "0s";
    const report = record.obsidianReportPath ? ` · ${record.obsidianReportPath}` : "";
    const textInfo = record.copySegmentCount ? ` · 字幕 ${record.copySegmentCount}` : "";
    const voiceInfo = record.voiceSegmentCount ? ` · 配音 ${record.voiceSegmentCount}` : "";
    const providerInfo = record.voiceProvider === "elevenlabs" ? " · ElevenLabs" : record.voiceProvider === "edge" ? " · 日语配音" : " · 剪映配音";
    const modeInfo = record.selectionMode === "manual" ? "手动片段" : "智能优选";
    const editInfo = record.editOptimized ? ` · 动态镜头 ${record.motionClipCount || 0} · 转场 ${record.transitionCount || 0}` : "";
    const warning = record.voiceFailureCount ? ` · ${record.voiceFailureCount} 条配音需重试` : "";
    elements.jianyingDraftStatus.textContent = `已生成日语可编辑剪映草稿：${record.draftName || "未命名"} · ${modeInfo} · ${record.clipCount || 0} 个片段 · ${duration}${textInfo}${voiceInfo}${providerInfo}${editInfo}${warning}${report}`;
    if (elements.draftCopyInput && !elements.draftCopyInput.value && copy.copyText) {
      elements.draftCopyInput.value = copy.copyText;
    }
    if (elements.elevenLabsApiKeyInput) elements.elevenLabsApiKeyInput.value = "";
    if (record.voiceProvider === "elevenlabs") loadRuntimeConfig();
    showToast("可编辑剪映草稿已生成");
  } catch (error) {
    elements.jianyingDraftStatus.textContent = `生成剪映草稿失败：${error.message}`;
    showToast(error.message);
  } finally {
    setJianyingDraftBusy(false);
  }
}

function productFilmTargetMs() {
  const seconds = Number(elements.productDurationSelect?.value || 30) || 30;
  return Math.max(5, Math.min(300, Math.round(seconds))) * 1000;
}

function productFilmStyle() {
  const value = String(elements.productStyleSelect?.value || "ecommerce");
  return PRODUCT_FILM_ROLE_PLANS[value] ? value : "ecommerce";
}

function draftEditSettings() {
  const editPace = String(elements.editPaceSelect?.value || "standard");
  const transitionStyle = String(elements.transitionStyleSelect?.value || "auto");
  const captionStyle = String(elements.captionStyleSelect?.value || "clean");
  return {
    editPace: ["standard", "fast", "calm"].includes(editPace) ? editPace : "standard",
    transitionStyle: ["auto", "dynamic", "soft", "minimal"].includes(transitionStyle) ? transitionStyle : "auto",
    captionStyle: ["clean", "sales", "none"].includes(captionStyle) ? captionStyle : "clean",
  };
}

function draftEditSettingsLabel() {
  const settings = draftEditSettings();
  const pace = elements.editPaceSelect?.selectedOptions?.[0]?.textContent || settings.editPace;
  const transition = elements.transitionStyleSelect?.selectedOptions?.[0]?.textContent || settings.transitionStyle;
  const caption = elements.captionStyleSelect?.selectedOptions?.[0]?.textContent || settings.captionStyle;
  return `${pace} · ${transition} · ${caption}`;
}

function productFilmScopeItems(allItems = entries(), filteredItems = null) {
  const scope = String(elements.productScopeSelect?.value || "current");
  if (scope === "all") return allItems;
  if (scope === "filtered") return Array.isArray(filteredItems) ? filteredItems : filterEntries(allItems);
  const active = activeBatch();
  return allItems.filter((item) => item.batchId === active.id);
}

function productFilmMaxClips(targetDurationMs) {
  const calculated = Math.max(4, Math.min(PRODUCT_FILM_MAX_CLIPS, Math.ceil((Number(targetDurationMs || 0) || 0) / 2500) + 2));
  const directorLimit = Math.round(Number(state.directorClipLimit || 0) || 0);
  return directorLimit > 0 ? Math.max(4, Math.min(calculated, directorLimit)) : calculated;
}

function productFilmRoleBonus(role, style) {
  const preferred = PRODUCT_FILM_ROLE_PLANS[style] || PRODUCT_FILM_ROLE_PLANS.ecommerce;
  const index = preferred.indexOf(role);
  if (index < 0) return role === "unassigned" ? -8 : 0;
  return Math.max(2, 10 - index);
}

function productFilmPacedDurationMs(role, durationMs, smartScore = 0) {
  const [minMs, maxMs] = PRODUCT_FILM_ROLE_DURATION_MS[role] || PRODUCT_FILM_ROLE_DURATION_MS.unassigned;
  const sourceMs = Math.max(0, Math.round(Number(durationMs || 0) || 0));
  if (sourceMs <= minMs) return sourceMs;
  const scoreBonus = Number(smartScore || 0) >= 82 ? 500 : Number(smartScore || 0) >= 72 ? 250 : 0;
  return Math.max(minMs, Math.min(sourceMs, maxMs + scoreBonus));
}

function productFilmCandidateRange(segment) {
  const startMs = Math.max(0, Math.round(Number(segment?.startMs || 0) || 0));
  const rawEndMs = Math.round(Number(segment?.endMs || 0) || 0);
  const durationMs = Math.round(Number(segment?.durationMs || 0) || 0);
  const endMs = rawEndMs > startMs ? rawEndMs : startMs + durationMs;
  return {
    startMs,
    endMs: Math.max(startMs, endMs),
    durationMs: Math.max(0, Math.max(startMs, endMs) - startMs),
  };
}

function buildProductFilmCandidates(items, style = productFilmStyle()) {
  return items
    .filter(isAutoEditCandidate)
    .flatMap((item) => {
      const itemSmart = smartEditSignal(item);
      return validSmartSegments(item, { minimumScore: PRODUCT_FILM_MIN_SCORE }).map((segment) => {
        const range = productFilmCandidateRange(segment);
        const role = normalizeEditRole(segment.role || item.editRole, "video");
        const segmentScore = Math.round(Number(segment.score || 0) || 0);
        const smartScore = Math.max(0, Math.min(100, Math.round(segmentScore * 0.62 + itemSmart.smartScore * 0.32 + productFilmRoleBonus(role, style))));
        const candidate = {
          item,
          segment,
          role,
          startMs: range.startMs,
          endMs: range.endMs,
          durationMs: range.durationMs,
          segmentScore,
          smartScore,
        };
        const secondaryRoles = inferProductCandidateSecondaryRoles(candidate);
        return {
          ...candidate,
          primaryRole: role,
          secondaryRoles,
          directionRoles: [role, ...secondaryRoles],
        };
      });
    })
    .filter((candidate) => candidate.durationMs >= MANUAL_CLIP_MIN_MS)
    .sort((a, b) => b.smartScore - a.smartScore || b.segmentScore - a.segmentScore || a.startMs - b.startMs);
}

function productCandidateKey(candidate) {
  const segmentId = String(candidate.segment?.id || "").trim();
  return `${candidate.item.url}|${segmentId || `${candidate.startMs}-${candidate.endMs}`}`;
}

function canUseProductCandidate(candidate, usedKeys, selectedRanges, selectedSourceCounts = null) {
  if (!candidate?.item?.url) return false;
  if (usedKeys.has(productCandidateKey(candidate))) return false;
  if (selectedSourceCounts && (selectedSourceCounts.get(candidate.item.url) || 0) >= PRODUCT_FILM_MAX_CLIPS_PER_SOURCE) return false;
  const ranges = selectedRanges.get(candidate.item.url) || [];
  return !ranges.some(([startMs, endMs]) => Math.min(candidate.endMs, endMs) - Math.max(candidate.startMs, startMs) > 250);
}

function markProductCandidate(candidate, usedKeys, selectedRanges, startMs, endMs, selectedSourceCounts = null) {
  usedKeys.add(productCandidateKey(candidate));
  const ranges = selectedRanges.get(candidate.item.url) || [];
  ranges.push([startMs, endMs]);
  selectedRanges.set(candidate.item.url, ranges);
  if (selectedSourceCounts) {
    selectedSourceCounts.set(candidate.item.url, (selectedSourceCounts.get(candidate.item.url) || 0) + 1);
  }
}

function productSellingPointSnippet() {
  const text = String(elements.productSellingPointsInput?.value || elements.draftCopyInput?.value || "")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return "";
  const first = text.split(/[。！？!?；;\n\r]/).map((part) => part.trim()).filter(Boolean)[0] || text;
  return first.slice(0, 72);
}

function productManualCopyText() {
  return String(elements.productSellingPointsInput?.value || elements.draftCopyInput?.value || "").trim();
}

function splitProductCopyText(text) {
  return String(text || "")
    .replace(/\r/g, "\n")
    .split(/[\n]+|(?<=[。.!！?？；;])\s+|(?<=[。.!！?？；;])/u)
    .map((part) => part.replace(/^[\s,，、]+|[\s,，、]+$/g, "").trim())
    .filter(Boolean)
    .slice(0, 48);
}

function inferCopyRole(line, index, total) {
  const text = String(line || "").toLowerCase();
  const has = (words) => words.some((word) => text.includes(word.toLowerCase()));
  const hasStrongDetail = has(["斜扣", "纽扣", "ボタン", "ウエスト", "ディテール", "面料", "素材", "腰头"]);
  const hasProofClaim = has(["显瘦", "遮肉", "修饰", "舒服", "舒适", "百搭", "不挑人", "腿型", "体型", "カバー", "細見え", "楽", "着回し", "きれいに見え", "スタイル", "脚", "すらっと", "長く"]);
  if (hasProofClaim && !hasStrongDetail) return "proof";
  if (has(["腰", "腰头", "斜扣", "扣", "纽扣", "面料", "细节", "特写", "口袋", "裤脚", "走线", "做工", "质感", "生地", "ボタン", "ウエスト", "裾", "ポケット", "ディテール", "素材"])) return "detail";
  if (has(["走", "行走", "走路", "转身", "动作", "垂感", "摆动", "坐下", "抬腿", "歩", "動", "落ち感", "揺れ", "ターン"])) return "motion";
  if (has(["显瘦", "遮肉", "修饰", "舒服", "舒适", "百搭", "不挑人", "腿型", "体型", "カバー", "細見え", "楽", "着回し", "きれいに見え"])) return "proof";
  if (has(["最后", "结尾", "同款", "详情", "商品页", "点击", "下单", "チェック", "気になる", "サイズ"])) return "ending";
  if (has(["上身", "试穿", "版型", "穿搭", "搭配", "轮廓", "着用", "シルエット", "コーデ", "穿く"])) return "try_on";
  if (has(["开头", "第一眼", "亮点", "注目", "まず", "一目", "一眼", "吸引"])) return "hook";
  if (index === 0) return "hook";
  if (index >= Math.max(0, total - 1)) return "ending";
  return "";
}

function copyRoleCompatible(copyRole, clipRole) {
  if (!copyRole) return true;
  if (copyRole === clipRole) return true;
  if (copyRole === "proof" && ["try_on", "motion"].includes(clipRole)) return true;
  if (copyRole === "try_on" && ["hook", "motion", "ending"].includes(clipRole)) return true;
  if (copyRole === "hook" && ["try_on", "motion"].includes(clipRole)) return true;
  if (copyRole === "ending" && ["try_on", "hook"].includes(clipRole)) return true;
  return false;
}

function rawProductCopyParts(manualText = productManualCopyText()) {
  const parts = splitProductCopyText(manualText);
  return parts.map((text, index) => ({
    text,
    index,
    role: inferCopyRole(text, index, parts.length),
    used: false,
  }));
}

function productCopyPacingProfile(targetDurationMs = productFilmTargetMs()) {
  const seconds = Math.max(5, Math.round(Number(targetDurationMs || 0) / 1000) || 15);
  if (seconds <= 16) return { seconds, maxLines: 5, totalChars: 92, lineChars: 23 };
  if (seconds <= 31) return { seconds, maxLines: 8, totalChars: 176, lineChars: 28 };
  return { seconds, maxLines: 11, totalChars: 260, lineChars: 32 };
}

function weightedCopyRole(part, style = productFilmStyle()) {
  const roleWeights = {
    hook: 900,
    try_on: 760,
    detail: style === "detail" ? 820 : 720,
    proof: 700,
    motion: style === "tryon" ? 740 : 660,
    ending: 620,
    transition: 360,
    "": 420,
  };
  const role = part?.role || "";
  let score = roleWeights[role] ?? 420;
  const text = String(part?.text || "");
  if (/主力|人気|一番|まず|注目|第一/.test(text)) score += 60;
  if (/斜め|ウエスト|ボタン|面料|素材|細部|ディテール/.test(text)) score += 45;
  if (/脚|スタイル|すっきり|長く|細見え|显瘦|遮肉/.test(text)) score += 45;
  if (/合わせ|トップス|コーデ|着回し|搭配/.test(text)) score += 30;
  score -= Math.max(0, Number(part?.index || 0)) * 3;
  return score;
}

function compactCopyTextForPacing(text, role = "", limit = 24) {
  const source = String(text || "").replace(/\s+/g, " ").trim();
  if (!source) return "";
  const has = (pattern) => pattern.test(source);
  const japanese = /[\u3040-\u30ff]/.test(source);
  let line = source;
  if (japanese) {
    if (role === "hook" && has(/主力|人気|一番|当店/)) line = "当店人気の一本です。";
    else if (role === "hook") line = "まずはシルエットをチェック。";
    else if (role === "detail" && has(/斜め|ウエスト|ボタン/)) line = "斜めウエストがポイント。";
    else if (role === "detail" && has(/ポケット/)) line = "ポケット付きで実用的。";
    else if (role === "detail") line = "細部まできれいに見せます。";
    else if (role === "proof" && has(/脚|長く|スタイル|すっきり/)) line = "脚をすっきり長く見せます。";
    else if (role === "proof") line = "体型をきれいにカバー。";
    else if (role === "motion") line = "動くたび落ち感がきれい。";
    else if (role === "try_on" && has(/トップス|合わせ|コーデ/)) line = "トップスとも合わせやすいです。";
    else if (role === "try_on") line = "着用感もすっきり自然。";
    else if (role === "ending") line = "気になる方はチェック。";
  } else {
    if (role === "hook" && has(/主力|爆款|热卖|人气|人気/)) line = "这是店里的主推款。";
    else if (role === "hook") line = "先看整体版型。";
    else if (role === "detail" && has(/斜扣|腰|扣|纽扣/)) line = "斜扣腰头是重点。";
    else if (role === "detail") line = "细节和面料看这里。";
    else if (role === "proof" && has(/显瘦|腿|遮肉|修饰/)) line = "腿型会显得更利落。";
    else if (role === "proof") line = "日常穿很修饰身形。";
    else if (role === "motion") line = "走动垂感会更明显。";
    else if (role === "try_on") line = "搭配上身很自然。";
    else if (role === "ending") line = "喜欢可以看同款。";
  }
  if (line.length <= limit) return line;
  const clauses = line.split(/[、，,。.!！?？；;]/).map((part) => part.trim()).filter(Boolean);
  const first = clauses.find((part) => part.length <= limit - 1) || clauses[0] || line;
  return `${first.slice(0, Math.max(8, limit - 1))}。`;
}

function normalizedProductCopyKey(text) {
  return String(text || "").replace(/[\s。.!！?？；;,，、]/g, "").toLowerCase();
}

function productCopyAlternativeLines(part) {
  const source = String(part?.originalText || part?.text || "").replace(/\s+/g, " ").trim();
  const role = part?.role || "";
  const japanese = /[\u3040-\u30ff]/.test(source);
  const alternatives = [];
  const add = (pattern, ja, zh) => {
    if (pattern.test(source)) alternatives.push(japanese ? ja : zh);
  };

  if (role === "detail") {
    add(/ダブルボタン|双扣|双排扣/i, "ダブルボタンがアクセント。", "双扣设计是重点。");
    add(/斜め|斜扣|不规则腰/i, "斜めウエストがポイント。", "斜扣腰头很有辨识度。");
    add(/ポケット|口袋/i, "ポケット付きで実用的。", "口袋设计兼顾实用性。");
    add(/素材|生地|デニム|面料|质感/i, "素材感もきれいです。", "面料质感清晰可见。");
    add(/裾|裤脚/i, "裾のラインもすっきり。", "裤脚线条干净利落。");
  } else if (role === "proof") {
    add(/脚.*長|すらっと|显腿长|腿长/i, "脚をすらっと長く見せます。", "腿部线条更显修长。");
    add(/細見え|スタイル|显瘦|修饰/i, "すっきり細見えします。", "上身效果更显利落。");
    add(/カバー|遮肉|体型/i, "腰まわりを自然にカバー。", "腰胯位置更自然遮肉。");
    add(/楽|快適|舒服|舒适/i, "楽な穿き心地も魅力。", "穿着舒适不拘束。");
  } else if (role === "try_on") {
    add(/トップス|合わせ|コーデ|搭配|百搭/i, "トップスとも合わせやすいです。", "日常上衣都很好搭配。");
    add(/シルエット|版型|轮廓/i, "着用シルエットもすっきり。", "上身版型干净利落。");
  } else if (role === "motion") {
    add(/落ち感|揺れ|垂感|走|歩|動/i, "動くたび落ち感がきれい。", "走动时垂感更加明显。");
  } else if (role === "hook") {
    add(/主力|人気|一番|主推|热卖/i, "当店人気の一本です。", "这是店里的主推款。");
    add(/シルエット|版型|第一眼|亮点/i, "まずはシルエットをチェック。", "第一眼先看整体版型。");
  } else if (role === "ending") {
    add(/チェック|商品|同款|详情|下单/i, "気になる方は商品をチェック。", "喜欢的话可以查看同款。");
  }
  return alternatives;
}

function compactOriginalProductCopyLine(text, limit = 24) {
  const source = String(text || "").replace(/\s+/g, " ").trim();
  if (!source) return "";
  if (source.length <= limit) return source;
  const clauses = source.split(/[、，,。.!！?？；;]/).map((part) => part.trim()).filter(Boolean);
  const fitting = clauses.find((part) => part.length >= 6 && part.length <= limit - 1);
  if (fitting) return `${fitting}。`;
  return `${source.slice(0, Math.max(8, limit - 1)).replace(/[、，,\s]+$/g, "")}。`;
}

function makeProductCopyLinesUnique(parts, limit = 24) {
  const used = new Set();
  const usedSources = new Set();
  return parts.flatMap((part) => {
    const sourceKey = normalizedProductCopyKey(part.originalText || part.text);
    if (sourceKey && usedSources.has(sourceKey)) return [];
    if (sourceKey) usedSources.add(sourceKey);
    const candidates = [
      part.text,
      ...productCopyAlternativeLines(part),
      compactOriginalProductCopyLine(part.originalText || part.text, limit),
    ]
      .map((line) => {
        const clean = String(line || "").replace(/\s+/g, " ").trim();
        return clean.length <= limit ? clean : compactOriginalProductCopyLine(clean, limit);
      })
      .filter(Boolean);
    const line = candidates.find((candidate) => {
      const key = normalizedProductCopyKey(candidate);
      return key && !used.has(key);
    });
    if (!line) return [];
    used.add(normalizedProductCopyKey(line));
    return [{ ...part, text: line }];
  });
}

function paceProductCopyParts(parts, options = {}) {
  const targetDurationMs = options.targetDurationMs || productFilmTargetMs();
  const profile = productCopyPacingProfile(targetDurationMs);
  const maxLines = Math.max(1, Math.min(Number(options.maxLines || profile.maxLines), profile.maxLines, parts.length || profile.maxLines));
  if (!parts.length) {
    return { parts: [], plan: { sourceCount: 0, plannedCount: 0, maxLines, compressed: false, estimatedSeconds: 0, seconds: profile.seconds } };
  }

  const roleLimits = { hook: 1, try_on: 2, detail: 1, proof: 1, motion: 1, ending: 1, transition: 1, "": 2 };
  const picked = [];
  const pickedIndexes = new Set();
  const roleCounts = {};
  const endingCandidate = parts.find((part) => part.role === "ending") || parts[parts.length - 1];
  const orderedCandidates = [...parts]
    .sort((a, b) => weightedCopyRole(b, options.style || productFilmStyle()) - weightedCopyRole(a, options.style || productFilmStyle()));

  const tryPick = (part, force = false) => {
    if (!part || pickedIndexes.has(part.index) || picked.length >= maxLines) return false;
    const role = part.role || "";
    const limit = roleLimits[role] ?? 1;
    if (!force && (roleCounts[role] || 0) >= limit) return false;
    picked.push(part);
    pickedIndexes.add(part.index);
    roleCounts[role] = (roleCounts[role] || 0) + 1;
    return true;
  };

  tryPick(parts[0], true);
  if (maxLines >= 4 && endingCandidate?.index !== parts[0]?.index) {
    tryPick(endingCandidate, true);
  }
  for (const part of orderedCandidates) {
    tryPick(part);
  }
  for (const part of parts) {
    tryPick(part, true);
  }

  let planned = picked
    .slice(0, maxLines)
    .sort((a, b) => a.index - b.index)
    .map((part, plannedIndex) => ({
      ...part,
      originalText: part.text,
      text: compactCopyTextForPacing(part.text, part.role, profile.lineChars),
      sourceIndex: part.index,
      index: plannedIndex,
      used: false,
    }));

  planned = makeProductCopyLinesUnique(planned, profile.lineChars);

  let totalChars = planned.reduce((sum, part) => sum + String(part.text || "").length, 0);
  if (totalChars > profile.totalChars) {
    planned = planned.map((part) => ({
      ...part,
      text: compactCopyTextForPacing(part.text, part.role, Math.max(14, profile.lineChars - 4)),
    }));
    planned = makeProductCopyLinesUnique(planned, Math.max(14, profile.lineChars - 4));
    totalChars = planned.reduce((sum, part) => sum + String(part.text || "").length, 0);
  }

  planned = planned.map((part, index) => ({ ...part, index }));

  const estimatedSeconds = Number((totalChars / 6.4).toFixed(1));
  return {
    parts: planned,
    plan: {
      sourceCount: parts.length,
      plannedCount: planned.length,
      maxLines,
      compressed: parts.length !== planned.length || planned.some((part) => part.originalText && part.originalText !== part.text),
      estimatedSeconds,
      seconds: profile.seconds,
      totalChars,
    },
  };
}

function autofitProductCopy() {
  if (!elements.productSellingPointsInput) return;
  const rawText = productManualCopyText();
  const rawParts = rawProductCopyParts(rawText);
  if (!rawParts.length) {
    showToast("先填写产品文案，再按时长压缩");
    return;
  }
  const paced = paceProductCopyParts(rawParts, {
    targetDurationMs: productFilmTargetMs(),
    style: productFilmStyle(),
  });
  const lines = paced.parts.map((part) => String(part.text || "").trim()).filter(Boolean);
  if (!lines.length) {
    showToast("当前文案没有可压缩内容");
    return;
  }
  elements.productSellingPointsInput.value = lines.join("\n");
  clearProductFilmCopyOverrides();
  state.productFilmCopyPlan = paced.plan;
  render();
  showToast(`已按 ${paced.plan.seconds || Math.round(productFilmTargetMs() / 1000)} 秒压缩 ${paced.plan.sourceCount}→${paced.plan.plannedCount} 句`);
}

function productCopyParts(manualText = productManualCopyText(), options = {}) {
  const raw = rawProductCopyParts(manualText);
  const paced = paceProductCopyParts(raw, options);
  state.productFilmCopyPlan = paced.plan;
  return paced.parts;
}

function candidateCopyEvidenceText(candidate) {
  const item = candidate?.item || {};
  const segment = candidate?.segment || {};
  const analysis = item.analysis && typeof item.analysis === "object" ? item.analysis : {};
  const secondMarks = Array.isArray(segment.secondMarks) ? segment.secondMarks : [];
  return [
    candidate?.role,
    item.name,
    item.sourcePath,
    item.sourceUrl,
    ...(Array.isArray(item.tags) ? item.tags : []),
    ...(Array.isArray(item.aiTags) ? item.aiTags : []),
    ...(Array.isArray(analysis.autoTags) ? analysis.autoTags : []),
    analysis.summary,
    ...(Array.isArray(analysis.suggestions) ? analysis.suggestions : []),
    analysis.adProfile?.contentSummary,
    ...(Array.isArray(analysis.adProfile?.productSignals) ? analysis.adProfile.productSignals : []),
    ...(Array.isArray(analysis.adProfile?.strengths) ? analysis.adProfile.strengths : []),
    ...(Array.isArray(analysis.adProfile?.risks) ? analysis.adProfile.risks : []),
    ...(Array.isArray(segment.tags) ? segment.tags : []),
    segment.adStageLabel,
    segment.contentDescription,
    segment.reason,
    ...(Array.isArray(segment.strengths) ? segment.strengths : []),
    ...(Array.isArray(segment.risks) ? segment.risks : []),
    segment.copyAngle,
    ...secondMarks.map((mark) => mark?.note || ""),
  ].filter(Boolean).join(" ").toLowerCase();
}

function inferProductCandidateSecondaryRoles(candidate) {
  const primaryRole = candidate?.role || "unassigned";
  const segment = candidate?.segment || {};
  const marks = Array.isArray(segment.secondMarks) ? segment.secondMarks : [];
  const evidence = [
    segment.contentDescription,
    segment.copyAngle,
    segment.adStage,
    segment.adStageLabel,
    ...(Array.isArray(segment.tags) ? segment.tags : []),
    ...(Array.isArray(segment.strengths) ? segment.strengths : []),
    ...(Array.isArray(segment.risks) ? segment.risks : []),
    ...marks.flatMap((mark) => [mark?.note, mark?.visualNote, mark?.cutAdvice, mark?.timelineZone]),
  ].filter(Boolean).join(" ").toLowerCase();
  const roles = [];
  const add = (role) => {
    if (role !== primaryRole && !roles.includes(role)) roles.push(role);
  };
  const hasAny = (terms) => terms.some((term) => evidence.includes(String(term).toLowerCase()));
  if (hasAny(["开头", "钩子", "第一眼", "hook", "opening", "注目"])) add("hook");
  if (hasAny(["上身", "试穿", "全身", "正面", "侧面", "背面", "着用", "シルエット", "try_on"])) add("try_on");
  if (hasAny(["细节镜头", "细节特写", "近景", "局部", "看清", "close-up", "ディテール", "クローズアップ"])) add("detail");
  if (hasAny(["走动", "走路", "行走", "转身", "摆动", "动作", "垂感", "歩", "ターン", "揺れ", "落ち感", "motion"])) add("motion");
  if (hasAny(["显瘦", "显腿长", "遮肉", "修饰", "舒适", "百搭", "证明", "細見え", "カバー", "着回し", "proof"])) add("proof");
  if (hasAny(["转场", "过渡", "切换", "节奏", "transition", "テンポ"])) add("transition");
  if (hasAny(["结尾", "收尾", "召回", "商品页", "点击", "下单", "cta", "ending", "チェック"])) add("ending");

  const maxVisualMotion = Math.max(0, ...marks.map((mark) => Number(mark?.visualMotion || 0) || 0));
  const maxMotionDelta = Math.max(0, ...marks.map((mark) => Number(mark?.motionDelta || 0) || 0));
  if (maxVisualMotion >= 14 || maxMotionDelta >= 0.18) add("motion");

  const totalMs = Number(candidate?.item?.technical?.durationMs || 0) || 0;
  if (candidate.startMs <= 2400 && candidate.smartScore >= 70) add("hook");
  if (totalMs && candidate.endMs >= Math.max(0, totalMs - 2800) && candidate.durationMs <= 5000 && candidate.smartScore >= 65) add("ending");
  if (candidate.durationMs <= 2200 && (maxVisualMotion >= 10 || maxMotionDelta >= 0.12)) add("transition");
  return roles;
}

function productCandidateRoles(candidate) {
  return [...new Set([candidate?.role || "unassigned", ...(candidate?.secondaryRoles || [])])];
}

function projectProductCandidateRole(candidate, role) {
  if (!candidate || !role || candidate.role === role) return candidate;
  if (!candidate.secondaryRoles?.includes(role)) return candidate;
  return {
    ...candidate,
    primaryRole: candidate.primaryRole || candidate.role,
    role,
    derivedRole: true,
  };
}

function copyCandidateKeywordScore(part, candidate) {
  const line = String(part?.text || "").toLowerCase();
  const evidence = candidateCopyEvidenceText(candidate);
  const termsByRole = {
    hook: ["第一眼", "开头", "亮点", "注目", "シルエット", "一目", "吸引"],
    try_on: ["上身", "试穿", "版型", "穿搭", "搭配", "轮廓", "着用", "シルエット", "コーデ"],
    detail: ["腰", "腰头", "斜扣", "扣", "纽扣", "面料", "细节", "特写", "口袋", "裤脚", "走线", "做工", "质感", "ボタン", "ウエスト", "裾", "ポケット", "素材"],
    motion: ["走", "行走", "转身", "动作", "垂感", "摆动", "坐下", "抬腿", "歩", "動", "落ち感", "揺れ", "ターン"],
    proof: ["显瘦", "遮肉", "修饰", "舒服", "舒适", "百搭", "不挑人", "腿型", "体型", "カバー", "細見え", "楽", "着回し"],
    transition: ["转场", "节奏", "切换", "テンポ"],
    ending: ["最后", "结尾", "同款", "详情", "商品页", "点击", "下单", "チェック", "サイズ"],
  };
  const terms = [...new Set([...(termsByRole[part?.role] || []), ...(PRODUCT_COPY_ROLE_KEYWORDS[part?.role] || [])])];
  return terms.reduce((score, term) => {
    const key = term.toLowerCase();
    if (!line.includes(key)) return score;
    return score + (evidence.includes(key) ? 8 : 2);
  }, 0);
}

function scoreProductCandidateForCopy(part, candidate) {
  const role = candidate?.role || "unassigned";
  const candidateRoles = productCandidateRoles(candidate);
  const smart = Number(candidate?.smartScore || 0) || 0;
  const segment = Number(candidate?.segmentScore || 0) || 0;
  let score = smart + segment * 0.25 + copyCandidateKeywordScore(part, candidate);
  if (part?.role) {
    if (role === part.role) score += 90;
    else if (candidateRoles.includes(part.role)) score += 72;
    else if (candidateRoles.some((candidateRole) => copyRoleCompatible(part.role, candidateRole))) score += 48;
    else return Number.NEGATIVE_INFINITY;
  } else if (role !== "unassigned") {
    score += 10;
  }
  return score;
}

function pickProductCandidateForCopy(part, candidates, usedKeys, selectedRanges, selectedSourceCounts = null) {
  const candidate = candidates
    .filter((candidate) => canUseProductCandidate(candidate, usedKeys, selectedRanges, selectedSourceCounts))
    .map((candidate) => ({ candidate, score: scoreProductCandidateForCopy(part, candidate) }))
    .filter((item) => Number.isFinite(item.score))
    .sort((a, b) => b.score - a.score || b.candidate.smartScore - a.candidate.smartScore || b.candidate.segmentScore - a.candidate.segmentScore)[0]?.candidate || null;
  return part?.role ? projectProductCandidateRole(candidate, part.role) : candidate;
}

function applyCopyPartToSelectedClip(clip, part) {
  if (!clip || !part) return;
  const role = clip.role || "unassigned";
  const matchType = part.role && role === part.role ? "role" : part.role && copyRoleCompatible(part.role, role) ? "compatible" : "neutral";
  const labels = {
    role: "按文案精准匹配镜头",
    compatible: "按文案匹配相近镜头",
    neutral: "按顺序承接自填文案",
  };
  clip.copyText = part.text.slice(0, 500);
  clip.copyMatch = {
    source: "manual",
    type: matchType,
    role: part.role || "",
    index: part.index,
    sourceIndex: part.sourceIndex ?? part.index,
    label: labels[matchType] || labels.neutral,
  };
  clip.note = `${clip.note || ""} · 文案第 ${Number(part.sourceIndex ?? part.index ?? 0) + 1} 句`.slice(0, 160);
}

function adaptCopyLinesToProductClips(clips, manualText = productManualCopyText()) {
  const copyParts = productCopyParts(manualText);
  if (!copyParts.length) return clips;
  return clips.map((clip) => {
    const role = clip.role || "unassigned";
    let match = copyParts.find((part) => !part.used && part.role && copyRoleCompatible(part.role, role));
    let matchType = "role";
    if (!match) {
      match = copyParts.find((part) => !part.used && !part.role);
      matchType = "neutral";
    }
    if (!match) {
      match = copyParts.find((part) => !part.used);
      matchType = "sequence";
    }
    if (!match) return clip;
    match.used = true;
    const label = matchType === "role" ? "按镜头匹配自填文案" : matchType === "neutral" ? "使用自填文案" : "顺序补入自填文案";
    return {
      ...clip,
      copyText: match.text.slice(0, 500),
      copyMatch: {
        source: "manual",
        type: matchType,
        role: match.role || "",
        index: match.index,
        sourceIndex: match.sourceIndex ?? match.index,
        label,
      },
    };
  });
}

function productClipIsVisualOnly(clip) {
  const markedVisual = clip?.copyMatch?.type === "visual" || clip?.copyMatch?.source === "broll";
  return markedVisual && !String(clip?.copyText || "").trim();
}

function markProductClipAsVisualOnly(clip) {
  if (!clip || clip.copyMatch?.source === "manual") return clip;
  const aiSuggestedCopy = String(clip.aiSuggestedCopy || clip.copyText || "").trim();
  return {
    ...clip,
    aiSuggestedCopy,
    copyText: "",
    copyMatch: {
      source: "broll",
      type: "visual",
      role: clip.role || "",
      label: "纯画面补镜，不重复字幕和配音",
    },
  };
}

function productClipCopyLine(candidate, index, productName) {
  const product = String(productName || productFilmName()).trim() || "このアイテム";
  const role = candidate.role || "unassigned";
  const sellingPoint = productSellingPointSnippet();
  const point = sellingPoint ? `注目ポイントは、${sellingPoint}。` : "";
  const templates = {
    hook: [
      "まずは全体シルエットをチェック。",
      "第一印象からすっきり見える一本です。",
      "穿いた瞬間のラインに注目です。",
    ],
    try_on: [
      "脚のラインが自然に見えます。",
      "着用シルエットもすっきり。",
      "トップスとも合わせやすいです。",
      "普段のコーデに取り入れやすい一本です。",
    ],
    detail: [
      "ウエストまわりのデザインに注目。",
      "ボタン位置がコーデのアクセントに。",
      "細部のラインもきれいに仕上がっています。",
      "近くで見るとデザインの違いが分かります。",
    ],
    motion: [
      "歩くと落ち感がきれい。",
      "動いたときのシルエットも自然です。",
      "揺れ感がコーデを軽やかに見せます。",
    ],
    transition: [
      "ここで角度を変えて見てみましょう。",
      "次は違うシルエットをチェック。",
      "テンポを変えて細部を見ていきます。",
    ],
    proof: [
      "腰まわりを自然にすっきり見せます。",
      "脚をまっすぐ長く見せやすいラインです。",
      "体型を拾いにくいシルエットです。",
    ],
    ending: [
      "気になる方は商品ページをチェック。",
      "毎日のコーデに取り入れてみてください。",
    ],
    unassigned: [
      `${product}の雰囲気を自然に見せます。`,
      `${product}のシルエットを別角度からチェック。`,
    ],
  };
  const variants = templates[role] || templates.unassigned;
  const line = variants[Math.abs(Number(index || 0)) % variants.length];
  if (index === 0 && point) return compactCopyTextForPacing(`${line} ${point}`, role, 28);
  return line.length <= 28 ? line : compactOriginalProductCopyLine(line, 28);
}

function productClipAiSuggestion(candidate, index, productName) {
  const role = candidate?.role || "unassigned";
  const roleLabel = optionLabel(EDIT_ROLE_OPTIONS, role);
  const evidence = candidateCopyEvidenceText(candidate);
  const script = productManualCopyText().toLowerCase();
  const suggestions = [];
  const includesAny = (text, terms) => terms.some((term) => text.includes(String(term).toLowerCase()));
  const addSuggestion = ({ roles, evidenceTerms = [], scriptTerms = [], text, signal, allowScriptOnly = false }) => {
    if (!roles.includes(role)) return;
    const evidenceMatched = includesAny(evidence, evidenceTerms);
    const scriptMatched = includesAny(script, scriptTerms.length ? scriptTerms : evidenceTerms);
    if (!evidenceMatched && !(allowScriptOnly && scriptMatched)) return;
    const reasonParts = [roleLabel];
    if (evidenceMatched && signal) reasonParts.push(signal);
    if (scriptMatched) reasonParts.push("脚本相关卖点");
    suggestions.push({ text, reason: `依据：${reasonParts.join(" · ")}` });
  };

  addSuggestion({
    roles: ["hook", "detail"],
    evidenceTerms: ["斜扣", "斜め", "不规则腰", "アシンメトリー"],
    scriptTerms: ["斜扣", "斜め", "不规则"],
    text: role === "hook" ? "一目で差がつく斜めウエスト。" : "斜めウエストがデザインのポイント。",
    signal: "斜扣腰头",
  });
  addSuggestion({
    roles: ["detail"],
    evidenceTerms: ["ダブルボタン", "双扣", "双排扣", "double button"],
    scriptTerms: ["ダブルボタン", "双扣", "双排扣"],
    text: "ダブルボタンがコーデのアクセント。",
    signal: "双扣细节",
  });
  addSuggestion({
    roles: ["detail"],
    evidenceTerms: ["ポケット", "口袋"],
    scriptTerms: ["ポケット", "口袋", "実用"],
    text: "ポケット付きで実用性もあります。",
    signal: "口袋细节",
  });
  addSuggestion({
    roles: ["detail"],
    evidenceTerms: ["デニム", "牛仔", "素材", "生地", "面料"],
    scriptTerms: ["デニム", "牛仔", "素材", "面料", "質感", "质感"],
    text: "デニムの素材感もきれいに見えます。",
    signal: "面料质感",
  });
  addSuggestion({
    roles: ["hook", "try_on", "proof"],
    evidenceTerms: ["ワイド", "阔腿", "wide leg"],
    scriptTerms: ["ワイド", "阔腿", "ゆったり"],
    text: role === "hook" ? "まずはワイドシルエットに注目。" : "ゆったりしたワイドラインが魅力です。",
    signal: "阔腿版型",
  });
  addSuggestion({
    roles: ["try_on", "proof"],
    evidenceTerms: ["全身", "上身", "着用", "シルエット", "try_on"],
    scriptTerms: ["脚", "腿长", "显腿长", "すらっと", "長く"],
    text: "脚をすらっと長く見せやすいラインです。",
    signal: "全身轮廓",
    allowScriptOnly: true,
  });
  addSuggestion({
    roles: ["try_on", "proof"],
    evidenceTerms: ["上身", "着用", "正面", "侧面", "シルエット", "try_on"],
    scriptTerms: ["显瘦", "細見え", "すっきり", "修饰", "スタイル"],
    text: "すっきり細見えするシルエットです。",
    signal: "上身展示",
    allowScriptOnly: true,
  });
  addSuggestion({
    roles: ["try_on", "proof"],
    evidenceTerms: ["上身", "着用", "体型", "腰", "ヒップ", "try_on"],
    scriptTerms: ["遮肉", "カバー", "体型", "腰", "お腹", "ヒップ"],
    text: "腰まわりを自然にカバーしてくれます。",
    signal: "腰胯轮廓",
    allowScriptOnly: true,
  });
  addSuggestion({
    roles: ["try_on", "proof"],
    evidenceTerms: ["コーデ", "搭配", "トップス", "着回し"],
    scriptTerms: ["コーデ", "搭配", "トップス", "百搭", "着回し"],
    text: "トップスを選ばず着回しやすいです。",
    signal: "穿搭展示",
    allowScriptOnly: true,
  });
  addSuggestion({
    roles: ["motion"],
    evidenceTerms: ["歩", "走", "ターン", "转身", "揺れ", "垂感", "落ち感", "動"],
    scriptTerms: ["歩", "走", "ターン", "转身", "垂感", "落ち感"],
    text: "動くたびに落ち感がきれいに出ます。",
    signal: "走动垂感",
  });
  addSuggestion({
    roles: ["ending"],
    evidenceTerms: ["全身", "正面", "着用", "ending", "结尾"],
    scriptTerms: ["チェック", "商品", "同款", "详情", "気になる"],
    text: "気になる方は商品ページをチェック。",
    signal: "完整收尾画面",
    allowScriptOnly: true,
  });

  const uniqueSuggestions = suggestions.filter((suggestion, suggestionIndex, all) => (
    all.findIndex((item) => normalizedProductCopyKey(item.text) === normalizedProductCopyKey(suggestion.text)) === suggestionIndex
  ));
  if (uniqueSuggestions.length) {
    return uniqueSuggestions[Math.abs(Number(index || 0)) % uniqueSuggestions.length];
  }

  const fallbackText = productClipCopyLine(candidate, index, productName);
  const segment = candidate?.segment || {};
  const evidenceLabels = [
    segment.copyAngle,
    ...(Array.isArray(segment.tags) ? segment.tags : []),
    ...(Array.isArray(candidate?.item?.aiTags) ? candidate.item.aiTags : []),
  ].filter(Boolean).slice(0, 2);
  return {
    text: fallbackText,
    reason: `依据：${[roleLabel, ...evidenceLabels].filter(Boolean).join(" · ") || "镜头用途"}`,
  };
}

function productClipFromCandidate(candidate, index, startMs, endMs, notePrefix) {
  const item = candidate.item;
  const segment = candidate.segment;
  const aiSuggestion = productClipAiSuggestion(candidate, index, notePrefix);
  const copyText = aiSuggestion.text;
  return {
    order: index,
    url: item.url,
    name: item.name || materialDisplayName(item.url),
    startMs,
    endMs,
    durationMs: Math.max(0, endMs - startMs),
    clipUnit: "segment",
    segmentId: String(segment.id || ""),
    segmentScore: candidate.segmentScore,
    role: candidate.role || item.editRole,
    primaryRole: candidate.primaryRole || candidate.role || item.editRole,
    secondaryRoles: Array.isArray(candidate.secondaryRoles) ? candidate.secondaryRoles : [],
    derivedRole: Boolean(candidate.derivedRole),
    secondMarks: Array.isArray(segment.secondMarks) ? segment.secondMarks : [],
    segmentTags: Array.isArray(segment.tags) ? segment.tags : [],
    copyText,
    aiSuggestedCopy: copyText,
    aiSuggestionReason: aiSuggestion.reason,
    note: `${notePrefix} · ${Math.round(candidate.smartScore || 0)}分 · ${optionLabel(EDIT_ROLE_OPTIONS, candidate.role)}${candidate.derivedRole ? "（复合分镜派生）" : ""}`.slice(0, 160),
  };
}

function productFilmClipKey(clip) {
  return [
    clip?.url || "",
    clip?.segmentId || "",
    Math.round(Number(clip?.startMs || 0) || 0),
    Math.round(Number(clip?.endMs || 0) || 0),
  ].join("|");
}

function productFilmEditedClips(clips) {
  const liveKeys = new Set(clips.map(productFilmClipKey));
  Object.keys(state.productFilmEdits || {}).forEach((key) => {
    if (!liveKeys.has(key)) delete state.productFilmEdits[key];
  });
  return clips.map((clip) => {
    const key = productFilmClipKey(clip);
    const edit = state.productFilmEdits[key] || {};
    const replacement = edit.replacement && typeof edit.replacement === "object" ? edit.replacement : null;
    const sourceClip = replacement ? { ...clip, ...replacement, order: clip.order } : clip;
    return {
      ...sourceClip,
      productClipKey: key,
      replacementActive: Boolean(replacement),
      enabled: edit.enabled !== false,
      copyText: edit.copyText !== undefined ? String(edit.copyText || "").slice(0, 500) : sourceClip.copyText,
      copyMatch: edit.copyMatch && typeof edit.copyMatch === "object" ? edit.copyMatch : sourceClip.copyMatch,
    };
  });
}

function enabledProductFilmClips(clips) {
  return productFilmEditedClips(clips)
    .filter((clip) => clip.enabled !== false)
    .map((clip, index) => ({ ...clip, order: index }));
}

function setProductFilmEdit(key, patch = {}) {
  if (!key) return;
  state.productFilmEdits[key] = {
    ...(state.productFilmEdits[key] || {}),
    ...patch,
  };
  scheduleProductDraftSave();
}

function productDraftSnapshot() {
  return {
    version: 2,
    updatedAt: new Date().toISOString(),
    activeBatchId: activeBatch()?.id || "",
    productName: elements.productNameInput?.value || "",
    duration: elements.productDurationSelect?.value || "30",
    scope: elements.productScopeSelect?.value || "current",
    style: elements.productStyleSelect?.value || "ecommerce",
    pace: elements.editPaceSelect?.value || "standard",
    transition: elements.transitionStyleSelect?.value || "auto",
    caption: elements.captionStyleSelect?.value || "clean",
    script: elements.productSellingPointsInput?.value || "",
    voiceover: elements.draftCopyInput?.value || "",
    voiceProvider: elements.draftVoiceProviderSelect?.value || "edge",
    speaker: elements.draftSpeakerSelect?.value || "ja-JP-NanamiNeural",
    voiceoverEnabled: Boolean(elements.draftVoiceoverToggle?.checked),
    edits: state.productFilmEdits || {},
    precutSignature: state.productPrecutSignature || "",
  };
}

function saveProductDraft() {
  try {
    const draft = productDraftSnapshot();
    window.localStorage.setItem(MATERIAL_PRODUCT_DRAFT_KEY, JSON.stringify(draft));
    if (elements.productDraftSaveState) elements.productDraftSaveState.textContent = `已自动保存 ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  } catch {
    if (elements.productDraftSaveState) elements.productDraftSaveState.textContent = "自动保存失败";
  }
}

function scheduleProductDraftSave() {
  window.clearTimeout(state.productDraftSaveTimer);
  if (elements.productDraftSaveState) elements.productDraftSaveState.textContent = "正在保存...";
  state.productDraftSaveTimer = window.setTimeout(saveProductDraft, 260);
}

function restoreProductDraft({ silent = false } = {}) {
  try {
    const draft = JSON.parse(window.localStorage.getItem(MATERIAL_PRODUCT_DRAFT_KEY) || "null");
    if (!draft || typeof draft !== "object") {
      if (!silent) showToast("没有可恢复的成片草稿");
      return false;
    }
    const setValue = (element, value, allowed = null) => {
      if (!element || value === undefined || value === null) return;
      const clean = String(value);
      if (!allowed || allowed.includes(clean)) element.value = clean;
    };
    setValue(elements.productNameInput, draft.productName);
    setValue(elements.productDurationSelect, draft.duration, ["15", "30", "45", "60"]);
    setValue(elements.productScopeSelect, draft.scope, ["current", "filtered", "all"]);
    setValue(elements.productStyleSelect, draft.style, ["ecommerce", "tryon", "detail"]);
    setValue(elements.editPaceSelect, draft.pace, ["standard", "fast", "calm"]);
    setValue(elements.transitionStyleSelect, draft.transition, ["auto", "dynamic", "soft", "minimal"]);
    setValue(elements.captionStyleSelect, draft.caption, ["clean", "sales", "none"]);
    setValue(elements.productSellingPointsInput, draft.script);
    setValue(elements.draftCopyInput, draft.voiceover);
    setValue(elements.draftVoiceProviderSelect, draft.voiceProvider, ["edge", "elevenlabs"]);
    setValue(elements.draftSpeakerSelect, draft.speaker);
    if (elements.draftVoiceoverToggle && draft.voiceoverEnabled !== undefined) elements.draftVoiceoverToggle.checked = Boolean(draft.voiceoverEnabled);
    state.productFilmEdits = draft.edits && typeof draft.edits === "object" ? draft.edits : {};
    state.productPrecutSignature = String(draft.precutSignature || "");
    if (elements.productDraftSaveState) elements.productDraftSaveState.textContent = `已恢复 ${draft.updatedAt ? formatDate(draft.updatedAt) : "上次草稿"}`;
    toggleVoiceProviderFields();
    if (!silent) {
      render();
      showToast("已恢复上次成片草稿");
    }
    return true;
  } catch {
    if (!silent) showToast("草稿内容损坏，无法恢复");
    return false;
  }
}

function clearProductDraft() {
  window.localStorage.removeItem(MATERIAL_PRODUCT_DRAFT_KEY);
  state.productFilmEdits = {};
  state.productPrecutSignature = "";
  elements.productSellingPointsInput.value = "";
  elements.draftCopyInput.value = "";
  if (elements.productDraftSaveState) elements.productDraftSaveState.textContent = "草稿已清空";
  render();
  showToast("成片草稿已清空");
}

function productFilmEditForKey(key) {
  if (!key) return {};
  return state.productFilmEdits[key] || {};
}

function clearProductFilmReplacement(key) {
  if (!key || !state.productFilmEdits[key]) return;
  delete state.productFilmEdits[key].replacement;
  render();
}

function replacementClipFromCandidate(candidate, slotClip, notePrefix = productFilmName()) {
  if (!candidate?.item || !candidate?.segment || !slotClip) return null;
  const range = productFilmCandidateRange(candidate.segment);
  const durationMs = productFilmPacedDurationMs(candidate.role, range.durationMs, candidate.smartScore);
  const startMs = range.startMs;
  const endMs = startMs + Math.max(MANUAL_CLIP_MIN_MS, Math.min(range.durationMs, durationMs || range.durationMs));
  const clip = productClipFromCandidate(candidate, slotClip.order || 0, startMs, endMs, notePrefix);
  return {
    ...clip,
    copyMatch: slotClip.copyMatch || clip.copyMatch,
    copyText: slotClip.copyText || clip.copyText,
    note: `${notePrefix} · 替换候选 · ${Math.round(candidate.smartScore || 0)}分 · ${optionLabel(EDIT_ROLE_OPTIONS, candidate.role)}`.slice(0, 160),
  };
}

function applyProductFilmReplacement(slotKey, candidate, slotClip) {
  const replacement = replacementClipFromCandidate(candidate, slotClip);
  if (!replacement) return;
  const edit = productFilmEditForKey(slotKey);
  setProductFilmEdit(slotKey, {
    ...edit,
    replacement,
    copyText: edit.copyText !== undefined ? edit.copyText : slotClip.copyText,
  });
  render();
}

function clearProductFilmCopyOverrides() {
  Object.keys(state.productFilmEdits || {}).forEach((key) => {
    if (state.productFilmEdits[key] && Object.prototype.hasOwnProperty.call(state.productFilmEdits[key], "copyText")) {
      delete state.productFilmEdits[key].copyText;
    }
  });
}

function addProductCandidateClip(selected, candidate, context) {
  const { targetDurationMs, usedKeys, selectedRanges, selectedSourceCounts, notePrefix } = context;
  if (!canUseProductCandidate(candidate, usedKeys, selectedRanges, selectedSourceCounts)) return false;
  const currentDuration = selected.reduce((sum, clip) => sum + clip.durationMs, 0);
  let startMs = candidate.startMs;
  let endMs = candidate.endMs;
  let durationMs = candidate.durationMs;
  const pacedDurationMs = productFilmPacedDurationMs(candidate.role, durationMs, candidate.smartScore);
  if (pacedDurationMs >= MANUAL_CLIP_MIN_MS && pacedDurationMs < durationMs) {
    durationMs = pacedDurationMs;
    endMs = startMs + durationMs;
  }
  const remainingMs = targetDurationMs - currentDuration;
  if (remainingMs <= 0) return false;
  if (durationMs > remainingMs) {
    if (remainingMs < MANUAL_CLIP_MIN_MS) return false;
    durationMs = remainingMs;
    endMs = startMs + durationMs;
  }
  selected.push(productClipFromCandidate(candidate, selected.length, startMs, endMs, notePrefix));
  markProductCandidate(candidate, usedKeys, selectedRanges, startMs, endMs, selectedSourceCounts);
  return true;
}

function buildProductFilmClips(items, targetDurationMs = productFilmTargetMs(), options = {}) {
  const style = options.style || productFilmStyle();
  const candidates = buildProductFilmCandidates(items, style);
  const selected = [];
  const usedKeys = new Set();
  const selectedRanges = new Map();
  const selectedSourceCounts = new Map();
  const maxClips = productFilmMaxClips(targetDurationMs);
  const notePrefix = options.notePrefix || "产品成片";
  const context = { targetDurationMs, usedKeys, selectedRanges, selectedSourceCounts, notePrefix };
  const plan = PRODUCT_FILM_ROLE_PLANS[style] || PRODUCT_FILM_ROLE_PLANS.ecommerce;
  const pickByRole = (role) => {
    const direct = candidates.find((candidate) => candidate.role === role && canUseProductCandidate(candidate, usedKeys, selectedRanges, selectedSourceCounts));
    if (direct) return direct;
    const derived = candidates.find((candidate) => candidate.secondaryRoles?.includes(role) && canUseProductCandidate(candidate, usedKeys, selectedRanges, selectedSourceCounts));
    return projectProductCandidateRole(derived, role);
  };
  const totalDuration = () => selected.reduce((sum, clip) => sum + clip.durationMs, 0);
  const copyParts = productCopyParts(options.manualText || productManualCopyText(), {
    targetDurationMs,
    maxLines: maxClips,
    style,
  });
  const copyMisses = [];

  if (copyParts.length) {
    for (const part of copyParts) {
      if (selected.length >= maxClips || totalDuration() >= targetDurationMs) {
        copyMisses.push({ ...part, reason: "目标时长或片段数量已满" });
        continue;
      }
      const candidate = pickProductCandidateForCopy(part, candidates, usedKeys, selectedRanges, selectedSourceCounts);
      if (!candidate) {
        copyMisses.push({
          ...part,
          reason: part.role ? `缺少${optionLabel(EDIT_ROLE_OPTIONS, part.role)}素材` : "没有可用高分片段",
        });
        continue;
      }
      const beforeCount = selected.length;
      if (addProductCandidateClip(selected, candidate, context) && selected.length > beforeCount) {
        applyCopyPartToSelectedClip(selected[selected.length - 1], part);
        part.used = true;
      } else {
        copyMisses.push({ ...part, reason: "片段时长不足或与已选片段重叠" });
      }
    }
  }

  let heldEndingClip = null;
  if (copyParts.length && selected.length > 1) {
    const lastClip = selected[selected.length - 1];
    if (lastClip?.copyMatch?.source === "manual" && (lastClip.copyMatch.role === "ending" || lastClip.role === "ending")) {
      heldEndingClip = selected.pop();
    }
  }

  const fillTargetDurationMs = heldEndingClip ? Math.max(0, targetDurationMs - heldEndingClip.durationMs) : targetDurationMs;
  const fillContext = heldEndingClip ? { ...context, targetDurationMs: fillTargetDurationMs } : context;
  const beforeEndingTarget = Math.max(MANUAL_CLIP_MIN_MS * 2, fillTargetDurationMs - 4500);
  if (!copyParts.length) {
    const hook = pickByRole("hook");
    if (hook) addProductCandidateClip(selected, hook, context);

    for (const role of plan.filter((role) => !["hook", "ending"].includes(role))) {
      if (selected.length >= maxClips || totalDuration() >= beforeEndingTarget) break;
      const candidate = pickByRole(role);
      if (candidate) addProductCandidateClip(selected, candidate, fillContext);
    }
  }

  for (const candidate of candidates) {
    if (selected.length >= maxClips || totalDuration() >= beforeEndingTarget) break;
    addProductCandidateClip(selected, candidate, fillContext);
  }

  if (heldEndingClip && selected.length < maxClips) {
    selected.push(heldEndingClip);
  } else if (!heldEndingClip) {
    const ending = pickByRole("ending");
    if (ending && selected.length < maxClips && totalDuration() < targetDurationMs) {
      addProductCandidateClip(selected, ending, context);
    }
  }

  if (!heldEndingClip) {
    for (const candidate of candidates) {
      if (selected.length >= maxClips || totalDuration() >= targetDurationMs) break;
      addProductCandidateClip(selected, candidate, context);
    }
  }

  const ordered = selected.map((clip, index) => ({ ...clip, order: index }));
  state.productFilmCopyMisses = copyMisses;
  return copyParts.length ? ordered.map(markProductClipAsVisualOnly) : adaptCopyLinesToProductClips(ordered);
}

function productFilmName() {
  return String(elements.productNameInput?.value || activeBatch()?.name || "").trim().slice(0, 80) || "AI剪辑成片";
}

function productFilmDraftName() {
  const clean = productFilmName().replace(/[<>:"/\\|?*\x00-\x1f]+/g, "_").replace(/\s+/g, " ").trim().slice(0, 46);
  const stamp = new Date().toISOString().slice(5, 16).replace(/[-T:]/g, "");
  return `产品成片_${clean || "未命名"}_${stamp}`;
}

function productFilmCopy(items, clips) {
  const manualText = productManualCopyText();
  if (manualText) {
    const clipCopy = clips.map((clip) => String(clip.copyText || "").trim()).filter(Boolean).join(" ");
    return (clipCopy || manualText).slice(0, 4000);
  }
  const name = productFilmName();
  const tags = [...new Set(items.flatMap((item) => [...(item.tags || []), ...(item.aiTags || [])]))].slice(0, 4);
  const roleNames = [...new Set(clips.map((clip) => optionLabel(EDIT_ROLE_OPTIONS, clip.role)).filter(Boolean))].slice(0, 4);
  const tagLine = tags.length ? `キーワードは、${tags.join("、")}。` : "";
  const roleLine = roleNames.length ? `映像は、${roleNames.join("、")}を中心に構成しています。` : "";
  return [
    `今回紹介するのは、${name}。`,
    tagLine,
    roleLine,
    "最初にシルエットを見せて、次に動きと細部をテンポよくつなぎます。",
    "気になる方は、同じアイテムをチェックしてみてください。",
  ].filter(Boolean).join(" ");
}

async function generateProductFilmDraft() {
  if (state.draftRunning || state.roughCutRunning) return;
  const allEntries = entries();
  const filtered = filterEntries(allEntries);
  const scopedItems = productFilmScopeItems(allEntries, filtered);
  const targetDurationMs = productFilmTargetMs();
  const health = productFilmHealth(scopedItems, productFilmStyle());
  if (!health.canGenerate) {
    const message = `${health.status}。请先补充素材、调整文案或切换素材范围。`;
    if (elements.productFilmStatus) elements.productFilmStatus.textContent = message;
    showToast(message);
    return;
  }
  const baseClips = buildProductFilmClips(scopedItems, targetDurationMs, {
    style: productFilmStyle(),
    notePrefix: productFilmName(),
  });
  const selectedClips = enabledProductFilmClips(baseClips);
  if (!selectedClips.length) {
    showToast("没有启用的成片片段，请先勾选片段或切换素材范围");
    if (elements.productFilmStatus) elements.productFilmStatus.textContent = "没有启用的成片片段。";
    return;
  }

  setJianyingDraftBusy(true);
  if (elements.productFilmStatus) {
    elements.productFilmStatus.textContent = `正在生成 ${productFilmName()}：${selectedClips.length} 个智能片段，目标 ${formatDurationMs(targetDurationMs)}。`;
  }
  if (elements.jianyingDraftStatus) {
    elements.jianyingDraftStatus.textContent = "正在按产品自动选片并生成可编辑剪映草稿...";
  }
  try {
    const editSettings = draftEditSettings();
    const payload = await requestJson("/api/material-library/jianying-draft", {
      method: "POST",
      body: JSON.stringify({
        draftName: productFilmDraftName(),
        maxClips: Math.min(30, selectedClips.length),
        maxDuration: Math.max(5, Math.round(targetDurationMs / 1000)),
        targetRatio: "auto",
        selectedClips,
        ...editSettings,
        voiceoverText: productFilmCopy(scopedItems, selectedClips),
        copyLanguage: "ja",
        voiceProvider: elements.draftVoiceProviderSelect?.value || "edge",
        speaker: elements.draftSpeakerSelect?.value || "ja-JP-NanamiNeural",
        generateVoiceover: elements.draftVoiceoverToggle?.checked ?? true,
        elevenLabsApiKey: elements.elevenLabsApiKeyInput?.value || "",
        elevenLabsVoiceId: elements.elevenLabsVoiceIdInput?.value || "",
        elevenLabsModel: elements.elevenLabsModelInput?.value || "eleven_multilingual_v2",
      }),
    });
    state.obsidian = payload.obsidian || state.obsidian;
    const result = payload.result || {};
    const record = result.record || {};
    const copy = result.copy || {};
    const duration = record.totalDurationMs ? formatDurationMs(record.totalDurationMs) : "0s";
    const report = record.obsidianReportPath ? ` · ${record.obsidianReportPath}` : "";
    const voiceInfo = record.voiceSegmentCount ? ` · 配音 ${record.voiceSegmentCount}` : "";
    const editInfo = record.editOptimized ? ` · 动态镜头 ${record.motionClipCount || 0} · 转场 ${record.transitionCount || 0}` : "";
    const warning = record.voiceFailureCount ? ` · ${record.voiceFailureCount} 条配音需重试` : "";
    if (elements.productFilmStatus) {
      elements.productFilmStatus.textContent = `已生成产品成片草稿：${record.draftName || "未命名"} · ${record.clipCount || 0} 个片段 · ${duration}${voiceInfo}${editInfo}${warning}${report}`;
    }
    if (elements.jianyingDraftStatus) {
      elements.jianyingDraftStatus.textContent = `已生成可编辑剪映草稿：${record.draftName || "未命名"} · 产品成片 · ${record.clipCount || 0} 个片段 · ${duration}${voiceInfo}${editInfo}${warning}${report}`;
    }
    if (elements.draftCopyInput && !elements.draftCopyInput.value && copy.copyText) {
      elements.draftCopyInput.value = copy.copyText;
    }
    if (elements.elevenLabsApiKeyInput) elements.elevenLabsApiKeyInput.value = "";
    if (record.voiceProvider === "elevenlabs") loadRuntimeConfig();
    showToast("产品成片剪映草稿已生成");
  } catch (error) {
    if (elements.productFilmStatus) elements.productFilmStatus.textContent = `产品成片失败：${error.message}`;
    if (elements.jianyingDraftStatus) elements.jianyingDraftStatus.textContent = `生成剪映草稿失败：${error.message}`;
    showToast(error.message);
  } finally {
    setJianyingDraftBusy(false);
  }
}

function productRoughCutName() {
  const clean = productFilmName().replace(/[<>:"/\\|?*\x00-\x1f]+/g, "_").replace(/\s+/g, " ").trim().slice(0, 56);
  return `预剪素材_${clean || "未命名"}`;
}

function renderRoughCutResult(record = state.roughCutRecord) {
  if (!elements.roughCutResult) return;
  if (!record?.videoUrl) {
    elements.roughCutResult.hidden = true;
    elements.roughCutResult.innerHTML = "";
    return;
  }
  const videoUrl = playableMaterialUrl(record.videoUrl);
  const downloadUrl = playableMaterialUrl(record.downloadUrl || record.videoUrl);
  const duration = formatDurationMs(Number(record.totalDurationMs || 0) || 0) || "0s";
  elements.roughCutResult.hidden = false;
  elements.roughCutResult.innerHTML = `
    <div class="material-rough-cut-head">
      <div>
        <span class="panel-kicker">ROUGH CUT</span>
        <strong>${escapeHtml(record.name || "文案匹配预剪素材")}</strong>
        <small>${Number(record.clipCount || 0)} 个片段 · ${escapeHtml(duration)} · 9:16 / 30fps / 静音</small>
      </div>
      <div class="material-rough-cut-actions">
        <a class="mini-action" href="${escapeHtml(videoUrl)}" target="_blank" rel="noopener">单独播放</a>
        <a class="mini-action primary" href="${escapeHtml(downloadUrl)}" download>下载 MP4</a>
      </div>
    </div>
    <video controls preload="metadata" src="${escapeHtml(videoUrl)}"></video>
    <small>这是按当前文案与标签生成的静音粗剪，正式字幕、配音和转场继续在 ChatCut 或剪映中编辑。</small>
  `;
}

async function exportProductRoughCut() {
  if (state.roughCutRunning || state.draftRunning) return;
  const allEntries = entries();
  const filtered = filterEntries(allEntries);
  const scopedItems = productFilmScopeItems(allEntries, filtered);
  const targetDurationMs = productFilmTargetMs();
  const health = productFilmHealth(scopedItems, productFilmStyle());
  if (!health.canGenerate) {
    const message = `${health.status}。请先补充素材、调整文案或切换素材范围。`;
    if (elements.productFilmStatus) elements.productFilmStatus.textContent = message;
    showToast(message);
    return;
  }
  const baseClips = buildProductFilmClips(scopedItems, targetDurationMs, {
    style: productFilmStyle(),
    notePrefix: productFilmName(),
  });
  const selectedClips = enabledProductFilmClips(baseClips);
  if (!selectedClips.length) {
    showToast("没有启用的预剪片段，请先确认生成前片段与文案");
    return;
  }

  setRoughCutBusy(true);
  if (elements.productFilmStatus) {
    elements.productFilmStatus.textContent = `正在按文案导出预剪素材：${selectedClips.length} 个片段，预计 ${formatDurationMs(selectedClips.reduce((sum, clip) => sum + Number(clip.durationMs || 0), 0))}。`;
  }
  try {
    const payload = await requestJson("/api/material-library/rough-cut", {
      method: "POST",
      body: JSON.stringify({
        name: productRoughCutName(),
        maxClips: Math.min(30, selectedClips.length),
        targetRatio: "9:16",
        selectedClips,
        copyText: productFilmCopy(scopedItems, selectedClips),
      }),
    });
    state.obsidian = payload.obsidian || state.obsidian;
    const result = payload.result || {};
    const record = result.record || {};
    state.roughCutRecord = record;
    renderRoughCutResult(record);
    if (elements.productFilmStatus) {
      elements.productFilmStatus.textContent = `预剪素材已导出：${record.clipCount || selectedClips.length} 个片段 · ${formatDurationMs(record.totalDurationMs || 0) || "0s"} · 已写入 Obsidian。`;
    }
    showToast("文案匹配预剪素材已导出");
  } catch (error) {
    if (elements.productFilmStatus) elements.productFilmStatus.textContent = `导出预剪素材失败：${error.message}`;
    showToast(error.message);
  } finally {
    setRoughCutBusy(false);
  }
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

function activeBatch() {
  return state.library.batches.find((batch) => batch.id === state.library.activeId) || state.library.batches[0];
}

function batchExists(batchId) {
  return state.library.batches.some((batch) => batch.id === batchId);
}

function batchName(batchId) {
  return state.library.batches.find((batch) => batch.id === batchId)?.name || "未分批";
}

function normalizeKind(kind) {
  const value = String(kind || "").trim();
  return ["image", "video", "audio"].includes(value) ? value : "image";
}

function kindLabel(kind) {
  return { image: "图片", video: "视频", audio: "音频" }[kind] || "素材";
}

function inferKindFromUrl(url) {
  if (/\.(mp4|mov|webm|m4v)(\?|#|$)/i.test(url)) return "video";
  if (/\.(mp3|wav|m4a|aac|ogg|flac)(\?|#|$)/i.test(url)) return "audio";
  return "image";
}

function materialDisplayName(url) {
  try {
    const parsed = new URL(url);
    const name = decodeURIComponent(parsed.pathname.split("/").filter(Boolean).pop() || parsed.host);
    return name || parsed.host;
  } catch {
    return String(url || "素材");
  }
}

const PANEL_MEDIA_PATH_PREFIXES = ["/external-materials/", "/uploads/", "/rough-cuts/", "/analysis-assets/"];

function playableMaterialUrl(rawUrl) {
  const value = String(rawUrl || "").trim();
  if (!value) return "";
  try {
    const parsed = new URL(value, window.location.href);
    const isPanelPath = PANEL_MEDIA_PATH_PREFIXES.some((prefix) => parsed.pathname.startsWith(prefix));
    if (!isPanelPath || !window.location.origin || window.location.origin === "null") return value;
    const host = parsed.hostname.toLowerCase();
    const isLoopback = host === "localhost" || host === "0.0.0.0" || host === "::1" || host.startsWith("127.");
    const isRelative = value.startsWith("/");
    const isCurrentPanel = parsed.origin === window.location.origin;
    const isKnownPanelOrigin = isLoopback || parsed.port === "8794";
    const isPanelOnlyPath = !parsed.pathname.startsWith("/uploads/");
    if (!isRelative && !isCurrentPanel && !isKnownPanelOrigin && !isPanelOnlyPath) return value;
    return `${window.location.origin}${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return value;
  }
}

function materialNeedsPlaybackProxy(item) {
  const codec = String(item?.technical?.videoCodec || "").trim().toLowerCase();
  return Boolean(codec && !["h264", "avc1", "vp8", "vp9", "av1"].includes(codec));
}

function playableVideoUrl(item) {
  const rawUrl = String(item?.url || "").trim();
  const normalizedUrl = playableMaterialUrl(rawUrl);
  if (!rawUrl || !materialNeedsPlaybackProxy(item)) return normalizedUrl;
  try {
    const parsed = new URL(normalizedUrl, window.location.href);
    const isPanelPath = PANEL_MEDIA_PATH_PREFIXES.some((prefix) => parsed.pathname.startsWith(prefix));
    if (!isPanelPath || parsed.origin !== window.location.origin) return normalizedUrl;
    return `${window.location.origin}/playback-material?url=${encodeURIComponent(rawUrl)}`;
  } catch {
    return normalizedUrl;
  }
}

function cleanUrl(url) {
  return String(url || "").trim().replace(/[.,;)\]，。；）】]+$/g, "");
}

function parseUrlList(value) {
  return [...new Set(String(value || "").split(/[\n,，]+/).map(cleanUrl).filter(Boolean))];
}

function parsePathList(value) {
  return [...new Set(String(value || "").split(/\n+/).map((line) => line.trim().replace(/^["']|["']$/g, "")).filter(Boolean))];
}

function formatBytes(value) {
  const size = Number(value || 0);
  if (!size) return "";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function trimNumber(value, digits = 3) {
  const number = Number(value || 0);
  if (!number) return "";
  return number.toFixed(digits).replace(/\.0+$|(?<=\.[0-9]*?)0+$/g, "").replace(/\.$/, "");
}

function formatDurationMs(value) {
  const durationMs = Number(value || 0) || 0;
  if (!durationMs) return "";
  if (durationMs < 60000) return `${trimNumber(durationMs / 1000, 1)}s`;
  const totalSeconds = Math.round(durationMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function normalizeManualClipSelection(raw) {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((clip) => clip && typeof clip === "object" && clip.url)
    .slice(0, 30)
    .map((clip) => ({
        id: String(clip.id || `clip-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`),
        url: String(clip.url || ""),
        startMs: Math.max(0, Math.round(Number(clip.startMs || 0) || 0)),
        endMs: Math.max(0, Math.round(Number(clip.endMs || 0) || 0)),
        clipUnit: clip.clipUnit === "segment" ? "segment" : "manual",
        segmentId: String(clip.segmentId || "").slice(0, 80),
        segmentScore: Math.max(0, Math.min(100, Math.round(Number(clip.segmentScore || 0) || 0))),
        segmentRole: String(clip.segmentRole || clip.role || "").slice(0, 40),
        tags: splitTags(clip.tags || clip.segmentTags || []),
        note: String(clip.note || "").slice(0, 160),
      }));
}

function loadManualClipSelection() {
  try {
    return normalizeManualClipSelection(JSON.parse(window.localStorage.getItem(MANUAL_CLIP_SELECTION_KEY) || "[]"));
  } catch {
    return [];
  }
}

function saveManualClipSelection() {
  window.localStorage.setItem(MANUAL_CLIP_SELECTION_KEY, JSON.stringify(state.manualClips.slice(0, 30)));
  window.clearTimeout(state.manualClipSaveTimer);
  state.manualClipSaveTimer = window.setTimeout(() => persistManualCutDraft().catch(() => {}), 240);
}

function manualCutDraftPayload() {
  return {
    version: 1,
    activeBatchId: activeBatch()?.id || "",
    selectedClipId: state.selectedManualClipId || "",
    clips: state.manualClips.map((clip, index) => ({
      ...clip,
      order: index,
      role: clip.segmentRole || "unassigned",
      tags: splitTags(clip.tags || []),
    })),
  };
}

async function persistManualCutDraft() {
  try {
    const payload = await requestJson("/api/material-library/manual-cut-draft", {
      method: "POST",
      body: JSON.stringify({ draft: manualCutDraftPayload() }),
    });
    state.manualClipSyncError = "";
    state.obsidian = payload.obsidian || state.obsidian;
    if (elements.manualTimelineStatus) elements.manualTimelineStatus.textContent = "片段顺序与标签已同步到 Obsidian";
  } catch (error) {
    state.manualClipSyncError = error.message;
    if (elements.manualTimelineStatus) elements.manualTimelineStatus.textContent = `浏览器已保存，Obsidian 同步失败：${error.message}`;
    throw error;
  }
}

function clampManualClipRange(clip, item) {
  const technical = normalizeTechnical(item?.technical, "video");
  const totalMs = Math.max(0, Math.round(Number(technical.durationMs || 0) || 0));
  let startMs = Math.max(0, Math.round(Number(clip?.startMs || 0) || 0));
  let endMs = Math.max(0, Math.round(Number(clip?.endMs || 0) || 0));
  if (!endMs || endMs <= startMs) endMs = startMs + MANUAL_CLIP_DEFAULT_MS;
  if (totalMs) {
    startMs = Math.min(startMs, Math.max(0, totalMs - MANUAL_CLIP_MIN_MS));
    endMs = Math.min(endMs, totalMs);
  }
  if (endMs - startMs < MANUAL_CLIP_MIN_MS) {
    endMs = totalMs ? Math.min(totalMs, startMs + MANUAL_CLIP_MIN_MS) : startMs + MANUAL_CLIP_MIN_MS;
  }
  if (endMs <= startMs) {
    startMs = 0;
    endMs = totalMs || MANUAL_CLIP_DEFAULT_MS;
  }
  return { startMs, endMs, durationMs: Math.max(0, endMs - startMs), totalMs };
}

function validSmartSegments(item, { minimumScore = 0 } = {}) {
  const segments = Array.isArray(item?.analysis?.segments) ? item.analysis.segments : [];
  return segments
    .filter((segment) => {
      const startMs = Number(segment?.startMs || 0) || 0;
      const endMs = Number(segment?.endMs || 0) || 0;
      return endMs - startMs >= MANUAL_CLIP_MIN_MS && (Number(segment?.score || 0) || 0) >= minimumScore;
    })
    .sort((a, b) => (Number(b.score || 0) || 0) - (Number(a.score || 0) || 0) || (Number(b.confidence || 0) || 0) - (Number(a.confidence || 0) || 0));
}

function bestSmartSegment(item) {
  return validSmartSegments(item)[0] || null;
}

function findSmartSegment(item, { id = "", startMs = null, endMs = null } = {}) {
  const segments = validSmartSegments(item);
  const cleanId = String(id || "").trim();
  if (cleanId) {
    const byId = segments.find((segment) => String(segment.id || "") === cleanId);
    if (byId) return byId;
  }
  if (startMs !== null && endMs !== null) {
    const start = Number(startMs || 0) || 0;
    const end = Number(endMs || 0) || 0;
    return segments.find((segment) => Math.abs((Number(segment.startMs || 0) || 0) - start) <= 150 && Math.abs((Number(segment.endMs || 0) || 0) - end) <= 150) || null;
  }
  return null;
}

function bestDefaultManualRange(item) {
  const technical = normalizeTechnical(item?.technical, "video");
  const totalMs = Math.max(0, Math.round(Number(technical.durationMs || 0) || 0));
  const segment = bestSmartSegment(item);
  if (segment) {
    return clampManualClipRange({ startMs: segment.startMs, endMs: segment.endMs }, item);
  }
  const hints = Array.isArray(item?.analysis?.cutHints) ? item.analysis.cutHints : [];
  const hint = hints
    .filter((entry) => entry && Number(entry.endMs || 0) - Number(entry.startMs || 0) >= MANUAL_CLIP_MIN_MS)
    .sort((a, b) => Number(b.confidence || 0) - Number(a.confidence || 0))[0];
  if (hint) {
    return clampManualClipRange({ startMs: hint.startMs, endMs: hint.endMs }, item);
  }
  return clampManualClipRange({ startMs: 0, endMs: totalMs ? Math.min(totalMs, MANUAL_CLIP_DEFAULT_MS) : MANUAL_CLIP_DEFAULT_MS }, item);
}

function secondsInputValue(ms) {
  return trimNumber(Number(ms || 0) / 1000, 2) || "0";
}

function secondsToMs(value) {
  return Math.max(0, Math.round((Number(value || 0) || 0) * 1000));
}

function segmentMarksLabel(segment) {
  const marks = Array.isArray(segment?.secondMarks) ? segment.secondMarks : [];
  return marks
    .slice(0, 6)
    .map((mark) => `${Number(mark.second || 0) || 0}s:${Math.round(Number(mark.score || 0) || 0)}`)
    .join(" / ");
}

function addManualClip(item, requestedRange = null) {
  if (!item?.url || item.kind !== "video") return;
  if (state.manualClips.length >= 30) {
    showToast("最多选择 30 个片段");
    return;
  }
  const range = requestedRange
    ? clampManualClipRange({ startMs: requestedRange.startMs, endMs: requestedRange.endMs }, item)
    : bestDefaultManualRange(item);
  const segment = requestedRange?.segment || findSmartSegment(item, { startMs: range.startMs, endMs: range.endMs });
  const note = String(
    requestedRange?.note
    || (segment ? `智能片段 ${formatRangeMs(segment.startMs, segment.endMs)} · ${Math.round(Number(segment.score || 0) || 0)}分` : "")
  ).slice(0, 160);
  state.manualClips.push({
    id: `clip-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    url: item.url,
    startMs: range.startMs,
    endMs: range.endMs,
    clipUnit: segment ? "segment" : "manual",
    segmentId: segment ? String(segment.id || "") : "",
    segmentScore: segment ? Math.round(Number(segment.score || 0) || 0) : 0,
    segmentRole: String(requestedRange?.role || segment?.role || item.editRole || "unassigned"),
    tags: splitTags(requestedRange?.tags || segment?.tags || []),
    note,
  });
  state.selectedManualClipId = state.manualClips[state.manualClips.length - 1].id;
  saveManualClipSelection();
  render();
  showToast(`已加入剪辑：${item.name || materialDisplayName(item.url)} · ${formatRangeMs(range.startMs, range.endMs)}`);
}

function addManualSegment(item, segment) {
  if (!segment) return;
  addManualClip(item, {
    startMs: segment.startMs,
    endMs: segment.endMs,
    segment,
    note: `智能片段 ${formatRangeMs(segment.startMs, segment.endMs)} · ${Math.round(Number(segment.score || 0) || 0)}分`,
  });
}

function removeManualClipsForUrl(url) {
  const before = state.manualClips.length;
  state.manualClips = state.manualClips.filter((clip) => clip.url !== url);
  if (state.manualClips.length !== before) saveManualClipSelection();
}

function updateManualClip(id, patch = {}) {
  const clip = state.manualClips.find((item) => item.id === id);
  if (!clip) return;
  Object.assign(clip, patch);
  const item = entries().find((entry) => entry.url === clip.url);
  const range = clampManualClipRange(clip, item);
  clip.startMs = range.startMs;
  clip.endMs = range.endMs;
  clip.note = String(clip.note || "").slice(0, 160);
  clip.tags = splitTags(clip.tags || []);
  const segment = findSmartSegment(item, { id: clip.segmentId, startMs: clip.startMs, endMs: clip.endMs });
  clip.clipUnit = segment ? "segment" : "manual";
  clip.segmentId = segment ? String(segment.id || "") : "";
  clip.segmentScore = segment ? Math.round(Number(segment.score || 0) || 0) : 0;
  clip.segmentRole = String(clip.segmentRole || segment?.role || item?.editRole || "unassigned");
  saveManualClipSelection();
  render();
}

function removeManualClip(id) {
  state.manualClips = state.manualClips.filter((clip) => clip.id !== id);
  if (state.selectedManualClipId === id) state.selectedManualClipId = state.manualClips[0]?.id || "";
  saveManualClipSelection();
  render();
}

function moveManualClip(id, delta) {
  const index = state.manualClips.findIndex((clip) => clip.id === id);
  const nextIndex = index + delta;
  if (index < 0 || nextIndex < 0 || nextIndex >= state.manualClips.length) return;
  const [clip] = state.manualClips.splice(index, 1);
  state.manualClips.splice(nextIndex, 0, clip);
  saveManualClipSelection();
  render();
}

function manualClipPayload(items = entries()) {
  const itemMap = new Map(items.map((item) => [item.url, item]));
  return state.manualClips
    .map((clip, index) => {
      const item = itemMap.get(clip.url);
      if (!item || item.kind !== "video") return null;
      const range = clampManualClipRange(clip, item);
      if (range.durationMs < MANUAL_CLIP_MIN_MS) return null;
      const segment = findSmartSegment(item, { id: clip.segmentId, startMs: range.startMs, endMs: range.endMs });
      const keyframes = Array.isArray(item.analysis?.keyframes) ? item.analysis.keyframes : [];
      const thumbnailFrame = keyframes
        .slice()
        .filter((frame) => frame?.path)
        .sort((a, b) => Math.abs(Number(a.timeMs || 0) - range.startMs) - Math.abs(Number(b.timeMs || 0) - range.startMs))[0];
      return {
        id: clip.id,
        order: index,
        url: item.url,
        name: item.name || materialDisplayName(item.url),
        startMs: range.startMs,
        endMs: range.endMs,
        durationMs: range.durationMs,
        thumbnail: analysisAssetUrl(thumbnailFrame?.path || ""),
        clipUnit: segment ? "segment" : "manual",
        segmentId: segment ? String(segment.id || "") : String(clip.segmentId || ""),
        segmentScore: segment ? Math.round(Number(segment.score || 0) || 0) : Math.round(Number(clip.segmentScore || 0) || 0),
        role: clip.segmentRole || segment?.role || item.editRole,
        secondMarks: segment?.secondMarks || [],
        segmentTags: splitTags(clip.tags || segment?.tags || []),
        note: clip.note || "",
      };
    })
    .filter(Boolean);
}

function technicalChips(item) {
  const technical = normalizeTechnical(item?.technical, item?.kind || "image");
  const chips = [];
  if (technical.width && technical.height) chips.push(`${technical.width}x${technical.height}`);
  if (["portrait", "landscape", "square"].includes(technical.orientation)) chips.push(technical.orientation);
  const duration = formatDurationMs(technical.durationMs);
  if (duration) chips.push(duration);
  const fps = trimNumber(technical.fps, 3);
  if (fps) chips.push(`${fps}fps`);
  if (technical.bitrateKbps) chips.push(`${technical.bitrateKbps}kbps`);
  if (item?.kind === "audio" && technical.audioCodec) chips.push(technical.audioCodec);
  if (item?.kind === "video" && technical.hasAudio) chips.push(technical.audioCodec ? `audio:${technical.audioCodec}` : "has-audio");
  return chips;
}

function invalidVideoReasons(item) {
  if (item?.kind !== "video") return [];
  const technical = normalizeTechnical(item.technical, "video");
  const size = Number(item.size || 0) || 0;
  const reasons = [];
  if (!item.url) reasons.push("缺少 URL");
  if (size > 0 && size < 1024) reasons.push("文件过小");
  if (!technical.durationMs) reasons.push("缺少时长");
  if (!technical.width || !technical.height) reasons.push("缺少分辨率");
  if (item.analysisStatus === "rejected") reasons.push("已标记废弃");
  return [...new Set(reasons)];
}

function videoHealthWarnings(item) {
  if (item?.kind !== "video") return [];
  const reasons = invalidVideoReasons(item);
  const frameIndex = item.analysis?.frameIndex || {};
  const indexedFrames = Number(frameIndex.indexedFrames || 0) || 0;
  const totalFrames = Number(frameIndex.totalFrames || 0) || 0;
  const hasAnalysisEvidence = Boolean(item.analysis?.frameCount || indexedFrames || item.analysis?.keyframes?.length);
  if (["ready", "analyzed"].includes(item.analysisStatus) && !hasAnalysisEvidence) reasons.push("缺少抽帧证据");
  if (totalFrames && indexedFrames && indexedFrames < totalFrames) reasons.push("帧索引未完整");
  return [...new Set(reasons)];
}

function isInvalidVideo(item) {
  return invalidVideoReasons(item).length > 0;
}

function hasFrameEvidence(item) {
  const frameIndex = item.analysis?.frameIndex || {};
  return Boolean(item.analysis?.frameCount || item.analysis?.keyframes?.length || Number(frameIndex.indexedFrames || 0));
}

function smartEditSignal(item) {
  const technical = normalizeTechnical(item?.technical, "video");
  const analysis = normalizeAnalysis(item?.analysis);
  let score = 0;
  const reasons = [];
  const penalties = [];
  const quality = normalizeQualityScore(item?.qualityScore);
  score += quality * 12;
  if (quality >= 4) reasons.push(`质量 ${quality}/5`);
  else if (quality <= 2) penalties.push(`质量偏低 ${quality}/5`);

  const priority = normalizePriority(item?.priority);
  score += ({ high: 15, normal: 7, low: -6 }[priority] || 0);
  if (priority === "high") reasons.push("高优先");
  if (priority === "low") penalties.push("低优先");

  const status = normalizeAnalysisStatus(item?.analysisStatus);
  score += status === "ready" ? 8 : 4;
  if (status === "ready") reasons.push("可剪辑");

  const role = normalizeEditRole(item?.editRole, "video");
  if (["hook", "try_on", "detail", "motion", "proof"].includes(role)) {
    score += 6;
    reasons.push(optionLabel(EDIT_ROLE_OPTIONS, role));
  } else if (["transition", "ending"].includes(role)) {
    score += 3;
  } else {
    score -= 8;
    penalties.push("用途未判断");
  }

  const pixels = technical.width * technical.height;
  if (technical.orientation === "portrait") {
    score += 8;
    reasons.push("竖屏");
  } else if (technical.orientation === "square") {
    score += 5;
  } else if (technical.orientation === "unknown") {
    score -= 5;
    penalties.push("画幅未知");
  } else {
    score += 1;
  }

  if (pixels >= 1080 * 1920) {
    score += 10;
    reasons.push("1080p");
  } else if (pixels >= 720 * 1280) {
    score += 8;
    reasons.push("720p+");
  } else if (pixels >= 540 * 960) {
    score += 4;
  } else {
    score -= 8;
    penalties.push("分辨率低");
  }

  const durationMs = Number(technical.durationMs || 0) || 0;
  if (durationMs >= 2500 && durationMs <= 12000) {
    score += 10;
    reasons.push("时长适合");
  } else if (durationMs > 12000 && durationMs <= 30000) {
    score += 7;
    reasons.push("可截高光");
  } else if (durationMs >= 1500 && durationMs < 2500) {
    score += 5;
  } else if (durationMs > 30000 && durationMs <= 60000) {
    score += 2;
    penalties.push("偏长");
  } else if (durationMs > 60000) {
    score -= 12;
    penalties.push("长视频需拆条");
  } else {
    score -= 20;
    penalties.push("时长异常");
  }

  if (technical.fps >= 24) score += 4;
  else if (technical.fps >= 15) score += 2;
  else {
    score -= 5;
    penalties.push("帧率低");
  }
  if (technical.bitrateKbps >= 2500) score += 5;
  else if (technical.bitrateKbps >= 800) score += 3;
  else if (technical.bitrateKbps && technical.bitrateKbps < 300) {
    score -= 8;
    penalties.push("码率低");
  }
  if (technical.hasAudio) score += 2;

  const frameIndex = analysis.frameIndex || {};
  const indexedFrames = Number(frameIndex.indexedFrames || 0) || 0;
  const totalFrames = Number(frameIndex.totalFrames || 0) || 0;
  if (frameIndex.complete && indexedFrames) {
    score += 8;
    reasons.push("帧索引完整");
  } else if (indexedFrames) {
    score += 5;
    reasons.push("有帧索引");
  } else if (analysis.keyframes?.length) {
    score += 3;
  } else {
    score -= 10;
    penalties.push("缺少帧证据");
  }
  if (totalFrames && indexedFrames && indexedFrames < totalFrames * 0.5) {
    score -= 5;
    penalties.push("帧索引不足");
  }

  const hints = Array.isArray(analysis.cutHints) ? analysis.cutHints.filter((hint) => hint && hint.endMs - hint.startMs >= 1200) : [];
  if (hints.length) {
    const confidence = Math.max(...hints.map((hint) => Number(hint.confidence || 0) || 0));
    score += Math.min(10, confidence * 10);
    reasons.push("AI截取建议");
  } else {
    score -= 3;
    penalties.push("缺少截取建议");
  }

  const segments = validSmartSegments({ analysis }, { minimumScore: 0 });
  if (segments.length) {
    const bestSegmentScore = Math.max(...segments.map((segment) => Number(segment.score || 0) || 0));
    score += Math.min(12, bestSegmentScore / 10);
    reasons.push(`已拆 ${segments.length} 段`);
    if (bestSegmentScore >= 80) reasons.push(`高分片段 ${Math.round(bestSegmentScore)}`);
  } else {
    penalties.push("未拆片段");
  }

  const tags = new Set([...(item?.tags || []), ...(item?.aiTags || []), ...(analysis.autoTags || [])]);
  [
    ["优先混剪", 8],
    ["可剪辑", 5],
    ["高清", 4],
    ["帧级索引", 4],
    ["废片", -25],
    ["异常", -15],
  ].forEach(([tag, bonus]) => {
    if (!tags.has(tag)) return;
    score += bonus;
    if (bonus > 0) reasons.push(tag);
    else penalties.push(tag);
  });

  const smartScore = Math.max(0, Math.min(100, Math.round(score)));
  const smartTier = smartScore >= 82 ? "excellent" : smartScore >= 70 ? "preferred" : smartScore >= 55 ? "usable" : "review";
  return { smartScore, smartTier, eligible: smartScore >= 55, reasons: [...new Set(reasons)].slice(0, 5), penalties: [...new Set(penalties)].slice(0, 5) };
}

function isAutoEditCandidate(item) {
  const technical = normalizeTechnical(item?.technical, "video");
  const smart = smartEditSignal(item);
  return item?.kind === "video"
    && ["ready", "analyzed"].includes(item.analysisStatus)
    && !isInvalidVideo(item)
    && technical.durationMs > 0
    && hasFrameEvidence(item)
    && smart.eligible;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function entries() {
  return Object.entries(state.library.items).map(([url, item], index) => {
    const kind = normalizeKind(item.kind || inferKindFromUrl(url));
    return {
      url,
      ...item,
      kind,
      batchId: batchExists(item.batchId) ? item.batchId : "",
      tags: splitTags(item.tags || []),
      aiTags: splitTags(item.aiTags || item.analysis?.autoTags || []),
      analysisStatus: normalizeAnalysisStatus(item.analysisStatus || item.status),
      editRole: normalizeEditRole(item.editRole || item.clipRole || item.role, kind),
      priority: normalizePriority(item.priority),
      qualityScore: normalizeQualityScore(item.qualityScore),
      notes: String(item.notes || ""),
      analysis: normalizeAnalysis(item.analysis),
      colorIndex: index,
    };
  }).filter((item) => item.kind === "video");
}

function tagInputTags() {
  return splitTags(elements.tagInput.value);
}

function upsertItem(url, patch = {}) {
  const previous = state.library.items[url] || {};
  const nextTags = patch.tags === undefined ? splitTags(previous.tags || []) : splitTags(patch.tags || []);
  const kind = normalizeKind(patch.kind || previous.kind || inferKindFromUrl(url));
  const analysis = normalizeAnalysis(patch.analysis === undefined ? previous.analysis : patch.analysis);
  const technical = normalizeTechnical(patch.technical === undefined ? previous.technical : patch.technical, kind);
  const analysisStatus = patch.analysisStatus === undefined
    ? normalizeAnalysisStatus(previous.analysisStatus || previous.status)
    : normalizeAnalysisStatus(patch.analysisStatus);
  state.library.items[url] = {
    ...previous,
    batchId: patch.batchId === undefined ? String(previous.batchId || "") : String(patch.batchId || ""),
    tags: nextTags,
    aiTags: patch.aiTags === undefined ? splitTags(previous.aiTags || analysis.autoTags || []) : splitTags(patch.aiTags || []),
    kind,
    name: String(patch.name || previous.name || ""),
    size: Number(patch.size ?? previous.size ?? 0),
    contentType: String(patch.contentType || previous.contentType || ""),
    localPath: String(patch.localPath ?? previous.localPath ?? ""),
    obsidianPath: String(patch.obsidianPath ?? previous.obsidianPath ?? ""),
    sourcePath: String(patch.sourcePath ?? previous.sourcePath ?? ""),
    externalPath: String(patch.externalPath ?? previous.externalPath ?? ""),
    sourceUrl: String(patch.sourceUrl ?? previous.sourceUrl ?? ""),
    importMethod: String(patch.importMethod ?? previous.importMethod ?? ""),
    importedAt: String(patch.importedAt ?? previous.importedAt ?? ""),
    analysisStatus,
    editRole: patch.editRole === undefined ? normalizeEditRole(previous.editRole || previous.clipRole || previous.role, kind) : normalizeEditRole(patch.editRole, kind),
    priority: patch.priority === undefined ? normalizePriority(previous.priority) : normalizePriority(patch.priority),
    qualityScore: patch.qualityScore === undefined ? normalizeQualityScore(previous.qualityScore) : normalizeQualityScore(patch.qualityScore),
    notes: patch.notes === undefined ? String(previous.notes || "").slice(0, 500) : String(patch.notes || "").slice(0, 500),
    analysis: { ...analysis, status: analysisStatus },
    technical,
    addedAt: String(previous.addedAt || patch.addedAt || new Date().toISOString()),
  };
}

function uniqueTags(items = entries()) {
  return [...new Set(items.flatMap((item) => item.tags || []))].sort((a, b) => a.localeCompare(b, "zh-CN"));
}

function renderSelect(select, options, value) {
  select.innerHTML = options.map((option) => `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`).join("");
  select.value = value;
}

function filterEntries(items) {
  let result = items;
  const filterBatch = state.library.filterBatchId;
  if (filterBatch === "current") result = result.filter((item) => item.batchId === state.library.activeId);
  else if (filterBatch === "unbatched") result = result.filter((item) => !item.batchId);
  else if (filterBatch !== "all") result = result.filter((item) => item.batchId === filterBatch);

  const allTags = uniqueTags(items);
  if (!allTags.includes(state.library.filterTag) && !["all", "untagged"].includes(state.library.filterTag)) {
    state.library.filterTag = "all";
  }
  if (state.library.filterTag === "untagged") result = result.filter((item) => !item.tags.length);
  else if (state.library.filterTag !== "all") result = result.filter((item) => item.tags.includes(state.library.filterTag));

  if (state.kindFilter !== "all") result = result.filter((item) => item.kind === state.kindFilter);
  if (state.statusFilter !== "all") result = result.filter((item) => item.analysisStatus === state.statusFilter);
  if (state.roleFilter !== "all") result = result.filter((item) => item.editRole === state.roleFilter);
  const query = state.search.trim().toLowerCase();
  if (query) {
    result = result.filter((item) => {
      const haystack = [
        item.url,
        item.name,
        materialDisplayName(item.url),
        batchName(item.batchId),
        item.kind,
        optionLabel(ANALYSIS_STATUS_OPTIONS, item.analysisStatus),
        optionLabel(EDIT_ROLE_OPTIONS, item.editRole),
        optionLabel(PRIORITY_OPTIONS, item.priority),
        item.notes,
        item.analysis?.summary,
        `智能分 ${smartEditSignal(item).smartScore}`,
        ...(item.aiTags || []),
        ...(item.analysis?.autoTags || []),
        videoHealthWarnings(item).join(" "),
        isInvalidVideo(item) ? "异常问题素材" : "",
        isAutoEditCandidate(item) ? "自动混剪候选池 智能混剪 智能优选" : "",
        technicalChips(item).join(" "),
        ...(item.tags || []),
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }
  return result;
}

function chatCutSyncScopeItems(allItems = entries(), filteredItems = null) {
  const scope = String(elements.chatcutSyncScopeSelect?.value || "filtered");
  const source = scope === "batch"
    ? allItems.filter((item) => item.batchId === activeBatch()?.id)
    : Array.isArray(filteredItems)
      ? filteredItems
      : filterEntries(allItems);
  return source.filter((item) => item.kind === "video" && item.url);
}

function chatCutSourceProductLabel(item) {
  const path = String(item?.sourcePath || item?.externalPath || item?.localPath || "").trim();
  const parts = path.split(/[\\/]+/).filter(Boolean);
  const markerIndex = parts.lastIndexOf("打标签");
  return markerIndex >= 0 && markerIndex + 1 < parts.length ? parts[markerIndex + 1] : "";
}

function chatCutSuggestedProductKey(items) {
  const labels = [...new Set(items.map(chatCutSourceProductLabel).filter(Boolean))];
  return labels.length === 1 ? labels[0] : "";
}

function chatCutFilterSnapshot(scope, items) {
  return {
    scope,
    activeBatchId: activeBatch()?.id || "",
    filterBatchId: state.library.filterBatchId,
    filterTag: state.library.filterTag,
    kind: state.kindFilter,
    status: state.statusFilter,
    role: state.roleFilter,
    search: state.search.trim(),
    requestedCount: items.length,
    capturedAt: new Date().toISOString(),
  };
}

function chatCutSyncStatusMeta(status) {
  return CHATCUT_SYNC_STATUS_META[String(status || "")] || { label: "未知", tone: "queued" };
}

function chatCutRequestSummaryText(request) {
  const summary = request?.summary || {};
  const parts = [
    `共 ${Number(summary.total || 0)}`,
    `待同步 ${Number(summary.pending || 0)}`,
    `同步中 ${Number(summary.syncing || 0)}`,
    `已导入 ${Number(summary.imported || 0) + Number(summary.alreadyImported || 0)}`,
  ];
  const problemCount = Number(summary.failed || 0) + Number(summary.unresolved || 0);
  if (problemCount) parts.push(`需处理 ${problemCount}`);
  return parts.join(" · ");
}

function renderChatCutSyncPanel(allItems = entries(), filteredItems = null) {
  if (!elements.chatcutSyncList) return;
  const scopedItems = chatCutSyncScopeItems(allItems, filteredItems);
  const readyItems = scopedItems.filter((item) => item.analysisStatus === "ready");
  const suggestedProductKey = chatCutSuggestedProductKey(readyItems);
  if (elements.chatcutProductKeyInput && document.activeElement !== elements.chatcutProductKeyInput) {
    const currentProductKey = String(elements.chatcutProductKeyInput.value || "").trim();
    if (!currentProductKey || currentProductKey === state.chatcutSuggestedProductKey) {
      elements.chatcutProductKeyInput.value = suggestedProductKey;
    }
  }
  state.chatcutSuggestedProductKey = suggestedProductKey;
  const requests = state.chatcutSync?.requests || [];
  const latest = requests[requests.length - 1] || null;
  const latestMeta = chatCutSyncStatusMeta(latest?.status);

  elements.chatcutScopeCount.textContent = String(scopedItems.length);
  elements.chatcutReadyCount.textContent = String(readyItems.length);
  elements.chatcutRequestCount.textContent = String(requests.length);
  elements.chatcutLastStatus.textContent = latest ? latestMeta.label : "未提交";
  elements.chatcutLastStatus.dataset.tone = latest ? latestMeta.tone : "idle";
  elements.chatcutSyncSubmitBtn.disabled = state.chatcutSyncRunning || !scopedItems.length;
  elements.chatcutSyncRefreshBtn.disabled = state.chatcutSyncRunning;

  if (!latest) {
    elements.chatcutSyncStatus.textContent = scopedItems.length
      ? `当前范围 ${scopedItems.length} 个视频，其中 ${readyItems.length} 个 ready；点击同步后由 ChatCut 官方连接器执行上传。`
      : "当前范围没有可提交的视频，请先选择批次或调整筛选。";
    elements.chatcutSyncList.innerHTML = "";
    return;
  }

  const latestItems = Array.isArray(latest.items) ? latest.items : [];
  const latestError = latestItems.find((item) => String(item?.error || "").trim())?.error || "";
  const statusMessages = {
    queued: `等待 ChatCut 同步执行器上传 · ${chatCutRequestSummaryText(latest)}`,
    syncing: `ChatCut 官方连接器正在上传 · ${chatCutRequestSummaryText(latest)}`,
    partial: `部分素材已进入 ChatCut，剩余项目需要重试 · ${chatCutRequestSummaryText(latest)}`,
    complete: `同步完成，素材已经进入 ChatCut 项目 · ${chatCutRequestSummaryText(latest)}`,
    failed: `同步失败${latestError ? `：${latestError}` : "，请检查项目权限或源文件"}`,
    blocked: `同步需要处理${latestError ? `：${latestError}` : "，请检查项目权限或 NAS 路径"}`,
  };
  elements.chatcutSyncStatus.textContent = `${latest.productKey || "未命名产品"} · ${statusMessages[latest.status] || chatCutRequestSummaryText(latest)}。`;
  elements.chatcutSyncList.innerHTML = requests.slice(-5).reverse().map((request) => {
    const meta = chatCutSyncStatusMeta(request.status);
    const batch = request.batchName ? ` · ${request.batchName}` : "";
    const time = formatAnalysisQueueTime(request.updatedAt || request.createdAt);
    return `
      <article class="material-chatcut-sync-item ${meta.tone}">
        <span>${escapeHtml(meta.label)}</span>
        <div>
          <strong>${escapeHtml(request.productKey || "未命名产品")}${escapeHtml(batch)}</strong>
          <small>${escapeHtml([time, chatCutRequestSummaryText(request), request.id].filter(Boolean).join(" · "))}</small>
          ${request.items?.find((item) => String(item?.error || "").trim())?.error ? `<small class="material-chatcut-sync-error">${escapeHtml(request.items.find((item) => String(item?.error || "").trim()).error)}</small>` : ""}
        </div>
      </article>
    `;
  }).join("");
}

async function submitChatCutSyncRequest() {
  if (state.chatcutSyncRunning) return;
  const projectUrl = String(elements.chatcutProjectUrlInput?.value || "").trim();
  const productKey = String(elements.chatcutProductKeyInput?.value || "").trim();
  const scope = String(elements.chatcutSyncScopeSelect?.value || "filtered");
  const allItems = entries();
  const filteredItems = filterEntries(allItems);
  const scopedItems = chatCutSyncScopeItems(allItems, filteredItems);
  try {
    if (!projectUrl) throw new Error("请先填写 ChatCut 项目链接");
    if (!productKey) throw new Error("请先填写产品名或 SKU");
    if (!scopedItems.length) throw new Error("当前同步范围没有视频素材");
    const batchIds = new Set(scopedItems.map((item) => item.batchId).filter(Boolean));
    if (batchIds.size > 1) throw new Error("当前筛选跨越多个批次，请先缩小到单个产品批次");

    state.chatcutSyncRunning = true;
    saveChatCutSyncPreferences();
    renderChatCutSyncPanel(allItems, filteredItems);
    elements.chatcutSyncStatus.textContent = "正在登记 ChatCut 同步任务...";
    const payload = await requestJson("/api/material-library/chatcut-sync/request", {
      method: "POST",
      body: JSON.stringify({
        projectUrl,
        productKey,
        scope,
        statuses: ["ready"],
        urls: scopedItems.map((item) => item.url),
        filterSnapshot: chatCutFilterSnapshot(scope, scopedItems),
      }),
    });
    state.chatcutSync = normalizeChatCutSync(payload.sync || {});
    const request = payload.request || {};
    showToast(`已进入 ChatCut 同步队列：${Number(request.summary?.pending || 0)} 个待上传`);
  } catch (error) {
    elements.chatcutSyncStatus.textContent = `提交失败：${error.message}`;
    showToast(error.message);
  } finally {
    state.chatcutSyncRunning = false;
    renderChatCutSyncPanel(entries(), filterEntries(entries()));
  }
}

function render() {
  const allEntries = entries();
  const active = activeBatch();
  const activeEntries = allEntries.filter((item) => item.batchId === active.id);
  const taggedEntries = allEntries.filter((item) => item.tags.length);
  const queuedEntries = allEntries.filter((item) => item.analysisStatus === "queued");
  const readyEntries = allEntries.filter((item) => item.analysisStatus === "ready");
  const analyzedEntries = allEntries.filter((item) => ["analyzed", "ready"].includes(item.analysisStatus));
  const videoEntries = allEntries;
  const invalidEntries = allEntries.filter(isInvalidVideo);
  const holdEntries = allEntries.filter((item) => ["hold", "rejected"].includes(item.analysisStatus) || isInvalidVideo(item));
  const unbatchedEntries = allEntries.filter((item) => !item.batchId);
  const activeVideoCount = activeEntries.length;
  const tags = uniqueTags(allEntries);
  const filtered = filterEntries(allEntries);

  renderSelect(elements.currentBatchSelect, state.library.batches.map((batch) => ({ value: batch.id, label: batch.name })), active.id);
  renderSelect(
    elements.batchFilterSelect,
    [
      { value: "all", label: "全部素材" },
      { value: "current", label: "当前批次" },
      { value: "unbatched", label: "未分批" },
      ...state.library.batches.map((batch) => ({ value: batch.id, label: batch.name })),
    ],
    state.library.filterBatchId
  );
  renderSelect(
    elements.tagFilterSelect,
    [
      { value: "all", label: "全部标签" },
      { value: "untagged", label: "未打标签" },
      ...tags.map((tag) => ({ value: tag, label: `#${tag}` })),
    ],
    state.library.filterTag
  );
  renderSelect(elements.statusFilterSelect, [{ value: "all", label: "全部状态" }, ...ANALYSIS_STATUS_OPTIONS], state.statusFilter);
  renderSelect(elements.roleFilterSelect, [{ value: "all", label: "全部用途" }, ...EDIT_ROLE_OPTIONS], state.roleFilter);
  if (document.activeElement !== elements.searchInput) elements.searchInput.value = state.search;

  if (document.activeElement !== elements.batchNameInput) elements.batchNameInput.value = active.name;
  elements.activeState.textContent = active.name;
  elements.totalState.textContent = `${allEntries.length} 个视频`;
  elements.totalCount.textContent = String(allEntries.length);
  elements.currentBatchCount.textContent = String(activeEntries.length);
  elements.taggedCount.textContent = String(taggedEntries.length);
  elements.queuedCount.textContent = String(queuedEntries.length);
  elements.readyCount.textContent = String(readyEntries.length);
  elements.analyzedCount.textContent = String(analyzedEntries.length);
  elements.videoCount.textContent = String(videoEntries.length);
  elements.holdCount.textContent = String(holdEntries.length);
  elements.unbatchedCount.textContent = String(unbatchedEntries.length);
  elements.filterCount.textContent = `${filtered.length}/${allEntries.length} 个视频`;
  elements.uploadQueueTitle.textContent = `当前批次（${activeEntries.length}）`;
  elements.uploadQueueDetail.textContent = activeEntries.length ? `${active.name} 已入库 ${activeEntries.length} 个视频` : "当前批次暂无新视频。";
  elements.uploadVideoCount.textContent = `视频 ${activeVideoCount}`;

  renderAnalysisQueue();
  renderQuickTags();
  renderSelectedTags();
  renderBatchList(allEntries);
  renderAutoEditPoolPanel(allEntries);
  renderChatCutSyncPanel(allEntries, filtered);
  renderProductFilmPanel(allEntries, filtered);
  renderWorkflowWorkbench(allEntries, activeEntries);
  renderManualClipPanel(allEntries);
  renderInvalidVideoPanel(invalidEntries);
  renderPriorityList(allEntries);
  renderWorkbenchAlerts(allEntries);
  renderAssetList(filtered, allEntries.length);
}

function currentWorkflowState(allItems, activeItems) {
  const pending = activeItems.filter((item) => !["analyzed", "ready"].includes(item.analysisStatus));
  const ready = activeItems.filter((item) => item.analysisStatus === "ready" || isAutoEditCandidate(item));
  const hasCopy = Boolean(productManualCopyText());
  const scopedItems = productFilmScopeItems(allItems, filterEntries(allItems));
  const baseClips = buildProductFilmClips(scopedItems, productFilmTargetMs(), { style: productFilmStyle(), notePrefix: productFilmName() });
  const clips = productFilmEditedClips(baseClips).filter((clip) => clip.enabled !== false);
  const matchScore = clips.length ? productCopyMatchScore(clips) : 0;
  const copySignature = productManualCopyText().replace(/\s+/g, " ").trim();
  const matched = Boolean(copySignature && state.productPrecutSignature === copySignature);
  let next = { step: "upload", label: "导入当前产品素材", detail: "当前批次还没有视频，先上传文件或引用 NAS 文件夹。" };
  if (activeItems.length && pending.length) next = { step: "analyze", label: `分析 ${pending.length} 个视频`, detail: "运行 Skill 逐秒识别镜头、用途、优缺点和可剪辑区间。" };
  else if (activeItems.length && !ready.length) next = { step: "review", label: "复核分析结果", detail: "当前没有可剪辑候选，请检查低分、异常或待补拍素材。" };
  else if (ready.length && !hasCopy) next = { step: "copy", label: "填写成片文案", detail: `已有 ${ready.length} 个候选片段；输入文案后才能按语义匹配画面。` };
  else if (hasCopy && !matched) next = { step: "match", label: "匹配文案与素材", detail: "按每句文案寻找对应的高分视频片段。" };
  else if (clips.length && matched) next = { step: "draft", label: "检查并生成草稿", detail: `已匹配 ${clips.length} 个片段，文案匹配度 ${matchScore}%。` };
  return { pending, ready, hasCopy, clips, matchScore, matched, next };
}

function renderWorkflowWorkbench(allItems, activeItems) {
  if (!elements.workflowSteps) return;
  const workflow = currentWorkflowState(allItems, activeItems);
  elements.workflowBatchCount.textContent = String(activeItems.length);
  elements.workflowPendingCount.textContent = String(workflow.pending.length);
  elements.workflowReadyCount.textContent = String(workflow.ready.length);
  elements.workflowMatchScore.textContent = `${workflow.matchScore}%`;
  elements.workflowNextDetail.textContent = workflow.next.detail;
  elements.workflowNextBtn.textContent = workflow.next.label;
  elements.workflowNextBtn.dataset.workflowAction = workflow.next.step;
  const completed = {
    upload: activeItems.length > 0,
    analyze: activeItems.length > 0 && workflow.pending.length === 0,
    review: workflow.ready.length > 0,
    copy: workflow.hasCopy,
    match: workflow.matched,
    draft: false,
  };
  elements.workflowSteps.querySelectorAll("[data-step]").forEach((button) => {
    const step = button.dataset.step;
    button.classList.toggle("is-complete", Boolean(completed[step]));
    button.classList.toggle("is-current", step === workflow.next.step);
  });
}

function focusWorkflowTarget(selector) {
  const target = document.querySelector(selector);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  if (typeof target.focus === "function" && ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(target.tagName)) {
    window.setTimeout(() => target.focus({ preventScroll: true }), 320);
  }
}

function prepareProductPrecut() {
  const activeItems = entries().filter((item) => item.batchId === activeBatch().id);
  if (!activeItems.length) {
    showToast("请先导入当前产品的视频素材");
    focusWorkflowTarget("#material-upload-section");
    return;
  }
  if (!productManualCopyText()) {
    showToast("请先填写脚本文案，一行一句效果更好");
    focusWorkflowTarget("#material-product-selling-points-input");
    return;
  }
  const pending = activeItems.filter((item) => !["analyzed", "ready"].includes(item.analysisStatus));
  if (pending.length) {
    showToast(`还有 ${pending.length} 个视频未分析，请先运行 Skill 分析`);
    focusWorkflowTarget("#material-analysis-status");
    return;
  }
  clearProductFilmCopyOverrides();
  state.productPrecutSignature = productManualCopyText().replace(/\s+/g, " ").trim();
  scheduleProductDraftSave();
  render();
  const clips = elements.productPreviewList?.querySelectorAll(".material-product-preview-item").length || 0;
  if (!clips) {
    showToast("没有找到高分匹配片段，请检查素材评分和剪辑用途");
    focusWorkflowTarget("#material-workbench-section");
    return;
  }
  showToast(`已按文案生成 ${clips} 个预剪片段`);
  focusWorkflowTarget("#material-product-preview-list");
}

function runWorkflowAction(step) {
  if (step === "analyze") {
    runMaterialAnalysis();
    return;
  }
  if (step === "match") {
    prepareProductPrecut();
    return;
  }
  const targets = {
    upload: "#material-upload-section",
    review: "#material-workbench-section",
    copy: "#material-product-selling-points-input",
    draft: "#material-product-preview-list",
  };
  if (targets[step]) focusWorkflowTarget(targets[step]);
}

function renderQuickTags() {
  elements.quickTags.innerHTML = "";
  const selected = new Set(tagInputTags());
  MATERIAL_EDITING_TAG_GROUPS.forEach((group) => {
    const section = document.createElement("section");
    section.className = "material-tag-group";
    section.innerHTML = `<strong>${escapeHtml(group.label)}</strong><div></div>`;
    const chipList = section.querySelector("div");
    group.tags.forEach((tag) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = selected.has(tag) ? "active" : "";
      button.textContent = tag;
      button.addEventListener("click", () => toggleTagInputTag(tag));
      chipList.appendChild(button);
    });
    elements.quickTags.appendChild(section);
  });
}

function setTagInputTags(tags) {
  elements.tagInput.value = splitTags(tags).join("、");
  renderSelectedTags();
}

function toggleTagInputTag(tag) {
  const current = tagInputTags();
  const exists = current.includes(tag);
  setTagInputTags(exists ? current.filter((item) => item !== tag) : [...current, tag]);
  renderQuickTags();
}

function renderSelectedTags() {
  const tags = tagInputTags();
  if (!tags.length) {
    elements.selectedTags.innerHTML = "<small>未选择标签</small>";
    return;
  }
  elements.selectedTags.innerHTML = tags.map((tag) => `<button type="button" data-tag="${escapeHtml(tag)}">#${escapeHtml(tag)}</button>`).join("");
  elements.selectedTags.querySelectorAll("button[data-tag]").forEach((button) => {
    button.addEventListener("click", () => toggleTagInputTag(button.dataset.tag));
  });
}

function renderBatchList(items) {
  elements.batchList.innerHTML = "";
  state.library.batches.forEach((batch) => {
    const batchEntries = items.filter((item) => item.batchId === batch.id);
    const tagCount = uniqueTags(batchEntries).length;
    const queuedCount = batchEntries.filter((item) => item.analysisStatus === "queued").length;
    const readyCount = batchEntries.filter((item) => item.analysisStatus === "ready").length;
    const row = document.createElement("article");
    row.className = `asset-batch-item ${batch.id === state.library.activeId ? "active" : ""}`;
    row.innerHTML = `
      <button type="button">
        <strong>${escapeHtml(batch.name)}</strong>
        <small>${batchEntries.length} 个素材 · ${readyCount} 可剪辑 · ${queuedCount} 待分析 · ${tagCount} 标签</small>
      </button>
    `;
    row.querySelector("button").addEventListener("click", () => {
      state.library.activeId = batch.id;
      state.library.filterBatchId = batch.id;
      saveLibrary();
      render();
    });
    elements.batchList.appendChild(row);
  });
}

function autoEditPoolStats(items) {
  const candidates = items
    .filter(isAutoEditCandidate)
    .map((item) => ({ ...item, smart: smartEditSignal(item) }))
    .sort((a, b) => b.smart.smartScore - a.smart.smartScore || priorityWeight(b.priority) - priorityWeight(a.priority) || b.qualityScore - a.qualityScore);
  const segmentCandidates = candidates.flatMap((item) => {
    const segments = validSmartSegments(item, { minimumScore: 55 });
    return segments.map((segment) => ({
      item,
      segment,
      role: segment.role || item.editRole || "unassigned",
      durationMs: Number(segment.durationMs || 0) || Math.max(0, (Number(segment.endMs || 0) || 0) - (Number(segment.startMs || 0) || 0)),
      smartScore: Math.max(0, Math.min(100, Math.round((item.smart.smartScore || 0) * 0.45 + (Number(segment.score || 0) || 0) * 0.55))),
    }));
  });
  const poolCandidates = segmentCandidates.length
    ? segmentCandidates
    : candidates.map((item) => ({
      item,
      segment: null,
      role: item.editRole || "unassigned",
      durationMs: Number(item.technical?.durationMs || 0) || 0,
      smartScore: item.smart.smartScore || 0,
    }));
  const roleCounts = poolCandidates.reduce((acc, candidate) => {
    const role = candidate.role || "unassigned";
    acc[role] = (acc[role] || 0) + 1;
    return acc;
  }, {});
  const updatedAt = candidates
    .map((item) => item.analysis?.updatedAt)
    .filter(Boolean)
    .sort((a, b) => String(b).localeCompare(String(a)))[0] || "";
  return {
    candidates,
    poolCandidates,
    segmentCandidates,
    totalDurationMs: poolCandidates.reduce((sum, item) => sum + (Number(item.durationMs || 0) || 0), 0),
    highCount: poolCandidates.filter((item) => item.smartScore >= 70).length,
    roleCounts,
    updatedAt,
    averageSmartScore: poolCandidates.length ? Math.round(poolCandidates.reduce((sum, item) => sum + item.smartScore, 0) / poolCandidates.length) : 0,
  };
}

function productFilmHealth(items, style = productFilmStyle()) {
  const candidates = buildProductFilmCandidates(items, style);
  const roleCounts = candidates.reduce((acc, candidate) => {
    const role = candidate.role || "unassigned";
    acc[role] = (acc[role] || 0) + 1;
    return acc;
  }, {});
  const required = PRODUCT_FILM_ROLE_REQUIREMENTS[style] || PRODUCT_FILM_ROLE_REQUIREMENTS.ecommerce;
  const covered = required.filter((role) => (roleCounts[role] || 0) > 0);
  const missing = required.filter((role) => !covered.includes(role));
  const score = required.length ? Math.round((covered.length / required.length) * 100) : 0;
  const missingLabel = missing.map((role) => optionLabel(EDIT_ROLE_OPTIONS, role)).join("、");
  const level = score >= 80 ? "ready" : score >= 50 ? "warning" : "blocked";
  const status = level === "ready"
    ? "结构完整，可以生成正式草稿"
    : level === "warning"
      ? `只建议生成测试草稿，缺少 ${missingLabel}`
      : `已阻止生成，先补齐 ${missingLabel || "核心镜头"}`;
  return { candidates, roleCounts, required, covered, missing, score, status, level, canGenerate: score >= 50 };
}

function renderProductFilmHealth(items, style) {
  return productFilmHealth(items, style);
}

function renderProductFilmQualityGate(health) {
  if (!elements.productQualityGate || !health) return;
  const labels = health.missing.map((role) => optionLabel(EDIT_ROLE_OPTIONS, role));
  const levelLabels = {
    ready: "正式生成就绪",
    warning: "仅建议测试草稿",
    blocked: "素材结构不足",
  };
  elements.productQualityGate.dataset.tone = health.level;
  elements.productQualityLabel.textContent = levelLabels[health.level] || "等待素材评估";
  elements.productQualityScore.textContent = `${health.score}%`;
  elements.productQualityProgress.value = health.score;
  elements.productQualityProgress.textContent = `${health.score}%`;
  elements.productQualityDetail.textContent = labels.length
    ? `已覆盖 ${health.covered.length}/${health.required.length} 类，缺少：${labels.join("、")}`
    : `已覆盖全部 ${health.required.length} 类核心镜头。`;
}

function renderProductQualityChecks(clips, health) {
  if (!elements.productQualityChecks) return;
  const enabled = clips.filter((clip) => clip.enabled !== false);
  const timelineChecks = productTimelineChecks(enabled, clips);
  const totalMs = enabled.reduce((sum, clip) => sum + (Number(clip.durationMs || 0) || 0), 0);
  const targetMs = productFilmTargetMs();
  const durationOk = totalMs >= targetMs * 0.72 && totalMs <= targetMs * 1.12;
  const roles = new Set(enabled.map((clip) => clip.role));
  const matchScore = productCopyMatchScore(enabled);
  const duplicateCheck = timelineChecks.find((item) => item.label.includes("重复片段"));
  const checks = [
    { ok: health.score >= 80, label: `角色覆盖 ${health.score}%` },
    { ok: matchScore >= 75, label: `文案匹配 ${matchScore}%` },
    { ok: durationOk, label: `时长 ${formatDurationMs(totalMs) || "0s"}/${Math.round(targetMs / 1000)}s` },
    { ok: roles.has("hook"), label: roles.has("hook") ? "开头钩子完整" : "缺少开头钩子" },
    { ok: roles.has("ending"), label: roles.has("ending") ? "结尾收口完整" : "缺少结尾收口" },
    { ok: duplicateCheck?.tone !== "warn", label: duplicateCheck?.label || "无重复片段" },
  ];
  elements.productQualityChecks.innerHTML = checks.map((check) => `<span class="${check.ok ? "ok" : "warn"}">${check.ok ? "通过" : "待处理"} · ${escapeHtml(check.label)}</span>`).join("");
}

function renderDirectionMonitor() {
  if (!elements.directionScore || !elements.directionRoles || !elements.directionActions) return;
  const monitor = state.directionMonitor && typeof state.directionMonitor === "object" ? state.directionMonitor : null;
  const panel = elements.directionScore.closest(".material-director-monitor-panel");
  if (panel) {
    panel.dataset.grade = monitor?.grade || "empty";
  }
  if (!monitor) {
    elements.directionScore.textContent = "0";
    elements.directionStatus.textContent = "等待日本剪辑导演判断";
    elements.directionUpdated.textContent = "未同步";
    elements.directionRoles.innerHTML = "<span>暂无方向数据</span>";
    elements.directionActions.innerHTML = "<small>点击刷新监控，会把方向判断写入 Obsidian。</small>";
    if (elements.refreshDirectionMonitorBtn) elements.refreshDirectionMonitorBtn.disabled = state.directionMonitorRunning;
    if (elements.applyDirectionPlanBtn) elements.applyDirectionPlanBtn.disabled = state.directionMonitorRunning;
    return;
  }
  const scopeLabel = monitor.scope?.scopeLabel ? ` · ${monitor.scope.scopeLabel}` : "";
  const editingPlan = monitor.editingPlan && typeof monitor.editingPlan === "object" ? monitor.editingPlan : null;
  const planLabel = editingPlan?.recommendedDurationSeconds
    ? ` · 建议 ${editingPlan.recommendedDurationSeconds}s/${editingPlan.recommendedClipCount || 0} 段`
    : "";
  elements.directionScore.textContent = String(monitor.score ?? 0);
  elements.directionStatus.textContent = `${monitor.verdict || "已完成方向判断"}${planLabel}${scopeLabel}`;
  elements.directionUpdated.textContent = monitor.updatedAt ? `同步 ${formatDate(monitor.updatedAt)}` : "已同步";
  const roles = Array.isArray(monitor.roleBreakdown) ? monitor.roleBreakdown : [];
  elements.directionRoles.innerHTML = roles.map((item) => {
    const primaryCount = Number(item.primaryCount ?? item.count ?? 0) || 0;
    const derivedCount = Number(item.derivedCount || 0) || 0;
    const countLabel = derivedCount ? `主 ${primaryCount} · 派 ${derivedCount}` : `${primaryCount}`;
    return `
    <span class="${item.status === "ok" ? "ok" : item.status === "derived" ? "derived" : "missing"}" title="${escapeHtml(derivedCount ? "主角色数量 + 可由复合分镜派生数量" : "主角色数量")}">
      <b>${escapeHtml(item.label || optionLabel(EDIT_ROLE_OPTIONS, item.role))}</b>
      <em>${escapeHtml(countLabel)}</em>
    </span>
  `;
  }).join("") || "<span>暂无角色覆盖</span>";
  const actions = Array.isArray(monitor.actions) ? monitor.actions.filter(Boolean).slice(0, 4) : [];
  const planMarkup = editingPlan ? `
    <div class="material-director-plan">
      <span>建议 ${Number(editingPlan.recommendedDurationSeconds || 15)}s</span>
      <span>${Number(editingPlan.recommendedClipCount || 6)} 个片段</span>
      <span>同源 ≤ ${Number(editingPlan.maxClipsPerSource || 2)}</span>
      <span>避免连续同类镜头</span>
    </div>
  ` : "";
  const actionMarkup = actions.length
    ? actions.map((action) => `<small>${escapeHtml(action)}</small>`).join("")
    : "<small>方向完整，可以直接进入剪映草稿生成。</small>";
  elements.directionActions.innerHTML = planMarkup + actionMarkup;
  if (elements.refreshDirectionMonitorBtn) elements.refreshDirectionMonitorBtn.disabled = state.directionMonitorRunning;
  if (elements.applyDirectionPlanBtn) elements.applyDirectionPlanBtn.disabled = state.directionMonitorRunning;
}

function clipCandidateKey(clip) {
  return `${clip?.url || ""}|${clip?.segmentId || `${Math.round(Number(clip?.startMs || 0) || 0)}-${Math.round(Number(clip?.endMs || 0) || 0)}`}`;
}

function productTransitionLabel(clip, index, clips) {
  if (index === 0) return "开场定帧";
  const previous = clips[index - 1] || {};
  const role = clip?.role || "unassigned";
  const previousRole = previous.role || "unassigned";
  if (role === "detail" || previousRole === "detail") return "细节推近";
  if (role === "motion" || previousRole === "motion") return "动作顺切";
  if (role === "transition") return "节奏过门";
  if (role === "ending") return "收束淡出";
  if (role === previousRole) return "同类跳切";
  return "轻转场";
}

function productTimelineChecks(enabled, allClips) {
  const duplicateMap = new Map();
  enabled.forEach((clip) => {
    const key = clipCandidateKey(clip);
    duplicateMap.set(key, (duplicateMap.get(key) || 0) + 1);
  });
  const duplicateCount = [...duplicateMap.values()].filter((count) => count > 1).length;
  const visualOnly = enabled.filter(productClipIsVisualOnly);
  const spoken = enabled.filter((clip) => !productClipIsVisualOnly(clip));
  const noCopy = spoken.filter((clip) => !String(clip.copyText || "").trim()).length;
  const copyCounts = new Map();
  spoken.forEach((clip) => {
    const key = String(clip.copyText || "").replace(/\s+/g, " ").trim().toLowerCase();
    if (key) copyCounts.set(key, (copyCounts.get(key) || 0) + 1);
  });
  const duplicateCopyCount = [...copyCounts.values()].filter((count) => count > 1).length;
  const weakMatch = spoken.filter((clip) => clip.copyMatch?.type === "sequence" || clip.copyMatch?.type === "neutral").length;
  const disabled = allClips.length - enabled.length;
  return [
    { tone: noCopy ? "warn" : "ok", label: noCopy ? `${noCopy} 段缺文案` : "文案完整" },
    { tone: duplicateCopyCount ? "warn" : "ok", label: duplicateCopyCount ? `${duplicateCopyCount} 句文案重复` : "文案无重复" },
    { tone: visualOnly.length ? "info" : "ok", label: visualOnly.length ? `${visualOnly.length} 段纯画面补镜` : "无需补镜" },
    { tone: duplicateCount ? "warn" : "ok", label: duplicateCount ? `${duplicateCount} 处重复片段` : "无重复片段" },
    { tone: weakMatch ? "warn" : "ok", label: weakMatch ? `${weakMatch} 段弱匹配` : "匹配稳定" },
    { tone: disabled ? "info" : "ok", label: disabled ? `${disabled} 段未启用` : "全部启用" },
  ];
}

function renderProductTimelinePreview(clips) {
  const enabled = clips.filter((clip) => clip.enabled !== false);
  if (!enabled.length) return "";
  const totalMs = enabled.reduce((sum, clip) => sum + (Number(clip.durationMs || 0) || 0), 0);
  const checks = productTimelineChecks(enabled, clips);
  const rail = enabled.map((clip, index) => {
    const durationMs = Number(clip.durationMs || 0) || 0;
    const width = totalMs ? Math.max(8, Math.round((durationMs / totalMs) * 100)) : Math.round(100 / enabled.length);
    const roleLabel = optionLabel(EDIT_ROLE_OPTIONS, clip.role);
    const transition = productTransitionLabel(clip, index, enabled);
    const tone = clip.copyMatch?.type === "role" ? "good" : clip.copyMatch?.type === "compatible" ? "ok" : "warn";
    return `
      <div class="material-product-timeline-segment ${tone}" style="--segment-width:${width}">
        <span>${String(index + 1).padStart(2, "0")}</span>
        <strong>${escapeHtml(roleLabel)}</strong>
        <small>${escapeHtml(formatDurationMs(durationMs) || "0s")} · ${escapeHtml(transition)}</small>
      </div>
    `;
  }).join("");
  return `
    <section class="material-product-timeline-panel" aria-label="生成前时间线预览">
      <div class="material-product-timeline-head">
        <div>
          <span class="panel-kicker">TIMELINE</span>
          <strong>生成前时间线</strong>
        </div>
        <small>${enabled.length} 段 · ${escapeHtml(formatDurationMs(totalMs) || "0s")} · ${Math.round(totalMs / 100) / 10}s</small>
      </div>
      <div class="material-product-timeline-rail">${rail}</div>
      <div class="material-product-timeline-checks">
        ${checks.map((check) => `<span class="${check.tone}">${escapeHtml(check.label)}</span>`).join("")}
      </div>
    </section>
  `;
}

function productCopyMatchMeta(clip) {
  if (productClipIsVisualOnly(clip)) {
    return { tone: "info", label: "纯画面补镜", detail: "承接口播画面，不重复生成字幕和配音" };
  }
  if (!String(clip.copyText || "").trim()) {
    return { tone: "bad", label: "缺文案", detail: "这段还没有字幕或配音文案" };
  }
  const match = clip.copyMatch || {};
  if (match.type === "role") return { tone: "good", label: "精准匹配", detail: match.label || "文案角色与画面角色一致" };
  if (match.type === "compatible") return { tone: "ok", label: "相近匹配", detail: match.label || "文案与画面方向接近" };
  if (match.source === "ai") return { tone: "ok", label: "AI 提示文案", detail: match.label || "已采用按镜头生成的 AI 文案" };
  if (match.source === "manual") return { tone: "warn", label: "顺序匹配", detail: match.label || "按文案顺序匹配到当前片段" };
  return { tone: "info", label: "自动文案", detail: "系统按镜头角色生成文案" };
}

function productCopyMatchScore(clips) {
  const enabled = clips.filter((clip) => clip.enabled !== false && !productClipIsVisualOnly(clip));
  if (!enabled.length) return 0;
  const scores = enabled.map((clip) => {
    if (!String(clip.copyText || "").trim()) return 0;
    const type = clip.copyMatch?.type || "";
    if (type === "role") return 100;
    if (type === "compatible") return 84;
    if (type === "neutral") return 66;
    if (type === "sequence") return 58;
    if (clip.copyMatch?.source === "ai") return 82;
    return clip.copyMatch?.source === "manual" ? 70 : 76;
  });
  return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
}

function rewriteMissingCopy(miss) {
  const lines = splitProductCopyText(productManualCopyText());
  const index = Math.max(0, Number(miss?.sourceIndex ?? miss?.index ?? 0) || 0);
  if (!lines[index]) return;
  const role = String(miss?.role || "unassigned");
  const replacements = {
    hook: "第一眼就能看清整体版型，穿搭效果自然又利落。",
    detail: "这款设计简洁耐看，日常搭配也很轻松。",
    try_on: "上身轮廓自然，正面和侧面都很好搭配。",
    motion: "走动时线条流畅，日常活动也很自然。",
    proof: "从实际上身效果来看，整体比例清爽利落。",
    ending: "喜欢这种穿搭风格，可以查看商品详情。",
    unassigned: "画面展示了这款商品自然、好搭配的一面。",
  };
  lines[index] = replacements[role] || replacements.unassigned;
  elements.productSellingPointsInput.value = lines.join("\n");
  state.productPrecutSignature = "";
  clearProductFilmCopyOverrides();
  scheduleProductDraftSave();
  render();
  showToast(`第 ${index + 1} 句已改为现有画面可承载的文案`);
}

function createMissingShotPrompt(miss) {
  const roleLabel = optionLabel(EDIT_ROLE_OPTIONS, miss?.role || "unassigned");
  const product = productFilmName();
  const prompt = [
    `9:16 竖屏真实日本电商短视频补镜，商品：${product}。`,
    `需要补充的镜头用途：${roleLabel}。`,
    `画面必须直接支持文案：${String(miss?.text || "").trim()}`,
    "保持商品版型、颜色、面料与参考素材一致，真实室内自然光，手机实拍质感。",
    "动作完整、主体清晰、镜头稳定，时长 5 秒，无字幕、无水印、无品牌 Logo。",
  ].join("\n");
  window.localStorage.setItem(MATERIAL_REVERSE_PROMPT_DRAFT_KEY, JSON.stringify({
    prompt,
    brief: `素材库缺口补镜：${roleLabel} · ${String(miss?.reason || "缺少对应素材")}`,
    targetMarket: "日本",
    contentLanguage: "日语",
    duration: 5,
    ratio: "9:16",
  }));
  window.localStorage.setItem("seedanceWorkspaceViewV1", "create");
  window.location.href = "/index.html#main-prompt-section";
}

function productReplacementCandidates(slotClip, allCandidates, enabledClips) {
  const copyRole = slotClip?.copyMatch?.role || (slotClip?.role && slotClip.role !== "unassigned" ? slotClip.role : "");
  const currentKey = clipCandidateKey(slotClip);
  const usedKeys = new Set(enabledClips.map(clipCandidateKey));
  usedKeys.delete(currentKey);
  return allCandidates
    .filter((candidate) => {
      const key = productCandidateKey(candidate);
      if (key === currentKey || usedKeys.has(key)) return false;
      return productCandidateRoles(candidate).some((candidateRole) => copyRoleCompatible(copyRole, candidateRole));
    })
    .map((candidate) => ({
      candidate,
      score: scoreProductCandidateForCopy({ role: copyRole, text: slotClip.copyText || "" }, candidate),
    }))
    .filter((item) => Number.isFinite(item.score))
    .sort((a, b) => b.score - a.score || b.candidate.smartScore - a.candidate.smartScore || b.candidate.segmentScore - a.candidate.segmentScore)
    .slice(0, 3)
    .map((item) => projectProductCandidateRole(item.candidate, copyRole));
}

function renderCopyMatchBoard(clips, items) {
  if (!clips.length) return "";
  const enabled = clips.filter((clip) => clip.enabled !== false);
  const spoken = enabled.filter((clip) => !productClipIsVisualOnly(clip));
  const visualOnlyCount = enabled.length - spoken.length;
  const candidates = buildProductFilmCandidates(items, productFilmStyle());
  const manualCount = spoken.filter((clip) => clip.copyMatch?.source === "manual").length;
  const matchScore = productCopyMatchScore(spoken);
  return `
    <section class="material-copy-match-board" aria-label="文案镜头匹配编辑器">
      <div class="material-copy-match-head">
        <div>
          <span class="panel-kicker">COPY MATCH</span>
          <strong>文案-镜头匹配编辑器</strong>
        </div>
        <small>${manualCount}/${spoken.length} 句已接入自填文案 · ${visualOnlyCount} 段纯画面 · 匹配 ${matchScore}%</small>
      </div>
      <div class="material-copy-match-list">
        ${clips.map((clip, index) => {
          const meta = productCopyMatchMeta(clip);
          const replacements = productReplacementCandidates(clip, candidates, enabled);
          const replacementActive = clip.replacementActive ? `<button type="button" data-action="reset-replacement">还原片段</button>` : "";
          return `
            <article class="material-copy-match-item ${meta.tone}" data-key="${escapeHtml(clip.productClipKey)}">
              <div class="material-copy-match-index">${index + 1}</div>
              <div class="material-copy-match-main">
                <div class="material-copy-match-title">
                  <strong>${escapeHtml(clip.copyText || (productClipIsVisualOnly(clip) ? "纯画面补镜（不重复文案）" : "未填写文案"))}</strong>
                  <span>${escapeHtml(meta.label)}</span>
                </div>
                <small>${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, clip.role))} · ${escapeHtml(formatRangeMs(clip.startMs, clip.endMs))} · ${escapeHtml(meta.detail)}</small>
                <div class="material-copy-match-candidates">
                  ${replacements.map((candidate) => `
                    <button type="button" data-action="replace" data-candidate-key="${escapeHtml(productCandidateKey(candidate))}">
                      ${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, candidate.role))} · ${Math.round(candidate.smartScore || 0)}分 · ${escapeHtml(formatRangeMs(candidate.startMs, candidate.endMs))}
                    </button>
                  `).join("") || "<span>暂无更优替换</span>"}
                  ${replacementActive}
                </div>
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function compactInsightText(text, limit = 96) {
  const value = String(text || "").replace(/\s+/g, " ").trim();
  if (!value) return "";
  return value.length > limit ? `${value.slice(0, Math.max(16, limit - 1))}...` : value;
}

function productClipInsightMarkup(clip, item) {
  if (!clip) return "";
  const segment = item ? findSmartSegment(item, { id: clip.segmentId, startMs: clip.startMs, endMs: clip.endMs }) : null;
  const match = clip.copyMatch || {};
  const insights = [];
  const addInsight = (tone, label, text) => {
    const clean = compactInsightText(text, 112);
    if (!clean) return;
    insights.push({ tone, label, text: clean });
  };

  if (match.source === "manual") {
    const matchLabel = match.type === "role"
      ? "\u6587\u6848\u7cbe\u51c6"
      : match.type === "compatible"
        ? "\u6587\u6848\u76f8\u8fd1"
        : "\u987a\u5e8f\u627f\u63a5";
    addInsight(match.type === "role" ? "good" : match.type === "compatible" ? "ok" : "warn", matchLabel, match.label || clip.copyText);
  } else if (productClipIsVisualOnly(clip)) {
    addInsight("info", "纯画面", match.label || "承接口播画面，不重复字幕和配音");
  }

  addInsight("info", "\u753b\u9762", segment?.contentDescription || segment?.reason || "");
  addInsight("info", "\u6587\u6848\u89d2\u5ea6", segment?.copyAngle || "");

  const strengths = Array.isArray(segment?.strengths) ? segment.strengths.filter(Boolean) : [];
  const risks = Array.isArray(segment?.risks) ? segment.risks.filter(Boolean) : [];
  addInsight("good", "\u4f18\u70b9", strengths[0] || "");
  addInsight("warn", "\u98ce\u9669", risks[0] || "");

  const bestMark = Array.isArray(clip.secondMarks)
    ? clip.secondMarks
        .filter((mark) => mark && (mark.cutAdvice || mark.note))
        .sort((a, b) => (Number(b.score || 0) || 0) - (Number(a.score || 0) || 0))[0]
    : null;
  addInsight("ok", "\u5207\u70b9", bestMark?.cutAdvice || bestMark?.note || "");

  const tags = [
    ...(Array.isArray(clip.segmentTags) ? clip.segmentTags : []),
    ...(Array.isArray(item?.tags) ? item.tags : []),
    ...(Array.isArray(item?.aiTags) ? item.aiTags : []),
  ].filter(Boolean).slice(0, 5);
  if (tags.length) addInsight("tag", "\u6807\u7b7e", tags.join(" / "));

  if (!insights.length) return "";
  return `
    <div class="material-product-clip-insights">
      ${insights.slice(0, 5).map((insight) => `
        <span class="${escapeHtml(insight.tone)}">
          <b>${escapeHtml(insight.label)}</b>
          <em>${escapeHtml(insight.text)}</em>
        </span>
      `).join("")}
    </div>
  `;
}

function renderProductFilmPreview(baseClips, items) {
  if (!elements.productPreviewList) return [];
  const clips = productFilmEditedClips(baseClips);
  const enabled = clips.filter((clip) => clip.enabled !== false);
  const itemMap = new Map(items.map((item) => [item.url, item]));
  if (elements.productPreviewSummary) {
    const totalMs = enabled.reduce((sum, clip) => sum + (Number(clip.durationMs || 0) || 0), 0);
    elements.productPreviewSummary.textContent = enabled.length
      ? `启用 ${enabled.length}/${clips.length} 个片段 · ${formatDurationMs(totalMs) || "0s"}`
      : "没有启用片段";
  }
  if (elements.productPreviewSummary) {
    const manualCount = enabled.filter((clip) => clip.copyMatch?.source === "manual").length;
    const aiCopyCount = enabled.filter((clip) => clip.copyMatch?.source === "ai").length;
    const visualOnlyCount = enabled.filter(productClipIsVisualOnly).length;
    const copyPlan = state.productFilmCopyPlan && typeof state.productFilmCopyPlan === "object" ? state.productFilmCopyPlan : null;
    if (enabled.length) {
      elements.productPreviewSummary.textContent += ` · 匹配 ${productCopyMatchScore(enabled)}% · ${draftEditSettingsLabel()}`;
    }
    if (state.directorClipLimit) {
      elements.productPreviewSummary.textContent += ` · 导演限制 ${state.directorClipLimit} 段`;
    }
    if (copyPlan?.compressed && copyPlan.sourceCount > copyPlan.plannedCount) {
      elements.productPreviewSummary.textContent += ` · 文案已按 ${copyPlan.seconds || Math.round(productFilmTargetMs() / 1000)} 秒压缩 ${copyPlan.sourceCount}→${copyPlan.plannedCount} 句`;
    } else if (copyPlan?.estimatedSeconds) {
      elements.productPreviewSummary.textContent += ` · 口播约 ${copyPlan.estimatedSeconds}s`;
    }
    if (manualCount) {
      elements.productPreviewSummary.textContent += ` · 已适配自填文案 ${manualCount} 句`;
    }
    if (aiCopyCount) {
      elements.productPreviewSummary.textContent += ` · 已采用 AI 文案 ${aiCopyCount} 句`;
    }
    if (visualOnlyCount) {
      elements.productPreviewSummary.textContent += ` · 纯画面补镜 ${visualOnlyCount} 段`;
    }
    const missCount = Array.isArray(state.productFilmCopyMisses) ? state.productFilmCopyMisses.length : 0;
    if (missCount) {
      elements.productPreviewSummary.textContent += ` · ${missCount} 句缺少对应素材`;
    }
  }
  if (!clips.length) {
    elements.productPreviewList.innerHTML = `
      <div class="material-workbench-empty">
        <strong>暂无可预览片段</strong>
        <small>先导入并分析视频，或切换到包含高分智能片段的素材范围。</small>
      </div>
    `;
    return clips;
  }
  const misses = Array.isArray(state.productFilmCopyMisses) ? state.productFilmCopyMisses : [];
  const missMarkup = misses.length ? `
    <div class="material-product-copy-misses">
      <strong>文案素材缺口</strong>
      ${misses.slice(0, 4).map((miss, missIndex) => `
        <div class="material-product-copy-miss" data-miss-index="${missIndex}">
          <small>第 ${Number(miss.sourceIndex ?? miss.index ?? 0) + 1} 句：${escapeHtml(miss.reason || "未匹配")} · ${escapeHtml(String(miss.text || "").slice(0, 80))}</small>
          <span><button type="button" data-action="rewrite-miss">改写文案</button><button type="button" data-action="generate-shot">生成补镜提示词</button></span>
        </div>
      `).join("")}
    </div>
  ` : "";
  const timelineMarkup = renderProductTimelinePreview(clips);
  const matchBoardMarkup = renderCopyMatchBoard(clips, items);
  elements.productPreviewList.innerHTML = timelineMarkup + matchBoardMarkup + missMarkup + clips.map((clip, index) => {
    const roleLabel = optionLabel(EDIT_ROLE_OPTIONS, clip.role);
    const name = clip.name || materialDisplayName(clip.url);
    const enabledChecked = clip.enabled !== false ? "checked" : "";
    const copyMatchLabel = clip.copyMatch?.label ? ` · ${clip.copyMatch.label}` : "";
    const insightMarkup = productClipInsightMarkup(clip, itemMap.get(clip.url));
    const aiSuggestedCopy = String(clip.aiSuggestedCopy || "").trim();
    const aiSuggestionReason = String(clip.aiSuggestionReason || "根据镜头用途与素材分析生成").trim();
    const suggestionUsed = aiSuggestedCopy && normalizedProductCopyKey(aiSuggestedCopy) === normalizedProductCopyKey(clip.copyText);
    const suggestionMarkup = aiSuggestedCopy ? `
      <div class="material-ai-copy-suggestion">
        <div>
          <span>AI COPY</span>
          <strong>${escapeHtml(aiSuggestedCopy)}</strong>
          <small>${escapeHtml(aiSuggestionReason)}</small>
        </div>
        <button type="button" data-action="apply-ai-copy" ${suggestionUsed ? "disabled" : ""}>${suggestionUsed ? "已采用" : "采用文案"}</button>
      </div>
    ` : "";
    const copyPlaceholder = productClipIsVisualOnly(clip)
      ? "纯画面补镜：默认不生成字幕和配音；需要时可手动填写"
      : "这段画面对应的字幕/配音文案";
    return `
      <article class="material-product-preview-item ${clip.enabled === false ? "disabled" : ""}" data-key="${escapeHtml(clip.productClipKey)}">
        <div class="material-product-preview-title">
          <span>${index + 1}</span>
          <div>
            <strong>${escapeHtml(name)}</strong>
            <small>${escapeHtml(roleLabel)} · ${escapeHtml(formatRangeMs(clip.startMs, clip.endMs))} · ${Math.round(Number(clip.segmentScore || 0) || 0)}分</small>
          </div>
          <label>
            <input data-field="enabled" type="checkbox" ${enabledChecked}>
            <em>启用</em>
          </label>
        </div>
        ${insightMarkup}
        ${suggestionMarkup}
        <textarea data-field="copyText" maxlength="500" rows="2" placeholder="${escapeHtml(copyPlaceholder)}">${escapeHtml(clip.copyText || "")}</textarea>
        <div class="material-product-preview-actions">
          <button type="button" data-action="preview">预览视频</button>
          <small>${escapeHtml(`${clip.note || ""}${copyMatchLabel}`)}</small>
        </div>
      </article>
    `;
  }).join("");
  elements.productPreviewList.querySelectorAll(".material-product-copy-miss").forEach((row) => {
    const miss = misses[Number(row.dataset.missIndex || 0)];
    row.querySelector('[data-action="rewrite-miss"]')?.addEventListener("click", () => rewriteMissingCopy(miss));
    row.querySelector('[data-action="generate-shot"]')?.addEventListener("click", () => createMissingShotPrompt(miss));
  });
  const candidateMap = new Map(buildProductFilmCandidates(items, productFilmStyle()).map((candidate) => [productCandidateKey(candidate), candidate]));
  elements.productPreviewList.querySelectorAll(".material-copy-match-item").forEach((row) => {
    const key = row.dataset.key || "";
    const clip = clips.find((item) => item.productClipKey === key);
    row.querySelectorAll('[data-action="replace"]').forEach((button) => {
      button.addEventListener("click", () => {
        const candidate = candidateMap.get(button.dataset.candidateKey || "");
        if (candidate && clip) applyProductFilmReplacement(key, candidate, clip);
      });
    });
    row.querySelector('[data-action="reset-replacement"]')?.addEventListener("click", () => clearProductFilmReplacement(key));
  });
  elements.productPreviewList.querySelectorAll(".material-product-preview-item").forEach((row) => {
    const key = row.dataset.key || "";
    const clip = clips.find((item) => item.productClipKey === key);
    const item = clip ? itemMap.get(clip.url) : null;
    row.querySelector('[data-field="enabled"]')?.addEventListener("change", (event) => {
      setProductFilmEdit(key, { enabled: event.currentTarget.checked });
      render();
    });
    row.querySelector('[data-field="copyText"]')?.addEventListener("input", (event) => {
      setProductFilmEdit(key, { copyText: event.currentTarget.value });
    });
    row.querySelector('[data-action="apply-ai-copy"]')?.addEventListener("click", () => {
      const aiSuggestedCopy = String(clip?.aiSuggestedCopy || "").trim();
      if (!aiSuggestedCopy) return;
      setProductFilmEdit(key, {
        copyText: aiSuggestedCopy,
        copyMatch: {
          source: "ai",
          type: "suggested",
          role: clip?.role || "",
          label: "已采用按镜头生成的 AI 提示文案",
        },
      });
      render();
      showToast("已采用 AI 提示文案");
    });
    row.querySelector('[data-action="preview"]')?.addEventListener("click", () => {
      if (item) openVideoLightbox(item, clip?.startMs || 0);
    });
  });
  return clips;
}

function renderProductFilmPanel(allItems, filteredItems) {
  if (!elements.generateProductFilmBtn) return;
  const active = activeBatch();
  if (elements.productNameInput && !elements.productNameInput.value && document.activeElement !== elements.productNameInput) {
    elements.productNameInput.value = active?.name || "";
  }
  const scopedItems = productFilmScopeItems(allItems, filteredItems);
  const style = productFilmStyle();
  const baseClips = buildProductFilmClips(scopedItems, productFilmTargetMs(), { style, notePrefix: productFilmName() });
  const clips = enabledProductFilmClips(baseClips);
  const totalMs = clips.reduce((sum, clip) => sum + (Number(clip.durationMs || 0) || 0), 0);
  const health = renderProductFilmHealth(scopedItems, style);
  renderProductFilmQualityGate(health);
  renderDirectionMonitor();
  const previewClips = renderProductFilmPreview(baseClips, scopedItems);
  renderProductQualityChecks(previewClips, health);
  if (elements.productFilmClipCount) elements.productFilmClipCount.textContent = String(clips.length);
  if (elements.productFilmDuration) elements.productFilmDuration.textContent = formatDurationMs(totalMs) || "0s";
  elements.generateProductFilmBtn.disabled = state.draftRunning || state.roughCutRunning || !clips.length || !health.canGenerate;
  if (elements.exportRoughCutBtn) {
    elements.exportRoughCutBtn.disabled = state.draftRunning || state.roughCutRunning || !clips.length || !health.canGenerate;
    if (!state.roughCutRunning) {
      elements.exportRoughCutBtn.textContent = health.level === "warning" ? "导出测试预剪" : "导出预剪素材";
    }
  }
  renderRoughCutResult();
  if (elements.productFilmStatus && !state.draftRunning) {
    const scopeLabel = elements.productScopeSelect?.selectedOptions?.[0]?.textContent || "当前范围";
    const styleLabel = elements.productStyleSelect?.selectedOptions?.[0]?.textContent || "产品成片";
    elements.productFilmStatus.textContent = clips.length
      ? `${scopeLabel} · ${styleLabel} · ${health?.status || "已匹配片段"} · ${health?.canGenerate ? `预计 ${formatDurationMs(totalMs) || "0s"}` : "需要补齐素材"}。`
      : `${scopeLabel} 暂无高分智能片段，请先运行 Skill 分析素材。`;
  }
}

function renderAutoEditPoolPanel(items) {
  const stats = autoEditPoolStats(items);
  const manualCount = manualClipPayload(items).length;
  elements.autoPoolCount.textContent = String(stats.poolCandidates.length);
  elements.autoPoolDuration.textContent = formatDurationMs(stats.totalDurationMs) || "0s";
  elements.autoPoolHighCount.textContent = String(stats.highCount);
  elements.autoPoolUpdated.textContent = stats.updatedAt ? `智能均分 ${stats.averageSmartScore || 0} · 最近分析 ${formatDate(stats.updatedAt)}` : "暂无分析结果";
  elements.generateJianyingDraftBtn.disabled = state.draftRunning || state.roughCutRunning || (!manualCount && !stats.poolCandidates.length);
  const roles = Object.entries(stats.roleCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
  if (!roles.length) {
    elements.autoPoolRoles.innerHTML = "<span>暂无用途分布</span>";
    return;
  }
  elements.autoPoolRoles.innerHTML = roles.map(([role, count]) => `
    <span><b>${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, role))}</b><em>${escapeHtml(count)}</em></span>
  `).join("");
}

const MANUAL_CLIP_QUICK_TAGS = [
  "开头钩子", "上身展示", "细节特写", "动作镜头", "卖点证明", "转场过渡", "结尾收口", "高分优选", "待复核",
];

function manualSourceItems(items) {
  const videos = items.filter((item) => item.kind === "video" && item.url);
  const currentBatchId = activeBatch()?.id || "";
  const currentBatchVideos = videos.filter((item) => item.batchId === currentBatchId);
  return currentBatchVideos.length ? currentBatchVideos : videos;
}

function setManualSourceStatus(message, tone = "neutral") {
  if (!elements.manualSourceStatus) return;
  elements.manualSourceStatus.textContent = message;
  elements.manualSourceStatus.dataset.tone = tone;
}

function activeManualSourceItem() {
  return entries().find((item) => item.url === state.manualSourceUrl) || null;
}

function manualSourceLabel(item) {
  return item?.name || materialDisplayName(item?.url || state.manualSourceUrl);
}

function manualSourceLoadingMessage(item) {
  if (materialNeedsPlaybackProxy(item)) {
    return `${manualSourceLabel(item)} · 正在准备 H.264 兼容预览，首次打开可能需要几秒…`;
  }
  return `${manualSourceLabel(item)} · 正在加载视频…`;
}

function renderManualRangeDuration() {
  if (!elements.manualRangeDuration) return;
  const startMs = secondsToMs(elements.manualInInput?.value);
  const endMs = secondsToMs(elements.manualOutInput?.value);
  const durationMs = Math.max(0, endMs - startMs);
  elements.manualRangeDuration.textContent = formatDurationMs(durationMs) || "0s";
  elements.manualRangeDuration.dataset.valid = durationMs >= MANUAL_CLIP_MIN_MS ? "true" : "false";
}

function handleManualSourceLoaded() {
  const item = activeManualSourceItem();
  if (!item || !elements.manualSourcePlayer) return;
  const seconds = Number(elements.manualSourcePlayer.duration || 0) || 0;
  const durationMs = seconds > 0 ? Math.round(seconds * 1000) : normalizeTechnical(item.technical, "video").durationMs;
  setManualSourceStatus(`${manualSourceLabel(item)} · 视频已就绪 · ${formatDurationMs(durationMs) || "时长读取中"} · 可播放和拖动快进`, "ready");
}

function handleManualSourceError() {
  const item = activeManualSourceItem();
  if (!item || !elements.manualSourcePlayer) return;
  const originalUrl = String(item.url || "");
  const playableUrl = playableVideoUrl(item);
  const addressNote = materialNeedsPlaybackProxy(item)
    ? "H.265/HEVC 兼容预览生成失败，请确认 FFmpeg 可用并重试"
    : playableUrl !== originalUrl
      ? "已自动修正旧面板地址，但文件仍无法读取"
      : "文件无法读取";
  const code = Number(elements.manualSourcePlayer.error?.code || 0) || 0;
  const codeNote = code ? `（错误 ${code}）` : "";
  setManualSourceStatus(`${manualSourceLabel(item)} · 无法播放${codeNote}：${addressNote}，请检查文件是否存在、登录是否有效，或当前电脑能否访问 NAS`, "error");
}

function syncManualSourceWorkspace(items, resetRange = false) {
  if (!elements.manualSourceSelect || !elements.manualSourcePlayer) return;
  const sources = manualSourceItems(items);
  if (!sources.length) {
    elements.manualSourceSelect.innerHTML = '<option value="">暂无上传视频</option>';
    elements.manualSourceSelect.disabled = true;
    elements.manualSourcePlayer.removeAttribute("src");
    elements.manualSourcePlayer.load();
    setManualSourceStatus("上传视频后会自动出现在这里。", "neutral");
    elements.manualAddRangeBtn.disabled = true;
    return;
  }
  elements.manualSourceSelect.disabled = false;
  elements.manualAddRangeBtn.disabled = false;
  const optionSignature = sources.map((item) => item.url).join("\n");
  if (elements.manualSourceSelect.dataset.signature !== optionSignature) {
    elements.manualSourceSelect.innerHTML = sources.map((item) => (
      `<option value="${escapeHtml(item.url)}">${escapeHtml(item.name || materialDisplayName(item.url))}</option>`
    )).join("");
    elements.manualSourceSelect.dataset.signature = optionSignature;
  }
  if (!sources.some((item) => item.url === state.manualSourceUrl)) state.manualSourceUrl = sources[0].url;
  elements.manualSourceSelect.value = state.manualSourceUrl;
  const item = sources.find((entry) => entry.url === state.manualSourceUrl) || sources[0];
  const range = bestDefaultManualRange(item);
  const videoUrl = playableVideoUrl(item);
  const sourceChanged = elements.manualSourcePlayer.dataset.url !== item.url || elements.manualSourcePlayer.src !== videoUrl;
  if (sourceChanged) {
    elements.manualSourcePlayer.dataset.url = item.url;
    setManualSourceStatus(manualSourceLoadingMessage(item), "loading");
    elements.manualSourcePlayer.src = videoUrl;
    elements.manualSourcePlayer.load();
  }
  if (sourceChanged || resetRange) {
    elements.manualInInput.value = secondsInputValue(range.startMs);
    elements.manualOutInput.value = secondsInputValue(range.endMs);
    renderManualRangeDuration();
  }
  const duration = normalizeTechnical(item.technical, "video").durationMs;
  if (!sourceChanged && elements.manualSourcePlayer.readyState >= HTMLMediaElement.HAVE_METADATA) {
    handleManualSourceLoaded();
  } else if (!sourceChanged) {
    setManualSourceStatus(`${manualSourceLabel(item)} · ${formatDurationMs(duration) || "等待视频时长"} · 正在等待视频数据`, "loading");
  }
}

function setManualRangeFromPlayhead(kind) {
  const player = elements.manualSourcePlayer;
  if (!player || !player.src) return;
  const seconds = Math.max(0, Number(player.currentTime || 0) || 0);
  if (kind === "in") {
    elements.manualInInput.value = trimNumber(seconds, 2) || "0";
  } else {
    elements.manualOutInput.value = trimNumber(seconds, 2) || "0";
  }
  renderManualRangeDuration();
  showToast(`已把 ${seconds.toFixed(1)}s 设为${kind === "in" ? "入点" : "出点"}`);
}

function addManualRangeFromWorkspace() {
  const item = entries().find((entry) => entry.url === state.manualSourceUrl);
  if (!item) {
    showToast("请先选择上传视频");
    return;
  }
  const startMs = secondsToMs(elements.manualInInput?.value);
  const endMs = secondsToMs(elements.manualOutInput?.value);
  if (endMs - startMs < MANUAL_CLIP_MIN_MS) {
    showToast("手动片段至少需要 1.2 秒，并且出点必须晚于入点");
    return;
  }
  addManualClip(item, {
    startMs,
    endMs,
    role: item.editRole || "unassigned",
    tags: [],
    note: `手动入出点 ${formatRangeMs(startMs, endMs)}`,
  });
}

function timelineScale(totalMs) {
  const seconds = Math.max(1, totalMs / 1000);
  return seconds <= 20 ? 42 : seconds <= 45 ? 30 : 22;
}

function renderManualTimeline(payload) {
  if (!elements.manualTimelineTrack || !elements.manualTimelineRuler) return;
  const totalMs = payload.reduce((sum, clip) => sum + clip.durationMs, 0);
  if (!payload.length) {
    elements.manualTimelineRuler.innerHTML = '<span style="left:0">00:00</span><span style="left:160px">00:05</span>';
    elements.manualTimelineTrack.innerHTML = '<div class="material-manual-timeline-empty"><strong>草稿时间线为空</strong><small>在上方播放上传视频，设置入点和出点后添加片段。</small></div>';
    elements.manualTimelineStatus.textContent = state.manualClipSyncError ? `Obsidian 同步提醒：${state.manualClipSyncError}` : "点击片段后可手动打标签";
    return;
  }
  const pxPerSecond = timelineScale(totalMs);
  const width = Math.max(680, Math.ceil(totalMs / 1000 * pxPerSecond) + 28);
  const tickStep = totalMs > 60000 ? 10 : 5;
  const ticks = [];
  for (let second = 0; second <= Math.ceil(totalMs / 1000); second += tickStep) {
    const minutes = Math.floor(second / 60);
    const remainder = second % 60;
    ticks.push(`<span style="left:${escapeHtml(second * pxPerSecond)}px">${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}</span>`);
  }
  elements.manualTimelineRuler.innerHTML = `<div style="width:${escapeHtml(width)}px">${ticks.join("")}</div>`;
  elements.manualTimelineTrack.innerHTML = `
    <div class="material-manual-timeline-canvas" style="width:${escapeHtml(width)}px">
      ${payload.map((clip, index) => {
        const selected = clip.id === state.selectedManualClipId;
        const widthPx = Math.max(48, Math.round(clip.durationMs / 1000 * pxPerSecond));
        const tags = splitTags(clip.segmentTags || []);
        return `
          <button class="material-manual-timeline-clip role-${escapeHtml(clip.role || "unassigned")}${selected ? " is-selected" : ""}" type="button" data-id="${escapeHtml(clip.id)}" style="width:${escapeHtml(widthPx)}px" aria-label="选择片段 ${escapeHtml(index + 1)} ${escapeHtml(clip.name)}">
            ${clip.thumbnail ? `<i style="background-image:url('${escapeHtml(clip.thumbnail)}')" aria-hidden="true"></i>` : ""}
            <span>${escapeHtml(index + 1)}</span>
            <strong>${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, clip.role || "unassigned"))}</strong>
            <small>${escapeHtml(formatDurationMs(clip.durationMs) || "0s")}${tags.length ? ` · #${escapeHtml(tags[0])}` : ""}</small>
          </button>
        `;
      }).join("")}
    </div>
  `;
  elements.manualTimelineTrack.querySelectorAll("button[data-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedManualClipId = button.dataset.id;
      saveManualClipSelection();
      renderManualClipPanel(entries());
    });
    button.addEventListener("dblclick", () => {
      const clip = state.manualClips.find((entry) => entry.id === button.dataset.id);
      const item = clip ? entries().find((entry) => entry.url === clip.url) : null;
      if (item) openVideoLightbox(item, clip.startMs || 0);
    });
  });
  const selectedIndex = state.manualClips.findIndex((clip) => clip.id === state.selectedManualClipId);
  elements.manualTimelineStatus.textContent = selectedIndex >= 0
    ? `已选择第 ${selectedIndex + 1} 段 · 修改用途或点击标签即可写入草稿`
    : "点击片段后可手动打标签";
}

function renderManualSelectedEditor(items) {
  if (!elements.manualSelectedEditor) return;
  const clip = state.manualClips.find((entry) => entry.id === state.selectedManualClipId);
  const item = clip ? items.find((entry) => entry.url === clip.url) : null;
  if (!clip || !item) {
    elements.manualSelectedEditor.hidden = true;
    return;
  }
  elements.manualSelectedEditor.hidden = false;
  const range = clampManualClipRange(clip, item);
  elements.manualSelectedLabel.textContent = `${item.name || materialDisplayName(item.url)} · ${formatRangeMs(range.startMs, range.endMs)}`;
  elements.manualSelectedRole.innerHTML = optionsMarkup(EDIT_ROLE_OPTIONS, clip.segmentRole || "unassigned");
  const tags = splitTags(clip.tags || []);
  elements.manualQuickTags.innerHTML = MANUAL_CLIP_QUICK_TAGS.map((tag) => (
    `<button type="button" data-tag="${escapeHtml(tag)}" class="${tags.includes(tag) ? "is-active" : ""}">#${escapeHtml(tag)}</button>`
  )).join("");
  elements.manualSelectedTags.innerHTML = tags.length
    ? tags.map((tag) => `<button type="button" data-tag="${escapeHtml(tag)}">#${escapeHtml(tag)} <span aria-hidden="true">×</span></button>`).join("")
    : "<span>当前片段还没有标签</span>";
  elements.manualQuickTags.querySelectorAll("button[data-tag]").forEach((button) => {
    button.addEventListener("click", () => {
      const next = tags.includes(button.dataset.tag)
        ? tags.filter((tag) => tag !== button.dataset.tag)
        : [...tags, button.dataset.tag];
      updateManualClip(clip.id, { tags: next });
    });
  });
  elements.manualSelectedTags.querySelectorAll("button[data-tag]").forEach((button) => {
    button.addEventListener("click", () => updateManualClip(clip.id, { tags: tags.filter((tag) => tag !== button.dataset.tag) }));
  });
}

function addTagsToSelectedManualClip() {
  const clip = state.manualClips.find((entry) => entry.id === state.selectedManualClipId);
  if (!clip) return;
  const tags = splitTags(elements.manualSelectedTagInput?.value || "");
  if (!tags.length) {
    showToast("请输入片段标签");
    return;
  }
  elements.manualSelectedTagInput.value = "";
  updateManualClip(clip.id, { tags: [...new Set([...(clip.tags || []), ...tags])] });
  showToast("片段标签已写入草稿");
}

function renderManualClipPanel(items) {
  if (!elements.manualClipList) return;
  syncManualSourceWorkspace(items);
  const itemMap = new Map(items.map((item) => [item.url, item]));
  if (state.libraryLoaded) {
    const before = state.manualClips.length;
    state.manualClips = state.manualClips.filter((clip) => itemMap.has(clip.url));
    if (state.manualClips.length !== before) saveManualClipSelection();
  }

  const payload = manualClipPayload(items);
  const totalMs = payload.reduce((sum, clip) => sum + clip.durationMs, 0);
  elements.manualClipCount.textContent = String(payload.length);
  elements.manualClipDuration.textContent = formatDurationMs(totalMs) || "0s";
  if (!state.manualClips.some((clip) => clip.id === state.selectedManualClipId)) {
    state.selectedManualClipId = state.manualClips[0]?.id || "";
  }
  renderManualTimeline(payload);
  renderManualSelectedEditor(items);
  if (elements.clearManualClipsBtn) elements.clearManualClipsBtn.disabled = !state.manualClips.length;
  if (!payload.length) {
    elements.manualClipList.innerHTML = `
      <div class="material-workbench-empty">
        <strong>还没有手动片段</strong>
        <small>在下方视频素材卡点击“加入剪辑”，再填写开始秒和结束秒。</small>
      </div>
    `;
    return;
  }

  elements.manualClipList.innerHTML = state.manualClips.map((clip, index) => {
    const item = itemMap.get(clip.url);
    if (!item) return "";
    const range = clampManualClipRange(clip, item);
    const segment = findSmartSegment(item, { id: clip.segmentId, startMs: range.startMs, endMs: range.endMs });
    const name = item.name || materialDisplayName(item.url);
    const role = clip.segmentRole || segment?.role || item.editRole;
    const segmentMeta = segment ? `智能片段 ${Math.round(Number(segment.score || 0) || 0)}分` : "手动片段";
    const clipTags = splitTags(clip.tags || segment?.tags || []);
    return `
      <article class="material-manual-clip-item" data-id="${escapeHtml(clip.id)}">
        <div class="material-manual-clip-title">
          <span>${index + 1}</span>
          <strong>${escapeHtml(name)}</strong>
          <small>${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, role))} · ${escapeHtml(segmentMeta)} · ${escapeHtml(formatDurationMs(range.durationMs) || "0s")}</small>
        </div>
        ${clipTags.length ? `<div class="material-manual-clip-tags">${clipTags.map((tag) => `<span>#${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
        <div class="material-manual-clip-fields">
          <label>
            <span>开始秒</span>
            <input data-field="startSec" type="number" min="0" step="0.1" value="${escapeHtml(secondsInputValue(range.startMs))}">
          </label>
          <label>
            <span>结束秒</span>
            <input data-field="endSec" type="number" min="0" step="0.1" value="${escapeHtml(secondsInputValue(range.endMs))}">
          </label>
        </div>
        <input class="material-manual-note" data-field="note" type="text" maxlength="160" placeholder="片段备注，可留空" value="${escapeHtml(clip.note || "")}">
        <div class="material-manual-clip-actions">
          <button type="button" data-action="preview">预览</button>
          <button type="button" data-action="up" ${index === 0 ? "disabled" : ""}>上移</button>
          <button type="button" data-action="down" ${index === state.manualClips.length - 1 ? "disabled" : ""}>下移</button>
          <button type="button" data-action="remove">删除</button>
        </div>
      </article>
    `;
  }).join("");

  elements.manualClipList.querySelectorAll(".material-manual-clip-item").forEach((row) => {
    const id = row.dataset.id;
    const clip = state.manualClips.find((item) => item.id === id);
    const item = clip ? itemMap.get(clip.url) : null;
    row.querySelector('[data-field="startSec"]').addEventListener("change", (event) => {
      updateManualClip(id, { startMs: secondsToMs(event.currentTarget.value) });
    });
    row.querySelector('[data-field="endSec"]').addEventListener("change", (event) => {
      updateManualClip(id, { endMs: secondsToMs(event.currentTarget.value) });
    });
    row.querySelector('[data-field="note"]').addEventListener("change", (event) => {
      updateManualClip(id, { note: event.currentTarget.value });
    });
    row.querySelector('[data-action="preview"]').addEventListener("click", () => {
      if (item) openVideoLightbox(item, clip?.startMs || 0);
    });
    row.querySelector('[data-action="up"]').addEventListener("click", () => moveManualClip(id, -1));
    row.querySelector('[data-action="down"]').addEventListener("click", () => moveManualClip(id, 1));
    row.querySelector('[data-action="remove"]').addEventListener("click", () => removeManualClip(id));
  });
}

function renderInvalidVideoPanel(items) {
  elements.invalidCount.textContent = String(items.length);
  if (!items.length) {
    elements.invalidList.innerHTML = `<div class="material-workbench-empty good"><strong>暂无问题素材</strong><small>当前视频都具备基础媒体信息。</small></div>`;
    return;
  }
  elements.invalidList.innerHTML = items.slice(0, 4).map((item) => `
    <button class="material-invalid-item" type="button" data-url="${escapeHtml(item.url)}">
      <strong>${escapeHtml(item.name || materialDisplayName(item.url))}</strong>
      <small>${escapeHtml(invalidVideoReasons(item).join(" · ") || "需要复核")}</small>
    </button>
  `).join("");
  elements.invalidList.querySelectorAll("button[data-url]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = state.library.items[button.dataset.url];
      const name = item?.name || materialDisplayName(button.dataset.url);
      applyWorkbenchFilter({ status: "all", kind: "video", search: name });
    });
  });
}

function priorityWeight(value) {
  return { high: 3, normal: 2, low: 1 }[value] || 0;
}

function analysisSummary(item) {
  const suggestions = Array.isArray(item.analysis?.suggestions) ? item.analysis.suggestions : [];
  return String(item.analysis?.summary || suggestions[0] || item.notes || "暂无分析摘要").slice(0, 160);
}

function applyWorkbenchFilter({ status = "all", kind = "all", role = "all", search = "" } = {}) {
  state.library.filterBatchId = "all";
  state.library.filterTag = "all";
  state.kindFilter = kind;
  state.statusFilter = status;
  state.roleFilter = role;
  state.search = search;
  render();
}

function renderPriorityList(items) {
  const candidates = items
    .filter(isAutoEditCandidate)
    .map((item) => ({ ...item, smart: smartEditSignal(item) }))
    .sort((a, b) => b.smart.smartScore - a.smart.smartScore || priorityWeight(b.priority) - priorityWeight(a.priority) || b.qualityScore - a.qualityScore || String(b.analysis?.updatedAt || "").localeCompare(String(a.analysis?.updatedAt || "")))
    .slice(0, 6);
  if (!candidates.length) {
    elements.priorityList.innerHTML = `<div class="material-workbench-empty"><strong>还没有可剪辑视频</strong><small>上传视频后点“分析待处理视频”，这里会显示优先候选。</small></div>`;
    return;
  }
  elements.priorityList.innerHTML = candidates.map((item) => `
    <button class="material-priority-item" type="button" data-url="${escapeHtml(item.url)}" data-status="${escapeHtml(item.analysisStatus)}">
      <span class="material-priority-score">${escapeHtml(item.smart.smartScore || 0)}</span>
      <span class="material-priority-body">
        <strong>${escapeHtml(item.name || materialDisplayName(item.url))}</strong>
        <small>智能分 · ${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, item.editRole))} · ${escapeHtml(optionLabel(PRIORITY_OPTIONS, item.priority))} · 质量 ${escapeHtml(item.qualityScore || 0)}/5</small>
        <em>${escapeHtml(analysisSummary(item))}</em>
        <em>${escapeHtml(item.smart.reasons.join(" · ") || technicalChips(item).join(" · ") || "等待更多质量信号")}</em>
      </span>
    </button>
  `).join("");
  elements.priorityList.querySelectorAll("button[data-url]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = state.library.items[button.dataset.url];
      const name = item?.name || materialDisplayName(button.dataset.url);
      applyWorkbenchFilter({ status: button.dataset.status || "ready", kind: "video", search: name });
    });
  });
}

function renderWorkbenchAlerts(items) {
  const alerts = items.filter((item) => ["hold", "rejected"].includes(item.analysisStatus) || isInvalidVideo(item)).slice(0, 6);
  if (!alerts.length) {
    elements.workbenchAlerts.innerHTML = `<div class="material-workbench-empty good"><strong>暂无异常素材</strong><small>当前没有待补拍或废弃项。</small></div>`;
    return;
  }
  elements.workbenchAlerts.innerHTML = alerts.map((item) => `
    <button class="material-alert-item status-${escapeHtml(item.analysisStatus)} ${isInvalidVideo(item) ? "is-invalid-video" : ""}" type="button" data-url="${escapeHtml(item.url)}" data-status="${escapeHtml(item.analysisStatus)}">
      <strong>${escapeHtml(item.name || materialDisplayName(item.url))}</strong>
      <small>${escapeHtml(optionLabel(ANALYSIS_STATUS_OPTIONS, item.analysisStatus))} · ${escapeHtml(videoHealthWarnings(item).join(" · ") || technicalChips(item).join(" · ") || "缺少技术信息")}</small>
      <em>${escapeHtml(analysisSummary(item))}</em>
    </button>
  `).join("");
  elements.workbenchAlerts.querySelectorAll("button[data-url]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = state.library.items[button.dataset.url];
      const name = item?.name || materialDisplayName(button.dataset.url);
      applyWorkbenchFilter({ status: button.dataset.status || "hold", kind: "all", search: name });
    });
  });
}

function previewMarkup(item) {
  if (item.kind === "image") {
    return `<img src="${escapeHtml(item.url)}" alt="${escapeHtml(item.name || materialDisplayName(item.url))}" loading="lazy">`;
  }
  if (item.kind === "video") {
    const videoUrl = playableVideoUrl(item);
    return `
      <button class="material-preview-button" type="button" data-action="preview-video" aria-label="播放 ${escapeHtml(item.name || materialDisplayName(item.url))}">
        <video src="${escapeHtml(videoUrl)}" muted playsinline preload="metadata"></video>
        <span>播放</span>
      </button>
    `;
  }
  return `<div class="material-asset-glyph" aria-hidden="true">♪</div>`;
}

function openVideoLightbox(item, startMs = 0) {
  if (!item?.url) return;
  const videoUrl = playableVideoUrl(item);
  state.videoLightboxUrl = videoUrl;
  elements.videoLightboxPlayer.src = videoUrl;
  elements.videoLightboxTitle.textContent = item.name || materialDisplayName(item.url);
  elements.videoLightboxUrl.textContent = videoUrl;
  elements.videoLightbox.hidden = false;
  elements.videoLightboxPlayer.load();
  const startSeconds = Math.max(0, Number(startMs || 0) / 1000);
  if (startSeconds) {
    const seek = () => {
      try {
        elements.videoLightboxPlayer.currentTime = startSeconds;
      } catch {
        // Some browsers reject seeking before metadata is ready.
      }
    };
    elements.videoLightboxPlayer.addEventListener("loadedmetadata", seek, { once: true });
  }
  document.body.classList.add("lightbox-open");
  elements.closeVideoLightboxBtn.focus();
}

function closeVideoLightbox() {
  if (!elements.videoLightbox || elements.videoLightbox.hidden) return;
  elements.videoLightbox.hidden = true;
  elements.videoLightboxPlayer.pause();
  elements.videoLightboxPlayer.removeAttribute("src");
  elements.videoLightboxPlayer.load();
  elements.videoLightboxUrl.textContent = "";
  state.videoLightboxUrl = "";
  document.body.classList.remove("lightbox-open");
}

function seekVideoLightbox(offsetSeconds) {
  if (!elements.videoLightboxPlayer || elements.videoLightbox.hidden) return;
  const player = elements.videoLightboxPlayer;
  const current = Number.isFinite(player.currentTime) ? player.currentTime : 0;
  const duration = Number.isFinite(player.duration) && player.duration > 0 ? player.duration : null;
  const target = duration ? Math.min(Math.max(current + offsetSeconds, 0), duration) : Math.max(current + offsetSeconds, 0);
  player.currentTime = target;
}

async function copyVideoLightboxUrl() {
  if (!state.videoLightboxUrl) {
    showToast("还没有可复制的视频 URL");
    return;
  }
  await navigator.clipboard.writeText(state.videoLightboxUrl);
  showToast("视频 URL 已复制");
}

function reversePromptMode() {
  return elements.reversePromptModes.find((input) => input.checked)?.value || "rebuild";
}

function reversePromptDuration(segment) {
  const segmentSeconds = Math.max(1, (Number(segment?.endMs || 0) - Number(segment?.startMs || 0)) / 1000);
  return REVERSE_PROMPT_DURATIONS.reduce((best, value) => (
    Math.abs(value - segmentSeconds) < Math.abs(best - segmentSeconds) ? value : best
  ), REVERSE_PROMPT_DURATIONS[0]);
}

function reversePromptDefaultSubject(item) {
  const name = String(item?.name || materialDisplayName(item?.url || "") || "当前商品")
    .replace(/\.(mp4|mov|webm|m4v)$/i, "")
    .replace(/[_-](?:\d+(?:\.\d+)?s?[-_]?){2,}.*$/i, "")
    .trim();
  return `一位目标市场的成年女性自然展示${name || "当前商品"}`.slice(0, 240);
}

function reversePromptEvidenceParts(item, segment) {
  const marks = Array.isArray(segment?.secondMarks) ? segment.secondMarks : [];
  const markNotes = marks.slice(0, 8).map((mark) => {
    const details = [
      mark.visualNote,
      mark.note,
      ...(Array.isArray(mark.pros) ? mark.pros : []),
      mark.cutAdvice,
    ].map((value) => String(value || "").trim()).filter(Boolean);
    return details.length ? `${Number(mark.second || 0) || 0}s：${details.join("；")}` : "";
  }).filter(Boolean);
  return [
    `来源：${item?.name || materialDisplayName(item?.url || "")}`,
    `片段：${formatRangeMs(segment?.startMs, segment?.endMs)}`,
    `用途：${segment?.adStageLabel || optionLabel(EDIT_ROLE_OPTIONS, segment?.role || item?.editRole)}`,
    segment?.contentDescription ? `画面：${segment.contentDescription}` : "",
    segment?.reason ? `选择原因：${segment.reason}` : "",
    Array.isArray(segment?.strengths) && segment.strengths.length ? `优点：${segment.strengths.join("、")}` : "",
    Array.isArray(segment?.risks) && segment.risks.length ? `风险：${segment.risks.join("、")}` : "",
    segment?.copyAngle ? `适配文案：${segment.copyAngle}` : "",
    ...markNotes,
  ].filter(Boolean);
}

function inferReversePromptCamera(item, segment) {
  const evidence = reversePromptEvidenceParts(item, segment).join(" ").toLowerCase();
  const role = String(segment?.role || item?.editRole || "");
  if (role === "detail" || /细节|特写|近景|腰头|纽扣|口袋|面料/.test(evidence)) {
    return "从稳定中近景缓慢推进到商品结构特写，终点停在最清楚的设计细节上";
  }
  if (role === "motion" || /走动|转身|抬腿|动作|摆动|步伐/.test(evidence)) {
    return "以稳定全身或中全景跟随主体运动，保持动作方向一致，动作完成后停稳半秒";
  }
  if (role === "hook" || /钩子|开头|第一眼|吸引/.test(evidence)) {
    return "第一帧直接看清商品和穿着结果，轻微快速推近，在两秒内完成视觉重点揭示";
  }
  if (role === "transition" || /转场|遮挡|抛|切点/.test(evidence)) {
    return "使用一个清楚的动作遮挡或转身作为转场，镜头方向连续，转场后立即重新看清商品";
  }
  return "使用稳定中景到全身景别，单一缓慢推近，终点保持商品轮廓清楚完整";
}

function buildLocalReversePrompt() {
  const item = state.reversePromptItem;
  const segment = state.reversePromptSegment;
  if (!item || !segment) return "";
  const mode = reversePromptMode();
  const subject = elements.reversePromptSubject?.value.trim() || reversePromptDefaultSubject(item);
  const market = elements.reversePromptMarket?.value || "日本";
  const language = elements.reversePromptLanguage?.value || REVERSE_PROMPT_MARKET_LANGUAGES[market] || "日语";
  const duration = reversePromptDuration(segment);
  const range = formatRangeMs(segment.startMs, segment.endMs);
  const stage = segment.adStageLabel || optionLabel(EDIT_ROLE_OPTIONS, segment.role || item.editRole);
  const action = segment.contentDescription || segment.reason || `完成一个清楚的${stage}动作`;
  const strengths = Array.isArray(segment.strengths) ? segment.strengths.slice(0, 4).join("、") : "";
  const risks = Array.isArray(segment.risks) ? segment.risks.slice(0, 3).join("、") : "";
  const modeLead = mode === "reference"
    ? `R2V。@Video1 的 ${range} 只负责动作节奏、构图、景别、机位和主运镜，不转移原人物身份、面部、服装、房间、Logo、字幕或音频。`
    : "T2V。根据已分析优秀片段的镜头语言重建一个原创商品镜头，不复制原人物身份、品牌标识或画面文字。";
  const timing = Math.max(1, Math.min(duration - 1, Math.round((Number(segment.endMs || 0) - Number(segment.startMs || 0)) / 1000)));
  return [
    modeLead,
    `生成一条 ${duration} 秒、9:16 竖屏的${market}电商短视频。主体：${subject}。`,
    `镜头任务：${stage}。可见动作：${action}。核心动作在前 ${timing} 秒内完成，结尾保持稳定可剪辑画面。`,
    `运镜：${inferReversePromptCamera(item, segment)}。`,
    strengths ? `保留这个分镜有效的视觉特征：${strengths}。` : "保持主体、商品和动作关系清楚，一次只表达一个视觉重点。",
    `使用方向明确、稳定的柔和自然光，商品颜色、版型、面料和结构细节保持一致；画面真实，避免过度磨皮和肢体变形。`,
    `面向${market}真实日常语境，不使用国家刻板印象；如后续加入口播或字幕，使用${language}自然口语。`,
    `声音留白，便于后期配音；不要生成烧录字幕、价格、促销承诺、水印或第三方 Logo。`,
    risks ? `主动规避原片段风险：${risks}。` : "避免无目的跳切、复杂多重运镜和与商品无关的道具。",
  ].join("\n").slice(0, 10000);
}

function renderReversePromptMeta() {
  const item = state.reversePromptItem;
  const segment = state.reversePromptSegment;
  if (!item || !segment || !elements.reversePromptMeta) return;
  const chips = [
    formatRangeMs(segment.startMs, segment.endMs),
    `${Math.round(Number(segment.score || 0) || 0)} 分`,
    segment.adStageLabel || optionLabel(EDIT_ROLE_OPTIONS, segment.role || item.editRole),
    `${reversePromptDuration(segment)} 秒生成规格`,
  ];
  elements.reversePromptMeta.innerHTML = chips.map((value) => `<span>${escapeHtml(value)}</span>`).join("");
  elements.reversePromptEvidence.textContent = reversePromptEvidenceParts(item, segment).join("\n");
}

function rebuildReversePrompt() {
  if (!state.reversePromptItem || !state.reversePromptSegment) return;
  elements.reversePromptOutput.value = buildLocalReversePrompt();
  elements.reversePromptStatus.textContent = "已根据分镜分析生成基础 Prompt，可继续编辑或使用 Skill 精修";
  renderReversePromptMeta();
}

function openReversePromptDialog(item, segment) {
  if (!item || !segment || !elements.reversePromptDialog) return;
  state.reversePromptItem = item;
  state.reversePromptSegment = segment;
  elements.reversePromptSource.textContent = `${item.name || materialDisplayName(item.url)} · ${formatRangeMs(segment.startMs, segment.endMs)}`;
  elements.reversePromptSubject.value = reversePromptDefaultSubject(item);
  elements.reversePromptMarket.value = "日本";
  elements.reversePromptLanguage.value = REVERSE_PROMPT_MARKET_LANGUAGES.日本;
  elements.reversePromptModes.forEach((input) => { input.checked = input.value === "rebuild"; });
  renderReversePromptMeta();
  rebuildReversePrompt();
  elements.reversePromptDialog.hidden = false;
  document.body.classList.add("lightbox-open");
  elements.reversePromptSubject.focus();
}

function closeReversePromptDialog() {
  if (!elements.reversePromptDialog || elements.reversePromptDialog.hidden) return;
  elements.reversePromptDialog.hidden = true;
  state.reversePromptRunning = false;
  document.body.classList.remove("lightbox-open");
}

function setReversePromptBusy(busy) {
  state.reversePromptRunning = busy;
  [elements.rebuildReversePromptBtn, elements.skillReversePromptBtn, elements.sendReversePromptBtn]
    .filter(Boolean)
    .forEach((button) => { button.disabled = busy; });
  if (elements.skillReversePromptBtn) elements.skillReversePromptBtn.textContent = busy ? "Skill 精修中..." : "Seedance Skill 精修";
}

async function refineReversePromptWithSkill() {
  if (state.reversePromptRunning) return;
  const prompt = elements.reversePromptOutput?.value.trim();
  if (!prompt) {
    showToast("请先生成基础 Prompt");
    return;
  }
  const segment = state.reversePromptSegment;
  const item = state.reversePromptItem;
  setReversePromptBusy(true);
  elements.reversePromptStatus.textContent = "正在调用已安装的 Seedance Skill 精修镜头提示词...";
  try {
    const mode = reversePromptMode();
    const payload = await requestJson("/api/skill/optimize-prompt", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        brief: reversePromptEvidenceParts(item, segment).join("\n"),
        targetMarket: elements.reversePromptMarket?.value || "日本",
        contentLanguage: elements.reversePromptLanguage?.value || "日语",
        ratio: "9:16",
        duration: reversePromptDuration(segment),
        generateAudio: false,
        refVideos: mode === "reference" && item?.url ? [item.url] : [],
      }),
    });
    const review = payload.review || {};
    if (!String(review.improvedPrompt || "").trim()) throw new Error("Skill 没有返回可用提示词");
    elements.reversePromptOutput.value = String(review.improvedPrompt).trim();
    const score = Number(review.scoreAfter || review.score || 0) || 0;
    elements.reversePromptStatus.textContent = `Seedance Skill 已精修${score ? ` · 评分 ${score}` : ""} · ${review.summary || "可发送到创作工作台"}`;
    showToast("片段反推 Prompt 已完成 Skill 精修");
  } catch (error) {
    elements.reversePromptStatus.textContent = `Skill 暂不可用，基础 Prompt 仍可使用：${error.message}`;
    showToast(error.message);
  } finally {
    setReversePromptBusy(false);
  }
}

async function copyReversePrompt() {
  const prompt = elements.reversePromptOutput?.value.trim();
  if (!prompt) {
    showToast("还没有可复制的提示词");
    return;
  }
  await navigator.clipboard.writeText(prompt);
  showToast("反推 Prompt 已复制");
}

function sendReversePromptToCreator() {
  const prompt = elements.reversePromptOutput?.value.trim();
  const item = state.reversePromptItem;
  const segment = state.reversePromptSegment;
  if (!prompt || !item || !segment) {
    showToast("还没有可发送的反推提示词");
    return;
  }
  const mode = reversePromptMode();
  window.localStorage.setItem(MATERIAL_REVERSE_PROMPT_DRAFT_KEY, JSON.stringify({
    prompt,
    brief: reversePromptEvidenceParts(item, segment).join("\n"),
    targetMarket: elements.reversePromptMarket?.value || "日本",
    contentLanguage: elements.reversePromptLanguage?.value || "日语",
    duration: reversePromptDuration(segment),
    ratio: "9:16",
    mode,
    refVideo: mode === "reference" ? item.url : "",
    materialId: item.id || "",
    materialName: item.name || materialDisplayName(item.url),
    segmentId: segment.id || "",
    startMs: Number(segment.startMs || 0) || 0,
    endMs: Number(segment.endMs || 0) || 0,
    createdAt: new Date().toISOString(),
  }));
  window.localStorage.setItem("seedanceWorkspaceViewV1", "create");
  window.location.assign("/index.html?workspace=create&source=material-reverse-prompt");
}

function optionsMarkup(options, selected) {
  return options.map((option) => `<option value="${escapeHtml(option.value)}"${option.value === String(selected) ? " selected" : ""}>${escapeHtml(option.label)}</option>`).join("");
}

function qualityLabel(score) {
  return score ? `${score} 分` : "未评分";
}

function frameIndexLabel(item) {
  const frameIndex = item.analysis?.frameIndex || {};
  const indexed = Number(frameIndex.indexedFrames || 0) || 0;
  const total = Number(frameIndex.totalFrames || 0) || 0;
  if (!indexed && !total) return "未建帧索引";
  return `帧索引 ${indexed}/${total || indexed}`;
}

function formatRangeMs(startMs, endMs) {
  const start = Math.max(0, Number(startMs || 0) || 0) / 1000;
  const end = Math.max(0, Number(endMs || 0) || 0) / 1000;
  return `${start.toFixed(start % 1 ? 1 : 0)}s-${end.toFixed(end % 1 ? 1 : 0)}s`;
}

function adProfileMarkup(item) {
  const profile = item.analysis?.adProfile || {};
  if (!profile.adScore && !profile.primaryStageLabel && !profile.contentSummary) return "";
  const strengths = Array.isArray(profile.strengths) ? profile.strengths.slice(0, 3) : [];
  const risks = Array.isArray(profile.risks) ? profile.risks.slice(0, 2) : [];
  const signals = Array.isArray(profile.productSignals) ? profile.productSignals.slice(0, 5) : [];
  return `
    <div class="material-ad-profile">
      <div class="material-ad-profile-head">
        <strong>${escapeHtml(profile.primaryStageLabel || "广告资产")}</strong>
        <span>${escapeHtml(profile.qualityTier ? `等级 ${profile.qualityTier}` : "待评级")} · ${escapeHtml(Math.round(Number(profile.adScore || 0) || 0))}分</span>
      </div>
      ${profile.contentSummary ? `<p>${escapeHtml(profile.contentSummary)}</p>` : ""}
      ${signals.length ? `<div class="material-ad-signal-row">${signals.map((signal) => `<span>${escapeHtml(signal)}</span>`).join("")}</div>` : ""}
      ${strengths.length ? `<div class="material-ad-note-row good">${strengths.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}</div>` : ""}
      ${risks.length ? `<div class="material-ad-note-row warn">${risks.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}</div>` : ""}
    </div>
  `;
}

function smartSegmentMarkup(item) {
  const segments = validSmartSegments(item).slice(0, 4);
  if (!segments.length) return "";
  return `
    <div class="material-smart-segments">
      <div class="material-smart-segments-head">
        <strong>智能拆分片段</strong>
        <span>${escapeHtml(segments.length)} / ${escapeHtml(item.analysis.segments.length)} 段</span>
      </div>
      <div class="material-smart-segment-list">
        ${segments.map((segment, index) => {
          const score = Math.round(Number(segment.score || 0) || 0);
          const marks = segmentMarksLabel(segment);
          return `
            <div class="material-smart-segment" data-segment-id="${escapeHtml(segment.id || `seg-${index + 1}`)}">
              <button type="button" data-action="preview-segment" data-segment-id="${escapeHtml(segment.id || `seg-${index + 1}`)}">
                <strong>${escapeHtml(formatRangeMs(segment.startMs, segment.endMs))}</strong>
                <span>${escapeHtml(score)}分 · ${escapeHtml(segment.adStageLabel || optionLabel(EDIT_ROLE_OPTIONS, segment.role || item.editRole))}</span>
                ${segment.contentDescription ? `<em>${escapeHtml(segment.contentDescription)}</em>` : marks ? `<em>每秒 ${escapeHtml(marks)}</em>` : ""}
                ${segment.copyAngle ? `<small>${escapeHtml(segment.copyAngle)}</small>` : ""}
              </button>
              <div class="material-smart-segment-actions">
                <button type="button" data-action="add-segment" data-segment-id="${escapeHtml(segment.id || `seg-${index + 1}`)}">加入</button>
                <button type="button" data-action="reverse-prompt" data-segment-id="${escapeHtml(segment.id || `seg-${index + 1}`)}">反推 Prompt</button>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function secondMarkToneLabel(tone) {
  const labels = {
    good: "高分可用",
    ok: "可用",
    warn: "需复核",
    bad: "不建议",
  };
  return labels[String(tone || "")] || "可用";
}

function secondMarkListText(value, fallback) {
  const list = Array.isArray(value) ? value.map((item) => String(item).trim()).filter(Boolean).slice(0, 3) : [];
  return list.length ? list.join("、") : fallback;
}

function secondMarkTone(mark) {
  const score = Number(mark?.score || 0) || 0;
  const tone = String(mark?.tone || "");
  if (tone === "bad" || score < 52) return "bad";
  if (tone === "warn" || score < 66) return "warn";
  if (tone === "good" || score >= 82) return "good";
  return "ok";
}

function secondTimelineLabel(value) {
  const labels = {
    opening: "开头",
    early: "前段",
    middle: "中段",
    late: "后段",
    ending: "尾段",
  };
  return labels[String(value || "")] || "";
}

function secondFocusGroups(marks, predicate, limit = 4) {
  const groups = [];
  let current = null;
  marks.forEach((mark) => {
    if (!predicate(mark)) {
      current = null;
      return;
    }
    const score = Math.round(Number(mark.score || 0) || 0);
    const note = String(mark.note || mark.visualNote || "").trim();
    if (current && Number(mark.startMs || 0) <= current.endMs + 80) {
      current.endMs = Number(mark.endMs || current.endMs) || current.endMs;
      current.count += 1;
      current.scoreTotal += score;
      if (note && !current.notes.includes(note)) current.notes.push(note);
      if (Array.isArray(mark.pros)) {
        mark.pros.forEach((item) => {
          const text = String(item || "").trim();
          if (text && !current.pros.includes(text)) current.pros.push(text);
        });
      }
      if (Array.isArray(mark.cons)) {
        mark.cons.forEach((item) => {
          const text = String(item || "").trim();
          if (text && !current.cons.includes(text)) current.cons.push(text);
        });
      }
      return;
    }
    current = {
      startMs: Number(mark.startMs || 0) || 0,
      endMs: Number(mark.endMs || 0) || 0,
      count: 1,
      scoreTotal: score,
      notes: note ? [note] : [],
      pros: Array.isArray(mark.pros) ? mark.pros.map((item) => String(item).trim()).filter(Boolean) : [],
      cons: Array.isArray(mark.cons) ? mark.cons.map((item) => String(item).trim()).filter(Boolean) : [],
    };
    groups.push(current);
  });
  return groups
    .map((group) => ({
      ...group,
      score: Math.round(group.scoreTotal / Math.max(1, group.count)),
      note: group.notes.slice(0, 2).join("、"),
      prosText: group.pros.slice(0, 2).join("、"),
      consText: group.cons.slice(0, 2).join("、"),
    }))
    .sort((a, b) => b.score - a.score || b.count - a.count)
    .slice(0, limit);
}

function secondFocusGroupMarkup(title, groups, tone, emptyText) {
  return `
    <div class="material-second-focus ${tone}">
      <strong>${escapeHtml(title)}</strong>
      ${groups.length ? groups.map((group) => `
        <button type="button" data-action="preview-second" data-start-ms="${escapeHtml(group.startMs)}">
          <b>${escapeHtml(formatRangeMs(group.startMs, group.endMs))} · ${escapeHtml(group.score)}分</b>
          <span>${escapeHtml(group.note || group.prosText || group.consText || "可预览确认")}</span>
        </button>
      `).join("") : `<span class="material-second-empty">${escapeHtml(emptyText)}</span>`}
    </div>
  `;
}

function secondAnalysisMarkup(item) {
  if (item.kind !== "video") return "";
  const marks = Array.isArray(item.analysis?.secondMarks)
    ? item.analysis.secondMarks
      .filter((mark) => mark && Number(mark.endMs || 0) > Number(mark.startMs || 0))
      .sort((a, b) => Number(a.startMs || 0) - Number(b.startMs || 0))
    : [];
  if (!marks.length) return "";
  const shown = marks.slice(0, 24);
  const highCount = marks.filter((mark) => Number(mark.score || 0) >= 78 || mark.tone === "good").length;
  const reviewCount = marks.filter((mark) => ["warn", "bad"].includes(mark.tone) || Number(mark.score || 0) < 66).length;
  const avgScore = Math.round(marks.reduce((sum, mark) => sum + (Number(mark.score || 0) || 0), 0) / marks.length);
  const sharpCount = marks.filter((mark) => Number(mark.sharpness || 0) >= 80 || String(mark.visualNote || "").includes("细节清晰")).length;
  const motionCount = marks.filter((mark) => Number(mark.visualMotion || 0) >= 18 || Number(mark.motionDelta || 0) >= 0.35).length;
  const bestGroups = secondFocusGroups(marks, (mark) => Number(mark.score || 0) >= 82 || mark.tone === "good");
  const riskGroups = secondFocusGroups(marks, (mark) => ["warn", "bad"].includes(mark.tone) || Number(mark.score || 0) < 66);
  const motionGroups = secondFocusGroups(marks, (mark) => Number(mark.visualMotion || 0) >= 18 || Number(mark.motionDelta || 0) >= 0.35);
  const timelineMarks = marks.slice(0, 120);
  return `
    <div class="material-second-analysis">
      <div class="material-second-analysis-head">
        <strong>秒级剪辑质检</strong>
        <span>${escapeHtml(marks.length)} 秒 · 均分 ${escapeHtml(avgScore)} · 高分 ${escapeHtml(highCount)} · 复核 ${escapeHtml(reviewCount)}</span>
      </div>
      <div class="material-second-scoreboard">
        <span><b>${escapeHtml(highCount)}</b><small>优先可用秒</small></span>
        <span><b>${escapeHtml(motionCount)}</b><small>节奏切点秒</small></span>
        <span><b>${escapeHtml(sharpCount)}</b><small>细节清晰秒</small></span>
        <span><b>${escapeHtml(reviewCount)}</b><small>短用/复核秒</small></span>
      </div>
      <div class="material-second-timeline" aria-label="秒级质量时间线">
        ${timelineMarks.map((mark) => {
          const tone = secondMarkTone(mark);
          const stage = secondTimelineLabel(mark.timelineZone);
          const score = Math.round(Number(mark.score || 0) || 0);
          const note = String(mark.note || mark.visualNote || "").trim();
          return `
            <button type="button" class="tone-${escapeHtml(tone)}" data-action="preview-second" data-start-ms="${escapeHtml(mark.startMs)}" title="${escapeHtml(formatRangeMs(mark.startMs, mark.endMs))} · ${escapeHtml(score)}分${stage ? ` · ${escapeHtml(stage)}` : ""}${note ? ` · ${escapeHtml(note)}` : ""}">
              <span style="height:${escapeHtml(Math.max(24, Math.min(100, score)))}%"></span>
            </button>
          `;
        }).join("")}
      </div>
      <div class="material-second-focus-grid">
        ${secondFocusGroupMarkup("优先使用", bestGroups, "good", "暂无明显高分秒段")}
        ${secondFocusGroupMarkup("节奏切点", motionGroups, "ok", "暂无明显动作切点")}
        ${secondFocusGroupMarkup("短用/避开", riskGroups, "warn", "暂无明显风险秒段")}
      </div>
      <details class="material-second-details">
        <summary>查看逐秒明细 · 前 ${escapeHtml(shown.length)} 秒</summary>
        <div class="material-second-list">
          ${shown.map((mark) => {
            const tone = secondMarkTone(mark);
          const score = Math.round(Number(mark.score || 0) || 0);
          const note = String(mark.note || mark.visualNote || "").trim();
          const pros = secondMarkListText(mark.pros, "暂无明显优点");
          const cons = secondMarkListText(mark.cons, "暂无明显缺点");
          const advice = String(mark.cutAdvice || mark.note || "建议结合相邻秒片段预览后使用。").slice(0, 120);
          return `
            <button type="button" class="material-second-item tone-${escapeHtml(tone)}" data-action="preview-second" data-start-ms="${escapeHtml(mark.startMs)}">
              <span>${escapeHtml(formatRangeMs(mark.startMs, mark.endMs))} · ${escapeHtml(score)}分 · ${escapeHtml(secondMarkToneLabel(tone))}${note ? ` · ${escapeHtml(note)}` : ""}</span>
              <strong>优点：${escapeHtml(pros)}</strong>
              <em>缺点：${escapeHtml(cons)}</em>
              <small>${escapeHtml(advice)}</small>
            </button>
          `;
          }).join("")}
        </div>
      </details>
      ${marks.length > shown.length ? `<small class="material-second-more">已显示前 ${escapeHtml(shown.length)} 秒，完整逐秒数据已写入 Obsidian。</small>` : ""}
    </div>
  `;
}

function analysisAdviceMarkup(item) {
  if (item.kind !== "video") return "";
  const summary = String(item.analysis?.summary || "").trim();
  const suggestions = Array.isArray(item.analysis?.suggestions) ? item.analysis.suggestions.filter(Boolean).slice(0, 3) : [];
  const cutHints = Array.isArray(item.analysis?.cutHints) ? item.analysis.cutHints.filter((hint) => hint && hint.endMs > hint.startMs).slice(0, 2) : [];
  const adMarkup = adProfileMarkup(item);
  const segmentMarkup = smartSegmentMarkup(item);
  const secondMarkup = secondAnalysisMarkup(item);
  if (!summary && !suggestions.length && !cutHints.length && !adMarkup && !segmentMarkup && !secondMarkup) return "";
  return `
    <div class="material-advice-panel">
      <div class="material-advice-head">
        <strong>Skill 分析建议</strong>
        ${item.analysis?.updatedAt ? `<span>${escapeHtml(formatDate(item.analysis.updatedAt))}</span>` : ""}
      </div>
      ${summary ? `<p>${escapeHtml(summary)}</p>` : ""}
      ${adMarkup}
      ${suggestions.length ? `<ul>${suggestions.map((suggestion) => `<li>${escapeHtml(suggestion)}</li>`).join("")}</ul>` : ""}
      ${cutHints.length ? `
        <div class="material-cut-hints">
          ${cutHints.map((hint) => `
            <span>${escapeHtml(formatRangeMs(hint.startMs, hint.endMs))} · ${escapeHtml(hint.role || "clip")} · ${escapeHtml(hint.reason || "自动剪辑候选段")}</span>
          `).join("")}
        </div>
      ` : ""}
      ${secondMarkup}
      ${segmentMarkup}
    </div>
  `;
}

function analysisAssetUrl(path) {
  const cleanPath = String(path || "").replace(/\\/g, "/").replace(/^\/+/, "");
  if (!cleanPath || !cleanPath.startsWith("analysis/")) return "";
  return `/analysis-assets/${encodeURIComponent(cleanPath)}`;
}

function keyframePreviewMarkup(item) {
  if (item.kind !== "video") return "";
  const keyframes = Array.isArray(item.analysis?.keyframes)
    ? item.analysis.keyframes
      .map((frame) => ({ ...frame, src: analysisAssetUrl(frame?.path) }))
      .filter((frame) => frame.src)
      .slice(0, 4)
    : [];
  if (!keyframes.length) return "";
  return `
    <div class="material-keyframes" aria-label="抽帧预览">
      <div class="material-keyframe-head">
        <strong>抽帧预览</strong>
        <span>${escapeHtml(keyframes.length)} / ${escapeHtml(item.analysis.keyframes.length)} 帧</span>
      </div>
      <div class="material-keyframe-strip">
        ${keyframes.map((frame) => `
          <button type="button" data-action="preview-video" title="${escapeHtml(formatDurationMs(frame.timeMs) || "关键帧")}">
            <img src="${escapeHtml(frame.src)}" alt="${escapeHtml(item.name || materialDisplayName(item.url))} ${escapeHtml(formatDurationMs(frame.timeMs) || "")}" loading="lazy">
            <span>${escapeHtml(formatDurationMs(frame.timeMs) || "")}</span>
          </button>
        `).join("")}
      </div>
    </div>
  `;
}

function videoHealthMarkup(item) {
  const warnings = videoHealthWarnings(item);
  if (!warnings.length) return "";
  const isFatal = isInvalidVideo(item);
  return `
    <div class="material-health-alert ${isFatal ? "is-invalid" : "is-warning"}">
      <strong>${isFatal ? "问题素材" : "分析提醒"}</strong>
      <span>${escapeHtml(warnings.join(" · "))}</span>
    </div>
  `;
}

function renderAssetList(items, totalCount) {
  if (!totalCount) {
    elements.assetList.innerHTML = `
      <article class="asset-batch-empty">
        <strong>暂无视频素材</strong>
        <small>上传视频，或导入视频 URL 后再进行 AI 分帧分析。</small>
      </article>
    `;
    return;
  }
  if (!items.length) {
    elements.assetList.innerHTML = `
      <article class="asset-batch-empty">
        <strong>没有匹配视频</strong>
        <small>调整批次、标签、状态、用途或搜索条件。</small>
      </article>
    `;
    return;
  }

  elements.assetList.innerHTML = "";
  const batchOptions = state.library.batches
    .map((batch) => `<option value="${escapeHtml(batch.id)}">${escapeHtml(batch.name)}</option>`)
    .join("");

  items.forEach((item) => {
    const row = document.createElement("article");
    row.className = `material-asset-card ${item.kind} status-${item.analysisStatus} ${isInvalidVideo(item) ? "is-invalid-video" : ""}`;
    const technical = technicalChips(item);
    const smart = smartEditSignal(item);
    const segmentCount = validSmartSegments(item).length;
    row.innerHTML = `
      <div class="material-asset-preview">${previewMarkup(item)}</div>
      <div class="material-asset-body">
        <div class="material-asset-title">
          <strong>${escapeHtml(item.name || materialDisplayName(item.url))}</strong>
          <span>${escapeHtml(kindLabel(item.kind))}</span>
          <span class="material-status-chip status-${escapeHtml(item.analysisStatus)}">${escapeHtml(optionLabel(ANALYSIS_STATUS_OPTIONS, item.analysisStatus))}</span>
        </div>
        <small>${escapeHtml(batchName(item.batchId))}${item.size ? ` · ${escapeHtml(formatBytes(item.size))}` : ""}${item.addedAt ? ` · ${escapeHtml(formatDate(item.addedAt))}` : ""}</small>
        <div class="material-analysis-strip">
          <span>${escapeHtml(optionLabel(EDIT_ROLE_OPTIONS, item.editRole))}</span>
          <span>${escapeHtml(optionLabel(PRIORITY_OPTIONS, item.priority))}</span>
          <span>${escapeHtml(qualityLabel(item.qualityScore))}</span>
          <span>${escapeHtml(smart.eligible ? `智能分 ${smart.smartScore}` : `待优化 ${smart.smartScore}`)}</span>
          <span>${item.analysis?.frameCount ? `${escapeHtml(item.analysis.frameCount)} 帧` : "未抽帧"}</span>
          <span>${segmentCount ? `${escapeHtml(segmentCount)} 智能片段` : "未拆片段"}</span>
          <span>${escapeHtml(frameIndexLabel(item))}</span>
        </div>
        ${videoHealthMarkup(item)}
        ${technical.length ? `<div class="material-analysis-strip material-technical-strip">${technical.map((chip) => `<span>${escapeHtml(chip)}</span>`).join("")}</div>` : ""}
        ${item.aiTags?.length ? `<div class="material-analysis-strip material-ai-tag-strip">${item.aiTags.map((tag) => `<span>#AI/${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
        ${analysisAdviceMarkup(item)}
        ${keyframePreviewMarkup(item)}
        <div class="asset-batch-tags">
          ${item.tags.length ? item.tags.map((tag) => `<button type="button" data-action="remove-tag" data-tag="${escapeHtml(tag)}">#${escapeHtml(tag)}</button>`).join("") : "<span>未打标签</span>"}
        </div>
        ${item.notes ? `<p class="material-notes">${escapeHtml(item.notes)}</p>` : ""}
        ${item.sourceUrl ? `<p>云盘来源：${escapeHtml(item.sourceUrl)}</p>` : ""}
        ${item.sourcePath || item.externalPath ? `<p>NAS 来源：${escapeHtml(item.sourcePath || item.externalPath)}</p>` : ""}
        <p>${escapeHtml(item.url)}</p>
      </div>
      <div class="material-asset-controls">
        <label>
          <span>批次</span>
          <select data-field="batchId" aria-label="素材所属批次">
            <option value="">未分批</option>
            ${batchOptions}
          </select>
        </label>
        <label>
          <span>状态</span>
          <select data-field="analysisStatus" aria-label="素材分析状态">
            ${optionsMarkup(ANALYSIS_STATUS_OPTIONS, item.analysisStatus)}
          </select>
        </label>
        <label>
          <span>用途</span>
          <select data-field="editRole" aria-label="素材剪辑用途">
            ${optionsMarkup(EDIT_ROLE_OPTIONS, item.editRole)}
          </select>
        </label>
        <div class="material-control-grid">
          <label>
            <span>优先</span>
            <select data-field="priority" aria-label="素材优先级">
              ${optionsMarkup(PRIORITY_OPTIONS, item.priority)}
            </select>
          </label>
          <label>
            <span>评分</span>
            <select data-field="qualityScore" aria-label="素材质量评分">
              ${optionsMarkup(QUALITY_SCORE_OPTIONS, item.qualityScore)}
            </select>
          </label>
        </div>
        <input class="material-note-input" data-field="notes" type="text" maxlength="160" aria-label="剪辑备注" placeholder="剪辑备注" value="${escapeHtml(item.notes || "")}">
        <div class="asset-batch-row-actions">
          ${item.kind === "video" ? `<button type="button" data-action="preview-video">播放</button>` : ""}
          ${item.kind === "video" ? `<button type="button" data-action="add-manual-clip">${segmentCount ? "加入最佳片段" : "加入剪辑"}</button>` : ""}
          <button type="button" data-action="tag">打标签</button>
          <button type="button" data-action="copy">复制</button>
          <button type="button" data-action="remove">移除</button>
        </div>
      </div>
    `;
    const batchSelect = row.querySelector('[data-field="batchId"]');
    batchSelect.value = item.batchId;
    batchSelect.addEventListener("change", () => {
      upsertItem(item.url, { batchId: batchSelect.value });
      saveLibrary();
      render();
      showToast(batchSelect.value ? "素材批次已更新" : "素材已设为未分批");
    });
    row.querySelector('[data-field="analysisStatus"]').addEventListener("change", (event) => {
      upsertItem(item.url, { analysisStatus: event.currentTarget.value });
      saveLibrary();
      render();
      showToast("分析状态已更新");
    });
    row.querySelector('[data-field="editRole"]').addEventListener("change", (event) => {
      upsertItem(item.url, { editRole: event.currentTarget.value });
      saveLibrary();
      render();
      showToast("剪辑用途已更新");
    });
    row.querySelector('[data-field="priority"]').addEventListener("change", (event) => {
      upsertItem(item.url, { priority: event.currentTarget.value });
      saveLibrary();
      render();
      showToast("优先级已更新");
    });
    row.querySelector('[data-field="qualityScore"]').addEventListener("change", (event) => {
      upsertItem(item.url, { qualityScore: event.currentTarget.value });
      saveLibrary();
      render();
      showToast("质量评分已更新");
    });
    row.querySelector('[data-field="notes"]').addEventListener("change", (event) => {
      upsertItem(item.url, { notes: event.currentTarget.value });
      saveLibrary();
      render();
      showToast("剪辑备注已保存");
    });
    row.querySelectorAll('[data-action="preview-video"]').forEach((button) => {
      button.addEventListener("click", () => openVideoLightbox(item));
    });
    row.querySelector('[data-action="add-manual-clip"]')?.addEventListener("click", () => addManualClip(item));
    row.querySelectorAll('[data-action="preview-segment"]').forEach((button) => {
      button.addEventListener("click", () => {
        const segment = findSmartSegment(item, { id: button.dataset.segmentId });
        openVideoLightbox(item, segment?.startMs || 0);
      });
    });
    row.querySelectorAll('[data-action="preview-second"]').forEach((button) => {
      button.addEventListener("click", () => {
        openVideoLightbox(item, Number(button.dataset.startMs || 0) || 0);
      });
    });
    row.querySelectorAll('[data-action="add-segment"]').forEach((button) => {
      button.addEventListener("click", () => {
        const segment = findSmartSegment(item, { id: button.dataset.segmentId });
        addManualSegment(item, segment);
      });
    });
    row.querySelectorAll('[data-action="reverse-prompt"]').forEach((button) => {
      button.addEventListener("click", () => {
        const segment = findSmartSegment(item, { id: button.dataset.segmentId });
        openReversePromptDialog(item, segment);
      });
    });
    row.querySelector('[data-action="tag"]').addEventListener("click", () => {
      const tags = tagInputTags();
      if (!tags.length) {
        showToast("先输入标签");
        return;
      }
      upsertItem(item.url, { tags: [...new Set([...(item.tags || []), ...tags])], batchId: item.batchId || activeBatch().id, kind: item.kind });
      saveLibrary();
      render();
      showToast("标签已更新");
    });
    row.querySelector('[data-action="copy"]').addEventListener("click", async () => {
      await navigator.clipboard.writeText(item.url);
      showToast("素材 URL 已复制");
    });
    row.querySelector('[data-action="remove"]').addEventListener("click", () => {
      delete state.library.items[item.url];
      removeManualClipsForUrl(item.url);
      saveLibrary();
      render();
      showToast("素材记录已移除");
    });
    row.querySelectorAll('[data-action="remove-tag"]').forEach((button) => {
      button.addEventListener("click", () => {
        upsertItem(item.url, { tags: item.tags.filter((tag) => tag !== button.dataset.tag), batchId: item.batchId, kind: item.kind });
        saveLibrary();
        render();
        showToast(`#${button.dataset.tag} 已移除`);
      });
    });
    elements.assetList.appendChild(row);
  });
}

function createBatch() {
  const batch = makeBatch(elements.batchNameInput.value);
  state.library.batches.unshift(batch);
  state.library.activeId = batch.id;
  state.library.filterBatchId = batch.id;
  saveLibrary();
  render();
  showToast(`已新建「${batch.name}」`);
}

function renameBatch() {
  const batch = activeBatch();
  const name = elements.batchNameInput.value.trim().slice(0, 40);
  if (!name) {
    showToast("批次名称不能为空");
    return;
  }
  batch.name = name;
  saveLibrary();
  render();
  showToast("批次名称已保存");
}

function deleteEmptyBatch() {
  const batch = activeBatch();
  const hasItems = entries().some((item) => item.batchId === batch.id);
  if (hasItems) {
    showToast("当前批次还有素材，先移动或移除素材");
    return;
  }
  if (state.library.batches.length <= 1) {
    batch.name = "默认批次";
    saveLibrary();
    render();
    showToast("已保留最后一个默认批次");
    return;
  }
  state.library.batches = state.library.batches.filter((item) => item.id !== batch.id);
  state.library.activeId = state.library.batches[0].id;
  if (state.library.filterBatchId === batch.id || state.library.filterBatchId === "current") {
    state.library.filterBatchId = "all";
  }
  saveLibrary();
  render();
  showToast("空批次已删除");
}

function applyTagsToActiveBatch(tags = tagInputTags()) {
  const nextTags = splitTags(tags);
  if (!nextTags.length) {
    showToast("先输入标签");
    return;
  }
  const batch = activeBatch();
  const targets = entries().filter((item) => item.batchId === batch.id);
  if (!targets.length) {
    elements.tagInput.value = nextTags.join("、");
    showToast("当前批次暂无素材");
    return;
  }
  targets.forEach((item) => {
    upsertItem(item.url, { tags: [...new Set([...(item.tags || []), ...nextTags])], batchId: batch.id, kind: item.kind });
  });
  saveLibrary();
  render();
  showToast(`已给 ${targets.length} 个素材打标签`);
}

function applyWorkflowToActiveBatch() {
  const patch = {};
  if (elements.bulkStatusSelect.value) patch.analysisStatus = elements.bulkStatusSelect.value;
  if (elements.bulkRoleSelect.value) patch.editRole = elements.bulkRoleSelect.value;
  if (elements.bulkPrioritySelect.value) patch.priority = elements.bulkPrioritySelect.value;
  if (!Object.keys(patch).length) {
    showToast("先选择要批量修改的状态、用途或优先级");
    return;
  }
  const batch = activeBatch();
  const targets = entries().filter((item) => item.batchId === batch.id);
  if (!targets.length) {
    showToast("当前批次暂无素材");
    return;
  }
  targets.forEach((item) => upsertItem(item.url, patch));
  saveLibrary();
  render();
  showToast(`已更新 ${targets.length} 个素材的剪辑准备字段`);
}

function setRemoteImportBusy(isBusy) {
  state.remoteImportRunning = isBusy;
  if (!elements.importUrlsBtn) return;
  elements.importUrlsBtn.disabled = isBusy;
  elements.importUrlsBtn.textContent = isBusy ? "导入中..." : "导入云盘并分析";
}

function setFolderImportBusy(isBusy) {
  state.folderImportRunning = isBusy;
  if (!elements.importFolderBtn) return;
  elements.importFolderBtn.disabled = isBusy;
  elements.importFolderBtn.textContent = isBusy ? "识别中..." : "引用 NAS 并分析";
}

async function importUrls() {
  const urls = parseUrlList(elements.urlImportInput.value);
  if (!urls.length) {
    showToast("先粘贴共享云盘地址或视频直链");
    return;
  }
  const batch = activeBatch();
  const tags = tagInputTags();
  setRemoteImportBusy(true);
  elements.analysisStatus.textContent = "正在从共享云盘导入视频，完成后会写入 Obsidian 并触发分析...";
  try {
    const payload = await requestJson("/api/material-library/import-remote", {
      method: "POST",
      body: JSON.stringify({
        urls,
        batchId: batch.id,
        tags,
        analyze: true,
      }),
    });
    state.library = normalizeLibrary(payload.library || state.library);
    state.obsidian = payload.obsidian || state.obsidian;
    if (batchExists(batch.id)) state.library.filterBatchId = batch.id;
    window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(state.library));
    elements.urlImportInput.value = "";
    render();

    const imported = Array.isArray(payload.imported) ? payload.imported.length : 0;
    const skipped = Array.isArray(payload.skipped) ? payload.skipped.length : 0;
    const failures = Array.isArray(payload.failures) ? payload.failures.length : 0;
    const result = payload.analysis?.result || {};
    const analyzed = Array.isArray(result.analyzed) ? result.analyzed.length : 0;
    const analysisFailures = Array.isArray(result.failures) ? result.failures.length : 0;
    const parts = [`导入 ${imported}`, `跳过 ${skipped}`, `失败 ${failures}`, `分析 ${analyzed}`];
    if (analysisFailures) parts.push(`待复核 ${analysisFailures}`);
    if (payload.analysisError) parts.push("分析未完成");
    elements.analysisStatus.textContent = `云盘导入完成：${parts.join(" · ")}${payload.analysisError ? ` · ${payload.analysisError}` : ""}`;
    showToast(`云盘导入完成：已入库 ${imported} 个视频`);
  } catch (error) {
    elements.analysisStatus.textContent = `云盘导入失败：${error.message}`;
    showToast(error.message);
  } finally {
    setRemoteImportBusy(false);
  }
}

async function importLocalFolders() {
  const paths = parsePathList(elements.localFolderInput.value);
  if (!paths.length) {
    showToast("先粘贴 NAS 或本地视频文件夹路径");
    return;
  }
  const batch = activeBatch();
  const tags = tagInputTags();
  setFolderImportBusy(true);
  elements.analysisStatus.textContent = "正在登记 NAS 视频引用，不复制原视频；随后会先分析一批素材...";
  try {
    const payload = await requestJson("/api/material-library/import-local-folder", {
      method: "POST",
      body: JSON.stringify({
        paths,
        batchId: batch.id,
        tags,
        analyze: true,
      }),
    });
    state.library = normalizeLibrary(payload.library || state.library);
    state.obsidian = payload.obsidian || state.obsidian;
    if (batchExists(batch.id)) state.library.filterBatchId = batch.id;
    window.localStorage.setItem(ASSET_BATCH_KEY, JSON.stringify(state.library));
    elements.localFolderInput.value = "";
    render();

    const imported = Array.isArray(payload.imported) ? payload.imported.length : 0;
    const skipped = Array.isArray(payload.skipped) ? payload.skipped.length : 0;
    const failures = Array.isArray(payload.failures) ? payload.failures.length : 0;
    const result = payload.analysis?.result || {};
    const analyzed = Array.isArray(result.analyzed) ? result.analyzed.length : 0;
    const analysisFailures = Array.isArray(result.failures) ? result.failures.length : 0;
    const parts = [`登记 ${imported}`, `跳过 ${skipped}`, `失败 ${failures}`, `分析 ${analyzed}`];
    if (analysisFailures) parts.push(`待复核 ${analysisFailures}`);
    if (payload.analysisError) parts.push("分析未完成");
    elements.analysisStatus.textContent = `NAS 引用导入完成：${parts.join(" · ")}${payload.analysisError ? ` · ${payload.analysisError}` : ""}`;
    showToast(`NAS 已入库 ${imported} 个视频，不复制原文件`);
  } catch (error) {
    elements.analysisStatus.textContent = `NAS 引用导入失败：${error.message}`;
    showToast(error.message);
  } finally {
    setFolderImportBusy(false);
  }
}

function filterUploadFiles(fileList, config) {
  return [...(fileList || [])].filter((file) => {
    const type = String(file?.type || "").toLowerCase();
    const name = String(file?.name || "").toLowerCase();
    return type.startsWith(config.fileTypePrefix) || config.extensions.some((extension) => name.endsWith(extension));
  });
}

function uploadKindForFile(file) {
  const type = String(file?.type || "").toLowerCase();
  const name = String(file?.name || "").toLowerCase();
  return Object.entries(UPLOAD_CONFIGS).find(([, config]) => type.startsWith(config.fileTypePrefix) || config.extensions.some((extension) => name.endsWith(extension)))?.[0] || "";
}

async function uploadFileGroup(kind, files) {
  const config = UPLOAD_CONFIGS[kind];
  const formData = new FormData();
  files.forEach((file) => formData.append(config.fieldName, file));
  const response = await fetch(config.endpoint, { method: "POST", body: formData });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `上传失败：${response.status}`);
  }
  const materials = Array.isArray(payload[config.responseKey]) ? payload[config.responseKey] : Array.isArray(payload.items) ? payload.items : [];
  const batch = activeBatch();
  const tags = tagInputTags();
  materials.forEach((material) => {
    if (!material?.url) return;
    upsertItem(material.url, {
      batchId: batch.id,
      tags: [...new Set([...(state.library.items[material.url]?.tags || []), ...tags])],
      kind,
      name: material.name || materialDisplayName(material.url),
      size: material.size,
      contentType: material.contentType,
      localPath: material.localPath,
      obsidianPath: material.obsidianPath,
      technical: material.technical,
      addedAt: new Date().toISOString(),
    });
  });
  return { count: materials.length, warning: payload.warning || "" };
}

async function uploadFiles(kind, fileList, refs) {
  const config = UPLOAD_CONFIGS[kind];
  const files = filterUploadFiles(fileList, config);
  if (!files.length) {
    showToast(config.emptyMessage);
    return;
  }
  const originalText = refs.button.textContent;
  refs.button.disabled = true;
  refs.button.textContent = config.uploadingText;
  refs.zone.classList.add("uploading");
  try {
    const result = await uploadFileGroup(kind, files);
    state.library.filterBatchId = activeBatch().id;
    saveLibrary();
    render();
    showToast(result.warning || config.doneText(result.count));
  } catch (error) {
    showToast(error.message);
  } finally {
    refs.button.disabled = false;
    refs.button.textContent = originalText;
    refs.zone.classList.remove("uploading", "drag-over");
    refs.input.value = "";
  }
}

async function uploadMixedFiles(fileList, refs) {
  const groups = { video: [] };
  let skipped = 0;
  [...(fileList || [])].forEach((file) => {
    const kind = uploadKindForFile(file);
    if (kind && groups[kind]) groups[kind].push(file);
    else skipped += 1;
  });
  if (!groups.video.length) {
    showToast("请选择视频文件：MP4 / MOV / WebM / M4V");
    return;
  }

  const originalText = refs.button.textContent;
  refs.button.disabled = true;
  refs.button.textContent = "上传中";
  refs.zone.classList.add("uploading");
  try {
    const result = await uploadFileGroup("video", groups.video);
    state.library.filterBatchId = activeBatch().id;
    saveLibrary();
    render();
    showToast(skipped ? `已上传 ${result.count} 个视频，跳过 ${skipped} 个非视频文件` : (result.warning || `已上传 ${result.count} 个视频`));
  } catch (error) {
    showToast(error.message);
  } finally {
    refs.button.disabled = false;
    refs.button.textContent = originalText;
    refs.zone.classList.remove("uploading", "drag-over");
    refs.input.value = "";
  }
}

function bindUploadZone(kind, refs) {
  if (!refs.zone || !refs.button || !refs.input) return;
  refs.button.addEventListener("click", (event) => {
    event.stopPropagation();
    refs.input.click();
  });
  refs.zone.addEventListener("click", () => refs.input.click());
  refs.zone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      refs.input.click();
    }
  });
  refs.input.addEventListener("change", () => uploadFiles(kind, refs.input.files, refs));
  ["dragenter", "dragover"].forEach((eventName) => {
    refs.zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      refs.zone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    refs.zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      refs.zone.classList.remove("drag-over");
    });
  });
  refs.zone.addEventListener("drop", (event) => uploadFiles(kind, event.dataTransfer.files, refs));
}

function bindMixedUploadZone(refs) {
  if (!refs.zone || !refs.button || !refs.input) return;
  refs.button.addEventListener("click", (event) => {
    event.stopPropagation();
    refs.input.click();
  });
  refs.zone.addEventListener("click", () => refs.input.click());
  refs.zone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      refs.input.click();
    }
  });
  refs.input.addEventListener("change", () => uploadMixedFiles(refs.input.files, refs));
  ["dragenter", "dragover"].forEach((eventName) => {
    refs.zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      refs.zone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    refs.zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      refs.zone.classList.remove("drag-over");
    });
  });
  refs.zone.addEventListener("drop", (event) => uploadMixedFiles(event.dataTransfer.files, refs));
}

function clearFilters({ persist = true, toast = true } = {}) {
  state.library.filterBatchId = "all";
  state.library.filterTag = "all";
  state.kindFilter = "video";
  state.statusFilter = "all";
  state.roleFilter = "all";
  state.search = "";
  elements.statusFilterSelect.value = "all";
  elements.roleFilterSelect.value = "all";
  elements.searchInput.value = "";
  if (persist) saveLibrary();
  render();
  if (toast) showToast("筛选已清除");
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 2600);
}

function applyCopyLibraryDraft() {
  let draft = null;
  try {
    draft = JSON.parse(window.sessionStorage.getItem("seedanceCopyLibraryDraft") || "null");
  } catch {
    draft = null;
  }
  if (!draft || typeof draft !== "object" || !String(draft.script || "").trim()) return;
  if (elements.draftCopyInput) elements.draftCopyInput.value = String(draft.script || "").trim();
  if (elements.productNameInput && !elements.productNameInput.value.trim() && String(draft.product || "").trim()) {
    elements.productNameInput.value = String(draft.product || "").trim();
  }
  const shotSegments = Array.isArray(draft.analysis?.segments) ? draft.analysis.segments : [];
  const materialTags = [...new Set(shotSegments.flatMap((segment) => Array.isArray(segment.materialTags) ? segment.materialTags : []).filter(Boolean))];
  if (elements.productSellingPointsInput && !elements.productSellingPointsInput.value.trim() && materialTags.length) {
    elements.productSellingPointsInput.value = materialTags.join("、");
  }
  if (shotSegments.length) {
    window.localStorage.setItem("seedanceActiveCopyShotPlan", JSON.stringify({
      copyId: draft.id || "",
      title: draft.title || "",
      segments: shotSegments,
      updatedAt: new Date().toISOString(),
    }));
  }
  window.sessionStorage.removeItem("seedanceCopyLibraryDraft");
  if (elements.jianyingDraftStatus) {
    const shotInfo = shotSegments.length ? ` · ${shotSegments.length} 个 AI 分镜` : "";
    elements.jianyingDraftStatus.textContent = `已载入视频文案库：${draft.title || "未命名文案"} · ${draft.duration || 15} 秒${shotInfo}。现在可按每句文案和素材标签选择对应片段，再生成剪映草稿。`;
  }
  window.setTimeout(() => showToast("已将文案库脚本带入素材混剪"), 100);
}

function updateBackToTopButton() {
  if (!elements.backToTopBtn) return;
  const shouldShow = window.scrollY > 520;
  elements.backToTopBtn.classList.toggle("show", shouldShow);
  elements.backToTopBtn.setAttribute("aria-hidden", shouldShow ? "false" : "true");
  elements.backToTopBtn.tabIndex = shouldShow ? 0 : -1;
}

function scrollToPageTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
  window.setTimeout(updateBackToTopButton, 320);
}

function jumpToMaterialSection(link, event) {
  const selector = String(link?.getAttribute("href") || "");
  if (!selector.startsWith("#")) return;
  const target = document.querySelector(selector);
  if (!target) return;
  event?.preventDefault();
  window.history.replaceState(null, "", selector);
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  document.querySelectorAll(".material-section-nav a.is-jump-active").forEach((item) => item.classList.remove("is-jump-active"));
  link.classList.add("is-jump-active");
  target.classList.remove("is-section-jump");
  window.requestAnimationFrame(() => {
    target.classList.add("is-section-jump");
    window.setTimeout(() => {
      target.classList.remove("is-section-jump");
      link.classList.remove("is-jump-active");
    }, 1400);
  });
}

function bindEvents() {
  elements.workflowNextBtn?.addEventListener("click", () => runWorkflowAction(elements.workflowNextBtn.dataset.workflowAction || "upload"));
  elements.workflowSteps?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-step]");
    if (!button) return;
    if (button.dataset.action) runWorkflowAction(button.dataset.action);
    else if (button.dataset.target) focusWorkflowTarget(button.dataset.target);
  });
  elements.refreshBtn.addEventListener("click", () => {
    loadLibrary().then(() => showToast("已从 Obsidian 刷新素材库"));
  });
  elements.backToTopBtn?.addEventListener("click", scrollToPageTop);
  window.addEventListener("scroll", updateBackToTopButton, { passive: true });
  document.querySelectorAll('.material-section-nav a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (event) => jumpToMaterialSection(link, event));
  });
  elements.currentBatchSelect.addEventListener("change", () => {
    if (!batchExists(elements.currentBatchSelect.value)) return;
    state.library.activeId = elements.currentBatchSelect.value;
    state.library.filterBatchId = elements.currentBatchSelect.value;
    saveLibrary();
    render();
  });
  elements.newBatchBtn.addEventListener("click", createBatch);
  elements.renameBatchBtn.addEventListener("click", renameBatch);
  elements.deleteEmptyBatchBtn.addEventListener("click", deleteEmptyBatch);
  elements.clearLibraryBtn?.addEventListener("click", clearMaterialLibrary);
  elements.applyCurrentTagsBtn.addEventListener("click", () => applyTagsToActiveBatch());
  elements.applyWorkflowBtn.addEventListener("click", applyWorkflowToActiveBatch);
  elements.syncUploadsBtn.addEventListener("click", () => runMaterialAnalysis({ syncOnly: true }));
  elements.analyzeQueuedBtn.addEventListener("click", () => runMaterialAnalysis());
  elements.analyzeForceBtn.addEventListener("click", () => runMaterialAnalysis({ force: true }));
  elements.clearAnalysisQueueBtn?.addEventListener("click", () => {
    state.analysisQueue = [];
    saveAnalysisQueue();
    renderAnalysisQueue();
    showToast("分析任务记录已清空");
  });
  elements.showAutoPoolBtn.addEventListener("click", () => applyWorkbenchFilter({ status: "all", kind: "video", search: "自动混剪候选池" }));
  elements.generateJianyingDraftBtn.addEventListener("click", generateJianyingDraft);
  elements.chatcutSyncSubmitBtn?.addEventListener("click", submitChatCutSyncRequest);
  elements.chatcutSyncRefreshBtn?.addEventListener("click", () => loadChatCutSync());
  elements.chatcutEmbedReloadBtn?.addEventListener("click", () => updateChatCutEmbed({ force: true }));
  elements.chatcutEmbedFrame?.addEventListener("load", () => {
    if (elements.chatcutEmbedStatus) elements.chatcutEmbedStatus.textContent = "ChatCut 页面已加载；如显示登录页，请先在窗口内登录";
  });
  elements.chatcutSyncScopeSelect?.addEventListener("change", () => {
    saveChatCutSyncPreferences();
    render();
  });
  elements.chatcutProjectUrlInput?.addEventListener("change", () => {
    saveChatCutSyncPreferences();
    updateChatCutEmbed({ force: true });
  });
  elements.chatcutProductKeyInput?.addEventListener("change", saveChatCutSyncPreferences);
  elements.generateProductFilmBtn?.addEventListener("click", generateProductFilmDraft);
  elements.exportRoughCutBtn?.addEventListener("click", exportProductRoughCut);
  elements.restoreProductDraftBtn?.addEventListener("click", () => restoreProductDraft());
  elements.clearProductDraftBtn?.addEventListener("click", clearProductDraft);
  elements.refreshDirectionMonitorBtn?.addEventListener("click", () => refreshDirectionMonitor());
  elements.applyDirectionPlanBtn?.addEventListener("click", applyDirectionPlan);
  elements.productDurationSelect?.addEventListener("change", () => {
    state.directorClipLimit = 0;
    scheduleProductDraftSave();
    render();
  });
  elements.productScopeSelect?.addEventListener("change", () => {
    state.directorClipLimit = 0;
    scheduleProductDraftSave();
    render();
  });
  elements.productStyleSelect?.addEventListener("change", () => {
    state.directorClipLimit = 0;
    scheduleProductDraftSave();
    render();
  });
  elements.editPaceSelect?.addEventListener("change", () => { scheduleProductDraftSave(); render(); });
  elements.transitionStyleSelect?.addEventListener("change", () => { scheduleProductDraftSave(); render(); });
  elements.captionStyleSelect?.addEventListener("change", () => { scheduleProductDraftSave(); render(); });
  elements.productNameInput?.addEventListener("input", () => { scheduleProductDraftSave(); render(); });
  elements.productSellingPointsInput?.addEventListener("input", () => {
    state.productPrecutSignature = "";
    clearProductFilmCopyOverrides();
    scheduleProductDraftSave();
    render();
  });
  elements.copyAutofitBtn?.addEventListener("click", autofitProductCopy);
  elements.matchPrecutBtn?.addEventListener("click", prepareProductPrecut);
  elements.draftCopyInput?.addEventListener("input", () => {
    clearProductFilmCopyOverrides();
    scheduleProductDraftSave();
    render();
  });
  elements.clearManualClipsBtn?.addEventListener("click", () => {
    state.manualClips = [];
    state.selectedManualClipId = "";
    saveManualClipSelection();
    render();
    showToast("手动剪辑片段已清空");
  });
  elements.manualSourceSelect?.addEventListener("change", () => {
    state.manualSourceUrl = elements.manualSourceSelect.value;
    syncManualSourceWorkspace(entries(), true);
  });
  elements.manualSourcePlayer?.addEventListener("loadstart", () => {
    const item = activeManualSourceItem();
    if (item) setManualSourceStatus(manualSourceLoadingMessage(item), "loading");
  });
  elements.manualSourcePlayer?.addEventListener("loadedmetadata", handleManualSourceLoaded);
  elements.manualSourcePlayer?.addEventListener("canplay", handleManualSourceLoaded);
  elements.manualSourcePlayer?.addEventListener("error", handleManualSourceError);
  elements.manualSetInBtn?.addEventListener("click", () => setManualRangeFromPlayhead("in"));
  elements.manualSetOutBtn?.addEventListener("click", () => setManualRangeFromPlayhead("out"));
  elements.manualInInput?.addEventListener("input", renderManualRangeDuration);
  elements.manualOutInput?.addEventListener("input", renderManualRangeDuration);
  elements.manualAddRangeBtn?.addEventListener("click", addManualRangeFromWorkspace);
  elements.manualSelectedRole?.addEventListener("change", () => {
    const clip = state.manualClips.find((entry) => entry.id === state.selectedManualClipId);
    if (clip) updateManualClip(clip.id, { segmentRole: elements.manualSelectedRole.value });
  });
  elements.manualApplyTagBtn?.addEventListener("click", addTagsToSelectedManualClip);
  elements.manualSelectedTagInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addTagsToSelectedManualClip();
    }
  });
  elements.manualSelectedPreviewBtn?.addEventListener("click", () => {
    const clip = state.manualClips.find((entry) => entry.id === state.selectedManualClipId);
    const item = clip ? entries().find((entry) => entry.url === clip.url) : null;
    if (item) openVideoLightbox(item, clip.startMs || 0);
  });
  elements.manualSelectedRemoveBtn?.addEventListener("click", () => {
    if (state.selectedManualClipId) removeManualClip(state.selectedManualClipId);
  });
  elements.draftVoiceProviderSelect?.addEventListener("change", () => { toggleVoiceProviderFields(); scheduleProductDraftSave(); });
  elements.draftSpeakerSelect?.addEventListener("change", scheduleProductDraftSave);
  elements.draftVoiceoverToggle?.addEventListener("change", scheduleProductDraftSave);
  elements.showInvalidBtn.addEventListener("click", () => applyWorkbenchFilter({ status: "all", kind: "video", search: "异常问题素材" }));
  elements.showReadyBtn.addEventListener("click", () => applyWorkbenchFilter({ status: "ready", kind: "video" }));
  elements.showHoldBtn.addEventListener("click", () => applyWorkbenchFilter({ status: "all", kind: "video", search: "异常问题素材" }));
  elements.tagInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applyTagsToActiveBatch();
    }
  });
  elements.tagInput.addEventListener("input", () => {
    renderSelectedTags();
    renderQuickTags();
  });
  elements.importUrlsBtn.addEventListener("click", importUrls);
  elements.importFolderBtn.addEventListener("click", importLocalFolders);
  elements.batchFilterSelect.addEventListener("change", () => {
    state.library.filterBatchId = elements.batchFilterSelect.value;
    saveLibrary();
    render();
  });
  elements.tagFilterSelect.addEventListener("change", () => {
    state.library.filterTag = elements.tagFilterSelect.value;
    saveLibrary();
    render();
  });
  elements.statusFilterSelect.addEventListener("change", () => {
    state.statusFilter = elements.statusFilterSelect.value;
    render();
  });
  elements.roleFilterSelect.addEventListener("change", () => {
    state.roleFilter = elements.roleFilterSelect.value;
    render();
  });
  elements.searchInput.addEventListener("input", () => {
    state.search = elements.searchInput.value;
    render();
  });
  elements.clearFilterBtn.addEventListener("click", clearFilters);
  elements.closeVideoLightboxBtn.addEventListener("click", closeVideoLightbox);
  elements.copyVideoLightboxUrlBtn.addEventListener("click", () => copyVideoLightboxUrl().catch((error) => showToast(error.message)));
  elements.rewindVideoBtn.addEventListener("click", () => seekVideoLightbox(-10));
  elements.forwardVideoBtn.addEventListener("click", () => seekVideoLightbox(10));
  elements.videoLightbox.addEventListener("click", (event) => {
    if (event.target?.dataset?.materialVideoLightboxClose !== undefined) closeVideoLightbox();
  });
  elements.closeReversePromptBtn?.addEventListener("click", closeReversePromptDialog);
  elements.reversePromptDialog?.addEventListener("click", (event) => {
    if (event.target?.dataset?.materialReversePromptClose !== undefined) closeReversePromptDialog();
  });
  elements.reversePromptModes.forEach((input) => input.addEventListener("change", rebuildReversePrompt));
  elements.reversePromptMarket?.addEventListener("change", () => {
    const language = REVERSE_PROMPT_MARKET_LANGUAGES[elements.reversePromptMarket.value];
    if (language) elements.reversePromptLanguage.value = language;
    rebuildReversePrompt();
  });
  elements.reversePromptLanguage?.addEventListener("change", rebuildReversePrompt);
  elements.rebuildReversePromptBtn?.addEventListener("click", rebuildReversePrompt);
  elements.skillReversePromptBtn?.addEventListener("click", () => refineReversePromptWithSkill().catch((error) => showToast(error.message)));
  elements.copyReversePromptBtn?.addEventListener("click", () => copyReversePrompt().catch((error) => showToast(error.message)));
  elements.sendReversePromptBtn?.addEventListener("click", sendReversePromptToCreator);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeReversePromptDialog();
      closeVideoLightbox();
      return;
    }
    if (!elements.videoLightbox || elements.videoLightbox.hidden) return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      seekVideoLightbox(-10);
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      seekVideoLightbox(10);
    }
  });
  bindMixedUploadZone({
    zone: elements.allUploadZone,
    button: elements.allUploadBtn,
    input: elements.allUploadInput,
  });
}

loadChatCutSyncPreferences();
bindEvents();
restoreProductDraft({ silent: true });
applyCopyLibraryDraft();
updateChatCutEmbed({ force: true });
render();
updateBackToTopButton();
loadRuntimeConfig();
loadLibrary();
window.setInterval(() => {
  if (document.hidden) return;
  const hasActiveChatCutTask = (state.chatcutSync?.requests || []).some((request) => ["queued", "syncing", "partial"].includes(String(request?.status || "")));
  if (hasActiveChatCutTask && !state.chatcutSyncRunning) loadChatCutSync({ silent: true });
}, 10000);
