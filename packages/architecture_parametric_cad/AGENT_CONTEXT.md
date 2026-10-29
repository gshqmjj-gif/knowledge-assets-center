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
- **Purpose**: 面向山地景观规划与参数化种植设计的 Rhino／Grasshopper 工具平台，将地形分析、现状评价、专项设计和成果输出整合为可连接、可复用的组件体系。
- **Hardware Constraints**: 常规设计工作站 (建议 16G 内存 + 独立显卡)
- **Runtime Environment**: Rhino / Grasshopper 平台 + 空间分析/GIS 插件组件
- **Deployment**: 🟢 纯本地离线运行 (基于本地 Rhino/Grasshopper 本地计算与离线 Mesh 分析)
- **Verified Advantages**: 【多模态空间数据输入】支持测绘高程点、等高线、地形 Mesh、土地利用及外部模型数据，建立从空间分析到方案生成完整流程。; 【全专项功能组件覆盖】覆盖总体规划、山地植物设计、生态修复、海绵雨洪、水库堰塞湖安全、道路游线、建筑设施选址、边坡地质安全、土方竖向等。; 【设计依据量化可追溯】把复杂地形转化为量化分析结果，直接驱动分区、选址、路径组织和种植配置，支持多方案迭代。
- **Strict Pitfalls & Gotchas**: 【当前版本边界】当前处于 DEMO 版本阶段，仍处于持续演进与功能完善中。; 【工程安全规划筛查】工程安全类工具主要服务于规划阶段筛查，专业深入设计需衔接专业工程力学模型验证。

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in 自然语言参数化工业CAD (Text-to-CAD).
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **XPlant2.0** (Source: https://mp.weixin.qq.com/s/azWKal9TNsvoXm6RqXyaLw)
- **text-to-cad：一句话生成能加工的 3D 零件** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=513)
