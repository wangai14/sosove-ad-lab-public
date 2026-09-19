from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROLE_ORDER = ["hook", "try_on", "detail", "motion", "proof", "transition", "ending", "backup", "unassigned"]
DIRECTOR_REQUIRED_ROLES = ["hook", "try_on", "detail", "motion", "proof", "ending"]
DIRECTOR_SEQUENCE_PATTERN = [
    "hook",
    "try_on",
    "detail",
    "motion",
    "proof",
    "transition",
    "try_on",
    "detail",
    "motion",
    "ending",
    "hook",
    "try_on",
    "transition",
    "proof",
    "backup",
    "unassigned",
]
DIRECTOR_TIMELINE_ORDER = {
    "hook": 0,
    "try_on": 1,
    "detail": 2,
    "motion": 3,
    "proof": 4,
    "transition": 5,
    "ending": 6,
    "backup": 7,
    "unassigned": 8,
}
AUTO_ROLE_FILL_LIMITS = {
    "hook": 2,
    "try_on": 3,
    "detail": 2,
    "motion": 2,
    "proof": 2,
    "transition": 2,
    "ending": 1,
    "backup": 1,
    "unassigned": 1,
}
MAX_AUTO_CLIPS_PER_SOURCE = 2
ROLE_LABELS = {
    "hook": "开头钩子",
    "try_on": "上身展示",
    "detail": "细节特写",
    "motion": "动作镜头",
    "transition": "转场氛围",
    "proof": "卖点证明",
    "ending": "结尾召回",
    "backup": "备用镜头",
    "unassigned": "待判断",
}
PRIORITY_WEIGHT = {"high": 30, "normal": 15, "low": 0}
MIN_SEGMENT_MS = 1200
DEFAULT_SEGMENT_MS = 6000
DEFAULT_SPEAKER = "zh_female_xiaopengyou"
DEFAULT_EDGE_JAPANESE_VOICE = "ja-JP-NanamiNeural"
DEFAULT_VOICE_PROVIDER = "edge"
DEFAULT_ELEVENLABS_MODEL = "eleven_multilingual_v2"
DEFAULT_COPY_LANGUAGE = "ja"
MAX_COPY_TEXT_CHARS = 2000
SMART_AUTO_MIN_SCORE = 55
AUTO_SEGMENT_TARGETS_MS = {
    "hook": (1200, 2400),
    "try_on": (2200, 3800),
    "detail": (1600, 3200),
    "motion": (1800, 3400),
    "transition": (1200, 2200),
    "proof": (1800, 3200),
    "ending": (1800, 3200),
    "backup": (1400, 2600),
    "unassigned": (1500, 3000),
}
DEFAULT_TRANSITION_MS = 420
ROLE_ACCENT_TEXT = {
    "hook": "LOOK",
    "try_on": "FIT",
    "detail": "DETAIL",
    "motion": "MOVE",
    "proof": "POINT",
    "transition": "NEXT",
    "ending": "CHECK",
    "backup": "CUT",
    "unassigned": "CUT",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_name(value: str, fallback: str) -> str:
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(value or "")).strip().strip(".")
    text = re.sub(r"\s+", " ", text)
    return text[:80] or fallback


def role_index(role: str) -> int:
    return DIRECTOR_TIMELINE_ORDER.get(role, DIRECTOR_TIMELINE_ORDER["unassigned"])


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def source_path_for(clip: dict[str, Any], vault_root: Path) -> Path | None:
    raw = str(clip.get("sourcePath") or clip.get("externalPath") or "").strip()
    if raw:
        path = Path(raw).expanduser()
        if not path.exists() or not path.is_file():
            return None
        return path
    else:
        obsidian_path = str(clip.get("obsidianPath") or "").strip()
        if not obsidian_path:
            return None
        path = vault_root / obsidian_path
    if not path.exists() or not path.is_file():
        return None
    if not is_inside(path, vault_root):
        return None
    return path


def clip_duration_ms(clip: dict[str, Any]) -> int:
    technical = clip.get("technical") if isinstance(clip.get("technical"), dict) else {}
    return max(0, as_int(technical.get("durationMs"), 0))


def choose_cut_hint(clip: dict[str, Any]) -> dict[str, Any]:
    duration_ms = clip_duration_ms(clip)
    hints = clip.get("cutHints") if isinstance(clip.get("cutHints"), list) else []
    role = str(clip.get("editRole") or "unassigned")
    normalized: list[dict[str, Any]] = []
    for hint in hints:
        if not isinstance(hint, dict):
            continue
        start_ms = max(0, as_int(hint.get("startMs"), 0))
        end_ms = as_int(hint.get("endMs"), start_ms + DEFAULT_SEGMENT_MS)
        if duration_ms:
            end_ms = min(end_ms, duration_ms)
        if end_ms - start_ms < MIN_SEGMENT_MS:
            continue
        normalized.append(
            {
                "startMs": start_ms,
                "endMs": end_ms,
                "role": str(hint.get("role") or role),
                "confidence": as_float(hint.get("confidence"), 0.0),
                "reason": str(hint.get("reason") or ""),
            }
        )
    if normalized:
        normalized.sort(
            key=lambda item: (
                item["role"] == role,
                item["confidence"],
                item["endMs"] - item["startMs"],
            ),
            reverse=True,
        )
        return normalized[0]

    end_ms = min(duration_ms or DEFAULT_SEGMENT_MS, DEFAULT_SEGMENT_MS)
    return {
        "startMs": 0,
        "endMs": max(MIN_SEGMENT_MS, end_ms),
        "role": role,
        "confidence": 0.35,
        "reason": "未找到 cutHints，使用素材开头片段。",
    }


def clip_score(clip: dict[str, Any]) -> float:
    smart_score = as_float(clip.get("smartScore"), -1.0)
    if smart_score >= 0:
        hint_bonus = 0.0
        hints = clip.get("cutHints") if isinstance(clip.get("cutHints"), list) else []
        confidences = [as_float(hint.get("confidence"), 0.0) for hint in hints if isinstance(hint, dict)]
        if confidences:
            hint_bonus = min(5.0, max(confidences) * 5)
        role_bonus = max(0, 6 - role_index(str(clip.get("editRole") or "unassigned")) * 0.4)
        return smart_score + hint_bonus + role_bonus
    quality = as_float(clip.get("qualityScore"), 0.0)
    priority = PRIORITY_WEIGHT.get(str(clip.get("priority") or "normal"), 10)
    role_bonus = max(0, 12 - role_index(str(clip.get("editRole") or "unassigned")))
    return priority + quality * 10 + role_bonus


def candidate_evidence_text(clip: dict[str, Any]) -> str:
    parts = [
        str(clip.get("contentDescription") or ""),
        str(clip.get("copyAngle") or ""),
        str(clip.get("adStage") or ""),
    ]
    for key in ("segmentTags", "strengths", "risks"):
        values = clip.get(key) if isinstance(clip.get(key), list) else []
        parts.extend(str(value or "") for value in values)
    if str(clip.get("clipUnit") or "video") != "segment":
        parts.extend([str(clip.get("summary") or ""), str(clip.get("name") or "")])
        for key in ("tags", "aiTags"):
            values = clip.get(key) if isinstance(clip.get(key), list) else []
            parts.extend(str(value or "") for value in values)
    marks = clip.get("secondMarks") if isinstance(clip.get("secondMarks"), list) else []
    for mark in marks[:12]:
        if not isinstance(mark, dict):
            continue
        parts.extend(str(mark.get(key) or "") for key in ("note", "visualNote", "cutAdvice", "timelineZone"))
    return " ".join(part for part in parts if part).lower()


