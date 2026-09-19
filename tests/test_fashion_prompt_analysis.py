from __future__ import annotations

import base64
import json
import unittest
from unittest.mock import patch

from seedance_web import server


def data_url(data: bytes = b"small-image") -> str:
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def ai_config() -> dict:
    return {
        "ai": {
            "apiKey": "private-fashion-key",
            "baseUrl": "http://vision.example.test/v1",
            "model": "vision-test-model",
            "temperature": 0.7,
            "maxTokens": 2600,
        }
    }


def local_prompt(index: int) -> dict:
    return {
        "index": index,
        "key": ("overview", "detail", "walking")[index],
        "title": ("整体展示", "结构细节", "走动展示")[index],
        "risk": "结构稳定",
        "prompt": (
            f"提示词{index + 1}｜测试｜15秒\n"
            "【模式】图像参考商品展示。\n"
            "【非叙事任务】实用意图：只展示测试背带裤；不编造剧情。\n"
            "【主任务】只完成测试背带裤商品展示。\n"
            "【参考】@产品正面全身图控制商品轮廓。\n"
            "【整体设定】原创成年女模特，普通手机记录感。\n"
            "【商品锁定】黑色宽松直筒背带裤，两条肩带和两个银色金属扣保持不变。\n"
            "【构图硬性要求】肩带到两侧裤脚完整可见。\n"
            "【时间轴】0—5秒自然站立；5—10秒缓慢转身；10—15秒停在完整全身构图。\n"
            "【连续性与物理】同一件商品，左右裤腿分别运动。\n"
            "【声音】轻微环境声，无对白、无生成配乐。\n"
            "【终点】测试背带裤完整清楚。\n"
            "【负面约束】不增减肩带、扣件或裤腿。\n"
            "【后期边界】字幕、配音、BGM、价格和CTA留到后期。"
        ),
    }


def optimization_payload() -> dict:
    return {
        "product": {
            "name": "测试背带裤",
            "category": "背带裤连体裤",
            "color": "黑色，银色五金",
            "silhouette": "宽松直筒",
            "frontStructure": "两条肩带和两个银色金属扣",
            "backStructure": "未确认",
            "material": "表面哑光",
            "stylingBoundary": "白色T恤是内搭",
            "anchors": "肩带数量，金属扣位置，裤腿分离",
            "promptMode": "fidelity",
            "duration": 15,
            "ratio": "9:16",
            "market": "日本日常女装电商",
            "scenes": ["安静的浅色室内"],
        },
        "commonLock": "商品是测试背带裤，类别固定为背带裤连体裤；保持黑色、两条肩带、两个银色金属扣和左右裤腿分离。",
        "compiler": {
            "name": "Seedance 2.0 Skill OS",
            "version": "6.7.0",
            "fashionSkill": "Fashion Product Seedance Prompts",
            "profile": "中文服装商品短提示词",
            "order": ["参考职责", "主体与动作", "运镜与终点", "物理光线", "声音", "商品保持"],
        },
        "template": {
            "id": "adaptive",
            "name": "完整新品自适应模板",
            "source": "19套 / 161镜头完整规则重构",
            "summary": "商品事实优先，完整拍摄结构",
            "promptRule": "每条只完成一个商品展示任务，并保留完整章节。",
            "rules": ["模板只控制拍法", "按品类生成物理规则"],
            "modules": ["参考角色表", "公共商品主锁", "构图硬要求", "分镜时间轴", "连续性与道具"],
            "qualityGate": ["不补全未知结构", "每镜头一个动作和一个运镜", "参考占位符逐字不变"],
            "promptArchitecture": "参考职责 → 商品锁定 → 构图 → 时间轴 → 连续性 → 修复",
            "profile": {
                "id": "overalls",
                "name": "背带裤 / 连体裤",
                "garmentSpan": "肩带、胸前片、腰胯、裆部到两侧裤脚",
                "overviewProof": "一体式连接关系和完整轮廓",
                "detailProof": "肩带、调节扣、胸前片和腰侧连接",
                "motionProof": "左右裤腿分别运动",
                "activityProof": "坐下起身时连接连续",
                "frontBackRule": "前扣转到背面后自然离开视野",
                "framing": "人物从头顶到鞋底完整入镜",
                "exclusions": ["不变成普通长裤或裙装", "左右裤腿不融合"],
            },
        },
        "referenceMap": [{"placeholder": "@产品正面全身图", "role": "正面全身", "authority": "类别、颜色和整体轮廓"}],
        "prompts": [local_prompt(index) for index in range(3)],
    }


