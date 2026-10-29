# AGENT CONTEXT: 自然语言参数化工业CAD (Text-to-CAD)
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: architecture | **Tags**: 建筑设计与空间计算, B站精选, architecture, parametric_design, 开源项目, 参数化算法与工业CAD, 知识资产, 洛克AI, text-to-cad, 微信公众号
**Description**: 一句话生成工业级可加工3D实体与尺寸工程图

## Structured Project Constraints & Technical Capabilities:
### Target Entity: text-to-cad：一句话生成能加工
- **Purpose**: 核心解决痛点: 一句话生成能加工的 3D 零件；装上之后你的 AI 能多做什么: 一句话生成能加工的 3D 零件，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 普通工作站或轻薄本即可无痛运行 / 运行环境: Python 3.9+ + OpenSCAD / FreeCAD CLI 工业引擎
- **Runtime Environment**: 硬件要求: 普通工作站或轻薄本即可无痛运行 + 运行环境: Python 3.9+ + OpenSCAD / FreeCAD CLI 工业引擎
- **Deployment**: 本地化支持: 🟢 100% 本地生成与导出标准工业文件 (离线即用，完全保护商业工业构件机密)
- **Verified Advantages**: 【工业级可用格式】直接输出标准 STEP / STL / 3MF，而非不可加工的游戏低模网格。; 【可制造性检查】自动验证壁厚、装配干涉与切削物理可行性，并自动出具带尺寸的工程图。; 【打样闭环】支持直接连通 3D 打印、钣金冲压与 CNC 代工服务一键打样下单。
- **Strict Pitfalls & Gotchas**: 【复杂曲面边界】当前最擅长规则机械零件与参数化装配体；极度复杂的自由流体有机曲面仍需手工建模配合。

### Target Entity: XPlant2.0
- **Purpose**: 围绕 XPlant2.0 打造的全自动化逻辑推演与工程实现工作流
- **Hardware Constraints**: 标准机器配置 (8G 内存即可无痛运行)
- **Runtime Environment**: 跨平台标准环境 (支持 macOS / Linux / Windows)
- **Deployment**: 🟢 本地命令行/独立工具 (无强联网依赖)
- **Verified Advantages**: 【成熟生态】工具链模块解耦度高，支持快速组合并无缝嵌入现有工程流。; 【透明推演】输出具备完整的上下文依据与调用日志，结论可二次逐项核对。; 【能力突破】针对特定业务痛点提供显著效率提升与流程优化。; 【端到端协同】从目标分析、环境依赖配齐到成果交付，构建一体化工作流。
- **Strict Pitfalls & Gotchas**: 【合规红线】严格限定合法学习或授权复刻，遵守开源许可与数据安全规范。; 【环境排错】涉及多工具串联，遇到报错应保留完整日志并逐项单点排查，切忌全量同时修改。; 【复刻边界】切忌盲目原样搬运；核心在于摸清行为逻辑后独立自研重写。; 【安全界限】自动化工具仅提供初步分析，复杂业务逻辑与生产环境仍需人工专项复核。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in 自然语言参数化工业CAD (Text-to-CAD).
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **XPlant2.0** (Source: https://mp.weixin.qq.com/s/azWKal9TNsvoXm6RqXyaLw)
- **text-to-cad：一句话生成能加工的 3D 零件** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=513)
