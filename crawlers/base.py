"""
Base Crawler and IngestedItem Data Models
"""
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class CodeSnippet:
    language: str
    code: str
    description: str = ""

@dataclass
class IngestedItem:
    title: str
    source_type: str                  # wechat_article, wechat_channel, bilibili_video, webpage, image
    source_url: str
    author: str = ""
    published_date: str = ""
    summary: str = ""
    content_markdown: str = ""
    key_points: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    keyframes: List[str] = field(default_factory=list)      # 关键帧相对路径或名称
    code_snippets: List[Dict[str, str]] = field(default_factory=list) # 代码段集合
    assets: List[str] = field(default_factory=list)         # 关联图片或图表
    metadata: Dict[str, Any] = field(default_factory=dict)
    ingested_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def slug(self) -> str:
        """生成安全的文件名标识"""
        safe_title = re.sub(r'[\/:*?"<>|\s]+', '_', self.title).strip('_')
        if not safe_title:
            safe_title = "untitled"
        return safe_title[:50]

class BaseCrawler:
    """抽象采集器基类"""
    name: str = "base"

    def match(self, input_str: str) -> bool:
        raise NotImplementedError

    def fetch(self, input_str: str, **kwargs) -> IngestedItem:
        raise NotImplementedError