def inferred_candidate_secondary_roles(clip: dict[str, Any], primary_role: str) -> list[str]:
    existing = clip.get("secondaryRoles") if isinstance(clip.get("secondaryRoles"), list) else []
    roles = [str(role) for role in existing if str(role) in ROLE_ORDER and str(role) != primary_role]
    evidence = candidate_evidence_text(clip)

    def add(role: str, terms: tuple[str, ...]) -> None:
        if role != primary_role and role not in roles and any(term in evidence for term in terms):
            roles.append(role)

    add("hook", ("开头", "钩子", "第一眼", "hook", "opening", "注目"))
    add("try_on", ("上身", "试穿", "全身", "正面", "侧面", "背面", "着用", "シルエット", "try_on"))
    add("detail", ("细节镜头", "细节特写", "近景", "局部", "看清", "close-up", "ディテール", "クローズアップ"))
    add("motion", ("走动", "走路", "转身", "摆动", "动作", "垂感", "歩", "ターン", "揺れ", "落ち感", "motion"))
    add("proof", ("显瘦", "显腿长", "遮肉", "修饰", "舒适", "百搭", "证明", "細見え", "カバー", "着回し", "proof"))
    add("transition", ("转场", "过渡", "切换", "节奏", "transition", "テンポ"))
    add("ending", ("结尾", "收尾", "召回", "商品页", "下单", "cta", "ending", "チェック"))

    marks = clip.get("secondMarks") if isinstance(clip.get("secondMarks"), list) else []
    visual_motion = max([as_float(mark.get("visualMotion"), 0.0) for mark in marks if isinstance(mark, dict)] or [0.0])
    motion_delta = max([as_float(mark.get("motionDelta"), 0.0) for mark in marks if isinstance(mark, dict)] or [0.0])
    if primary_role != "motion" and "motion" not in roles and (visual_motion >= 14 or motion_delta >= 0.18):
        roles.append("motion")

    start_ms = as_int(clip.get("sourceStartMs") or clip.get("segmentStartMs"), 0)
    end_ms = as_int(clip.get("sourceEndMs") or clip.get("segmentEndMs"), 0)
    duration_ms = as_int(clip.get("durationMs"), 0) or max(0, end_ms - start_ms)
    technical = clip.get("technical") if isinstance(clip.get("technical"), dict) else {}
    total_ms = as_int(technical.get("durationMs"), 0)
    smart_score = as_float(clip.get("smartScore"), 0.0)
    if primary_role != "hook" and "hook" not in roles and start_ms <= 2400 and smart_score >= 70:
        roles.append("hook")
    if primary_role != "ending" and "ending" not in roles and total_ms and end_ms >= max(0, total_ms - 2800) and duration_ms <= 5000 and smart_score >= 65:
        roles.append("ending")
    if primary_role != "transition" and "transition" not in roles and duration_ms <= 2200 and (visual_motion >= 10 or motion_delta >= 0.12):
        roles.append("transition")
    return roles


def candidate_for_role(candidate: dict[str, Any], role: str) -> dict[str, Any] | None:
    if str(candidate.get("role") or "") == role:
        return candidate
    secondary_roles = candidate.get("secondaryRoles") if isinstance(candidate.get("secondaryRoles"), list) else []
    if role not in secondary_roles:
        return None
    return {
        **candidate,
        "primaryRole": candidate.get("primaryRole") or candidate.get("role") or "unassigned",
        "role": role,
        "derivedRole": True,
        "score": as_float(candidate.get("score"), 0.0) - 6.0,
    }


def build_candidates(pool: dict[str, Any], vault_root: Path) -> list[dict[str, Any]]:
    clips = pool.get("clips") if isinstance(pool.get("clips"), list) else []
    candidates: list[dict[str, Any]] = []
    for clip in clips:
        if not isinstance(clip, dict):
            continue
        if str(clip.get("status") or "").lower() not in {"ready", "analyzed"}:
            continue
        if clip.get("autoEditEligible") is False:
            continue
        smart_score = as_float(clip.get("smartScore"), -1.0)
        if smart_score >= 0 and smart_score < SMART_AUTO_MIN_SCORE:
            continue
        source = source_path_for(clip, vault_root)
        if not source:
            continue
        hint = choose_cut_hint(clip)
        primary_role = str(clip.get("editRole") or hint.get("role") or "unassigned")
        candidates.append(
            {
                "clip": clip,
                "sourcePath": str(source),
                "hint": hint,
                "role": primary_role,
                "primaryRole": primary_role,
                "secondaryRoles": inferred_candidate_secondary_roles(clip, primary_role),
                "score": clip_score(clip),
            }
        )
    return candidates


def candidate_range(candidate: dict[str, Any]) -> tuple[int, int]:
    hint = candidate.get("hint") if isinstance(candidate.get("hint"), dict) else {}
    start_ms = max(0, as_int(hint.get("startMs"), 0))
    end_ms = as_int(hint.get("endMs"), start_ms + DEFAULT_SEGMENT_MS)
    return start_ms, max(start_ms, end_ms)


def candidate_key(candidate: dict[str, Any]) -> str:
    clip = candidate.get("clip") if isinstance(candidate.get("clip"), dict) else {}
    source = str(candidate.get("sourcePath") or "")
    segment_id = str(clip.get("segmentId") or "").strip()
    start_ms, end_ms = candidate_range(candidate)
    unit = str(clip.get("clipUnit") or "video")
    range_id = segment_id or f"{start_ms}-{end_ms}"
    return f"{source}|{unit}|{range_id}"


def candidate_source_key(candidate: dict[str, Any]) -> str:
    return str(candidate.get("sourcePath") or "").strip().lower()


def can_select_candidate(
    candidate: dict[str, Any],
    used_keys: set[str],
    selected_ranges: dict[str, list[tuple[int, int]]],
    selected_source_counts: dict[str, int] | None = None,
    selected_role_counts: dict[str, int] | None = None,
    source_limit: int = 0,
    role_limits: dict[str, int] | None = None,
) -> bool:
    key = candidate_key(candidate)
    if key in used_keys:
        return False
    start_ms, end_ms = candidate_range(candidate)
    if end_ms - start_ms < MIN_SEGMENT_MS:
        return False
    source = str(candidate.get("sourcePath") or "")
    source_key = candidate_source_key(candidate)
    if source_limit and selected_source_counts is not None and selected_source_counts.get(source_key, 0) >= source_limit:
        return False
    role = str(candidate.get("role") or "unassigned")
    if role_limits is not None and selected_role_counts is not None:
        role_limit = role_limits.get(role, max(1, min(2, role_limits.get("unassigned", 1))))
        if selected_role_counts.get(role, 0) >= role_limit:
            return False
    for existing_start, existing_end in selected_ranges.get(source, []):
        overlap_ms = min(end_ms, existing_end) - max(start_ms, existing_start)
        if overlap_ms > 250:
            return False
    return True


def mark_candidate_selected(
    candidate: dict[str, Any],
    used_keys: set[str],
    selected_ranges: dict[str, list[tuple[int, int]]],
    selected_source_counts: dict[str, int] | None = None,
    selected_role_counts: dict[str, int] | None = None,
) -> None:
    used_keys.add(candidate_key(candidate))
    start_ms, end_ms = candidate_range(candidate)
    selected_ranges.setdefault(str(candidate.get("sourcePath") or ""), []).append((start_ms, end_ms))
    if selected_source_counts is not None:
        source_key = candidate_source_key(candidate)
        selected_source_counts[source_key] = selected_source_counts.get(source_key, 0) + 1
    if selected_role_counts is not None:
        role = str(candidate.get("role") or "unassigned")
        selected_role_counts[role] = selected_role_counts.get(role, 0) + 1


def auto_paced_duration_ms(role: str, duration_ms: int, score: float = 0.0) -> int:
    min_ms, max_ms = AUTO_SEGMENT_TARGETS_MS.get(role, AUTO_SEGMENT_TARGETS_MS["unassigned"])
    if duration_ms <= min_ms:
        return duration_ms
    score_bonus = 500 if score >= 82 else 250 if score >= 72 else 0
    return max(min_ms, min(duration_ms, max_ms + score_bonus))


def director_sequence_penalty(candidate: dict[str, Any], previous: dict[str, Any] | None) -> float:
    if previous is None:
        return 0.0
    penalty = 0.0
    if str(candidate.get("role") or "") == str(previous.get("role") or ""):
        penalty += 18.0
    if str(candidate.get("sourcePath") or "") == str(previous.get("sourcePath") or ""):
        penalty += 24.0
    return penalty


