---
title: free-claude-code：用免费额度跑 Claude Code 这类编程工具
source_type: bilibili_video
source_url: https://www.bilibili.com/video/BV1UAn36aEX3?t=329
author: 洛克AI
published_date: '2026-10-27'
ingested_at: '2026-10-27 05:28:01'
tags:
- 洛克AI
- 开源项目
- ai_tech
- free-claude-code
- B站精选
- local_llm
keyframes:
- keyframes/video_BV1UAn36aEX3_06_free-claude-code_concept.jpg
- keyframes/video_BV1UAn36aEX3_06_free-claude-code_demo.jpg
snippets:
- snippets/20261027_free-claude-code：用免费额度跑_Claude_Code_这类编程工具_snip_01.sh
assets: []
---

# free-claude-code：用免费额度跑 Claude Code 这类编程工具

> **所属合辑**: 《这周 GitHub 上涨星最猛的 10 个 AI 开源项目》 | **UP主**: 洛克AI | **原片定位时间**: `05:29`
> **视频直达点播**: [https://www.bilibili.com/video/BV1UAn36aEX3?t=329](https://www.bilibili.com/video/BV1UAn36aEX3?t=329)
> **开源项目代码仓**: [https://github.com/Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code)

## 🖼️ 核心讲解与等距机械原理超清画面 (1280×720 HD)

- **【概念机动画与设计思想】FIG 06 免费模型路由器**:
  ![free-claude-code 原理概念图解](keyframes/video_BV1UAn36aEX3_06_free-claude-code_concept.jpg)
  *拦截转译 Claude 官方请求，无缝分发给 Gemini Flash / Groq / 本地 Ollama*

- **【实操证据与运行参数】**:
  ![free-claude-code 实操验证与界面证据](keyframes/video_BV1UAn36aEX3_06_free-claude-code_demo.jpg)

## 🎙️ UP主原声台词讲解与核心原意
> 上次聊到哪 他都记得 第六个 FreeCloudCode 免费用商AI编辑工具 六万八千克行 一月底见库 这周长了三千七百多 Code Codex这些编成工具 很好用 但是贵 他的做法 是在你电脑上起一个代理 把这些工具发出去的请求 转给别的模型服务商 他接了六十一家服务上 包括各家的免费额度 和起来一个月有十三一多免费头肯 也能接你本地的模型 默认用的是 因为的NIM上的模型 11种编成工具 共用一个模型目录 某一家服务掛了 他自动切到 你排好的下一个模型 这一轮对话不用从来 你甚至可以在手机上 用Telegram 或者DisCode 发一段五音 让他去洗带吧 要说清楚 他不是Enthropic官方的项目 背后跑的 也不是Cloud本身的模型 但如果你想先凌晨本 事实这类AI编成工具 这是现在门砍最低的一条路 第七个 Knowledge Work Plugins

## 📌 核心功能与技术定位
- **核心解决痛点**: 用免费额度跑 Claude Code 这类编程工具
- **装上之后你的 AI 能多做什么**: 用免费额度跑 Claude Code 这类编程工具，显著突破传统工作流瓶颈。
- **官方 GitHub 仓库**: `https://github.com/Alishahryar1/free-claude-code`

## ⚙️ 底层原理与技术机制
- **工作机理**: 拦截转译 Claude 官方请求，无缝分发给 Gemini Flash / Groq / 本地 Ollama

## 💻 硬件配置与运行环境
- **硬件要求**: 代理本身极度轻量；若运行本地大模型建议 8GB+ 显存
- **运行环境**: Node.js 18+ 或 Python 3.10+ + Claude Code CLI

## 🔒 能否纯本地运行与安全边界
- **本地化支持**: 🟡 本地网关服务 (网关运行于 127.0.0.1；若对接 Ollama 则全流程纯离线脱网)

## 🏆 同类方案对比与独特优势
- 【官方原生 CLI 体验】完美保留 Claude Code 优秀的交互体验与多工具调用生态。
- 【零账单成本开销】充分利用 Gemini 2.0 Flash 极高免费配额或 Groq 极速推理，免除昂贵 Token 费。
- 【热插拔多模型切换】可在云端免费模型与本地私有模型间秒级灵活切换。

## ⚠️ 劣势边界与避坑要点
- 【非 Anthropic 官方出品】该项目为社区逆向协议桥接器，代码理解上限取决于后端选定的模型质量。

## 🚀 快速上手与克隆指令
```shell
git clone https://github.com/Alishahryar1/free-claude-code
```
