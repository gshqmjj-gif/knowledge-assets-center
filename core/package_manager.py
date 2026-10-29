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

from config import PRIMARY_DOMAINS, PACKAGES_DIR, resolve_domain, resolve_sub_category, save_custom_domain
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

    def rename_package(self, package_id: str, new_name: str, new_description: Optional[str] = None) -> bool:
        """直接重命名知识资产包名称与定位简介，并同步更新聚合体系大纲"""
        pkg_dir = self.packages_dir / package_id
        meta_file = pkg_dir / "package.yaml"
        if not meta_file.exists():
            return False
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        clean_name = new_name.strip()
        if not clean_name:
            return False
        meta["name"] = clean_name
        if new_description is not None:
            meta["description"] = new_description.strip()
        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(meta_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        self.synthesize_package(package_id)
        logger.info(f"Renamed package {package_id} to '{clean_name}'.")
        return True

    def move_package(self, package_id: str, new_domain: str, new_sub_category: Optional[str] = None) -> bool:
        """调整知识资产包的一级领域与二级子方向归属（支持拖拽或面板调整）"""
        pkg_dir = self.packages_dir / package_id
        meta_file = pkg_dir / "package.yaml"
        if not meta_file.exists():
            return False
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        domain_key = resolve_domain(new_domain)
        dom_info = PRIMARY_DOMAINS.get(domain_key, PRIMARY_DOMAINS.get("inbox", {}))
        domain_name = dom_info.get("name", domain_key)
        domain_icon = dom_info.get("icon", "📁")

        sub_cats = dom_info.get("sub_categories", {})
        sub_id = new_sub_category or (list(sub_cats.keys())[0] if sub_cats else "general")
        sub_info = sub_cats.get(sub_id, {})
        sub_name = sub_info.get("name", sub_id)
        sub_icon = sub_info.get("icon", "📌")

        meta["domain"] = domain_key
        meta["domain_name"] = domain_name
        meta["domain_icon"] = domain_icon
        meta["sub_category"] = sub_id
        meta["sub_category_name"] = sub_name
        meta["sub_category_icon"] = sub_icon
        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 同步更新标签
        tags = set(meta.get("tags", []))
        tags.add(domain_name)
        tags.add(sub_name)
        meta["tags"] = list(tags)[:12]

        with open(meta_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        self.synthesize_package(package_id)
        logger.info(f"Moved package {package_id} to [{domain_name} > {sub_name}].")
        return True

    def rename_source(self, package_id: str, source_filename: str, new_title: str) -> bool:
        """直接重命名单篇文献资料的标题，并同步更新 Markdown 元数据与大纲"""
        pkg_dir = self.packages_dir / package_id
        meta_file = pkg_dir / "package.yaml"
        if not meta_file.exists():
            return False
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        clean_title = new_title.strip()
        if not clean_title:
            return False

        found_source = None
        for s in meta.get("sources", []):
            if s.get("file") == source_filename or Path(s.get("file")).name == Path(source_filename).name:
                s["title"] = clean_title
                found_source = s
                break

        if not found_source:
            return False

        # 更新 source markdown 实体文件中的 frontmatter 和一级标题
        target_file = pkg_dir / found_source.get("file")
        if target_file.exists():
            content = target_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1]) or {}
                    fm["title"] = clean_title
                    fm_str = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
                    body = parts[2]
                    body_lines = body.splitlines()
                    for idx, line in enumerate(body_lines):
                        if line.startswith("# "):
                            body_lines[idx] = f"# {clean_title}"
                            break
                    target_file.write_text(f"---\n{fm_str}---\n" + "\n".join(body_lines), encoding="utf-8")

        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(meta_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

        self.synthesize_package(package_id)
        logger.info(f"Renamed source {source_filename} in {package_id} to '{clean_title}'.")
        return True

    def move_source(self, from_package_id: str, to_package_id: str, source_filename: str) -> bool:
        """将某篇文献资料迁移至另一个资产包中（含关键帧、本地离线图片与代码片段）"""
        from_dir = self.packages_dir / from_package_id
        to_dir = self.packages_dir / to_package_id
        if not from_dir.exists() or not to_dir.exists() or from_package_id == to_package_id:
            return False

        from_meta_file = from_dir / "package.yaml"
        to_meta_file = to_dir / "package.yaml"
        with open(from_meta_file, "r", encoding="utf-8") as f:
            from_meta = yaml.safe_load(f) or {}
        with open(to_meta_file, "r", encoding="utf-8") as f:
            to_meta = yaml.safe_load(f) or {}

        # 找到目标 source
        target_source = None
        new_from_sources = []
        for s in from_meta.get("sources", []):
            if s.get("file") == source_filename or Path(s.get("file")).name == Path(source_filename).name:
                target_source = s
            else:
                new_from_sources.append(s)

        if not target_source:
            return False

        # 物理迁移 markdown 源文件
        src_file = from_dir / target_source.get("file")
        if not src_file.exists():
            return False

        dest_src_file = to_dir / "sources" / src_file.name
        dest_src_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_file), str(dest_src_file))

        # 读取 frontmatter 并迁移关联的 keyframes, assets, snippets
        content = dest_src_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                for kf in fm.get("keyframes", []):
                    kf_src = from_dir / kf
                    if kf_src.exists():
                        kf_dest = to_dir / "keyframes" / kf_src.name
                        kf_dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(kf_src), str(kf_dest))
                for ast in fm.get("assets", []):
                    ast_src = from_dir / ast
                    if ast_src.exists():
                        ast_dest = to_dir / "assets" / ast_src.name
                        ast_dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(ast_src), str(ast_dest))
                for snip in fm.get("snippets", []):
                    snip_src = from_dir / snip
                    if snip_src.exists():
                        snip_dest = to_dir / "snippets" / snip_src.name
                        snip_dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(snip_src), str(snip_dest))

        # 迁移对应的知识特征卡片 (knowledge_matrix)
        entity_name = target_source.get("associated_entity")
        if entity_name:
            from_matrix = from_meta.get("knowledge_matrix", [])
            other_uses = any(s.get("associated_entity") == entity_name for s in new_from_sources)
            card_to_move = next((m for m in from_matrix if m.get("entity_name") == entity_name), None)
            if card_to_move and not other_uses:
                from_meta["knowledge_matrix"] = [m for m in from_matrix if m.get("entity_name") != entity_name]
            if card_to_move:
                to_matrix = to_meta.get("knowledge_matrix", [])
                if not any(m.get("entity_name") == entity_name for m in to_matrix):
                    to_matrix.append(card_to_move)
                to_meta["knowledge_matrix"] = to_matrix

        # 更新双方 package.yaml
        from_meta["sources"] = new_from_sources
        from_meta["item_count"] = len(new_from_sources)
        from_meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(from_meta_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(from_meta, f, allow_unicode=True, sort_keys=False)

        target_source["file"] = f"sources/{dest_src_file.name}"
        to_sources = to_meta.get("sources", [])
        to_sources.append(target_source)
        to_meta["sources"] = to_sources
        to_meta["item_count"] = len(to_sources)
        to_meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(to_meta_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(to_meta, f, allow_unicode=True, sort_keys=False)

        # 重新双向合成
        self.synthesize_package(from_package_id)
        self.synthesize_package(to_package_id)
        logger.info(f"Moved source {source_filename} from {from_package_id} to {to_package_id}.")
        return True

    def split_source_to_package(
        self,
        source_package_id: str,
        source_filename: str,
        new_package_name: str,
        new_description: Optional[str] = None,
        target_domain: Optional[str] = None,
        target_sub_category: Optional[str] = None
    ) -> Optional[str]:
        """
        三级内容独立拆分：将某篇文献资料从原资产包中剥离，独立建立为全新的知识资产包（独立子项目）
        彻底避免不同工具/项目被无脑合并成一个资产包的问题
        """
        clean_name = new_package_name.strip()
        if not clean_name:
            return None

        from_dir = self.packages_dir / source_package_id
        if not from_dir.exists():
            return None

        with open(from_dir / "package.yaml", "r", encoding="utf-8") as f:
            from_meta = yaml.safe_load(f) or {}

        dom_key = target_domain or from_meta.get("domain", "inbox")
        sub_id = target_sub_category or from_meta.get("sub_category", "quick_capture")

        # 生成新的资产包 ID
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name).strip('_').lower()
        if not slug:
            slug = "subproject"
        new_pkg_id = f"{dom_key}_{slug}"[:36].rstrip('_')
        if (self.packages_dir / new_pkg_id).exists():
            new_pkg_id = f"{new_pkg_id}_{datetime.now().strftime('%m%d_%H%M%S')}"

        dom_info = PRIMARY_DOMAINS.get(dom_key, PRIMARY_DOMAINS.get("inbox", {}))
        dom_name = dom_info.get("name", dom_key)
        sub_info = dom_info.get("sub_categories", {}).get(sub_id, {})
        sub_name = sub_info.get("name", sub_id)

        desc = new_description.strip() if new_description else f"{dom_name} > {sub_name} 独立子项目知识资产"

        self.create_package(
            package_id=new_pkg_id,
            name=clean_name,
            description=desc,
            domain=dom_key,
            sub_category=sub_id,
            tags=[dom_name, sub_name, clean_name]
        )

        success = self.move_source(source_package_id, new_pkg_id, source_filename)
        if not success:
            return None

        logger.info(f"Split source {source_filename} from {source_package_id} to new package {new_pkg_id} ('{clean_name}')")
        return new_pkg_id

    def promote_package_to_subcategory(
        self,
        package_id: str,
        new_sub_name: str,
        new_sub_icon: str = "📌",
        target_domain: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        三级内容升级为二级分类：将一个知识资产包（子项目）提升为该一级领域下的全新二级子板块
        并在 custom_domains.yaml 中持久化注册，让分类体系随业务灵活成长
        """
        clean_sub_name = new_sub_name.strip()
        if not clean_sub_name:
            return None

        pkg_dir = self.packages_dir / package_id
        if not pkg_dir.exists():
            return None

        with open(pkg_dir / "package.yaml", "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

        dom_key = target_domain or meta.get("domain", "inbox")
        dom_info = PRIMARY_DOMAINS.get(dom_key, PRIMARY_DOMAINS.get("inbox", {}))
        dom_name = dom_info.get("name", dom_key)
        dom_icon = dom_info.get("icon", "📁")

        # 生成合法的 sub_key
        sub_slug = re.sub(r'[^a-zA-Z0-9_]', '_', clean_sub_name).strip('_').lower()
        if not sub_slug or len(sub_slug) < 2:
            sub_slug = f"sub_{datetime.now().strftime('%m%d_%H%M%S')}"
        sub_key = sub_slug[:24]

        # 持久化注册新二级板块
        save_custom_domain(
            domain_key=dom_key,
            domain_name=dom_name,
            domain_icon=dom_icon,
            sub_key=sub_key,
            sub_name=clean_sub_name,
            sub_icon=new_sub_icon or "📌",
            keywords=[clean_sub_name.lower(), dom_name.lower(), sub_key.lower()]
        )

        # 调整该资产包归属到新创建的二级子板块
        self.move_package(package_id, dom_key, sub_key)
        logger.info(f"Promoted package {package_id} to new subcategory [{dom_name} > {clean_sub_name} ({sub_key})]")
        return dom_key, sub_key

    def _find_matching_package_in_sub_category(self, domain_key: str, sub_id: str, item: IngestedItem, search_blob: str) -> Optional[str]:
        """
        在指定的二级子类别中，按专属工具/项目实体严格查找匹配的资产包：
        只有当新资料确实是关于该已有工具（如 OpenMontage 后续教程）时才合入；
        若属于完全不同的独立工具（如 WorkBuddy vs OpenMontage），则返回 None，由系统创建全新独立包！
        """
        item_title_lower = item.title.lower()
        item_tags_lower = [t.lower() for t in item.tags]

        for pkg in self.list_packages():
            if pkg.get("domain") == domain_key and pkg.get("sub_category") == sub_id:
                pkg_name = pkg.get("name", "").lower()
                pkg_id = pkg.get("id", "").lower()
                pkg_tags = [t.lower() for t in pkg.get("tags", [])]
                matrix_entities = [m.get("entity_name", "").lower() for m in pkg.get("knowledge_matrix", [])]

                # 提取包的专属项目标识关键词
                # 例如从 "OpenMontage AI视频代码剪辑工坊" 提取 "openmontage"
                candidates = set()
                candidates.add(pkg_id.replace(f"{domain_key}_", ""))
                for part in re.split(r'[\s\-_+（）()]+', pkg_name):
                    if len(part) >= 3 and not any(common in part for common in ["ai", "视频", "工坊", "助手", "工作流", "知识", "资产包"]):
                        candidates.add(part)
                for ent in matrix_entities:
                    if len(ent) >= 3:
                        candidates.add(ent)

                for cand in candidates:
                    if cand and len(cand) >= 3:
                        if cand in item_title_lower or any(cand in t for t in item_tags_lower):
                            return pkg.get("id")

        return None

    def _create_independent_package_for_item(self, domain_key: str, sub_id: str, item: IngestedItem) -> str:
        """
        为二级类别下的独立新项目自动创建专属的独立资产包（标签）：
        智能从标题提炼独立项目名，彻底避免粗暴多项目名拼接
        """
        dom_info = PRIMARY_DOMAINS.get(domain_key, PRIMARY_DOMAINS["inbox"])
        sub_name = dom_info.get("sub_categories", {}).get(sub_id, {}).get("name", sub_id)

        # 提炼项目主体名称
        title_clean = item.title.strip()
        # 移除如 "用"、"把"、"附教程"、"史诗级更新" 等常见营销前缀后缀
        title_clean = re.sub(r'^(用|把|基于|让)\s*', '', title_clean)
        extracted = re.split(r'[：:—\-|，,]|（|\(|附教程|史诗级', title_clean)[0].strip()
        if len(extracted) < 2 or len(extracted) > 28:
            extracted = title_clean[:20].strip()

        # 生成干净 slug
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', item.slug()[:20]).strip('_').lower()
        if not slug:
            slug = f"project_{datetime.now().strftime('%m%d%H%M')}"
        new_pkg_id = f"{domain_key}_{slug}"
        if (self.packages_dir / new_pkg_id).exists():
            new_pkg_id = f"{new_pkg_id}_{datetime.now().strftime('%H%M%S')}"

        pkg_display_name = f"{extracted}"
        self.create_package(
            package_id=new_pkg_id,
            name=pkg_display_name,
            description=item.summary or f"{dom_info['name']} > {sub_name} 独立子项目知识资产",
            domain=domain_key,
            sub_category=sub_id,
            tags=[dom_info['name'], sub_name, extracted] + item.tags[:3]
        )
        return new_pkg_id

    def route_item_to_package(
        self,
        item: IngestedItem,
        preferred_package: Optional[str] = None,
        preferred_domain: Optional[str] = None,
        preferred_sub_category: Optional[str] = None
    ) -> str:
        """
        智能多级归类路由：根据实体元数据、领域偏好、子方向与关键词密度，将知识精准路由到最适合的资产包
        """
        meta_dict = getattr(item, "metadata", {}) or {}
        target_pkg = preferred_package or meta_dict.get("preferred_package")
        raw_dom = preferred_domain or meta_dict.get("domain")
        target_domain = raw_dom if (raw_dom and raw_dom in PRIMARY_DOMAINS) else (preferred_domain if preferred_domain else None)
        target_sub_cat = preferred_sub_category or meta_dict.get("sub_category")

        search_blob = f"{item.title} {item.summary} {' '.join(item.tags)} {item.content_markdown[:1000]}".lower()

        # 1. 显式指定了资产包
        if target_pkg:
            clean_pkg_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', target_pkg).lower().strip('_')
            # 若已存在同名资产包直接返回
            if (self.packages_dir / clean_pkg_id).exists():
                return clean_pkg_id
            for p in self.list_packages():
                if p.get("id") == clean_pkg_id or p.get("name") == target_pkg:
                    return p.get("id")
            
            # 若不存在则创建
            domain_val = target_domain or "inbox"
            sub_id, _ = resolve_sub_category(domain_val, search_blob)
            self.create_package(clean_pkg_id, name=target_pkg, domain=domain_val, sub_category=sub_id)
            return clean_pkg_id

        # 2. 显式指定了一级领域与子方向 (或从 item.metadata 读取)
        if target_domain:
            domain_key = resolve_domain(target_domain)
            sub_id = target_sub_cat
            if not sub_id:
                sub_id, sub_name = resolve_sub_category(domain_key, search_blob)
            
            # 检查在当前子类别下，是否有强匹配相同实体/项目的已有资产包
            matched_pkg_id = self._find_matching_package_in_sub_category(domain_key, sub_id, item, search_blob)
            if matched_pkg_id:
                return matched_pkg_id

            # 若属于该子类别下的新独立项目/工具，创建专属独立资产包（标签）
            return self._create_independent_package_for_item(domain_key, sub_id, item)

        # 3. 智能语义加权匹配：先精准识别所属子方向与一级领域
        best_domain_key = None
        best_sub_id = None
        highest_score = 0

        for dom_key, dom_data in PRIMARY_DOMAINS.items():
            if dom_key == "inbox":
                continue
            for sub_key, sub_data in dom_data.get("sub_categories", {}).items():
                score = 0
                matched_kws = []
                for kw in sub_data.get("keywords", []):
                    kw_lower = kw.lower()
                    if kw_lower in search_blob:
                        matched_kws.append(kw_lower)
                        # 核心关键词在标题或标签中权重翻倍
                        weight = 3 if (kw_lower in item.title.lower() or any(kw_lower in t.lower() for t in item.tags)) else 1
                        score += weight
                # 需命中至少2个不同关键词或单一高密度核心词(score >= 4)才建立强关联
                if (len(matched_kws) >= 2 or score >= 4) and score > highest_score:
                    highest_score = score
                    best_domain_key = dom_key
                    best_sub_id = sub_key

        # 若命中特定子方向 (得分 >= 3)
        if best_domain_key and best_sub_id and highest_score >= 3:
            # 检查在当前子类别下，是否有强匹配相同实体/项目的已有资产包
            matched_pkg_id = self._find_matching_package_in_sub_category(best_domain_key, best_sub_id, item, search_blob)
            if matched_pkg_id:
                return matched_pkg_id

            # 若属于该子方向的新独立项目/工具，创建专属独立资产包（标签）
            return self._create_independent_package_for_item(best_domain_key, best_sub_id, item)

        # 4. 兜底通用收件箱
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

    def classify_content(self, item: IngestedItem) -> Dict[str, Any]:
        """
        智能分类置信度判定：评估内容是否能被现有分类表结构化。
        若置信度不足 (无法精准结构化归类)，提炼智能推荐新分类，供弹窗交互决策。
        """
        meta_dict = getattr(item, "metadata", {}) or {}
        target_pkg = meta_dict.get("preferred_package")
        raw_domain = meta_dict.get("domain")
        target_domain = raw_domain if (raw_domain and raw_domain in PRIMARY_DOMAINS) else None
        target_sub = meta_dict.get("sub_category")

        # 若内容已显式指定了资产包或领域
        if target_pkg or target_domain:
            d_key = target_domain or "inbox"
            s_key = target_sub or "general"
            return {
                "is_matched": True,
                "matched_domain": d_key,
                "matched_sub_category": s_key,
                "score": 10,
                "suggested": None
            }

        search_blob = f"{item.title} {item.summary} {' '.join(item.tags)} {item.content_markdown[:1000]}".lower()

        best_domain_key = None
        best_sub_id = None
        highest_score = 0

        for dom_key, dom_data in PRIMARY_DOMAINS.items():
            if dom_key == "inbox":
                continue
            for sub_key, sub_data in dom_data.get("sub_categories", {}).items():
                score = 0
                matched_kws = []
                for kw in sub_data.get("keywords", []):
                    kw_lower = kw.lower()
                    if kw_lower in search_blob:
                        matched_kws.append(kw_lower)
                        weight = 3 if (kw_lower in item.title.lower() or any(kw_lower in t.lower() for t in item.tags)) else 1
                        score += weight
                if (len(matched_kws) >= 2 or score >= 4) and score > highest_score:
                    highest_score = score
                    best_domain_key = dom_key
                    best_sub_id = sub_key

        # 强匹配判定 (至少命中2个不同关键词或得分 >= 3)
        if best_domain_key and best_sub_id and highest_score >= 3:
            return {
                "is_matched": True,
                "matched_domain": best_domain_key,
                "matched_sub_category": best_sub_id,
                "score": highest_score,
                "suggested": None
            }

        # 无法按照目前分类表结构化：生成智能推荐新类别
        title_lower = (item.title + " " + item.summary).lower()
        if any(k in title_lower for k in ["医学", "医疗", "医药", "健康科普", "针灸", "穴位", "临床", "疾病", "养生"]):
            sug_domain_name = "生命健康与医药前沿"
            sug_domain_key = "health_medicine"
            sug_domain_icon = "🧬"
            sug_sub_name = "临床诊疗与健康科普"
            sug_sub_key = "clinical_health"
            sug_sub_icon = "💊"
        elif any(k in title_lower for k in ["游戏研发", "游戏引擎", "玩法设计", "虚幻引擎", "unity3d", "打击感", "关卡设计", "boss战"]):
            sug_domain_name = "游戏研发与互动叙事"
            sug_domain_key = "game_dev"
            sug_domain_icon = "🎮"
            sug_sub_name = "游戏引擎与关卡机制"
            sug_sub_key = "mechanics"
            sug_sub_icon = "🕹️"
        elif any(k in title_lower for k in ["法律", "法规", "合规审查", "合同法", "诉讼", "律师", "知识产权", "版权侵权"]):
            sug_domain_name = "法律合规与商业法务"
            sug_domain_key = "law_compliance"
            sug_domain_icon = "⚖️"
            sug_sub_name = "企业法务与合同审查"
            sug_sub_key = "compliance_review"
            sug_sub_icon = "📜"
        elif any(k in title_lower for k in ["金融投资", "财务报表", "股票市场", "量化交易", "公司估值", "宏观经济", "基金理财"]):
            sug_domain_name = "金融投资与量化经济"
            sug_domain_key = "finance_investing"
            sug_domain_icon = "📈"
            sug_sub_name = "宏观研报与投资逻辑"
            sug_sub_key = "macro_investment"
            sug_sub_icon = "💹"
        elif any(k in title_lower for k in ["美食", "料理", "烹饪", "咖啡", "烘焙", "拉花", "餐厅", "甜点", "西点"]):
            sug_domain_name = "美食烹饪与生活艺术"
            sug_domain_key = "lifestyle_culinary"
            sug_domain_icon = "☕"
            sug_sub_name = "餐饮工艺与精品甜点"
            sug_sub_key = "craft_culinary"
            sug_sub_icon = "🥐"
        else:
            clean_tag = item.tags[0] if (item.tags and len(item.tags[0]) <= 8) else item.title[:8]
            clean_tag = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', clean_tag) or "新兴专题"
            sug_domain_name = f"{clean_tag}研究与探索"
            sug_domain_key = re.sub(r'[^a-zA-Z0-9_]', '_', clean_tag).lower().strip('_') or "new_topic"
            sug_domain_icon = "💡"
            sug_sub_name = f"{clean_tag}实战方法论"
            sug_sub_key = f"{sug_domain_key}_practices"
            sug_sub_icon = "📌"

        return {
            "is_matched": False,
            "matched_domain": None,
            "matched_sub_category": None,
            "score": highest_score,
            "suggested": {
                "domain_key": sug_domain_key,
                "domain_name": sug_domain_name,
                "domain_icon": sug_domain_icon,
                "sub_key": sug_sub_key,
                "sub_name": sug_sub_name,
                "sub_icon": sug_sub_icon
            }
        }

    def create_custom_domain_and_package(
        self,
        domain_key: str,
        domain_name: str,
        domain_icon: str,
        sub_key: str,
        sub_name: str,
        sub_icon: str
    ) -> str:
        """用户确认允许创建新类别后，持久化注册领域与子方向并创建资产包"""
        clean_dom = re.sub(r'[^a-zA-Z0-9_\-]', '_', domain_key).lower().strip('_')
        clean_sub = re.sub(r'[^a-zA-Z0-9_\-]', '_', sub_key).lower().strip('_')
        save_custom_domain(clean_dom, domain_name, domain_icon, clean_sub, sub_name, sub_icon)

        pkg_id = f"{clean_dom}_{clean_sub}"
        pkg_name = f"{sub_name}知识资产包"
        if not (self.packages_dir / pkg_id).exists():
            self.create_package(
                package_id=pkg_id,
                name=pkg_name,
                description=f"{domain_name} > {sub_name} 知识资产沉淀",
                domain=clean_dom,
                sub_category=clean_sub,
                tags=[domain_name, sub_name, "自定义新类别"]
            )
        return pkg_id

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
