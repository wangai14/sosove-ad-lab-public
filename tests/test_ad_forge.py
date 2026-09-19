from __future__ import annotations

import base64
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from seedance_web import ad_forge
from seedance_web import server


class AdForgeProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_path = Path(self.temp_dir.name) / "ad-forge-projects.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_project_applies_defaults_and_owner(self) -> None:
        project = ad_forge.create_project(
            self.store_path,
            "alice",
            {"name": "夏日通勤裤", "productName": "斜扣阔腿牛仔裤", "shotCount": 4},
        )

        self.assertEqual(project["owner"], "alice")
        self.assertEqual(project["name"], "夏日通勤裤")
        self.assertEqual(project["productDescription"], "")
        self.assertEqual(project["settings"]["ratio"], "9:16")
        self.assertEqual(project["settings"]["imageSize"], "auto")
        self.assertEqual(project["settings"]["totalDuration"], 20)
        self.assertEqual(len(project["shots"]), 4)
        self.assertEqual(project["shots"][0]["generationMode"], "multimodal")
        self.assertEqual(project["shots"][0]["referencePrivacyMode"], "product-only")
        self.assertEqual(project["shots"][0]["imageGenerationMode"], "auto")
        self.assertEqual(project["shots"][0]["imageGenerationRoute"], "")
        self.assertEqual(project["shots"][0]["imageReferenceCount"], 0)
        self.assertEqual(project["shots"][0]["imageReferenceAssets"], [])
        self.assertEqual(project["shots"][0]["referenceVideos"], [])
        self.assertTrue(self.store_path.exists())

    def test_projects_are_user_scoped_and_admin_can_see_all(self) -> None:
        alice = ad_forge.create_project(self.store_path, "alice", {"name": "A"})
        bob = ad_forge.create_project(self.store_path, "bob", {"name": "B"})

        self.assertEqual([item["id"] for item in ad_forge.list_projects(self.store_path, "alice")], [alice["id"]])
        self.assertEqual(
            {item["id"] for item in ad_forge.list_projects(self.store_path, "root", is_admin=True)},
            {alice["id"], bob["id"]},
        )

    def test_non_owner_cannot_read_or_update_project(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "Private"})

        with self.assertRaises(ad_forge.ProjectNotFound):
            ad_forge.get_project(self.store_path, project["id"], "bob")
        with self.assertRaises(ad_forge.ProjectNotFound):
            ad_forge.update_project(self.store_path, project["id"], "bob", {"name": "Taken"})

    def test_update_project_normalizes_settings_and_brief(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "Draft"})
        updated = ad_forge.update_project(
            self.store_path,
            project["id"],
            "alice",
            {
                "name": "  New name  ",
                "productDescription": "  深灰色宽松吊带裤，垂坠面料  ",
                "brief": {"summary": "  展示真实通勤穿搭  ", "sellingPoints": ["斜扣腰头", "", "垂感"]},
                "settings": {"shotCount": 6, "totalDuration": 30, "ratio": "16:9", "imageSize": "1024x1024", "market": "美国"},
            },
        )

        self.assertEqual(updated["name"], "New name")
        self.assertEqual(updated["productDescription"], "深灰色宽松吊带裤，垂坠面料")
        self.assertEqual(updated["brief"]["summary"], "展示真实通勤穿搭")
        self.assertEqual(updated["brief"]["sellingPoints"], ["斜扣腰头", "垂感"])
        self.assertEqual(updated["settings"]["shotCount"], 6)
        self.assertEqual(updated["settings"]["ratio"], "16:9")
        self.assertEqual(updated["settings"]["imageSize"], "1024x1024")
        self.assertEqual(len(updated["shots"]), 6)

    def test_archive_hides_project_from_default_list(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "Archive me"})
        ad_forge.archive_project(self.store_path, project["id"], "alice", True)

        self.assertEqual(ad_forge.list_projects(self.store_path, "alice"), [])
        archived = ad_forge.list_projects(self.store_path, "alice", include_archived=True)
        self.assertEqual(archived[0]["id"], project["id"])
        self.assertTrue(archived[0]["archived"])

    def test_store_is_valid_json_after_multiple_writes(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "Stable"})
        ad_forge.update_project(self.store_path, project["id"], "alice", {"currentStep": 2})

        payload = json.loads(self.store_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["projects"][0]["currentStep"], 2)

    def test_shot_reference_videos_are_persisted_and_limited(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "References"})
        shot_id = project["shots"][0]["id"]
        videos = [
            {"url": "https://cdn.example.com/motion-a.mp4", "name": "walk", "durationMs": 6000},
            {"url": "https://cdn.example.com/motion-b.mp4", "name": "turn", "durationMs": 7000},
        ]

        updated = ad_forge.update_shot(
            self.store_path,
            project["id"],
            "alice",
            shot_id,
            {"referenceVideos": videos, "generationMode": "prompt-only"},
        )

        self.assertEqual([item["url"] for item in updated["shots"][0]["referenceVideos"]], [item["url"] for item in videos])
        self.assertEqual([item["durationMs"] for item in updated["shots"][0]["referenceVideos"]], [6000, 7000])
        self.assertEqual(updated["shots"][0]["generationMode"], "prompt-only")
        with self.assertRaises(ad_forge.InvalidProject):
            ad_forge.update_shot(
                self.store_path,
                project["id"],
                "alice",
                shot_id,
                {"referenceVideos": [*videos, {"url": "https://cdn.example.com/too-long.mp4", "durationMs": 3000}]},
            )

    def test_reference_privacy_mode_is_persisted_and_normalized(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "Privacy"})
        updated = ad_forge.update_shot(
            self.store_path,
            project["id"],
            "alice",
            project["shots"][0]["id"],
            {"referencePrivacyMode": "direct"},
        )
        self.assertEqual(updated["shots"][0]["referencePrivacyMode"], "direct")

        normalized = ad_forge.normalize_shot({"referencePrivacyMode": "invalid"}, 0, 1, 5)
        self.assertEqual(normalized["referencePrivacyMode"], "product-only")

    def test_shot_image_generation_mode_is_persisted_and_normalized(self) -> None:
        project = ad_forge.create_project(self.store_path, "alice", {"name": "Image mode"})
        shot_id = project["shots"][0]["id"]

        updated = ad_forge.update_shot(
            self.store_path,
            project["id"],
            "alice",
            shot_id,
            {"imageGenerationMode": "reference"},
        )

        self.assertEqual(updated["shots"][0]["imageGenerationMode"], "reference")
        updated["shots"][0]["imageGenerationMode"] = "unsupported"
        self.assertEqual(ad_forge.normalize_project(updated)["shots"][0]["imageGenerationMode"], "auto")


