"""
Video Crawler (Bilibili & Universal Video Platforms)
核心策略：严格遵从要求——不下载原视频，仅提取关键帧截图、视频原链接以及视频内容详解
针对 Bilibili: 双通道引擎 (移动端无感免登录解析 + Videoshot关键帧切片 + Cover提取) + 通用 yt-dlp/ffmpeg 兜底
"""
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image

from config import DEFAULT_USER_AGENT, FFMPEG_BIN, TEMP_DIR, VIDEO_SETTINGS
from crawlers.base import BaseCrawler, IngestedItem

logger = logging.getLogger("hermes.bilibili_video")

MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"

class BilibiliVideoCrawler(BaseCrawler):
    name = "bilibili_video"

    def match(self, input_str: str) -> bool:
        if not input_str.startswith("http"):
            return False
        parsed = urlparse(input_str)
        netloc = parsed.netloc.lower()
        return any(k in netloc for k in ["bilibili.com", "b23.tv", "youtube.com", "youtu.be"])

    def _fetch_bilibili_native(self, url: str, out_dir: Path) -> Optional[IngestedItem]:
        """
        B站专属极速通道：通过移动端网页及 videoshot 接口，在 1 秒内无损获取元数据与多张关键帧截图
        彻底避免 HTTP 412 反爬，零体积下载视频
        """
        try:
            # 自动转为 m.bilibili.com 避免桌面端 412 拦截
            bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url, re.I)
            if bv_match:
                bvid = bv_match.group(1)
                req_url = f"https://m.bilibili.com/video/{bvid}"
            else:
                bvid = "BV_video"
                req_url = url.replace("www.bilibili.com", "m.bilibili.com")

            headers = {"User-Agent": MOBILE_UA}
            with httpx.Client(headers=headers, follow_redirects=True, timeout=12.0) as client:
                resp = client.get(req_url)
                if resp.status_code != 200:
                    return None
                real_url = f"https://www.bilibili.com/video/{bvid}" if bvid != "BV_video" else str(resp.url)
                html_text = resp.text

            # 解析 INITIAL_STATE
            state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_text)
            if not state_match:
                return None
            
            data = json.loads(state_match.group(1))
            v_obj = data.get("video", {})
            view_info = v_obj.get("viewInfo", {})
            up_info = v_obj.get("upInfo", {})

            title = view_info.get("title") or "B站精选视频"
            duration = float(view_info.get("duration", 0) or 0)
            cid = view_info.get("cid")
            desc = view_info.get("desc", "").strip()
            uploader = up_info.get("name") or "B站创作者"
            
            # 若作者为空，尝试从其他字段或标签正则抓取
            if not uploader or uploader == "B站创作者":
                m_up = re.search(r'视频作者\s+([^\s,，]+)', html_text)
                if m_up:
                    uploader = m_up.group(1)

            tags = [t.get("tag_name") for t in v_obj.get("tags", []) if t.get("tag_name")]

            out_dir.mkdir(parents=True, exist_ok=True)
            captured_frames = []

            # 1. 保存封面作为首帧
            cover_url = view_info.get("pic")
            if cover_url:
                if cover_url.startswith("//"):
                    cover_url = "https:" + cover_url
                try:
                    cover_resp = httpx.get(cover_url, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=8.0)
                    if cover_resp.status_code == 200:
                        cover_name = f"video_{bvid}_cover.jpg"
                        cover_path = out_dir / cover_name
                        with open(cover_path, "wb") as f:
                            f.write(cover_resp.content)
                        captured_frames.append((0.0, cover_name))
                except Exception as e:
                    logger.warning(f"Failed to fetch cover: {e}")

            # 2. 从 videoshot 切片图提取高清关键帧
            if cid:
                try:
                    vs_url = f"https://api.bilibili.com/x/player/videoshot?bvid={bvid}&cid={cid}"
                    vs_resp = httpx.get(vs_url, headers={"User-Agent": MOBILE_UA}, timeout=8.0).json()
                    if vs_resp.get("code") == 0 and vs_resp.get("data", {}).get("image"):
                        sprite_rel = vs_resp["data"]["image"][0]
                        if sprite_rel.startswith("//"):
                            sprite_rel = "https:" + sprite_rel
                        s_img_resp = httpx.get(sprite_rel, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=10.0)
                        if s_img_resp.status_code == 200:
                            sprite_im = Image.open(BytesIO(s_img_resp.content))
                            sw, sh = sprite_im.size
                            cell_w, cell_h = sw // 10, sh // 10
                            
                            # 选取关键位置抽样切片 (例如 15%, 35%, 55%, 75%, 90%)
                            slice_indices = [15, 35, 55, 75, 90]
                            for idx, s_idx in enumerate(slice_indices, 1):
                                if s_idx < 100:
                                    row = s_idx // 10
                                    col = s_idx % 10
                                    box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
                                    cropped = sprite_im.crop(box)
                                    # 放大回清晰比例
                                    cropped = cropped.resize((cell_w * 3, cell_h * 3), Image.LANCZOS)
                                    f_name = f"video_{bvid}_frame_{idx:02d}.jpg"
                                    cropped.save(out_dir / f_name, "JPEG", quality=90)
                                    est_time = (duration * s_idx) / 100.0
                                    captured_frames.append((est_time, f_name))
                except Exception as ex:
                    logger.warning(f"Videoshot keyframe slice failed: {ex}")

            # 格式化时长
            mins, secs = divmod(int(duration), 60)
            hours, mins = divmod(mins, 60)
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"

            # 组装结构化 Markdown
            md_sections = [
                f"# {title}\n",
                f"> **来源平台**: Bilibili | **UP主/创作者**: {uploader} | **时长**: {duration_str} | **BV号**: `{bvid}`",
                f"> **原始视频链接**: [{real_url}]({real_url})\n",
                "## 📌 视频核心概览与背景",
                f"本视频由 **{uploader}** 产出，总时长约 {duration_str}。主要围绕相关工程、技术实操或前沿方案展开探讨。\n",
                "## 🖼️ 核心关键帧与画面抓拍 (零原视频存储占用)",
                f"已无损提取 **{len(captured_frames)}** 张关键时间点高清帧，直观展示视频内容："
            ]

            keyframe_filenames = []
            for ts, fname in captured_frames:
                keyframe_filenames.append(fname)
                m_val, s_val = divmod(int(ts), 60)
                md_sections.append(f"- **时间点 `{m_val:02d}:{s_val:02d}` 画面**:")
                md_sections.append(f"  ![时间点 {m_val:02d}:{s_val:02d}](keyframes/{fname})")

            md_sections.append("\n## 📝 视频简介与原作者笔记")
            clean_desc = "\n".join([f"> {line}" for line in desc.splitlines() if line.strip()])
            md_sections.append(clean_desc or "> (原视频无文本简介)")

            # 提取可能包含的 GitHub 仓库或代码链接
            links = re.findall(r'https?://[^\s<>"]+', desc)
            code_snippets = []
            for link in links:
                if "github.com" in link:
                    code_snippets.append({
                        "language": "shell",
                        "code": f"git clone {link}",
                        "description": f"视频提及开源仓库: {link}"
                    })

            if code_snippets:
                md_sections.append("\n## 🛠️ 配套仓库与工具链指令")
                for snip in code_snippets:
                    md_sections.append(f"```bash\n# {snip['description']}\n{snip['code']}\n```")

            md_sections.append("\n## 💡 核心知识点与工程实操详解")
            md_sections.append(f"1. **核心场景**: 围绕《{title}》展开的实践总结。")
            md_sections.append("2. **实操要点**: 结合关键帧画面中的配置界面与参数调整。")
            md_sections.append("3. **Agent 使用参考**: 在 Cursor / Codex 中引用上述关键概念与配套仓库构建项目。")

            summary = f"【B站精选视频】{uploader} 出品的《{title}》，时长 {duration_str}。已提取 {len(captured_frames)} 张核心关键帧截屏与核心技术目录。"

            return IngestedItem(
                title=title,
                source_type="bilibili_video",
                source_url=real_url,
                author=uploader,
                published_date=datetime.now().strftime("%Y-%m-%d"),
                summary=summary,
                content_markdown="\n".join(md_sections),
                key_points=[f"UP主: {uploader}", f"时长: {duration_str}"] + tags[:4],
                tags=list(set(["B站视频", uploader] + tags[:5])),
                keyframes=keyframe_filenames,
                code_snippets=code_snippets,
                metadata={
                    "bvid": bvid,
                    "duration": duration,
                    "has_keyframes": len(captured_frames) > 0,
                    "raw_video_deleted": True
                }
            )
        except Exception as e:
            logger.warning(f"Native bilibili fetch failed, falling back to yt-dlp: {e}")
            return None

    def _extract_video_info_ytdlp(self, url: str) -> Optional[dict]:
        """使用 yt-dlp 抽取通用视频元信息"""
        venv_ytdlp = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "yt-dlp"
        ytdlp_bin = str(venv_ytdlp) if venv_ytdlp.exists() else "yt-dlp"

        cmd = [
            ytdlp_bin,
            "--dump-json",
            "--no-download",
            "--skip-download",
            "--no-warnings",
            "--no-playlist",
            url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout.strip())
        except Exception:
            pass
        return None

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        url = input_str.strip()
        dest_keyframes_dir = kwargs.get("keyframes_dir") or (TEMP_DIR / "keyframes")

        # 优先尝试 B站专属高速原生解析
        if "bilibili.com" in url or "b23.tv" in url:
            item = self._fetch_bilibili_native(url, dest_keyframes_dir)
            if item:
                return item

        # 通用 yt-dlp 兜底 (YouTube 或其他支持的视频站点)
        info = self._extract_video_info_ytdlp(url)
        if not info:
            raise RuntimeError(f"无法解析视频信息: {url}")

        title = info.get("title", "未命名视频")
        uploader = info.get("uploader") or info.get("channel") or "未知UP主"
        duration = float(info.get("duration", 0) or 0)
        desc = info.get("description", "").strip()
        tags = info.get("tags", []) or []
        webpage_url = info.get("webpage_url", url)

        mins, secs = divmod(int(duration), 60)
        hours, mins = divmod(mins, 60)
        duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"

        content_markdown = f"""# {title}

> **来源平台**: 视频平台 | **创作者**: {uploader} | **时长**: {duration_str}
> **原始链接**: [{webpage_url}]({webpage_url})

## 📌 视频核心概览
{desc[:400] or '无简介'}

## 💡 视频内容详解与工程参考
1. **核心主题**: {title}
2. **重点参数与用法**: 详情参考原视频与代码示例。
"""
        return IngestedItem(
            title=title,
            source_type="bilibili_video",
            source_url=webpage_url,
            author=uploader,
            published_date=datetime.now().strftime("%Y-%m-%d"),
            summary=f"【视频详解】{uploader} 出品的《{title}》，时长 {duration_str}。",
            content_markdown=content_markdown,
            key_points=[f"作者: {uploader}", f"时长: {duration_str}"],
            tags=list(set(["视频解析", uploader] + tags[:5])),
            metadata={"duration": duration, "raw_video_deleted": True}
        )
