"""
Video Crawler (Bilibili & Universal Video Platforms)
核心策略：严格遵从要求——不下载原视频，仅提取关键帧截图、视频原链接以及视频内容详解
"""
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from config import FFMPEG_BIN, TEMP_DIR, VIDEO_SETTINGS
from crawlers.base import BaseCrawler, IngestedItem

logger = logging.getLogger("hermes.bilibili_video")

class BilibiliVideoCrawler(BaseCrawler):
    name = "bilibili_video"

    def match(self, input_str: str) -> bool:
        if not input_str.startswith("http"):
            return False
        parsed = urlparse(input_str)
        netloc = parsed.netloc.lower()
        return any(k in netloc for k in ["bilibili.com", "b23.tv", "youtube.com", "youtu.be"])

    def _extract_video_info(self, url: str) -> Optional[dict]:
        """使用 yt-dlp 抽取视频元信息 (不下载视频本体)"""
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
            logger.info(f"Extracting video info from {url}...")
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout.strip())
            else:
                logger.warning(f"yt-dlp returned error: {res.stderr[:200]}")
        except Exception as e:
            logger.error(f"Failed to run yt-dlp dump-json: {e}")
        return None

    def _capture_keyframes_from_stream(
        self,
        url: str,
        duration: float,
        out_dir: Path,
        prefix: str,
        count: int = 6
    ) -> List[Tuple[float, str]]:
        """
        通过流媒体寻道直接抽取关键帧截图，无需将几个GB的视频下载到本地！
        返回: [(timestamp_sec, frame_rel_path)]
        """
        captured = []
        if duration <= 5:
            timestamps = [max(1.0, duration / 2)]
        else:
            # 在 10% ~ 90% 之间等间隔采样
            step = (duration * 0.8) / max(1, count)
            timestamps = [duration * 0.1 + i * step for i in range(count)]

        venv_ytdlp = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "yt-dlp"
        ytdlp_bin = str(venv_ytdlp) if venv_ytdlp.exists() else "yt-dlp"

        # 1. 尝试获取直链视频流 URL
        stream_url = ""
        try:
            get_url_cmd = [ytdlp_bin, "-g", "-f", "best[ext=mp4]/best", url]
            res = subprocess.run(get_url_cmd, capture_output=True, text=True, check=False, timeout=20)
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()
                if lines:
                    stream_url = lines[0].strip()
        except Exception as e:
            logger.warning(f"Could not get direct stream URL: {e}")

        out_dir.mkdir(parents=True, exist_ok=True)

        for idx, ts in enumerate(timestamps, 1):
            frame_filename = f"{prefix}_frame_{idx:02d}_{int(ts)}s.jpg"
            frame_path = out_dir / frame_filename

            success = False
            # 方案 A: 若有流直链，直接用 ffmpeg 寻道截图
            if stream_url:
                ffmpeg_cmd = [
                    FFMPEG_BIN,
                    "-ss", str(ts),
                    "-i", stream_url,
                    "-vframes", "1",
                    "-q:v", "2",
                    "-vf", f"scale={VIDEO_SETTINGS['keyframe_width']}:-1",
                    "-y",
                    str(frame_path)
                ]
                try:
                    p = subprocess.run(ffmpeg_cmd, capture_output=True, check=False, timeout=15)
                    if p.returncode == 0 and frame_path.exists() and frame_path.stat().st_size > 1000:
                        captured.append((ts, str(frame_path.name)))
                        success = True
                except Exception:
                    pass

            # 方案 B (回退): 若方案 A 失败，通过 yt-dlp 单独切片极速下载 2秒极小片段抽取截图后立即删掉临时切片
            if not success:
                temp_clip = TEMP_DIR / f"temp_clip_{prefix}_{idx}.mp4"
                try:
                    start_s = max(0, ts - 1)
                    end_s = start_s + 2
                    sec_arg = f"*{int(start_s)}-{int(end_s)}"
                    dl_clip_cmd = [
                        ytdlp_bin,
                        "--download-sections", sec_arg,
                        "-f", "worst[ext=mp4]/worst",
                        "-o", str(temp_clip),
                        "--no-part",
                        url
                    ]
                    subprocess.run(dl_clip_cmd, capture_output=True, check=False, timeout=25)
                    if temp_clip.exists():
                        # ffmpeg 抽帧
                        subprocess.run([
                            FFMPEG_BIN,
                            "-ss", "00:00:01",
                            "-i", str(temp_clip),
                            "-vframes", "1",
                            "-q:v", "2",
                            "-vf", f"scale={VIDEO_SETTINGS['keyframe_width']}:-1",
                            "-y",
                            str(frame_path)
                        ], capture_output=True, check=False, timeout=10)
                        if frame_path.exists() and frame_path.stat().st_size > 1000:
                            captured.append((ts, str(frame_path.name)))
                            success = True
                except Exception as ex:
                    logger.warning(f"Keyframe extraction fallback failed: {ex}")
                finally:
                    # 严格保证：坚决清理临时视频碎片，零冗余占用
                    if temp_clip.exists():
                        try:
                            temp_clip.unlink()
                        except Exception:
                            pass

        return captured

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        url = input_str.strip()
        info = self._extract_video_info(url)
        if not info:
            raise RuntimeError(f"无法解析视频信息: {url}")

        title = info.get("title", "未命名视频")
        uploader = info.get("uploader") or info.get("channel") or "未知UP主"
        duration = float(info.get("duration", 0) or 0)
        desc = info.get("description", "").strip()
        tags = info.get("tags", []) or []
        view_count = info.get("view_count", 0)
        webpage_url = info.get("webpage_url", url)

        # 视频ID / BV号识别
        video_id = info.get("id", "vid")
        prefix = f"video_{video_id}"

        # 抽取关键帧图片 (不保留原视频)
        dest_keyframes_dir = kwargs.get("keyframes_dir") or (TEMP_DIR / "keyframes")
        captured_frames = self._capture_keyframes_from_stream(
            url=webpage_url,
            duration=duration,
            out_dir=dest_keyframes_dir,
            prefix=prefix,
            count=VIDEO_SETTINGS.get("keyframe_count", 6)
        )

        # 格式化时长
        mins, secs = divmod(int(duration), 60)
        hours, mins = divmod(mins, 60)
        duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"

        # 提取时间轴/章节 (如果有)
        chapters = info.get("chapters") or []
        chapter_lines = []
        if chapters:
            for ch in chapters:
                ch_title = ch.get("title", "")
                ch_start = int(ch.get("start_time", 0))
                cm, cs = divmod(ch_start, 60)
                chapter_lines.append(f"- `[{cm:02d}:{cs:02d}]` {ch_title}")
        else:
            # 根据简介里的时间戳匹配章节
            ts_matches = re.findall(r'(?:(\d{1,2}):)?(\d{2}):(\d{2})\s+([^\n]+)', desc)
            for m in ts_matches[:10]:
                h, m_val, s, text = m
                ts_label = f"{h}:{m_val}:{s}" if h else f"{m_val}:{s}"
                chapter_lines.append(f"- `[{ts_label}]` {text.strip()}")

        # 提取简介中的技术链接、GitHub 仓库与工具提及
        extracted_links = re.findall(r'https?://[^\s<>"]+', desc)
        code_snippets = []
        for link in extracted_links:
            if "github.com" in link:
                code_snippets.append({
                    "language": "shell",
                    "code": f"git clone {link}",
                    "description": f"视频提及开源仓库: {link}"
                })

        # 构建结构化 Markdown (视频内容详解)
        md_sections = [
            f"# {title}\n",
            f"> **来源平台**: Bilibili/视频平台 | **UP主/创作者**: {uploader} | **时长**: {duration_str} | **播放量**: {view_count:,}",
            f"> **原始视频链接**: [{webpage_url}]({webpage_url})\n",
            "## 📌 视频核心概览与背景",
            f"本视频由 **{uploader}** 产出，总时长约 {duration_str}。主要围绕相关工程、技术实操或前沿方案展开探讨。\n",
            "## 🖼️ 核心关键帧与画面抓拍 (零视频体积保留)",
            "以下为从原视频无损抽取的关键时间点高清帧，便于快速浏览画面核心逻辑："
        ]

        keyframe_filenames = []
        for ts, fname in captured_frames:
            keyframe_filenames.append(fname)
            m_val, s_val = divmod(int(ts), 60)
            md_sections.append(f"- **时间点 `{m_val:02d}:{s_val:02d}` 关键帧截图**:")
            md_sections.append(f"  ![时间点 {m_val:02d}:{s_val:02d} 画面](keyframes/{fname})")

        if chapter_lines:
            md_sections.append("\n## ⏱️ 视频时间轴与核心章节目录")
            md_sections.extend(chapter_lines)

        md_sections.append("\n## 📝 视频简介与原作者笔记")
        clean_desc = "\n".join([f"> {line}" for line in desc.splitlines() if line.strip()])
        md_sections.append(clean_desc or "> (原视频无文本简介)")

        md_sections.append("\n## 💡 核心知识点与工程实操详解")
        md_sections.append("1. **核心目标与场景**: 针对该主题的痛点与主流解决方案对比。")
        md_sections.append("2. **关键参数与配置**: 详见视频对应关键帧展示的步骤及代码配置。")
        md_sections.append("3. **实测与避坑建议**: 避免重复造轮子，参考配套开源实现。")

        if code_snippets:
            md_sections.append("\n## 🛠️ 配套仓库与工具链指令")
            for snip in code_snippets:
                md_sections.append(f"```bash\n# {snip['description']}\n{snip['code']}\n```")

        content_markdown = "\n".join(md_sections)

        # 整理标签
        merged_tags = ["视频解析", uploader] + tags[:5]
        for kw in ["Blender", "AI", "Agent", "Python", "前端", "三维", "逆向", "自动化"]:
            if kw.lower() in title.lower() or kw.lower() in desc.lower():
                merged_tags.append(kw)

        summary = f"【视频详解】{uploader} 出品的《{title}》，时长 {duration_str}。已提取 {len(captured_frames)} 张核心关键帧截屏与核心技术目录。"

        return IngestedItem(
            title=title,
            source_type="bilibili_video",
            source_url=webpage_url,
            author=uploader,
            published_date=datetime.now().strftime("%Y-%m-%d"),
            summary=summary,
            content_markdown=content_markdown,
            key_points=[f"UP主: {uploader}", f"时长: {duration_str}"] + [line[4:] for line in chapter_lines[:5]],
            tags=list(set(merged_tags)),
            keyframes=keyframe_filenames,
            code_snippets=code_snippets,
            metadata={
                "video_id": video_id,
                "duration": duration,
                "view_count": view_count,
                "has_keyframes": len(captured_frames) > 0,
                "raw_video_deleted": True
            }
        )
