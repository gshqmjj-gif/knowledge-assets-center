"""
知识资产中心 Configuration (配置中心)
多级知识层级体系 (一级领域 > 二级子方向/专题 > 三级资产包)
"""
import os
import shutil
import yaml
from pathlib import Path

# 根目录配置
BASE_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = BASE_DIR / "packages"
TEMPLATES_DIR = BASE_DIR / "templates"
TEMP_DIR = BASE_DIR / "temp"
CUSTOM_DOMAINS_FILE = BASE_DIR / "custom_domains.yaml"

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
GIT_DEFAULT_AUTHOR = "知识资产中心 Agent <kb@local>"

# 多级领域知识分类体系 (一级领域 > 二级子方向/专题)
PRIMARY_DOMAINS = {
    "ai_tech": {
        "name": "AI科技与大模型",
        "icon": "🤖",
        "aliases": ["AI", "ai", "AI科技", "人工智能", "大模型", "智能体", "agent", "llm"],
        "sub_categories": {
            "ai_reverse": {
                "name": "逆向工程与代码复刻",
                "icon": "⚡",
                "keywords": ["逆向", "复刻", "reverse", "decompil", "rea", "pentagi", "ghidra", "ida", "反编译", "软件复刻"]
            },
            "ai_video": {
                "name": "AI视频与多模态创作",
                "icon": "🎬",
                "keywords": ["视频", "video", "opus", "runway", "sora", "cogvideo", "分镜", "关键帧", "剪辑", "视觉生成"]
            },
            "ai_agents": {
                "name": "智能体与工作流自动化",
                "icon": "🤖",
                "keywords": ["agent", "智能体", "mcp", "工作流", "langchain", "autogen", "crewai", "prompt", "提示词"]
            },
            "local_llm": {
                "name": "本地大模型与端侧推理优化",
                "icon": "🧠",
                "keywords": ["本地", "ollama", "rag", "知识库", "微调", "vllm", "llama", "airllm", "显存", "端侧", "推理优化", "私有化", "embedding", "向量检索"]
            },
            "visual_design": {
                "name": "架构可视化与技术图解",
                "icon": "📊",
                "keywords": ["架构图", "技术图解", "diagram", "时序图", "流程图", "excalidraw", "mermaid", "svg", "图解规矩", "视觉呈现"]
            }
        }
    },
    "productivity": {
        "name": "知识生产力与办公自动化",
        "icon": "📑",
        "aliases": ["生产力", "办公", "效率", "插件", "工作流", "productivity", "office"],
        "sub_categories": {
            "work_automation": {
                "name": "岗位工作流与企业自动化插件",
                "icon": "⚡",
                "keywords": ["岗位插件", "工作流", "自动化", "cowork", "企业级", "提示词规范", "知识工作者", "业务流程", "plugins"]
            }
        }
    },
    "business": {
        "name": "商业与商业模式",
        "icon": "💼",
        "aliases": ["商业", "商业模式", "商学", "变现", "运营", "营销", "投资", "出海", "business", "biz"],
        "sub_categories": {
            "monetization": {
                "name": "出海与独立开发变现",
                "icon": "🌍",
                "keywords": ["出海", "变现", "独立开发", "海外", "stripe", "global", "跨境", "副业", "产品出海"]
            },
            "saas_growth": {
                "name": "SaaS定价与增长策略",
                "icon": "📈",
                "keywords": ["saas", "定价", "增长", "获客", "留存", "plg", "mrr", "arr", "席位计费", "roi"]
            },
            "biz_breakdown": {
                "name": "商业模式与案例拆解",
                "icon": "🛒",
                "keywords": ["商业模式", "电商", "变现案例", "财报", "拆解", "盈利模式", "商业逻辑", "竞争壁垒"]
            }
        }
    },
    "architecture": {
        "name": "建筑设计与空间计算",
        "icon": "🏛️",
        "aliases": ["建筑", "空间", "室内", "空间计算", "bim", "architecture", "arch"],
        "sub_categories": {
            "parametric_design": {
                "name": "参数化算法与工业CAD",
                "icon": "📐",
                "keywords": ["参数化", "cad", "text-to-cad", "3d零件", "工程图", "grasshopper", "rhino", "幕墙", "立面", "可制造性", "cnc", "3d打印"]
            },
            "bim_automation": {
                "name": "BIM自动化与施工流转",
                "icon": "🏗️",
                "keywords": ["bim", "revit", "施工图", "构件", "装配式", "空间计算", "结构力学", "深化设计"]
            },
            "spatial_planning": {
                "name": "空间规划与户型计算",
                "icon": "🌐",
                "keywords": ["户型", "空间规划", "城市设计", "动线", "建筑学", "平面布局", "空间矩阵"]
            }
        }
    },
    "3d_visual": {
        "name": "三维与数字艺术",
        "icon": "🎨",
        "aliases": ["3D", "3d", "三维", "建模", "渲染", "blender", "视觉", "cg"],
        "sub_categories": {
            "blender_pipeline": {
                "name": "Blender建模与节点工作流",
                "icon": "🎨",
                "keywords": ["blender", "几何节点", "材质", "拓扑", "着色器", "shader", "雕刻", "布线"]
            },
            "gaussian_splatting": {
                "name": "3D高斯泼溅与实景重建",
                "icon": "⚡",
                "keywords": ["3dgs", "gaussian splatting", "nerf", "实景重建", "点云", "摄影测量", "trellis"]
            },
            "virtual_production": {
                "name": "虚幻引擎与数字制片",
                "icon": "🎮",
                "keywords": ["ue5", "虚幻引擎", "数字人", "场景", "虚拟制片", "vfx", "电影级渲染"]
            }
        }
    },
    "engineering": {
        "name": "全栈工程与系统研发",
        "icon": "⚙️",
        "aliases": ["技术", "工程", "开发", "代码", "全栈", "后端", "前端", "爬虫", "code", "dev"],
        "sub_categories": {
            "crawler_spider": {
                "name": "现代爬虫与自动化抓包",
                "icon": "🕷️",
                "keywords": ["爬虫", "逆向抓包", "playwright", "selenium", "自动化", "anti-bot", "charles", "frida"]
            },
            "backend_arch": {
                "name": "高并发系统与云原生SRE运维",
                "icon": "⚡",
                "keywords": ["后端", "sre", "opensre", "故障排查", "运维", "prometheus", "可观测性", "rca", "监控", "fastapi", "docker", "k8s", "redis", "postgres", "微服务", "并发"]
            },
            "frontend_ui": {
                "name": "前端交互与现代组件工程",
                "icon": "💻",
                "keywords": ["react", "vue", "nextjs", "tailwind", "typescript", "threejs", "canvas", "webgpu"]
            }
        }
    },
    "inbox": {
        "name": "待整理临时收件箱",
        "icon": "📥",
        "aliases": ["通用", "综合", "其他", "收藏", "inbox", "general"],
        "sub_categories": {
            "quick_capture": {
                "name": "临时快速收集",
                "icon": "📌",
                "keywords": ["临时", "速记", "待归档", "inbox"]
            }
        }
    }
}

