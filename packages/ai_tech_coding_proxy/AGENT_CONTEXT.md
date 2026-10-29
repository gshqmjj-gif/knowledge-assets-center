# AGENT CONTEXT: Free-Claude-Code 编程助手代理与多模型路由
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: AI科技与大模型, 编程助手代理与模型路由, 知识资产
**Description**: 本地代理拦截转译 Claude Code / Codex 请求，聚合 61 家服务商免费 Token 额度并实现自动化故障切换

## Structured Project Constraints & Technical Capabilities:
### Target Entity: Ollama + Codex + Claude
- **Purpose**: 核心解决痛点: 用免费额度跑 Claude Code 这类编程工具；装上之后你的 AI 能多做什么: 用免费额度跑 Claude Code 这类编程工具，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 代理本身极度轻量；若运行本地大模型建议 8GB+ 显存 / 运行环境: Node.js 18+ 或 Python 3.10+ + Claude Code CLI
- **Runtime Environment**: 硬件要求: 代理本身极度轻量；若运行本地大模型建议 8GB+ 显存 + 运行环境: Node.js 18+ 或 Python 3.10+ + Claude Code CLI
- **Deployment**: 本地化支持: 🟡 本地网关服务 (网关运行于 127.0.0.1；若对接 Ollama 则全流程纯离线脱网)
- **Verified Advantages**: 【官方原生 CLI 体验】完美保留 Claude Code 优秀的交互体验与多工具调用生态。; 【零账单成本开销】充分利用 Gemini 2.0 Flash 极高免费配额或 Groq 极速推理，免除昂贵 Token 费。; 【热插拔多模型切换】可在云端免费模型与本地私有模型间秒级灵活切换。
- **Strict Pitfalls & Gotchas**: 【非 Anthropic 官方出品】该项目为社区逆向协议桥接器，代码理解上限取决于后端选定的模型质量。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in Free-Claude-Code 编程助手代理与多模型路由.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **free-claude-code：用免费额度跑 Claude Code 这类编程工具** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=329)
