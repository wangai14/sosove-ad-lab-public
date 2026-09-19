from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_VAULT_ROOT = Path(
    os.environ.get("SEEDANCE_OBSIDIAN_MATERIAL_ROOT")
    or Path(__file__).resolve().parents[4] / "material-vault"
)
DEFAULT_LOCAL_BASE_URL = os.environ.get("SEEDANCE_LOCAL_ASSET_BASE_URL") or "http://127.0.0.1:8794"

UPLOAD_KINDS = {
    "images": {"kind": "image", "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif"}},
    "videos": {"kind": "video", "extensions": {".mp4", ".mov", ".webm", ".m4v"}},
    "audios": {"kind": "audio", "extensions": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm", ".flac"}},
}

ROLE_LABELS = {
    "hook": "开头钩子",
    "try_on": "上身展示",
    "detail": "细节特写",
    "motion": "动作镜头",
    "transition": "转场",
    "proof": "卖点证明",
    "bgm": "BGM / 音效",
    "ending": "结尾召回",
}

AD_STAGE_LABELS = {
    "hook": "开头钩子",
    "intro": "中段介绍",
    "detail": "细节卖点",
    "try_on": "上身展示",
    "proof": "效果证明",
    "motion": "动作节奏",
    "transition": "转场过渡",
    "cta": "结尾转化",
}

PRIORITY_RANK = {"high": 3, "normal": 2, "low": 1}
AUTO_EDIT_POOL_NAME = "auto-edit-pool.json"

ROLE_KEYWORDS = {
    "detail": [
        "细节", "特写", "近景", "面料", "材质", "纹理", "走线", "纽扣", "斜扣", "扣子", "腰头", "腰部", "口袋",
        "裤脚", "裤腰", "拉链", "版型细节", "detail", "close", "closeup", "close-up", "button", "waist", "pocket",
        "生地", "素材", "ディテール", "ボタン", "ウエスト", "ポケット",
    ],
    "try_on": [
        "上身", "试穿", "穿搭", "模特", "全身", "半身", "真人", "展示", "look", "try", "tryon", "try-on",
        "model", "fit", "wear", "着用", "試着", "コーデ", "全身",
    ],
    "motion": [
        "动作", "走路", "行走", "转身", "旋转", "摆动", "抬腿", "坐下", "动态", "motion", "walk", "turn",
        "move", "movement", "歩く", "動き", "ターン",
    ],
    "proof": [
        "显瘦", "遮肉", "腿长", "高腰", "修饰", "版型", "垂感", "舒适", "弹力", "主力", "爆款", "卖点",
        "proof", "slim", "shape", "脚長", "細見え", "体型カバー", "楽ちん", "人気",
    ],
    "hook": [
        "开头", "钩子", "封面", "第一眼", "主图", "爆点", "亮点", "hook", "opening", "cover", "top", "first",
        "冒頭", "注目",
    ],
    "transition": [
        "转场", "空镜", "氛围", "过渡", "切换", "节奏", "transition", "bridge", "broll", "b-roll", "cut",
    ],
    "ending": [
        "结尾", "收尾", "cta", "召回", "详情", "下单", "ending", "end", "closing", "最後", "チェック",
    ],
}

