# Video Material Analysis Schema

Use these fields when writing results back to the material library.

## Item Fields

- `kind`: keep `video` for analyzed video materials.
- `technical.width`, `technical.height`: source video dimensions.
- `technical.durationMs`: duration in milliseconds.
- `technical.fps`: average frame rate.
- `technical.bitrateKbps`: approximate bitrate.
- `technical.orientation`: `portrait`, `landscape`, `square`, or `unknown`.
- `technical.hasAudio`: whether an audio stream is present.
- `technical.videoCodec`, `technical.audioCodec`: codec names from ffprobe.
- `analysisStatus`: use `ready` for directly usable clips, `analyzed` for usable but not yet ready, `hold` for manual review, `rejected` for unusable materials.
- `editRole`: one of `hook`, `try_on`, `detail`, `motion`, `transition`, `proof`, `ending`.
- `priority`: `high`, `normal`, or `low`.
- `qualityScore`: 1-5, where 5 is best.
- `aiTags`: model/rule generated retrieval tags. Preserve user-authored `tags` separately.

## Analysis Object

```json
{
  "status": "ready",
  "frameCount": 6,
  "keyframes": [
    { "timeMs": 1500, "path": "analysis/frames/video-id/frame_001.jpg", "note": "sampled keyframe" }
  ],
  "summary": "Concise editing-readiness summary.",
  "suggestions": ["Concrete editing advice."],
  "autoTags": ["AI分析", "开头钩子", "竖屏", "优先混剪"],
  "frameIndex": {
    "path": "analysis/frame-index/video-id.json",
    "mode": "ffprobe-frame-metadata",
    "totalFrames": 240,
    "indexedFrames": 240,
    "complete": true
  },
  "editingProfile": {
    "version": 2,
    "productType": "pants",
    "primaryRole": "try_on",
    "roleScores": { "try_on": 42, "detail": 18 },
    "roleCoverage": { "hook": 1, "try_on": 4, "proof": 2 },
    "recommendedUse": "primary",
    "recommendedSegmentDurationMs": 3400,
    "readinessScore": 88,
    "topSegmentIds": ["seg-001", "seg-004"],
    "copyMatchRoles": ["try_on", "detail", "proof"]
  },
  "adProfile": {
    "version": 1,
    "adScore": 88,
    "qualityTier": "A",
    "primaryStage": "hook",
    "primaryStageLabel": "开头钩子",
    "stageCoverage": { "hook": 3, "detail": 6, "try_on": 5 },
    "stageBestScores": { "hook": 92, "detail": 89 },
    "productType": "pants",
    "productSignals": ["斜扣", "牛仔", "阔腿"],
    "contentSummary": "This material is best used as a conversion ad hook/detail asset.",
    "strengths": ["存在高分广告片段，可优先进主剪"],
    "risks": ["关键帧少，转场前后需要留余量"],
    "bestSegmentIds": ["seg-001", "seg-004"],
    "recommendedTags": ["开头钩子", "广告等级A", "斜扣"]
  },
  "secondMarks": [
    {
      "second": 0,
      "startMs": 0,
      "endMs": 1000,
      "frameCount": 24,
      "keyFrames": 1,
      "avgPacketSize": 12345,
      "relativePacket": 1.22,
      "motionDelta": 0.31,
      "timelineZone": "opening",
      "brightness": 128.4,
      "contrast": 42.1,
      "sharpness": 96.5,
      "visualMotion": 18.3,
      "visualNote": "动作变化明显",
      "score": 75,
      "note": "开头信息高点，动作变化明显",
      "pros": ["帧连续，顺剪安全", "信息量明显高于全片"],
      "cons": ["缺少关键帧，转场需留余量"],
      "cutAdvice": "适合放在开头，承接第一句文案或建立商品主体。",
      "tone": "ok"
    }
  ],
  "cutHints": [
    { "startMs": 0, "endMs": 4500, "role": "hook", "confidence": 0.72, "reason": "前段适合开头钩子。" }
  ],
  "segments": [
    {
      "id": "seg-001",
      "startMs": 0,
      "endMs": 3000,
      "durationMs": 3000,
      "role": "hook",
      "adStage": "hook",
      "adStageLabel": "开头钩子",
      "score": 86,
      "confidence": 0.86,
      "reason": "3 秒智能片段；每秒均分 72.4；开头钩子。",
      "contentDescription": "适合做广告开头，用裤装画面先抓注意力；可关联卖点：斜扣、牛仔。",
      "strengths": ["高分片段，可优先进主剪", "开头抓注意力能力强"],
      "risks": ["关键帧少，转场前后需要留余量"],
      "copyAngle": "开头可用强问题/强利益点：为什么这条裤子最近主推？",
      "secondMarks": [
        { "second": 0, "startMs": 0, "endMs": 1000, "frameCount": 24, "keyFrames": 1, "avgPacketSize": 12345, "relativePacket": 1.22, "motionDelta": 0.31, "timelineZone": "opening", "brightness": 128.4, "contrast": 42.1, "sharpness": 96.5, "visualMotion": 18.3, "visualNote": "动作变化明显", "score": 75, "note": "开头信息高点，动作变化明显", "pros": ["帧连续，顺剪安全"], "cons": [], "cutAdvice": "适合放在开头，承接第一句文案或建立商品主体。", "tone": "ok" }
      ],
      "tags": ["智能切片", "开头钩子", "可混剪", "高分片段"]
    }
  ],
  "updatedAt": "2026-07-03T00:00:00Z"
}
```

## Frame Index Files

Write per-video frame metadata to `analysis/frame-index/<video-id>.json`.
The index should store ffprobe-derived records for every frame when the file is small enough, capped by `--max-frame-records` for safety:

```json
{
  "version": 1,
  "sourceUrl": "http://127.0.0.1:8794/uploads/videos/example.mp4",
  "mode": "ffprobe-frame-metadata",
  "totalFrames": 240,
  "indexedFrames": 240,
  "complete": true,
  "frames": [
    { "index": 0, "timeMs": 0, "pictType": "I", "keyFrame": true, "codedPictureNumber": 0, "packetSize": 12345 }
  ]
}
```

## Auto Edit Pool

Write machine-readable clips for downstream auto-edit skills to `data/auto-edit-pool.json`.
Only include `kind: video` items with `analysisStatus` in `ready` or `analyzed`.
Each clip should include source path, URL, manual tags, `aiTags`, technical metadata, keyframes, `frameIndex`, `adProfile`, `secondMarks`, `cutHints`, and `segments` when segment-level analysis is available.
Include `editingProfile` when available so downstream draft generators can prefer primary-use clips, match copy roles, and avoid low-readiness materials.
Include segment-level `adStage`, `contentDescription`, `strengths`, `risks`, and `copyAngle` so downstream draft generators can choose hooks, product-intro shots, detail-selling-point shots, proof clips, transitions, and CTA endings deliberately.

## Scoring Rules

- Prefer portrait and square clips for short-form ecommerce ads.
- Give high priority to clear 720p+ or 1080p+ clips between 1.5 and 60 seconds.
- Mark very short clips as `transition` unless labels suggest a stronger role.
- Mark long clips over 60 seconds as needing shot segmentation before automatic editing.
- Keep user-authored `notes` and existing business tags unless explicitly asked to rewrite them.
