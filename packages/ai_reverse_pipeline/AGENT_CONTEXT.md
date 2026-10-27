# AGENT CONTEXT: AI逆向分析与软件复刻流水线
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: ai_tech | **Tags**: 洛克AI, REA, 开源项目, ai_reverse, 逆向工程, Codex, ai_tech, MCP, 代码复刻, B站精选, PentAGI
**Description**: REA + Reverse-skill + PentAGI 自动化逆向、逻辑推演与 1:1 复刻工程流水线

## Structured Project Constraints & Technical Capabilities:
### Target Entity: REA
- **Purpose**: 核心解决痛点: 让 AI 逆向任何 App，一直拆到二进制；装上之后你的 AI 能多做什么: 让 AI 逆向任何 App，一直拆到二进制，显著突破传统工作流瓶颈。
- **Hardware Constraints**: 硬件要求: 轻量级要求: 任意主流 Mac/PC (8G+内存，无需独显，轻量CPU即可) / 运行环境: Node.js (>= 18) + Python 3.10+ + Ghidra/IDA 反编译分析器
- **Runtime Environment**: 硬件要求: 轻量级要求: 任意主流 Mac/PC (8G + 内存，无需独显，轻量CPU即可) + 运行环境: Node.js (>= 18) + Python 3.10 + Ghidra/IDA 反编译分析器 + Docker 容器环境 + MCP (Model Context Protocol) 插件客户端 + 反编译分析器 (Ghidra / IDA)
- **Deployment**: 本地化支持: 🟢 100% 本地运行 (反编译、二进制分析与比对完全离线，模型推演支持 Ollama 本地部署)
- **Verified Advantages**: 【全自动端到端证据链】每一个反推的函数均配有反编译汇编与内存调用链证据，结论可逐项溯源核对。; 【闭环编译验证】实测老游戏声道函数复刻，3200 组单元测试全覆盖，二进制产物 63 字节完全吻合。; 【深入最底层】不仅拆解前端网页和桌面界面，还能一路探查到底层二进制机器码。; 【成熟生态】工具链模块解耦度高，支持快速组合并无缝嵌入现有工程流。 [补充: 草稿鸭]; 【结论可查】推演带证据链追溯：Codex 照着 REA 那份带证据的解释，用你熟悉的工具写一个属于你的版本 [补充: 草稿鸭]
- **Strict Pitfalls & Gotchas**: 【合规红线】严格限定合法学习或授权复刻，严禁对明确禁止逆向或商业加密混淆做对抗破解。; 【复杂函数防幻觉】对极长未导出二进制函数需结合动态插桩验证，不能单凭 LLM 静态猜测。; 【环境排错】多工具链依赖配置：Reverseskill 会判断这次该走哪条路，缺什么工具就装什么 [补充: 草稿鸭]; 【复刻边界】切忌盲目原样搬运；核心在于摸清行为逻辑后独立自研重写。 [补充: 草稿鸭]; 【安全界限】自动化工具仅提供初步分析，复杂业务逻辑与生产环境仍需人工专项复核。 [补充: 草稿鸭]

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in AI逆向分析与软件复刻流水线.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **REA：让 AI 逆向任何 App，一直拆到二进制** (Source: https://www.bilibili.com/video/BV1UAn36aEX3?t=35)
- **REA + Reverse-skill + PentAGI复刻任何软件** (Source: https://mp.weixin.qq.com/s/dK_p1fHAQA3u-zbn5er7ZA)
- **我把 3 个 Star 过万的 Skill 串起来，搭了一条能“复刻任意软件”的流水线** (Source: https://mp.weixin.qq.com/s/bs7SwRd7GrVEiaI_ARDP0g)