def order_selected_for_director(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = list(selected)
    ordered: list[dict[str, Any]] = []

    def take_best(role: str | None = None) -> dict[str, Any] | None:
        pool = [item for item in remaining if role is None or item.get("role") == role]
        if not pool:
            return None
        previous = ordered[-1] if ordered else None
        pool.sort(
            key=lambda item: (
                director_sequence_penalty(item, previous),
                -as_float(item.get("score"), 0.0),
                role_index(str(item.get("role") or "unassigned")),
            )
        )
        chosen = pool[0]
        remaining.remove(chosen)
        return chosen

    for role in DIRECTOR_SEQUENCE_PATTERN:
        item = take_best(role)
        if item is not None:
            ordered.append(item)
        if not remaining:
            break

    while remaining:
        item = take_best(None)
        if item is None:
            break
        ordered.append(item)

    return ordered


def select_timeline(candidates: list[dict[str, Any]], max_clips: int, max_duration_ms: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()
    selected_ranges: dict[str, list[tuple[int, int]]] = {}
    selected_source_counts: dict[str, int] = {}
    selected_role_counts: dict[str, int] = {}

    for role in DIRECTOR_REQUIRED_ROLES:
        role_items = []
        for item in candidates:
            projected = candidate_for_role(item, role)
            if projected and can_select_candidate(
                projected,
                used_keys,
                selected_ranges,
                selected_source_counts,
                selected_role_counts,
                MAX_AUTO_CLIPS_PER_SOURCE,
            ):
                role_items.append(projected)
        if not role_items:
            continue
        role_items.sort(key=lambda item: item["score"], reverse=True)
        selected.append(role_items[0])
        mark_candidate_selected(role_items[0], used_keys, selected_ranges, selected_source_counts, selected_role_counts)
        if len(selected) >= max_clips:
            break

    if len(selected) < max_clips:
        fill = [
            item
            for item in candidates
            if can_select_candidate(
                item,
                used_keys,
                selected_ranges,
                selected_source_counts,
                selected_role_counts,
                MAX_AUTO_CLIPS_PER_SOURCE,
                AUTO_ROLE_FILL_LIMITS,
            )
        ]
        fill.sort(key=lambda item: item["score"], reverse=True)
        for item in fill:
            if not can_select_candidate(
                item,
                used_keys,
                selected_ranges,
                selected_source_counts,
                selected_role_counts,
                MAX_AUTO_CLIPS_PER_SOURCE,
                AUTO_ROLE_FILL_LIMITS,
            ):
                continue
            selected.append(item)
            mark_candidate_selected(item, used_keys, selected_ranges, selected_source_counts, selected_role_counts)
            if len(selected) >= max_clips:
                break

    selected = order_selected_for_director(selected)

    timeline: list[dict[str, Any]] = []
    cursor = 0
    for selected_index, item in enumerate(selected):
        hint = item["hint"]
        start_ms = as_int(hint["startMs"], 0)
        end_ms = as_int(hint["endMs"], start_ms + DEFAULT_SEGMENT_MS)
        duration_ms = max(0, end_ms - start_ms)
        if duration_ms < MIN_SEGMENT_MS:
            continue
        duration_ms = auto_paced_duration_ms(item["role"], duration_ms, as_float(item.get("score"), 0.0))
        if max_duration_ms:
            remaining_slots = max(1, len(selected) - selected_index)
            remaining_budget = max(0, max_duration_ms - cursor)
            slot_budget = max(MIN_SEGMENT_MS, remaining_budget // remaining_slots)
            duration_ms = min(duration_ms, slot_budget)
        end_ms = start_ms + duration_ms
        if max_duration_ms and cursor + duration_ms > max_duration_ms:
            remaining = max_duration_ms - cursor
            if remaining < MIN_SEGMENT_MS:
                break
            duration_ms = remaining
            end_ms = start_ms + duration_ms
        clip = item["clip"]
        timeline.append(
            {
                "sourcePath": item["sourcePath"],
                "obsidianPath": clip.get("obsidianPath") or "",
                "url": clip.get("url") or "",
                "name": clip.get("name") or Path(item["sourcePath"]).name,
                "role": item["role"],
                "roleLabel": ROLE_LABELS.get(item["role"], item["role"]),
                "primaryRole": item.get("primaryRole") or item["role"],
                "secondaryRoles": item.get("secondaryRoles") if isinstance(item.get("secondaryRoles"), list) else [],
                "derivedRole": bool(item.get("derivedRole")),
                "qualityScore": clip.get("qualityScore"),
                "priority": clip.get("priority") or "normal",
                "smartScore": clip.get("smartScore"),
                "smartTier": clip.get("smartTier") or "",
                "smartReasons": clip.get("smartReasons") if isinstance(clip.get("smartReasons"), list) else [],
                "smartPenalties": clip.get("smartPenalties") if isinstance(clip.get("smartPenalties"), list) else [],
                "clipUnit": clip.get("clipUnit") or "video",
                "segmentId": clip.get("segmentId") or "",
                "segmentScore": clip.get("segmentScore"),
                "segmentTags": clip.get("segmentTags") if isinstance(clip.get("segmentTags"), list) else [],
                "secondMarks": clip.get("secondMarks") if isinstance(clip.get("secondMarks"), list) else [],
                "sourceStartMs": start_ms,
                "sourceEndMs": end_ms,
                "durationMs": duration_ms,
                "targetStartMs": cursor,
                "targetEndMs": cursor + duration_ms,
                "reason": hint.get("reason") or "",
                "summary": clip.get("summary") or "",
                "suggestions": clip.get("suggestions") if isinstance(clip.get("suggestions"), list) else [],
                "tags": clip.get("tags") if isinstance(clip.get("tags"), list) else [],
                "aiTags": clip.get("aiTags") if isinstance(clip.get("aiTags"), list) else [],
                "technical": clip.get("technical") if isinstance(clip.get("technical"), dict) else {},
            }
        )
        cursor += duration_ms
        if max_duration_ms and cursor >= max_duration_ms:
            break
    return timeline


def selected_clips_from_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return []
    data = read_json(path, {})
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("clips"), list):
        return [item for item in data["clips"] if isinstance(item, dict)]
    return []


def selected_timeline(selected_clips: list[dict[str, Any]], vault_root: Path, max_clips: int, max_duration_ms: int) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    cursor = 0
    for raw in selected_clips[:max_clips]:
        source = source_path_for(raw, vault_root)
        if not source:
            continue
        technical = raw.get("technical") if isinstance(raw.get("technical"), dict) else {}
        source_total_ms = as_int(technical.get("durationMs"), 0)
        start_ms = max(0, as_int(raw.get("sourceStartMs", raw.get("startMs", 0)), 0))
        end_ms = as_int(raw.get("sourceEndMs", raw.get("endMs", 0)), 0)
        duration_ms = as_int(raw.get("durationMs"), 0)
        if end_ms <= start_ms:
            end_ms = start_ms + (duration_ms or DEFAULT_SEGMENT_MS)
        if source_total_ms:
            start_ms = min(start_ms, max(0, source_total_ms - MIN_SEGMENT_MS))
            end_ms = min(end_ms, source_total_ms)
        duration_ms = max(0, end_ms - start_ms)
        if duration_ms < MIN_SEGMENT_MS:
            continue
        if max_duration_ms and cursor + duration_ms > max_duration_ms:
            remaining = max_duration_ms - cursor
            if remaining < MIN_SEGMENT_MS:
                break
            duration_ms = remaining
            end_ms = start_ms + duration_ms

        role = str(raw.get("role") or raw.get("editRole") or "unassigned")
        timeline.append(
            {
                "sourcePath": str(source),
                "obsidianPath": raw.get("obsidianPath") or "",
                "url": raw.get("url") or "",
                "name": raw.get("name") or Path(source).name,
                "role": role,
                "roleLabel": ROLE_LABELS.get(role, role),
                "qualityScore": raw.get("qualityScore"),
                "priority": raw.get("priority") or "normal",
                "clipUnit": raw.get("clipUnit") or "manual",
                "segmentId": raw.get("segmentId") or "",
                "segmentScore": raw.get("segmentScore"),
                "segmentTags": raw.get("segmentTags") if isinstance(raw.get("segmentTags"), list) else [],
                "secondMarks": raw.get("secondMarks") if isinstance(raw.get("secondMarks"), list) else [],
                "sourceStartMs": start_ms,
                "sourceEndMs": end_ms,
                "durationMs": duration_ms,
                "targetStartMs": cursor,
                "targetEndMs": cursor + duration_ms,
                "reason": raw.get("manualNote") or "手动选择片段。",
                "summary": raw.get("summary") or "",
                "suggestions": raw.get("suggestions") if isinstance(raw.get("suggestions"), list) else [],
                "copyText": raw.get("copyText") or "",
                "copyMatch": raw.get("copyMatch") if isinstance(raw.get("copyMatch"), dict) else {},
                "tags": raw.get("tags") if isinstance(raw.get("tags"), list) else [],
                "aiTags": raw.get("aiTags") if isinstance(raw.get("aiTags"), list) else [],
                "technical": technical,
                "manualSelection": True,
            }
        )
        cursor += duration_ms
        if max_duration_ms and cursor >= max_duration_ms:
            break
    return timeline


def timeline_resolution(timeline: list[dict[str, Any]], target_ratio: str) -> tuple[int, int]:
    if target_ratio == "16:9":
        return 1920, 1080
    if target_ratio == "9:16":
        return 1080, 1920
    portrait = 0
    landscape = 0
    for item in timeline:
        technical = item.get("technical") if isinstance(item.get("technical"), dict) else {}
        width = as_int(technical.get("width"), 0)
        height = as_int(technical.get("height"), 0)
        if height >= width:
            portrait += 1
        else:
            landscape += 1
    return (1080, 1920) if portrait >= landscape else (1920, 1080)


def sec(value_ms: int) -> str:
    return f"{value_ms / 1000:.3f}s"


def director_beat_for_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    role = str(item.get("role") or "unassigned")
    phase_map = {
        "hook": "opening",
        "try_on": "fit-build",
        "detail": "detail-proof",
        "motion": "movement-proof",
        "proof": "claim-proof",
        "transition": "rhythm-bridge",
        "ending": "closing",
    }
    intent_map = {
        "hook": "用第一眼画面制造停留，不解释太多。",
        "try_on": "展示上身版型，承担主体信息。",
        "detail": "切到近景，打破连续上身拼接感。",
        "motion": "用动作证明垂感和真实穿着。",
        "proof": "把卖点落到可见画面上。",
        "transition": "作为节奏换气，不承担卖点。",
        "ending": "收住画面，给用户留下完整印象。",
    }
    return {
        "directorPhase": phase_map.get(role, "support"),
        "directorIntent": intent_map.get(role, "作为补充镜头使用，避免连续重复。"),
        "accentText": ROLE_ACCENT_TEXT.get(role, "CUT"),
        "antiSpliceReason": "按镜头功能编排，并通过字幕强调、动态关键帧和关系转场降低拼接感。",
        "beatIndex": index + 1,
    }


def motion_plan_for_item(item: dict[str, Any], index: int, edit_pace: str = "standard") -> dict[str, Any]:
    role = str(item.get("role") or "unassigned")
    direction = -1 if index % 2 else 1
    pace = edit_pace if edit_pace in {"standard", "fast", "calm"} else "standard"
    plans = {
        "hook": ("开头轻推近", 1.0, 1.055, 0.0, 0.0, 0.0, 0.0),
        "try_on": ("上身稳定推近", 1.0, 1.035, 0.0, 0.0, 0.0, 0.0),
        "detail": ("细节轻横移", 1.025, 1.07, -0.012 * direction, 0.012 * direction, 0.0, 0.0),
        "motion": ("动作轻跟随", 1.0, 1.025, 0.008 * direction, -0.008 * direction, 0.0, 0.0),
        "transition": ("转场氛围推近", 1.015, 1.055, 0.012 * direction, -0.012 * direction, 0.0, 0.0),
        "proof": ("卖点轻推近", 1.0, 1.04, 0.0, 0.0, 0.0, 0.0),
        "ending": ("结尾轻拉远", 1.045, 1.0, 0.0, 0.0, 0.0, 0.0),
    }
    label, scale_start, scale_end, x_start, x_end, y_start, y_end = plans.get(
        role,
        ("自然轻推近", 1.0, 1.03, 0.0, 0.0, 0.0, 0.0),
    )
    strength = {"standard": 1.0, "fast": 1.28, "calm": 0.58}.get(pace, 1.0)
    scale_start = 1.0 + ((scale_start - 1.0) * strength)
    scale_end = 1.0 + ((scale_end - 1.0) * strength)
    x_start *= strength
    x_end *= strength
    y_start *= strength
    y_end *= strength
    if pace == "fast" and role in {"hook", "motion", "transition"}:
        scale_end += 0.008
    return {
        "motionPreset": label,
        "motionLabel": label,
        "editPace": pace,
        **director_beat_for_item(item, index),
        "scaleStart": round(scale_start, 4),
        "scaleEnd": round(scale_end, 4),
        "positionXStart": round(x_start, 4),
        "positionXEnd": round(x_end, 4),
        "positionYStart": round(y_start, 4),
        "positionYEnd": round(y_end, 4),
    }


def transition_plan_for_pair(previous: dict[str, Any], current: dict[str, Any], index: int, transition_style: str = "auto") -> dict[str, Any]:
    previous_role = str(previous.get("role") or "unassigned")
    current_role = str(current.get("role") or "unassigned")
    same_source = str(previous.get("sourcePath") or "") == str(current.get("sourcePath") or "")
    style = transition_style if transition_style in {"auto", "dynamic", "soft", "minimal"} else "auto"

    if previous_role == current_role and not same_source:
        name, duration_ms, label = "zoom", 480, "同类镜头变焦打散"
    elif current_role == "ending":
        name, duration_ms, label = "dissolve", 520, "柔和收尾叠化"
    elif same_source:
        name, duration_ms, label = "blur", 360, "同素材模糊衔接"
    elif previous_role == "hook" or current_role == "try_on":
        name, duration_ms, label = "zoom", 360, "开场变焦衔接"
    elif "transition" in {previous_role, current_role}:
        name, duration_ms, label = "blur", 420, "氛围模糊转场"
    elif "motion" in {previous_role, current_role}:
        name, duration_ms, label = "dissolve", 420, "动作柔和叠化"
    elif index % 3 == 0:
        name, duration_ms, label = "blur", 380, "节奏模糊过渡"
    else:
        name, duration_ms, label = "dissolve", DEFAULT_TRANSITION_MS, "自然叠化"

    if style == "dynamic":
        name = "zoom" if index % 2 else "blur"
        duration_ms = max(280, min(duration_ms, 420))
        label = f"{label} · 快节奏"
    elif style == "soft":
        name = "dissolve"
        duration_ms = max(duration_ms, 520)
        label = f"{label} · 柔和"
    elif style == "minimal":
        name = "dissolve"
        duration_ms = min(duration_ms, 260)
        label = f"{label} · 少转场"

    return {
        "name": name,
        "durationMs": duration_ms,
        "label": label,
        "transitionStyle": style,
        "fromRole": previous_role,
        "toRole": current_role,
    }


def load_keyframe_bindings(skill_root: Path) -> tuple[Any | None, Any | None]:
    scripts_path = skill_root / "scripts"
    vendor_path = scripts_path / "vendor"
    for path in (scripts_path, vendor_path):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
    try:
        from pyJianYingDraft import Keyframe, KeyframeProperty as KP

        return KP, Keyframe
    except Exception:
        try:
            from pyJianYingDraft.keyframe import Keyframe, KeyframeProperty as KP

            return KP, Keyframe
        except Exception:
            return None, None


def apply_motion_keyframes(segment: Any, item: dict[str, Any], keyframe_property: Any, keyframe_cls: Any) -> dict[str, Any]:
    plan = item.setdefault("editPlan", {})
    if segment is None or keyframe_property is None:
        status = {"applied": False, "reason": "keyframe binding unavailable"}
        plan["motionStatus"] = status
        return status

    start_ms = as_int(item.get("targetStartMs"), 0)
    duration_ms = as_int(item.get("durationMs"), DEFAULT_SEGMENT_MS)
    if duration_ms < MIN_SEGMENT_MS:
        status = {"applied": False, "reason": "clip too short for motion keyframes"}
        plan["motionStatus"] = status
        return status

    t_start = start_ms * 1000
    t_end = (start_ms + duration_ms) * 1000
    easing = getattr(keyframe_cls, "EASE_IN_OUT", {}) if keyframe_cls is not None else {}

    try:
        segment.add_keyframe(keyframe_property.uniform_scale, t_start, float(plan.get("scaleStart", 1.0)), **easing)
        segment.add_keyframe(keyframe_property.uniform_scale, t_end, float(plan.get("scaleEnd", 1.03)), **easing)
        x_start = float(plan.get("positionXStart", 0.0))
        x_end = float(plan.get("positionXEnd", 0.0))
        y_start = float(plan.get("positionYStart", 0.0))
        y_end = float(plan.get("positionYEnd", 0.0))
        if x_start or x_end:
            segment.add_keyframe(keyframe_property.position_x, t_start, x_start, **easing)
            segment.add_keyframe(keyframe_property.position_x, t_end, x_end, **easing)
        if y_start or y_end:
            segment.add_keyframe(keyframe_property.position_y, t_start, y_start, **easing)
            segment.add_keyframe(keyframe_property.position_y, t_end, y_end, **easing)
    except Exception as exc:
        status = {"applied": False, "reason": str(exc)}
        plan["motionStatus"] = status
        return status

    status = {"applied": True, "keyframes": 2}
    plan["motionStatus"] = status
    return status


def apply_native_transition(
    project: Any,
    previous_segment: Any,
    previous_item: dict[str, Any],
    current_item: dict[str, Any],
    index: int,
    transition_style: str = "auto",
) -> dict[str, Any]:
    plan = transition_plan_for_pair(previous_item, current_item, index, transition_style)
    previous_item["nextTransition"] = plan
    current_item["incomingTransition"] = plan

    if previous_segment is None:
        status = {**plan, "applied": False, "reason": "previous segment unavailable"}
        previous_item["nextTransition"] = status
        current_item["incomingTransition"] = status
        return status

    try:
        transition = project.add_transition_simple(
            plan["name"],
            video_segment=previous_segment,
            duration=sec(as_int(plan.get("durationMs"), DEFAULT_TRANSITION_MS)),
        )
    except Exception as exc:
        status = {**plan, "applied": False, "reason": str(exc)}
        previous_item["nextTransition"] = status
        current_item["incomingTransition"] = status
        return status

    status = {**plan, "applied": bool(transition)}
    if transition is None:
        status["reason"] = "transition not resolved by JianYing wrapper"
    previous_item["nextTransition"] = status
    current_item["incomingTransition"] = status
    return status


def add_director_beat_text(project: Any, item: dict[str, Any], caption_style: str = "clean") -> dict[str, Any]:
    edit_plan = item.get("editPlan") if isinstance(item.get("editPlan"), dict) else {}
    style = caption_style if caption_style in {"clean", "sales", "none"} else "clean"
    if style == "none":
        status = {"applied": False, "reason": "director caption disabled"}
        edit_plan["accentStatus"] = status
        return status
    text = str(edit_plan.get("accentText") or "").strip()
    if style == "sales":
        sales_text = clean_copy_text(str(item.get("copyText") or ""))
        if sales_text:
            text = sales_text[:28]
    if not text:
        return {"applied": False, "reason": "empty accent text"}
    start_ms = as_int(item.get("targetStartMs"), 0) + 120
    duration_ms = min(900, max(520, int(as_int(item.get("durationMs"), DEFAULT_SEGMENT_MS) * 0.34)))
    kwargs: dict[str, Any] = {}
    try:
        import pyJianYingDraft as draft

        kwargs = {
            "clip_settings": draft.ClipSettings(transform_y=0.68),
            "style": draft.TextStyle(size=6.5, bold=True, color=(1.0, 1.0, 1.0), align=1),
            "border": draft.TextBorder(color=(0.0, 0.0, 0.0), alpha=0.85, width=28.0),
        }
    except Exception:
        kwargs = {}
    try:
        segment = project.add_text_simple(
            text,
            start_time=sec(start_ms),
            duration=sec(duration_ms),
            track_name="Director_Beat",
            anim_in="fade",
            anim_out="fade",
            **kwargs,
        )
    except Exception as exc:
        status = {"applied": False, "text": text, "reason": str(exc)}
        edit_plan["accentStatus"] = status
        return status
    status = {"applied": bool(segment), "text": text, "track": "Director_Beat", "captionStyle": style}
    if segment is None:
        status["reason"] = "text segment not created"
    edit_plan["accentStatus"] = status
    return status


def clean_copy_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:MAX_COPY_TEXT_CHARS]


def split_copy_text(text: str) -> list[str]:
    text = clean_copy_text(text)
    if not text:
        return []
    raw_parts = re.split(r"(?<=[。！？!?；;])\s*|[\n\r]+", text)
    return [part.strip(" ，,。！？!?；;") for part in raw_parts if part.strip(" ，,。！？!?；;")]


def material_copy_line(item: dict[str, Any], index: int, language: str = DEFAULT_COPY_LANGUAGE) -> str:
    role = str(item.get("role") or "")
    role_label = str(item.get("roleLabel") or ROLE_LABELS.get(role, "素材展示"))
    tags = [str(tag) for tag in item.get("aiTags", []) if str(tag).strip()]
    name = str(item.get("name") or "")
    product = ""
    match = re.search(r"(\d{6,})", name)
    if match:
        product = match.group(1)

    if language == "ja":
        if role == "hook":
            return "まず注目したいのは、すっきり見えるきれいなシルエット。"
        if role == "try_on":
            return "斜めボタンのデザインで、脚のラインが自然にきれいに見えます。"
        if role == "detail":
            return "近くで見ると、ボタン位置と素材感までしっかり伝わります。"
        if role == "motion":
            return "歩いた時の落ち感がきれいで、毎日のコーデにも合わせやすい一本です。"
        if role == "transition":
            return "ここで雰囲気を切り替えて、着用感の見せ方をテンポよくつなぎます。"
        if role == "proof":
            return "腰まわりはすっきり、ワイドなラインで体型カバーもしやすいです。"
        if role == "ending":
            return "気になる方は、同じアイテムをぜひチェックしてみてください。"
        if product:
            return f"{product} は、シルエットとディテールを見せたい時に使いやすい素材です。"
        if tags:
            return f"このカットは{tags[0]}の印象を伝える素材として使えます。"
        return f"第 {index + 1} カットは、商品の雰囲気を自然に見せる素材です。"

    if role == "hook":
        return f"这条先看版型，上身效果比普通牛仔裤更显利落。"
    if role == "try_on":
        return f"这段适合做上身展示，重点看裤腿垂感和斜扣设计。"
    if role == "detail":
        return f"这里放细节特写，让用户看清面料、扣位和剪裁。"
    if role == "motion":
        return f"走动镜头可以表现真实垂坠感，混剪里建议放在中段。"
    if role == "transition":
        return f"这个镜头适合用来转场，把节奏从展示带到卖点。"
    if role == "proof":
        return f"这里可以承接卖点说明，强化显瘦和百搭感。"
    if role == "ending":
        return f"结尾用这段收住画面，引导用户继续看同款。"
    if product:
        return f"{product} 这段作为{role_label}素材，适合放进自动混剪。"
    if tags:
        return f"这段素材适合做{role_label}，关键词是{tags[0]}。"
    return f"第 {index + 1} 段素材适合做{role_label}。"


def default_voiceover_text(timeline: list[dict[str, Any]], language: str = DEFAULT_COPY_LANGUAGE) -> str:
    lines = [material_copy_line(item, index, language) for index, item in enumerate(timeline)]
    return " ".join(lines)


def copy_lines_for_timeline(timeline: list[dict[str, Any]], custom_text: str, language: str = DEFAULT_COPY_LANGUAGE) -> list[str]:
    clip_lines = [clean_copy_text(str(item.get("copyText") or "")) for item in timeline]
    if any(clip_lines):
        # Explicit clip copy is authoritative. Empty entries are intentional B-roll
        # and must not recycle narration from another shot.
        return clip_lines

    parts = split_copy_text(custom_text)
    if not parts:
        parts = split_copy_text(default_voiceover_text(timeline, language))
    if not timeline:
        return []
    if len(parts) <= len(timeline):
        defaults = split_copy_text(default_voiceover_text(timeline, language))
        return [(parts[index] if index < len(parts) else defaults[index % len(defaults)]) for index in range(len(timeline))]

    lines: list[str] = []
    for index in range(len(timeline)):
        start = round(index * len(parts) / len(timeline))
        end = round((index + 1) * len(parts) / len(timeline))
        chunk = parts[start:end] or [parts[min(index, len(parts) - 1)]]
        lines.append(" ".join(chunk))
    return lines


def clean_voice_provider(value: str) -> str:
    provider = str(value or DEFAULT_VOICE_PROVIDER).strip().lower()
    return provider if provider in {"jianying", "elevenlabs", "edge"} else DEFAULT_VOICE_PROVIDER


def clean_copy_language(value: str) -> str:
    language = str(value or DEFAULT_COPY_LANGUAGE).strip().lower()
    return language if language in {"ja", "zh"} else DEFAULT_COPY_LANGUAGE


def clean_voice_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(value or "").strip())[:120]


