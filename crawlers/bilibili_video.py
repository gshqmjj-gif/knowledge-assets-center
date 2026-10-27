"""
Video Crawler (Bilibili & Universal Video Platforms)
核心策略：严格遵从要求——不下载原视频，仅提取高清关键帧截图、视频原链接以及视频内容详解
升级能力：
1. 1080P/720P 超清关键帧截取 (直接通过 ffmpeg 远程流切帧，告别模糊切片)
2. 多章节/多技术项目原子化拆解 (Multi-Item Decomposition)
"""
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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

    def _get_hd_stream_url(self, bvid: str, cid: str) -> Optional[str]:
        """通过 B站 playurl 接口获取无须鉴权的高清 mp4 直链"""
        try:
            api_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&type=&otype=json&platform=html5&high_quality=1"
            headers = {
                "User-Agent": DEFAULT_USER_AGENT,
                "Referer": f"https://www.bilibili.com/video/{bvid}"
            }
            with httpx.Client(headers=headers, timeout=10.0) as client:
                r = client.get(api_url).json()
                if r.get("code") == 0:
                    durl = r.get("data", {}).get("durl", [])
                    if durl:
                        return durl[0]["url"]
        except Exception as e:
            logger.warning(f"Failed to fetch HD playurl: {e}")
        return None

    def _capture_hd_frame_ffmpeg(self, stream_url: str, sec: float, out_path: Path, bvid: str) -> bool:
        """通过 ffmpeg 对远程流指定时间戳精准提取一帧 720P/1080P 高清截屏 (零原视频存储)"""
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"

        cmd = [
            FFMPEG_BIN,
            "-headers", f"Referer: https://www.bilibili.com/\r\nUser-Agent: {DEFAULT_USER_AGENT}\r\n",
            "-ss", time_str,
            "-i", stream_url,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            str(out_path)
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=18)
            if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000:
                return True
        except Exception as e:
            logger.warning(f"FFmpeg HD capture failed at {time_str}: {e}")
        return False

    def _parse_chapters_and_projects(self, desc: str) -> List[Dict[str, Any]]:
        """从视频简介中解析结构化时间戳章节与 GitHub 项目清单"""
        # 匹配时间戳：00:35 01 REA：让 AI 逆向任何 App，一直拆到二进制
        time_matches = re.findall(r'(\d{1,2}:\d{2})\s+([0-9]{1,2}\s+[A-Za-z0-9_\-\+]+[：:][^\n]+)', desc)
        if not time_matches:
            # 兼容其他时间戳格式：00:35 REA...
            time_matches = re.findall(r'(\d{1,2}:\d{2})\s+([^\n]+)', desc)

        # 匹配项目链接：01 REA：https://github.com/morluto/rea
        links_pattern = r'([0-9]{1,2}\s+[A-Za-z0-9_\-\+]+|[A-Za-z0-9_\-\+]+)[：:]\s*(https://github\.com/[^\s]+)'
        raw_links = re.findall(links_pattern, desc)
        links_map = {}
        for k, url in raw_links:
            clean_k = re.sub(r'[^a-zA-Z0-9_\-\+]', '', k).lower()
            links_map[clean_k] = url

        chapters = []
        for ts_str, raw_title in time_matches:
            raw_title_clean = raw_title.strip()
            # 忽略纯开场/结尾
            if any(k in raw_title_clean for k in ["开场", "结尾", "片尾", "片头", "总结", "前言"]):
                continue

            parts = ts_str.split(':')
            sec = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else 0

            # 提取实体名称与核心功能描述
            m_entity = re.search(r'(?:[0-9]{1,2}\s+)?([A-Za-z0-9_\-\+]+)[：:]\s*(.*)', raw_title_clean)
            if m_entity:
                entity_name = m_entity.group(1).strip()
                core_desc = m_entity.group(2).strip()
            else:
                entity_name = raw_title_clean.split()[0] if raw_title_clean.split() else "Project"
                core_desc = raw_title_clean

            # 匹配 GitHub 链接
            clean_k = re.sub(r'[^a-zA-Z0-9_\-\+]', '', entity_name).lower()
            github_url = links_map.get(clean_k, "")
            if not github_url:
                for k_map, u in links_map.items():
                    if k_map in clean_k or clean_k in k_map:
                        github_url = u
                        break

            chapters.append({
                "raw_title": raw_title_clean,
                "entity_name": entity_name,
                "core_desc": core_desc,
                "timestamp_str": ts_str,
                "sec": sec,
                "github_url": github_url
            })

        return chapters

    def _fetch_bilibili_native(self, url: str, out_dir: Path) -> Optional[IngestedItem]:
        """
        B站原生超清解析与多项目原子化拆解
        """
        try:
            bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url, re.I)
            bvid = bv_match.group(1) if bv_match else "BV_video"
            req_url = f"https://m.bilibili.com/video/{bvid}" if bvid != "BV_video" else url

            headers = {"User-Agent": MOBILE_UA}
            with httpx.Client(headers=headers, follow_redirects=True, timeout=12.0) as client:
                resp = client.get(req_url)
                if resp.status_code != 200:
                    return None
                real_url = f"https://www.bilibili.com/video/{bvid}" if bvid != "BV_video" else str(resp.url)
                html_text = resp.text

            state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_text)
            if not state_match:
                return None
            
            data = json.loads(state_match.group(1))
            v_obj = data.get("video", {})
            view_info = v_obj.get("viewInfo", {})
            up_info = v_obj.get("upInfo", {})

            title = view_info.get("title") or "B站精选视频"
            duration = float(view_info.get("duration", 0) or 0)
            cid = str(view_info.get("cid") or "")
            desc = view_info.get("desc", "").strip()
            uploader = up_info.get("name") or "B站创作者"
            
            if not uploader or uploader == "B站创作者":
                m_up = re.search(r'视频作者\s+([^\s,，]+)', html_text)
                if m_up:
                    uploader = m_up.group(1)

            tags = [t.get("tag_name") for t in v_obj.get("tags", []) if t.get("tag_name")]
            out_dir.mkdir(parents=True, exist_ok=True)

            # 1. 保存封面
            cover_url = view_info.get("pic")
            cover_name = f"video_{bvid}_cover.jpg"
            cover_path = out_dir / cover_name
            if cover_url:
                if cover_url.startswith("//"):
                    cover_url = "https:" + cover_url
                try:
                    cover_resp = httpx.get(cover_url, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=8.0)
                    if cover_resp.status_code == 200:
                        cover_path.write_bytes(cover_resp.content)
                except Exception as e:
                    logger.warning(f"Failed to fetch cover: {e}")

            # 2. 获取 720P/1080P 高清流直链
            stream_url = self._get_hd_stream_url(bvid, cid)

            # 3. 解析是否包含多章节/多项目 (原子化拆解)
            parsed_chapters = self._parse_chapters_and_projects(desc)
            sub_items = []
            captured_frames = []

            if parsed_chapters and len(parsed_chapters) >= 2 and stream_url:
                logger.info(f"Detected {len(parsed_chapters)} structured project chapters in video {bvid}!")
                for idx, chap in enumerate(parsed_chapters, 1):
                    # 在时间戳后 3 秒抓取，避开转场黑屏
                    sample_sec = min(duration - 2, chap["sec"] + 3)
                    safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', chap["entity_name"]).strip('_')
                    frame_filename = f"video_{bvid}_{idx:02d}_{safe_slug}.jpg"
                    frame_out_path = out_dir / frame_filename

                    ok = self._capture_hd_frame_ffmpeg(stream_url, sample_sec, frame_out_path, bvid)
                    frame_to_use = frame_filename if ok else cover_name
                    captured_frames.append((chap["sec"], frame_to_use))

                    # 针对该子项目生成独立的原子知识项 (Sub-Item)
                    sub_title = f"{chap['entity_name']}：{chap['core_desc']}"
                    sub_url = f"https://www.bilibili.com/video/{bvid}?t={chap['sec']}"
                    
                    sub_md_lines = [
                        f"# {sub_title}\n",
                        f"> **所属合辑**: 《{title}》 | **UP主**: {uploader} | **原片定位时间**: `{chap['timestamp_str']}`",
                        f"> **视频直达点播**: [{sub_url}]({sub_url})",
                    ]
                    if chap["github_url"]:
                        sub_md_lines.append(f"> **开源项目代码仓**: [{chap['github_url']}]({chap['github_url']})\n")
                    else:
                        sub_md_lines.append("\n")

                    sub_md_lines.append("## 🖼️ 核心讲解高清画面 (1280×720 HD)\n")
                    sub_md_lines.append(f"![{chap['entity_name']} 实操画面](keyframes/{frame_to_use})\n")

                    sub_md_lines.append("## 📌 核心功能与技术定位\n")
                    sub_md_lines.append(f"- **核心解决痛点**: {chap['core_desc']}")
                    if chap["github_url"]:
                        sub_md_lines.append(f"- **官方 GitHub 仓库**: `{chap['github_url']}`")
                        sub_md_lines.append(f"- **本地拉取指令**: `git clone {chap['github_url']}`")

                    sub_md_lines.append(f"\n## 💡 视频出处上下文")
                    sub_md_lines.append(f"来源于 {uploader} 发布的精选技术盘点《{title}》，在 `{chap['timestamp_str']}` 进行重点演示。")

                    sub_item = IngestedItem(
                        title=sub_title,
                        source_type="bilibili_video",
                        source_url=sub_url,
                        author=uploader,
                        published_date=datetime.now().strftime("%Y-%m-%d"),
                        summary=f"{chap['entity_name']}: {chap['core_desc']} (开源仓库: {chap['github_url'] or '见视频演示'})",
                        content_markdown="\n".join(sub_md_lines),
                        key_points=[chap["entity_name"], chap["core_desc"], f"时间戳: {chap['timestamp_str']}"],
                        tags=list(set([chap["entity_name"], "开源项目", "B站精选", uploader])),
                        keyframes=[frame_to_use],
                        code_snippets=[{"language": "shell", "code": f"git clone {chap['github_url']}", "description": f"拉取 {chap['entity_name']}"}] if chap["github_url"] else [],
                        metadata={
                            "entity_name": chap["entity_name"],
                            "timestamp": chap["timestamp_str"],
                            "github_url": chap["github_url"],
                            "parent_bvid": bvid,
                            "parent_title": title
                        }
                    )
                    sub_items.append(sub_item)

            else:
                # 常规单一主题视频：抽取 6 张超清画面
                if stream_url and duration > 10:
                    sample_points = [
                        ("01_intro", max(2, duration * 0.1)),
                        ("02_core1", duration * 0.28),
                        ("03_core2", duration * 0.48),
                        ("04_demo", duration * 0.68),
                        ("05_code", duration * 0.82),
                        ("06_summary", duration * 0.94),
                    ]
                    for name_p, sec_p in sample_points:
                        frame_filename = f"video_{bvid}_hd_{name_p}.jpg"
                        frame_out = out_dir / frame_filename
                        if self._capture_hd_frame_ffmpeg(stream_url, sec_p, frame_out, bvid):
                            captured_frames.append((sec_p, frame_filename))

                if not captured_frames and cover_path.exists():
                    captured_frames.append((0.0, cover_name))

            # 格式化时长
            mins, secs = divmod(int(duration), 60)
            hours, mins = divmod(mins, 60)
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"

            # 组装母项 Markdown
            md_sections = [
                f"# {title}\n",
                f"> **来源平台**: Bilibili | **UP主/创作者**: {uploader} | **时长**: {duration_str} | **BV号**: `{bvid}`",
                f"> **原始视频链接**: [{real_url}]({real_url})\n",
                "## 📌 视频核心概览与背景",
                f"本视频由 **{uploader}** 产出，总时长约 {duration_str}。包含 {len(sub_items)} 个独立技术方案或项目分享。\n",
                "## 🖼️ 核心高清关键帧 (1280×720 HD · 零原视频存储占用)",
                f"已提取 **{len(captured_frames)}** 张关键时间点高清帧，精准直观展示内容："
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
                        "description": f"开源项目仓库: {link}"
                    })

            summary = f"【B站精选视频】{uploader} 出品的《{title}》，时长 {duration_str}。已提取 {len(captured_frames)} 张核心超清关键帧截屏与 {len(sub_items)} 个拆解子项。"

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
                sub_items=sub_items,
                metadata={
                    "bvid": bvid,
                    "duration": duration,
                    "has_keyframes": len(captured_frames) > 0,
                    "sub_items_count": len(sub_items)
                }
            )
        except Exception as e:
            logger.error(f"Bilibili native fetch failed: {e}")
            return None

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        url = input_str.strip()
        out_dir = kwargs.get("keyframes_dir") or (TEMP_DIR / "keyframes")
        out_dir.mkdir(parents=True, exist_ok=True)

        if "bilibili.com" in url or "b23.tv" in url:
            item = self._fetch_bilibili_native(url, out_dir)
            if item:
                return item

        # 兜底
        return IngestedItem(
            title=f"视频解析: {url[:30]}",
            source_type="bilibili_video",
            source_url=url,
            summary="视频信息暂存",
            content_markdown=f"# 视频信息\n\n来源链接: {url}"
        )
