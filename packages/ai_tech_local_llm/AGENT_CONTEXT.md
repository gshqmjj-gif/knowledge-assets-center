# AGENT CONTEXT: ai_tech_local_llm
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: 洛克AI, 开源项目, AI科技与大模型, 本地大模型与端侧推理优化, ai_tech, free-claude-code, B站精选, AirLLM, 知识资产, local_llm
**Description**: ai_tech_local_llm 相关知识沉淀与实战资产包

## Structured Project Constraints & Technical Capabilities:
### Target Entity: AirLLM：4GB 显卡跑 70B 大
- **Purpose**: 核心解决痛点: 4GB 显卡跑 70B 大模型；装上之后你的 AI 能多做什么: 4GB 显卡跑 70B 大模型，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 仅需 4GB 显存 (GTX 1650/RTX 3060/Apple Silicon Mac 皆可)，推荐高速 NVMe SSD + 32G 内存 / 运行环境: Python 3.10+ + PyTorch + CUDA / MPS 加速库
- **Runtime Environment**: 硬件要求: 仅需 4GB 显存 (GTX 1650/RTX 3060/Apple Silicon Mac 皆可)，推荐高速 NVMe SSD + 32G 内存 + 运行环境: Python 3.10+ + PyTorch + CUDA / MPS 加速库
- **Deployment**: 本地化支持: 🟢 100% 纯本地离线单机运行 (所有计算与模型权重封存于本地硬件，极致安全)
- **Verified Advantages**: 【不量化·不蒸馏·不剪枝】零精度损失，100% 保留 FP16/BF16 原始输出品质与数学严密性。; 【极致显存吞吐】实测 2.8 万亿 (2.8T) 参数超大规模模型，全过程仅占 3.72GB 显存！; 【支持微调】支持 125B 巨型模型在 6GB 显存内通过 LoRA 进行个性化下游微调。
- **Strict Pitfalls & Gotchas**: 【以时间换空间】依赖频繁的磁盘到显存流式 I/O，Token 产出速度较慢，适合离线分析、重构审计与长文归纳。

### Target Entity: Ollama + Codex + Claude
- **Purpose**: 核心解决痛点: 用免费额度跑 Claude Code 这类编程工具；装上之后你的 AI 能多做什么: 用免费额度跑 Claude Code 这类编程工具，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 代理本身极度轻量；若运行本地大模型建议 8GB+ 显存 / 运行环境: Node.js 18+ 或 Python 3.10+ + Claude Code CLI
- **Runtime Environment**: 硬件要求: 代理本身极度轻量；若运行本地大模型建议 8GB+ 显存 + 运行环境: Node.js 18+ 或 Python 3.10+ + Claude Code CLI
- **Deployment**: 本地化支持: 🟡 本地网关服务 (网关运行于 127.0.0.1；若对接 Ollama 则全流程纯离线脱网)
- **Verified Advantages**: 【官方原生 CLI 体验】完美保留 Claude Code 优秀的交互体验与多工具调用生态。; 【零账单成本开销】充分利用 Gemini 2.0 Flash 极高免费配额或 Groq 极速推理，免除昂贵 Token 费。; 【热插拔多模型切换】可在云端免费模型与本地私有模型间秒级灵活切换。
- **Strict Pitfalls & Gotchas**: 【非 Anthropic 官方出品】该项目为社区逆向协议桥接器，代码理解上限取决于后端选定的模型质量。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in ai_tech_local_llm.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **AirLLM：4GB 显卡跑 70B 大模型** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=449)
- **free-claude-code：用免费额度跑 Claude Code 这类编程工具** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=329)
