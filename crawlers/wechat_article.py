"""
WeChat Official Account Article Crawler
微信公众号文章解析采集器
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import DEFAULT_USER_AGENT, TEMP_DIR
from crawlers.base import BaseCrawler, IngestedItem

logger = logging.getLogger("hermes.wechat_article")

class WeChatArticleCrawler(BaseCrawler):
    name = "wechat_article"

    def match(self, input_str: str) -> bool:
        if not input_str.startswith("http"):
            return False
        parsed = urlparse(input_str)
        return "mp.weixin.qq.com" in parsed.netloc

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

        # 1. 提取标题
        title = ""
        title_tag = soup.find("h1", class_="rich_media_title") or soup.find(id="activity-name")
        if title_tag:
            title = title_tag.get_text(strip=True)
        if not title:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
        if not title and soup.title:
            title = soup.title.get_text(strip=True)
        if not title:
            title = "微信公众号文章"

        # 2. 提取作者/公众号名称
        author = ""
        author_tag = soup.find(id="js_name") or soup.find("a", class_="rich_media_meta_link")
        if author_tag:
            author = author_tag.get_text(strip=True)
        if not author:
            meta_author = soup.find("meta", property="og:article:author")
            if meta_author and meta_author.get("content"):
                author = meta_author["content"].strip()

        # 3. 提取发布时间
        published_date = ""
        time_match = re.search(r'var\s+publish_time\s*=\s*"(\d+)";', html_text) or \
                     re.search(r'createTime\s*:\s*\'?(\d+)\'?', html_text)
        if time_match:
            try:
                ts = int(time_match.group(1))
                published_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        if not published_date:
            published_date = datetime.now().strftime("%Y-%m-%d")

        # 4. 正文解析与清洗，并将关键配图下载为本地离线副本 (杜绝防盗链与链接失效)
        content_div = soup.find(id="js_content")
        markdown_lines = []
        code_snippets = []
        key_points = []
        images = []
        dest_assets_dir = kwargs.get("assets_dir") or (TEMP_DIR / "assets")
        dest_assets_dir.mkdir(parents=True, exist_ok=True)

        img_counter = 0

        if content_div:
            # 提取所有代码块
            for pre in content_div.find_all(["pre", "code"]):
                code_text = pre.get_text().strip()
                if len(code_text) > 20 and "\n" in code_text:
                    lang = "python"
                    first_line = code_text.splitlines()[0].lower()
                    if "npm" in first_line or "import " in first_line and ("react" in code_text or "const " in code_text):
                        lang = "typescript"
                    elif "docker" in first_line or "pip " in first_line or "git " in first_line:
                        lang = "bash"
                    
                    # 避免重复
                    if not any(s["code"] == code_text for s in code_snippets):
                        code_snippets.append({
                            "language": lang,
                            "code": code_text,
                            "description": f"代码片段 #{len(code_snippets)+1}"
                        })

            # 清洗正文元素
            for elem in content_div.descendants:
                if elem.name in ["h1", "h2", "h3", "h4"]:
                    h_text = elem.get_text(strip=True)
                    if h_text:
                        level = "#" * int(elem.name[1])
                        markdown_lines.append(f"\n{level} {h_text}\n")
                        key_points.append(h_text)
                elif elem.name == "p":
                    p_text = elem.get_text(strip=True)
                    if p_text:
                        markdown_lines.append(f"{p_text}\n")
                elif elem.name == "img":
                    src = elem.get("data-src") or elem.get("src")
                    if src and src.startswith("http"):
                        alt = elem.get("alt") or f"插图_{img_counter+1}"
                        # 离线下载文章所有配图 (附带微信防盗链 Referer 请求头)
                        local_img_name = ""
                        if img_counter < 60:
                            try:
                                img_counter += 1
                                safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', title)[:20].strip('_')
                                ext = "png"
                                if "wx_fmt=jpeg" in src or "wx_fmt=jpg" in src:
                                    ext = "jpg"
                                elif "wx_fmt=gif" in src:
                                    ext = "gif"
                                local_filename = f"wechat_{safe_slug}_{img_counter:02d}.{ext}"
                                local_img_path = dest_assets_dir / local_filename
                                if not local_img_path.exists():
                                    img_headers = {
                                        "User-Agent": DEFAULT_USER_AGENT,
                                        "Referer": "https://mp.weixin.qq.com/",
                                        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
                                    }
                                    with httpx.Client(headers=img_headers, timeout=12.0) as img_client:
                                        r_img = img_client.get(src)
                                        if r_img.status_code == 200 and len(r_img.content) > 1000:
                                            with open(local_img_path, "wb") as f_img:
                                                f_img.write(r_img.content)
                                            local_img_name = local_filename
                                            images.append(str(local_img_path))
                                else:
                                    local_img_name = local_filename
                                    images.append(str(local_img_path))
                            except Exception as e:
                                logger.warning(f"Failed to fetch image offline: {e}")

                        if local_img_name:
                            markdown_lines.append(f"\n![{alt}](assets/{local_img_name})\n")
                        else:
                            markdown_lines.append(f"\n![{alt}]({src})\n")
                elif elem.name == "pre":
                    code = elem.get_text().strip()
                    if code:
                        markdown_lines.append(f"\n```\n{code}\n```\n")

        # 若遍历解析内容较少，直接纯文本回退
        content_markdown = "".join(markdown_lines).strip()
        if not content_markdown and content_div:
            content_markdown = content_div.get_text(separator="\n\n", strip=True)

        # 5. 自动提取标签与生成简述
        tags = ["微信公众号"]
        if author:
            tags.append(author)
        for kw in ["架构", "AI", "Agent", "Python", "前端", "爬虫", "Blender", "工作流", "全栈"]:
            if kw.lower() in title.lower() or kw.lower() in content_markdown[:1000].lower():
                tags.append(kw)

        # 提炼摘要 (前300字或关键句)
        summary = ""
        clean_text = re.sub(r'#|\*|`|\[|\]|\(http\S+\)|!\[.*?\]', '', content_markdown)
        clean_text = ' '.join(clean_text.split())
        if clean_text:
            summary = clean_text[:280] + ("..." if len(clean_text) > 280 else "")

        return IngestedItem(
            title=title,
            source_type="wechat_article",
            source_url=url,
            author=author,
            published_date=published_date,
            summary=summary,
            content_markdown=content_markdown,
            key_points=key_points[:8],
            tags=list(set(tags)),
            code_snippets=code_snippets,
            assets=images[:10],
            metadata={
                "crawler": "WeChatArticleCrawler",
                "images_count": len(images),
                "snippets_count": len(code_snippets)
            }
        )
