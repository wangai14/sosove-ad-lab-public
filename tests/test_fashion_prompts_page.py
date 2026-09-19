from __future__ import annotations

import unittest
from pathlib import Path

from seedance_web import server


class FashionPromptPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_dir = Path(__file__).resolve().parents[1]
        cls.static_dir = cls.project_dir / "static"
        cls.html = (cls.static_dir / "fashion-prompts.html").read_text(encoding="utf-8")
        cls.script = (cls.static_dir / "fashion-prompts.js").read_text(encoding="utf-8")
        cls.styles = (cls.static_dir / "fashion-prompts.css").read_text(encoding="utf-8")

    def test_page_assets_and_server_route_exist(self) -> None:
        self.assertTrue((self.static_dir / "fashion-prompts.css").is_file())
        self.assertTrue((self.static_dir / "fashion-prompts.js").is_file())
        server_source = (self.project_dir / "server.py").read_text(encoding="utf-8")
        self.assertIn('"/fashion-prompts.html"', server_source)
        self.assertIn('self.serve_static("fashion-prompts.html")', server_source)

    def test_page_exposes_product_reference_and_output_controls(self) -> None:
        required_ids = (
            "product-name",
            "category",
            "front-structure",
            "fragile-anchors",
            "reference-input",
            "reference-grid",
            "template-preset",
            "template-resolution",
            "template-resolution-name",
            "prompt-mode",
            "duration",
            "prompt-count",
            "generate-button",
            "prompt-list",
            "copy-direct-all-button",
            "copy-all-button",
            "download-button",
            "reset-product-button",
        )
        for element_id in required_ids:
            self.assertIn(f'id="{element_id}"', self.html)

    def test_workbench_is_routed_for_general_products(self) -> None:
        self.assertIn("通用商品视频提示词", self.html)
        for category in ("美妆个护", "食品饮料", "家居日用", "数码电子", "宠物用品", "其他商品"):
            self.assertIn(f'value="{category}"', self.html)
        self.assertIn("外形 / 规格 / 轮廓", self.html)
        self.assertIn("材质 / 质地 / 内容物", self.html)
        self.assertIn("const PRODUCT_PROFILES = {", self.script)
        self.assertIn("function inferProductProfile(product", self.script)
        for profile in ("beauty", "food", "home", "electronics", "appliance", "pet", "universal_product"):
            self.assertIn(f"  {profile}: {{", self.script)
        self.assertIn("function productRoleForProfile(roleKey", self.script)
        self.assertIn("function recommendedScenesForProfile(profile", self.script)

    def test_category_specific_fields_and_platform_presets_are_visible(self) -> None:
        for element_id in (
            "category-detail-sheet",
            "category-detail-title",
            "category-detail-grid",
            "platform-preset",
            "platform-preset-card",
            "platform-preset-ratio",
            "platform-preset-pace",
            "platform-preset-focus",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("const CATEGORY_FIELD_SCHEMAS = {", self.script)
        self.assertIn("const PLATFORM_PRESETS = {", self.script)
        self.assertIn("function renderCategoryFields(", self.script)
        self.assertIn("function applyPlatformPreset(", self.script)
        for platform in ("tiktok", "facebook", "instagram", "amazon", "independent", "custom"):
            self.assertIn(f'value="{platform}"', self.html)

    def test_consistency_fidelity_and_history_workspaces_are_present(self) -> None:
        for element_id in (
            "reference-consistency-panel",
            "reference-consistency-score",
            "reference-consistency-summary",
            "fidelity-score-panel",
            "fidelity-score-value",
            "fidelity-dimensions",
            "version-history-panel",
            "version-history-list",
            "history-compare-left",
            "history-compare-right",
            "history-compare-button",
            "history-compare-result",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        for function in (
            "referenceFingerprint",
            "ensureReferenceConsistency",
            "renderReferenceConsistency",
            "renderFidelityReport",
            "saveHistorySnapshot",
            "compareHistoryVersions",
            "restoreHistoryVersion",
        ):
            self.assertIn(f"function {function}(", self.script)
        self.assertIn("sosove-product-prompt-history-v1", self.script)

    def test_page_exposes_visible_ai_configuration_and_analysis_controls(self) -> None:
        for element_id in (
            "ai-config-base-url",
            "ai-config-model",
            "ai-config-key",
            "save-ai-config-button",
            "test-ai-config-button",
            "ai-config-test-result",
            "ai-config-test-state",
            "ai-config-test-detail",
            "endpoint-warning",
            "analyze-product-button",
            "ai-analysis-state",
            "ai-review-panel",
            "ai-review-list",
            "apply-ai-review-button",
            "discard-ai-review-button",
            "optimize-prompts-button",
            "ai-optimize-state",
            "ai-optimize-usage",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("AI生成提示词包", self.html)
        self.assertIn("都会调用模型并消耗 Token", self.html)
        self.assertIn("复制和下载 TXT 不消耗", self.html)
        self.assertIn("消耗 Token", self.html)
        self.assertIn("不重复上传商品图片", self.html)
        self.assertIn("function saveAiConfig()", self.script)
        self.assertIn("function testAiConfig()", self.script)
        self.assertIn('requestJson("/api/config/test/ai"', self.script)
        self.assertIn('testMode: "invoke"', self.script)
        self.assertIn("function analyzeProductWithAi()", self.script)
        self.assertIn("function optimizePromptsWithAi()", self.script)
        self.assertIn('requestJson("/api/fashion-prompts/analyze"', self.script)
        self.assertIn('requestJson("/api/fashion-prompts/generate"', self.script)
        self.assertIn('requestJson("/api/fashion-prompts/optimize"', self.script)
        self.assertIn("async function generatePack()", self.script)
        self.assertIn("function applyAiGeneration(result", self.script)
        self.assertIn("每次 AI 生成都会消耗 Token", self.script)
        self.assertIn('option value="3" selected', self.html)
        self.assertIn("高还原3条通常约3—5分钟", self.html)
        self.assertIn("请不要重复点击或关闭页面", self.script)
        self.assertIn("function applyAiAnalysis(analysis, selectedKeys", self.script)
        self.assertIn("function stageAiAnalysis(analysis)", self.script)
        self.assertIn("等待人工确认", self.script)
        self.assertIn("function applyAiOptimization(result)", self.script)
        self.assertIn("Seedance 2.0 Skill OS", self.html)
        self.assertIn("v6.7.0", self.html)

    def test_prompt_pack_contains_independent_clip_roles_and_post_boundary(self) -> None:
        for role in ("overview", "detail", "walking", "routine", "activity", "lifestyle", "ending"):
            self.assertIn(f"  {role}: {{", self.script)
        self.assertIn("【非叙事任务】", self.script)
        self.assertIn("【构图硬性要求】", self.script)
        self.assertIn("【连续性与物理】", self.script)
        self.assertIn("【后期边界】", self.script)
        self.assertIn("字幕、日语配音、BGM、价格、优惠、法律文案和CTA全部留到可编辑剪辑阶段", self.script)

    def test_dual_prompt_outputs_and_reference_coverage_downgrade_are_present(self) -> None:
        self.assertIn("Seedance直贴版", self.html)
        self.assertIn("检查完整版", self.html)
        self.assertIn("function buildDirectPrompt(role, product, sourcePrompt", self.script)
        self.assertIn("function buildDirectPackText(product, prompts", self.script)
        self.assertIn("function referenceCoverage(product", self.script)
        self.assertIn("不转到参考图未覆盖的背面", self.script)
        self.assertIn("不展示或补全未知背面", self.script)
        self.assertIn('data-prompt-variant="direct"', self.script)
        self.assertIn("String(item.prompt || \"\").trim()", self.script)

    def test_supplied_knitwear_template_is_analyzed_and_product_facts_stay_separate(self) -> None:
        self.assertIn("V领纯色长袖针织衫_Seedance提示词合集(1).txt", self.html)
        self.assertIn("19</b> 套原始方案", self.html)
        self.assertIn("161</b> 个原始镜头", self.html)
        self.assertIn("8</b> 镜头精细版", self.html)
        self.assertIn("高还原 8 镜头（推荐）", self.html)
        self.assertIn("精简稳定 3 镜头", self.html)
        self.assertIn("高还原模式直接生成完整8镜头", self.html)
        self.assertIn('value="auto" selected', self.html)
        self.assertIn('value="knitwear"', self.html)
        self.assertIn("完整新品自适应规则", self.html)
        self.assertIn("完整重构规则", self.html)
        self.assertIn("function resolvePromptTemplate(product", self.script)
        self.assertIn("function inferGarmentProfile(product", self.script)
        self.assertIn("function roleForTemplate(roleKey, template, product", self.script)
        self.assertIn("const GARMENT_PROFILES = {", self.script)
        for profile in ("knitwear", "overalls", "trousers", "dress", "outerwear", "top"):
            self.assertIn(f"  {profile}: {{", self.script)
        self.assertIn("【模板策略】", self.script)
        self.assertIn("template: compactTemplate(state.template)", self.script)
        for stale_fact in ("中灰色", "三粒同色", "方形贴袋", "埃菲尔铁塔"):
            self.assertNotIn(stale_fact, self.script)

    def test_short_duration_uses_continuous_action_and_download_is_utf8(self) -> None:
        self.assertIn("if (duration <= 5 || role.oneTake)", self.script)
        self.assertIn("【连续动作】", self.script)
        self.assertIn("【展示】", self.script)
        self.assertIn("【段落终点】", self.script)
        self.assertIn('new Blob(["\\ufeff", state.packText]', self.script)
        self.assertIn('type: "text/plain;charset=utf-8"', self.script)

    def test_fifteen_second_mode_builds_eight_numbered_shots(self) -> None:
        self.assertIn("const DENSE_TIMELINE_RANGES = [", self.script)
        self.assertIn('["00:12.5", "00:15"]', self.script)
        self.assertIn("function buildDenseTimeline(role, product", self.script)
        self.assertIn("15秒高密度8镜头", self.script)
        self.assertIn("镜头${index + 1}：", self.script)
        self.assertIn("if (duration >= 15) return buildDenseTimeline", self.script)
        self.assertIn("15秒高还原模式直接生成8个编号镜头", self.script)

    def test_direct_prompt_defaults_to_full_fidelity_and_keeps_stable_fallback(self) -> None:
        self.assertIn('option value="fidelity" selected', self.html)
        self.assertIn('option value="stable"', self.html)
        self.assertIn("function isFidelityMode(product", self.script)
        self.assertIn("function expectedDirectShotCount(product", self.script)
        self.assertIn('if (isFidelityMode(product)) return String(sourcePrompt || "").trim()', self.script)
        self.assertIn("【核心商品锁】${productLock}", self.script)
        self.assertIn("function compactDenseMotionBlock(prompt, role)", self.script)
        self.assertIn("function directShotIndices(roleKey)", self.script)
        self.assertIn("15秒只生成以下3个主镜头", self.script)
        self.assertIn("const DIRECT_SHOT_INDEX_MAP = Object.fromEntries", self.script)
        self.assertIn("return DIRECT_SHOT_INDEX_MAP[roleKey] || [0, 1, 2]", self.script)
        self.assertIn("function denseBlockField(block, label)", self.script)
        self.assertIn("function compactFactList(value, itemLimit", self.script)
        self.assertIn("const SEEDANCE_SKILL_COMPILER = Object.freeze", self.script)
        self.assertIn("function compactDirectReference(role, fallback", self.script)
        self.assertIn("function directPromptQuality(prompt, productOrDuration)", self.script)
        self.assertIn('order: ["参考职责", "主体与动作", "运镜与终点", "物理光线", "声音", "商品保持"]', self.script)
        self.assertIn("compiler: compactCompilerProfile()", self.script)
        self.assertIn("roleKey: item.value", self.script)
        self.assertIn("images,", self.script)
        self.assertIn("function lightForScene(scene", self.script)
        self.assertIn("【光线】${lightForScene(scene)}", self.script)
        self.assertIn("每次只复制一条，不能把整包一次粘贴到 Seedance", self.script)
        self.assertIn("完整核心商品锁和8个编号镜头", self.script)
        self.assertNotIn("8镜头完整分镜保留在检查完整版中", self.script)

    def test_generator_is_current_form_driven_without_old_product_leakage(self) -> None:
        self.assertIn("本次提示词只读取当前表单", self.script)
        self.assertIn("AI 会读取当前新品与参考图", self.html)
        self.assertIn("不套预写镜头文案", self.html)
        self.assertIn("可留空自动命名", self.html)
        self.assertIn("商品名称未填写，已自动命名为", self.script)
        self.assertIn('product.name = `${color}${category}` || "当前商品新品"', self.script)
        self.assertIn("function generateLocalPack()", self.script)
        self.assertIn("async function generatePack()", self.script)
        self.assertIn("function resetProduct()", self.script)
        self.assertIn("localStorage.removeItem(STORAGE_KEY)", self.script)
        for stale_product in ("斜扣牛仔裤", "T恤罩衫", "百褶半身裙"):
            self.assertNotIn(stale_product, self.script)

    def test_responsive_layout_and_reduced_motion_are_present(self) -> None:
        self.assertIn("@media (max-width: 900px)", self.styles)
        self.assertIn("@media (max-width: 560px)", self.styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.styles)
        self.assertIn(".empty-output[hidden]", self.styles)


if __name__ == "__main__":
    unittest.main()
