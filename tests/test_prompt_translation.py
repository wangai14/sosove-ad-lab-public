from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from seedance_web import server


class PromptTranslationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "ai": {
                "apiKey": "ai-key",
                "baseUrl": "https://ai.example.test/v1",
                "model": "gpt-test",
            },
            "translation": {
                "model": "translator-test",
                "temperature": 0.3,
                "maxTokens": 2200,
            },
        }

    def test_translation_uses_ai_key_fallback_and_normalizes_json(self) -> None:
        response_text = json.dumps(
            {
                "translation": "こちらは人気商品です。",
                "alternateTranslation": "当店で特に人気のアイテムです。",
                "backTranslation": "这是很受欢迎的商品。",
                "consistencyScore": 94,
                "consistencyNotes": ["商品卖点保持一致"],
                "compliance": {"riskLevel": "low", "flaggedTerms": [], "suggestions": []},
            },
            ensure_ascii=False,
        )
        with patch.object(server, "read_runtime_config", return_value=self.config), patch.object(
            server, "call_ai_chat", return_value={"choices": [{"message": {"content": response_text}}]}
        ):
            result = server.translate_prompt_text(
                {
                    "text": "这是很受欢迎的商品。",
                    "sourceLanguage": "zh-CN",
                    "targetLanguage": "ja-JP",
                    "market": "Japan",
                    "scene": "voiceover",
                    "tone": "natural",
                    "backTranslation": True,
                    "dualPass": True,
                    "complianceAudit": True,
                    "preserveFormat": True,
                }
            )
        self.assertEqual(result["translation"], "こちらは人気商品です。")
        self.assertEqual(result["alternateTranslation"], "当店で特に人気のアイテムです。")
        self.assertEqual(result["consistencyScore"], 94)
        self.assertEqual(result["model"], "translator-test")

    def test_translation_config_reports_ai_fallback(self) -> None:
        config = server.build_config_response(self.config)["config"]["translation"]
        self.assertTrue(config["hasApiKey"])
        self.assertTrue(config["usingAiFallback"])
        self.assertEqual(config["model"], "translator-test")

    def test_translation_prompt_requires_native_daily_speech(self) -> None:
        response_text = json.dumps(
            {
                "translation": "これ、今かなり人気なんです。",
                "alternateTranslation": "最近よく選ばれているアイテムです。",
                "backTranslation": "这个最近很受欢迎。",
                "consistencyScore": 95,
                "consistencyNotes": [],
                "compliance": {"riskLevel": "low", "flaggedTerms": [], "suggestions": []},
            },
            ensure_ascii=False,
        )
        with patch.object(server, "read_runtime_config", return_value=self.config), patch.object(
            server,
            "call_ai_chat",
            return_value={"choices": [{"message": {"content": response_text}}]},
        ) as call:
            server.translate_prompt_text(
                {
                    "text": "这是我们店最受欢迎的商品。",
                    "sourceLanguage": "zh-CN",
                    "targetLanguage": "ja-JP",
                    "market": "Japan",
                    "scene": "voiceover",
                    "tone": "natural",
                }
            )

        request_body = call.call_args.args[0]
        system_prompt = request_body["messages"][0]["content"]
        user_context = json.loads(request_body["messages"][1]["content"])
        self.assertIn("native-language adaptation", system_prompt)
        self.assertIn("ready to read aloud", system_prompt)
        self.assertIn("Japanese fashion ecommerce", user_context["native_localization_brief"]["language_guidance"])
        self.assertIn("short spoken beats", user_context["native_localization_brief"]["language_guidance"])

    def test_compliance_check_flags_risky_ad_language_and_returns_replacement(self) -> None:
        response_text = json.dumps(
            {
                "riskLevel": "medium",
                "summary": "One absolute claim needs a softer phrase.",
                "flaggedTerms": [
                    {
                        "term": "guaranteed to make your legs look longer",
                        "category": "absolute promise",
                        "reason": "Guarantee language is an unsupported promise.",
                        "suggestion": "designed to create a longer-looking silhouette",
                    }
                ],
                "suggestions": ["Use appearance-focused wording instead of a guarantee."],
            },
            ensure_ascii=False,
        )
        with patch.object(server, "read_runtime_config", return_value=self.config), patch.object(
            server,
            "call_ai_chat",
            return_value={"choices": [{"message": {"content": response_text}}]},
        ) as call:
            result = server.check_translated_ad_copy(
                {
                    "text": "These jeans are guaranteed to make your legs look longer.",
                    "targetLanguage": "en-US",
                    "market": "United States",
                    "scene": "voiceover",
                }
            )

        review = result["compliance"]
        self.assertEqual(review["riskLevel"], "medium")
        self.assertEqual(review["flaggedTerms"][0]["term"], "guaranteed to make your legs look longer")
        self.assertEqual(review["flaggedTerms"][0]["suggestion"], "designed to create a longer-looking silhouette")
        system_prompt = call.call_args.args[0]["messages"][0]["content"]
        self.assertIn("medical or efficacy claims", system_prompt)
        self.assertIn("absolute or guaranteed language", system_prompt)

    def test_translation_config_probe_target_is_supported(self) -> None:
        with patch.object(server, "read_runtime_config", return_value=self.config):
            result = server.validate_runtime_config({"testMode": "config"}, kind="translation")
        self.assertIn("translation", result)
        self.assertTrue(result["translation"]["ok"])

    def test_translation_connectivity_probe_uses_translation_config(self) -> None:
        with patch.object(server, "read_runtime_config", return_value=self.config):
            with patch.object(
                server,
                "probe_translation_runtime",
                return_value={"ok": True, "networkOk": True},
            ) as probe:
                result = server.validate_runtime_config({"testMode": "connectivity"}, kind="translation")
        self.assertEqual(result, {"translation": {"ok": True, "networkOk": True}})
        probe.assert_called_once()
        probe_config, probe_mode = probe.call_args.args
        self.assertEqual(probe_mode, "connectivity")
        self.assertEqual(probe_config["translation"], self.config["translation"])


if __name__ == "__main__":
    unittest.main()
