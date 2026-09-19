# SOSOVE Materials Panel Integration

Use this reference with the local workbench at `http://127.0.0.1:8794/materials.html`.

## Operating Principle

Treat the panel as the current source of truth for material state. Treat the skill as the editing judgment layer. Do not independently overwrite panel data from an offline audit while the panel is active.

## Authentication

- The panel redirects unauthenticated users to its login screen.
- Ask the user to sign in in the local panel when authentication is required.
- Never ask for, read, store, or submit the user's password.
- Use browser page-context requests when reading authenticated APIs so the existing session cookie is preserved.
- Do not call authenticated panel endpoints from an unauthenticated shell request and interpret the redirect or `401` response as an empty library.

## Standard Panel Workflow

1. **Choose scope**
   - Select the current batch for one product or upload session.
   - Use current filters for a curated subset.
   - Use all materials only for a library-wide audit.

2. **Check intake state**
   - Confirm video count, queued analysis, analyzed count, ready count, and hold/rejected items.
   - Relabel obvious role errors before generating a plan.

3. **Run analysis when needed**
   - Use `Skill 分析素材` for queued or new videos.
   - Use force reanalysis only when the current analysis is stale, incorrect, or missing frame evidence.
   - Wait for the analysis queue to finish before judging role coverage.

4. **Refresh director monitor**
   - Choose product-film style: `ecommerce`, `tryon`, or `detail`.
   - Refresh `日本剪辑导演监控`.
   - Read score, verdict, primary/derived role counts, missing roles, actions, recommended duration, clip count, and per-source limit.

5. **Apply or revise the plan**
   - Apply the director plan only when the user wants the panel's duration, clip limit, or copy plan changed.
   - Inspect the generated shot-plan preview before creating any editor draft.
   - Use manual clip selection to replace weak automatic choices, set source ranges, reorder moments, and remove repetition.

6. **Route to the target editor**
   - **ChatCut:** use the panel plan and selected source moments as evidence, then build the edit with original ChatCut assets and timeline items. Do not generate a JianYing draft.
   - **JianYing:** call draft generation only after the user requests it and the shot plan has been reviewed.
   - **Analysis only:** stop after reporting findings; do not apply the plan or generate a draft.

## Panel-to-ChatCut Sync

Use `scripts/select_panel_materials.py` to turn panel tags or batch scope into a deterministic ChatCut import manifest.

The manifest contains:

- readable `sourcePath`, `externalPath`, or `localPath`
- file size, modified time, and a stable file-version fingerprint
- batch and tag provenance
- editing role and analysis status
- candidate score and ad stage
- recommended source start/end milliseconds
- project-specific already-imported skips with existing ChatCut asset IDs
- missing required roles and a shorter-version recommendation when coverage is incomplete
- unresolved items that require a remote-import fallback or user action

Default safety rules:

- Sync only `ready` materials unless the user explicitly includes queued/hold items.
- Require an explicit batch, tag, or current panel filter when multiple products exist.
- Limit the first sync to 6-12 role-balanced originals.
- Deduplicate by resolved source path and skip assets already present in ChatCut.
- Block cross-batch synchronization unless the user explicitly narrows or authorizes the scope.
- Use one ChatCut import session and one helper invocation for the batch.
- Preserve original source files; never flatten or concatenate before import.
- For UNC/NAS paths, confirm the path is readable before starting ChatCut upload.
- If local transfer is denied by host policy, stop and ask the user to upload through the ChatCut media panel.

For ChatCut remixing, prefer the manifest's recommended source ranges but verify the visual moments. Order source blocks by the approved story rather than by filename or upload order. Within each story beat, keep several distinct usable moments from the same original asset together before switching sources; do not round-robin one clip from every asset.

### Request Processing Workflow

1. Read the newest `queued`, `partial`, or explicitly requested record from `data/chatcut-sync.json`.
2. Confirm that its `productKey`, `projectId`, batch, and exact URL snapshot match the user's intended product.
3. Run the selector with `--sync-request-id`; do not rebuild the scope from a broader current library view.
4. Read the current ChatCut asset library and combine that evidence with the panel fingerprint ledger.
5. Create one ChatCut import session and upload all remaining originals in one helper invocation.
6. Post per-item `syncing`, `imported`, or `failed` updates back to the panel; imported updates require `chatcutAssetId`.
7. Resume only failed or pending fingerprints on retry. A changed file gets a new fingerprint and is treated as a new source version.
8. Build or duplicate a safe editable ChatCut timeline only when remixing is requested.
9. Verify imported assets, source ranges, timeline structure, captions/audio, and representative composed frames.

