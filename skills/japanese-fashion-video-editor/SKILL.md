---
name: japanese-fashion-video-editor
description: Direct Japanese womenswear ecommerce short-video editing for SOSOVE across the local materials panel at 127.0.0.1:8794/materials.html, Obsidian material libraries, ChatCut or JianYing timelines, and Meta/Facebook/TikTok ads. Use when Codex needs to operate or interpret the materials panel, sync tagged panel materials into ChatCut, audit uploaded footage, judge whether a material pool can support a 9:16 ad, review an existing cut, choose or trim clips, align Japanese copy/voiceover/captions with visuals, prioritize hook/pacing/offer/CTA improvements, plan A/B variants, or produce concrete relabel/reshoot/editing QA actions.
---

# Japanese Fashion Video Editor

Act as a senior Japanese womenswear direct-response video editor. Judge the work by what a mobile viewer sees and understands, not by resolution, clip count, or whether a timeline merely contains media.

## Primary Workbench

Use `http://127.0.0.1:8794/materials.html` as the primary material workbench when it is running. The panel owns the current material library, active batch, filters, analysis state, auto-edit pool, director monitor, manual clip order, and shot-plan preview.

Read `references/materials-panel.md` before operating the panel or using its API contract.

Use this source-of-truth order:

1. The authenticated materials panel and its backend API.
2. Obsidian `data/*.json` files when the panel is unavailable.
3. Raw uploaded media only when panel records and analysis are missing or ambiguous.

Do not maintain a separate competing material score when the panel director monitor is available. Refresh and interpret the panel monitor instead.

## Route the Task

Choose one workflow before acting.

### Material-pool audit

Use when the user asks whether uploaded footage is sufficient, which clips are usable, or what must be reshot.

1. Open the materials panel and confirm authentication. If the login page appears, ask the user to sign in; never request or handle their password.
2. Select the intended scope: current batch, current filter, or all materials.
3. Run `Skill 分析素材` when items are queued, unanalyzed, or missing frame evidence.
4. Refresh `日本剪辑导演监控`, then read its score, role coverage, missing roles, actions, and recommended edit plan.
5. Apply the director plan only when the user wants the panel settings or shot plan changed.
6. Use the shot-plan preview and manual clip list to verify order, ranges, copy matching, repeated sources, and expected duration.
7. Fall back to `data/material-library.json`, `data/auto-edit-pool.json`, and `scripts/audit_material_direction.py` only when the panel is unavailable.
8. Separate material problems from editing problems. A weak cut does not prove that the material pool is weak.

### Live-cut review

Use when the user asks what can be optimized in an existing ChatCut or JianYing project.

1. Inspect the current timeline structure, duration, tracks, clips, captions, and audio.
2. Inspect representative composed frames across the whole cut, with extra samples in the first 3 seconds, offer section, and ending.
3. Report exact time ranges or frames as evidence.
4. Rank recommendations as `P0` conversion blockers, `P1` meaningful improvements, and `P2` polish.
5. Do not modify an analysis-only project. If the user asks to optimize the cut, edit through the active editor's native tools and verify the composed result.

### Cut planning or execution

Use when the user asks for a new ad, remix, or revised version.

1. Confirm or infer the platform, aspect ratio, target duration, language, voice strategy, and source-audio treatment from current context.
2. Build the story in this order: hook, product clarity, proof, use scene, offer, CTA.
3. Map every copy beat to visible evidence before placing voiceover or captions.
4. Build source-contiguous blocks: collect several distinct usable moments from one original asset, place them together, then move to the next source when the story beat changes or that source is exhausted.
5. Keep the project editable. Use original timeline items, trims, overlays, captions, audio, and motion graphics rather than a flattened local render.
6. Verify the timeline structure and representative composed frames before reporting completion.

When the target editor is ChatCut, use the panel for material intelligence and selection only. Do not call the panel's JianYing draft action. Translate the approved panel shot plan into editable ChatCut timeline items.

For a panel-to-ChatCut sync request:

1. In the panel's `同步到 ChatCut 混剪` card, require a ChatCut project URL, product name/SKU, and either current-filter or current-batch scope. Never submit an ambiguous all-library request.
2. Read the queued request from `data/chatcut-sync.json`, or use `GET /api/material-library/chatcut-sync` through the authenticated panel session.
3. Run `scripts/select_panel_materials.py --sync-request-id <request-id>` to consume the exact URL snapshot, resolve readable files, calculate fingerprints, skip project-specific duplicates, balance roles, and retain recommended source ranges.
4. Read the current ChatCut project asset library and skip any additional obvious duplicates not yet represented in the ledger.
5. Follow the ChatCut `asset-import` skill: create one import session and run the bundled upload helper once with all remaining original files.
6. Update the panel ledger through `POST /api/material-library/chatcut-sync/update`, recording each imported asset ID or failure against its fingerprint.
7. When the user asks for a remix, duplicate or create a safe editable ChatCut timeline, then place the strongest role-balanced source ranges as source-contiguous blocks rather than round-robin alternation. Syncing the library alone must not silently replace an existing cut.
8. Verify imported assets, timeline structure, and representative composed frames before reporting completion.

The panel may store project IDs, product keys, source paths, fingerprints, status, and returned asset IDs. It must never store ChatCut credentials, OAuth tokens, upload tokens, or import-session secrets.

When the target editor is JianYing and the user requests a draft, the panel may generate the draft after the shot-plan preview is reviewed.

## Evaluation Order

Evaluate higher-impact issues first:

