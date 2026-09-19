from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from seedance_web import server


class OperationsCenterTests(unittest.TestCase):
    def test_material_library_can_skip_slow_metadata_hydration(self) -> None:
        with TemporaryDirectory() as temp_dir:
            library_file = Path(temp_dir) / "material-library.json"
            library_file.write_text('{"version": 1, "batches": [], "items": {}}', encoding="utf-8")
            with (
                patch.object(server, "MATERIAL_LIBRARY_FILE", library_file),
                patch.object(server, "ensure_obsidian_material_dirs"),
                patch.object(server, "hydrate_material_library_metadata") as hydrate,
            ):
                library = server.read_material_library(hydrate_metadata=False)

        hydrate.assert_not_called()
        self.assertEqual(library["items"], {})

    def test_batch_coverage_reports_missing_required_roles(self) -> None:
        library = server.normalize_material_library(
            {
                "batches": [{"id": "batch-a", "name": "SKU-A"}],
                "activeId": "batch-a",
                "items": {
                    "/hook.mp4": {
                        "batchId": "batch-a",
                        "kind": "video",
                        "analysisStatus": "ready",
                        "editRole": "hook",
                        "qualityScore": 5,
                    },
                    "/detail.mp4": {
                        "batchId": "batch-a",
                        "kind": "video",
                        "analysisStatus": "ready",
                        "editRole": "detail",
                        "qualityScore": 4,
                    },
                    "/pending.mp4": {
                        "batchId": "batch-a",
                        "kind": "video",
                        "analysisStatus": "queued",
                        "editRole": "motion",
                    },
                },
            }
        )

        coverage = server.operations_batch_coverage(library)[0]

        self.assertEqual(coverage["total"], 3)
        self.assertEqual(coverage["ready"], 2)
        self.assertEqual(coverage["queued"], 1)
        self.assertEqual(coverage["coverageScore"], 33)
        self.assertIn("motion", coverage["missingRoles"])
        self.assertNotIn("hook", coverage["missingRoles"])

    def test_executor_is_offline_when_queue_waits_without_recent_heartbeat(self) -> None:
        now = server.iso_timestamp("2026-07-22T10:10:00Z")
        health = server.chatcut_executor_health(
            {"lastSeenAt": "2026-07-22T10:00:00Z", "state": "idle"},
            [{"status": "queued"}],
            now_timestamp=now,
        )
        self.assertEqual(health["health"], "offline")
        self.assertEqual(health["activeRequestCount"], 1)

    def test_recent_heartbeat_marks_executor_online(self) -> None:
        now = server.iso_timestamp("2026-07-22T10:01:00Z")
        health = server.chatcut_executor_health(
            {"lastSeenAt": "2026-07-22T10:00:30Z", "state": "syncing"},
            [{"status": "syncing"}],
            now_timestamp=now,
        )
        self.assertEqual(health["health"], "online")
        self.assertEqual(health["ageSeconds"], 30)


if __name__ == "__main__":
    unittest.main()
