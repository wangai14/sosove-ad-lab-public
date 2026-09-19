from __future__ import annotations

import argparse
import base64
import binascii
import cgi
import copy
import html
import hashlib
import hmac
import io
import ipaddress
import json
import mimetypes
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

try:
    from seedance_web.chatcut_sync import build_sync_request, normalize_ledger, update_sync_request
except ImportError:
    from chatcut_sync import build_sync_request, normalize_ledger, update_sync_request

try:
    from seedance_web import ad_forge
except ImportError:
    import ad_forge


PROJECT_DIR = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_DIR / "static"
ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
CONFIG_DIR = Path(os.environ.get("SEEDANCE_RUNTIME_DIR") or PROJECT_DIR / ".runtime").expanduser()
CONFIG_FILE = CONFIG_DIR / "config.json"
AUTH_FILE = CONFIG_DIR / "auth.json"
SESSION_SECRET_FILE = CONFIG_DIR / "session-secret.json"
UPLOAD_ROOT = CONFIG_DIR / "uploads"
DRAFT_REQUEST_DIR = CONFIG_DIR / "jianying-draft-requests"
AD_FORGE_PROJECTS_FILE = CONFIG_DIR / "ad-forge-projects.json"
AD_FORGE_EXPORT_ROOT = CONFIG_DIR / "ad-forge-exports"
AD_FORGE_IMAGE_ROOT = CONFIG_DIR / "ad-forge-images"
AD_FORGE_IMAGE_CONFIG_FILE = CONFIG_DIR / "ad-forge-image-config.json"
FFPROBE_BIN = shutil.which("ffprobe")
FFMPEG_BIN = shutil.which("ffmpeg")
DEFAULT_OBSIDIAN_MATERIAL_ROOT = Path(
    os.environ.get("SEEDANCE_DEFAULT_OBSIDIAN_MATERIAL_ROOT")
    or PROJECT_DIR / "material-vault"
)
OBSIDIAN_MATERIAL_ROOT = Path(os.environ.get("SEEDANCE_OBSIDIAN_MATERIAL_ROOT") or DEFAULT_OBSIDIAN_MATERIAL_ROOT).expanduser()
OBSIDIAN_DATA_DIR = OBSIDIAN_MATERIAL_ROOT / "data"
OBSIDIAN_BATCH_DIR = OBSIDIAN_MATERIAL_ROOT / "batches"
OBSIDIAN_ANALYSIS_DIR = OBSIDIAN_MATERIAL_ROOT / "analysis"
OBSIDIAN_UPLOAD_ROOT = OBSIDIAN_MATERIAL_ROOT / "uploads"
OBSIDIAN_SYSTEM_DIR = OBSIDIAN_MATERIAL_ROOT / "system"
OBSIDIAN_ROUGH_CUT_DIR = OBSIDIAN_MATERIAL_ROOT / "rough-cuts"
OBSIDIAN_PLAYBACK_PROXY_DIR = OBSIDIAN_MATERIAL_ROOT / "playback-cache"
MATERIAL_LIBRARY_FILE = OBSIDIAN_DATA_DIR / "material-library.json"
AUTO_EDIT_POOL_FILE = OBSIDIAN_DATA_DIR / "auto-edit-pool.json"
UPLOAD_SYNC_IGNORE_FILE = OBSIDIAN_DATA_DIR / "upload-sync-ignore.json"
JIANYING_DRAFTS_INDEX_FILE = OBSIDIAN_DATA_DIR / "jianying-drafts.json"
ROUGH_CUTS_INDEX_FILE = OBSIDIAN_DATA_DIR / "rough-cuts.json"
MATERIAL_DIRECTION_MONITOR_FILE = OBSIDIAN_DATA_DIR / "material-direction-monitor.json"
MATERIAL_DIRECTION_REPORT_FILE = OBSIDIAN_ANALYSIS_DIR / "剪辑方向监控.md"
MANUAL_CUT_DRAFT_FILE = OBSIDIAN_DATA_DIR / "manual-cut-draft.json"
MANUAL_CUT_DRAFT_REPORT_FILE = OBSIDIAN_ANALYSIS_DIR / "手动分段草稿.md"
CHATCUT_SYNC_FILE = OBSIDIAN_DATA_DIR / "chatcut-sync.json"
CHATCUT_EXECUTOR_STATUS_FILE = OBSIDIAN_DATA_DIR / "chatcut-executor.json"
EDITING_TASKS_FILE = OBSIDIAN_DATA_DIR / "editing-tasks.json"
EDITING_TASKS_REPORT_FILE = OBSIDIAN_SYSTEM_DIR / "剪辑任务看板.md"
VIDEO_COPY_LIBRARY_FILE = OBSIDIAN_DATA_DIR / "video-copy-library.json"
VIDEO_COPY_LIBRARY_INDEX_FILE = OBSIDIAN_SYSTEM_DIR / "视频文案库.md"
PUBLIC_RUNTIME_CONFIG_FILE = OBSIDIAN_DATA_DIR / "runtime-config.public.json"
PUBLIC_AUTH_USERS_FILE = OBSIDIAN_DATA_DIR / "auth-users.public.json"
PROJECT_MANIFEST_FILE = OBSIDIAN_DATA_DIR / "project-manifest.json"
MATERIAL_INDEX_FILE = OBSIDIAN_MATERIAL_ROOT / "素材库总览.md"
SYSTEM_INDEX_FILE = OBSIDIAN_SYSTEM_DIR / "网站数据总览.md"
VIDEO_MATERIAL_ANALYZER_SCRIPT = Path(
    os.environ.get("VIDEO_MATERIAL_ANALYZER_SCRIPT")
    or PROJECT_DIR / "skills" / "video-material-analyzer" / "scripts" / "analyze_uploaded_videos.py"
).expanduser()
DEFAULT_MATERIAL_ANALYZER_PYTHON = Path(sys.executable)
MATERIAL_ANALYZER_PYTHON = Path(os.environ.get("MATERIAL_ANALYZER_PYTHON") or DEFAULT_MATERIAL_ANALYZER_PYTHON)
MATERIAL_ANALYZER_TIMEOUT_SECONDS = int(os.environ.get("MATERIAL_ANALYZER_TIMEOUT_SECONDS") or "600")
JIANYING_DRAFT_GENERATOR_SCRIPT = Path(
    os.environ.get("JIANYING_DRAFT_GENERATOR_SCRIPT")
    or PROJECT_DIR / "scripts" / "generate_jianying_draft.py"
).expanduser()
JIANYING_EDITOR_SKILL_ROOT = Path(
    os.environ.get("JIANYING_EDITOR_SKILL_ROOT")
    or PROJECT_DIR / "skills" / "jianying-editor"
).expanduser()
JAPANESE_EDITOR_SKILL_ROOT = Path(
    os.environ.get("JAPANESE_EDITOR_SKILL_ROOT")
    or PROJECT_DIR / "skills" / "japanese-fashion-video-editor"
).expanduser()
JIANYING_PYTHON = Path(
    os.environ.get("JIANYING_PYTHON")
    or CONFIG_DIR / "jianying-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
).expanduser()
JIANYING_DRAFT_TIMEOUT_SECONDS = int(os.environ.get("JIANYING_DRAFT_TIMEOUT_SECONDS") or "600")
ROUGH_CUT_GENERATOR_SCRIPT = Path(
    os.environ.get("ROUGH_CUT_GENERATOR_SCRIPT")
    or PROJECT_DIR / "scripts" / "export_rough_cut.py"
).expanduser()
ROUGH_CUT_TIMEOUT_SECONDS = int(os.environ.get("ROUGH_CUT_TIMEOUT_SECONDS") or "600")
DEFAULT_MODEL = "doubao-seedance-2-0-260128"
DEFAULT_AI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AI_MODEL = "gpt-4o-mini"
DEFAULT_AD_FORGE_IMAGE_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AD_FORGE_IMAGE_MODEL = "gpt-image-2"
DEFAULT_ELEVENLABS_MODEL = "eleven_multilingual_v2"
DEFAULT_SKILL_DIR = PROJECT_DIR / "skills" / "sosove-japan-fashion-video-generator"
DEFAULT_SEEDANCE_REVIEW_SKILL_DIR = Path(
    os.environ.get("SEEDANCE_REVIEW_SKILL_DIR")
    or Path.home() / ".codex" / "skills" / "seedance-20"
).expanduser()
SEEDANCE_REVIEW_SKILL_FILES = [
    "SKILL.md",
    "skills/seedance-prompt/SKILL.md",
    "skills/seedance-antislop/SKILL.md",
    "references/directors-read.md",
    "references/quick-ref.md",
    "references/multilingual-community-examples.md",
    "skills/seedance-filter/SKILL.md",
    "skills/seedance-copyright/SKILL.md",
    "references/reference-workflow.md",
    "references/surface-prompt-profiles.md",
]
AD_FORGE_PROMPT_SKILL_FILES = [
    "SKILL.md",
    "skills/seedance-prompt/SKILL.md",
    "skills/seedance-recipes/SKILL.md",
    "skills/seedance-antislop/SKILL.md",
    "references/directors-read.md",
    "references/quick-ref.md",
    "references/allocation-model.md",
    "references/pro-filmmaking-standards.md",
    "references/shot-list-continuity.md",
    "references/multilingual-community-examples.md",
]
MAX_SEEDANCE_REVIEW_CONTEXT_CHARS = int(os.environ.get("SEEDANCE_REVIEW_CONTEXT_CHARS") or "80000")
MAX_AD_FORGE_PROMPT_SKILL_CONTEXT_CHARS = int(os.environ.get("AD_FORGE_PROMPT_SKILL_CONTEXT_CHARS") or "90000")
COMMON_SKILL_REFERENCE_FILES = [
    "references/fact-metric-rules.md",
    "references/seedance-rules.md",
    "references/output-format.md",
]
PRODUCT_SKILL_REFERENCE_FILES = {
    "dress": "references/dress-structures.md",
    "pants": "references/pants-structures.md",
    "skirt": "references/skirt-structures.md",
    "fallback": "references/fallback-structures.md",
}
MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_SEEDANCE_INLINE_IMAGE_TOTAL_BYTES = 32 * 1024 * 1024
MAX_FASHION_ANALYSIS_IMAGES = 6
MAX_FASHION_ANALYSIS_IMAGE_BYTES = 8 * 1024 * 1024
MAX_FASHION_ANALYSIS_TOTAL_BYTES = 24 * 1024 * 1024
FASHION_ANALYSIS_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
FASHION_REFERENCE_ROLES = {"front_full", "front_detail", "back", "side", "fabric", "extra"}
FASHION_PROMPT_MODES = {"fidelity", "stable"}
FASHION_PLATFORM_PRESETS = {"tiktok", "facebook", "instagram", "amazon", "independent", "custom"}
FASHION_REFERENCE_CONSISTENCY_STATUSES = {"consistent", "warning", "conflict", "single", "not_provided"}
MAX_FASHION_OPTIMIZATION_PROMPTS = 7
MAX_FASHION_OPTIMIZATION_PROMPT_CHARS = 16000
MAX_FASHION_GENERATION_PROMPT_CHARS = 16000
FASHION_GENERATION_ROLE_KEYS = {
    3: ["overview", "detail", "walking"],
    5: ["overview", "detail", "walking", "routine", "ending"],
    7: ["overview", "detail", "walking", "routine", "activity", "lifestyle", "ending"],
}
FASHION_GENERATION_ROLE_BRIEFS = {
    "overview": ("外观与完整形态", "证明完整外形、比例、颜色、部件数量和商品边界"),
    "detail": ("关键结构与材质", "从当前商品最易漂移且已有证据的结构中选择一个重点，证明形状、数量、位置和连接关系"),
    "walking": ("真实操作演示", "用一个与当前品类匹配的低风险动作，证明商品结构和物理状态连续"),
    "routine": ("日常使用流程", "按真实先后顺序完成一个普通使用流程，商品与配件状态不得跳变"),
    "activity": ("功能状态证明", "只展示已经确认的可见功能状态与停止终点，不扩写性能或功效宣称"),
    "lifestyle": ("真实场景适配", "把商品放入一个与用途匹配的克制场景，环境和人物始终从属于商品"),
    "ending": ("干净商品收尾", "生成一个动作完整、便于剪辑衔接的稳定商品终点，不添加新卖点或新道具"),
}

# Legacy API and function names retain "fashion" for backwards compatibility,
# but the workbench now routes all common ecommerce product families.
FASHION_GENERAL_CATEGORIES = {
    "美妆个护", "食品饮料", "家居日用", "厨房用品", "数码电子", "家用电器",
    "鞋包配饰", "母婴玩具", "宠物用品", "运动户外", "汽车用品", "其他商品",
    "背带裤连体裤", "长裤", "半身裙", "连衣裙", "上衣", "外套", "其他女装",
}
FASHION_APPAREL_CATEGORIES = {
    "背带裤连体裤", "长裤", "半身裙", "连衣裙", "上衣", "外套", "其他女装",
}
FASHION_PRODUCT_PROFILES: dict[str, dict[str, Any]] = {
    "apparel": {
        "id": "apparel", "name": "服饰", "subject": "同一位原创成年模特与同一件服饰商品",
        "operator": "模特只做自然站立、转身、正常步行或当前服饰允许的低复杂度动作",
        "productSpan": "商品从最上缘到下摆或裤脚的完整穿着轮廓",
        "overviewProof": "完整轮廓、长度、正侧关系和已确认的背面结构",
        "detailProof": "领口、门襟、腰头、扣件、口袋、袖口、下摆或其他已确认结构",
        "motionProof": "商品随身体与重力自然运动，已确认结构保持稳定",
        "activityProof": "动作发生处只产生真实临时形变，停止后按当前材质自然稳定",
        "continuityRule": "同一人物、同一件商品、同一颜色和同一套造型连续；未知背面不展示、不补全",
        "framing": "商品上下边缘完整可见，不被手、包、头发或画面边缘遮挡",
        "exclusions": ["不改变服饰品类、版型、长度或开合", "不新增未确认口袋、扣件、拼接或功能", "不复制正面结构到背面"],
        "scenes": ["安静的浅色室内", "简洁玄关", "普通住宅街道"],
    },
    "beauty": {
        "id": "beauty", "name": "美妆个护", "subject": "同一件商品与一双干净的成年人的手",
        "operator": "成年人只在手背或商品允许的非敏感区域完成一次克制演示",
        "productSpan": "包装、容器、开合件、标签位置与可见内容物",
        "overviewProof": "容器外形、包装比例、颜色和开合关系", "detailProof": "刷头、泵头、瓶口、盖体与可见质地",
        "motionProof": "开盖、取用、少量延展与归位的真实顺序", "activityProof": "内容物只呈现参考可见的流动、延展或附着状态",
        "continuityRule": "容器、盖体、工具和内容物用量连续，已取出的内容物不会凭空回到容器",
        "framing": "商品与操作手清楚，标签和开合结构不被手指遮住",
        "exclusions": ["不改变包装、刷头、泵头或盖体结构", "不虚构上脸效果、疗效、成分或即时功效", "不让内容物颜色、稠度或用量跳变"],
        "scenes": ["纯净梳妆台", "自然光浴室台面", "简洁旅行收纳台"],
    },
    "food": {
        "id": "food", "name": "食品饮料", "subject": "同一份商品、原包装与一双干净的成年人的手",
        "operator": "成年人按真实食用顺序开封、倒出、冲泡或摆盘",
        "productSpan": "完整包装、封口、内容物形态、份量关系与盛放容器",
        "overviewProof": "包装外形、规格感、主色与内容物对应关系", "detailProof": "封口、可见断面、气泡、蒸汽或表面状态",
        "motionProof": "开封、倒出、切开或搅拌的真实物理过程", "activityProof": "内容物只呈现参考和档案确认的流动、软硬、酥脆或热气状态",
        "continuityRule": "包装开封状态、内容物总量与盛放位置连续，倒出或取走后数量只合理减少",
        "framing": "包装和内容物至少一项完整可见，食品接触面干净",
        "exclusions": ["不虚构口味、配方、营养、产地或健康功效", "不让内容物凭空增加、回流或变成另一种食品", "不生成不卫生接触、过量飞溅或危险烹饪"],
        "scenes": ["干净餐桌", "自然光厨房台面", "简洁早餐场景"],
    },
    "home": {
        "id": "home", "name": "家居日用", "subject": "同一件家居商品与一双成年人的手",
        "operator": "成年人按真实家务流程摆放、开合、装入或整理",
        "productSpan": "商品完整外轮廓、支撑结构、开合件、接缝与实际附带物",
        "overviewProof": "尺寸比例、完整形态与空间占用关系", "detailProof": "连接、边缘、把手、卡扣、支脚或收纳分区",
        "motionProof": "摆放、开合、承托或整理过程中的结构稳定", "activityProof": "在正常低风险动作下保持当前形态与连接关系",
        "continuityRule": "开合状态、内部物品数量与摆放位置连续，不凭空增减配件",
        "framing": "商品完整边缘与操作点清楚，不被家具或手臂遮挡",
        "exclusions": ["不虚构承重、耐久、抗菌或安全等级", "不增减隔层、支脚、卡扣或配件", "不出现穿模、悬浮或不可能的开合方式"],
        "scenes": ["真实家庭使用空间", "纯净收纳角落", "自然光客厅"],
    },
    "kitchen": {
        "id": "kitchen", "name": "厨房用品", "subject": "同一件厨房用品、少量普通食材与一双成年人的手",
        "operator": "成年人在安全干净的台面按正确方向握持和使用",
        "productSpan": "主体、手柄、开口、工作面、连接件与实际配件",
        "overviewProof": "完整外形、握持关系和台面尺度", "detailProof": "手柄连接、刻度、边缘、盖体、滤网或工作面",
        "motionProof": "握持、开合、倾倒、切分或搅拌的合理动作", "activityProof": "正常使用时结构连接与食材状态变化连续",
        "continuityRule": "工具、配件与食材数量连续，操作方向符合真实结构",
        "framing": "工作端、手柄和食材接触点清楚，危险边缘始终受控",
        "exclusions": ["不虚构锋利度、耐热、无毒或烹饪效果", "不出现危险握持或失控飞溅", "不增减盖体、滤网、刀片或连接件"],
        "scenes": ["自然光厨房台面", "干净水槽旁", "简洁餐前准备区"],
    },
    "electronics": {
        "id": "electronics", "name": "数码电子", "subject": "同一套数码商品、实际配件与一双成年人的手",
        "operator": "成年人按真实接口和控件做一次清楚的桌面操作",
        "productSpan": "设备主体、充电盒或底座、按键、接口、指示灯、屏幕与实际配件",
        "overviewProof": "整机外形、部件数量、颜色和收纳关系", "detailProof": "接口、按键、转轴、触点、扬声器孔或屏幕边框",
        "motionProof": "开合、取放、插接、按键与屏幕交互的正确顺序", "activityProof": "指示灯或屏幕状态只按已确认功能变化，部件连接稳定",
        "continuityRule": "设备、左右部件、线材和工作状态连续，接口方向与收纳位置正确",
        "framing": "设备完整或关键操作区清楚，屏幕保持简洁且不生成乱码",
        "exclusions": ["不虚构续航、音质、算力、防水或连接性能", "不增减按键、接口、耳机、线材或指示灯", "不让屏幕、灯光、转轴或插头状态无原因跳变"],
        "scenes": ["纯净自然光桌面", "真实居家办公桌", "简洁通勤桌面"],
    },
    "appliance": {
        "id": "appliance", "name": "家用电器", "subject": "同一台家电、实际附件与一双成年人的手",
        "operator": "成年人先确认放置与控件，再启动一个已确认的低风险功能",
        "productSpan": "整机、底座、门盖、水箱、滤网、出风口、控制区与实际附件",
        "overviewProof": "整机外形、尺寸关系、部件位置和工作朝向", "detailProof": "控制区、门盖、滤网、水箱、接口或出风口",
        "motionProof": "开合、装入、按键、工作与关机归位的完整顺序", "activityProof": "只展示已确认的灯光、转动、气流、水流或声音状态",
        "continuityRule": "整机和可拆部件数量、装配方向与工作状态连续，先关机再拆卸或清洁",
        "framing": "整机和操作区清楚，电源、水源与高温部位不被错误操作",
        "exclusions": ["不虚构功率、节能、净化、杀菌或效率", "不生成带电拆卸、湿手插电或接触高温等危险动作", "不增减滤网、水箱、门盖、按钮或附件"],
        "scenes": ["真实家庭使用空间", "自然光厨房或浴室", "简洁家务区"],
    },
    "accessory": {
        "id": "accessory", "name": "鞋包配饰", "subject": "同一件配饰与同一位成年使用者",
        "operator": "成年人按商品类型完成佩戴、开合、背负或正常步行演示",
        "productSpan": "商品完整轮廓、开合件、带体、五金、内部分区、鞋底或实际配件",
        "overviewProof": "完整外形、尺寸比例与佩戴或携带关系", "detailProof": "五金、车线、扣件、拉链、带体、鞋底或内部分区",
        "motionProof": "开合、调节、背负、穿脱或正常步行中的结构稳定", "activityProof": "与身体接触处和活动连接件按真实重力运动",
        "continuityRule": "商品、肩带、鞋带、五金和内装数量连续，左右件不互换",
        "framing": "商品主体完整可见，手、衣物与身体不遮住关键结构",
        "exclusions": ["不虚构容量、舒适、防水、耐磨或材质成分", "不增减带体、五金、鞋带、拉链或左右件", "不让包体、鞋型或首饰比例随镜头变化"],
        "scenes": ["纯净穿搭区", "真实玄关", "克制的通勤环境"],
    },
    "toy": {
        "id": "toy", "name": "母婴玩具", "subject": "同一件商品与一双成年人的手",
        "operator": "成年人负责组装、开启或演示；儿童不承担危险动作",
        "productSpan": "主体、部件、连接点、活动结构、包装与实际配件",
        "overviewProof": "完整形态、部件数量、颜色和比例", "detailProof": "连接点、按钮、活动件、纹理与边缘",
        "motionProof": "组装、推动、旋转或触发的正确顺序", "activityProof": "活动件只按真实连接与已确认功能运动",
        "continuityRule": "所有部件数量、装配方向与位置连续，小零件不凭空出现或消失",
        "framing": "商品和成人操作手清楚，连接点与活动路径不被遮挡",
        "exclusions": ["不虚构适龄、安全、益智、无毒或认证信息", "不生成婴幼儿无人看护或危险玩法", "不增减零件、按钮、轮子或活动关节"],
        "scenes": ["明亮家庭游戏区", "纯净儿童房桌面", "简洁收纳区"],
    },
    "pet": {
        "id": "pet", "name": "宠物用品", "subject": "同一件宠物商品、一双成年人的手与一只自然状态的宠物",
        "operator": "成年人先完成设置，宠物自主靠近或使用，不强迫摆拍",
        "productSpan": "商品主体、开口、卡扣、容器、连接件与实际配件",
        "overviewProof": "完整形态、尺寸比例与宠物使用关系", "detailProof": "开口、卡扣、出水口、缝线、连接点或容器",
        "motionProof": "安装、填充、开合或调整后宠物自然使用的过程", "activityProof": "商品受力、液体、食物或活动件按真实物理变化",
        "continuityRule": "商品、配件、食物或水量连续，宠物外观与项圈等保持一致",
        "framing": "商品始终是主体，宠物不被束缚，操作手不遮挡关键结构",
        "exclusions": ["不虚构健康、舒缓、训练或安全功效", "不强迫宠物动作、不制造惊吓或不适", "不增减卡扣、容器、牵引结构或配件"],
        "scenes": ["安静家庭宠物角", "自然光客厅地面", "安全户外休息区"],
    },
    "sports": {
        "id": "sports", "name": "运动户外", "subject": "同一件运动户外商品与同一位成年人",
        "operator": "成年人先调节与检查，再完成一次低强度、安全的真实使用动作",
        "productSpan": "主体、握持区、带体、锁扣、支撑点、鞋底或实际附件",
        "overviewProof": "完整外形、尺寸比例与正确使用关系", "detailProof": "锁扣、带体、支撑、纹路、握把或连接点",
        "motionProof": "调节、穿戴、展开、握持或低强度运动过程", "activityProof": "受力点、回弹或活动连接只按真实结构变化",
        "continuityRule": "商品、锁扣、带体与附件数量连续，调节位置保持一致",
        "framing": "完整商品与关键受力点可见，动作空间安全",
        "exclusions": ["不虚构性能、保护、防伤、耐久或专业认证", "不生成高速、极限、危险地形或错误使用", "不增减带体、锁扣、支撑或左右件"],
        "scenes": ["安全室内训练区", "平整户外步道", "简洁装备整理区"],
    },
    "automotive": {
        "id": "automotive", "name": "汽车用品", "subject": "同一件汽车用品、静止车辆与一双成年人的手",
        "operator": "车辆保持熄火静止，成年人按正确位置安装、调节或演示",
        "productSpan": "商品主体、安装件、卡扣、线材、接口、支撑面与实际附件",
        "overviewProof": "完整外形、部件数量与车内安装位置关系", "detailProof": "卡扣、接口、支架、线材路径、接触面或控制区",
        "motionProof": "安装、锁定、调节、连接与拆卸的正确顺序", "activityProof": "固定、转轴或控件只在安全静止状态下演示",
        "continuityRule": "车辆、商品、卡扣、线材和安装位置连续，车辆全程静止",
        "framing": "商品和安装点清楚，不遮挡驾驶视线或车辆安全控制",
        "exclusions": ["不虚构适配车型、安全、防护或性能", "不在行驶中安装、拍摄或操作，不遮挡视线", "不增减卡扣、线材、接口或支架"],
        "scenes": ["熄火静止的整洁车内", "安全停车位", "纯净汽车用品展示台"],
    },
    "universal_product": {
        "id": "universal_product", "name": "其他商品", "subject": "同一件商品与一双成年人的手",
        "operator": "成年人只按当前已确认结构完成一个低风险操作",
        "productSpan": "商品完整外轮廓、主要结构、开合件、连接处、材质与实际附件",
        "overviewProof": "完整外形、比例、颜色与部件数量", "detailProof": "最易漂移的结构、边缘、连接与可见材质",
        "motionProof": "拿起、旋转、开合、放回或当前商品真实允许的动作", "activityProof": "商品状态只按当前可见材质、结构与重力变化",
        "continuityRule": "商品、可拆部件和附件数量连续，操作方向服从已确认结构",
        "framing": "商品完整或目标细节清楚，操作手不遮挡关键边缘",
        "exclusions": ["不虚构功能、参数、功效、材质成分或认证", "不新增未确认部件、开口、接口或装饰", "不使用危险、不可能或与商品无关的动作"],
        "scenes": ["纯净自然光桌面", "真实家庭使用空间", "简洁商业使用环境"],
    },
}
MAX_AD_FORGE_IMAGE_BYTES = 25 * 1024 * 1024
MAX_AD_FORGE_EDIT_REFERENCES = 4
MAX_AD_FORGE_EDIT_TOTAL_BYTES = 32 * 1024 * 1024
AD_FORGE_IMAGE_REQUEST_LOCK = threading.RLock()
AD_FORGE_IMAGE_REQUESTS: dict[str, dict[str, Any]] = {}
MAX_IMAGE_UPLOAD_COUNT = 9
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_VIDEO_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_VIDEO_UPLOAD_COUNT = 4
ALLOWED_VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-m4v": ".m4v",
}
MAX_AUDIO_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_AUDIO_UPLOAD_COUNT = 4
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
}
MAX_REMOTE_IMPORT_URLS = int(os.environ.get("SEEDANCE_REMOTE_IMPORT_MAX_URLS") or "50")
MAX_REMOTE_IMPORT_PAGE_BYTES = int(os.environ.get("SEEDANCE_REMOTE_IMPORT_PAGE_BYTES") or str(2 * 1024 * 1024))
REMOTE_IMPORT_TIMEOUT_SECONDS = int(os.environ.get("SEEDANCE_REMOTE_IMPORT_TIMEOUT_SECONDS") or "60")
REMOTE_IMPORT_USER_AGENT = "SeedanceMaterialImporter/1.0"
MAX_LOCAL_FOLDER_IMPORT_FILES = int(os.environ.get("SEEDANCE_LOCAL_FOLDER_IMPORT_MAX_FILES") or "5000")
MAX_LOCAL_FOLDER_ANALYZE_LIMIT = int(os.environ.get("SEEDANCE_LOCAL_FOLDER_ANALYZE_LIMIT") or "50")
MATERIAL_UPLOAD_CONFIGS: dict[str, dict[str, Any]] = {
    "images": {
        "fields": ["images", "image", "files", "file"],
        "item_key": "images",
        "display_name": "Image",
        "url_label": "图片",
        "allowed_types": ALLOWED_IMAGE_TYPES,
        "max_bytes": MAX_IMAGE_UPLOAD_BYTES,
        "max_count": MAX_IMAGE_UPLOAD_COUNT,
    },
    "videos": {
        "fields": ["videos", "video", "files", "file"],
        "item_key": "videos",
        "display_name": "Video",
        "url_label": "视频",
        "allowed_types": ALLOWED_VIDEO_TYPES,
        "max_bytes": MAX_VIDEO_UPLOAD_BYTES,
        "max_count": MAX_VIDEO_UPLOAD_COUNT,
    },
    "audios": {
        "fields": ["audios", "audio", "files", "file"],
        "item_key": "audios",
        "display_name": "Audio",
        "url_label": "音频",
        "allowed_types": ALLOWED_AUDIO_TYPES,
        "max_bytes": MAX_AUDIO_UPLOAD_BYTES,
        "max_count": MAX_AUDIO_UPLOAD_COUNT,
    },
}
ANALYSIS_STATUS_LABELS = {
    "queued": "待 AI 分析",
    "analyzing": "分析中",
    "analyzed": "已分析",
    "ready": "可剪辑",
    "hold": "待补拍",
    "rejected": "废弃",
}
EDIT_ROLE_LABELS = {
    "unassigned": "待判断",
    "hook": "开头钩子",
    "try_on": "上身展示",
    "detail": "细节特写",
    "motion": "动作镜头",
    "transition": "转场氛围",
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
PRIORITY_LABELS = {
    "high": "高优先",
    "normal": "普通",
    "low": "低优先",
}
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
MODEL_PRESETS = [
    {
        "label": "Seedance 2.0",
        "value": DEFAULT_MODEL,
        "hint": "doubao-seedance-2-0-260128",
    }
]
MODEL_ALIASES = {
    "seed2.0": DEFAULT_MODEL,
    "seed-2.0": DEFAULT_MODEL,
    "seedance2.0": DEFAULT_MODEL,
    "seedance-2.0": DEFAULT_MODEL,
    "seedance2": DEFAULT_MODEL,
    "seedance-2": DEFAULT_MODEL,
}
VALID_RATIOS = {"9:16", "16:9", "1:1"}
VALID_DURATIONS = {5, 10, 11, 15}
MIN_QUANTITY = 1
MAX_QUANTITY = 4
MIN_PROMPT_COUNT = 1
MAX_PROMPT_COUNT = 4
FILE_RESPONSE_CHUNK_SIZE = 1024 * 1024
PLAYBACK_PROXY_TIMEOUT_SECONDS = int(os.environ.get("SEEDANCE_PLAYBACK_PROXY_TIMEOUT_SECONDS") or "600")
PLAYBACK_PROXY_LOCK = threading.Lock()
SESSION_COOKIE_NAME = "seedance_session"
SESSION_TTL_SECONDS = int(os.environ.get("SEEDANCE_SESSION_TTL_SECONDS") or str(7 * 24 * 60 * 60))
PASSWORD_HASH_ITERATIONS = int(os.environ.get("SEEDANCE_PASSWORD_HASH_ITERATIONS") or "260000")
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 10 * 60
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 8
LOGIN_ATTEMPTS: dict[str, list[float]] = {}
AUTH_ROLES = {"admin", "customer"}
EDITING_TASK_STATUS_LABELS = {
    "assigned": "待接单",
    "in_progress": "制作中",
    "review": "待审核",
    "revision": "需修改",
    "done": "已完成",
    "paused": "已暂停",
}
EDITING_TASK_STATUS_FLOW = set(EDITING_TASK_STATUS_LABELS)
COPY_LIBRARY_STAGE_LABELS = {
    "hook": "开头钩子",
    "pain_point": "痛点共鸣",
    "product_intro": "产品介绍",
    "detail_proof": "细节证明",
    "outfit": "穿搭场景",
    "cta": "收尾引导",
    "full_script": "完整脚本",
}
COPY_LIBRARY_STATUS_LABELS = {
    "template": "结构模板",
    "collected": "已收藏",
    "testing": "待测试",
    "verified": "已验证",
}


def parse_http_byte_range(range_header: str, file_size: int) -> tuple[int, int] | None:
    if not range_header:
        return None
    if file_size <= 0 or not range_header.startswith("bytes="):
        raise ValueError("Invalid byte range.")

    range_spec = range_header.removeprefix("bytes=").strip()
    if "," in range_spec:
        raise ValueError("Multiple byte ranges are not supported.")
    start_text, separator, end_text = range_spec.partition("-")
    if separator != "-":
        raise ValueError("Invalid byte range.")

    if not start_text:
        suffix_length = int(end_text)
        if suffix_length <= 0:
            raise ValueError("Invalid byte range.")
        start = max(file_size - suffix_length, 0)
        end = file_size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
        end = min(end, file_size - 1)

    if start < 0 or end < start or start >= file_size:
        raise ValueError("Requested range is outside the file.")
    return start, end


def b64encode_url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64decode_url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def clean_auth_username(value: object) -> str:
    username = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,64}", username):
        raise ValueError("账号只能使用 3-64 位字母、数字、下划线、点、@ 或横线。")
    return username


def clean_auth_password(value: object) -> str:
    password = str(value or "")
    if len(password) < 8 or len(password) > 128:
        raise ValueError("密码长度需要在 8-128 位之间。")
    return password


def clean_auth_display_name(value: object, fallback: str = "") -> str:
    display_name = str(value or "").strip()
    if not display_name:
        return str(fallback or "").strip()
    if len(display_name) > 80:
        raise ValueError("显示名称最多 80 个字符。")
    if any(ord(char) < 32 for char in display_name):
        raise ValueError("显示名称包含无效字符。")
    return display_name


def password_hash(password: str, salt: bytes, iterations: int = PASSWORD_HASH_ITERATIONS) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return b64encode_url(digest)


def clean_auth_role(value: object, default: str = "customer") -> str:
    role = str(value or default).strip()
    return role if role in AUTH_ROLES else default


def make_auth_user(username: str, password: str, role: str = "customer", display_name: str = "") -> dict[str, Any]:
    username = clean_auth_username(username)
    password = clean_auth_password(password)
    salt = os.urandom(16)
    now = utc_now_iso()
    return {
        "id": f"user-{uuid.uuid4().hex[:12]}",
        "username": username,
        "displayName": clean_auth_display_name(display_name, username),
        "role": clean_auth_role(role),
        "enabled": True,
        "passwordSalt": b64encode_url(salt),
        "passwordHash": password_hash(password, salt),
        "iterations": PASSWORD_HASH_ITERATIONS,
        "sessionVersion": 0,
        "createdAt": now,
        "updatedAt": now,
        "passwordUpdatedAt": now,
    }


def normalize_auth_user(value: dict[str, Any]) -> dict[str, Any] | None:
    try:
        username = clean_auth_username(value.get("username"))
    except ValueError:
        return None
    role = clean_auth_role(value.get("role"), "customer")
    try:
        session_version = max(0, int(value.get("sessionVersion") or 0))
    except (TypeError, ValueError):
        session_version = 0
    return {
        "id": str(value.get("id") or f"user-{uuid.uuid4().hex[:12]}"),
        "username": username,
        "displayName": clean_auth_display_name(value.get("displayName"), username),
        "role": role,
        "enabled": bool(value.get("enabled", True)),
        "passwordSalt": str(value.get("passwordSalt") or ""),
        "passwordHash": str(value.get("passwordHash") or ""),
        "iterations": int(value.get("iterations") or PASSWORD_HASH_ITERATIONS),
        "sessionVersion": session_version,
        "createdAt": str(value.get("createdAt") or utc_now_iso()),
        "updatedAt": str(value.get("updatedAt") or value.get("createdAt") or utc_now_iso()),
        "lastLoginAt": str(value.get("lastLoginAt") or ""),
        "passwordUpdatedAt": str(value.get("passwordUpdatedAt") or value.get("updatedAt") or value.get("createdAt") or ""),
    }


def normalize_auth_config(value: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    session_secret = str(value.get("sessionSecret") or "").strip()
    if len(session_secret) < 32:
        session_secret = secrets_token(48)

    users: list[dict[str, Any]] = []
    raw_users = value.get("users")
    if isinstance(raw_users, list):
        for raw_user in raw_users:
            if not isinstance(raw_user, dict):
                continue
            user = normalize_auth_user(raw_user)
            if user and user.get("passwordSalt") and user.get("passwordHash"):
                users.append(user)
    elif {"username", "passwordSalt", "passwordHash", "iterations"}.issubset(value):
        legacy_user = normalize_auth_user(
            {
                "username": value.get("username"),
                "role": "admin",
                "enabled": True,
                "passwordSalt": value.get("passwordSalt"),
                "passwordHash": value.get("passwordHash"),
                "iterations": value.get("iterations"),
                "createdAt": value.get("createdAt"),
            }
        )
        if legacy_user:
            users.append(legacy_user)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for user in users:
        key = user["username"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(user)
    if not deduped:
        return None
    if not any(user["role"] == "admin" and user.get("enabled", True) for user in deduped):
        deduped[0]["role"] = "admin"
        deduped[0]["enabled"] = True

    return {
        "version": 2,
        "sessionSecret": session_secret,
        "users": deduped,
        "createdAt": str(value.get("createdAt") or utc_now_iso()),
        "updatedAt": str(value.get("updatedAt") or utc_now_iso()),
    }


def read_auth_file() -> dict[str, Any] | None:
    if not AUTH_FILE.exists():
        return None
    try:
        payload = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    config = normalize_auth_config(payload)
    if config and payload.get("version") != 2:
        save_auth_config(config)
    return config


def read_env_auth_config() -> dict[str, Any] | None:
    username = os.environ.get("SEEDANCE_AUTH_USERNAME", "").strip()
    password = os.environ.get("SEEDANCE_AUTH_PASSWORD", "")
    if not username or not password:
        return None
    user = {
        "id": "env-admin",
        "username": username,
        "displayName": username,
        "role": "admin",
        "enabled": True,
        "sessionVersion": 0,
        "createdAt": "",
        "updatedAt": "",
        "lastLoginAt": "",
        "passwordUpdatedAt": "",
    }
    return {
        "mode": "env",
        "version": 2,
        "users": [user],
        "username": username,
        "password": password,
        "sessionSecret": read_or_create_session_secret(),
    }


def read_auth_config() -> dict[str, Any] | None:
    env_config = read_env_auth_config()
    if env_config:
        return env_config
    return read_auth_file()


def save_auth_config(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("mode") == "env":
        raise ValueError("当前已通过环境变量配置登录账号，不能在页面里管理客户账号。")
    normalized = normalize_auth_config(config)
    if not normalized:
        raise ValueError("认证配置无效。")
    normalized["updatedAt"] = utc_now_iso()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    sync_obsidian_project_data(auth_config=normalized)
    return normalized


def read_or_create_session_secret() -> str:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if SESSION_SECRET_FILE.exists():
        try:
            payload = json.loads(SESSION_SECRET_FILE.read_text(encoding="utf-8"))
            secret = str(payload.get("sessionSecret") or "").strip() if isinstance(payload, dict) else ""
            if len(secret) >= 32:
                return secret
        except (OSError, json.JSONDecodeError):
            pass
    secret = secrets_token(48)
    SESSION_SECRET_FILE.write_text(json.dumps({"sessionSecret": secret, "createdAt": utc_now_iso()}, indent=2), encoding="utf-8")
    return secret


def secrets_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def create_auth_config(username: str, password: str) -> dict[str, Any]:
    username = clean_auth_username(username)
    password = clean_auth_password(password)
    if read_env_auth_config():
        raise ValueError("当前已通过环境变量配置登录账号，不能在页面里重新初始化。")
    if read_auth_file():
        raise ValueError("管理员账号已经创建，请直接登录。")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "version": 2,
        "sessionSecret": secrets_token(48),
        "users": [make_auth_user(username, password, "admin")],
        "createdAt": utc_now_iso(),
    }
    return save_auth_config(config)


def auth_users(config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or read_auth_config()
    return list(config.get("users") or []) if config else []


def find_auth_user(config: dict[str, Any] | None, username: str) -> dict[str, Any] | None:
    target = str(username or "").strip().lower()
    if not config or not target:
        return None
    for user in auth_users(config):
        if str(user.get("username") or "").lower() == target:
            return user
    return None


def public_auth_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(user.get("id") or ""),
        "username": str(user.get("username") or ""),
        "displayName": clean_auth_display_name(user.get("displayName"), str(user.get("username") or "")),
        "role": clean_auth_role(user.get("role")),
        "enabled": bool(user.get("enabled", True)),
        "createdAt": str(user.get("createdAt") or ""),
        "updatedAt": str(user.get("updatedAt") or ""),
        "lastLoginAt": str(user.get("lastLoginAt") or ""),
        "passwordUpdatedAt": str(user.get("passwordUpdatedAt") or ""),
    }


def rotate_auth_user_password(user: dict[str, Any], password: str) -> dict[str, Any]:
    password = clean_auth_password(password)
    salt = os.urandom(16)
    now = utc_now_iso()
    user["passwordSalt"] = b64encode_url(salt)
    user["passwordHash"] = password_hash(password, salt)
    user["iterations"] = PASSWORD_HASH_ITERATIONS
    try:
        session_version = int(user.get("sessionVersion") or 0)
    except (TypeError, ValueError):
        session_version = 0
    user["sessionVersion"] = session_version + 1
    user["passwordUpdatedAt"] = now
    user["updatedAt"] = now
    return user


def create_customer_user(username: str, password: str, role: str = "customer", display_name: str = "") -> dict[str, Any]:
    config = read_auth_config()
    if not config:
        raise ValueError("需要先创建管理员账号。")
    if config.get("mode") == "env":
        raise ValueError("环境变量账号模式下不能添加客户账号。")
    username = clean_auth_username(username)
    password = clean_auth_password(password)
    role = clean_auth_role(role, "customer")
    if find_auth_user(config, username):
        raise ValueError("这个账号已经存在。")
    user = make_auth_user(username, password, role, display_name)
    config["users"] = [*auth_users(config), user]
    save_auth_config(config)
    return user


def set_auth_user_enabled(username: str, enabled: bool) -> dict[str, Any]:
    config = read_auth_config()
    if not config:
        raise ValueError("认证配置不存在。")
    if config.get("mode") == "env":
        raise ValueError("环境变量账号模式下不能修改客户账号。")
    user = find_auth_user(config, username)
    if not user:
        raise ValueError("账号不存在。")
    if user.get("role") == "admin" and not enabled:
        enabled_admins = [item for item in auth_users(config) if item.get("role") == "admin" and item.get("enabled", True) and item.get("username") != user.get("username")]
        if not enabled_admins:
            raise ValueError("不能停用最后一个管理员账号。")
    user["enabled"] = bool(enabled)
    user["updatedAt"] = utc_now_iso()
    save_auth_config(config)
    return user


def delete_auth_user(username: str, actor_username: str = "") -> dict[str, Any]:
    config = read_auth_config()
    if not config:
        raise ValueError("认证配置不存在。")
    if config.get("mode") == "env":
        raise ValueError("环境变量账号模式下不能删除页面账号。")
    username = clean_auth_username(username)
    actor_username = str(actor_username or "").strip()
    if actor_username and username.lower() == actor_username.lower():
        raise ValueError("不能删除当前登录账号，请先用其他管理员账号登录后再删除。")
    users = auth_users(config)
    user = find_auth_user(config, username)
    if not user:
        raise ValueError("账号不存在。")
    remaining_users = [
        item
        for item in users
        if str(item.get("username") or "").lower() != username.lower()
    ]
    if user.get("role") == "admin" and not any(item.get("role") == "admin" and item.get("enabled", True) for item in remaining_users):
        raise ValueError("不能删除最后一个可用管理员账号。")
    config["users"] = remaining_users
    save_auth_config(config)
    return user


def reset_auth_user_password(username: str, password: str) -> dict[str, Any]:
    config = read_auth_config()
    if not config:
        raise ValueError("认证配置不存在。")
    if config.get("mode") == "env":
        raise ValueError("环境变量账号模式下不能重置页面账号密码。")
    user = find_auth_user(config, clean_auth_username(username))
    if not user:
        raise ValueError("账号不存在。")
    rotate_auth_user_password(user, password)
    save_auth_config(config)
    return user


def change_auth_user_password(username: str, current_password: object, new_password: object) -> dict[str, Any]:
    config = read_auth_config()
    if not config:
        raise ValueError("认证配置不存在。")
    if config.get("mode") == "env":
        raise ValueError("环境变量账号模式下请在服务器环境变量中修改密码。")
    username = clean_auth_username(username)
    current_password_text = clean_auth_password(current_password)
    new_password_text = clean_auth_password(new_password)
    if current_password_text == new_password_text:
        raise ValueError("新密码不能和当前密码相同。")
    if not verify_auth_password(config, username, current_password_text):
        raise ValueError("当前密码不正确。")
    user = find_auth_user(config, username)
    if not user:
        raise ValueError("账号不存在。")
    rotate_auth_user_password(user, new_password_text)
    save_auth_config(config)
    return user


def clean_task_status(value: object, default: str = "assigned") -> str:
    status = str(value or default).strip()
    return status if status in EDITING_TASK_STATUS_FLOW else default


def clean_task_priority(value: object) -> str:
    priority = str(value or "normal").strip()
    return priority if priority in {"high", "normal", "low"} else "normal"


def clean_task_text(value: object, max_len: int = 160) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())[:max_len]


def clean_task_multiline(value: object, max_len: int = 4000) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)[:max_len]


def clean_task_due_at(value: object) -> str:
    due_at = clean_task_text(value, 40)
    if not due_at:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?", due_at):
        return due_at.replace("T", " ")
    return due_at[:40]


def clean_task_material_scope(value: object) -> str:
    scope = str(value or "current").strip()
    return scope if scope in {"current", "filtered", "all", "batch", "manual"} else "current"


def normalize_editing_task(value: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    try:
        assignee = clean_auth_username(value.get("assignee"))
    except ValueError:
        return None
    now = utc_now_iso()
    task_id = clean_material_id(value.get("id")) or f"task-{uuid.uuid4().hex[:12]}"
    title = clean_task_text(value.get("title"), 140)
    product_name = clean_task_text(value.get("productName"), 140)
    if not title:
        title = product_name or "未命名剪辑任务"
    status = clean_task_status(value.get("status"))
    return {
        "id": task_id,
        "title": title,
        "productName": product_name,
        "assignee": assignee,
        "status": status,
        "priority": clean_task_priority(value.get("priority")),
        "dueAt": clean_task_due_at(value.get("dueAt")),
        "materialScope": clean_task_material_scope(value.get("materialScope")),
        "batchId": clean_material_id(value.get("batchId")),
        "batchName": clean_task_text(value.get("batchName"), 120),
        "brief": clean_task_multiline(value.get("brief"), 4000),
        "script": clean_task_multiline(value.get("script"), 6000),
        "deliveryNote": clean_task_multiline(value.get("deliveryNote"), 3000),
        "resultUrl": clean_task_text(value.get("resultUrl"), 1000),
        "createdBy": clean_task_text(value.get("createdBy"), 80),
        "createdAt": str(value.get("createdAt") or now),
        "updatedAt": str(value.get("updatedAt") or now),
        "acceptedAt": str(value.get("acceptedAt") or ""),
        "submittedAt": str(value.get("submittedAt") or ""),
        "completedAt": str(value.get("completedAt") or ""),
        "revisionAt": str(value.get("revisionAt") or ""),
    }


def read_editing_tasks_payload() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if EDITING_TASKS_FILE.exists():
        try:
            data = json.loads(EDITING_TASKS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
    else:
        data = {}
    raw_tasks = data.get("tasks") if isinstance(data, dict) and isinstance(data.get("tasks"), list) else []
    tasks = [task for task in (normalize_editing_task(item) for item in raw_tasks) if task]
    return {
        "version": 1,
        "type": "seedance_editing_tasks",
        "updatedAt": str(data.get("updatedAt") or utc_now_iso()) if isinstance(data, dict) else utc_now_iso(),
        "tasks": tasks,
    }


def editing_task_status_counts(tasks: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in EDITING_TASK_STATUS_LABELS}
    for task in tasks:
        status = clean_task_status(task.get("status"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def editing_tasks_markdown(payload: dict[str, Any]) -> str:
    tasks = payload.get("tasks") if isinstance(payload.get("tasks"), list) else []
    counts = editing_task_status_counts(tasks)
    lines = [
        "---",
        "type: seedance_editing_task_board",
        f"updated_at: {payload.get('updatedAt')}",
        f"task_count: {len(tasks)}",
        "---",
        "",
        "# 剪辑任务看板",
        "",
        f"- 任务 JSON：`{obsidian_relative(EDITING_TASKS_FILE)}`",
        f"- 任务总数：{len(tasks)}",
        f"- 待接单：{counts.get('assigned', 0)}",
        f"- 制作中：{counts.get('in_progress', 0)}",
        f"- 待审核：{counts.get('review', 0)}",
        f"- 已完成：{counts.get('done', 0)}",
        "",
    ]
    if not tasks:
        lines.append("暂无剪辑任务。")
        return "\n".join(lines) + "\n"
    for status, label in EDITING_TASK_STATUS_LABELS.items():
        status_tasks = [task for task in tasks if clean_task_status(task.get("status")) == status]
        if not status_tasks:
            continue
        lines.extend(["", f"## {label}", ""])
        for task in sorted(status_tasks, key=lambda item: str(item.get("updatedAt") or ""), reverse=True):
            product = f" / {task.get('productName')}" if task.get("productName") else ""
            due = f" / 截止 {task.get('dueAt')}" if task.get("dueAt") else ""
            scope = task.get("batchName") or task.get("batchId") or task.get("materialScope") or "未指定素材范围"
            lines.append(f"- **{task.get('title')}{product}**：@{task.get('assignee')} / {scope}{due}")
            if task.get("brief"):
                lines.append(f"  - 要求：{task.get('brief').splitlines()[0][:120]}")
            if task.get("resultUrl"):
                lines.append(f"  - 成片：{task.get('resultUrl')}")
    return "\n".join(lines) + "\n"


def write_editing_tasks_payload(payload: dict[str, Any]) -> dict[str, Any]:
    tasks = [task for task in (normalize_editing_task(item) for item in payload.get("tasks", [])) if task]
    normalized = {
        "version": 1,
        "type": "seedance_editing_tasks",
        "updatedAt": utc_now_iso(),
        "statusLabels": EDITING_TASK_STATUS_LABELS,
        "tasks": tasks,
    }
    write_obsidian_json(EDITING_TASKS_FILE, normalized)
    EDITING_TASKS_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    EDITING_TASKS_REPORT_FILE.write_text(editing_tasks_markdown(normalized), encoding="utf-8")
    sync_obsidian_project_data()
    return normalized


def clean_copy_library_text(value: object, maximum: int, *, multiline: bool = False) -> str:
    text = str(value or "").strip()
    if not multiline:
        text = re.sub(r"\s+", " ", text)
    if len(text) > maximum:
        text = text[:maximum].rstrip()
    return text


def clean_copy_library_tags(value: object) -> list[str]:
    if isinstance(value, list):
        raw_values = value
    else:
        raw_values = re.split(r"[，,、\n\r]+", str(value or ""))
    tags: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        tag = clean_copy_library_text(raw, 24).lstrip("#")
        key = tag.lower()
        if tag and key not in seen:
            seen.add(key)
            tags.append(tag)
        if len(tags) >= 12:
            break
    return tags


def clean_copy_library_duration(value: object) -> int:
    try:
        duration = int(value or 15)
    except (TypeError, ValueError):
        duration = 15
    return max(3, min(duration, 180))


def clean_copy_library_metric(value: object) -> int:
    try:
        metric = int(value or 0)
    except (TypeError, ValueError):
        metric = 0
    return max(0, min(metric, 100_000_000))


def clean_copy_library_score(value: object, default: int = 0) -> int:
    try:
        score = int(float(value if value is not None else default))
    except (TypeError, ValueError):
        score = default
    return max(0, min(score, 100))


def normalize_video_copy_analysis(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw_segments = value.get("segments") if isinstance(value.get("segments"), list) else []
    segments: list[dict[str, Any]] = []
    cursor = 0.0
    for index, raw in enumerate(raw_segments[:24]):
        if not isinstance(raw, dict):
            continue
        text = clean_copy_library_text(raw.get("text") or raw.get("narration"), 1000, multiline=True)
        if not text:
            continue
        try:
            start_sec = max(0.0, float(raw.get("startSec") if raw.get("startSec") is not None else cursor))
        except (TypeError, ValueError):
            start_sec = cursor
        try:
            end_sec = float(raw.get("endSec") if raw.get("endSec") is not None else start_sec + 3)
        except (TypeError, ValueError):
            end_sec = start_sec + 3
        end_sec = max(start_sec + 0.5, min(end_sec, 180.0))
        role = str(raw.get("role") or "product_intro").strip()
        if role not in COPY_LIBRARY_STAGE_LABELS:
            role = "product_intro"
        segments.append(
            {
                "index": index,
                "startSec": round(start_sec, 2),
                "endSec": round(end_sec, 2),
                "text": text,
                "role": role,
                "shotType": clean_copy_library_text(raw.get("shotType"), 100) or "产品相关画面",
                "materialTags": clean_copy_library_tags(raw.get("materialTags") or raw.get("tags")),
                "reason": clean_copy_library_text(raw.get("reason"), 300),
            }
        )
        cursor = end_sec
    return {
        "score": clean_copy_library_score(value.get("score")),
        "hookScore": clean_copy_library_score(value.get("hookScore")),
        "pacingScore": clean_copy_library_score(value.get("pacingScore")),
        "materialMatchScore": clean_copy_library_score(value.get("materialMatchScore")),
        "summary": clean_copy_library_text(value.get("summary"), 600, multiline=True),
        "segments": segments,
        "missingShots": [clean_copy_library_text(item, 180) for item in value.get("missingShots", [])[:12] if clean_copy_library_text(item, 180)] if isinstance(value.get("missingShots"), list) else [],
        "suggestions": [clean_copy_library_text(item, 260) for item in value.get("suggestions", [])[:12] if clean_copy_library_text(item, 260)] if isinstance(value.get("suggestions"), list) else [],
        "model": clean_copy_library_text(value.get("model"), 160),
        "updatedAt": str(value.get("updatedAt") or ""),
    }


def normalize_video_copy_entry(value: dict[str, Any], *, default_created_by: str = "") -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    now = utc_now_iso()
    script = clean_copy_library_text(value.get("script"), 12000, multiline=True)
    if not script:
        return None
    title = clean_copy_library_text(value.get("title"), 120)
    stage = str(value.get("stage") or "full_script").strip()
    if stage not in COPY_LIBRARY_STAGE_LABELS:
        stage = "full_script"
    status = str(value.get("status") or "collected").strip()
    if status not in COPY_LIBRARY_STATUS_LABELS:
        status = "collected"
    raw_performance = value.get("performance") if isinstance(value.get("performance"), dict) else {}
    return {
        "id": clean_material_id(value.get("id")) or f"copy-{uuid.uuid4().hex[:12]}",
        "title": title or "未命名视频文案",
        "product": clean_copy_library_text(value.get("product"), 80),
        "market": clean_copy_library_text(value.get("market"), 60) or "日本",
        "language": clean_copy_library_text(value.get("language"), 40) or "ja-JP",
        "stage": stage,
        "style": clean_copy_library_text(value.get("style"), 60) or "自然种草",
        "duration": clean_copy_library_duration(value.get("duration")),
        "status": status,
        "tags": clean_copy_library_tags(value.get("tags")),
        "source": clean_copy_library_text(value.get("source"), 300),
        "script": script,
        "notes": clean_copy_library_text(value.get("notes"), 1200, multiline=True),
        "performance": {
            "views": clean_copy_library_metric(raw_performance.get("views")),
            "orders": clean_copy_library_metric(raw_performance.get("orders")),
            "saves": clean_copy_library_metric(raw_performance.get("saves")),
        },
        "analysis": normalize_video_copy_analysis(value.get("analysis")),
        "createdBy": clean_copy_library_text(value.get("createdBy"), 80) or default_created_by,
        "createdAt": str(value.get("createdAt") or now),
        "updatedAt": str(value.get("updatedAt") or now),
    }


def default_video_copy_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": "copy-template-jp-hook",
            "title": "15 秒女装 · 前 3 秒上身钩子",
            "product": "女装裤装",
            "market": "日本",
            "language": "ja-JP",
            "stage": "hook",
            "style": "自然种草",
            "duration": 15,
            "status": "template",
            "tags": ["15秒", "开头钩子", "上身效果", "日系女装"],
            "source": "SOSOVE 高互动结构模板",
            "script": "0-3秒｜え、これ履くだけでシルエットがこんなにすっきり見えるの？\n3-8秒｜ウエストまわりはすっきり、脚まわりはゆとりがあるから、普段使いしやすいんです。\n8-15秒｜トップスを変えるだけで雰囲気も変わるので、気になる方はぜひチェックしてみて。",
            "notes": "镜头顺序：整体上身 → 腰头/口袋细节 → 走动或换搭配。先用整体变化建立停留，再补细节。",
        },
        {
            "id": "copy-template-detail-proof",
            "title": "15 秒细节特写 · 卖点证明结构",
            "product": "服装细节款",
            "market": "日本",
            "language": "ja-JP",
            "stage": "detail_proof",
            "style": "细节证明",
            "duration": 15,
            "status": "template",
            "tags": ["细节特写", "卖点证明", "面料", "15秒"],
            "source": "SOSOVE 高互动结构模板",
            "script": "0-3秒｜近くで見ると、このディテールが本当にかわいい。\n3-9秒｜斜めに入ったデザインと使いやすいポケットで、シンプルなトップスに合わせてもポイントになります。\n9-15秒｜生地の落ち感もきれいなので、動いたときのシルエットまで楽しめます。",
            "notes": "准备腰头、纽扣、口袋、面料、走动垂坠五类镜头；每句对应一个清晰特写。",
        },
        {
            "id": "copy-template-outfit-cta",
            "title": "15 秒穿搭场景 · 自然收尾结构",
            "product": "通勤休闲女装",
            "market": "日本",
            "language": "ja-JP",
            "stage": "outfit",
            "style": "生活化推荐",
            "duration": 15,
            "status": "template",
            "tags": ["穿搭场景", "通勤", "收尾引导", "15秒"],
            "source": "SOSOVE 高互动结构模板",
            "script": "0-4秒｜今日はシンプルなトップスに合わせてみました。\n4-10秒｜きれいめにもカジュアルにも寄せやすいから、朝コーデに迷った日にも使いやすいです。\n10-15秒｜気になったら、手持ちのトップスと合わせるイメージで見てみてください。",
            "notes": "镜头顺序：全身搭配 → 坐立/走动 → 换上衣或配饰 → 商品与穿搭全景收尾。",
        },
    ]


def normalize_video_copy_library(value: dict[str, Any]) -> dict[str, Any]:
    raw_items = value.get("items") if isinstance(value, dict) and isinstance(value.get("items"), list) else []
    entries = [entry for entry in (normalize_video_copy_entry(item) for item in raw_items) if entry]
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for entry in entries:
        if entry["id"] in seen:
            continue
        seen.add(entry["id"])
        items.append(entry)
    items.sort(key=lambda item: str(item.get("updatedAt") or ""), reverse=True)
    return {
        "version": 1,
        "type": "seedance_video_copy_library",
        "updatedAt": str(value.get("updatedAt") or utc_now_iso()) if isinstance(value, dict) else utc_now_iso(),
        "stageLabels": COPY_LIBRARY_STAGE_LABELS,
        "statusLabels": COPY_LIBRARY_STATUS_LABELS,
        "items": items,
    }


def video_copy_library_markdown(library: dict[str, Any]) -> str:
    items = library.get("items") if isinstance(library.get("items"), list) else []
    lines = [
        "# 视频文案库",
        "",
        f"> 已收录 {len(items)} 条文案 · 最近更新 {library.get('updatedAt') or ''}",
        "",
    ]
    for item in items:
        stage = COPY_LIBRARY_STAGE_LABELS.get(item.get("stage"), item.get("stage") or "完整脚本")
        status = COPY_LIBRARY_STATUS_LABELS.get(item.get("status"), item.get("status") or "已收藏")
        tags = " · ".join(f"#{tag}" for tag in item.get("tags", [])) or "未打标签"
        analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else {}
        analysis_text = f" · AI {analysis.get('score')} 分 · {len(analysis.get('segments') or [])} 个分镜" if analysis.get("score") else ""
        lines.extend(
            [
                f"## {item.get('title') or '未命名视频文案'}",
                f"- 阶段：{stage} · {item.get('duration') or 15} 秒 · {status}{analysis_text}",
                f"- 市场：{item.get('market') or ''} · {item.get('language') or ''} · {item.get('style') or ''}",
                f"- 标签：{tags}",
                f"- 来源：{item.get('source') or '未填写'}",
                "- 文案：",
                *[f"  > {line}" for line in str(item.get("script") or "").splitlines()],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_video_copy_library(library: dict[str, Any]) -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    normalized = normalize_video_copy_library(library)
    normalized["updatedAt"] = utc_now_iso()
    write_obsidian_json(VIDEO_COPY_LIBRARY_FILE, normalized)
    VIDEO_COPY_LIBRARY_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    VIDEO_COPY_LIBRARY_INDEX_FILE.write_text(video_copy_library_markdown(normalized), encoding="utf-8")
    sync_obsidian_project_data()
    return normalized


def read_video_copy_library() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if not VIDEO_COPY_LIBRARY_FILE.exists():
        return write_video_copy_library({"items": default_video_copy_templates()})
    try:
        data = json.loads(VIDEO_COPY_LIBRARY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return normalize_video_copy_library({})
    return normalize_video_copy_library(data if isinstance(data, dict) else {})


def create_video_copy_entry(payload: dict[str, Any], created_by: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    library = read_video_copy_library()
    candidate = dict(payload or {})
    candidate["id"] = f"copy-{uuid.uuid4().hex[:12]}"
    candidate["createdBy"] = created_by
    candidate["createdAt"] = utc_now_iso()
    candidate["updatedAt"] = utc_now_iso()
    entry = normalize_video_copy_entry(candidate, default_created_by=created_by)
    if not entry:
        raise ValueError("请填写需要保存的视频文案。")
    library["items"] = [entry, *(library.get("items") or [])]
    return write_video_copy_library(library), entry


def update_video_copy_entry(payload: dict[str, Any], updated_by: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    copy_id = clean_material_id(payload.get("id"))
    if not copy_id:
        raise ValueError("缺少需要更新的文案编号。")
    library = read_video_copy_library()
    current = next((item for item in library.get("items", []) if item.get("id") == copy_id), None)
    if not current:
        raise ValueError("未找到这条视频文案。")
    candidate = {**current, **payload, "id": copy_id, "createdAt": current.get("createdAt"), "createdBy": current.get("createdBy"), "updatedAt": utc_now_iso()}
    entry = normalize_video_copy_entry(candidate, default_created_by=updated_by)
    if not entry:
        raise ValueError("请填写需要保存的视频文案。")
    library["items"] = [entry if item.get("id") == copy_id else item for item in library.get("items", [])]
    return write_video_copy_library(library), entry


def delete_video_copy_entry(payload: dict[str, Any]) -> dict[str, Any]:
    copy_id = clean_material_id(payload.get("id"))
    if not copy_id:
        raise ValueError("缺少需要删除的文案编号。")
    library = read_video_copy_library()
    items = [item for item in library.get("items", []) if item.get("id") != copy_id]
    if len(items) == len(library.get("items", [])):
        raise ValueError("未找到这条视频文案。")
    library["items"] = items
    return write_video_copy_library(library)


def analyze_video_copy_entry(payload: dict[str, Any], analyzed_by: str = "") -> dict[str, Any]:
    script = clean_copy_library_text(payload.get("script"), 12000, multiline=True)
    if not script:
        raise ValueError("请先填写需要拆解的视频文案。")
    runtime_config = read_runtime_config()
    model = get_ai_model(runtime_config)
    if not get_ai_api_key(runtime_config):
        raise AiError(HTTPStatus.BAD_REQUEST, "请先配置 AI 提示词模型 API Key。")
    duration = clean_copy_library_duration(payload.get("duration"))
    system_prompt = (
        "你是一名有 20 年经验的日本女装短视频剪辑导演和广告文案策划。"
        "请把用户的视频口播文案拆成可执行的逐句分镜计划，用于从已有视频素材库匹配镜头。"
        "分析开头钩子、节奏、卖点顺序、镜头可匹配性和素材缺口。"
        "每个分镜必须给出开始秒、结束秒、对应文案、文案角色、推荐镜头类型、素材搜索标签和匹配原因。"
        "role 只使用 hook、pain_point、product_intro、detail_proof、outfit、cta。"
        "时间段按目标时长连续分配，不要重叠；素材标签应是可用于视频素材库检索的短词。"
        "保持产品事实，不添加源文案没有提到的功效或承诺。"
        "只返回一个有效 JSON 对象，字段为 score、hookScore、pacingScore、materialMatchScore、summary、segments、missingShots、suggestions。"
        "四个分数均为 0-100 整数。segments 每项包含 startSec、endSec、text、role、shotType、materialTags、reason。"
    )
    context = {
        "title": clean_copy_library_text(payload.get("title"), 120),
        "product": clean_copy_library_text(payload.get("product"), 80),
        "market": clean_copy_library_text(payload.get("market"), 60) or "日本",
        "language": clean_copy_library_text(payload.get("language"), 40) or "ja-JP",
        "style": clean_copy_library_text(payload.get("style"), 60) or "自然种草",
        "targetDurationSec": duration,
        "script": script,
    }
    response = call_ai_chat(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False, indent=2)},
            ],
            "temperature": 0.25,
            "max_tokens": max(1600, min(get_ai_max_tokens(runtime_config), 3200)),
        },
        timeout_seconds=parse_int_env("AI_TIMEOUT_SECONDS", 120),
        config=runtime_config,
    )
    raw = extract_ai_text(response).strip()
    if not raw:
        raise AiError(HTTPStatus.BAD_GATEWAY, "文案拆解模型返回了空内容。")
    analysis = normalize_video_copy_analysis(
        {
            **parse_json_object(raw),
            "model": model,
            "updatedAt": utc_now_iso(),
        }
    )
    if not analysis.get("segments"):
        raise AiError(HTTPStatus.BAD_GATEWAY, "文案拆解结果中没有可用分镜。")
    result: dict[str, Any] = {"analysis": analysis, "library": None, "entry": None}
    copy_id = clean_material_id(payload.get("id"))
    if not copy_id:
        return result
    library = read_video_copy_library()
    current = next((item for item in library.get("items", []) if item.get("id") == copy_id), None)
    if not current:
        raise ValueError("未找到需要保存分析结果的视频文案。")
    candidate = {
        **current,
        "analysis": analysis,
        "updatedAt": utc_now_iso(),
    }
    entry = normalize_video_copy_entry(candidate, default_created_by=analyzed_by)
    library["items"] = [entry if item.get("id") == copy_id else item for item in library.get("items", [])]
    result["library"] = write_video_copy_library(library)
    result["entry"] = entry
    return result


def editing_task_visible(task: dict[str, Any], user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    if user.get("role") == "admin":
        return True
    return str(task.get("assignee") or "").lower() == str(user.get("username") or "").lower()


def public_editing_task(task: dict[str, Any]) -> dict[str, Any]:
    public = dict(task)
    public["status"] = clean_task_status(public.get("status"))
    public["statusLabel"] = EDITING_TASK_STATUS_LABELS.get(public["status"], public["status"])
    public["priority"] = clean_task_priority(public.get("priority"))
    return public


def editing_tasks_for_user(user: dict[str, Any] | None) -> list[dict[str, Any]]:
    tasks = read_editing_tasks_payload().get("tasks", [])
    visible = [public_editing_task(task) for task in tasks if editing_task_visible(task, user)]
    return sorted(visible, key=lambda item: str(item.get("updatedAt") or item.get("createdAt") or ""), reverse=True)


def find_task_index(tasks: list[dict[str, Any]], task_id: str) -> int:
    for index, task in enumerate(tasks):
        if task.get("id") == task_id:
            return index
    return -1


def create_editing_task(payload: dict[str, Any], created_by: str) -> dict[str, Any]:
    config = read_auth_config()
    assignee = clean_auth_username(payload.get("assignee"))
    assignee_user = find_auth_user(config, assignee) if config else None
    if not assignee_user or assignee_user.get("role") != "customer" or not assignee_user.get("enabled", True):
        raise ValueError("请选择一个已启用的客户账号。")
    title = clean_task_text(payload.get("title"), 140)
    product_name = clean_task_text(payload.get("productName"), 140)
    brief = clean_task_multiline(payload.get("brief"), 4000)
    script = clean_task_multiline(payload.get("script"), 6000)
    if not title and not product_name:
        raise ValueError("请填写任务标题或产品名。")
    if not brief and not script:
        raise ValueError("请填写剪辑要求或脚本文案。")
    now = utc_now_iso()
    task = normalize_editing_task(
        {
            "id": f"task-{uuid.uuid4().hex[:12]}",
            "title": title or f"{product_name} 剪辑任务",
            "productName": product_name,
            "assignee": assignee,
            "status": "assigned",
            "priority": payload.get("priority"),
            "dueAt": payload.get("dueAt"),
            "materialScope": payload.get("materialScope"),
            "batchId": payload.get("batchId"),
            "batchName": payload.get("batchName"),
            "brief": brief,
            "script": script,
            "createdBy": created_by,
            "createdAt": now,
            "updatedAt": now,
        }
    )
    if not task:
        raise ValueError("任务数据无效。")
    current = read_editing_tasks_payload()
    current["tasks"] = [task, *current.get("tasks", [])]
    saved = write_editing_tasks_payload(current)
    return public_editing_task(saved["tasks"][0])


def update_editing_task(payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    task_id = clean_material_id(payload.get("id") or payload.get("taskId"))
    if not task_id:
        raise ValueError("缺少任务 ID。")
    current = read_editing_tasks_payload()
    tasks = current.get("tasks", [])
    index = find_task_index(tasks, task_id)
    if index < 0:
        raise ValueError("任务不存在。")
    task = tasks[index]
    is_admin = user.get("role") == "admin"
    if not is_admin and not editing_task_visible(task, user):
        raise ValueError("只能更新自己的剪辑任务。")

    now = utc_now_iso()
    previous_status = clean_task_status(task.get("status"))
    if "status" in payload:
        task["status"] = clean_task_status(payload.get("status"), previous_status)
    if "deliveryNote" in payload:
        task["deliveryNote"] = clean_task_multiline(payload.get("deliveryNote"), 3000)
    if "resultUrl" in payload:
        task["resultUrl"] = clean_task_text(payload.get("resultUrl"), 1000)

    if is_admin:
        for field, cleaner in {
            "title": lambda value: clean_task_text(value, 140),
            "productName": lambda value: clean_task_text(value, 140),
            "priority": clean_task_priority,
            "dueAt": clean_task_due_at,
            "materialScope": clean_task_material_scope,
            "batchId": clean_material_id,
            "batchName": lambda value: clean_task_text(value, 120),
            "brief": lambda value: clean_task_multiline(value, 4000),
            "script": lambda value: clean_task_multiline(value, 6000),
        }.items():
            if field in payload:
                task[field] = cleaner(payload.get(field))
        if "assignee" in payload:
            assignee = clean_auth_username(payload.get("assignee"))
            assignee_user = find_auth_user(read_auth_config(), assignee)
            if not assignee_user or assignee_user.get("role") != "customer" or not assignee_user.get("enabled", True):
                raise ValueError("请选择一个已启用的客户账号。")
            task["assignee"] = assignee

    status = clean_task_status(task.get("status"))
    if status != previous_status:
        if status == "in_progress" and not task.get("acceptedAt"):
            task["acceptedAt"] = now
        if status == "review":
            task["submittedAt"] = now
        if status == "done":
            task["completedAt"] = now
        if status == "revision":
            task["revisionAt"] = now
    task["updatedAt"] = now
    tasks[index] = task
    saved = write_editing_tasks_payload(current)
    return public_editing_task(saved["tasks"][index])


def verify_auth_password(config: dict[str, Any], username: str, password: str) -> bool:
    if config.get("mode") == "env":
        env_username = str(config.get("username") or "")
        return hmac.compare_digest(env_username, username) and hmac.compare_digest(str(config.get("password") or ""), password)
    user = find_auth_user(config, username)
    if not user or not user.get("enabled", True):
        return False
    try:
        salt = b64decode_url(str(user.get("passwordSalt") or ""))
        iterations = int(user.get("iterations") or PASSWORD_HASH_ITERATIONS)
    except (TypeError, ValueError, binascii.Error):
        return False
    expected = str(user.get("passwordHash") or "")
    actual = password_hash(password, salt, iterations)
    return hmac.compare_digest(expected, actual)


def authenticate_auth_user(config: dict[str, Any], username: str, password: str) -> dict[str, Any] | None:
    if not verify_auth_password(config, username, password):
        return None
    return find_auth_user(config, username)


def create_session_token(username: str, config: dict[str, Any]) -> str:
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    user = find_auth_user(config, username)
    try:
        session_version = int(user.get("sessionVersion") or 0) if user else 0
    except (TypeError, ValueError):
        session_version = 0
    body = b64encode_url(
        json.dumps(
            {"u": username, "exp": expires_at, "n": secrets_token(12), "sv": session_version},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    secret = str(config.get("sessionSecret") or read_or_create_session_secret()).encode("utf-8")
    signature = b64encode_url(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{signature}"


def verify_session_token(token: str) -> str:
    user = verify_session_user(token)
    return str(user.get("username") or "") if user else ""


def verify_session_user(token: str) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    config = read_auth_config()
    if not config:
        return None
    body, signature = token.split(".", 1)
    secret = str(config.get("sessionSecret") or read_or_create_session_secret()).encode("utf-8")
    expected = b64encode_url(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(b64decode_url(body).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    username = str(payload.get("u") or "")
    expires_at = int(payload.get("exp") or 0)
    if expires_at < int(time.time()):
        return None
    user = find_auth_user(config, username)
    if not user or not user.get("enabled", True):
        return None
    try:
        token_session_version = int(payload.get("sv") or 0)
        user_session_version = int(user.get("sessionVersion") or 0)
    except (TypeError, ValueError):
        return None
    if token_session_version != user_session_version:
        return None
    return user


def build_auth_cookie(token: str) -> str:
    parts = [
        f"{SESSION_COOKIE_NAME}={token}",
        "Path=/",
        "HttpOnly",
        "SameSite=Lax",
        f"Max-Age={SESSION_TTL_SECONDS}",
    ]
    if os.environ.get("SEEDANCE_AUTH_SECURE_COOKIE") == "1":
        parts.append("Secure")
    return "; ".join(parts)


def clear_auth_cookie() -> str:
    return f"{SESSION_COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"


def auth_status_for(username: str = "") -> dict[str, Any]:
    config = read_auth_config()
    user = find_auth_user(config, username) if username and config else None
    role = clean_auth_role(user.get("role"), "customer") if user else ""
    return {
        "authenticated": bool(user),
        "setupRequired": config is None,
        "username": str(user.get("username") or "") if user else "",
        "displayName": clean_auth_display_name(user.get("displayName"), str(user.get("username") or "")) if user else "",
        "role": role,
        "canManageUsers": role == "admin",
        "userCount": len(auth_users(config)),
        "sessionTtlSeconds": SESSION_TTL_SECONDS,
    }


def client_attempt_key(handler: BaseHTTPRequestHandler) -> str:
    host = handler.client_address[0] if handler.client_address else "unknown"
    return str(host or "unknown")


def is_login_rate_limited(key: str) -> bool:
    now = time.time()
    recent = [item for item in LOGIN_ATTEMPTS.get(key, []) if now - item < LOGIN_RATE_LIMIT_WINDOW_SECONDS]
    LOGIN_ATTEMPTS[key] = recent
    return len(recent) >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def record_login_failure(key: str) -> None:
    now = time.time()
    LOGIN_ATTEMPTS[key] = [item for item in LOGIN_ATTEMPTS.get(key, []) if now - item < LOGIN_RATE_LIMIT_WINDOW_SECONDS]
    LOGIN_ATTEMPTS[key].append(now)


def clear_login_failures(key: str) -> None:
    LOGIN_ATTEMPTS.pop(key, None)


def generate_ad_forge_storyboard(project: dict[str, Any]) -> tuple[list[dict[str, Any]], str, str]:
    fallback = ad_forge.build_fallback_storyboard(project)
    if not get_ai_api_key():
        return fallback, "fallback", "AI 提示词接口尚未配置，已使用本地导演模板。"
    try:
        response = call_ai_chat(
            {
                "model": get_ai_model(),
                "messages": ad_forge.build_storyboard_messages(project),
                "temperature": 0.45,
                "max_tokens": 2600,
            },
            timeout_seconds=parse_int_env("AD_FORGE_AI_TIMEOUT_SECONDS", 120),
        )
        raw = extract_ai_text(response).strip()
        parsed = ad_forge.extract_json_object(raw)
        if not raw or not isinstance(parsed.get("shots"), list):
            return fallback, "fallback", "AI 返回格式不完整，已使用本地导演模板。"
        return ad_forge.parse_storyboard_response(raw, project), "ai", ""
    except (AiError, OSError, ValueError) as exc:
        return fallback, "fallback", f"AI 分镜暂不可用，已使用本地导演模板：{str(exc)[:240]}"


def generate_ad_forge_skill_prompts(project: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    product_description = ad_forge.clean_text(project.get("productDescription"), ad_forge.TEXT_LIMIT)
    if not product_description:
        raise ad_forge.InvalidProject("请先填写产品描述，再使用 Seedance Skill 生成双提示词。")

    runtime_config = read_runtime_config()
    model = get_ai_model(runtime_config)
    if not get_ai_api_key(runtime_config):
        raise AiError(HTTPStatus.BAD_REQUEST, "请先配置 AI 提示词模型 API Key。")

    skill_context, skill_files = load_ad_forge_prompt_skill_context()
    skill_status = build_seedance_review_skill_status()
    settings = ad_forge.normalize_settings(project.get("settings"))
    brief = ad_forge.normalize_brief(project.get("brief"))
    context = {
        "surface": "Volcengine Ark / Seedance 2.0",
        "skill": {"name": skill_status.get("name"), "version": skill_status.get("version")},
        "productName": ad_forge.clean_text(project.get("productName"), 240),
        "productDescription": product_description,
        "existingBrief": brief,
        "targetMarket": settings["market"],
        "contentLanguage": settings["language"],
        "platform": settings["platform"],
        "videoRatio": settings["ratio"],
        "imageSize": ad_forge_image_size(settings["ratio"], settings["imageSize"]),
        "shotCount": settings["shotCount"],
        "totalDurationSeconds": settings["totalDuration"],
        "generateAudio": settings["generateAudio"],
        "style": settings["style"],
        "character": settings["character"],
        "lighting": settings["lighting"],
    }
    system_prompt = (
        f"你正在执行本机已安装的 {skill_status.get('name') or 'seedance-20'} "
        f"v{skill_status.get('version') or 'unknown'}，LOCAL SKILL CONTEXT 是必须遵守的运行规则。"
        "任务是把真实产品描述编排成电商广告分镜，并为每个镜头同时生成一条图片提示词和一条 Seedance 2.0 视频提示词。"
        "先在内部完成 Director's Read：纯产品/功能证明使用非叙事路线；有人物表演时才使用叙事路线。"
        "每镜只承载一个可见证据、一个主要动作和一个主要运镜，保持人物、服装、商品、场景、光向连续。"
        "不得新增产品描述中没有的颜色、面料、结构、功效、价格、折扣、库存、品牌授权、身体效果或人物身份。"
        "图片提示词是单张关键帧：描述该镜最有证据力的静止瞬间、主体、构图、物理光源、材质和留白；"
        "不要写运动时间轴，不生成字幕、价格卡、水印或拼贴。"
        "视频提示词必须是可直接提交给 Seedance 的自然语言，包含主体与主要动作、场景、一个运镜及终点、"
        "物理光源、声音意图和保持约束；不要泄露 Director's Read 内部字段，不使用电影感、震撼、8K、专业级等空泛词。"
        "广告字幕和 CTA 文案只放在 copy 字段，生成画面保持无文字，便于后期编辑。"
        f"必须返回有效 JSON，shots 数组正好包含 {settings['shotCount']} 项。"
        "每项字段必须是 role、title、scene、camera、imagePrompt、videoPrompt、copy、duration。"
        "role 只允许 hook、problem、reveal、detail、proof、cta；duration 使用给定总时长的合理整数分配。"
        f"imagePrompt 使用清晰中文；videoPrompt 使用 {settings['language']}，必要的镜头术语可保留英文。"
        "只返回 JSON，不要 Markdown、解释、代码围栏或额外文本。\n\n"
        f"LOCAL SKILL CONTEXT:\n{skill_context}"
    )
    response = call_ai_chat(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False, indent=2)},
            ],
            "temperature": 0.25,
            "max_tokens": max(2800, min(get_ai_max_tokens(runtime_config), 4800)),
        },
        timeout_seconds=parse_int_env("AD_FORGE_SKILL_TIMEOUT_SECONDS", 180),
        config=runtime_config,
    )
    raw = extract_ai_text(response).strip()
    parsed = ad_forge.extract_json_object(raw)
    if not raw or not isinstance(parsed.get("shots"), list):
        raise AiError(HTTPStatus.BAD_GATEWAY, "Seedance Skill 没有返回有效的双提示词分镜，请重试。")
    shots = ad_forge.parse_storyboard_response(raw, project)
    return shots, {**skill_status, "files": skill_files}, model


def read_ad_forge_image_private_config() -> dict[str, Any]:
    if not AD_FORGE_IMAGE_CONFIG_FILE.exists():
        return {}
    try:
        payload = json.loads(AD_FORGE_IMAGE_CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def get_ad_forge_image_api_key(config: dict[str, Any] | None = None) -> str:
    private = read_ad_forge_image_private_config()
    runtime_value = str(get_config_section("imageGeneration", config).get("apiKey") or "").strip()
    configured = runtime_value or str(private.get("apiKey") or "").strip()
    return configured or os.environ.get("AD_FORGE_IMAGE_API_KEY", "").strip()


def get_ad_forge_image_model(config: dict[str, Any] | None = None) -> str:
    private = read_ad_forge_image_private_config()
    runtime_value = str(get_config_section("imageGeneration", config).get("model") or "").strip()
    configured = runtime_value or str(private.get("model") or "").strip()
    model = configured or os.environ.get("AD_FORGE_IMAGE_MODEL", DEFAULT_AD_FORGE_IMAGE_MODEL).strip()
    if not model or len(model) > 160 or not MODEL_ID_RE.fullmatch(model):
        return DEFAULT_AD_FORGE_IMAGE_MODEL
    return model


def get_ad_forge_image_base_url(config: dict[str, Any] | None = None) -> str:
    private = read_ad_forge_image_private_config()
    runtime_value = str(get_config_section("imageGeneration", config).get("baseUrl") or "").strip()
    configured = runtime_value or str(private.get("baseUrl") or "").strip()
    value = (configured or os.environ.get("AD_FORGE_IMAGE_API_BASE_URL", DEFAULT_AD_FORGE_IMAGE_BASE_URL)).strip().rstrip("/")
    parsed = urlparse(value)
    is_local_http = parsed.scheme == "http" and (parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}
    if (parsed.scheme != "https" and not is_local_http) or not parsed.netloc or parsed.username or parsed.password:
        raise AdForgeImageError(HTTPStatus.BAD_REQUEST, "生图服务地址必须使用 HTTPS（本机调试地址除外）。")
    return value


def build_ad_forge_image_endpoint() -> str:
    base_url = get_ad_forge_image_base_url()
    if base_url.endswith("/images/generations"):
        return base_url
    return f"{base_url}/images/generations"


def build_ad_forge_image_edit_endpoint() -> str:
    base_url = get_ad_forge_image_base_url()
    if base_url.endswith("/images/edits"):
        return base_url
    if base_url.endswith("/images/generations"):
        return f"{base_url.removesuffix('/images/generations')}/images/edits"
    return f"{base_url}/images/edits"


def clean_ad_forge_image_request_id(value: Any) -> str:
    request_id = ad_forge.clean_text(value, 100)
    if not re.fullmatch(r"img-[A-Za-z0-9_-]{12,96}", request_id):
        raise ad_forge.InvalidProject("生图请求标识无效。")
    return request_id


def register_ad_forge_image_request(
    request_id: Any,
    username: str,
    project_id: str,
    shot_id: str,
) -> threading.Event:
    clean_id = clean_ad_forge_image_request_id(request_id)
    event = threading.Event()
    with AD_FORGE_IMAGE_REQUEST_LOCK:
        if clean_id in AD_FORGE_IMAGE_REQUESTS:
            raise ad_forge.InvalidProject("生图请求标识重复，请重新提交。")
        AD_FORGE_IMAGE_REQUESTS[clean_id] = {
            "event": event,
            "username": str(username or ""),
            "projectId": str(project_id or ""),
            "shotId": str(shot_id or ""),
        }
    return event


def cancel_ad_forge_image_request(
    request_id: Any,
    username: str,
    project_id: str,
    shot_id: str,
) -> bool:
    clean_id = clean_ad_forge_image_request_id(request_id)
    with AD_FORGE_IMAGE_REQUEST_LOCK:
        request_state = AD_FORGE_IMAGE_REQUESTS.get(clean_id)
        if not request_state or any(
            request_state.get(key) != expected
            for key, expected in {
                "username": str(username or ""),
                "projectId": str(project_id or ""),
                "shotId": str(shot_id or ""),
            }.items()
        ):
            return False
        request_state["event"].set()
        return True


def finish_ad_forge_image_request(request_id: Any, event: threading.Event) -> None:
    clean_id = clean_ad_forge_image_request_id(request_id)
    with AD_FORGE_IMAGE_REQUEST_LOCK:
        request_state = AD_FORGE_IMAGE_REQUESTS.get(clean_id)
        if request_state and request_state.get("event") is event:
            AD_FORGE_IMAGE_REQUESTS.pop(clean_id, None)


def commit_ad_forge_image_request(request_id: Any, event: threading.Event) -> bool:
    clean_id = clean_ad_forge_image_request_id(request_id)
    with AD_FORGE_IMAGE_REQUEST_LOCK:
        request_state = AD_FORGE_IMAGE_REQUESTS.get(clean_id)
        if not request_state or request_state.get("event") is not event or event.is_set():
            return False
        AD_FORGE_IMAGE_REQUESTS.pop(clean_id, None)
        return True


def raise_if_ad_forge_image_cancelled(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise AdForgeImageCancelled()


def delete_saved_ad_forge_image(local_path: str, root: Path | None = None) -> None:
    prefix = "/ad-forge-images/"
    clean_path = str(local_path or "")
    if not clean_path.startswith(prefix):
        return
    image_root = (root or AD_FORGE_IMAGE_ROOT).resolve()
    target = (image_root / clean_path.removeprefix(prefix)).resolve()
    try:
        target.relative_to(image_root)
    except ValueError:
        return
    target.unlink(missing_ok=True)


def ad_forge_image_size(ratio: str, requested_size: str = "auto") -> str:
    requested = str(requested_size or "auto").strip()
    if requested in ad_forge.IMAGE_SIZES:
        return requested
    return {
        "9:16": "1024x1536",
        "16:9": "1536x1024",
        "1:1": "1024x1024",
    }.get(str(ratio or "9:16"), "1024x1536")


def build_ad_forge_image_prompt(project: dict[str, Any], shot: dict[str, Any]) -> str:
    settings = ad_forge.normalize_settings(project.get("settings"))
    image_size = ad_forge_image_size(settings.get("ratio"), settings.get("imageSize"))
    image_shape = {
        "1024x1536": "portrait",
        "1536x1024": "landscape",
        "1024x1024": "square",
    }[image_size]
    brief = ad_forge.normalize_brief(project.get("brief"))
    product_name = ad_forge.clean_text(project.get("productName"), 240)
    product_description = ad_forge.clean_text(project.get("productDescription"), 1800)
    title = ad_forge.clean_text(shot.get("title"), 120)
    scene = ad_forge.clean_text(shot.get("scene"), 1200)
    direction = ad_forge.clean_text(shot.get("imagePrompt") or shot.get("prompt"), 3600)
    if not any([product_name, title, scene, direction]):
        raise ad_forge.InvalidProject("当前镜头还没有可用于生图的描述。")
    selling_points = "、".join(brief.get("sellingPoints") or [])
    prompt = f"""Create one production-ready advertising storyboard keyframe as a single still image.
Product: {product_name or 'the product described in the shot'}
Product description: {product_description or 'use only the product facts supplied in this project'}
Shot: {title}
Scene and subject: {scene}
Direction: {direction}
Audience and market: {brief.get('audience') or 'general ecommerce audience'} / {settings.get('market')}
Visual direction: {settings.get('style')}; {settings.get('lighting')}; {settings.get('character')}
Product facts to preserve: {selling_points or 'preserve every visible product detail exactly as described'}
Composition: a {image_shape} {image_size} image canvas for a {settings.get('ratio')} target video, one coherent camera view, clear product evidence, natural anatomy, realistic materials and lighting.
Do not create a collage, split screen, watermark, logo, subtitle, price card, or baked-in text. Keep clean negative space for editable captions added later."""
    return prompt.strip()[:6000]


def resolve_ad_forge_reference_image_url(value: Any, project_id: str = "") -> Path:
    url = ad_forge.clean_url(value)
    path = unquote(urlparse(url).path).replace("\\", "/")
    if path.startswith("/uploads/images/"):
        target = resolve_upload_target("images", path.removeprefix("/uploads/images/"))
    elif path.startswith("/ad-forge-images/"):
        clean_path = path.removeprefix("/ad-forge-images/").lstrip("/")
        parts = [part for part in clean_path.split("/") if part]
        valid_filename = len(parts) == 2 and re.fullmatch(r"[A-Za-z0-9._-]+\.(png|jpg|webp)", parts[1], flags=re.IGNORECASE)
        if not valid_filename or not re.fullmatch(r"ad-[a-f0-9]{16}", parts[0]):
            raise FileNotFoundError("参考图片路径无效。")
        if project_id and parts[0] != project_id:
            raise FileNotFoundError("参考图片不属于当前项目。")
        image_root = AD_FORGE_IMAGE_ROOT.resolve()
        target = (image_root / parts[0] / parts[1]).resolve()
        try:
            target.relative_to(image_root)
        except ValueError as exc:
            raise FileNotFoundError("参考图片路径无效。") from exc
    else:
        item = find_material_entry_for_playback(url)
        if not item or clean_material_kind(item.get("kind"), url) != "image":
            raise FileNotFoundError("参考图片不是本机已登记素材。")
        source = resolve_material_source_path(item)
        if not source:
            raise FileNotFoundError("参考图片源文件不可用。")
        target = source.resolve()
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("参考图片源文件不可用。")
    return target


def resolve_ad_forge_image_reference_entries(
    project: dict[str, Any],
    shot: dict[str, Any],
) -> list[tuple[str, Path]]:
    mode = ad_forge.clean_text(shot.get("imageGenerationMode"), 30)
    mode = mode if mode in ad_forge.IMAGE_GENERATION_MODES else "auto"
    if mode == "prompt":
        return []
    shot_urls = [shot.get("referenceImage"), *(shot.get("referenceAssets") or [])]
    project_urls = list(project.get("referenceAssets") or [])
    candidates = [*shot_urls, *project_urls]
    candidates.sort(
        key=lambda item: (
            0
            if "/uploads/images/" in urlparse(str(item or "")).path
            else 2
            if "/ad-forge-images/" in urlparse(str(item or "")).path
            else 1
        )
    )
    resolved: list[tuple[str, Path, bool]] = []
    seen: set[str] = set()
    for url in candidates:
        if not url:
            continue
        try:
            path = resolve_ad_forge_reference_image_url(url, str(project.get("id") or ""))
        except (FileNotFoundError, ValueError):
            continue
        identity = os.path.normcase(str(path.resolve()))
        if identity in seen:
            continue
        seen.add(identity)
        is_generated = "/ad-forge-images/" in urlparse(str(url or "")).path
        resolved.append((ad_forge.clean_url(url), path, is_generated))
    source_references = [(url, path) for url, path, is_generated in resolved if not is_generated]
    generated_references = [(url, path) for url, path, is_generated in resolved if is_generated]
    if mode == "reference" and not source_references:
        raise ad_forge.InvalidProject("当前镜头缺少原始商品参考图。请先上传参考图或设为全片参考；强制参考模式不会使用 AI 关键帧代替原图。")
    return (source_references or generated_references)[:MAX_AD_FORGE_EDIT_REFERENCES]


def resolve_ad_forge_image_references(project: dict[str, Any], shot: dict[str, Any]) -> list[Path]:
    return [path for _url, path in resolve_ad_forge_image_reference_entries(project, shot)]


def build_ad_forge_product_lock_prompt(reference_count: int) -> str:
    reference_label = "image #1" if reference_count == 1 else f"images #1–#{reference_count}"
    return f"""PRODUCT LOCK — HIGHEST PRIORITY
The attached reference {reference_label} is the authoritative source for the physical product, not merely a style suggestion. Reuse that exact product; do not design a similar substitute.
For product category, neckline geometry and depth, sleeve cut and length, waist construction and width, seam and trim placement, silhouette, leg width, fabric texture, drape, length and proportions, the reference images override every conflicting sentence in the product description, scene or shot direction below.
Target-color rule: an explicit color in the shot direction may recolor the same SKU only; recoloring must not change its construction, texture or silhouette. If no target color is explicit, preserve the color of reference image #1. Never blend colors from multiple references.
Do not copy the reference person's biometric identity, accessories or background unless the shot explicitly requests them. The only allowed changes are model identity, pose, camera, crop, lighting, background and an explicit target color. Before rendering, visually check the garment against reference image #1 and correct any changed product feature."""


def read_ad_forge_reference_image(path: Path) -> tuple[str, str, bytes]:
    size = path.stat().st_size
    if size <= 0 or size > MAX_IMAGE_UPLOAD_BYTES:
        raise AdForgeImageError(HTTPStatus.BAD_REQUEST, "单张参考图片必须小于 10MB。")
    content = path.read_bytes()
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        content_type, suffix = "image/png", ".png"
    elif content.startswith(b"\xff\xd8\xff"):
        content_type, suffix = "image/jpeg", ".jpg"
    elif content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        content_type, suffix = "image/webp", ".webp"
    else:
        raise AdForgeImageError(HTTPStatus.BAD_REQUEST, "参考图片必须是 PNG、JPEG 或 WebP 文件。")
    safe_stem = re.sub(r"[^A-Za-z0-9_-]", "-", path.stem)[:60].strip("-") or "reference"
    return f"{safe_stem}{suffix}", content_type, content


def encode_ad_forge_multipart(fields: dict[str, str], images: list[Path]) -> tuple[bytes, str]:
    boundary = f"----SOSOVEAdForge{secrets.token_hex(16)}"
    chunks: list[bytes] = []
    total_image_bytes = 0
    for name, value in fields.items():
        safe_name = re.sub(r"[^A-Za-z0-9_-]", "", name)
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="{safe_name}"\r\n\r\n'.encode("ascii"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for image_path in images[:MAX_AD_FORGE_EDIT_REFERENCES]:
        filename, content_type, content = read_ad_forge_reference_image(image_path)
        total_image_bytes += len(content)
        if total_image_bytes > MAX_AD_FORGE_EDIT_TOTAL_BYTES:
            raise AdForgeImageError(HTTPStatus.BAD_REQUEST, "参考图片合计不能超过 32MB。")
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode("ascii"),
                f"Content-Type: {content_type}\r\n\r\n".encode("ascii"),
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def call_ad_forge_image_api(
    prompt: str,
    ratio: str,
    requested_size: str = "auto",
    reference_images: list[Path] | None = None,
) -> dict[str, Any]:
    api_key = get_ad_forge_image_api_key()
    if not api_key:
        raise AdForgeImageError(HTTPStatus.BAD_REQUEST, "生图服务密钥尚未配置。")
    body = {
        "model": get_ad_forge_image_model(),
        "prompt": ad_forge.clean_text(prompt, 6000),
        "n": 1,
        "size": ad_forge_image_size(ratio, requested_size),
        "quality": "auto",
        "response_format": "b64_json",
    }
    if not body["prompt"]:
        raise AdForgeImageError(HTTPStatus.BAD_REQUEST, "生图提示词不能为空。")
    images = list(reference_images or [])[:MAX_AD_FORGE_EDIT_REFERENCES]
    if images:
        request_data, content_type = encode_ad_forge_multipart(
            {key: str(value) for key, value in body.items() if key != "quality"},
            images,
        )
        endpoint = build_ad_forge_image_edit_endpoint()
    else:
        request_data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        content_type = "application/json"
        endpoint = build_ad_forge_image_endpoint()
    request = Request(
        endpoint,
        data=request_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=parse_int_env("AD_FORGE_IMAGE_TIMEOUT_SECONDS", 240)) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        message = read_error_message(exc)
        status = HTTPStatus(exc.code) if exc.code in HTTPStatus._value2member_map_ else HTTPStatus.BAD_GATEWAY
        raise AdForgeImageError(status, f"生图服务返回错误：{message[:600]}") from exc
    except URLError as exc:
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, f"无法连接生图服务：{exc.reason}") from exc
    except TimeoutError as exc:
        raise AdForgeImageError(HTTPStatus.GATEWAY_TIMEOUT, "生图等待超时，可以直接重试当前镜头。") from exc
    except OSError as exc:
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, f"生图连接失败：{str(exc)[:300]}") from exc
    except json.JSONDecodeError as exc:
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, "生图服务返回了无效 JSON。") from exc


def extract_ad_forge_image_bytes(response: dict[str, Any]) -> tuple[bytes, str]:
    data = response.get("data") if isinstance(response, dict) else None
    first = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
    encoded = first.get("b64_json") if isinstance(first, dict) else None
    if not isinstance(encoded, str) or not encoded.strip():
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, "生图服务没有返回 base64 图片数据。")
    if len(encoded) > (MAX_AD_FORGE_IMAGE_BYTES * 4 // 3) + 4096:
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, "生图结果超过 25MB 限制。")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, "生图服务返回了损坏的 base64 图片。") from exc
    if not content or len(content) > MAX_AD_FORGE_IMAGE_BYTES:
        raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, "生图结果为空或超过 25MB 限制。")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return content, ".png"
    if content.startswith(b"\xff\xd8\xff"):
        return content, ".jpg"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return content, ".webp"
    raise AdForgeImageError(HTTPStatus.BAD_GATEWAY, "生图服务返回的文件不是 PNG、JPEG 或 WebP。")


def save_ad_forge_image(project_id: str, shot_id: str, content: bytes, suffix: str, root: Path | None = None) -> str:
    if not re.fullmatch(r"ad-[a-f0-9]{16}", str(project_id or "")):
        raise ad_forge.InvalidProject("项目标识无效。")
    safe_shot_id = re.sub(r"[^A-Za-z0-9_-]", "-", str(shot_id or ""))[:80].strip("-")
    if not safe_shot_id or suffix not in {".png", ".jpg", ".webp"}:
        raise ad_forge.InvalidProject("分镜图片文件名无效。")
    image_root = (root or AD_FORGE_IMAGE_ROOT).resolve()
    target_dir = (image_root / project_id).resolve()
    try:
        target_dir.relative_to(image_root)
    except ValueError as exc:
        raise ad_forge.InvalidProject("分镜图片保存路径无效。") from exc
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{safe_shot_id}-{int(time.time())}-{uuid.uuid4().hex[:8]}{suffix}"
    target = target_dir / filename
    temporary = target.with_name(f".{filename}.tmp")
    temporary.write_bytes(content)
    temporary.replace(target)
    return f"/ad-forge-images/{project_id}/{filename}"


def generate_ad_forge_image(
    project: dict[str, Any],
    shot: dict[str, Any],
    root: Path | None = None,
    cancel_event: threading.Event | None = None,
) -> tuple[str, str, str, list[str]]:
    raise_if_ad_forge_image_cancelled(cancel_event)
    settings = ad_forge.normalize_settings(project.get("settings"))
    image_size = ad_forge_image_size(settings.get("ratio"), settings.get("imageSize"))
    prompt = build_ad_forge_image_prompt(project, shot)
    reference_entries = resolve_ad_forge_image_reference_entries(project, shot)
    reference_urls = [url for url, _path in reference_entries]
    reference_images = [path for _url, path in reference_entries]
    if reference_images:
        prompt = f"{build_ad_forge_product_lock_prompt(len(reference_images))}\n\nSHOT BRIEF\n{prompt}"[:6000]
    raise_if_ad_forge_image_cancelled(cancel_event)
    response = call_ad_forge_image_api(
        prompt,
        settings.get("ratio"),
        settings.get("imageSize"),
        reference_images=reference_images,
    )
    raise_if_ad_forge_image_cancelled(cancel_event)
    content, suffix = extract_ad_forge_image_bytes(response)
    raise_if_ad_forge_image_cancelled(cancel_event)
    local_path = save_ad_forge_image(str(project.get("id") or ""), str(shot.get("id") or ""), content, suffix, root)
    return local_path, prompt, image_size, reference_urls


def download_ad_forge_clip(url: str, target: Path, max_bytes: int = 700 * 1024 * 1024) -> None:
    with open_remote_import_url(url, headers={"Accept": "video/*,application/octet-stream"}) as response:
        content_length = str(response.headers.get("Content-Length") or "").strip()
        if content_length.isdigit() and int(content_length) > max_bytes:
            raise ValueError("单个视频片段超过 700MB，无法合成。")
        total = 0
        with target.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("单个视频片段超过 700MB，无法合成。")
                output.write(chunk)
        if total == 0:
            raise ValueError("下载到的视频片段为空。")


def run_ad_forge_ffmpeg(command: list[str], timeout_seconds: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        shell=False,
    )


def compose_ad_forge_project(project: dict[str, Any]) -> str:
    if not FFMPEG_BIN:
        raise RuntimeError("服务器未安装 FFmpeg，暂时无法合成视频。")
    clip_urls = ad_forge.composition_clips(project)
    project_id = str(project.get("id") or "")
    if not re.fullmatch(r"ad-[a-f0-9]{16}", project_id):
        raise ValueError("项目 ID 无效。")
    export_dir = (AD_FORGE_EXPORT_ROOT / project_id).resolve()
    export_root = AD_FORGE_EXPORT_ROOT.resolve()
    try:
        export_dir.relative_to(export_root)
    except ValueError as exc:
        raise ValueError("导出目录无效。") from exc
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"sosove-ad-lab-{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp4"
    output_path = export_dir / filename

    with tempfile.TemporaryDirectory(prefix="ad-forge-") as temp_dir:
        work_dir = Path(temp_dir)
        local_clips: list[Path] = []
        for index, url in enumerate(clip_urls, start=1):
            target = work_dir / f"clip-{index:02d}.mp4"
            download_ad_forge_clip(url, target)
            local_clips.append(target)
        concat_file = work_dir / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.as_posix()}'" for path in local_clips),
            encoding="utf-8",
        )
        copy_result = run_ad_forge_ffmpeg(
            [
                str(FFMPEG_BIN),
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        if copy_result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            encode_result = run_ad_forge_ffmpeg(
                [
                    str(FFMPEG_BIN),
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "20",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "160k",
                    "-movflags",
                    "+faststart",
                    str(output_path),
                ]
            )
            if encode_result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
                detail = (encode_result.stderr or copy_result.stderr or "FFmpeg 未返回错误信息")[-800:]
                output_path.unlink(missing_ok=True)
                raise RuntimeError(f"视频合成失败：{detail}")
    return f"/ad-forge-exports/{project_id}/{filename}"


class SeedanceHandler(BaseHTTPRequestHandler):
    server_version = "SeedanceWeb/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in {"/login", "/login.html"}:
            self.serve_static("login.html")
            return
        if path == "/healthz":
            self.send_json(
                {
                    "ok": True,
                    "service": "seedance-web",
                    "obsidianRoot": str(OBSIDIAN_MATERIAL_ROOT),
                    "runtimeDir": str(CONFIG_DIR),
                    "ffmpeg": bool(FFMPEG_BIN),
                    "ffprobe": bool(FFPROBE_BIN),
                }
            )
            return
        if path == "/api/auth/status":
            self.send_json({"ok": True, "auth": auth_status_for(self.authenticated_username())})
            return
        if self.is_public_static_path(path):
            self.serve_static(path.removeprefix("/static/"))
            return
        if not self.require_authentication(path):
            return

        if path in {"/", "/index.html"}:
            self.serve_static("index.html")
            return
        if path in {"/prompt-translate", "/prompt-translate.html"}:
            self.serve_static("prompt-translate.html")
            return
        if path in {"/accounts", "/accounts.html"}:
            if not self.require_admin():
                return
            self.serve_static("accounts.html")
            return
        if path in {"/copy-library", "/copy-library.html"}:
            self.serve_static("copy-library.html")
            return
        if path in {"/materials", "/materials.html"}:
            self.serve_static("materials.html")
            return
        if path in {"/chatcut", "/chatcut.html"}:
            self.serve_static("chatcut.html")
            return
        if path in {"/operations", "/operations.html"}:
            self.serve_static("operations.html")
            return
        if path in {"/editing-tasks", "/editing-tasks.html"}:
            self.serve_static("editing-tasks.html")
            return
        if path in {"/ad-forge", "/ad-forge.html"}:
            self.serve_static("ad-forge.html")
            return
        if path in {"/fashion-prompts", "/fashion-prompts.html"}:
            self.serve_static("fashion-prompts.html")
            return
        if path.startswith("/static/"):
            self.serve_static(path.removeprefix("/static/"))
            return
        if path == "/playback-material":
            self.serve_material_playback(parsed.query)
            return
        for kind in MATERIAL_UPLOAD_CONFIGS:
            prefix = f"/uploads/{kind}/"
            if path.startswith(prefix):
                self.serve_upload(kind, path.removeprefix(prefix))
                return
        if path == "/api/health":
            self.send_json(
                {
                    "ok": True,
                    "service": "seedance-web",
                    "hasApiKey": bool(get_api_key()),
                    "hasAiApiKey": bool(get_ai_api_key()),
                    "hasImageApiKey": bool(get_ad_forge_image_api_key()),
                    "model": get_default_model(),
                    "defaultModel": get_default_model(),
                    "arkEndpoint": get_ark_endpoint(),
                    "modelPresets": MODEL_PRESETS,
                    "aiModel": get_ai_model(),
                    "aiBaseUrl": get_ai_base_url(),
                    "imageModel": get_ad_forge_image_model(),
                    "skill": build_skill_status(),
                    "promptReviewSkill": build_seedance_review_skill_status(),
                    "ratios": sorted(VALID_RATIOS),
                    "durations": sorted(VALID_DURATIONS),
                    "minQuantity": MIN_QUANTITY,
                    "maxQuantity": MAX_QUANTITY,
                    "minPromptCount": MIN_PROMPT_COUNT,
                    "maxPromptCount": MAX_PROMPT_COUNT,
                }
            )
            return
        if path == "/api/auth/users":
            if not self.require_admin():
                return
            self.send_json({"ok": True, "users": [public_auth_user(user) for user in auth_users()], "auth": auth_status_for(self.authenticated_username())})
            return
        if path == "/api/editing-tasks":
            user = self.authenticated_user()
            is_admin = bool(user and user.get("role") == "admin")
            users = []
            if is_admin:
                users = [
                    public_auth_user(item)
                    for item in auth_users()
                    if item.get("role") == "customer" and item.get("enabled", True)
                ]
            self.send_json(
                {
                    "ok": True,
                    "tasks": editing_tasks_for_user(user),
                    "users": users,
                    "statusLabels": EDITING_TASK_STATUS_LABELS,
                    "auth": auth_status_for(self.authenticated_username()),
                    "obsidian": build_obsidian_status(),
                }
            )
            return
        if path == "/api/ad-forge/projects":
            user = self.authenticated_user()
            if not user:
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
                return
            is_admin = user.get("role") == "admin"
            query = parse_qs(parsed.query)
            include_archived = str((query.get("archived") or [""])[0]).lower() in {"1", "true", "yes"}
            projects = ad_forge.list_projects(
                AD_FORGE_PROJECTS_FILE,
                str(user.get("username") or ""),
                is_admin=is_admin,
                include_archived=include_archived,
            )
            self.send_json(
                {
                    "ok": True,
                    "projects": projects,
                    "auth": auth_status_for(self.authenticated_username()),
                    "capabilities": {
                        "ai": bool(get_ai_api_key()),
                        "aiModel": get_ai_model(),
                        "aiBaseUrl": get_ai_base_url(),
                        "imageGeneration": bool(get_ad_forge_image_api_key()),
                        "imageModel": get_ad_forge_image_model(),
                        "imageBaseUrl": get_ad_forge_image_base_url(),
                        "publicAssets": bool(get_asset_public_base_url()),
                        "inlineLocalImages": True,
                        "promptSkill": build_seedance_review_skill_status(),
                        "seedance": bool(get_api_key()),
                        "seedanceModel": get_default_model(),
                        "seedanceEndpoint": get_ark_endpoint(),
                        "ffmpeg": bool(FFMPEG_BIN),
                    },
                }
            )
            return
        if path == "/api/config":
            self.send_json(build_config_response())
            return
        if path == "/api/copy-library":
            self.send_json({"ok": True, "library": read_video_copy_library(), "obsidian": build_obsidian_status()})
            return
        if path == "/api/material-library":
            self.send_json({"ok": True, "library": read_material_library(), "obsidian": build_obsidian_status()})
            return
        if path == "/api/material-library/auto-edit-pool":
            self.send_json({"ok": True, "pool": read_auto_edit_pool(), "obsidian": build_obsidian_status()})
            return
        if path == "/api/material-library/director-monitor":
            self.send_json({"ok": True, "monitor": read_material_direction_monitor(), "obsidian": build_obsidian_status()})
            return
        if path == "/api/material-library/manual-cut-draft":
            self.send_json({"ok": True, "draft": read_manual_cut_draft(), "obsidian": build_obsidian_status()})
            return
        if path == "/api/material-library/chatcut-sync":
            self.send_json({"ok": True, "sync": read_chatcut_sync_ledger(), "obsidian": build_obsidian_status()})
            return
        if path == "/api/operations-center":
            self.send_json({"ok": True, "operations": build_operations_center(self.authenticated_user()), "obsidian": build_obsidian_status()})
            return
        if path.startswith("/analysis-assets/"):
            self.serve_analysis_asset(path.removeprefix("/analysis-assets/"))
            return
        if path.startswith("/external-materials/"):
            self.serve_external_material(path.removeprefix("/external-materials/"))
            return
        if path.startswith("/ad-forge-exports/"):
            self.serve_ad_forge_export(path.removeprefix("/ad-forge-exports/"))
            return
        if path.startswith("/ad-forge-images/"):
            self.serve_ad_forge_image(path.removeprefix("/ad-forge-images/"))
            return
        if path.startswith("/rough-cuts/"):
            self.serve_rough_cut(path.removeprefix("/rough-cuts/"))
            return
        if path.startswith("/api/tasks/"):
            task_id = path.removeprefix("/api/tasks/").strip()
            if not task_id:
                self.send_error_json(HTTPStatus.BAD_REQUEST, "Task id is required.")
                return
            self.proxy_status(task_id)
            return

        self.send_error_json(HTTPStatus.NOT_FOUND, "Route not found.")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/auth/login":
            self.handle_auth_login()
            return
        if path == "/api/auth/logout":
            self.send_json({"ok": True}, headers={"Set-Cookie": clear_auth_cookie()})
            return
        if not self.require_authentication(path):
            return

        if path == "/api/auth/change-password":
            user = self.authenticated_user()
            if not user:
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
                return
            payload = self.read_json_body()
            try:
                updated_user = change_auth_user_password(user.get("username"), payload.get("currentPassword"), payload.get("newPassword"))
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            config = read_auth_config()
            token = create_session_token(str(updated_user.get("username") or ""), config or {})
            self.send_json(
                {
                    "ok": True,
                    "user": public_auth_user(updated_user),
                    "auth": auth_status_for(str(updated_user.get("username") or "")),
                },
                headers={"Set-Cookie": build_auth_cookie(token)},
            )
            return

        if path == "/api/auth/users":
            if not self.require_admin():
                return
            payload = self.read_json_body()
            try:
                user = create_customer_user(
                    payload.get("username"),
                    payload.get("password"),
                    payload.get("role") or "customer",
                    payload.get("displayName") or "",
                )
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "user": public_auth_user(user), "users": [public_auth_user(item) for item in auth_users()]})
            return

        if path == "/api/auth/users/reset-password":
            if not self.require_admin():
                return
            payload = self.read_json_body()
            current_username = self.authenticated_username()
            try:
                user = reset_auth_user_password(payload.get("username"), payload.get("password"))
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            headers = {}
            if current_username and current_username.lower() == str(user.get("username") or "").lower():
                config = read_auth_config()
                headers["Set-Cookie"] = build_auth_cookie(create_session_token(current_username, config or {}))
            self.send_json(
                {
                    "ok": True,
                    "user": public_auth_user(user),
                    "users": [public_auth_user(item) for item in auth_users()],
                    "auth": auth_status_for(current_username),
                },
                headers=headers,
            )
            return

        if path == "/api/auth/users/delete":
            if not self.require_admin():
                return
            payload = self.read_json_body()
            current_username = self.authenticated_username()
            try:
                user = delete_auth_user(payload.get("username"), current_username)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json(
                {
                    "ok": True,
                    "deletedUser": public_auth_user(user),
                    "users": [public_auth_user(item) for item in auth_users()],
                    "auth": auth_status_for(current_username),
                }
            )
            return

        if path == "/api/auth/users/set-enabled":
            if not self.require_admin():
                return
            payload = self.read_json_body()
            try:
                user = set_auth_user_enabled(payload.get("username"), bool(payload.get("enabled")))
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "user": public_auth_user(user), "users": [public_auth_user(item) for item in auth_users()]})
            return

        if path == "/api/editing-tasks":
            user = self.authenticated_user()
            if not user:
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
                return
            payload = self.read_json_body()
            if user.get("role") != "admin":
                payload["assignee"] = user.get("username")
            try:
                task = create_editing_task(payload, self.authenticated_username())
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            users = []
            if user.get("role") == "admin":
                users = [
                    public_auth_user(item)
                    for item in auth_users()
                    if item.get("role") == "customer" and item.get("enabled", True)
                ]
            self.send_json(
                {
                    "ok": True,
                    "task": task,
                    "tasks": editing_tasks_for_user(user),
                    "users": users,
                    "obsidian": build_obsidian_status(),
                }
            )
            return

        if path == "/api/editing-tasks/update":
            user = self.authenticated_user()
            if not user:
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
                return
            payload = self.read_json_body()
            try:
                task = update_editing_task(payload, user)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            users = []
            if user.get("role") == "admin":
                users = [
                    public_auth_user(item)
                    for item in auth_users()
                    if item.get("role") == "customer" and item.get("enabled", True)
                ]
            self.send_json(
                {
                    "ok": True,
                    "task": task,
                    "tasks": editing_tasks_for_user(user),
                    "users": users,
                    "obsidian": build_obsidian_status(),
                }
            )
            return

        if path in {
            "/api/ad-forge/projects",
            "/api/ad-forge/projects/update",
            "/api/ad-forge/projects/archive",
            "/api/ad-forge/storyboard",
            "/api/ad-forge/skill/generate-prompts",
            "/api/ad-forge/images/generate",
            "/api/ad-forge/images/cancel",
            "/api/ad-forge/shots/update",
            "/api/ad-forge/shots/reorder",
            "/api/ad-forge/compose",
        }:
            self.handle_ad_forge_post(path)
            return

        if path == "/api/build":
            payload = self.read_json_body()
            try:
                self.validate_seedance_project_access(payload)
                body = build_seedance_body(payload)
                quantity = parse_quantity(payload.get("quantity"))
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            public_body = public_seedance_request_body(body)
            self.send_json({"ok": True, "quantity": quantity, "request": public_body, "curl": build_curl_preview(body)})
            return

        if path == "/api/tasks":
            payload = self.read_json_body()
            try:
                self.validate_seedance_project_access(payload)
                body = build_seedance_body(payload)
                quantity = parse_quantity(payload.get("quantity"))
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.proxy_submit(body, quantity)
            return

        if path == "/api/fashion-prompts/analyze":
            payload = self.read_json_body()
            try:
                result = analyze_fashion_product(payload)
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/fashion-prompts/generate":
            payload = self.read_json_body()
            try:
                result = generate_fashion_prompts(payload)
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/fashion-prompts/optimize":
            payload = self.read_json_body()
            try:
                result = optimize_fashion_prompts(payload)
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/config":
            payload = self.read_json_body()
            try:
                config = save_runtime_config(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "config": config})
            return

        if path == "/api/copy-library":
            payload = self.read_json_body()
            try:
                library, entry = create_video_copy_entry(payload, self.authenticated_username())
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "library": library, "entry": entry, "obsidian": build_obsidian_status()})
            return

        if path == "/api/copy-library/update":
            payload = self.read_json_body()
            try:
                library, entry = update_video_copy_entry(payload, self.authenticated_username())
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "library": library, "entry": entry, "obsidian": build_obsidian_status()})
            return

        if path == "/api/copy-library/analyze":
            payload = self.read_json_body()
            try:
                result = analyze_video_copy_entry(payload, self.authenticated_username())
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result, "obsidian": build_obsidian_status()})
            return

        if path == "/api/copy-library/delete":
            payload = self.read_json_body()
            try:
                library = delete_video_copy_entry(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "library": library, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library":
            payload = self.read_json_body()
            try:
                library = save_material_library(payload.get("library") if isinstance(payload.get("library"), dict) else payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "library": library, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library/clear":
            result = clear_material_library()
            self.send_json({"ok": True, **result})
            return

        if path == "/api/material-library/analyze":
            payload = self.read_json_body()
            try:
                result = run_material_analyzer(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except RuntimeError as exc:
                self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/material-library/director-monitor":
            payload = self.read_json_body()
            try:
                monitor = write_material_direction_monitor(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "monitor": monitor, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library/manual-cut-draft":
            payload = self.read_json_body()
            try:
                draft = write_manual_cut_draft(payload.get("draft") if isinstance(payload.get("draft"), dict) else payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "draft": draft, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library/chatcut-sync/request":
            payload = self.read_json_body()
            try:
                sync, request_record = create_chatcut_sync_request(payload, self.authenticated_username())
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "sync": sync, "request": request_record, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library/chatcut-sync/preview":
            payload = self.read_json_body()
            try:
                request_record = preview_chatcut_sync_request(payload, self.authenticated_username())
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "preview": request_record, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library/chatcut-sync/update":
            payload = self.read_json_body()
            try:
                sync, request_record = apply_chatcut_sync_update(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "sync": sync, "request": request_record, "obsidian": build_obsidian_status()})
            return

        if path == "/api/material-library/import-remote":
            payload = self.read_json_body()
            try:
                result = import_remote_video_materials(payload, self.build_upload_url)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except RuntimeError as exc:
                self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/material-library/import-local-folder":
            payload = self.read_json_body()
            try:
                result = import_local_folder_video_materials(payload, self.build_external_material_url)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except RuntimeError as exc:
                self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/material-library/jianying-draft":
            payload = self.read_json_body()
            try:
                result = run_jianying_draft_generator(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except RuntimeError as exc:
                self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/material-library/rough-cut":
            payload = self.read_json_body()
            try:
                result = run_rough_cut_generator(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except RuntimeError as exc:
                self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        if path == "/api/material-library/query":
            payload = self.read_json_body()
            try:
                result = query_material_library(payload)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result, "obsidian": build_obsidian_status()})
            return

        if path == "/api/config/test" or path in {
            "/api/config/test/ark",
            "/api/config/test/ai",
            "/api/config/test/image",
            "/api/config/test/translation",
            "/api/config/test/elevenlabs",
        }:
            payload = self.read_json_body()
            try:
                kind = path.removeprefix("/api/config/test/").strip() if path != "/api/config/test" else None
                result = validate_runtime_config(payload, kind=kind or None)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "result": result})
            return

        for kind in MATERIAL_UPLOAD_CONFIGS:
            if path == f"/api/uploads/{kind}":
                self.handle_material_upload(kind)
                return

        if path == "/api/prompt/generate":
            payload = self.read_json_body()
            self.proxy_prompt_generation(payload)
            return

        if path == "/api/prompt/translate":
            payload = self.read_json_body()
            try:
                result = translate_prompt_text(payload)
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "result": result})
            return

        if path == "/api/prompt/compliance-check":
            payload = self.read_json_body()
            try:
                result = check_translated_ad_copy(payload)
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "result": result})
            return

        if path == "/api/skill/generate":
            payload = self.read_json_body()
            self.proxy_skill_generation(payload)
            return

        if path in {"/api/skill/optimize-prompt", "/api/skill/review-prompt"}:
            payload = self.read_json_body()
            try:
                result = review_seedance_prompt(payload)
            except AiError as exc:
                self.send_error_json(exc.status, exc.message)
                return
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        self.send_error_json(HTTPStatus.NOT_FOUND, "Route not found.")

    def authenticated_username(self) -> str:
        user = self.authenticated_user()
        return str(user.get("username") or "") if user else ""

    def authenticated_user(self) -> dict[str, Any] | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie") or "")
        except Exception:
            return None
        token = cookie.get(SESSION_COOKIE_NAME)
        return verify_session_user(token.value) if token else None

    def is_public_static_path(self, path: str) -> bool:
        return path in {"/static/styles.css", "/static/login.js"}

    def require_authentication(self, path: str) -> bool:
        if self.authenticated_username():
            return True
        if path.startswith("/api/"):
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
            return False
        target = quote(self.path if self.path.startswith("/") else path, safe="")
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_common_headers(content_type="text/plain; charset=utf-8", cache=False)
        self.send_header("Location", f"/login.html?next={target}")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def require_admin(self) -> bool:
        user = self.authenticated_user()
        if user and user.get("role") == "admin":
            return True
        if self.path.startswith("/api/"):
            self.send_error_json(HTTPStatus.FORBIDDEN, "只有管理员可以管理客户账号。")
            return False
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_common_headers(content_type="text/plain; charset=utf-8", cache=False)
        self.send_header("Location", "/materials.html")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def handle_auth_login(self) -> None:
        key = client_attempt_key(self)
        if is_login_rate_limited(key):
            self.send_error_json(HTTPStatus.TOO_MANY_REQUESTS, "登录尝试过多，请稍后再试。")
            return

        payload = self.read_json_body()
        raw_username = payload.get("username")
        raw_password = payload.get("password")
        setup = bool(payload.get("setup"))
        config = read_auth_config()

        try:
            username = clean_auth_username(raw_username)
            password = clean_auth_password(raw_password)
        except ValueError as exc:
            record_login_failure(key)
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return

        if config is None:
            if not setup:
                self.send_error_json(HTTPStatus.PRECONDITION_REQUIRED, "需要先创建管理员账号。")
                return
            try:
                config = create_auth_config(username, password)
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            user = find_auth_user(config, username)
        else:
            user = authenticate_auth_user(config, username, password)

        if not user:
            record_login_failure(key)
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "账号或密码不正确。")
            return

        clear_login_failures(key)
        if config.get("mode") != "env":
            user["lastLoginAt"] = utc_now_iso()
            user["updatedAt"] = user.get("updatedAt") or utc_now_iso()
            config["users"] = auth_users(config)
            save_auth_config(config)
        token = create_session_token(str(user.get("username") or username), config)
        self.send_json(
            {
                "ok": True,
                "auth": auth_status_for(str(user.get("username") or username)),
            },
            headers={"Set-Cookie": build_auth_cookie(token)},
        )

    def handle_ad_forge_post(self, path: str) -> None:
        user = self.authenticated_user()
        if not user:
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
            return
        username = str(user.get("username") or "")
        is_admin = user.get("role") == "admin"
        payload = self.read_json_body()
        try:
            if path == "/api/ad-forge/projects":
                project = ad_forge.create_project(AD_FORGE_PROJECTS_FILE, username, payload)
            elif path == "/api/ad-forge/projects/update":
                project = ad_forge.update_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    payload.get("changes") if isinstance(payload.get("changes"), dict) else payload,
                    is_admin=is_admin,
                )
            elif path == "/api/ad-forge/projects/archive":
                project = ad_forge.archive_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    bool(payload.get("archived", True)),
                    is_admin=is_admin,
                )
            elif path == "/api/ad-forge/storyboard":
                existing = ad_forge.get_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    is_admin=is_admin,
                )
                if payload.get("forceFallback"):
                    shots, source, warning = ad_forge.build_fallback_storyboard(existing), "fallback", "已使用本地导演模板重建分镜。"
                else:
                    shots, source, warning = generate_ad_forge_storyboard(existing)
                project = ad_forge.replace_storyboard(
                    AD_FORGE_PROJECTS_FILE,
                    existing["id"],
                    username,
                    shots,
                    source,
                    warning,
                    is_admin=is_admin,
                )
            elif path == "/api/ad-forge/skill/generate-prompts":
                existing = ad_forge.get_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    is_admin=is_admin,
                )
                shots, skill_status, _prompt_model = generate_ad_forge_skill_prompts(existing)
                project = ad_forge.replace_storyboard(
                    AD_FORGE_PROJECTS_FILE,
                    existing["id"],
                    username,
                    shots,
                    "seedance-skill",
                    "",
                    is_admin=is_admin,
                )
                project = ad_forge.update_project(
                    AD_FORGE_PROJECTS_FILE,
                    existing["id"],
                    username,
                    {
                        "promptSkill": skill_status.get("name") or "seedance-20",
                        "promptSkillVersion": skill_status.get("version") or "",
                        "promptGeneratedAt": utc_now_iso(),
                        "warning": "",
                    },
                    is_admin=is_admin,
                )
            elif path == "/api/ad-forge/images/generate":
                existing = ad_forge.get_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    is_admin=is_admin,
                )
                shot_id = ad_forge.clean_text(payload.get("shotId"), 80)
                shot = next((item for item in existing.get("shots", []) if item.get("id") == shot_id), None)
                if not shot:
                    raise ad_forge.ProjectNotFound("分镜不存在。")
                request_id = clean_ad_forge_image_request_id(payload.get("requestId"))
                cancel_event = register_ad_forge_image_request(
                    request_id,
                    username,
                    existing["id"],
                    shot_id,
                )
                try:
                    try:
                        local_path, _image_prompt, image_size, image_reference_assets = generate_ad_forge_image(
                            existing,
                            shot,
                            cancel_event=cancel_event,
                        )
                        if not commit_ad_forge_image_request(request_id, cancel_event):
                            delete_saved_ad_forge_image(local_path)
                            raise AdForgeImageCancelled()
                    except AdForgeImageCancelled:
                        raise
                    except AdForgeImageError as exc:
                        ad_forge.update_shot(
                            AD_FORGE_PROJECTS_FILE,
                            existing["id"],
                            username,
                            shot_id,
                            {"imageError": exc.message},
                            is_admin=is_admin,
                        )
                        raise
                    image_url = self.build_upload_url(local_path)
                    source_reference_assets = [
                        item
                        for item in shot.get("referenceAssets", [])
                        if item
                        and item != image_url
                        and "/ad-forge-images/" not in urlparse(str(item)).path
                    ]
                    reference_assets = [
                        image_url,
                        *source_reference_assets,
                    ][:9]
                    project = ad_forge.update_shot(
                        AD_FORGE_PROJECTS_FILE,
                        existing["id"],
                        username,
                        shot_id,
                        {
                            "referenceImage": image_url,
                            "referenceAssets": reference_assets,
                            "referenceImageSource": "generated",
                            "imageModel": get_ad_forge_image_model(),
                            "imageSize": image_size,
                            "imageGeneratedAt": utc_now_iso(),
                            "imageGenerationRoute": "edits" if image_reference_assets else "generations",
                            "imageReferenceCount": len(image_reference_assets),
                            "imageReferenceAssets": image_reference_assets,
                            "imageError": "",
                        },
                        is_admin=is_admin,
                    )
                finally:
                    finish_ad_forge_image_request(request_id, cancel_event)
            elif path == "/api/ad-forge/images/cancel":
                existing = ad_forge.get_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    is_admin=is_admin,
                )
                shot_id = ad_forge.clean_text(payload.get("shotId"), 80)
                if not any(item.get("id") == shot_id for item in existing.get("shots", [])):
                    raise ad_forge.ProjectNotFound("分镜不存在。")
                cancelled = cancel_ad_forge_image_request(
                    payload.get("requestId"),
                    username,
                    existing["id"],
                    shot_id,
                )
                projects = ad_forge.list_projects(
                    AD_FORGE_PROJECTS_FILE,
                    username,
                    is_admin=is_admin,
                )
                self.send_json({"ok": True, "cancelled": cancelled, "project": existing, "projects": projects})
                return
            elif path == "/api/ad-forge/shots/update":
                project = ad_forge.update_shot(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    payload.get("shotId"),
                    payload.get("changes") if isinstance(payload.get("changes"), dict) else payload,
                    is_admin=is_admin,
                )
            elif path == "/api/ad-forge/shots/reorder":
                project = ad_forge.reorder_shots(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    payload.get("shotIds") if isinstance(payload.get("shotIds"), list) else [],
                    is_admin=is_admin,
                )
            elif path == "/api/ad-forge/compose":
                existing = ad_forge.get_project(
                    AD_FORGE_PROJECTS_FILE,
                    payload.get("projectId"),
                    username,
                    is_admin=is_admin,
                )
                export_url = compose_ad_forge_project(existing)
                project = ad_forge.update_project(
                    AD_FORGE_PROJECTS_FILE,
                    existing["id"],
                    username,
                    {"finalVideoUrl": export_url, "currentStep": 5},
                    is_admin=is_admin,
                )
            else:
                self.send_error_json(HTTPStatus.NOT_FOUND, "Route not found.")
                return
        except ad_forge.ProjectNotFound:
            self.send_error_json(HTTPStatus.NOT_FOUND, "项目不存在。")
            return
        except AiError as exc:
            self.send_error_json(exc.status, exc.message)
            return
        except (ad_forge.InvalidProject, ValueError) as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except AdForgeImageError as exc:
            self.send_error_json(exc.status, exc.message)
            return
        except (RuntimeError, TimeoutError, OSError) as exc:
            self.send_error_json(HTTPStatus.BAD_GATEWAY, str(exc))
            return
        projects = ad_forge.list_projects(
            AD_FORGE_PROJECTS_FILE,
            username,
            is_admin=is_admin,
        )
        self.send_json({"ok": True, "project": project, "projects": projects})

    def serve_ad_forge_export(self, relative_path: str) -> None:
        clean_path = unquote(relative_path).replace("\\", "/").lstrip("/")
        parts = [part for part in clean_path.split("/") if part]
        if len(parts) != 2 or not re.fullmatch(r"ad-[a-f0-9]{16}", parts[0]) or not re.fullmatch(r"[A-Za-z0-9._-]+\.mp4", parts[1]):
            self.send_error_json(HTTPStatus.NOT_FOUND, "导出文件不存在。")
            return
        user = self.authenticated_user()
        if not user:
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
            return
        try:
            ad_forge.get_project(
                AD_FORGE_PROJECTS_FILE,
                parts[0],
                str(user.get("username") or ""),
                is_admin=user.get("role") == "admin",
            )
        except ad_forge.ProjectNotFound:
            self.send_error_json(HTTPStatus.NOT_FOUND, "导出文件不存在。")
            return
        target = (AD_FORGE_EXPORT_ROOT / parts[0] / parts[1]).resolve()
        try:
            target.relative_to(AD_FORGE_EXPORT_ROOT.resolve())
        except ValueError:
            self.send_error_json(HTTPStatus.NOT_FOUND, "导出文件不存在。")
            return
        self.serve_ranged_video_file(target)

    def serve_ad_forge_image(self, relative_path: str) -> None:
        clean_path = unquote(relative_path).replace("\\", "/").lstrip("/")
        parts = [part for part in clean_path.split("/") if part]
        valid_filename = len(parts) == 2 and re.fullmatch(r"[A-Za-z0-9._-]+\.(png|jpg|webp)", parts[1])
        if len(parts) != 2 or not re.fullmatch(r"ad-[a-f0-9]{16}", parts[0]) or not valid_filename:
            self.send_error_json(HTTPStatus.NOT_FOUND, "分镜图片不存在。")
            return
        user = self.authenticated_user()
        if not user:
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录。")
            return
        try:
            ad_forge.get_project(
                AD_FORGE_PROJECTS_FILE,
                parts[0],
                str(user.get("username") or ""),
                is_admin=user.get("role") == "admin",
            )
        except ad_forge.ProjectNotFound:
            self.send_error_json(HTTPStatus.NOT_FOUND, "分镜图片不存在。")
            return
        target = (AD_FORGE_IMAGE_ROOT / parts[0] / parts[1]).resolve()
        try:
            target.relative_to(AD_FORGE_IMAGE_ROOT.resolve())
        except ValueError:
            self.send_error_json(HTTPStatus.NOT_FOUND, "分镜图片不存在。")
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "分镜图片不存在。")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        file_size = target.stat().st_size
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=True)
        self.send_header("Cache-Control", "private, max-age=86400")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.write_file_range(target, 0, file_size)

    def proxy_submit(self, body: dict[str, Any], quantity: int) -> None:
        tasks: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for index in range(quantity):
            try:
                tasks.append(call_ark("POST", get_ark_endpoint(), body=body))
            except ArkError as exc:
                errors.append({"index": index + 1, "status": int(exc.status), "message": exc.message})
                break

        if not tasks and errors:
            first_error = errors[0]
            status = HTTPStatus(first_error["status"])
            self.send_error_json(status, str(first_error["message"]))
            return

        self.send_json(
            {
                "ok": True,
                "partial": bool(errors),
                "quantity": quantity,
                "task": tasks[0] if tasks else None,
                "tasks": tasks,
                "errors": errors,
                "request": public_seedance_request_body(body),
            }
        )

    def validate_seedance_project_access(self, payload: dict[str, Any]) -> None:
        project_id = ad_forge.clean_text(payload.get("projectId"), 80)
        if not project_id:
            return
        user = self.authenticated_user()
        if not user:
            raise ad_forge.ProjectNotFound("请先登录。")
        ad_forge.get_project(
            AD_FORGE_PROJECTS_FILE,
            project_id,
            str(user.get("username") or ""),
            is_admin=user.get("role") == "admin",
        )

    def proxy_status(self, task_id: str) -> None:
        try:
            result = call_ark("GET", f"{get_ark_endpoint()}/{task_id}")
        except ArkError as exc:
            self.send_error_json(exc.status, exc.message)
            return
        self.send_json({"ok": True, "task": result})

    def proxy_prompt_generation(self, payload: dict[str, Any]) -> None:
        try:
            prompt = generate_seedance_prompt(payload)
        except AiError as exc:
            self.send_error_json(exc.status, exc.message)
            return
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json({"ok": True, "prompt": prompt, "model": get_ai_model()})

    def proxy_skill_generation(self, payload: dict[str, Any]) -> None:
        try:
            result = generate_skill_video_plan(payload)
        except AiError as exc:
            self.send_error_json(exc.status, exc.message)
            return
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json({"ok": True, **result})

    def serve_static(self, relative_path: str) -> None:
        target = (STATIC_DIR / relative_path).resolve()
        try:
            target.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid static path.")
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "File not found.")
            return

        content = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=False)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_analysis_asset(self, relative_path: str) -> None:
        clean_path = unquote(relative_path).replace("\\", "/").lstrip("/")
        if not clean_path:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Analysis asset path is required.")
            return
        base = OBSIDIAN_ANALYSIS_DIR.resolve()
        target_root = OBSIDIAN_MATERIAL_ROOT if clean_path.startswith("analysis/") else OBSIDIAN_ANALYSIS_DIR
        target = (target_root / clean_path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid analysis asset path.")
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Analysis asset not found.")
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        file_size = target.stat().st_size
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=True)
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.write_file_range(target, 0, file_size)

    def serve_material_playback(self, query: str) -> None:
        requested_url = str((parse_qs(query).get("url") or [""])[0]).strip()
        if not requested_url:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Material URL is required.")
            return
        try:
            item, source = resolve_material_playback_source(requested_url)
            target = ensure_browser_playback_video(source, item)
        except FileNotFoundError as exc:
            self.send_error_json(HTTPStatus.NOT_FOUND, str(exc))
            return
        except ValueError as exc:
            self.send_error_json(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc))
            return
        self.serve_ranged_video_file(target)

    def serve_ranged_video_file(self, target: Path) -> None:
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Playback video not found.")
            return
        file_size = target.stat().st_size
        try:
            byte_range = parse_http_byte_range((self.headers.get("Range") or "").strip(), file_size)
        except (TypeError, ValueError):
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_common_headers(content_type="video/mp4", cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if byte_range:
            start, end = byte_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_common_headers(content_type="video/mp4", cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()
            self.write_file_range(target, start, content_length)
            return
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type="video/mp4", cache=True)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.write_file_range(target, 0, file_size)

    def serve_upload(self, kind: str, relative_path: str) -> None:
        try:
            target = resolve_upload_target(kind, relative_path)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Uploaded file not found.")
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        file_size = target.stat().st_size
        try:
            byte_range = parse_http_byte_range((self.headers.get("Range") or "").strip(), file_size)
        except (TypeError, ValueError):
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_common_headers(content_type=content_type, cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if byte_range:
            start, end = byte_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_common_headers(content_type=content_type, cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()
            self.write_file_range(target, start, content_length)
            return

        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=True)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.write_file_range(target, 0, file_size)

    def serve_external_material(self, relative_path: str) -> None:
        try:
            target = resolve_external_material_target(relative_path)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "External material file not found.")
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        file_size = target.stat().st_size
        try:
            byte_range = parse_http_byte_range((self.headers.get("Range") or "").strip(), file_size)
        except (TypeError, ValueError):
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_common_headers(content_type=content_type, cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if byte_range:
            start, end = byte_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_common_headers(content_type=content_type, cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()
            self.write_file_range(target, start, content_length)
            return

        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=True)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.write_file_range(target, 0, file_size)

    def serve_rough_cut(self, relative_path: str) -> None:
        clean_path = unquote(relative_path).replace("\\", "/").lstrip("/")
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}/preview\.mp4", clean_path):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid rough cut path.")
            return
        base = OBSIDIAN_ROUGH_CUT_DIR.resolve()
        target = (OBSIDIAN_ROUGH_CUT_DIR / clean_path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid rough cut path.")
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Rough cut video not found.")
            return

        content_type = "video/mp4"
        file_size = target.stat().st_size
        try:
            byte_range = parse_http_byte_range((self.headers.get("Range") or "").strip(), file_size)
        except (TypeError, ValueError):
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_common_headers(content_type=content_type, cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if byte_range:
            start, end = byte_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_common_headers(content_type=content_type, cache=True)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()
            self.write_file_range(target, start, content_length)
            return

        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=True)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.write_file_range(target, 0, file_size)

    def handle_material_upload(self, kind: str) -> None:
        try:
            config = upload_config_for(kind)
            items = self.read_uploaded_files(kind)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return

        saved = []
        upload_dir = upload_dir_for(kind)
        upload_dir.mkdir(parents=True, exist_ok=True)
        batch_library = read_material_library()
        batch = active_material_batch(batch_library)
        for item in items:
            material_kind = material_kind_from_upload_kind(kind)
            suffix = config["allowed_types"][item["contentType"]]
            filename = f"{uuid.uuid4().hex}{suffix}"
            target = upload_dir / filename
            target.write_bytes(item["content"])
            local_path = f"/uploads/{kind}/{filename}"
            technical = extract_material_technical(target, material_kind)
            material = {
                "name": item["name"],
                "size": len(item["content"]),
                "contentType": item["contentType"],
                "url": self.build_upload_url(local_path),
                "localPath": local_path,
                "obsidianPath": str(target.relative_to(OBSIDIAN_MATERIAL_ROOT).as_posix()),
                "technical": technical,
                "isPublic": bool(get_asset_public_base_url()),
            }
            saved.append(
                material
            )
            upsert_material_library_item(
                batch_library,
                material["url"],
                {
                    "batchId": batch["id"],
                    "kind": material_kind,
                    "name": item["name"],
                    "size": len(item["content"]),
                    "contentType": item["contentType"],
                    "localPath": local_path,
                    "obsidianPath": material["obsidianPath"],
                    "technical": technical,
                    "analysisStatus": "queued",
                    "editRole": clean_edit_role("", material_kind),
                    "priority": "normal",
                    "qualityScore": 0,
                    "notes": "",
                    "analysis": clean_material_analysis({}, "queued"),
                    "addedAt": utc_now_iso(),
                },
            )
        save_material_library(batch_library)
        item_key = str(config["item_key"])
        warning = "" if get_asset_public_base_url() else f"已保存到 Obsidian；当前返回的是本地 URL。Seedance 远端生成需要公网可访问{config['url_label']} URL。"
        self.send_json(
            {
                "ok": True,
                "items": saved,
                item_key: saved,
                "warning": warning,
            }
        )

    def read_uploaded_files(self, kind: str) -> list[dict[str, Any]]:
        config = upload_config_for(kind)
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            raise ValueError(f"{config['display_name']} upload must use multipart/form-data.")

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise ValueError("No upload file received.")
        if length > int(config["max_bytes"]) * int(config["max_count"]):
            raise ValueError(f"Uploaded {kind} are too large.")

        raw = self.rfile.read(length)
        form = cgi.FieldStorage(
            fp=io.BytesIO(raw),
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(length),
            },
        )

        files: list[Any] = []
        for key in config["fields"]:
            if key not in form:
                continue
            value = form[key]
            files.extend(value if isinstance(value, list) else [value])

        if not files:
            raise ValueError(f"No {config['display_name'].lower()} file received.")
        if len(files) > int(config["max_count"]):
            raise ValueError(f"Upload at most {config['max_count']} {kind} at a time.")

        items = []
        for file_item in files:
            if not getattr(file_item, "filename", ""):
                continue
            data = file_item.file.read() if getattr(file_item, "file", None) else b""
            name = Path(str(getattr(file_item, "filename", "") or kind)).name
            content_type = normalize_upload_content_type(name, str(getattr(file_item, "type", "") or ""), config["allowed_types"])
            if content_type not in config["allowed_types"]:
                raise ValueError(f"Unsupported {config['display_name'].lower()} type: {content_type or name}.")
            if not data:
                raise ValueError(f"{config['display_name']} is empty: {name}.")
            if len(data) > int(config["max_bytes"]):
                max_mb = int(config["max_bytes"]) // 1024 // 1024
                raise ValueError(f"{config['display_name']} is larger than {max_mb}MB: {name}.")
            items.append({"name": name, "contentType": content_type, "content": data})
        if not items:
            raise ValueError(f"No {config['display_name'].lower()} file received.")
        return items

    def build_upload_url(self, local_path: str) -> str:
        public_base_url = get_asset_public_base_url()
        if public_base_url:
            return f"{public_base_url}{local_path}"
        host = self.headers.get("Host") or "127.0.0.1"
        return f"http://{host}{local_path}"

    def build_external_material_url(self, source_path: Path) -> str:
        local_path = external_material_local_path(source_path)
        host = self.headers.get("Host") or "127.0.0.1"
        return f"http://{host}{local_path}"

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK, headers: dict[str, str] | None = None) -> None:
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_common_headers(content_type="application/json; charset=utf-8", cache=False)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"ok": False, "error": message}, status=status)

    def is_allowed_cors_origin(self, origin: str) -> bool:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        allowed_origins = {
            item.strip().rstrip("/")
            for item in os.environ.get("SEEDANCE_CORS_ORIGINS", "").split(",")
            if item.strip()
        }
        normalized_origin = origin.rstrip("/")
        if normalized_origin in allowed_origins:
            return True
        host = (self.headers.get("Host") or "").lower()
        return bool(host and parsed.netloc.lower() == host)

    def send_common_headers(
        self,
        content_type: str = "text/plain; charset=utf-8",
        cache: bool = False,
    ) -> None:
        self.send_header("Content-Type", content_type)
        origin = self.headers.get("Origin") or ""
        if origin and self.is_allowed_cors_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin.rstrip("/"))
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.send_header("Access-Control-Expose-Headers", "Content-Length, Content-Range, Accept-Ranges")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "base-uri 'self'; form-action 'self'; frame-ancestors 'self'")
        if not cache:
            self.send_header("Cache-Control", "no-store")

    def write_file_range(self, target: Path, start: int, length: int) -> None:
        remaining = length
        with target.open("rb") as file:
            file.seek(start)
            while remaining > 0:
                chunk = file.read(min(FILE_RESPONSE_CHUNK_SIZE, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[seedance-web] {self.address_string()} - {format % args}")


def upload_config_for(kind: str) -> dict[str, Any]:
    config = MATERIAL_UPLOAD_CONFIGS.get(kind)
    if not config:
        raise ValueError(f"Unsupported upload material type: {kind}.")
    return config


def upload_dir_for(kind: str) -> Path:
    upload_config_for(kind)
    return OBSIDIAN_UPLOAD_ROOT / kind


def legacy_upload_dir_for(kind: str) -> Path:
    upload_config_for(kind)
    return UPLOAD_ROOT / kind


def resolve_upload_target(kind: str, relative_path: str) -> Path:
    upload_config_for(kind)
    candidates = [upload_dir_for(kind), legacy_upload_dir_for(kind)]
    for upload_dir in candidates:
        target = (upload_dir / relative_path).resolve()
        try:
            target.relative_to(upload_dir.resolve())
        except ValueError:
            continue
        if target.exists() and target.is_file():
            return target
    upload_dir = upload_dir_for(kind)
    target = (upload_dir / relative_path).resolve()
    try:
        target.relative_to(upload_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid upload path.") from exc
    return target


def material_kind_from_upload_kind(kind: str) -> str:
    return {"images": "image", "videos": "video", "audios": "audio"}.get(kind, "image")


def external_material_id(source_path: Path | str) -> str:
    normalized = os.path.normcase(os.path.abspath(str(source_path))).strip()
    return hashlib.sha1(normalized.encode("utf-8", errors="ignore")).hexdigest()[:20]


def external_material_local_path(source_path: Path | str) -> str:
    path = Path(source_path)
    filename = quote(path.name or f"{external_material_id(path)}.mp4")
    return f"/external-materials/videos/{external_material_id(path)}/{filename}"


def external_material_video_extensions() -> set[str]:
    return {str(suffix).lower() for suffix in ALLOWED_VIDEO_TYPES.values()}


def resolve_external_material_target(relative_path: str) -> Path:
    clean_path = unquote(relative_path).replace("\\", "/").lstrip("/")
    match = re.fullmatch(r"videos/([a-f0-9]{20})/[^/]+", clean_path, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Invalid external material path.")
    material_id = match.group(1).lower()
    library = read_material_library()
    for item in material_entries(library):
        local_path = str(item.get("localPath") or "")
        source = resolve_material_source_path(item)
        if not source or source.suffix.lower() not in external_material_video_extensions():
            continue
        if external_material_id(source) == material_id and local_path.startswith(f"/external-materials/videos/{material_id}/"):
            return source
    raise ValueError("External material is not registered in the library.")


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def normalize_upload_content_type(name: str, reported_type: str, allowed_types: dict[str, str]) -> str:
    reported = reported_type.split(";", 1)[0].strip().lower()
    guessed = (mimetypes.guess_type(name)[0] or "").strip().lower()
    candidates = [item for item in [reported, guessed] if item and item != "application/octet-stream"]
    for content_type in candidates:
        if content_type in allowed_types:
            return content_type

    suffix = Path(name).suffix.lower()
    for content_type, allowed_suffix in allowed_types.items():
        if suffix == allowed_suffix:
            return content_type
    return reported or guessed


class SafeRemoteImportRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Request | None:
        validate_remote_import_url(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def parse_remote_import_urls(value: object) -> list[str]:
    raw_items = value if isinstance(value, list) else [value]
    urls: list[str] = []
    for item in raw_items:
        text = str(item or "")
        found = re.findall(r"https?://[^\s\"'<>]+", text, flags=re.IGNORECASE)
        candidates = found or [part.strip() for part in text.splitlines()]
        for candidate in candidates:
            clean = clean_remote_import_url(candidate)
            if clean and clean not in urls:
                urls.append(clean)
    return urls[:MAX_REMOTE_IMPORT_URLS]


def clean_remote_import_url(value: object) -> str:
    text = html.unescape(str(value or "")).strip().strip("\"'<>")
    return text.rstrip(".,;，。；、)]}）】")


def validate_remote_import_url(url: str) -> None:
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("云盘导入只支持 http/https 链接。")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"无法解析云盘链接域名：{parsed.hostname}") from exc
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError(f"云盘链接解析到了无效地址：{address}") from exc
        if not ip.is_global:
            raise ValueError("云盘导入不允许访问本机、内网或保留地址。")


def open_remote_import_url(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    validate_remote_import_url(url)
    request_headers = {
        "User-Agent": REMOTE_IMPORT_USER_AGENT,
        "Accept": "text/html,video/*,application/octet-stream,*/*",
        **(headers or {}),
    }
    request = Request(url, headers=request_headers, method=method)
    opener = build_opener(SafeRemoteImportRedirectHandler)
    return opener.open(request, timeout=REMOTE_IMPORT_TIMEOUT_SECONDS)


def remote_video_suffixes() -> set[str]:
    return set(ALLOWED_VIDEO_TYPES.values())


def remote_url_has_video_suffix(url: str) -> bool:
    path = unquote(urlparse(url).path or "").lower()
    return Path(path).suffix in remote_video_suffixes()


def remote_value_looks_video(url: str, content_type: str = "", filename: str = "") -> bool:
    clean_type = content_type.split(";", 1)[0].strip().lower()
    return (
        clean_type in ALLOWED_VIDEO_TYPES
        or clean_type.startswith("video/")
        or remote_url_has_video_suffix(url)
        or Path(filename.lower()).suffix in remote_video_suffixes()
    )


def remote_response_filename(headers: Any, url: str, content_type: str = "", force_video_suffix: bool = False) -> str:
    disposition = str(headers.get("Content-Disposition") or "")
    filename = ""
    if disposition:
        _, params = cgi.parse_header(disposition)
        filename = str(params.get("filename") or params.get("filename*") or "")
        if "''" in filename:
            filename = filename.split("''", 1)[1]
        filename = unquote(filename)
    if not filename:
        filename = unquote(Path(urlparse(url).path or "").name)
    filename = Path(filename or "cloud-video").name
    suffix = Path(filename).suffix.lower()
    if suffix not in remote_video_suffixes():
        if not force_video_suffix:
            safe_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", Path(filename).stem).strip().strip(".")[:80] or "cloud-video"
            return f"{safe_stem}{suffix}"
        normalized_type = normalize_upload_content_type(filename, content_type, ALLOWED_VIDEO_TYPES)
        suffix = ALLOWED_VIDEO_TYPES.get(normalized_type) or ".mp4"
        filename = f"{Path(filename).stem or 'cloud-video'}{suffix}"
    safe_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", Path(filename).stem).strip().strip(".")[:80] or "cloud-video"
    return f"{safe_stem}{Path(filename).suffix.lower()}"


def extract_remote_video_urls_from_html(source_url: str, body: bytes, content_type: str) -> list[str]:
    charset = "utf-8"
    charset_match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type or "", flags=re.IGNORECASE)
    if charset_match:
        charset = charset_match.group(1)
    text = body.decode(charset, errors="replace")
    candidates: list[str] = []
    for match in re.finditer(r'''(?:href|src)=["']([^"']+)["']''', text, flags=re.IGNORECASE):
        candidates.append(match.group(1))
    candidates.extend(re.findall(r"https?://[^\s\"'<>]+", text, flags=re.IGNORECASE))
    urls: list[str] = []
    for candidate in candidates:
        absolute = clean_remote_import_url(urljoin(source_url, candidate))
        if remote_url_has_video_suffix(absolute) and absolute not in urls:
            urls.append(absolute)
    return urls[:MAX_REMOTE_IMPORT_URLS]


def discover_remote_video_urls(seed_urls: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    discovered: list[str] = []
    failures: list[dict[str, str]] = []
    for seed_url in seed_urls:
        if len(discovered) >= MAX_REMOTE_IMPORT_URLS:
            break
        try:
            before_count = len(discovered)
            validate_remote_import_url(seed_url)
            if remote_url_has_video_suffix(seed_url):
                if seed_url not in discovered:
                    discovered.append(seed_url)
                continue
            try:
                with open_remote_import_url(seed_url, method="HEAD") as response:
                    final_url = clean_remote_import_url(response.geturl() or seed_url)
                    content_type = str(response.headers.get("Content-Type") or response.headers.get_content_type() or "")
                    filename = remote_response_filename(response.headers, final_url, content_type)
                    if remote_value_looks_video(final_url, content_type, filename):
                        if final_url not in discovered:
                            discovered.append(final_url)
                        continue
            except (HTTPError, URLError, OSError, ValueError):
                pass

            with open_remote_import_url(seed_url, method="GET", headers={"Range": f"bytes=0-{MAX_REMOTE_IMPORT_PAGE_BYTES - 1}"}) as response:
                final_url = clean_remote_import_url(response.geturl() or seed_url)
                content_type = str(response.headers.get("Content-Type") or response.headers.get_content_type() or "")
                filename = remote_response_filename(response.headers, final_url, content_type)
                if remote_value_looks_video(final_url, content_type, filename):
                    if final_url not in discovered:
                        discovered.append(final_url)
                    continue
                body = response.read(MAX_REMOTE_IMPORT_PAGE_BYTES + 1)
                extracted = extract_remote_video_urls_from_html(final_url, body[:MAX_REMOTE_IMPORT_PAGE_BYTES], content_type)
                for url in extracted:
                    validate_remote_import_url(url)
                    if url not in discovered:
                        discovered.append(url)
            if len(discovered) == before_count:
                failures.append({"url": seed_url, "error": "未在分享页里找到可下载的视频直链。"})
        except Exception as exc:
            failures.append({"url": seed_url, "error": str(exc)})
    return discovered[:MAX_REMOTE_IMPORT_URLS], failures


def remote_video_already_imported(library: dict[str, Any], source_url: str) -> bool:
    for item_url, item in (library.get("items") or {}).items():
        if item_url == source_url or str(item.get("sourceUrl") or "") == source_url:
            return True
    return False


def download_remote_video(source_url: str, build_url) -> dict[str, Any]:
    with open_remote_import_url(source_url, method="GET") as response:
        final_url = clean_remote_import_url(response.geturl() or source_url)
        validate_remote_import_url(final_url)
        content_type = str(response.headers.get("Content-Type") or response.headers.get_content_type() or "")
        raw_filename = remote_response_filename(response.headers, final_url, content_type)
        if not remote_value_looks_video(final_url, content_type, raw_filename):
            raise ValueError("链接不是可下载的视频文件，请使用视频直链或公开分享页。")
        filename = remote_response_filename(response.headers, final_url, content_type, force_video_suffix=True)
        normalized_type = normalize_upload_content_type(filename, content_type, ALLOWED_VIDEO_TYPES)
        suffix = ALLOWED_VIDEO_TYPES.get(normalized_type) or Path(filename).suffix.lower() or ".mp4"
        content_length = parse_non_negative_int(response.headers.get("Content-Length"))
        if content_length and content_length > MAX_VIDEO_UPLOAD_BYTES:
            max_mb = MAX_VIDEO_UPLOAD_BYTES // (1024 * 1024)
            raise ValueError(f"视频超过 {max_mb}MB，已跳过：{filename}")

        upload_dir = upload_dir_for("videos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        target = upload_dir / f"{uuid.uuid4().hex}{suffix}"
        temp_target = target.with_suffix(f"{target.suffix}.tmp")
        total = 0
        try:
            with temp_target.open("wb") as output:
                while True:
                    chunk = response.read(FILE_RESPONSE_CHUNK_SIZE)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_VIDEO_UPLOAD_BYTES:
                        max_mb = MAX_VIDEO_UPLOAD_BYTES // (1024 * 1024)
                        raise ValueError(f"视频超过 {max_mb}MB，已停止下载：{filename}")
                    output.write(chunk)
            if total <= 0:
                raise ValueError(f"视频下载为空：{filename}")
            temp_target.replace(target)
        finally:
            if temp_target.exists():
                temp_target.unlink()

    local_path = f"/uploads/videos/{target.name}"
    technical = extract_material_technical(target, "video")
    return {
        "name": filename,
        "size": total,
        "contentType": normalized_type if normalized_type in ALLOWED_VIDEO_TYPES else (mimetypes.guess_type(filename)[0] or "video/mp4"),
        "url": build_url(local_path),
        "localPath": local_path,
        "obsidianPath": str(target.relative_to(OBSIDIAN_MATERIAL_ROOT).as_posix()),
        "sourceUrl": final_url,
        "technical": technical,
        "isPublic": bool(get_asset_public_base_url()),
    }


def import_remote_video_materials(payload: dict[str, Any], build_url) -> dict[str, Any]:
    seed_urls = parse_remote_import_urls(payload.get("urls") or payload.get("urlText") or payload.get("url"))
    if not seed_urls:
        raise ValueError("请粘贴共享云盘地址或视频直链。")
    tags = clean_tags(payload.get("tags"))
    requested_batch_id = str(payload.get("batchId") or "").strip()
    analyze_after_import = bool(payload.get("analyze", True))

    library = read_material_library()
    batch = next((item for item in library.get("batches", []) if item["id"] == requested_batch_id), None) or active_material_batch(library)
    discovered_urls, failures = discover_remote_video_urls(seed_urls)
    imported: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for source_url in discovered_urls:
        if remote_video_already_imported(library, source_url):
            skipped.append({"url": source_url, "reason": "已导入过"})
            continue
        try:
            material = download_remote_video(source_url, build_url)
            imported.append(material)
            upsert_material_library_item(
                library,
                material["url"],
                {
                    "batchId": batch["id"],
                    "kind": "video",
                    "name": material["name"],
                    "size": material["size"],
                    "contentType": material["contentType"],
                    "localPath": material["localPath"],
                    "obsidianPath": material["obsidianPath"],
                    "sourceUrl": material["sourceUrl"],
                    "importMethod": "remote-cloud",
                    "importedAt": utc_now_iso(),
                    "technical": material["technical"],
                    "tags": tags,
                    "analysisStatus": "queued",
                    "editRole": "unassigned",
                    "priority": "normal",
                    "qualityScore": 0,
                    "notes": f"云盘导入：{material['sourceUrl']}"[:500],
                    "analysis": clean_material_analysis({}, "queued"),
                    "addedAt": utc_now_iso(),
                },
            )
        except Exception as exc:
            failures.append({"url": source_url, "error": str(exc)})

    if not imported and not skipped:
        first_error = failures[0]["error"] if failures else "没有找到可导入的视频文件。"
        raise ValueError(first_error)

    saved_library = save_material_library(library)
    analysis_error = ""
    analysis_payload: dict[str, Any] | None = None
    if analyze_after_import and imported:
        try:
            analysis_payload = run_material_analyzer({"limit": min(MAX_REMOTE_IMPORT_URLS, max(len(imported), 1))})
            saved_library = analysis_payload.get("library") or read_material_library()
        except (ValueError, RuntimeError) as exc:
            analysis_error = str(exc)

    return {
        "imported": imported,
        "skipped": skipped,
        "failures": failures,
        "discoveredCount": len(discovered_urls),
        "analysis": analysis_payload,
        "analysisError": analysis_error,
        "library": saved_library,
        "obsidian": build_obsidian_status(),
    }


def parse_local_folder_import_paths(value: object) -> list[Path]:
    raw_items = value if isinstance(value, list) else [value]
    paths: list[Path] = []
    seen: set[str] = set()
    for item in raw_items:
        for line in str(item or "").splitlines():
            text = line.strip().strip("\"'")
            if not text:
                continue
            path = Path(text).expanduser()
            key = os.path.normcase(os.path.abspath(str(path)))
            if key in seen:
                continue
            seen.add(key)
            paths.append(path)
    return paths


def local_video_already_imported(library: dict[str, Any], source_path: Path) -> bool:
    target_id = external_material_id(source_path)
    target_norm = os.path.normcase(os.path.abspath(str(source_path)))
    for item in material_entries(library):
        for key in ("sourcePath", "externalPath", "sourceUrl"):
            raw = str(item.get(key) or "").strip()
            if raw and os.path.normcase(os.path.abspath(raw)) == target_norm:
                return True
        local_path = str(item.get("localPath") or "")
        if local_path.startswith(f"/external-materials/videos/{target_id}/"):
            return True
    return False


def scan_local_video_files(roots: list[Path], max_files: int) -> tuple[list[Path], list[dict[str, str]]]:
    files: list[Path] = []
    failures: list[dict[str, str]] = []
    extensions = external_material_video_extensions()
    for root in roots:
        try:
            if not root.exists() or not root.is_dir():
                failures.append({"path": str(root), "error": "文件夹不存在或无法访问"})
                continue
            iterator = root.rglob("*")
            for path in iterator:
                if len(files) >= max_files:
                    return files, failures
                try:
                    if path.is_file() and path.suffix.lower() in extensions:
                        files.append(path)
                except OSError as exc:
                    failures.append({"path": str(path), "error": str(exc)})
        except OSError as exc:
            failures.append({"path": str(root), "error": str(exc)})
    files.sort(key=lambda item: str(item).lower())
    return files[:max_files], failures


def import_local_folder_video_materials(payload: dict[str, Any], build_url) -> dict[str, Any]:
    roots = parse_local_folder_import_paths(payload.get("paths") or payload.get("pathText") or payload.get("path"))
    if not roots:
        raise ValueError("请粘贴 NAS 或本地视频文件夹路径。")
    try:
        max_files = int(payload.get("maxFiles") or MAX_LOCAL_FOLDER_IMPORT_FILES)
    except (TypeError, ValueError) as exc:
        raise ValueError("maxFiles must be a number.") from exc
    max_files = min(max(max_files, 1), MAX_LOCAL_FOLDER_IMPORT_FILES)

    tags = clean_tags(payload.get("tags"))
    requested_batch_id = str(payload.get("batchId") or "").strip()
    analyze_after_import = bool(payload.get("analyze", True))
    library = read_material_library()
    batch = next((item for item in library.get("batches", []) if item["id"] == requested_batch_id), None) or active_material_batch(library)

    discovered, failures = scan_local_video_files(roots, max_files)
    imported: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for source_path in discovered:
        try:
            if local_video_already_imported(library, source_path):
                skipped.append({"path": str(source_path), "reason": "已登记过"})
                continue
            stat = source_path.stat()
            local_path = external_material_local_path(source_path)
            material = {
                "name": source_path.name,
                "size": stat.st_size,
                "contentType": normalize_upload_content_type(source_path.name, "", ALLOWED_VIDEO_TYPES) or "video/mp4",
                "url": build_url(source_path),
                "localPath": local_path,
                "obsidianPath": "",
                "sourcePath": str(source_path),
                "externalPath": str(source_path),
                "sourceUrl": "",
                "technical": clean_material_technical({}, "video"),
                "isPublic": False,
            }
            imported.append(material)
            upsert_material_library_item(
                library,
                material["url"],
                {
                    "batchId": batch["id"],
                    "kind": "video",
                    "name": material["name"],
                    "size": material["size"],
                    "contentType": material["contentType"],
                    "localPath": material["localPath"],
                    "obsidianPath": "",
                    "sourcePath": material["sourcePath"],
                    "externalPath": material["externalPath"],
                    "sourceUrl": "",
                    "importMethod": "nas-reference",
                    "importedAt": utc_now_iso(),
                    "technical": material["technical"],
                    "tags": tags,
                    "analysisStatus": "queued",
                    "editRole": "unassigned",
                    "priority": "normal",
                    "qualityScore": 0,
                    "notes": f"NAS 引用：{material['sourcePath']}"[:500],
                    "analysis": clean_material_analysis({}, "queued"),
                    "addedAt": utc_now_iso(),
                },
            )
        except OSError as exc:
            failures.append({"path": str(source_path), "error": str(exc)})

    if not imported and not skipped:
        first_error = failures[0]["error"] if failures else "没有找到可登记的视频文件。"
        raise ValueError(first_error)

    saved_library = save_material_library(library)
    analysis_error = ""
    analysis_payload: dict[str, Any] | None = None
    if analyze_after_import and imported:
        try:
            analysis_limit = min(MAX_LOCAL_FOLDER_ANALYZE_LIMIT, max(len(imported), 1))
            analysis_payload = run_material_analyzer({"limit": analysis_limit})
            saved_library = analysis_payload.get("library") or read_material_library()
        except (ValueError, RuntimeError) as exc:
            analysis_error = str(exc)

    return {
        "imported": imported,
        "skipped": skipped,
        "failures": failures,
        "discoveredCount": len(discovered),
        "analysis": analysis_payload,
        "analysisError": analysis_error,
        "library": saved_library,
        "obsidian": build_obsidian_status(),
    }


def run_material_analyzer(payload: dict[str, Any]) -> dict[str, Any]:
    script = VIDEO_MATERIAL_ANALYZER_SCRIPT.expanduser()
    if not script.exists() or not script.is_file():
        raise ValueError(f"Video material analyzer script not found: {script}")

    analyzer_python = MATERIAL_ANALYZER_PYTHON.expanduser()
    command = [str(analyzer_python if analyzer_python.exists() else Path(sys.executable)), "-B", str(script), "--vault-root", str(OBSIDIAN_MATERIAL_ROOT)]
    if payload.get("force"):
        command.append("--force")
    if payload.get("syncOnly"):
        command.append("--sync-only")
    if payload.get("dryRun"):
        command.append("--dry-run")

    raw_limit = payload.get("limit")
    if raw_limit not in (None, "", 0, "0"):
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:
            raise ValueError("Analyzer limit must be a number.") from exc
        if limit < 0 or limit > 200:
            raise ValueError("Analyzer limit must be between 0 and 200.")
        if limit:
            command.extend(["--limit", str(limit)])

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["SEEDANCE_OBSIDIAN_MATERIAL_ROOT"] = str(OBSIDIAN_MATERIAL_ROOT)

    try:
        completed = subprocess.run(
            command,
            cwd=str(PROJECT_DIR.parent),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=MATERIAL_ANALYZER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Video material analyzer timed out after {MATERIAL_ANALYZER_TIMEOUT_SECONDS}s.") from exc
    except OSError as exc:
        raise RuntimeError(f"Video material analyzer failed to start: {exc}") from exc

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    result: dict[str, Any] = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                result = parsed
        except json.JSONDecodeError:
            result = {}

    if completed.returncode != 0 and not result:
        raise RuntimeError(stderr or stdout or f"Video material analyzer failed with exit code {completed.returncode}.")

    library = save_material_library(read_material_library())
    return {
        "exitCode": completed.returncode,
        "result": result,
        "stderr": stderr[-2000:] if stderr else "",
        "library": library,
        "obsidian": build_obsidian_status(),
    }


def parse_clip_time_ms(value: object) -> int:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0
    if number < 0 or number == float("inf") or number != number:
        return 0
    return max(0, int(round(number)))


def write_selected_jianying_clips(raw_clips: object, max_clips: int) -> str:
    if raw_clips in (None, ""):
        return ""
    if not isinstance(raw_clips, list):
        raise ValueError("selectedClips must be a list.")
    if not raw_clips:
        return ""
    if len(raw_clips) > 30:
        raise ValueError("最多只能手动选择 30 个片段。")

    library = read_material_library()
    items = library.get("items") if isinstance(library.get("items"), dict) else {}
    selected: list[dict[str, Any]] = []
    for index, raw_clip in enumerate(raw_clips[:max_clips], start=1):
        if not isinstance(raw_clip, dict):
            continue
        url = str(raw_clip.get("url") or "").strip()
        if not url:
            continue
        material = items.get(url)
        if not isinstance(material, dict):
            raise ValueError(f"第 {index} 个手动片段不在素材库里，请刷新页面后重新选择。")
        if clean_material_kind(material.get("kind"), url) != "video":
            raise ValueError(f"第 {index} 个手动片段不是视频素材。")

        technical = clean_material_technical(material.get("technical"), "video")
        total_ms = parse_non_negative_int(technical.get("durationMs"))
        start_ms = parse_clip_time_ms(raw_clip.get("startMs", raw_clip.get("sourceStartMs", 0)))
        if "endMs" in raw_clip:
            end_ms = parse_clip_time_ms(raw_clip.get("endMs"))
        elif "sourceEndMs" in raw_clip:
            end_ms = parse_clip_time_ms(raw_clip.get("sourceEndMs"))
        elif "durationMs" in raw_clip:
            end_ms = start_ms + parse_clip_time_ms(raw_clip.get("durationMs"))
        else:
            end_ms = start_ms + 6000

        if end_ms <= start_ms:
            end_ms = start_ms + 6000
        if total_ms:
            start_ms = min(start_ms, max(0, total_ms - 1200))
            end_ms = min(end_ms, total_ms)
        if end_ms - start_ms < 1200:
            raise ValueError(f"第 {index} 个手动片段太短，至少需要 1.2 秒。")

        analysis = material.get("analysis") if isinstance(material.get("analysis"), dict) else {}
        suggestions = analysis.get("suggestions") if isinstance(analysis.get("suggestions"), list) else []
        segments = clean_material_segments(analysis.get("segments"))
        raw_segment_id = str(raw_clip.get("segmentId") or "").strip()[:80]
        matched_segment = next((segment for segment in segments if raw_segment_id and segment.get("id") == raw_segment_id), None)
        if not matched_segment:
            matched_segment = next(
                (
                    segment for segment in segments
                    if abs(parse_non_negative_int(segment.get("startMs")) - start_ms) <= 150
                    and abs(parse_non_negative_int(segment.get("endMs")) - end_ms) <= 150
                ),
                None,
            )
        segment_score = parse_non_negative_int(matched_segment.get("score")) if matched_segment else parse_non_negative_int(raw_clip.get("segmentScore"))
        segment_marks = matched_segment.get("secondMarks") if matched_segment else raw_clip.get("secondMarks")
        raw_segment_tags = clean_tags(raw_clip.get("segmentTags"))
        segment_tags = raw_segment_tags or ((matched_segment or {}).get("tags") if matched_segment else [])
        role = clean_edit_role(raw_clip.get("role") or (matched_segment or {}).get("role") or material.get("editRole"), "video")
        ad_stage = clean_material_ad_stage((matched_segment or {}).get("adStage") or raw_clip.get("adStage"))
        raw_copy_match = raw_clip.get("copyMatch") if isinstance(raw_clip.get("copyMatch"), dict) else {}
        copy_match = {
            "source": str(raw_copy_match.get("source") or "").strip()[:40],
            "type": str(raw_copy_match.get("type") or "").strip()[:40],
            "role": clean_edit_role(raw_copy_match.get("role") or "", "video") if raw_copy_match.get("role") else "",
            "index": parse_non_negative_int(raw_copy_match.get("index")),
            "sourceIndex": parse_non_negative_int(raw_copy_match.get("sourceIndex")),
            "label": str(raw_copy_match.get("label") or "").strip()[:120],
        } if raw_copy_match else {}
        selected.append(
            {
                "order": index - 1,
                "url": url,
                "name": str(material.get("name") or material_display_name(url)).strip()[:220],
                "sourcePath": str(material.get("sourcePath") or material.get("externalPath") or "").strip(),
                "obsidianPath": str(material.get("obsidianPath") or "").strip(),
                "sourceUrl": str(material.get("sourceUrl") or "").strip()[:1000],
                "sourceStartMs": start_ms,
                "sourceEndMs": end_ms,
                "durationMs": end_ms - start_ms,
                "role": role,
                "adStage": ad_stage,
                "adStageLabel": str((matched_segment or {}).get("adStageLabel") or AD_STAGE_LABELS.get(ad_stage, "") or raw_clip.get("adStageLabel") or "").strip()[:40],
                "contentDescription": str((matched_segment or {}).get("contentDescription") or raw_clip.get("contentDescription") or "").strip()[:360],
                "strengths": clean_material_mark_strings((matched_segment or {}).get("strengths") or raw_clip.get("strengths"), 8),
                "risks": clean_material_mark_strings((matched_segment or {}).get("risks") or raw_clip.get("risks"), 8),
                "copyAngle": str((matched_segment or {}).get("copyAngle") or raw_clip.get("copyAngle") or "").strip()[:220],
                "priority": clean_priority(material.get("priority")),
                "qualityScore": clean_quality_score(material.get("qualityScore")),
                "clipUnit": "segment" if matched_segment or raw_clip.get("clipUnit") == "segment" else "manual",
                "segmentId": str((matched_segment or {}).get("id") or raw_segment_id)[:80],
                "segmentScore": segment_score,
                "segmentTags": clean_tags(segment_tags),
                "secondMarks": clean_material_second_marks(segment_marks),
                "tags": clean_tags(material.get("tags")),
                "aiTags": clean_tags(material.get("aiTags") or analysis.get("autoTags")),
                "technical": technical,
                "summary": str(analysis.get("summary") or "").strip()[:1200],
                "suggestions": [str(item).strip()[:260] for item in suggestions[:8] if str(item).strip()],
                "manualNote": str(raw_clip.get("note") or "").strip()[:160],
                "copyText": str(raw_clip.get("copyText") or raw_clip.get("scriptLine") or "").strip()[:500],
                "copyMatch": copy_match,
            }
        )

    if not selected:
        return ""

    DRAFT_REQUEST_DIR.mkdir(parents=True, exist_ok=True)
    request_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    request_path = DRAFT_REQUEST_DIR / f"selected-clips-{request_id}.json"
    request_path.write_text(
        json.dumps({"createdAt": utc_now_iso(), "mode": "manual", "clips": selected}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(request_path)


def run_jianying_draft_generator(payload: dict[str, Any]) -> dict[str, Any]:
    script = JIANYING_DRAFT_GENERATOR_SCRIPT.expanduser()
    skill_root = JIANYING_EDITOR_SKILL_ROOT.expanduser()
    python_bin = JIANYING_PYTHON.expanduser() if JIANYING_PYTHON.expanduser().exists() else Path(sys.executable)
    if not script.exists() or not script.is_file():
        raise ValueError(f"JianYing draft generator script not found: {script}")
    if not (skill_root / "scripts" / "jy_wrapper.py").exists():
        raise ValueError(f"jianying-editor skill is incomplete or missing: {skill_root}")

    try:
        max_clips = int(payload.get("maxClips") or 8)
    except (TypeError, ValueError) as exc:
        raise ValueError("maxClips must be a number.") from exc
    if max_clips < 1 or max_clips > 30:
        raise ValueError("maxClips must be between 1 and 30.")

    selected_clips_file = write_selected_jianying_clips(payload.get("selectedClips"), max_clips)
    if not selected_clips_file and not AUTO_EDIT_POOL_FILE.exists():
        raise ValueError("Auto edit pool not found. Run material analysis first or manually select clips.")

    try:
        max_duration = float(payload.get("maxDuration") or 60)
    except (TypeError, ValueError) as exc:
        raise ValueError("maxDuration must be a number.") from exc
    if max_duration < 5 or max_duration > 300:
        raise ValueError("maxDuration must be between 5 and 300 seconds.")

    target_ratio = str(payload.get("targetRatio") or "auto")
    if target_ratio not in {"auto", "9:16", "16:9"}:
        raise ValueError("targetRatio must be auto, 9:16, or 16:9.")

    edit_pace = str(payload.get("editPace") or "standard").strip().lower()
    if edit_pace not in {"standard", "fast", "calm"}:
        raise ValueError("editPace must be standard, fast, or calm.")

    transition_style = str(payload.get("transitionStyle") or "auto").strip().lower()
    if transition_style not in {"auto", "dynamic", "soft", "minimal"}:
        raise ValueError("transitionStyle must be auto, dynamic, soft, or minimal.")

    caption_style = str(payload.get("captionStyle") or "clean").strip().lower()
    if caption_style not in {"clean", "sales", "none"}:
        raise ValueError("captionStyle must be clean, sales, or none.")

    voice_provider = str(payload.get("voiceProvider") or "edge").strip().lower()
    if voice_provider not in {"jianying", "elevenlabs", "edge"}:
        raise ValueError("voiceProvider must be jianying, elevenlabs, or edge.")

    copy_language = str(payload.get("copyLanguage") or "ja").strip().lower()
    if copy_language not in {"ja", "zh"}:
        raise ValueError("copyLanguage must be ja or zh.")

    default_speaker = "ja-JP-NanamiNeural" if voice_provider == "edge" else "zh_female_xiaopengyou"
    speaker = re.sub(r"[^A-Za-z0-9_\\-]", "", str(payload.get("speaker") or default_speaker).strip())[:120] or default_speaker
    generate_voiceover = bool(payload.get("generateVoiceover", True))
    voiceover_text = str(payload.get("voiceoverText") or "").strip()
    voiceover_text_file = ""
    if voiceover_text:
        DRAFT_REQUEST_DIR.mkdir(parents=True, exist_ok=True)
        request_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        request_path = DRAFT_REQUEST_DIR / f"{request_id}.txt"
        request_path.write_text(voiceover_text[:4000], encoding="utf-8")
        voiceover_text_file = str(request_path)

    runtime_config = read_runtime_config()
    if any(key in payload for key in ("elevenLabsApiKey", "elevenLabsVoiceId", "elevenLabsModel", "clearElevenLabsApiKey")):
        runtime_config = merge_runtime_config_payload(runtime_config, payload)
        write_runtime_config(runtime_config)
    elevenlabs_api_key = get_elevenlabs_api_key(runtime_config)
    elevenlabs_voice_id = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("elevenLabsVoiceId") or get_elevenlabs_voice_id(runtime_config)).strip())[:120]
    elevenlabs_model = re.sub(r"[^A-Za-z0-9_.-]", "", str(payload.get("elevenLabsModel") or get_elevenlabs_model(runtime_config)).strip())[:120] or DEFAULT_ELEVENLABS_MODEL

    command = [
        str(python_bin),
        "-B",
        str(script),
        "--vault-root",
        str(OBSIDIAN_MATERIAL_ROOT),
        "--pool-file",
        str(AUTO_EDIT_POOL_FILE),
        "--skill-root",
        str(skill_root),
        "--target-ratio",
        target_ratio,
        "--edit-pace",
        edit_pace,
        "--transition-style",
        transition_style,
        "--caption-style",
        caption_style,
        "--max-clips",
        str(max_clips),
        "--max-duration",
        str(max_duration),
        "--speaker",
        speaker,
        "--copy-language",
        copy_language,
        "--voice-provider",
        voice_provider,
        "--elevenlabs-voice-id",
        elevenlabs_voice_id,
        "--elevenlabs-model",
        elevenlabs_model,
        "--json",
    ]
    if generate_voiceover:
        command.append("--generate-voiceover")
    if voiceover_text_file:
        command.extend(["--voiceover-text-file", voiceover_text_file])
    if selected_clips_file:
        command.extend(["--selected-clips-file", selected_clips_file])
    draft_name = str(payload.get("draftName") or "").strip()
    if draft_name:
        command.extend(["--draft-name", draft_name[:100]])

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["JY_SKILL_ROOT"] = str(skill_root)
    env["SEEDANCE_OBSIDIAN_MATERIAL_ROOT"] = str(OBSIDIAN_MATERIAL_ROOT)
    if elevenlabs_api_key:
        env["ELEVENLABS_API_KEY"] = elevenlabs_api_key

    try:
        completed = subprocess.run(
            command,
            cwd=str(PROJECT_DIR.parent),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=JIANYING_DRAFT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"JianYing draft generation timed out after {JIANYING_DRAFT_TIMEOUT_SECONDS}s.") from exc
    except OSError as exc:
        raise RuntimeError(f"JianYing draft generator failed to start: {exc}") from exc

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    parsed: dict[str, Any] = {}
    for line in reversed(stdout.splitlines()):
        text = line.strip()
        if not text.startswith("{"):
            continue
        try:
            candidate = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            parsed = candidate
            break

    if completed.returncode != 0 or not parsed.get("ok"):
        reason = parsed.get("error") if isinstance(parsed, dict) else ""
        raise RuntimeError(reason or stderr or stdout or f"JianYing draft generator failed with exit code {completed.returncode}.")

    return {
        "exitCode": completed.returncode,
        "result": parsed,
        "stderr": stderr[-2000:] if stderr else "",
        "stdout": stdout[-2000:] if stdout else "",
        "obsidian": build_obsidian_status(),
    }


def run_rough_cut_generator(payload: dict[str, Any]) -> dict[str, Any]:
    script = ROUGH_CUT_GENERATOR_SCRIPT.expanduser()
    ffmpeg = Path(str(FFMPEG_BIN or "")).expanduser()
    if not script.exists() or not script.is_file():
        raise ValueError(f"Rough cut generator script not found: {script}")
    if not FFMPEG_BIN or not ffmpeg.exists():
        raise ValueError("FFmpeg is not available. Install FFmpeg before exporting rough cuts.")

    try:
        max_clips = int(payload.get("maxClips") or 12)
    except (TypeError, ValueError) as exc:
        raise ValueError("maxClips must be a number.") from exc
    if max_clips < 1 or max_clips > 30:
        raise ValueError("maxClips must be between 1 and 30.")

    selected_clips_file = write_selected_jianying_clips(payload.get("selectedClips"), max_clips)
    if not selected_clips_file:
        raise ValueError("没有可导出的预剪片段，请先确认生成前片段与文案。")

    target_ratio = str(payload.get("targetRatio") or "9:16").strip()
    if target_ratio not in {"9:16", "16:9"}:
        raise ValueError("targetRatio must be 9:16 or 16:9.")

    name = str(payload.get("name") or payload.get("draftName") or "AI预剪素材").strip()[:100]
    command = [
        str(Path(sys.executable)),
        "-B",
        str(script),
        "--vault-root",
        str(OBSIDIAN_MATERIAL_ROOT),
        "--selected-clips-file",
        selected_clips_file,
        "--name",
        name,
        "--target-ratio",
        target_ratio,
        "--ffmpeg",
        str(ffmpeg),
        "--json",
    ]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["SEEDANCE_OBSIDIAN_MATERIAL_ROOT"] = str(OBSIDIAN_MATERIAL_ROOT)

    try:
        completed = subprocess.run(
            command,
            cwd=str(PROJECT_DIR.parent),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=ROUGH_CUT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Rough cut export timed out after {ROUGH_CUT_TIMEOUT_SECONDS}s.") from exc
    except OSError as exc:
        raise RuntimeError(f"Rough cut generator failed to start: {exc}") from exc

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    parsed: dict[str, Any] = {}
    for line in reversed(stdout.splitlines()):
        text = line.strip()
        if not text.startswith("{"):
            continue
        try:
            candidate = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            parsed = candidate
            break

    if completed.returncode != 0 or not parsed.get("ok"):
        reason = parsed.get("error") if isinstance(parsed, dict) else ""
        raise RuntimeError(reason or stderr or stdout or f"Rough cut generator failed with exit code {completed.returncode}.")

    record = parsed.get("record") if isinstance(parsed.get("record"), dict) else {}
    relative_video = str(record.get("relativeVideoPath") or "").strip().lstrip("/")
    if relative_video:
        record["videoUrl"] = f"/{quote(relative_video, safe='/')}"
        record["downloadUrl"] = record["videoUrl"]
    parsed["record"] = record
    return {
        "exitCode": completed.returncode,
        "result": parsed,
        "stderr": stderr[-2000:] if stderr else "",
        "stdout": stdout[-2000:] if stdout else "",
        "obsidian": build_obsidian_status(),
    }


def build_obsidian_status() -> dict[str, Any]:
    return {
        "root": str(OBSIDIAN_MATERIAL_ROOT),
        "libraryFile": str(MATERIAL_LIBRARY_FILE),
        "autoEditPoolFile": str(AUTO_EDIT_POOL_FILE),
        "materialDirectionMonitorFile": str(MATERIAL_DIRECTION_MONITOR_FILE),
        "materialDirectionReportFile": str(MATERIAL_DIRECTION_REPORT_FILE),
        "manualCutDraftFile": str(MANUAL_CUT_DRAFT_FILE),
        "manualCutDraftReportFile": str(MANUAL_CUT_DRAFT_REPORT_FILE),
        "videoCopyLibraryFile": str(VIDEO_COPY_LIBRARY_FILE),
        "videoCopyLibraryIndexFile": str(VIDEO_COPY_LIBRARY_INDEX_FILE),
        "uploadSyncIgnoreFile": str(UPLOAD_SYNC_IGNORE_FILE),
        "jianyingDraftsFile": str(JIANYING_DRAFTS_INDEX_FILE),
        "roughCutsFile": str(ROUGH_CUTS_INDEX_FILE),
        "roughCutsDir": str(OBSIDIAN_ROUGH_CUT_DIR),
        "chatcutExecutorStatusFile": str(CHATCUT_EXECUTOR_STATUS_FILE),
        "runtimeConfigFile": str(PUBLIC_RUNTIME_CONFIG_FILE),
        "authUsersFile": str(PUBLIC_AUTH_USERS_FILE),
        "projectManifestFile": str(PROJECT_MANIFEST_FILE),
        "indexFile": str(MATERIAL_INDEX_FILE),
        "systemIndexFile": str(SYSTEM_INDEX_FILE),
        "analysisDir": str(OBSIDIAN_ANALYSIS_DIR),
        "systemDir": str(OBSIDIAN_SYSTEM_DIR),
        "analyzerScript": str(VIDEO_MATERIAL_ANALYZER_SCRIPT),
        "analyzerAvailable": VIDEO_MATERIAL_ANALYZER_SCRIPT.exists(),
        "jianyingDraftGeneratorScript": str(JIANYING_DRAFT_GENERATOR_SCRIPT),
        "jianyingDraftGeneratorAvailable": JIANYING_DRAFT_GENERATOR_SCRIPT.exists(),
        "jianyingSkillRoot": str(JIANYING_EDITOR_SKILL_ROOT),
        "jianyingSkillAvailable": (JIANYING_EDITOR_SKILL_ROOT / "scripts" / "jy_wrapper.py").exists(),
        "japaneseEditorSkillRoot": str(JAPANESE_EDITOR_SKILL_ROOT),
        "japaneseEditorSkillAvailable": (JAPANESE_EDITOR_SKILL_ROOT / "SKILL.md").exists(),
        "jianyingPython": str(JIANYING_PYTHON),
        "jianyingPythonAvailable": JIANYING_PYTHON.exists(),
        "ffprobeAvailable": bool(FFPROBE_BIN),
        "exists": OBSIDIAN_MATERIAL_ROOT.exists(),
        "secretPolicy": "API Key、密码哈希和 Session Secret 仅保存在本地 .runtime；Obsidian 只保存脱敏索引。",
    }


DIRECTION_ROLE_REQUIREMENTS = {
    "ecommerce": ["hook", "try_on", "detail", "motion", "proof", "ending"],
    "tryon": ["hook", "try_on", "motion", "detail", "proof", "ending"],
    "detail": ["hook", "detail", "proof", "motion", "try_on", "ending"],
}
DIRECTION_ROLE_TERMS = {
    "hook": ("开头", "钩子", "第一眼", "抓注意", "opening", "hook", "注目", "一目"),
    "try_on": ("上身", "试穿", "全身", "正面", "侧面", "背面", "着用", "シルエット", "try_on"),
    "detail": ("细节镜头", "细节特写", "近景", "局部", "看清", "close-up", "ディテール", "クローズアップ"),
    "motion": ("走动", "走路", "行走", "转身", "摆动", "抬腿", "动作", "垂感", "歩", "ターン", "揺れ", "落ち感", "motion"),
    "proof": ("显瘦", "显腿长", "遮肉", "修饰", "舒适", "百搭", "垂感", "证明", "細見え", "脚", "カバー", "着回し", "proof"),
    "transition": ("转场", "过渡", "切换", "节奏", "transition", "テンポ"),
    "ending": ("结尾", "收尾", "召回", "商品页", "点击", "下单", "cta", "ending", "チェック"),
}


def read_material_direction_monitor() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if MATERIAL_DIRECTION_MONITOR_FILE.exists():
        try:
            data = json.loads(MATERIAL_DIRECTION_MONITOR_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return write_material_direction_monitor({"scope": "all", "style": "ecommerce"})


def clean_monitor_urls(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item or "").strip() for item in value if str(item or "").strip()}


def material_direction_items(library: dict[str, Any], payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_items = material_entries(normalize_material_library(library))
    scope = str(payload.get("scope") or "all").strip().lower()
    style = str(payload.get("style") or "ecommerce").strip().lower()
    if style not in DIRECTION_ROLE_REQUIREMENTS:
        style = "ecommerce"
    urls = clean_monitor_urls(payload.get("urls"))
    batch_id = str(payload.get("batchId") or "").strip()
    if urls:
        scoped = [item for item in all_items if str(item.get("url") or "") in urls]
        scope_label = "当前页面筛选"
    elif scope == "current" and batch_id:
        scoped = [item for item in all_items if str(item.get("batchId") or "") == batch_id]
        batch_name = next((str(batch.get("name") or "") for batch in library.get("batches", []) if isinstance(batch, dict) and str(batch.get("id") or "") == batch_id), "")
        scope_label = batch_name or "当前批次"
    else:
        scoped = all_items
        scope_label = "全部素材"
        scope = "all"
    return scoped, {"scope": scope, "style": style, "batchId": batch_id, "scopeLabel": scope_label, "urlCount": len(urls)}


def role_for_direction_clip(clip: dict[str, Any]) -> str:
    role = clean_edit_role(clip.get("editRole") or clip.get("role"), "video")
    return role if role in EDIT_ROLE_LABELS else "unassigned"


def direction_clip_evidence_text(clip: dict[str, Any]) -> str:
    parts: list[str] = [
        str(clip.get("contentDescription") or ""),
        str(clip.get("copyAngle") or ""),
        str(clip.get("adStage") or ""),
        str(clip.get("adStageLabel") or ""),
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
        parts.extend(
            str(mark.get(key) or "")
            for key in ("note", "visualNote", "cutAdvice", "timelineZone")
        )
        for key in ("pros", "cons"):
            values = mark.get(key) if isinstance(mark.get(key), list) else []
            parts.extend(str(value or "") for value in values)
    return " ".join(part for part in parts if part).lower()


def infer_direction_secondary_roles(clip: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    primary = role_for_direction_clip(clip)
    evidence = direction_clip_evidence_text(clip)
    roles: list[str] = []
    reasons: dict[str, str] = {}

    def add(role: str, reason: str) -> None:
        if role != primary and role not in roles:
            roles.append(role)
            reasons[role] = reason

    for role, terms in DIRECTION_ROLE_TERMS.items():
        if any(term in evidence for term in terms):
            add(role, "画面描述或标签命中")

    marks = clip.get("secondMarks") if isinstance(clip.get("secondMarks"), list) else []
    visual_motion = max(
        [parse_non_negative_float(mark.get("visualMotion")) for mark in marks if isinstance(mark, dict)] or [0.0]
    )
    motion_delta = max(
        [parse_non_negative_float(mark.get("motionDelta")) for mark in marks if isinstance(mark, dict)] or [0.0]
    )
    if visual_motion >= 14 or motion_delta >= 0.18:
        add("motion", "逐秒运动量达到动作镜头阈值")

    start_ms = parse_non_negative_int(clip.get("sourceStartMs") or clip.get("segmentStartMs"))
    end_ms = parse_non_negative_int(clip.get("sourceEndMs") or clip.get("segmentEndMs"))
    duration_ms = parse_non_negative_int(clip.get("durationMs")) or max(0, end_ms - start_ms)
    technical = clip.get("technical") if isinstance(clip.get("technical"), dict) else {}
    total_ms = parse_non_negative_int(technical.get("durationMs"))
    smart_score = parse_non_negative_int(clip.get("smartScore"))
    if start_ms <= 2400 and smart_score >= 70:
        add("hook", "位于源视频前段且质量分较高")
    if total_ms and end_ms and end_ms >= max(0, total_ms - 2800) and duration_ms <= 5000 and smart_score >= 65:
        add("ending", "位于源视频尾段，可作为干净收尾")
    if duration_ms and duration_ms <= 2200 and (visual_motion >= 10 or motion_delta >= 0.12):
        add("transition", "短时长且存在画面变化，可作为过渡")
    return roles, reasons


def build_material_direction_monitor(library: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    items, scope_info = material_direction_items(library, payload)
    urls = {str(item.get("url") or "") for item in items if str(item.get("url") or "")}
    pool = build_auto_edit_pool(library)
    pool_clips = pool.get("clips") if isinstance(pool.get("clips"), list) else []
    clips = [
        clip for clip in pool_clips
        if isinstance(clip, dict)
        and (not urls or str(clip.get("url") or "") in urls)
        and parse_non_negative_int(clip.get("smartScore")) >= 55
    ]
    enriched_clips: list[dict[str, Any]] = []
    for clip in clips:
        primary_role = role_for_direction_clip(clip)
        existing_secondary = clip.get("secondaryRoles") if isinstance(clip.get("secondaryRoles"), list) else []
        inferred_secondary, inferred_reasons = infer_direction_secondary_roles(clip)
        secondary_roles = [
            role for role in dict.fromkeys([*existing_secondary, *inferred_secondary])
            if role in EDIT_ROLE_LABELS and role not in {primary_role, "bgm", "unassigned"}
        ]
        enriched_clips.append(
            {
                **clip,
                "primaryRole": primary_role,
                "secondaryRoles": secondary_roles,
                "directionRoles": [primary_role, *secondary_roles],
                "secondaryRoleReasons": inferred_reasons,
            }
        )
    clips = enriched_clips
    role_counts = Counter(str(clip.get("primaryRole") or "unassigned") for clip in clips)
    effective_role_counts: Counter[str] = Counter()
    derived_role_counts: Counter[str] = Counter()
    for clip in clips:
        for role in dict.fromkeys(clip.get("directionRoles") or []):
            effective_role_counts[role] += 1
        for role in clip.get("secondaryRoles") or []:
            derived_role_counts[role] += 1
    required = DIRECTION_ROLE_REQUIREMENTS.get(scope_info["style"], DIRECTION_ROLE_REQUIREMENTS["ecommerce"])
    covered = [role for role in required if effective_role_counts.get(role, 0) > 0]
    missing = [role for role in required if role not in covered]
    derived_only = [role for role in required if not role_counts.get(role, 0) and derived_role_counts.get(role, 0)]
    high_clips = [clip for clip in clips if parse_non_negative_int(clip.get("smartScore")) >= 70]
    excellent_clips = [clip for clip in clips if parse_non_negative_int(clip.get("smartScore")) >= 82]
    average_score = round(sum(parse_non_negative_int(clip.get("smartScore")) for clip in clips) / len(clips)) if clips else 0
    dominant_role = ""
    dominant_count = 0
    if role_counts:
        dominant_role, dominant_count = role_counts.most_common(1)[0]
    dominance_ratio = round(dominant_count / len(clips), 3) if clips else 0

    score = sum(
        8 if role_counts.get(role, 0) else 5 if derived_role_counts.get(role, 0) else 0
        for role in required
    )
    score += min(18, len(high_clips) * 3)
    score += min(12, len(excellent_clips) * 4)
    score += min(12, max(0, average_score - 50) * 0.4)
    score += 10 if len(clips) >= 8 else 6 if len(clips) >= 5 else 0
    if missing:
        score -= len(missing) * 6
    if derived_only:
        score -= len(derived_only) * 2
    if dominance_ratio > 0.45:
        score -= round((dominance_ratio - 0.45) * 40)
    score = max(0, min(100, round(score)))

    if score >= 90:
        grade = "excellent"
        verdict = "方向很好，可以生成正式草稿"
    elif score >= 75:
        grade = "good"
        verdict = "方向可用，适合生成并少量人工调整"
    elif score >= 60:
        grade = "usable"
        verdict = "能生成粗剪，但建议先补强缺口"
    elif score >= 40:
        grade = "weak"
        verdict = "方向偏弱，自动混剪风险较高"
    else:
        grade = "not-ready"
        verdict = "暂不建议自动混剪"

    actions: list[str] = []
    if not clips:
        actions.append("先运行 Skill 分析素材，生成自动混剪候选池。")
    for role in derived_only:
        actions.append(
            f"{EDIT_ROLE_LABELS.get(role, role)}可由 {derived_role_counts.get(role, 0)} 段复合分镜派生：生成草稿时自动截取，但建议人工预览。"
        )
    for role in missing:
        actions.append(f"真正缺少{EDIT_ROLE_LABELS.get(role, role)}：当前素材没有足够画面证据，生成时缩短文案或使用替代镜头。")
    if dominance_ratio > 0.45 and dominant_role:
        actions.append(f"{EDIT_ROLE_LABELS.get(dominant_role, dominant_role)}占比过高：保留最高分片段，其余降级为备用。")
    if average_score and average_score < 55:
        actions.append("候选平均分偏低：优先重跑分析并手动挑选 2-4 秒高光片段。")
    if len(clips) < 5:
        actions.append("可用候选少于 5 段：不建议生成 30 秒以上成片。")
    if not actions:
        actions.append("可直接生成 15-30 秒剪映草稿，再检查文案和画面是否逐段对应。")

    by_source: dict[str, int] = defaultdict(int)
    for clip in clips:
        source = str(clip.get("sourcePath") or clip.get("name") or clip.get("url") or "").strip()
        if source:
            by_source[source] += 1
    repeated_sources = [
        {"source": source, "name": Path(source).name or source[:80], "count": count}
        for source, count in sorted(by_source.items(), key=lambda item: item[1], reverse=True)
        if count >= 3
    ][:8]

    roles = [*required, "transition", "unassigned"]
    role_breakdown = [
        {
            "role": role,
            "label": EDIT_ROLE_LABELS.get(role, role),
            "count": int(effective_role_counts.get(role, 0)),
            "primaryCount": int(role_counts.get(role, 0)),
            "derivedCount": int(derived_role_counts.get(role, 0)),
            "required": role in required,
            "status": "ok" if role_counts.get(role, 0) else "derived" if derived_role_counts.get(role, 0) else "missing",
        }
        for role in roles
    ]
    recommended_duration = 15 if score < 60 or len(missing) >= 2 else 30
    editing_plan = {
        "recommendedDurationSeconds": recommended_duration,
        "recommendedClipCount": 6 if recommended_duration == 15 else 8,
        "maxClipsPerSource": 2,
        "avoidConsecutiveSameRole": True,
        "roleTargets": {
            role: (2 if role == "try_on" else 1) if effective_role_counts.get(role, 0) else 0
            for role in required
        },
    }
    return {
        "version": 2,
        "type": "japanese_fashion_video_editor_direction_monitor",
        "updatedAt": utc_now_iso(),
        "scope": scope_info,
        "score": score,
        "grade": grade,
        "verdict": verdict,
        "materialCount": len(items),
        "candidateCount": len(clips),
        "highCandidateCount": len(high_clips),
        "excellentCandidateCount": len(excellent_clips),
        "averageSmartScore": average_score,
        "requiredRoles": required,
        "coveredRoles": covered,
        "missingRoles": missing,
        "derivedOnlyRoles": derived_only,
        "roleBreakdown": role_breakdown,
        "dominantRole": dominant_role,
        "dominanceRatio": dominance_ratio,
        "repeatedSources": repeated_sources,
        "actions": actions,
        "editingPlan": editing_plan,
        "skill": {
            "name": "japanese-fashion-video-editor",
            "path": str(JAPANESE_EDITOR_SKILL_ROOT),
            "available": (JAPANESE_EDITOR_SKILL_ROOT / "SKILL.md").exists(),
        },
        "obsidianReportPath": str(MATERIAL_DIRECTION_REPORT_FILE.relative_to(OBSIDIAN_MATERIAL_ROOT)),
    }


def material_direction_markdown(monitor: dict[str, Any]) -> str:
    scope = monitor.get("scope") if isinstance(monitor.get("scope"), dict) else {}
    lines = [
        "# 剪辑方向监控",
        "",
        f"- 更新时间：{monitor.get('updatedAt')}",
        f"- 范围：{scope.get('scopeLabel') or '全部素材'}",
        f"- 方向分：{monitor.get('score')} / 100",
        f"- 判断：{monitor.get('verdict')}",
        f"- 素材数：{monitor.get('materialCount')}",
        f"- 可用候选：{monitor.get('candidateCount')}，高分候选：{monitor.get('highCandidateCount')}，优秀候选：{monitor.get('excellentCandidateCount')}",
        f"- 候选平均分：{monitor.get('averageSmartScore')}",
        "",
        "## 角色覆盖",
        "",
        "| 方向 | 主角色 | 可派生 | 合计 | 状态 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in monitor.get("roleBreakdown", []):
        if not isinstance(item, dict):
            continue
        status = "OK" if item.get("status") == "ok" else "可派生" if item.get("status") == "derived" else "缺"
        lines.append(
            f"| {item.get('label')} | {item.get('primaryCount', 0)} | {item.get('derivedCount', 0)} | {item.get('count')} | {status} |"
        )
    editing_plan = monitor.get("editingPlan") if isinstance(monitor.get("editingPlan"), dict) else {}
    if editing_plan:
        lines.extend(
            [
                "",
                "## 推荐成片参数",
                "",
                f"- 建议时长：{editing_plan.get('recommendedDurationSeconds')} 秒",
                f"- 建议片段：{editing_plan.get('recommendedClipCount')} 段",
                f"- 同源片段上限：{editing_plan.get('maxClipsPerSource')} 段",
            ]
        )
    lines.extend(["", "## 导演建议", ""])
    lines.extend(f"- {action}" for action in monitor.get("actions", []) if str(action).strip())
    repeated = monitor.get("repeatedSources") if isinstance(monitor.get("repeatedSources"), list) else []
    if repeated:
        lines.extend(["", "## 重复来源提醒", ""])
        for item in repeated:
            if isinstance(item, dict):
                lines.append(f"- {item.get('name') or item.get('source')}：{item.get('count')} 段")
    lines.append("")
    return "\n".join(lines)


def write_material_direction_monitor(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object.")
    library = read_material_library()
    auto_edit_pool = build_auto_edit_pool(library)
    AUTO_EDIT_POOL_FILE.write_text(json.dumps(auto_edit_pool, ensure_ascii=False, indent=2), encoding="utf-8")
    monitor = build_material_direction_monitor(library, payload)
    MATERIAL_DIRECTION_MONITOR_FILE.write_text(json.dumps(monitor, ensure_ascii=False, indent=2), encoding="utf-8")
    MATERIAL_DIRECTION_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    MATERIAL_DIRECTION_REPORT_FILE.write_text(material_direction_markdown(monitor), encoding="utf-8")
    return monitor


def normalize_manual_cut_draft(value: object) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    raw_clips = source.get("clips") if isinstance(source.get("clips"), list) else []
    clips: list[dict[str, Any]] = []
    for index, raw_clip in enumerate(raw_clips[:30], start=1):
        if not isinstance(raw_clip, dict):
            continue
        url = str(raw_clip.get("url") or "").strip()[:4000]
        start_ms = parse_non_negative_int(raw_clip.get("startMs"))
        end_ms = parse_non_negative_int(raw_clip.get("endMs"))
        if not url or end_ms - start_ms < 1200:
            continue
        clip_id = re.sub(r"[^A-Za-z0-9._:-]+", "-", str(raw_clip.get("id") or f"manual-{index}").strip())[:80].strip("-")
        clips.append(
            {
                "id": clip_id or f"manual-{index}",
                "url": url,
                "startMs": start_ms,
                "endMs": end_ms,
                "clipUnit": "segment" if raw_clip.get("clipUnit") == "segment" else "manual",
                "segmentId": str(raw_clip.get("segmentId") or "").strip()[:80],
                "segmentScore": min(100, parse_non_negative_int(raw_clip.get("segmentScore"))),
                "role": clean_edit_role(raw_clip.get("role") or raw_clip.get("segmentRole"), "video"),
                "tags": clean_tags(raw_clip.get("tags") or raw_clip.get("segmentTags")),
                "note": str(raw_clip.get("note") or "").strip()[:160],
                "order": len(clips),
            }
        )
    return {
        "version": 1,
        "activeBatchId": str(source.get("activeBatchId") or "").strip()[:80],
        "selectedClipId": str(source.get("selectedClipId") or "").strip()[:80],
        "clips": clips,
        "updatedAt": str(source.get("updatedAt") or "").strip()[:40],
    }


def manual_cut_draft_markdown(draft: dict[str, Any]) -> str:
    library = read_material_library()
    items = library.get("items") if isinstance(library.get("items"), dict) else {}
    lines = [
        "# 手动分段草稿",
        "",
        f"> 更新时间：{draft.get('updatedAt') or '未保存'}",
        f"> 片段数量：{len(draft.get('clips') or [])}",
        "",
        "| 顺序 | 素材 | 源时间 | 用途 | 标签 | 备注 |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for index, clip in enumerate(draft.get("clips") or [], start=1):
        material = items.get(clip.get("url")) if isinstance(items, dict) else None
        name = str((material or {}).get("name") or Path(urlparse(str(clip.get("url") or "")).path).name or "视频素材")
        start = parse_non_negative_int(clip.get("startMs")) / 1000
        end = parse_non_negative_int(clip.get("endMs")) / 1000
        tags = "、".join(clean_tags(clip.get("tags"))) or "-"
        role = EDIT_ROLE_LABELS.get(str(clip.get("role") or "unassigned"), "待判断")
        note = str(clip.get("note") or "-").replace("|", "｜").replace("\n", " ")
        lines.append(f"| {index} | {name.replace('|', '｜')} | {start:g}s-{end:g}s | {role} | {tags} | {note} |")
    lines.extend(["", "片段顺序、入点、出点、用途和标签均来自视频素材库的手动分段草稿。", ""])
    return "\n".join(lines)


def read_manual_cut_draft() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if not MANUAL_CUT_DRAFT_FILE.exists():
        return normalize_manual_cut_draft({})
    try:
        value = json.loads(MANUAL_CUT_DRAFT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        value = {}
    return normalize_manual_cut_draft(value)


def write_manual_cut_draft(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("manual cut draft must be an object.")
    ensure_obsidian_material_dirs()
    draft = normalize_manual_cut_draft(value)
    draft["updatedAt"] = utc_now_iso()
    MANUAL_CUT_DRAFT_FILE.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    MANUAL_CUT_DRAFT_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANUAL_CUT_DRAFT_REPORT_FILE.write_text(manual_cut_draft_markdown(draft), encoding="utf-8")
    sync_obsidian_project_data()
    return draft


def read_chatcut_sync_ledger() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if not CHATCUT_SYNC_FILE.exists():
        return normalize_ledger({})
    try:
        return normalize_ledger(json.loads(CHATCUT_SYNC_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return normalize_ledger({})


def write_chatcut_sync_ledger(sync: dict[str, Any]) -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    normalized = normalize_ledger(sync)
    CHATCUT_SYNC_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def create_chatcut_sync_request(payload: dict[str, Any], created_by: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object.")
    sync, request_record = build_sync_request(
        read_material_library(),
        payload,
        read_chatcut_sync_ledger(),
        created_by=created_by,
    )
    return write_chatcut_sync_ledger(sync), request_record


def preview_chatcut_sync_request(payload: dict[str, Any], created_by: str = "") -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object.")
    ledger = read_chatcut_sync_ledger()
    preview_ledger = {
        "version": ledger.get("version", 1),
        "updatedAt": ledger.get("updatedAt", ""),
        "requests": [],
        "assets": ledger.get("assets", []),
    }
    _, request_record = build_sync_request(
        read_material_library(),
        payload,
        preview_ledger,
        created_by=created_by,
    )
    request_record["preview"] = True
    return request_record


def apply_chatcut_sync_update(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object.")
    sync, request_record = update_sync_request(read_chatcut_sync_ledger(), payload)
    return write_chatcut_sync_ledger(sync), request_record


OPERATIONS_REQUIRED_ROLES = ("hook", "try_on", "detail", "motion", "proof", "ending")


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def iso_timestamp(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def chatcut_executor_health(
    status_value: object,
    requests: list[dict[str, Any]],
    *,
    now_timestamp: float | None = None,
) -> dict[str, Any]:
    status = status_value if isinstance(status_value, dict) else {}
    now_value = time.time() if now_timestamp is None else now_timestamp
    last_seen_at = str(status.get("lastSeenAt") or "")
    last_seen_timestamp = iso_timestamp(last_seen_at)
    age_seconds = max(0, int(now_value - last_seen_timestamp)) if last_seen_timestamp else None
    active_requests = [
        request
        for request in requests
        if str(request.get("status") or "") in {"queued", "syncing", "partial"}
    ]
    if age_seconds is not None and age_seconds <= 120:
        health = "online"
        label = "执行器在线"
    elif active_requests:
        health = "offline"
        label = "执行器离线"
    else:
        health = "idle"
        label = "当前无活动任务"
    return {
        "health": health,
        "label": label,
        "lastSeenAt": last_seen_at,
        "ageSeconds": age_seconds,
        "state": str(status.get("state") or "unknown"),
        "action": str(status.get("action") or ""),
        "requestId": str(status.get("requestId") or ""),
        "host": str(status.get("host") or ""),
        "activeRequestCount": len(active_requests),
        "statusFile": obsidian_relative(CHATCUT_EXECUTOR_STATUS_FILE),
    }


def operations_batch_coverage(library: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [item for item in material_entries(library) if clean_material_kind(item.get("kind"), item.get("url")) == "video"]
    batches = [batch for batch in library.get("batches", []) if isinstance(batch, dict)]
    batch_ids = [str(batch.get("id") or "") for batch in batches]
    if any(not str(item.get("batchId") or "") for item in entries):
        batches.append({"id": "", "name": "未分批"})
    result: list[dict[str, Any]] = []
    for batch in batches:
        batch_id = str(batch.get("id") or "")
        batch_items = [item for item in entries if str(item.get("batchId") or "") == batch_id]
        if not batch_items and batch_id not in batch_ids:
            continue
        status_counts = material_status_counts(batch_items)
        usable_items = [item for item in batch_items if clean_analysis_status(item.get("analysisStatus")) == "ready"]
        role_counts = material_role_counts(usable_items)
        role_coverage = [
            {
                "role": role,
                "label": EDIT_ROLE_LABELS.get(role, role),
                "count": int(role_counts.get(role, 0)),
                "status": "ok" if role_counts.get(role, 0) else "missing",
            }
            for role in OPERATIONS_REQUIRED_ROLES
        ]
        missing_roles = [item["role"] for item in role_coverage if item["status"] == "missing"]
        covered_count = len(OPERATIONS_REQUIRED_ROLES) - len(missing_roles)
        quality_values = [clean_quality_score(item.get("qualityScore")) for item in usable_items]
        quality_values = [value for value in quality_values if value > 0]
        result.append(
            {
                "batchId": batch_id,
                "batchName": str(batch.get("name") or "未命名批次"),
                "total": len(batch_items),
                "ready": len(usable_items),
                "queued": int(status_counts.get("queued", 0)),
                "analyzing": int(status_counts.get("analyzing", 0)),
                "hold": int(status_counts.get("hold", 0)),
                "rejected": int(status_counts.get("rejected", 0)),
                "coverageScore": round(covered_count / len(OPERATIONS_REQUIRED_ROLES) * 100),
                "averageQuality": round(sum(quality_values) / len(quality_values), 1) if quality_values else 0,
                "roles": role_coverage,
                "missingRoles": missing_roles,
                "missingLabels": [EDIT_ROLE_LABELS.get(role, role) for role in missing_roles],
            }
        )
    return sorted(result, key=lambda item: (item["ready"] > 0, item["total"], item["batchName"]), reverse=True)


def operations_job_status(category: str, status: object) -> tuple[str, str]:
    value = str(status or "").strip().lower()
    maps = {
        "editing": {
            "assigned": ("queued", "待接单"),
            "in_progress": ("running", "制作中"),
            "review": ("review", "待审核"),
            "revision": ("warning", "需修改"),
            "done": ("done", "已完成"),
            "paused": ("blocked", "已暂停"),
        },
        "chatcut": {
            "queued": ("queued", "待执行"),
            "syncing": ("running", "上传中"),
            "partial": ("warning", "部分完成"),
            "complete": ("done", "已完成"),
            "failed": ("failed", "失败"),
            "blocked": ("blocked", "需处理"),
        },
    }
    return maps.get(category, {}).get(value, ("queued", value or "待处理"))


def build_operations_jobs(
    editing_tasks: list[dict[str, Any]],
    chatcut_requests: list[dict[str, Any]],
    drafts: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for task in editing_tasks:
        tone, label = operations_job_status("editing", task.get("status"))
        jobs.append(
            {
                "id": str(task.get("id") or ""),
                "category": "editing",
                "categoryLabel": "剪辑派单",
                "title": str(task.get("title") or "未命名剪辑任务"),
                "detail": " · ".join(filter(None, [str(task.get("productName") or ""), str(task.get("assignee") or ""), str(task.get("batchName") or "")])),
                "status": tone,
                "statusLabel": label,
                "updatedAt": str(task.get("updatedAt") or task.get("createdAt") or ""),
                "href": "/editing-tasks.html",
            }
        )
    for request in chatcut_requests:
        tone, label = operations_job_status("chatcut", request.get("status"))
        summary = request.get("summary") if isinstance(request.get("summary"), dict) else {}
        imported = int(summary.get("imported", 0) or 0) + int(summary.get("alreadyImported", 0) or 0)
        problems = int(summary.get("failed", 0) or 0) + int(summary.get("unresolved", 0) or 0)
        jobs.append(
            {
                "id": str(request.get("id") or ""),
                "category": "chatcut",
                "categoryLabel": "ChatCut 同步",
                "title": str(request.get("productKey") or "未命名产品"),
                "detail": f"{request.get('batchName') or '未分批'} · 已进入 {imported}/{int(summary.get('total', 0) or 0)}" + (f" · 需处理 {problems}" if problems else ""),
                "status": tone,
                "statusLabel": label,
                "updatedAt": str(request.get("updatedAt") or request.get("createdAt") or ""),
                "href": "/chatcut.html",
            }
        )
    for draft in drafts[-30:]:
        failed_count = int(draft.get("failedCount", 0) or 0) + int(draft.get("transitionFailureCount", 0) or 0) + int(draft.get("voiceFailureCount", 0) or 0)
        director_score = int(draft.get("directorScore", 0) or 0)
        tone = "warning" if failed_count or (director_score and director_score < 60) else "done"
        label = "需复核" if tone == "warning" else "草稿完成"
        jobs.append(
            {
                "id": str(draft.get("id") or ""),
                "category": "draft",
                "categoryLabel": "剪映草稿",
                "title": str(draft.get("draftName") or "未命名草稿"),
                "detail": f"{int(draft.get('clipCount', 0) or 0)} 个片段 · {round(int(draft.get('totalDurationMs', 0) or 0) / 1000, 1)} 秒" + (f" · 导演 {director_score} 分" if director_score else ""),
                "status": tone,
                "statusLabel": label,
                "updatedAt": str(draft.get("createdAt") or ""),
                "href": "/materials.html",
            }
        )
    for batch in coverage:
        if not batch.get("total"):
            continue
        if batch.get("analyzing"):
            tone, label = "running", "分析中"
        elif batch.get("queued"):
            tone, label = "queued", "待分析"
        elif batch.get("missingRoles"):
            tone, label = "warning", "素材有缺口"
        else:
            tone, label = "done", "素材就绪"
        jobs.append(
            {
                "id": f"material-{batch.get('batchId') or 'unbatched'}",
                "category": "analysis",
                "categoryLabel": "素材分析",
                "title": str(batch.get("batchName") or "未命名批次"),
                "detail": f"可剪辑 {batch.get('ready', 0)}/{batch.get('total', 0)} · 覆盖 {batch.get('coverageScore', 0)}%",
                "status": tone,
                "statusLabel": label,
                "updatedAt": "",
                "href": "/materials.html",
            }
        )
    return sorted(jobs, key=lambda item: (iso_timestamp(item.get("updatedAt")), item.get("category") == "analysis"), reverse=True)[:120]


def build_operations_alerts(
    editing_tasks: list[dict[str, Any]],
    executor: dict[str, Any],
    coverage: list[dict[str, Any]],
    drafts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if executor.get("health") == "offline":
        alerts.append({"tone": "critical", "title": "ChatCut 执行器离线", "detail": f"{executor.get('activeRequestCount', 0)} 个同步任务正在等待执行。", "href": "/chatcut.html"})
    now_value = time.time()
    overdue = [task for task in editing_tasks if task.get("dueAt") and str(task.get("status")) != "done" and iso_timestamp(f"{task.get('dueAt')}T23:59:59+08:00") < now_value]
    if overdue:
        alerts.append({"tone": "critical", "title": f"{len(overdue)} 个剪辑任务已逾期", "detail": "请优先处理截止日期已过的派单。", "href": "/editing-tasks.html"})
    for batch in coverage:
        if not batch.get("total"):
            continue
        missing = batch.get("missingLabels") or []
        if missing:
            alerts.append({"tone": "warning", "title": f"{batch.get('batchName')} 缺少 {len(missing)} 类镜头", "detail": "、".join(missing), "href": "/materials.html"})
        if batch.get("queued") or batch.get("analyzing"):
            alerts.append({"tone": "info", "title": f"{batch.get('batchName')} 还有素材未分析", "detail": f"待分析 {batch.get('queued', 0)} · 分析中 {batch.get('analyzing', 0)}", "href": "/materials.html"})
    low_score_drafts = [draft for draft in drafts[-20:] if 0 < int(draft.get("directorScore", 0) or 0) < 60]
    if low_score_drafts:
        alerts.append({"tone": "warning", "title": f"{len(low_score_drafts)} 个近期草稿导演评分偏低", "detail": "建议补齐镜头角色后重新生成。", "href": "/materials.html"})
    return alerts[:12]


def data_file_health(path: Path, label: str, warning_bytes: int) -> dict[str, Any]:
    size = path.stat().st_size if path.exists() and path.is_file() else 0
    return {
        "label": label,
        "path": obsidian_relative(path),
        "bytes": size,
        "sizeMb": round(size / (1024 * 1024), 1),
        "status": "warning" if size >= warning_bytes else "ok",
    }


def build_operations_center(user: dict[str, Any] | None = None) -> dict[str, Any]:
    library = read_material_library(hydrate_metadata=False)
    editing_tasks = editing_tasks_for_user(user)
    chatcut_sync = read_chatcut_sync_ledger()
    chatcut_requests = [item for item in chatcut_sync.get("requests", []) if isinstance(item, dict)]
    draft_payload = read_json_object(JIANYING_DRAFTS_INDEX_FILE)
    drafts = [item for item in draft_payload.get("drafts", []) if isinstance(item, dict)] if isinstance(draft_payload.get("drafts"), list) else []
    coverage = operations_batch_coverage(library)
    executor = chatcut_executor_health(read_json_object(CHATCUT_EXECUTOR_STATUS_FILE), chatcut_requests)
    jobs = build_operations_jobs(editing_tasks, chatcut_requests, drafts, coverage)
    alerts = build_operations_alerts(editing_tasks, executor, coverage, drafts)
    status_counts = Counter(str(job.get("status") or "queued") for job in jobs)
    return {
        "version": 1,
        "type": "seedance_operations_center",
        "updatedAt": utc_now_iso(),
        "metrics": {
            "active": sum(status_counts.get(status, 0) for status in ("queued", "running", "review")),
            "attention": sum(status_counts.get(status, 0) for status in ("warning", "blocked", "failed")),
            "completed": status_counts.get("done", 0),
            "materialsReady": sum(int(batch.get("ready", 0)) for batch in coverage),
            "drafts": len(drafts),
        },
        "executor": executor,
        "jobs": jobs,
        "alerts": alerts,
        "coverage": coverage,
        "dataHealth": [
            data_file_health(MATERIAL_LIBRARY_FILE, "素材库索引", 50 * 1024 * 1024),
            data_file_health(AUTO_EDIT_POOL_FILE, "自动剪辑素材池", 100 * 1024 * 1024),
            data_file_health(CHATCUT_SYNC_FILE, "ChatCut 同步记录", 20 * 1024 * 1024),
            data_file_health(JIANYING_DRAFTS_INDEX_FILE, "剪映草稿索引", 20 * 1024 * 1024),
            data_file_health(ROUGH_CUTS_INDEX_FILE, "预剪素材索引", 20 * 1024 * 1024),
        ],
        "obsidian": {
            "root": str(OBSIDIAN_MATERIAL_ROOT),
            "executorStatusFile": obsidian_relative(CHATCUT_EXECUTOR_STATUS_FILE),
        },
    }


def ensure_obsidian_material_dirs() -> None:
    OBSIDIAN_MATERIAL_ROOT.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_BATCH_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_ROUGH_CUT_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_PLAYBACK_PROXY_DIR.mkdir(parents=True, exist_ok=True)
    if not ROUGH_CUTS_INDEX_FILE.exists():
        write_obsidian_json(ROUGH_CUTS_INDEX_FILE, {"version": 1, "updatedAt": "", "roughCuts": []})
    for kind in MATERIAL_UPLOAD_CONFIGS:
        upload_dir_for(kind).mkdir(parents=True, exist_ok=True)
    migrate_legacy_uploads_to_obsidian()


def migrate_legacy_uploads_to_obsidian() -> None:
    for kind in MATERIAL_UPLOAD_CONFIGS:
        legacy_dir = legacy_upload_dir_for(kind)
        if not legacy_dir.exists() or not legacy_dir.is_dir():
            continue
        upload_dir = upload_dir_for(kind)
        for source in legacy_dir.iterdir():
            if not source.is_file():
                continue
            target = upload_dir / source.name
            if not target.exists():
                shutil.copy2(source, target)


def read_material_library(*, hydrate_metadata: bool = True) -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if not MATERIAL_LIBRARY_FILE.exists():
        return normalize_material_library({})
    try:
        data = json.loads(MATERIAL_LIBRARY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return normalize_material_library({})
    library = normalize_material_library(data if isinstance(data, dict) else {})
    if hydrate_metadata and hydrate_material_library_metadata(library):
        return save_material_library(library)
    return library


def save_material_library(library: dict[str, Any]) -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    normalized = normalize_material_library(library)
    MATERIAL_LIBRARY_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    write_auto_edit_pool_file(normalized)
    write_material_markdown_files(normalized)
    sync_obsidian_project_data(library=normalized)
    return normalized


def upload_sync_keys_for_material(url: str, item: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for value in (item.get("obsidianPath"), item.get("localPath")):
        text = str(value or "").strip().replace("\\", "/").lstrip("/")
        if text.startswith("uploads/"):
            keys.add(text)
    parsed_path = urlparse(str(url or "")).path.replace("\\", "/").lstrip("/")
    if parsed_path.startswith("uploads/"):
        keys.add(parsed_path)
    return keys


def read_upload_sync_ignore() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if not UPLOAD_SYNC_IGNORE_FILE.exists():
        return {"version": 1, "paths": [], "updatedAt": ""}
    try:
        data = json.loads(UPLOAD_SYNC_IGNORE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "paths": [], "updatedAt": ""}
    raw_paths = data.get("paths") if isinstance(data, dict) else []
    paths = sorted({
        str(path or "").strip().replace("\\", "/").lstrip("/")
        for path in raw_paths
        if str(path or "").strip().replace("\\", "/").lstrip("/").startswith("uploads/")
    })
    return {
        "version": 1,
        "paths": paths,
        "updatedAt": str(data.get("updatedAt") or "") if isinstance(data, dict) else "",
    }


def add_upload_sync_ignores(paths: set[str], reason: str = "") -> int:
    clean_paths = {
        str(path or "").strip().replace("\\", "/").lstrip("/")
        for path in paths
        if str(path or "").strip().replace("\\", "/").lstrip("/").startswith("uploads/")
    }
    if not clean_paths:
        return 0
    current = read_upload_sync_ignore()
    before = set(current.get("paths") or [])
    merged = sorted(before | clean_paths)
    write_obsidian_json(
        UPLOAD_SYNC_IGNORE_FILE,
        {
            "version": 1,
            "updatedAt": utc_now_iso(),
            "reason": reason,
            "paths": merged,
        },
    )
    return len(set(merged) - before)


def clear_material_library() -> dict[str, Any]:
    current = read_material_library()
    cleared_at = utc_now_iso()
    previous_count = len(material_entries(current))
    previous_pool = read_auto_edit_pool()
    upload_ignore_paths: set[str] = set()
    for url, item in (current.get("items") or {}).items():
        if isinstance(item, dict):
            upload_ignore_paths.update(upload_sync_keys_for_material(str(url), item))
    ignored_upload_count = add_upload_sync_ignores(upload_ignore_paths, "clear-material-library")
    library = save_material_library(
        {
            "version": 1,
            "updatedAt": cleared_at,
            "activeId": "batch-default",
            "filterBatchId": "all",
            "filterTag": "all",
            "batches": [{"id": "batch-default", "name": "默认批次", "createdAt": cleared_at}],
            "items": {},
        }
    )
    write_manual_cut_draft({"activeBatchId": "batch-default", "clips": []})
    return {
        "library": library,
        "clearedAt": cleared_at,
        "clearedCount": previous_count,
        "clearedAutoPoolCount": parse_non_negative_int(previous_pool.get("clipCount")),
        "ignoredUploadCount": ignored_upload_count,
        "obsidian": build_obsidian_status(),
        "deletePolicy": "只清空素材库索引和自动混剪候选池，不删除 NAS 原文件、上传视频文件、分析报告或剪映草稿。",
    }


def read_auto_edit_pool() -> dict[str, Any]:
    ensure_obsidian_material_dirs()
    if AUTO_EDIT_POOL_FILE.exists():
        try:
            data = json.loads(AUTO_EDIT_POOL_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    pool = build_auto_edit_pool(read_material_library())
    write_obsidian_json(AUTO_EDIT_POOL_FILE, pool)
    return pool


def write_auto_edit_pool_file(library: dict[str, Any]) -> dict[str, Any]:
    pool = build_auto_edit_pool(library)
    write_obsidian_json(AUTO_EDIT_POOL_FILE, pool)
    return pool


def auto_edit_smart_signal(item: dict[str, Any], analysis: dict[str, Any], technical: dict[str, Any]) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []
    penalties: list[str] = []

    quality = clean_quality_score(item.get("qualityScore"))
    score += quality * 12
    if quality >= 4:
        reasons.append(f"质量评分 {quality}/5")
    elif quality <= 2:
        penalties.append(f"质量评分偏低 {quality}/5")

    priority = clean_priority(item.get("priority"))
    priority_score = {"high": 15, "normal": 7, "low": -6}.get(priority, 0)
    score += priority_score
    if priority == "high":
        reasons.append("高优先级素材")
    elif priority == "low":
        penalties.append("低优先级素材")

    status = clean_analysis_status(item.get("analysisStatus"))
    score += 8 if status == "ready" else 4
    if status == "ready":
        reasons.append("状态已标记可剪辑")

    role = clean_edit_role(item.get("editRole"), "video")
    if role in {"hook", "try_on", "detail", "motion", "proof"}:
        score += 6
        reasons.append(f"用途明确：{EDIT_ROLE_LABELS.get(role, role)}")
    elif role in {"transition", "ending"}:
        score += 3
        reasons.append(f"可作为{EDIT_ROLE_LABELS.get(role, role)}")
    else:
        score -= 8
        penalties.append("剪辑用途未判断")

    width = parse_non_negative_int(technical.get("width"))
    height = parse_non_negative_int(technical.get("height"))
    pixels = width * height
    orientation = clean_material_orientation(technical.get("orientation"), width, height, "video")
    if orientation == "portrait":
        score += 8
        reasons.append("竖屏适合短视频混剪")
    elif orientation == "square":
        score += 5
        reasons.append("方形画幅可用于短视频")
    elif orientation == "landscape":
        score += 1
    else:
        score -= 5
        penalties.append("画幅未知")

    if pixels >= 1080 * 1920:
        score += 10
        reasons.append("1080p 级别清晰度")
    elif pixels >= 720 * 1280:
        score += 8
        reasons.append("720p+ 清晰度")
    elif pixels >= 540 * 960:
        score += 4
    else:
        score -= 8
        penalties.append("分辨率偏低")

    duration_ms = parse_non_negative_int(technical.get("durationMs"))
    if 2500 <= duration_ms <= 12000:
        score += 10
        reasons.append("时长适合直接混剪")
    elif 12000 < duration_ms <= 30000:
        score += 7
        reasons.append("时长适合截取高光段")
    elif 1500 <= duration_ms < 2500:
        score += 5
        reasons.append("短片段适合转场或节奏点")
    elif 30000 < duration_ms <= 60000:
        score += 2
        penalties.append("时长偏长，需要依赖智能截取")
    elif duration_ms > 60000:
        score -= 12
        penalties.append("长视频需要先拆条")
    else:
        score -= 20
        penalties.append("视频时长过短或缺失")

    fps = parse_non_negative_float(technical.get("fps"))
    if fps >= 24:
        score += 4
    elif fps >= 15:
        score += 2
    else:
        score -= 5
        penalties.append("帧率偏低")

    bitrate = parse_non_negative_int(technical.get("bitrateKbps"))
    if bitrate >= 2500:
        score += 5
        reasons.append("码率较高")
    elif bitrate >= 800:
        score += 3
    elif bitrate and bitrate < 300:
        score -= 8
        penalties.append("码率偏低")

    if technical.get("hasAudio"):
        score += 2

    frame_index = analysis.get("frameIndex") if isinstance(analysis.get("frameIndex"), dict) else {}
    indexed_frames = parse_non_negative_int(frame_index.get("indexedFrames"))
    total_frames = parse_non_negative_int(frame_index.get("totalFrames"))
    if frame_index.get("complete") and indexed_frames:
        score += 8
        reasons.append("帧索引完整")
    elif indexed_frames:
        score += 5
        reasons.append("具备帧级索引")
    elif analysis.get("keyframes"):
        score += 3
        reasons.append("具备关键帧")
    else:
        score -= 10
        penalties.append("缺少帧级分析证据")
    if total_frames and indexed_frames and indexed_frames < total_frames * 0.5:
        score -= 5
        penalties.append("帧索引覆盖不足")

    cut_hints = analysis.get("cutHints") if isinstance(analysis.get("cutHints"), list) else []
    segments = analysis.get("segments") if isinstance(analysis.get("segments"), list) else []
    valid_hints = [
        hint for hint in cut_hints
        if isinstance(hint, dict) and parse_non_negative_int(hint.get("endMs")) - parse_non_negative_int(hint.get("startMs")) >= 1200
    ]
    if valid_hints:
        best_confidence = max(parse_non_negative_float(hint.get("confidence")) for hint in valid_hints)
        score += min(10, best_confidence * 10)
        reasons.append("已有 AI 推荐剪辑片段")
    else:
        score -= 3
        penalties.append("缺少 AI 截取建议")
    valid_segments = [
        segment for segment in segments
        if isinstance(segment, dict) and parse_non_negative_int(segment.get("endMs")) - parse_non_negative_int(segment.get("startMs")) >= 1200
    ]
    if valid_segments:
        best_segment_score = max(parse_non_negative_int(segment.get("score")) for segment in valid_segments)
        score += min(12, best_segment_score / 10)
        reasons.append(f"已拆分 {len(valid_segments)} 个智能片段")
    else:
        penalties.append("未拆分片段")

    tags = set(clean_tags([*clean_tags(item.get("tags")), *clean_tags(item.get("aiTags")), *clean_tags(analysis.get("autoTags"))]))
    for tag, bonus in {"优先混剪": 8, "可剪辑": 5, "高清": 4, "帧级索引": 4, "废片": -25, "异常": -15}.items():
        if tag in tags:
            score += bonus
            if bonus > 0:
                reasons.append(f"标签命中：{tag}")
            else:
                penalties.append(f"标签命中：{tag}")

    smart_score = max(0, min(100, int(round(score))))
    if smart_score >= 82:
        tier = "excellent"
    elif smart_score >= 70:
        tier = "preferred"
    elif smart_score >= 55:
        tier = "usable"
    else:
        tier = "review"
    return {
        "smartScore": smart_score,
        "smartTier": tier,
        "autoEditEligible": smart_score >= 55,
        "smartReasons": reasons[:8],
        "smartPenalties": penalties[:8],
    }


def build_segment_clip(item: dict[str, Any], analysis: dict[str, Any], technical: dict[str, Any], base_clip: dict[str, Any], smart: dict[str, Any], segment: dict[str, Any]) -> dict[str, Any]:
    segment_score = parse_non_negative_int(segment.get("score"))
    combined_score = max(0, min(100, int(round(smart.get("smartScore", 0) * 0.45 + segment_score * 0.55))))
    start_ms = parse_non_negative_int(segment.get("startMs"))
    end_ms = parse_non_negative_int(segment.get("endMs"))
    role = clean_edit_role(segment.get("role") or base_clip.get("editRole"), "video")
    reason = str(segment.get("reason") or "智能拆分片段。").strip()
    clip = {
        **base_clip,
        "clipUnit": "segment",
        "segmentId": str(segment.get("id") or f"{start_ms}-{end_ms}")[:80],
        "segmentStartMs": start_ms,
        "segmentEndMs": end_ms,
        "sourceStartMs": start_ms,
        "sourceEndMs": end_ms,
        "durationMs": max(0, end_ms - start_ms),
        "editRole": role,
        "adStage": clean_material_ad_stage(segment.get("adStage")),
        "adStageLabel": str(segment.get("adStageLabel") or "").strip()[:40],
        "contentDescription": str(segment.get("contentDescription") or "").strip()[:360],
        "strengths": clean_material_mark_strings(segment.get("strengths"), 8),
        "risks": clean_material_mark_strings(segment.get("risks"), 8),
        "copyAngle": str(segment.get("copyAngle") or "").strip()[:220],
        "segmentScore": segment_score,
        "smartScore": combined_score,
        "smartTier": "excellent" if combined_score >= 82 else "preferred" if combined_score >= 70 else "usable" if combined_score >= 55 else "review",
        "autoEditEligible": combined_score >= 55,
        "smartReasons": [reason, *smart.get("smartReasons", [])][:8],
        "smartPenalties": smart.get("smartPenalties", []),
        "secondMarks": segment.get("secondMarks") if isinstance(segment.get("secondMarks"), list) else [],
        "segmentTags": clean_tags(segment.get("tags")),
        "cutHints": [
            {
                "startMs": start_ms,
                "endMs": end_ms,
                "role": role,
                "confidence": min(1.0, parse_non_negative_float(segment.get("confidence")) or combined_score / 100),
                "reason": reason,
            }
        ],
    }
    secondary_roles, secondary_reasons = infer_direction_secondary_roles(clip)
    clip["primaryRole"] = role
    clip["secondaryRoles"] = secondary_roles
    clip["directionRoles"] = [role, *secondary_roles]
    clip["secondaryRoleReasons"] = secondary_reasons
    return clip


def build_auto_edit_pool(library: dict[str, Any]) -> dict[str, Any]:
    clips = []
    for item in material_entries(normalize_material_library(library)):
        if clean_material_kind(item.get("kind")) != "video":
            continue
        if clean_analysis_status(item.get("analysisStatus")) not in {"ready", "analyzed"}:
            continue
        analysis = clean_material_analysis(item.get("analysis"), item.get("analysisStatus"))
        technical = clean_material_technical(item.get("technical"), "video")
        frame_index = analysis.get("frameIndex") if isinstance(analysis.get("frameIndex"), dict) else {}
        has_frame_evidence = bool(
            analysis.get("frameCount")
            or analysis.get("keyframes")
            or parse_non_negative_int(frame_index.get("indexedFrames"))
        )
        if parse_non_negative_int(item.get("size")) and parse_non_negative_int(item.get("size")) < 1024:
            continue
        if not technical.get("durationMs") or not technical.get("width") or not technical.get("height"):
            continue
        if not has_frame_evidence:
            continue
        smart = auto_edit_smart_signal(item, analysis, technical)
        if not smart["autoEditEligible"]:
            continue
        base_clip = {
            "url": item.get("url", ""),
            "name": item.get("name", ""),
            "status": clean_analysis_status(item.get("analysisStatus")),
            "editRole": clean_edit_role(item.get("editRole"), "video"),
            "priority": clean_priority(item.get("priority")),
            "qualityScore": clean_quality_score(item.get("qualityScore")),
            "tags": clean_tags(item.get("tags")),
            "aiTags": clean_tags(item.get("aiTags") or analysis.get("autoTags")),
            "technical": technical,
            "summary": analysis.get("summary", ""),
            "suggestions": analysis.get("suggestions", []),
            "keyframes": analysis.get("keyframes", []),
            "frameIndex": analysis.get("frameIndex", {}),
            "editingProfile": analysis.get("editingProfile", {}),
            "adProfile": analysis.get("adProfile", {}),
            "secondMarks": analysis.get("secondMarks", []),
            "cutHints": analysis.get("cutHints", []),
            "segments": analysis.get("segments", []),
            "obsidianPath": item.get("obsidianPath", ""),
            "sourcePath": str(resolve_material_source_path(item) or ""),
            "updatedAt": analysis.get("updatedAt", ""),
            "clipUnit": "video",
            **smart,
        }
        secondary_roles, secondary_reasons = infer_direction_secondary_roles(base_clip)
        base_clip["primaryRole"] = base_clip["editRole"]
        base_clip["secondaryRoles"] = secondary_roles
        base_clip["directionRoles"] = [base_clip["editRole"], *secondary_roles]
        base_clip["secondaryRoleReasons"] = secondary_reasons
        segments = analysis.get("segments") if isinstance(analysis.get("segments"), list) else []
        segment_clips = [
            build_segment_clip(item, analysis, technical, base_clip, smart, segment)
            for segment in segments[:40]
            if isinstance(segment, dict) and parse_non_negative_int(segment.get("score")) >= 55
        ]
        if segment_clips:
            clips.extend(segment_clips)
        else:
            clips.append(base_clip)
    clips.sort(key=lambda item: (item.get("smartScore", 0), {"high": 3, "normal": 2, "low": 1}.get(item["priority"], 0), item["qualityScore"]), reverse=True)
    return {
        "version": 1,
        "type": "seedance_auto_edit_material_pool",
        "scoring": {
            "version": 2,
            "mode": "segment-smart-quality-auto-edit",
            "minimumSmartScore": 55,
            "description": "自动把视频拆成几秒片段，根据每秒帧数据、质量分、优先级、画幅清晰度、时长、帧索引、cutHints 和 AI 标签筛选混剪素材。",
        },
        "updatedAt": utc_now_iso(),
        "libraryRoot": str(OBSIDIAN_MATERIAL_ROOT),
        "materialCount": len(material_entries(library)),
        "clipCount": len(clips),
        "clips": clips,
    }


def query_material_library(payload: dict[str, Any]) -> dict[str, Any]:
    library = read_material_library()
    kind = str(payload.get("kind") or "video").strip()
    if kind not in {"all", "image", "video", "audio"}:
        raise ValueError("kind must be all, image, video, or audio.")
    statuses = clean_query_values(payload.get("statuses") or payload.get("status") or ["ready", "analyzed"], set(ANALYSIS_STATUS_LABELS))
    roles = clean_query_values(payload.get("roles") or payload.get("role"), set(EDIT_ROLE_LABELS))
    required_tags = clean_tags(payload.get("tags") or payload.get("tag"))
    orientation = str(payload.get("orientation") or "").strip()
    if orientation and orientation not in {"portrait", "landscape", "square", "audio", "unknown"}:
        raise ValueError("orientation is invalid.")
    min_score = clean_quality_score(payload.get("minScore"))
    query = str(payload.get("query") or "").strip().lower()
    limit = parse_non_negative_int(payload.get("limit") or 40)
    limit = min(max(limit, 1), 200)

    matches = []
    for item in material_entries(library):
        item_kind = clean_material_kind(item.get("kind"))
        if kind != "all" and item_kind != kind:
            continue
        status = clean_analysis_status(item.get("analysisStatus"))
        if statuses and status not in statuses:
            continue
        role = clean_edit_role(item.get("editRole"), item_kind)
        if roles and role not in roles:
            continue
        score = clean_quality_score(item.get("qualityScore"))
        if min_score and score < min_score:
            continue
        technical = clean_material_technical(item.get("technical"), item_kind)
        if orientation and technical.get("orientation") != orientation:
            continue
        analysis = clean_material_analysis(item.get("analysis"), status)
        all_tags = clean_tags([*clean_tags(item.get("tags")), *clean_tags(item.get("aiTags")), *clean_tags(analysis.get("autoTags"))])
        smart = auto_edit_smart_signal(item, analysis, technical) if item_kind == "video" else {}
        if required_tags and not all(tag in all_tags for tag in required_tags):
            continue
        haystack = " ".join(
            [
                str(item.get("name") or ""),
                str(item.get("url") or ""),
                str(item.get("notes") or ""),
                str(analysis.get("summary") or ""),
                f"智能分 {smart.get('smartScore', 0)}",
                " ".join(all_tags),
            ]
        ).lower()
        if query and query not in haystack:
            continue
        matches.append(
            {
                "url": item.get("url"),
                "name": item.get("name"),
                "kind": item_kind,
                "status": status,
                "editRole": role,
                "priority": clean_priority(item.get("priority")),
                "qualityScore": score,
                "tags": clean_tags(item.get("tags")),
                "aiTags": all_tags,
                "technical": technical,
                "analysis": analysis,
                "smartScore": smart.get("smartScore", 0),
                "smartTier": smart.get("smartTier", ""),
                "autoEditEligible": smart.get("autoEditEligible", False),
                "smartReasons": smart.get("smartReasons", []),
                "smartPenalties": smart.get("smartPenalties", []),
                "obsidianPath": item.get("obsidianPath", ""),
                "sourceUrl": item.get("sourceUrl", ""),
                "importMethod": item.get("importMethod", ""),
                "sourcePath": str(resolve_material_source_path(item) or ""),
            }
        )
    matches.sort(key=lambda item: (item.get("smartScore", 0), {"high": 3, "normal": 2, "low": 1}.get(item["priority"], 0), item["qualityScore"]), reverse=True)
    return {"count": len(matches), "items": matches[:limit], "library": library}


def clean_query_values(value: object, allowed: set[str]) -> list[str]:
    if value is None or value == "":
        return []
    raw = value if isinstance(value, list) else str(value).replace(",", " ").replace("，", " ").split()
    cleaned = []
    for item in raw:
        text = str(item).strip()
        if text in allowed and text not in cleaned:
            cleaned.append(text)
    return cleaned


def normalize_material_library(value: dict[str, Any]) -> dict[str, Any]:
    raw_batches = value.get("batches") if isinstance(value.get("batches"), list) else []
    batches = []
    seen_batch_ids: set[str] = set()
    for raw_batch in raw_batches:
        if not isinstance(raw_batch, dict):
            continue
        batch_id = clean_material_id(raw_batch.get("id")) or f"batch-{uuid.uuid4().hex[:10]}"
        if batch_id in seen_batch_ids:
            continue
        seen_batch_ids.add(batch_id)
        name = str(raw_batch.get("name") or "默认批次").strip()[:80] or "默认批次"
        batches.append(
            {
                "id": batch_id,
                "name": name,
                "createdAt": str(raw_batch.get("createdAt") or utc_now_iso()),
            }
        )
    if not batches:
        batches.append({"id": f"batch-{uuid.uuid4().hex[:10]}", "name": "默认批次", "createdAt": utc_now_iso()})

    raw_items = value.get("items") if isinstance(value.get("items"), dict) else {}
    items: dict[str, dict[str, Any]] = {}
    for url, raw_item in raw_items.items():
        if not isinstance(raw_item, dict):
            continue
        clean_url = str(url or "").strip()
        if not clean_url:
            continue
        batch_id = str(raw_item.get("batchId") or "").strip()
        if batch_id and not any(batch["id"] == batch_id for batch in batches):
            batch_id = ""
        kind = clean_material_kind(raw_item.get("kind"), clean_url)
        analysis_status = clean_analysis_status(raw_item.get("analysisStatus") or raw_item.get("status"))
        raw_analysis = raw_item.get("analysis") if isinstance(raw_item.get("analysis"), dict) else {}
        items[clean_url] = {
            "batchId": batch_id,
            "tags": clean_tags(raw_item.get("tags")),
            "aiTags": clean_tags(raw_item.get("aiTags") or raw_analysis.get("autoTags")),
            "kind": kind,
            "name": str(raw_item.get("name") or material_display_name(clean_url)).strip()[:220],
            "size": parse_non_negative_int(raw_item.get("size")),
            "contentType": str(raw_item.get("contentType") or "").strip()[:120],
            "localPath": str(raw_item.get("localPath") or "").strip(),
            "obsidianPath": str(raw_item.get("obsidianPath") or "").strip(),
            "sourcePath": str(raw_item.get("sourcePath") or "").strip()[:2000],
            "externalPath": str(raw_item.get("externalPath") or "").strip()[:2000],
            "sourceUrl": str(raw_item.get("sourceUrl") or "").strip()[:1000],
            "importMethod": str(raw_item.get("importMethod") or "").strip()[:80],
            "importedAt": str(raw_item.get("importedAt") or "").strip()[:40],
            "technical": clean_material_technical(raw_item.get("technical"), kind),
            "analysisStatus": analysis_status,
            "editRole": clean_edit_role(raw_item.get("editRole") or raw_item.get("clipRole") or raw_item.get("role"), kind),
            "priority": clean_priority(raw_item.get("priority")),
            "qualityScore": clean_quality_score(raw_item.get("qualityScore")),
            "notes": clean_material_notes(raw_item.get("notes")),
            "analysis": clean_material_analysis(raw_analysis, analysis_status),
            "addedAt": str(raw_item.get("addedAt") or utc_now_iso()),
        }

    active_id = str(value.get("activeId") or "").strip()
    if not any(batch["id"] == active_id for batch in batches):
        active_id = batches[0]["id"]
    filter_batch_id = str(value.get("filterBatchId") or "all").strip()
    if filter_batch_id not in {"all", "current", "unbatched"} and not any(batch["id"] == filter_batch_id for batch in batches):
        filter_batch_id = "all"

    return {
        "version": 1,
        "updatedAt": utc_now_iso(),
        "activeId": active_id,
        "filterBatchId": filter_batch_id,
        "filterTag": str(value.get("filterTag") or "all").strip()[:80] or "all",
        "batches": batches,
        "items": items,
    }


def upsert_material_library_item(library: dict[str, Any], url: str, patch: dict[str, Any]) -> None:
    normalized = normalize_material_library(library)
    library.clear()
    library.update(normalized)
    clean_url = str(url or "").strip()
    if not clean_url:
        return
    previous = dict(library.get("items", {}).get(clean_url) or {})
    previous.update(patch)
    previous["tags"] = clean_tags(previous.get("tags"))
    previous["aiTags"] = clean_tags(previous.get("aiTags"))
    previous["kind"] = clean_material_kind(previous.get("kind"), clean_url)
    previous["name"] = str(previous.get("name") or material_display_name(clean_url)).strip()[:220]
    previous["size"] = parse_non_negative_int(previous.get("size"))
    previous["contentType"] = str(previous.get("contentType") or "").strip()[:120]
    previous["localPath"] = str(previous.get("localPath") or "").strip()
    previous["obsidianPath"] = str(previous.get("obsidianPath") or "").strip()
    previous["sourcePath"] = str(previous.get("sourcePath") or "").strip()[:2000]
    previous["externalPath"] = str(previous.get("externalPath") or "").strip()[:2000]
    previous["sourceUrl"] = str(previous.get("sourceUrl") or "").strip()[:1000]
    previous["importMethod"] = str(previous.get("importMethod") or "").strip()[:80]
    previous["importedAt"] = str(previous.get("importedAt") or "").strip()[:40]
    previous["analysisStatus"] = clean_analysis_status(previous.get("analysisStatus") or previous.get("status"))
    previous["editRole"] = clean_edit_role(previous.get("editRole") or previous.get("clipRole") or previous.get("role"), previous["kind"])
    previous["priority"] = clean_priority(previous.get("priority"))
    previous["qualityScore"] = clean_quality_score(previous.get("qualityScore"))
    previous["notes"] = clean_material_notes(previous.get("notes"))
    previous["technical"] = clean_material_technical(previous.get("technical"), previous["kind"])
    previous["analysis"] = clean_material_analysis(previous.get("analysis"), previous["analysisStatus"])
    previous["addedAt"] = str(previous.get("addedAt") or utc_now_iso())
    library.setdefault("items", {})[clean_url] = previous


def active_material_batch(library: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_material_library(library)
    library.clear()
    library.update(normalized)
    active_id = library.get("activeId")
    for batch in library.get("batches", []):
        if batch["id"] == active_id:
            return batch
    return library["batches"][0]


def clean_material_id(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]+", "-", str(value or "").strip())[:80].strip("-")


def clean_tags(value: object) -> list[str]:
    if isinstance(value, list):
        raw = " ".join(str(item) for item in value)
    else:
        raw = str(value or "")
    for separator in [",", "，", "、", "#", "\n", "\r", "\t"]:
        raw = raw.replace(separator, " ")
    tags = []
    for item in raw.split(" "):
        tag = item.strip()[:32]
        if tag and tag not in tags:
            tags.append(tag)
    return tags[:24]


def clean_material_kind(value: object, url: str = "") -> str:
    kind = str(value or "").strip()
    if kind in {"image", "video", "audio"}:
        return kind
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".mp4", ".mov", ".webm", ".m4v"}:
        return "video"
    if suffix in {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}:
        return "audio"
    return "image"


def clean_analysis_status(value: object) -> str:
    status = str(value or "").strip()
    return status if status in ANALYSIS_STATUS_LABELS else "queued"


def clean_edit_role(value: object, kind: str = "image") -> str:
    role = str(value or "").strip()
    if role in EDIT_ROLE_LABELS:
        return role
    return "bgm" if kind == "audio" else "unassigned"


def clean_priority(value: object) -> str:
    priority = str(value or "").strip()
    return priority if priority in PRIORITY_LABELS else "normal"


def clean_quality_score(value: object) -> int:
    try:
        score = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return score if 0 <= score <= 5 else 0


def clean_material_notes(value: object) -> str:
    return str(value or "").strip()[:500]


def clean_material_analysis(value: object, status: str = "queued") -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    suggestions = source.get("suggestions")
    keyframes = source.get("keyframes")
    auto_tags = source.get("autoTags")
    return {
        "status": clean_analysis_status(source.get("status") or status),
        "frameCount": parse_non_negative_int(source.get("frameCount")),
        "keyframes": keyframes[:120] if isinstance(keyframes, list) else [],
        "summary": str(source.get("summary") or "").strip()[:1200],
        "suggestions": [str(item).strip()[:260] for item in suggestions[:40] if str(item).strip()] if isinstance(suggestions, list) else [],
        "autoTags": clean_tags(auto_tags),
        "frameIndex": clean_material_frame_index(source.get("frameIndex")),
        "editingProfile": source.get("editingProfile") if isinstance(source.get("editingProfile"), dict) else {},
        "adProfile": clean_material_ad_profile(source.get("adProfile")),
        "secondMarks": clean_material_second_marks(source.get("secondMarks"), 600),
        "cutHints": clean_material_cut_hints(source.get("cutHints")),
        "segments": clean_material_segments(source.get("segments")),
        "updatedAt": str(source.get("updatedAt") or "").strip()[:40],
    }


def clean_material_frame_index(value: object) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    return {
        "path": str(source.get("path") or "").strip()[:260],
        "mode": str(source.get("mode") or "").strip()[:80],
        "totalFrames": parse_non_negative_int(source.get("totalFrames")),
        "indexedFrames": parse_non_negative_int(source.get("indexedFrames")),
        "complete": bool(source.get("complete")),
        "maxRecords": parse_non_negative_int(source.get("maxRecords")),
    }


def clean_material_ad_stage(value: object) -> str:
    stage = str(value or "").strip()
    return stage if stage in AD_STAGE_LABELS else ""


def clean_material_ad_profile(value: object) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    stage_coverage = source.get("stageCoverage") if isinstance(source.get("stageCoverage"), dict) else {}
    stage_best_scores = source.get("stageBestScores") if isinstance(source.get("stageBestScores"), dict) else {}
    return {
        "version": parse_non_negative_int(source.get("version")) or 1,
        "adScore": min(100, parse_non_negative_int(source.get("adScore"))),
        "qualityTier": str(source.get("qualityTier") or "").strip()[:4],
        "primaryStage": clean_material_ad_stage(source.get("primaryStage")),
        "primaryStageLabel": str(source.get("primaryStageLabel") or "").strip()[:40],
        "stageCoverage": {clean_material_ad_stage(key) or str(key)[:40]: parse_non_negative_int(value) for key, value in stage_coverage.items()},
        "stageBestScores": {clean_material_ad_stage(key) or str(key)[:40]: min(100, parse_non_negative_int(value)) for key, value in stage_best_scores.items()},
        "productType": str(source.get("productType") or "").strip()[:40],
        "productSignals": clean_material_mark_strings(source.get("productSignals"), 12),
        "contentSummary": str(source.get("contentSummary") or "").strip()[:360],
        "strengths": clean_material_mark_strings(source.get("strengths"), 8),
        "risks": clean_material_mark_strings(source.get("risks"), 8),
        "bestSegmentIds": clean_material_mark_strings(source.get("bestSegmentIds"), 12),
        "recommendedTags": clean_material_mark_strings(source.get("recommendedTags"), 12),
    }


def clean_material_cut_hints(value: object) -> list[dict[str, Any]]:
    hints = value if isinstance(value, list) else []
    cleaned: list[dict[str, Any]] = []
    for item in hints[:24]:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "startMs": parse_non_negative_int(item.get("startMs")),
                "endMs": parse_non_negative_int(item.get("endMs")),
                "role": str(item.get("role") or "").strip()[:40],
                "confidence": min(1.0, parse_non_negative_float(item.get("confidence"))),
                "reason": str(item.get("reason") or "").strip()[:220],
            }
        )
    return cleaned


def clean_material_mark_strings(value: object, limit: int = 4) -> list[str]:
    raw = value if isinstance(value, list) else []
    return [str(item).strip()[:80] for item in raw[:limit] if str(item).strip()]


def clean_material_second_marks(value: object, limit: int = 12) -> list[dict[str, Any]]:
    marks = value if isinstance(value, list) else []
    cleaned: list[dict[str, Any]] = []
    clean_limit = max(0, min(parse_non_negative_int(limit), 600))
    for item in marks[:clean_limit]:
        if not isinstance(item, dict):
            continue
        tone = str(item.get("tone") or "").strip()
        if tone not in {"good", "ok", "warn", "bad"}:
            tone = "ok"
        cleaned.append(
            {
                "second": parse_non_negative_int(item.get("second")),
                "startMs": parse_non_negative_int(item.get("startMs")),
                "endMs": parse_non_negative_int(item.get("endMs")),
                "frameCount": parse_non_negative_int(item.get("frameCount")),
                "keyFrames": parse_non_negative_int(item.get("keyFrames")),
                "avgPacketSize": parse_non_negative_int(item.get("avgPacketSize")),
                "relativePacket": parse_non_negative_float(item.get("relativePacket")),
                "motionDelta": parse_non_negative_float(item.get("motionDelta")),
                "timelineZone": str(item.get("timelineZone") or "").strip()[:40],
                "brightness": parse_non_negative_float(item.get("brightness")),
                "contrast": parse_non_negative_float(item.get("contrast")),
                "sharpness": parse_non_negative_float(item.get("sharpness")),
                "visualMotion": parse_non_negative_float(item.get("visualMotion")),
                "visualNote": str(item.get("visualNote") or "").strip()[:120],
                "score": min(100, parse_non_negative_int(item.get("score"))),
                "note": str(item.get("note") or "").strip()[:120],
                "pros": clean_material_mark_strings(item.get("pros")),
                "cons": clean_material_mark_strings(item.get("cons")),
                "cutAdvice": str(item.get("cutAdvice") or "").strip()[:220],
                "tone": tone,
            }
        )
    return cleaned


def clean_material_segments(value: object) -> list[dict[str, Any]]:
    segments = value if isinstance(value, list) else []
    cleaned: list[dict[str, Any]] = []
    for index, item in enumerate(segments[:120], start=1):
        if not isinstance(item, dict):
            continue
        start_ms = parse_non_negative_int(item.get("startMs"))
        end_ms = parse_non_negative_int(item.get("endMs"))
        duration_ms = parse_non_negative_int(item.get("durationMs")) or max(0, end_ms - start_ms)
        if end_ms <= start_ms or duration_ms < 800:
            continue
        score = min(100, parse_non_negative_int(item.get("score")))
        cleaned.append(
            {
                "id": clean_material_id(item.get("id")) or f"seg-{index:03d}",
                "startMs": start_ms,
                "endMs": end_ms,
                "durationMs": duration_ms,
                "role": clean_edit_role(item.get("role"), "video"),
                "adStage": clean_material_ad_stage(item.get("adStage")),
                "adStageLabel": str(item.get("adStageLabel") or "").strip()[:40],
                "score": score,
                "confidence": min(1.0, parse_non_negative_float(item.get("confidence"))),
                "reason": str(item.get("reason") or "").strip()[:260],
                "contentDescription": str(item.get("contentDescription") or "").strip()[:360],
                "strengths": clean_material_mark_strings(item.get("strengths"), 8),
                "risks": clean_material_mark_strings(item.get("risks"), 8),
                "copyAngle": str(item.get("copyAngle") or "").strip()[:220],
                "secondMarks": clean_material_second_marks(item.get("secondMarks")),
                "tags": clean_tags(item.get("tags")),
            }
        )
    cleaned.sort(key=lambda segment: (segment["score"], segment["confidence"]), reverse=True)
    return cleaned


def parse_non_negative_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def parse_non_negative_float(value: object) -> float:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    if number < 0 or number == float("inf") or number != number:
        return 0.0
    return number


def clean_material_orientation(value: object, width: int, height: int, kind: str = "image") -> str:
    orientation = str(value or "").strip()
    if kind == "audio":
        return "audio"
    if orientation in {"portrait", "landscape", "square", "unknown"}:
        return orientation
    if width and height:
        if width == height:
            return "square"
        return "landscape" if width > height else "portrait"
    return "unknown"


def clean_material_technical(value: object, kind: str = "image") -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    width = parse_non_negative_int(source.get("width"))
    height = parse_non_negative_int(source.get("height"))
    duration_ms = parse_non_negative_int(source.get("durationMs") or source.get("duration"))
    fps = round(parse_non_negative_float(source.get("fps")), 3)
    bitrate_kbps = parse_non_negative_int(source.get("bitrateKbps") or source.get("bitrate"))
    return {
        "width": width,
        "height": height,
        "durationMs": duration_ms,
        "fps": fps,
        "bitrateKbps": bitrate_kbps,
        "orientation": clean_material_orientation(source.get("orientation"), width, height, kind),
        "hasAudio": bool(source.get("hasAudio")) if kind == "video" else kind == "audio",
        "videoCodec": str(source.get("videoCodec") or "").strip()[:80],
        "audioCodec": str(source.get("audioCodec") or "").strip()[:80],
    }


def technical_metadata_is_empty(technical: dict[str, Any]) -> bool:
    return not any(
        [
            technical.get("width"),
            technical.get("height"),
            technical.get("durationMs"),
            technical.get("fps"),
            technical.get("bitrateKbps"),
            technical.get("videoCodec"),
            technical.get("audioCodec"),
        ]
    )


def merge_material_technical(current: dict[str, Any], extracted: dict[str, Any], kind: str) -> dict[str, Any]:
    current_clean = clean_material_technical(current, kind)
    extracted_clean = clean_material_technical(extracted, kind)
    orientation = current_clean["orientation"]
    if orientation == "unknown":
        orientation = extracted_clean["orientation"]
    return clean_material_technical(
        {
            "width": current_clean["width"] or extracted_clean["width"],
            "height": current_clean["height"] or extracted_clean["height"],
            "durationMs": current_clean["durationMs"] or extracted_clean["durationMs"],
            "fps": current_clean["fps"] or extracted_clean["fps"],
            "bitrateKbps": current_clean["bitrateKbps"] or extracted_clean["bitrateKbps"],
            "orientation": orientation,
            "hasAudio": current_clean["hasAudio"] or extracted_clean["hasAudio"] or kind == "audio",
            "videoCodec": current_clean["videoCodec"] or extracted_clean["videoCodec"],
            "audioCodec": current_clean["audioCodec"] or extracted_clean["audioCodec"],
        },
        kind,
    )


def parse_duration_ms(value: object) -> int:
    seconds = parse_non_negative_float(value)
    return int(round(seconds * 1000)) if seconds else 0


def parse_frame_rate(value: object) -> float:
    raw = str(value or "").strip()
    if not raw or raw == "0/0":
        return 0.0
    if "/" in raw:
        numerator, denominator = raw.split("/", 1)
        denominator_value = parse_non_negative_float(denominator)
        if not denominator_value:
            return 0.0
        return round(parse_non_negative_float(numerator) / denominator_value, 3)
    return round(parse_non_negative_float(raw), 3)


def resolve_material_source_path(item: dict[str, Any]) -> Path | None:
    root = OBSIDIAN_MATERIAL_ROOT.resolve()
    for key in ("sourcePath", "externalPath"):
        raw_path = str(item.get(key) or "").strip()
        if raw_path:
            candidate = Path(raw_path).expanduser()
            if candidate.exists() and candidate.is_file():
                return candidate
    obsidian_path = str(item.get("obsidianPath") or "").strip()
    if obsidian_path:
        candidate = (OBSIDIAN_MATERIAL_ROOT / obsidian_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            candidate = None
        if candidate and candidate.exists() and candidate.is_file():
            return candidate
    local_path = str(item.get("localPath") or "").strip()
    if local_path.startswith("/uploads/"):
        parsed_path = urlparse(local_path).path
        for upload_kind in MATERIAL_UPLOAD_CONFIGS:
            prefix = f"/uploads/{upload_kind}/"
            if parsed_path.startswith(prefix):
                try:
                    return resolve_upload_target(upload_kind, parsed_path.removeprefix(prefix))
                except ValueError:
                    return None
    return None


def find_material_entry_for_playback(requested_url: str, library: dict[str, Any] | None = None) -> dict[str, Any] | None:
    value = str(requested_url or "").strip()
    if not value:
        return None
    material_library = library if isinstance(library, dict) else read_material_library(hydrate_metadata=False)
    items = material_library.get("items") if isinstance(material_library.get("items"), dict) else {}
    if value in items and isinstance(items[value], dict):
        return {"url": value, **items[value]}
    requested_path = unquote(urlparse(value).path).replace("\\", "/")
    for url, raw_item in items.items():
        if not isinstance(raw_item, dict):
            continue
        item_paths = {
            unquote(urlparse(str(url)).path).replace("\\", "/"),
            unquote(urlparse(str(raw_item.get("localPath") or "")).path).replace("\\", "/"),
        }
        if requested_path and requested_path in item_paths:
            return {"url": str(url), **raw_item}
    return None


def resolve_material_playback_source(requested_url: str, library: dict[str, Any] | None = None) -> tuple[dict[str, Any], Path]:
    item = find_material_entry_for_playback(requested_url, library)
    if not item or clean_material_kind(item.get("kind"), requested_url) != "video":
        raise FileNotFoundError("Video material is not registered in the library.")
    source = resolve_material_source_path(item)
    if not source or not source.exists() or not source.is_file():
        raise FileNotFoundError("Video source file is unavailable on this computer or NAS.")
    return item, source


def material_needs_playback_proxy(item: dict[str, Any]) -> bool:
    technical = clean_material_technical(item.get("technical"), "video")
    codec = str(technical.get("videoCodec") or "").strip().lower()
    return bool(codec and codec not in {"h264", "avc1", "vp8", "vp9", "av1"})


def playback_proxy_path(source: Path) -> Path:
    stat = source.stat()
    fingerprint = "|".join(
        [
            os.path.normcase(str(source.resolve())),
            str(stat.st_size),
            str(stat.st_mtime_ns),
            "browser-h264-v1",
        ]
    )
    proxy_id = hashlib.sha256(fingerprint.encode("utf-8", errors="ignore")).hexdigest()[:32]
    return OBSIDIAN_PLAYBACK_PROXY_DIR / f"{proxy_id}.mp4"


def browser_playback_proxy_command(source: Path, output: Path) -> list[str]:
    if not FFMPEG_BIN:
        raise ValueError("FFmpeg is unavailable; cannot create an H.264 browser preview.")
    return [
        str(FFMPEG_BIN),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-sn",
        "-dn",
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(output),
    ]


def ensure_browser_playback_video(source: Path, item: dict[str, Any]) -> Path:
    if not material_needs_playback_proxy(item):
        return source
    target = playback_proxy_path(source)
    if target.exists() and target.is_file() and target.stat().st_size > 0:
        return target
    with PLAYBACK_PROXY_LOCK:
        if target.exists() and target.is_file() and target.stat().st_size > 0:
            return target
        OBSIDIAN_PLAYBACK_PROXY_DIR.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.stem}-{uuid.uuid4().hex[:8]}.tmp.mp4")
        command = browser_playback_proxy_command(source, temporary)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=PLAYBACK_PROXY_TIMEOUT_SECONDS,
                check=False,
            )
            if completed.returncode != 0 or not temporary.exists() or temporary.stat().st_size <= 0:
                detail = (completed.stderr or completed.stdout or "FFmpeg returned no output.").strip()[-600:]
                raise ValueError(f"Failed to create browser-compatible preview: {detail}")
            temporary.replace(target)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Creating the browser-compatible preview timed out.") from exc
        except OSError as exc:
            raise ValueError(f"Unable to create browser-compatible preview: {exc}") from exc
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)
    return target


def extract_material_technical(file_path: Path, kind: str) -> dict[str, Any]:
    if not FFPROBE_BIN or not file_path.exists() or not file_path.is_file():
        return clean_material_technical({}, kind)
    command = [
        FFPROBE_BIN,
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration,bit_rate:format=duration,bit_rate",
        "-of",
        "json",
        str(file_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return clean_material_technical({}, kind)
    if result.returncode != 0 or not result.stdout.strip():
        return clean_material_technical({}, kind)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return clean_material_technical({}, kind)
    streams = payload.get("streams") if isinstance(payload.get("streams"), list) else []
    format_payload = payload.get("format") if isinstance(payload.get("format"), dict) else {}
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), streams[0] if streams else {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    bitrate_value = parse_non_negative_float(format_payload.get("bit_rate") or video_stream.get("bit_rate") or audio_stream.get("bit_rate"))
    extracted = {
        "width": parse_non_negative_int(video_stream.get("width")),
        "height": parse_non_negative_int(video_stream.get("height")),
        "durationMs": parse_duration_ms(format_payload.get("duration") or video_stream.get("duration") or audio_stream.get("duration")),
        "fps": parse_frame_rate(video_stream.get("avg_frame_rate")),
        "bitrateKbps": int(round(bitrate_value / 1000)) if bitrate_value else 0,
        "hasAudio": bool(audio_stream) or kind == "audio",
        "videoCodec": str(video_stream.get("codec_name") or "").strip()[:80],
        "audioCodec": str(audio_stream.get("codec_name") or "").strip()[:80],
    }
    return clean_material_technical(extracted, kind)


def hydrate_material_library_metadata(library: dict[str, Any]) -> bool:
    changed = False
    for url, item in (library.get("items") or {}).items():
        kind = clean_material_kind(item.get("kind"), url)
        technical = clean_material_technical(item.get("technical"), kind)
        source_path = resolve_material_source_path(item)
        if source_path and source_path.exists() and source_path.is_file():
            if not parse_non_negative_int(item.get("size")):
                file_size = parse_non_negative_int(source_path.stat().st_size)
                if file_size and item.get("size") != file_size:
                    item["size"] = file_size
                    changed = True
            extracted = extract_material_technical(source_path, kind)
            merged = merge_material_technical(technical, extracted, kind)
            if merged != technical:
                item["technical"] = merged
                changed = True
            else:
                item["technical"] = technical
        else:
            item["technical"] = technical
    return changed


def material_display_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name if parsed.path else ""
    return name or parsed.netloc or "素材"


def write_obsidian_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def obsidian_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(OBSIDIAN_MATERIAL_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    if root.is_file():
        return 1
    return sum(1 for path in root.rglob("*") if path.is_file())


def build_public_runtime_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    raw_config = read_runtime_config() if config is None else config
    public_config = build_config_response(raw_config)["config"]
    for section_name in ("ark", "ai", "elevenlabs"):
        section = public_config.get(section_name)
        if isinstance(section, dict):
            section.pop("apiKeyPreview", None)
    asset_base_url = str(get_config_section("assets", raw_config).get("publicBaseUrl") or os.environ.get("ASSET_PUBLIC_BASE_URL", "")).strip().rstrip("/")
    public_config["assets"] = {
        "publicBaseUrl": asset_base_url,
        "hasPublicBaseUrl": bool(asset_base_url),
    }
    return {
        "version": 1,
        "type": "seedance_public_runtime_config",
        "updatedAt": utc_now_iso(),
        "config": public_config,
        "redaction": {
            "secretsStoredInObsidian": False,
            "note": "真实 API Key 不写入 Obsidian；这里仅保留是否已配置。",
        },
    }


def build_public_auth_users(config: dict[str, Any] | None = None) -> dict[str, Any]:
    auth_config = read_auth_config() if config is None else config
    users = [public_auth_user(user) for user in auth_users(auth_config)] if auth_config else []
    return {
        "version": 1,
        "type": "seedance_public_auth_users",
        "updatedAt": utc_now_iso(),
        "mode": "environment" if auth_config and auth_config.get("mode") == "env" else "local_file",
        "userCount": len(users),
        "users": users,
        "redaction": {
            "passwordHashesStoredInObsidian": False,
            "sessionSecretsStoredInObsidian": False,
            "note": "Obsidian 只保存账号管理索引，不保存密码哈希、盐值或 Session Secret。",
        },
    }


def build_project_manifest(
    library: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    auth_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    material_library = normalize_material_library(library) if library is not None else read_material_library()
    items = material_entries(material_library)
    status_counts = material_status_counts(items)
    editing_task_payload = read_editing_tasks_payload()
    editing_tasks = editing_task_payload.get("tasks", [])
    upload_counts = {kind: count_files(upload_dir_for(kind)) for kind in MATERIAL_UPLOAD_CONFIGS}
    legacy_upload_counts = {kind: count_files(legacy_upload_dir_for(kind)) for kind in MATERIAL_UPLOAD_CONFIGS}
    return {
        "version": 1,
        "type": "seedance_obsidian_project_manifest",
        "updatedAt": utc_now_iso(),
        "vaultRoot": str(OBSIDIAN_MATERIAL_ROOT),
        "dataFiles": {
            "materialLibrary": obsidian_relative(MATERIAL_LIBRARY_FILE),
            "autoEditPool": obsidian_relative(AUTO_EDIT_POOL_FILE),
            "manualCutDraft": obsidian_relative(MANUAL_CUT_DRAFT_FILE),
            "manualCutDraftReport": obsidian_relative(MANUAL_CUT_DRAFT_REPORT_FILE),
            "videoCopyLibrary": obsidian_relative(VIDEO_COPY_LIBRARY_FILE),
            "videoCopyLibraryIndex": obsidian_relative(VIDEO_COPY_LIBRARY_INDEX_FILE),
            "roughCuts": obsidian_relative(ROUGH_CUTS_INDEX_FILE),
            "runtimeConfigPublic": obsidian_relative(PUBLIC_RUNTIME_CONFIG_FILE),
            "authUsersPublic": obsidian_relative(PUBLIC_AUTH_USERS_FILE),
            "editingTasks": obsidian_relative(EDITING_TASKS_FILE),
            "editingTaskBoard": obsidian_relative(EDITING_TASKS_REPORT_FILE),
            "projectManifest": obsidian_relative(PROJECT_MANIFEST_FILE),
            "materialIndex": obsidian_relative(MATERIAL_INDEX_FILE),
            "systemIndex": obsidian_relative(SYSTEM_INDEX_FILE),
        },
        "directories": {
            "uploads": obsidian_relative(OBSIDIAN_UPLOAD_ROOT),
            "analysis": obsidian_relative(OBSIDIAN_ANALYSIS_DIR),
            "roughCuts": obsidian_relative(OBSIDIAN_ROUGH_CUT_DIR),
            "playbackCache": obsidian_relative(OBSIDIAN_PLAYBACK_PROXY_DIR),
            "batches": obsidian_relative(OBSIDIAN_BATCH_DIR),
            "system": obsidian_relative(OBSIDIAN_SYSTEM_DIR),
        },
        "counts": {
            "batches": len(material_library.get("batches", [])),
            "materials": len(items),
            "status": status_counts,
            "obsidianUploads": upload_counts,
            "legacyRuntimeUploadsCopiedFrom": legacy_upload_counts,
            "analysisFiles": count_files(OBSIDIAN_ANALYSIS_DIR),
            "roughCutFiles": count_files(OBSIDIAN_ROUGH_CUT_DIR),
            "playbackProxyFiles": count_files(OBSIDIAN_PLAYBACK_PROXY_DIR),
            "accounts": len(auth_users(auth_config or read_auth_config())),
            "editingTasks": len(editing_tasks),
            "editingTaskStatus": editing_task_status_counts(editing_tasks),
        },
        "runtime": {
            "arkConfigured": bool(get_api_key(config)),
            "aiConfigured": bool(get_ai_api_key(config)),
            "videoAnalyzerAvailable": VIDEO_MATERIAL_ANALYZER_SCRIPT.exists(),
            "roughCutGeneratorAvailable": ROUGH_CUT_GENERATOR_SCRIPT.exists(),
            "ffmpegAvailable": bool(FFMPEG_BIN),
            "ffprobeAvailable": bool(FFPROBE_BIN),
        },
        "secretPolicy": {
            "keptLocalOnly": [
                str(AUTH_FILE),
                str(SESSION_SECRET_FILE),
                f"{CONFIG_FILE} 中的 API Key 字段",
            ],
            "reason": "这些是登录凭据或第三方 API 密钥，不适合写入可浏览的 Obsidian 笔记库。",
        },
    }


def write_system_index_markdown(manifest: dict[str, Any], runtime_public: dict[str, Any], auth_public: dict[str, Any]) -> None:
    counts = manifest.get("counts", {})
    data_files = manifest.get("dataFiles", {})
    directories = manifest.get("directories", {})
    runtime = manifest.get("runtime", {})
    lines = [
        "---",
        "type: seedance_system_index",
        f"updated_at: {manifest.get('updatedAt')}",
        f"material_count: {counts.get('materials', 0)}",
        f"account_count: {counts.get('accounts', 0)}",
        f"editing_task_count: {counts.get('editingTasks', 0)}",
        "---",
        "",
        "# 网站数据总览",
        "",
        "## 数据入口",
        "",
        f"- 素材库 JSON：`{data_files.get('materialLibrary')}`",
        f"- 自动剪辑素材池：`{data_files.get('autoEditPool')}`",
        f"- 预剪素材索引：`{data_files.get('roughCuts')}`",
        f"- 剪辑任务 JSON：`{data_files.get('editingTasks')}`",
        f"- 剪辑任务看板：[[{Path(str(data_files.get('editingTaskBoard', 'system/剪辑任务看板.md'))).with_suffix('').as_posix()}]]",
        f"- 公开运行配置：`{data_files.get('runtimeConfigPublic')}`",
        f"- 公开账号索引：`{data_files.get('authUsersPublic')}`",
        f"- 项目 Manifest：`{data_files.get('projectManifest')}`",
        f"- 素材库总览：[[{Path(str(data_files.get('materialIndex', '素材库总览.md'))).with_suffix('').as_posix()}]]",
        "",
        "## 文件目录",
        "",
        f"- 上传素材：`{directories.get('uploads')}`",
        f"- AI 分析与抽帧：`{directories.get('analysis')}`",
        f"- 文案匹配预剪素材：`{directories.get('roughCuts')}`",
        f"- 批次笔记：`{directories.get('batches')}`",
        f"- 系统索引：`{directories.get('system')}`",
        "",
        "## 当前状态",
        "",
        f"- 批次数：{counts.get('batches', 0)}",
        f"- 素材数：{counts.get('materials', 0)}",
        f"- 账号数：{counts.get('accounts', 0)}",
        f"- 剪辑任务数：{counts.get('editingTasks', 0)}",
        f"- 分析文件数：{counts.get('analysisFiles', 0)}",
        f"- 预剪素材文件数：{counts.get('roughCutFiles', 0)}",
        f"- Ark / Seedance 配置：{'已配置' if runtime.get('arkConfigured') else '未配置'}",
        f"- AI 分析配置：{'已配置' if runtime.get('aiConfigured') else '未配置'}",
        f"- 视频素材分析脚本：{'可用' if runtime.get('videoAnalyzerAvailable') else '不可用'}",
        f"- FFprobe：{'可用' if runtime.get('ffprobeAvailable') else '不可用'}",
        "",
        "## 素材状态",
        "",
    ]
    status_counts = counts.get("status", {}) if isinstance(counts.get("status"), dict) else {}
    for status, label in ANALYSIS_STATUS_LABELS.items():
        lines.append(f"- {label}：{status_counts.get(status, 0)}")
    task_status_counts = counts.get("editingTaskStatus", {}) if isinstance(counts.get("editingTaskStatus"), dict) else {}
    lines.extend(["", "## 剪辑任务状态", ""])
    for status, label in EDITING_TASK_STATUS_LABELS.items():
        lines.append(f"- {label}：{task_status_counts.get(status, 0)}")
    lines.extend(
        [
            "",
            "## 账号索引",
            "",
        ]
    )
    users = auth_public.get("users") if isinstance(auth_public.get("users"), list) else []
    if users:
        for user in users:
            state = "启用" if user.get("enabled") else "停用"
            lines.append(f"- `{user.get('username')}`：{user.get('role')} / {state} / 最近登录 {user.get('lastLoginAt') or '暂无'}")
    else:
        lines.append("- 暂无账号")
    lines.extend(
        [
            "",
            "## 安全策略",
            "",
            "- Obsidian 保存业务数据、公开索引和脱敏配置。",
            "- API Key、密码哈希、盐值、Session Secret 继续只保存在网站本地 `.runtime`。",
            "- 客户账号只能访问素材库，账号管理仍由管理员权限控制。",
            "",
            "## 运行配置摘要",
            "",
            f"- Seedance 模型：`{runtime_public.get('config', {}).get('ark', {}).get('model', '')}`",
            f"- AI 模型：`{runtime_public.get('config', {}).get('ai', {}).get('model', '')}`",
            f"- 公网素材 Base URL：`{runtime_public.get('config', {}).get('assets', {}).get('publicBaseUrl') or '未配置'}`",
            "",
        ]
    )
    SYSTEM_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYSTEM_INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")


def sync_obsidian_project_data(
    library: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    auth_config: dict[str, Any] | None = None,
) -> None:
    ensure_obsidian_material_dirs()
    runtime_public = build_public_runtime_config(config)
    auth_public = build_public_auth_users(auth_config)
    manifest = build_project_manifest(library=library, config=config, auth_config=auth_config)
    write_obsidian_json(PUBLIC_RUNTIME_CONFIG_FILE, runtime_public)
    write_obsidian_json(PUBLIC_AUTH_USERS_FILE, auth_public)
    write_obsidian_json(PROJECT_MANIFEST_FILE, manifest)
    write_system_index_markdown(manifest, runtime_public, auth_public)


def write_material_markdown_files(library: dict[str, Any]) -> None:
    write_material_index(library)
    write_batch_markdown_files(library)


def write_material_index(library: dict[str, Any]) -> None:
    items = material_entries(library)
    status_counts = material_status_counts(items)
    lines = [
        "---",
        "type: seedance_material_index",
        f"updated_at: {library.get('updatedAt')}",
        f"material_count: {len(items)}",
        "---",
        "",
        "# 素材库总览",
        "",
        f"- Obsidian 根目录：`{OBSIDIAN_MATERIAL_ROOT}`",
        f"- AI 分析目录：`{OBSIDIAN_ANALYSIS_DIR}`",
        f"- 网站数据总览：[[system/{SYSTEM_INDEX_FILE.stem}]]",
        f"- 自动剪辑素材池：`{obsidian_relative(AUTO_EDIT_POOL_FILE)}`",
        f"- 批次数：{len(library.get('batches', []))}",
        f"- 素材数：{len(items)}",
        f"- 待 AI 分析：{status_counts.get('queued', 0)}",
        f"- 已分析：{status_counts.get('analyzed', 0)}",
        f"- 可剪辑：{status_counts.get('ready', 0)}",
        "",
        "## 批次",
        "",
    ]
    for batch in library.get("batches", []):
        batch_items = [item for item in items if item["batchId"] == batch["id"]]
        lines.append(f"- [[batches/{safe_note_name(batch['name'])}|{batch['name']}]]：{len(batch_items)} 个素材")
    if not library.get("batches"):
        lines.append("- 暂无批次")
    lines.extend(["", "## 最近素材", ""])
    for item in items[:30]:
        lines.append(material_markdown_line(item))
    if not items:
        lines.append("- 暂无素材")
    MATERIAL_INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_batch_markdown_files(library: dict[str, Any]) -> None:
    items = material_entries(library)
    existing = {path.name for path in OBSIDIAN_BATCH_DIR.glob("*.md")}
    wanted: set[str] = set()
    for batch in library.get("batches", []):
        filename = f"{safe_note_name(batch['name'])}.md"
        wanted.add(filename)
        batch_items = [item for item in items if item["batchId"] == batch["id"]]
        tags = sorted({tag for item in batch_items for tag in item.get("tags", [])})
        status_counts = material_status_counts(batch_items)
        role_counts = material_role_counts(batch_items)
        lines = [
            "---",
            "type: seedance_material_batch",
            f"batch_id: {batch['id']}",
            f"name: {yaml_quote(batch['name'])}",
            f"created_at: {batch.get('createdAt')}",
            f"updated_at: {library.get('updatedAt')}",
            "analysis_status:",
            *[f"  {status}: {status_counts.get(status, 0)}" for status in ANALYSIS_STATUS_LABELS],
            "tags:",
            *[f"  - {yaml_quote(tag)}" for tag in tags],
            "---",
            "",
            f"# {batch['name']}",
            "",
            f"- 素材数：{len(batch_items)}",
            f"- 待 AI 分析：{status_counts.get('queued', 0)}",
            f"- 可剪辑：{status_counts.get('ready', 0)}",
            f"- 标签：{', '.join(tags) if tags else '无'}",
            f"- 剪辑用途：{', '.join(f'{EDIT_ROLE_LABELS.get(role, role)} {count}' for role, count in role_counts.items()) if role_counts else '无'}",
            "",
            "## 素材",
            "",
        ]
        if batch_items:
            lines.extend(material_markdown_line(item) for item in batch_items)
        else:
            lines.append("- 暂无素材")
        (OBSIDIAN_BATCH_DIR / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    for stale_name in existing - wanted:
        stale_path = OBSIDIAN_BATCH_DIR / stale_name
        if stale_path.is_file():
            stale_path.unlink()


def material_entries(library: dict[str, Any]) -> list[dict[str, Any]]:
    batch_names = {batch["id"]: batch["name"] for batch in library.get("batches", [])}
    entries = []
    for url, item in (library.get("items") or {}).items():
        entry = dict(item)
        entry["url"] = url
        entry["batchName"] = batch_names.get(entry.get("batchId"), "未分批")
        entries.append(entry)
    return sorted(entries, key=lambda item: str(item.get("addedAt") or ""), reverse=True)


def material_status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in ANALYSIS_STATUS_LABELS}
    for item in items:
        status = clean_analysis_status(item.get("analysisStatus"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def material_role_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        role = clean_edit_role(item.get("editRole"), clean_material_kind(item.get("kind")))
        counts[role] = counts.get(role, 0) + 1
    return {role: count for role, count in counts.items() if count}


def material_markdown_line(item: dict[str, Any]) -> str:
    tags = " ".join(f"#{tag}" for tag in item.get("tags", []))
    ai_tags = " ".join(f"#AI/{tag}" for tag in item.get("aiTags", []))
    label = item.get("name") or material_display_name(item.get("url", ""))
    obsidian_path = item.get("obsidianPath")
    attachment = f"![[{obsidian_path}]] " if obsidian_path else ""
    status = ANALYSIS_STATUS_LABELS.get(clean_analysis_status(item.get("analysisStatus")), "待 AI 分析")
    role = EDIT_ROLE_LABELS.get(clean_edit_role(item.get("editRole"), clean_material_kind(item.get("kind"))), "待判断")
    priority = PRIORITY_LABELS.get(clean_priority(item.get("priority")), "普通")
    quality = clean_quality_score(item.get("qualityScore"))
    technical_text = format_material_technical_summary(clean_material_technical(item.get("technical"), clean_material_kind(item.get("kind"))))
    notes = clean_material_notes(item.get("notes"))
    meta = f"{item.get('kind', 'image')} · {status} · {role} · {priority} · {'评分 ' + str(quality) if quality else '未评分'}"
    if technical_text:
        meta = f"{meta} · {technical_text}"
    note_text = f" · 备注：{notes}" if notes else ""
    tag_text = f" · {tags}" if tags else ""
    ai_tag_text = f" · {ai_tags}" if ai_tags else ""
    return f"- {attachment}[{label}]({item.get('url', '')}) · {meta}{tag_text}{ai_tag_text}{note_text}".rstrip()


def safe_note_name(value: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", str(value or "未命名批次")).strip().strip(".")
    return name[:100] or "未命名批次"


def trim_float_text(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def format_material_technical_summary(technical: dict[str, Any]) -> str:
    parts: list[str] = []
    width = parse_non_negative_int(technical.get("width"))
    height = parse_non_negative_int(technical.get("height"))
    if width and height:
        parts.append(f"{width}x{height}")
    orientation = str(technical.get("orientation") or "").strip()
    if orientation in {"portrait", "landscape", "square"}:
        parts.append(orientation)
    duration_ms = parse_non_negative_int(technical.get("durationMs"))
    if duration_ms:
        parts.append(f"{trim_float_text(duration_ms / 1000)}s")
    fps = parse_non_negative_float(technical.get("fps"))
    if fps:
        parts.append(f"{trim_float_text(fps)}fps")
    bitrate_kbps = parse_non_negative_int(technical.get("bitrateKbps"))
    if bitrate_kbps:
        parts.append(f"{bitrate_kbps}kbps")
    audio_codec = str(technical.get("audioCodec") or "").strip()
    video_codec = str(technical.get("videoCodec") or "").strip()
    if not width and not height and audio_codec:
        parts.append(audio_codec)
    elif video_codec and not parts:
        parts.append(video_codec)
    return " / ".join(parts)


def yaml_quote(value: object) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


class ArkError(Exception):
    def __init__(self, status: HTTPStatus, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


class AiError(Exception):
    def __init__(self, status: HTTPStatus, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


class AdForgeImageError(Exception):
    def __init__(self, status: HTTPStatus, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


class AdForgeImageCancelled(AdForgeImageError):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.CONFLICT, "关键帧生成已取消，返回结果不会保存。")


def build_seedance_body(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("Prompt is required.")

    ratio = str(payload.get("ratio") or "9:16").strip()
    if ratio not in VALID_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio}.")

    duration = parse_duration(payload.get("duration"))
    if duration not in VALID_DURATIONS:
        raise ValueError("Duration must be 5, 10, 11, or 15 seconds.")

    ref_images = parse_url_list(payload.get("refImages"))
    ref_videos = parse_url_list(payload.get("refVideos"))
    ref_audios = parse_url_list(payload.get("refAudios"))
    if len(ref_images) > ad_forge.MAX_REFERENCE_IMAGES:
        raise ValueError(f"Reference images are limited to {ad_forge.MAX_REFERENCE_IMAGES} per task.")
    if len(ref_videos) > ad_forge.MAX_REFERENCE_VIDEOS:
        raise ValueError(f"Reference videos are limited to {ad_forge.MAX_REFERENCE_VIDEOS} per task.")
    if len(ref_images) + len(ref_videos) + len(ref_audios) > 12:
        raise ValueError("Reference files are limited to 12 per task.")
    raw_video_durations = payload.get("refVideoDurationsMs") if isinstance(payload.get("refVideoDurationsMs"), list) else []
    if raw_video_durations and len(raw_video_durations) != len(ref_videos):
        raise ValueError("Reference video duration metadata must match the video list.")
    try:
        video_duration_total = sum(max(0, int(value or 0)) for value in raw_video_durations)
    except (TypeError, ValueError) as exc:
        raise ValueError("Reference video duration metadata is invalid.") from exc
    if video_duration_total > ad_forge.MAX_REFERENCE_VIDEO_DURATION_MS:
        raise ValueError("Reference videos may total at most 15 seconds per task.")

    project_id = ad_forge.clean_text(payload.get("projectId"), 80)
    if project_id and not re.fullmatch(r"ad-[a-f0-9]{16}", project_id):
        raise ValueError("视频任务关联的项目 ID 无效。")
    reference_privacy_mode = ad_forge.clean_text(payload.get("referencePrivacyMode"), 30) or "direct"
    if reference_privacy_mode not in ad_forge.REFERENCE_PRIVACY_MODES:
        raise ValueError("参考图片真人处理模式无效。")
    prepared_images = prepare_seedance_reference_images(ref_images, project_id, reference_privacy_mode)
    validate_seedance_remote_references(ref_videos, "视频")
    validate_seedance_remote_references(ref_audios, "音频")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    content.extend(content_item(url, "image_url", "image_url", "reference_image") for url in prepared_images)
    content.extend(content_item(url, "video_url", "video_url", "reference_video") for url in ref_videos)
    content.extend(content_item(url, "audio_url", "audio_url", "reference_audio") for url in ref_audios)

    return {
        "model": parse_model(payload.get("model")),
        "content": content,
        "ratio": ratio,
        "duration": duration,
        "watermark": bool(payload.get("watermark")),
        "generate_audio": bool(payload.get("generateAudio")),
    }


def prepare_seedance_reference_images(
    values: list[str],
    project_id: str = "",
    privacy_mode: str = "direct",
) -> list[str]:
    prepared: list[str] = []
    inline_total = 0
    for value in values:
        parsed = urlparse(value)
        local_path = unquote(parsed.path).replace("\\", "/")
        managed_local_path = local_path.startswith(("/uploads/images/", "/ad-forge-images/"))
        if is_public_url(value) and not (privacy_mode == "product-only" and managed_local_path):
            if privacy_mode == "product-only":
                raise ValueError("商品隐私模式只能处理面板已上传的图片；请先把公网图片上传到参考图区域。")
            prepared.append(value)
            continue
        if parsed.scheme == "data":
            raise ValueError("请上传参考图片文件；为安全起见，页面不接受手工填写的 Base64 图片。")
        if parsed.scheme not in {"", "http", "https"}:
            raise ValueError("参考图片地址无效，请上传图片或使用公网 http/https 图片 URL。")
        if parsed.scheme in {"http", "https"} and not is_local_or_private_url(value):
            raise ValueError("参考图片地址无效，请使用可公开访问的 http/https URL。")

        if local_path.startswith("/ad-forge-images/") and not project_id:
            raise ValueError("分镜关键帧缺少项目归属信息，请刷新页面后重试。")
        try:
            image_path = resolve_ad_forge_reference_image_url(value, project_id)
            _filename, content_type, content = read_ad_forge_reference_image(image_path)
        except AdForgeImageError as exc:
            raise ValueError(exc.message) from exc
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError("本机参考图已失效或不属于当前项目，请重新上传后再生成视频。") from exc
        if privacy_mode == "product-only":
            content_type, content = build_seedance_product_only_reference(content, content_type)
        inline_total += len(content)
        if inline_total > MAX_SEEDANCE_INLINE_IMAGE_TOTAL_BYTES:
            raise ValueError("本机参考图片合计不能超过 32MB，请减少图片数量或压缩图片后重试。")
        encoded = base64.b64encode(content).decode("ascii")
        prepared.append(f"data:{content_type};base64,{encoded}")
    return prepared


def build_seedance_product_only_reference(content: bytes, content_type: str) -> tuple[str, bytes]:
    try:
        from PIL import Image, ImageDraw, ImageOps, ImageStat, UnidentifiedImageError
    except ImportError as exc:
        raise ValueError("服务缺少图片隐私处理组件 Pillow，请安装后重试。") from exc

    try:
        source = Image.open(io.BytesIO(content))
        source.seek(0)
        source_width, source_height = source.size
        if source_width < 64 or source_height < 64 or source_width * source_height > 36_000_000:
            raise ValueError("参考图片尺寸不适合隐私处理，请使用边长 64–6000px 的图片。")
        image = ImageOps.exif_transpose(source).convert("RGB")
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("参考图片无法读取，请重新上传 PNG、JPEG 或 WebP 图片。") from exc

    width, height = image.size
    if width < 64 or height < 64 or width * height > 36_000_000:
        raise ValueError("参考图片尺寸不适合隐私处理，请使用边长 64–6000px 的图片。")

    face_regions: list[tuple[int, int, int, int]] = []
    try:
        import cv2
        import numpy as np

        gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
        min_face = max(28, min(width, height) // 18)
        detected = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(min_face, min_face))
        for x, y, face_width, face_height in detected:
            face_regions.append(
                (
                    max(0, int(x - face_width * 0.28)),
                    max(0, int(y - face_height * 0.35)),
                    min(width, int(x + face_width * 1.28)),
                    min(height, int(y + face_height * 1.25)),
                )
            )
    except (ImportError, AttributeError, OSError, ValueError):
        face_regions = []

    if not face_regions:
        face_regions = [
            (
                int(width * 0.30),
                0,
                int(width * 0.70),
                int(height * (0.22 if height >= width else 0.18)),
            )
        ]

    sample = image.crop((0, 0, max(1, width // 8), max(1, height // 8)))
    median = ImageStat.Stat(sample).median
    fill = tuple(max(24, min(242, int(channel))) for channel in median[:3])
    draw = ImageDraw.Draw(image)
    for left, top, right, bottom in face_regions:
        if right <= left or bottom <= top:
            continue
        radius = max(4, int(min(right - left, bottom - top) * 0.14))
        draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=fill)

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    masked = output.getvalue()
    if not masked or len(masked) > MAX_IMAGE_UPLOAD_BYTES:
        raise ValueError("隐私处理后的参考图片超过 10MB，请压缩原图后重试。")
    return "image/png", masked


def validate_seedance_remote_references(values: list[str], label: str) -> None:
    invalid = [value for value in values if not is_public_url(value)]
    if not invalid:
        return
    local = any(is_local_or_private_url(value) for value in invalid)
    if local:
        raise ValueError(
            f"本机或局域网参考{label}无法由远程 Seedance 下载。"
            f"请先配置公网素材地址，或移除参考{label}后重试；本机参考图片会由服务端自动内嵌。"
        )
    raise ValueError(f"参考{label}必须使用公网可访问的 http/https URL。")


def content_item(url: str, item_type: str, url_key: str, role: str) -> dict[str, Any]:
    return {
        "type": item_type,
        url_key: {"url": url},
        "role": role,
    }


def public_seedance_request_body(body: dict[str, Any]) -> dict[str, Any]:
    public_body = {key: value for key, value in body.items() if key != "content"}
    public_content: list[dict[str, Any]] = []
    for raw_item in body.get("content") if isinstance(body.get("content"), list) else []:
        if not isinstance(raw_item, dict):
            continue
        item = dict(raw_item)
        image_url = item.get("image_url")
        if isinstance(image_url, dict):
            url = str(image_url.get("url") or "")
            if url.startswith("data:image/") and ";base64," in url:
                prefix = url.split(",", 1)[0]
                item["image_url"] = {**image_url, "url": f"{prefix},[本机参考图已安全内嵌，预览已隐藏]"}
        public_content.append(item)
    public_body["content"] = public_content
    return public_body


def parse_duration(value: Any) -> int:
    try:
        return int(value or 10)
    except (TypeError, ValueError):
        return 10


def parse_quantity(value: Any) -> int:
    try:
        quantity = int(value or MIN_QUANTITY)
    except (TypeError, ValueError):
        quantity = MIN_QUANTITY
    if quantity < MIN_QUANTITY or quantity > MAX_QUANTITY:
        raise ValueError(f"Quantity must be between {MIN_QUANTITY} and {MAX_QUANTITY}.")
    return quantity


def parse_prompt_count(value: Any) -> int:
    try:
        count = int(value or MIN_PROMPT_COUNT)
    except (TypeError, ValueError):
        count = MIN_PROMPT_COUNT
    return min(MAX_PROMPT_COUNT, max(MIN_PROMPT_COUNT, count))


def parse_url_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value]
    else:
        raw = str(value or "")
        for separator in [",", "\n", "\r", "\t"]:
            raw = raw.replace(separator, " ")
        items = [item.strip() for item in raw.split(" ")]
    return [item for item in items if item]


def is_public_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not is_local_or_private_url(value)


def is_local_or_private_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.strip("[]").lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost") or hostname.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return "." not in hostname
    return not address.is_global


def read_runtime_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_runtime_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    sync_obsidian_project_data(config=config)


def get_config_section(name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    source = read_runtime_config() if config is None else config
    section = source.get(name)
    return section if isinstance(section, dict) else {}


def save_runtime_config(payload: dict[str, Any]) -> dict[str, Any]:
    config = merge_runtime_config_payload(read_runtime_config(), payload)
    if payload.get("clearImageGenerationApiKey") and AD_FORGE_IMAGE_CONFIG_FILE.exists():
        private = read_ad_forge_image_private_config()
        if private.pop("apiKey", None) is not None:
            AD_FORGE_IMAGE_CONFIG_FILE.write_text(json.dumps(private, ensure_ascii=False, indent=2), encoding="utf-8")
    write_runtime_config(config)
    return build_config_response(config)["config"]


def merge_runtime_config_payload(base_config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    config = json.loads(json.dumps(base_config))
    ark = dict(config.get("ark") or {})
    ai = dict(config.get("ai") or {})
    image_generation = dict(config.get("imageGeneration") or {})
    translation = dict(config.get("translation") or {})
    elevenlabs = dict(config.get("elevenlabs") or {})

    if payload.get("clearArkApiKey"):
        ark.pop("apiKey", None)
    elif str(payload.get("arkApiKey") or "").strip():
        ark["apiKey"] = str(payload.get("arkApiKey") or "").strip()

    if "arkEndpoint" in payload:
        ark["endpoint"] = parse_url_config(payload.get("arkEndpoint"), ARK_ENDPOINT, "Ark endpoint")

    if "seedanceModel" in payload or "model" in payload:
        ark["model"] = parse_model(payload.get("seedanceModel") or payload.get("model"))

    if payload.get("clearAiApiKey"):
        ai.pop("apiKey", None)
    elif str(payload.get("aiApiKey") or "").strip():
        ai["apiKey"] = str(payload.get("aiApiKey") or "").strip()

    if "aiBaseUrl" in payload:
        ai["baseUrl"] = parse_url_config(payload.get("aiBaseUrl"), DEFAULT_AI_BASE_URL, "AI base URL").rstrip("/")

    if "aiModel" in payload:
        ai["model"] = parse_text_config(payload.get("aiModel"), DEFAULT_AI_MODEL, "AI model", max_length=200)

    if "aiTemperature" in payload:
        ai["temperature"] = parse_float_config(payload.get("aiTemperature"), 0.7, 0, 2, "AI temperature")

    if "aiMaxTokens" in payload:
        ai["maxTokens"] = parse_int_config(payload.get("aiMaxTokens"), 700, 128, 4000, "AI max tokens")

    if payload.get("clearImageGenerationApiKey"):
        image_generation.pop("apiKey", None)
    elif str(payload.get("imageGenerationApiKey") or "").strip():
        image_generation["apiKey"] = str(payload.get("imageGenerationApiKey") or "").strip()

    if "imageGenerationBaseUrl" in payload:
        image_generation["baseUrl"] = parse_url_config(
            payload.get("imageGenerationBaseUrl"),
            DEFAULT_AD_FORGE_IMAGE_BASE_URL,
            "Image generation base URL",
        ).rstrip("/")

    if "imageGenerationModel" in payload:
        image_generation["model"] = parse_text_config(
            payload.get("imageGenerationModel"),
            DEFAULT_AD_FORGE_IMAGE_MODEL,
            "Image generation model",
            max_length=160,
        )

    if payload.get("clearTranslationApiKey"):
        translation.pop("apiKey", None)
    elif str(payload.get("translationApiKey") or "").strip():
        translation["apiKey"] = str(payload.get("translationApiKey") or "").strip()

    if "translationBaseUrl" in payload:
        translation["baseUrl"] = parse_url_config(payload.get("translationBaseUrl"), DEFAULT_AI_BASE_URL, "Translation base URL").rstrip("/")

    if "translationModel" in payload:
        translation["model"] = parse_text_config(payload.get("translationModel"), DEFAULT_AI_MODEL, "Translation model", max_length=200)

    if "translationTemperature" in payload:
        translation["temperature"] = parse_float_config(payload.get("translationTemperature"), 0.3, 0, 1.5, "Translation temperature")

    if "translationMaxTokens" in payload:
        translation["maxTokens"] = parse_int_config(payload.get("translationMaxTokens"), 2200, 256, 6000, "Translation max tokens")

    if payload.get("clearElevenLabsApiKey"):
        elevenlabs.pop("apiKey", None)
    elif str(payload.get("elevenLabsApiKey") or "").strip():
        elevenlabs["apiKey"] = str(payload.get("elevenLabsApiKey") or "").strip()

    if "elevenLabsVoiceId" in payload:
        voice_id = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("elevenLabsVoiceId") or "").strip())[:120]
        if voice_id:
            elevenlabs["voiceId"] = voice_id

    if "elevenLabsModel" in payload:
        elevenlabs["model"] = parse_text_config(payload.get("elevenLabsModel"), DEFAULT_ELEVENLABS_MODEL, "ElevenLabs model", max_length=120)

    config["ark"] = ark
    config["ai"] = ai
    config["imageGeneration"] = image_generation
    config["translation"] = translation
    config["elevenlabs"] = elevenlabs
    return config


def validate_runtime_config(payload: dict[str, Any], kind: str | None = None) -> dict[str, Any]:
    if kind and kind not in {"ark", "ai", "image", "translation", "elevenlabs"}:
        raise ValueError("Unsupported config test target.")
    mode = str(payload.get("testMode") or "config").strip().lower() if isinstance(payload, dict) else "config"
    if mode not in {"config", "connectivity", "invoke"}:
        raise ValueError("Unsupported config test mode.")
    config = merge_runtime_config_payload(read_runtime_config(), payload) if payload else read_runtime_config()
    response = build_config_response(config)["config"]

    if mode in {"connectivity", "invoke"}:
        live_results = {
            "ark": probe_ark_runtime(config, mode),
            "ai": probe_ai_runtime(config, mode),
            "image": probe_image_runtime(config, mode),
            "translation": probe_translation_runtime(config, mode),
        }
        if kind in live_results:
            return {kind: live_results[kind]}
        if kind == "elevenlabs":
            return {kind: validate_elevenlabs_config_response(response)}
        return live_results

    results = {
        "ark": validate_ark_config_response(response),
        "ai": validate_ai_config_response(response),
        "image": validate_image_config_response(response),
        "translation": validate_translation_config_response(response),
        "elevenlabs": validate_elevenlabs_config_response(response),
    }
    return {kind: results[kind]} if kind else results


def validate_ark_config_response(response: dict[str, Any]) -> dict[str, Any]:
    ark = response["ark"]
    ready = bool(ark["hasApiKey"] and ark["model"] and ark["endpoint"])
    return {
        "ok": ready,
        "message": "CPA 视频节点配置已就绪（未提交生成任务）" if ready else "请配置 CPA 视频节点 Key、完整 Endpoint 和 Seedance 模型",
    }


def validate_ai_config_response(response: dict[str, Any]) -> dict[str, Any]:
    ai = response["ai"]
    ready = bool(ai["hasApiKey"] and ai["model"] and ai["baseUrl"])
    return {
        "ok": ready,
        "message": "CPA AI 节点配置已就绪（兼容 chat/completions）" if ready else "请配置 CPA AI 节点 Key、Base URL 和模型",
    }


def validate_translation_config_response(response: dict[str, Any]) -> dict[str, Any]:
    translation = response["translation"]
    ready = bool(translation["hasApiKey"] and translation["model"] and translation["baseUrl"])
    return {
        "ok": ready,
        "message": "提示词翻译模型配置已就绪" if ready else "请配置翻译 Key、Base URL 和模型，或先完成 AI 提示词接口配置",
    }


def validate_image_config_response(response: dict[str, Any]) -> dict[str, Any]:
    image = response["imageGeneration"]
    ready = bool(image["hasApiKey"] and image["model"] and image["baseUrl"])
    return {
        "ok": ready,
        "message": "生图节点配置已就绪（兼容 images/generations）" if ready else "请配置生图 Key、Base URL 和模型",
    }


def validate_elevenlabs_config_response(response: dict[str, Any]) -> dict[str, Any]:
    elevenlabs = response["elevenlabs"]
    ready = bool(elevenlabs["hasApiKey"] and elevenlabs["voiceId"] and elevenlabs["model"])
    return {
        "ok": ready,
        "message": "ElevenLabs 配音已就绪" if ready else "请配置 ElevenLabs API Key、Voice ID 和模型",
    }


def probe_http_endpoint(
    method: str,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    started = time.perf_counter()
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request_headers = {"User-Agent": "SOSOVE-Engine-ConfigProbe/1.0", **headers}
    if body is not None:
        request_headers.setdefault("Content-Type", "application/json")
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(4096).decode("utf-8", errors="replace")
            return {
                "networkOk": True,
                "httpStatus": int(getattr(response, "status", 200) or 200),
                "latencyMs": round((time.perf_counter() - started) * 1000),
                "responsePreview": raw[:240],
            }
    except HTTPError as exc:
        raw = exc.read(4096).decode("utf-8", errors="replace")
        return {
            "networkOk": True,
            "httpStatus": int(exc.code),
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "responsePreview": raw[:240],
            "error": probe_error_text(raw, exc.code),
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "networkOk": False,
            "httpStatus": None,
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "error": str(getattr(exc, "reason", None) or exc),
        }


def probe_error_text(raw: str, status: int | None = None) -> str:
    if raw:
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return str(payload.get("message") or payload.get("error") or payload)[:300]
        except json.JSONDecodeError:
            return raw[:300]
    return f"HTTP {status}" if status else "远端未返回响应"


def probe_ai_runtime(config: dict[str, Any], mode: str) -> dict[str, Any]:
    response = build_config_response(config)["config"]
    ai = response["ai"]
    base_url = get_ai_base_url(config)
    model = get_ai_model(config)
    endpoint = build_ai_chat_endpoint(config)
    base_result = {
        "endpoint": endpoint,
        "model": model,
        "checkedAt": utc_now_iso(),
    }
    if not (ai["hasApiKey"] and model and ai["baseUrl"]):
        return {
            **base_result,
            "ok": False,
            "networkOk": False,
            "authOk": False,
            "modelOk": False,
            "message": "请先填写 AI Key、Base URL 和模型名称",
        }

    if mode == "invoke":
        started = time.perf_counter()
        try:
            result = call_ai_chat(
                {
                    "model": model,
                    "messages": [{"role": "user", "content": "Connectivity test. Reply exactly OK."}],
                    "temperature": 0,
                    "max_tokens": 8,
                },
                timeout_seconds=25,
                config=config,
            )
            reply = extract_ai_text(result).strip()
            return {
                **base_result,
                "ok": bool(reply),
                "networkOk": True,
                "authOk": True,
                "modelOk": bool(reply),
                "httpStatus": 200,
                "latencyMs": round((time.perf_counter() - started) * 1000),
                "reply": reply[:120],
                "message": "AI 模型试调用成功" if reply else "AI 返回成功，但没有可读文本",
            }
        except AiError as exc:
            return {
                **base_result,
                "ok": False,
                "networkOk": int(exc.status) != 502,
                "authOk": int(exc.status) not in {401, 403},
                "modelOk": False,
                "httpStatus": int(exc.status),
                "latencyMs": round((time.perf_counter() - started) * 1000),
                "message": exc.message[:300],
            }

    models_endpoint = f"{base_url.rstrip('/')}/models" if not base_url.rstrip('/').endswith("/models") else base_url.rstrip("/")
    probe = probe_http_endpoint(
        "GET",
        models_endpoint,
        {"Authorization": f"Bearer {get_ai_api_key(config)}"},
    )
    status = probe.get("httpStatus")
    auth_ok = False if status in {401, 403} else None
    model_ok = None
    if status == 200:
        try:
            payload = json.loads(str(probe.get("responsePreview") or "{}"))
            ids = [str(item.get("id")) for item in payload.get("data", []) if isinstance(item, dict)]
            model_ok = model in ids if ids else None
        except (TypeError, json.JSONDecodeError):
            model_ok = None
    reachable = bool(probe.get("networkOk"))
    ok = reachable and auth_ok is not False
    message = (
        "AI 节点已连通，Key 已被接受；模型目录接口可用"
        if status == 200 and model_ok is not False
        else "AI 节点已连通，当前地址未提供 /models；点击“试调用模型”确认模型"
        if ok
        else "AI 节点已响应，但 Key 鉴权失败"
        if reachable
        else f"AI 节点连接失败：{probe.get('error') or '网络超时'}"
    )
    return {
        **base_result,
        **probe,
        "ok": ok,
        "authOk": auth_ok,
        "modelOk": model_ok,
        "message": message,
    }


def probe_image_runtime(config: dict[str, Any], mode: str) -> dict[str, Any]:
    response = build_config_response(config)["config"]
    image = response["imageGeneration"]
    base_url = get_ad_forge_image_base_url(config)
    model = get_ad_forge_image_model(config)
    models_endpoint = f"{base_url.rstrip('/')}/models" if not base_url.rstrip('/').endswith("/models") else base_url.rstrip("/")
    generation_endpoint = base_url.rstrip("/") if base_url.rstrip("/").endswith("/images/generations") else f"{base_url.rstrip('/')}/images/generations"
    base_result = {
        "endpoint": generation_endpoint,
        "probeEndpoint": models_endpoint,
        "model": model,
        "checkedAt": utc_now_iso(),
    }
    if not (image["hasApiKey"] and model and image["baseUrl"]):
        return {
            **base_result,
            "ok": False,
            "networkOk": False,
            "authOk": False,
            "modelOk": False,
            "message": "请先填写生图 Key、Base URL 和模型名称",
        }

    probe = probe_http_endpoint(
        "GET",
        models_endpoint,
        {"Authorization": f"Bearer {get_ad_forge_image_api_key(config)}"},
    )
    status = probe.get("httpStatus")
    auth_ok = False if status in {401, 403} else None
    model_ok = None
    if status == 200:
        try:
            payload = json.loads(str(probe.get("responsePreview") or "{}"))
            ids = [str(item.get("id")) for item in payload.get("data", []) if isinstance(item, dict)]
            model_ok = model in ids if ids else None
        except (TypeError, json.JSONDecodeError):
            model_ok = None
    reachable = bool(probe.get("networkOk"))
    accepted_status = isinstance(status, int) and status < 500
    ok = reachable and accepted_status and auth_ok is not False and model_ok is not False
    message = (
        "生图节点已连通，Key 已被接受，模型目录校验通过"
        if status == 200 and model_ok is not False
        else f"生图节点已连通，但模型目录中没有 {model}"
        if status == 200 and model_ok is False
        else "生图节点已响应，当前地址未提供 /models；生成接口配置保持可用"
        if ok
        else "生图节点已响应，但 Key 鉴权失败"
        if reachable and auth_ok is False
        else f"生图节点返回 HTTP {status}：{probe.get('error') or '服务异常'}"
        if reachable
        else f"生图节点连接失败：{probe.get('error') or '网络超时'}"
    )
    return {
        **base_result,
        **probe,
        "ok": ok,
        "authOk": auth_ok,
        "modelOk": model_ok,
        "message": message,
    }


def probe_translation_runtime(config: dict[str, Any], mode: str) -> dict[str, Any]:
    result = probe_ai_runtime(translation_as_ai_config(config), mode)
    result["message"] = str(result.get("message") or "").replace("AI ", "翻译 ", 1)
    return result


def probe_ark_runtime(config: dict[str, Any], mode: str) -> dict[str, Any]:
    response = build_config_response(config)["config"]
    ark = response["ark"]
    endpoint = get_ark_endpoint(config)
    model = get_default_model(config)
    base_result = {
        "endpoint": endpoint,
        "model": model,
        "checkedAt": utc_now_iso(),
    }
    if not (ark["hasApiKey"] and endpoint and model):
        return {
            **base_result,
            "ok": False,
            "networkOk": False,
            "authOk": False,
            "modelOk": False,
            "message": "请先填写 Ark Key、完整视频 Endpoint 和 Seedance 模型",
        }

    if mode == "invoke":
        started = time.perf_counter()
        try:
            result = call_ark(
                "POST",
                endpoint,
                body={
                    "model": model,
                    "content": [{"type": "text", "text": "连接测试：生成一条简单的 5 秒竖屏商品展示测试视频，只验证模型调用。"}],
                    "ratio": "9:16",
                    "duration": 5,
                    "watermark": False,
                    "generate_audio": False,
                },
                config=config,
                timeout_seconds=45,
            )
            task_id = ""
            if isinstance(result, dict):
                task_id = str(result.get("id") or result.get("task_id") or result.get("taskId") or "")
                data = result.get("data")
                if not task_id and isinstance(data, dict):
                    task_id = str(data.get("id") or data.get("task_id") or data.get("taskId") or "")
            return {
                **base_result,
                "ok": True,
                "networkOk": True,
                "authOk": True,
                "modelOk": True,
                "httpStatus": 200,
                "latencyMs": round((time.perf_counter() - started) * 1000),
                "taskId": task_id,
                "message": "视频模型试调用成功，测试任务已提交" if task_id else "视频模型已响应，测试任务已提交",
            }
        except ArkError as exc:
            return {
                **base_result,
                "ok": False,
                "networkOk": int(exc.status) != 502,
                "authOk": int(exc.status) not in {401, 403},
                "modelOk": False,
                "httpStatus": int(exc.status),
                "latencyMs": round((time.perf_counter() - started) * 1000),
                "message": exc.message[:300],
            }

    probe = probe_http_endpoint(
        "GET",
        endpoint,
        {"Authorization": f"Bearer {get_api_key(config)}"},
    )
    status = probe.get("httpStatus")
    auth_ok = False if status in {401, 403} else None
    reachable = bool(probe.get("networkOk"))
    ok = reachable and auth_ok is not False
    message = (
        "视频节点已连通；任务接口不接受空 GET，点击“试调用模型”确认 Key 和模型"
        if ok
        else "视频节点已响应，但鉴权失败"
        if reachable
        else f"视频节点连接失败：{probe.get('error') or '网络超时'}"
    )
    return {
        **base_result,
        **probe,
        "ok": ok,
        "authOk": auth_ok,
        "modelOk": None,
        "message": message,
    }


def build_config_response(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "config": {
            "ark": {
                "endpoint": get_ark_endpoint(config),
                "model": get_default_model(config),
                "hasApiKey": bool(get_api_key(config)),
                "apiKeyPreview": mask_secret(get_api_key(config)),
                "presets": MODEL_PRESETS,
            },
            "ai": {
                "baseUrl": get_ai_base_url(config),
                "model": get_ai_model(config),
                "hasApiKey": bool(get_ai_api_key(config)),
                "apiKeyPreview": mask_secret(get_ai_api_key(config)),
                "temperature": get_ai_temperature(config),
                "maxTokens": get_ai_max_tokens(config),
            },
            "imageGeneration": {
                "baseUrl": get_ad_forge_image_base_url(config),
                "model": get_ad_forge_image_model(config),
                "hasApiKey": bool(get_ad_forge_image_api_key(config)),
                "apiKeyPreview": mask_secret(get_ad_forge_image_api_key(config)),
            },
            "translation": {
                "baseUrl": get_translation_base_url(config),
                "model": get_translation_model(config),
                "hasApiKey": bool(get_translation_api_key(config)),
                "apiKeyPreview": mask_secret(get_translation_api_key(config)),
                "temperature": get_translation_temperature(config),
                "maxTokens": get_translation_max_tokens(config),
                "usingAiFallback": not bool(get_config_section("translation", config).get("apiKey")),
            },
            "elevenlabs": {
                "hasApiKey": bool(get_elevenlabs_api_key(config)),
                "apiKeyPreview": mask_secret(get_elevenlabs_api_key(config)),
                "voiceId": get_elevenlabs_voice_id(config),
                "model": get_elevenlabs_model(config),
            },
        },
    }


def parse_url_config(value: Any, default: str, label: str) -> str:
    text = str(value or "").strip() or default
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an http/https URL.")
    return text


def parse_text_config(value: Any, default: str, label: str, max_length: int = 128) -> str:
    text = str(value or "").strip() or default
    if len(text) > max_length:
        raise ValueError(f"{label} is too long.")
    if any(ord(char) < 32 for char in text):
        raise ValueError(f"{label} contains invalid characters.")
    return text


def parse_int_config(value: Any, default: int, minimum: int, maximum: int, label: str) -> int:
    raw = default if value is None or value == "" else value
    try:
        number = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.")
    if number < minimum or number > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return number


def parse_float_config(value: Any, default: float, minimum: float, maximum: float, label: str) -> float:
    raw = default if value is None or value == "" else value
    try:
        number = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.")
    if number < minimum or number > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return number


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def get_ark_endpoint(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("ark", config).get("endpoint") or "").strip()
    return configured or os.environ.get("ARK_ENDPOINT", "").strip() or ARK_ENDPOINT


def get_asset_public_base_url() -> str:
    configured = str(get_config_section("assets").get("publicBaseUrl") or "").strip()
    return (configured or os.environ.get("ASSET_PUBLIC_BASE_URL", "").strip()).rstrip("/")


def get_default_model(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("ark", config).get("model") or "").strip()
    return configured or os.environ.get("SEEDANCE_MODEL", "").strip() or os.environ.get("ARK_MODEL", "").strip() or DEFAULT_MODEL


def parse_model(value: Any) -> str:
    raw = str(value or "").strip()
    model = MODEL_ALIASES.get(normalize_model_alias(raw), raw) if raw else get_default_model()
    if not model:
        raise ValueError("Seedance model is required.")
    if len(model) > 128:
        raise ValueError("Seedance model id is too long.")
    if not MODEL_ID_RE.match(model):
        raise ValueError("Seedance model id may only contain letters, numbers, dot, colon, underscore, and hyphen.")
    return model


def normalize_model_alias(value: str) -> str:
    return value.lower().replace(" ", "").replace("_", "-")


def get_api_key(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("ark", config).get("apiKey") or "").strip()
    return configured or os.environ.get("ARK_API_KEY", "").strip()


def get_ai_base_url(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("ai", config).get("baseUrl") or "").strip()
    return (configured or os.environ.get("AI_API_BASE_URL", DEFAULT_AI_BASE_URL)).strip().rstrip("/")


def get_ai_model(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("ai", config).get("model") or "").strip()
    return configured or os.environ.get("AI_MODEL", DEFAULT_AI_MODEL).strip()


def get_ai_api_key(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("ai", config).get("apiKey") or "").strip()
    explicit_key = configured or os.environ.get("AI_API_KEY", "").strip() or os.environ.get("OPENAI_API_KEY", "").strip()
    if explicit_key:
        return explicit_key
    if "volces.com" in get_ai_base_url(config):
        return get_api_key(config)
    return ""


def get_translation_base_url(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("translation", config).get("baseUrl") or "").strip()
    return (configured or get_ai_base_url(config)).rstrip("/")


def get_translation_model(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("translation", config).get("model") or "").strip()
    return configured or get_ai_model(config)


def get_translation_api_key(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("translation", config).get("apiKey") or "").strip()
    return configured or get_ai_api_key(config)


def get_translation_temperature(config: dict[str, Any] | None = None) -> float:
    configured = get_config_section("translation", config).get("temperature")
    if configured is not None:
        try:
            return float(configured)
        except (TypeError, ValueError):
            pass
    return 0.3


def get_translation_max_tokens(config: dict[str, Any] | None = None) -> int:
    configured = get_config_section("translation", config).get("maxTokens")
    if configured is not None:
        try:
            return int(configured)
        except (TypeError, ValueError):
            pass
    return 2200


def translation_as_ai_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    source = json.loads(json.dumps(read_runtime_config() if config is None else config))
    source["ai"] = {
        "apiKey": get_translation_api_key(config),
        "baseUrl": get_translation_base_url(config),
        "model": get_translation_model(config),
        "temperature": get_translation_temperature(config),
        "maxTokens": get_translation_max_tokens(config),
    }
    return source


def get_elevenlabs_api_key(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("elevenlabs", config).get("apiKey") or "").strip()
    return configured or os.environ.get("ELEVENLABS_API_KEY", "").strip()


def get_elevenlabs_voice_id(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("elevenlabs", config).get("voiceId") or "").strip()
    return re.sub(r"[^A-Za-z0-9_-]", "", configured or os.environ.get("ELEVENLABS_VOICE_ID", "").strip())[:120]


def get_elevenlabs_model(config: dict[str, Any] | None = None) -> str:
    configured = str(get_config_section("elevenlabs", config).get("model") or "").strip()
    model = configured or os.environ.get("ELEVENLABS_MODEL", "").strip() or DEFAULT_ELEVENLABS_MODEL
    return re.sub(r"[^A-Za-z0-9_.-]", "", model)[:120] or DEFAULT_ELEVENLABS_MODEL


def get_ai_temperature(config: dict[str, Any] | None = None) -> float:
    configured = get_config_section("ai", config).get("temperature")
    if configured is not None:
        try:
            return float(configured)
        except (TypeError, ValueError):
            pass
    return parse_float_env("AI_TEMPERATURE", 0.7)


def get_ai_max_tokens(config: dict[str, Any] | None = None) -> int:
    configured = get_config_section("ai", config).get("maxTokens")
    if configured is not None:
        try:
            return int(configured)
        except (TypeError, ValueError):
            pass
    return parse_int_env("AI_MAX_TOKENS", 700)


def call_ark(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    api_key = get_api_key(config)
    if not api_key:
        raise ArkError(
            HTTPStatus.BAD_REQUEST,
            "ARK_API_KEY is missing. Set it in PowerShell before starting the server.",
        )

    data = None
    headers = {"Authorization": f"Bearer {api_key}"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_seconds or 90) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        message = read_error_message(exc)
        status = HTTPStatus(exc.code) if exc.code in HTTPStatus._value2member_map_ else HTTPStatus.BAD_GATEWAY
        raise ArkError(status, message) from exc
    except URLError as exc:
        raise ArkError(HTTPStatus.BAD_GATEWAY, f"Ark request failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ArkError(HTTPStatus.BAD_GATEWAY, "Ark returned an invalid JSON response.") from exc


def build_native_localization_brief(target_language: str, market: str, scene: str) -> dict[str, str]:
    language_guidance = {
        "ja-JP": (
            "Write present-day standard Japanese as used in Japanese fashion ecommerce, Reels, and TikTok. "
            "Use a warm, natural です・ます base for sales copy, split long Chinese-style clauses into short spoken beats, "
            "and choose everyday Japanese wording a local creator would say aloud. Avoid textbook Japanese, direct Chinese syntax, "
            "overly formal keigo, and invented slang or dialect."
        ),
        "en-US": (
            "Write contemporary American English that sounds natural when spoken in a product video. "
            "Use short, rhythmic sentences and familiar ecommerce wording; avoid literal Chinese sentence order, stiff business language, "
            "and forced slang."
        ),
        "ko-KR": (
            "Write contemporary standard Korean suitable for a local ecommerce video. "
            "Use natural spoken pacing and locally familiar product wording; avoid literal Chinese syntax, overly formal constructions, "
            "and invented slang or dialect."
        ),
    }
    scene_guidance = {
        "voiceover": "The main translation must be ready to read aloud: natural breath groups, short clauses, and no written-language stiffness.",
        "social_ad": "Use native platform-ad rhythm that feels human and credible, never a translated sales script.",
        "product_copy": "Make product benefits easy to understand in local everyday wording while keeping all facts accurate.",
        "video_prompt": "Keep production instructions precise, but express descriptions in natural target-language order rather than source-language order.",
    }
    return {
        "localization_priority": "Native daily speech first: preserve intent and facts, then rewrite for how a local person naturally speaks.",
        "market_note": f"Localize for {market or 'the selected target market'} rather than translating word by word.",
        "language_guidance": language_guidance.get(
            target_language,
            "Use standard contemporary language that a local person would naturally say aloud; avoid literal source-language syntax and forced slang.",
        ),
        "scene_guidance": scene_guidance.get(scene, scene_guidance["video_prompt"]),
    }


def translate_prompt_text(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or "").strip()
    if not text:
        raise ValueError("需要填写待翻译的提示词或文案。")
    if len(text) > 12000:
        raise ValueError("待翻译文本最多 12000 个字符。")

    language_labels = {
        "auto": "自动识别",
        "zh-CN": "简体中文",
        "ja-JP": "日语",
        "en-US": "美式英语",
        "ko-KR": "韩语",
    }
    scene_labels = {
        "video_prompt": "AI 视频生成提示词",
        "voiceover": "电商视频口播文案",
        "social_ad": "Facebook / TikTok 广告文案",
        "product_copy": "商品卖点文案",
    }
    tone_labels = {
        "natural": "当地人日常口语（优先）",
        "direct_response": "带货转化",
        "professional": "专业准确",
        "soft": "温和生活化",
    }
    source_language = str(payload.get("sourceLanguage") or "auto")
    target_language = str(payload.get("targetLanguage") or "ja-JP")
    if source_language not in language_labels or target_language not in language_labels or target_language == "auto":
        raise ValueError("翻译语言设置无效。")
    market = str(payload.get("market") or "Japan").strip()[:80]
    scene = str(payload.get("scene") or "video_prompt")
    tone = str(payload.get("tone") or "natural")
    if scene not in scene_labels or tone not in tone_labels:
        raise ValueError("翻译场景或语言风格无效。")

    back_translation = bool(payload.get("backTranslation", True))
    dual_pass = bool(payload.get("dualPass", True))
    compliance_audit = bool(payload.get("complianceAudit", True))
    preserve_format = bool(payload.get("preserveFormat", True))
    runtime_config = read_runtime_config()
    model = get_translation_model(runtime_config)
    effective_config = translation_as_ai_config(runtime_config)
    if not get_translation_api_key(runtime_config):
        raise AiError(HTTPStatus.BAD_REQUEST, "请先配置翻译模型 API Key，或完成 AI 提示词接口配置。")

    native_localization_brief = build_native_localization_brief(target_language, market, scene)
    system_prompt = (
        "You are a senior localization editor for ecommerce video prompts and ad copy. "
        "Treat every request as native-language adaptation, never as sentence-by-sentence translation. "
        "First infer the source intent, emotional rhythm, and speaking situation; then write what a real local person would naturally say in the target market. "
        "The translation field must be ready to read aloud, with natural word order, rhythm, and everyday wording. "
        "Do not preserve source-language syntax, map words one-to-one, or keep unnatural repetitions just because they appear in the source. "
        "Avoid translationese, invented product claims, awkward literal phrasing, forced slang, and overly formal written language. "
        "Accuracy means preserving the original meaning and product facts while sounding like a native speaker in the target market. "
        "Keep product facts, shot order, timecodes, camera directions, quantities, and formatting unless the user asks otherwise. "
        "Create a second independent translation for consistency comparison when requested, then back-translate the main version. "
        "Audit the localized copy for Facebook and TikTok ad risks, including medical efficacy claims, absolute guarantees, false promises, "
        "body-shaming language, discriminatory wording, fake scarcity, and unsupported superlatives. "
        "Return only one valid JSON object with keys: translation, alternateTranslation, backTranslation, consistencyScore, "
        "consistencyNotes, compliance. compliance must contain riskLevel, flaggedTerms, suggestions. "
        "consistencyScore must be an integer from 0 to 100. Arrays must contain concise strings."
    )
    user_context = {
        "source_language": language_labels[source_language],
        "target_language": language_labels[target_language],
        "target_market": market,
        "content_scene": scene_labels[scene],
        "language_tone": tone_labels[tone],
        "native_localization_brief": native_localization_brief,
        "perform_back_translation": back_translation,
        "perform_dual_version_check": dual_pass,
        "perform_ad_compliance_audit": compliance_audit,
        "preserve_timecodes_shot_structure_and_linebreaks": preserve_format,
        "source_text": text,
    }
    response = call_ai_chat(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_context, ensure_ascii=False, indent=2)},
            ],
            "temperature": min(max(get_translation_temperature(runtime_config), 0), 1.5),
            "max_tokens": get_translation_max_tokens(runtime_config),
        },
        timeout_seconds=parse_int_env("TRANSLATION_TIMEOUT_SECONDS", 90),
        config=effective_config,
    )
    raw = extract_ai_text(response).strip()
    if not raw:
        raise AiError(HTTPStatus.BAD_GATEWAY, "翻译模型返回了空内容。")
    parsed = parse_json_object(raw)
    translation = str(parsed.get("translation") or raw).strip()
    alternate = str(parsed.get("alternateTranslation") or parsed.get("alternate_translation") or "").strip() if dual_pass else ""
    back = str(parsed.get("backTranslation") or parsed.get("back_translation") or "").strip() if back_translation else ""
    try:
        consistency_score = max(0, min(100, int(parsed.get("consistencyScore") or parsed.get("consistency_score") or (90 if translation else 0))))
    except (TypeError, ValueError):
        consistency_score = 90 if translation else 0
    notes_raw = parsed.get("consistencyNotes") or parsed.get("consistency_notes") or []
    consistency_notes = [str(item).strip() for item in notes_raw if str(item).strip()] if isinstance(notes_raw, list) else [str(notes_raw).strip()] if notes_raw else []
    compliance_raw = parsed.get("compliance") if isinstance(parsed.get("compliance"), dict) else {}
    flagged_raw = compliance_raw.get("flaggedTerms") or compliance_raw.get("flagged_terms") or []
    suggestions_raw = compliance_raw.get("suggestions") or []
    flagged_terms = flagged_raw if isinstance(flagged_raw, list) else [flagged_raw] if flagged_raw else []
    suggestions = [str(item).strip() for item in suggestions_raw if str(item).strip()] if isinstance(suggestions_raw, list) else [str(suggestions_raw).strip()] if suggestions_raw else []
    return {
        "translation": translation,
        "alternateTranslation": alternate,
        "backTranslation": back,
        "consistencyScore": consistency_score,
        "consistencyNotes": consistency_notes,
        "compliance": {
            "riskLevel": str(compliance_raw.get("riskLevel") or compliance_raw.get("risk_level") or "low").lower(),
            "flaggedTerms": flagged_terms,
            "suggestions": suggestions,
        },
        "model": model,
        "sourceLanguage": source_language,
        "targetLanguage": target_language,
        "market": market,
        "translatedAt": utc_now_iso(),
    }


def check_translated_ad_copy(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or "").strip()
    if not text:
        raise ValueError("请先填写需要核查的翻译文案。")
    if len(text) > 12000:
        raise ValueError("待核查文案最多 12000 个字符。")

    target_language = str(payload.get("targetLanguage") or "en-US").strip()[:50]
    market = str(payload.get("market") or "United States").strip()[:80]
    scene = str(payload.get("scene") or "social_ad").strip()[:80]
    runtime_config = read_runtime_config()
    model = get_translation_model(runtime_config)
    effective_config = translation_as_ai_config(runtime_config)
    if not get_translation_api_key(runtime_config):
        raise AiError(HTTPStatus.BAD_REQUEST, "请先配置翻译模型 API Key，或完成 AI 提示词接口配置。")

    system_prompt = (
        "You are a strict paid-social ad copy compliance reviewer for Facebook and TikTok. "
        "Review the supplied localized copy before voiceover or publishing. "
        "Check specifically for medical or efficacy claims, absolute or guaranteed language, false promises, "
        "unsupported superlatives, misleading before/after implications, and unrealistic outcome claims. "
        "Flag only wording that is genuinely risky, quote the exact risky term or phrase, explain why briefly, "
        "and give a natural replacement that keeps the original sales intent. "
        "Do not invent product facts or rewrite the whole copy when there is no issue. "
        "Return only one valid JSON object with keys: riskLevel, summary, flaggedTerms, suggestions. "
        "riskLevel must be low, medium, or high. Each flaggedTerms entry must contain term, category, reason, and suggestion. "
        "If no issue is found, return riskLevel low with an empty flaggedTerms array and concise suggestions."
    )
    user_context = {
        "target_language": target_language,
        "target_market": market,
        "content_scene": scene,
        "review_instruction": "Check Facebook/TikTok prohibited wording: medical efficacy, absolute wording, and false promises.",
        "translated_text": text,
    }
    response = call_ai_chat(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_context, ensure_ascii=False, indent=2)},
            ],
            "temperature": min(max(get_translation_temperature(runtime_config), 0), 1.0),
            "max_tokens": min(get_translation_max_tokens(runtime_config), 1800),
        },
        timeout_seconds=parse_int_env("TRANSLATION_TIMEOUT_SECONDS", 90),
        config=effective_config,
    )
    raw = extract_ai_text(response).strip()
    if not raw:
        raise AiError(HTTPStatus.BAD_GATEWAY, "违规词核查模型返回了空内容。")
    parsed = parse_json_object(raw)
    review_payload = parsed.get("compliance") if isinstance(parsed.get("compliance"), dict) else parsed
    risk_level = str(review_payload.get("riskLevel") or review_payload.get("risk_level") or "low").strip().lower()
    if risk_level not in {"low", "medium", "high"}:
        risk_level = "medium"
    raw_terms = review_payload.get("flaggedTerms") or review_payload.get("flagged_terms") or []
    if not isinstance(raw_terms, list):
        raw_terms = [raw_terms]
    flagged_terms: list[dict[str, str]] = []
    for item in raw_terms:
        if isinstance(item, dict):
            term = str(item.get("term") or item.get("phrase") or "").strip()
            if term:
                flagged_terms.append(
                    {
                        "term": term,
                        "category": str(item.get("category") or "广告风险").strip(),
                        "reason": str(item.get("reason") or "建议调整表达。 ").strip(),
                        "suggestion": str(item.get("suggestion") or item.get("replacement") or "").strip(),
                    }
                )
        elif str(item).strip():
            flagged_terms.append(
                {
                    "term": str(item).strip(),
                    "category": "广告风险",
                    "reason": "建议调整表达。",
                    "suggestion": "",
                }
            )
    raw_suggestions = review_payload.get("suggestions") or []
    if not isinstance(raw_suggestions, list):
        raw_suggestions = [raw_suggestions]
    suggestions = [str(item).strip() for item in raw_suggestions if str(item).strip()]
    return {
        "compliance": {
            "riskLevel": risk_level,
            "summary": str(review_payload.get("summary") or "已完成 Facebook / TikTok 广告违禁词核查。").strip(),
            "flaggedTerms": flagged_terms,
            "suggestions": suggestions,
        },
        "model": model,
        "checkedAt": utc_now_iso(),
    }


CREATIVE_MARKET_LANGUAGE_DEFAULTS = {
    "日本": "日语",
    "japan": "日语",
    "美国": "美式英语",
    "united states": "美式英语",
    "usa": "美式英语",
    "英国": "英式英语",
    "united kingdom": "英式英语",
    "uk": "英式英语",
    "韩国": "韩语",
    "south korea": "韩语",
    "法国": "法语",
    "france": "法语",
    "德国": "德语",
    "germany": "德语",
    "西班牙": "西班牙语",
    "spain": "西班牙语",
    "墨西哥": "西班牙语",
    "mexico": "西班牙语",
    "意大利": "意大利语",
    "italy": "意大利语",
    "巴西": "巴西葡萄牙语",
    "brazil": "巴西葡萄牙语",
    "泰国": "泰语",
    "thailand": "泰语",
    "越南": "越南语",
    "vietnam": "越南语",
    "印度尼西亚": "印度尼西亚语",
    "indonesia": "印度尼西亚语",
    "沙特阿拉伯": "阿拉伯语",
    "saudi arabia": "阿拉伯语",
    "阿联酋": "阿拉伯语",
    "united arab emirates": "阿拉伯语",
}


def get_creative_target_market(payload: dict[str, Any]) -> str:
    return str(payload.get("targetMarket") or payload.get("market") or "日本").strip()[:80] or "日本"


def get_creative_content_language(payload: dict[str, Any], market: str | None = None) -> str:
    raw = str(payload.get("contentLanguage") or payload.get("language") or "").strip()[:80]
    if raw and raw.lower() not in {"auto", "follow market", "match market"}:
        return raw
    target_market = market or get_creative_target_market(payload)
    return CREATIVE_MARKET_LANGUAGE_DEFAULTS.get(target_market.casefold(), "目标市场当地主要语言")


def apply_creative_localization_lock(prompt: str, target_market: str, content_language: str) -> str:
    text = str(prompt or "").strip()
    prefix: list[str] = []
    if target_market.casefold() not in text.casefold():
        prefix.append(f"目标市场为{target_market}，人物、日常场景和造型符合当地真实语境，不使用国家刻板印象")
    if content_language.casefold() not in text.casefold():
        prefix.append(f"如有口播或字幕，使用{content_language}和当地自然口语，不要翻译腔")
    return "。".join([*prefix, text]).strip("。")[:10000]


def generate_seedance_prompt(payload: dict[str, Any]) -> str:
    brief = str(payload.get("brief") or "").strip()
    draft = str(payload.get("draftPrompt") or "").strip()
    if not brief and not draft:
        raise ValueError("Brief or existing prompt is required.")

    model = get_ai_model()
    if not model:
        raise AiError(HTTPStatus.BAD_REQUEST, "AI_MODEL is missing.")

    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)
    system_prompt = (
        "You are a senior cross-market AI video prompt writer for SOSOVE womenswear ecommerce. "
        "The target market and content language in USER CONTEXT are authoritative; use Japan and Japanese only when they are explicitly selected or no market is supplied. "
        "Write one production-ready Seedance prompt in Chinese. Be concrete and visual. "
        "Preserve garment design details from the user's notes. Include subject, age/style, scene, actions, "
        "camera language, lighting, material close-ups, and realism constraints. Localize people, everyday setting, styling, dialogue, and social-video rhythm for the target market without stereotypes. "
        "If dialogue, voiceover, or captions are requested, use the selected content language with native local phrasing rather than translationese. "
        "Avoid markdown, titles, bullet points, subtitles, on-screen text, logos, or extra props unless requested. "
        "Return only the final prompt."
    )
    user_prompt = build_prompt_generation_user_message(payload, brief, draft)
    response = call_ai_chat(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": get_ai_temperature(),
            "max_tokens": get_ai_max_tokens(),
        }
    )
    generated = extract_ai_text(response)
    if not generated:
        raise AiError(HTTPStatus.BAD_GATEWAY, "AI response did not include prompt text.")
    prompt = generated.strip().strip('"')
    if seedance_prompt_needs_repair(prompt):
        return local_seedance_prompt(
            infer_product_type(f"{brief}\n{draft}"),
            f"{brief}\n{draft}",
            str(payload.get("ratio") or "9:16"),
            parse_duration(payload.get("duration")),
            target_market=target_market,
            content_language=content_language,
        )
    return apply_creative_localization_lock(prompt, target_market, content_language)


SEEDANCE_REFERENCE_TAG_RE = re.compile(
    r"@(?:图片|视频|音频|image|video|audio)\d+",
    re.IGNORECASE,
)


def extract_seedance_reference_tags(prompt: str) -> list[str]:
    return list(dict.fromkeys(SEEDANCE_REFERENCE_TAG_RE.findall(prompt or "")))


def normalize_seedance_score(raw_score: object, fallback: int = 0) -> int:
    try:
        return max(0, min(100, int(float(raw_score))))
    except (TypeError, ValueError):
        return fallback


def normalize_seedance_prompt_review(value: dict[str, Any], original_prompt: str) -> dict[str, Any]:
    legacy_score = normalize_seedance_score(value.get("score"), 0)
    score_before = normalize_seedance_score(
        value.get("scoreBefore", value.get("score_before")),
        legacy_score,
    )
    score_after = normalize_seedance_score(
        value.get("scoreAfter", value.get("score_after")),
        legacy_score or score_before,
    )
    score_after = max(score_before, score_after)

    verdict = str(value.get("verdict") or "revise").strip().lower()
    verdict_aliases = {
        "通过": "pass",
        "可生成": "pass",
        "修改": "revise",
        "需修改": "revise",
        "阻止": "block",
        "不建议生成": "block",
    }
    verdict = verdict_aliases.get(verdict, verdict)
    if verdict not in {"pass", "revise", "block"}:
        verdict = "pass" if score_after >= 85 else "revise"

    raw_issues = value.get("issues") or []
    if not isinstance(raw_issues, list):
        raw_issues = [raw_issues]
    issues: list[dict[str, str]] = []
    for item in raw_issues[:12]:
        if isinstance(item, dict):
            severity = str(item.get("severity") or item.get("level") or "warning").strip().lower()
            severity = {"warn": "warning", "error": "error", "info": "info"}.get(severity, severity)
            if severity not in {"error", "warning", "info"}:
                severity = "warning"
            finding = str(item.get("finding") or item.get("message") or item.get("problem") or "").strip()[:800]
            suggestion = str(item.get("suggestion") or item.get("repair") or item.get("fix") or "").strip()[:1200]
            if not finding and not suggestion:
                continue
            issues.append(
                {
                    "severity": severity,
                    "category": str(item.get("category") or "提示词质量").strip()[:80],
                    "finding": finding or "建议调整当前表达。",
                    "suggestion": suggestion,
                }
            )
        elif str(item).strip():
            issues.append(
                {
                    "severity": "warning",
                    "category": "提示词质量",
                    "finding": str(item).strip()[:800],
                    "suggestion": "",
                }
            )

    def clean_string_list(raw_value: object, limit: int = 8) -> list[str]:
        entries = raw_value if isinstance(raw_value, list) else [raw_value]
        return [str(item).strip()[:500] for item in entries if str(item).strip()][:limit]

    improved_prompt = str(
        value.get("improvedPrompt")
        or value.get("improved_prompt")
        or value.get("optimizedPrompt")
        or original_prompt
    ).strip()[:10000]
    required_reference_tags = extract_seedance_reference_tags(original_prompt)
    restored_reference_tags = [tag for tag in required_reference_tags if tag not in improved_prompt]
    if restored_reference_tags:
        improved_prompt = f"{' '.join(restored_reference_tags)}。{improved_prompt}".strip()[:10000]
        issues.append(
            {
                "severity": "info",
                "category": "素材引用",
                "finding": "优化结果曾遗漏原提示词中的素材引用标签，系统已原样补回。",
                "suggestion": "应用前确认每个引用素材的职责仍与原提示词一致。",
            }
        )
    mode = str(value.get("mode") or "T2V").strip().upper()
    if mode not in {"T2V", "I2V", "V2V", "R2V", "FLF2V", "EDIT", "EXTEND"}:
        mode = "R2V" if "@" in original_prompt else "T2V"
    return {
        "score": score_after,
        "scoreBefore": score_before,
        "scoreAfter": score_after,
        "verdict": verdict,
        "summary": str(value.get("summary") or "已按 Seedance 2.0 Skill 完成提示词优化。").strip()[:1200],
        "mode": mode,
        "strengths": clean_string_list(value.get("strengths") or value.get("preservedContent")),
        "preservedContent": clean_string_list(value.get("preservedContent") or value.get("strengths")),
        "issues": issues,
        "improvedPrompt": improved_prompt or original_prompt,
        "changeSummary": clean_string_list(value.get("changeSummary") or value.get("change_summary")),
        "referenceTags": required_reference_tags,
        "referenceTagsPreserved": not any(tag not in improved_prompt for tag in required_reference_tags),
        "restoredReferenceTags": restored_reference_tags,
    }


def review_seedance_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("请先填写需要优化的视频生成提示词。")
    if len(prompt) > 10000:
        raise ValueError("视频生成提示词不能超过 10000 个字符。")

    runtime_config = read_runtime_config()
    model = get_ai_model(runtime_config)
    if not get_ai_api_key(runtime_config):
        raise AiError(HTTPStatus.BAD_REQUEST, "请先配置 AI 提示词模型 API Key。")

    skill_context, skill_files = load_seedance_review_skill_context()
    system_prompt = (
        "你是 Seedance 2.0 提示词优化导演。以下 LOCAL SKILL CONTEXT 来自已安装的 seedance-20 v6.7.0，"
        "必须作为本次重写规则。你的主要任务不是点评，而是把用户原提示词重写成效果更好、可直接提交到火山 Ark 的视频提示词；"
        "即使原提示词已经可用，也必须返回经过精炼的 improvedPrompt，不能只返回意见。"
        "先判断 T2V、I2V、V2V、R2V、FLF2V、EDIT 或 EXTEND 模式，再按主体与主要动作、场景、"
        "一个主镜头运动及明确终点、物理光源、声音、保持约束的顺序重写。"
        "每条短片聚焦一个可见节拍和一个主要运镜，确保动作在给定时长内可执行。"
        "商品展示、功能演示和纯视觉产品镜头走非叙事路线，不得虚构人物心理、冲突或剧情。"
        "删除电影感、震撼、8K、专业、高质量等空泛词，改成可观察的动作、构图、材质、光源和声音。"
        "I2V/R2V 不要重复描述参考素材已经呈现的静态内容，重点写运动、镜头、时间、参考职责和保持约束。"
        "USER CONTEXT.targetMarket 和 contentLanguage 是本次本地化的最高优先级；人物、日常场景、造型、口播和节奏要适应该市场，"
        "只有明确选择日本或未提供市场时才使用日本与日语默认值。不得使用国家刻板印象。"
        "必须逐字保留 USER CONTEXT.requiredReferenceTags 中的每个 @ 引用标签，不得翻译、改大小写、重编号或删除。"
        "必须保留用户明确提供的商品事实、核心创意和硬性要求；不得新增未提供的功效、价格、颜色、面料、"
        "身体效果、品牌授权、人物身份或其他商品事实。不要把内部 Director's Read 标签写入最终提示词。"
        "如果内容安全或授权存在实质风险，verdict 返回 block，但仍要给出安全、原创、可执行的替代 improvedPrompt。"
        "只返回一个有效 JSON 对象，字段必须为 scoreBefore、scoreAfter、score、verdict、summary、mode、"
        "preservedContent、strengths、issues、improvedPrompt、changeSummary。scoreBefore 和 scoreAfter 为 0-100 整数，"
        "score 等于 scoreAfter；verdict 只用 pass、revise、block；preservedContent 列出保留的事实、引用和创意，"
        "changeSummary 列出实际完成的主要重写。"
        "issues 每项包含 severity、category、finding、suggestion，severity 只用 error、warning、info。"
        "improvedPrompt 必须是可直接提交的自然语言视频提示词，不要使用 Markdown 标题或代码块。\n\n"
        f"LOCAL SKILL CONTEXT:\n{skill_context}"
    )

    ref_images = payload.get("refImages") if isinstance(payload.get("refImages"), list) else []
    ref_videos = payload.get("refVideos") if isinstance(payload.get("refVideos"), list) else []
    ref_audios = payload.get("refAudios") if isinstance(payload.get("refAudios"), list) else []
    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)
    user_context = {
        "surface": "Volcengine Ark / Seedance 2.0",
        "model": str(payload.get("model") or get_default_model()).strip()[:160],
        "targetMarket": target_market,
        "contentLanguage": content_language,
        "ratio": str(payload.get("ratio") or "9:16").strip()[:20],
        "durationSeconds": parse_duration(payload.get("duration")),
        "generateAudio": bool(payload.get("generateAudio")),
        "referenceCounts": {
            "images": len(ref_images),
            "videos": len(ref_videos),
            "audios": len(ref_audios),
        },
        "requiredReferenceTags": extract_seedance_reference_tags(prompt),
        "productBrief": str(payload.get("brief") or "").strip()[:4000],
        "prompt": prompt,
    }
    response = call_ai_chat(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_context, ensure_ascii=False, indent=2)},
            ],
            "temperature": 0.2,
            "max_tokens": max(1800, min(get_ai_max_tokens(runtime_config), 3200)),
        },
        timeout_seconds=parse_int_env("SEEDANCE_REVIEW_TIMEOUT_SECONDS", 120),
        config=runtime_config,
    )
    raw = extract_ai_text(response).strip()
    if not raw:
        raise AiError(HTTPStatus.BAD_GATEWAY, "Seedance Skill 优化模型返回了空内容。")
    parsed = parse_json_object(raw)
    if not parsed:
        raise AiError(HTTPStatus.BAD_GATEWAY, "Seedance Skill 优化结果不是有效 JSON，请重试。")
    review_payload = parsed.get("review") if isinstance(parsed.get("review"), dict) else parsed
    completed_at = utc_now_iso()
    normalized_review = normalize_seedance_prompt_review(review_payload, prompt)
    localized_prompt = apply_creative_localization_lock(
        normalized_review["improvedPrompt"],
        target_market,
        content_language,
    )
    if localized_prompt != normalized_review["improvedPrompt"]:
        normalized_review["improvedPrompt"] = localized_prompt
        normalized_review["changeSummary"] = [
            *normalized_review["changeSummary"],
            f"锁定{target_market}市场与{content_language}本地化要求",
        ][:8]
    return {
        "review": normalized_review,
        "skill": {**build_seedance_review_skill_status(), "files": skill_files},
        "model": model,
        "optimizedAt": completed_at,
        "reviewedAt": completed_at,
    }


def generate_skill_video_plan(payload: dict[str, Any]) -> dict[str, Any]:
    brief = str(payload.get("brief") or "").strip()
    draft = str(payload.get("draftPrompt") or "").strip()
    if not brief and not draft:
        raise ValueError("Product brief or existing prompt is required.")

    model = get_ai_model()
    if not model:
        raise AiError(HTTPStatus.BAD_REQUEST, "AI_MODEL is missing.")

    prompt_count = parse_prompt_count(payload.get("promptCount"))
    skill_context, skill_files = load_skill_context(f"{brief}\n{draft}")
    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)
    system_prompt = (
        "You are executing a local Codex skill for SOSOVE cross-market womenswear video production. "
        "Follow the provided SKILL.md and reference files as procedural instructions. "
        "The user-selected target market and content language override any Japanese defaults found in the local skill context. "
        "Use Japanese-market assumptions only when Japan is selected or no target market was supplied. "
        f"The active target market is {target_market}, and the content language is {content_language}. "
        "Generate fact-safe localized ad copy, a segmented UGC script, real-shoot SOP, "
        "Seedance prompts, and material gaps. Do not invent missing product facts. "
        "Return only a valid JSON object with these keys: product_type, content, seedance_prompt, prompts, "
        "negative_prompt, missing_materials. The content value must be Markdown in Chinese with native target-language copy where required. "
        f"The prompts value must contain exactly {prompt_count} distinct production-ready Chinese Seedance prompts. "
        "Each prompts item must have title, angle, seedance_prompt, and negative_prompt. "
        "Each seedance prompt must be directly submit-ready, Chinese, visual, and not Markdown. "
        "Keep brand and model names such as SOSOVE or Seedance in their original form when needed."
    )
    user_prompt = build_skill_generation_user_message(payload, brief, draft, skill_context)
    try:
        response = call_ai_chat(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": min(max(get_ai_temperature(), 0.2), 1.0),
                "max_tokens": max(get_ai_max_tokens(), 1800),
            },
            timeout_seconds=parse_int_env("SKILL_AI_TIMEOUT_SECONDS", 20),
        )
    except AiError as exc:
        return generate_local_skill_video_plan(payload, brief, draft, skill_files, str(exc.message), model, prompt_count)
    raw = extract_ai_text(response)
    if not raw:
        return generate_local_skill_video_plan(payload, brief, draft, skill_files, "AI response did not include skill output.", model, prompt_count)

    parsed = parse_json_object(raw)
    content = str(parsed.get("content") or raw).strip()
    seedance_prompt = str(parsed.get("seedance_prompt") or "").strip()
    if not seedance_prompt:
        seedance_prompt = extract_seedance_prompt(content)
    if not seedance_prompt:
        seedance_prompt = content
    prompt_repaired = False
    prompt_warning = ""
    if seedance_prompt_needs_repair(seedance_prompt):
        seedance_prompt = local_seedance_prompt(
            infer_product_type(f"{brief}\n{draft}"),
            f"{brief}\n{draft}",
            str(payload.get("ratio") or "9:16"),
            parse_duration(payload.get("duration")),
            target_market=target_market,
            content_language=content_language,
        )
        prompt_repaired = True
        prompt_warning = "AI 返回的 seedance_prompt 不是可直接提交的视频提示词，已用本地规则修正。"
    prompt_items = normalize_skill_prompt_items(
        parsed,
        seedance_prompt,
        negative_prompt=str(parsed.get("negative_prompt") or "").strip(),
        product_text=f"{brief}\n{draft}",
        payload=payload,
        prompt_count=prompt_count,
    )
    seedance_prompt = prompt_items[0]["seedancePrompt"] if prompt_items else seedance_prompt

    negative_prompt = str(parsed.get("negative_prompt") or "").strip()
    missing_materials = parsed.get("missing_materials")
    if not isinstance(missing_materials, list):
        missing_materials = []

    return {
        "model": model,
        "skill": build_skill_status(),
        "skillFiles": skill_files,
        "productType": str(parsed.get("product_type") or "").strip(),
        "content": content,
        "prompt": seedance_prompt,
        "seedancePrompt": seedance_prompt,
        "prompts": prompt_items,
        "promptCount": len(prompt_items),
        "negativePrompt": negative_prompt,
        "missingMaterials": [str(item) for item in missing_materials],
        "fallback": False,
        "promptRepaired": prompt_repaired,
        "warning": prompt_warning,
    }


def generate_local_skill_video_plan(
    payload: dict[str, Any],
    brief: str,
    draft: str,
    skill_files: list[str],
    reason: str,
    model: str,
    prompt_count: int | None = None,
) -> dict[str, Any]:
    source_text = f"{brief}\n{draft}"
    product_type = infer_product_type(source_text)
    ratio = str(payload.get("ratio") or "9:16")
    duration = parse_duration(payload.get("duration"))
    count = parse_prompt_count(prompt_count)
    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)
    product_label = local_product_label(product_type)
    copy_lines = [
        f"用{content_language}写一句{target_market}当地口语化的穿着结果钩子",
        f"用{content_language}自然说明一个有画面证据的商品细节",
        f"用{content_language}连接{target_market}日常使用或穿搭场景",
        f"用{content_language}写一句不虚构优惠的低压 CTA",
    ]
    structure = local_structure(product_type)
    prompt_items = build_local_prompt_items(
        product_type,
        source_text,
        ratio,
        duration,
        count,
        target_market=target_market,
        content_language=content_language,
    )
    seedance_prompt = prompt_items[0]["seedancePrompt"]
    negative_prompt = (
        "No cinematic fashion film, no luxury commercial, no runway walk, no heavy beauty filter, "
        "no exaggerated slimming transformation, no body deformation, no distorted hands, "
        "no changed product design, no changed color, no unsupported text claims."
    )
    missing_materials = [
        "商品价格/折扣未确认时，不写折扣、促销、库存相关文案。",
        "材质/弹力/凉感未确认时，不写素材功能承诺。",
        "尺码和模特身高未确认时，CTA 引导查看商品页。",
        "缺少正面、侧面、背面和细节参考图时，Seedance 只能做弱结构保持。",
    ]
    content = f"""## 商品事实表
| 字段 | 内容 | 来源 | 可用于文案 | 风险备注 |
| --- | --- | --- | --- | --- |
| 商品资料 | {source_text or "未提供"} | 用户输入 | 是 | 仅使用已写明信息 |
| 品类 | {product_label} | 本地规则判断 | 是 | 如判断不准，补充品类名后重生成 |
| 价格/折扣 | 未提供 | 未提供 | 否 | 不写优惠承诺 |
| 材质/功能 | 未提供 | 未提供 | 否 | 不写弹力、凉感、抗皱等功能 |
| 尺码/模特身高 | 未提供 | 未提供 | 否 | CTA 引导查看商品页 |

## 推荐结构
结构名：{structure["name"]}
适用品类：{product_label}
核心假设：先用真实上身/穿着效果建立信任，再用细节动作证明舒适和遮盖，最后低压 CTA。
目标市场：{target_market}；内容语言：{content_language}。
数据/素材依据：本地 skill 规则生成；AI 节点未返回，已启用多国家本地兜底。原因：{reason}

| 段落 | 时间 | 画面 | 动作 | 本地化字幕/口播 | 中文解释 | 目的 |
| --- | --- | --- | --- | --- | --- | --- |
| Hook | 0-3s | {structure["hook_shot"]} | {structure["hook_action"]} | {copy_lines[0]} | 先给目标人群看到穿着结果 | 停止滑动 |
| Body proof | 3-12s | {structure["body_shot"]} | {structure["body_action"]} | {copy_lines[1]} | 用动作证明版型和舒适度 | 建立信任 |
| Scene | 12-22s | {structure["scene_shot"]} | {structure["scene_action"]} | {copy_lines[2]} | 展示通勤和休日想象 | 提高使用场景 |
| CTA | 最后3-8s | 商品页/颜色尺码信息 | 定格展示 | {copy_lines[3]} | 不写未提供优惠 | 引导查看 |

## 实拍 SOP
| 镜头 | 必拍画面 | 模特动作 | 机位/景别 | 证明卖点 | 注意 |
| --- | --- | --- | --- | --- | --- |
| 1 | 第一秒已穿上身 | 自然站立或轻走 | 手机竖屏，中近景 | 真实穿着效果 | 不用包装/挂拍开头 |
| 2 | 细节近景 | 手部整理关键结构 | 近景 | 商品结构 | 不改变扣子、腰头、领口、裙摆等 |
| 3 | 正侧背全身 | 走动、转身 | 全身景 | 版型和遮盖 | 保持真实体型 |
| 4 | 日常动作 | 坐下、抬手或转身 | 中景/全身 | 舒适度 | 未确认功能不写硬承诺 |
| 5 | 场景搭配 | 换包/鞋/外搭 | 全身景 | 通勤/休日 | 风格真实，不像广告大片 |

## Seedance Prompt
视频生成提示词：
真实手机实拍风格，{product_label}，面向{target_market}用户，目标人群以用户输入为准。第一秒直接展示已经穿上后的真实效果，随后展示细节近景、正侧背全身走动和日常动作测试。画面采用符合{target_market}日常环境的自然光和手持镜头；如有口播或字幕，使用自然{content_language}，不夸张瘦身，不改变商品结构。

队列首条：
{seedance_prompt}

## Prompt 队列
{format_prompt_queue_markdown(prompt_items)}

Negative Prompt:
{negative_prompt}

参考图建议：
- 图 1：商品正面全身图
- 图 2：侧面/背面穿着图
- 图 3：关键结构细节图

## 素材缺口 / 风险提醒
| 缺口 | 影响 | 建议补拍/补充 | 优先级 |
| --- | --- | --- | --- |
| 价格/折扣未提供 | 不能写优惠 CTA | 补商品页价格或不写优惠 | 中 |
| 材质/功能未提供 | 不能写弹力、凉感、抗皱 | 补页面参数或只写视觉体感 | 高 |
| 结构参考图不足 | AI 可能改商品结构 | 补正面、侧面、背面、细节图 | 高 |
| 模特身高/尺码未提供 | 长度和尺码参考弱 | 补模特身高和试穿尺码 | 中 |

## 可沉淀资产
Hook tags：{product_label}/真实上身/{target_market}本地钩子
Body tags：商品细节/动作证明/自然穿着效果
CTA copy：使用{content_language}引导查看商品页，不虚构优惠
Scene tags：{target_market}工作日/周末/日常外出
Visual-action tags：走动/转身/坐下/细节整理
"""
    return {
        "model": model,
        "skill": build_skill_status(),
        "skillFiles": skill_files,
        "productType": product_type,
        "content": content,
        "prompt": seedance_prompt,
        "seedancePrompt": seedance_prompt,
        "prompts": prompt_items,
        "promptCount": len(prompt_items),
        "negativePrompt": negative_prompt,
        "missingMaterials": missing_materials,
        "fallback": True,
        "warning": f"AI 节点未及时返回，已使用本地 skill 规则兜底生成。原因：{reason}",
    }


def build_skill_generation_user_message(payload: dict[str, Any], brief: str, draft: str, skill_context: str) -> str:
    ratio = str(payload.get("ratio") or "9:16")
    duration = parse_duration(payload.get("duration"))
    quantity = parse_quantity(payload.get("quantity"))
    prompt_count = parse_prompt_count(payload.get("promptCount"))
    ref_images = parse_url_list(payload.get("refImages"))
    ref_videos = parse_url_list(payload.get("refVideos"))
    ref_audios = parse_url_list(payload.get("refAudios"))
    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)
    context = {
        "brand": "SOSOVE",
        "target_market": target_market,
        "content_language": content_language,
        "target_audience": "Use the audience in the product brief; do not replace it with a Japanese default.",
        "market_localization_rule": "Localize people, everyday setting, styling, spoken rhythm, and platform-native wording for this market without stereotypes.",
        "ratio": ratio,
        "duration_seconds": duration,
        "batch_quantity": quantity,
        "prompt_count": prompt_count,
        "reference_images": ref_images,
        "reference_videos": ref_videos,
        "reference_audios": ref_audios,
        "generate_audio": bool(payload.get("generateAudio")),
        "watermark": bool(payload.get("watermark")),
        "product_brief": brief,
        "existing_seedance_prompt_or_notes": draft,
    }
    return (
        "Use the local skill instructions below to generate a complete production plan. "
        "First infer the product type, then apply the matching reference structure. "
        "If the product facts are incomplete, mark them as 未提供 and avoid unsupported claims. "
        f"Produce exactly {prompt_count} distinct Chinese Seedance prompts in the JSON prompts array. "
        "The seedance_prompt fields must be Chinese video-generation prompts that can be submitted directly; do not write them as analysis, Markdown, or copy tables. "
        "Make each prompt a different creative angle, for example pain-point proof, detail proof, scene expansion, or comfort test. "
        "Also set seedance_prompt to the first prompts item's seedance_prompt.\n\n"
        "LOCAL SKILL CONTEXT:\n"
        f"{skill_context}\n\n"
        "USER CONTEXT:\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def get_skill_dir() -> Path:
    configured = os.environ.get("SOSOVE_VIDEO_SKILL_DIR", "").strip()
    return Path(configured) if configured else DEFAULT_SKILL_DIR


def build_skill_status() -> dict[str, Any]:
    skill_dir = get_skill_dir()
    skill_md = skill_dir / "SKILL.md"
    return {
        "name": "sosove-japan-fashion-video-generator",
        "path": str(skill_dir),
        "exists": skill_md.exists(),
    }


def get_seedance_review_skill_dir() -> Path:
    configured = os.environ.get("SEEDANCE_REVIEW_SKILL_DIR", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_SEEDANCE_REVIEW_SKILL_DIR


def build_seedance_review_skill_status() -> dict[str, Any]:
    skill_dir = get_seedance_review_skill_dir()
    skill_md = skill_dir / "SKILL.md"
    version = ""
    if skill_md.exists() and skill_md.is_file():
        try:
            header = skill_md.read_text(encoding="utf-8")[:4000]
            match = re.search(r"(?m)^\s*version:\s*[\"']?([^\"'\r\n]+)", header)
            version = match.group(1).strip() if match else ""
        except OSError:
            version = ""
    return {
        "name": "seedance-20",
        "path": str(skill_dir),
        "exists": skill_md.exists(),
        "version": version,
    }


def load_seedance_review_skill_context() -> tuple[str, list[str]]:
    return load_seedance_skill_context_files(SEEDANCE_REVIEW_SKILL_FILES)


def load_ad_forge_prompt_skill_context() -> tuple[str, list[str]]:
    return load_seedance_skill_context_files(
        AD_FORGE_PROMPT_SKILL_FILES,
        max_chars=MAX_AD_FORGE_PROMPT_SKILL_CONTEXT_CHARS,
    )


def load_seedance_skill_context_files(
    relative_files: list[str],
    max_chars: int = MAX_SEEDANCE_REVIEW_CONTEXT_CHARS,
) -> tuple[str, list[str]]:
    skill_dir = get_seedance_review_skill_dir()
    if not (skill_dir / "SKILL.md").is_file():
        raise ValueError(f"Seedance prompt review skill is not installed: {skill_dir}")

    parts: list[str] = []
    loaded: list[str] = []
    total_chars = 0
    for relative_name in relative_files:
        path = skill_dir / relative_name
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not content:
            continue
        remaining = max_chars - total_chars
        if remaining <= 0:
            break
        content = content[:remaining]
        parts.append(f"--- FILE: {relative_name} ---\n{content}")
        loaded.append(relative_name)
        total_chars += len(content)

    if not parts:
        raise ValueError(f"Seedance prompt review skill has no readable review files: {skill_dir}")
    return "\n\n".join(parts), loaded


def load_skill_context(product_text: str = "") -> tuple[str, list[str]]:
    skill_dir = get_skill_dir()
    if not skill_dir.exists():
        raise ValueError(f"Skill directory not found: {skill_dir}")
    files = ["SKILL.md", *COMMON_SKILL_REFERENCE_FILES, *select_product_reference_files(product_text)]
    parts: list[str] = []
    loaded: list[str] = []
    for relative_name in files:
        path = skill_dir / relative_name
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        loaded.append(relative_name)
        parts.append(f"--- FILE: {relative_name} ---\n{text}")
    if not parts:
        raise ValueError(f"No readable skill files found under: {skill_dir}")
    return "\n\n".join(parts), loaded


def select_product_reference_files(product_text: str) -> list[str]:
    product_type = infer_product_type(product_text)
    if product_type in PRODUCT_SKILL_REFERENCE_FILES:
        return [PRODUCT_SKILL_REFERENCE_FILES[product_type]]
    return [PRODUCT_SKILL_REFERENCE_FILES["fallback"]]


def infer_product_type(product_text: str) -> str:
    text = product_text.lower()
    selected: list[str] = []
    keyword_groups = [
        ("pants", ["裤", "牛仔", "阔腿", "jeans", "denim", "pants", "slacks", "cargo", "wide-leg"]),
        ("skirt", ["半身裙", "百褶裙", "裙", "skirt", "pleated", "midi skirt", "maxi skirt", "skort"]),
        ("dress", ["连衣裙", "衬衫裙", "ワンピース", "dress", "shirt dress", "one-piece", "tunic"]),
        ("fallback", ["上衣", "衬衫", "针织", "开衫", "外套", "马甲", "blouse", "knit", "cardigan", "jacket", "coat", "top"]),
    ]
    for key, keywords in keyword_groups:
        if any(keyword in text for keyword in keywords):
            return key
    return "fallback"


def local_product_label(product_type: str) -> str:
    return {
        "pants": "裤装 / 阔腿裤 / 牛仔裤",
        "skirt": "半身裙",
        "dress": "连衣裙 / 衬衫裙 / One-piece",
        "fallback": "上装 / 外套 / 未确认品类",
    }.get(product_type, "未确认品类")


def local_japanese_copy(product_type: str) -> list[str]:
    copy_bank = {
        "pants": [
            "下っ腹ぽっこり、気になる人へ",
            "お尻と太ももを拾いにくい",
            "通勤にも休日にも使える",
            "サイズ詳細は商品ページでチェック",
        ],
        "skirt": [
            "腰まわり、自然にカバー",
            "歩くたびにきれいに揺れる",
            "きれいめにもカジュアルにも",
            "丈感・サイズ詳細は商品ページへ",
        ],
        "dress": [
            "大人っぽく、でも重く見えない",
            "ストンと落ちて体のラインを拾いにくい",
            "通勤にも休日にも使える一枚",
            "サイズ詳細は商品ページへ",
        ],
        "fallback": [
            "一枚でさっと決まる",
            "体のラインを拾いにくい",
            "パンツにもスカートにも合わせやすい",
            "カラー・サイズは商品ページでチェック",
        ],
    }
    return copy_bank.get(product_type, copy_bank["fallback"])


def local_structure(product_type: str) -> dict[str, str]:
    structures = {
        "pants": {
            "name": "下半身痛点 -> 腰部解决 -> 臀腿证明 -> 舒适测试 -> 场景 CTA",
            "hook_shot": "普通裤与本品效果对比，腰腹或臀腿区域礼貌展示",
            "hook_action": "先展示顾虑，再切换到本品穿着结果",
            "body_shot": "腰部细节、正面走动、侧背走动、坐下起身",
            "body_action": "整理腰头、走两步、坐下再起身",
            "scene_shot": "T恤/衬衫/外套切换",
            "scene_action": "通勤包和休闲鞋切换",
        },
        "skirt": {
            "name": "腰臀顾虑 -> 垂坠证明 -> 走动转身 -> 坐下/台阶 -> 场景 CTA",
            "hook_shot": "已穿上后的腰部到全身效果",
            "hook_action": "轻转身展示裙长和腰臀线条",
            "body_shot": "正侧背全身、裙摆、褶皱或开衩细节",
            "body_action": "走动、小幅转身、坐下或上下台阶",
            "scene_shot": "上班鞋包与周末搭配切换",
            "scene_action": "换包、换鞋、轻整理裙摆",
        },
        "dress": {
            "name": "上身质感 -> 全身比例 -> 腰部调整 -> 遮盖垂坠 -> 场景 CTA",
            "hook_shot": "第一秒已穿上身，上半身近景",
            "hook_action": "整理领口、口袋或腰部结构",
            "body_shot": "全身侧走、腰部调整、手臂抬起或侧面检查",
            "body_action": "走动、调整腰绳、抬手检查二の腕",
            "scene_shot": "办公室和周末搭配",
            "scene_action": "换包、换鞋或加外搭",
        },
        "fallback": {
            "name": "穿着结果 -> 细节近景 -> 活动证明 -> 搭配分层 -> 场景 CTA",
            "hook_shot": "第一秒已穿上身，上半身或全身结果",
            "hook_action": "自然站立并整理领口/袖口/下摆",
            "body_shot": "领口、袖子、纽扣、纹理、正侧背检查",
            "body_action": "抬手、转肩、侧身和背面检查",
            "scene_shot": "裤装/半身裙/内搭变化",
            "scene_action": "换下装或外搭，展示日常搭配",
        },
    }
    return structures.get(product_type, structures["fallback"])


def normalize_skill_prompt_items(
    parsed: dict[str, Any],
    first_prompt: str,
    negative_prompt: str,
    product_text: str,
    payload: dict[str, Any],
    prompt_count: int,
) -> list[dict[str, str]]:
    product_type = infer_product_type(product_text)
    ratio = str(payload.get("ratio") or "9:16")
    duration = parse_duration(payload.get("duration"))
    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)
    items: list[dict[str, str]] = []
    raw_items = parsed.get("prompts")
    if isinstance(raw_items, list):
        for index, item in enumerate(raw_items):
            if isinstance(item, dict):
                prompt = str(item.get("seedance_prompt") or item.get("prompt") or "").strip()
                title = str(item.get("title") or f"Prompt {index + 1}").strip()
                angle = str(item.get("angle") or "").strip()
                item_negative = str(item.get("negative_prompt") or negative_prompt or "").strip()
            else:
                prompt = str(item or "").strip()
                title = f"Prompt {index + 1}"
                angle = ""
                item_negative = negative_prompt
            if not prompt:
                continue
            if seedance_prompt_needs_repair(prompt):
                prompt = local_seedance_prompt(
                    product_type,
                    product_text,
                    ratio,
                    duration,
                    index,
                    target_market=target_market,
                    content_language=content_language,
                )
            prompt = apply_creative_localization_lock(prompt, target_market, content_language)
            items.append(
                {
                    "title": title or f"Prompt {index + 1}",
                    "angle": angle or local_variant_title(product_type, index),
                    "seedancePrompt": prompt,
                    "negativePrompt": item_negative,
                }
            )
            if len(items) >= prompt_count:
                break

    if first_prompt and len(items) < prompt_count and not any(item["seedancePrompt"] == first_prompt for item in items):
        items.insert(
            0,
            {
                "title": "Prompt 1",
                "angle": local_variant_title(product_type, 0),
                "seedancePrompt": apply_creative_localization_lock(
                    first_prompt if not seedance_prompt_needs_repair(first_prompt) else local_seedance_prompt(
                        product_type,
                        product_text,
                        ratio,
                        duration,
                        0,
                        target_market=target_market,
                        content_language=content_language,
                    ),
                    target_market,
                    content_language,
                ),
                "negativePrompt": negative_prompt,
            },
        )

    while len(items) < prompt_count:
        index = len(items)
        items.append(
            {
                "title": f"Prompt {index + 1}",
                "angle": local_variant_title(product_type, index),
                "seedancePrompt": local_seedance_prompt(
                    product_type,
                    product_text,
                    ratio,
                    duration,
                    index,
                    target_market=target_market,
                    content_language=content_language,
                ),
                "negativePrompt": negative_prompt,
            }
        )
    return items[:prompt_count]


def build_local_prompt_items(
    product_type: str,
    product_text: str,
    ratio: str,
    duration: int,
    prompt_count: int,
    target_market: str = "日本",
    content_language: str = "日语",
) -> list[dict[str, str]]:
    items = []
    for index in range(parse_prompt_count(prompt_count)):
        items.append(
            {
                "title": f"Prompt {index + 1}",
                "angle": local_variant_title(product_type, index),
                "seedancePrompt": local_seedance_prompt(
                    product_type,
                    product_text,
                    ratio,
                    duration,
                    index,
                    target_market=target_market,
                    content_language=content_language,
                ),
                "negativePrompt": (
                    "No cinematic fashion film, no luxury commercial, no runway walk, no heavy beauty filter, "
                    "no exaggerated slimming transformation, no body deformation, no changed garment design, no text overlays."
                ),
            }
        )
    return items


def format_prompt_queue_markdown(prompt_items: list[dict[str, str]]) -> str:
    rows = ["| 序号 | 角度 | Seedance Prompt |", "| --- | --- | --- |"]
    for index, item in enumerate(prompt_items, start=1):
        prompt = item["seedancePrompt"].replace("|", "/").replace("\n", " ")
        rows.append(f"| {index} | {item.get('angle') or item.get('title') or f'Prompt {index}'} | {prompt} |")
    return "\n".join(rows)


def local_variant_title(product_type: str, index: int) -> str:
    titles = {
        "pants": ["腰腹舒适测试", "臀腿不贴身走动", "通勤休日穿搭切换", "腰部细节近景"],
        "skirt": ["腰臀自然遮盖", "裙摆走动垂坠", "坐下台阶日常测试", "通勤休日搭配"],
        "dress": ["第一秒上身质感", "腰部调整和垂坠", "二の腕自然遮盖", "通勤休日一衣多穿"],
        "fallback": ["上身结果展示", "细节和活动证明", "搭配分层场景", "正侧背版型检查"],
    }
    values = titles.get(product_type, titles["fallback"])
    return values[index % len(values)]


def local_variant_focus_en(product_type: str, index: int) -> str:
    focus = {
        "pants": [
            "Focus the pacing on the waistband close-up and the sitting-standing comfort test.",
            "Focus the pacing on side and back walking shots that show a non-clinging hip and thigh silhouette.",
            "Focus the pacing on two outfit changes: a neat office look and a relaxed weekend look.",
            "Focus the pacing on hand-held detail shots of the waist, pockets, front closure, and fabric drape.",
        ],
        "skirt": [
            "Focus the pacing on waist and hip fit without exaggerating body changes.",
            "Focus the pacing on the skirt hem movement while walking and turning naturally.",
            "Focus the pacing on sitting, standing, and stair movement for daily comfort.",
            "Focus the pacing on office and weekend styling with subtle shoe and bag changes.",
        ],
        "dress": [
            "Focus the pacing on the first-second upper-body worn result and garment texture.",
            "Focus the pacing on waist adjustment and side walking to show drape.",
            "Focus the pacing on arm raise and side angle to show natural upper-arm coverage.",
            "Focus the pacing on office and weekend styling with small accessory changes.",
        ],
        "fallback": [
            "Focus the pacing on the worn result in the first second.",
            "Focus the pacing on construction details and natural arm movement.",
            "Focus the pacing on practical layering and daily styling.",
            "Focus the pacing on front, side, and back fit checks.",
        ],
    }
    values = focus.get(product_type, focus["fallback"])
    return values[index % len(values)]


def local_seedance_prompt(
    product_type: str,
    product_text: str,
    ratio: str,
    duration: int,
    variant_index: int = 0,
    target_market: str = "日本",
    content_language: str = "日语",
) -> str:
    product_label = local_product_label(product_type)
    product_note = compact_product_note(product_text)
    structure = local_structure(product_type)
    variant_focus = local_variant_title(product_type, variant_index)
    return (
        f"{duration}秒{ratio}真实手机实拍风格UGC视频，品牌为SOSOVE女装，目标市场为{target_market}。"
        f"模特年龄、形象与造型以用户填写的目标人群为准，符合{target_market}真实消费者与当地日常环境，穿着{product_label}。"
        f"商品信息：{product_note or '以参考图中的服装为准，严格保持颜色、版型、长度、腰头、下摆、领口、口袋、纽扣和面料纹理'}。"
        f"本条重点：{variant_focus}。"
        f"0-1秒：{structure['hook_shot']}，{structure['hook_action']}，第一秒直接看到穿上后的真实效果。"
        f"1-3秒：拍摄关键细节近景，重点展示{structure['body_shot']}，手部自然整理衣服，不遮挡结构。"
        f"3-{max(4, duration - 2)}秒：{structure['body_action']}，展示正面、侧面、背面、走动和日常动作中的自然垂坠与舒适度。"
        f"最后场景：{structure['scene_shot']}，{structure['scene_action']}，营造符合{target_market}工作日与日常外出的真实氛围。"
        f"如需要口播或字幕，使用{content_language}，表达像{target_market}当地创作者自然说话，不要翻译腔。"
        f"画面使用符合{target_market}生活环境的室内自然光或日常街区光线，手持手机镜头，真实肤质和真实体型比例。"
        "整体像真实买家/达人随手拍，不要电影感大片，不要T台走秀，不要奢侈品广告感。"
        "不要使用国家刻板印象，不要添加价格牌、促销卡片、品牌水印、夸张字幕、额外商品功效、过度瘦身、身体变形或改变服装设计。"
    )


def compact_product_note(product_text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", product_text or "").strip()
    return text[:limit].rstrip()


def local_product_label_en(product_type: str, product_text: str) -> str:
    color = extract_color_en(product_text)
    garment = infer_garment_en(product_type, product_text)
    return f"{color} {garment}" if color else garment


def extract_color_en(product_text: str) -> str:
    text = product_text.lower()
    color_map = [
        ("gray", ["灰色", "灰", "グレー", "gray", "grey"]),
        ("white", ["白色", "白", "ホワイト", "white"]),
        ("black", ["黑色", "黑", "ブラック", "black"]),
        ("navy", ["藏青", "深蓝", "ネイビー", "navy"]),
        ("blue", ["蓝色", "蓝", "ブルー", "blue"]),
        ("beige", ["米色", "杏色", "ベージュ", "beige"]),
        ("brown", ["棕色", "咖色", "ブラウン", "brown"]),
        ("green", ["绿色", "绿", "グリーン", "green"]),
        ("pink", ["粉色", "粉", "ピンク", "pink"]),
        ("red", ["红色", "红", "レッド", "red"]),
        ("khaki", ["卡其", "カーキ", "khaki"]),
        ("ivory", ["象牙", "アイボリー", "ivory"]),
    ]
    for color, keywords in color_map:
        if any(keyword in text for keyword in keywords):
            return color
    return ""


def infer_garment_en(product_type: str, product_text: str) -> str:
    text = product_text.lower()
    if product_type == "pants":
        if any(keyword in text for keyword in ["牛仔", "denim", "jeans"]):
            return "wide-leg denim pants" if any(keyword in text for keyword in ["阔腿", "wide-leg"]) else "denim pants"
        if any(keyword in text for keyword in ["阔腿", "wide-leg"]):
            return "wide-leg pants"
        if any(keyword in text for keyword in ["西裤", "slacks"]):
            return "tailored slacks"
        return "pants"
    if product_type == "skirt":
        if any(keyword in text for keyword in ["百褶", "pleated"]):
            return "pleated midi skirt"
        if any(keyword in text for keyword in ["半身裙", "skirt"]):
            return "midi skirt"
        return "skirt"
    if product_type == "dress":
        if any(keyword in text for keyword in ["衬衫裙", "shirt dress"]):
            return "shirt dress"
        if any(keyword in text for keyword in ["无袖", "sleeveless"]):
            return "sleeveless dress"
        return "one-piece dress"
    if any(keyword in text for keyword in ["开衫", "cardigan"]):
        return "cardigan"
    if any(keyword in text for keyword in ["外套", "jacket", "coat"]):
        return "light outerwear"
    if any(keyword in text for keyword in ["衬衫", "blouse", "shirt"]):
        return "blouse"
    if any(keyword in text for keyword in ["针织", "knit"]):
        return "knit top"
    return "womenswear item"


def local_proof_points_en(product_type: str, product_text: str) -> str:
    text = product_text.lower()
    points: list[str] = []
    if any(keyword in text for keyword in ["腰腹", "下腹", "肚", "お腹", "belly", "waist"]):
        points.append("comfortable waist and lower-belly area")
    if any(keyword in text for keyword in ["臀", "腿", "太もも", "hip", "thigh"]):
        points.append("non-clinging hip and thigh silhouette")
    if any(keyword in text for keyword in ["通勤", "office", "commute"]):
        points.append("office styling")
    if any(keyword in text for keyword in ["周末", "休日", "weekend", "休闲"]):
        points.append("weekend casual styling")
    if any(keyword in text for keyword in ["垂", "drape"]):
        points.append("soft drape while walking")
    if any(keyword in text for keyword in ["口袋", "pocket"]):
        points.append("clear pocket placement")
    if any(keyword in text for keyword in ["腰绳", "抽绳", "drawstring"]):
        points.append("clear drawstring waist detail")
    if any(keyword in text for keyword in ["斜扣", "asymmetric"]):
        points.append("clear asymmetric button waist detail")

    defaults = {
        "pants": ["waist close-up", "front and side walking", "sitting and standing comfort test"],
        "skirt": ["waist and hip fit", "hem movement", "sitting or stair movement"],
        "dress": ["upper-body detail", "full-body drape", "arm and side coverage"],
        "fallback": ["detail close-up", "arm movement", "front, side, and back fit check"],
    }
    points.extend(item for item in defaults.get(product_type, defaults["fallback"]) if item not in points)
    return ", ".join(points[:7])


def local_structure_en(product_type: str) -> dict[str, str]:
    structures = {
        "pants": {
            "opening": "show the pants already worn in a clear full-body or waist-to-ankle view, with a respectful focus on the waist and lower-body fit.",
            "detail": "cut to a close-up of the waistband, front closure, pockets, and fabric drape; hands gently smooth the waist without hiding the design.",
            "proof": "show front walking, side walking, back view, then sitting down and standing up to demonstrate natural movement and comfort.",
            "scene": "switch between a simple office outfit and a relaxed weekend outfit while keeping the same pants clearly visible.",
        },
        "skirt": {
            "opening": "show the skirt already worn from waist to full body, clearly showing waist fit and length.",
            "detail": "cut to the waistband, pleats or hem, and fabric layers; hands lightly brush the skirt fabric.",
            "proof": "show front, side, and back walking, a gentle turn, and sitting or stair movement to show drape and daily comfort.",
            "scene": "switch between clean office styling and casual weekend styling with shoes and bag changes.",
        },
        "dress": {
            "opening": "show the dress already worn in an upper-body close-up, then a quick full-body result.",
            "detail": "cut to collar, pockets, waist detail, sleeve or armhole, and hem drape.",
            "proof": "show side walking, waist adjustment if present, arm raise, side angle, and full-body turn.",
            "scene": "show office and weekend styling with small accessory changes.",
        },
        "fallback": {
            "opening": "show the item already worn in a clear upper-body or full-body result.",
            "detail": "cut to neckline, sleeves, buttons, texture, hem, pockets, or closure depending on the actual design.",
            "proof": "show arm movement, shoulder turn, side view, and back view to prove natural daily fit.",
            "scene": "style the item with pants, skirt, or an inner layer in practical daily outfits.",
        },
    }
    return structures.get(product_type, structures["fallback"])


def parse_json_object(text: str) -> dict[str, Any]:
    raw = text.strip()
    candidates = [raw]
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fence_match:
        candidates.insert(0, fence_match.group(1))
    brace_start = raw.find("{")
    brace_end = raw.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        candidates.append(raw[brace_start : brace_end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def parse_fashion_analysis_images(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_images = payload.get("images")
    if not isinstance(raw_images, list) or not raw_images:
        raise ValueError("请至少上传一张商品参考图。")
    if len(raw_images) > MAX_FASHION_ANALYSIS_IMAGES:
        raise ValueError(f"AI 商品识别最多支持 {MAX_FASHION_ANALYSIS_IMAGES} 张图片。")

    images: list[dict[str, str]] = []
    total_bytes = 0
    pattern = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$")
    for index, item in enumerate(raw_images):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index + 1} 张图片格式无效。")
        data_url = str(item.get("dataUrl") or "").strip()
        match = pattern.fullmatch(data_url)
        if not match or match.group(1) not in FASHION_ANALYSIS_IMAGE_TYPES:
            raise ValueError(f"第 {index + 1} 张图片必须是 JPG、PNG 或 WebP。")
        try:
            decoded = base64.b64decode(match.group(2), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"第 {index + 1} 张图片数据无效。") from exc
        if not decoded or len(decoded) > MAX_FASHION_ANALYSIS_IMAGE_BYTES:
            raise ValueError(f"第 {index + 1} 张图片不能超过 8MB。")
        total_bytes += len(decoded)
        if total_bytes > MAX_FASHION_ANALYSIS_TOTAL_BYTES:
            raise ValueError("AI 商品识别图片总大小不能超过 24MB。")
        role = str(item.get("role") or "extra").strip()
        images.append(
            {
                "name": compact_product_note(str(item.get("name") or f"image-{index + 1}"), 160),
                "role": role if role in FASHION_REFERENCE_ROLES else "extra",
                "dataUrl": data_url,
            }
        )
    return images


def normalize_fashion_analysis_category(value: Any) -> str:
    text = str(value or "").strip()
    if text in FASHION_GENERAL_CATEGORIES:
        return text
    lowered = text.lower()
    category_routes = [
        ("美妆个护", ["美妆", "个护", "口红", "唇釉", "粉底", "眼影", "面霜", "精华", "乳液", "洗护", "香水", "cosmetic", "beauty", "lipstick", "skincare"]),
        ("食品饮料", ["食品", "饮料", "零食", "咖啡", "茶", "果汁", "燕麦", "饼干", "面包", "糖果", "food", "drink", "snack", "beverage"]),
        ("宠物用品", ["宠物", "猫砂", "牵引", "宠物饮水", "pet", "cat", "dog"]),
        ("汽车用品", ["汽车", "车载", "车内", "行车", "方向盘", "座椅", "支架", "automotive", "car accessory"]),
        ("运动户外", ["运动", "户外", "健身", "瑜伽", "露营", "登山", "球拍", "哑铃", "sports", "outdoor", "fitness", "camping"]),
        ("母婴玩具", ["母婴", "玩具", "积木", "童车", "玩偶", "拼图", "toy", "baby", "kids"]),
        ("鞋包配饰", ["鞋", "包", "手袋", "背包", "首饰", "项链", "耳环", "手表", "腰带", "shoe", "bag", "jewelry", "accessor"]),
        ("家用电器", ["家电", "风扇", "吹风", "吸尘", "加湿", "空气炸", "咖啡机", "电饭", "洗衣", "冰箱", "appliance", "vacuum", "dryer"]),
        ("数码电子", ["数码", "电子", "耳机", "手机", "键盘", "鼠标", "相机", "音箱", "充电", "显示器", "蓝牙", "digital", "electronic", "earbud", "headphone", "keyboard", "mouse", "camera", "bluetooth"]),
        ("厨房用品", ["厨房", "锅", "刀", "杯", "餐具", "砧板", "烘焙", "榨汁", "kitchen", "cookware", "utensil"]),
        ("家居日用", ["家居", "日用", "收纳", "置物", "清洁", "床品", "灯具", "家具", "home", "storage", "organizer", "furniture"]),
    ]
    for category, keywords in category_routes:
        if any(keyword in lowered for keyword in keywords):
            return category
    if any(keyword in lowered for keyword in ["背带", "overalls", "overall", "jumpsuit", "salopette", "连体裤"]):
        return "背带裤连体裤"
    if any(keyword in lowered for keyword in ["连衣裙", "dress", "ワンピース"]):
        return "连衣裙"
    if any(keyword in lowered for keyword in ["半身裙", "skirt", "スカート"]):
        return "半身裙"
    if any(keyword in lowered for keyword in ["裤", "pants", "trousers", "jeans", "パンツ"]):
        return "长裤"
    if any(keyword in lowered for keyword in ["外套", "jacket", "coat", "アウター"]):
        return "外套"
    if any(keyword in lowered for keyword in ["上衣", "shirt", "blouse", "top", "シャツ"]):
        return "上衣"
    return "其他商品"


def infer_fashion_product_profile(product: dict[str, Any]) -> dict[str, Any]:
    """Resolve one safe product route from the current product facts only."""
    evidence = " ".join(
        str(product.get(key) or "")
        for key in ("name", "category", "silhouette", "frontStructure", "backStructure", "material", "anchors")
    ).lower()
    category = normalize_fashion_analysis_category(product.get("category") or evidence)
    if category in FASHION_APPAREL_CATEGORIES:
        profile_id = "apparel"
    else:
        profile_id = {
            "美妆个护": "beauty", "食品饮料": "food", "家居日用": "home", "厨房用品": "kitchen",
            "数码电子": "electronics", "家用电器": "appliance", "鞋包配饰": "accessory", "母婴玩具": "toy",
            "宠物用品": "pet", "运动户外": "sports", "汽车用品": "automotive", "其他商品": "universal_product",
        }.get(category, "universal_product")
    return copy.deepcopy(FASHION_PRODUCT_PROFILES[profile_id])


def fashion_role_briefs_for_profile(profile: dict[str, Any]) -> dict[str, tuple[str, str]]:
    name = str(profile.get("name") or "商品")
    return {
        "overview": (f"{name} · 外观与完整形态", f"只证明{profile['overviewProof']}"),
        "detail": (f"{name} · 关键结构与材质", f"只证明当前最易漂移结构以及{profile['detailProof']}"),
        "walking": (f"{name} · 真实操作演示", f"只用一个开场动作证明{profile['motionProof']}"),
        "routine": (f"{name} · 日常使用流程", f"只完成一个真实使用顺序，证明{profile['motionProof']}"),
        "activity": (f"{name} · 功能状态证明", f"只证明{profile['activityProof']}，不扩写性能或功效"),
        "lifestyle": (f"{name} · 真实场景适配", f"只证明{profile['overviewProof']}与一个真实使用场景的关系"),
        "ending": (f"{name} · 干净商品收尾", "只生成一个已完成动作、可供剪辑衔接的干净商品终点"),
    }


def normalize_fashion_analysis_text(value: Any, limit: int, unknown: bool = False) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text and unknown:
        return "未确认"
    return text[:limit].rstrip()


def normalize_fashion_analysis_list(value: Any, limit: int, item_limit: int = 160) -> list[str]:
    items = value if isinstance(value, list) else re.split(r"[\n,，、；;]+", str(value or ""))
    normalized: list[str] = []
    for item in items:
        text = normalize_fashion_analysis_text(item, item_limit)
        if text and text not in normalized:
            normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def safe_ai_usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    return {
        key: int(usage[key])
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        if isinstance(usage.get(key), int) and usage[key] >= 0
    }


def normalize_fashion_category_details(value: Any) -> dict[str, str]:
    """Keep a small, safe set of category-specific observable facts."""
    if not isinstance(value, dict):
        return {}
    details: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = clean_copy_library_text(raw_key, 48)
        detail = clean_copy_library_text(raw_value, 320)
        if not key or not detail or key in details:
            continue
        details[key] = detail
        if len(details) >= 8:
            break
    return details


def normalize_fashion_platform_strategy(value: Any) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    limits = {"label": 80, "pace": 220, "focus": 260, "safeArea": 220}
    return {
        key: text
        for key, limit in limits.items()
        if (text := clean_copy_library_text(source.get(key), limit))
    }


def normalize_fashion_reference_consistency(value: Any, image_count: int) -> dict[str, Any]:
    """Normalize the vision model's multi-reference identity check."""
    count = max(0, min(int(image_count or 0), MAX_FASHION_ANALYSIS_IMAGES))
    source = value if isinstance(value, dict) else {}
    if count == 0:
        return {
            "status": "not_provided",
            "score": 0,
            "sameProduct": None,
            "summary": "未上传参考图，无法执行一致性检查。",
            "conflicts": [],
            "canonicalSources": [],
        }
    if count == 1:
        return {
            "status": "single",
            "score": 100,
            "sameProduct": True,
            "summary": normalize_fashion_analysis_text(source.get("summary"), 260)
            or "单张参考图无需执行跨图一致性检查。",
            "conflicts": [],
            "canonicalSources": [],
        }

    raw_status = clean_copy_library_text(source.get("status"), 24).lower()
    status = raw_status if raw_status in {"consistent", "warning", "conflict"} else "warning"
    raw_same_product = source.get("sameProduct")
    same_product = raw_same_product if isinstance(raw_same_product, bool) else status != "conflict"
    if same_product is False:
        status = "conflict"

    default_scores = {"consistent": 94, "warning": 68, "conflict": 28}
    try:
        score = int(round(float(source.get("score", default_scores[status]))))
    except (TypeError, ValueError):
        score = default_scores[status]
    score = max(0, min(100, score))
    if status == "conflict":
        score = min(score, 49)

    conflicts: list[dict[str, Any]] = []
    raw_conflicts = source.get("conflicts")
    if isinstance(raw_conflicts, list):
        for item in raw_conflicts[:8]:
            if not isinstance(item, dict):
                continue
            dimension = normalize_fashion_analysis_text(item.get("dimension"), 80)
            detail = normalize_fashion_analysis_text(item.get("detail"), 260)
            raw_indices = item.get("images") if isinstance(item.get("images"), list) else []
            indices: list[int] = []
            for raw_index in raw_indices:
                try:
                    index = int(raw_index)
                except (TypeError, ValueError):
                    continue
                if 0 <= index < count and index not in indices:
                    indices.append(index)
            severity = clean_copy_library_text(item.get("severity"), 24).lower()
            if severity not in {"warning", "critical"}:
                severity = "critical" if status == "conflict" else "warning"
            if dimension or detail:
                conflicts.append(
                    {"dimension": dimension or "未命名维度", "images": indices, "detail": detail, "severity": severity}
                )

    canonical_sources: list[dict[str, Any]] = []
    seen_dimensions: set[str] = set()
    raw_sources = source.get("canonicalSources")
    if isinstance(raw_sources, list):
        for item in raw_sources[:8]:
            if not isinstance(item, dict):
                continue
            dimension = normalize_fashion_analysis_text(item.get("dimension"), 80)
            try:
                index = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            if not dimension or dimension in seen_dimensions or not 0 <= index < count:
                continue
            seen_dimensions.add(dimension)
            canonical_sources.append(
                {
                    "dimension": dimension,
                    "index": index,
                    "reason": normalize_fashion_analysis_text(item.get("reason"), 220),
                }
            )

    summary = normalize_fashion_analysis_text(source.get("summary"), 320)
    if not summary:
        summary = {
            "consistent": "多张参考图中的商品颜色、轮廓和主要结构一致。",
            "warning": "参考图存在无法确认的差异，请按权威来源逐项核对。",
            "conflict": "参考图可能不是同一商品，已阻止混合不同结构生成。",
        }[status]
    return {
        "status": status,
        "score": score,
        "sameProduct": same_product,
        "summary": summary,
        "conflicts": conflicts,
        "canonicalSources": canonical_sources,
    }


def normalize_fashion_analysis_result(value: dict[str, Any], image_count: int) -> dict[str, Any]:
    raw_roles = value.get("referenceRoles")
    reference_roles: list[dict[str, Any]] = []
    used_indices: set[int] = set()
    if isinstance(raw_roles, list):
        for item in raw_roles:
            if not isinstance(item, dict):
                continue
            try:
                index = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            role = str(item.get("role") or "").strip()
            if index < 0 or index >= image_count or index in used_indices or role not in FASHION_REFERENCE_ROLES:
                continue
            used_indices.add(index)
            reference_roles.append(
                {
                    "index": index,
                    "role": role,
                    "reason": normalize_fashion_analysis_text(item.get("reason"), 180),
                }
            )

    return {
        "suggestedName": normalize_fashion_analysis_text(value.get("suggestedName"), 80),
        "category": normalize_fashion_analysis_category(value.get("category")),
        "color": normalize_fashion_analysis_text(value.get("color"), 100, unknown=True),
        "silhouette": normalize_fashion_analysis_text(value.get("silhouette"), 220, unknown=True),
        "frontStructure": normalize_fashion_analysis_text(value.get("frontStructure"), 460, unknown=True),
        "backStructure": normalize_fashion_analysis_text(value.get("backStructure"), 360, unknown=True),
        "material": normalize_fashion_analysis_text(value.get("material"), 220, unknown=True),
        "categoryDetails": normalize_fashion_category_details(value.get("categoryDetails")),
        "stylingBoundary": normalize_fashion_analysis_text(value.get("stylingBoundary"), 260, unknown=True),
        "fragileAnchors": normalize_fashion_analysis_list(value.get("fragileAnchors"), 6, 120),
        "referenceRoles": reference_roles,
        "uncertainFacts": normalize_fashion_analysis_list(value.get("uncertainFacts"), 8, 180),
        "warnings": normalize_fashion_analysis_list(value.get("warnings"), 6, 180),
        "referenceConsistency": normalize_fashion_reference_consistency(value.get("referenceConsistency"), image_count),
    }


def analyze_fashion_product(payload: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    images = parse_fashion_analysis_images(payload)
    active_config = read_runtime_config() if config is None else config
    product_name = normalize_fashion_analysis_text(payload.get("productName"), 80)
    category_hint = normalize_fashion_analysis_text(payload.get("category"), 80)
    category_details_hint = normalize_fashion_category_details(payload.get("categoryDetails"))
    role_hints = [
        {"index": index, "fileName": image["name"], "userRoleHint": image["role"]}
        for index, image in enumerate(images)
    ]
    system_prompt = (
        "You are a conservative ecommerce product analyst for any product category. Analyze only observable facts in the supplied images. "
        "First identify the product family, then separate the product from people, hands, pets, styling items, props, rooms, vehicles, food styling, logos and watermarks. "
        "Never infer material composition, ingredients, taste, medical or beauty effects, comfort, performance, durability, compatibility, safety certification or other benefits. "
        "If a back, bottom, interface, internal structure or detail is missing, write 未确认 instead of inventing it. "
        "For multiple images, first decide whether they show the same exact sellable product. Compare color, silhouette, interfaces, readable-mark placement, component count, component position and included accessories. "
        "Do not average or merge conflicting products. Mark obvious cross-product conflicts as conflict; use warning when evidence is merely incomplete. Choose one clearer authority image per disputed dimension and give every image only one primary reference role. "
        "Return exactly one JSON object and no markdown. Use concise Simplified Chinese values."
    )
    schema = {
        "suggestedName": "基于可见品类与结构的简短商品名；用户已有明确名称时可原样保留",
        "category": "只能是：美妆个护、食品饮料、家居日用、厨房用品、数码电子、家用电器、鞋包配饰、母婴玩具、宠物用品、运动户外、汽车用品、其他商品、背带裤连体裤、长裤、半身裙、连衣裙、上衣、外套、其他女装",
        "color": "可见主色、辅色与五金色；多色商品只记录当前图片可见状态",
        "silhouette": "整体外形、规格感、长度、轮廓与主要部件关系",
        "frontStructure": "主视图可见结构、开合、接口、按键、封口、五金、标签位置与数量",
        "backStructure": "背面、底部、接口或隐藏侧可见结构；没有权威图片则写未确认",
        "material": "只写可见哑光/光泽、纹理、透明度、流动、酥脆、挺括或垂落状态，不推断成分",
        "categoryDetails": {
            "fieldKey": "按品类补充可见事实；美妆写质地/泵头/色号，食品写包装/内容物/开封，数码写接口/按键/指示灯，其他品类写同等重要结构"
        },
        "stylingBoundary": "明确哪些人物、手、宠物、食材、内搭、道具、配件或环境不属于商品本体",
        "fragileAnchors": ["3到6个最容易漂移成另一件商品的可观察结构"],
        "referenceRoles": [{"index": 0, "role": "front_full|front_detail|back|side|fabric|extra", "reason": "角色依据"}],
        "uncertainFacts": ["图片不足、遮挡或冲突导致的待确认事实"],
        "warnings": ["可能造成串品或参考冲突的简短提醒"],
        "referenceConsistency": {
            "status": "consistent|warning|conflict",
            "score": "0到100的整数",
            "sameProduct": "是否确认全部图片为同一个具体商品",
            "summary": "颜色、轮廓、接口、文字位置、部件数量位置和配件的一句话结论",
            "conflicts": [{"dimension": "冲突维度", "images": [0, 1], "detail": "差异", "severity": "warning|critical"}],
            "canonicalSources": [{"dimension": "单一事实维度", "index": 0, "reason": "为什么该图是权威来源"}],
        },
    }
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"用户提供的商品名称：{product_name or '未填写'}\n"
                f"用户选择的品类：{category_hint or '未填写'}\n"
                f"用户已填写的品类专用事实：{json.dumps(category_details_hint, ensure_ascii=False)}\n"
                f"图片与当前人工角色提示：{json.dumps(role_hints, ensure_ascii=False)}\n"
                "名称、品类、专用事实和人工角色都是待核对提示；若视觉证据明显不符请在warnings指出，不得覆盖成不可见事实。每张图只建议一个主要角色。\n"
                f"严格按这个 JSON 结构返回：{json.dumps(schema, ensure_ascii=False)}"
            ),
        }
    ]
    for index, image in enumerate(images):
        content.append({"type": "text", "text": f"参考图 {index}：{image['name']}"})
        content.append({"type": "image_url", "image_url": {"url": image["dataUrl"]}})

    response = call_ai_chat(
        {
            "model": get_ai_model(active_config),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": min(get_ai_temperature(active_config), 0.2),
            "max_tokens": min(max(get_ai_max_tokens(active_config), 1600), 4000),
        },
        timeout_seconds=parse_int_env("FASHION_ANALYSIS_TIMEOUT_SECONDS", 180),
        config=active_config,
    )
    raw = extract_ai_text(response)
    parsed = parse_json_object(raw)
    if not parsed:
        raise AiError(HTTPStatus.BAD_GATEWAY, "视觉模型没有返回有效的商品档案 JSON。请确认该模型支持图片输入。")
    analysis = normalize_fashion_analysis_result(parsed, len(images))
    return {
        "analysis": analysis,
        "referenceConsistency": analysis["referenceConsistency"],
        "model": get_ai_model(active_config),
        "usage": safe_ai_usage(response),
        "insecureEndpoint": get_ai_base_url(active_config).startswith("http://"),
    }


def parse_fashion_generation_images(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_images = payload.get("images")
    if raw_images in (None, []):
        return []
    return parse_fashion_analysis_images({"images": raw_images})


def normalize_fashion_product_payload(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    try:
        duration = int(raw.get("duration") or 15)
        count = int(raw.get("count") or 3)
    except (TypeError, ValueError) as exc:
        raise ValueError("输出时长或提示词数量无效。") from exc
    if duration not in {5, 10, 15}:
        raise ValueError("输出时长只能是 5、10 或 15 秒。")
    if count not in FASHION_GENERATION_ROLE_KEYS:
        raise ValueError("提示词数量只能是 3、5 或 7 条。")
    platform_preset = clean_copy_library_text(raw.get("platformPreset"), 24).lower() or "custom"
    if platform_preset not in FASHION_PLATFORM_PRESETS:
        platform_preset = "custom"
    product = {
        "name": clean_copy_library_text(raw.get("name"), 100),
        "category": clean_copy_library_text(raw.get("category"), 80),
        "color": clean_copy_library_text(raw.get("color"), 220),
        "silhouette": clean_copy_library_text(raw.get("silhouette"), 500),
        "frontStructure": clean_copy_library_text(raw.get("frontStructure"), 900),
        "backStructure": clean_copy_library_text(raw.get("backStructure"), 700),
        "material": clean_copy_library_text(raw.get("material"), 500),
        "categoryDetails": normalize_fashion_category_details(raw.get("categoryDetails")),
        "stylingBoundary": clean_copy_library_text(raw.get("stylingBoundary"), 500),
        "anchors": clean_copy_library_text(raw.get("anchors"), 700),
        "promptMode": clean_copy_library_text(raw.get("promptMode"), 24) or "fidelity",
        "duration": duration,
        "count": count,
        "ratio": clean_copy_library_text(raw.get("ratio"), 24) or "9:16",
        "market": clean_copy_library_text(raw.get("market"), 100) or "日本日常电商",
        "scenes": normalize_fashion_analysis_list(raw.get("scenes"), 6, 100),
        "platformPreset": platform_preset,
        "platformStrategy": normalize_fashion_platform_strategy(raw.get("platformStrategy")),
    }
    if product["promptMode"] not in FASHION_PROMPT_MODES:
        raise ValueError("提示词模式只能是高还原或精简稳定。")
    if not product["name"]:
        color = re.split(r"[，,；;。]", product["color"])[0].strip()[:24]
        category = product["category"] if product["category"] not in {"", "其他商品"} else "商品新品"
        product["name"] = f"{color}{category}" or "当前商品新品"
    if not any(product[key] for key in ("category", "color", "silhouette", "frontStructure", "material")):
        raise ValueError("商品档案信息太少，请至少填写品类、颜色、外形、主要结构或材质中的一项。")
    if not product["scenes"]:
        product["scenes"] = ["纯净自然光桌面"]
    return product


def normalize_fashion_generation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    product = normalize_fashion_product_payload(payload.get("product"))
    common_lock = clean_task_multiline(payload.get("commonLock"), 7000)
    if len(common_lock) < 30:
        raise ValueError("公共商品锁不完整，请检查商品档案后重试。")

    reference_map: list[dict[str, str]] = []
    seen_placeholders: set[str] = set()
    raw_reference_map = payload.get("referenceMap")
    if isinstance(raw_reference_map, list):
        for item in raw_reference_map[:MAX_FASHION_ANALYSIS_IMAGES]:
            if not isinstance(item, dict):
                continue
            placeholder = clean_copy_library_text(item.get("placeholder"), 100)
            if not placeholder.startswith("@") or placeholder in seen_placeholders:
                continue
            seen_placeholders.add(placeholder)
            reference_map.append(
                {
                    "placeholder": placeholder,
                    "role": clean_copy_library_text(item.get("role"), 80),
                    "roleKey": clean_copy_library_text(item.get("roleKey"), 40),
                    "authority": clean_copy_library_text(item.get("authority"), 260),
                    "fileName": clean_copy_library_text(item.get("fileName"), 160),
                }
            )

    raw_images = payload.get("images")
    image_count = len(raw_images) if isinstance(raw_images, list) else len(reference_map)
    reference_consistency = normalize_fashion_reference_consistency(
        payload.get("referenceConsistency"), image_count
    )

    raw_compiler = payload.get("compiler")
    compiler_source = raw_compiler if isinstance(raw_compiler, dict) else {}
    compiler = {
        "name": clean_copy_library_text(compiler_source.get("name"), 120) or "Seedance 2.0 Skill OS",
        "version": clean_copy_library_text(compiler_source.get("version"), 32) or "6.7.0",
        "fashionSkill": clean_copy_library_text(compiler_source.get("fashionSkill"), 120) or "Universal Product Prompt Router",
        "profile": clean_copy_library_text(compiler_source.get("profile"), 120) or "中文通用商品短视频提示词",
        "order": normalize_fashion_analysis_list(compiler_source.get("order"), 8, 80),
    }
    product_profile = infer_fashion_product_profile(product)
    role_briefs = fashion_role_briefs_for_profile(product_profile)
    role_keys = FASHION_GENERATION_ROLE_KEYS[product["count"]]
    roles = [
        {
            "index": index,
            "key": key,
            "title": role_briefs[key][0],
            "proofGoal": role_briefs[key][1],
        }
        for index, key in enumerate(role_keys)
    ]
    diversity_rules = {
        "uniqueHookPerPrompt": True,
        "uniquePrimaryActionPerPrompt": True,
        "uniqueFirstCameraPerPrompt": True,
        "requiredDifferentFields": ["mainTask", "firstAction", "firstCamera"],
        "instruction": "同一批提示词必须使用不同主任务、不同第一动作和不同首个机位；只换标题、形容词或场景不算不同。",
        "roleOrder": role_keys,
    }
    return {
        "product": product,
        "productProfile": product_profile,
        "commonLock": common_lock,
        "compiler": compiler,
        "referenceMap": reference_map,
        "referenceConsistency": reference_consistency,
        "roles": roles,
        "diversityRules": diversity_rules,
    }


def replace_fashion_prompt_section(prompt: str, label: str, body: str) -> str:
    preamble, ordered, sections = parse_fashion_prompt_sections(prompt)
    if label not in sections:
        return prompt
    rebuilt = [preamble] if preamble else []
    for current_label, current_body in ordered:
        rebuilt.append(f"【{current_label}】{body if current_label == label else current_body}")
    return "\n".join(rebuilt).strip()


def fashion_generation_shot_ids(prompt: str) -> list[int]:
    ids: list[int] = []
    for value in re.findall(r"镜头\s*(\d+)\s*(?:[：:]|】)", prompt):
        shot_id = int(value)
        if shot_id not in ids:
            ids.append(shot_id)
    return ids


def normalize_fashion_inspection_timeline(prompt: str, duration: int) -> str:
    if duration < 15:
        return prompt
    exact_ranges = [
        "00:00—00:02", "00:02—00:03.5", "00:03.5—00:05", "00:05—00:07",
        "00:07—00:08.5", "00:08.5—00:10", "00:10—00:12.5", "00:12.5—00:15",
    ]
    _, _, sections = parse_fashion_prompt_sections(prompt)
    timeline = sections.get("时间轴", "")
    if not timeline:
        return prompt
    normalized = timeline
    for index, time_range in enumerate(exact_ranges, start=1):
        pattern = re.compile(
            rf"镜头\s*{index}\s*(?:[：:]\s*)?"
            r"(?:\[[^\]\r\n]{0,40}\]|[0-9:.]+\s*[-—–至~]\s*[0-9:.]+)?\s*[｜|]?"
        )
        normalized, count = pattern.subn(f"镜头{index}：[{time_range}]｜", normalized, count=1)
        if not count:
            return prompt
    return replace_fashion_prompt_section(prompt, "时间轴", normalized)


def fashion_direct_shot_count(product: dict[str, Any]) -> int:
    duration = int(product.get("duration") or 15)
    if duration >= 15:
        return 8 if product.get("promptMode") == "fidelity" else 3
    return 2 if duration >= 10 else 1


def upsert_fashion_prompt_section(prompt: str, label: str, body: str, after_label: str = "") -> str:
    preamble, ordered, sections = parse_fashion_prompt_sections(prompt)
    if label in sections:
        return replace_fashion_prompt_section(prompt, label, body)
    if not ordered:
        return f"{preamble}\n【{label}】{body}".strip()
    rebuilt = [preamble] if preamble else []
    inserted = False
    for current_label, current_body in ordered:
        rebuilt.append(f"【{current_label}】{current_body}")
        if current_label == after_label:
            rebuilt.append(f"【{label}】{body}")
            inserted = True
    if not inserted:
        rebuilt.append(f"【{label}】{body}")
    return "\n".join(rebuilt).strip()


def enforce_fashion_fidelity_layers(prompt: str, context: dict[str, Any]) -> str:
    product = context["product"]
    profile = context.get("productProfile") or infer_fashion_product_profile(product)
    styling = product.get("stylingBoundary") or "人物、手、宠物、道具与环境属于展示层，不属于商品本体"
    material = product.get("material") or "商品材质与状态只按参考图和当前档案可见事实生成"
    anchors = product.get("anchors") or "当前档案已确认的颜色、轮廓和结构"
    if profile.get("id") != "apparel":
        subject = (
            f"全片复用{profile['subject']}；{styling}。商品、实际配件、内容物与操作手的数量和位置前后连续，"
            "人物、手、宠物、道具和环境始终从属于商品，不遮挡当前关键结构。"
        )
        performance = (
            f"{profile['operator']}。只完成镜头规定的一个可见动作，按真实先后顺序开始、变化、完成并停住；"
            "不摆拍、不反复触发、不增加第二项功能或戏剧表演。"
        )
        physics = (
            f"商品全程保持干净、结构连续；可见材质、内容物或工作状态只服从“{material}”。"
            f"{profile['continuityRule']}。跨镜头持续锁定：{anchors}；不闪烁、不穿模、不凭空增减部件、不生成未确认功能。"
        )
        prompt = upsert_fashion_prompt_section(prompt, "主体与操作连续性", subject, "整体设定")
        prompt = upsert_fashion_prompt_section(prompt, "自然操作", performance, "主体与操作连续性")
        return upsert_fashion_prompt_section(prompt, "商品状态与物理", physics, "连续性与物理")

    person = (
        "全片复用同一位原创成年东亚女性、同一张脸、同一年龄感、发型、淡妆、健康自然体态和同一套穿搭；"
        f"{styling}。人物、内搭、鞋包和道具始终从属于商品展示，不遮挡领口、门襟、腰线、口袋、袖口或下摆等当前关键结构。"
    )
    performance = (
        "人物像在真实生活中完成镜头规定的小事，不走秀、不听口令逐项摆拍；视线优先跟随手中任务、前方道路或环境目标，只在合适时短暂扫过镜头。"
        "动作之间保留自然呼吸、眨眼、手指小动作、轻微重心变化和完成后的短暂停顿；每镜头只完成一个主动作，动作结束后再切镜。"
    )
    physics = (
        f"商品全程保持干净、结构连续；可见面料表现只服从“{material}”。褶皱、摆动与回落只由身体动作、重力和场景中已经写明的轻微气流产生；"
        f"动作停止后恢复当前材质应有的自然状态。跨镜头持续锁定：{anchors}；不闪烁、不换材质、不穿模、不产生未确认的永久结构。"
    )
    prompt = upsert_fashion_prompt_section(prompt, "人物与穿搭连续性", person, "整体设定")
    prompt = upsert_fashion_prompt_section(prompt, "自然表演", performance, "人物与穿搭连续性")
    return upsert_fashion_prompt_section(prompt, "服装状态与物理", physics, "连续性与物理")


def enforce_fashion_direct_product_lock(
    prompt: str,
    common_lock: str,
    preferred_label: str = "核心商品锁",
) -> str:
    preamble, ordered, sections = parse_fashion_prompt_sections(prompt)
    if not ordered:
        return f"【{preferred_label}】{common_lock}\n{prompt}".strip()
    rebuilt = [preamble] if preamble else []
    inserted = False
    insert_after = "主体与动作" if "主体与动作" in sections else "参考"
    for label, body in ordered:
        if label in {"商品锁定", "核心商品锁"}:
            if not inserted:
                rebuilt.append(f"【{preferred_label}】{common_lock}")
                inserted = True
            continue
        rebuilt.append(f"【{label}】{body}")
        if label == insert_after and not inserted:
            rebuilt.append(f"【{preferred_label}】{common_lock}")
            inserted = True
    if not inserted:
        rebuilt.insert(1 if preamble else 0, f"【{preferred_label}】{common_lock}")
    return "\n".join(rebuilt).strip()


def normalize_fashion_reference_sigils(text: str, allowed_placeholders: set[str]) -> str:
    protected = text
    sentinels: dict[str, str] = {}
    for index, placeholder in enumerate(sorted(allowed_placeholders, key=len, reverse=True)):
        sentinel = f"__FASHION_REFERENCE_{index}__"
        if placeholder in protected:
            protected = protected.replace(placeholder, sentinel)
            sentinels[sentinel] = placeholder
    protected = protected.replace("@", "")
    for sentinel, placeholder in sentinels.items():
        protected = protected.replace(sentinel, placeholder)
    return protected


FASHION_PROMPT_NEGATIVE_MARKERS = re.compile(
    r"(?:禁止|不得|不可|不应|不要|避免|杜绝|排除|无须|无需|不写|不使用|"
    r"不加入|不添加|不生成|不出现|不做|不承诺|不宣称|不推断|不包含)"
)


def fashion_prompt_term_is_negated(prompt: str, start: int) -> bool:
    prefix = prompt[max(0, start - 80) : start]
    clause = re.split(r"[。；;！？!?\r\n]", prefix)[-1]
    return bool(FASHION_PROMPT_NEGATIVE_MARKERS.search(clause))


def fashion_prompt_has_unnegated_term(prompt: str, term: str) -> bool:
    """Return True only when a guarded term is used as a positive prompt claim.

    Generated prompts often repeat forbidden claims inside 【负面约束】 (for
    example, "禁止写显瘦、抗皱或4K").  Treating a mere string occurrence as
    a hallucination rejects otherwise valid model output.  Scan each section
    and ignore both explicitly negative sections and clauses led by a negative
    instruction, while preserving the guard for actual positive claims.  The
    section label alone is not enough: every allowed occurrence still needs an
    explicit negative marker, so a leaked fact appended to 【后期边界】 cannot
    slip through.
    """
    for match in re.finditer(re.escape(term), prompt, flags=re.IGNORECASE):
        if not fashion_prompt_term_is_negated(prompt, match.start()):
            return True
    return False


def sanitize_fashion_generation_claims(prompt: str, product_text: str) -> tuple[str, set[str]]:
    replacements = {
        "显瘦": "轮廓比例清楚",
        "抗皱": "衣面状态以参考图为准",
        "凉感": "材质观感以参考图为准",
        "舒适透气": "穿着状态自然",
        "高级感": "真实日常质感",
        "4K": "画面清晰",
        "8K": "画面清晰",
    }
    repaired: set[str] = set()
    sanitized = prompt
    for term, replacement in replacements.items():
        if term in product_text:
            continue

        def replace(match: re.Match[str]) -> str:
            if fashion_prompt_term_is_negated(sanitized, match.start()):
                return match.group(0)
            repaired.add(term)
            return replacement

        sanitized = re.sub(re.escape(term), replace, sanitized, flags=re.IGNORECASE)
    return sanitized, repaired


def fashion_prompt_diversity_signature(item: dict[str, Any]) -> dict[str, str]:
    """Extract the three visible decisions that make one prompt materially distinct."""
    prompt = str(item.get("inspectionPrompt") or item.get("prompt") or item.get("directPrompt") or "")
    _, _, sections = parse_fashion_prompt_sections(prompt)
    main_task = sections.get("主任务", "")
    first_action_match = re.search(r"(?:^|\n)画面[：:]\s*([^\n]+)", prompt)
    if not first_action_match:
        first_action_match = re.search(r"(?:连续动作|主体与动作)[】：:]\s*([^\n。]+)", prompt)
    first_camera_match = re.search(r"镜头\s*1\s*[：:]\s*\[[^\]]+\]\s*[｜|]\s*([^\n｜|]+)", prompt)
    if not first_camera_match:
        first_camera_match = re.search(r"(?:^|\n)镜头[：:]\s*([^\n；。]+)", prompt)

    def normalize(value: str) -> str:
        value = re.sub(r"[\s\W_]+", "", value or "", flags=re.UNICODE).lower()
        return value[:180]

    return {
        "mainTask": normalize(main_task),
        "firstAction": normalize(first_action_match.group(1) if first_action_match else ""),
        "firstCamera": normalize(first_camera_match.group(1) if first_camera_match else ""),
    }


def validate_fashion_prompt_diversity(prompts: list[dict[str, Any]]) -> None:
    """Reject batches that merely rename the same opening plan."""
    if len(prompts) < 2:
        return
    labels = {"mainTask": "主任务", "firstAction": "第一动作", "firstCamera": "首个机位"}
    signatures = [fashion_prompt_diversity_signature(item) for item in prompts]
    for field, label in labels.items():
        values = [signature[field] for signature in signatures]
        if any(not value for value in values):
            raise AiError(HTTPStatus.BAD_GATEWAY, f"提示词差异不足：无法核对每条的{label}，请重新生成。")
        duplicates = {value for value, count in Counter(values).items() if count > 1}
        if duplicates:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"提示词差异不足：同一批存在重复的{label}，请重新生成。")


def validate_fashion_generation_result(result: dict[str, Any], context: dict[str, Any]) -> None:
    product = context["product"]
    product_text = json.dumps(product, ensure_ascii=False)
    allowed_placeholders = {
        item["placeholder"] for item in context["referenceMap"] if item.get("placeholder")
    }
    legacy_facts = ["中灰色", "三粒同色", "方形贴袋", "埃菲尔铁塔"]
    unsupported_claims = ["显瘦", "抗皱", "凉感", "舒适透气", "高级感"]
    required_sections = [
        "【模式】", "【非叙事任务】", "【主任务】", "【参考】", "【整体设定】", "【商品锁定】",
        "【构图硬性要求】", "【时间轴】", "【连续性与物理】", "【声音】", "【终点】",
        "【负面约束】", "【后期边界】",
    ]
    profile = context.get("productProfile") or infer_fashion_product_profile(product)
    fidelity_sections = (
        ["【人物与穿搭连续性】", "【自然表演】", "【服装状态与物理】"]
        if profile.get("id") == "apparel"
        else ["【主体与操作连续性】", "【自然操作】", "【商品状态与物理】"]
    )
    exact_ranges = [
        "00:00—00:02", "00:02—00:03.5", "00:03.5—00:05", "00:05—00:07",
        "00:07—00:08.5", "00:08.5—00:10", "00:10—00:12.5", "00:12.5—00:15",
    ]
    fidelity = product.get("promptMode") == "fidelity"
    expected_direct_count = fashion_direct_shot_count(product)
    for item in result["prompts"]:
        number = item["index"] + 1
        direct = item["directPrompt"]
        inspection = item["inspectionPrompt"]
        combined = f"{direct}\n{inspection}"
        if product["name"] not in direct or product["name"] not in inspection:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条遗漏了当前商品名称，请重试生成。")
        direct_ids = fashion_prompt_shot_ids(direct) if fidelity else fashion_generation_shot_ids(direct)
        if direct_ids != list(range(1, expected_direct_count + 1)):
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条直贴版镜头数不符合 {product['duration']} 秒规则，请重试生成。")
        if fidelity:
            for section in required_sections:
                if section not in direct:
                    raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条高还原版遗漏了{section}，请重试生成。")
            for section in fidelity_sections:
                if section not in direct:
                    raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条高还原版遗漏了{section}，请重试生成。")
        elif "【核心商品锁】" not in direct and "【商品锁定】" not in direct:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条精简版遗漏了核心商品锁，请重试生成。")
        for section in required_sections:
            if section not in inspection:
                raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条检查完整版遗漏了{section}，请重试生成。")
        inspection_ids = fashion_prompt_shot_ids(inspection)
        if product["duration"] >= 15:
            if inspection_ids != list(range(1, 9)) or any(value not in inspection for value in exact_ranges):
                raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条没有返回完整的 15 秒八镜头时间轴，请重试生成。")
            if fidelity and any(value not in direct for value in exact_ranges):
                raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条高还原版缺少完整的 15 秒八镜头时间码，请重试生成。")
        elif inspection_ids and len(inspection_ids) > expected_direct_count:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条检查版镜头过多，请重试生成。")
        placeholder_scan = combined
        used_placeholders = {placeholder for placeholder in allowed_placeholders if placeholder in combined}
        for placeholder in sorted(allowed_placeholders, key=len, reverse=True):
            placeholder_scan = placeholder_scan.replace(placeholder, "")
        unknown_placeholders = set(re.findall(r"@[A-Za-z0-9_\-\u4e00-\u9fff]+", placeholder_scan))
        if unknown_placeholders:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条改写或虚构了参考标签，请重试生成。")
        if allowed_placeholders and not used_placeholders:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条没有使用已绑定的商品参考图，请重试生成。")
        for fact in legacy_facts:
            if fact not in product_text and (
                fashion_prompt_has_unnegated_term(direct, fact)
                or fashion_prompt_has_unnegated_term(inspection, fact)
            ):
                raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条串入了旧商品事实“{fact}”，请重试生成。")
        for claim in unsupported_claims:
            if claim not in product_text and (
                fashion_prompt_has_unnegated_term(direct, claim)
                or fashion_prompt_has_unnegated_term(inspection, claim)
            ):
                raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条加入了未确认宣称“{claim}”，请重试生成。")
        if any(
            fashion_prompt_has_unnegated_term(prompt, quality)
            for prompt in (direct, inspection)
            for quality in ("4K", "8K")
        ):
            raise AiError(HTTPStatus.BAD_GATEWAY, f"AI 第 {number} 条加入了空泛画质词，请重试生成。")
    validate_fashion_prompt_diversity(result["prompts"])


def normalize_fashion_generation_result(value: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    expected_roles = context["roles"]
    fidelity = context["product"].get("promptMode") == "fidelity"
    allowed_placeholders = {
        item["placeholder"] for item in context["referenceMap"] if item.get("placeholder")
    }
    raw_prompts = value.get("prompts")
    if not isinstance(raw_prompts, list) or len(raw_prompts) != len(expected_roles):
        raise AiError(HTTPStatus.BAD_GATEWAY, "AI 没有返回完整的提示词数量，请重试生成。")
    by_index: dict[int, dict[str, Any]] = {}
    product_text = json.dumps(context["product"], ensure_ascii=False)
    repaired_claims: set[str] = set()
    for raw in raw_prompts:
        if not isinstance(raw, dict):
            continue
        try:
            index = int(raw.get("index"))
        except (TypeError, ValueError):
            continue
        if index < 0 or index >= len(expected_roles) or index in by_index:
            continue
        direct = clean_task_multiline(raw.get("directPrompt"), MAX_FASHION_GENERATION_PROMPT_CHARS)
        inspection = clean_task_multiline(raw.get("inspectionPrompt"), MAX_FASHION_GENERATION_PROMPT_CHARS)
        if len(inspection) < 300 or (not fidelity and len(direct) < 120):
            continue
        expected = expected_roles[index]
        if clean_copy_library_text(raw.get("key"), 60) != expected["key"]:
            continue
        if context["product"]["name"] not in inspection:
            inspection = f"【当前商品】{context['product']['name']}。\n{inspection}"
        inspection = enforce_fashion_direct_product_lock(inspection, context["commonLock"], "商品锁定")
        inspection = normalize_fashion_inspection_timeline(inspection, context["product"]["duration"])
        inspection = normalize_fashion_reference_sigils(inspection, allowed_placeholders)
        if fidelity:
            inspection = enforce_fashion_fidelity_layers(inspection, context)
            inspection, current_repairs = sanitize_fashion_generation_claims(inspection, product_text)
            repaired_claims.update(current_repairs)
            direct = inspection
        else:
            if context["product"]["name"] not in direct:
                direct = f"【当前商品】{context['product']['name']}。\n{direct}"
            direct = enforce_fashion_direct_product_lock(direct, context["commonLock"])
            direct = normalize_fashion_reference_sigils(direct, allowed_placeholders)
            inspection, inspection_repairs = sanitize_fashion_generation_claims(inspection, product_text)
            direct, direct_repairs = sanitize_fashion_generation_claims(direct, product_text)
            repaired_claims.update(inspection_repairs)
            repaired_claims.update(direct_repairs)
        by_index[index] = {
            "index": index,
            "key": expected["key"],
            "title": clean_copy_library_text(raw.get("title"), 100) or expected["title"],
            "risk": clean_copy_library_text(raw.get("risk"), 100) or "AI 动态评估",
            "scene": clean_copy_library_text(raw.get("scene"), 140) or context["product"]["scenes"][index % len(context["product"]["scenes"])],
            "directPrompt": direct,
            "inspectionPrompt": inspection,
        }
    if set(by_index) != set(range(len(expected_roles))):
        raise AiError(HTTPStatus.BAD_GATEWAY, "AI 返回的提示词索引、角色或正文不完整，请重试生成。")
    prompts = [by_index[index] for index in range(len(expected_roles))]
    repairs: list[dict[str, str]] = []
    raw_repairs = value.get("repairs")
    if isinstance(raw_repairs, list):
        for item in raw_repairs[:5]:
            if not isinstance(item, dict):
                continue
            title = clean_copy_library_text(item.get("title"), 100)
            text = clean_task_multiline(item.get("text"), 700)
            if title and text:
                repairs.append({"title": title, "text": text})
    notes = normalize_fashion_analysis_list(value.get("notes"), 4, 180)
    if repaired_claims:
        repaired_note = "服务器已自动中性化未确认宣称：" + "、".join(sorted(repaired_claims))
        notes = [repaired_note, *notes][:4]
    result = {
        "prompts": prompts,
        "repairs": repairs,
        "notes": notes,
    }
    validate_fashion_generation_result(result, context)
    return result


def fashion_fidelity_text(value: Any) -> str:
    return re.sub(r"[\s，,。；;：:、｜|/\\（）()【】\[\]·\-—_]+", "", str(value or "")).lower()


def fashion_fidelity_fact_score(prompt_texts: list[str], facts: list[str]) -> int:
    normalized_facts = [fashion_fidelity_text(fact) for fact in facts if fact and fact not in {"未确认", "未知"}]
    normalized_facts = [fact for fact in normalized_facts if fact]
    if not normalized_facts:
        return 100
    if not prompt_texts:
        return 0
    prompt_hits: list[float] = []
    for text in prompt_texts:
        hits = sum(1 for fact in normalized_facts if fact in text)
        prompt_hits.append(hits / len(normalized_facts))
    return int(round(sum(prompt_hits) / len(prompt_hits) * 100))


def calculate_fashion_prompt_fidelity(context: dict[str, Any], prompts: list[dict[str, Any]]) -> dict[str, Any]:
    """Predict whether final prompt text preserves observable product facts.

    This is deliberately a prompt-level preflight score, not a claim about the
    pixels of a video that has not been generated yet.
    """
    product = context.get("product") if isinstance(context.get("product"), dict) else {}
    prompt_texts: list[str] = []
    raw_prompt_texts: list[str] = []
    for item in prompts if isinstance(prompts, list) else []:
        if not isinstance(item, dict):
            continue
        pieces = [item.get("directPrompt"), item.get("inspectionPrompt"), item.get("prompt")]
        text = "\n".join(str(piece or "") for piece in pieces if piece)
        if text:
            raw_prompt_texts.append(text)
            prompt_texts.append(fashion_fidelity_text(text))

    category_details = product.get("categoryDetails") if isinstance(product.get("categoryDetails"), dict) else {}
    anchor_facts = normalize_fashion_analysis_list(product.get("anchors"), 8, 180)
    structure_facts = [
        str(product.get("frontStructure") or ""),
        str(product.get("backStructure") or ""),
        *[str(value) for value in category_details.values()],
    ]
    identity_score = fashion_fidelity_fact_score(
        prompt_texts, [str(product.get("name") or ""), str(product.get("category") or "")]
    )
    color_score = fashion_fidelity_fact_score(prompt_texts, [str(product.get("color") or "")])
    silhouette_score = fashion_fidelity_fact_score(prompt_texts, [str(product.get("silhouette") or "")])
    structure_score = fashion_fidelity_fact_score(prompt_texts, structure_facts)
    parts_score = fashion_fidelity_fact_score(prompt_texts, anchor_facts)

    text_scores: list[int] = []
    for raw_text in raw_prompt_texts:
        boundary_hits = sum(
            marker in raw_text
            for marker in ("无字幕", "画内文字", "不新增", "不改写", "已有标识", "后期边界", "留到后期")
        )
        text_scores.append(min(100, boundary_hits * 34))
    text_score = int(round(sum(text_scores) / len(text_scores))) if text_scores else 0

    placeholders = [
        str(item.get("placeholder") or "")
        for item in context.get("referenceMap", [])
        if isinstance(item, dict) and item.get("placeholder")
    ]
    references_score = fashion_fidelity_fact_score(prompt_texts, placeholders) if placeholders else 100

    dimension_data = [
        ("identity", "商品身份", identity_score, "商品名与品类是否在每条最终提示词中保持明确。"),
        ("color", "颜色", color_score, "主色、辅色与五金色是否被完整锁定。"),
        ("silhouette", "轮廓", silhouette_score, "整体外形、比例与规格感是否被保留。"),
        ("structure", "结构与接口", structure_score, "主要结构和品类专用字段是否进入最终提示词。"),
        ("text", "文字边界", text_score, "是否禁止新增、改写画内文字并把营销文案留到后期。"),
        ("parts", "部件数量与位置", parts_score, "脆弱锚点、部件数量和位置是否被持续锁定。"),
        ("references", "参考图职责", references_score, "已绑定参考图是否以原占位符进入每条提示词。"),
    ]
    weights = {"identity": 0.18, "color": 0.14, "silhouette": 0.14, "structure": 0.18, "text": 0.10, "parts": 0.14, "references": 0.12}
    dimensions = [
        {"key": key, "label": label, "score": score, "message": message}
        for key, label, score, message in dimension_data
    ]
    score = int(round(sum(item[2] * weights[item[0]] for item in dimension_data)))

    consistency = context.get("referenceConsistency") if isinstance(context.get("referenceConsistency"), dict) else {}
    consistency_status = consistency.get("status")
    if consistency_status == "conflict" or consistency.get("sameProduct") is False:
        score = max(0, score - 25)
    elif consistency_status == "warning":
        score = max(0, score - 6)

    suggestions_by_key = {
        "identity": "在每条提示词中重复当前商品名和准确品类，避免退化成通用商品。",
        "color": "把主色、辅色和五金色写入公共商品锁后重新生成。",
        "silhouette": "补充并锁定完整轮廓、比例和规格感，再生成全部版本。",
        "structure": "补充接口、按键、泵头、开封方式等品类专用结构，并指定权威参考图。",
        "text": "增加“已有文字按参考保持，不新增或改写，营销文案后期添加”的边界。",
        "parts": "明确关键部件的数量、位置和连接关系，加入不可增减约束。",
        "references": "为每张参考图分配单一职责，并确保 @参考占位符保留在最终提示词中。",
    }
    suggestions = [suggestions_by_key[item["key"]] for item in dimensions if item["score"] < 70]
    if consistency_status == "conflict" or consistency.get("sameProduct") is False:
        suggestions.insert(0, "参考图存在串品冲突，请删除错误图片或按维度重新指定权威来源后再生成。")
    suggestions = suggestions[:5]
    grade = "高锁定" if score >= 90 else "可生成" if score >= 75 else "需复核" if score >= 60 else "高风险"
    summary = (
        f"生成前预测 {score} 分：最终提示词已覆盖多数商品事实。"
        if score >= 75
        else f"生成前预测 {score} 分：仍有商品事实未充分锁定，建议按下方项目补齐后重生成。"
    )
    return {"score": score, "grade": grade, "summary": summary, "dimensions": dimensions, "suggestions": suggestions}


def generate_fashion_prompts(payload: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    context = normalize_fashion_generation_payload(payload)
    if context["referenceConsistency"].get("status") == "conflict" or context["referenceConsistency"].get("sameProduct") is False:
        raise ValueError("参考图一致性检查发现串品冲突，请删除冲突图片或重新指定权威来源后再生成。")
    images = parse_fashion_generation_images(payload)
    active_config = read_runtime_config() if config is None else config
    product = context["product"]
    profile = context["productProfile"]
    fidelity = product.get("promptMode") == "fidelity"
    has_back_reference = any(item.get("roleKey") == "back" for item in context["referenceMap"])
    direct_count = fashion_direct_shot_count(product)
    inspection_rule = (
        "检查完整版必须在【时间轴】中写镜头1至镜头8，并逐字使用这八段时间："
        "00:00—00:02、00:02—00:03.5、00:03.5—00:05、00:05—00:07、"
        "00:07—00:08.5、00:08.5—00:10、00:10—00:12.5、00:12.5—00:15。"
        if product["duration"] >= 15
        else f"检查完整版最多使用 {direct_count} 个镜头。"
    )
    direct_rule = (
        "当前是高还原模式：inspectionPrompt就是最终直接粘贴到Seedance的正文，必须把完整商品锁、参考职责、主体与操作连续性、自然演示、商品物理、声音、必要排除和终点全部写进这一条正文。"
        "15秒必须使用镜头1至镜头8以及规定的八段时间，每镜头只安排一个可见动作、一个主要视角、一个商品展示证据和一个完成终点。"
        "八个镜头共同服务本条唯一主任务，不用八次重复站立，不机械复用同一套动作。directPrompt返回空字符串，服务器会把检查完整版直接作为高还原直贴版，避免重复生成浪费Token。"
        if fidelity
        else (
            "当前是精简稳定模式：directPrompt是实际送入Seedance的独立生成单元。"
            f"必须明确编号镜头1至镜头{direct_count}；同一地点、同一主体、同一商品、同一颜色和同一组实际配件连续发生，每镜头一个主动作、一个主要视角和一个可核对终点。"
            "inspectionPrompt仍保留完整检查章节和15秒八镜头分镜。"
        )
    )
    system_prompt = (
        "你是通用电商商品 Seedance 2.0 提示词导演，由 Seedance 2.0 Skill OS v6.7.0 和 Universal Product Prompt Router 双重约束。"
        "这次必须从当前新品资料与参考图片重新导演，禁止填充预写镜头模板，禁止复用示例商品的动作、场景、人物或商品细节。"
        "先读取productProfile再设计镜头：服饰才允许模特穿着走动；美妆使用容器和手背演示；食品使用包装、内容物与卫生操作；数码使用设备、接口和控件；家居、厨房、家电、宠物、运动、汽车等必须服从各自operator、continuityRule与exclusions。"
        "固定的 JSON 和章节只是交付格式，不是拍摄模板；每条的动作、机位、光线、场景和终点都要根据当前商品最容易漂移的结构独立推导，不得机械重复同一套动作与镜头。"
        "这是非叙事商品证明任务，不编造剧情、人物欲望、情绪转折或商品人格。每条只承担一个主要生成预算。"
        "商品档案、公共商品锁、参考职责和图片是唯一事实源；不得猜测未知背面、底部、接口、内容物、开合、五金、成分、参数或功能，不得写疗效、健康、安全、性能、显瘦、舒适、凉感、抗皱或高级感等未确认宣称。"
        "多图冲突时每个维度只选择一个最清晰权威来源。没有背面或底部参考时不得补全隐藏结构；只有侧面参考时最多使用轻微三分之二角度。"
        "必须服从referenceConsistency：每个维度只使用canonicalSources指定的单一权威图片；不得把冲突图片调和成一个现实中不存在的混合商品。"
        "platformStrategy只控制画幅、节奏、首屏重点与安全区，不得覆盖商品事实，也不代表平台永久技术上限。"
        f"{direct_rule}"
        "不要写电影感、大片感、氛围感、4K、8K等空泛质量词；不用复杂环绕、剧烈动作、慢动作、职业摆拍或无依据的材质与工作状态。"
        "人物、手、宠物、食材、配件、道具与环境都是从属层，不得遮挡商品；画面无字幕、价格、UI、水印和拍摄设备。商品已有标识只按参考保持，不新增或改写可读文字。声音只写与动作同步的自然环境声，无对白、无生成配乐，BGM与文案留到后期。"
        "检查完整版也必须是本次 AI 原创编排，并完整包含这些章节且各出现一次："
        "【模式】【非叙事任务】【主任务】【参考】【整体设定】【商品锁定】【构图硬性要求】【时间轴】【连续性与物理】【声音】【终点】【负面约束】【后期边界】。"
        "高还原模式下服务器还会按品类锁定主体连续性、自然操作和商品物理三层；AI在整体设定和镜头动作中必须与productProfile一致，不得把所有商品都写成模特走秀，也不得让道具遮挡商品。"
        f"{inspection_rule}"
        "严格执行diversityRules：同一批每条的【主任务】、镜头1【画面】第一动作、镜头1首个机位必须分别不同；只换标题、场景或形容词不算不同。"
        "保持输入中的 @参考占位符逐字不变，只能使用 referenceMap 中存在的占位符。"
        "返回一个有效 JSON 对象，不要 Markdown、解释或代码围栏。结构必须是："
        '{"prompts":[{"index":0,"key":"overview","title":"本条中文标题","risk":"本条主要风险","scene":"实际选用的一个地点","directPrompt":"高还原模式留空；精简模式写稳定版","inspectionPrompt":"AI从零写的完整高还原版"}],'
        '"repairs":[{"title":"单一故障名称","text":"只修复一个故障的可追加条款"}],"notes":["最多4条简短说明"]}。'
    )
    model_context = {
        **context,
        "referencePolicy": {
            "hasBackAuthority": has_back_reference,
            "instruction": "背面、底部或隐藏侧展示只能由 hasBackAuthority=true 授权；不得仅凭未知描述补全。",
        },
        "outputRules": {
            "directShotCount": direct_count,
            "promptMode": product["promptMode"],
            "sameSceneWithinEachDirectPrompt": not fidelity,
            "independentPromptCount": product["count"],
            "writeFromScratch": True,
            "embedCompleteProductLockInEveryCopiedPrompt": True,
            "productRoute": profile["id"],
            "requireDistinctMainTaskFirstActionAndCamera": True,
        },
    }
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": "当前新品生成上下文：\n" + json.dumps(model_context, ensure_ascii=False, indent=2),
        }
    ]
    for index, image in enumerate(images):
        content.append({"type": "text", "text": f"当前新品参考图 {index + 1}：{image['name']}；人工角色：{image['role']}"})
        content.append({"type": "image_url", "image_url": {"url": image["dataUrl"]}})
    default_timeout = 600 if fidelity or product["count"] > 3 else 360
    response = call_ai_chat(
        {
            "model": get_ai_model(active_config),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": min(max(get_ai_temperature(active_config), 0.2), 0.4),
            "max_tokens": 20000 if product["count"] <= 3 else 32000,
        },
        timeout_seconds=parse_int_env("FASHION_GENERATION_TIMEOUT_SECONDS", default_timeout),
        config=active_config,
    )
    raw = extract_ai_text(response)
    parsed = parse_json_object(raw)
    if not parsed:
        raise AiError(HTTPStatus.BAD_GATEWAY, "AI 没有返回有效的新品提示词 JSON，请重试生成。")
    normalized = normalize_fashion_generation_result(parsed, context)
    return {
        **normalized,
        "fidelityReport": calculate_fashion_prompt_fidelity(context, normalized["prompts"]),
        "model": get_ai_model(active_config),
        "usage": safe_ai_usage(response),
        "insecureEndpoint": get_ai_base_url(active_config).startswith("http://"),
    }


def normalize_fashion_optimization_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_product = payload.get("product")
    if not isinstance(raw_product, dict):
        raise ValueError("缺少当前商品档案，请先重新生成本地提示词。")
    platform_preset = clean_copy_library_text(raw_product.get("platformPreset"), 24).lower() or "custom"
    if platform_preset not in FASHION_PLATFORM_PRESETS:
        platform_preset = "custom"
    product = {
        "name": clean_copy_library_text(raw_product.get("name"), 100),
        "category": clean_copy_library_text(raw_product.get("category"), 80),
        "color": clean_copy_library_text(raw_product.get("color"), 220),
        "silhouette": clean_copy_library_text(raw_product.get("silhouette"), 500),
        "frontStructure": clean_copy_library_text(raw_product.get("frontStructure"), 900),
        "backStructure": clean_copy_library_text(raw_product.get("backStructure"), 700),
        "material": clean_copy_library_text(raw_product.get("material"), 500),
        "categoryDetails": normalize_fashion_category_details(raw_product.get("categoryDetails")),
        "stylingBoundary": clean_copy_library_text(raw_product.get("stylingBoundary"), 500),
        "anchors": clean_copy_library_text(raw_product.get("anchors"), 700),
        "promptMode": clean_copy_library_text(raw_product.get("promptMode"), 24) or "fidelity",
        "duration": raw_product.get("duration"),
        "ratio": clean_copy_library_text(raw_product.get("ratio"), 24),
        "market": clean_copy_library_text(raw_product.get("market"), 100),
        "scenes": normalize_fashion_analysis_list(raw_product.get("scenes"), 6, 100),
        "platformPreset": platform_preset,
        "platformStrategy": normalize_fashion_platform_strategy(raw_product.get("platformStrategy")),
    }
    if not product["name"]:
        raise ValueError("商品名称为空，请先重新生成本地提示词。")
    if product["promptMode"] not in FASHION_PROMPT_MODES:
        raise ValueError("提示词模式只能是高还原或精简稳定。")

    common_lock = clean_task_multiline(payload.get("commonLock"), 7000)
    if len(common_lock) < 30:
        raise ValueError("公共商品锁不完整，请先重新生成本地提示词。")

    raw_prompts = payload.get("prompts")
    if not isinstance(raw_prompts, list) or not raw_prompts:
        raise ValueError("没有可供 AI 优化的本地提示词。")
    if len(raw_prompts) > MAX_FASHION_OPTIMIZATION_PROMPTS:
        raise ValueError(f"AI 优化一次最多处理 {MAX_FASHION_OPTIMIZATION_PROMPTS} 条提示词。")
    prompts: list[dict[str, Any]] = []
    used_indices: set[int] = set()
    for position, item in enumerate(raw_prompts):
        if not isinstance(item, dict):
            raise ValueError(f"第 {position + 1} 条提示词格式无效。")
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"第 {position + 1} 条提示词缺少有效索引。") from exc
        if index < 0 or index >= len(raw_prompts) or index in used_indices:
            raise ValueError("本地提示词索引重复或不连续，请重新生成。")
        prompt = clean_task_multiline(item.get("prompt"), MAX_FASHION_OPTIMIZATION_PROMPT_CHARS)
        if len(prompt) < 80:
            raise ValueError(f"第 {position + 1} 条本地提示词过短，请重新生成。")
        used_indices.add(index)
        prompts.append(
            {
                "index": index,
                "key": clean_copy_library_text(item.get("key"), 60),
                "title": clean_copy_library_text(item.get("title"), 100),
                "risk": clean_copy_library_text(item.get("risk"), 100),
                "prompt": prompt,
            }
        )
    if used_indices != set(range(len(raw_prompts))):
        raise ValueError("本地提示词索引不连续，请重新生成。")
    prompts.sort(key=lambda item: item["index"])

    reference_map: list[dict[str, str]] = []
    raw_reference_map = payload.get("referenceMap")
    if isinstance(raw_reference_map, list):
        for item in raw_reference_map[:MAX_FASHION_ANALYSIS_IMAGES]:
            if not isinstance(item, dict):
                continue
            reference_map.append(
                {
                    "placeholder": clean_copy_library_text(item.get("placeholder"), 100),
                    "role": clean_copy_library_text(item.get("role"), 100),
                    "authority": clean_copy_library_text(item.get("authority"), 260),
                }
            )
    raw_template = payload.get("template")
    template_source = raw_template if isinstance(raw_template, dict) else {}
    raw_profile = template_source.get("profile")
    profile_source = raw_profile if isinstance(raw_profile, dict) else {}
    profile = {
        "id": clean_copy_library_text(profile_source.get("id"), 60) or "universal",
        "name": clean_copy_library_text(profile_source.get("name"), 100) or "通用商品",
        "garmentSpan": clean_copy_library_text(profile_source.get("garmentSpan"), 260),
        "productSpan": clean_copy_library_text(profile_source.get("productSpan"), 260),
        "overviewProof": clean_copy_library_text(profile_source.get("overviewProof"), 360),
        "detailProof": clean_copy_library_text(profile_source.get("detailProof"), 360),
        "motionProof": clean_copy_library_text(profile_source.get("motionProof"), 420),
        "activityProof": clean_copy_library_text(profile_source.get("activityProof"), 420),
        "frontBackRule": clean_copy_library_text(profile_source.get("frontBackRule"), 420),
        "continuityRule": clean_copy_library_text(profile_source.get("continuityRule"), 420),
        "subject": clean_copy_library_text(profile_source.get("subject"), 260),
        "operator": clean_copy_library_text(profile_source.get("operator"), 360),
        "framing": clean_copy_library_text(profile_source.get("framing"), 360),
        "exclusions": normalize_fashion_analysis_list(profile_source.get("exclusions"), 6, 220),
    }
    template = {
        "id": clean_copy_library_text(template_source.get("id"), 60) or "universal",
        "name": clean_copy_library_text(template_source.get("name"), 120) or "通用商品稳定模板",
        "source": clean_copy_library_text(template_source.get("source"), 220) or "页面通用规则",
        "summary": clean_copy_library_text(template_source.get("summary"), 500),
        "promptRule": clean_copy_library_text(template_source.get("promptRule"), 1800),
        "rules": normalize_fashion_analysis_list(template_source.get("rules"), 8, 260),
        "modules": normalize_fashion_analysis_list(template_source.get("modules"), 14, 160),
        "qualityGate": normalize_fashion_analysis_list(template_source.get("qualityGate"), 12, 220),
        "promptArchitecture": clean_copy_library_text(template_source.get("promptArchitecture"), 1600),
        "profile": profile,
    }
    raw_compiler = payload.get("compiler")
    compiler_source = raw_compiler if isinstance(raw_compiler, dict) else {}
    compiler = {
        "name": clean_copy_library_text(compiler_source.get("name"), 120) or "Seedance 2.0 Skill OS",
        "version": clean_copy_library_text(compiler_source.get("version"), 32) or "6.7.0",
        "fashionSkill": clean_copy_library_text(compiler_source.get("fashionSkill"), 120) or "Universal Product Prompt Router",
        "profile": clean_copy_library_text(compiler_source.get("profile"), 120) or "中文通用商品短视频提示词",
        "order": normalize_fashion_analysis_list(compiler_source.get("order"), 8, 80),
    }
    product_profile = infer_fashion_product_profile(product)
    reference_consistency = normalize_fashion_reference_consistency(
        payload.get("referenceConsistency"), len(reference_map)
    )
    return {
        "product": product,
        "productProfile": product_profile,
        "commonLock": common_lock,
        "compiler": compiler,
        "template": template,
        "referenceMap": reference_map,
        "referenceConsistency": reference_consistency,
        "prompts": prompts,
    }


def normalize_fashion_optimization_result(value: dict[str, Any], expected_count: int) -> dict[str, Any]:
    raw_prompts = value.get("prompts")
    if not isinstance(raw_prompts, list):
        raise AiError(HTTPStatus.BAD_GATEWAY, "模型没有返回完整的 prompts 数组，已保留本地版本。")
    prompts: list[dict[str, Any]] = []
    used_indices: set[int] = set()
    for item in raw_prompts:
        if not isinstance(item, dict):
            continue
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        prompt = clean_task_multiline(item.get("prompt"), MAX_FASHION_OPTIMIZATION_PROMPT_CHARS)
        if index < 0 or index >= expected_count or index in used_indices or len(prompt) < 80:
            continue
        used_indices.add(index)
        prompts.append({"index": index, "prompt": prompt})
    if used_indices != set(range(expected_count)):
        raise AiError(HTTPStatus.BAD_GATEWAY, "模型返回的提示词数量或索引不完整，已保留本地版本。")
    prompts.sort(key=lambda item: item["index"])
    notes = normalize_fashion_analysis_list(value.get("notes"), 3, 160)
    return {"prompts": prompts, "notes": notes}


FASHION_PROMPT_MUTABLE_SECTIONS = {
    "时间轴",
    "连续动作",
    "镜头",
    "展示",
    "段落终点",
    "终点",
}


def parse_fashion_prompt_sections(prompt: str) -> tuple[str, list[tuple[str, str]], dict[str, str]]:
    text = clean_task_multiline(prompt, MAX_FASHION_OPTIMIZATION_PROMPT_CHARS)
    matches = list(re.finditer(r"【([^】\r\n]+)】", text))
    if not matches:
        return text, [], {}
    preamble = text[: matches[0].start()].rstrip()
    ordered: list[tuple[str, str]] = []
    by_label: dict[str, str] = {}
    for position, match in enumerate(matches):
        label = match.group(1).strip()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        ordered.append((label, body))
        by_label[label] = body
    return preamble, ordered, by_label


def fashion_prompt_shot_ids(prompt: str) -> list[int]:
    _, _, sections = parse_fashion_prompt_sections(prompt)
    timeline = sections.get("时间轴", "")
    return [int(value) for value in re.findall(r"镜头\s*(\d+)(?=\s*(?:[：:\[（(]|$))", timeline)]


def merge_fashion_optimized_prompt(original: str, candidate: str) -> str:
    preamble, original_ordered, original_sections = parse_fashion_prompt_sections(original)
    _, _, candidate_sections = parse_fashion_prompt_sections(candidate)
    if not original_ordered:
        return original
    if "时间轴" in original_sections and "时间轴" not in candidate_sections:
        raise AiError(HTTPStatus.BAD_GATEWAY, "模型遗漏了多镜头时间轴，已保留本地版本。")
    if "连续动作" in original_sections and "连续动作" not in candidate_sections:
        raise AiError(HTTPStatus.BAD_GATEWAY, "模型改变了一镜到底结构，已保留本地版本。")
    merged = [preamble] if preamble else []
    for label, original_body in original_ordered:
        body = candidate_sections.get(label, original_body) if label in FASHION_PROMPT_MUTABLE_SECTIONS else original_body
        merged.append(f"【{label}】{body}")
    return "\n".join(merged).strip()


def lock_fashion_optimization_result(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    originals = {item["index"]: item["prompt"] for item in context["prompts"]}
    return {
        **result,
        "prompts": [
            {
                "index": item["index"],
                "prompt": merge_fashion_optimized_prompt(originals[item["index"]], item["prompt"]),
            }
            for item in result["prompts"]
        ],
    }


def validate_fashion_optimization_preservation(result: dict[str, Any], context: dict[str, Any]) -> None:
    optimized_by_index = {item["index"]: item["prompt"] for item in result["prompts"]}
    placeholders = [item["placeholder"] for item in context["referenceMap"] if item.get("placeholder")]
    required_sections = [
        "【模式】",
        "【非叙事任务】",
        "【主任务】",
        "【参考】",
        "【整体设定】",
        "【商品锁定】",
        "【构图硬性要求】",
        "【连续性与物理】",
        "【声音】",
        "【终点】",
        "【负面约束】",
        "【后期边界】",
    ]
    product_name = context["product"]["name"]
    legacy_facts = ["中灰色", "三粒同色", "方形贴袋", "埃菲尔铁塔"]
    product_text = json.dumps(context["product"], ensure_ascii=False)
    for original in context["prompts"]:
        index = original["index"]
        optimized = optimized_by_index[index]
        _, _, original_sections = parse_fashion_prompt_sections(original["prompt"])
        _, _, optimized_sections = parse_fashion_prompt_sections(optimized)
        for section in required_sections:
            if section in original["prompt"] and section not in optimized:
                raise AiError(HTTPStatus.BAD_GATEWAY, f"模型遗漏了第 {index + 1} 条的{section}，已保留本地版本。")
        for label, original_body in original_sections.items():
            if label not in FASHION_PROMPT_MUTABLE_SECTIONS and optimized_sections.get(label) != original_body:
                raise AiError(HTTPStatus.BAD_GATEWAY, f"第 {index + 1} 条的商品事实章节未被锁定，已保留本地版本。")
        if "【时间轴】" in original["prompt"] and "【时间轴】" not in optimized:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"模型遗漏了第 {index + 1} 条的时间轴，已保留本地版本。")
        if "【连续动作】" in original["prompt"] and "【连续动作】" not in optimized:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"模型改变了第 {index + 1} 条的一镜到底结构，已保留本地版本。")
        original_shot_ids = fashion_prompt_shot_ids(original["prompt"])
        if original_shot_ids and fashion_prompt_shot_ids(optimized) != original_shot_ids:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"模型改变了第 {index + 1} 条的镜头数量或编号，已保留本地版本。")
        if product_name not in optimized:
            raise AiError(HTTPStatus.BAD_GATEWAY, f"模型遗漏了第 {index + 1} 条的当前商品名称，已保留本地版本。")
        for placeholder in placeholders:
            if placeholder in original["prompt"] and placeholder not in optimized:
                raise AiError(HTTPStatus.BAD_GATEWAY, f"模型改动了第 {index + 1} 条的参考占位符，已保留本地版本。")
        for legacy_fact in legacy_facts:
            if legacy_fact not in product_text and legacy_fact in optimized and legacy_fact not in original["prompt"]:
                raise AiError(HTTPStatus.BAD_GATEWAY, f"模型把旧模板事实带入了第 {index + 1} 条，已保留本地版本。")


def optimize_fashion_prompts(payload: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    context = normalize_fashion_optimization_payload(payload)
    active_config = read_runtime_config() if config is None else config
    duration = int(context["product"].get("duration") or 15)
    fidelity = context["product"].get("promptMode") == "fidelity"
    timeline_rule = (
        (
            "当前是15秒高还原直贴层：必须原样保留镜头1—8的数量、编号与八个时间段；八个镜头都会直接送入Seedance。可以优化每镜头动作、主要视角、展示目标和完成终点，但不得合并、删除、新增或重新编号镜头。每镜头只保留一个可见动作、一个主要视角和一个完成终点，八个镜头共同服务本条唯一商品证明任务。"
            if fidelity
            else "当前是15秒稳定模式：必须原样保留检查版镜头1—8的数量、编号与八个时间段；可以优化每镜头动作、主要视角、展示目标和完成终点，但不得合并、删除、新增或重新编号镜头。镜头1—3是精简直贴生成单元的来源，三者必须保持同一地点、同一主体、同一商品和同一组实际配件，每镜头只保留一个可见动作、一个主要运镜和一个完成终点，不得在前三镜头加入换场、额外剧情或第二个动作。镜头4—8仅供检查和后期拆分。"
        )
        if duration >= 15
        else "5秒使用单镜头连续动作；10秒最多2个镜头；每镜头只写一个主动作、一个主要运镜、一个展示目标和一个动作完成后的段落终点。"
    )
    product_profile = context["productProfile"]
    system_prompt = (
        "你是由 Seedance 2.0 Skill OS v6.7.0 与 Universal Product Prompt Router 共同约束的通用电商商品提示词编译器，执行非叙事商品展示任务。"
        "先在内部完成非叙事导演判断：utility intent 是当前主任务；拒绝编造人物欲望、冲突、情绪转折或商品人格。不要把这些内部标签写入输出。"
        "每条只分配一个主要生成预算：整体和细节优先商品身份，操作和功能优先单一动作，生活场景仍需压低环境密度；不得同时索取高商品精度、剧烈运动和复杂场景。"
        "输入中的商品档案和公共商品锁是不可修改的唯一事实；不得添加未知背面、底部、接口、开合、配件、成分、参数、疗效、健康、安全、性能、舒适或高级感等信息。"
        "服从referenceConsistency中的单维权威来源，禁止融合冲突参考图；platformStrategy只控制节奏、构图重点和安全区，不得修改商品事实。"
        "输入中的template是从19套、161个镜头的参考TXT重构出的完整拍摄方法，必须充分执行它的modules、qualityGate、promptArchitecture和profile；template绝不是商品事实。即使模板名称或来源文件提到V领、针织衫、颜色、扣件、口袋、人物、穿搭或地点，也不得把这些内容带入当前商品，除非当前商品档案明确确认。"
        "逐条只优化【时间轴】或一镜到底的【连续动作】【镜头】【展示】【段落终点】，以及【终点】。其他章节是不可修改的商品事实层，即使返回时改写，服务器也会恢复为本地原文。"
        "不得改变条数、索引、模式、主任务、参考职责、商品颜色、类别、结构、构图要求、连续性、声音、负面约束、后期边界或占位符。"
        "每条必须独立可用。返回的prompt字段只写允许修改的动态章节：多镜头使用【时间轴】和【终点】；一镜到底使用【连续动作】【镜头】【展示】【段落终点】和【终点】。服务器会把它们合并回完整提示词，不要重复不可修改章节。"
        f"{timeline_rule}"
        f"当前产品路由为{product_profile['name']}。整体镜头必须完整呈现productProfile.productSpan；细节镜头必须让结构边缘、数量、位置、连接关系和相邻材质可核对。"
        "把人物、手、宠物、食材、配件、道具和环境放在从属层；全片使用同一商品、同一颜色和同一组实际配件。材质、内容物或工作状态只按当前档案描述可见变化，不把动作演示改写成商品功效。"
        "按productProfile.subject和operator选择主体与动作；只有服饰类才使用模特穿着、走动和衣料摩擦。默认日常真实实拍、无新增画内文字、无对白、无生成配乐；字幕、本地化配音、BGM、价格和CTA留到后期。"
        "保持所有以@开头的参考占位符逐字不变。删除空泛质量词，不写电影大片、T台或奢侈品广告式堆词。"
        "动态章节按参考职责、主体与可见动作、一个运镜及终点、物理光线、声音、保持约束的顺序编译；不要用同义句重复展示目标，不要把一条提示词写成拍摄说明书。"
        "压缩优先级固定为：参考标签与职责、商品身份、动作与终点、一个运镜、物理光源、声音、连续性约束。先删除背景装饰、重复动作、第二运镜和空泛形容词。"
        "只返回一个有效 JSON 对象，不要 Markdown，不要解释。结构必须是："
        '{"prompts":[{"index":0,"prompt":"仅包含允许优化的动态章节"}],"notes":["最多3条简短优化说明"]}。'
    )
    response = call_ai_chat(
        {
            "model": get_ai_model(active_config),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False, indent=2)},
            ],
            "temperature": min(max(get_ai_temperature(active_config), 0.15), 0.3),
            "max_tokens": 12000,
        },
        timeout_seconds=parse_int_env("FASHION_OPTIMIZATION_TIMEOUT_SECONDS", 240),
        config=active_config,
    )
    raw = extract_ai_text(response)
    parsed = parse_json_object(raw)
    if not parsed:
        raise AiError(HTTPStatus.BAD_GATEWAY, "模型没有返回有效的提示词 JSON，已保留本地版本。")
    normalized = normalize_fashion_optimization_result(parsed, len(context["prompts"]))
    locked = lock_fashion_optimization_result(normalized, context)
    validate_fashion_optimization_preservation(locked, context)
    return {
        **locked,
        "fidelityReport": calculate_fashion_prompt_fidelity(context, locked["prompts"]),
        "model": get_ai_model(active_config),
        "usage": safe_ai_usage(response),
        "insecureEndpoint": get_ai_base_url(active_config).startswith("http://"),
    }


def extract_seedance_prompt(content: str) -> str:
    markers = [
        "视频生成提示词：",
        "视频生成提示词:",
        "Seedance Prompt：",
        "Seedance Prompt:",
        "中文 Prompt：",
        "中文 Prompt:",
        "中文提示词：",
        "中文提示词:",
        "English Prompt:",
        "English:",
        "英文 Prompt:",
        "英文提示词：",
        "英文：",
    ]
    for marker in markers:
        index = content.find(marker)
        if index < 0:
            continue
        prompt = content[index + len(marker) :].strip()
        prompt = re.split(r"\n\s*(?:Negative Prompt|负面提示词|参考图建议|Prompt 队列|##|###|中文：|Chinese:|English:)", prompt, maxsplit=1)[0].strip()
        if prompt:
            return prompt.strip().strip('"')
    return ""


def seedance_prompt_needs_repair(prompt: str) -> bool:
    text = prompt.strip()
    has_cjk = contains_cjk_or_kana(text)
    if len(text) < 40:
        return True
    if len(text) < 80 and not has_cjk:
        return True
    if len(text) > 2800:
        return True
    if text.startswith("#") or "## " in text or "\n|" in text:
        return True
    blocked_markers = [
        "商品事实表",
        "推荐结构",
        "分段脚本",
        "实拍 SOP",
        "素材缺口",
        "可沉淀资产",
        "中文：",
        "Chinese:",
    ]
    if any(marker in text for marker in blocked_markers):
        return True
    if not has_cjk:
        return True
    return False


def contains_cjk_or_kana(text: str) -> bool:
    return any(
        "\u3040" <= char <= "\u30ff"
        or "\u3400" <= char <= "\u4dbf"
        or "\u4e00" <= char <= "\u9fff"
        or "\uf900" <= char <= "\ufaff"
        or "\uac00" <= char <= "\ud7af"
        for char in text
    )


def build_prompt_generation_user_message(payload: dict[str, Any], brief: str, draft: str) -> str:
    ratio = str(payload.get("ratio") or "9:16")
    duration = parse_duration(payload.get("duration"))
    quantity = parse_quantity(payload.get("quantity"))
    ref_images = parse_url_list(payload.get("refImages"))
    ref_videos = parse_url_list(payload.get("refVideos"))
    ref_audios = parse_url_list(payload.get("refAudios"))
    generate_audio = bool(payload.get("generateAudio"))
    watermark = bool(payload.get("watermark"))
    target_market = get_creative_target_market(payload)
    content_language = get_creative_content_language(payload, target_market)

    context = {
        "brand": "SOSOVE",
        "target_platform": "short-form ecommerce video",
        "target_market": target_market,
        "content_language": content_language,
        "localization_rule": "Use target-market people, everyday settings, styling, spoken rhythm, and native wording without stereotypes or invented product facts.",
        "ratio": ratio,
        "duration_seconds": duration,
        "batch_quantity": quantity,
        "generate_audio": generate_audio,
        "watermark": watermark,
        "reference_image_count": len(ref_images),
        "reference_video_count": len(ref_videos),
        "reference_audio_count": len(ref_audios),
        "reference_images": ref_images,
        "reference_videos": ref_videos,
        "reference_audios": ref_audios,
        "user_brief": brief,
        "existing_draft_prompt": draft,
    }
    return (
        "Create a Seedance prompt from this structured context. "
        "If reference images exist, explicitly instruct the model to replicate the garment silhouette, color tone, fabric texture, trim, hem, edge details, and length proportion.\n\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def call_ai_chat(
    body: dict[str, Any],
    timeout_seconds: int | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = get_ai_api_key(config)
    if not api_key:
        raise AiError(
            HTTPStatus.BAD_REQUEST,
            "AI_API_KEY is missing. Set AI_API_KEY or OPENAI_API_KEY before starting the server.",
        )

    endpoint = build_ai_chat_endpoint(config)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = Request(endpoint, data=data, headers=headers, method="POST")

    try:
        with urlopen(request, timeout=timeout_seconds or parse_int_env("AI_TIMEOUT_SECONDS", 180)) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        message = read_error_message(exc)
        status = HTTPStatus(exc.code) if exc.code in HTTPStatus._value2member_map_ else HTTPStatus.BAD_GATEWAY
        raise AiError(status, message) from exc
    except URLError as exc:
        raise AiError(HTTPStatus.BAD_GATEWAY, f"AI request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise AiError(HTTPStatus.GATEWAY_TIMEOUT, "AI request timed out. Try a shorter brief or increase AI_TIMEOUT_SECONDS.") from exc
    except OSError as exc:
        raise AiError(HTTPStatus.BAD_GATEWAY, f"AI connection failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AiError(HTTPStatus.BAD_GATEWAY, "AI returned an invalid JSON response.") from exc


def build_ai_chat_endpoint(config: dict[str, Any] | None = None) -> str:
    base_url = get_ai_base_url(config)
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def extract_ai_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") if isinstance(response, dict) else None
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            parts.append(item["text"])
                    if parts:
                        return "\n".join(parts)
            if isinstance(first.get("text"), str):
                return first["text"]
    output_text = response.get("output_text") if isinstance(response, dict) else None
    return output_text if isinstance(output_text, str) else ""


def parse_int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def parse_float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def read_error_message(exc: HTTPError) -> str:
    raw = exc.read().decode("utf-8", errors="replace")
    if not raw:
        return f"Ark API error: HTTP {exc.code}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(payload, dict):
        message = str(payload.get("message") or payload.get("error") or payload.get("detail") or payload)
    else:
        message = str(payload)
    lowered = message.lower()
    if "inputimagesensitivecontentdetected.privacyinformation" in lowered or "may contain real person" in lowered:
        return (
            "Seedance 拒绝了含真人脸的普通参考图。请在镜头的“真人处理”中使用“商品隐私模式”，"
            "或改为纯提示词；需要保留真人身份时，必须使用火山方舟已授权的 Asset ID。"
        )
    if "resource download failed" in lowered and "image_url" in lowered:
        return "Seedance 无法下载参考图片。请确认公网图片 URL 可直接访问；面板上传的本机参考图会自动内嵌，请刷新页面后重新提交。"
    if "resource download failed" in lowered and "video_url" in lowered:
        return "Seedance 无法下载参考视频。请使用公网可直接访问的视频 URL，或先移除本机参考视频后重试。"
    if "resource download failed" in lowered:
        return "Seedance 无法下载参考素材。请确认素材 URL 可公网直接访问后重试。"
    return message


def build_curl_preview(body: dict[str, Any]) -> str:
    json_body = json.dumps(public_seedance_request_body(body), ensure_ascii=False, indent=2)
    return (
        "curl -X POST "
        f"{get_ark_endpoint()} "
        '-H "Authorization: Bearer $ARK_API_KEY" '
        '-H "Content-Type: application/json" '
        f"--data '{json_body}'"
    )


def run(host: str, port: int) -> None:
    try:
        sync_obsidian_project_data()
    except Exception as exc:
        print(f"Warning: failed to sync Obsidian project data: {exc}", file=sys.stderr)
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((host, port), SeedanceHandler)
    print(f"Seedance Web running at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Seedance video web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
