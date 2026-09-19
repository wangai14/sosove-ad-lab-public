from __future__ import annotations

import io
import unittest
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from seedance_web import server


def runtime_config() -> dict:
    return {
        "ark": {
            "apiKey": "ark-test-key",
            "endpoint": "https://ark.example.test/api/v3/contents/generations/tasks",
            "model": "seedance-test-model",
        },
        "ai": {
            "apiKey": "ai-test-key",
            "baseUrl": "https://ai.example.test/v1",
            "model": "gpt-test-model",
            "temperature": 0.7,
            "maxTokens": 700,
        },
        "imageGeneration": {
            "apiKey": "image-test-key",
            "baseUrl": "https://images.example.test/v1",
            "model": "gpt-image-test",
        },
        "elevenlabs": {},
    }


class ConfigProbeTests(unittest.TestCase):
    def test_ai_invoke_reports_model_reply(self) -> None:
        with patch.object(server, "call_ai_chat", return_value={"choices": [{"message": {"content": "OK"}}]}):
            result = server.probe_ai_runtime(runtime_config(), "invoke")
        self.assertTrue(result["ok"])
        self.assertTrue(result["networkOk"])
        self.assertTrue(result["modelOk"])
        self.assertEqual(result["reply"], "OK")

    def test_ark_connectivity_treats_method_rejection_as_reachable(self) -> None:
        error = HTTPError(
            url="https://ark.example.test/api/v3/contents/generations/tasks",
            code=HTTPStatus.METHOD_NOT_ALLOWED,
            msg="method not allowed",
            hdrs=None,
            fp=io.BytesIO(b'{"message":"method not allowed"}'),
        )
        with patch.object(server, "urlopen", side_effect=error):
            result = server.probe_ark_runtime(runtime_config(), "connectivity")
        self.assertTrue(result["networkOk"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["httpStatus"], 405)

    def test_ai_invoke_marks_auth_error(self) -> None:
        error = server.AiError(HTTPStatus.UNAUTHORIZED, "invalid api key")
        with patch.object(server, "call_ai_chat", side_effect=error):
            result = server.probe_ai_runtime(runtime_config(), "invoke")
        self.assertFalse(result["ok"])
        self.assertTrue(result["networkOk"])
        self.assertFalse(result["authOk"])
        self.assertEqual(result["httpStatus"], 401)

    def test_config_response_exposes_masked_image_generation_details(self) -> None:
        with patch.object(server, "read_ad_forge_image_private_config", return_value={}):
            image = server.build_config_response(runtime_config())["config"]["imageGeneration"]

        self.assertEqual(image["baseUrl"], "https://images.example.test/v1")
        self.assertEqual(image["model"], "gpt-image-test")
        self.assertTrue(image["hasApiKey"])
        self.assertNotIn("image-test-key", image["apiKeyPreview"])

    def test_image_connectivity_checks_models_without_generating_an_image(self) -> None:
        response = MagicMock()
        response.status = 200
        response.read.return_value = b'{"data":[{"id":"gpt-image-test"}]}'
        response.__enter__.return_value = response

        with patch.object(server, "read_ad_forge_image_private_config", return_value={}), patch.object(server, "urlopen", return_value=response) as opener:
            result = server.probe_image_runtime(runtime_config(), "connectivity")

        self.assertTrue(result["ok"])
        self.assertTrue(result["networkOk"])
        self.assertTrue(result["modelOk"])
        self.assertEqual(result["httpStatus"], 200)
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, "https://images.example.test/v1/models")
        self.assertEqual(request.get_method(), "GET")

    def test_image_connectivity_marks_gateway_error(self) -> None:
        error = HTTPError(
            url="https://images.example.test/v1/models",
            code=HTTPStatus.BAD_GATEWAY,
            msg="bad gateway",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"upstream unavailable"}'),
        )
        with patch.object(server, "read_ad_forge_image_private_config", return_value={}), patch.object(server, "urlopen", side_effect=error):
            result = server.probe_image_runtime(runtime_config(), "connectivity")

        self.assertFalse(result["ok"])
        self.assertTrue(result["networkOk"])
        self.assertEqual(result["httpStatus"], 502)

    def test_runtime_image_config_overrides_legacy_private_config(self) -> None:
        legacy = {"apiKey": "legacy-key", "baseUrl": "https://legacy.example.test/v1", "model": "legacy-image"}
        with patch.object(server, "read_ad_forge_image_private_config", return_value=legacy):
            self.assertEqual(server.get_ad_forge_image_api_key(runtime_config()), "image-test-key")
            self.assertEqual(server.get_ad_forge_image_base_url(runtime_config()), "https://images.example.test/v1")
            self.assertEqual(server.get_ad_forge_image_model(runtime_config()), "gpt-image-test")

    def test_frontend_exposes_image_generation_configuration(self) -> None:
        html = (server.STATIC_DIR / "index.html").read_text(encoding="utf-8")
        script = (server.STATIC_DIR / "app.js").read_text(encoding="utf-8")

        for field_id in ["image-summary-state", "image-api-key-input", "image-base-url-input", "image-model-input"]:
            self.assertIn(f'id="{field_id}"', html)
        self.assertIn("imageGenerationBaseUrl", script)
        self.assertIn("imageGenerationModel", script)


if __name__ == "__main__":
    unittest.main()
