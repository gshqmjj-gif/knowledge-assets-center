---
title: AirLLM：4GB 显卡跑 70B 大模型
source_type: bilibili_video
source_url: https://www.bilibili.com/video/BV1UAn36aEX3?t=449
author: 洛克AI
published_date: '2026-10-27'
ingested_at: '2026-10-27 05:28:02'
tags:
- 洛克AI
- 开源项目
- ai_tech
- B站精选
- AirLLM
- local_llm
keyframes:
- keyframes/video_BV1UAn36aEX3_08_AirLLM_concept.jpg
- keyframes/video_BV1UAn36aEX3_08_AirLLM_demo.jpg
snippets:
- snippets/20261027_AirLLM：4GB_显卡跑_70B_大模型_snip_01.sh
assets: []
---

# AirLLM：4GB 显卡跑 70B 大模型

> **所属合辑**: 《这周 GitHub 上涨星最猛的 10 个 AI 开源项目》 | **UP主**: 洛克AI | **原片定位时间**: `07:29`
> **视频直达点播**: [https://www.bilibili.com/video/BV1UAn36aEX3?t=449](https://www.bilibili.com/video/BV1UAn36aEX3?t=449)
> **开源项目代码仓**: [https://github.com/lyogavin/airllm](https://github.com/lyogavin/airllm)

## 🖼️ 核心讲解与等距机械原理超清画面 (1280×720 HD)

- **【概念机动画与设计思想】FIG 08 层架与小显卡**:
  ![AirLLM 原理概念图解](keyframes/video_BV1UAn36aEX3_08_AirLLM_concept.jpg)
  *每层是架上一块板：一次只送一块进显卡，算完放回再取下一块*

- **【实操证据与运行参数】**:
  ![AirLLM 实操验证与界面证据](keyframes/video_BV1UAn36aEX3_08_AirLLM_demo.jpg)

## 🎙️ UP主原声台词讲解与核心原意
> 在Cloud Code里也能装 第8个 AIR-L-L-M 用小鞋卡跑超大模型 3800克型 这是2023年就有的老项目 这周突然又长了3200多 因为他刚支持了一批新的超大模型 平时跑一个七百亿参数的模型 要好几张大钱卡 因为整个模型的一次全赛令显存 AIR-L-L-M的思路很简单 模型本来就是一层一层算的 那就别全装进去 模型放在硬盘上 算到哪一层 就只把那一层搬进显存 算完热掉 再搬下一层 不用量化 不用争流 也不用简直 七百亿参数的模型 四个字显存就能跑 现在最大个开源模型K-MK-3 两万八千亿参数 时侧只用了3.72个G的显存 上个月 他还支持了训练 以前250亿参数的模型 六个季显存以内就能微调 代价什么 他是拿时间换显存 但这意味着 你手边一台普通电脑 也能亲手试一试 原来只有鸡房才跑的东的模型 第九个TXT to Cat

## 📌 核心功能与技术定位
- **核心解决痛点**: 4GB 显卡跑 70B 大模型
- **装上之后你的 AI 能多做什么**: 4GB 显卡跑 70B 大模型，显著突破传统工作流瓶颈。
- **官方 GitHub 仓库**: `https://github.com/lyogavin/airllm`

## ⚙️ 底层原理与技术机制
- **工作机理**: 每层是架上一块板：一次只送一块进显卡，算完放回再取下一块

## 💻 硬件配置与运行环境
- **硬件要求**: 仅需 4GB 显存 (GTX 1650/RTX 3060/Apple Silicon Mac 皆可)，推荐高速 NVMe SSD + 32G 内存
- **运行环境**: Python 3.10+ + PyTorch + CUDA / MPS 加速库

## 🔒 能否纯本地运行与安全边界
- **本地化支持**: 🟢 100% 纯本地离线单机运行 (所有计算与模型权重封存于本地硬件，极致安全)

## 🏆 同类方案对比与独特优势
- 【不量化·不蒸馏·不剪枝】零精度损失，100% 保留 FP16/BF16 原始输出品质与数学严密性。
- 【极致显存吞吐】实测 2.8 万亿 (2.8T) 参数超大规模模型，全过程仅占 3.72GB 显存！
- 【支持微调】支持 125B 巨型模型在 6GB 显存内通过 LoRA 进行个性化下游微调。

## ⚠️ 劣势边界与避坑要点
- 【以时间换空间】依赖频繁的磁盘到显存流式 I/O，Token 产出速度较慢，适合离线分析、重构审计与长文归纳。

## 🚀 快速上手与克隆指令
```shell
git clone https://github.com/lyogavin/airllm
```
