# Hermes 知识资产中心 (Hermes Knowledge Base)

> **专为 Cursor、Codex 与 Hermes 平台 Agent 打造的私有化知识资产库与自动化创建助手**  
> 自动爬取与解析微信公众号、视频号、B站视频、技术网页、架构图片，智能拆解并聚类为结构化“知识资产包”，支持毫秒级检索并一键派发给 AI Agent 作为项目上下文参考。

---

## 🌟 核心特性与架构

```
                     [多源多模态采集输入]
   微信公众号       微信视频号        B站/视频平台       网页/技术博客       架构图/图片
       │                │                │                  │                 │
       ▼                ▼                ▼                  ▼                 ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                    Hermes Crawler Dispatcher (调度器)                            │
 └──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                         [结构化数据清洗与多模态提炼]
     ┌───────────────────────────┬───────────────────────────┐
     ▼                           ▼                           ▼
 代码片段提取 (Snippets)     关键帧无损抓拍 (Keyframes)    正文与图表清洗 (Sources & Assets)
 (自动语言识别、解耦保存)     (严格零原视频占用、免存大文件)  (Markdown转换、YAML元数据)
     └───────────────────────────┼───────────────────────────┘
                                 │
                                 ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                  Knowledge Package Manager (知识资产包聚类重组中心)               │
 │                                                                                  │
 │  packages/<package_id>/                                                          │
 │  ├── package.yaml        # 资产包元数据、标签与收录索引                          │
 │  ├── SUMMARY.md          # 聚合知识体系全景、方法论精要与关键帧画廊              │
 │  ├── AGENT_CONTEXT.md    # 专为 AI Agent 优化的高浓度上下文参考 Prompt            │
 │  ├── sources/            # 单篇结构化文档 (*.md 含 Frontmatter)                  │
 │  ├── keyframes/          # 视频核心时间轴高清截图 (*.jpg)                        │
 │  ├── snippets/           # 可复用代码块与脚本 (*.py, *.ts, *.sh)                │
 │  └── assets/             # 架构图、脑图与设计素材                                │
 └──────────────────────────────────────────────────────────────────────────────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
  [Git 自动版本跟踪]       [全库毫秒级检索]           [一键 Agent 上下文派发]
  每次录入自动生成 Commit   搜资产包/来源/代码段        Cursor (.mdc) / Codex / Hermes
```

### 1. 多源全自动采集与解析
- **微信公众号文章**: 自动提取标题、作者、发布日期、清洗 HTML 为标准 Markdown，自动剥离 code 代码块并下载关键配图。
- **微信视频号 / 短视频**: 支持分享链接或文本，提取关键帧与要点心得。
- **B站 / 视频网站 (严格规范)**:
  - **核心准则**：**坚决不保存原视频大文件**，杜绝磁盘暴涨！
  - **关键帧抓拍**：秒级抽取 4~6 张时间轴高清帧画廊，直观保留视频关键画面与参数界面。
  - **视频内容详解**：结构化提炼作者、时长、简介笔记、章节时间戳、提及的 GitHub 仓库与实操建议。
- **通用技术网页**: 智能剔除页眉页脚与广告侧边栏，支持 Zhihu、GitHub、掘金、CSDN 及独立博客。
- **图片与图表资产**: 自动识别架构图、流程图、脑图，提取分辨率与宽高比类型，归档入库。

### 2. 结构化拆分与“知识资产包”重组
- **智能聚类**：根据语义与关键词自动将知识归档至对应资产包（如 `ai_agent_architecture`、`3d_graphics_and_blender`、`frontend_engineering` 等），也支持手动指定。
- **多维拆解沉淀**：
  - 提取可复用代码至 `snippets/`
  - 提取视频关键帧至 `keyframes/`
  - 动态重构全景大纲 `SUMMARY.md` 与高浓度参考 `AGENT_CONTEXT.md`

### 3. 一键赋能 Cursor、Codex 与 Hermes
- **Cursor 模式**: 一键生成 Cursor Rule (`.cursor/rules/<pkg>.mdc` 或 `.cursorrules`)，包含工程规范与验证代码。
- **Codex 模式**: 一键生成 System Knowledge Prompt，定义领域约束与 API 结构。
- **Hermes 模式**: 一键生成专供 Hermes / Claude Code 使用的资产包知识底座。
- **一键剪贴板 (`--copy`)**: 自动调用系统 `pbcopy`，终端执行完毕即可直接 `Cmd+V` 粘贴到 Agent 对话框。

