"""
Agent Exporter & Knowledge Retrieval Engine
负责便捷检索知识资产，并一键打包输出为适用于 Cursor、Codex、Hermes 等 Agent 的参考上下文
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from config import PACKAGES_DIR
from core.package_manager import KnowledgePackageManager

logger = logging.getLogger("hermes.exporter")

class AgentExporter:
    def __init__(self, package_manager: Optional[KnowledgePackageManager] = None):
        self.pm = package_manager or KnowledgePackageManager()

    def search(self, query: str) -> Dict[str, Any]:
        """
        全库综合检索：在资产包、来源文档、提取代码段中检索关键词
        """
        q = query.lower().strip()
        matched_packages = []
        matched_sources = []
        matched_snippets = []

        for pkg in self.pm.list_packages():
            pkg_id = pkg.get("id")
            pkg_name = pkg.get("name", "")
            pkg_desc = pkg.get("description", "")
            tags = [t.lower() for t in pkg.get("tags", [])]

            # 资产包层面匹配
            score = 0
            if q in pkg_name.lower():
                score += 10
            if q in pkg_desc.lower():
                score += 5
            if any(q in t for t in tags):
                score += 7

            if score > 0:
                matched_packages.append({
                    "id": pkg_id,
                    "name": pkg_name,
                    "description": pkg_desc,
                    "tags": pkg.get("tags", []),
                    "score": score
                })

            # 搜索 sources 目录下的具体文件
            pkg_dir = Path(pkg.get("path"))
            sources_dir = pkg_dir / "sources"
            if sources_dir.exists():
                for sf in sources_dir.glob("*.md"):
                    try:
                        content = sf.read_text(encoding="utf-8")
                        if q in sf.name.lower() or q in content.lower():
                            # 提取匹配上下文片段
                            idx = content.lower().find(q)
                            start = max(0, idx - 40)
                            end = min(len(content), idx + 80)
                            snippet_preview = content[start:end].replace("\n", " ")
                            matched_sources.append({
                                "package_id": pkg_id,
                                "package_name": pkg_name,
                                "filename": sf.name,
                                "path": str(sf),
                                "snippet": f"...{snippet_preview}..."
                            })
                    except Exception:
                        pass

            # 搜索 snippets 目录
            snippets_dir = pkg_dir / "snippets"
            if snippets_dir.exists():
                for sc in snippets_dir.iterdir():
                    if sc.is_file():
                        try:
                            s_content = sc.read_text(encoding="utf-8")
                            if q in sc.name.lower() or q in s_content.lower():
                                matched_snippets.append({
                                    "package_id": pkg_id,
                                    "package_name": pkg_name,
                                    "filename": sc.name,
                                    "path": str(sc)
                                })
                        except Exception:
                            pass

        return {
            "query": query,
            "packages": sorted(matched_packages, key=lambda x: x["score"], reverse=True),
            "sources": matched_sources[:15],
            "snippets": matched_snippets[:10]
        }

    def export_for_cursor(self, package_id: str, format_type: str = "mdc") -> str:
        """
        生成适用于 Cursor 的规则或上下文
        format_type: 'mdc' (Cursor Rule 文件) 或 'cursorrules'
        """
        pkg = self.pm.get_package(package_id)
        if not pkg:
            raise ValueError(f"资产包不存在: {package_id}")

        pkg_dir = Path(pkg.get("path"))
        pkg_name = pkg.get("name", package_id)
        description = pkg.get("description", "")
        tags = pkg.get("tags", [])

        # 收集代码片段
        snippets_text = []
        snippets_dir = pkg_dir / "snippets"
        if snippets_dir.exists():
            for sf in sorted(snippets_dir.iterdir())[:5]:
                if sf.is_file():
                    try:
                        c = sf.read_text(encoding="utf-8")
                        snippets_text.append(f"### {sf.name}\n```\n{c[:800]}\n```")
                    except Exception:
                        pass

        # 收集来源清单
        sources_list = [f"- {s.get('title')} ({s.get('type')}) - {s.get('url')}" for s in pkg.get("sources", [])[:8]]

        if format_type == "mdc":
            rule_content = f"""---
