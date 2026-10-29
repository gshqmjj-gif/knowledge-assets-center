# AGENT CONTEXT: 端侧推理与极限显存优化 (AirLLM 70B)
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: AI科技与大模型, 本地大模型与端侧推理优化, 知识资产
**Description**: 基于权重分层加载与量化，实现消费级单卡 4GB 显存运行 70B 大模型

## Structured Project Constraints & Technical Capabilities:
### Target Entity: AirLLM：4GB 显卡跑 70B 大
- **Purpose**: 核心解决痛点: 4GB 显卡跑 70B 大模型；装上之后你的 AI 能多做什么: 4GB 显卡跑 70B 大模型，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 仅需 4GB 显存 (GTX 1650/RTX 3060/Apple Silicon Mac 皆可)，推荐高速 NVMe SSD + 32G 内存 / 运行环境: Python 3.10+ + PyTorch + CUDA / MPS 加速库
- **Runtime Environment**: 硬件要求: 仅需 4GB 显存 (GTX 1650/RTX 3060/Apple Silicon Mac 皆可)，推荐高速 NVMe SSD + 32G 内存 + 运行环境: Python 3.10+ + PyTorch + CUDA / MPS 加速库
- **Deployment**: 本地化支持: 🟢 100% 纯本地离线单机运行 (所有计算与模型权重封存于本地硬件，极致安全)
- **Verified Advantages**: 【不量化·不蒸馏·不剪枝】零精度损失，100% 保留 FP16/BF16 原始输出品质与数学严密性。; 【极致显存吞吐】实测 2.8 万亿 (2.8T) 参数超大规模模型，全过程仅占 3.72GB 显存！; 【支持微调】支持 125B 巨型模型在 6GB 显存内通过 LoRA 进行个性化下游微调。
- **Strict Pitfalls & Gotchas**: 【以时间换空间】依赖频繁的磁盘到显存流式 I/O，Token 产出速度较慢，适合离线分析、重构审计与长文归纳。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in 端侧推理与极限显存优化 (AirLLM 70B).
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **AirLLM：4GB 显卡跑 70B 大模型** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=449)
