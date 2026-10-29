---
title: claude-mem：给 AI 加上跨对话的长期记忆
source_type: bilibili_video
source_url: https://www.bilibili.com/video/BV1UAn36aEX3?t=278
author: 洛克AI
published_date: '2026-10-27'
ingested_at: '2026-10-27 05:28:01'
tags:
- 洛克AI
- 开源项目
- ai_tech
- B站精选
- ai_agents
- claude-mem
keyframes:
- keyframes/video_BV1UAn36aEX3_05_claude-mem_concept.jpg
- keyframes/video_BV1UAn36aEX3_05_claude-mem_demo.jpg
snippets:
- snippets/20261027_claude-mem：给_AI_加上跨对话的长期记忆_snip_01.sh
assets: []
---

# claude-mem：给 AI 加上跨对话的长期记忆

> **所属合辑**: 《这周 GitHub 上涨星最猛的 10 个 AI 开源项目》 | **UP主**: 洛克AI | **原片定位时间**: `04:38`
> **视频直达点播**: [https://www.bilibili.com/video/BV1UAn36aEX3?t=278](https://www.bilibili.com/video/BV1UAn36aEX3?t=278)
> **开源项目代码仓**: [https://github.com/thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)

## 🖼️ 核心讲解与等距机械原理超清画面 (1280×720 HD)

- **【概念机动画与设计思想】FIG 05 记忆回转柜**:
  ![claude-mem 原理概念图解](keyframes/video_BV1UAn36aEX3_05_claude-mem_concept.jpg)
  *对话结束自动归档入柜，新对话自动检索唤醒历史上下文与项目偏好*

- **【实操证据与运行参数】**:
  ![claude-mem 实操验证与界面证据](keyframes/video_BV1UAn36aEX3_05_claude-mem_demo.jpg)

## 🎙️ UP主原声台词讲解与核心原意
> 给你做一个心体材的 第五个Code,MEM 给AI家长期记忆 十万一千克型 他是去年八月就有的老项目 这个月长了七千多 这一周三千多 用AI寫过代码的都知道 开一个心对话 他就全忘了 昨天修过的八个 定好的方案 你得从头再讲一遍 Cloud温 会在后台订阵AI每次 用了什么工具 改了什么 自动记下来 再用AI压缩成一条条材料 存进本地数据库 下次开心对话 他不是把所有东西 一股脑塞回去 而是先查所引 挑出相关的几条 需要了 再去细节 官方说 这样大概能省十倍的头肯 CloudCode Codex Geminai OpenCode 都能装 装上以后 你的AI就像一个 一直跟着这个项目的老同事 上次聊到哪 他都记得 第六个

## 📌 核心功能与技术定位
- **核心解决痛点**: 给 AI 加上跨对话的长期记忆
- **装上之后你的 AI 能多做什么**: 给 AI 加上跨对话的长期记忆，显著突破传统工作流瓶颈。
- **官方 GitHub 仓库**: `https://github.com/thedotmack/claude-mem`

## ⚙️ 底层原理与技术机制
- **工作机理**: 对话结束自动归档入柜，新对话自动检索唤醒历史上下文与项目偏好

## 💻 硬件配置与运行环境
- **硬件要求**: 轻量级无感常驻，内存占用 < 50MB
- **运行环境**: SQLite 3 + Python 3.9+ + Claude Code CLI

## 🔒 能否纯本地运行与安全边界
- **本地化支持**: 🟢 100% 本地数据库存储 (数据库保存在本地 .claude-mem，零数据上传第三方云端)

## 🏆 同类方案对比与独特优势
- 【跨会话零遗忘】无缝衔接多天甚至数周的长期研发任务，保留项目架构认知与个人编码风格。
- 【极低 Token 消耗】基于本地向量检索，仅在命中上下文时按需唤醒关键片段，不污染主窗口。
- 【透明可查可改】本地 SQLite 数据明文可查，支持开发者手动编辑或清洗记忆。

## ⚠️ 劣势边界与避坑要点
- 【重大技术栈重构需清洗】当项目发生架构大重构时，建议清理旧技术栈先验，避免陈旧记忆干扰决策。

## 🚀 快速上手与克隆指令
```shell
git clone https://github.com/thedotmack/claude-mem
```
