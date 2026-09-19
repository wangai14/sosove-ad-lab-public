from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SELECTOR_PATH = (
    Path.home()
    / ".codex"
    / "skills"
    / "japanese-fashion-video-editor"
    / "scripts"
    / "select_panel_materials.py"
)
SPEC = importlib.util.spec_from_file_location("select_panel_materials", SELECTOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load selector: {SELECTOR_PATH}")
SELECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SELECTOR)


class PanelMaterialSelectorTests(unittest.TestCase):
    def write_vault(self, root: Path, library: dict, pool: dict | None = None, ledger: dict | None = None) -> None:
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "material-library.json").write_text(json.dumps(library, ensure_ascii=False), encoding="utf-8")
        (data_dir / "auto-edit-pool.json").write_text(json.dumps(pool or {"clips": []}), encoding="utf-8")
        (data_dir / "chatcut-sync.json").write_text(json.dumps(ledger or {"requests": [], "assets": []}), encoding="utf-8")

    def args(self, vault_root: Path, **overrides: object) -> argparse.Namespace:
        values = {
            "vault_root": str(vault_root),
            "batch_id": "",
            "batch_name": "",
            "tag": [],
            "match_any_tag": False,
            "role": [],
            "status": ["ready"],
            "url": [],
            "project_id": "",
            "sync_request_id": "",
            "limit": 12,
            "json_out": "",
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_role_specific_fallback_duration(self) -> None:
        hook = SELECTOR.best_segment({"editRole": "hook", "technical": {"durationMs": 10000}}, [])
        try_on = SELECTOR.best_segment({"editRole": "try_on", "technical": {"durationMs": 10000}}, [])
        detail = SELECTOR.best_segment({"editRole": "detail", "technical": {"durationMs": 10000}}, [])
        self.assertEqual(hook["endMs"], 1800)
        self.assertEqual(try_on["endMs"], 2800)
        self.assertEqual(detail["endMs"], 2000)

    def test_status_filter_reports_unreadable_ready_item(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hold_path = root / "hold.mp4"
            hold_path.write_bytes(b"hold")
            library = {
                "batches": [{"id": "batch-a", "name": "SKU-A"}],
                "items": {
                    "http://panel/ready.mp4": {
                        "batchId": "batch-a",
                        "name": "ready.mp4",
                        "sourcePath": str(root / "missing.mp4"),
                        "analysisStatus": "ready",
                        "editRole": "hook",
                    },
                    "http://panel/hold.mp4": {
                        "batchId": "batch-a",
                        "name": "hold.mp4",
                        "sourcePath": str(hold_path),
                        "analysisStatus": "hold",
                        "editRole": "detail",
                    },
                },
            }
            self.write_vault(root, library)
            manifest = SELECTOR.build_manifest(self.args(root))
            self.assertEqual(manifest["summary"]["selected"], 0)
            self.assertEqual(manifest["summary"]["unresolved"], 1)
            self.assertEqual(manifest["unresolved"][0]["url"], "http://panel/ready.mp4")

    def test_sync_request_uses_exact_urls_and_skips_imported_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_path = root / "hook.mp4"
            second_path = root / "detail.mp4"
            extra_path = root / "extra.mp4"
            first_path.write_bytes(b"hook")
            second_path.write_bytes(b"detail")
            extra_path.write_bytes(b"extra")
            first_url = "http://panel/hook.mp4"
            second_url = "http://panel/detail.mp4"
            first_stat = first_path.stat()
            first_fingerprint = SELECTOR.material_fingerprint(
                str(first_path),
                first_stat.st_size,
                first_stat.st_mtime_ns,
                first_url,
            )
            project_id = "0eecd62e-f1ff-4446-8cb3-5d2ef5b5276f"
            library = {
                "batches": [{"id": "batch-a", "name": "SKU-A"}],
                "items": {
                    first_url: {
                        "batchId": "batch-a",
                        "name": "hook.mp4",
                        "sourcePath": str(first_path),
                        "analysisStatus": "ready",
                        "editRole": "hook",
                    },
                    second_url: {
                        "batchId": "batch-a",
                        "name": "detail.mp4",
                        "sourcePath": str(second_path),
                        "analysisStatus": "ready",
                        "editRole": "detail",
                    },
                    "http://panel/extra.mp4": {
                        "batchId": "batch-a",
                        "name": "extra.mp4",
                        "sourcePath": str(extra_path),
                        "analysisStatus": "ready",
                        "editRole": "try_on",
                    },
                },
            }
            ledger = {
                "requests": [
                    {
                        "id": "ccsync-test",
                        "projectId": project_id,
                        "productKey": "SKU-A",
                        "status": "queued",
                        "items": [
                            {"panelUrl": first_url, "status": "pending"},
                            {"panelUrl": second_url, "status": "pending"},
                        ],
                    }
                ],
                "assets": [
                    {
                        "projectId": project_id,
                        "fingerprint": first_fingerprint,
                        "chatcutAssetId": "asset-existing",
                        "status": "imported",
                    }
                ],
            }
            self.write_vault(root, library, ledger=ledger)
            manifest = SELECTOR.build_manifest(self.args(root, sync_request_id="ccsync-test"))
            self.assertEqual(manifest["syncRequest"]["id"], "ccsync-test")
            self.assertEqual(manifest["summary"]["selected"], 1)
            self.assertEqual(manifest["summary"]["skippedAlreadyImported"], 1)
            self.assertEqual(manifest["items"][0]["url"], second_url)
            self.assertNotIn("http://panel/extra.mp4", manifest["filters"]["urls"])
            self.assertEqual(manifest["skippedAlreadyImported"][0]["chatcutAssetId"], "asset-existing")


if __name__ == "__main__":
    unittest.main()