description: Project guidelines and architectural knowledge for {pkg_name}
globs: *
alwaysApply: false
---

# {pkg_name} - Cursor Rule & Knowledge Base Context

> **Asset Package**: `{package_id}` | **Tags**: `{', '.join(tags)}`
> **Description**: {description}

## 🎯 Engineering Directives for Cursor
1. When generating or refactoring code in this project, adhere strictly to the design patterns and best practices outlined below.
2. Modularize components cleanly and follow the conventions verified in our reference assets.
3. Reuse standard utilities and avoid re-inventing solutions that have established snippets.

## 🛠️ Verified Reference Code Snippets
{chr(10).join(snippets_text) if snippets_text else '> (Refer to package snippets directory for full examples)'}

## 📚 Knowledge Sources Referenced
{chr(10).join(sources_list) if sources_list else '> (No sources listed)'}
"""
            return rule_content.strip()
        else:
            return f"# Cursor Rules for {pkg_name}\n\n{description}\n\n" + "\n".join(snippets_text)

    def export_for_codex(self, package_id: str) -> str:
        """
        生成适用于 OpenAI Codex / Agent 的高浓度工程上下文 Prompt
        """
        pkg = self.pm.get_package(package_id)
        if not pkg:
            raise ValueError(f"资产包不存在: {package_id}")

        pkg_dir = Path(pkg.get("path"))
        agent_ctx_file = pkg_dir / "AGENT_CONTEXT.md"
        summary_file = pkg_dir / "SUMMARY.md"

        ctx_content = ""
        if agent_ctx_file.exists():
            ctx_content = agent_ctx_file.read_text(encoding="utf-8")
        elif summary_file.exists():
            ctx_content = summary_file.read_text(encoding="utf-8")

        prompt = f"""<SYSTEM_KNOWLEDGE_CONTEXT>
Knowledge Package: {pkg.get('name')} (ID: {package_id})
Domain: {pkg.get('domain')}
Tags: {', '.join(pkg.get('tags', []))}

{ctx_content}

[INSTRUCTIONS FOR CODEX / AI AGENT]:
- Use the above domain knowledge as authoritative project reference.
- Implement the requested user task using the patterns and code structures cataloged above.
</SYSTEM_KNOWLEDGE_CONTEXT>"""
        return prompt

    def export_for_hermes(self, package_id: str) -> str:
        """
        生成适用于 Hermes / Claude Code / Antigravity Agent 的专用知识注入包
        """
        pkg = self.pm.get_package(package_id)
        if not pkg:
            raise ValueError(f"资产包不存在: {package_id}")

        pkg_dir = Path(pkg.get("path"))
        summary_file = pkg_dir / "SUMMARY.md"
        summary_text = summary_file.read_text(encoding="utf-8") if summary_file.exists() else ""

        hermes_content = f"""# Hermes Asset Package Reference: {pkg.get('name')}

```yaml
package_id: {package_id}
domain: {pkg.get('domain')}
items_count: {pkg.get('item_count')}
updated_at: {pkg.get('updated_at')}
```

## Distilled Knowledge & Guidelines
{summary_text}

## Agent Action Plan:
- Incorporate this knowledge package into the current subproject architecture.
- Keep dependencies lean and preserve documentation integrity.
"""
        return hermes_content

    def copy_to_clipboard(self, text: str) -> bool:
        """一键复制到 macOS 剪贴板 (pbcopy)"""
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=text)
            return p.returncode == 0
        except Exception as e:
            logger.warning(f"Failed to copy to clipboard: {e}")
            return False

    def read_from_clipboard(self) -> str:
        """从 macOS 剪贴板读取内容 (pbpaste)"""
        try:
            res = subprocess.run(["pbpaste"], capture_output=True, text=True, check=False)
            return res.stdout.strip()
        except Exception:
            return ""