### 4. Git 原生资产版本库
- 仓库内建独立 Git 管理，每次知识录入或资产包更新自动生成标准规范的提交记录（如 `feat(kb): ingest [bilibili_video] ...`），方便回溯演进。

---

## 🚀 极速安装与配置

本系统已配置好专用的 Python 3.12 虚拟环境与核心依赖（`httpx`, `yt-dlp`, `pillow`, `fastapi`, `rich`, `typer` 等），并在本地 Git 仓库就绪。

### 环境路径配置
项目根目录：`/Users/pro/Documents/coding project/antigravity/trytry/hermes_kb`

可随时使用根目录下的 `hermes.sh` 便捷启动器：
```bash
cd "/Users/pro/Documents/coding project/antigravity/trytry/hermes_kb"
./hermes.sh --help
```

> **可选快捷命令**：可在 `~/.zshrc` 中添加别名，全局随时调用：
> ```bash
> alias hermes-kb="/Users/pro/Documents/coding\ project/antigravity/trytry/hermes_kb/hermes.sh"
> ```

---

## 🛠️ CLI 命令使用指南

### 1. 采集并录入知识 (`ingest`)
```bash
# 1. 采集微信公众号文章 (自动智能分类)
./hermes.sh ingest "https://mp.weixin.qq.com/s/your_article_url"

# 2. 采集 B站视频 (自动抽取时间轴关键帧截图，免存大体积视频)
./hermes.sh ingest "https://www.bilibili.com/video/BV1xx411c7m9"

# 3. 指定归属资产包 (例如录入到 3d_graphics_and_blender)
./hermes.sh ingest "https://github.com/trellis-3d/trellis" --package "3d_graphics_and_blender"

# 4. 采集本地图片 / 架构图
./hermes.sh ingest "/path/to/architecture_diagram.png" --package "system_architecture"
```

### 2. 从系统剪贴板一键录入 (`ingest-clip`)
在 Mac 上刷微信、B站或网页时，复制链接（`Cmd+C`）后直接执行：
```bash
./hermes.sh ingest-clip
```

### 3. 查看知识资产包全景 (`list` & `show`)
```bash
# 查看所有资产包清单
./hermes.sh list

# 深度查看指定资产包内容与关键帧明细
./hermes.sh show ai_agent_architecture
```

### 4. 全库关键词检索 (`search`)
```bash
# 检索资产包、来源正文或提取代码段
./hermes.sh search "智能体"
```

### 5. 导出并派发给 Agent (`export`)
```bash
# 导出为 Cursor Rule 并一键复制到剪贴板 (直接在 Cursor 里粘贴)
./hermes.sh export ai_agent_architecture --target cursor --copy

# 导出为 Cursor 项目规则文件 (.cursor/rules/agent.mdc)
./hermes.sh export ai_agent_architecture --target cursor --out .cursor/rules/agent.mdc

# 导出为 Codex / GPT 上下文 Prompt 并复制
./hermes.sh export ai_agent_architecture --target codex --copy

# 导出为 Hermes 知识注入包
./hermes.sh export ai_agent_architecture --target hermes --copy
```

### 6. 启动可视化 Web 控制台 (`serve`)
```bash
./hermes.sh serve --port 8765
```
打开浏览器访问 `http://127.0.0.1:8765`：
- 支持图形化粘贴 URL 快速录入
- 直观浏览视频关键帧高清画廊
- 按钮一键复制 Cursor / Codex / Hermes 上下文

### 7. 查看 Git 资产演进版本 (`git-log`)
```bash
./hermes.sh git-log
```

---

## 📁 资产包物理目录结构规范

每个资产包在物理磁盘上均保持完全开放、纯文本/标准图片、无专有数据库绑定的极简结构，天然适合 Git 同步：

```text
packages/
└── ai_agent_architecture/
    ├── package.yaml               # 资产包基础信息、标签与来源清单
    ├── SUMMARY.md                 # 聚合知识图谱、核心方法论、关键帧画廊
    ├── AGENT_CONTEXT.md           # 面向 Agent 优化的高纯度上下文 Prompt
    ├── sources/                   # 收录的各篇结构化文档 (*.md)
    │   ├── 20261026_wechat_article_xxx.md
    │   └── 20261026_bilibili_video_xxx.md
    ├── keyframes/                 # 视频时间轴关键帧截屏 (无损高清 JPG)
    │   └── video_BVxxx_cover.jpg
    ├── snippets/                  # 剥离出的即插即用代码模块 (*.py, *.sh)
    └── assets/                    # 架构原图与视觉设计素材
```