class AdForgeStoryboardTests(unittest.TestCase):
    def project(self, **overrides):
        base = ad_forge.new_project_payload(
            "alice",
            {
                "productName": "斜扣阔腿牛仔裤",
                "brief": {
                    "summary": "为日本通勤女性制作真实自然的短视频广告",
                    "sellingPoints": ["斜扣腰头", "垂感", "一裤多穿"],
                },
                "settings": {"shotCount": 4, "totalDuration": 20, "market": "日本", "language": "日语"},
            },
        )
        base.update(overrides)
        return base

    def test_fallback_storyboard_is_complete_and_duration_balanced(self) -> None:
        shots = ad_forge.build_fallback_storyboard(self.project())

        self.assertEqual(len(shots), 4)
        self.assertEqual(sum(shot["duration"] for shot in shots), 20)
        self.assertEqual([shot["order"] for shot in shots], [1, 2, 3, 4])
        self.assertTrue(all(shot["prompt"] for shot in shots))
        self.assertEqual(shots[0]["role"], "hook")
        self.assertEqual(shots[-1]["role"], "cta")

    def test_parse_storyboard_response_accepts_fenced_json_and_fills_missing_fields(self) -> None:
        raw = """```json
        {"shots":[
          {"title":"问题钩子","role":"hook","scene":"通勤前的镜前试穿","prompt":"模特展示腰头"},
          {"title":"结构细节","role":"detail","scene":"腰头近景","prompt":"手指向斜扣"}
        ]}
        ```"""
        project = self.project()
        project["settings"]["shotCount"] = 2
        project["settings"]["totalDuration"] = 10

        shots = ad_forge.parse_storyboard_response(raw, project)

        self.assertEqual(len(shots), 2)
        self.assertEqual(sum(shot["duration"] for shot in shots), 10)
        self.assertEqual(shots[1]["title"], "结构细节")
        self.assertIn("斜扣", shots[1]["prompt"])

    def test_reorder_and_task_result_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "projects.json"
            project = ad_forge.create_project(path, "alice", {"name": "Tasks"})
            shot_ids = [shot["id"] for shot in project["shots"]]

            reordered = ad_forge.reorder_shots(path, project["id"], "alice", list(reversed(shot_ids)))
            self.assertEqual([shot["id"] for shot in reordered["shots"]], list(reversed(shot_ids)))
            self.assertEqual([shot["order"] for shot in reordered["shots"]], [1, 2, 3, 4])

            shot_id = reordered["shots"][0]["id"]
            linked = ad_forge.update_shot(
                path,
                project["id"],
                "alice",
                shot_id,
                {"taskId": "task-123", "status": "generating"},
            )
            self.assertEqual(linked["shots"][0]["taskId"], "task-123")

            completed = ad_forge.update_shot(
                path,
                project["id"],
                "alice",
                shot_id,
                {"status": "completed", "videoUrl": "https://cdn.example.com/result.mp4"},
            )
            self.assertEqual(completed["shots"][0]["videoUrl"], "https://cdn.example.com/result.mp4")
            self.assertEqual(completed["progress"]["videosReady"], 1)

    def test_image_generation_metadata_is_normalized_and_counted(self) -> None:
        project = self.project()
        project["shots"] = ad_forge.build_fallback_storyboard(project)
        project["shots"][0].update(
            {
                "referenceImage": "http://127.0.0.1/generated.png",
                "imagePrompt": "深灰色吊带裤全身静态关键帧",
                "referenceImageSource": "generated",
                "imageModel": "gpt-image-2",
                "imageSize": "1024x1536",
                "imageGeneratedAt": "2026-08-15T10:00:00Z",
                "imageGenerationRoute": "edits",
                "imageReferenceCount": 99,
                "imageReferenceAssets": ["http://127.0.0.1/uploads/images/product.png"],
            }
        )

        normalized = ad_forge.normalize_project(project)

        self.assertEqual(normalized["shots"][0]["referenceImageSource"], "generated")
        self.assertEqual(normalized["shots"][0]["imagePrompt"], "深灰色吊带裤全身静态关键帧")
        self.assertEqual(normalized["shots"][0]["imageModel"], "gpt-image-2")
        self.assertEqual(normalized["shots"][0]["imageSize"], "1024x1536")
        self.assertEqual(normalized["shots"][0]["imageGenerationRoute"], "edits")
        self.assertEqual(normalized["shots"][0]["imageReferenceCount"], 1)
        self.assertEqual(normalized["shots"][0]["imageReferenceAssets"], ["http://127.0.0.1/uploads/images/product.png"])
        self.assertEqual(normalized["progress"]["imagesReady"], 1)

    def test_composition_inputs_only_include_successful_non_excluded_shots(self) -> None:
        project = self.project()
        project["shots"] = ad_forge.build_fallback_storyboard(project)
        project["shots"][0]["videoUrl"] = "https://cdn.example.com/a.mp4"
        project["shots"][1]["videoUrl"] = "https://cdn.example.com/b.mp4"
        project["shots"][1]["excluded"] = True

        clips = ad_forge.composition_clips(project)

        self.assertEqual(clips, ["https://cdn.example.com/a.mp4"])

    def test_composition_requires_at_least_one_video(self) -> None:
        with self.assertRaises(ad_forge.InvalidProject):
            ad_forge.composition_clips(self.project())