Request states are `queued`, `syncing`, `partial`, `complete`, `failed`, and `blocked`. Item states are `pending`, `syncing`, `imported`, `already_imported`, `failed`, `unresolved`, and `skipped`.

## Backend API Contract

Use these endpoints through the authenticated panel session when direct structured reads are useful:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/auth/status` | Confirm authentication and role. |
| `GET` | `/api/material-library` | Read library, batches, items, and Obsidian status. |
| `GET` | `/api/material-library/auto-edit-pool` | Read analyzed candidate clips. |
| `GET` | `/api/material-library/director-monitor` | Read the current saved director monitor. |
| `GET` | `/api/material-library/chatcut-sync` | Read ChatCut sync requests and fingerprint-to-asset mappings. |
| `POST` | `/api/material-library/director-monitor` | Refresh monitor for scope/style/URLs. |
| `POST` | `/api/material-library/analyze` | Start material analysis. |
| `POST` | `/api/material-library/query` | Query materials by structured criteria. |
| `POST` | `/api/material-library/chatcut-sync/request` | Queue an exact current-filter or current-batch ChatCut sync request. |
| `POST` | `/api/material-library/chatcut-sync/update` | Record per-item import progress, returned asset IDs, and failures. |
| `POST` | `/api/material-library/jianying-draft` | Generate JianYing draft; use only with explicit user intent. |

Director-monitor request shape:

```json
{
  "scope": "current",
  "batchId": "batch-id",
  "style": "ecommerce",
  "urls": ["selected-or-filtered-material-url"]
}
```

Important monitor response fields:

- `score`, `grade`, `verdict`
- `materialCount`, `candidateCount`, `averageSmartScore`
- `roleBreakdown`, `coveredRoles`, `missingRoles`, `derivedOnlyRoles`
- `dominantRole`, `dominanceRatio`, `repeatedSources`
- `actions`
- `editingPlan.recommendedDurationSeconds`
- `editingPlan.recommendedClipCount`
- `editingPlan.maxClipsPerSource`

ChatCut sync request shape:

```json
{
  "projectUrl": "https://app.chatcut.io/zh/editor/<project-id>",
  "productKey": "SKU-or-product-name",
  "scope": "filtered",
  "statuses": ["ready"],
  "urls": ["exact-panel-material-url"],
  "filterSnapshot": {
    "filterBatchId": "batch-id",
    "filterTag": "优先混剪",
    "status": "ready",
    "role": "all",
    "search": ""
  }
}
```

ChatCut sync update shape:

```json
{
  "requestId": "ccsync-xxxxxxxxxxxx",
  "items": [
    {
      "fingerprint": "sha256-file-version-fingerprint",
      "status": "imported",
      "chatcutAssetId": "chatcut-asset-id",
      "error": ""
    }
  ]
}
```

## Data Flow

```text
uploads / NAS / remote URL
        -> materials panel library
        -> AI analysis + frame evidence
        -> auto-edit pool
        -> director monitor
        -> shot-plan preview / manual clip order
        -> ChatCut sync request + fingerprint ledger
        -> editable ChatCut timeline or JianYing draft
```

The panel persists library, candidate-pool, director-monitor, and report data into Obsidian. Avoid writing parallel versions unless performing an explicit offline recovery.

## Failure Handling

- **Panel not running:** check the local URL once, then use the offline audit script and Obsidian files.
- **Login page shown:** ask the user to sign in and resume after confirmation.
- **Empty director monitor:** confirm scope contains materials, run analysis, then refresh the monitor.
- **Candidates exist but score is weak:** inspect role distribution, derived roles, repeated sources, and smart scores before requesting more material.
- **Sync request is blocked:** inspect unresolved paths, ready status, product/SKU, and cross-batch scope before retrying.
- **Sync request is partial:** retry only pending/failed fingerprints; do not re-upload imported items.
- **Plan is good but the finished ad is weak:** diagnose the target editor timeline; this is an editing problem, not a panel material problem.
- **ChatCut task accidentally points toward JianYing generation:** stop and route the approved shot plan into ChatCut instead.
