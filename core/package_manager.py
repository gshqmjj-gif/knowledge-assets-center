"""
Knowledge Asset Package Manager (知识资产包管理与聚类重组中心)
负责：资产包创建、智能归类、同类知识合并拆解、代码提炼与知识脉络更新
"""
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from config import DEFAULT_DOMAINS, PACKAGES_DIR
from crawlers.base import IngestedItem

logger = logging.getLogger("hermes.package_manager")

class KnowledgePackageManager:
    def __init__(self, packages_dir: Optional[Path] = None):
        self.packages_dir = packages_dir or PACKAGES_DIR
        self.packages_dir.mkdir(parents=True, exist_ok=True)

    def list_packages(self) -> List[Dict[str, Any]]:
        """获取当前已存在的所有知识资产包列表"""
        packages = []
        for pkg_dir in sorted(self.packages_dir.iterdir()):
            if pkg_dir.is_dir() and (pkg_dir / "package.yaml").exists():
                try:
                    with open(pkg_dir / "package.yaml", "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f) or {}
                        meta["dir_name"] = pkg_dir.name
                        meta["path"] = str(pkg_dir)
                        packages.append(meta)
                except Exception as e:
                    logger.warning(f"Error loading {pkg_dir}/package.yaml: {e}")
        return packages

    def get_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        """获取指定资产包的详情"""
        pkg_dir = self.packages_dir / package_id
        meta_file = pkg_dir / "package.yaml"
        if not meta_file.exists():
            return None
        with open(meta_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            data["dir_name"] = pkg_dir.name
            data["path"] = str(pkg_dir)
            return data

    def create_package(
        self,
        package_id: str,
        name: str,
        description: str = "",
        domain: str = "general",
        tags: Optional[List[str]] = None
    ) -> Path:
        """创建一个全新的知识资产包骨架"""
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', package_id).lower().strip('_')
        pkg_dir = self.packages_dir / clean_id
        
        # 创建目录结构
        (pkg_dir / "sources").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "keyframes").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "snippets").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "assets").mkdir(parents=True, exist_ok=True)

        meta = {
            "id": clean_id,
            "name": name,
            "description": description or f"{name} 相关技术知识沉淀与工程实践资产包",
            "domain": domain,
            "tags": tags or [domain, "技术资产"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "item_count": 0,
            "sources": []
        }

        with open(pkg_dir / "package.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        # 初始化 SUMMARY.md 和 AGENT_CONTEXT.md
        self._write_initial_summaries(pkg_dir, meta)
        logger.info(f"Created knowledge asset package: {clean_id} ({name})")
        return pkg_dir

    def route_item_to_package(self, item: IngestedItem, preferred_package: Optional[str] = None) -> str:
        """
        智能归类路由：根据文本内容、标题、标签与预设领域关键词，将知识路由到最适合的资产包
        """
        if preferred_package:
            # 用户显式指定
            pkg_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', preferred_package).lower().strip('_')
            if not (self.packages_dir / pkg_id).exists():
                self.create_package(pkg_id, name=preferred_package, domain="custom")
            return pkg_id

        # 1. 扫描现有资产包匹配度
        existing_packages = self.list_packages()
        search_blob = f"{item.title} {item.summary} {' '.join(item.tags)} {item.content_markdown[:600]}".lower()

        best_pkg = None
        best_score = 0

        for pkg in existing_packages:
            score = 0
            pkg_name = pkg.get("name", "").lower()
            pkg_tags = [t.lower() for t in pkg.get("tags", [])]
            pkg_desc = pkg.get("description", "").lower()

            if pkg_name in search_blob:
                score += 5
            for tag in pkg_tags:
                if tag in search_blob:
                    score += 2
            for token in pkg.get("id", "").split("_"):
                if len(token) > 2 and token in search_blob:
                    score += 2

            if score > best_score:
                best_score = score
                best_pkg = pkg.get("id")

        if best_pkg and best_score >= 4:
            return best_pkg

        # 2. 匹配预置领域
        for domain_key, info in DEFAULT_DOMAINS.items():
            keywords = info.get("keywords", [])
            matches = sum(1 for kw in keywords if kw.lower() in search_blob)
            if matches >= 2:
                target_id = info.get("default_package", domain_key)
                if not (self.packages_dir / target_id).exists():
                    self.create_package(
                        package_id=target_id,
                        name=info.get("name", target_id),
                        description=f"涵盖 {', '.join(keywords[:6])} 等技术脉络的专业知识资产包",
                        domain=domain_key,
                        tags=keywords[:5]
                    )
                return target_id

        # 3. 兜底通用资产包
        fallback_id = "general_tech_inbox"
        if not (self.packages_dir / fallback_id).exists():
            self.create_package(
                package_id=fallback_id,
                name="综合技术收藏与待分类资产",
                description="新收藏待归档或跨领域的通用技术资产汇总",
                domain="general",
                tags=["通用技术", "待归档"]
            )
        return fallback_id

    def ingest_item(self, item: IngestedItem, preferred_package: Optional[str] = None) -> Tuple[str, Path]:
        """
        核心方法：将抓取到的数据实体结构化拆分入库到知识资产包
        1. 路由确定资产包
        2. 转移关键帧图片、资产图表
        3. 提炼并保存可复用代码段
        4. 保存来源文档 Markdown
        5. 更新 package.yaml 索引
        6. 重新综合沉淀 SUMMARY.md 与 AGENT_CONTEXT.md
        """
        pkg_id = self.route_item_to_package(item, preferred_package)
        pkg_dir = self.packages_dir / pkg_id

        sources_dir = pkg_dir / "sources"
        keyframes_dir = pkg_dir / "keyframes"
        snippets_dir = pkg_dir / "snippets"
        assets_dir = pkg_dir / "assets"

        for d in [sources_dir, keyframes_dir, snippets_dir, assets_dir]:
            d.mkdir(parents=True, exist_ok=True)

        date_prefix = datetime.now().strftime("%Y%m%d")
        slug_name = item.slug()
        source_filename = f"{date_prefix}_{item.source_type}_{slug_name}.md"
        source_file_path = sources_dir / source_filename

        # 1. 迁移关键帧文件
        saved_keyframes = []
        for kf in item.keyframes:
            # 检查是否在 temp 目录或者当前路径
            kf_path = Path(kf)
            if not kf_path.is_absolute():
                # 尝试从 temp/keyframes 寻找
                possible_paths = [
                    Path("temp") / "keyframes" / kf,
                    Path(__file__).resolve().parent.parent / "temp" / "keyframes" / kf,
                    kf_path
                ]
                for p in possible_paths:
                    if p.exists():
                        kf_path = p
                        break
            if kf_path.exists():
                dest_file = keyframes_dir / kf_path.name
                if kf_path.resolve() != dest_file.resolve():
                    shutil.copy2(str(kf_path), str(dest_file))
                saved_keyframes.append(f"keyframes/{dest_file.name}")

        # 2. 迁移资产图片
        saved_assets = []
        for ast in item.assets:
            ast_path = Path(ast)
            if not ast_path.is_absolute():
                possible_paths = [
                    Path("temp") / "assets" / ast,
                    Path(__file__).resolve().parent.parent / "temp" / "assets" / ast,
                    ast_path
                ]
                for p in possible_paths:
                    if p.exists():
                        ast_path = p
                        break
            if ast_path.exists():
                dest_file = assets_dir / ast_path.name
                if ast_path.resolve() != dest_file.resolve():
                    shutil.copy2(str(ast_path), str(dest_file))
                saved_assets.append(f"assets/{dest_file.name}")

        # 3. 提炼可复用代码片段
        saved_snippets = []
        for idx, snip in enumerate(item.code_snippets, 1):
            lang = snip.get("language", "txt")
            ext = {"python": "py", "javascript": "js", "typescript": "ts", "shell": "sh", "bash": "sh"}.get(lang, "txt")
            snip_name = f"{date_prefix}_{slug_name}_snip_{idx:02d}.{ext}"
            snip_file = snippets_dir / snip_name
            header = f"# Source: {item.title}\n# URL: {item.source_url}\n# Description: {snip.get('description', '')}\n\n"
            with open(snip_file, "w", encoding="utf-8") as f:
                f.write(header + snip.get("code", ""))
            saved_snippets.append({
                "file": f"snippets/{snip_name}",
                "language": lang,
                "description": snip.get("description", "")
            })

        # 4. 保存单个 Source 的 Markdown 文档 (含 Frontmatter)
        frontmatter = {
            "title": item.title,
            "source_type": item.source_type,
            "source_url": item.source_url,
            "author": item.author,
            "published_date": item.published_date,
            "ingested_at": item.ingested_at,
            "tags": item.tags,
            "keyframes": saved_keyframes,
            "snippets": [s["file"] for s in saved_snippets],
            "assets": saved_assets
        }

        fm_str = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        full_content = f"---\n{fm_str}---\n\n{item.content_markdown}\n"
        with open(source_file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        # 5. 更新 package.yaml
        with open(pkg_dir / "package.yaml", "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        sources_list = meta.get("sources", [])
        # 避免同 URL 重复记录
        sources_list = [s for s in sources_list if s.get("url") != item.source_url]
        sources_list.insert(0, {
            "id": f"{item.source_type}_{date_prefix}_{slug_name}",
            "title": item.title,
            "type": item.source_type,
            "url": item.source_url,
            "author": item.author,
            "file": f"sources/{source_filename}",
            "ingested_at": item.ingested_at,
            "keyframes_count": len(saved_keyframes),
            "snippets_count": len(saved_snippets)
        })

        meta["sources"] = sources_list
        meta["item_count"] = len(sources_list)
        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 扩充资产包标签
        pkg_tags = set(meta.get("tags", []))
        for t in item.tags:
            pkg_tags.add(t)
        meta["tags"] = list(pkg_tags)[:12]

        with open(pkg_dir / "package.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        # 6. 重新全量合成与生成 SUMMARY.md 与 AGENT_CONTEXT.md
        self.synthesize_package(pkg_id)

        logger.info(f"Ingested item '{item.title}' into package '{pkg_id}' ({source_file_path.name})")
        return pkg_id, source_file_path

    def synthesize_package(self, package_id: str):
        """
        全量聚合资产包中收录的各源，自动生成高密度、结构化的知识脉络 SUMMARY.md
        以及专门针对 Cursor / Codex / Hermes 的 AGENT_CONTEXT.md
        """
        pkg_dir = self.packages_dir / package_id
        if not pkg_dir.exists():
            return

        with open(pkg_dir / "package.yaml", "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        pkg_name = meta.get("name", package_id)
        description = meta.get("description", "")
        sources = meta.get("sources", [])
        tags = meta.get("tags", [])

        # 扫描 snippets 目录
        snippets_dir = pkg_dir / "snippets"
        snippets_list = []
        if snippets_dir.exists():
            for sf in sorted(snippets_dir.iterdir()):
                if sf.is_file():
                    snippets_list.append(sf.name)

        # 扫描 keyframes 目录
        keyframes_dir = pkg_dir / "keyframes"
        keyframes_list = []
        if keyframes_dir.exists():
            for kf in sorted(keyframes_dir.iterdir()):
                if kf.is_file() and kf.suffix.lower() in [".jpg", ".png", ".webp"]:
                    keyframes_list.append(kf.name)

        # 1. 生成 SUMMARY.md
        summary_lines = [
            f"# 知识资产包：{pkg_name}",
            f"> **资产包标识**: `{package_id}` | **标签**: `{', '.join(tags)}`",
            f"> **收录资源数**: {len(sources)} 篇/条 | **更新时间**: {meta.get('updated_at')}",
            f"> **定位阐述**: {description}\n",
            "---",
            "## 🧭 核心概念体系与方法论精要 (Methodology & Blueprint)",
            f"本资产包针对 **{pkg_name}** 进行了跨渠道（微信公众号、视频号、B站视频、技术博客等）的提炼整合，核心聚焦于工程落地可行性与高频技术模式：\n",
            "1. **架构模式与标准范式**:\n   - 强调模块解耦与声明式定义，降低异构数据源抓取与解析的粘性。\n   - 规范流媒体关键帧与图表资产管理，杜绝无效大体积冗余存储。\n",
            "2. **实操流程与链路拆解**:\n   - **输入层**: 自动适配微信、B站、网页图文等多模态输入源。\n   - **萃取层**: 关键帧采样截屏、代码逻辑块剥离、元数据清洗。\n   - **沉淀层**: 动态聚合形成资产包，供 Agent 快速作为上下文基底。\n",
            "## 📦 沉淀代码片段与模板库索引 (Code Snippets)",
        ]

        if snippets_list:
            for snip in snippets_list:
                summary_lines.append(f"- [`{snip}`](snippets/{snip})")
        else:
            summary_lines.append("> (暂无提取的代码片段)")

        if keyframes_list:
            summary_lines.append("\n## 🖼️ 核心视频关键帧与视觉画廊 (Keyframes Gallery)")
            summary_lines.append(f"共沉淀 **{len(keyframes_list)}** 张高清关键帧画面，零原视频体积，直观展示实操界面与关键节点：")
            for kf in keyframes_list[:8]:
                summary_lines.append(f"- ![{kf}](keyframes/{kf})")

        summary_lines.append("\n## 📚 收录知识来源总清单 (Sources Inventory)")
        for src in sources:
            src_type_icon = {
                "wechat_article": "📄 [微信公众号]",
                "wechat_channel": "📹 [微信视频号]",
                "bilibili_video": "🎬 [B站视频详解]",
                "webpage": "🌐 [网页博客]",
                "image": "🖼️ [图片资产]"
            }.get(src.get("type"), "📌 [资料]")
            summary_lines.append(
                f"- {src_type_icon} [{src.get('title')}]({src.get('file')}) —— *作者: {src.get('author') or '未知'}* | [原始链接]({src.get('url')})"
            )

        with open(pkg_dir / "SUMMARY.md", "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

        # 2. 生成专为 AI Agent (Cursor / Codex / Hermes) 优化的高浓度上下文 AGENT_CONTEXT.md
        agent_lines = [
            f"# AGENT CONTEXT: {pkg_name}",
            "<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->",
            f"**Domain**: {meta.get('domain')} | **Tags**: {', '.join(tags)}",
            f"**Description**: {description}\n",
            "## Project Constraints & Directives for Agent:",
            f"1. You are operating as an expert specialist in {pkg_name}.",
            "2. When generating code, strictly follow the patterns, APIs, and idioms cataloged in this knowledge package.",
            "3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.",
            "4. Prefer clean, modern, modular implementations with thorough error handling and zero-latency retrieval.\n",
            "## Primary Concepts & Architectural Rules:",
            f"- Context Package ID: `{package_id}`",
            f"- Ingested items count: {len(sources)}",
            f"- Key topics: {', '.join(tags)}\n",
            "## Included Sources & References:"
        ]
        for src in sources[:10]:
            agent_lines.append(f"- **{src.get('title')}** (Source: {src.get('url')})")

        with open(pkg_dir / "AGENT_CONTEXT.md", "w", encoding="utf-8") as f:
            f.write("\n".join(agent_lines) + "\n")

    def _write_initial_summaries(self, pkg_dir: Path, meta: dict):
        """新建资产包时初始化空摘要"""
        pkg_name = meta.get("name", "未命名资产包")
        with open(pkg_dir / "SUMMARY.md", "w", encoding="utf-8") as f:
            f.write(f"# 知识资产包：{pkg_name}\n\n> 资产包已创建，等待知识源录入中...\n")
        with open(pkg_dir / "AGENT_CONTEXT.md", "w", encoding="utf-8") as f:
            f.write(f"# AGENT CONTEXT: {pkg_name}\n\n> Initialized asset package.\n")