def resolve_domain(input_domain_or_alias: str) -> str:
    """根据别名或模糊输入匹配标准一级领域 ID"""
    if not input_domain_or_alias:
        return "inbox"
    s = input_domain_or_alias.strip().lower()
    for dom_id, info in PRIMARY_DOMAINS.items():
        if s == dom_id.lower() or s == info["name"].lower():
            return dom_id
        for alias in info.get("aliases", []):
            if s == alias.lower() or alias.lower() in s:
                return dom_id
    return "inbox"

def resolve_sub_category(domain_key: str, text_blob: str) -> tuple[str, str]:
    """根据内容关键词在指定领域下自动路由二级子方向"""
    dom_info = PRIMARY_DOMAINS.get(domain_key)
    if not dom_info:
        dom_info = PRIMARY_DOMAINS["inbox"]
        domain_key = "inbox"

    sub_cats = dom_info.get("sub_categories", {})
    if not sub_cats:
        return "default", "默认子分类"

    blob_lower = text_blob.lower()
    best_sub = None
    best_matches = 0

    for sub_id, sub_info in sub_cats.items():
        matches = sum(1 for kw in sub_info.get("keywords", []) if kw.lower() in blob_lower)
        if matches > best_matches:
            best_matches = matches
            best_sub = (sub_id, sub_info.get("name", sub_id))

    if best_sub and best_matches > 0:
        return best_sub

    # 默认选该领域的第一个子方向
    first_key = list(sub_cats.keys())[0]
    return first_key, sub_cats[first_key]["name"]

# 视频整理设置 (严格规范：不存原视频，提取关键帧截屏与核心详解)
VIDEO_SETTINGS = {
    "keyframe_count": 6,           # 默认从视频中均匀提取 6 张关键帧
    "keyframe_width": 1280,        # 关键帧缩放宽度 (保持高清且省空间)
    "keep_raw_video": False,       # 绝对不保留原始大视频文件
    "subtitles_languages": ["zh-Hans", "zh-CN", "zh", "en"]
}

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def load_custom_domains():
    """从本地 custom_domains.yaml 加载用户已授权创建的自定义领域与子方向"""
    if CUSTOM_DOMAINS_FILE.exists():
        try:
            with open(CUSTOM_DOMAINS_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                for d_key, d_val in data.items():
                    if d_key in PRIMARY_DOMAINS:
                        PRIMARY_DOMAINS[d_key]["sub_categories"].update(d_val.get("sub_categories", {}))
                    else:
                        PRIMARY_DOMAINS[d_key] = d_val
        except Exception as e:
            pass

def save_custom_domain(domain_key: str, domain_name: str, domain_icon: str, sub_key: str, sub_name: str, sub_icon: str, keywords: list = None):
    """持久化保存用户授权新创建的类别体系至 custom_domains.yaml"""
    custom_data = {}
    if CUSTOM_DOMAINS_FILE.exists():
        try:
            with open(CUSTOM_DOMAINS_FILE, "r", encoding="utf-8") as f:
                custom_data = yaml.safe_load(f) or {}
        except Exception:
            pass

    if domain_key not in custom_data:
        custom_data[domain_key] = {
            "name": domain_name,
            "icon": domain_icon or "📁",
            "aliases": [domain_name, domain_key],
            "sub_categories": {}
        }

    custom_data[domain_key]["sub_categories"][sub_key] = {
        "name": sub_name,
        "icon": sub_icon or "📌",
        "keywords": keywords or [sub_name.lower(), domain_name.lower(), sub_key.lower()]
    }

    with open(CUSTOM_DOMAINS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(custom_data, f, allow_unicode=True, sort_keys=False)

    load_custom_domains()

# 初始化时加载已有自定义领域
load_custom_domains()
