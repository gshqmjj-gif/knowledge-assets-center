---
title: REA：让 AI 逆向任何 App，一直拆到二进制
source_type: bilibili_video
source_url: https://www.bilibili.com/video/BV1UAn36aEX3?t=35
author: 洛克AI
published_date: '2026-10-27'
ingested_at: '2026-10-27 05:28:01'
tags:
- 洛克AI
- REA
- 开源项目
- ai_reverse
- ai_tech
- B站精选
keyframes:
- keyframes/video_BV1UAn36aEX3_01_REA_concept.jpg
- keyframes/video_BV1UAn36aEX3_01_REA_demo.jpg
snippets:
- snippets/20261027_REA：让_AI_逆向任何_App，一直拆到二进制_snip_01.sh
assets: []
---

# REA：让 AI 逆向任何 App，一直拆到二进制

> **所属合辑**: 《这周 GitHub 上涨星最猛的 10 个 AI 开源项目》 | **UP主**: 洛克AI | **原片定位时间**: `00:35`
> **视频直达点播**: [https://www.bilibili.com/video/BV1UAn36aEX3?t=35](https://www.bilibili.com/video/BV1UAn36aEX3?t=35)
> **开源项目代码仓**: [https://github.com/morluto/rea](https://github.com/morluto/rea)

## 🖼️ 核心讲解与等距机械原理超清画面 (1280×720 HD)

- **【概念机动画与设计思想】FIG 01 逆向拆解台**:
  ![REA 原理概念图解](keyframes/video_BV1UAn36aEX3_01_REA_concept.jpg)
  *四层叠在导柱上的 App，探针逐层伸进去读，旁边吐出证据纸带*

- **【实操证据与运行参数】**:
  ![REA 实操验证与界面证据](keyframes/video_BV1UAn36aEX3_01_REA_demo.jpg)

## 🎙️ UP主原声台词讲解与核心原意
> 第一个R1A全程RewardsEngineer anything 逆向一切 现在26万9千可行 他4月份才见库 工这一周就长了21万4千克 今天一天又是3万多 他活在哪 你看到别的APP里有个功能做的特别好 以前想知道他是怎么实现的 被董会变 会用反边一工具 一行一行去看 现在装上REA 跟你的AI说一句 帮我搞清楚这个APP的搜索是怎么做的 把证据给我 在在我的项目里做一个类似的 AI就会自己去拆 网业 桌面应用 一直拆到最底层的二斤制 他会调用Gitra IDA这些逆向工具 甚至调用练一路往下追 每个结论都复上证据 他们放出来的案例里 AI把一个老游戏里 计算声音左右升到的函数 还原成了CIDA 3200多组测试全部对上 便宜出来的63个字节 和原版抑谋一样 也就是说以后 你看到任何一个好功能 都可以先让AI替你把他拆开 讲明白 第二个

## 📌 核心功能与技术定位
- **核心解决痛点**: 让 AI 逆向任何 App，一直拆到二进制
- **装上之后你的 AI 能多做什么**: 让 AI 逆向任何 App，一直拆到二进制，显著突破传统工作流瓶颈。
- **官方 GitHub 仓库**: `https://github.com/morluto/rea`

## ⚙️ 底层原理与技术机制
- **工作机理**: 四层叠在导柱上的 App，探针逐层伸进去读，旁边吐出证据纸带

## 💻 硬件配置与运行环境
- **硬件要求**: 轻量级要求: 任意主流 Mac/PC (8G+内存，无需独显，轻量CPU即可)
- **运行环境**: Node.js (>= 18) + Python 3.10+ + Ghidra/IDA 反编译分析器

## 🔒 能否纯本地运行与安全边界
- **本地化支持**: 🟢 100% 本地运行 (反编译、二进制分析与比对完全离线，模型推演支持 Ollama 本地部署)

## 🏆 同类方案对比与独特优势
- 【全自动端到端证据链】每一个反推的函数均配有反编译汇编与内存调用链证据，结论可逐项溯源核对。
- 【闭环编译验证】实测老游戏声道函数复刻，3200 组单元测试全覆盖，二进制产物 63 字节完全吻合。
- 【深入最底层】不仅拆解前端网页和桌面界面，还能一路探查到底层二进制机器码。

## ⚠️ 劣势边界与避坑要点
- 【合规红线】严格限定合法学习或授权复刻，严禁对明确禁止逆向或商业加密混淆做对抗破解。
- 【复杂函数防幻觉】对极长未导出二进制函数需结合动态插桩验证，不能单凭 LLM 静态猜测。

## 🚀 快速上手与克隆指令
```shell
git clone https://github.com/morluto/rea
```
