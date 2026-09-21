现在的功能全貌
一、Seedance 视频生成工作台（index.html）
- 火山 Ark / CPA 中转接口配置，AI 提示词接口与视频生成接口分开配置、分开测试
- Seedance 模型可配，默认 doubao-seedance-2-0-260128，支持 seed2.0 这类别名
- 图片、视频、音频三类素材：本地上传 + URL 输入 + 缩略图/在线预览 + 点击放大或播放
- 素材角色设置：参考图、首帧、尾帧、细节图、动作参考、无脸动作版、背景音乐等
- “仅工作台参考”角色：可预览、可 @ 引用，但不进 Seedance 请求体
- 提示词里 @图片1、@视频1、@音频1 自动补全，每个素材颜色区分
- 提示词模板库：6 套 SOSOVE 常用结构，可追加或替换
- 提示词质量检查：分镜、镜头语言、商品细节、动作、素材引用、合规风险，给分数
- 合规修复：把“换脸/换头像”改写成 AI 虚拟角色外观参考
- AI 虚拟角色设定：无脸安全模式，人脸素材默认不提交
- 生成前预检：接口、模型、URL 有效性、本地/内网 URL 拦截、人脸风险
- 比例（9:16 / 16:9 / 1:1）、时长（5/10/11/15s）、生成数量、有声、水印
- 提示词生成记录，点击回填复用
- 任务中心：批量任务队列、自动轮询、进度统计、JSON 请求预览
- 失败任务一键“修复重试”，单条任务可复制 Prompt、预览视频
- 视频结果预览、复制 URL、下载
二、AI 剪辑素材库（materials.html）
- 视频批量上传，按批次管理
- AI 逐秒分析：优缺点、广告阶段、剪辑用途标签
- 优质片段、开头钩子、细节特写、卖点证明等角色筛选
- 自动混剪候选池，按产品一键成片
- 生成前质量检查 + 成片片段预览
- 手动分段时间线、片段用途和快捷标签编辑
- 草稿文案和配音
- 问题视频素材单独归类
- 优先剪辑 / 需要复核素材分区
- 六步成片流程导航
三、广告视频工作台（ad-forge.html）
- 广告项目管理
- 商品事实 → 分镜编排
- AI 分镜生成、镜头编辑、排序
- 分镜图片生成、任务取消
- 广告合成
- 可编辑性交接
四、商品视频提示词工坊（fashion-prompts.html）
- 商品档案录入
- 按品类切换专用事实模板
- 参考图角色定义
- AI 导演约束和模板
- 输出设置
- 提示词包生成，含商品还原度评分、独立视频提示词
- 生成前质检、失败修复条款
- 多市场版本
五、ChatCut 混剪同步（chatcut.html）
- 素材同步队列
- 同步请求创建、预览、状态更新
- 导入进度记录
六、其他生产配套
- 视频文案库：文案管理、翻译、口语化改写、违禁词检查
- 提示词翻译：本地化校验
- 剪映草稿生成：配音、字幕、片段独立轨道，时间线可编辑
- 粗剪导出
- 客户剪辑任务看板
- 运行中心：生产状态总览
- 账号管理：管理员 / 剪辑账号、密码重置、启停
- 登录鉴权，首次访问需登录
七、开源与部署
- Dockerfile + docker-compose，可 VPS 部署
- 环境变量配置，密钥不进仓库
- 可移植脚本和 Skill 文档随仓库发布
- MIT License
一句话总结
现在是「素材进来 → AI 分析打标 → 自动/手动组片 → 提示词生成 → Seedance 出片 → 剪映/ChatCut 落地 → 任务和账号管理」的完整链路，不只是视频生成面板。
需要提醒的是：素材分析、剪映草稿、ChatCut 同步这些依赖本机 FFmpeg、剪映环境或对应 Skill；没配 AI Key 和 Ark Key 时，素材库、登录、结构查看仍可用，但分析和生成不会跑。
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
