"""
General Webpage Crawler
通用网页与技术博客采集器 (支持 Zhihu, GitHub, Juejin, CSDN, 个人独立博客等)
"""
import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import DEFAULT_USER_AGENT
from crawlers.base import BaseCrawler, IngestedItem

logger = logging.getLogger("hermes.webpage")

class WebpageCrawler(BaseCrawler):
    name = "webpage"

    def match(self, input_str: str) -> bool:
        if not input_str.startswith("http"):
            return False
        return True

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        url = input_str.strip()
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

        with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html_text = resp.text

        soup = BeautifulSoup(html_text, "lxml")

        # 移除无关噪音标签
        for bad_tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "svg", "form"]):
            bad_tag.decompose()

        # 1. 提取标题
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
        if not title and soup.title:
            title = soup.title.get_text(strip=True)
        if not title:
            parsed = urlparse(url)
            title = f"网页内容 ({parsed.netloc})"

        # 2. 提取作者
        author = ""
        meta_author = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="author")
        if meta_author and meta_author.get("content"):
            author = meta_author["content"].strip()
        if not author:
            parsed = urlparse(url)
            author = parsed.netloc

        # 3. 寻找正文核心容器
        content_container = (
            soup.find("article") or
            soup.find("main") or
            soup.find(class_=re.compile(r"content|post-body|article-body|entry-content|markdown-body", re.I)) or
            soup.find(id=re.compile(r"content|post-body|article|main", re.I)) or
            soup.body
        )

        markdown_lines = []
        code_snippets = []
        key_points = []
        images = []

        if content_container:
            # 提取所有代码片段
            for pre in content_container.find_all("pre"):
                code_text = pre.get_text().strip()
                if len(code_text) > 15:
                    code_class = ""
                    code_elem = pre.find("code")
                    if code_elem and code_elem.get("class"):
                        code_class = " ".join(code_elem.get("class"))
                    
                    lang = "python"
                    if "js" in code_class or "javascript" in code_class:
                        lang = "javascript"
                    elif "ts" in code_class or "typescript" in code_class:
                        lang = "typescript"
                    elif "bash" in code_class or "sh" in code_class:
                        lang = "bash"
                    elif "json" in code_class:
                        lang = "json"

                    if not any(s["code"] == code_text for s in code_snippets):
                        code_snippets.append({
                            "language": lang,
                            "code": code_text,
                            "description": f"代码块 #{len(code_snippets)+1}"
                        })

            # 解析为 Markdown
            for elem in content_container.find_all(["h1", "h2", "h3", "h4", "p", "pre", "img", "li"]):
                if elem.name in ["h1", "h2", "h3", "h4"]:
                    t = elem.get_text(strip=True)
                    if t:
                        markdown_lines.append(f"\n{'#' * int(elem.name[1])} {t}\n")
                        key_points.append(t)
                elif elem.name == "p":
                    t = elem.get_text(strip=True)
                    if t:
                        markdown_lines.append(f"{t}\n")
                elif elem.name == "li":
                    t = elem.get_text(strip=True)
                    if t:
                        markdown_lines.append(f"- {t}\n")
                elif elem.name == "pre":
                    c = elem.get_text().strip()
                    if c:
                        markdown_lines.append(f"\n```\n{c}\n```\n")
                elif elem.name == "img":
                    src = elem.get("src") or elem.get("data-src")
                    if src and src.startswith("http"):
                        alt = elem.get("alt") or "配图"
                        markdown_lines.append(f"\n![{alt}]({src})\n")
                        images.append(src)

        content_markdown = "".join(markdown_lines).strip()
        if not content_markdown and content_container:
            content_markdown = content_container.get_text(separator="\n\n", strip=True)

        clean_text = re.sub(r'#|\*|`|\[|\]|\(http\S+\)|!\[.*?\]', '', content_markdown)
        clean_text = ' '.join(clean_text.split())
        summary = clean_text[:280] + ("..." if len(clean_text) > 280 else "")

        domain_host = urlparse(url).netloc
        tags = [domain_host, "网页资料"]

        return IngestedItem(
            title=title,
            source_type="webpage",
            source_url=url,
            author=author,
            published_date=datetime.now().strftime("%Y-%m-%d"),
            summary=summary,
            content_markdown=content_markdown,
            key_points=key_points[:8],
            tags=list(set(tags)),
            code_snippets=code_snippets,
            assets=images[:8],
            metadata={"domain": domain_host, "snippets_count": len(code_snippets)}
        )