def clean_tts_model(value: str, default: str = DEFAULT_ELEVENLABS_MODEL) -> str:
    model = re.sub(r"[^A-Za-z0-9_.-]", "", str(value or default).strip())[:120]
    return model or default


def elevenlabs_api_key() -> str:
    return str(os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def clean_edge_voice(value: str) -> str:
    voice = re.sub(r"[^A-Za-z0-9_-]", "", str(value or DEFAULT_EDGE_JAPANESE_VOICE).strip())[:120]
    return voice or DEFAULT_EDGE_JAPANESE_VOICE


def generate_edge_audio(text: str, output_path: Path, voice: str) -> Path:
    import asyncio
    import edge_tts

    clean_text = clean_copy_text(text)
    if not clean_text:
        raise RuntimeError("日语配音文案为空。")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async def _save() -> None:
        communicate = edge_tts.Communicate(clean_text, clean_edge_voice(voice))
        await communicate.save(str(output_path))

    asyncio.run(_save())
    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError("日语配音没有生成音频。")
    return output_path


def generate_elevenlabs_audio(text: str, output_path: Path, api_key: str, voice_id: str, model_id: str) -> Path:
    if not api_key:
        raise RuntimeError("ElevenLabs API Key 未配置。")
    if not voice_id:
        raise RuntimeError("ElevenLabs Voice ID 未配置。")
    clean_text = clean_copy_text(text)
    if not clean_text:
        raise RuntimeError("ElevenLabs 文案为空。")

    query = urlencode({"output_format": "mp3_44100_128"})
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?{query}"
    body = {
        "text": clean_text,
        "model_id": clean_tts_model(model_id),
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
        },
    }
    request = Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(request, timeout=90) as response:
            audio_bytes = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"ElevenLabs HTTP {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"ElevenLabs 请求失败：{exc.reason}") from exc
    if not audio_bytes:
        raise RuntimeError("ElevenLabs 没有返回音频。")
    output_path.write_bytes(audio_bytes)
    return output_path


