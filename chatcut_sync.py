from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ID_PATTERN = re.compile(
    r"(?i)([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})"
)
REQUEST_STATUSES = {"queued", "syncing", "partial", "complete", "failed", "blocked"}
ITEM_STATUSES = {"pending", "syncing", "imported", "already_imported", "failed", "unresolved", "skipped"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_project_id(value: object) -> str:
    match = PROJECT_ID_PATTERN.search(str(value or "").strip())
    if not match:
        raise ValueError("请输入有效的 ChatCut 项目链接或完整 projectId。")
    return match.group(1).lower()


def clean_product_key(value: object) -> str:
    product_key = re.sub(r"\s+", " ", str(value or "").strip())[:120]
    if not product_key:
        raise ValueError("同步前必须填写产品名或 SKU，避免不同产品素材混入同一项目。")
    return product_key


def source_product_label(path: object) -> str:
    parts = [part for part in re.split(r"[\\/]+", str(path or "").strip()) if part]
    marker_indexes = [index for index, part in enumerate(parts) if part == "打标签"]
    if not marker_indexes:
        return ""
    index = marker_indexes[-1] + 1
    return parts[index][:160] if index < len(parts) else ""


def normalized_product_identity(value: object) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", str(value or "").casefold())


def product_key_matches_source(product_key: str, source_label: str) -> bool:
    product = normalized_product_identity(product_key)
    source = normalized_product_identity(source_label)
    if not product or not source:
        return True
    if product in source or source in product:
        return True
    product_numbers = set(re.findall(r"\d{4,}", product))
    source_numbers = set(re.findall(r"\d{4,}", source))
    if product_numbers and source_numbers and product_numbers & source_numbers:
        return True
    product_hanzi = "".join(re.findall(r"[\u3400-\u9fff]", product))
    source_hanzi = "".join(re.findall(r"[\u3400-\u9fff]", source))
    if len(product_hanzi) >= 4 and len(source_hanzi) >= 4:
        product_pairs = {product_hanzi[index : index + 2] for index in range(len(product_hanzi) - 1)}
        source_pairs = {source_hanzi[index : index + 2] for index in range(len(source_hanzi) - 1)}
        overlap = len(product_pairs & source_pairs)
        return overlap >= 2 and overlap / max(1, min(len(product_pairs), len(source_pairs))) >= 0.3
    return False


def normalize_ledger(value: object) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    requests = [item for item in data.get("requests", []) if isinstance(item, dict)][-100:]
    assets = [item for item in data.get("assets", []) if isinstance(item, dict)][-5000:]
    return {
        "version": 1,
        "type": "chatcut_material_sync_ledger",
        "updatedAt": str(data.get("updatedAt") or utc_now_iso()),
        "requests": requests,
        "assets": assets,
    }


def resolve_source_path(item: dict[str, Any]) -> tuple[str, str, int, int]:
    for field in ("sourcePath", "externalPath", "localPath"):
        raw_path = str(item.get(field) or "").strip()
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            continue
        stat = path.stat()
        return str(path), field, int(stat.st_size), int(stat.st_mtime_ns)
    return "", "", 0, 0


def material_fingerprint(path: str, size: int, modified_ns: int, panel_url: str) -> str:
    identity = "|".join(
        [
            str(Path(path)).casefold() if path else "",
            str(max(0, size)),
            str(max(0, modified_ns)),
            panel_url.strip(),
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def existing_asset_map(ledger: dict[str, Any], project_id: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for asset in ledger.get("assets", []):
        if not isinstance(asset, dict):
            continue
        if str(asset.get("projectId") or "").lower() != project_id:
            continue
        fingerprint = str(asset.get("fingerprint") or "")
        asset_id = str(asset.get("chatcutAssetId") or "")
        if fingerprint and asset_id and asset.get("status") == "imported":
            result[fingerprint] = asset
    return result


def request_fingerprints(request: dict[str, Any]) -> list[str]:
    items = request.get("items") if isinstance(request.get("items"), list) else []
    return sorted(
        str(item.get("fingerprint") or "")
        for item in items
        if isinstance(item, dict) and str(item.get("fingerprint") or "")
    )


def matching_active_request(
    ledger: dict[str, Any],
    project_id: str,
    product_key: str,
    fingerprints: list[str],
) -> dict[str, Any] | None:
    if not fingerprints:
        return None
    requests = ledger.get("requests") if isinstance(ledger.get("requests"), list) else []
    for request in reversed(requests):
        if not isinstance(request, dict):
            continue
        if str(request.get("status") or "") not in {"queued", "syncing", "partial"}:
            continue
        if str(request.get("projectId") or "").lower() != project_id:
            continue
        if str(request.get("productKey") or "").casefold() != product_key.casefold():
            continue
        if request_fingerprints(request) == fingerprints:
            return request
    return None


def request_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in ITEM_STATUSES}
    for item in items:
        status = str(item.get("status") or "pending")
        if status in counts:
            counts[status] += 1
    return {
        "total": len(items),
        "pending": counts["pending"],
        "syncing": counts["syncing"],
        "imported": counts["imported"],
        "alreadyImported": counts["already_imported"],
        "failed": counts["failed"],
        "unresolved": counts["unresolved"],
        "skipped": counts["skipped"],
    }


def request_status(items: list[dict[str, Any]]) -> str:
    statuses = {str(item.get("status") or "pending") for item in items}
    if statuses and statuses <= {"imported", "already_imported", "skipped"}:
        return "complete"
    if "syncing" in statuses:
        return "syncing"
    if "pending" in statuses:
        return "queued"
    if statuses & {"imported", "already_imported"} and statuses & {"failed", "unresolved"}:
        return "partial"
    if statuses and statuses <= {"unresolved", "skipped"}:
        return "blocked"
    return "failed"


def build_sync_request(
    library: dict[str, Any],
    payload: dict[str, Any],
    ledger_value: object,
    created_by: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger = normalize_ledger(ledger_value)
    project_value = payload.get("projectId") or payload.get("projectUrl")
    project_id = clean_project_id(project_value)
    product_key = clean_product_key(payload.get("productKey"))
    raw_urls = payload.get("urls") if isinstance(payload.get("urls"), list) else []
    urls = list(dict.fromkeys(str(url or "").strip() for url in raw_urls if str(url or "").strip()))
    if not urls:
        raise ValueError("当前同步范围没有素材，请先选择批次或筛选结果。")
    if len(urls) > 30:
        raise ValueError("单次最多同步 30 个原始素材，请缩小筛选范围。")

    statuses = {
        str(status or "").strip().lower()
        for status in (payload.get("statuses") if isinstance(payload.get("statuses"), list) else ["ready"])
        if str(status or "").strip()
    }
    items_map = library.get("items") if isinstance(library.get("items"), dict) else {}
    batches = {
        str(batch.get("id") or ""): str(batch.get("name") or "")
        for batch in library.get("batches", [])
        if isinstance(batch, dict)
    }
    selected: list[tuple[str, dict[str, Any]]] = []
    for url in urls:
        item = items_map.get(url)
        if not isinstance(item, dict):
            continue
        material_status = str(item.get("analysisStatus") or item.get("status") or "").strip().lower()
        if statuses and material_status not in statuses:
            continue
        selected.append((url, item))
    if not selected:
        raise ValueError("筛选结果中没有符合状态要求的素材，默认只同步 ready 素材。")

    batch_ids = {str(item.get("batchId") or "") for _, item in selected if str(item.get("batchId") or "")}
    if len(batch_ids) > 1 and not bool(payload.get("allowMixedBatches")):
        raise ValueError("当前筛选跨越多个批次，请选择单个产品批次后再同步。")

    imported = existing_asset_map(ledger, project_id)
    request_items: list[dict[str, Any]] = []
    for panel_url, item in selected:
        source_path, path_field, size, modified_ns = resolve_source_path(item)
        fingerprint = material_fingerprint(source_path, size, modified_ns, panel_url)
        existing = imported.get(fingerprint)
        status = "already_imported" if existing else "pending" if source_path else "unresolved"
        request_items.append(
            {
                "panelUrl": panel_url,
                "name": str(item.get("name") or Path(source_path).name or panel_url)[-220:],
                "sourcePath": source_path,
                "pathField": path_field,
                "size": size,
                "modifiedNs": modified_ns,
                "fingerprint": fingerprint,
                "batchId": str(item.get("batchId") or ""),
                "batchName": batches.get(str(item.get("batchId") or ""), ""),
                "tags": [str(tag) for tag in item.get("tags", []) if str(tag).strip()][:30],
                "role": str(item.get("editRole") or item.get("role") or "unassigned"),
                "analysisStatus": str(item.get("analysisStatus") or item.get("status") or ""),
                "status": status,
                "chatcutAssetId": str(existing.get("chatcutAssetId") or "") if existing else "",
                "error": "" if source_path or existing else "没有可读取的本地、NAS或上传路径。",
            }
        )

    source_labels = sorted(
        {
            source_product_label(item.get("sourcePath"))
            for item in request_items
            if source_product_label(item.get("sourcePath"))
        }
    )
    if len(source_labels) > 1:
        raise ValueError(f"当前同步范围包含多个产品目录：{'、'.join(source_labels[:4])}。请按单个产品筛选后再同步。")
    source_label = source_labels[0] if source_labels else ""
    if source_label and not product_key_matches_source(product_key, source_label):
        raise ValueError(f"产品名/SKU与素材目录不一致：填写的是“{product_key}”，素材来自“{source_label}”。请改成对应产品后再同步。")

    duplicate = matching_active_request(
        ledger,
        project_id,
        product_key,
        sorted(str(item.get("fingerprint") or "") for item in request_items if item.get("fingerprint")),
    )
    if duplicate:
        return ledger, duplicate

    now = utc_now_iso()
    batch_id = next(iter(batch_ids), "")
    request = {
        "id": f"ccsync-{uuid.uuid4().hex[:12]}",
        "createdAt": now,
        "updatedAt": now,
        "createdBy": str(created_by or ""),
        "projectId": project_id,
        "projectUrl": f"https://app.chatcut.io/zh/editor/{project_id}",
        "productKey": product_key,
        "scope": str(payload.get("scope") or "filtered"),
        "batchId": batch_id,
        "batchName": batches.get(batch_id, ""),
        "sourceProductLabel": source_label,
        "filterSnapshot": payload.get("filterSnapshot") if isinstance(payload.get("filterSnapshot"), dict) else {},
        "items": request_items,
    }
    request["summary"] = request_summary(request_items)
    request["status"] = request_status(request_items)
    ledger["requests"] = [*ledger.get("requests", []), request][-100:]
    ledger["updatedAt"] = now
    return ledger, request


def update_sync_request(
    ledger_value: object,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger = normalize_ledger(ledger_value)
    request_id = str(payload.get("requestId") or "").strip()
    if not request_id:
        raise ValueError("requestId is required.")
    request = next((item for item in ledger["requests"] if str(item.get("id") or "") == request_id), None)
    if not request:
        raise ValueError("ChatCut sync request not found.")
    updates = payload.get("items") if isinstance(payload.get("items"), list) else []
    if not updates:
        raise ValueError("At least one sync item update is required.")

    request_items = request.get("items") if isinstance(request.get("items"), list) else []
    now = utc_now_iso()
    for raw_update in updates:
        if not isinstance(raw_update, dict):
            continue
        fingerprint = str(raw_update.get("fingerprint") or "")
        panel_url = str(raw_update.get("panelUrl") or "")
        target = next(
            (
                item
                for item in request_items
                if (fingerprint and item.get("fingerprint") == fingerprint)
                or (panel_url and item.get("panelUrl") == panel_url)
            ),
            None,
        )
        if not target:
            continue
        status = str(raw_update.get("status") or "").strip().lower()
        if status not in ITEM_STATUSES:
            raise ValueError(f"Invalid sync item status: {status}")
        asset_id = str(raw_update.get("chatcutAssetId") or "").strip()
        if status == "imported" and not asset_id:
            raise ValueError("Imported items require chatcutAssetId.")
        target["status"] = status
        target["chatcutAssetId"] = asset_id or str(target.get("chatcutAssetId") or "")
        target["error"] = str(raw_update.get("error") or "")[:500]
        target["updatedAt"] = now
        if status == "imported":
            asset_record = {
                "projectId": request["projectId"],
                "productKey": request["productKey"],
                "requestId": request_id,
                "panelUrl": target.get("panelUrl"),
                "sourcePath": target.get("sourcePath"),
                "fingerprint": target.get("fingerprint"),
                "chatcutAssetId": target["chatcutAssetId"],
                "status": "imported",
                "updatedAt": now,
            }
            ledger["assets"] = [
                asset
                for asset in ledger["assets"]
                if not (
                    asset.get("projectId") == asset_record["projectId"]
                    and asset.get("fingerprint") == asset_record["fingerprint"]
                )
            ]
            ledger["assets"].append(asset_record)

    request["items"] = request_items
    request["summary"] = request_summary(request_items)
    request["status"] = request_status(request_items)
    request["updatedAt"] = now
    ledger["updatedAt"] = now
    ledger["assets"] = ledger["assets"][-5000:]
    return ledger, request
