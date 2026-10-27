# AGENT CONTEXT: AI逆向分析与软件复刻流水线
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: 逆向工程, 代码复刻, REA, PentAGI, Codex, MCP
**Description**: REA + Reverse-skill + PentAGI 自动化逆向、逻辑推演与 1:1 复刻工程流水线

## Structured Project Constraints & Technical Capabilities:
### Target Entity: REA + Reverse-skill + PentAGI
- **Purpose**: 把 REA、Reverseskill、PentAGI 这三个 Skill 搭起来以后，能做一件挺完整的事：看到一个软件功能，先让 AI 去查它是怎么实现的，再按我们自己的技术栈写一个新版本，最后在上线前帮忙找一轮安全问题
- **Hardware Constraints**: 轻量级要求: 任意主流Mac/PC (8G+内存，无需独显，轻量CPU即可)
- **Runtime Environment**: Docker 容器环境 + Node.js (>= 18) + MCP (Model Context Protocol) 插件客户端 + 反编译分析器 (Ghidra / IDA)
- **Deployment**: 🟢 本地命令行/独立工具 (无强联网依赖)
- **Verified Advantages**: 【社区验证】核心组件在 GitHub 斩获 36万 Star，能力经过广泛开源社区实战验证。; 【结论可查】推演带证据链追溯：它比较实用的一点，是会给结论带证据，比如它看到了哪个文件、哪段代码、哪次运行结果; 【干净复刻】基于行为推演重写自主版本，有效规避版权与混淆对抗风险。; 【端到端协同】从目标分析、环境依赖配齐到安全初筛，构建一体化工作流。; 【成熟生态】工具链模块解耦度高，支持快速组合并无缝嵌入现有工程流。 [补充: 草稿鸭]
- **Strict Pitfalls & Gotchas**: 【合规红线】严禁技术对抗：这一套组合下来，基本能复刻任何软件，但禁止逆向和加混淆的别碰，这玩意儿只能拿来学习使用，只复刻允许复刻的软件，没有风险; 【环境排错】多工具链依赖配置：Node 版本不对，MCP 没挂上，Docker 起不来，目标选得太大，AI 一口气吐出一大堆分析，看着挺热闹，其实能用的没几条; 【复刻边界】严禁机械抄袭：很多人看到“复刻软件”，第一反应是把别人的东西原样搬过来; 【安全界限】自动化检测仅为辅助：PentAGI 能帮忙找问题，但不能拿它当系统安全的证明

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in AI逆向分析与软件复刻流水线.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **REA + Reverse-skill + PentAGI复刻任何软件** (Source: https://mp.weixin.qq.com/s/dK_p1fHAQA3u-zbn5er7ZA)
- **我把 3 个 Star 过万的 Skill 串起来，搭了一条能“复刻任意软件”的流水线** (Source: https://mp.weixin.qq.com/s/bs7SwRd7GrVEiaI_ARDP0g)
