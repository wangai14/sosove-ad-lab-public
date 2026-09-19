from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seedance_web import server


class MaterialPlaybackProxyTests(unittest.TestCase):
    def test_resolves_registered_video_by_stored_or_current_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            source.write_bytes(b"video")
            library = {
                "items": {
                    "http://127.0.0.1:8794/uploads/videos/source.mp4": {
                        "kind": "video",
                        "sourcePath": str(source),
                        "localPath": "/uploads/videos/source.mp4",
                        "technical": {"videoCodec": "hevc"},
                    }
                }
            }
            item, resolved = server.resolve_material_playback_source(
                "http://10.0.0.25:8794/uploads/videos/source.mp4",
                library,
            )
            self.assertEqual(resolved, source)
            self.assertEqual(item["technical"]["videoCodec"], "hevc")

    def test_hevc_proxy_uses_h264_faststart_and_reuses_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mp4"
            source.write_bytes(b"hevc-source")
            cache = root / "playback-cache"
            item = {"kind": "video", "technical": {"videoCodec": "hevc"}}

            def fake_run(command: list[str], **_: object):
                Path(command[-1]).write_bytes(b"h264-proxy")
                return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with (
                patch.object(server, "FFMPEG_BIN", "ffmpeg"),
                patch.object(server, "OBSIDIAN_PLAYBACK_PROXY_DIR", cache),
                patch.object(server.subprocess, "run", side_effect=fake_run) as run_mock,
            ):
                first = server.ensure_browser_playback_video(source, item)
                second = server.ensure_browser_playback_video(source, item)

            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), b"h264-proxy")
            self.assertEqual(run_mock.call_count, 1)
            command = run_mock.call_args.args[0]
            self.assertIn("libx264", command)
            self.assertIn("yuv420p", command)
            self.assertIn("+faststart", command)

    def test_h264_source_does_not_create_proxy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            source.write_bytes(b"h264-source")
            item = {"kind": "video", "technical": {"videoCodec": "h264"}}
            with patch.object(server.subprocess, "run") as run_mock:
                result = server.ensure_browser_playback_video(source, item)
            self.assertEqual(result, source)
            run_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
