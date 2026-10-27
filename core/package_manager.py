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

from config import PRIMARY_DOMAINS, PACKAGES_DIR, resolve_domain, resolve_sub_category
from core.knowledge_distiller import KnowledgeDistiller
from core.knowledge_merger import KnowledgeMerger
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
        domain: str = "inbox",
        sub_category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Path:
        """创建一个全新的知识资产包骨架 (关联一级领域与二级子方向)"""
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', package_id).lower().strip('_')
        pkg_dir = self.packages_dir / clean_id
        
        # 匹配一级领域与二级子方向
        domain_key = resolve_domain(domain)
        dom_info = PRIMARY_DOMAINS.get(domain_key, PRIMARY_DOMAINS["inbox"])
        domain_name = dom_info["name"]
        domain_icon = dom_info.get("icon", "📁")

        sub_cats = dom_info.get("sub_categories", {})
        sub_id = sub_category or list(sub_cats.keys())[0] if sub_cats else "general"
        sub_info = sub_cats.get(sub_id, {})
        sub_name = sub_info.get("name", sub_id)
        sub_icon = sub_info.get("icon", "📌")

        # 创建目录结构
        (pkg_dir / "sources").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "keyframes").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "snippets").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "assets").mkdir(parents=True, exist_ok=True)

        meta = {
            "id": clean_id,
            "name": name,
            "description": description or f"{name} 相关知识沉淀与实战资产包",
            "domain": domain_key,
            "domain_name": domain_name,
            "domain_icon": domain_icon,
            "sub_category": sub_id,
            "sub_category_name": sub_name,
            "sub_category_icon": sub_icon,
            "tags": tags or [domain_name, sub_name, "知识资产"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "item_count": 0,
            "knowledge_matrix": [],
            "sources": []
        }

        with open(pkg_dir / "package.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        # 初始化 SUMMARY.md 和 AGENT_CONTEXT.md
        self._write_initial_summaries(pkg_dir, meta)
        logger.info(f"Created package: {clean_id} ({name}) under [{domain_name} > {sub_name}]")
        return pkg_dir

    def delete_package(self, package_id: str) -> bool:
        """彻底删除指定的知识资产包及其所有物理文件 (拒绝污染)"""
        pkg_dir = self.packages_dir / package_id
        if pkg_dir.exists() and pkg_dir.is_dir():
            shutil.rmtree(pkg_dir)
            logger.info(f"Deleted package {package_id} completely.")
            return True
        return False

    def delete_source(self, package_id: str, source_filename: str) -> bool:
        """从资产包中删除单篇文献，并重新增量合成知识矩阵"""
        pkg_dir = self.packages_dir / package_id
        if not pkg_dir.exists():
            return False

        meta_file = pkg_dir / "package.yaml"
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        # 找到并删除该源文件
        sources = meta.get("sources", [])
        new_sources = []
        target_file_to_del = None
        for s in sources:
            if s.get("file") == source_filename or Path(s.get("file")).name == Path(source_filename).name:
                target_file_to_del = pkg_dir / s.get("file")
            else:
                new_sources.append(s)

        if target_file_to_del and target_file_to_del.exists():
            try:
                target_file_to_del.unlink()
            except Exception:
                pass

        meta["sources"] = new_sources
        meta["item_count"] = len(new_sources)
        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 重新增量重构知识矩阵
        distiller = KnowledgeDistiller()
        merger = KnowledgeMerger()
        matrix = []
        for s in reversed(new_sources):
            sf = pkg_dir / s.get("file")
            if sf.exists():
                cnt = sf.read_text(encoding="utf-8")
                if cnt.startswith("---"):
                    parts = cnt.split("---", 2)
                    if len(parts) >= 3:
                        cnt = parts[2]
                card = distiller.distill(s.get("title"), cnt, domain=meta.get("domain", "ai_tech"), source_label=s.get("author") or s.get("title")[:15])
                matrix, is_merged, entity_name = merger.merge_card_into_matrix(matrix, card, s.get("author") or s.get("title")[:15])
                s["associated_entity"] = entity_name
                s["incremental_merged"] = is_merged

        meta["knowledge_matrix"] = matrix
        with open(meta_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        self.synthesize_package(package_id)
        logger.info(f"Deleted source {source_filename} from package {package_id} and re-synthesized.")
        return True

    def route_item_to_package(
        self,
        item: IngestedItem,
        preferred_package: Optional[str] = None,
        preferred_domain: Optional[str] = None,
        preferred_sub_category: Optional[str] = None
    ) -> str:
        """
        智能多级归类路由：根据领域偏好、子方向与关键词密度，将知识路由到最适合的资产包
        """
        search_blob = f"{item.title} {item.summary} {' '.join(item.tags)} {item.content_markdown[:800]}".lower()

        # 1. 用户显式指定了资产包
        if preferred_package:
            pkg_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', preferred_package).lower().strip('_')
            if not (self.packages_dir / pkg_id).exists():
                domain_val = preferred_domain or "inbox"
                sub_id, _ = resolve_sub_category(domain_val, search_blob)
                self.create_package(pkg_id, name=preferred_package, domain=domain_val, sub_category=sub_id)
            return pkg_id

        # 2. 用户指定了一级领域与子方向
        if preferred_domain:
            domain_key = resolve_domain(preferred_domain)
            sub_id = preferred_sub_category
            if not sub_id:
                sub_id, sub_name = resolve_sub_category(domain_key, search_blob)
            
            # 查找该领域与子方向下是否已有对应资产包
            for pkg in self.list_packages():
                if pkg.get("domain") == domain_key and pkg.get("sub_category") == sub_id:
                    return pkg.get("id")

            # 若无，自动创建该子方向的专属资产包
            dom_info = PRIMARY_DOMAINS.get(domain_key, PRIMARY_DOMAINS["inbox"])
            sub_name = dom_info.get("sub_categories", {}).get(sub_id, {}).get("name", sub_id)
            new_pkg_id = f"{domain_key}_{sub_id}"
            if not (self.packages_dir / new_pkg_id).exists():
                self.create_package(
                    package_id=new_pkg_id,
                    name=f"{sub_name}知识资产包",
                    description=f"{dom_info['name']} > {sub_name} 专题领域知识沉淀",
                    domain=domain_key,
                    sub_category=sub_id,
                    tags=[dom_info['name'], sub_name]
                )
            return new_pkg_id

        # 3. 全局自动匹配：优先匹配已有资产包
        existing_packages = self.list_packages()
        best_pkg = None
        best_score = 0
        for pkg in existing_packages:
            score = 0
            pkg_name = pkg.get("name", "").lower()
            pkg_tags = [t.lower() for t in pkg.get("tags", [])]
            if pkg_name in search_blob:
                score += 5
            for tag in pkg_tags:
                if tag in search_blob:
                    score += 2
            if score > best_score:
                best_score = score
                best_pkg = pkg.get("id")

        if best_pkg and best_score >= 4:
            return best_pkg

        # 4. 其次自动匹配一级领域与二级子方向
        best_domain = None
        domain_max_matches = 0
        for domain_key, info in PRIMARY_DOMAINS.items():
            matches = 0
            for sub_id, sub_info in info.get("sub_categories", {}).items():
                matches += sum(1 for kw in sub_info.get("keywords", []) if kw.lower() in search_blob)
            if matches > domain_max_matches:
                domain_max_matches = matches
                best_domain = (domain_key, info)

        if best_domain and domain_max_matches >= 2:
            domain_key, info = best_domain
            sub_id, sub_name = resolve_sub_category(domain_key, search_blob)
            target_id = f"{domain_key}_{sub_id}"
            if not (self.packages_dir / target_id).exists():
                self.create_package(
                    package_id=target_id,
                    name=f"{sub_name}知识资产包",
                    description=f"{info['name']} > {sub_name} 专题领域沉淀",
                    domain=domain_key,
                    sub_category=sub_id,
                    tags=[info['name'], sub_name]
                )
            return target_id

        # 5. 兜底通用收件箱
        fallback_id = "inbox_quick_capture"
        if not (self.packages_dir / fallback_id).exists():
            self.create_package(
                package_id=fallback_id,
                name="临时待整理收件箱",
                description="新收藏待归档或跨领域的综合知识暂存",
                domain="inbox",
                sub_category="quick_capture",
                tags=["临时收藏", "待归档"]
            )
        return fallback_id

    def ingest_item(
        self,
        item: IngestedItem,
        preferred_package: Optional[str] = None,
        preferred_domain: Optional[str] = None,
        preferred_sub_category: Optional[str] = None
    ) -> Tuple[str, Path]:
        """
        核心方法：将抓取到的数据实体结构化拆分入库到知识资产包
        若传入条目包含原子化子项目 (sub_items，如多项目推荐视频或合辑)：
        自动将每个子项拆解，独立路由归入各自所属领域与子方向的资产包中！
        """
        if getattr(item, "sub_items", None) and len(item.sub_items) >= 2:
            logger.info(f"Detected multi-topic collection ({len(item.sub_items)} items). Decomposing and routing each sub-item to its designated package...")
            affected_packages = []
            first_pkg_id = None
            first_path = None
            for sub in item.sub_items:
                target_pkg_id, sub_source_path = self._ingest_single_item(sub)
                if target_pkg_id not in affected_packages:
                    affected_packages.append(target_pkg_id)
                if not first_pkg_id:
                    first_pkg_id = target_pkg_id
                    first_path = sub_source_path

            item.metadata["packages_affected"] = affected_packages
            logger.info(f"Successfully decomposed into {len(item.sub_items)} items across packages: {affected_packages}")
            return first_pkg_id, first_path

        pkg_id, path = self._ingest_single_item(item, preferred_package, preferred_domain, preferred_sub_category)
        item.metadata["packages_affected"] = [pkg_id]
        return pkg_id, path

    def _ingest_single_item(
        self,
        item: IngestedItem,
        preferred_package: Optional[str] = None,
        preferred_domain: Optional[str] = None,
        preferred_sub_category: Optional[str] = None
    ) -> Tuple[str, Path]:
        pkg_id = self.route_item_to_package(item, preferred_package, preferred_domain, preferred_sub_category)
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

        # 5.1 结构化知识特征抽取与增量去重融合 (Incremental Merge)
        distiller = KnowledgeDistiller()
        merger = KnowledgeMerger()
        source_label = item.author or item.title[:20]
        distilled_card = distiller.distill(
            title=item.title,
            text=item.content_markdown,
            domain=meta.get("domain", "ai_tech"),
            source_label=source_label
        )

        existing_matrix = meta.get("knowledge_matrix", [])
        updated_matrix, is_merged, entity_name = merger.merge_card_into_matrix(
            existing_matrix, distilled_card, source_label
        )
        meta["knowledge_matrix"] = updated_matrix

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
            "snippets_count": len(saved_snippets),
            "associated_entity": entity_name,
            "incremental_merged": is_merged
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

        # 6. 重新全量合成与生成结构化知识脉络 SUMMARY.md 与 AGENT_CONTEXT.md
        self.synthesize_package(pkg_id)

        logger.info(f"Ingested item '{item.title}' into package '{pkg_id}' (Entity: {entity_name}, Merged: {is_merged})")
        return pkg_id, source_file_path

    def synthesize_package(self, package_id: str):
        """
        全量聚合资产包中收录的各源，自动生成高密度、结构化的知识脉络 SUMMARY.md
        以及专门针对 Cursor / Codex / Hermes 的 AGENT_CONTEXT.md
        包含：核心方案对比矩阵、硬件配置/运行环境/本地离线/优劣势结构化卡片
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
        knowledge_matrix = meta.get("knowledge_matrix", [])

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

        # 1. 生成高质量、高密度的结构化知识汇总 SUMMARY.md
        summary_lines = [
            f"# 知识资产包：{pkg_name}",
            f"> **资产包标识**: `{package_id}` | **一级领域**: {meta.get('domain_icon', '📁')} {meta.get('domain_name', meta.get('domain'))}",
            f"> **收录资源数**: {len(sources)} 篇/条 | **沉淀知识实体**: {len(knowledge_matrix)} 个 | **更新时间**: {meta.get('updated_at')}",
            f"> **定位阐述**: {description}\n",
            "---",
            "## 🌟 核心技术与工程特性对比矩阵 (Structured Knowledge Matrix)",
            "本表由系统从收录的各篇资料中自动抽取、去重并增量融合提炼而成：\n"
        ]

        if knowledge_matrix:
            summary_lines.append("| 核心方案/实体 | 核心定位与功能 | 💻 硬件配置要求 | 🌐 运行环境与依赖 | 🔒 能否本地离线运行 | ⚡ 同类核心优势 | ⚠️ 劣势与踩坑要点 | 👥 融合来源数 |")
            summary_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |")
            for k in knowledge_matrix:
                adv_summary = "<br>".join([f"• {a}" for a in k.get("competitive_advantages", [])[:3]])
                pit_summary = "<br>".join([f"• {p}" for p in k.get("limitations_and_pitfalls", [])[:3]])
                summary_lines.append(
                    f"| **{k.get('entity_name')}** | {k.get('core_function')} | {k.get('hardware_specs')} | {k.get('environment')} | {k.get('local_deployable')} | {adv_summary or '-'} | {pit_summary or '-'} | {k.get('merged_sources_count', 1)} 篇融合 |"
                )
            summary_lines.append("\n---\n")

            summary_lines.append("## 📋 深度结构化特征卡片详解 (Detailed Entities)")
            for idx, k in enumerate(knowledge_matrix, 1):
                summary_lines.append(f"### {idx}. 方案实体: {k.get('entity_name')}")
                summary_lines.append(f"- **🎯 核心功能与定位**: {k.get('core_function')}")
                summary_lines.append(f"- **💻 硬件配置规格**: `{k.get('hardware_specs')}`")
                summary_lines.append(f"- **🌐 运行环境与依赖栈**: `{k.get('environment')}`")
                summary_lines.append(f"- **🔒 本地化与隐私能力**: {k.get('local_deployable')}")
                
                summary_lines.append("- **⚡ 同类对比核心优势**:")
                for adv in k.get("competitive_advantages", []):
                    summary_lines.append(f"  - {adv}")

                summary_lines.append("- **⚠️ 劣势、边界与避坑踩坑要点**:")
                for pit in k.get("limitations_and_pitfalls", []):
                    summary_lines.append(f"  - {pit}")

                if k.get("quickstart_commands"):
                    summary_lines.append("- **🛠️ 上手验证常用指令**:")
                    for cmd in k.get("quickstart_commands"):
                        summary_lines.append(f"  ```bash\n  {cmd}\n  ```")

                if k.get("key_insights"):
                    summary_lines.append("- **💡 实战心法与核心认知**:")
                    for ins in k.get("key_insights"):
                        summary_lines.append(f"  - {ins}")

                summary_lines.append(f"- **👥 知识贡献来源**: {', '.join(k.get('sources_contributed', [])) or '全库沉淀'}\n")
        else:
            summary_lines.append("> (暂无抽取到的知识卡片，待录入后自动呈现)\n")

        summary_lines.append("## 📦 沉淀代码片段与模板库索引 (Code Snippets)")
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

        summary_lines.append("\n## 📚 原始知识本地脱机存档清单 (Local Offline Archives)")
        summary_lines.append("> 提示：所有正文、代码与排版均已 100% 离线克隆至本地 Git 仓库，外部链接失效亦可永久脱机查阅：")
        for src in sources:
            src_type_icon = {
                "wechat_article": "📄 [微信公众号]",
                "wechat_channel": "📹 [微信视频号]",
                "bilibili_video": "🎬 [B站视频详解]",
                "webpage": "🌐 [网页博客]",
                "image": "🖼️ [图片资产]"
            }.get(src.get("type"), "📌 [资料]")
            merge_badge = " `[已去重增量融合]`" if src.get("incremental_merged") else ""
            summary_lines.append(
                f"- {src_type_icon} **[{src.get('title')}]({src.get('file')})**{merge_badge} —— *作者: {src.get('author') or '未知'}* | [原始链接]({src.get('url')})"
            )

        with open(pkg_dir / "SUMMARY.md", "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

        # 2. 生成专为 AI Agent (Cursor / Codex / Hermes) 优化的高浓度上下文 AGENT_CONTEXT.md
        agent_lines = [
            f"# AGENT CONTEXT: {pkg_name}",
            "<!-- This file is auto-generated for Cursor, Codex and Hermes Agent Reference -->",
            f"**Domain**: {meta.get('domain')} | **Tags**: {', '.join(tags)}",
            f"**Description**: {description}\n",
            "## Structured Project Constraints & Technical Capabilities:",
        ]

        if knowledge_matrix:
            for k in knowledge_matrix:
                agent_lines.append(f"### Target Entity: {k.get('entity_name')}")
                agent_lines.append(f"- **Purpose**: {k.get('core_function')}")
                agent_lines.append(f"- **Hardware Constraints**: {k.get('hardware_specs')}")
                agent_lines.append(f"- **Runtime Environment**: {k.get('environment')}")
                agent_lines.append(f"- **Deployment**: {k.get('local_deployable')}")
                agent_lines.append(f"- **Verified Advantages**: {'; '.join(k.get('competitive_advantages', []))}")
                agent_lines.append(f"- **Strict Pitfalls & Gotchas**: {'; '.join(k.get('limitations_and_pitfalls', []))}\n")

        agent_lines.extend([
            "## Project Constraints & Directives for Agent:",
            f"1. You are operating as an expert specialist in {pkg_name}.",
            "2. When generating code, strictly follow the hardware constraints and environment dependencies cataloged above.",
            "3. Do not re-download raw videos or save binary bloat; strictly use keyframes, transcripts, and atomic snippets.",
            "4. Respect the pitfalls and limitations outlined above to prevent dead ends.\n",
            "## Included Sources & References:"
        ])
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
