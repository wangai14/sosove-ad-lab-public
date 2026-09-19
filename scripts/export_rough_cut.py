from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_name(value: object, fallback: str = "AI预剪素材") -> str:
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(value or "").strip())
    text = re.sub(r"\s+", " ", text).strip(" ._")
    return (text or fallback)[:80]


def read_json(path: Path, fallback: object) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def parse_ms(value: object) -> int:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0
    if number < 0 or number != number or number == float("inf"):
        return 0
    return int(round(number))


def resolve_source_path(clip: dict[str, Any], vault_root: Path) -> Path:
    for key in ("sourcePath", "externalPath"):
        raw = str(clip.get(key) or "").strip()
        if raw:
            candidate = Path(raw).expanduser()
            if candidate.exists() and candidate.is_file():
                return candidate
    obsidian_path = str(clip.get("obsidianPath") or "").strip()
    if obsidian_path:
        candidate = (vault_root / obsidian_path).resolve()
        try:
            candidate.relative_to(vault_root.resolve())
        except ValueError as exc:
            raise ValueError("素材的 Obsidian 路径超出素材库范围。") from exc
        if candidate.exists() and candidate.is_file():
            return candidate
    raise ValueError(f"找不到素材文件：{clip.get('name') or clip.get('url') or '未命名视频'}")


def normalize_clips(payload: object, vault_root: Path) -> list[dict[str, Any]]:
    clips = payload.get("clips") if isinstance(payload, dict) else None
    if not isinstance(clips, list) or not clips:
        raise ValueError("没有可导出的预剪片段。")
    if len(clips) > 30:
        raise ValueError("一次最多导出 30 个预剪片段。")

    normalized: list[dict[str, Any]] = []
    output_cursor_ms = 0
    for index, raw_clip in enumerate(clips, start=1):
        if not isinstance(raw_clip, dict):
            continue
        source_path = resolve_source_path(raw_clip, vault_root)
        start_ms = parse_ms(raw_clip.get("sourceStartMs", raw_clip.get("startMs")))
        end_ms = parse_ms(raw_clip.get("sourceEndMs", raw_clip.get("endMs")))
        if end_ms <= start_ms:
            end_ms = start_ms + parse_ms(raw_clip.get("durationMs"))
        duration_ms = end_ms - start_ms
        if duration_ms < 1200:
            raise ValueError(f"第 {index} 个预剪片段不足 1.2 秒。")
        if duration_ms > 12000:
            end_ms = start_ms + 12000
            duration_ms = 12000
        normalized.append(
            {
                "order": len(normalized),
                "name": str(raw_clip.get("name") or source_path.name).strip()[:220],
                "url": str(raw_clip.get("url") or "").strip(),
                "sourcePath": str(source_path),
                "sourceStartMs": start_ms,
                "sourceEndMs": end_ms,
                "durationMs": duration_ms,
                "outputStartMs": output_cursor_ms,
                "outputEndMs": output_cursor_ms + duration_ms,
                "role": str(raw_clip.get("role") or "unassigned").strip()[:40],
                "segmentId": str(raw_clip.get("segmentId") or "").strip()[:80],
                "segmentScore": parse_ms(raw_clip.get("segmentScore")),
                "segmentTags": [str(item).strip()[:80] for item in (raw_clip.get("segmentTags") or [])[:20] if str(item).strip()],
                "copyText": str(raw_clip.get("copyText") or "").strip()[:500],
                "copyMatch": raw_clip.get("copyMatch") if isinstance(raw_clip.get("copyMatch"), dict) else {},
            }
        )
        output_cursor_ms += duration_ms
    if not normalized:
        raise ValueError("没有有效的预剪片段。")
    return normalized


def ratio_size(value: str) -> tuple[int, int]:
    return (1920, 1080) if value == "16:9" else (1080, 1920)


def ffmpeg_clip_command(ffmpeg: str, clip: dict[str, Any], output: Path, width: int, height: int) -> list[str]:
    start_seconds = clip["sourceStartMs"] / 1000
    duration_seconds = clip["durationMs"] / 1000
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        "fps=30,setsar=1,format=yuv420p"
    )
    return [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start_seconds:.3f}",
        "-t",
        f"{duration_seconds:.3f}",
        "-i",
        clip["sourcePath"],
        "-map",
        "0:v:0",
        "-vf",
        video_filter,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        str(output),
    ]


def concat_file_line(path: Path) -> str:
    normalized = path.resolve().as_posix().replace("'", "'\\''")
    return f"file '{normalized}'"


def run_command(command: list[str], timeout_seconds: int) -> None:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        reason = (completed.stderr or completed.stdout or "FFmpeg 执行失败").strip()
        raise RuntimeError(reason[-1600:])