class AdForgeStaticContractTests(unittest.TestCase):
    def test_server_registers_page_and_api_routes(self) -> None:
        source = Path(server.__file__).read_text(encoding="utf-8")
        self.assertIn('"/ad-forge.html"', source)
        self.assertIn('"/api/ad-forge/projects"', source)
        self.assertIn('"/api/ad-forge/storyboard"', source)
        self.assertIn('"/api/ad-forge/skill/generate-prompts"', source)
        self.assertIn('"/api/ad-forge/images/generate"', source)
        self.assertIn('"/api/ad-forge/images/cancel"', source)
        self.assertIn('"/api/ad-forge/compose"', source)

    def test_frontend_exposes_five_step_workflow_and_task_integration(self) -> None:
        static_dir = Path(server.__file__).parent / "static"
        html = (static_dir / "ad-forge.html").read_text(encoding="utf-8")
        script = (static_dir / "ad-forge.js").read_text(encoding="utf-8")
        styles = (static_dir / "ad-forge.css").read_text(encoding="utf-8")

        for label in ["需求", "分镜", "提示词", "视频", "合成"]:
            self.assertIn(label, html)
        self.assertIn('id="project-list"', html)
        self.assertIn('id="storyboard-grid"', html)
        self.assertIn('id="shot-inspector"', html)
        self.assertIn('id="timeline-track"', html)
        self.assertIn('"/api/tasks"', script)
        self.assertIn('"/api/ad-forge/storyboard"', script)
        self.assertIn('"/api/ad-forge/images/generate"', script)
        self.assertIn('"/api/ad-forge/images/cancel"', script)
        self.assertIn("cancelImage(shot.id)", script)
        self.assertIn('id="generate-all-images-button"', html)
        self.assertIn('id="generate-image-button"', html)
        self.assertIn('id="product-description-input"', html)
        self.assertIn('id="generate-skill-prompts-button"', html)
        self.assertIn('id="prompt-model-state"', html)
        self.assertIn('id="image-model-state"', html)
        self.assertIn("Images Generations + Edits", html)
        self.assertIn('id="video-model-state"', html)
        self.assertIn('id="service-node-summary"', html)
        self.assertIn('<details class="service-node-panel" id="service-node-panel">', html)
        self.assertIn('id="service-node-models"', html)
        self.assertIn('data-service-node="ai"', html)
        self.assertIn('data-service-node="image"', html)
        self.assertIn('data-service-node="ark"', html)
        self.assertIn('id="test-prompt-node-button"', html)
        self.assertIn('id="test-image-node-button"', html)
        self.assertIn('id="test-video-node-button"', html)
        self.assertIn('id="shot-image-prompt-input"', html)
        self.assertIn('id="image-generation-mode-select"', html)
        self.assertIn('id="image-generation-reference-state"', html)
        self.assertIn("强制使用参考图", html)
        self.assertIn('id="generation-mode-select"', html)
        self.assertIn('id="reference-privacy-mode-select"', html)
        self.assertIn('id="reference-image-list"', html)
        self.assertIn('id="shot-reference-video-input"', html)
        self.assertIn('id="reference-video-list"', html)
        self.assertIn('id="inspector-collapse-button"', html)
        self.assertIn('id="inspector-reopen-button"', html)
        self.assertIn('id="task-confirm-dialog"', html)
        self.assertIn('aria-label="允许生成背景音乐与环境声"', html)
        self.assertIn('aria-label="允许生成字幕、利益点和 CTA"', html)
        self.assertIn('id="reference-quickbar"', html)
        self.assertIn('id="quick-upload-reference-button"', html)
        self.assertIn('id="quick-upload-reference-video-button"', html)
        self.assertIn('id="quick-reference-image-count"', html)
        self.assertIn('id="quick-reference-video-count"', html)
        self.assertIn('id="manage-reference-button"', html)
        self.assertIn('id="image-size-select"', html)
        self.assertIn('object-fit: contain', styles)
        self.assertIn("--skill-purple", styles)
        self.assertIn('"/api/ad-forge/skill/generate-prompts"', script)
        self.assertIn("state.capabilities.aiModel", script)
        self.assertIn("state.capabilities.imageBaseUrl", script)
        self.assertIn('protocol: "Images Generations + Edits"', script)
        self.assertIn('`/api/config/test/${kind}`', script)
        self.assertIn("testServiceNode", script)
        self.assertIn("state.capabilities.seedanceModel", script)
        self.assertIn("state.capabilities.seedanceEndpoint", script)
        self.assertIn("state.capabilities.inlineLocalImages", script)
        self.assertIn("projectId: state.project.id", script)
        self.assertIn("本机参考图会由服务端自动安全内嵌", script)
        self.assertIn("商品隐私模式", script)
        self.assertIn("referencePrivacyMode", script)
        self.assertIn("Faces are intentionally removed for privacy", script)
        self.assertIn("friendlyShotError", script)
        self.assertIn("confirmTaskBatch", script)
        self.assertIn("stepCompletionState", script)
        self.assertIn("shot-card-error", script)
        self.assertIn("window.innerWidth <= 1080", script)
        self.assertIn("当前已启用商品隐私模式", script)
        self.assertIn("refVideoDurationsMs", script)
        self.assertIn("uploadReferenceVideos", script)
        self.assertIn("renderReferenceQuickbar", script)
        self.assertIn("openReferenceManager", script)
        self.assertIn("imageGenerationMode", script)
        self.assertIn('imageGenerationMode: "reference"', script)
        self.assertIn("sourceReferenceImageUrls", script)
        self.assertIn("imageGenerationRoute", script)
        self.assertIn("原图驱动", script)
        self.assertIn("toggleProjectReferenceImage", script)
        self.assertIn("/images/edits", script)
        self.assertIn("--vermilion", styles)
        self.assertIn("--sumi: #162a30", styles)
        self.assertIn("--atelier: #2f7475", styles)
        self.assertIn("--surface: #fcfefd", styles)
        self.assertIn(".stage-heading::after", styles)
        self.assertIn(".shot-card.is-selected::after", styles)
        self.assertIn("repeat(auto-fit, minmax(min(100%, 560px), 1fr))", styles)
        self.assertIn(":focus-visible", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)
        self.assertIn("@media (max-width: 760px)", styles)
        self.assertIn("overflow-x: hidden", styles)
        self.assertIn("clamp(480px, 22vw, 560px)", styles)
        self.assertIn("@media (max-width: 1080px)", styles)
        self.assertIn("width: min(680px, calc(100vw - 24px))", styles)
        self.assertIn("max-width: calc(100vw - 24px)", styles)
        self.assertIn(".inspector-preview .shot-art { width: 100%; max-height: none; }", styles)
        self.assertNotIn(".inspector-preview { min-height: 220px; max-height: 440px", styles)
        self.assertIn("#shot-prompt-input { min-height: 210px; }", styles)
        self.assertIn("max-height: 260px", styles)
        self.assertIn("body.inspector-collapsed", styles)
        self.assertIn("position: sticky", styles)
        self.assertIn(".task-confirm-dialog", styles)
        self.assertIn(".shot-card-error", styles)
        self.assertIn("max-height: calc(100vh - var(--header-height) - var(--workflow-height) - var(--timeline-height) - 8px)", styles)

    def test_completed_shot_video_can_play_inside_the_site(self) -> None:
        static_dir = Path(server.__file__).parent / "static"
        html = (static_dir / "ad-forge.html").read_text(encoding="utf-8")
        script = (static_dir / "ad-forge.js").read_text(encoding="utf-8")
        styles = (static_dir / "ad-forge.css").read_text(encoding="utf-8")

        self.assertIn('id="video-player-modal"', html)
        self.assertIn('id="video-player-video" controls autoplay playsinline', html)
        self.assertIn('id="video-player-download"', html)
        self.assertIn('data-action="play-video"', script)
        self.assertIn("function openVideoPlayer(shot)", script)
        self.assertIn("function closeVideoPlayer()", script)
        self.assertIn("elements.videoPlayerVideo.play()", script)
        self.assertIn("elements.videoPlayerVideo.pause()", script)
        self.assertIn(".video-player-modal", styles)
        self.assertIn(".shot-play-overlay", styles)