PRODUCT_KEYWORDS = {
    "pants": ["裤", "牛仔裤", "阔腿", "长裤", "裤脚", "裤腰", "jeans", "pants", "denim", "パンツ", "デニム"],
    "dress": ["连衣裙", "裙", "dress", "onepiece", "ワンピース", "スカート"],
    "tops": ["上衣", "衬衫", "针织", "毛衣", "t恤", "top", "shirt", "blouse", "トップス"],
    "outer": ["外套", "大衣", "夹克", "coat", "jacket", "outer", "アウター"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync and analyze uploaded video materials in the Obsidian material vault.")
    parser.add_argument("--vault-root", default=str(DEFAULT_VAULT_ROOT), help="Obsidian material vault root.")
    parser.add_argument("--library", default="", help="Explicit material-library.json path.")
    parser.add_argument("--local-base-url", default=DEFAULT_LOCAL_BASE_URL, help="Local URL base used for synced upload entries.")
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe") or "ffprobe", help="ffprobe executable path.")
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg", help="ffmpeg executable path.")
    parser.add_argument("--frame-count", type=int, default=6, help="Number of frames to sample per video.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of videos to analyze. 0 means no limit.")
    parser.add_argument("--batch", default="", help="Only analyze video items in the matching batch id or exact batch name.")
    parser.add_argument("--max-frame-records", type=int, default=5000, help="Maximum per-frame metadata records to store per video.")
    parser.add_argument("--segment-seconds", type=float, default=3.0, help="Smart segment window size in seconds.")
    parser.add_argument("--segment-stride-seconds", type=float, default=1.0, help="Smart segment scan stride in seconds.")
    parser.add_argument("--max-segments", type=int, default=80, help="Maximum smart segments to store per video.")
    parser.add_argument("--max-visual-seconds", type=int, default=240, help="Maximum seconds to sample for visual quality metrics.")
    parser.add_argument("--no-frame-index", action="store_true", help="Skip ffprobe per-frame metadata indexing.")
    parser.add_argument("--no-visual-metrics", action="store_true", help="Skip per-second brightness/sharpness/motion sampling.")
    parser.add_argument("--force", action="store_true", help="Re-analyze videos even when already analyzed or ready.")
    parser.add_argument("--no-sync", action="store_true", help="Do not scan uploads/ for missing material entries before analysis.")
    parser.add_argument("--sync-only", action="store_true", help="Only sync upload files into the library; do not analyze videos.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files or frames.")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return make_empty_library()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Material library must be a JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_empty_library() -> dict[str, Any]:
    batch_id = f"batch-{hashlib.sha1(utc_now().encode()).hexdigest()[:10]}"
    return {
        "version": 1,
        "updatedAt": utc_now(),
        "activeId": batch_id,
        "filterBatchId": "all",
        "filterTag": "all",
        "batches": [{"id": batch_id, "name": "默认批次", "createdAt": utc_now()}],
        "items": {},
    }


def ensure_library_shape(library: dict[str, Any]) -> None:
    batches = library.get("batches")
    if not isinstance(batches, list) or not batches:
        batch_id = f"batch-{hashlib.sha1(utc_now().encode()).hexdigest()[:10]}"
        library["batches"] = [{"id": batch_id, "name": "默认批次", "createdAt": utc_now()}]
        library["activeId"] = batch_id
    if not library.get("activeId"):
        library["activeId"] = library["batches"][0]["id"]
    if not isinstance(library.get("items"), dict):
        library["items"] = {}
    library.setdefault("version", 1)
    library.setdefault("filterBatchId", "all")
    library.setdefault("filterTag", "all")


def active_batch_id(library: dict[str, Any]) -> str:
    ensure_library_shape(library)
    return str(library.get("activeId") or library["batches"][0]["id"])


def safe_name(value: str, fallback: str = "material") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return cleaned[:80] or fallback


def item_id(url: str, item: dict[str, Any]) -> str:
    base = item.get("name") or Path(urlparse(url).path).name or "video"
    digest = hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:10]
    return f"{safe_name(str(base), 'video')}-{digest}"


def clean_base_url(value: str) -> str:
    return str(value or DEFAULT_LOCAL_BASE_URL).strip().rstrip("/")


def upload_url(base_url: str, folder: str, filename: str) -> str:
    return f"{clean_base_url(base_url)}/uploads/{folder}/{filename}"


def default_analysis(status: str = "queued") -> dict[str, Any]:
    return {
        "status": status,
        "frameCount": 0,
        "keyframes": [],
        "summary": "",
        "suggestions": [],
        "autoTags": [],
        "frameIndex": {},
        "cutHints": [],
        "segments": [],
        "updatedAt": "",
    }


def default_technical(kind: str) -> dict[str, Any]:
    return {
        "width": 0,
        "height": 0,
        "durationMs": 0,
        "fps": 0.0,
        "bitrateKbps": 0,
        "orientation": "audio" if kind == "audio" else "unknown",
        "hasAudio": kind == "audio",
        "videoCodec": "",
        "audioCodec": "",
    }


def existing_upload_keys(items: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for url, item in items.items():
        if not isinstance(item, dict):
            continue
        for value in [item.get("obsidianPath"), item.get("localPath")]:
            text = str(value or "").strip().replace("\\", "/").lstrip("/")
            if text:
                keys.add(text)
        parsed = urlparse(str(url or ""))
        path = parsed.path.replace("\\", "/").lstrip("/")
        if path.startswith("uploads/"):
            keys.add(path)
    return keys


def ignored_upload_keys(root: Path) -> set[str]:
    ignore_path = root / "data" / "upload-sync-ignore.json"
    if not ignore_path.exists() or not ignore_path.is_file():
        return set()
    try:
        data = json.loads(ignore_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    raw_paths = data.get("paths") if isinstance(data, dict) else []
    return {
        str(path or "").strip().replace("\\", "/").lstrip("/")
        for path in raw_paths
        if str(path or "").strip().replace("\\", "/").lstrip("/").startswith("uploads/")
    }


def sync_uploads(library: dict[str, Any], root: Path, local_base_url: str) -> list[dict[str, Any]]:
    ensure_library_shape(library)
    items: dict[str, Any] = library["items"]
    existing = existing_upload_keys(items)
    ignored = ignored_upload_keys(root)
    added: list[dict[str, Any]] = []
    batch_id = active_batch_id(library)
    upload_root = root / "uploads"
    for folder, config in UPLOAD_KINDS.items():
        folder_path = upload_root / folder
        if not folder_path.exists():
            continue
        for path in sorted(folder_path.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file() or path.suffix.lower() not in config["extensions"]:
                continue
            rel = f"uploads/{folder}/{path.name}"
            if rel in ignored:
                continue
            if rel in existing:
                continue
            kind = str(config["kind"])
            url = upload_url(local_base_url, folder, path.name)
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            items[url] = {
                "batchId": batch_id,
                "tags": [],
                "kind": kind,
                "name": path.name,
                "size": path.stat().st_size,
                "contentType": content_type,
                "localPath": f"/uploads/{folder}/{path.name}",
                "obsidianPath": rel,
                "technical": default_technical(kind),
                "analysisStatus": "queued",
                "editRole": "bgm" if kind == "audio" else "unassigned",
                "priority": "normal",
                "qualityScore": 0,
                "aiTags": [],
                "notes": "",
                "analysis": default_analysis("queued"),
                "addedAt": utc_now(),
            }
            existing.add(rel)
            added.append({"url": url, "kind": kind, "name": path.name, "path": rel})
    if added:
        library["updatedAt"] = utc_now()
    return added


def resolve_source_path(item: dict[str, Any], vault_root: Path) -> Path | None:
    for key in ("sourcePath", "externalPath"):
        raw_path = str(item.get(key) or "").strip()
        if raw_path:
            candidate = Path(raw_path).expanduser()
            if candidate.exists() and candidate.is_file():
                return candidate
    obsidian_path = str(item.get("obsidianPath") or "").strip()
    if obsidian_path:
        candidate = (vault_root / obsidian_path).resolve()
        try:
            candidate.relative_to(vault_root.resolve())
        except ValueError:
            candidate = None
        if candidate and candidate.exists() and candidate.is_file():
            return candidate
    local_path = str(item.get("localPath") or "").strip()
    if local_path.startswith("/uploads/"):
        candidate = (vault_root / urlparse(local_path).path.lstrip("/")).resolve()
        try:
            candidate.relative_to(vault_root.resolve())
        except ValueError:
            candidate = None
        if candidate and candidate.exists() and candidate.is_file():
            return candidate
    return None


def run_json(command: list[str], timeout: int = 12) -> dict[str, Any]:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return json.loads(result.stdout or "{}")


def parse_float(value: object) -> float:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return number if number > 0 else 0.0


def parse_int(value: object) -> int:
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def parse_fps(value: object) -> float:
    raw = str(value or "").strip()
    if not raw or raw == "0/0":
        return 0.0
    if "/" in raw:
        numerator, denominator = raw.split("/", 1)
        denominator_value = parse_float(denominator)
        return round(parse_float(numerator) / denominator_value, 3) if denominator_value else 0.0
    return round(parse_float(raw), 3)


def material_search_text(item: dict[str, Any]) -> str:
    analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else {}
    parts: list[str] = [
        str(item.get("name") or ""),
        str(item.get("sourcePath") or ""),
        str(item.get("externalPath") or ""),
        str(item.get("sourceUrl") or ""),
        str(item.get("notes") or ""),
        str(analysis.get("summary") or ""),
    ]
    for key in ("tags", "aiTags"):
        values = item.get(key)
        if isinstance(values, list):
            parts.extend(str(value) for value in values)
    suggestions = analysis.get("suggestions") if isinstance(analysis.get("suggestions"), list) else []
    parts.extend(str(value) for value in suggestions)
    return " ".join(parts).lower()


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    haystack = str(text or "").lower()
    hits: list[str] = []
    for keyword in keywords:
        key = str(keyword or "").lower()
        if key and key in haystack and keyword not in hits:
            hits.append(keyword)
    return hits


def role_keyword_scores(text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    for role, keywords in ROLE_KEYWORDS.items():
        hits = keyword_hits(text, keywords)
        if hits:
            scores[role] = len(hits) * 12 + min(18, sum(len(str(hit)) for hit in hits) // 3)
    return scores


def dominant_product_type(text: str) -> str:
    best_type = ""
    best_score = 0
    for product_type, keywords in PRODUCT_KEYWORDS.items():
        score = len(keyword_hits(text, keywords))
        if score > best_score:
            best_type = product_type
            best_score = score
    return best_type


def material_primary_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            str(item.get("name") or ""),
            str(item.get("sourcePath") or ""),
            str(item.get("externalPath") or ""),
            str(item.get("sourceUrl") or ""),
        ]
    ).lower()


def material_product_type(item: dict[str, Any]) -> str:
    primary = material_primary_text(item)
    primary_type = dominant_product_type(primary)
    if primary_type:
        return primary_type
    return dominant_product_type(material_search_text(item))


def orientation(width: int, height: int) -> str:
    if not width or not height:
        return "unknown"
    if width == height:
        return "square"
    return "landscape" if width > height else "portrait"


def probe_video(path: Path, ffprobe: str) -> dict[str, Any]:
    payload = run_json([
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration,bit_rate:format=duration,bit_rate",
        "-of",
        "json",
        str(path),
    ])
    streams = payload.get("streams") if isinstance(payload.get("streams"), list) else []
    fmt = payload.get("format") if isinstance(payload.get("format"), dict) else {}
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    width = parse_int(video.get("width"))
    height = parse_int(video.get("height"))
    duration_ms = int(round(parse_float(fmt.get("duration") or video.get("duration")) * 1000))
    bitrate = parse_float(fmt.get("bit_rate") or video.get("bit_rate") or audio.get("bit_rate"))
    return {
        "width": width,
        "height": height,
        "durationMs": duration_ms,
        "fps": parse_fps(video.get("avg_frame_rate")),
        "bitrateKbps": int(round(bitrate / 1000)) if bitrate else 0,
        "orientation": orientation(width, height),
        "hasAudio": bool(audio),
        "videoCodec": str(video.get("codec_name") or "")[:80],
        "audioCodec": str(audio.get("codec_name") or "")[:80],
    }


def frame_positions(duration_ms: int, count: int) -> list[float]:
    count = max(1, min(count, 12))
    if duration_ms <= 0:
        return [0.0]
    duration_s = duration_ms / 1000
    if duration_s <= 1:
        return [0.0]
    return [round(min(duration_s - 0.08, duration_s * (index + 1) / (count + 1)), 3) for index in range(count)]


def extract_frames(path: Path, frame_dir: Path, ffmpeg: str, duration_ms: int, count: int, dry_run: bool) -> list[dict[str, Any]]:
    positions = frame_positions(duration_ms, count)
    if dry_run:
        return [{"timeMs": int(pos * 1000), "path": "", "note": "dry-run frame"} for pos in positions]
    frames: list[dict[str, Any]] = []
    frame_dir.mkdir(parents=True, exist_ok=True)
    for index, position in enumerate(positions, start=1):
        target = frame_dir / f"frame_{index:03d}.jpg"
        command = [ffmpeg, "-y", "-ss", str(position), "-i", str(path), "-frames:v", "1", "-q:v", "3", str(target)]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, check=False)
        if result.returncode == 0 and target.exists():
            frames.append({"timeMs": int(position * 1000), "path": target, "note": "sampled keyframe"})
    return frames


def frame_time_ms(frame: dict[str, Any]) -> int:
    raw = frame.get("best_effort_timestamp_time") or frame.get("pkt_pts_time") or 0
    return int(round(parse_float(raw) * 1000))


def probe_frame_index(path: Path, ffprobe: str, max_records: int) -> dict[str, Any]:
    max_records = max(1, min(max_records, 50000))
    payload = run_json(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "frame=best_effort_timestamp_time,pkt_pts_time,pict_type,key_frame,coded_picture_number,pkt_size",
            "-of",
            "json",
            str(path),
        ],
        timeout=60,
    )
    source_frames = payload.get("frames") if isinstance(payload.get("frames"), list) else []
    records: list[dict[str, Any]] = []
    for index, frame in enumerate(source_frames):
        if len(records) >= max_records:
            break
        if not isinstance(frame, dict):
            continue
        records.append(
            {
                "index": index,
                "timeMs": frame_time_ms(frame),
                "pictType": str(frame.get("pict_type") or "")[:8],
                "keyFrame": str(frame.get("key_frame") or "0") == "1",
                "codedPictureNumber": parse_int(frame.get("coded_picture_number")),
                "packetSize": parse_int(frame.get("pkt_size")),
            }
        )
    return {
        "mode": "ffprobe-frame-metadata",
        "totalFrames": len(source_frames),
        "indexedFrames": len(records),
        "complete": len(records) == len(source_frames),
        "maxRecords": max_records,
        "frames": records,
    }


def write_frame_index(root: Path, vid: str, url: str, item: dict[str, Any], tech: dict[str, Any], frame_index: dict[str, Any], dry_run: bool) -> Path:
    target = root / "analysis" / "frame-index" / f"{vid}.json"
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sourceUrl": url,
                    "name": item.get("name") or "",
                    "technical": tech,
                    **frame_index,
                    "updatedAt": utc_now(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return target


def build_auto_tags(item: dict[str, Any], tech: dict[str, Any], role: str, status: str, score: int, frame_index: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    text = material_search_text(item)

    def add(tag: str) -> None:
        cleaned = str(tag or "").strip()
        if cleaned and cleaned not in tags:
            tags.append(cleaned)

    add("AI分析")
    add(ROLE_LABELS.get(role, role))
    add("可剪辑" if status == "ready" else "待复核")
    orientation_tag = {"portrait": "竖屏", "landscape": "横屏", "square": "方屏"}.get(str(tech.get("orientation") or ""))
    add(orientation_tag or "")
    duration_ms = parse_int(tech.get("durationMs"))
    if duration_ms <= 3000:
        add("短镜头")
    elif duration_ms >= 60000:
        add("长素材")
    else:
        add("标准片段")
    if max(parse_int(tech.get("width")), parse_int(tech.get("height"))) >= 1080:
        add("高清")
    if tech.get("hasAudio"):
        add("有音轨")
    else:
        add("无音轨")
    if score >= 4:
        add("优先混剪")
    elif score <= 2:
        add("低质复核")
    if parse_int(frame_index.get("totalFrames")):
        add("帧级索引")
    product_type = material_product_type(item)
    if product_type:
        add({"pants": "裤装", "dress": "裙装", "tops": "上装", "outer": "外套"}[product_type])
    role_scores = role_keyword_scores(text)
    for related_role, related_score in sorted(role_scores.items(), key=lambda pair: pair[1], reverse=True)[:3]:
        add(f"文本命中-{ROLE_LABELS.get(related_role, related_role)}")
    for keyword in keyword_hits(text, ["斜扣", "腰头", "口袋", "显瘦", "腿长", "阔腿", "牛仔", "面料", "垂感", "高腰"])[:6]:
        add(keyword)
    for tag in item.get("tags") or []:
        text = str(tag)
        if text in {"成品", "定制", "高光镜", "营销", "单品图展示", "达人素材", "数字人试穿"}:
            add(text)
    return tags[:32]


def build_cut_hints(tech: dict[str, Any], role: str, score: int) -> list[dict[str, Any]]:
    duration_ms = parse_int(tech.get("durationMs"))
    if not duration_ms:
        return []
    hints: list[dict[str, Any]] = []
    if role == "transition" or duration_ms <= 3000:
        hints.append({"startMs": 0, "endMs": min(duration_ms, 3000), "role": "transition", "confidence": 0.74, "reason": "短片段适合节奏点或转场。"})
    elif role == "hook":
        hints.append({"startMs": 0, "endMs": min(duration_ms, 4500), "role": "hook", "confidence": 0.72, "reason": "前段适合开头钩子。"})
    elif role == "detail":
        hints.append({"startMs": max(0, duration_ms // 4), "endMs": min(duration_ms, duration_ms // 4 + 5000), "role": "detail", "confidence": 0.68, "reason": "中前段优先作为细节展示候选。"})
    elif role == "try_on":
        hints.append({"startMs": 0, "endMs": min(duration_ms, 8000), "role": "try_on", "confidence": 0.7, "reason": "优先作为上身展示主镜头。"})
    else:
        hints.append({"startMs": 0, "endMs": min(duration_ms, 6000), "role": role, "confidence": 0.62, "reason": "按当前素材用途生成的默认候选段。"})
    if duration_ms > 12000:
        midpoint = duration_ms // 2
        hints.append({"startMs": max(0, midpoint - 2500), "endMs": min(duration_ms, midpoint + 2500), "role": "backup", "confidence": 0.55, "reason": "中段作为自动混剪备用镜头。"})
    if score <= 2:
        for hint in hints:
            hint["confidence"] = round(max(0.35, float(hint["confidence"]) - 0.18), 2)
            hint["reason"] = f"{hint['reason']} 质量分偏低，需复核。"
    return hints[:4]


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def median_number(values: list[float]) -> float:
    cleaned = sorted(float(value) for value in values if float(value or 0) > 0)
    if not cleaned:
        return 0.0
    midpoint = len(cleaned) // 2
    if len(cleaned) % 2:
        return cleaned[midpoint]
    return (cleaned[midpoint - 1] + cleaned[midpoint]) / 2


def append_unique(target: list[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in target:
        target.append(text)


def timeline_zone(progress: float) -> str:
    if progress < 0.16:
        return "opening"
    if progress < 0.38:
        return "early"
    if progress < 0.68:
        return "middle"
    if progress < 0.88:
        return "late"
    return "ending"


def timeline_zone_label(zone: str) -> str:
    return {
        "opening": "开头",
        "early": "前段",
        "middle": "中段",
        "late": "后段",
        "ending": "尾段",
    }.get(zone, "中段")


def sample_second_visual_metrics(path: Path, duration_ms: int, max_seconds: int) -> list[dict[str, Any]]:
    second_count = max(0, min(parse_int(max_seconds) or 0, int((duration_ms + 999) // 1000)))
    if second_count <= 0:
        return []
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return []

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []

    metrics: list[dict[str, Any]] = []
    previous_thumb: Any = None
    try:
        for second in range(second_count):
            sample_ms = min(max(0, duration_ms - 80), second * 1000 + 500)
            cap.set(cv2.CAP_PROP_POS_MSEC, sample_ms)
            ok, frame = cap.read()
            if not ok or frame is None:
                metrics.append({"second": second})
                previous_thumb = None
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            thumb = cv2.resize(gray, (96, 128), interpolation=cv2.INTER_AREA)
            brightness = float(np.mean(gray))
            contrast = float(np.std(gray))
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            motion = 0.0 if previous_thumb is None else float(np.mean(cv2.absdiff(thumb, previous_thumb)))
            previous_thumb = thumb
            metrics.append(
                {
                    "second": second,
                    "brightness": round(brightness, 1),
                    "contrast": round(contrast, 1),
                    "sharpness": round(sharpness, 1),
                    "visualMotion": round(motion, 1),
                }
            )
    finally:
        cap.release()
    return metrics


def visual_note(visual: dict[str, Any]) -> str:
    if not visual:
        return ""
    brightness = parse_float(visual.get("brightness"))
    sharpness = parse_float(visual.get("sharpness"))
    motion = parse_float(visual.get("visualMotion"))
    if sharpness and sharpness < 28:
        return "清晰度偏软"
    if motion >= 18:
        return "动作变化明显"
    if brightness and brightness < 45:
        return "画面偏暗"
    if brightness > 220:
        return "曝光偏亮"
    if sharpness >= 90:
        return "细节清晰"
    return "画面稳定"


def second_mark_judgement(
    frame_count: int,
    key_frames: int,
    avg_packet: int,
    score: int,
    tech: dict[str, Any] | None = None,
    role: str = "",
    context: dict[str, Any] | None = None,
    visual: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tech = tech or {}
    context = context or {}
    visual = visual or {}
    pros: list[str] = []
    cons: list[str] = []
    fps = parse_float(tech.get("fps"))
    orientation_value = str(tech.get("orientation") or "")
    packet_ratio = parse_float(context.get("packetRatio"))
    frame_ratio = parse_float(context.get("frameRatio"))
    motion_delta = parse_float(context.get("motionDelta"))
    progress = parse_float(context.get("progress"))
    zone = str(context.get("timelineZone") or timeline_zone(progress))
    second = parse_int(context.get("second"))
    peak = str(context.get("packetPeak") or "")
    role_label = ROLE_LABELS.get(role, role or "镜头")

    if frame_ratio >= 0.92 or frame_count >= 20:
        append_unique(pros, "帧连续，顺剪安全")
    elif frame_ratio >= 0.62 or frame_count >= 10:
        append_unique(pros, "帧数基本够用")
    elif frame_count > 0:
        append_unique(cons, "这一秒帧数偏少，动作可能不连贯")
    else:
        append_unique(cons, "缺少帧数据")

    if packet_ratio >= 1.35:
        append_unique(pros, "信息量明显高于全片")
    elif packet_ratio >= 1.08:
        append_unique(pros, "画面信息量偏高")
    elif packet_ratio >= 0.78:
        append_unique(pros, "画面信息量稳定")
    elif avg_packet:
        append_unique(cons, "信息量低于全片均值")

    if motion_delta >= 0.5:
        append_unique(pros, "前后画面变化强，适合做切点")
    elif motion_delta >= 0.18:
        append_unique(pros, "有轻微动作变化")
    elif zone not in {"opening", "ending"}:
        append_unique(cons, "画面变化小，避免停留太久")

    if key_frames:
        append_unique(pros, "有关键帧，可做切入点")
    else:
        append_unique(cons, "缺少关键帧，转场需留余量")

    brightness = parse_float(visual.get("brightness"))
    contrast = parse_float(visual.get("contrast"))
    sharpness = parse_float(visual.get("sharpness"))
    visual_motion = parse_float(visual.get("visualMotion"))
    if visual:
        if sharpness >= 90:
            append_unique(pros, "画面细节清晰")
        elif sharpness and sharpness < 28:
            append_unique(cons, "清晰度偏软")
        if 50 <= brightness <= 210:
            append_unique(pros, "曝光正常")
        elif brightness and brightness < 45:
            append_unique(cons, "画面偏暗")
        elif brightness > 220:
            append_unique(cons, "曝光偏亮")
        if contrast >= 32:
            append_unique(pros, "层次感可用")
        elif contrast and contrast < 18:
            append_unique(cons, "对比度偏弱")
        if visual_motion >= 18:
            append_unique(pros, "视觉动作变化明显")
        elif visual_motion and visual_motion < 4 and role == "motion":
            append_unique(cons, "动作镜头感不足")

    if peak == "high":
        append_unique(pros, f"{timeline_zone_label(zone)}信息高点")
    elif peak == "low":
        append_unique(cons, f"{timeline_zone_label(zone)}信息低点")

    if fps >= 24:
        append_unique(pros, "帧率适合短视频")
    elif fps and fps < 20:
        append_unique(cons, "帧率偏低")
    if orientation_value == "landscape":
        append_unique(cons, "横版需裁切适配")

    if score >= 78:
        tone = "good"
        advice = f"这一秒质量高，可优先作为{role_label}主镜头。"
    elif score >= 62:
        tone = "ok"
        advice = f"这一秒可用，建议和相邻高分秒拼成{role_label}片段。"
    elif score >= 48:
        tone = "warn"
        advice = "只建议短用，生成前最好人工预览。"
    else:
        tone = "bad"
        advice = "不建议自动使用，除非人工确认画面可用。"

    if score >= 58:
        if zone == "opening" and packet_ratio >= 0.9:
            advice = "适合放在开头，承接第一句文案或建立商品主体。"
        elif peak == "high" and role == "detail":
            advice = "适合讲细节卖点，建议配合纽扣、腰头、面料类文案。"
        elif peak == "high" and role == "try_on":
            advice = "适合承接上身展示文案，可作为主展示镜头。"
        elif motion_delta >= 0.35 or visual_motion >= 18:
            advice = "适合做动作切点或转场前后 0.3 秒的节奏镜头。"
        elif role == "proof" and zone in {"middle", "late"}:
            advice = "适合放在卖点证明段，承接显瘦、版型、腿长类文案。"
        elif zone == "ending":
            advice = "适合做尾段收束，搭配下单提醒或品牌露出。"

    return {
        "pros": pros[:4],
        "cons": cons[:4],
        "cutAdvice": advice,
        "tone": tone,
    }


def second_marks_from_frames(
    frame_index: dict[str, Any],
    duration_ms: int,
    tech: dict[str, Any] | None = None,
    role: str = "",
    visual_metrics: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    frames = frame_index.get("frames") if isinstance(frame_index.get("frames"), list) else []
    if not duration_ms:
        return []
    second_count = max(1, min(3600, int((duration_ms + 999) // 1000)))
    buckets: list[dict[str, Any]] = [
        {"second": index, "startMs": index * 1000, "endMs": min(duration_ms, (index + 1) * 1000), "frameCount": 0, "keyFrames": 0, "packetTotal": 0, "iFrames": 0}
        for index in range(second_count)
    ]
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        time_ms = min(duration_ms, max(0, parse_int(frame.get("timeMs"))))
        bucket_index = min(second_count - 1, time_ms // 1000)
        bucket = buckets[bucket_index]
        bucket["frameCount"] += 1
        if frame.get("keyFrame"):
            bucket["keyFrames"] += 1
        if str(frame.get("pictType") or "").upper() == "I":
            bucket["iFrames"] += 1
        bucket["packetTotal"] += parse_int(frame.get("packetSize"))
    for bucket in buckets:
        frame_count = parse_int(bucket.get("frameCount"))
        bucket["avgPacketSize"] = int(round(parse_int(bucket.get("packetTotal")) / frame_count)) if frame_count else 0

    frame_counts = [parse_int(bucket.get("frameCount")) for bucket in buckets if parse_int(bucket.get("frameCount"))]
    packet_values = [parse_int(bucket.get("avgPacketSize")) for bucket in buckets if parse_int(bucket.get("avgPacketSize"))]
    typical_frame_count = median_number([float(value) for value in frame_counts]) or parse_float((tech or {}).get("fps")) or max(frame_counts or [1])
    median_packet = median_number([float(value) for value in packet_values]) or max(packet_values or [1])
    sorted_packets = sorted(packet_values)
    visual_by_second = {
        parse_int(item.get("second")): item
        for item in (visual_metrics or [])
        if isinstance(item, dict)
    }
    marks: list[dict[str, Any]] = []
    for index, bucket in enumerate(buckets):
        frame_count = parse_int(bucket.get("frameCount"))
        avg_packet = parse_int(bucket.get("avgPacketSize"))
        frame_ratio = frame_count / typical_frame_count if typical_frame_count else 0.0
        packet_ratio = avg_packet / median_packet if median_packet else 0.0
        prev_packet = parse_int(buckets[index - 1].get("avgPacketSize")) if index > 0 else avg_packet
        next_packet = parse_int(buckets[index + 1].get("avgPacketSize")) if index + 1 < len(buckets) else avg_packet
        motion_delta = max(abs(avg_packet - prev_packet), abs(avg_packet - next_packet)) / median_packet if median_packet else 0.0
        packet_rank = 0.0
        if avg_packet and sorted_packets:
            packet_rank = sum(1 for value in sorted_packets if value <= avg_packet) / len(sorted_packets)
        peak = "high" if packet_rank >= 0.78 else "low" if packet_rank <= 0.22 else "mid"
        second = parse_int(bucket.get("second"))
        progress = parse_int(bucket.get("startMs")) / duration_ms if duration_ms else 0.0
        zone = timeline_zone(progress)
        visual = visual_by_second.get(second, {})

        score = 48
        if frame_ratio >= 0.92:
            score += 13
        elif frame_ratio >= 0.62:
            score += 7
        elif frame_ratio > 0:
            score -= 8
        else:
            score -= 16
        if packet_ratio >= 1.35:
            score += 15
        elif packet_ratio >= 1.08:
            score += 10
        elif packet_ratio >= 0.78:
            score += 4
        elif packet_ratio > 0:
            score -= 9
        if motion_delta >= 0.5:
            score += 7 if role in {"hook", "motion", "transition", "try_on"} else 3
        elif motion_delta >= 0.18:
            score += 4
        elif role == "motion":
            score -= 4
        if parse_int(bucket.get("keyFrames")) or parse_int(bucket.get("iFrames")):
            score += 4

        brightness = parse_float(visual.get("brightness"))
        contrast = parse_float(visual.get("contrast"))
        sharpness = parse_float(visual.get("sharpness"))
        visual_motion = parse_float(visual.get("visualMotion"))
        if visual:
            if sharpness >= 90:
                score += 8
            elif sharpness >= 38:
                score += 3
            elif sharpness:
                score -= 8
            if 50 <= brightness <= 210:
                score += 3
            elif brightness:
                score -= 6
            if contrast >= 32:
                score += 3
            elif contrast and contrast < 18:
                score -= 3
            if visual_motion >= 18:
                score += 4 if role in {"motion", "try_on", "hook"} else 2

        if zone == "opening" and score >= 58:
            score += 3
        elif zone == "ending" and role == "ending":
            score += 3

        note_parts: list[str] = []
        if peak == "high":
            note_parts.append(f"{timeline_zone_label(zone)}信息高点")
        elif peak == "low":
            note_parts.append(f"{timeline_zone_label(zone)}信息低点")
        else:
            note_parts.append(f"{timeline_zone_label(zone)}稳定承接")
        v_note = visual_note(visual)
        if v_note:
            note_parts.append(v_note)
        elif motion_delta >= 0.35:
            note_parts.append("前后变化明显")
        elif frame_count < 5:
            note_parts.append("帧数据偏少")
        note = "，".join(note_parts[:2])
        context = {
            "second": second,
            "packetRatio": round(packet_ratio, 2),
            "frameRatio": round(frame_ratio, 2),
            "motionDelta": round(motion_delta, 2),
            "progress": round(progress, 3),
            "timelineZone": zone,
            "packetPeak": peak,
        }
        judgement = second_mark_judgement(
            frame_count,
            parse_int(bucket.get("keyFrames")) or parse_int(bucket.get("iFrames")),
            avg_packet,
            clamp_score(score),
            tech,
            role,
            context,
            visual,
        )
        marks.append(
            {
                "second": second,
                "startMs": parse_int(bucket.get("startMs")),
                "endMs": parse_int(bucket.get("endMs")),
                "frameCount": frame_count,
                "keyFrames": parse_int(bucket.get("keyFrames")),
                "avgPacketSize": avg_packet,
                "relativePacket": round(packet_ratio, 2),
                "motionDelta": round(motion_delta, 2),
                "timelineZone": zone,
                "brightness": parse_float(visual.get("brightness")),
                "contrast": parse_float(visual.get("contrast")),
                "sharpness": parse_float(visual.get("sharpness")),
                "visualMotion": parse_float(visual.get("visualMotion")),
                "visualNote": visual_note(visual),
                "score": clamp_score(score),
                "note": note,
                **judgement,
            }
        )
    return marks


def segment_role(base_role: str, start_ms: int, end_ms: int, duration_ms: int) -> str:
    segment_duration = end_ms - start_ms
    progress = (start_ms / duration_ms) if duration_ms else 0
    if segment_duration <= 2200:
        return "transition" if base_role not in {"hook", "detail"} else base_role
    if start_ms <= 1500 and base_role in {"try_on", "motion", "proof", "transition"}:
        return "hook"
    if duration_ms and end_ms >= duration_ms - 2800 and base_role not in {"hook", "detail", "try_on"}:
        return "ending"
    if duration_ms >= 12000 and base_role == "try_on":
        if progress >= 0.58:
            return "proof"
        if progress >= 0.32:
            return "motion"
    if duration_ms >= 12000 and base_role == "motion" and 0.35 <= progress <= 0.7:
        return "try_on"
    if duration_ms >= 10000 and base_role == "proof" and progress <= 0.25:
        return "hook"
    return base_role or "unassigned"


def product_type_label(product_type: str) -> str:
    return {
        "pants": "裤装",
        "dress": "连衣裙",
        "tops": "上衣",
        "outer": "外套",
    }.get(product_type, "商品")


def product_signal_hits(text: str) -> list[str]:
    signal_keywords = [
        "斜扣", "腰头", "双扣", "纽扣", "口袋", "裤脚", "阔腿", "牛仔", "高腰", "显瘦", "遮肉", "腿长",
        "版型", "垂感", "面料", "弹力", "百搭", "主力", "爆款", "不规则",
        "ボタン", "ウエスト", "デニム", "脚長", "細見え", "体型カバー", "着回し",
    ]
    return keyword_hits(text, signal_keywords)[:8]


def ad_stage_for_segment(role: str, start_ms: int, end_ms: int, duration_ms: int, score: int, marks: list[dict[str, Any]]) -> str:
    progress = start_ms / duration_ms if duration_ms else 0.0
    avg_motion = sum(parse_float(mark.get("visualMotion")) for mark in marks) / len(marks) if marks else 0.0
    avg_relative = sum(parse_float(mark.get("relativePacket")) for mark in marks) / len(marks) if marks else 0.0
    avg_sharpness = sum(parse_float(mark.get("sharpness")) for mark in marks) / len(marks) if marks else 0.0
    if progress <= 0.18 and score >= 70:
        return "hook"
    if role == "ending" or (duration_ms and end_ms >= duration_ms - 2600):
        return "cta"
    if progress >= 0.86:
        return "cta"
    if role == "transition" or (end_ms - start_ms <= 1800 and avg_motion >= 12):
        return "transition"
    if progress < 0.38:
        if role == "detail" and avg_relative >= 1.35 and avg_sharpness >= 70:
            return "detail"
        return "intro"
    if progress >= 0.68:
        if role == "detail" and avg_relative >= 1.15 and avg_sharpness >= 70:
            return "detail"
        return "proof"
    if role == "proof":
        return "proof"
    if role == "detail":
        return "detail"
    if role == "motion" or avg_motion >= 18:
        return "motion"
    if role == "try_on":
        return "try_on"
    return "try_on"


def segment_strengths(score: int, marks: list[dict[str, Any]], stage: str) -> list[str]:
    strengths: list[str] = []
    avg_sharpness = sum(parse_float(mark.get("sharpness")) for mark in marks) / len(marks) if marks else 0.0
    avg_motion = sum(parse_float(mark.get("visualMotion")) for mark in marks) / len(marks) if marks else 0.0
    avg_relative = sum(parse_float(mark.get("relativePacket")) for mark in marks) / len(marks) if marks else 0.0
    key_frames = sum(parse_int(mark.get("keyFrames")) for mark in marks)
    if score >= 86:
        append_unique(strengths, "高分片段，可优先进主剪")
    elif score >= 74:
        append_unique(strengths, "可用度高，适合作为主片段")
    if avg_relative >= 1.25:
        append_unique(strengths, "画面信息量高，适合承载卖点")
    if avg_sharpness >= 90:
        append_unique(strengths, "清晰度高，商品细节更容易看清")
    if avg_motion >= 18:
        append_unique(strengths, "动作变化明显，适合带节奏")
    if key_frames:
        append_unique(strengths, "含关键帧，落剪点更安全")
    if stage == "hook":
        append_unique(strengths, "开头抓注意力能力强")
    elif stage == "detail":
        append_unique(strengths, "适合讲细节设计和卖点")
    elif stage == "proof":
        append_unique(strengths, "适合承接显瘦、版型、上身效果证明")
    return strengths[:5]


def segment_risks(marks: list[dict[str, Any]], stage: str) -> list[str]:
    risks: list[str] = []
    avg_sharpness = sum(parse_float(mark.get("sharpness")) for mark in marks) / len(marks) if marks else 0.0
    avg_motion = sum(parse_float(mark.get("visualMotion")) for mark in marks) / len(marks) if marks else 0.0
    low_seconds = [mark for mark in marks if parse_int(mark.get("score")) < 62]
    missing_key = sum(1 for mark in marks if not parse_int(mark.get("keyFrames")))
    if low_seconds:
        append_unique(risks, f"{len(low_seconds)} 秒质量偏低，建议避开或短用")
    if avg_sharpness and avg_sharpness < 38:
        append_unique(risks, "清晰度偏软，不适合讲细节")
    if stage in {"hook", "motion"} and avg_motion < 6:
        append_unique(risks, "画面变化偏小，节奏感不足")
    if missing_key >= max(2, len(marks) // 2):
        append_unique(risks, "关键帧少，转场前后需要留余量")
    return risks[:4]


def segment_content_description(stage: str, role: str, product_type: str, product_signals: list[str], marks: list[dict[str, Any]]) -> str:
    product = product_type_label(product_type)
    signals = "、".join(product_signals[:3])
    signal_text = f"；可关联卖点：{signals}" if signals else ""
    avg_motion = sum(parse_float(mark.get("visualMotion")) for mark in marks) / len(marks) if marks else 0.0
    avg_sharpness = sum(parse_float(mark.get("sharpness")) for mark in marks) / len(marks) if marks else 0.0
    visual_text = "动作变化明显" if avg_motion >= 18 else "画面稳定"
    if avg_sharpness >= 90:
        visual_text += "，细节清晰"
    stage_templates = {
        "hook": f"适合做广告开头，用 {product} 画面先抓注意力{signal_text}。",
        "intro": f"适合做中段产品介绍，承接商品名称、版型和核心卖点{signal_text}。",
        "detail": f"适合做细节卖点镜头，突出 {product} 的设计、材质或局部特征{signal_text}。",
        "try_on": f"适合做上身展示，说明穿着效果、搭配感和整体版型{signal_text}。",
        "proof": f"适合做效果证明，承接显瘦、遮肉、腿长、版型修饰类文案{signal_text}。",
        "motion": f"适合做动作节奏镜头，用走动/转身/摆动增强广告节奏{signal_text}。",
        "transition": f"适合做转场过渡，连接两个卖点或作为节奏切换点{signal_text}。",
        "cta": f"适合做结尾转化，配合下单提醒、主推款强调或品牌露出{signal_text}。",
    }
    return f"{stage_templates.get(stage, stage_templates['intro'])} 画面判断：{visual_text}。"


def segment_copy_angle(stage: str, product_signals: list[str]) -> str:
    signals = "、".join(product_signals[:3])
    if stage == "hook":
        return "开头可用强问题/强利益点：为什么这条裤子最近主推？"
    if stage == "intro":
        return f"介绍商品核心：{signals or '版型、颜色、适合人群'}。"
    if stage == "detail":
        return f"讲局部设计：{signals or '腰头、纽扣、口袋、面料'}。"
    if stage == "try_on":
        return "讲上身效果：显瘦、腿长、搭配不挑人。"
    if stage == "proof":
        return "讲结果证明：遮肉、修饰腿型、日常好穿。"
    if stage == "motion":
        return "配合节奏文案或 BGM 节拍，用来制造剪辑动感。"
    if stage == "cta":
        return "结尾引导：主推款、尺码/颜色、现在下单。"
    return "承接上下文，作为过渡文案或补充说明。"


def build_smart_segments(
    tech: dict[str, Any],
    role: str,
    item_score: int,
    frame_index: dict[str, Any],
    segment_seconds: float,
    stride_seconds: float,
    max_segments: int,
    item_text: str = "",
    product_type: str = "",
    second_marks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    duration_ms = parse_int(tech.get("durationMs"))
    if duration_ms < 1200:
        return []
    segment_ms = max(1200, min(12000, int(round(parse_float(segment_seconds) * 1000)) or 3000))
    stride_ms = max(500, min(segment_ms, int(round(parse_float(stride_seconds) * 1000)) or 1000))
    max_segments = max(1, min(parse_int(max_segments) or 80, 200))
    second_marks = second_marks if second_marks is not None else second_marks_from_frames(frame_index, duration_ms, tech, role)
    if not second_marks:
        second_marks = [
            {
                "second": index,
                "startMs": index * 1000,
                "endMs": min(duration_ms, (index + 1) * 1000),
                "frameCount": 0,
                "keyFrames": 0,
                "avgPacketSize": 0,
                "score": 50,
                "note": "未建立每秒帧数据",
                "pros": [],
                "cons": ["未建立帧级索引"],
                "cutAdvice": "需要先建立帧索引后再判断这一秒的画面优缺点。",
                "tone": "warn",
            }
            for index in range(max(1, int((duration_ms + 999) // 1000)))
        ]

    starts: list[int] = []
    cursor = 0
    while cursor < duration_ms and len(starts) < max_segments * 2:
        starts.append(cursor)
        if cursor + segment_ms >= duration_ms:
            break
        cursor += stride_ms
    if starts and starts[-1] + segment_ms < duration_ms and duration_ms > segment_ms:
        starts.append(max(0, duration_ms - segment_ms))

    segments: list[dict[str, Any]] = []
    width = parse_int(tech.get("width"))
    height = parse_int(tech.get("height"))
    pixels = width * height
    text_role_scores = role_keyword_scores(item_text)
    product_type = product_type or dominant_product_type(item_text)
    product_signals = product_signal_hits(item_text)
    for index, start_ms in enumerate(starts):
        end_ms = min(duration_ms, start_ms + segment_ms)
        if end_ms - start_ms < 1200:
            continue
        marks = [mark for mark in second_marks if parse_int(mark.get("endMs")) > start_ms and parse_int(mark.get("startMs")) < end_ms]
        mark_score = sum(parse_int(mark.get("score")) for mark in marks) / len(marks) if marks else 50
        role_value = segment_role(role, start_ms, end_ms, duration_ms)
        score = mark_score * 0.45 + item_score * 10
        if tech.get("orientation") == "portrait":
            score += 8
        elif tech.get("orientation") == "square":
            score += 5
        if pixels >= 720 * 1280:
            score += 8
        elif pixels >= 540 * 960:
            score += 4
        if 1800 <= end_ms - start_ms <= 6000:
            score += 8
        if start_ms <= 1000:
            score += 5
        if parse_float(tech.get("fps")) >= 24:
            score += 3
        score += min(12, text_role_scores.get(role_value, 0) * 0.25)
        if product_type == "pants" and role_value in {"try_on", "motion", "proof", "detail"}:
            score += 4
        if role_value == "hook" and start_ms <= 1500:
            score += 5
        elif role_value == "ending" and duration_ms and end_ms >= duration_ms - 3000:
            score += 4
        elif role_value == "detail" and 1200 <= end_ms - start_ms <= 4500:
            score += 4
        key_frames = sum(parse_int(mark.get("keyFrames")) for mark in marks)
        if key_frames:
            score += 3
        segment_score = clamp_score(score)
        confidence = round(max(0.35, min(0.98, segment_score / 100)), 2)
        ad_stage = ad_stage_for_segment(role_value, start_ms, end_ms, duration_ms, segment_score, marks)
        strengths = segment_strengths(segment_score, marks, ad_stage)
        risks = segment_risks(marks, ad_stage)
        content_description = segment_content_description(ad_stage, role_value, product_type, product_signals, marks)
        copy_angle = segment_copy_angle(ad_stage, product_signals)
        reason_parts = [
            f"{round((end_ms - start_ms) / 1000, 2)} 秒智能片段",
            f"每秒均分 {round(mark_score, 1)}",
            ROLE_LABELS.get(role_value, role_value),
            AD_STAGE_LABELS.get(ad_stage, ad_stage),
        ]
        if key_frames:
            reason_parts.append("含关键帧")
        if strengths:
            reason_parts.append(strengths[0])
        segments.append(
            {
                "id": f"seg-{index + 1:03d}",
                "startMs": start_ms,
                "endMs": end_ms,
                "durationMs": end_ms - start_ms,
                "role": role_value,
                "adStage": ad_stage,
                "adStageLabel": AD_STAGE_LABELS.get(ad_stage, ad_stage),
                "score": segment_score,
                "confidence": confidence,
                "reason": "；".join(reason_parts) + "。",
                "contentDescription": content_description,
                "strengths": strengths,
                "risks": risks,
                "copyAngle": copy_angle,
                "secondMarks": marks[:12],
                "tags": [
                    "智能切片",
                    ROLE_LABELS.get(role_value, role_value),
                    AD_STAGE_LABELS.get(ad_stage, ad_stage),
                    "可混剪",
                ] + (["高分片段"] if segment_score >= 80 else []) + product_signals[:3],
            }
        )
    segments.sort(key=lambda segment: (parse_int(segment.get("score")), parse_float(segment.get("confidence"))), reverse=True)
    return segments[:max_segments]


def guess_role(item: dict[str, Any], tech: dict[str, Any]) -> str:
    text = material_search_text(item)
    scores = {
        "hook": 0,
        "try_on": 0,
        "detail": 0,
        "motion": 0,
        "transition": 0,
        "proof": 0,
        "ending": 0,
    }
    for role, value in role_keyword_scores(text).items():
        scores[role] = scores.get(role, 0) + value
    duration_ms = parse_int(tech.get("durationMs"))
    if duration_ms and duration_ms <= 2500:
        scores["transition"] += 34
        scores["hook"] += 12
    elif duration_ms and duration_ms <= 6000:
        scores["hook"] += 24
        scores["try_on"] += 8
    elif duration_ms and duration_ms >= 45000:
        scores["try_on"] += 12
        scores["motion"] += 8
        scores["proof"] += 5
    if tech.get("orientation") == "portrait":
        scores["try_on"] += 16
        scores["hook"] += 8
    elif tech.get("orientation") == "landscape":
        scores["motion"] += 12
        scores["detail"] += 4
    if material_product_type(item) == "pants":
        scores["try_on"] += 8
        scores["motion"] += 6
        scores["proof"] += 6
        if keyword_hits(text, ["斜扣", "腰头", "口袋", "裤脚", "面料"]):
            scores["detail"] += 18
    best_role, best_score = max(scores.items(), key=lambda pair: pair[1])
    if best_score > 0:
        return best_role
    if duration_ms and duration_ms <= 2500:
        return "transition"
    if duration_ms and duration_ms <= 6000:
        return "hook"
    return "try_on" if tech.get("orientation") == "portrait" else "motion"


def score_video(tech: dict[str, Any], item: dict[str, Any] | None = None) -> int:
    width = parse_int(tech.get("width"))
    height = parse_int(tech.get("height"))
    duration_ms = parse_int(tech.get("durationMs"))
    fps = parse_float(tech.get("fps"))
    bitrate_kbps = parse_int(tech.get("bitrateKbps"))
    if not width or not height:
        return 1
    score = 2.0
    pixels = width * height
    if pixels >= 1080 * 1920 or min(width, height) >= 1080:
        score += 1.3
    elif max(width, height) >= 1080 or min(width, height) >= 720:
        score += 1
    elif max(width, height) < 720:
        score -= 0.8
    if tech.get("orientation") in {"portrait", "square"}:
        score += 0.8
    if 1500 <= duration_ms <= 45000:
        score += 0.8
    elif 45000 < duration_ms <= 90000:
        score += 0.35
    elif duration_ms < 1000:
        score -= 1.0
    if fps and fps < 20:
        score -= 0.9
    elif fps >= 24:
        score += 0.35
    if bitrate_kbps >= 3500:
        score += 0.45
    elif bitrate_kbps and bitrate_kbps < 900:
        score -= 0.45
    if duration_ms > 120000:
        score -= 0.8
    text = material_search_text(item or {})
    if keyword_hits(text, ["模糊", "抖动", "糊", "低清", "废片"]):
        score -= 0.8
    if keyword_hits(text, ["高光", "主力", "爆款", "优先", "可剪辑"]):
        score += 0.35
    return max(1, min(5, int(round(score))))


def build_suggestions(tech: dict[str, Any], role: str, score: int) -> list[str]:
    suggestions: list[str] = []
    orient = tech.get("orientation")
    duration_ms = parse_int(tech.get("durationMs"))
    if orient == "portrait":
        suggestions.append("适合优先进入 9:16 竖版短视频剪辑池。")
    elif orient == "square":
        suggestions.append("适合方形素材池；进入竖版模板前建议检查上下裁切。")
    elif orient == "landscape":
        suggestions.append("横版素材进入竖版自动剪辑前需要裁切或画布适配。")
    if duration_ms and duration_ms <= 3000:
        suggestions.append("时长很短，优先作为转场、节奏点或开头闪切素材。")
    elif duration_ms and duration_ms <= 8000:
        suggestions.append("时长适合做开头钩子或单个卖点段落。")
    elif duration_ms and duration_ms > 60000:
        suggestions.append("时长偏长，建议先做镜头切分后再进入自动剪辑。")
    if not tech.get("hasAudio"):
        suggestions.append("未检测到音轨，可直接搭配 BGM 或口播使用。")
    suggestions.append(f"初步剪辑用途建议：{ROLE_LABELS.get(role, role)}。")
    if score <= 2:
        suggestions.append("质量评分偏低，建议人工复核清晰度、抖动和主体可见度。")
    return suggestions[:8]


def recommended_segment_duration_ms(role: str, tech: dict[str, Any]) -> int:
    duration_ms = parse_int(tech.get("durationMs"))
    defaults = {
        "hook": 2200,
        "try_on": 3400,
        "detail": 2400,
        "motion": 3000,
        "transition": 1400,
        "proof": 2800,
        "ending": 2600,
    }
    target = defaults.get(role, 2600)
    if duration_ms:
        target = min(target, max(1200, duration_ms))
    return target


def build_editing_profile(item: dict[str, Any], tech: dict[str, Any], role: str, score: int, segments: list[dict[str, Any]]) -> dict[str, Any]:
    text = material_search_text(item)
    role_scores = role_keyword_scores(text)
    product_type = material_product_type(item)
    best_segments = sorted(segments, key=lambda segment: parse_int(segment.get("score")), reverse=True)[:8]
    role_counts: dict[str, int] = {}
    for segment in segments:
        segment_role_value = str(segment.get("role") or "unassigned")
        role_counts[segment_role_value] = role_counts.get(segment_role_value, 0) + 1
    readiness_score = 45 + score * 9
    if tech.get("orientation") == "portrait":
        readiness_score += 10
    elif tech.get("orientation") == "square":
        readiness_score += 6
    if best_segments:
        readiness_score += min(18, int(sum(parse_int(segment.get("score")) for segment in best_segments[:4]) / max(1, min(4, len(best_segments)))) // 8)
    if parse_int(tech.get("durationMs")) > 90000:
        readiness_score -= 8
    readiness_score = clamp_score(readiness_score)
    use_level = "primary" if readiness_score >= 82 else "support" if readiness_score >= 64 else "review"
    return {
        "version": 2,
        "productType": product_type,
        "primaryRole": role,
        "roleScores": role_scores,
        "roleCoverage": role_counts,
        "recommendedUse": use_level,
        "recommendedSegmentDurationMs": recommended_segment_duration_ms(role, tech),
        "readinessScore": readiness_score,
        "topSegmentIds": [str(segment.get("id") or "") for segment in best_segments],
        "copyMatchRoles": [role_value for role_value, _ in sorted(role_scores.items(), key=lambda pair: pair[1], reverse=True)[:4]],
    }


def build_ad_profile(item: dict[str, Any], tech: dict[str, Any], role: str, score: int, segments: list[dict[str, Any]], second_marks: list[dict[str, Any]]) -> dict[str, Any]:
    text = material_search_text(item)
    product_type = material_product_type(item)
    product_signals = product_signal_hits(text)
    stage_counts: dict[str, int] = {}
    stage_best_scores: dict[str, int] = {}
    for segment in segments:
        stage = str(segment.get("adStage") or "")
        if not stage:
            continue
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        stage_best_scores[stage] = max(stage_best_scores.get(stage, 0), parse_int(segment.get("score")))
    best_segments = sorted(segments, key=lambda segment: parse_int(segment.get("score")), reverse=True)[:6]
    best_stage = ""
    if stage_best_scores:
        best_stage = max(stage_best_scores.items(), key=lambda pair: (pair[1], stage_counts.get(pair[0], 0)))[0]
    elif role == "hook":
        best_stage = "hook"
    elif role == "detail":
        best_stage = "detail"
    elif role == "proof":
        best_stage = "proof"
    else:
        best_stage = "intro"

    high_seconds = sum(1 for mark in second_marks if parse_int(mark.get("score")) >= 78)
    avg_sharpness = sum(parse_float(mark.get("sharpness")) for mark in second_marks) / len(second_marks) if second_marks else 0.0
    avg_motion = sum(parse_float(mark.get("visualMotion")) for mark in second_marks) / len(second_marks) if second_marks else 0.0
    best_segment_score = parse_int(best_segments[0].get("score")) if best_segments else 0
    ad_score = 38 + score * 8 + min(22, best_segment_score // 4) + min(12, high_seconds)
    if tech.get("orientation") == "portrait":
        ad_score += 8
    if avg_sharpness >= 80:
        ad_score += 5
    if avg_motion >= 12:
        ad_score += 4
    ad_score = clamp_score(ad_score)
    quality_tier = "A" if ad_score >= 86 else "B" if ad_score >= 72 else "C" if ad_score >= 58 else "D"

    strengths: list[str] = []
    risks: list[str] = []
    if best_segment_score >= 86:
        append_unique(strengths, "存在高分广告片段，可优先进主剪")
    if high_seconds:
        append_unique(strengths, f"{high_seconds} 秒高分画面，可做自动混剪候选")
    if avg_sharpness >= 80:
        append_unique(strengths, "整体清晰度适合广告展示")
    if avg_motion >= 12:
        append_unique(strengths, "动作变化较足，剪辑节奏好做")
    if product_signals:
        append_unique(strengths, f"可关联卖点：{'、'.join(product_signals[:4])}")
    if best_segment_score < 68:
        append_unique(risks, "缺少明显高分片段，建议人工挑选")
    if avg_sharpness and avg_sharpness < 36:
        append_unique(risks, "整体清晰度偏软，不适合主讲细节")
    if avg_motion < 5 and best_stage in {"hook", "motion"}:
        append_unique(risks, "动作变化偏少，开头节奏可能不够")

    stage_label = AD_STAGE_LABELS.get(best_stage, best_stage)
    product_label = product_type_label(product_type)
    content_summary = (
        f"这条素材更适合作为{stage_label}素材，主体方向是{product_label}广告画面。"
        f"{' 重点可讲：' + '、'.join(product_signals[:5]) + '。' if product_signals else ''}"
        f"最高分片段 {best_segment_score}/100，广告可用等级 {quality_tier}。"
    )
    return {
        "version": 1,
        "adScore": ad_score,
        "qualityTier": quality_tier,
        "primaryStage": best_stage,
        "primaryStageLabel": stage_label,
        "stageCoverage": stage_counts,
        "stageBestScores": stage_best_scores,
        "productType": product_type,
        "productSignals": product_signals,
        "contentSummary": content_summary,
        "strengths": strengths[:6],
        "risks": risks[:5],
        "bestSegmentIds": [str(segment.get("id") or "") for segment in best_segments],
        "recommendedTags": [stage_label, f"广告等级{quality_tier}", *product_signals[:5]],
    }


def apply_tags(item: dict[str, Any], role: str, status: str, auto_tags: list[str]) -> None:
    tags = [str(tag).strip() for tag in item.get("tags") or [] if str(tag).strip()]
    for tag in ["AI分析", ROLE_LABELS.get(role, role), "可剪辑" if status == "ready" else "待复核", *auto_tags[:8]]:
        if tag and tag not in tags:
            tags.append(tag)
    item["tags"] = tags[:24]


def relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_video_note(note_path: Path, item: dict[str, Any], url: str, tech: dict[str, Any], frames: list[dict[str, Any]], root: Path) -> None:
    note_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: video_material_analysis",
        f"source_url: {json.dumps(url, ensure_ascii=False)}",
        f"status: {item.get('analysisStatus')}",
        f"edit_role: {item.get('editRole')}",
        f"quality_score: {item.get('qualityScore')}",
        f"updated_at: {item.get('analysis', {}).get('updatedAt')}",
        "---",
        "",
        f"# {item.get('name') or '未命名视频素材'}",
        "",
        f"- 状态：{item.get('analysisStatus')}",
        f"- 剪辑用途：{ROLE_LABELS.get(str(item.get('editRole')), item.get('editRole'))}",
        f"- 质量评分：{item.get('qualityScore')}/5",
        f"- 分辨率：{tech.get('width')}x{tech.get('height')} ({tech.get('orientation')})",
        f"- 时长：{round(parse_int(tech.get('durationMs')) / 1000, 2)} 秒",
        f"- FPS：{tech.get('fps')}",
        f"- 音轨：{'有' if tech.get('hasAudio') else '无'}",
        f"- AI 标签：{', '.join(item.get('aiTags') or []) if item.get('aiTags') else '无'}",
        f"- 帧级索引：`{item.get('analysis', {}).get('frameIndex', {}).get('path', '') or '未生成'}`",
        "",
        "## 分析摘要",
        "",
        str(item.get("analysis", {}).get("summary") or ""),
        "",
        "## 剪辑建议",
        "",
    ]
    lines.extend(f"- {suggestion}" for suggestion in item.get("analysis", {}).get("suggestions", []))
    profile = item.get("analysis", {}).get("editingProfile") if isinstance(item.get("analysis"), dict) else {}
    if isinstance(profile, dict) and profile:
        role_coverage = profile.get("roleCoverage") if isinstance(profile.get("roleCoverage"), dict) else {}
        copy_roles = profile.get("copyMatchRoles") if isinstance(profile.get("copyMatchRoles"), list) else []
        lines.extend(
            [
                "",
                "## 剪辑画像",
                "",
                f"- 推荐使用级别：{profile.get('recommendedUse')}",
                f"- 剪辑可用度：{profile.get('readinessScore')}/100",
                f"- 建议片段时长：{round(parse_int(profile.get('recommendedSegmentDurationMs')) / 1000, 2)} 秒",
                f"- 商品类型：{profile.get('productType') or '未判断'}",
                f"- 片段角色覆盖：{', '.join(f'{ROLE_LABELS.get(str(key), key)} {value}' for key, value in role_coverage.items()) or '无'}",
                f"- 文案匹配方向：{', '.join(ROLE_LABELS.get(str(role), str(role)) for role in copy_roles) or '无'}",
            ]
        )
    ad_profile = item.get("analysis", {}).get("adProfile") if isinstance(item.get("analysis"), dict) else {}
    if isinstance(ad_profile, dict) and ad_profile:
        stage_coverage = ad_profile.get("stageCoverage") if isinstance(ad_profile.get("stageCoverage"), dict) else {}
        strengths = ad_profile.get("strengths") if isinstance(ad_profile.get("strengths"), list) else []
        risks = ad_profile.get("risks") if isinstance(ad_profile.get("risks"), list) else []
        product_signals = ad_profile.get("productSignals") if isinstance(ad_profile.get("productSignals"), list) else []
        lines.extend(
            [
                "",
                "## 广告资产画像",
                "",
                f"- 广告阶段：{ad_profile.get('primaryStageLabel') or '待判断'}",
                f"- 广告等级：{ad_profile.get('qualityTier') or 'C'} · {ad_profile.get('adScore') or 0}/100",
                f"- 内容描述：{ad_profile.get('contentSummary') or '暂无'}",
                f"- 可讲卖点：{', '.join(str(value) for value in product_signals[:8]) or '待补充'}",
                f"- 阶段覆盖：{', '.join(f'{AD_STAGE_LABELS.get(str(key), key)} {value}' for key, value in stage_coverage.items()) or '无'}",
            ]
        )
        if strengths:
            lines.extend(["", "### 广告优点", ""])
            lines.extend(f"- {value}" for value in strengths[:8])
        if risks:
            lines.extend(["", "### 使用风险", ""])
            lines.extend(f"- {value}" for value in risks[:6])
    lines.extend(["", "## 抽帧", ""])
    if frames:
        for frame in frames:
            frame_path = frame.get("path")
            rel = frame_path if isinstance(frame_path, str) else relative_posix(frame_path, root)
            timestamp = round(parse_int(frame.get("timeMs")) / 1000, 2)
            lines.append(f"- {timestamp}s ![[{rel}]]")
    else:
        lines.append("- 未生成抽帧。")
    second_marks = item.get("analysis", {}).get("secondMarks") if isinstance(item.get("analysis"), dict) else []
    lines.extend(["", "## 逐秒优缺点", ""])
    if isinstance(second_marks, list) and second_marks:
        valid_marks = [mark for mark in second_marks if isinstance(mark, dict)]
        tone_labels = {"good": "高分可用", "ok": "可用", "warn": "需复核", "bad": "不建议"}
        for mark in valid_marks[:120]:
            second = parse_int(mark.get("second"))
            score = parse_int(mark.get("score"))
            tone = tone_labels.get(str(mark.get("tone") or ""), "可用")
            pros = "、".join(str(value).strip() for value in mark.get("pros") or [] if str(value).strip()) or "暂无明显优点"
            cons = "、".join(str(value).strip() for value in mark.get("cons") or [] if str(value).strip()) or "暂无明显缺点"
            advice = str(mark.get("cutAdvice") or mark.get("note") or "建议结合相邻秒片段预览后使用。")
            lines.append(f"- {second}s · {score}/100 · {tone} · 优点：{pros} · 缺点：{cons} · 剪法：{advice}")
        if len(valid_marks) > 120:
            lines.append(f"- 已省略 {len(valid_marks) - 120} 秒，完整逐秒数据见 `data/material-library.json`。")
    else:
        lines.append("- 暂无逐秒帧分析数据。")
    cut_hints = item.get("analysis", {}).get("cutHints") if isinstance(item.get("analysis"), dict) else []
    lines.extend(["", "## 自动剪辑候选段", ""])
    if cut_hints:
        for hint in cut_hints:
            start = round(parse_int(hint.get("startMs")) / 1000, 2)
            end = round(parse_int(hint.get("endMs")) / 1000, 2)
            lines.append(f"- {start}s - {end}s · {hint.get('role')} · {hint.get('reason')}")
    else:
        lines.append("- 暂无候选段。")
    segments = item.get("analysis", {}).get("segments") if isinstance(item.get("analysis"), dict) else []
    lines.extend(["", "## 智能拆分片段", ""])
    if isinstance(segments, list) and segments:
        for segment in segments[:20]:
            start = round(parse_int(segment.get("startMs")) / 1000, 2)
            end = round(parse_int(segment.get("endMs")) / 1000, 2)
            lines.append(
                f"- {start}s - {end}s · {segment.get('role')} · {segment.get('adStageLabel') or segment.get('adStage') or ''} · 片段分 {segment.get('score')} · {segment.get('contentDescription') or segment.get('reason')}"
            )
    else:
        lines.append("- 暂无智能拆分片段。")
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_item(url: str, item: dict[str, Any], root: Path, args: argparse.Namespace) -> dict[str, Any]:
    source_path = resolve_source_path(item, root)
    if not source_path:
        raise FileNotFoundError("local source video not found")
    tech = probe_video(source_path, args.ffprobe)
    role = guess_role(item, tech)
    score = score_video(tech, item)
    item_text = material_search_text(item)
    product_type = material_product_type(item)
    status = "ready" if score >= 4 and parse_int(tech.get("durationMs")) >= 1000 else "analyzed" if score >= 2 else "hold"
    priority = "high" if score >= 4 else "normal" if score >= 3 else "low"
    vid = item_id(url, item)
    frame_dir = root / "analysis" / "frames" / vid
    frames = extract_frames(source_path, frame_dir, args.ffmpeg, parse_int(tech.get("durationMs")), args.frame_count, args.dry_run)
    frame_index_data = {"mode": "disabled", "totalFrames": 0, "indexedFrames": 0, "complete": False, "maxRecords": 0, "frames": []}
    frame_index_path = root / "analysis" / "frame-index" / f"{vid}.json"
    if not args.no_frame_index:
        frame_index_data = probe_frame_index(source_path, args.ffprobe, args.max_frame_records)
        frame_index_path = write_frame_index(root, vid, url, item, tech, frame_index_data, args.dry_run)
    visual_metrics = [] if args.no_visual_metrics else sample_second_visual_metrics(source_path, parse_int(tech.get("durationMs")), args.max_visual_seconds)
    second_marks = second_marks_from_frames(frame_index_data, parse_int(tech.get("durationMs")), tech, role, visual_metrics)
    keyframes = [
        {"timeMs": parse_int(frame.get("timeMs")), "path": "" if args.dry_run else relative_posix(frame["path"], root), "note": frame.get("note", "sampled keyframe")}
        for frame in frames
    ]
    frame_index_summary = {
        "path": "" if args.dry_run or args.no_frame_index else relative_posix(frame_index_path, root),
        "mode": frame_index_data.get("mode"),
        "totalFrames": parse_int(frame_index_data.get("totalFrames")),
        "indexedFrames": parse_int(frame_index_data.get("indexedFrames")),
        "complete": bool(frame_index_data.get("complete")),
        "maxRecords": parse_int(frame_index_data.get("maxRecords")),
    }
    segments = build_smart_segments(
        tech,
        role,
        score,
        frame_index_data,
        args.segment_seconds,
        args.segment_stride_seconds,
        args.max_segments,
        item_text,
        product_type,
        second_marks,
    )
    top_segment_score = max([parse_int(segment.get("score")) for segment in segments] or [0])
    if score >= 3 and top_segment_score >= 82 and parse_int(tech.get("durationMs")) >= 1000:
        status = "ready"
        priority = "high"
    editing_profile = build_editing_profile(item, tech, role, score, segments)
    ad_profile = build_ad_profile(item, tech, role, score, segments, second_marks)
    auto_tags = build_auto_tags(item, tech, role, status, score, frame_index_data)
    for tag in ad_profile.get("recommendedTags") or []:
        clean_tag = str(tag).strip()
        if clean_tag and clean_tag not in auto_tags:
            auto_tags.append(clean_tag)
    cut_hints = build_cut_hints(tech, role, score)
    if segments:
        segment_hints = [
            {
                "startMs": parse_int(segment.get("startMs")),
                "endMs": parse_int(segment.get("endMs")),
                "role": str(segment.get("role") or role),
                "confidence": parse_float(segment.get("confidence")),
                "reason": str(segment.get("reason") or "智能拆分片段。"),
            }
            for segment in sorted(segments, key=lambda value: parse_int(value.get("score")), reverse=True)[:4]
        ]
        cut_hints = segment_hints + cut_hints
    suggestions = build_suggestions(tech, role, score)
    if editing_profile.get("recommendedUse") == "primary":
        suggestions.append("建议作为主剪辑候选素材，可优先进入产品成片自动混剪。")
    elif editing_profile.get("recommendedUse") == "support":
        suggestions.append("建议作为辅助镜头使用，优先匹配文案中的相近卖点或过渡段。")
    else:
        suggestions.append("建议先人工复核主体清晰度和可用片段，再进入自动混剪。")
    if editing_profile.get("copyMatchRoles"):
        labels = [ROLE_LABELS.get(str(role_value), str(role_value)) for role_value in editing_profile["copyMatchRoles"][:3]]
        suggestions.append(f"文案匹配优先方向：{'、'.join(labels)}。")
    if ad_profile.get("contentSummary"):
        suggestions.append(str(ad_profile["contentSummary"]))
    suggestions = suggestions[:10]
    summary = (
        f"检测到 {tech.get('orientation')} 视频，分辨率 {tech.get('width')}x{tech.get('height')}，"
        f"时长约 {round(parse_int(tech.get('durationMs')) / 1000, 2)} 秒。"
        f"初步适合作为{ROLE_LABELS.get(role, role)}素材，质量评分 {score}/5。"
        f"剪辑可用度 {editing_profile.get('readinessScore', 0)}/100，推荐用途 {editing_profile.get('recommendedUse', 'review')}。"
        f"广告资产定位：{ad_profile.get('primaryStageLabel', '待判断')}，广告等级 {ad_profile.get('qualityTier', 'C')}，广告分 {ad_profile.get('adScore', 0)}/100。"
        f"已建立 {frame_index_summary['indexedFrames']}/{frame_index_summary['totalFrames']} 帧元数据索引。"
    )
    item["technical"] = tech
    item["analysisStatus"] = status
    item["editRole"] = role
    item["priority"] = priority
    item["qualityScore"] = score
    item["aiTags"] = auto_tags
    item["analysis"] = {
        "status": status,
        "frameCount": len(keyframes),
        "keyframes": keyframes,
        "summary": summary,
        "suggestions": suggestions,
        "autoTags": auto_tags,
        "frameIndex": frame_index_summary,
        "editingProfile": editing_profile,
        "adProfile": ad_profile,
        "secondMarks": second_marks,
        "cutHints": cut_hints,
        "segments": segments,
        "updatedAt": utc_now(),
    }
    apply_tags(item, role, status, auto_tags)
    note_path = root / "analysis" / "videos" / f"{vid}.md"
    if not args.dry_run:
        write_video_note(note_path, item, url, tech, frames, root)
    return {
        "url": url,
        "name": item.get("name"),
        "status": status,
        "role": role,
        "score": score,
        "frames": len(keyframes),
        "indexedFrames": frame_index_summary["indexedFrames"],
        "segments": len(segments),
        "aiTags": auto_tags,
        "note": str(note_path),
    }


def should_analyze(item: dict[str, Any], force: bool) -> bool:
    if str(item.get("kind") or "").strip() != "video":
        return False
    if force:
        return True
    return str(item.get("analysisStatus") or "queued") in {"queued", "hold", "analyzing"}


def write_run_summary(root: Path, added: list[dict[str, Any]], analyzed: list[dict[str, Any]], failures: list[dict[str, Any]], dry_run: bool) -> Path:
    summary_dir = root / "analysis"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "素材分析运行记录.md"
    lines = [
        "---",
        "type: material_analysis_run",
        f"updated_at: {utc_now()}",
        f"dry_run: {str(dry_run).lower()}",
        "---",
        "",
        "# 素材分析运行记录",
        "",
        f"- 新补登记素材：{len(added)}",
        f"- 已分析视频：{len(analyzed)}",
        f"- 失败/待复核：{len(failures)}",
        "",
        "## 新补登记素材",
        "",
    ]
    lines.extend(f"- {entry['kind']} · {entry['name']} · `{entry['path']}`" for entry in added[:200])
    if not added:
        lines.append("- 无")
    lines.extend(["", "## 已分析视频", ""])
    lines.extend(f"- {entry.get('name')} · {entry.get('status')} · {entry.get('role')} · 评分 {entry.get('score')} · 抽帧 {entry.get('frames')}" for entry in analyzed)
    if not analyzed:
        lines.append("- 无")
    lines.extend(["", "## 失败/待复核", ""])
    lines.extend(f"- {entry.get('name') or entry.get('url')} · {entry.get('error')}" for entry in failures)
    if not failures:
        lines.append("- 无")
    if not dry_run:
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def material_sort_key(entry: dict[str, Any]) -> tuple[int, int, int]:
    priority = PRIORITY_RANK.get(str(entry.get("priority") or "normal"), 0)
    score = parse_int(entry.get("qualityScore"))
    duration = parse_int((entry.get("technical") or {}).get("durationMs")) if isinstance(entry.get("technical"), dict) else 0
    return (priority, score, -duration)


def build_auto_edit_pool(library: dict[str, Any], root: Path) -> dict[str, Any]:
    ensure_library_shape(library)
    clips: list[dict[str, Any]] = []
    for url, item in (library.get("items") or {}).items():
        if not isinstance(item, dict) or str(item.get("kind")) != "video":
            continue
        if str(item.get("analysisStatus") or "") not in {"ready", "analyzed"}:
            continue
        analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else {}
        tech = item.get("technical") if isinstance(item.get("technical"), dict) else {}
        source_path = resolve_source_path(item, root)
        clips.append(
            {
                "url": url,
                "name": item.get("name") or Path(urlparse(url).path).name,
                "status": item.get("analysisStatus"),
                "editRole": item.get("editRole"),
                "priority": item.get("priority"),
                "qualityScore": parse_int(item.get("qualityScore")),
                "tags": [str(tag) for tag in item.get("tags") or []],
                "aiTags": [str(tag) for tag in item.get("aiTags") or analysis.get("autoTags") or []],
                "technical": tech,
                "summary": analysis.get("summary") or "",
                "suggestions": analysis.get("suggestions") if isinstance(analysis.get("suggestions"), list) else [],
                "keyframes": analysis.get("keyframes") if isinstance(analysis.get("keyframes"), list) else [],
                "frameIndex": analysis.get("frameIndex") if isinstance(analysis.get("frameIndex"), dict) else {},
                "editingProfile": analysis.get("editingProfile") if isinstance(analysis.get("editingProfile"), dict) else {},
                "adProfile": analysis.get("adProfile") if isinstance(analysis.get("adProfile"), dict) else {},
                "secondMarks": analysis.get("secondMarks") if isinstance(analysis.get("secondMarks"), list) else [],
                "cutHints": analysis.get("cutHints") if isinstance(analysis.get("cutHints"), list) else [],
                "segments": analysis.get("segments") if isinstance(analysis.get("segments"), list) else [],
                "obsidianPath": item.get("obsidianPath") or "",
                "sourcePath": str(source_path) if source_path else "",
                "updatedAt": analysis.get("updatedAt") or library.get("updatedAt") or "",
            }
        )
    clips.sort(key=material_sort_key, reverse=True)
    return {
        "version": 1,
        "type": "seedance_auto_edit_material_pool",
        "updatedAt": utc_now(),
        "libraryRoot": str(root),
        "materialCount": len(library.get("items") or {}),
        "clipCount": len(clips),
        "clips": clips,
    }


def write_auto_edit_pool(root: Path, library: dict[str, Any], dry_run: bool) -> Path:
    target = root / "data" / AUTO_EDIT_POOL_NAME
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(build_auto_edit_pool(library, root), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def selected_batch_ids(library: dict[str, Any], selector: str) -> set[str]:
    clean_selector = str(selector or "").strip()
    if not clean_selector:
        return set()
    if clean_selector.lower() in {"active", "current", "当前"}:
        return {str(library.get("activeId") or "").strip()}
    matched: set[str] = set()
    selector_fold = clean_selector.casefold()
    for batch in library.get("batches") or []:
        if not isinstance(batch, dict):
            continue
        batch_id = str(batch.get("id") or "").strip()
        name = str(batch.get("name") or "").strip()
        if batch_id.casefold() == selector_fold or name.casefold() == selector_fold:
            matched.add(batch_id)
    if not matched:
        raise ValueError(f"Batch not found: {clean_selector}")
    return matched


def main() -> int:
    args = parse_args()
    root = Path(args.vault_root).expanduser().resolve()
    library_path = Path(args.library).expanduser().resolve() if args.library else root / "data" / "material-library.json"
    library = read_json(library_path)
    ensure_library_shape(library)

    added: list[dict[str, Any]] = []
    if not args.no_sync:
        added = sync_uploads(library, root, args.local_base_url)

    items: dict[str, Any] = library["items"]
    batch_ids = selected_batch_ids(library, args.batch)
    targets = [
        (str(url), item)
        for url, item in items.items()
        if isinstance(item, dict)
        and (not batch_ids or str(item.get("batchId") or "") in batch_ids)
        and should_analyze(item, args.force)
    ]
    if args.limit > 0:
        targets = targets[: args.limit]

    analyzed: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    if not args.sync_only:
        for url, item in targets:
            try:
                analyzed.append(analyze_item(url, item, root, args))
            except Exception as exc:
                failures.append({"url": url, "name": item.get("name"), "error": str(exc)})
                item["analysisStatus"] = "hold"
                item.setdefault("analysis", default_analysis("hold"))
                item["analysis"].update({"status": "hold", "summary": f"视频分析失败：{exc}", "updatedAt": utc_now()})

    library["updatedAt"] = utc_now()
    summary_path = write_run_summary(root, added, analyzed, failures, args.dry_run)
    auto_edit_pool_path = write_auto_edit_pool(root, library, args.dry_run)
    if not args.dry_run:
        write_json(library_path, library)

    print(
        json.dumps(
            {
                "dryRun": args.dry_run,
                "synced": added,
                "analyzed": analyzed,
                "failures": failures,
                "summary": str(summary_path),
                "autoEditPool": str(auto_edit_pool_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failures and not analyzed and not added else 0


if __name__ == "__main__":
    raise SystemExit(main())