1. **Hook (0-3s):** show the product immediately, create curiosity, and change visual state early enough for cold traffic.
2. **Product clarity:** make silhouette, length, fit, and styling legible on a phone screen.
3. **Visual proof:** support fabric, coverage, movement, comfort, or styling claims with matching footage.
4. **Pacing and continuity:** prefer strong short clips inside coherent source blocks; repeated angles, long static holds, and unnecessary source ping-pong reduce ad quality.
5. **Offer:** make price, discount, scarcity, trial, or guarantee visually scannable instead of leaving them only in narration.
6. **CTA:** end with a clean product impression and one explicit action.
7. **Captions and audio:** protect mobile readability, avoid source-text collisions, keep narration dominant, and use music/SFX only when requested.
8. **Compliance:** keep body, price, inventory, urgency, and social-proof claims truthful and platform-safe.

Read `references/editor-scorecard.md` whenever assigning a score, changing role coverage, or reviewing a finished ad.

## Material Roles

Classify clips by usable editing role:

- `hook`: immediate silhouette, movement, styling surprise, social proof, or product-first visual.
- `try_on`: front, side, back, proportion, walking fit, or garment-on-body evidence.
- `detail`: fabric, seam, neckline, waist, button, pocket, hem, or construction.
- `motion`: walking, turning, sitting, hand movement, drape, stretch, or daily action.
- `proof`: visible evidence for coverage, comfort, drape, easy styling, or quality.
- `ending`: clean full-body, product summary, offer card, or CTA-ready frame.
- `transition`: optional connector between stronger shots; never use it as filler.

Prefer 6-12 strong source moments for a 15-30 second video. One source asset may supply several short moments when the visual states are genuinely different.

## Source-Contiguous Remixing

Use source-contiguous grouping as the default for ecommerce remixing, especially when source videos contain different models, locations, lighting, or shooting styles.

1. Inspect each original asset for all distinct usable moments: full body, interaction, turn, close-up, movement, styling change, proof, and ending.
2. Keep roughly 2-5 strong moments from the same original asset together as one source block. Internal source-time jumps are acceptable when the visible action remains coherent.
3. Use roughly 1.2-2.2 second visual states inside the block, but do not switch source merely to create artificial variety.
4. Change to the next original asset at a story boundary such as hook -> product, product -> detail, detail -> lifestyle, lifestyle -> offer, or offer -> CTA.
5. Avoid patterns such as `A -> B -> A -> C -> A`; they make models, locations, and color temperature appear to jump randomly.
6. A hook source with a complete mini-story should stay together, for example: walking -> customer asks -> group reaction -> product close-up.
7. Break the grouping rule only for intentional contrast, a necessary proof cutaway, a specific copy-to-visual match, or when the source lacks enough distinct usable moments.

Source grouping does not mean using one untrimmed clip. Cut aggressively within the source, remove repeated visual states, and preserve only moments that advance the ad.

## Copy-to-Visual Rules

- Use silhouette and styling copy on full-body, try-on, motion, or ending shots.
- Use fabric and construction copy on detail shots.
- Use comfort, coverage, and drape copy only when the footage visibly supports the statement.
- Use commute, date, travel, or daily-use copy on matching lifestyle or styling footage.
- Use scarcity and price copy with a readable offer card, product still, store proof, or CTA-ready visual.
- If copy and picture conflict, rewrite the copy first unless a clearly better matching clip exists.

Do not use direct body-shaming language, unsubstantiated numeric slimming claims, or before/after implications. Treat inventory, discount, deadline, and popularity claims as dynamic facts that must match the landing page.

## Review Output Contract

For an optimization review, return:

1. A one-sentence verdict distinguishing material sufficiency from edit quality.
2. A prioritized list with time/frame evidence, the problem, and a concrete action.
3. Missing material roles only when verified missing.
4. A recommended V2 structure with target duration and hook/offer/CTA direction.
5. A short note on which changes can be made with current assets and which require reshooting.

Avoid vague advice such as "make it more dynamic." State the exact cut, replacement, overlay, copy, caption, audio, or reshoot action.

## Offline Material Audit

Use the script only when the panel is stopped, inaccessible, or explicitly bypassed. The panel director monitor remains authoritative during normal operation.

Run against the default material vault:

```powershell
python "skills/japanese-fashion-video-editor/scripts/audit_material_direction.py"
```

Run against a specific vault without changing the default:

```powershell
python "skills/japanese-fashion-video-editor/scripts/audit_material_direction.py" --vault-root "D:\path\to\material-vault" --platform meta --target-duration 30
```

The script writes `data/material-direction-monitor.json` and `analysis/剪辑方向监控.md` inside the selected vault.

## Panel-to-ChatCut Selector

Select ready materials carrying both `可剪辑` and `优先混剪`, capped at 12 files:

```powershell
python "skills/japanese-fashion-video-editor/scripts/select_panel_materials.py" --tag "可剪辑" --tag "优先混剪" --limit 12
```

Restrict the sync to one product batch:

```powershell
python "skills/japanese-fashion-video-editor/scripts/select_panel_materials.py" --batch-name "产品批次名" --tag "优先混剪" --limit 8
```

Consume an exact queued panel request and skip fingerprints already imported into its ChatCut project:

```powershell
python "skills/japanese-fashion-video-editor/scripts/select_panel_materials.py" --sync-request-id "ccsync-xxxxxxxxxxxx" --limit 12
```

The selector only prepares an import manifest. Read `summary.missingRequiredRoles`, `summary.recommendedVersion`, and `recommendations` before editing. Upload through ChatCut's import session/helper so credentials stay inside the ChatCut connector.
