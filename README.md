# SOSOVE Ad Lab

本地优先的 AI 电商视频工作台，覆盖素材导入、逐秒分析、剪辑用途标签、自动混剪候选池、剪映草稿、ChatCut 同步、视频文案库、商品提示词和账号任务管理。

这个仓库可以独立克隆到另一台电脑运行。真实 API Key、账号密码、上传视频、Obsidian/NAS 素材和运行数据都不会提交到 Git。

## 主要能力

- 视频素材上传与 NAS/本地文件夹引用，不复制原始大文件
- AI 素材分析、逐秒优缺点、广告阶段识别和剪辑用途标签
- 优质片段、开头钩子、细节特写、卖点证明等角色筛选
- 自动混剪候选池、文案匹配、生成前质量检查和时间线预览
- 可编辑剪映草稿生成，配音、字幕和片段结构保留为独立轨道
- ChatCut 素材同步队列和导入进度记录
- 视频文案库、翻译、口语化改写和广告违禁词检查
- 商品视频提示词工坊与 Seedance 提示词优化
- 管理员和剪辑账号、客户剪辑任务看板
- Obsidian 可读索引，敏感凭据只保存在本机运行目录

## 环境要求

- Python 3.11 或更高版本
- FFmpeg 与 FFprobe
- 可选：剪映、ChatCut、Obsidian、对应 Codex Skills
- 可选：视频分析脚本依赖 `opencv-python-headless`，音频试听依赖 `edge-tts`

Windows 下可先安装 FFmpeg，并确保 `ffmpeg`、`ffprobe` 在 `PATH` 中。

## 快速启动

Windows PowerShell：

```powershell
git clone https://github.com/sosoveooo-bit/sosove-ad-lab-public.git
cd sosove-ad-lab-public
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python server.py --host 127.0.0.1 --port 8794
```

macOS / Linux：

```bash
git clone https://github.com/sosoveooo-bit/sosove-ad-lab-public.git
cd sosove-ad-lab-public
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python server.py --host 127.0.0.1 --port 8794
```

打开：

- 素材工作台：`http://127.0.0.1:8794/materials.html`
- 广告工作台：`http://127.0.0.1:8794/ad-forge.html`
- 商品提示词：`http://127.0.0.1:8794/fashion-prompts.html`
- 服务配置：`http://127.0.0.1:8794/`

首次访问会进入登录页。请在 `.env` 中设置管理员账号：

```dotenv
SEEDANCE_AUTH_USERNAME=admin
SEEDANCE_AUTH_PASSWORD=replace-with-a-long-random-password
```

## 数据目录

默认数据位置：

- 运行配置、登录凭据、上传文件：`./.runtime/`
- 素材库与 Obsidian 索引：`./material-vault/`

可以在 `.env` 中改为已有 Obsidian 素材目录：

```dotenv
SEEDANCE_OBSIDIAN_MATERIAL_ROOT=D:\Backup\Documents\Obsidian Vault\素材上传
```

如果要继续使用原来的工作区目录，也可以保持源码中的环境变量配置。`.runtime/`、`material-vault/`、上传视频、日志和本地虚拟环境均已加入 `.gitignore`。

## AI 与生成服务

按需填写 `.env` 或网页配置页中的模型节点。未配置的模型不会影响素材库、登录和本地剪辑结构查看。

```dotenv
AI_API_BASE_URL=https://your-openai-compatible.example/v1
AI_API_KEY=
AI_MODEL=

AD_FORGE_IMAGE_API_BASE_URL=https://your-image-endpoint.example/v1
AD_FORGE_IMAGE_API_KEY=
AD_FORGE_IMAGE_MODEL=gpt-image-2

ARK_API_KEY=
SEEDANCE_MODEL=doubao-seedance-2-0-260128

ELEVENLABS_API_KEY=
```

不要把真实 Key 写入源码或提交到 GitHub。仓库不会附带第三方接口、账号、Cookie、Session Secret 或生成结果。

## 可选 Skills 与剪映

仓库已包含以下可移植脚本和 Skill 文档：

- `skills/video-material-analyzer/`
- `skills/japanese-fashion-video-editor/`
- `scripts/generate_jianying_draft.py`
- `scripts/export_rough_cut.py`
- `scripts/chatcut_sync_queue.py`

如果使用剪映草稿生成，需要本机安装对应剪映环境和 `jianying-editor` Skill。可通过 `.env` 指定路径：

```dotenv
JIANYING_EDITOR_SKILL_ROOT=C:\path\to\jianying-editor
JIANYING_PYTHON=C:\path\to\python.exe
```

素材分析和剪辑草稿默认在运行面板的电脑上生成。另一台电脑拉取项目后，仍需准备自己的 Python、FFmpeg、素材目录和模型 Key。

## 测试

```powershell
python -m unittest discover -s tests -v
node --check static/materials.js
node --check static/chatcut.js
node --check static/fashion-prompts.js
```

## 开源说明

本项目使用 MIT License。请遵守第三方服务、素材版权、平台广告规则和账号数据隐私要求；仓库只提供本地工作台代码，不提供任何素材或商业数据。
