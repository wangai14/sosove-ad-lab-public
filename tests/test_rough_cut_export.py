from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "export_rough_cut.py"
SPEC = importlib.util.spec_from_file_location("export_rough_cut", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load rough cut exporter: {SCRIPT_PATH}")
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


class RoughCutExportTests(unittest.TestCase):
    def test_normalize_clips_preserves_source_and_output_timecodes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.mp4"
            second = root / "second.mp4"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            clips = EXPORTER.normalize_clips(
                {
                    "clips": [
                        {
                            "name": "hook.mp4",
                            "sourcePath": str(first),
                            "sourceStartMs": 500,
                            "sourceEndMs": 2500,
                            "role": "hook",
                            "copyText": "opening",
                        },
                        {
                            "name": "detail.mp4",
                            "sourcePath": str(second),
                            "sourceStartMs": 1000,
                            "sourceEndMs": 15000,
                            "role": "detail",
                        },
                    ]
                },
                root,
            )

        self.assertEqual(clips[0]["durationMs"], 2000)
        self.assertEqual(clips[0]["outputStartMs"], 0)
        self.assertEqual(clips[1]["durationMs"], 12000)
        self.assertEqual(clips[1]["outputStartMs"], 2000)
        self.assertEqual(clips[1]["outputEndMs"], 14000)

    def test_ffmpeg_command_exports_silent_vertical_video(self) -> None:
        command = EXPORTER.ffmpeg_clip_command(
            "ffmpeg",
            {"sourcePath": "source.mp4", "sourceStartMs": 1200, "durationMs": 2400},
            Path("output.mp4"),
            1080,
            1920,
        )
        self.assertIn("-an", command)
        self.assertIn("libx264", command)
        self.assertIn("scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920", command[command.index("-vf") + 1])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for the rough cut integration test.")
    def test_export_writes_video_timeline_report_and_obsidian_index(self) -> None:
        ffmpeg = str(shutil.which("ffmpeg"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            data_dir.mkdir(parents=True)
            source = root / "source.mp4"
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x22aa88:s=180x320:d=3",
                    "-vf",
                    "fps=30,format=yuv420p",
                    "-c:v",
                    "libx264",
                    str(source),
                ],
                check=True,
            )
            selected = root / "selected.json"
            selected.write_text(
                json.dumps(
                    {
                        "clips": [
                            {
                                "name": "source.mp4",
                                "sourcePath": str(source),
                                "sourceStartMs": 0,
                                "sourceEndMs": 1300,
                                "role": "hook",
                                "copyText": "hook copy",
                            },
                            {
                                "name": "source.mp4",
                                "sourcePath": str(source),
                                "sourceStartMs": 1400,
                                "sourceEndMs": 2700,
                                "role": "detail",
                                "copyText": "detail copy",
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = EXPORTER.export_rough_cut(
                argparse.Namespace(
                    vault_root=str(root),
                    selected_clips_file=str(selected),
                    name="test rough cut",
                    target_ratio="9:16",
                    ffmpeg=ffmpeg,
                    timeout_seconds=60,
                    json=True,
                )
            )
            record = result["record"]
            timeline = json.loads(Path(record["timelinePath"]).read_text(encoding="utf-8"))
            index = json.loads((data_dir / "rough-cuts.json").read_text(encoding="utf-8"))

            self.assertTrue(Path(record["videoPath"]).exists())
            self.assertTrue((root / record["obsidianReportPath"]).exists())
            self.assertEqual(record["clipCount"], 2)
            self.assertEqual(record["totalDurationMs"], 2600)
            self.assertEqual(timeline["clips"][1]["outputStartMs"], 1300)
            self.assertEqual(index["roughCuts"][0]["id"], record["id"])


if __name__ == "__main__":
    unittest.main()