class AdForgeReferenceRequestTests(unittest.TestCase):
    def test_seedance_body_includes_image_and_video_references(self) -> None:
        body = server.build_seedance_body(
            {
                "prompt": "模特向前走两步",
                "ratio": "9:16",
                "duration": 5,
                "model": "doubao-seedance-2-0-260128",
                "refImages": ["https://cdn.example.com/product.jpg"],
                "refVideos": ["https://cdn.example.com/motion.mp4"],
                "refVideoDurationsMs": [7000],
            }
        )

        self.assertEqual([item["type"] for item in body["content"]], ["text", "image_url", "video_url"])
        self.assertEqual(body["content"][1]["role"], "reference_image")
        self.assertEqual(body["content"][2]["role"], "reference_video")

    def test_seedance_body_inlines_local_png_jpeg_and_webp_references(self) -> None:
        fixtures = [
            ("product.png", b"\x89PNG\r\n\x1a\n" + b"png-bytes", "image/png"),
            ("product.jpg", b"\xff\xd8\xff\xe0" + b"jpeg-bytes", "image/jpeg"),
            ("product.webp", b"RIFF\x10\x00\x00\x00WEBP" + b"webp-bytes", "image/webp"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            urls = []
            for filename, content, _content_type in fixtures:
                path = Path(temp_dir) / filename
                path.write_bytes(content)
                paths.append(path)
                urls.append(f"http://127.0.0.1:8799/uploads/images/{filename}")

            with mock.patch.object(server, "resolve_ad_forge_reference_image_url", side_effect=paths):
                body = server.build_seedance_body(
                    {
                        "projectId": "ad-1111111111111111",
                        "prompt": "保持商品一致并轻微转身",
                        "ratio": "9:16",
                        "duration": 5,
                        "refImages": urls,
                    }
                )

        image_items = body["content"][1:]
        self.assertEqual(len(image_items), 3)
        for item, (_filename, content, content_type) in zip(image_items, fixtures):
            encoded_url = item["image_url"]["url"]
            self.assertTrue(encoded_url.startswith(f"data:{content_type};base64,"))
            self.assertEqual(base64.b64decode(encoded_url.split(",", 1)[1]), content)
        self.assertNotIn("127.0.0.1", json.dumps(body))

    def test_seedance_body_rejects_oversized_local_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "oversized.png"
            image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * server.MAX_IMAGE_UPLOAD_BYTES)
            with mock.patch.object(server, "resolve_ad_forge_reference_image_url", return_value=image_path):
                with self.assertRaisesRegex(ValueError, "10MB"):
                    server.build_seedance_body(
                        {
                            "prompt": "测试",
                            "ratio": "9:16",
                            "duration": 5,
                            "refImages": ["http://127.0.0.1:8799/uploads/images/oversized.png"],
                        }
                    )

    def test_seedance_body_rejects_inline_image_total_limit(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"small"
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "product.png"
            image_path.write_bytes(png)
            with (
                mock.patch.object(server, "resolve_ad_forge_reference_image_url", return_value=image_path),
                mock.patch.object(server, "MAX_SEEDANCE_INLINE_IMAGE_TOTAL_BYTES", len(png) + 1),
            ):
                with self.assertRaisesRegex(ValueError, "合计不能超过 32MB"):
                    server.build_seedance_body(
                        {
                            "prompt": "测试",
                            "ratio": "9:16",
                            "duration": 5,
                            "refImages": [
                                "http://127.0.0.1:8799/uploads/images/one.png",
                                "http://127.0.0.1:8799/uploads/images/two.png",
                            ],
                        }
                    )

    def test_seedance_body_rejects_local_video_with_actionable_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "本机或局域网参考视频"):
            server.build_seedance_body(
                {
                    "prompt": "参考动作",
                    "ratio": "9:16",
                    "duration": 5,
                    "refVideos": ["http://127.0.0.1:8799/uploads/videos/motion.mp4"],
                    "refVideoDurationsMs": [5000],
                }
            )

    def test_public_request_hides_inline_base64(self) -> None:
        inline_url = "data:image/png;base64," + base64.b64encode(b"secret-image").decode("ascii")
        body = {
            "model": "doubao-seedance-2-0-260128",
            "content": [
                {"type": "text", "text": "测试"},
                {"type": "image_url", "image_url": {"url": inline_url}, "role": "reference_image"},
            ],
        }

        public_body = server.public_seedance_request_body(body)

        self.assertIn("预览已隐藏", public_body["content"][1]["image_url"]["url"])
        self.assertNotIn(base64.b64encode(b"secret-image").decode("ascii"), json.dumps(public_body))
        self.assertEqual(body["content"][1]["image_url"]["url"], inline_url)

    def test_product_only_reference_masks_face_area_and_preserves_garment_area(self) -> None:
        from PIL import Image, ImageDraw

        source = Image.new("RGB", (200, 300), (238, 238, 238))
        draw = ImageDraw.Draw(source)
        draw.ellipse((70, 10, 130, 80), fill=(210, 150, 120))
        draw.rectangle((45, 115, 155, 285), fill=(40, 80, 150))
        raw = io.BytesIO()
        source.save(raw, format="PNG")

        content_type, masked_bytes = server.build_seedance_product_only_reference(raw.getvalue(), "image/png")
        masked = Image.open(io.BytesIO(masked_bytes)).convert("RGB")

        self.assertEqual(content_type, "image/png")
        self.assertNotEqual(masked.getpixel((100, 45)), source.getpixel((100, 45)))
        self.assertEqual(masked.getpixel((100, 200)), source.getpixel((100, 200)))

    def test_seedance_body_applies_product_privacy_mode_to_local_image(self) -> None:
        from PIL import Image

        source = Image.new("RGB", (160, 240), (230, 230, 230))
        raw = io.BytesIO()
        source.save(raw, format="JPEG")
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "product.jpg"
            image_path.write_bytes(raw.getvalue())
            with mock.patch.object(server, "resolve_ad_forge_reference_image_url", return_value=image_path):
                body = server.build_seedance_body(
                    {
                        "prompt": "只参考服装",
                        "ratio": "9:16",
                        "duration": 5,
                        "refImages": ["http://127.0.0.1:8799/uploads/images/product.jpg"],
                        "referencePrivacyMode": "product-only",
                    }
                )

        encoded_url = body["content"][1]["image_url"]["url"]
        self.assertTrue(encoded_url.startswith("data:image/png;base64,"))
        self.assertNotIn("127.0.0.1", encoded_url)

    def test_product_privacy_mode_rejects_unmanaged_public_image(self) -> None:
        with self.assertRaisesRegex(ValueError, "先把公网图片上传"):
            server.build_seedance_body(
                {
                    "prompt": "测试",
                    "ratio": "9:16",
                    "duration": 5,
                    "refImages": ["https://cdn.example.com/person.jpg"],
                    "referencePrivacyMode": "product-only",
                }
            )

    def test_privacy_error_is_translated_to_actionable_chinese(self) -> None:
        class FakeError:
            code = 400

            @staticmethod
            def read():
                return json.dumps(
                    {
                        "error": {
                            "code": "InputImageSensitiveContentDetected.PrivacyInformation",
                            "message": "The input image may contain real person",
                        }
                    }
                ).encode("utf-8")

        message = server.read_error_message(FakeError())
        self.assertIn("商品隐私模式", message)
        self.assertIn("Asset ID", message)

    def test_seedance_body_rejects_reference_video_limit_violations(self) -> None:
        payload = {
            "prompt": "动作参考测试",
            "ratio": "9:16",
            "duration": 5,
            "model": "doubao-seedance-2-0-260128",
            "refVideos": [f"https://cdn.example.com/{index}.mp4" for index in range(4)],
            "refVideoDurationsMs": [3000, 3000, 3000, 3000],
        }
        with self.assertRaises(ValueError):
            server.build_seedance_body(payload)

        payload["refVideos"] = payload["refVideos"][:3]
        payload["refVideoDurationsMs"] = [6000, 6000, 4000]
        with self.assertRaises(ValueError):
            server.build_seedance_body(payload)


class AdForgeImageGenerationTests(unittest.TestCase):
    def project(self) -> dict:
        project = ad_forge.new_project_payload(
            "alice",
            {
                "productName": "斜扣阔腿牛仔裤",
                "productDescription": "深蓝色斜扣阔腿牛仔裤，交叉腰头，垂坠宽腿版型",
                "brief": {
                    "summary": "为日本通勤女性制作真实自然的短视频广告",
                    "audience": "25–40 岁日本通勤女性",
                    "sellingPoints": ["斜扣腰头", "垂感"],
                },
                "settings": {"shotCount": 2, "totalDuration": 10, "ratio": "9:16"},
            },
        )
        project["shots"] = ad_forge.build_fallback_storyboard(project)
        return project

    def test_image_prompt_preserves_product_facts_and_editability(self) -> None:
        project = self.project()

        prompt = server.build_ad_forge_image_prompt(project, project["shots"][0])

        self.assertIn("斜扣阔腿牛仔裤", prompt)
        self.assertIn("斜扣腰头", prompt)
        self.assertIn("Do not create", prompt)
        self.assertIn("baked-in text", prompt)

    def test_image_generation_prefers_the_dedicated_image_prompt(self) -> None:
        project = self.project()
        project["shots"][0]["imagePrompt"] = "单张静态关键帧，斜扣腰头近景，柔和窗光。"
        project["shots"][0]["prompt"] = "VIDEO_ONLY_MODEL_WALKS_TWO_STEPS"

        prompt = server.build_ad_forge_image_prompt(project, project["shots"][0])

        self.assertIn("单张静态关键帧", prompt)
        self.assertNotIn("VIDEO_ONLY_MODEL_WALKS_TWO_STEPS", prompt)

    def test_seedance_skill_generates_image_and_video_prompt_pairs(self) -> None:
        project = self.project()
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "shots": [
                                    {
                                        "role": "hook",
                                        "title": "版型第一眼",
                                        "scene": "街角咖啡店外的全身展示",
                                        "camera": "稳定缓慢推近",
                                        "imagePrompt": "深蓝色阔腿牛仔裤全身静态关键帧",
                                        "videoPrompt": "模特向前走两步，镜头稳定后退并停在全身构图。",
                                        "copy": "自然垂坠",
                                        "duration": 5,
                                    },
                                    {
                                        "role": "cta",
                                        "title": "细节收束",
                                        "scene": "腰头细节与完整裤型",
                                        "camera": "近景后回到全身",
                                        "imagePrompt": "斜扣交叉腰头静态细节关键帧",
                                        "videoPrompt": "手指向斜扣结构，镜头从腰头近景平稳回到全身。",
                                        "copy": "今すぐチェック",
                                        "duration": 5,
                                    },
                                ]
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }
        with (
            mock.patch.object(server, "read_runtime_config", return_value={}),
            mock.patch.object(server, "get_ai_model", return_value="test-model"),
            mock.patch.object(server, "get_ai_api_key", return_value="test-key"),
            mock.patch.object(server, "get_ai_max_tokens", return_value=4000),
            mock.patch.object(server, "load_ad_forge_prompt_skill_context", return_value=("LOCAL RULES", ["SKILL.md"])),
            mock.patch.object(server, "build_seedance_review_skill_status", return_value={"name": "seedance-20", "version": "6.7.0", "exists": True}),
            mock.patch.object(server, "call_ai_chat", return_value=response) as call_ai,
        ):
            shots, skill, model = server.generate_ad_forge_skill_prompts(project)

        self.assertEqual(len(shots), 2)
        self.assertIn("静态关键帧", shots[0]["imagePrompt"])
        self.assertIn("向前走两步", shots[0]["prompt"])
        self.assertEqual(skill["version"], "6.7.0")
        self.assertEqual(model, "test-model")
        system_prompt = call_ai.call_args.args[0]["messages"][0]["content"]
        self.assertIn("LOCAL RULES", system_prompt)
        self.assertIn("图片提示词", system_prompt)

    def test_seedance_skill_requires_product_description(self) -> None:
        project = self.project()
        project["productDescription"] = ""

        with self.assertRaises(ad_forge.InvalidProject):
            server.generate_ad_forge_skill_prompts(project)

    def test_image_size_can_follow_video_ratio_or_use_explicit_canvas(self) -> None:
        self.assertEqual(server.ad_forge_image_size("9:16"), "1024x1536")
        self.assertEqual(server.ad_forge_image_size("16:9"), "1536x1024")
        self.assertEqual(server.ad_forge_image_size("1:1"), "1024x1024")
        self.assertEqual(server.ad_forge_image_size("16:9", "1024x1536"), "1024x1536")
        self.assertEqual(server.ad_forge_image_size("9:16", "invalid"), "1024x1536")

    def test_invalid_image_size_is_normalized_to_auto(self) -> None:
        settings = ad_forge.normalize_settings({"ratio": "16:9", "imageSize": "2048x2048"})

        self.assertEqual(settings["imageSize"], "auto")

    def test_reference_mode_requires_an_available_image(self) -> None:
        project = self.project()
        shot = project["shots"][0]
        shot["imageGenerationMode"] = "reference"

        with self.assertRaises(ad_forge.InvalidProject):
            server.resolve_ad_forge_image_references(project, shot)

    def test_reference_mode_rejects_generated_keyframe_as_product_source(self) -> None:
        project = self.project()
        shot = project["shots"][0]
        shot["imageGenerationMode"] = "reference"
        shot["referenceImage"] = f"http://127.0.0.1:8799/ad-forge-images/{project['id']}/frame.png"

        with mock.patch.object(server, "resolve_ad_forge_reference_image_url", return_value=Path("frame.png")):
            with self.assertRaises(ad_forge.InvalidProject):
                server.resolve_ad_forge_image_references(project, shot)

    def test_prompt_mode_skips_reference_resolution(self) -> None:
        project = self.project()
        shot = project["shots"][0]
        shot["imageGenerationMode"] = "prompt"
        shot["referenceAssets"] = ["http://127.0.0.1:8799/uploads/images/product.png"]

        with mock.patch.object(server, "resolve_ad_forge_reference_image_url") as resolve_reference:
            self.assertEqual(server.resolve_ad_forge_image_references(project, shot), [])

        resolve_reference.assert_not_called()

    def test_original_product_reference_is_preferred_over_generated_frame(self) -> None:
        project = self.project()
        shot = project["shots"][0]
        uploaded_url = "http://127.0.0.1:8799/uploads/images/product.png"
        generated_url = f"http://127.0.0.1:8799/ad-forge-images/{project['id']}/frame.png"
        shot["referenceImage"] = generated_url
        shot["referenceAssets"] = [generated_url, uploaded_url]
        uploaded_path = Path("product.png")
        generated_path = Path("frame.png")

        def resolve_reference(url, _project_id):
            return uploaded_path if url == uploaded_url else generated_path

        with mock.patch.object(server, "resolve_ad_forge_reference_image_url", side_effect=resolve_reference):
            references = server.resolve_ad_forge_image_references(project, shot)

        self.assertEqual(references, [uploaded_path])

    def test_image_edit_request_uses_multipart_without_leaking_local_path(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"reference-image-bytes"

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"data": []}'

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "product-reference.png"
            image_path.write_bytes(png)
            with (
                mock.patch.object(server, "get_ad_forge_image_api_key", return_value="test-key"),
                mock.patch.object(server, "get_ad_forge_image_model", return_value="gpt-image-2"),
                mock.patch.object(server, "build_ad_forge_image_edit_endpoint", return_value="https://images.example/v1/images/edits"),
                mock.patch.object(server, "urlopen", return_value=FakeResponse()) as open_request,
            ):
                server.call_ad_forge_image_api("keep the product", "9:16", reference_images=[image_path])

            request = open_request.call_args.args[0]
            request_body = request.data
            self.assertEqual(request.full_url, "https://images.example/v1/images/edits")
            self.assertTrue(request.get_header("Content-type").startswith("multipart/form-data; boundary="))
            self.assertIn(b'name="image"; filename="product-reference.png"', request_body)
            self.assertIn(png, request_body)
            self.assertNotIn(str(Path(temp_dir)).encode("utf-8"), request_body)

    def test_reference_generation_puts_product_lock_first_and_returns_trace(self) -> None:
        project = self.project()
        shot = project["shots"][0]
        reference_url = "http://127.0.0.1:8799/uploads/images/product.png"
        generated_png = b"\x89PNG\r\n\x1a\n" + b"generated"

        with tempfile.TemporaryDirectory() as temp_dir:
            reference_path = Path(temp_dir) / "product.png"
            reference_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"reference")
            output_root = Path(temp_dir) / "outputs"
            with (
                mock.patch.object(server, "resolve_ad_forge_image_reference_entries", return_value=[(reference_url, reference_path)]),
                mock.patch.object(
                    server,
                    "call_ad_forge_image_api",
                    return_value={"data": [{"b64_json": base64.b64encode(generated_png).decode("ascii")}]},
                ) as call_image,
            ):
                _local_path, prompt, _image_size, reference_urls = server.generate_ad_forge_image(
                    project,
                    shot,
                    output_root,
                )

        self.assertTrue(prompt.startswith("PRODUCT LOCK — HIGHEST PRIORITY"))
        self.assertLess(prompt.index("PRODUCT LOCK"), prompt.index("Product description"))
        self.assertIn("reference images override every conflicting sentence", prompt)
        self.assertEqual(reference_urls, [reference_url])
        self.assertEqual(call_image.call_args.kwargs["reference_images"], [reference_path])

    def test_image_generation_without_references_uses_generation_endpoint(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"data": []}'

        with (
            mock.patch.object(server, "get_ad_forge_image_api_key", return_value="test-key"),
            mock.patch.object(server, "get_ad_forge_image_model", return_value="gpt-image-2"),
            mock.patch.object(server, "build_ad_forge_image_endpoint", return_value="https://images.example/v1/images/generations"),
            mock.patch.object(server, "urlopen", return_value=FakeResponse()) as open_request,
        ):
            server.call_ad_forge_image_api("new keyframe", "9:16")

        request = open_request.call_args.args[0]
        self.assertEqual(request.full_url, "https://images.example/v1/images/generations")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data.decode("utf-8"))["model"], "gpt-image-2")

    def test_reference_file_validation_rejects_wrong_magic_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "fake.png"
            image_path.write_bytes(b"this-is-not-a-png")

            with self.assertRaises(server.AdForgeImageError):
                server.read_ad_forge_reference_image(image_path)

    def test_reference_resolution_rejects_cross_project_generated_image(self) -> None:
        with self.assertRaises(FileNotFoundError):
            server.resolve_ad_forge_reference_image_url(
                "/ad-forge-images/ad-1111111111111111/frame.png",
                "ad-2222222222222222",
            )

    def test_reference_resolution_rejects_upload_path_traversal(self) -> None:
        with self.assertRaises(ValueError):
            server.resolve_ad_forge_reference_image_url("/uploads/images/../../secret.png")

    def test_image_cancel_request_is_scoped_and_cleaned_up(self) -> None:
        request_id = "img-0123456789abcdef0123456789abcdef"
        event = server.register_ad_forge_image_request(request_id, "alice", "ad-project", "shot-1")
        try:
            self.assertFalse(server.cancel_ad_forge_image_request(request_id, "bob", "ad-project", "shot-1"))
            self.assertFalse(event.is_set())
            self.assertTrue(server.cancel_ad_forge_image_request(request_id, "alice", "ad-project", "shot-1"))
            self.assertTrue(event.is_set())
        finally:
            server.finish_ad_forge_image_request(request_id, event)
        self.assertFalse(server.cancel_ad_forge_image_request(request_id, "alice", "ad-project", "shot-1"))

    def test_committed_image_request_cannot_be_cancelled_after_completion(self) -> None:
        request_id = "img-fedcba9876543210fedcba9876543210"
        event = server.register_ad_forge_image_request(request_id, "alice", "ad-project", "shot-1")

        self.assertTrue(server.commit_ad_forge_image_request(request_id, event))
        self.assertFalse(server.cancel_ad_forge_image_request(request_id, "alice", "ad-project", "shot-1"))

    def test_cancelled_image_result_is_not_saved(self) -> None:
        project = self.project()
        event = threading.Event()
        png = b"\x89PNG\r\n\x1a\n" + b"cancelled-image"

        def cancelled_response(*_args, **_kwargs):
            event.set()
            return {"data": [{"b64_json": base64.b64encode(png).decode("ascii")}]}

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            server,
            "call_ad_forge_image_api",
            side_effect=cancelled_response,
        ):
            with self.assertRaises(server.AdForgeImageCancelled):
                server.generate_ad_forge_image(
                    project,
                    project["shots"][0],
                    Path(temp_dir),
                    cancel_event=event,
                )
            self.assertEqual(list(Path(temp_dir).rglob("*")), [])

    def test_extract_and_save_generated_png(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"test-image"
        response = {"data": [{"b64_json": base64.b64encode(png).decode("ascii")}]}

        content, suffix = server.extract_ad_forge_image_bytes(response)

        self.assertEqual(content, png)
        self.assertEqual(suffix, ".png")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = server.save_ad_forge_image(
                "ad-0123456789abcdef",
                "shot-123",
                content,
                suffix,
                Path(temp_dir),
            )
            target = Path(temp_dir) / "ad-0123456789abcdef" / Path(path).name
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), png)

    def test_extract_rejects_non_image_payload(self) -> None:
        response = {"data": [{"b64_json": base64.b64encode(b"not-an-image").decode("ascii")}]}

        with self.assertRaises(server.AdForgeImageError):
            server.extract_ad_forge_image_bytes(response)

    def test_external_plain_http_image_endpoint_is_rejected(self) -> None:
        with self.assertRaises(server.AdForgeImageError):
            server.get_ad_forge_image_base_url({"imageGeneration": {"baseUrl": "http://example.com/v1"}})


if __name__ == "__main__":
    unittest.main()
