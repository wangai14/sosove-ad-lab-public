from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from seedance_web import server


class MultiMarketCreationTests(unittest.TestCase):
    def test_market_language_defaults_follow_selected_country(self) -> None:
        self.assertEqual(server.get_creative_target_market({"targetMarket": "美国"}), "美国")
        self.assertEqual(server.get_creative_content_language({"targetMarket": "美国"}, "美国"), "美式英语")
        self.assertEqual(server.get_creative_content_language({"targetMarket": "韩国"}, "韩国"), "韩语")
        self.assertEqual(
            server.get_creative_content_language(
                {"targetMarket": "美国", "contentLanguage": "西班牙语"},
                "美国",
            ),
            "西班牙语",
        )

    def test_local_fallback_uses_market_without_japan_hardcoding(self) -> None:
        prompt = server.local_seedance_prompt(
            "pants",
            "斜扣阔腿牛仔裤",
            "9:16",
            10,
            target_market="美国",
            content_language="美式英语",
        )

        self.assertIn("目标市场为美国", prompt)
        self.assertIn("使用美式英语", prompt)
        self.assertNotIn("日本女性", prompt)
        self.assertNotIn("日本街头", prompt)

    def test_ai_prompt_generation_receives_and_locks_market_context(self) -> None:
        response = {"choices": [{"message": {"content": "模特转身展示斜扣阔腿牛仔裤，镜头停在腰头特写。"}}]}
        with (
            patch.object(server, "get_ai_model", return_value="test-model"),
            patch.object(server, "call_ai_chat", return_value=response) as call,
        ):
            prompt = server.generate_seedance_prompt(
                {
                    "brief": "斜扣阔腿牛仔裤，面向美国通勤女性",
                    "targetMarket": "美国",
                    "contentLanguage": "美式英语",
                    "ratio": "9:16",
                    "duration": 10,
                }
            )

        request_body = call.call_args.args[0]
        self.assertIn("cross-market", request_body["messages"][0]["content"])
        user_context = json.loads(request_body["messages"][1]["content"].split("\n\n", 1)[1])
        self.assertEqual(user_context["target_market"], "美国")
        self.assertEqual(user_context["content_language"], "美式英语")
        self.assertIn("目标市场为美国", prompt)
        self.assertIn("使用美式英语", prompt)

    def test_creation_form_exposes_market_and_language_controls(self) -> None:
        static_dir = Path(server.__file__).parent / "static"
        html = (static_dir / "index.html").read_text(encoding="utf-8")
        script = (static_dir / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="creative-market-input"', html)
        self.assertIn('id="creative-language-select"', html)
        self.assertIn('id="prompt-market-input"', html)
        self.assertIn('id="prompt-language-select"', html)
        self.assertIn('id="prompt-market-lock-state"', html)
        self.assertIn('<select id="prompt-market-input"', html)
        self.assertIn('<option value="美国">美国</option>', html)
        self.assertIn('<option value="__custom__">其他国家</option>', html)
        self.assertIn('id="prompt-custom-market-input"', html)
        self.assertIn('id="creative-custom-market-input"', html)
        self.assertIn("目标市场 / 国家", html)
        self.assertIn("MARKET_LOCALIZATION", script)
        self.assertIn("targetMarket: creativeMarketValue()", script)
        self.assertIn("contentLanguage: resolvedCreativeLanguage()", script)
        self.assertIn("function promptWithMarketLocalization", script)
        self.assertIn("function readMarketControl", script)
        self.assertIn("function writeMarketControl", script)
        self.assertIn("生成市场锁定（最高优先级）", script)
        self.assertIn("promptWithFaceSwapInstruction(promptWithMarketLocalization(basePrompt))", script)


if __name__ == "__main__":
    unittest.main()
