---
title: text-to-cad：一句话生成能加工的 3D 零件
source_type: bilibili_video
source_url: https://www.bilibili.com/video/BV1UAn36aEX3?t=513
author: 洛克AI
published_date: '2026-10-27'
ingested_at: '2026-10-27 05:28:02'
tags:
- parametric_design
- 洛克AI
- 开源项目
- architecture
- B站精选
- text-to-cad
keyframes:
- keyframes/video_BV1UAn36aEX3_09_text-to-cad_concept.jpg
- keyframes/video_BV1UAn36aEX3_09_text-to-cad_demo.jpg
snippets:
- snippets/20261027_text-to-cad：一句话生成能加工的_3D_零件_snip_01.sh
assets: []
---

# text-to-cad：一句话生成能加工的 3D 零件

> **所属合辑**: 《这周 GitHub 上涨星最猛的 10 个 AI 开源项目》 | **UP主**: 洛克AI | **原片定位时间**: `08:33`
> **视频直达点播**: [https://www.bilibili.com/video/BV1UAn36aEX3?t=513](https://www.bilibili.com/video/BV1UAn36aEX3?t=513)
> **开源项目代码仓**: [https://github.com/earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad)

## 🖼️ 核心讲解与等距机械原理超清画面 (1280×720 HD)

- **【概念机动画与设计思想】FIG 09 3D打印机**:
  ![text-to-cad 原理概念图解](keyframes/video_BV1UAn36aEX3_09_text-to-cad_concept.jpg)
  *零件一层层长出来，检查灯变绿、出工程图，再装箱送去打样加工*

- **【实操证据与运行参数】**:
  ![text-to-cad 实操验证与界面证据](keyframes/video_BV1UAn36aEX3_09_text-to-cad_demo.jpg)

## 🎙️ UP主原声台词讲解与核心原意
> 第九个TXT to Cat 一句话做出能加工的零件 两万七千可行 四月下旬才见库 这个月长了四千八 这一周将近两千 以前做一个3.0件 得打开节模软件 化草图,纳身,导角,一步一步见 现在你跟AI说 给我做一个固定数媒派的之价 四个M25的螺丝孔 毕后两毫米 他就在你本地生成3.3D模型 导出 step,STL,3MF 这些标准格式 他还会做可製造性检查 看这个零件到底能不能加工出来 再出一张戴尺寸的工程图 对后还能直接连到3D打印 板金和CNC加工服务 下单把食物做出来 Clode,Codex,Cursor,Geminai 都能装 从一句话到一个拿在手里的零件 中间不需要你回见模 最后一个OpenSRE

## 📌 核心功能与技术定位
- **核心解决痛点**: 一句话生成能加工的 3D 零件
- **装上之后你的 AI 能多做什么**: 一句话生成能加工的 3D 零件，显著突破传统工作流瓶颈。
- **官方 GitHub 仓库**: `https://github.com/earthtojake/text-to-cad`

## ⚙️ 底层原理与技术机制
- **工作机理**: 零件一层层长出来，检查灯变绿、出工程图，再装箱送去打样加工

## 💻 硬件配置与运行环境
- **硬件要求**: 普通工作站或轻薄本即可无痛运行
- **运行环境**: Python 3.9+ + OpenSCAD / FreeCAD CLI 工业引擎

## 🔒 能否纯本地运行与安全边界
- **本地化支持**: 🟢 100% 本地生成与导出标准工业文件 (离线即用，完全保护商业工业构件机密)

## 🏆 同类方案对比与独特优势
- 【工业级可用格式】直接输出标准 STEP / STL / 3MF，而非不可加工的游戏低模网格。
- 【可制造性检查】自动验证壁厚、装配干涉与切削物理可行性，并自动出具带尺寸的工程图。
- 【打样闭环】支持直接连通 3D 打印、钣金冲压与 CNC 代工服务一键打样下单。

## ⚠️ 劣势边界与避坑要点
- 【复杂曲面边界】当前最擅长规则机械零件与参数化装配体；极度复杂的自由流体有机曲面仍需手工建模配合。

## 🚀 快速上手与克隆指令
```shell
git clone https://github.com/earthtojake/text-to-cad
```
