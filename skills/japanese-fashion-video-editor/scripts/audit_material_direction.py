from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_VAULT_ROOT = Path(
    os.environ.get("SEEDANCE_OBSIDIAN_MATERIAL_ROOT")
    or Path(__file__).resolve().parents[4] / "material-vault"
)
REQUIRED_ROLES = ["hook", "try_on", "detail", "motion", "proof", "ending"]
ROLE_LABELS = {
    "hook": "开头钩子",
    "try_on": "上身展示",
    "detail": "细节特写",
    "motion": "动作镜头",
    "transition": "转场氛围",
    "proof": "卖点证明",
    "ending": "结尾召回",
    "unassigned": "待判断",
}
ROLE_ALIASES = {
    "try-on": "try_on",
    "tryon": "try_on",
    "full_body": "try_on",
    "full-body": "try_on",
    "closeup": "detail",
    "close_up": "detail",
    "cta": "ending",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def material_entries(library: dict[str, Any]) -> list[dict[str, Any]]:
    batches = {
        str(batch.get("id") or ""): str(batch.get("name") or "")
        for batch in library.get("batches", [])
        if isinstance(batch, dict)
    }
    items = library.get("items") if isinstance(library.get("items"), dict) else {}
    entries: list[dict[str, Any]] = []
    for url, item in items.items():
        if not isinstance(item, dict):
            continue
        entry = dict(item)
        entry["url"] = url
        entry["batchName"] = batches.get(str(entry.get("batchId") or ""), "未分批")
        entries.append(entry)
    return entries


def candidate_role(candidate: dict[str, Any]) -> str:
    raw_role = str(candidate.get("editRole") or candidate.get("role") or "unassigned").strip().lower()
    role = ROLE_ALIASES.get(raw_role, raw_role)
    return role if role in ROLE_LABELS else "unassigned"


def source_key(clip: dict[str, Any]) -> str:
    return str(clip.get("sourcePath") or clip.get("name") or clip.get("url") or "").strip()


def has_edit_hint(clip: dict[str, Any]) -> bool:
    hint_fields = (
        "cutHint",
        "sourceStartMs",
        "sourceEndMs",
        "startMs",
        "endMs",
        "sourceTimeMs",
        "frameIndex",
        "frameAnalysis",
    )
    return any(clip.get(field) not in (None, "", [], {}) for field in hint_fields)


def score_band(score: int) -> tuple[str, str]:
    if score >= 90:
        return "excellent", "方向完整，可生成正式草稿并进入投放前检查。"
    if score >= 75:
        return "good", "方向可用，适合生成草稿并做少量人工调整。"
    if score >= 60:
        return "usable", "可以生成聚焦版本，但应优先修复关键缺口。"
    if score >= 40:
        return "weak", "素材方向偏弱，自动混剪风险较高。"
    return "not-ready", "暂不建议自动混剪，应先补拍、重标或重新分析。"


def build_actions(
    clips: list[dict[str, Any]],
    missing: list[str],
    dominant_role: str,
    dominance_ratio: float,
    average_score: int,
    edit_ready_ratio: float,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not clips:
        actions.append({
            "priority": "P0",
            "role": "pool",
            "action": "先运行素材分析或补充已标记片段，当前没有达到最低分数的候选镜头。",
        })
    for role in missing:
        priority = "P0" if role in {"hook", "detail", "proof", "ending"} else "P1"
        actions.append({
            "priority": priority,
            "role": role,
            "action": f"缺少{ROLE_LABELS[role]}：重新标记现有片段，若全库不存在对应证据，再补拍具体镜头。",
        })
    if dominance_ratio > 0.45 and dominant_role:
        actions.append({
            "priority": "P1",
            "role": dominant_role,
            "action": f"{ROLE_LABELS.get(dominant_role, dominant_role)}占比过高：只保留最高分的2-3段，其余降级为备用。",
        })
    if average_score and average_score < 60:
        actions.append({
            "priority": "P1",
            "role": "quality",
            "action": "候选平均分偏低：重跑分析，并手动确认2-4秒的清晰高光区间。",
        })
    if clips and edit_ready_ratio < 0.5:
        actions.append({
            "priority": "P1",
            "role": "readiness",
            "action": "超过一半候选缺少切点或帧级证据：补充source range、cut hint或frame analysis。",
        })
    if len(clips) < 5:
        actions.append({
            "priority": "P0",
            "role": "quantity",
            "action": "可用候选少于5段：不建议制作30秒版本，先补足镜头或改做更短测试。",
        })
    if not actions:
        actions.append({
            "priority": "P2",
            "role": "draft",
            "action": "素材池可直接支持15-30秒草稿；下一步检查文案、画面、优惠和CTA是否逐段对应。",
        })
    return actions


def build_monitor(
    vault_root: Path,
    batch_id: str = "",
    platform: str = "meta",
    target_duration: int = 30,
    min_score: int = 55,
) -> dict[str, Any]:
    library = read_json(vault_root / "data" / "material-library.json", {"items": {}, "batches": []})
    pool = read_json(vault_root / "data" / "auto-edit-pool.json", {"clips": []})
    all_entries = material_entries(library if isinstance(library, dict) else {})
    if batch_id:
        entries = [item for item in all_entries if str(item.get("batchId") or "") == batch_id]
        urls = {str(item.get("url") or "") for item in entries}
    else:
        entries = all_entries
        urls = {str(item.get("url") or "") for item in entries}

    raw_clips = pool.get("clips") if isinstance(pool, dict) and isinstance(pool.get("clips"), list) else []
    clips = [
        clip
        for clip in raw_clips
        if isinstance(clip, dict)
        and (not urls or str(clip.get("url") or "") in urls)
        and as_int(clip.get("smartScore"), 0) >= min_score
    ]

    role_counts = Counter(candidate_role(clip) for clip in clips)
    high_clips = [clip for clip in clips if as_int(clip.get("smartScore"), 0) >= 70]
    excellent_clips = [clip for clip in clips if as_int(clip.get("smartScore"), 0) >= 82]
    average_score = round(sum(as_int(clip.get("smartScore"), 0) for clip in clips) / len(clips)) if clips else 0
    missing = [role for role in REQUIRED_ROLES if role_counts.get(role, 0) <= 0]
    covered = [role for role in REQUIRED_ROLES if role not in missing]

    dominant_role, dominant_count = ("", 0)
    if role_counts:
        dominant_role, dominant_count = role_counts.most_common(1)[0]
    dominance_ratio = round(dominant_count / len(clips), 3) if clips else 0

    sources = [source_key(clip) for clip in clips if source_key(clip)]
    unique_source_count = len(set(sources))
    edit_ready_count = sum(1 for clip in clips if has_edit_hint(clip))
    edit_ready_ratio = round(edit_ready_count / len(clips), 3) if clips else 0

    role_coverage_score = round((len(covered) / len(REQUIRED_ROLES)) * 45)
    quality_score = 0
    if clips:
        quality_score = round(min(12, average_score * 0.12) + min(8, (len(high_clips) / len(clips)) * 8))
    diversity_score = 0
    if clips:
        source_ratio = unique_source_count / len(clips) if clips else 0
        diversity_score = round(min(10, source_ratio * 15) + max(0, 5 - max(0, dominance_ratio - 0.45) * 20))
        diversity_score = max(0, min(15, diversity_score))
    readiness_score = round(edit_ready_ratio * 10)
    quantity_score = 10 if len(clips) >= 8 else 7 if len(clips) >= 5 else 4 if len(clips) >= 3 else 0

    penalty = 0
    if dominance_ratio > 0.45:
        penalty += round((dominance_ratio - 0.45) * 20)
    score = max(0, min(100, role_coverage_score + quality_score + diversity_score + readiness_score + quantity_score - penalty))
    grade, verdict = score_band(score)

    actions = build_actions(clips, missing, dominant_role, dominance_ratio, average_score, edit_ready_ratio)
    supported_durations: list[int] = []
    if len(clips) >= 5 and not {"hook", "ending"}.intersection(missing):
        supported_durations.append(15)
    if len(clips) >= 8 and not missing:
        supported_durations.append(30)

    role_breakdown = [
        {
            "role": role,
            "label": ROLE_LABELS.get(role, role),
            "count": int(role_counts.get(role, 0)),
            "required": role in REQUIRED_ROLES,
            "status": "ok" if role_counts.get(role, 0) else "missing",
        }
        for role in [*REQUIRED_ROLES, "transition", "unassigned"]
    ]

    by_source: dict[str, int] = defaultdict(int)
    for clip in clips:
        key = source_key(clip)
        if key:
            by_source[key] += 1
    repeated_sources = [
        {"source": source, "count": count}
        for source, count in sorted(by_source.items(), key=lambda item: item[1], reverse=True)
        if count >= 3
    ][:8]

    return {
        "version": 2,
        "type": "japanese_fashion_video_editor_direction_monitor",
        "updatedAt": utc_now(),
        "vaultRoot": str(vault_root),
        "scope": {
            "batchId": batch_id,
            "platform": platform,
            "targetDurationSeconds": target_duration,
            "minimumSmartScore": min_score,
        },
        "score": score,
        "grade": grade,
        "verdict": verdict,
        "scoreComponents": {
            "roleCoverage": role_coverage_score,
            "candidateQuality": quality_score,
            "visualDiversity": diversity_score,
            "editReadiness": readiness_score,
            "quantity": quantity_score,
            "penalty": penalty,
        },
        "materialCount": len(entries),
        "candidateCount": len(clips),
        "highCandidateCount": len(high_clips),
        "excellentCandidateCount": len(excellent_clips),
        "averageSmartScore": average_score,
        "uniqueSourceCount": unique_source_count,
        "editReadyCount": edit_ready_count,
        "editReadyRatio": edit_ready_ratio,
        "missingRoles": missing,
        "coveredRoles": covered,
        "roleBreakdown": role_breakdown,
        "dominantRole": dominant_role,
        "dominanceRatio": dominance_ratio,
        "repeatedSources": repeated_sources,
        "supportedDurationsSeconds": supported_durations,
        "actions": [item["action"] for item in actions],
        "priorityActions": actions,
    }


def markdown_report(monitor: dict[str, Any]) -> str:
    components = monitor.get("scoreComponents", {})
    lines = [
        "# 剪辑方向监控",
        "",
        f"- 更新时间：{monitor['updatedAt']}",
        f"- 方向分：{monitor['score']} / 100",
        f"- 判断：{monitor['verdict']}",
        f"- 素材数：{monitor['materialCount']}",
        f"- 可用候选：{monitor['candidateCount']}，高分候选：{monitor['highCandidateCount']}，优秀候选：{monitor['excellentCandidateCount']}",
        f"- 候选平均分：{monitor['averageSmartScore']}",
        f"- 可支持时长：{', '.join(str(item) + '秒' for item in monitor.get('supportedDurationsSeconds', [])) or '暂不建议自动成片'}",
        "",
        "## 分数组成",
        "",
        f"- 角色覆盖：{components.get('roleCoverage', 0)} / 45",
        f"- 候选质量：{components.get('candidateQuality', 0)} / 20",
        f"- 视觉多样性：{components.get('visualDiversity', 0)} / 15",
        f"- 剪辑就绪度：{components.get('editReadiness', 0)} / 10",
        f"- 数量：{components.get('quantity', 0)} / 10",
        f"- 扣分：-{components.get('penalty', 0)}",
        "",
        "## 角色覆盖",
        "",
        "| 方向 | 数量 | 状态 |",
        "| --- | ---: | --- |",
    ]
    for item in monitor.get("roleBreakdown", []):
        lines.append(f"| {item['label']} | {item['count']} | {'OK' if item['status'] == 'ok' else '缺失'} |")

    lines.extend(["", "## 导演建议", ""])
    for item in monitor.get("priorityActions", []):
        lines.append(f"- **{item['priority']}** {item['action']}")

    repeated = monitor.get("repeatedSources") if isinstance(monitor.get("repeatedSources"), list) else []
    if repeated:
        lines.extend(["", "## 重复来源提醒", ""])
        for item in repeated:
            source = str(item.get("source") or "")
            lines.append(f"- {Path(source).name or source}：{item.get('count')} 段")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Japanese womenswear editing material direction.")
    parser.add_argument("--vault-root", default=str(DEFAULT_VAULT_ROOT))
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--platform", choices=("meta", "tiktok", "ecommerce"), default="meta")
    parser.add_argument("--target-duration", type=int, choices=(15, 20, 25, 30, 45, 60), default=30)
    parser.add_argument("--min-score", type=int, default=55)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).expanduser().resolve()
    monitor = build_monitor(
        vault_root,
        batch_id=args.batch_id.strip(),
        platform=args.platform,
        target_duration=args.target_duration,
        min_score=max(0, min(100, args.min_score)),
    )
    write_json(vault_root / "data" / "material-direction-monitor.json", monitor)
    report_path = vault_root / "analysis" / "剪辑方向监控.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown_report(monitor), encoding="utf-8")

    if args.json:
        print(json.dumps({"ok": True, "monitor": monitor, "reportPath": str(report_path)}, ensure_ascii=False))
    else:
        print(f"{monitor['score']}/100 {monitor['verdict']}")
        print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
