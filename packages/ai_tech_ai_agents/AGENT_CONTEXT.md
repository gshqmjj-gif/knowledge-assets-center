# AGENT CONTEXT: ai_tech_ai_agents
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: 洛克AI, skills, 开源项目, AI科技与大模型, ai_tech, B站精选, AI视频与多模态创作, ai_agents, claude-mem, 知识资产
**Description**: ai_tech_ai_agents 相关知识沉淀与实战资产包

## Structured Project Constraints & Technical Capabilities:
### Target Entity: Claude
- **Purpose**: 核心解决痛点: 给 AI 加上跨对话的长期记忆；装上之后你的 AI 能多做什么: 给 AI 加上跨对话的长期记忆，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 轻量级无感常驻，内存占用 < 50MB / 运行环境: SQLite 3 + Python 3.9+ + Claude Code CLI
- **Runtime Environment**: 硬件要求: 轻量级无感常驻，内存占用 < 50MB + 运行环境: SQLite 3 + Python 3.9+ + Claude Code CLI
- **Deployment**: 本地化支持: 🟢 100% 本地数据库存储 (数据库保存在本地 .claude-mem，零数据上传第三方云端)
- **Verified Advantages**: 【跨会话零遗忘】无缝衔接多天甚至数周的长期研发任务，保留项目架构认知与个人编码风格。; 【极低 Token 消耗】基于本地向量检索，仅在命中上下文时按需唤醒关键片段，不污染主窗口。; 【透明可查可改】本地 SQLite 数据明文可查，支持开发者手动编辑或清洗记忆。
- **Strict Pitfalls & Gotchas**: 【重大技术栈重构需清洗】当项目发生架构大重构时，建议清理旧技术栈先验，避免陈旧记忆干扰决策。

### Target Entity: skills：让 AI 先问清楚、再写测
- **Purpose**: 核心解决痛点: 让 AI 先问清楚、再写测试的编程技能包；装上之后你的 AI 能多做什么: 让 AI 先问清楚、再写测试的编程技能包，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 标准配置 (任意现代计算机，无特殊硬件要求) / 运行环境: Claude Code / Cursor / Windsurf 编程环境
- **Runtime Environment**: 硬件要求: 标准配置 (任意现代计算机，无特殊硬件要求) + 运行环境: Claude Code / Cursor / Windsurf 编程环境
- **Deployment**: 本地化支持: 🟢 100% 本地规则注入 (纯 Markdown / Rules 规范，随项目 Git 仓库协同版本化)
- **Verified Advantages**: 【Grill-Me 反向拷问】AI 动笔前先反过来深挖需求边界与异常场景，把关键分支问清楚再写代码。; 【TDD 测试先行闭环】AI 先写一个会失败的测试亮红灯，再改代码让其变绿，每一步都有严谨反馈。; 【架构健康度体检】内置 8 项架构定期排查流程，避免代码腐化与盲目扩张。
- **Strict Pitfalls & Gotchas**: 【避免过度死板】快速原型探索阶段全量开启 TDD 和问询流程会略微增加交互轮次，推荐在生产重构时启用。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in ai_tech_ai_agents.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **claude-mem：给 AI 加上跨对话的长期记忆** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=278)
- **skills：让 AI 先问清楚、再写测试的编程技能包** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=101)
