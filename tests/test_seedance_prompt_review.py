from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seedance_web import server


class SeedancePromptReviewTests(unittest.TestCase):
    def make_skill(self, root: Path) -> None:
        (root / "SKILL.md").write_text(
            '---\nname: seedance-20\nmetadata:\n  version: "6.7.0"\n---\n',
            encoding="utf-8",
        )
        for relative in server.SEEDANCE_REVIEW_SKILL_FILES:
            target = root / relative
            if target == root / "SKILL.md":
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"review rule from {relative}\n", encoding="utf-8")

    def runtime_config(self) -> dict:
        return {
            "ai": {
                "apiKey": "ai-test-key",
                "baseUrl": "https://ai.example.test/v1",
                "model": "gpt-test-model",
                "maxTokens": 2200,
            }
        }

    def test_skill_status_reads_installed_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_skill(root)
            with patch.object(server, "get_seedance_review_skill_dir", return_value=root):
                status = server.build_seedance_review_skill_status()
        self.assertTrue(status["exists"])
        self.assertEqual(status["name"], "seedance-20")
        self.assertEqual(status["version"], "6.7.0")

    def test_review_uses_skill_context_and_normalizes_result(self) -> None:
        response_text = json.dumps(
            {
                "scoreBefore": 58,
                "scoreAfter": 88,
                "score": 88,
                "verdict": "revise",
                "summary": "已保留商品和动作意图，并补全镜头终点与光源。",
                "mode": "r2v",
                "strengths": ["商品是明确主体"],
                "preservedContent": ["@视频1", "斜扣阔腿牛仔裤", "模特转身展示"],
                "issues": [
                    {
                        "severity": "warning",
                        "category": "镜头",
                        "finding": "推镜没有写终点。",
                        "suggestion": "让镜头停在斜扣腰头特写。",
                    }
                ],
                "improvedPrompt": "@视频1仅提供动作节奏。模特转身展示牛仔裤，镜头缓慢推近并停在斜扣腰头特写。",
                "changeSummary": ["明确参考视频职责", "补充镜头终点"],
            },
            ensure_ascii=False,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_skill(root)
            with (
                patch.object(server, "get_seedance_review_skill_dir", return_value=root),
                patch.object(server, "read_runtime_config", return_value=self.runtime_config()),
                patch.object(
                    server,
                    "call_ai_chat",
                    return_value={"choices": [{"message": {"content": response_text}}]},
                ) as call,
            ):
                result = server.review_seedance_prompt(
                    {
                        "prompt": "@视频1 模特转身展示牛仔裤，镜头缓慢推近。",
                        "brief": "斜扣阔腿牛仔裤",
                        "ratio": "9:16",
                        "duration": 10,
                        "model": "doubao-seedance-2-0-260128",
                        "refVideos": ["https://assets.example.test/ref.mp4"],
                    }
                )

        self.assertEqual(result["review"]["score"], 88)
        self.assertEqual(result["review"]["scoreBefore"], 58)
        self.assertEqual(result["review"]["scoreAfter"], 88)
        self.assertEqual(result["review"]["verdict"], "revise")
        self.assertEqual(result["review"]["mode"], "R2V")
        self.assertEqual(result["review"]["preservedContent"][0], "@视频1")
        self.assertTrue(result["review"]["referenceTagsPreserved"])
        self.assertEqual(result["skill"]["version"], "6.7.0")
        self.assertEqual(len(result["skill"]["files"]), len(server.SEEDANCE_REVIEW_SKILL_FILES))
        request_body = call.call_args.args[0]
        self.assertIn("LOCAL SKILL CONTEXT", request_body["messages"][0]["content"])
        self.assertIn("seedance-antislop", request_body["messages"][0]["content"])
        self.assertIn("主要任务不是点评", request_body["messages"][0]["content"])
        self.assertIn("必须逐字保留", request_body["messages"][0]["content"])
        self.assertIn("不得新增未提供的功效、价格、颜色、面料", request_body["messages"][0]["content"])
        user_context = json.loads(request_body["messages"][1]["content"])
        self.assertEqual(user_context["referenceCounts"]["videos"], 1)
        self.assertEqual(user_context["requiredReferenceTags"], ["@视频1"])
        self.assertNotIn("https://assets.example.test/ref.mp4", request_body["messages"][1]["content"])
        self.assertIn("optimizedAt", result)

    def test_normalization_restores_reference_tags_and_clamps_scores(self) -> None:
        normalized = server.normalize_seedance_prompt_review(
            {
                "scoreBefore": -8,
                "scoreAfter": 132,
                "verdict": "pass",
                "improvedPrompt": "模特转身后，镜头停在斜扣腰头近景。",
            },
            "参考@视频1的动作，商品以@图片2为准。",
        )

        self.assertEqual(normalized["scoreBefore"], 0)
        self.assertEqual(normalized["scoreAfter"], 100)
        self.assertIn("@视频1", normalized["improvedPrompt"])
        self.assertIn("@图片2", normalized["improvedPrompt"])
        self.assertEqual(normalized["restoredReferenceTags"], ["@视频1", "@图片2"])
        self.assertTrue(normalized["referenceTagsPreserved"])
        self.assertTrue(any(item["category"] == "素材引用" for item in normalized["issues"]))

    def test_prompt_optimizer_ui_uses_optimization_language(self) -> None:
        static_dir = Path(server.__file__).parent / "static"
        html = (static_dir / "index.html").read_text(encoding="utf-8")
        script = (static_dir / "app.js").read_text(encoding="utf-8")

        self.assertIn("Skill 优化提示词", html)
        self.assertIn("保留内容", html)
        self.assertIn("主要修改", html)
        self.assertIn("/api/skill/optimize-prompt", script)
        self.assertIn("Skill 优化中", script)

    def test_review_requires_prompt(self) -> None:
        with self.assertRaisesRegex(ValueError, "请先填写"):
            server.review_seedance_prompt({"prompt": ""})

    def test_missing_skill_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "missing"
            with patch.object(server, "get_seedance_review_skill_dir", return_value=root):
                with self.assertRaisesRegex(ValueError, "not installed"):
                    server.load_seedance_review_skill_context()


if __name__ == "__main__":
    unittest.main()
