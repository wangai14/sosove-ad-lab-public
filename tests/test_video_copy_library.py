from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from seedance_web import server


class VideoCopyLibraryTests(unittest.TestCase):
    def test_normalizes_script_entry_with_tags_and_metrics(self) -> None:
        entry = server.normalize_video_copy_entry(
            {
                "id": "copy-demo-01",
                "title": "15 秒开头钩子",
                "product": "阔腿裤",
                "stage": "hook",
                "status": "verified",
                "duration": 15,
                "tags": "15秒、开头钩子、阔腿裤",
                "script": "0-3秒｜开头钩子\n3-15秒｜细节和收尾",
                "performance": {"views": "120000", "saves": 3800, "orders": 95},
            },
            default_created_by="editor_01",
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry["stage"], "hook")
        self.assertEqual(entry["status"], "verified")
        self.assertEqual(entry["tags"], ["15秒", "开头钩子", "阔腿裤"])
        self.assertEqual(entry["performance"]["views"], 120000)
        self.assertEqual(entry["createdBy"], "editor_01")

    def test_create_and_update_copy_entry_use_library_storage(self) -> None:
        base_library = server.normalize_video_copy_library({"items": []})
        stored: list[dict] = []

        def write_library(value: dict) -> dict:
            normalized = server.normalize_video_copy_library(value)
            stored.append(normalized)
            return normalized

        with patch.object(server, "read_video_copy_library", return_value=base_library), patch.object(
            server, "write_video_copy_library", side_effect=write_library
        ):
            library, created = server.create_video_copy_entry(
                {"title": "测试文案", "script": "0-15秒｜完整脚本", "status": "testing"},
                "editor_01",
            )
        self.assertEqual(created["createdBy"], "editor_01")
        self.assertEqual(len(library["items"]), 1)

        with patch.object(server, "read_video_copy_library", return_value=library), patch.object(
            server, "write_video_copy_library", side_effect=write_library
        ):
            updated_library, updated = server.update_video_copy_entry(
                {"id": created["id"], "title": "已验证文案", "script": "0-15秒｜更新后的完整脚本", "status": "verified"},
                "editor_02",
            )
        self.assertEqual(updated["title"], "已验证文案")
        self.assertEqual(updated["status"], "verified")
        self.assertEqual(updated["createdBy"], "editor_01")
        self.assertEqual(len(updated_library["items"]), 1)
        self.assertGreaterEqual(len(stored), 2)

    def test_ai_analysis_returns_timed_shot_plan_and_material_tags(self) -> None:
        config = {
            "ai": {
                "apiKey": "ai-key",
                "baseUrl": "https://ai.example.test/v1",
                "model": "gpt-test",
                "maxTokens": 2200,
            }
        }
        response_text = json.dumps(
            {
                "score": 91,
                "hookScore": 94,
                "pacingScore": 88,
                "materialMatchScore": 90,
                "summary": "开头明确，细节镜头需求清楚。",
                "segments": [
                    {
                        "startSec": 0,
                        "endSec": 3,
                        "text": "开头钩子",
                        "role": "hook",
                        "shotType": "整体上身",
                        "materialTags": ["全身", "正面", "走动"],
                        "reason": "先展示整体变化。",
                    },
                    {
                        "startSec": 3,
                        "endSec": 8,
                        "text": "腰头细节",
                        "role": "detail_proof",
                        "shotType": "腰头特写",
                        "materialTags": ["纽扣", "腰头", "口袋"],
                        "reason": "对应产品设计细节。",
                    },
                ],
                "missingShots": ["面料垂坠特写"],
                "suggestions": ["收尾增加穿搭全景。"],
            },
            ensure_ascii=False,
        )
        with patch.object(server, "read_runtime_config", return_value=config), patch.object(
            server,
            "call_ai_chat",
            return_value={"choices": [{"message": {"content": response_text}}]},
        ):
            result = server.analyze_video_copy_entry(
                {
                    "title": "15 秒裤装文案",
                    "product": "阔腿裤",
                    "duration": 15,
                    "script": "0-3秒｜开头钩子\n3-8秒｜腰头细节",
                },
                "editor_01",
            )

        analysis = result["analysis"]
        self.assertEqual(analysis["score"], 91)
        self.assertEqual(len(analysis["segments"]), 2)
        self.assertEqual(analysis["segments"][0]["role"], "hook")
        self.assertEqual(analysis["segments"][1]["materialTags"], ["纽扣", "腰头", "口袋"])
        self.assertEqual(analysis["missingShots"], ["面料垂坠特写"])


if __name__ == "__main__":
    unittest.main()