def generation_payload() -> dict:
    payload = optimization_payload()
    return {
        "product": {**payload["product"], "count": 3},
        "commonLock": payload["commonLock"],
        "compiler": payload["compiler"],
        "referenceMap": [
            {
                "placeholder": "@产品正面全身图",
                "role": "正面全身",
                "roleKey": "front_full",
                "authority": "类别、颜色和整体轮廓",
                "fileName": "front.png",
            }
        ],
        "images": [{"name": "front.png", "role": "front_full", "dataUrl": data_url()}],
    }


def generated_prompt(index: int) -> dict:
    keys = ("overview", "detail", "walking")
    main_tasks = (
        "证明测试背带裤的完整轮廓与长度。",
        "证明测试背带裤两条肩带与两个银色金属扣的位置关系。",
        "证明测试背带裤正常步行时左右裤腿保持分离。",
    )
    first_actions = (
        "成年女模特正面自然站定，让整件商品完整出现后停住。",
        "成年女模特双手离开肩带和金属扣，让关键结构无遮挡后停住。",
        "成年女模特从两米外自然走近两步，双脚停稳后保持不动。",
    )
    first_cameras = ("固定正面全身景", "受控正面结构近景", "低幅度后退跟拍全身景")
    ranges = ("00:00—00:02", "00:02—00:03.5", "00:03.5—00:05", "00:05—00:07", "00:07—00:08.5", "00:08.5—00:10", "00:10—00:12.5", "00:12.5—00:15")
    timeline = "\n\n".join(
        f"镜头{shot + 1}：[{time_range}]｜{first_cameras[index] if shot == 0 else '自然固定视角'}\n"
        f"画面：{first_actions[index] if shot == 0 else '成年女模特完成一次克制动作后停住。'}\n"
        "展示：测试背带裤当前可见结构。\n段落终点：商品清楚且动作结束。"
        for shot, time_range in enumerate(ranges)
    )
    direct = (
        f"测试背带裤，15秒，9:16。@产品正面全身图只控制商品类别、黑色和完整轮廓。\n"
        "【镜头1】同一浅色室内，模特正面自然站定，固定全身景，动作完成后商品完整清楚。\n"
        "【镜头2】同一地点，模特向侧前方转小角度后停住，轻微横向跟随并停止。\n"
        "【镜头3】同一地点，模特自然走两步后站定，固定全身构图保持到结束。\n"
        "自然窗光，轻微脚步与衣料声，无对白、无生成配乐。保持同一件测试背带裤、两条肩带、两个银色金属扣和左右裤腿分离；无字幕、Logo、UI、水印。"
    )
    inspection = (
        f"提示词{index + 1}｜测试背带裤｜15秒\n"
        "【模式】商品参考图驱动的非叙事展示。\n"
        "【非叙事任务】只证明当前测试背带裤，不编造剧情。\n"
        f"【主任务】{main_tasks[index]}\n"
        "【参考】@产品正面全身图控制类别、颜色和完整轮廓。\n"
        "【整体设定】同一原创成年女模特，同一浅色室内，自然窗光。\n"
        "【商品锁定】模型草稿会被服务器替换。\n"
        "【构图硬性要求】肩带到两侧裤脚完整可见。\n"
        f"【时间轴】\n{timeline}\n"
        "【连续性与物理】同一人物、同一件测试背带裤，左右裤腿分别自然运动。\n"
        "【声音】轻微环境声，无对白、无生成配乐。\n"
        "【终点】测试背带裤完整清楚，动作结束。\n"
        "【负面约束】不增减肩带、金属扣或裤腿。\n"
        "【后期边界】字幕、配音、BGM、价格和CTA留到后期。"
    )
    return {
        "index": index,
        "key": keys[index],
        "title": ("整体稳定展示", "关键结构细节", "自然走动与物理")[index],
        "risk": "商品结构稳定",
        "scene": "安静的浅色室内",
        "directPrompt": direct,
        "inspectionPrompt": inspection,
    }


