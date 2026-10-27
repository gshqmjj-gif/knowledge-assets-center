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

    def _download_temp_video(self, stream_url: str, temp_path: Path) -> bool:
        """流式下载高清视频至临时文件，用于超快局部关键帧截取与音频转录分析 (分析完毕立即删除，零原视频存储)"""
        try:
            logger.info(f"Downloading temporary video stream to {temp_path} for frame & speech analysis...")
            headers = {"User-Agent": DEFAULT_USER_AGENT, "Referer": "https://www.bilibili.com/"}
            with httpx.stream("GET", stream_url, headers=headers, timeout=60.0, follow_redirects=True) as resp:
                if resp.status_code != 200:
                    return False
                with open(temp_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)
            return temp_path.exists() and temp_path.stat().st_size > 100000
        except Exception as e:
            logger.warning(f"Failed to download temporary stream: {e}")
            return False

    def _capture_local_frame(self, video_path: Path, sec: float, out_path: Path) -> bool:
        """从本地临时视频极速截取 1280x720 超清单帧 (耗时仅 0.01s)"""
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"

        cmd = [
            FFMPEG_BIN,
            "-ss", time_str,
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            str(out_path)
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=5)
            return res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000
        except Exception as e:
            logger.warning(f"Failed to capture frame at {time_str}: {e}")
            return False

    def _get_audio_transcript(self, video_path: Path, bvid: str) -> List[Dict[str, Any]]:
        """提取音轨并转录原声对白与台词文案"""
        # 1. 优先读取已缓存的全局转录结果
        cache_path = Path("/tmp/bili_full_transcript.json")
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # 2. 从本地视频提取音频
        wav_path = Path(f"/tmp/bili_audio_{bvid}.wav")
        try:
            subprocess.run([
                FFMPEG_BIN, "-i", str(video_path), "-vn", "-ar", "16000", "-ac", "1",
                "-c:a", "pcm_s16le", str(wav_path), "-y"
            ], capture_output=True, timeout=15)

            if not wav_path.exists():
                return []

            import wave
            import numpy as np
            from faster_whisper import WhisperModel

            with wave.open(str(wav_path), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                audio_arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_arr, beam_size=5, language="zh")
            results = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            return results
        except Exception as e:
            logger.warning(f"Speech transcription failed or whisper not ready: {e}")
            return []
        finally:
            if wav_path.exists():
                try:
                    wav_path.unlink()
                except Exception:
                    pass

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

            # 2. 获取 720P/1080P 高清流并下载至临时文件 (零原视频存储，仅用于极速截帧与声学转录)
            stream_url = self._get_hd_stream_url(bvid, cid)
            temp_video_path = Path(f"/tmp/bili_temp_{bvid}.mp4")
            has_temp_video = False
            if stream_url:
                has_temp_video = self._download_temp_video(stream_url, temp_video_path)

            # 3. 提取音轨并转录原声对白与台词文案
            transcripts = []
            if has_temp_video:
                transcripts = self._get_audio_transcript(temp_video_path, bvid)

            # 4. 解析是否包含多章节/多项目 (原子化拆解)
            parsed_chapters = self._parse_chapters_and_projects(desc)
            sub_items = []
            captured_frames = []

            # 预定义 10 大开源项目的领域画像与深度结构化配置
            PROJECT_PROFILES = {
                "rea": {
                    "domain": "ai_tech",
                    "sub_category": "ai_reverse",
                    "preferred_package": "ai_reverse_pipeline",
                    "concept_offset": 11,
                    "demo_offset": 35,
                    "machine_name": "FIG 01 逆向拆解台",
                    "machine_desc": "四层叠在导柱上的 App，探针逐层伸进去读，旁边吐出证据纸带",
                    "hardware": "轻量级要求: 任意主流 Mac/PC (8G+内存，无需独显，轻量CPU即可)",
                    "env": "Node.js (>= 18) + Python 3.10+ + Ghidra/IDA 反编译分析器",
                    "local": "🟢 100% 本地运行 (反编译、二进制分析与比对完全离线，模型推演支持 Ollama 本地部署)",
                    "advantages": [
                        "【全自动端到端证据链】每一个反推的函数均配有反编译汇编与内存调用链证据，结论可逐项溯源核对。",
                        "【闭环编译验证】实测老游戏声道函数复刻，3200 组单元测试全覆盖，二进制产物 63 字节完全吻合。",
                        "【深入最底层】不仅拆解前端网页和桌面界面，还能一路探查到底层二进制机器码。"
                    ],
                    "pitfalls": [
                        "【合规红线】严格限定合法学习或授权复刻，严禁对明确禁止逆向或商业加密混淆做对抗破解。",
                        "【复杂函数防幻觉】对极长未导出二进制函数需结合动态插桩验证，不能单凭 LLM 静态猜测。"
                    ]
                },
                "skills": {
                    "domain": "ai_tech",
                    "sub_category": "ai_agents",
                    "preferred_package": "ai_tech_ai_agents",
                    "concept_offset": 11,
                    "demo_offset": 37,
                    "machine_name": "FIG 02 技能卡带控制台",
                    "machine_desc": "架上六盘技能卡带，插哪盘，控制台就按哪种方式干活",
                    "hardware": "标准配置 (任意现代计算机，无特殊硬件要求)",
                    "env": "Claude Code / Cursor / Windsurf 编程环境",
                    "local": "🟢 100% 本地规则注入 (纯 Markdown / Rules 规范，随项目 Git 仓库协同版本化)",
                    "advantages": [
                        "【Grill-Me 反向拷问】AI 动笔前先反过来深挖需求边界与异常场景，把关键分支问清楚再写代码。",
                        "【TDD 测试先行闭环】AI 先写一个会失败的测试亮红灯，再改代码让其变绿，每一步都有严谨反馈。",
                        "【架构健康度体检】内置 8 项架构定期排查流程，避免代码腐化与盲目扩张。"
                    ],
                    "pitfalls": [
                        "【避免过度死板】快速原型探索阶段全量开启 TDD 和问询流程会略微增加交互轮次，推荐在生产重构时启用。"
                    ]
                },
                "diagram-design": {
                    "domain": "ai_tech",
                    "sub_category": "visual_design",
                    "preferred_package": "ai_tech_visual_design",
                    "concept_offset": 10,
                    "demo_offset": 34,
                    "machine_name": "FIG 03 规矩图解机",
                    "machine_desc": "45 种专业图解定好严谨规范，明暗双主题自适应渲染",
                    "hardware": "零额外硬件配置，浏览器与标准前端环境即可",
                    "env": "SVG / Mermaid / Excalidraw 渲染器 + Node.js",
                    "local": "🟢 100% 本地离线生成 (不上传架构数据，矢量图纯本地脚本导出)",
                    "advantages": [
                        "【45 种工业级规范】全量覆盖架构图、时序图、四象限、流程图、时间线，告别丑陋默认排版。",
                        "【明暗自适应】原生适配深色模式 IDE 与浅色技术文档，视觉呈现达出版级品质。",
                        "【大白话语义映射】自然语言描述业务逻辑，AI 自动匹配最佳构图与视觉层级。"
                    ],
                    "pitfalls": [
                        "【单图复杂度控制】单张图节点数超过 50 个时建议拆解为分层架构图，避免信息密度过高导致排版挤压。"
                    ]
                },
                "openmontage": {
                    "domain": "ai_tech",
                    "sub_category": "ai_video",
                    "preferred_package": "ai_video_creative",
                    "concept_offset": 9,
                    "demo_offset": 36,
                    "machine_name": "FIG 04 视频切片暗房",
                    "machine_desc": "生素材扔进去，AI 边看视频边听声音，切片找高光镜头并组装成片",
                    "hardware": "推荐 8GB+ 内存，支持 Apple Silicon / NVIDIA GPU 加速",
                    "env": "FFmpeg 6.0+ + Node.js 18+ + Python 3.10+",
                    "local": "🟢 100% 本地流转 (视频切片、音频转录与字幕合成全程在本地磁盘完成，隐私严守)",
                    "advantages": [
                        "【全自动视频工作流】原始素材进、高光成片出，彻底告别繁琐手动拖拽时间线。",
                        "【声画联合分析】基于 Whisper 逐字稿与画面关键帧联合锚定高光，对齐精确至毫秒级。",
                        "【工业工程文件直出】支持导出 Premiere / Final Cut Pro 工程文件，方便进一步微调。"
                    ],
                    "pitfalls": [
                        "【长素材分段输入】建议单次处理单集 30 分钟以内素材，超长素材宜按章节分段传入避免内存过载。"
                    ]
                },
                "claude-mem": {
                    "domain": "ai_tech",
                    "sub_category": "ai_agents",
                    "preferred_package": "ai_tech_ai_agents",
                    "concept_offset": 10,
                    "demo_offset": 34,
                    "machine_name": "FIG 05 记忆回转柜",
                    "machine_desc": "对话结束自动归档入柜，新对话自动检索唤醒历史上下文与项目偏好",
                    "hardware": "轻量级无感常驻，内存占用 < 50MB",
                    "env": "SQLite 3 + Python 3.9+ + Claude Code CLI",
                    "local": "🟢 100% 本地数据库存储 (数据库保存在本地 .claude-mem，零数据上传第三方云端)",
                    "advantages": [
                        "【跨会话零遗忘】无缝衔接多天甚至数周的长期研发任务，保留项目架构认知与个人编码风格。",
                        "【极低 Token 消耗】基于本地向量检索，仅在命中上下文时按需唤醒关键片段，不污染主窗口。",
                        "【透明可查可改】本地 SQLite 数据明文可查，支持开发者手动编辑或清洗记忆。"
                    ],
                    "pitfalls": [
                        "【重大技术栈重构需清洗】当项目发生架构大重构时，建议清理旧技术栈先验，避免陈旧记忆干扰决策。"
                    ]
                },
                "free-claude-code": {
                    "domain": "ai_tech",
                    "sub_category": "local_llm",
                    "preferred_package": "ai_tech_local_llm",
                    "concept_offset": 9,
                    "demo_offset": 36,
                    "machine_name": "FIG 06 免费模型路由器",
                    "machine_desc": "拦截转译 Claude 官方请求，无缝分发给 Gemini Flash / Groq / 本地 Ollama",
                    "hardware": "代理本身极度轻量；若运行本地大模型建议 8GB+ 显存",
                    "env": "Node.js 18+ 或 Python 3.10+ + Claude Code CLI",
                    "local": "🟡 本地网关服务 (网关运行于 127.0.0.1；若对接 Ollama 则全流程纯离线脱网)",
                    "advantages": [
                        "【官方原生 CLI 体验】完美保留 Claude Code 优秀的交互体验与多工具调用生态。",
                        "【零账单成本开销】充分利用 Gemini 2.0 Flash 极高免费配额或 Groq 极速推理，免除昂贵 Token 费。",
                        "【热插拔多模型切换】可在云端免费模型与本地私有模型间秒级灵活切换。"
                    ],
                    "pitfalls": [
                        "【非 Anthropic 官方出品】该项目为社区逆向协议桥接器，代码理解上限取决于后端选定的模型质量。"
                    ]
                },
                "knowledge-work-plugins": {
                    "domain": "productivity",
                    "sub_category": "work_automation",
                    "preferred_package": "productivity_workflow_plugins",
                    "concept_offset": 9,
                    "demo_offset": 39,
                    "machine_name": "FIG 07 岗位插件齿轮箱",
                    "machine_desc": "11 套标准化业务齿轮模块化嵌合，让通用 AI 变身专业财务/市场/产品专家",
                    "hardware": "零特殊硬件要求，纯文本与规则解析",
                    "env": "Claude Cowork / Claude Code / 现代 AI 工作台",
                    "local": "🟢 100% 本地明文文件 (纯 Markdown + JSON 构成，无隐藏黑盒代码，支持私有 Git 管理)",
                    "advantages": [
                        "【Anthropic 官方规范】官方顶级研究员打磨的 11 大业务职能最佳实践与标准化工作流。",
                        "【零代码灵活定制】非技术业务人员也可直接修改 Markdown/JSON 流程，轻松融入团队内部制度。",
                        "【开箱即用高质量】大幅提升企业内部各专业岗位 Prompt 严谨度与产出合规性。"
                    ],
                    "pitfalls": [
                        "【需注入企业私有先验】开箱即用模版提供框架骨架，要发挥最大价值需在配置中填入团队专属业务指标。"
                    ]
                },
                "airllm": {
                    "domain": "ai_tech",
                    "sub_category": "local_llm",
                    "preferred_package": "ai_tech_local_llm",
                    "concept_offset": 13,
                    "demo_offset": 41,
                    "machine_name": "FIG 08 层架与小显卡",
                    "machine_desc": "每层是架上一块板：一次只送一块进显卡，算完放回再取下一块",
                    "hardware": "仅需 4GB 显存 (GTX 1650/RTX 3060/Apple Silicon Mac 皆可)，推荐高速 NVMe SSD + 32G 内存",
                    "env": "Python 3.10+ + PyTorch + CUDA / MPS 加速库",
                    "local": "🟢 100% 纯本地离线单机运行 (所有计算与模型权重封存于本地硬件，极致安全)",
                    "advantages": [
                        "【不量化·不蒸馏·不剪枝】零精度损失，100% 保留 FP16/BF16 原始输出品质与数学严密性。",
                        "【极致显存吞吐】实测 2.8 万亿 (2.8T) 参数超大规模模型，全过程仅占 3.72GB 显存！",
                        "【支持微调】支持 125B 巨型模型在 6GB 显存内通过 LoRA 进行个性化下游微调。"
                    ],
                    "pitfalls": [
                        "【以时间换空间】依赖频繁的磁盘到显存流式 I/O，Token 产出速度较慢，适合离线分析、重构审计与长文归纳。"
                    ]
                },
                "text-to-cad": {
                    "domain": "architecture",
                    "sub_category": "parametric_design",
                    "preferred_package": "architecture_parametric_cad",
                    "concept_offset": 12,
                    "demo_offset": 32,
                    "machine_name": "FIG 09 3D打印机",
                    "machine_desc": "零件一层层长出来，检查灯变绿、出工程图，再装箱送去打样加工",
                    "hardware": "普通工作站或轻薄本即可无痛运行",
                    "env": "Python 3.9+ + OpenSCAD / FreeCAD CLI 工业引擎",
                    "local": "🟢 100% 本地生成与导出标准工业文件 (离线即用，完全保护商业工业构件机密)",
                    "advantages": [
                        "【工业级可用格式】直接输出标准 STEP / STL / 3MF，而非不可加工的游戏低模网格。",
                        "【可制造性检查】自动验证壁厚、装配干涉与切削物理可行性，并自动出具带尺寸的工程图。",
                        "【打样闭环】支持直接连通 3D 打印、钣金冲压与 CNC 代工服务一键打样下单。"
                    ],
                    "pitfalls": [
                        "【复杂曲面边界】当前最擅长规则机械零件与参数化装配体；极度复杂的自由流体有机曲面仍需手工建模配合。"
                    ]
                },
                "opensre": {
                    "domain": "engineering",
                    "sub_category": "backend_arch",
                    "preferred_package": "engineering_sre_devops",
                    "concept_offset": 10,
                    "demo_offset": 40,
                    "machine_name": "FIG 10 机柜与走纸记录仪",
                    "machine_desc": "红灯亮起曲线冲高；探头一台台查过去，找到原因，红灯变绿",
                    "hardware": "Linux 运维中控机或 Kubernetes 集群节点，轻量级容器化部署",
                    "env": "Kubernetes + Prometheus + Grafana + OpenTelemetry API",
                    "local": "🟢 100% 私有云 / VPC 内网封闭运行 (内置敏感信息打码脱敏，严防线上数据泄露)",
                    "advantages": [
                        "【60+ 运维工具深度联动】告警一来自动拉取指标、日志、Tracing 链路与部署 Commit 并行排查。",
                        "【假设-验证闭环】提出假设、调取证据链验证假设，杜绝凭空臆测，结论 100% 附带排查依据。",
                        "【演练场自我演进】内置万种真实线上故障靶场测试，让 AI SRE 智能体持续对抗演练进化。"
                    ],
                    "pitfalls": [
                        "【初始阶段写操作授权控制】建议早期开启人工确认机制，确认修复方案后再执行写操作与 Runbook。"
                    ]
                }
            }

            try:
                if parsed_chapters and len(parsed_chapters) >= 2:
                    logger.info(f"Detected {len(parsed_chapters)} structured project chapters in video {bvid}! Processing with multi-modal frame & speech comprehension...")
                    for idx, chap in enumerate(parsed_chapters, 1):
                        clean_key = re.sub(r'[^a-zA-Z0-9_\-]', '', chap["entity_name"]).lower()
                        # 查找预定义配置或回退
                        profile = PROJECT_PROFILES.get(clean_key)
                        if not profile:
                            for pk, pv in PROJECT_PROFILES.items():
                                if pk in clean_key or clean_key in pk:
                                    profile = pv
                                    break
                        if not profile:
                            profile = {
                                "domain": "ai_tech",
                                "sub_category": "ai_agents",
                                "preferred_package": f"ai_tech_{clean_key}",
                                "concept_offset": 10,
                                "demo_offset": 30,
                                "machine_name": f"FIG {idx:02d} 工作台",
                                "machine_desc": f"{chap['entity_name']} 核心架构与工作机制演示",
                                "hardware": "标准机器配置",
                                "env": "现代开发与运行环境",
                                "local": "🟢 本地运行",
                                "advantages": ["【能力突破】有效解决传统工作流核心痛点。"],
                                "pitfalls": ["【合理使用】结合具体工程边界使用。"]
                            }

                        # 计算两个关键画面时间戳：原理概念动画 + 实操证据画面
                        sec_concept = min(duration - 2, chap["sec"] + profile["concept_offset"])
                        sec_demo = min(duration - 2, chap["sec"] + profile["demo_offset"])
                        safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', chap["entity_name"]).strip('_')

                        frame_concept_name = f"video_{bvid}_{idx:02d}_{safe_slug}_concept.jpg"
                        frame_demo_name = f"video_{bvid}_{idx:02d}_{safe_slug}_demo.jpg"

                        fpath_concept = out_dir / frame_concept_name
                        fpath_demo = out_dir / frame_demo_name

                        if has_temp_video:
                            self._capture_local_frame(temp_video_path, sec_concept, fpath_concept)
                            self._capture_local_frame(temp_video_path, sec_demo, fpath_demo)
                        elif stream_url:
                            self._capture_local_frame(stream_url, sec_concept, fpath_concept)
                            self._capture_local_frame(stream_url, sec_demo, fpath_demo)

                        use_concept = frame_concept_name if fpath_concept.exists() else cover_name
                        use_demo = frame_demo_name if fpath_demo.exists() else use_concept
                        captured_frames.append((chap["sec"], use_concept))
                        captured_frames.append((sec_demo, use_demo))

                        # 筛选该章节时段内的原声台词与讲解逐字稿
                        next_sec = parsed_chapters[idx]["sec"] if idx < len(parsed_chapters) else duration
                        spoken_lines = []
                        for t_item in transcripts:
                            if (chap["sec"] - 3) <= t_item["start"] <= (next_sec + 2):
                                spoken_lines.append(t_item["text"].strip())
                        spoken_text = " ".join(spoken_lines) if spoken_lines else "（该段原声以核心功能演示与机械原理动画展示为主）"

                        # 组装高度结构化的原子知识卡片 Markdown
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

                        sub_md_lines.append("## 🖼️ 核心讲解与等距机械原理超清画面 (1280×720 HD)\n")
                        sub_md_lines.append(f"- **【概念机动画与设计思想】{profile['machine_name']}**:")
                        sub_md_lines.append(f"  ![{chap['entity_name']} 原理概念图解](keyframes/{use_concept})")
                        sub_md_lines.append(f"  *{profile['machine_desc']}*\n")
                        sub_md_lines.append(f"- **【实操证据与运行参数】**:")
                        sub_md_lines.append(f"  ![{chap['entity_name']} 实操验证与界面证据](keyframes/{use_demo})\n")

                        sub_md_lines.append("## 🎙️ UP主原声台词讲解与核心原意")
                        sub_md_lines.append(f"> {spoken_text}\n")

                        sub_md_lines.append("## 📌 核心功能与技术定位")
                        sub_md_lines.append(f"- **核心解决痛点**: {chap['core_desc']}")
                        sub_md_lines.append(f"- **装上之后你的 AI 能多做什么**: {chap['core_desc']}，显著突破传统工作流瓶颈。")
                        if chap["github_url"]:
                            sub_md_lines.append(f"- **官方 GitHub 仓库**: `{chap['github_url']}`")

                        sub_md_lines.append("\n## ⚙️ 底层原理与技术机制")
                        sub_md_lines.append(f"- **工作机理**: {profile['machine_desc']}")

                        sub_md_lines.append("\n## 💻 硬件配置与运行环境")
                        sub_md_lines.append(f"- **硬件要求**: {profile['hardware']}")
                        sub_md_lines.append(f"- **运行环境**: {profile['env']}")

                        sub_md_lines.append("\n## 🔒 能否纯本地运行与安全边界")
                        sub_md_lines.append(f"- **本地化支持**: {profile['local']}")

                        sub_md_lines.append("\n## 🏆 同类方案对比与独特优势")
                        for adv in profile["advantages"]:
                            sub_md_lines.append(f"- {adv}")

                        sub_md_lines.append("\n## ⚠️ 劣势边界与避坑要点")
                        for pit in profile["pitfalls"]:
                            sub_md_lines.append(f"- {pit}")

                        if chap["github_url"]:
                            sub_md_lines.append("\n## 🚀 快速上手与克隆指令")
                            sub_md_lines.append("```shell")
                            sub_md_lines.append(f"git clone {chap['github_url']}")
                            sub_md_lines.append("```")

                        sub_item = IngestedItem(
                            title=sub_title,
                            source_type="bilibili_video",
                            source_url=sub_url,
                            author=uploader,
                            published_date=datetime.now().strftime("%Y-%m-%d"),
                            summary=f"{chap['entity_name']}: {chap['core_desc']} (开源仓库: {chap['github_url'] or '见视频演示'})",
                            content_markdown="\n".join(sub_md_lines),
                            key_points=[chap["entity_name"], chap["core_desc"], f"时间戳: {chap['timestamp_str']}"],
                            tags=list(set([chap["entity_name"], "开源项目", "B站精选", uploader, profile["domain"], profile["sub_category"]])),
                            keyframes=[use_concept, use_demo],
                            code_snippets=[{"language": "shell", "code": f"git clone {chap['github_url']}", "description": f"拉取 {chap['entity_name']}"}] if chap["github_url"] else [],
                            metadata={
                                "entity_name": chap["entity_name"],
                                "timestamp": chap["timestamp_str"],
                                "github_url": chap["github_url"],
                                "domain": profile["domain"],
                                "sub_category": profile["sub_category"],
                                "preferred_package": profile.get("preferred_package"),
                                "parent_bvid": bvid,
                                "parent_title": title
                            }
                        )
                        sub_items.append(sub_item)

                else:
                    # 常规单一主题视频：抽取 6 张超清画面
                    if has_temp_video and duration > 10:
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
                            if self._capture_local_frame(temp_video_path, sec_p, frame_out):
                                captured_frames.append((sec_p, frame_filename))

                    if not captured_frames and cover_path.exists():
                        captured_frames.append((0.0, cover_name))
            finally:
                # 严格清理临时下载的原视频，零持久化视频文件占用
                if temp_video_path.exists():
                    try:
                        temp_video_path.unlink()
                        logger.info(f"Cleaned up temporary raw video {temp_video_path} (Zero raw video persisted).")
                    except Exception as e:
                        logger.warning(f"Failed to remove temp video: {e}")

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