def write_report(path: Path, record: dict[str, Any], clips: list[dict[str, Any]]) -> None:
    lines = [
        f"# {record['name']}",
        "",
        f"- 创建时间：{record['createdAt']}",
        f"- 预剪视频：`{record['relativeVideoPath']}`",
        f"- 片段清单：`{record['relativeTimelinePath']}`",
        f"- 片段数量：{record['clipCount']}",
        f"- 总时长：{round(record['totalDurationMs'] / 1000, 2)} 秒",
        f"- 输出规格：{record['width']} × {record['height']} / 30fps / 静音",
        "",
        "> 此文件只用于快速检查文案与画面匹配。原视频和可编辑时间码均保留，正式剪辑继续在 ChatCut 或剪映完成。",
        "",
        "## 片段顺序",
        "",
    ]
    for clip in clips:
        start = clip["sourceStartMs"] / 1000
        end = clip["sourceEndMs"] / 1000
        copy_text = clip.get("copyText") or "纯画面片段"
        lines.append(
            f"- {clip['order'] + 1}. {clip['name']} · {start:.2f}s–{end:.2f}s · {clip['role']} · {copy_text}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_index(index_path: Path, record: dict[str, Any]) -> None:
    payload = read_json(index_path, {"roughCuts": []})
    records = payload.get("roughCuts") if isinstance(payload, dict) and isinstance(payload.get("roughCuts"), list) else []
    records = [item for item in records if isinstance(item, dict) and item.get("id") != record["id"]]
    records.insert(0, record)
    write_json(index_path, {"version": 1, "updatedAt": record["createdAt"], "roughCuts": records[:100]})


def export_rough_cut(args: argparse.Namespace) -> dict[str, Any]:
    vault_root = Path(args.vault_root).expanduser().resolve()
    selected_file = Path(args.selected_clips_file).expanduser().resolve()
    ffmpeg = str(Path(args.ffmpeg).expanduser()) if args.ffmpeg else str(shutil.which("ffmpeg") or "")
    if not ffmpeg or not Path(ffmpeg).exists():
        raise ValueError("未找到 FFmpeg，无法导出预剪素材。")
    clips = normalize_clips(read_json(selected_file, {}), vault_root)
    width, height = ratio_size(args.target_ratio)
    created_at = utc_now_iso()
    rough_cut_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    name = clean_name(args.name, f"AI预剪素材_{rough_cut_id}")
    output_dir = vault_root / "rough-cuts" / rough_cut_id
    temporary_dir = output_dir / ".working"
    output_path = output_dir / "preview.mp4"
    timeline_path = output_dir / "timeline.json"
    report_path = output_dir / "预剪素材说明.md"
    output_dir.mkdir(parents=True, exist_ok=False)
    temporary_dir.mkdir(parents=True, exist_ok=True)

    try:
        rendered: list[Path] = []
        for index, clip in enumerate(clips, start=1):
            target = temporary_dir / f"clip_{index:03d}.mp4"
            run_command(ffmpeg_clip_command(ffmpeg, clip, target, width, height), args.timeout_seconds)
            rendered.append(target)

        concat_path = temporary_dir / "concat.txt"
        concat_path.write_text("\n".join(concat_file_line(path) for path in rendered) + "\n", encoding="utf-8")
        run_command(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            args.timeout_seconds,
        )

        relative_video = output_path.relative_to(vault_root).as_posix()
        relative_timeline = timeline_path.relative_to(vault_root).as_posix()
        relative_report = report_path.relative_to(vault_root).as_posix()
        record = {
            "id": rough_cut_id,
            "name": name,
            "createdAt": created_at,
            "clipCount": len(clips),
            "totalDurationMs": sum(clip["durationMs"] for clip in clips),
            "width": width,
            "height": height,
            "fps": 30,
            "muted": True,
            "videoPath": str(output_path),
            "relativeVideoPath": relative_video,
            "timelinePath": str(timeline_path),
            "relativeTimelinePath": relative_timeline,
            "obsidianReportPath": relative_report,
            "sourceMode": "copy-matched-smart-segments",
        }
        write_json(timeline_path, {"record": record, "clips": clips})
        write_report(report_path, record, clips)
        update_index(vault_root / "data" / "rough-cuts.json", record)
        return {"ok": True, "record": record, "clips": clips}
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(temporary_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a silent rough cut from copy-matched material segments.")
    parser.add_argument("--vault-root", required=True)
    parser.add_argument("--selected-clips-file", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--target-ratio", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--ffmpeg", default="")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = export_rough_cut(args)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
