"""
Crawler Dispatcher (多模态采集调度器)
自动识别微信公众号、视频号、B站/视频、通用网页、图片等输入类型，分发至对应采集器
"""
import logging
from typing import List, Optional

from crawlers.base import BaseCrawler, IngestedItem
from crawlers.bilibili_video import BilibiliVideoCrawler
from crawlers.image_asset import ImageAssetCrawler
from crawlers.webpage import WebpageCrawler
from crawlers.wechat_article import WeChatArticleCrawler
from crawlers.wechat_channels import WeChatChannelsCrawler

logger = logging.getLogger("hermes.dispatcher")

class CrawlerDispatcher:
    def __init__(self):
        # 采集器优先级顺序
        self.crawlers: List[BaseCrawler] = [
            ImageAssetCrawler(),
            WeChatArticleCrawler(),
            BilibiliVideoCrawler(),
            WeChatChannelsCrawler(),
            WebpageCrawler()  # 通用网页兜底
        ]

    def dispatch(self, input_str: str, **kwargs) -> IngestedItem:
        target = input_str.strip()
        if not target:
            raise ValueError("输入内容不可为空")

        for crawler in self.crawlers:
            if crawler.match(target):
                logger.info(f"Dispatched [{target[:60]}...] to crawler: {crawler.name}")
                return crawler.fetch(target, **kwargs)

        # 若都不匹配且不是 URL，作为纯文本/笔记解析
        logger.info("No URL crawler matched, treating input as raw technical note...")
        return self._fallback_raw_text(target)

    def _fallback_raw_text(self, text: str) -> IngestedItem:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        title = lines[0][:40] if lines else "速记技术知识资产"
        return IngestedItem(
            title=title,
            source_type="quick_note",
            source_url="local://quick_note",
            author="User Manual Capture",
            summary=text[:200] + ("..." if len(text) > 200 else ""),
            content_markdown=f"# {title}\n\n{text}",
            key_points=[title],
            tags=["速记笔记", "本地知识"]
        )
