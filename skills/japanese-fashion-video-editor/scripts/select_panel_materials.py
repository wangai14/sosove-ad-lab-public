from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_VAULT_PARENT = Path(
    os.environ.get("SEEDANCE_OBSIDIAN_MATERIAL_ROOT")
    or Path(__file__).resolve().parents[4] / "material-vault"
)
ROLE_ORDER = ["hook", "try_on", "detail", "motion", "proof", "ending", "transition", "unassigned"]
PRIORITY_SCORE = {"high": 3, "normal": 2, "low": 1}
ROLE_FALLBACK_DURATION_MS = {
    "hook": (1200, 1800),
    "detail": (1200, 2000),
    "try_on": (1800, 2800),
    "motion": (1600, 2400),
    "proof": (1600, 2400),
    "ending": (1800, 2600),
    "transition": (1200, 1800),
    "unassigned": (1500, 2200),
}
REQUIRED_ROLES = ["hook", "try_on", "detail", "proof", "ending"]


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def discover_vault_root(explicit: str) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root / "data" / "material-library.json").exists():
            raise ValueError(f"Material library not found under: {root}")
        return root
    if (DEFAULT_VAULT_PARENT / "data" / "material-library.json").exists():
        return DEFAULT_VAULT_PARENT.resolve()
    matches = list(DEFAULT_VAULT_PARENT.glob("*/data/material-library.json"))
    if not matches:
        raise ValueError("No materials panel library was found. Pass --vault-root explicitly.")
    return matches[0].parent.parent.resolve()


def normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def material_entries(library: dict[str, Any]) -> list[dict[str, Any]]:
    batches = {
        str(batch.get("id") or ""): str(batch.get("name") or "")
        for batch in library.get("batches", [])
        if isinstance(batch, dict)
    }
    items = library.get("items") if isinstance(library.get("items"), dict) else {}
    entries: list[dict[str, Any]] = []
    for url, raw_item in items.items():
        if not isinstance(raw_item, dict):
            continue
        item = dict(raw_item)
        item["url"] = str(url)
        item["batchName"] = batches.get(str(item.get("batchId") or ""), "")
        entries.append(item)
    return entries


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


