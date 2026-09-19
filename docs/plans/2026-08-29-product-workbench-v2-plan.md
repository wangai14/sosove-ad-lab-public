# Product Workbench V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为通用商品提示词工坊增加品类专用字段、参考图一致性、还原度评分、平台预设和版本历史。

**Architecture:** 保持当前无构建 HTML/CSS/JavaScript 前端和 Python HTTP 服务。新增数据继续通过现有分析、生成和优化 API 传递；一致性复用视觉分析调用，还原度由服务端确定性评分，历史只存浏览器 localStorage。

**Tech Stack:** Python 3、标准库 HTTP 服务、原生 HTML/CSS/JavaScript、unittest/pytest。

---

### Task 1: 固定数据契约与失败测试

**Files:**
- Modify: `seedance_web/tests/test_fashion_prompt_analysis.py`
- Modify: `seedance_web/tests/test_fashion_prompts_page.py`

**Steps:**
1. 写出品类字段、平台预设、一致性报告、还原评分和历史 UI 的失败测试。
2. 运行两个目标测试文件，确认新断言失败。

### Task 2: 品类专用字段与平台预设

**Files:**
- Modify: `seedance_web/static/fashion-prompts.html`
- Modify: `seedance_web/static/fashion-prompts.css`
- Modify: `seedance_web/static/fashion-prompts.js`
- Modify: `seedance_web/server.py`

**Steps:**
1. 增加动态品类字段容器和平台预设选择/说明卡。
2. 建立白名单 schema 和平台策略，完成切换、保存、恢复及旧数据兼容。
3. 把 `categoryDetails`、`platformPreset` 和 `platformStrategy` 写入商品档案、公共商品锁和 AI 上下文。
4. 运行页面和服务端目标测试。

### Task 3: 参考图一致性预检

**Files:**
- Modify: `seedance_web/static/fashion-prompts.html`
- Modify: `seedance_web/static/fashion-prompts.css`
- Modify: `seedance_web/static/fashion-prompts.js`
- Modify: `seedance_web/server.py`
- Modify: `seedance_web/tests/test_fashion_prompt_analysis.py`

**Steps:**
1. 扩展视觉分析 JSON，规范化一致性状态、冲突和单维权威来源。
2. 在参考图区渲染状态、分数、冲突和建议。
3. 参考变更后使报告过期；多图生成时自动检查，严重冲突停止生成。
4. 将已确认报告传入生成上下文。
5. 运行一致性单元测试。

### Task 4: 商品还原度评分

**Files:**
- Modify: `seedance_web/server.py`
- Modify: `seedance_web/static/fashion-prompts.html`
- Modify: `seedance_web/static/fashion-prompts.css`
- Modify: `seedance_web/static/fashion-prompts.js`
- Modify: `seedance_web/tests/test_fashion_prompt_analysis.py`

**Steps:**
1. 实现七维确定性提示词评分与修复建议。
2. 生成、精修接口返回评分；前端展示总分、维度和“预测分”边界。
3. 补充高分、缺颜色、参考冲突的测试。

### Task 5: 本地版本历史与比较

**Files:**
- Modify: `seedance_web/static/fashion-prompts.html`
- Modify: `seedance_web/static/fashion-prompts.css`
- Modify: `seedance_web/static/fashion-prompts.js`
- Modify: `seedance_web/tests/test_fashion_prompts_page.py`

**Steps:**
1. 增加最多 12 个快照的本地存储读写和容量降级。
2. 成功生成、精修后自动存版本。
3. 实现版本列表、双版本设置/提示词差异比较和恢复。
4. 恢复时清除不可恢复的图片文件并明确提示重新绑定。

### Task 6: 集成验证与服务重启

**Files:**
- Verify: `seedance_web/static/fashion-prompts.js`
- Verify: `seedance_web/tests`

**Steps:**
1. 运行 `node --check seedance_web/static/fashion-prompts.js`。
2. 运行两个目标测试文件。
3. 运行 `python -m pytest seedance_web/tests -q`，预期全部通过。
4. 只停止命令行为 `seedance_web.server --port 8794` 的旧进程并隐藏启动新进程。
5. 验证登录页和 8794 监听状态；鉴权后的视觉检查由当前登录会话完成。

> 工作区当前包含大量不属于本功能的现有变更，计划不创建提交，避免误收用户文件。
