"""
Hermes Knowledge Base Crawlers
"""
from crawlers.base import BaseCrawler, IngestedItem
from crawlers.bilibili_video import BilibiliVideoCrawler
from crawlers.dispatcher import CrawlerDispatcher
from crawlers.image_asset import ImageAssetCrawler
from crawlers.webpage import WebpageCrawler
from crawlers.wechat_article import WeChatArticleCrawler
from crawlers.wechat_channels import WeChatChannelsCrawler

__all__ = [
    "BaseCrawler",
    "IngestedItem",
    "CrawlerDispatcher",
    "WeChatArticleCrawler",
    "BilibiliVideoCrawler",
    "WeChatChannelsCrawler",
    "WebpageCrawler",
    "ImageAssetCrawler"
]
