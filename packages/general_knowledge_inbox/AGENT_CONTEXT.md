# AGENT CONTEXT: 通用知识与综合收藏
<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->
**Domain**: general_inbox | **Tags**: AI, 草稿鸭, 通用知识, 微信公众号, EARS, AI开源无界, 待归档
**Description**: 新收藏待归档或跨领域的综合知识资产汇总

## Structured Project Constraints & Technical Capabilities:
### Target Entity: Claude
- **Purpose**: Claude Opus 5.5是强，我看到很多代码炫酷耍帅的视频。
- **Hardware Constraints**: 标准机器配置 (4G~8G 内存即可无痛运行)
- **Runtime Environment**: Python 3.10+
- **Deployment**: 🟢 本地命令行/独立工具 (无强联网依赖)
- **Verified Advantages**: 模块解耦度高，支持无缝嵌入现有工作流; 输出带证据链追溯，结论可二次核对验证
- **Strict Pitfalls & Gotchas**: 依赖外部环境版本一致性，版本漂移可能导致调用失败; 对于超大规模复杂项目，AI 一次性分析可能出现幻觉或切分过粗

### Target Entity: REA + Reverse-skill + PentAGI
- **Purpose**: 分析我自己有权分析的软件功能
- **Hardware Constraints**: 轻量级要求: 任意主流Mac/PC (8G+内存，无需高配独立显卡)
- **Runtime Environment**: Docker 容器环境 + Node.js (>= 18) + MCP (Model Context Protocol) 插件协议客户端 + 反编译分析器 (Ghidra / IDA / Hopper)
- **Deployment**: 🟢 100% 纯本地离线运行 (无需云端依赖，数据完全私有安全)
- **Verified Advantages**: REA 社区背书极强 (GitHub 36万 Star); 比较实用的一点，是会给结论带证据，比如它看到了哪个文件、哪段代码、哪次运行结果; 会给结论带证据，比如它看到了哪个文件、哪段代码、哪次运行结果; 照着理解重写，不是抄对方的代码 [增量补充: 草稿鸭]; 有出处的解释，再帮你为自己的项目做一个类似版本 [增量补充: 草稿鸭]; 有出处的解释” [增量补充: 草稿鸭]
- **Strict Pitfalls & Gotchas**: 禁止逆向和加混淆的别碰，这玩意儿只能拿来学习使用，只复刻允许复刻的软件，没有风险; 禁止逆向，有混淆加密的，不要去做技术对抗; Node 版本不对，MCP 没挂上，Docker 起不来，目标选得太大，AI 一口气吐出一大堆分析，看着挺热闹，其实能; 加混淆的别碰，这玩意儿只能拿来学习使用，只复刻允许复刻的软件，没有风险; 容易踩的坑

### 小白看不懂的地方 [增量补充: 草稿鸭]; 痛点是：逆向/分析要用一堆工具，新手根本不知道该用哪个、怎么装 [增量补充: 草稿鸭]; 合规边界：仅限合法研究或已授权目标，禁止碰商业加混淆与加密对抗目标 [增量补充: 草稿鸭]; 依赖链繁琐：涉及多工具串联，需预先配齐 MCP 协议与指定运行时版本 [增量补充: 草稿鸭]

## Project Constraints & Directives for Agent:
1. You are operating as an expert specialist in 通用知识与综合收藏.
2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.
3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.
4. Respect the pitfalls and limitations outlined above to prevent dead ends.

## Included Sources & References:
- **REA + Reverse-skill + PentAGI复刻任何软件** (Source: https://mp.weixin.qq.com/s/dK_p1fHAQA3u-zbn5er7ZA)
- **我把 3 个 Star 过万的 Skill 串起来，搭了一条能“复刻任意软件”的流水线** (Source: https://mp.weixin.qq.com/s/bs7SwRd7GrVEiaI_ARDP0g)
- **Opus 5.5，你竟然这样做视频～！** (Source: https://mp.weixin.qq.com/s/jZwxMX9nWsD0abzrPWe0Ig)
