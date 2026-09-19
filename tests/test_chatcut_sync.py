from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seedance_web import server
from seedance_web.chatcut_sync import build_sync_request, clean_project_id, update_sync_request


PROJECT_ID = "0eecd62e-f1ff-4446-8cb3-5d2ef5b5276f"


class ChatCutSyncTests(unittest.TestCase):
    def make_library(self, root: Path, second_batch: bool = False) -> tuple[dict, list[str]]:
        first_path = root / "hook.mp4"
        second_path = root / "detail.mp4"
        first_path.write_bytes(b"hook-video")
        second_path.write_bytes(b"detail-video")
        urls = ["http://panel/hook.mp4", "http://panel/detail.mp4"]
        return (
            {
                "batches": [
                    {"id": "batch-a", "name": "SKU-A"},
                    {"id": "batch-b", "name": "SKU-B"},
                ],
                "items": {
                    urls[0]: {
                        "batchId": "batch-a",
                        "name": "hook.mp4",
                        "sourcePath": str(first_path),
                        "analysisStatus": "ready",
                        "editRole": "hook",
                        "tags": ["可剪辑", "优先混剪"],
                    },
                    urls[1]: {
                        "batchId": "batch-b" if second_batch else "batch-a",
                        "name": "detail.mp4",
                        "sourcePath": str(second_path),
                        "analysisStatus": "ready",
                        "editRole": "detail",
                        "tags": ["可剪辑", "优先混剪"],
                    },
                },
            },
            urls,
        )

    def test_clean_project_id_accepts_editor_url(self) -> None:
        value = clean_project_id(f"https://app.chatcut.io/zh/editor/{PROJECT_ID}")
        self.assertEqual(value, PROJECT_ID)

    def test_request_requires_product_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            with self.assertRaisesRegex(ValueError, "产品名或 SKU"):
                build_sync_request(library, {"projectId": PROJECT_ID, "urls": urls}, {})

    def test_request_rejects_mixed_batches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory), second_batch=True)
            with self.assertRaisesRegex(ValueError, "跨越多个批次"):
                build_sync_request(
                    library,
                    {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": urls},
                    {},
                )

    def test_import_update_creates_dedup_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            ledger, request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": urls},
                {},
                created_by="admin",
            )
            self.assertEqual(request["status"], "queued")
            self.assertEqual(request["summary"]["pending"], 2)
            first_item = request["items"][0]
            ledger, completed = update_sync_request(
                ledger,
                {
                    "requestId": request["id"],
                    "items": [
                        {
                            "fingerprint": first_item["fingerprint"],
                            "status": "imported",
                            "chatcutAssetId": "asset-123",
                        }
                    ],
                },
            )
            self.assertEqual(completed["summary"]["imported"], 1)
            self.assertEqual(len(ledger["assets"]), 1)

            next_ledger, next_request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": [urls[0]]},
                ledger,
            )
            self.assertEqual(next_request["status"], "complete")
            self.assertEqual(next_request["summary"]["alreadyImported"], 1)
            self.assertEqual(next_request["items"][0]["chatcutAssetId"], "asset-123")
            self.assertEqual(len(next_ledger["assets"]), 1)

    def test_ready_filter_and_unreadable_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            library["items"][urls[0]]["analysisStatus"] = "hold"
            Path(library["items"][urls[1]]["sourcePath"]).unlink()
            _, request = build_sync_request(
                library,
                {
                    "projectId": PROJECT_ID,
                    "productKey": "SKU-A",
                    "urls": urls,
                    "statuses": ["ready"],
                },
                {},
            )
            self.assertEqual(request["status"], "blocked")
            self.assertEqual(request["summary"]["total"], 1)
            self.assertEqual(request["summary"]["unresolved"], 1)
            self.assertEqual(request["items"][0]["panelUrl"], urls[1])

    def test_file_change_creates_new_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            ledger, request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": [urls[0]]},
                {},
            )
            first_item = request["items"][0]
            ledger, _ = update_sync_request(
                ledger,
                {
                    "requestId": request["id"],
                    "items": [
                        {
                            "fingerprint": first_item["fingerprint"],
                            "status": "imported",
                            "chatcutAssetId": "asset-old",
                        }
                    ],
                },
            )
            Path(library["items"][urls[0]]["sourcePath"]).write_bytes(b"hook-video-updated")
            _, changed_request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": [urls[0]]},
                ledger,
            )
            self.assertEqual(changed_request["status"], "queued")
            self.assertNotEqual(changed_request["items"][0]["fingerprint"], first_item["fingerprint"])
            self.assertEqual(changed_request["items"][0]["chatcutAssetId"], "")

    def test_partial_failure_can_resume_to_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            ledger, request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": urls},
                {},
            )
            first_item, second_item = request["items"]
            ledger, partial = update_sync_request(
                ledger,
                {
                    "requestId": request["id"],
                    "items": [
                        {
                            "fingerprint": first_item["fingerprint"],
                            "status": "imported",
                            "chatcutAssetId": "asset-1",
                        },
                        {
                            "fingerprint": second_item["fingerprint"],
                            "status": "failed",
                            "error": "temporary upload failure",
                        },
                    ],
                },
            )
            self.assertEqual(partial["status"], "partial")
            self.assertEqual(partial["summary"]["failed"], 1)

            ledger, syncing = update_sync_request(
                ledger,
                {
                    "requestId": request["id"],
                    "items": [{"fingerprint": second_item["fingerprint"], "status": "syncing"}],
                },
            )
            self.assertEqual(syncing["status"], "syncing")

            ledger, completed = update_sync_request(
                ledger,
                {
                    "requestId": request["id"],
                    "items": [
                        {
                            "fingerprint": second_item["fingerprint"],
                            "status": "imported",
                            "chatcutAssetId": "asset-2",
                        }
                    ],
                },
            )
            self.assertEqual(completed["status"], "complete")
            self.assertEqual(completed["summary"]["imported"], 2)
            self.assertEqual(len(ledger["assets"]), 2)

    def test_filter_snapshot_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            snapshot = {
                "scope": "filtered",
                "filterBatchId": "batch-a",
                "filterTag": "优先混剪",
                "status": "ready",
                "role": "detail",
                "search": "垂感",
                "requestedCount": 2,
            }
            _, request = build_sync_request(
                library,
                {
                    "projectId": PROJECT_ID,
                    "productKey": "SKU-A",
                    "scope": "filtered",
                    "urls": urls,
                    "filterSnapshot": snapshot,
                },
                {},
            )
            self.assertEqual(request["filterSnapshot"], snapshot)
            self.assertEqual([item["panelUrl"] for item in request["items"]], urls)

    def test_duplicate_active_request_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            ledger, first = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": urls},
                {},
            )
            next_ledger, duplicate = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": list(reversed(urls))},
                ledger,
            )
            self.assertEqual(duplicate["id"], first["id"])
            self.assertEqual(len(next_ledger["requests"]), 1)

    def test_preview_does_not_reuse_or_write_active_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            library, urls = self.make_library(Path(directory))
            active_ledger, active_request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": urls},
                {},
            )
            with (
                patch.object(server, "read_material_library", return_value=library),
                patch.object(server, "read_chatcut_sync_ledger", return_value=active_ledger),
                patch.object(server, "write_chatcut_sync_ledger") as write_ledger,
            ):
                preview = server.preview_chatcut_sync_request(
                    {"projectId": PROJECT_ID, "productKey": "SKU-A", "urls": urls},
                    created_by="admin",
                )

            self.assertTrue(preview["preview"])
            self.assertNotEqual(preview["id"], active_request["id"])
            self.assertEqual(preview["summary"]["pending"], 2)
            write_ledger.assert_not_called()

    def test_product_key_must_match_tagging_source_folder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "打标签" / "1343107-不规则斜扣阔腿牛仔裤2"
            root.mkdir(parents=True)
            source = root / "hook.mp4"
            source.write_bytes(b"video")
            url = "http://panel/hook.mp4"
            library = {
                "batches": [{"id": "batch-a", "name": "7.4号"}],
                "items": {
                    url: {
                        "batchId": "batch-a",
                        "name": source.name,
                        "sourcePath": str(source),
                        "analysisStatus": "ready",
                        "editRole": "hook",
                    }
                },
            }
            with self.assertRaisesRegex(ValueError, "素材目录不一致"):
                build_sync_request(
                    library,
                    {"projectId": PROJECT_ID, "productKey": "黑色法式修身长裙", "urls": [url]},
                    {},
                )
            _, request = build_sync_request(
                library,
                {"projectId": PROJECT_ID, "productKey": "1343107 不规则斜扣阔腿牛仔裤", "urls": [url]},
                {},
            )
            self.assertEqual(request["sourceProductLabel"], "1343107-不规则斜扣阔腿牛仔裤2")


if __name__ == "__main__":
    unittest.main()
