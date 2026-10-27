"""
Hermes Knowledge Base Configuration (配置中心)
"""
import os
import shutil
from pathlib import Path

# 根目录配置
BASE_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = BASE_DIR / "packages"
TEMPLATES_DIR = BASE_DIR / "templates"
TEMP_DIR = BASE_DIR / "temp"

# 创建核心目录
PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# 工具检测 (ffmpeg / ffprobe / yt-dlp)
def find_binary(name: str, fallback_paths: list[str]) -> str:
    found = shutil.which(name)
    if found:
        return found
    for p in fallback_paths:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return name

FFMPEG_BIN = find_binary("ffmpeg", ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"])
FFPROBE_BIN = find_binary("ffprobe", ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"])

# Git 配置
GIT_AUTO_COMMIT = True
GIT_DEFAULT_AUTHOR = "HermesKB Agent <hermes@local>"

# 预置领域与分类标签体系（用于智能聚类知识资产包）
DEFAULT_DOMAINS = {
    "web_dev_frontend": {
        "name": "前端与现代交互工程",
        "keywords": ["react", "vue", "nextjs", "css", "tailwind", "typescript", "threejs", "canvas", "webgpu", "ui", "ux", "前端", "组件"],
        "default_package": "frontend_engineering"
    },
    "agent_and_llm": {
        "name": "AI智能体与大模型工程",
        "keywords": ["agent", "llm", "langchain", "prompt", "rag", "mcp", "cursor", "codex", "claude", "gpt", "fine-tune", "智能体", "大模型", "工作流", "知识库"],
        "default_package": "ai_agent_architecture"
    },
    "crawler_and_automation": {
        "name": "爬虫逆向与全流程自动化",
        "keywords": ["crawler", "spider", "scrape", "selenium", "playwright", "wechat", "bilibili", "automation", "逆向", "公众号", "视频号", "爬虫", "抓包"],
        "default_package": "crawler_and_automation"
    },
    "computer_graphics_3d": {
        "name": "3D图形生成与数字制作",
        "keywords": ["blender", "threejs", "3d", "gaussian splatting", "3dgs", "nerf", "geometry", "mesh", "shader", "houdini", "建模", "渲染", "数字人"],
        "default_package": "3d_graphics_and_blender"
    },
    "system_and_backend": {
        "name": "后端架构与高性能系统",
        "keywords": ["fastapi", "docker", "k8s", "redis", "database", "postgres", "distributed", "microservice", "后端", "微服务", "架构", "并发"],
        "default_package": "system_architecture"
    },
    "product_and_methodology": {
        "name": "产品思维与设计方法论",
        "keywords": ["product", "growth", "strategy", "design pattern", "architecture", "方法论", "商业模式", "产品设计", "思维模型"],
        "default_package": "product_and_methodology"
    }
}

# 视频整理设置 (严格规范：不存原视频，提取关键帧截屏与核心详解)
VIDEO_SETTINGS = {
    "keyframe_count": 6,           # 默认从视频中均匀提取 6 张关键帧
    "keyframe_width": 1280,        # 关键帧缩放宽度 (保持高清且省空间)
    "keep_raw_video": False,       # 绝对不保留原始大视频文件
    "subtitles_languages": ["zh-Hans", "zh-CN", "zh", "en"]
}

# 网络请求通用头
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