def find_sync_request(ledger: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    if not request_id:
        return None
    requests = ledger.get("requests") if isinstance(ledger.get("requests"), list) else []
    return next(
        (
            request
            for request in requests
            if isinstance(request, dict) and str(request.get("id") or "") == request_id
        ),
        None,
    )


def imported_fingerprints(ledger: dict[str, Any], project_id: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not project_id:
        return result
    assets = ledger.get("assets") if isinstance(ledger.get("assets"), list) else []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if str(asset.get("projectId") or "").lower() != project_id.lower():
            continue
        fingerprint = str(asset.get("fingerprint") or "")
        asset_id = str(asset.get("chatcutAssetId") or "")
        if fingerprint and asset_id and str(asset.get("status") or "") == "imported":
            result[fingerprint] = asset_id
    return result


def numeric_score(value: object, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def clip_score(clip: dict[str, Any]) -> int:
    ad_profile = clip.get("adProfile") if isinstance(clip.get("adProfile"), dict) else {}
    return max(
        numeric_score(clip.get("score")),
        numeric_score(clip.get("smartScore")),
        numeric_score(ad_profile.get("adScore")),
    )


def normalized_role(value: object) -> str:
    role = str(value or "unassigned").strip().lower()
    aliases = {
        "try-on": "try_on",
        "tryon": "try_on",
        "full_body": "try_on",
        "full-body": "try_on",
        "closeup": "detail",
        "close_up": "detail",
        "cta": "ending",
    }
    role = aliases.get(role, role)
    return role if role in ROLE_ORDER else "unassigned"


def segment_candidates(pool_clip: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    segments = pool_clip.get("segments") if isinstance(pool_clip.get("segments"), list) else []
    for raw_segment in segments:
        if not isinstance(raw_segment, dict):
            continue
        candidates.append(
            {
                "startMs": numeric_score(raw_segment.get("startMs")),
                "endMs": numeric_score(raw_segment.get("endMs")),
                "score": clip_score(raw_segment),
                "role": normalized_role(raw_segment.get("role") or pool_clip.get("editRole")),
                "adStage": str(raw_segment.get("adStage") or ""),
                "segmentId": str(raw_segment.get("id") or ""),
                "reason": str(raw_segment.get("reason") or raw_segment.get("contentDescription") or ""),
            }
        )
    if str(pool_clip.get("clipUnit") or "") == "segment" or pool_clip.get("segmentId"):
        candidates.append(
            {
                "startMs": numeric_score(pool_clip.get("startMs") or pool_clip.get("sourceStartMs")),
                "endMs": numeric_score(pool_clip.get("endMs") or pool_clip.get("sourceEndMs")),
                "score": clip_score(pool_clip),
                "role": normalized_role(pool_clip.get("editRole") or pool_clip.get("role")),
                "adStage": str(pool_clip.get("adStage") or ""),
                "segmentId": str(pool_clip.get("segmentId") or ""),
                "reason": str(pool_clip.get("reason") or pool_clip.get("contentDescription") or ""),
            }
        )
    cut_hints = pool_clip.get("cutHints") if isinstance(pool_clip.get("cutHints"), list) else []
    for index, raw_hint in enumerate(cut_hints):
        if not isinstance(raw_hint, dict):
            continue
        candidates.append(
            {
                "startMs": numeric_score(raw_hint.get("startMs")),
                "endMs": numeric_score(raw_hint.get("endMs")),
                "score": max(clip_score(pool_clip), round(float(raw_hint.get("confidence") or 0) * 100)),
                "role": normalized_role(raw_hint.get("role") or pool_clip.get("editRole")),
                "adStage": "",
                "segmentId": f"hint-{index + 1}",
                "reason": str(raw_hint.get("reason") or ""),
            }
        )
    return [candidate for candidate in candidates if candidate["endMs"] > candidate["startMs"]]


def pool_index(pool: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    clips = pool.get("clips") if isinstance(pool.get("clips"), list) else []
    for raw_clip in clips:
        if not isinstance(raw_clip, dict):
            continue
        url = str(raw_clip.get("url") or "").strip()
        if not url:
            continue
        grouped[url].append(raw_clip)
    return grouped


def best_segment(item: dict[str, Any], related_clips: list[dict[str, Any]]) -> dict[str, Any]:
    item_role = normalized_role(item.get("editRole") or item.get("role"))
    candidates: list[dict[str, Any]] = []
    for pool_clip in related_clips:
        candidates.extend(segment_candidates(pool_clip))
    if candidates:
        candidates.sort(
            key=lambda candidate: (
                candidate["role"] == item_role,
                candidate["adStage"] == "hook" and item_role == "hook",
                candidate["score"],
                min(5000, candidate["endMs"] - candidate["startMs"]),
            ),
            reverse=True,
        )
        return candidates[0]
    fallback_min_ms, fallback_max_ms = ROLE_FALLBACK_DURATION_MS.get(item_role, ROLE_FALLBACK_DURATION_MS["unassigned"])
    duration_ms = numeric_score(item.get("durationMs") or (item.get("technical") or {}).get("durationMs"))
    fallback_duration_ms = min(duration_ms, fallback_max_ms) if duration_ms else fallback_max_ms
    return {
        "startMs": 0,
        "endMs": max(1, fallback_duration_ms),
        "score": max(numeric_score(item.get("smartScore")), numeric_score(item.get("qualityScore")) * 20),
        "role": item_role,
        "adStage": "",
        "segmentId": "fallback",
        "reason": (
            "No analyzed segment was available; use the role-specific "
            f"{fallback_min_ms}-{fallback_max_ms}ms opening range and verify manually."
        ),
    }


def entry_matches(
    item: dict[str, Any],
    batch_id: str,
    batch_name: str,
    tags: list[str],
    match_any_tag: bool,
    roles: list[str],
    statuses: list[str],
    urls: set[str],
    restrict_urls: bool,
) -> bool:
    if batch_id and str(item.get("batchId") or "") != batch_id:
        return False
    if batch_name and str(item.get("batchName") or "").casefold() != batch_name.casefold():
        return False
    if restrict_urls and str(item.get("url") or "") not in urls:
        return False
    item_tags = set(normalize_list(item.get("tags"))) | set(normalize_list(item.get("aiTags")))
    if tags:
        tag_matches = [tag in item_tags for tag in tags]
        if match_any_tag and not any(tag_matches):
            return False
        if not match_any_tag and not all(tag_matches):
            return False
    if roles and normalized_role(item.get("editRole") or item.get("role")) not in roles:
        return False
    item_status = str(item.get("analysisStatus") or item.get("status") or "").strip().lower()
    return not statuses or item_status in statuses


def balanced_select(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate["role"]].append(candidate)
    for role_candidates in groups.values():
        role_candidates.sort(key=lambda item: item["sortKey"], reverse=True)

    selected: list[dict[str, Any]] = []
    selected_paths: set[str] = set()
    while len(selected) < limit:
        added = False
        for role in ROLE_ORDER:
            while groups[role] and groups[role][0]["path"] in selected_paths:
                groups[role].pop(0)
            if not groups[role]:
                continue
            candidate = groups[role].pop(0)
            selected.append(candidate)
            selected_paths.add(candidate["path"])
            added = True
            if len(selected) >= limit:
                break
        if not added:
            break
    return selected


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    vault_root = discover_vault_root(args.vault_root)
    library = read_json(vault_root / "data" / "material-library.json", {"items": {}, "batches": []})
    pool = read_json(vault_root / "data" / "auto-edit-pool.json", {"clips": []})
    ledger = read_json(vault_root / "data" / "chatcut-sync.json", {"requests": [], "assets": []})
    related_by_url = pool_index(pool if isinstance(pool, dict) else {})
    sync_request_id = str(getattr(args, "sync_request_id", "") or "").strip()
    sync_request = find_sync_request(ledger if isinstance(ledger, dict) else {}, sync_request_id)
    if sync_request_id and not sync_request:
        raise ValueError(f"ChatCut sync request not found: {sync_request_id}")
    request_items = sync_request.get("items") if isinstance(sync_request, dict) and isinstance(sync_request.get("items"), list) else []
    request_urls = {
        str(item.get("panelUrl") or "")
        for item in request_items
        if isinstance(item, dict)
        and str(item.get("panelUrl") or "")
        and str(item.get("status") or "pending") not in {"imported", "already_imported", "skipped"}
    }
    explicit_urls = set(args.url or [])
    url_filter = request_urls if sync_request else explicit_urls
    restrict_urls = bool(sync_request or explicit_urls)
    roles = [normalized_role(role) for role in args.role]
    statuses = [status.strip().lower() for status in args.status if status.strip()]
    project_id = str(
        (sync_request or {}).get("projectId")
        or getattr(args, "project_id", "")
        or ""
    ).strip().lower()
    imported = imported_fingerprints(ledger if isinstance(ledger, dict) else {}, project_id)

    candidates: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    skipped_already_imported: list[dict[str, Any]] = []
    for item in material_entries(library if isinstance(library, dict) else {}):
        if not entry_matches(
            item,
            batch_id=args.batch_id,
            batch_name=args.batch_name,
            tags=args.tag,
            match_any_tag=args.match_any_tag,
            roles=roles,
            statuses=statuses,
            urls=url_filter,
            restrict_urls=restrict_urls,
        ):
            continue
        path, path_field, size, modified_ns = resolve_source_path(item)
        if not path:
            unresolved.append(
                {
                    "url": item.get("url"),
                    "name": item.get("name"),
                    "reason": "No readable sourcePath, externalPath, or localPath.",
                }
            )
            continue
        panel_url = str(item.get("url") or "")
        fingerprint = material_fingerprint(path, size, modified_ns, panel_url)
        if fingerprint in imported:
            skipped_already_imported.append(
                {
                    "url": panel_url,
                    "name": str(item.get("name") or Path(path).name),
                    "path": path,
                    "fingerprint": fingerprint,
                    "chatcutAssetId": imported[fingerprint],
                    "reason": "This exact file version is already imported into the target ChatCut project.",
                }
            )
            continue
        segment = best_segment(item, related_by_url.get(str(item.get("url") or ""), []))
        role = normalized_role(segment.get("role") or item.get("editRole") or item.get("role"))
        tags = list(dict.fromkeys([*normalize_list(item.get("tags")), *normalize_list(item.get("aiTags"))]))
        priority = str(item.get("priority") or "normal").strip().lower()
        score = max(segment["score"], numeric_score(item.get("smartScore")), numeric_score(item.get("qualityScore")) * 20)
        candidate = {
            "url": str(item.get("url") or ""),
            "name": str(item.get("name") or Path(path).name),
            "path": path,
            "pathField": path_field,
            "size": size,
            "modifiedNs": modified_ns,
            "fingerprint": fingerprint,
            "batchId": str(item.get("batchId") or ""),
            "batchName": str(item.get("batchName") or ""),
            "tags": tags,
            "role": role,
            "status": str(item.get("analysisStatus") or item.get("status") or ""),
            "priority": priority,
            "score": score,
            "recommendedStartMs": segment["startMs"],
            "recommendedEndMs": segment["endMs"],
            "recommendedDurationMs": segment["endMs"] - segment["startMs"],
            "segmentId": segment["segmentId"],
            "adStage": segment["adStage"],
            "reason": segment["reason"],
        }
        candidate["sortKey"] = [
            PRIORITY_SCORE.get(priority, 2),
            score,
            -ROLE_ORDER.index(role),
        ]
        candidates.append(candidate)

    deduplicated: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        path_key = str(Path(candidate["path"])).casefold()
        existing = deduplicated.get(path_key)
        if existing is None or candidate["sortKey"] > existing["sortKey"]:
            deduplicated[path_key] = candidate
    unique_candidates = list(deduplicated.values())
    selected = balanced_select(unique_candidates, max(1, min(30, args.limit)))
    for candidate in selected:
        candidate.pop("sortKey", None)

    role_counts: dict[str, int] = defaultdict(int)
    for candidate in selected:
        role_counts[candidate["role"]] += 1
    missing_required_roles = [role for role in REQUIRED_ROLES if not role_counts.get(role)]
    total_recommended_duration_ms = sum(item["recommendedDurationMs"] for item in selected)
    full_ad_ready = not missing_required_roles and bool(selected)
    if full_ad_ready:
        recommended_target_seconds = max(15, min(30, round(total_recommended_duration_ms / 1000)))
        recommended_version = "15-30s 完整直效广告"
        recommendations = ["Role coverage is complete; verify the selected moments before timeline placement."]
    elif selected:
        recommended_target_seconds = max(6, min(15, round(total_recommended_duration_ms / 1000)))
        recommended_version = "6-15s 精简商品展示"
        recommendations = [
            f"Missing required roles: {', '.join(missing_required_roles)}.",
            "Use a shorter product-first version or add the missing shots before building a full direct-response ad.",
        ]
    else:
        recommended_target_seconds = 0
        recommended_version = "暂不可成片"
        recommendations = ["No readable, ready, non-duplicate source files are available for this request."]
    return {
        "version": 1,
        "type": "chatcut_panel_sync_manifest",
        "vaultRoot": str(vault_root),
        "filters": {
            "batchId": args.batch_id,
            "batchName": args.batch_name,
            "tags": args.tag,
            "matchAnyTag": args.match_any_tag,
            "roles": roles,
            "statuses": statuses,
            "urls": sorted(url_filter),
            "limit": args.limit,
            "projectId": project_id,
            "syncRequestId": sync_request_id,
        },
        "syncRequest": {
            "id": sync_request_id,
            "projectId": project_id,
            "productKey": str((sync_request or {}).get("productKey") or ""),
            "status": str((sync_request or {}).get("status") or ""),
        } if sync_request else None,
        "summary": {
            "matchedReadable": len(unique_candidates),
            "selected": len(selected),
            "unresolved": len(unresolved),
            "skippedAlreadyImported": len(skipped_already_imported),
            "roleCounts": dict(role_counts),
            "missingRequiredRoles": missing_required_roles,
            "fullAdReady": full_ad_ready,
            "recommendedVersion": recommended_version,
            "recommendedTargetDurationSeconds": recommended_target_seconds,
            "totalRecommendedDurationMs": total_recommended_duration_ms,
        },
        "recommendations": recommendations,
        "paths": [item["path"] for item in selected],
        "items": selected,
        "unresolved": unresolved,
        "skippedAlreadyImported": skipped_already_imported,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select tagged SOSOVE panel materials for ChatCut import.")
    parser.add_argument("--vault-root", default="")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--batch-name", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--match-any-tag", action="store_true")
    parser.add_argument("--role", action="append", default=[])
    parser.add_argument("--status", action="append", default=[])
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--project-id", default="")
    parser.add_argument("--sync-request-id", default="")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()
    if not args.status:
        args.status = ["ready"]
    manifest = build_manifest(args)
    output = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.json_out:
        output_path = Path(args.json_out).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