class FashionPromptAnalysisTests(unittest.TestCase):
    def test_analysis_category_supports_general_product_routes(self) -> None:
        cases = {
            "lipstick cosmetics": "美妆个护",
            "即食燕麦食品": "食品饮料",
            "wireless bluetooth earbuds": "数码电子",
            "宠物饮水器": "宠物用品",
            "收纳置物架": "家居日用",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(server.normalize_fashion_analysis_category(source), expected)

    def test_generation_context_contains_product_profile_and_diversity_rules(self) -> None:
        payload = generation_payload()
        payload["product"].update({
            "name": "蓝牙降噪耳机",
            "category": "数码电子",
            "silhouette": "椭圆充电盒与两只入耳式耳机",
            "frontStructure": "翻盖、状态灯与两只独立耳机",
            "material": "哑光塑料与金属触点",
        })
        context = server.normalize_fashion_generation_payload(payload)
        self.assertEqual(context["productProfile"]["id"], "electronics")
        self.assertTrue(context["diversityRules"]["uniqueHookPerPrompt"])
        self.assertTrue(context["diversityRules"]["uniquePrimaryActionPerPrompt"])
        self.assertIn("按键", context["productProfile"]["motionProof"])

    def test_every_general_product_category_uses_a_non_apparel_route(self) -> None:
        routes = {
            "美妆个护": "beauty",
            "食品饮料": "food",
            "家居日用": "home",
            "厨房用品": "kitchen",
            "数码电子": "electronics",
            "家用电器": "appliance",
            "鞋包配饰": "accessory",
            "母婴玩具": "toy",
            "宠物用品": "pet",
            "运动户外": "sports",
            "汽车用品": "automotive",
            "其他商品": "universal_product",
        }
        for category, expected_profile in routes.items():
            with self.subTest(category=category):
                profile = server.infer_fashion_product_profile({"name": category, "category": category})
                self.assertEqual(profile["id"], expected_profile)
                self.assertNotIn("模特", profile["operator"])

    def test_product_payload_keeps_category_details_and_platform_strategy(self) -> None:
        product = generation_payload()["product"]
        product.update(
            {
                "category": "数码电子",
                "categoryDetails": {
                    "interfaces": "底部 USB-C 接口",
                    "controls": "左右耳机各一处触控区",
                    "indicators": "盒体正面一枚绿色状态灯",
                    "unknown": "会被服务端保守保留为普通扩展字段",
                },
                "platformPreset": "tiktok",
                "platformStrategy": {
                    "label": "TikTok 竖屏广告",
                    "pace": "前置钩子，快速证明",
                    "focus": "第一秒出现商品和一次可见动作",
                    "safeArea": "主体保持在中央安全区",
                },
            }
        )
        normalized = server.normalize_fashion_product_payload(product)
        self.assertEqual(normalized["categoryDetails"]["interfaces"], "底部 USB-C 接口")
        self.assertEqual(normalized["platformPreset"], "tiktok")
        self.assertIn("前置钩子", normalized["platformStrategy"]["pace"])
        self.assertIn("中央安全区", normalized["platformStrategy"]["safeArea"])

    def test_reference_consistency_normalizes_conflicts_and_authorities(self) -> None:
        report = server.normalize_fashion_reference_consistency(
            {
                "status": "conflict",
                "score": 28,
                "sameProduct": False,
                "summary": "两张图的接口数量和主体颜色冲突",
                "conflicts": [
                    {"dimension": "接口", "images": [0, 1, 9], "detail": "接口数量不同", "severity": "critical"}
                ],
                "canonicalSources": [
                    {"dimension": "完整外形", "index": 0, "reason": "主视图最清晰"},
                    {"dimension": "接口", "index": 1, "reason": "底部特写"},
                ],
            },
            2,
        )
        self.assertEqual(report["status"], "conflict")
        self.assertFalse(report["sameProduct"])
        self.assertEqual(report["conflicts"][0]["images"], [0, 1])
        self.assertEqual(len(report["canonicalSources"]), 2)

    def test_prompt_fidelity_report_penalizes_missing_product_facts(self) -> None:
        payload = generation_payload()
        payload["product"].update(
            {
                "category": "数码电子",
                "color": "雾面白色",
                "silhouette": "椭圆充电盒与两只入耳式耳机",
                "frontStructure": "正面一枚状态灯",
                "categoryDetails": {"interfaces": "底部 USB-C 接口"},
                "platformPreset": "tiktok",
                "platformStrategy": {"pace": "前置钩子", "focus": "第一秒完整商品"},
            }
        )
        context = server.normalize_fashion_generation_payload(payload)
        good_prompts = [generated_prompt(index) for index in range(3)]
        good_report = server.calculate_fashion_prompt_fidelity(context, good_prompts)
        weak_prompts = [{**item, "directPrompt": "只拍一个普通商品。", "inspectionPrompt": "只拍一个普通商品。"} for item in good_prompts]
        weak_report = server.calculate_fashion_prompt_fidelity(context, weak_prompts)
        self.assertGreater(good_report["score"], weak_report["score"])
        self.assertEqual([item["key"] for item in good_report["dimensions"]], [
            "identity", "color", "silhouette", "structure", "text", "parts", "references"
        ])
        self.assertTrue(weak_report["suggestions"])

    def test_diversity_validation_rejects_repeated_primary_opening(self) -> None:
        source = generated_prompt(0)
        prompts = [{**source, "index": index, "key": ("overview", "detail", "walking")[index]} for index in range(3)]
        with self.assertRaisesRegex(server.AiError, "提示词差异不足"):
            server.validate_fashion_prompt_diversity(prompts)

    def test_generation_product_without_name_is_automatically_named(self) -> None:
        product = generation_payload()["product"]
        product["name"] = ""
        normalized = server.normalize_fashion_product_payload(product)
        self.assertEqual(normalized["name"], "黑色背带裤连体裤")

    def test_image_parser_accepts_supported_data_url_and_normalizes_role(self) -> None:
        images = server.parse_fashion_analysis_images(
            {"images": [{"name": "front.png", "role": "unknown", "dataUrl": data_url()}]}
        )
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["role"], "extra")
        self.assertEqual(images[0]["name"], "front.png")

    def test_image_parser_rejects_missing_or_unsupported_images(self) -> None:
        with self.assertRaisesRegex(ValueError, "至少上传"):
            server.parse_fashion_analysis_images({"images": []})
        with self.assertRaisesRegex(ValueError, "JPG、PNG 或 WebP"):
            server.parse_fashion_analysis_images(
                {"images": [{"name": "bad.gif", "role": "front_full", "dataUrl": "data:image/gif;base64,R0lGODlh"}]}
            )

    def test_result_normalization_keeps_observed_fields_and_valid_roles(self) -> None:
        result = server.normalize_fashion_analysis_result(
            {
                "category": "denim overalls",
                "color": "深蓝色",
                "frontStructure": "两条肩带，各有一个银色金属扣",
                "fragileAnchors": ["肩带数量", "金属扣位置", "胸前片比例", "裤腿分离"],
                "referenceRoles": [
                    {"index": 0, "role": "front_full", "reason": "完整正面"},
                    {"index": 0, "role": "back", "reason": "重复索引应丢弃"},
                    {"index": 9, "role": "side", "reason": "越界应丢弃"},
                ],
            },
            image_count=2,
        )
        self.assertEqual(result["category"], "背带裤连体裤")
        self.assertEqual(result["color"], "深蓝色")
        self.assertEqual(result["backStructure"], "未确认")
        self.assertEqual(result["referenceRoles"], [{"index": 0, "role": "front_full", "reason": "完整正面"}])

    def test_analysis_sends_images_to_configured_model_and_returns_safe_usage(self) -> None:
        model_output = {
            "suggestedName": "直筒牛仔背带裤",
            "category": "背带裤连体裤",
            "color": "深蓝色，银色五金",
            "silhouette": "宽松直筒长裤",
            "frontStructure": "矩形胸前片，两条肩带，各有一个银色金属扣",
            "backStructure": "未确认",
            "material": "中等厚度牛仔纹理，表面哑光",
            "stylingBoundary": "白色T恤为内搭，不属于商品",
            "fragileAnchors": ["肩带数量", "金属扣位置", "胸前片比例"],
            "referenceRoles": [{"index": 0, "role": "front_full", "reason": "完整轮廓"}],
            "uncertainFacts": ["背面结构缺少图片"],
            "warnings": [],
        }
        response = {
            "choices": [{"message": {"content": json.dumps(model_output, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200, "other": "hidden"},
        }
        with patch.object(server, "call_ai_chat", return_value=response) as call:
            result = server.analyze_fashion_product(
                {
                    "productName": "测试背带裤",
                    "images": [{"name": "front.png", "role": "front_full", "dataUrl": data_url()}],
                },
                config=ai_config(),
            )

        request_body = call.call_args.args[0]
        request_text = json.dumps(request_body, ensure_ascii=False)
        self.assertEqual(request_body["model"], "vision-test-model")
        self.assertIn("data:image/png;base64,", request_text)
        self.assertNotIn("private-fashion-key", request_text)
        self.assertEqual(result["analysis"]["suggestedName"], "直筒牛仔背带裤")
        self.assertEqual(result["usage"], {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200})
        self.assertTrue(result["insecureEndpoint"])

    def test_config_response_never_returns_full_ai_key(self) -> None:
        ai = server.build_config_response(ai_config())["config"]["ai"]
        self.assertTrue(ai["hasApiKey"])
        self.assertNotIn("private-fashion-key", json.dumps(ai))
        self.assertIn("...", ai["apiKeyPreview"])

    def test_ai_generation_uses_current_product_images_and_returns_complete_pack(self) -> None:
        response = {
            "choices": [{"message": {"content": json.dumps({
                "prompts": [generated_prompt(index) for index in range(3)],
                "repairs": [{"title": "扣件漂移", "text": "追加：两个银色金属扣数量和位置保持不变。"}],
                "notes": ["按当前新品重新编排"],
            }, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 1800, "total_tokens": 3000, "hidden": 1},
        }
        with patch.object(server, "call_ai_chat", return_value=response) as call:
            result = server.generate_fashion_prompts(generation_payload(), config=ai_config())

        request_body = call.call_args.args[0]
        request_text = json.dumps(request_body, ensure_ascii=False)
        self.assertEqual(request_body["model"], "vision-test-model")
        self.assertEqual(request_body["max_tokens"], 20000)
        self.assertEqual(call.call_args.kwargs["timeout_seconds"], 600)
        self.assertIn("data:image/png;base64,", request_text)
        self.assertIn("禁止填充预写镜头模板", request_text)
        user_context = request_body["messages"][1]["content"][0]["text"]
        self.assertIn('"writeFromScratch": true', user_context)
        self.assertIn("Seedance 2.0 Skill OS v6.7.0", request_text)
        self.assertNotIn("private-fashion-key", request_text)
        self.assertEqual([item["key"] for item in result["prompts"]], ["overview", "detail", "walking"])
        self.assertIn(generation_payload()["commonLock"], result["prompts"][0]["inspectionPrompt"])
        self.assertIn(generation_payload()["commonLock"], result["prompts"][0]["directPrompt"])
        self.assertEqual(server.fashion_generation_shot_ids(result["prompts"][0]["directPrompt"]), list(range(1, 9)))
        self.assertIn("【人物与穿搭连续性】", result["prompts"][0]["directPrompt"])
        self.assertIn("【自然表演】", result["prompts"][0]["directPrompt"])
        self.assertIn("【服装状态与物理】", result["prompts"][0]["directPrompt"])
        self.assertEqual(result["usage"], {"prompt_tokens": 1200, "completion_tokens": 1800, "total_tokens": 3000})

    def test_fidelity_mode_accepts_empty_ai_direct_and_builds_it_from_full_prompt(self) -> None:
        prompts = [generated_prompt(index) for index in range(3)]
        for item in prompts:
            item["directPrompt"] = ""
        context = server.normalize_fashion_generation_payload(generation_payload())
        result = server.normalize_fashion_generation_result({"prompts": prompts}, context)
        for item in result["prompts"]:
            self.assertEqual(item["directPrompt"], item["inspectionPrompt"])
            self.assertEqual(server.fashion_generation_shot_ids(item["directPrompt"]), list(range(1, 9)))
            self.assertIn(generation_payload()["commonLock"], item["directPrompt"])

    def test_ai_generation_removes_unknown_reference_tag_and_keeps_bound_tag(self) -> None:
        prompts = [generated_prompt(index) for index in range(3)]
        prompts[1]["directPrompt"] = prompts[1]["directPrompt"].replace("@产品正面全身图", "@错误商品图")
        response = {"choices": [{"message": {"content": json.dumps({"prompts": prompts}, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            result = server.generate_fashion_prompts(generation_payload(), config=ai_config())
        self.assertNotIn("@错误商品图", result["prompts"][1]["directPrompt"])
        self.assertIn("@产品正面全身图", result["prompts"][1]["inspectionPrompt"])

    def test_ai_generation_restores_product_name_when_direct_prompt_omits_it(self) -> None:
        context = server.normalize_fashion_generation_payload(generation_payload())
        prompts = [generated_prompt(index) for index in range(3)]
        for item in prompts:
            item["directPrompt"] = item["directPrompt"].replace("测试背带裤", "当前商品")
        result = server.normalize_fashion_generation_result({"prompts": prompts}, context)
        for item in result["prompts"]:
            self.assertIn("测试背带裤", item["directPrompt"])
            self.assertIn(generation_payload()["commonLock"], item["directPrompt"])

    def test_stable_mode_keeps_three_shots_and_embeds_complete_product_lock(self) -> None:
        payload = generation_payload()
        payload["product"]["promptMode"] = "stable"
        context = server.normalize_fashion_generation_payload(payload)
        result = server.normalize_fashion_generation_result(
            {"prompts": [generated_prompt(index) for index in range(3)]},
            context,
        )
        for item in result["prompts"]:
            self.assertEqual(server.fashion_generation_shot_ids(item["directPrompt"]), [1, 2, 3])
            self.assertIn("【核心商品锁】", item["directPrompt"])
            self.assertIn(payload["commonLock"], item["directPrompt"])

    def test_ai_generation_normalizes_common_eight_shot_time_formats(self) -> None:
        inspection = generated_prompt(0)["inspectionPrompt"].replace("—", "-")
        normalized = server.normalize_fashion_inspection_timeline(inspection, 15)
        for time_range in ("00:00—00:02", "00:02—00:03.5", "00:12.5—00:15"):
            self.assertIn(time_range, normalized)
        self.assertEqual(server.fashion_prompt_shot_ids(normalized), list(range(1, 9)))

    def test_ai_generation_removes_unbound_reference_sigils_without_images(self) -> None:
        payload = generation_payload()
        payload["referenceMap"] = []
        payload["images"] = []
        context = server.normalize_fashion_generation_payload(payload)
        result = server.normalize_fashion_generation_result(
            {"prompts": [generated_prompt(index) for index in range(3)]},
            context,
        )
        self.assertNotIn("@", json.dumps(result["prompts"], ensure_ascii=False))
        self.assertIn("产品正面全身图", result["prompts"][0]["directPrompt"])

    def test_ai_generation_rejects_old_product_fact_leakage(self) -> None:
        prompts = [generated_prompt(index) for index in range(3)]
        prompts[2]["inspectionPrompt"] += " 在埃菲尔铁塔前结束。"
        response = {"choices": [{"message": {"content": json.dumps({"prompts": prompts}, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            with self.assertRaisesRegex(server.AiError, "旧商品事实"):
                server.generate_fashion_prompts(generation_payload(), config=ai_config())

    def test_ai_generation_accepts_guarded_terms_inside_negative_constraints(self) -> None:
        prompts = [generated_prompt(index) for index in range(3)]
        for item in prompts:
            item["inspectionPrompt"] = item["inspectionPrompt"].replace(
                "【负面约束】",
                "【负面约束】禁止写显瘦、抗皱、凉感、舒适透气或高级感；禁止4K、8K空泛画质词；"
                "不得串入中灰色、三粒同色、方形贴袋或埃菲尔铁塔等旧商品事实。",
            )
        context = server.normalize_fashion_generation_payload(generation_payload())
        result = server.normalize_fashion_generation_result({"prompts": prompts}, context)
        self.assertEqual(len(result["prompts"]), 3)

    def test_ai_generation_repairs_positive_unconfirmed_claim(self) -> None:
        prompts = [generated_prompt(index) for index in range(3)]
        prompts[0]["inspectionPrompt"] = prompts[0]["inspectionPrompt"].replace(
            "【整体设定】同一原创成年女模特，同一浅色室内，自然窗光。",
            "【整体设定】同一原创成年女模特，同一浅色室内，自然窗光，穿着后显瘦，4K高级感。",
        )
        context = server.normalize_fashion_generation_payload(generation_payload())
        result = server.normalize_fashion_generation_result({"prompts": prompts}, context)
        self.assertNotIn("穿着后显瘦", result["prompts"][0]["inspectionPrompt"])
        self.assertNotIn("4K高级感", result["prompts"][0]["inspectionPrompt"])
        self.assertIn("轮廓比例清楚", result["prompts"][0]["inspectionPrompt"])
        self.assertIn("服务器已自动中性化未确认宣称", result["notes"][0])

    def test_prompt_optimization_uses_text_only_and_returns_complete_safe_result(self) -> None:
        optimized = [
            {
                "index": index,
                "prompt": local_prompt(index)["prompt"] + "\n【终点】动作完成后保持商品完整清晰到视频结束。",
            }
            for index in range(3)
        ]
        response = {
            "choices": [{"message": {"content": json.dumps({"prompts": optimized, "notes": ["强化动作终点"]}, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 600, "total_tokens": 1500, "hidden": "drop"},
        }
        with patch.object(server, "call_ai_chat", return_value=response) as call:
            result = server.optimize_fashion_prompts(optimization_payload(), config=ai_config())

        request_body = call.call_args.args[0]
        request_text = json.dumps(request_body, ensure_ascii=False)
        self.assertEqual(request_body["model"], "vision-test-model")
        self.assertEqual(request_body["max_tokens"], 12000)
        self.assertNotIn("data:image/", request_text)
        self.assertNotIn("private-fashion-key", request_text)
        self.assertIn("测试背带裤", request_text)
        self.assertIn("完整新品自适应模板", request_text)
        self.assertIn("公共商品主锁", request_text)
        self.assertIn("背带裤 / 连体裤", request_text)
        self.assertIn("15秒高还原直贴层", request_text)
        self.assertIn("镜头1—8", request_text)
        self.assertIn("八个镜头都会直接送入Seedance", request_text)
        self.assertIn("Seedance 2.0 Skill OS v6.7.0", request_text)
        self.assertIn("Fashion Product Seedance Prompts", request_text)
        self.assertIn("一个主要生成预算", request_text)
        self.assertEqual([item["index"] for item in result["prompts"]], [0, 1, 2])
        self.assertEqual(result["usage"], {"prompt_tokens": 900, "completion_tokens": 600, "total_tokens": 1500})
        self.assertEqual(result["notes"], ["强化动作终点"])

    def test_prompt_optimization_rejects_incomplete_model_result(self) -> None:
        incomplete = {"prompts": [{"index": 0, "prompt": local_prompt(0)["prompt"]}], "notes": []}
        response = {"choices": [{"message": {"content": json.dumps(incomplete, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            with self.assertRaisesRegex(server.AiError, "数量或索引不完整"):
                server.optimize_fashion_prompts(optimization_payload(), config=ai_config())

    def test_prompt_optimization_restores_locked_reference_placeholder(self) -> None:
        optimized = []
        for index in range(3):
            prompt = local_prompt(index)["prompt"] + "\n【终点】保持稳定。"
            if index == 1:
                prompt = prompt.replace("@产品正面全身图", "@错误参考图")
            optimized.append({"index": index, "prompt": prompt})
        response = {"choices": [{"message": {"content": json.dumps({"prompts": optimized}, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            result = server.optimize_fashion_prompts(optimization_payload(), config=ai_config())
        self.assertIn("@产品正面全身图", result["prompts"][1]["prompt"])
        self.assertNotIn("@错误参考图", result["prompts"][1]["prompt"])

    def test_prompt_optimization_restores_missing_locked_section(self) -> None:
        optimized = []
        for index in range(3):
            prompt = local_prompt(index)["prompt"]
            if index == 1:
                prompt = prompt.replace("【连续性与物理】同一件商品，左右裤腿分别运动。\n", "")
            optimized.append({"index": index, "prompt": prompt})
        response = {"choices": [{"message": {"content": json.dumps({"prompts": optimized}, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            result = server.optimize_fashion_prompts(optimization_payload(), config=ai_config())
        self.assertIn("【连续性与物理】同一件商品，左右裤腿分别运动。", result["prompts"][1]["prompt"])

    def test_prompt_optimization_only_accepts_mutable_motion_and_endpoint_sections(self) -> None:
        optimized = []
        for index in range(3):
            prompt = local_prompt(index)["prompt"]
            prompt = prompt.replace("黑色宽松直筒背带裤", "红色紧身连衣裙")
            prompt = prompt.replace("0—5秒自然站立", "0—5秒向前自然走两步后停住")
            optimized.append({"index": index, "prompt": prompt})
        response = {"choices": [{"message": {"content": json.dumps({"prompts": optimized}, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            result = server.optimize_fashion_prompts(optimization_payload(), config=ai_config())
        for item in result["prompts"]:
            self.assertIn("黑色宽松直筒背带裤", item["prompt"])
            self.assertNotIn("红色紧身连衣裙", item["prompt"])
            self.assertIn("0—5秒向前自然走两步后停住", item["prompt"])

    def test_prompt_optimization_rejects_old_template_fact_leakage(self) -> None:
        optimized = []
        for index in range(3):
            prompt = local_prompt(index)["prompt"]
            if index == 2:
                prompt = prompt.replace("0—5秒自然站立", "0—5秒在埃菲尔铁塔前自然站立")
            optimized.append({"index": index, "prompt": prompt})
        response = {"choices": [{"message": {"content": json.dumps({"prompts": optimized}, ensure_ascii=False)}}]}
        with patch.object(server, "call_ai_chat", return_value=response):
            with self.assertRaisesRegex(server.AiError, "旧模板事实"):
                server.optimize_fashion_prompts(optimization_payload(), config=ai_config())

    def test_prompt_optimization_rejects_dense_shot_count_changes(self) -> None:
        ranges = ("00:00—00:02", "00:02—00:03.5", "00:03.5—00:05", "00:05—00:07", "00:07—00:08.5", "00:08.5—00:10", "00:10—00:12.5", "00:12.5—00:15")
        timeline = "\n\n".join(
            f"镜头{index + 1}：[{time_range}]｜测试景别\n画面：测试动作。\n镜头：固定视角。\n展示：商品结构。\n段落终点：动作结束。"
            for index, time_range in enumerate(ranges)
        )
        original = local_prompt(0)["prompt"].replace(
            "【时间轴】0—5秒自然站立；5—10秒缓慢转身；10—15秒停在完整全身构图。",
            f"【时间轴】\n{timeline}",
        )
        candidate = "【时间轴】\n" + "\n\n".join(timeline.split("\n\n")[:7]) + "\n【终点】测试背带裤完整清楚。"
        merged = server.merge_fashion_optimized_prompt(original, candidate)
        payload = optimization_payload()
        payload["prompts"] = [{**local_prompt(0), "prompt": original}]
        context = server.normalize_fashion_optimization_payload(payload)
        result = {"prompts": [{"index": 0, "prompt": merged}], "notes": []}
        self.assertEqual(server.fashion_prompt_shot_ids(original), list(range(1, 9)))
        with self.assertRaisesRegex(server.AiError, "镜头数量或编号"):
            server.validate_fashion_optimization_preservation(result, context)


if __name__ == "__main__":
    unittest.main()
