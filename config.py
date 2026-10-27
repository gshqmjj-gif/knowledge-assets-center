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

# 一级领域知识分类体系 (Top-Level Domains)
PRIMARY_DOMAINS = {
    "business": {
        "name": "商业与商业模式",
        "icon": "💼",
        "aliases": ["商业", "商业模式", "商学", "变现", "运营", "营销", "投资", "出海", "business", "biz"],
        "keywords": [
            "商业模式", "商业", "变现", "运营", "营销", "投融资", "战略", "流量", "增长",
            "出海", "创业", "定价", "市场", "电商", "财报", "SaaS", "估值", "商业化",
            "business", "monetization", "marketing", "startup", "strategy", "roi", "b2b", "b2c"
        ],
        "default_package": "business_and_strategy",
        "default_package_name": "商业模式与战略运营"
    },
    "ai_tech": {
        "name": "AI科技与大模型",
        "icon": "🤖",
        "aliases": ["AI", "ai", "AI科技", "人工智能", "大模型", "智能体", "agent", "llm"],
        "keywords": [
            "agent", "llm", "langchain", "prompt", "rag", "mcp", "cursor", "codex", "claude",
            "gpt", "fine-tune", "智能体", "大模型", "工作流", "知识库", "提示词", "深度学习",
            "神经网络", "aigc", "transformer", "embedding", "openai", "anthropic"
        ],
        "default_package": "ai_tech_and_agents",
        "default_package_name": "AI前沿科技与智能体工程"
    },
    "architecture": {
        "name": "建筑设计与空间计算",
        "icon": "🏛️",
        "aliases": ["建筑", "空间", "室内", "空间计算", "bim", "architecture", "arch"],
        "keywords": [
            "建筑设计", "建筑", "规划", "室内设计", "空间", "结构", "参数化", "草图", "rhino",
            "grasshopper", "bim", "revit", "建筑学", "户型", "空间计算", "景观设计",
            "architecture", "parametric", "spatial", "urban design", "facade", "cad"
        ],
        "default_package": "architecture_and_spatial",
        "default_package_name": "建筑设计与空间计算"
    },
    "3d_and_visual": {
        "name": "三维与数字艺术",
        "icon": "🎨",
        "aliases": ["3D", "3d", "三维", "建模", "渲染", "blender", "视觉", "cg"],
        "keywords": [
            "blender", "threejs", "3d", "gaussian splatting", "3dgs", "nerf", "geometry",
            "mesh", "shader", "houdini", "建模", "渲染", "雕刻", "拓扑", "材质", "灯光",
            "虚幻引擎", "ue5", "unity", "数字人", "vfx", "视效", "动效"
        ],
        "default_package": "3d_and_digital_art",
        "default_package_name": "三维建模与数字视觉艺术"
    },
    "product_and_design": {
        "name": "产品设计与用户体验",
        "icon": "💡",
        "aliases": ["产品", "设计", "体验", "交互", "ui", "ux", "product"],
        "keywords": [
            "产品经理", "产品设计", "ui", "ux", "交互设计", "用户体验", "需求分析", "流程图",
            "线框图", "原型", "figma", "设计系统", "体验设计", "增长黑客", "用户研究",
            "product management", "design system", "wireframe", "prototype"
        ],
        "default_package": "product_and_ux_design",
        "default_package_name": "产品逻辑与交互设计"
    },
    "engineering_and_dev": {
        "name": "全栈工程与系统研发",
        "icon": "⚙️",
        "aliases": ["技术", "工程", "开发", "代码", "全栈", "后端", "前端", "爬虫", "code", "dev"],
        "keywords": [
            "python", "react", "vue", "nextjs", "css", "tailwind", "typescript", "fastapi",
            "docker", "k8s", "redis", "database", "postgres", "microservice", "爬虫", "逆向",
            "抓包", "自动化", "selenium", "playwright", "后端", "微服务", "架构", "并发"
        ],
        "default_package": "fullstack_engineering",
        "default_package_name": "全栈开发与系统工程"
    },
    "general_inbox": {
        "name": "通用知识与综合收藏",
        "icon": "📥",
        "aliases": ["通用", "综合", "其他", "收藏", "inbox", "general"],
        "keywords": ["知识", "通用", "灵感", "随笔", "读书笔记", "方法论"],
        "default_package": "general_knowledge_inbox",
        "default_package_name": "通用技术与灵感收藏箱"
    }
}

def resolve_domain(input_domain_or_alias: str) -> str:
    """根据别名或模糊输入匹配标准领域 ID"""
    if not input_domain_or_alias:
        return "general_inbox"
    s = input_domain_or_alias.strip().lower()
    for dom_id, info in PRIMARY_DOMAINS.items():
        if s == dom_id.lower() or s == info["name"].lower():
            return dom_id
        for alias in info.get("aliases", []):
            if s == alias.lower() or alias.lower() in s:
                return dom_id
    return "general_inbox"

# 兼容旧字段
DEFAULT_DOMAINS = PRIMARY_DOMAINS

# 视频整理设置 (严格规范：不存原视频，提取关键帧截屏与核心详解)
VIDEO_SETTINGS = {
    "keyframe_count": 6,           # 默认从视频中均匀提取 6 张关键帧
    "keyframe_width": 1280,        # 关键帧缩放宽度 (保持高清且省空间)
    "keep_raw_video": False,       # 绝对不保留原始大视频文件
    "subtitles_languages": ["zh-Hans", "zh-CN", "zh", "en"]
}

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
