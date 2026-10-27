"""
Image Asset Crawler
图片资产解析与图表资料入库 (支持架构图、流程图、脑图、UI线框图等)
"""
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from config import DEFAULT_USER_AGENT, TEMP_DIR
from crawlers.base import BaseCrawler, IngestedItem

logger = logging.getLogger("hermes.image_asset")

class ImageAssetCrawler(BaseCrawler):
    name = "image_asset"

    def match(self, input_str: str) -> bool:
        s = input_str.strip().lower()
        image_exts = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp")
        if any(s.endswith(ext) or ext + "?" in s for ext in image_exts):
            return True
        if Path(input_str).is_file() and any(input_str.lower().endswith(ext) for ext in image_exts):
            return True
        return False

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        target = input_str.strip()
        dest_assets_dir = kwargs.get("assets_dir") or (TEMP_DIR / "assets")
        dest_assets_dir.mkdir(parents=True, exist_ok=True)

        filename = ""
        local_path: Optional[Path] = None

        if target.startswith("http"):
            parsed = urlparse(target)
            orig_name = Path(parsed.path).name or "image.jpg"
            filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{orig_name}"
            local_path = dest_assets_dir / filename
            headers = {"User-Agent": DEFAULT_USER_AGENT}
            with httpx.Client(headers=headers, timeout=15.0) as client:
                resp = client.get(target)
                resp.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(resp.content)
        else:
            p = Path(target)
            if not p.exists():
                raise FileNotFoundError(f"Image file not found: {target}")
            filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{p.name}"
            local_path = dest_assets_dir / filename
            shutil.copy2(str(p), str(local_path))

        # 分析图片元数据
        width, height = 0, 0
        img_format = "UNKNOWN"
        aspect_ratio_type = "标准"
        try:
            with Image.open(local_path) as im:
                width, height = im.size
                img_format = im.format or "IMAGE"
                ratio = width / max(1, height)
                if ratio > 1.8:
                    aspect_ratio_type = "全景/宽幅横图 (常为架构全景图或时序流图)"
                elif ratio < 0.6:
                    aspect_ratio_type = "长图 (常为脑图清单或长条图文总结)"
                else:
                    aspect_ratio_type = "标准比例 (截屏/示意图/UI设计)"
        except Exception as e:
            logger.warning(f"Error reading image details: {e}")

        title = f"图片资产_{Path(filename).stem}"
        size_kb = round(local_path.stat().st_size / 1024, 1)

        # 构建结构化说明
        md_lines = [
            f"# {title}\n",
            f"> **图像格式**: {img_format} | **分辨率**: {width}x{height} | **文件大小**: {size_kb} KB",
            f"> **类型推断**: {aspect_ratio_type}\n",
            "## 🖼️ 图片预览",
            f"![{title}](assets/{filename})\n",
            "## 📌 图像资产价值与应用提示",
            f"- **图表类型**: 适合作为项目设计、架构参考、UI组件排版的重要视觉资产。",
            f"- **Agent 参考指南**: 在 Cursor / Codex 编码时，可引用此图对应的业务实体或数据流向设计。",
            f"- **原始来源**: `{target}`"
        ]

        content_markdown = "\n".join(md_lines)

        return IngestedItem(
            title=title,
            source_type="image",
            source_url=target,
            author="Visual Asset",
            published_date=datetime.now().strftime("%Y-%m-%d"),
            summary=f"图片视觉资产 ({width}x{height}, {size_kb}KB)，类型：{aspect_ratio_type}。",
            content_markdown=content_markdown,
            key_points=[f"尺寸: {width}x{height}", f"格式: {img_format}", aspect_ratio_type],
            tags=["图片资产", img_format.lower(), "设计参考"],
            assets=[filename],
            metadata={
                "width": width,
                "height": height,
                "format": img_format,
                "size_kb": size_kb,
                "filename": filename
            }
        )
