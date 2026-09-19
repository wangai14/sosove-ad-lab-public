from __future__ import annotations

import json
import re
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STORE_VERSION = 1
STORE_LOCK = threading.RLock()
PROJECT_NAME_LIMIT = 120
TEXT_LIMIT = 6000
SHOT_COUNT_MIN = 2
SHOT_COUNT_MAX = 6
IMAGE_SIZES = {"1024x1536", "1536x1024", "1024x1024"}
IMAGE_SIZE_OPTIONS = {"auto", *IMAGE_SIZES}
MAX_REFERENCE_IMAGES = 9
MAX_REFERENCE_VIDEOS = 3
MAX_REFERENCE_VIDEO_DURATION_MS = 15_000
REFERENCE_MODES = {"multimodal", "prompt-only"}
REFERENCE_PRIVACY_MODES = {"product-only", "direct"}
IMAGE_GENERATION_MODES = {"auto", "reference", "prompt"}

DEFAULT_SETTINGS: dict[str, Any] = {
    "ratio": "9:16",
    "imageSize": "auto",
    "shotCount": 4,
    "totalDuration": 20,
    "market": "日本",
    "language": "日语",
    "platform": "TikTok",
    "style": "editorial-natural",
    "character": "local-creator",
    "lighting": "soft-daylight",
    "model": "doubao-seedance-2-0-260128",
    "generateAudio": True,
    "bgm": True,
    "onScreenText": True,
}

ROLE_SEQUENCE = ["hook", "problem", "reveal", "detail", "proof", "cta"]
ROLE_LABELS = {
    "hook": "开头钩子",
    "problem": "痛点证据",
    "reveal": "产品揭晓",
    "detail": "结构细节",
    "proof": "上身证明",
    "cta": "行动召回",
}


class ProjectNotFound(ValueError):
    """Raised for missing projects and ownership violations."""