def add_voiceover_segment(
    project: Any,
    text: str,
    start_ms: int,
    speaker: str,
    provider: str,
    elevenlabs_voice_id: str,
    elevenlabs_model: str,
) -> Any:
    if provider == "elevenlabs":
        temp_dir = Path(project.root) / project.name / "temp_assets"
        output_path = temp_dir / f"elevenlabs_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = generate_elevenlabs_audio(
            text,
            output_path,
            elevenlabs_api_key(),
            elevenlabs_voice_id,
            elevenlabs_model,
        )
        return project.add_audio_safe(str(audio_path), start_time=sec(start_ms), track_name="Editable_VoiceOver")
    if provider == "edge":
        temp_dir = Path(project.root) / project.name / "temp_assets"
        output_path = temp_dir / f"japanese_tts_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = generate_edge_audio(text, output_path, speaker or DEFAULT_EDGE_JAPANESE_VOICE)
        return project.add_audio_safe(str(audio_path), start_time=sec(start_ms), track_name="Editable_VoiceOver")
    return project.add_tts_intelligent(
        text,
        speaker=speaker or DEFAULT_SPEAKER,
        start_time=sec(start_ms),
        track_name="Editable_VoiceOver",
    )


def add_editable_copy_tracks(
    project: Any,
    timeline: list[dict[str, Any]],
    custom_text: str,
    speaker: str,
    generate_voiceover: bool,
    voice_provider: str = DEFAULT_VOICE_PROVIDER,
    elevenlabs_voice_id: str = "",
    elevenlabs_model: str = DEFAULT_ELEVENLABS_MODEL,
    copy_language: str = DEFAULT_COPY_LANGUAGE,
) -> dict[str, Any]:
    language = clean_copy_language(copy_language)
    lines = copy_lines_for_timeline(timeline, custom_text, language)
    text_segments = 0
    voice_segments = 0
    voice_failures: list[dict[str, Any]] = []
    provider = clean_voice_provider(voice_provider)
    voice_id = clean_voice_id(elevenlabs_voice_id)
    model = clean_tts_model(elevenlabs_model)
    display_speaker = speaker or (DEFAULT_EDGE_JAPANESE_VOICE if provider == "edge" else DEFAULT_SPEAKER)

    for item, line in zip(timeline, lines):
        start_ms = as_int(item.get("targetStartMs"), 0)
        duration_ms = max(MIN_SEGMENT_MS, as_int(item.get("durationMs"), DEFAULT_SEGMENT_MS))
        item["copyText"] = line
        if not line:
            continue
        text_segment = project.add_text_simple(
            line,
            start_time=sec(start_ms),
            duration=sec(duration_ms),
            track_name="Editable_Copy",
        )
        if text_segment is not None:
            text_segments += 1

        if generate_voiceover:
            try:
                audio_segment = add_voiceover_segment(
                    project,
                    line,
                    start_ms,
                    speaker or DEFAULT_SPEAKER,
                    provider,
                    voice_id,
                    model,
                )
            except Exception as exc:
                audio_segment = None
                voice_failures.append({"name": item.get("name") or "", "text": line, "reason": str(exc)})
            if audio_segment is not None:
                voice_segments += 1
            elif not voice_failures or voice_failures[-1].get("text") != line:
                voice_failures.append({"name": item.get("name") or "", "text": line, "reason": "TTS returned no audio"})

    return {
        "copyText": " ".join(line for line in lines if line),
        "copyLanguage": language,
        "speaker": display_speaker,
        "voiceProvider": provider,
        "elevenLabsVoiceId": voice_id,
        "elevenLabsModel": model,
        "generateVoiceover": bool(generate_voiceover),
        "textTrack": "Editable_Copy",
        "voiceTrack": "Editable_VoiceOver" if generate_voiceover else "",
        "textSegments": text_segments,
        "voiceSegments": voice_segments,
        "voiceFailures": voice_failures,
    }


