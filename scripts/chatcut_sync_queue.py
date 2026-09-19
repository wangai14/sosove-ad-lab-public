from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from seedance_web.chatcut_sync import (
    VIDEO_EXTENSIONS,
    normalize_ledger,
    product_key_matches_source,
    source_product_label,
    update_sync_request,
)


DEFAULT_OBSIDIAN_ROOT = PROJECT_ROOT / "material-vault"


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def ledger_path() -> Path:
    root = Path(os.environ.get("SEEDANCE_OBSIDIAN_MATERIAL_ROOT") or DEFAULT_OBSIDIAN_ROOT).expanduser()
    return root / "data" / "chatcut-sync.json"


def executor_status_path(path: Path | None = None) -> Path:
    target = path or ledger_path()
    return target.parent / "chatcut-executor.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_executor_heartbeat(
    path: Path | None = None,
    *,
    state: str,
    action: str,
    request_id: str = "",
    error: str = "",
) -> dict[str, Any]:
    target = executor_status_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "type": "chatcut_sync_executor_status",
        "lastSeenAt": utc_now_iso(),
        "state": str(state or "unknown")[:40],
        "action": str(action or "")[:80],
        "requestId": str(request_id or "")[:120],
        "error": str(error or "")[:500],
        "host": socket.gethostname(),
        "processId": os.getpid(),
    }
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
        temp_path = Path(handle.name)
    temp_path.replace(target)
    return payload


def read_ledger(path: Path | None = None) -> dict[str, Any]:
    target = path or ledger_path()
    if not target.exists():
        return normalize_ledger({})
    try:
        return normalize_ledger(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return normalize_ledger({})


def write_ledger(value: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    target = path or ledger_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_ledger(value)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False, indent=2))
        temp_path = Path(handle.name)
    temp_path.replace(target)
    return normalized


def active_items(request: dict[str, Any]) -> list[dict[str, Any]]:
    items = request.get("items") if isinstance(request.get("items"), list) else []
    return [
        item
        for item in items
        if isinstance(item, dict) and str(item.get("status") or "pending") in {"pending", "failed"}
    ]


def request_payload(request: dict[str, Any]) -> dict[str, Any]:
    items = active_items(request)
    validation = validate_request(request, items)
    return {
        "ok": True,
        "requestId": request.get("id", ""),
        "projectId": request.get("projectId", ""),
        "projectUrl": request.get("projectUrl", ""),
        "productKey": request.get("productKey", ""),
        "batchId": request.get("batchId", ""),
        "batchName": request.get("batchName", ""),
        "sourceProductLabel": request.get("sourceProductLabel", ""),
        "status": request.get("status", ""),
        "summary": request.get("summary", {}),
        "filterSnapshot": request.get("filterSnapshot", {}),
        "validation": validation,
        "items": items,
    }


def validate_request(request: dict[str, Any], items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    selected = items if items is not None else active_items(request)
    errors: list[str] = []
    batch_ids = {str(item.get("batchId") or "") for item in selected if str(item.get("batchId") or "")}
    if len(batch_ids) > 1:
        errors.append("同步任务包含多个产品批次")
    source_labels = sorted(
        {
            source_product_label(item.get("sourcePath"))
            for item in selected
            if source_product_label(item.get("sourcePath"))
        }
    )
    if len(source_labels) > 1:
        errors.append(f"同步任务包含多个产品目录：{'、'.join(source_labels[:4])}")
    source_label = source_labels[0] if len(source_labels) == 1 else str(request.get("sourceProductLabel") or "")
    product_key = str(request.get("productKey") or "")
    if source_label and not product_key_matches_source(product_key, source_label):
        errors.append(f"产品名“{product_key}”与素材目录“{source_label}”不一致")
    for item in selected:
        path = Path(str(item.get("sourcePath") or ""))
        if str(item.get("analysisStatus") or "") != "ready":
            errors.append(f"{item.get('name') or path.name} 不是 ready 状态")
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            errors.append(f"{item.get('name') or path.name} 不是支持的视频格式")
        if not path.exists() or not path.is_file():
            errors.append(f"源文件不存在：{path}")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors)), "sourceProductLabels": source_labels}


def find_request(ledger: dict[str, Any], request_id: str = "", latest: bool = False) -> dict[str, Any] | None:
    requests = [item for item in ledger.get("requests", []) if isinstance(item, dict)]
    if request_id:
        return next((item for item in requests if str(item.get("id") or "") == request_id), None)
    candidates = [
        item
        for item in requests
        if str(item.get("status") or "") in {"queued", "partial"} and active_items(item)
    ]
    if not candidates:
        return None
    return candidates[-1] if latest else candidates[0]


def update_items(
    request_id: str,
    updates: list[dict[str, Any]],
    path: Path | None = None,
) -> dict[str, Any]:
    ledger = read_ledger(path)
    next_ledger, request = update_sync_request(
        ledger,
        {"requestId": request_id, "items": updates},
    )
    write_ledger(next_ledger, path)
    return request_payload(request)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and update the ChatCut sync queue.")
    parser.add_argument("--ledger", type=Path, default=None, help="Override chatcut-sync.json path")
    sub = parser.add_subparsers(dest="command", required=True)

    next_parser = sub.add_parser("next", help="Print the next queued request")
    next_parser.add_argument("--request-id", default="")
    next_parser.add_argument("--latest", action="store_true")

    claim_parser = sub.add_parser("claim", help="Mark pending/failed items as syncing")
    claim_parser.add_argument("--request-id", required=True)

    mark_parser = sub.add_parser("mark", help="Apply item updates from a JSON file or inline JSON")
    mark_parser.add_argument("--request-id", required=True)
    mark_parser.add_argument("--updates-file", type=Path)
    mark_parser.add_argument("--updates-json", default="")
    return parser


def main() -> int:
    configure_stdio()
    args = build_parser().parse_args()
    path = args.ledger
    if args.command == "next":
        request = find_request(read_ledger(path), args.request_id, args.latest)
        write_executor_heartbeat(
            path,
            state="ready" if request else "idle",
            action="read_queue",
            request_id=str(request.get("id") or "") if request else "",
        )
        print(json.dumps(request_payload(request) if request else {"ok": True, "request": None}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "claim":
        ledger = read_ledger(path)
        request = find_request(ledger, args.request_id)
        if not request:
            raise SystemExit(f"request not found: {args.request_id}")
        validation = validate_request(request)
        if not validation["ok"]:
            raise SystemExit("; ".join(validation["errors"]))
        updates = [
            {
                "fingerprint": item.get("fingerprint", ""),
                "panelUrl": item.get("panelUrl", ""),
                "status": "syncing",
                "error": "",
            }
            for item in active_items(request)
        ]
        result = update_items(args.request_id, updates, path)
        write_executor_heartbeat(path, state="syncing", action="claim", request_id=args.request_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "mark":
        if args.updates_file:
            updates = json.loads(args.updates_file.read_text(encoding="utf-8"))
        elif args.updates_json:
            updates = json.loads(args.updates_json)
        else:
            raise SystemExit("mark requires --updates-file or --updates-json")
        if not isinstance(updates, list):
            raise SystemExit("updates must be a JSON array")
        result = update_items(args.request_id, updates, path)
        result_status = str(result.get("status") or "")
        state = "idle" if result_status == "complete" else "needs_attention" if result_status in {"failed", "blocked", "partial"} else "syncing"
        write_executor_heartbeat(path, state=state, action="mark", request_id=args.request_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    main()
