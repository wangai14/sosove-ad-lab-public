from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from scripts.chatcut_sync_queue import (
    executor_status_path,
    find_request,
    read_ledger,
    request_payload,
    update_items,
    write_executor_heartbeat,
    write_ledger,
)
from seedance_web.chatcut_sync import build_sync_request


PROJECT_ID = "0eecd62e-f1ff-4446-8cb3-5d2ef5b5276f"


class ChatCutSyncQueueTests(unittest.TestCase):
    def make_queue(self, root: Path) -> tuple[Path, dict]:
        source = root / "hook.mp4"
        source.write_bytes(b"video")
        panel_url = "http://panel/hook.mp4"
        library = {
            "batches": [{"id": "batch-a", "name": "SKU-A"}],
            "items": {
                panel_url: {
                    "batchId": "batch-a",
                    "name": source.name,
                    "sourcePath": str(source),
                    "analysisStatus": "ready",
                    "editRole": "hook",
                    "tags": ["开头钩子", "优先混剪"],
                }
            },
        }
        ledger, request = build_sync_request(
            library,
            {
                "projectId": PROJECT_ID,
                "productKey": "SKU-A",
                "urls": [panel_url],
            },
            {},
        )
        path = root / "chatcut-sync.json"
        write_ledger(ledger, path)
        return path, request

    def test_next_claim_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, original = self.make_queue(Path(directory))
            selected = find_request(read_ledger(path))
            self.assertIsNotNone(selected)
            self.assertEqual(request_payload(selected)["requestId"], original["id"])

            claimed = update_items(
                original["id"],
                [
                    {
                        "fingerprint": original["items"][0]["fingerprint"],
                        "status": "syncing",
                    }
                ],
                path,
            )
            self.assertEqual(claimed["status"], "syncing")
            self.assertEqual(claimed["summary"]["syncing"], 1)

            completed = update_items(
                original["id"],
                [
                    {
                        "fingerprint": original["items"][0]["fingerprint"],
                        "status": "imported",
                        "chatcutAssetId": "asset-123",
                    }
                ],
                path,
            )
            self.assertEqual(completed["status"], "complete")
            self.assertEqual(completed["summary"]["imported"], 1)
            self.assertEqual(len(read_ledger(path)["assets"]), 1)

    def test_inaccessible_project_can_be_marked_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, original = self.make_queue(Path(directory))
            blocked = update_items(
                original["id"],
                [
                    {
                        "fingerprint": original["items"][0]["fingerprint"],
                        "status": "unresolved",
                        "error": "ChatCut project access lost",
                    }
                ],
                path,
            )
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(blocked["summary"]["unresolved"], 1)

    def test_executor_heartbeat_is_written_next_to_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "chatcut-sync.json"
            payload = write_executor_heartbeat(
                ledger,
                state="syncing",
                action="claim",
                request_id="ccsync-test",
            )
            status_path = executor_status_path(ledger)
            saved = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "syncing")
            self.assertEqual(saved["requestId"], "ccsync-test")
            self.assertTrue(saved["lastSeenAt"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