def timeline_role_counts(timeline: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in timeline:
        role = str(item.get("role") or "unassigned")
        counts[role] = counts.get(role, 0) + 1
    return counts


def timeline_source_counts(timeline: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in timeline:
        source = str(item.get("sourcePath") or item.get("name") or "").strip()
        if not source:
            continue
        counts[source] = counts.get(source, 0) + 1
    return counts


def build_director_brief(timeline: list[dict[str, Any]], selection_mode: str) -> dict[str, Any]:
    role_counts = timeline_role_counts(timeline)
    source_counts = timeline_source_counts(timeline)
    missing_roles = [role for role in DIRECTOR_REQUIRED_ROLES if role_counts.get(role, 0) <= 0]
    dominant_role = ""
    dominant_ratio = 0.0
    if role_counts and timeline:
        dominant_role = max(role_counts, key=lambda role: role_counts[role])
        dominant_ratio = round(role_counts[dominant_role] / max(1, len(timeline)), 3)

    repeated_sources = [
        {"source": source, "name": Path(source).name, "count": count}
        for source, count in sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
        if count > MAX_AUTO_CLIPS_PER_SOURCE
    ]
    consecutive_same_role = 0
    consecutive_same_source = 0
    for previous, current in zip(timeline, timeline[1:]):
        if str(previous.get("role") or "") == str(current.get("role") or ""):
            consecutive_same_role += 1
        if str(previous.get("sourcePath") or "") == str(current.get("sourcePath") or ""):
            consecutive_same_source += 1
    splice_risk = min(100, consecutive_same_role * 18 + consecutive_same_source * 24 + len(repeated_sources) * 8)
    warnings: list[str] = []
    actions: list[str] = []
    if missing_roles:
        labels = [ROLE_LABELS.get(role, role) for role in missing_roles]
        warnings.append("缺少成片必需镜头：" + "、".join(labels))
        actions.append("先补拍或重标缺失角色，再生成正式成片。")
    if dominant_ratio > 0.45 and dominant_role:
        warnings.append(f"{ROLE_LABELS.get(dominant_role, dominant_role)}占比过高，成片容易像同类片段拼接。")
        actions.append("降低重复角色片段数量，优先补入细节、动作、卖点证明和结尾。")
    if repeated_sources:
        warnings.append("同一源视频进入草稿过多，画面变化会不足。")
        actions.append("限制单源视频入选数量，或从更多源视频补入不同角度。")
    if selection_mode == "manual":
        actions.append("手动片段建议按开头、上身、细节、动作、卖点、结尾重新排序。")

    if splice_risk >= 36:
        warnings.append("连续同类或同源镜头偏多，成片会显得像素材拼接。")
        actions.append("优先补入细节、动作、卖点证明镜头，或手动把同类上身镜头打散。")

    score = 100
    score -= len(missing_roles) * 12
    if dominant_ratio > 0.45:
        score -= int((dominant_ratio - 0.45) * 100)
    score -= min(20, len(repeated_sources) * 5)
    score -= min(18, int(splice_risk / 6))
    score = max(0, min(100, score))
    verdict = "ready" if score >= 75 and not missing_roles else "rough-cut" if score >= 55 else "needs-material"

    return {
        "version": 1,
        "selectionMode": selection_mode,
        "score": score,
        "verdict": verdict,
        "roleCounts": role_counts,
        "sourceCount": len(source_counts),
        "dominantRole": dominant_role,
        "dominanceRatio": dominant_ratio,
        "missingRoles": missing_roles,
        "repeatedSources": repeated_sources[:8],
        "spliceRisk": splice_risk,
        "consecutiveSameRole": consecutive_same_role,
        "consecutiveSameSource": consecutive_same_source,
        "warnings": warnings,
        "actions": actions,
    }


def markdown_cell(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).replace("|", "\\|").strip()


def markdown_report(record: dict[str, Any], timeline: list[dict[str, Any]], copy_result: dict[str, Any] | None = None) -> str:
    selection_label = "手动选择片段" if record.get("selectionMode") == "manual" else "智能自动候选池"
    lines = [
        f"# {record['draftName']}",
        "",
        "- 类型：AI 剪辑素材库生成的剪映草稿",
        f"- 片段来源：{selection_label}",
        f"- 创建时间：{record['createdAt']}",
        f"- 剪映草稿路径：`{record['draftPath']}`",
        f"- 草稿分辨率：{record['width']}x{record['height']}",
        f"- 片段数：{record['clipCount']}",
        f"- 时间线总时长：{round(record['totalDurationMs'] / 1000, 2)} 秒",
        f"- 剪辑优化：动态镜头 {record.get('motionClipCount') or 0} 段，原生转场 {record.get('transitionCount') or 0} 个",
        "",
        "## 时间线",
        "",
        "| 时间线 | 用途 | 对应文案 | 智能/片段分 | 素材 | 源片段 | 剪辑优化 | AI 建议 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in timeline:
        suggestion = "；".join(str(v) for v in item.get("suggestions", [])[:2]) or item.get("reason") or ""
        smart_score = item.get("smartScore")
        segment_score = item.get("segmentScore")
        score_label = str(smart_score if smart_score not in (None, "") else "")
        if item.get("clipUnit") == "segment" and segment_score not in (None, ""):
            score_label = f"{score_label}/{segment_score}段" if score_label else f"{segment_score}段"
        source_label = f"{round(item['sourceStartMs'] / 1000, 2)}s-{round(item['sourceEndMs'] / 1000, 2)}s"
        if item.get("segmentId"):
            source_label = f"{source_label} ({item.get('segmentId')})"
        edit_plan = item.get("editPlan") if isinstance(item.get("editPlan"), dict) else {}
        motion_label = str(edit_plan.get("motionLabel") or edit_plan.get("motionPreset") or "")
        incoming = item.get("incomingTransition") if isinstance(item.get("incomingTransition"), dict) else {}
        transition_label = ""
        if incoming:
            applied = "已应用" if incoming.get("applied") else "待手动"
            transition_label = f"{incoming.get('label') or incoming.get('name')}({applied})"
        edit_label = "；".join(part for part in [transition_label, motion_label] if part) or "自然切"
        copy_match = item.get("copyMatch") if isinstance(item.get("copyMatch"), dict) else {}
        copy_index = copy_match.get("sourceIndex", copy_match.get("index"))
        copy_prefix = f"第 {int(copy_index) + 1} 句：" if isinstance(copy_index, int) and copy_index >= 0 else ""
        copy_label = f"{copy_prefix}{item.get('copyText') or ''}".strip()
        lines.append(
            "| "
            f"{round(item['targetStartMs'] / 1000, 2)}s-{round(item['targetEndMs'] / 1000, 2)}s"
            " | "
            f"{markdown_cell(item['roleLabel'])}"
            " | "
            f"{markdown_cell(copy_label)}"
            " | "
            f"{markdown_cell(score_label)}"
            " | "
            f"{markdown_cell(item['name'])}"
            " | "
            f"{markdown_cell(source_label)}"
            " | "
            f"{markdown_cell(edit_label)}"
            " | "
            f"{markdown_cell(suggestion)}"
            " |"
        )
    director_brief = record.get("directorBrief") if isinstance(record.get("directorBrief"), dict) else {}
    if director_brief:
        role_counts = director_brief.get("roleCounts") if isinstance(director_brief.get("roleCounts"), dict) else {}
        role_text = "、".join(
            f"{ROLE_LABELS.get(str(role), str(role))}:{count}"
            for role, count in role_counts.items()
        ) or "无"
        warnings = director_brief.get("warnings") if isinstance(director_brief.get("warnings"), list) else []
        actions = director_brief.get("actions") if isinstance(director_brief.get("actions"), list) else []
        lines.extend(
            [
                "",
                "## 导演质检",
                "",
                f"- 结构评分：{director_brief.get('score') or 0}/100",
                f"- 结论：{director_brief.get('verdict') or 'unknown'}",
                f"- 角色分布：{role_text}",
                f"- 源视频数量：{director_brief.get('sourceCount') or 0}",
                f"- 主要角色：{ROLE_LABELS.get(str(director_brief.get('dominantRole') or ''), str(director_brief.get('dominantRole') or '无'))}，占比 {director_brief.get('dominanceRatio') or 0}",
            ]
        )
        if warnings:
            lines.extend(["", "### 风险", ""])
            lines.extend(f"- {warning}" for warning in warnings)
        if actions:
            lines.extend(["", "### 下一步", ""])
            lines.extend(f"- {action}" for action in actions)
    if copy_result:
        lines.extend(
            [
                "",
                "## 可编辑配音文案",
                "",
                f"- 字幕轨道：`{copy_result.get('textTrack') or 'Editable_Copy'}`",
                f"- 配音轨道：`{copy_result.get('voiceTrack') or '未生成配音'}`",
                f"- 配音来源：`{copy_result.get('voiceProvider') or DEFAULT_VOICE_PROVIDER}`",
                f"- 脚本语言：`{copy_result.get('copyLanguage') or DEFAULT_COPY_LANGUAGE}`",
                f"- 声音：`{copy_result.get('speaker') or DEFAULT_SPEAKER}`",
                "",
                str(copy_result.get("copyText") or ""),
                "",
            ]
        )
        failures = copy_result.get("voiceFailures") if isinstance(copy_result.get("voiceFailures"), list) else []
        if failures:
            lines.extend(
                [
                    "### 配音生成提示",
                    "",
                    "- 部分 TTS 配音没有生成成功，草稿仍保留可编辑字幕轨；可以在剪映里替换配音，或回到面板重新生成。",
                    "",
                ]
            )
    lines.extend(
        [
            "",
            "## 后续剪辑建议",
            "",
            "- 草稿已自动加入轻微推拉/横移动效和片段间原生转场，不再只是顺序拼接。",
            "- 打开剪映后可以继续调整每段时长、替换转场、修改字幕和配音。",
            "- 这些剪辑优化信息已经写入 timeline.json，后续自动混剪 skill 可以直接复用。",
            "",
        ]
    )
    return "\n".join(lines)


def update_draft_index(vault_root: Path, record: dict[str, Any]) -> None:
    index_path = vault_root / "data" / "jianying-drafts.json"
    index = read_json(index_path, {"drafts": []})
    drafts = index.get("drafts") if isinstance(index.get("drafts"), list) else []
    drafts = [item for item in drafts if isinstance(item, dict) and item.get("id") != record["id"]]
    drafts.insert(0, record)
    index = {"updatedAt": record["createdAt"], "drafts": drafts[:100]}
    write_json(index_path, index)


def load_jy_project(skill_root: Path) -> Any:
    scripts_path = skill_root / "scripts"
    if not (scripts_path / "jy_wrapper.py").exists():
        raise RuntimeError(f"jianying-editor scripts not found: {scripts_path}")
    sys.path.insert(0, str(scripts_path))
    from jy_wrapper import JyProject

    return JyProject


def create_jianying_draft(args: argparse.Namespace) -> dict[str, Any]:
    vault_root = Path(args.vault_root).expanduser().resolve()
    pool_file = Path(args.pool_file).expanduser().resolve()
    skill_root = Path(args.skill_root).expanduser().resolve()

    pool = read_json(pool_file, {})
    max_duration_ms = max(0, int(float(args.max_duration) * 1000))
    selected_file = Path(args.selected_clips_file).expanduser().resolve() if args.selected_clips_file else None
    selection_mode = "manual" if selected_file else "smart-auto"
    if selected_file:
        timeline = selected_timeline(selected_clips_from_file(selected_file), vault_root, args.max_clips, max_duration_ms)
    else:
        candidates = build_candidates(pool, vault_root)
        timeline = select_timeline(candidates, args.max_clips, max_duration_ms)
    if not timeline:
        raise RuntimeError("没有可用于生成剪映草稿的视频片段，请先运行素材分析或重新选择手动片段。")

    width, height = timeline_resolution(timeline, args.target_ratio)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_draft_name = f"AI素材库_手动草稿_{timestamp}" if selection_mode == "manual" else f"AI素材库_自动草稿_{timestamp}"
    draft_name = clean_name(args.draft_name or default_draft_name, default_draft_name)

    JyProject = load_jy_project(skill_root)
    keyframe_property, keyframe_cls = load_keyframe_bindings(skill_root)
    project = JyProject(draft_name, width=width, height=height, overwrite=True)
    added: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    edit_result: dict[str, Any] = {
        "optimized": True,
        "editStyle": f"{args.edit_pace}-{args.transition_style}-{args.caption_style}",
        "editPace": args.edit_pace,
        "transitionStyle": args.transition_style,
        "captionStyle": args.caption_style,
        "motionClipCount": 0,
        "transitionCount": 0,
        "accentTextCount": 0,
        "motionFailures": [],
        "transitionFailures": [],
        "accentTextFailures": [],
    }
    previous_segment = None
    previous_item: dict[str, Any] | None = None
    for item in timeline:
        item["editPlan"] = motion_plan_for_item(item, len(added), args.edit_pace)
        segment = project.add_clip(
            item["sourcePath"],
            source_start=sec(item["sourceStartMs"]),
            duration=sec(item["durationMs"]),
            target_start=sec(item["targetStartMs"]),
            track_name="VideoTrack",
        )
        if segment is None:
            failures.append({"name": item["name"], "sourcePath": item["sourcePath"], "reason": "add_clip returned None"})
            continue

        motion_status = apply_motion_keyframes(segment, item, keyframe_property, keyframe_cls)
        if motion_status.get("applied"):
            edit_result["motionClipCount"] += 1
        else:
            edit_result["motionFailures"].append({"name": item.get("name") or "", "reason": motion_status.get("reason") or ""})

        accent_status = add_director_beat_text(project, item, args.caption_style)
        if accent_status.get("applied"):
            edit_result["accentTextCount"] += 1
        elif accent_status.get("reason") != "director caption disabled":
            edit_result["accentTextFailures"].append({"name": item.get("name") or "", "reason": accent_status.get("reason") or ""})

        if previous_item is not None:
            transition_status = apply_native_transition(project, previous_segment, previous_item, item, len(added), args.transition_style)
            if transition_status.get("applied"):
                edit_result["transitionCount"] += 1
            else:
                edit_result["transitionFailures"].append(
                    {
                        "from": previous_item.get("name") or "",
                        "to": item.get("name") or "",
                        "transition": transition_status.get("name") or "",
                        "reason": transition_status.get("reason") or "",
                    }
                )
        added.append(item)
        previous_segment = segment
        previous_item = item

    if not added:
        raise RuntimeError("剪映草稿创建失败：没有任何片段成功写入时间线。")

    voiceover_text = clean_copy_text(args.voiceover_text or "")
    if args.voiceover_text_file:
        file_text = read_text(Path(args.voiceover_text_file).expanduser())
        if file_text:
            voiceover_text = clean_copy_text(file_text)
    copy_result = add_editable_copy_tracks(
        project,
        added,
        voiceover_text,
        args.speaker,
        bool(args.generate_voiceover),
        args.voice_provider,
        args.elevenlabs_voice_id,
        args.elevenlabs_model,
        args.copy_language,
    )
    director_brief = build_director_brief(added, selection_mode)
    edit_result["directorBrief"] = director_brief

    save_result = project.save()
    draft_path = str(save_result.get("draft_path") if isinstance(save_result, dict) else "")
    created_at = utc_now()
    draft_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
    draft_obsidian_dir = vault_root / "jianying-drafts" / draft_id
    timeline_path = draft_obsidian_dir / "timeline.json"
    report_path = draft_obsidian_dir / "剪映草稿说明.md"

    record = {
        "id": draft_id,
        "draftName": draft_name,
        "draftPath": draft_path,
        "createdAt": created_at,
        "clipCount": len(added),
        "failedCount": len(failures),
        "totalDurationMs": sum(as_int(item.get("durationMs"), 0) for item in added),
        "width": width,
        "height": height,
        "sourcePool": str(pool_file),
        "selectionMode": selection_mode,
        "selectedClipsFile": str(selected_file or ""),
        "timelinePath": str(timeline_path),
        "reportPath": str(report_path),
        "obsidianTimelinePath": str(timeline_path.relative_to(vault_root)),
        "obsidianReportPath": str(report_path.relative_to(vault_root)),
        "editableDraft": True,
        "copyText": copy_result.get("copyText") or "",
        "copyLanguage": copy_result.get("copyLanguage") or DEFAULT_COPY_LANGUAGE,
        "copyTextTrack": copy_result.get("textTrack") or "",
        "voiceTrack": copy_result.get("voiceTrack") or "",
        "voiceProvider": copy_result.get("voiceProvider") or DEFAULT_VOICE_PROVIDER,
        "elevenLabsVoiceId": copy_result.get("elevenLabsVoiceId") or "",
        "elevenLabsModel": copy_result.get("elevenLabsModel") or "",
        "speaker": copy_result.get("speaker") or "",
        "copySegmentCount": copy_result.get("textSegments") or 0,
        "voiceSegmentCount": copy_result.get("voiceSegments") or 0,
        "voiceFailureCount": len(copy_result.get("voiceFailures") or []),
        "editOptimized": True,
        "editStyle": edit_result.get("editStyle") or "auto-product",
        "editPace": edit_result.get("editPace") or "standard",
        "transitionStyle": edit_result.get("transitionStyle") or "auto",
        "captionStyle": edit_result.get("captionStyle") or "clean",
        "motionClipCount": edit_result.get("motionClipCount") or 0,
        "transitionCount": edit_result.get("transitionCount") or 0,
        "accentTextCount": edit_result.get("accentTextCount") or 0,
        "transitionFailureCount": len(edit_result.get("transitionFailures") or []),
        "directorScore": director_brief.get("score") or 0,
        "directorVerdict": director_brief.get("verdict") or "",
        "directorBrief": director_brief,
    }

    write_json(timeline_path, {"record": record, "timeline": added, "copy": copy_result, "edit": edit_result, "failures": failures})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown_report(record, added, copy_result), encoding="utf-8")
    update_draft_index(vault_root, record)

    return {"ok": True, "record": record, "timeline": added, "copy": copy_result, "edit": edit_result, "failures": failures}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a JianYing draft from Obsidian auto-edit pool.")
    parser.add_argument("--vault-root", required=True)
    parser.add_argument("--pool-file", required=True)
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--selected-clips-file", default="")
    parser.add_argument("--draft-name", default="")
    parser.add_argument("--target-ratio", choices=["auto", "9:16", "16:9"], default="auto")
    parser.add_argument("--edit-pace", choices=["standard", "fast", "calm"], default="standard")
    parser.add_argument("--transition-style", choices=["auto", "dynamic", "soft", "minimal"], default="auto")
    parser.add_argument("--caption-style", choices=["clean", "sales", "none"], default="clean")
    parser.add_argument("--max-clips", type=int, default=8)
    parser.add_argument("--max-duration", type=float, default=60.0, help="Maximum timeline duration in seconds.")
    parser.add_argument("--voiceover-text", default="")
    parser.add_argument("--voiceover-text-file", default="")
    parser.add_argument("--speaker", default=DEFAULT_SPEAKER)
    parser.add_argument("--copy-language", choices=["ja", "zh"], default=DEFAULT_COPY_LANGUAGE)
    parser.add_argument("--voice-provider", choices=["jianying", "elevenlabs", "edge"], default=DEFAULT_VOICE_PROVIDER)
    parser.add_argument("--elevenlabs-voice-id", default="")
    parser.add_argument("--elevenlabs-model", default=DEFAULT_ELEVENLABS_MODEL)
    parser.add_argument("--generate-voiceover", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.max_clips = max(1, min(args.max_clips, 30))
    try:
        result = create_jianying_draft(args)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        payload = {"ok": False, "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
