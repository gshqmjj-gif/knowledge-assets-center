---
title: REA + Reverse-skill + PentAGI复刻任何软件
source_type: wechat_article
source_url: https://mp.weixin.qq.com/s/dK_p1fHAQA3u-zbn5er7ZA
author: 草稿鸭
published_date: '2026-10-26'
ingested_at: '2026-10-26 20:53:56'
tags:
- AI
- 草稿鸭
- 微信公众号
keyframes: []
snippets: []
assets: []
---

# 让 Codex 用这 3 个开源神器，1:1 复刻任何软件

![让 Codex 用这 3 个开源神器，1:1 复刻任何软件](https://mmbiz.qpic.cn/mmbiz_png/JdznImgLVOkP6PUfhLqW8Dr4JvdtDYPZv8a439LODSdicl68JtVUORBbyvVUQUFSFtWf5NlzQuZib5Gic771tianl41IqotPjXh8vFVs2ZgYuQk/640?wx_fmt=png)
最近 REA 在 X 刷屏了。很多人只盯着 REA，拿它去逆向软件，但是
逆向 ≠ 复刻
但是 REA + Reverse-skill + PentAGI 能接成一条完整的流水线。把它们一起交给 Codex，可以实现：看到一个喜欢的软件功能 → 搞懂它怎么实现 → 用自己的技术栈做出同样的版本 → 顺手确认它安全。

## 01📚 目录

## 02三个工具怎么配合，小白怎么复刻一个项目
不懂编程的人也可以复刻项目。复刻一个完整项目，就是把它拆成一个个小功能。逐个做出来，最后拼起来。
你要做的事是说清楚需求，再检查 AI 做出来的东西。动手的活可以交给工具。整件事分成四段，每段一个主力工具。按顺序走一遍，就能复刻一个功能。

### 三个工具的分工
先让 REA 看懂目标。你看到一个想复刻的功能，就把目标交给 REA。REA 会读对方的程序，追它的处理过程。做完这些，它会交给你一份解释。每个结论都告诉你依据在哪个文件、哪一段，你能自己去核对。
看懂之后，Reverse-skill 负责把工具备齐。REA 干活要用一堆工具，而且不同目标用的工具不一样。新手根本不知道该用哪个。Reverse-skill 会判断这次该走哪条路，缺什么工具就装什么。踩过的坑它会记下来，下次直接绕开。
接着让 Codex 写你的版本。Codex 照着 REA 那份带证据的解释，用你熟悉的工具写一个属于你的版本。这是照着理解重写，不是抄对方的代码。
最后是上线前检查。做出来的东西要上线了，先用 PentAGI 测一遍。PentAGI 是一队 AI，带着二十多种专业安全工具。它带着这些工具在隔离的环境里跑一遍。跑完会找出一批漏洞，然后给你一份报告。只是自己练手、不打算上线，这一步可以跳过。
四段走完，一个功能就复刻出来了。要上线的东西，别忘了最后一段。

### 复刻时你的操作顺序

### 小白容易踩的坑

### 小白看不懂的地方

## 03先认识这三个神器

### 1.REA：看懂“它是怎么做的”
REA 全称 Reverse Engineer Anything。它是给 Codex、Claude Code 这类 AI 编程助手用的逆向分析工具。
逆向分析是：从一个现成软件的程序和行为出发，查清某个功能是怎样实现的。它能研究网页、桌面应用和二进制程序。你看到一个喜欢的功能，让 AI 用 REA 去读取相关程序、追踪处理过程，它会给你一份有出处的解释，再帮你为自己的项目做一个类似版本。每条结论都会记录依据，方便核对。

![REA 在 GitHub 上的项目主页](https://mmbiz.qpic.cn/sz_mmbiz_png/JdznImgLVOlvXh15eLPZ1OJsciaLbiatn6HLJrIjeW2LbXXJlOKVRwcGpJJbIuXiaJmBib64K6Ne4QOY9OQlIWKcpDuI1eaOqXlDb79xlehr42U/640?wx_fmt=png)

### 2.Reverse-skill：帮 AI 自动挑工具、搭环境
Reverse-skill 是一个技能路由包，支持 Claude Code、Cursor、Cline、Kiro 等 AI 编程客户端。
它解决的痛点是：逆向/分析要用一堆工具，新手根本不知道该用哪个、怎么装。Reverse-skill 做了三件事：

![Reverse-skill 在 GitHub 上的项目主页](https://mmbiz.qpic.cn/sz_mmbiz_png/JdznImgLVOl0bXAsNtXwkv3bIzd9l3omKJlF2IEt1zeNibYPicTScm1ecDvTmvW8RZvOQwg1TFMzROticjJSsf6trHd1trhMWqUDkXAjdU0PLs/640?wx_fmt=png)

### 3.PentAGI：复刻完还要确认它安全
PentAGI 是开源的“AI 红队”。多个 AI 智能体分工：一个搜信息、一个写测试代码、一个执行，彼此沟通，最后输出一份漏洞报告，全程在 Docker 沙箱里跑。
你复刻出自己的版本后，用它测一遍，确保没留下明显的安全漏洞。

![PentAGI 在 GitHub 上的项目主页](https://mmbiz.qpic.cn/sz_mmbiz_png/JdznImgLVOkgtYfR0wYJagbmCp71kaibDjqfJzZM2NoibluSsPR5rgt1cYkrYtJY6MB1sh1sDKfpKEIAkibQmUKfrSAXgw7iaFcELrOuomUVqbg/640?wx_fmt=png)

## 04三个神器怎么配合
一次完整的“复刻”，四个角色各管一摊：

![一次完整的「复刻」，谁管哪一摊](https://mmbiz.qpic.cn/sz_mmbiz_jpg/JdznImgLVOk0Knga1lO9ibiabPibibn8eSwWazFAx3FM5BoWQvsxwicDS8HnX9C4FVnVSRStNpJict5OPxqHy48g5GwVzRshffKBs5HfEsdo3ZkwY/640?wx_fmt=jpeg)

## 05完整工作流：五步复刻一个功能
下面以“复刻某个网页的一个小功能”为例。准备阶段会用到几条命令，后面基本就是跟 Codex 聊天。

### 第 1 步 · 装好三样东西
先装好 Codex（或 Claude Code）桌面端并登录。把下面这段话直接发给 Codex，让它带你装：
我想在你（Codex）里接入两个开源工具，用来逆向分析、复刻软件功能。我不懂编程，请一步步带我，每一步说清在哪个窗口操作、要粘贴什么、成功后会看到什么。
请你：
这两个工具的官方页面，长这样：

![REA 的 README 开头，一句话说清它是干嘛的](https://mmbiz.qpic.cn/sz_mmbiz_png/JdznImgLVOkx4J42TlBqiawk9iawG7MHmrkGsWReO5m3y8n8FcJBoojHnFXiakaHW87yN9DBH4H6eFUxRVZ2vYiaNaIcUicAXTfb0weLeNZ40Ids/640?wx_fmt=png)

![Reverse-skill 的前置要求和安装命令](https://mmbiz.qpic.cn/sz_mmbiz_png/JdznImgLVOmEibxJcK6k6aGTGLDZypT9OVO8tbibZm6GIEIicd6QMk4oAjtkWibSzBr584WI7LLc2ATJWrY5V66hWjCfqfIbdT1XiaNkSYtibbBsc/640?wx_fmt=png)

### 第 2 步 · 让 REA 读懂目标功能
把下面这段发给 Codex，把【】里的内容换成你自己的：
我想搞懂【某个网页 / 软件，例如 Chrome 断网小恐龙】的【某个功能，例如障碍物为什么越来越快】是怎么实现的，之后要用我自己的技术栈做一个类似版本。
请你：

### 第 3 步 · 核对“有出处的解释”
REA 会把关键逻辑读出来，附上文件名、行号这类依据。你不用全看懂，重点确认一句话：它的结论能找到出处。想核对更细的，发这段：
请展示 REA 这次分析的 Evidence（证据）记录：你具体读了哪些文件、哪几段代码，每条结论分别基于什么。
再用一段大白话，把这个功能的实现原理讲给完全不懂编程的人听。

### 第 4 步 · 让 Codex 做出你自己的版本
确认理解没问题后，发这段让它动手。注意这是理解思路后重写，不是复制原代码：
根据上面 REA 的分析，请用【我的技术栈，例如 HTML + JS】帮我实现一个功能类似的版本。要求：

### 第 5 步 · 用 PentAGI 做安全体检
如果你复刻的是要上线的东西（尤其有后端、有表单），上线前做一次安全体检。发这段：
我用 PentAGI 给自己的这套系统做一次渗透测试（这是我自己有权测试的系统）。
请你：

![PentAGI 的系统要求和安装方式](https://mmbiz.qpic.cn/mmbiz_png/JdznImgLVOkpyibQCc3rRF1x0oiaVF3vXN1Qo4TczhiaTtPQkqSJLlGVTh30OU5ibhzqb5ibsco5JVQb2rjy2dLzLBC7rjbXN1USFFJ8YlC18BZA/640?wx_fmt=png)

## 06卡住了怎么办
遇到报错，先把“出错前的操作 + 报错原文”发给 Codex，用这个模板：
我在跟练三件套复刻功能，刚才在【终端/客户端】做了【具体操作】，出现报错：【粘贴报错】。请先解释原因，再给我下一步具体操作，说明在哪个窗口做、成功后会看到什么。我不懂编程。
几种常见情况：

![常见现象与处理](https://mmbiz.qpic.cn/sz_mmbiz_jpg/JdznImgLVOmjjZHbxwJKc8icLHyReBmdv7haalEIYF5GfM0w3dkBicHDJf382e5gXlmDTS7OetqEmmHm42LoEtakz4UvexXRAh67449J5CCibg/640?wx_fmt=jpeg)

## 07一句话总结
REA 帮你看懂，Reverse-skill 帮你调度，PentAGI 帮你体检，Codex 把它们串起来动手做。