class InvalidProject(ValueError):
    """Raised when a project mutation is invalid."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: Any, limit: int = TEXT_LIMIT) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", "", str(value or "")).strip()[:limit]


def clean_string_list(value: Any, limit: int = 12, item_limit: int = 180) -> list[str]:
    raw = value if isinstance(value, list) else []
    result: list[str] = []
    for item in raw:
        text = clean_text(item, item_limit)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def clean_url(value: Any) -> str:
    text = clean_text(value, 1600)
    if not text:
        return ""
    if text.startswith(("http://", "https://", "/uploads/", "/external-materials/", "/ad-forge-exports/")):
        return text
    return ""


def normalize_reference_video(value: Any) -> dict[str, Any] | None:
    source = value if isinstance(value, dict) else {"url": value}
    url = clean_url(source.get("url") or source.get("videoUrl"))
    if not url:
        return None
    try:
        duration_ms = int(source.get("durationMs") or source.get("duration") or 0)
    except (TypeError, ValueError):
        duration_ms = 0
    return {
        "url": url,
        "name": clean_text(source.get("name"), 240) or "参考视频",
        "durationMs": min(MAX_REFERENCE_VIDEO_DURATION_MS, max(0, duration_ms)),
        "contentType": clean_text(source.get("contentType"), 100),
    }


def normalize_reference_videos(value: Any) -> list[dict[str, Any]]:
    raw = value if isinstance(value, list) else []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_duration_ms = 0
    for item in raw:
        video = normalize_reference_video(item)
        if not video or video["url"] in seen:
            continue
        duration_ms = int(video.get("durationMs") or 0)
        if duration_ms and total_duration_ms + duration_ms > MAX_REFERENCE_VIDEO_DURATION_MS:
            continue
        result.append(video)
        seen.add(video["url"])
        total_duration_ms += duration_ms
        if len(result) >= MAX_REFERENCE_VIDEOS:
            break
    return result


def validate_reference_videos(value: Any) -> list[dict[str, Any]]:
    raw = value if isinstance(value, list) else []
    normalized = [video for video in (normalize_reference_video(item) for item in raw) if video]
    unique = {video["url"]: video for video in normalized}
    if len(unique) > MAX_REFERENCE_VIDEOS:
        raise InvalidProject(f"每个镜头最多使用 {MAX_REFERENCE_VIDEOS} 个参考视频。")
    videos = list(unique.values())
    total_duration_ms = sum(int(video.get("durationMs") or 0) for video in videos)
    if total_duration_ms > MAX_REFERENCE_VIDEO_DURATION_MS:
        raise InvalidProject("每个镜头的参考视频总时长最多 15 秒。")
    return videos


def bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(maximum, max(minimum, number))


def allocate_durations(total_duration: int, shot_count: int) -> list[int]:
    count = bounded_int(shot_count, 4, SHOT_COUNT_MIN, SHOT_COUNT_MAX)
    total = bounded_int(total_duration, count * 5, count * 5, count * 15)
    base, remainder = divmod(total, count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def normalize_settings(value: Any, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    source = {**DEFAULT_SETTINGS, **(fallback or {})}
    if isinstance(value, dict):
        source.update(value)
    shot_count = bounded_int(source.get("shotCount"), 4, SHOT_COUNT_MIN, SHOT_COUNT_MAX)
    total_duration = bounded_int(source.get("totalDuration"), shot_count * 5, shot_count * 5, shot_count * 15)
    ratio = clean_text(source.get("ratio"), 10)
    if ratio not in {"9:16", "16:9", "1:1"}:
        ratio = "9:16"
    image_size = clean_text(source.get("imageSize"), 20)
    if image_size not in IMAGE_SIZE_OPTIONS:
        image_size = "auto"
    platform = clean_text(source.get("platform"), 30)
    if platform not in {"TikTok", "Facebook", "Instagram", "Google", "Other"}:
        platform = "TikTok"
    return {
        "ratio": ratio,
        "imageSize": image_size,
        "shotCount": shot_count,
        "totalDuration": total_duration,
        "market": clean_text(source.get("market"), 80) or "日本",
        "language": clean_text(source.get("language"), 80) or "日语",
        "platform": platform,
        "style": clean_text(source.get("style"), 80) or DEFAULT_SETTINGS["style"],
        "character": clean_text(source.get("character"), 80) or DEFAULT_SETTINGS["character"],
        "lighting": clean_text(source.get("lighting"), 80) or DEFAULT_SETTINGS["lighting"],
        "model": clean_text(source.get("model"), 160) or DEFAULT_SETTINGS["model"],
        "generateAudio": bool(source.get("generateAudio", True)),
        "bgm": bool(source.get("bgm", True)),
        "onScreenText": bool(source.get("onScreenText", True)),
    }


def normalize_brief(value: Any, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    source = {**(fallback or {})}
    if isinstance(value, dict):
        source.update(value)
    return {
        "summary": clean_text(source.get("summary"), TEXT_LIMIT),
        "audience": clean_text(source.get("audience"), 800),
        "sellingPoints": clean_string_list(source.get("sellingPoints"), limit=10),
    }


def default_role(index: int, count: int) -> str:
    if index == 0:
        return "hook"
    if index == count - 1:
        return "cta"
    middle = ["problem", "reveal", "detail", "proof"]
    return middle[min(index - 1, len(middle) - 1)]


def empty_shot(index: int, count: int, duration: int) -> dict[str, Any]:
    role = default_role(index, count)
    return {
        "id": f"shot-{uuid.uuid4().hex[:12]}",
        "order": index + 1,
        "role": role,
        "title": ROLE_LABELS[role],
        "scene": "",
        "camera": "",
        "imagePrompt": "",
        "prompt": "",
        "copy": "",
        "duration": duration,
        "referenceImage": "",
        "referenceAssets": [],
        "referenceVideos": [],
        "generationMode": "multimodal",
        "referencePrivacyMode": "product-only",
        "imageGenerationMode": "auto",
        "referenceImageSource": "",
        "imageModel": "",
        "imageSize": "",
        "imageGeneratedAt": "",
        "imageGenerationRoute": "",
        "imageReferenceCount": 0,
        "imageReferenceAssets": [],
        "imageError": "",
        "taskId": "",
        "status": "draft",
        "videoUrl": "",
        "error": "",
        "excluded": False,
    }


def normalize_shot(value: Any, index: int, count: int, default_duration: int) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    shot = empty_shot(index, count, default_duration)
    role = clean_text(source.get("role"), 30)
    if role in ROLE_LABELS:
        shot["role"] = role
    shot["id"] = clean_text(source.get("id"), 80) or shot["id"]
    shot["order"] = index + 1
    shot["title"] = clean_text(source.get("title"), 120) or ROLE_LABELS[shot["role"]]
    shot["scene"] = clean_text(source.get("scene"), 1200)
    shot["camera"] = clean_text(source.get("camera"), 800)
    shot["imagePrompt"] = clean_text(source.get("imagePrompt") or source.get("stillPrompt"), TEXT_LIMIT)
    shot["prompt"] = clean_text(source.get("prompt") or source.get("videoPrompt"), TEXT_LIMIT)
    shot["copy"] = clean_text(source.get("copy") or source.get("subtitle"), 1000)
    shot["duration"] = bounded_int(source.get("duration"), default_duration, 5, 15)
    shot["referenceImage"] = clean_url(source.get("referenceImage") or source.get("imageUrl"))
    shot["referenceAssets"] = [clean_url(item) for item in source.get("referenceAssets", []) if clean_url(item)][:MAX_REFERENCE_IMAGES]
    shot["referenceVideos"] = normalize_reference_videos(source.get("referenceVideos"))
    generation_mode = clean_text(source.get("generationMode"), 30)
    shot["generationMode"] = generation_mode if generation_mode in REFERENCE_MODES else "multimodal"
    privacy_mode = clean_text(source.get("referencePrivacyMode"), 30)
    shot["referencePrivacyMode"] = privacy_mode if privacy_mode in REFERENCE_PRIVACY_MODES else "product-only"
    image_generation_mode = clean_text(source.get("imageGenerationMode"), 30)
    shot["imageGenerationMode"] = image_generation_mode if image_generation_mode in IMAGE_GENERATION_MODES else "auto"
    image_source = clean_text(source.get("referenceImageSource"), 20)
    shot["referenceImageSource"] = image_source if image_source in {"generated", "uploaded"} else ""
    shot["imageModel"] = clean_text(source.get("imageModel"), 160)
    image_size = clean_text(source.get("imageSize"), 20)
    shot["imageSize"] = image_size if image_size in IMAGE_SIZES else ""
    shot["imageGeneratedAt"] = clean_text(source.get("imageGeneratedAt"), 80)
    image_generation_route = clean_text(source.get("imageGenerationRoute"), 30)
    shot["imageGenerationRoute"] = image_generation_route if image_generation_route in {"generations", "edits"} else ""
    shot["imageReferenceAssets"] = [
        clean_url(item) for item in source.get("imageReferenceAssets", []) if clean_url(item)
    ][:4]
    shot["imageReferenceCount"] = (
        len(shot["imageReferenceAssets"])
        if shot["imageReferenceAssets"]
        else bounded_int(source.get("imageReferenceCount"), 0, 0, 4)
    )
    shot["imageError"] = clean_text(source.get("imageError"), 1200)
    shot["taskId"] = clean_text(source.get("taskId"), 240)
    status = clean_text(source.get("status"), 40)
    shot["status"] = status if status in {"draft", "ready", "queued", "generating", "completed", "failed"} else "draft"
    shot["videoUrl"] = clean_url(source.get("videoUrl"))
    shot["error"] = clean_text(source.get("error"), 1200)
    shot["excluded"] = bool(source.get("excluded", False))
    if shot["videoUrl"]:
        shot["status"] = "completed"
    return shot


def progress_for(project: dict[str, Any]) -> dict[str, Any]:
    shots = project.get("shots") if isinstance(project.get("shots"), list) else []
    images_ready = sum(1 for shot in shots if shot.get("referenceImage"))
    videos_ready = sum(1 for shot in shots if shot.get("videoUrl"))
    failed = sum(1 for shot in shots if shot.get("status") == "failed")
    generating = sum(1 for shot in shots if shot.get("status") in {"queued", "generating"})
    prompts_ready = sum(1 for shot in shots if shot.get("prompt"))
    final_ready = bool(project.get("finalVideoUrl"))
    total_units = max(1, len(shots) * 2 + 1)
    completed_units = prompts_ready + videos_ready + (1 if final_ready else 0)
    return {
        "shotsTotal": len(shots),
        "imagesReady": images_ready,
        "promptsReady": prompts_ready,
        "videosReady": videos_ready,
        "failed": failed,
        "generating": generating,
        "finalReady": final_ready,
        "percent": min(100, round(completed_units / total_units * 100)),
    }


def normalize_project(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    owner = clean_text(value.get("owner"), 80).lower()
    project_id = clean_text(value.get("id"), 80)
    if not owner or not project_id:
        return None
    settings = normalize_settings(value.get("settings"))
    durations = allocate_durations(settings["totalDuration"], settings["shotCount"])
    raw_shots = value.get("shots") if isinstance(value.get("shots"), list) else []
    shots = [
        normalize_shot(raw_shots[index] if index < len(raw_shots) else {}, index, settings["shotCount"], durations[index])
        for index in range(settings["shotCount"])
    ]
    created_at = clean_text(value.get("createdAt"), 80) or utc_now_iso()
    project = {
        "id": project_id,
        "owner": owner,
        "name": clean_text(value.get("name"), PROJECT_NAME_LIMIT) or "未命名广告项目",
        "productName": clean_text(value.get("productName"), 240),
        "productDescription": clean_text(value.get("productDescription"), TEXT_LIMIT),
        "brief": normalize_brief(value.get("brief")),
        "settings": settings,
        "referenceAssets": [clean_url(item) for item in value.get("referenceAssets", []) if clean_url(item)][:12],
        "shots": shots,
        "currentStep": bounded_int(value.get("currentStep"), 1, 1, 5),
        "storyboardSource": clean_text(value.get("storyboardSource"), 40) or "draft",
        "promptSkill": clean_text(value.get("promptSkill"), 120),
        "promptSkillVersion": clean_text(value.get("promptSkillVersion"), 40),
        "promptGeneratedAt": clean_text(value.get("promptGeneratedAt"), 80),
        "warning": clean_text(value.get("warning"), 1200),
        "finalVideoUrl": clean_url(value.get("finalVideoUrl")),
        "archived": bool(value.get("archived", False)),
        "createdAt": created_at,
        "updatedAt": clean_text(value.get("updatedAt"), 80) or created_at,
    }
    project["progress"] = progress_for(project)
    return project


def new_project_payload(owner: str, payload: Any = None) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    settings_source = dict(source.get("settings") or {}) if isinstance(source.get("settings"), dict) else {}
    for key in DEFAULT_SETTINGS:
        if key in source:
            settings_source[key] = source[key]
    now = utc_now_iso()
    project_id = f"ad-{uuid.uuid4().hex[:16]}"
    candidate = {
        "id": project_id,
        "owner": clean_text(owner, 80).lower(),
        "name": source.get("name") or source.get("productName") or "未命名广告项目",
        "productName": source.get("productName"),
        "productDescription": source.get("productDescription"),
        "brief": source.get("brief"),
        "settings": settings_source,
        "referenceAssets": source.get("referenceAssets") or [],
        "shots": source.get("shots") or [],
        "currentStep": 1,
        "createdAt": now,
        "updatedAt": now,
    }
    project = normalize_project(candidate)
    if not project:
        raise InvalidProject("项目所有者不能为空。")
    return project


def read_store(path: Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"version": STORE_VERSION, "projects": []}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": STORE_VERSION, "projects": []}
    projects = [item for item in (normalize_project(raw) for raw in data.get("projects", [])) if item]
    return {"version": STORE_VERSION, "projects": projects}


def write_store(path: Path, store: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": STORE_VERSION, "projects": store.get("projects", [])}
    temp_path = target.with_suffix(target.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(target)


def list_projects(path: Path, username: str, is_admin: bool = False, include_archived: bool = False) -> list[dict[str, Any]]:
    clean_username = clean_text(username, 80).lower()
    with STORE_LOCK:
        projects = read_store(path)["projects"]
    visible = [
        deepcopy(project)
        for project in projects
        if (is_admin or project["owner"] == clean_username) and (include_archived or not project["archived"])
    ]
    return sorted(visible, key=lambda item: item.get("updatedAt", ""), reverse=True)


def get_project(path: Path, project_id: str, username: str, is_admin: bool = False) -> dict[str, Any]:
    clean_id = clean_text(project_id, 80)
    clean_username = clean_text(username, 80).lower()
    with STORE_LOCK:
        for project in read_store(path)["projects"]:
            if project["id"] == clean_id and (is_admin or project["owner"] == clean_username):
                return deepcopy(project)
    raise ProjectNotFound("项目不存在。")


def create_project(path: Path, owner: str, payload: Any = None) -> dict[str, Any]:
    project = new_project_payload(owner, payload)
    with STORE_LOCK:
        store = read_store(path)
        store["projects"].append(project)
        write_store(path, store)
    return deepcopy(project)


def _find_project_index(store: dict[str, Any], project_id: str, username: str, is_admin: bool = False) -> int:
    clean_id = clean_text(project_id, 80)
    clean_username = clean_text(username, 80).lower()
    for index, project in enumerate(store.get("projects", [])):
        if project["id"] == clean_id and (is_admin or project["owner"] == clean_username):
            return index
    raise ProjectNotFound("项目不存在。")


def update_project(
    path: Path,
    project_id: str,
    username: str,
    payload: Any,
    is_admin: bool = False,
) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    with STORE_LOCK:
        store = read_store(path)
        index = _find_project_index(store, project_id, username, is_admin)
        current = store["projects"][index]
        candidate = deepcopy(current)
        if "name" in source:
            candidate["name"] = clean_text(source.get("name"), PROJECT_NAME_LIMIT) or current["name"]
        if "productName" in source:
            candidate["productName"] = clean_text(source.get("productName"), 240)
        if "productDescription" in source:
            candidate["productDescription"] = clean_text(source.get("productDescription"), TEXT_LIMIT)
        if "brief" in source:
            candidate["brief"] = normalize_brief(source.get("brief"), current.get("brief"))
        if "settings" in source:
            candidate["settings"] = normalize_settings(source.get("settings"), current.get("settings"))
        if "referenceAssets" in source:
            candidate["referenceAssets"] = [clean_url(item) for item in source.get("referenceAssets", []) if clean_url(item)][:12]
        if "currentStep" in source:
            candidate["currentStep"] = bounded_int(source.get("currentStep"), current.get("currentStep", 1), 1, 5)
        if "finalVideoUrl" in source:
            candidate["finalVideoUrl"] = clean_url(source.get("finalVideoUrl"))
        if "warning" in source:
            candidate["warning"] = clean_text(source.get("warning"), 1200)
        if "storyboardSource" in source:
            candidate["storyboardSource"] = clean_text(source.get("storyboardSource"), 40) or "draft"
        if "promptSkill" in source:
            candidate["promptSkill"] = clean_text(source.get("promptSkill"), 120)
        if "promptSkillVersion" in source:
            candidate["promptSkillVersion"] = clean_text(source.get("promptSkillVersion"), 40)
        if "promptGeneratedAt" in source:
            candidate["promptGeneratedAt"] = clean_text(source.get("promptGeneratedAt"), 80)
        if "shots" in source and isinstance(source.get("shots"), list):
            candidate["shots"] = source["shots"]
            candidate["settings"]["shotCount"] = bounded_int(len(source["shots"]), 4, SHOT_COUNT_MIN, SHOT_COUNT_MAX)
        candidate["updatedAt"] = utc_now_iso()
        normalized = normalize_project(candidate)
        if not normalized:
            raise InvalidProject("项目数据无效。")
        store["projects"][index] = normalized
        write_store(path, store)
        return deepcopy(normalized)


def archive_project(path: Path, project_id: str, username: str, archived: bool = True, is_admin: bool = False) -> dict[str, Any]:
    with STORE_LOCK:
        store = read_store(path)
        index = _find_project_index(store, project_id, username, is_admin)
        store["projects"][index]["archived"] = bool(archived)
        store["projects"][index]["updatedAt"] = utc_now_iso()
        store["projects"][index] = normalize_project(store["projects"][index])
        write_store(path, store)
        return deepcopy(store["projects"][index])


def fallback_roles(count: int) -> list[str]:
    if count <= 2:
        return ["hook", "cta"]
    if count == 3:
        return ["hook", "detail", "cta"]
    if count == 4:
        return ["hook", "detail", "proof", "cta"]
    if count == 5:
        return ["hook", "problem", "detail", "proof", "cta"]
    return ROLE_SEQUENCE[:count]


def build_fallback_storyboard(project: dict[str, Any]) -> list[dict[str, Any]]:
    settings = normalize_settings(project.get("settings"))
    brief = normalize_brief(project.get("brief"))
    product = clean_text(project.get("productName"), 240) or "当前商品"
    points = brief["sellingPoints"] or ["版型", "细节", "日常搭配"]
    point_text = "、".join(points)
    summary = brief["summary"] or "真实自然的短视频广告"
    durations = allocate_durations(settings["totalDuration"], settings["shotCount"])
    roles = fallback_roles(settings["shotCount"])
    templates = {
        "hook": ("第一眼结果", "干净背景中的上身结果或商品英雄位", "快速推近后稳定停住", f"第一秒展示{product}的整体效果，直接点出{points[0]}，画面真实自然，适合{settings['platform']}竖屏广告。"),
        "problem": ("使用前痛点", "与商品卖点直接相关的真实生活场景", "手持近景与动作匹配切", f"用一个可见动作表现消费者在意的问题，再自然引出{product}，不夸张身体变化。"),
        "reveal": ("产品揭晓", "人物拿起或穿上商品的完整展示", "动作转场后缓慢推进", f"完整展示{product}，保持颜色、轮廓和结构清晰，强调{point_text}。"),
        "detail": ("细节证据", "商品结构与材质的近景校样", "微距横移与轻微环绕", f"以手部动作指向{points[min(1, len(points) - 1)]}，随后回到完整商品，细节与利益点严格对应。"),
        "proof": ("真实验证", "日常走动、转身或使用场景", "侧面跟拍与正侧背切换", f"通过自然动作证明{points[min(2, len(points) - 1)]}，保持同一人物、服装与场景连续。"),
        "cta": ("商品定格", "留有文案安全区的最终英雄画面", "低速推近并停留", f"让{product}清晰停留，使用{settings['language']}给出单一行动指令，结束时不再增加新卖点。"),
    }
    shots: list[dict[str, Any]] = []
    for index, role in enumerate(roles):
        title, scene, camera, prompt = templates[role]
        shot = empty_shot(index, len(roles), durations[index])
        shot.update(
            {
                "role": role,
                "title": title,
                "scene": scene,
                "camera": camera,
                "imagePrompt": (
                    f"单张广告分镜关键帧，{settings['ratio']}构图。{scene}。"
                    f"清楚呈现{product}以及{points[min(index, len(points) - 1)]}的视觉证据，"
                    "真实材质与自然人体，画面干净，不生成字幕、价格、拼贴或水印。"
                ),
                "prompt": f"{durations[index]}秒，{settings['ratio']}。{prompt} 项目方向：{summary}",
                "copy": points[min(index, len(points) - 1)] if role != "cta" else "今すぐチェック",
                "status": "ready",
            }
        )
        shots.append(shot)
    return shots


def extract_json_object(text: str) -> dict[str, Any]:
    raw = clean_text(text, 50000)
    candidates = [raw]
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.insert(0, fenced.group(1))
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        candidates.append(raw[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def parse_storyboard_response(text: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    settings = normalize_settings(project.get("settings"))
    parsed = extract_json_object(text)
    raw_shots = parsed.get("shots") if isinstance(parsed.get("shots"), list) else []
    fallback = build_fallback_storyboard(project)
    durations = allocate_durations(settings["totalDuration"], settings["shotCount"])
    shots: list[dict[str, Any]] = []
    for index in range(settings["shotCount"]):
        source = raw_shots[index] if index < len(raw_shots) and isinstance(raw_shots[index], dict) else fallback[index]
        source = dict(source)
        if source.get("videoPrompt") and not source.get("prompt"):
            source["prompt"] = source["videoPrompt"]
        merged = {**fallback[index], **source, "duration": durations[index]}
        shots.append(normalize_shot(merged, index, settings["shotCount"], durations[index]))
        shots[-1]["status"] = "ready"
    return shots


def build_storyboard_messages(project: dict[str, Any]) -> list[dict[str, str]]:
    settings = normalize_settings(project.get("settings"))
    brief = normalize_brief(project.get("brief"))
    context = {
        "product_name": clean_text(project.get("productName"), 240),
        "product_description": clean_text(project.get("productDescription"), TEXT_LIMIT),
        "brief": brief["summary"],
        "audience": brief["audience"],
        "selling_points": brief["sellingPoints"],
        "market": settings["market"],
        "language": settings["language"],
        "platform": settings["platform"],
        "ratio": settings["ratio"],
        "shot_count": settings["shotCount"],
        "total_duration_seconds": settings["totalDuration"],
    }
    system = (
        "You are a direct-response video creative director. Return only valid JSON with a shots array. "
        "Each shot needs role, title, scene, camera, imagePrompt, videoPrompt, copy, and duration. Keep claims evidence-based, "
        "preserve product facts, maintain character and wardrobe continuity, and make each prompt ready for Seedance."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(context, ensure_ascii=False, indent=2)},
    ]


def replace_storyboard(
    path: Path,
    project_id: str,
    username: str,
    shots: list[dict[str, Any]],
    source: str,
    warning: str = "",
    is_admin: bool = False,
) -> dict[str, Any]:
    project = get_project(path, project_id, username, is_admin)
    settings = project["settings"]
    durations = allocate_durations(settings["totalDuration"], settings["shotCount"])
    normalized = [
        normalize_shot(shots[index] if index < len(shots) else {}, index, settings["shotCount"], durations[index])
        for index in range(settings["shotCount"])
    ]
    for shot in normalized:
        shot["status"] = "ready" if shot["prompt"] else "draft"
    return update_project(
        path,
        project_id,
        username,
        {"shots": normalized, "storyboardSource": source, "warning": warning, "currentStep": 2},
        is_admin,
    )


def update_shot(
    path: Path,
    project_id: str,
    username: str,
    shot_id: str,
    payload: Any,
    is_admin: bool = False,
) -> dict[str, Any]:
    project = get_project(path, project_id, username, is_admin)
    clean_id = clean_text(shot_id, 80)
    source = payload if isinstance(payload, dict) else {}
    index = next((position for position, shot in enumerate(project["shots"]) if shot["id"] == clean_id), -1)
    if index < 0:
        raise ProjectNotFound("分镜不存在。")
    candidate = {**project["shots"][index]}
    allowed = {
        "title",
        "role",
        "scene",
        "camera",
        "imagePrompt",
        "prompt",
        "copy",
        "duration",
        "referenceImage",
        "referenceAssets",
        "referenceVideos",
        "generationMode",
        "referencePrivacyMode",
        "imageGenerationMode",
        "referenceImageSource",
        "imageModel",
        "imageSize",
        "imageGeneratedAt",
        "imageGenerationRoute",
        "imageReferenceCount",
        "imageReferenceAssets",
        "imageError",
        "taskId",
        "status",
        "videoUrl",
        "error",
        "excluded",
    }
    for key in allowed:
        if key in source:
            candidate[key] = validate_reference_videos(source[key]) if key == "referenceVideos" else source[key]
    project["shots"][index] = candidate
    return update_project(path, project_id, username, {"shots": project["shots"]}, is_admin)


def reorder_shots(
    path: Path,
    project_id: str,
    username: str,
    shot_ids: list[str],
    is_admin: bool = False,
) -> dict[str, Any]:
    project = get_project(path, project_id, username, is_admin)
    current_ids = [shot["id"] for shot in project["shots"]]
    ordered_ids = [clean_text(item, 80) for item in shot_ids]
    if len(ordered_ids) != len(current_ids) or set(ordered_ids) != set(current_ids):
        raise InvalidProject("分镜顺序必须包含当前项目的全部分镜。")
    by_id = {shot["id"]: shot for shot in project["shots"]}
    ordered = [by_id[shot_id] for shot_id in ordered_ids]
    return update_project(path, project_id, username, {"shots": ordered}, is_admin)


def composition_clips(project: dict[str, Any]) -> list[str]:
    shots = project.get("shots") if isinstance(project.get("shots"), list) else []
    clips = [
        clean_url(shot.get("videoUrl"))
        for shot in shots
        if isinstance(shot, dict) and not shot.get("excluded") and clean_url(shot.get("videoUrl"))
    ]
    if not clips:
        raise InvalidProject("至少需要一个已生成的视频片段才能合成。")
    return clips
