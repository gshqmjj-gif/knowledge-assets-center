"""
WeChat Channels (视频号) Crawler
处理微信视频号分享链接、解析文本、提取关键帧与要点
"""
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import DEFAULT_USER_AGENT, FFMPEG_BIN, TEMP_DIR, VIDEO_SETTINGS
from crawlers.base import BaseCrawler, IngestedItem

logger = logging.getLogger("hermes.wechat_channels")

class WeChatChannelsCrawler(BaseCrawler):
    name = "wechat_channels"

    def match(self, input_str: str) -> bool:
        if "sph" in input_str or "channels" in input_str or "findermp" in input_str or "视频号" in input_str:
            return True
        if input_str.startswith("http"):
            parsed = urlparse(input_str)
            if "weixin.qq.com" in parsed.netloc and ("sph" in parsed.path or "video" in parsed.path):
                return True
        return False

    def _extract_keyframes(self, video_path_or_url: str, out_dir: Path, prefix: str) -> List[str]:
        """从视频或短片中提取 4 张关键帧 (不留原视频)"""
        out_dir.mkdir(parents=True, exist_ok=True)
        captured = []
        # 截取前、中、后若干帧
        timestamps = ["00:00:02", "00:00:08", "00:00:15", "00:00:25"]
        for i, ts in enumerate(timestamps, 1):
            frame_name = f"{prefix}_frame_{i:02d}.jpg"
            frame_path = out_dir / frame_name
            cmd = [
                FFMPEG_BIN,
                "-ss", ts,
                "-i", video_path_or_url,
                "-vframes", "1",
                "-q:v", "2",
                "-vf", f"scale={VIDEO_SETTINGS['keyframe_width']}:-1",
                "-y",
                str(frame_path)
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, timeout=12)
                if res.returncode == 0 and frame_path.exists() and frame_path.stat().st_size > 500:
                    captured.append(frame_name)
            except Exception:
                pass
        return captured

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        title = "微信视频号分享"
        author = "微信创作者"
        desc = ""
        url = input_str.strip()
        keyframes = []

        dest_keyframes_dir = kwargs.get("keyframes_dir") or (TEMP_DIR / "keyframes")

        # 判断是否为 URL 还是分享卡片文字
        if url.startswith("http"):
            try:
                headers = {"User-Agent": DEFAULT_USER_AGENT}
                with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        og_title = soup.find("meta", property="og:title")
                        if og_title and og_title.get("content"):
                            title = og_title["content"].strip()
                        og_desc = soup.find("meta", property="og:description")
                        if og_desc and og_desc.get("content"):
                            desc = og_desc["content"].strip()
                        author_tag = soup.find("div", class_="account_name") or soup.find("meta", property="og:site_name")
                        if author_tag:
                            author = author_tag.get("content") or author_tag.get_text(strip=True)
            except Exception as e:
                logger.warning(f"Could not scrape channels URL directly: {e}")
        else:
            # 文本分享解析 (常见格式：【视频号】作者名：描述内容...)
            desc = input_str
            title_match = re.search(r'【(.*?)】', input_str)
            if title_match:
                author = title_match.group(1)
            first_line = [l.strip() for l in input_str.splitlines() if l.strip()]
            if first_line:
                title = first_line[0][:40]

        # 如果传入了临时视频文件进行抽帧
        video_temp_file = kwargs.get("video_file")
        if video_temp_file and Path(video_temp_file).exists():
            vpath = Path(video_temp_file)
            keyframes = self._extract_keyframes(str(vpath), dest_keyframes_dir, prefix="wechat_sph")
            # 严格规范：立即删除原视频文件
            try:
                vpath.unlink()
            except Exception:
                pass

        # 构造 Markdown
        md_lines = [
            f"# 视频号: {title}\n",
            f"> **创作者**: {author} | **来源平台**: 微信视频号",
            f"> **链接/原记录**: {url}\n",
            "## 📌 视频要点速览",
            f"{desc or '暂无详细文字描述，详情请参考提取的关键帧与原视频号动态。'}\n"
        ]

        if keyframes:
            md_lines.append("## 🖼️ 核心关键帧抓拍")
            for kf in keyframes:
                md_lines.append(f"- ![{kf}](keyframes/{kf})")

        md_lines.append("\n## 💡 知识沉淀与应用思考")
        md_lines.append("1. **核心场景**: 微信生态下的短平快知识点输出与展示技巧。")
        md_lines.append("2. **转化建议**: 提炼为 Cursor / Agent 可复用的提示词或功能模块。")

        return IngestedItem(
            title=title,
            source_type="wechat_channel",
            source_url=url,
            author=author,
            published_date=datetime.now().strftime("%Y-%m-%d"),
            summary=f"微信视频号《{title}》({author})，提炼了关键帧及技术要点。",
            content_markdown="\n".join(md_lines),
            key_points=[title, f"作者: {author}"],
            tags=["视频号", "微信生态", author],
            keyframes=keyframes,
            metadata={"crawler": "WeChatChannelsCrawler", "raw_video_deleted": True}
        )
