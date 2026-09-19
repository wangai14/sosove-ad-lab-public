---
name: video-material-analyzer
description: Analyze uploaded video materials for AI editing readiness from the user's Obsidian material vault. Use when the user asks to analyze uploaded materials, uploaded videos, sync uploads into the material library, 抽帧, 分析素材, 视频素材分析, 判断剪辑用途, 给后期自动剪辑建议, 写回 Obsidian, or update the AI editing material library.
---

# Video Material Analyzer

## Core Workflow

Use this skill to turn uploaded assets into structured editing intelligence for the Seedance material library.

1. Locate the material vault from `SEEDANCE_OBSIDIAN_MATERIAL_ROOT`, or default to `<repository>/material-vault` when the variable is not set.
2. Scan `uploads/images`, `uploads/videos`, and `uploads/audios` and register missing files into `data/material-library.json` before analysis.
3. Select video items with `kind: video` and `analysisStatus` in `queued`, `hold`, or `analyzing` unless the user requests `--force`.
4. Run `scripts/analyze_uploaded_videos.py` to extract media metadata, sample video frames, generate first-pass editing recommendations, update the library JSON, and write Obsidian analysis notes.
5. Generate frame-level metadata under `analysis/frame-index/` and a downstream auto-edit pool at `data/auto-edit-pool.json`.
6. If the user needs creative judgment, inspect generated keyframes under `analysis/frames/` and refine `analysis.summary`, `analysis.suggestions`, `editRole`, `qualityScore`, `priority`, `aiTags`, and `analysisStatus`.
7. Keep final data in Obsidian, not only in chat. The material library JSON, video notes, frame indexes, auto-edit pool, frames, and run summary are the source of truth.

## Quick Commands

Sync uploads and analyze queued videos:

```powershell
python "skills/video-material-analyzer/scripts/analyze_uploaded_videos.py"
```

Preview what would sync/analyze without writing changes:

```powershell
python "skills/video-material-analyzer/scripts/analyze_uploaded_videos.py" --dry-run
```

Only sync `uploads/` files into the material library, without video analysis:

```powershell
python "skills/video-material-analyzer/scripts/analyze_uploaded_videos.py" --sync-only
```

Re-run all videos, including already analyzed or ready videos:

```powershell
python "skills/video-material-analyzer/scripts/analyze_uploaded_videos.py" --force
```

Use a specific vault root:

```powershell
python "skills/video-material-analyzer/scripts/analyze_uploaded_videos.py" --vault-root "D:\path\to\material-vault"
```

## Output Contract

The analyzer writes these fields back to each synced video material:

- `technical`: resolution, duration, fps, bitrate, orientation, codec, and audio-track presence.
- `analysisStatus`: `ready`, `analyzed`, `hold`, or `rejected` depending on usability.
- `editRole`: likely editing use such as `hook`, `try_on`, `detail`, `motion`, `transition`, `proof`, `bgm`, or `ending`.
- `priority`: `high`, `normal`, or `low`.
- `qualityScore`: integer 1-5.
- `aiTags`: generated retrieval tags used by the auto-edit skill, separate from manual `tags`.
- `analysis`: summary, suggestions, sampled keyframes, frame count, autoTags, frameIndex, adProfile, secondMarks, cutHints, segments, and updated timestamp.
- `analysis.adProfile`: conversion-ad material profile with ad stage, ad score, quality tier, product signals, strengths, risks, and recommended tags.
- `analysis.segments[]`: smart clips with `adStage`, `contentDescription`, `strengths`, `risks`, and `copyAngle` for hook/product-intro/detail/proof/CTA retrieval.

The script also writes:

- Per-video notes to `analysis/videos/*.md`.
- Sampled frames to `analysis/frames/<video-id>/frame_*.jpg`.
- Per-frame metadata to `analysis/frame-index/<video-id>.json`.
- Auto-edit retrieval pool to `data/auto-edit-pool.json`.
- A run summary to `analysis/素材分析运行记录.md`.

Read `references/analysis-schema.md` before changing field names, scoring rules, or markdown output format.

## Visual Review Guidance

The script is deterministic and conservative. For nuanced video advice, use the sampled frames it creates:

1. Open representative files in `analysis/frames/<video-id>/`.
2. Judge visual content: product visibility, model motion, camera stability, hook strength, detail clarity, and transition usefulness.
3. Update the material's `analysis.summary` and `analysis.suggestions` with concrete editing advice.
4. Prefer practical edit labels over vague descriptions: opening hook, try-on display, detail close-up, motion shot, transition, proof, ending.

Do not overwrite user tags or notes unless the user asks. Add analysis tags only when they help retrieval.
