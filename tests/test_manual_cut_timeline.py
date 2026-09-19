from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seedance_web import server


class ManualCutTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.static_dir = Path(__file__).resolve().parents[1] / "static"
        cls.html = (cls.static_dir / "materials.html").read_text(encoding="utf-8")
        cls.script = (cls.static_dir / "materials.js").read_text(encoding="utf-8")
        cls.styles = (cls.static_dir / "styles.css").read_text(encoding="utf-8")

    def test_manual_timeline_exposes_source_range_and_clip_tags(self) -> None:
        for element_id in (
            "material-manual-source-select",
            "material-manual-source-player",
            "material-manual-in-input",
            "material-manual-out-input",
            "material-manual-range-duration",
            "material-manual-add-range-btn",
            "material-manual-timeline-track",
            "material-manual-selected-role",
            "material-manual-selected-tag-input",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("function addManualRangeFromWorkspace", self.script)
        self.assertIn("function renderManualTimeline", self.script)
        self.assertIn("function renderManualRangeDuration", self.script)
        self.assertIn("function addTagsToSelectedManualClip", self.script)
        self.assertIn('href="#material-manual-cut-section">手动分段</a>', self.html)
        self.assertIn('id="material-manual-cut-section"', self.html)
        self.assertIn("function jumpToMaterialSection", self.script)
        self.assertIn("if (state.libraryLoaded)", self.script)
        self.assertIn(".material-manual-timeline-clip", self.styles)

    def test_material_workflow_exposes_guided_precut_entry(self) -> None:
        for element_id in (
            "material-workflow-next-btn",
            "material-workflow-steps",
            "material-workflow-batch-count",
            "material-workflow-pending-count",
            "material-workflow-ready-count",
            "material-workflow-match-score",
            "material-match-precut-btn",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("function renderWorkflowWorkbench", self.script)
        self.assertIn("function prepareProductPrecut", self.script)
        self.assertIn("function runWorkflowAction", self.script)
        self.assertIn(".material-workflow-steps", self.styles)

    def test_product_draft_quality_and_gap_recovery_controls_exist(self) -> None:
        for element_id in (
            "material-product-draft-save-state",
            "material-restore-product-draft-btn",
            "material-clear-product-draft-btn",
            "material-product-quality-checks",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        for function_name in (
            "function saveProductDraft",
            "function restoreProductDraft",
            "function renderProductQualityChecks",
            "function rewriteMissingCopy",
            "function createMissingShotPrompt",
        ):
            self.assertIn(function_name, self.script)
        self.assertIn("生成补镜提示词", self.script)
        self.assertIn(".material-product-quality-checks", self.styles)

    def test_panel_media_urls_follow_current_page_origin(self) -> None:
        start = self.script.index("const PANEL_MEDIA_PATH_PREFIXES")
        end = self.script.index("function cleanUrl", start)
        helper_script = self.script[start:end]
        probe = f"""
global.window = {{ location: {{
  origin: "http://10.0.0.25:8794",
  href: "http://10.0.0.25:8794/materials.html"
}} }};
{helper_script}
console.log(JSON.stringify({{
  stale: playableMaterialUrl("http://127.0.0.1:8794/uploads/videos/demo.mp4?token=1"),
  relative: playableMaterialUrl("/rough-cuts/demo/preview.mp4"),
  external: playableMaterialUrl("https://cdn.example.com/media/demo.mp4"),
  externalUpload: playableMaterialUrl("https://cdn.example.com/uploads/demo.mp4"),
  hevcProxy: playableVideoUrl({{
    url: "http://127.0.0.1:8794/uploads/videos/demo.mp4",
    technical: {{videoCodec: "hevc"}}
  }}),
  h264Direct: playableVideoUrl({{
    url: "http://127.0.0.1:8794/uploads/videos/demo.mp4",
    technical: {{videoCodec: "h264"}}
  }})
}}));
"""
        completed = subprocess.run(
            ["node", "-e", probe],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["stale"], "http://10.0.0.25:8794/uploads/videos/demo.mp4?token=1")
        self.assertEqual(result["relative"], "http://10.0.0.25:8794/rough-cuts/demo/preview.mp4")
        self.assertEqual(result["external"], "https://cdn.example.com/media/demo.mp4")
        self.assertEqual(result["externalUpload"], "https://cdn.example.com/uploads/demo.mp4")
        self.assertEqual(
            result["hevcProxy"],
            "http://10.0.0.25:8794/playback-material?url=http%3A%2F%2F127.0.0.1%3A8794%2Fuploads%2Fvideos%2Fdemo.mp4",
        )
        self.assertEqual(result["h264Direct"], "http://10.0.0.25:8794/uploads/videos/demo.mp4")
        self.assertIn("elements.manualSourcePlayer.src = videoUrl", self.script)
        self.assertIn("elements.videoLightboxPlayer.src = videoUrl", self.script)
        self.assertIn("<video src=\"${escapeHtml(videoUrl)}\"", self.script)

    def test_manual_draft_normalization_keeps_role_and_tags(self) -> None:
        draft = server.normalize_manual_cut_draft(
            {
                "activeBatchId": "batch-a",
                "clips": [
                    {
                        "id": "clip-1",
                        "url": "http://panel/video.mp4",
                        "startMs": 1200,
                        "endMs": 3600,
                        "role": "detail",
                        "tags": ["斜扣", "细节特写"],
                    },
                    {
                        "id": "too-short",
                        "url": "http://panel/video.mp4",
                        "startMs": 0,
                        "endMs": 500,
                    },
                ],
            }
        )
        self.assertEqual(len(draft["clips"]), 1)
        self.assertEqual(draft["clips"][0]["role"], "detail")
        self.assertEqual(draft["clips"][0]["tags"], ["斜扣", "细节特写"])

    def test_manual_draft_writes_json_and_obsidian_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_file = root / "data" / "manual-cut-draft.json"
            report_file = root / "analysis" / "手动分段草稿.md"
            draft_file.parent.mkdir(parents=True)
            report_file.parent.mkdir(parents=True)
            library = {
                "items": {
                    "http://panel/video.mp4": {"name": "斜扣牛仔裤.mp4"},
                }
            }
            with (
                patch.object(server, "MANUAL_CUT_DRAFT_FILE", draft_file),
                patch.object(server, "MANUAL_CUT_DRAFT_REPORT_FILE", report_file),
                patch.object(server, "ensure_obsidian_material_dirs"),
                patch.object(server, "sync_obsidian_project_data"),
                patch.object(server, "read_material_library", return_value=library),
            ):
                saved = server.write_manual_cut_draft(
                    {
                        "clips": [
                            {
                                "id": "clip-1",
                                "url": "http://panel/video.mp4",
                                "startMs": 1000,
                                "endMs": 4000,
                                "role": "hook",
                                "tags": ["开头钩子"],
                                "note": "第一眼清楚",
                            }
                        ]
                    }
                )
            self.assertTrue(draft_file.exists())
            self.assertTrue(report_file.exists())
            self.assertEqual(saved["clips"][0]["role"], "hook")
            self.assertIn("斜扣牛仔裤.mp4", report_file.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(draft_file.read_text(encoding="utf-8"))["clips"][0]["tags"], ["开头钩子"])

    def test_manual_labels_override_ai_segment_when_exporting_draft(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request_dir = Path(directory)
            url = "http://panel/video.mp4"
            library = {
                "items": {
                    url: {
                        "kind": "video",
                        "name": "video.mp4",
                        "technical": {"durationMs": 10000},
                        "editRole": "hook",
                        "analysis": {
                            "segments": [
                                {
                                    "id": "seg-1",
                                    "startMs": 0,
                                    "endMs": 3000,
                                    "role": "hook",
                                    "score": 90,
                                    "tags": ["AI钩子"],
                                }
                            ]
                        },
                    }
                }
            }
            with (
                patch.object(server, "DRAFT_REQUEST_DIR", request_dir),
                patch.object(server, "read_material_library", return_value=library),
            ):
                path = server.write_selected_jianying_clips(
                    [
                        {
                            "url": url,
                            "startMs": 0,
                            "endMs": 3000,
                            "segmentId": "seg-1",
                            "role": "detail",
                            "segmentTags": ["手动细节", "斜扣"],
                        }
                    ],
                    8,
                )
            clip = json.loads(Path(path).read_text(encoding="utf-8"))["clips"][0]
            self.assertEqual(clip["role"], "detail")
            self.assertEqual(clip["segmentTags"], ["手动细节", "斜扣"])


if __name__ == "__main__":
    unittest.main()
