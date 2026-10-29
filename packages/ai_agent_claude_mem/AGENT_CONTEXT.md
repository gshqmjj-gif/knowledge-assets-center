# AGENT CONTEXT: Claude-Mem 智能体跨对话长期记忆库
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: AI科技与大模型, 智能体长期记忆与上下文, 知识资产
**Description**: 为 AI 编程与交互智能体赋予跨会话、跨生命周期的长期记忆与上下文精准语义召回

## Structured Project Constraints & Technical Capabilities:
### Target Entity: Claude
- **Purpose**: 核心解决痛点: 给 AI 加上跨对话的长期记忆；装上之后你的 AI 能多做什么: 给 AI 加上跨对话的长期记忆，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 轻量级无感常驻，内存占用 < 50MB / 运行环境: SQLite 3 + Python 3.9+ + Claude Code CLI
- **Runtime Environment**: 硬件要求: 轻量级无感常驻，内存占用 < 50MB + 运行环境: SQLite 3 + Python 3.9+ + Claude Code CLI
- **Deployment**: 本地化支持: 🟢 100% 本地数据库存储 (数据库保存在本地 .claude-mem，零数据上传第三方云端)
- **Verified Advantages**: 【跨会话零遗忘】无缝衔接多天甚至数周的长期研发任务，保留项目架构认知与个人编码风格。; 【极低 Token 消耗】基于本地向量检索，仅在命中上下文时按需唤醒关键片段，不污染主窗口。; 【透明可查可改】本地 SQLite 数据明文可查，支持开发者手动编辑或清洗记忆。
- **Strict Pitfalls & Gotchas**: 【重大技术栈重构需清洗】当项目发生架构大重构时，建议清理旧技术栈先验，避免陈旧记忆干扰决策。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in Claude-Mem 智能体跨对话长期记忆库.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **claude-mem：给 AI 加上跨对话的长期记忆** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=278)
