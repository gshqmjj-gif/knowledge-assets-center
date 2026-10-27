"""
Hermes Knowledge Base Web Server & API
提供本地可视化操作台：多级知识分层、全局检索、一键采集、多渠道知识库浏览、关键帧视觉预览、一键导出给 Cursor / Codex / Hermes
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import PACKAGES_DIR, PRIMARY_DOMAINS
from core.agent_exporter import AgentExporter
from core.git_manager import GitManager
from core.package_manager import KnowledgePackageManager
from crawlers.dispatcher import CrawlerDispatcher

logger = logging.getLogger("hermes.web")

app = FastAPI(title="知识资产中心 (Knowledge Assets Hub)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pm = KnowledgePackageManager()
exporter = AgentExporter(pm)
git_mgr = GitManager()
dispatcher = CrawlerDispatcher()

# 静态资源挂载 (查看关键帧与架构图)
app.mount("/packages", StaticFiles(directory=str(PACKAGES_DIR)), name="packages")

class IngestRequest(BaseModel):
    url: str
    package: Optional[str] = None
    domain: Optional[str] = None
    sub_category: Optional[str] = None
    allow_create_new: Optional[bool] = False
    new_domain_key: Optional[str] = None
    new_domain_name: Optional[str] = None
    new_domain_icon: Optional[str] = None
    new_sub_key: Optional[str] = None
    new_sub_name: Optional[str] = None
    new_sub_icon: Optional[str] = None
    force_confirm: Optional[bool] = False

class CopyRequest(BaseModel):
    text: str

@app.get("/api/taxonomy")
def get_taxonomy():
    pkgs = pm.list_packages()
    stats = {}
    for p in pkgs:
        d = p.get("domain", "inbox")
        sub = p.get("sub_category", "default")
        stats.setdefault(d, {}).setdefault(sub, 0)
        stats[d][sub] += 1
    total_sources = sum(p.get("item_count", 0) for p in pkgs)
    return {
        "domains": PRIMARY_DOMAINS,
        "stats": stats,
        "total_packages": len(pkgs),
        "total_sources": total_sources
    }

@app.get("/api/domains")
def list_domains():
    return {"domains": PRIMARY_DOMAINS}

@app.get("/api/packages")
def list_packages(domain: Optional[str] = None, sub: Optional[str] = None):
    pkgs = pm.list_packages()
    if domain and domain != "all":
        pkgs = [p for p in pkgs if p.get("domain") == domain]
    if sub and sub != "all":
        pkgs = [p for p in pkgs if p.get("sub_category") == sub]
    return {"packages": pkgs}

@app.delete("/api/packages/{package_id}")
def delete_package_api(package_id: str):
    ok = pm.delete_package(package_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Package not found")
    git_mgr.commit(f"feat(kb): delete package '{package_id}'")
    return {"success": True, "message": f"Package {package_id} deleted."}

@app.delete("/api/packages/{package_id}/sources")
def delete_source_api(package_id: str, file: str):
    ok = pm.delete_source(package_id, file)
    if not ok:
        raise HTTPException(status_code=404, detail="Source not found")
    git_mgr.commit(f"feat(kb): delete source '{file}' from '{package_id}'")
    return {"success": True, "message": f"Source {file} deleted."}

@app.get("/api/search")
def search_api(q: str):
    return exporter.search(q)

@app.get("/api/packages/{package_id}")
def get_package(package_id: str):
    pkg = pm.get_package(package_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Asset package not found")
    
    pkg_dir = Path(pkg["path"])
    summary_file = pkg_dir / "SUMMARY.md"
    agent_file = pkg_dir / "AGENT_CONTEXT.md"

    summary_text = summary_file.read_text(encoding="utf-8") if summary_file.exists() else ""
    agent_text = agent_file.read_text(encoding="utf-8") if agent_file.exists() else ""

    # 获取所有关键帧图片链接
    keyframes = []
    kf_dir = pkg_dir / "keyframes"
    if kf_dir.exists():
        for f in sorted(kf_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in [".jpg", ".png", ".webp"]:
                keyframes.append(f"/packages/{package_id}/keyframes/{f.name}")

    return {
        "metadata": pkg,
        "summary": summary_text,
        "agent_context": agent_text,
        "keyframes": keyframes
    }

@app.post("/api/ingest")
def ingest_api(req: IngestRequest):
    try:
        import re
        item = dispatcher.dispatch(req.url)

        # 1. 用户允许创建新类别
        if req.allow_create_new and req.new_domain_name and req.new_sub_name:
            dom_key = req.new_domain_key or re.sub(r'[^a-zA-Z0-9_]', '_', req.new_domain_name).lower().strip('_')
            sub_key = req.new_sub_key or re.sub(r'[^a-zA-Z0-9_]', '_', req.new_sub_name).lower().strip('_')
            new_pkg_id = pm.create_custom_domain_and_package(
                domain_key=dom_key,
                domain_name=req.new_domain_name,
                domain_icon=req.new_domain_icon or "📁",
                sub_key=sub_key,
                sub_name=req.new_sub_name,
                sub_icon=req.new_sub_icon or "📌"
            )
            pkg_id, source_path = pm.ingest_item(
                item,
                preferred_package=new_pkg_id,
                preferred_domain=dom_key,
                preferred_sub_category=sub_key
            )

        # 2. 用户显式指定了现有领域/子方向或已有资产包
        elif req.package or req.domain or req.sub_category:
            pkg_id, source_path = pm.ingest_item(
                item,
                preferred_package=req.package,
                preferred_domain=req.domain,
                preferred_sub_category=req.sub_category
            )

        # 3. 自动识别：若无法按照现有分类表结构化，弹出确认对话框
        else:
            has_sub_items = getattr(item, "sub_items", None) and len(item.sub_items) >= 2
            if not has_sub_items:
                clf_result = pm.classify_content(item)
                if not clf_result["is_matched"] and not req.force_confirm:
                    # 构建完整分类树供用户选择现有类别
                    taxonomy_list = []
                    for dk, dv in PRIMARY_DOMAINS.items():
                        subs = [
                            {"id": sk, "name": sv.get("name", sk), "icon": sv.get("icon", "📌")}
                            for sk, sv in dv.get("sub_categories", {}).items()
                        ]
                        taxonomy_list.append({
                            "domain_key": dk,
                            "domain_name": dv.get("name", dk),
                            "domain_icon": dv.get("icon", "📁"),
                            "sub_categories": subs
                        })

                    return {
                        "success": False,
                        "needs_confirmation": True,
                        "message": "未能精准匹配现有分类体系，请确认是否允许创建新类别或指定某一现有类别。",
                        "item_preview": {
                            "title": item.title,
                            "source_type": item.source_type,
                            "author": item.author,
                            "summary": item.summary,
                            "tags": item.tags,
                            "url": req.url
                        },
                        "suggested_category": clf_result["suggested"],
                        "existing_taxonomy": taxonomy_list
                    }

            pkg_id, source_path = pm.ingest_item(item)
        
        # Git 自动提交
        commit_hash = git_mgr.commit(f"feat(kb): ingest [{item.source_type}] {item.title[:40]} into package '{pkg_id}'")

        pkg_meta = pm.get_package(pkg_id) or {}
        packages_affected = item.metadata.get("packages_affected", [pkg_id])
        sub_items_count = len(getattr(item, "sub_items", []))

        return {
            "success": True,
            "title": item.title,
            "source_type": item.source_type,
            "package_id": pkg_id,
            "package_name": pkg_meta.get("name"),
            "domain_name": pkg_meta.get("domain_name"),
            "domain_icon": pkg_meta.get("domain_icon"),
            "sub_category_name": pkg_meta.get("sub_category_name"),
            "sub_category_icon": pkg_meta.get("sub_category_icon"),
            "source_file": source_path.name if source_path else "",
            "keyframes_count": len(item.keyframes),
            "snippets_count": len(item.code_snippets),
            "decomposed": sub_items_count >= 2,
            "sub_items_count": sub_items_count,
            "packages_affected": packages_affected,
            "commit": commit_hash
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/{package_id}")
def export_api(package_id: str, target: str = "cursor"):
    try:
        if target == "cursor":
            content = exporter.export_for_cursor(package_id, format_type="mdc")
        elif target == "codex":
            content = exporter.export_for_codex(package_id)
        elif target == "hermes":
            content = exporter.export_for_hermes(package_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid target agent")
        return {"content": content, "target": target}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/copy")
def copy_api(req: CopyRequest):
    success = exporter.copy_to_clipboard(req.text)
    return {"success": success}

@app.get("/api/clipboard")
def get_clipboard_api():
    text = exporter.read_from_clipboard()
    return {"text": text}

@app.get("/api/source_content/{package_id}")
def get_source_content(package_id: str, file: str):
    pkg = pm.get_package(package_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    
    pkg_dir = Path(pkg["path"])
    clean_file = file.lstrip("/")
    target_file = pkg_dir / clean_file
    
    try:
        target_file.resolve().relative_to(pkg_dir.resolve())
    except Exception:
        raise HTTPException(status_code=403, detail="Forbidden file access")
        
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Source file not found")
        
    content = target_file.read_text(encoding="utf-8")
    return {
        "filename": target_file.name,
        "path": str(target_file),
        "content": content
    }

@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTML_DASHBOARD

HTML_DASHBOARD = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="referrer" content="no-referrer">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>知识资产中心</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #0b0f17; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    .glass-card { background: rgba(18, 23, 33, 0.88); backdrop-filter: blur(12px); border: 1px solid #232b38; }
    .glass-pane { background: rgba(14, 18, 26, 0.95); border: 1px solid #232b38; }
    .btn-gradient { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .btn-agent { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
    .active-nav-item { background: rgba(99, 102, 241, 0.18) !important; border-color: #6366f1 !important; color: #ffffff !important; }
    .active-pkg-card { border-color: #6366f1 !important; background: rgba(99, 102, 241, 0.1) !important; box-shadow: 0 0 15px rgba(99, 102, 241, 0.2); }
    .prose-clean h1 { font-size: 1.4rem; font-weight: 700; color: #ffffff; margin-top: 1.25rem; margin-bottom: 0.6rem; }
    .prose-clean h2 { font-size: 1.2rem; font-weight: 600; color: #e6edf3; margin-top: 1.25rem; margin-bottom: 0.5rem; border-bottom: 1px solid #2d3748; padding-bottom: 0.25rem; }
    .prose-clean h3 { font-size: 1.05rem; font-weight: 600; color: #93c5fd; margin-top: 1rem; margin-bottom: 0.4rem; }
    .prose-clean p { margin-bottom: 0.75rem; line-height: 1.65; color: #cbd5e1; }
    .prose-clean pre { background: #0d1117; padding: 0.85rem; border-radius: 0.5rem; border: 1px solid #30363d; overflow-x: auto; margin-bottom: 0.85rem; }
    .prose-clean code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.85rem; color: #fbcfe8; }
    .prose-clean img { max-width: 100%; height: auto; border-radius: 0.5rem; margin: 0.85rem 0; border: 1px solid #30363d; }
    .prose-clean table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; font-size: 0.82rem; }
    .prose-clean th, .prose-clean td { border: 1px solid #30363d; padding: 0.45rem 0.65rem; text-align: left; }
    .prose-clean th { background: #161b22; color: #ffffff; font-weight: 600; }
    .prose-clean tr:nth-child(even) { background: #0d1117; }
    .prose-clean blockquote { border-left: 3px solid #6366f1; padding-left: 0.75rem; color: #94a3b8; margin: 0.75rem 0; font-style: italic; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0b0f17; }
    ::-webkit-scrollbar-thumb { background: #232b38; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #374151; }
  </style>
</head>
<body class="min-h-screen flex flex-col">
  <!-- Toast Notification Container -->
  <div id="toast" class="fixed top-5 right-5 z-50 transform transition-all duration-300 translate-y-[-100px] opacity-0 pointer-events-none">
    <div id="toastContent" class="glass-card px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 text-sm font-medium border border-indigo-500/50">
      <i id="toastIcon" class="fa-solid fa-circle-check text-emerald-400"></i>
      <span id="toastMsg" class="text-white">通知内容</span>
    </div>
  </div>

  <!-- Top Sticky Header -->
  <header class="sticky top-0 z-40 bg-[#0b0f17]/90 backdrop-blur-md border-b border-gray-800/80 px-5 py-3">
    <div class="max-w-[1720px] mx-auto flex items-center justify-between gap-4">
      <!-- Logo & Title -->
      <div class="flex items-center space-x-3 shrink-0">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white font-black text-xl shadow-md shadow-indigo-500/30 tracking-tight">
          K
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold text-white tracking-tight">知识资产中心</h1>
            <span class="text-[10px] bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 px-1.5 py-0.2 rounded font-mono">v2.0</span>
          </div>
          <p class="text-[11px] text-gray-400">微信/视频号/B站/网页/图片多模态沉淀 · 纯本地 Git 离线脱机存储</p>
        </div>
      </div>

      <!-- Center: Global Real-time Search -->
      <div class="flex-1 max-w-2xl relative">
        <div class="relative flex items-center">
          <i class="fa-solid fa-magnifying-glass absolute left-3.5 text-gray-400 text-xs"></i>
          <input id="globalSearchInput" type="text" oninput="handleSearch(this.value)" placeholder="全库实时检索：资产包、技术实体、硬件配置、代码或作者... (支持全文字段匹配)" 
            class="w-full bg-gray-900/90 border border-gray-700/80 rounded-xl pl-9 pr-8 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition shadow-inner">
          <button id="btnClearSearch" onclick="clearSearch()" class="absolute right-3 text-gray-400 hover:text-white hidden text-xs">
            <i class="fa-solid fa-circle-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Right Actions & Status Badges -->
      <div class="flex items-center space-x-3 shrink-0 text-xs">
        <div class="hidden sm:flex items-center gap-2 bg-gray-900 border border-gray-800 px-3 py-1.5 rounded-xl text-gray-300 font-mono">
          <i class="fa-solid fa-cubes text-indigo-400"></i>
          <span id="statPkgCount">0</span> 资产包
          <span class="text-gray-600">|</span>
          <i class="fa-solid fa-file-shield text-emerald-400"></i>
          <span id="statSrcCount">0</span> 脱机文档
        </div>
        <button onclick="toggleIngestPanel()" class="btn-gradient hover:opacity-95 text-white px-3.5 py-1.5 rounded-xl font-medium transition flex items-center gap-1.5 shadow">
          <i class="fa-solid fa-plus-circle"></i> 录入新知识
        </button>
      </div>
    </div>
  </header>

  <!-- Collapsible Ingestion Panel -->
  <div id="ingestPanel" class="bg-gray-950/95 border-b border-gray-800/80 px-6 py-5 hidden transition-all">
    <div class="max-w-[1720px] mx-auto">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
          <i class="fa-solid fa-bolt text-emerald-400"></i> 一键极速采集并结构化入库
        </h3>
        <span class="text-xs text-gray-400">支持：微信公众号文章、视频号分享卡片、B站视频(免下原片截取关键帧)、技术网页、本地图片</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
        <!-- 一级领域选择 -->
        <div class="md:col-span-2">
          <select id="selectDomain" onchange="handleDomainChange()" class="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500">
            <option value="">⚡ 智能识别一级领域</option>
            <option value="ai_tech">🤖 AI科技与大模型</option>
            <option value="business">💼 商业与商业模式</option>
            <option value="architecture">🏛️ 建筑设计与空间计算</option>
            <option value="3d_visual">🎨 三维与数字艺术</option>
            <option value="engineering">⚙️ 全栈工程与研发</option>
            <option value="inbox">📥 待整理临时收件箱</option>
          </select>
        </div>
        <!-- 二级子方向选择 -->
        <div class="md:col-span-2">
          <select id="selectSubCategory" class="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500">
            <option value="">📌 智能识别二级子方向</option>
          </select>
        </div>
        <!-- URL 输入 -->
        <div class="md:col-span-6 flex gap-2">
          <input id="inputUrl" type="text" placeholder="粘贴微信公众号文章链接、视频号分享文本、B站视频地址、网页 URL 或图片路径..." 
            class="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-3.5 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-xs">
          <button onclick="readFromClip()" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-xl text-xs font-medium border border-gray-700 transition flex items-center gap-1.5 shrink-0">
            <i class="fa-regular fa-clipboard"></i> 剪贴板
          </button>
        </div>
        <!-- 提交采集按钮 -->
        <div class="md:col-span-2">
          <button id="btnIngest" onclick="handleIngest()" class="w-full btn-gradient hover:opacity-95 text-white py-2 rounded-xl text-xs font-semibold transition flex items-center justify-center gap-1.5 shadow">
            <i class="fa-solid fa-download"></i> 抓取并增量归包
          </button>
        </div>
      </div>
      <div id="ingestStatus" class="mt-2 text-xs hidden"></div>
    </div>
  </div>

  <!-- Main 3-Column Body -->
  <main class="flex-1 max-w-[1720px] w-full mx-auto px-5 py-4 overflow-hidden flex flex-col">
    <!-- Search Results View (Shown when searching) -->
    <div id="searchResultsView" class="hidden flex-1 overflow-y-auto space-y-4">
      <div class="flex justify-between items-center border-b border-gray-800 pb-3">
        <h3 class="text-base font-bold text-white flex items-center gap-2">
          <i class="fa-solid fa-magnifying-glass text-indigo-400"></i> 全库综合检索结果: <span id="searchQueryLabel" class="text-indigo-400 font-mono"></span>
        </h3>
        <button onclick="clearSearch()" class="text-xs text-gray-400 hover:text-white px-3 py-1 bg-gray-800 rounded-lg">
          <i class="fa-solid fa-arrow-left mr-1"></i> 返回层级导航
        </button>
      </div>
      <div id="searchResultsContent" class="space-y-6">
        <!-- Rendered by JS -->
      </div>
    </div>

    <!-- Normal 3-Pane Hierarchy View -->
    <div id="normalHierarchyView" class="flex-1 grid grid-cols-12 gap-5 h-[calc(100vh-100px)]">
      <!-- Column 1: Knowledge Taxonomy Tree (一级领域与二级专题导航) -->
      <aside class="col-span-12 md:col-span-3 lg:col-span-2 flex flex-col glass-pane rounded-2xl p-3 overflow-hidden">
        <div class="flex justify-between items-center px-2 py-2 border-b border-gray-800/80 mb-2">
          <span class="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
            <i class="fa-solid fa-sitemap text-indigo-400"></i> 知识层级分类
          </span>
          <button onclick="loadTaxonomy()" class="text-[11px] text-gray-400 hover:text-white" title="刷新分类"><i class="fa-solid fa-rotate-right"></i></button>
        </div>
        
        <div class="flex-1 overflow-y-auto space-y-1.5 pr-1" id="taxonomyTree">
          <!-- Rendered dynamically -->
          <div class="text-center py-10 text-xs text-gray-500">加载层级树...</div>
        </div>
      </aside>

      <!-- Column 2: Packages List (资产包精选卡片) -->
      <section class="col-span-12 md:col-span-4 lg:col-span-3 flex flex-col glass-pane rounded-2xl p-3 overflow-hidden">
        <div class="flex justify-between items-center px-2 py-2 border-b border-gray-800/80 mb-2">
          <div>
            <h3 id="currentFilterTitle" class="text-xs font-bold text-white flex items-center gap-1.5">
              <i class="fa-solid fa-cubes text-indigo-400"></i> 全部知识资产包
            </h3>
            <span id="pkgListSubTitle" class="text-[10px] text-gray-400">包含 0 个资产包</span>
          </div>
          <button onclick="loadPackages()" class="text-[11px] text-gray-400 hover:text-white"><i class="fa-solid fa-arrows-rotate"></i></button>
        </div>

        <div class="flex-1 overflow-y-auto space-y-2 pr-1" id="packagesList">
          <div class="text-center py-12 text-xs text-gray-500">加载中...</div>
        </div>
      </section>

      <!-- Column 3: Package Inspector & Agent Dispatch Hub (资产包深度检视与 Agent 派发) -->
      <section class="col-span-12 md:col-span-5 lg:col-span-7 flex flex-col glass-pane rounded-2xl p-5 overflow-hidden">
        <div id="inspectorContent" class="flex-1 overflow-y-auto pr-2">
          <div class="text-center py-32 text-gray-500">
            <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-600">
              <i class="fa-solid fa-cubes-stacked text-3xl"></i>
            </div>
            <h4 class="text-sm font-semibold text-gray-400">请选择左侧的知识资产包</h4>
            <p class="text-xs text-gray-500 mt-1">检视硬件/环境/优劣势对比矩阵、100%本地脱机源文，并一键派发给 Cursor、Codex 或 Hermes</p>
          </div>
        </div>
      </section>
    </div>
  </main>

  <!-- Local Offline Reader Modal (100% 本地脱机阅读器) -->
  <div id="readerModal" class="fixed inset-0 bg-black/85 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
    <div class="bg-gray-900 border border-gray-700 w-full max-w-4xl max-h-[90vh] rounded-2xl flex flex-col shadow-2xl">
      <div class="flex justify-between items-center px-6 py-4 border-b border-gray-800 bg-gray-950/80 rounded-t-2xl">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-medium">
              <i class="fa-solid fa-hard-drive mr-1"></i> 100% 本地脱机永久归档 (免依赖原链接)
            </span>
            <span id="modalPath" class="text-[11px] text-gray-500 font-mono"></span>
          </div>
          <h3 id="modalTitle" class="text-base font-bold text-white mt-1"></h3>
        </div>
        <button onclick="closeReaderModal()" class="text-gray-400 hover:text-white p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>
      <div id="modalBody" class="p-6 overflow-y-auto flex-1 text-xs text-gray-200 leading-relaxed font-sans space-y-4">
      </div>
    </div>
  </div>

  <!-- Video Player Modal (控制台内嵌免流播放器) -->
  <div id="videoModal" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
    <div class="bg-gray-900 border border-gray-700 w-full max-w-4xl max-h-[92vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden">
      <div class="flex justify-between items-center px-6 py-4 border-b border-gray-800 bg-gray-950/80">
        <div class="flex items-center gap-2.5">
          <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
          <h3 id="videoModalTitle" class="text-sm font-bold text-white truncate max-w-xl"></h3>
        </div>
        <button onclick="closeVideoModal()" class="text-gray-400 hover:text-white p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>
      <div id="videoPlayerContainer" class="p-6 overflow-y-auto flex-1 flex flex-col items-center justify-center min-h-[460px]">
      </div>
    </div>
  </div>

  <!-- Keyframe Full-Resolution Lightbox Modal -->
  <div id="lightboxModal" class="fixed inset-0 bg-black/95 backdrop-blur-md z-50 hidden flex items-center justify-center p-4" onclick="closeLightboxModal()">
    <div class="max-w-5xl max-h-[90vh] flex flex-col items-center justify-center relative" onclick="event.stopPropagation()">
      <button onclick="closeLightboxModal()" class="absolute -top-10 right-0 text-gray-400 hover:text-white p-2 rounded-lg bg-gray-800 transition">
        <i class="fa-solid fa-xmark text-lg"></i>
      </button>
      <img id="lightboxImg" src="" class="max-w-full max-h-[85vh] rounded-xl border border-gray-800 shadow-2xl object-contain">
      <div id="lightboxCaption" class="mt-2 text-xs font-mono text-gray-400 text-center"></div>
    </div>
  </div>

  <!-- Interactive Classification Decision Modal (分类未命中交互决策弹窗) -->
  <div id="classificationModal" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
    <div class="bg-gray-900 border border-yellow-500/40 w-full max-w-2xl max-h-[92vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <div class="flex justify-between items-center px-6 py-4 border-b border-gray-800 bg-gray-950/90">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-yellow-500/20 text-yellow-400 flex items-center justify-center text-sm font-bold border border-yellow-500/30">
            <i class="fa-solid fa-triangle-exclamation"></i>
          </div>
          <div>
            <h3 class="text-sm font-bold text-white">未能精准匹配现有知识分类表</h3>
            <p class="text-[11px] text-gray-400">系统对该内容的分析未命中现有领域，请决策分类归属：</p>
          </div>
        </div>
        <button onclick="closeClassificationModal()" class="text-gray-400 hover:text-white p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 transition">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <div class="p-6 overflow-y-auto flex-1 space-y-5 text-xs text-gray-200">
        <!-- Ingested Content Preview Card -->
        <div class="bg-gray-950/80 border border-gray-800 rounded-xl p-3.5 space-y-2">
          <div class="flex items-center justify-between text-[11px] text-gray-400">
            <span class="flex items-center gap-1.5 text-indigo-400 font-medium">
              <i class="fa-solid fa-file-lines"></i> 待入库实体
            </span>
            <span id="clfSourceType" class="font-mono bg-gray-900 px-2 py-0.5 rounded border border-gray-800"></span>
          </div>
          <h4 id="clfTitle" class="text-sm font-bold text-white leading-snug"></h4>
          <p id="clfSummary" class="text-xs text-gray-400 line-clamp-2"></p>
        </div>

        <!-- Choice 1: Allow Creating New Category -->
        <div class="border border-emerald-500/40 bg-emerald-950/10 rounded-xl p-4 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span class="text-xs font-bold text-white">选项一：我允许创建新的分类类别 (推荐)</span>
            </div>
            <span class="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-mono">智能推荐</span>
          </div>
          <p class="text-[11px] text-gray-400">系统将根据您确认的名称，永久扩展分类体系并自动生成专属资产包：</p>
          
          <div class="grid grid-cols-2 gap-3 pt-1">
            <div>
              <label class="block text-[11px] text-gray-400 mb-1">一级所属领域名称</label>
              <input id="clfNewDomainName" type="text" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
            </div>
            <div>
              <label class="block text-[11px] text-gray-400 mb-1">二级子方向专题名称</label>
              <input id="clfNewSubName" type="text" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
            </div>
          </div>

          <button id="btnAllowCreateNew" onclick="confirmCreateNewCategory()" class="w-full mt-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium py-2 rounded-lg text-xs shadow-md shadow-emerald-900/30 flex items-center justify-center gap-2 transition">
            <i class="fa-solid fa-folder-plus"></i> 允许并以新类别创建资产包入库
          </button>
        </div>

        <!-- Choice 2: Disallow, Let User Select Existing Category -->
        <div class="border border-indigo-500/30 bg-indigo-950/10 rounded-xl p-4 space-y-3">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
            <span class="text-xs font-bold text-white">选项二：我不允许，由我指定归入某一现有类别</span>
          </div>
          <p class="text-[11px] text-gray-400">从当前的知识库领域分类表中选择最符合的分类：</p>

          <div class="pt-1">
            <select id="clfSelectExisting" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500">
            </select>
          </div>

          <button id="btnSelectExisting" onclick="confirmSelectExistingCategory()" class="w-full mt-2 bg-gray-800 hover:bg-gray-700 text-white font-medium py-2 rounded-lg text-xs border border-gray-700 flex items-center justify-center gap-2 transition">
            <i class="fa-solid fa-check"></i> 归入所选现有类别
          </button>
        </div>
      </div>

      <div class="px-6 py-3 border-t border-gray-800 bg-gray-950/90 flex justify-end">
        <button onclick="closeClassificationModal()" class="text-xs text-gray-400 hover:text-white px-3 py-1.5 rounded-lg hover:bg-gray-800 transition">
          放弃本次录入
        </button>
      </div>
    </div>
  </div>

  <script>
    let taxonomyData = null;
    let currentDomain = 'all';
    let currentSubCategory = 'all';
    let currentCategoryName = '全部知识资产包';
    let activePackageId = null;
    let searchDebounceTimer = null;

    // Toast 浮动提示
    function showToast(msg, isSuccess = true) {
      const toast = document.getElementById('toast');
      const toastMsg = document.getElementById('toastMsg');
      const toastIcon = document.getElementById('toastIcon');
      toastMsg.innerText = msg;
      toastIcon.className = isSuccess ? 'fa-solid fa-circle-check text-emerald-400' : 'fa-solid fa-triangle-exclamation text-rose-400';
      toast.classList.remove('translate-y-[-100px]', 'opacity-0', 'pointer-events-none');
      setTimeout(() => {
        toast.classList.add('translate-y-[-100px]', 'opacity-0', 'pointer-events-none');
      }, 3500);
    }

    function toggleIngestPanel() {
      const panel = document.getElementById('ingestPanel');
      panel.classList.toggle('hidden');
    }

    // 处理领域联动二级子分类
    function handleDomainChange() {
      const domSelect = document.getElementById('selectDomain');
      const subSelect = document.getElementById('selectSubCategory');
      const domVal = domSelect.value;
      subSelect.innerHTML = '<option value="">📌 智能识别二级子方向</option>';
      if (!domVal || !taxonomyData || !taxonomyData.domains[domVal]) return;

      const subCats = taxonomyData.domains[domVal].sub_categories || {};
      for (const [subId, subInfo] of Object.entries(subCats)) {
        const opt = document.createElement('option');
        opt.value = subId;
        opt.innerText = `${subInfo.icon || '📌'} ${subInfo.name}`;
        subSelect.appendChild(opt);
      }
    }

    // 1. 加载知识层级树 (Taxonomy Tree)
    async function loadTaxonomy() {
      try {
        const res = await fetch('/api/taxonomy');
        taxonomyData = await res.json();
        const treeContainer = document.getElementById('taxonomyTree');
        document.getElementById('statPkgCount').innerText = taxonomyData.total_packages || 0;
        document.getElementById('statSrcCount').innerText = taxonomyData.total_sources || 0;

        let html = `
          <div onclick="selectCategory('all', 'all', '全部知识资产包')" 
            class="px-2.5 py-2 rounded-xl cursor-pointer text-xs flex items-center justify-between transition border border-transparent hover:bg-gray-800/80 ${currentDomain === 'all' ? 'active-nav-item' : 'text-gray-300'}">
            <span class="flex items-center gap-2 font-medium">
              <i class="fa-solid fa-layer-group text-indigo-400"></i> 全部资产
            </span>
            <span class="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded font-mono">${taxonomyData.total_packages}</span>
          </div>
        `;

        for (const [domKey, domInfo] of Object.entries(taxonomyData.domains)) {
          const domStats = taxonomyData.stats[domKey] || {};
          const domTotal = Object.values(domStats).reduce((a, b) => a + b, 0);
          const isDomActive = currentDomain === domKey && currentSubCategory === 'all';

          html += `
            <div class="pt-1.5">
              <div onclick="selectCategory('${domKey}', 'all', '${domInfo.name}')" 
                class="px-2.5 py-1.5 rounded-xl cursor-pointer text-xs flex items-center justify-between transition border border-transparent hover:bg-gray-800/60 font-semibold ${isDomActive ? 'active-nav-item' : 'text-gray-200'}">
                <span class="flex items-center gap-1.5 truncate">
                  <span>${domInfo.icon || '📁'}</span>
                  <span class="truncate">${domInfo.name}</span>
                </span>
                <span class="text-[10px] bg-gray-800/90 text-gray-400 px-1.5 py-0.2 rounded font-mono">${domTotal}</span>
              </div>
              <div class="pl-4 space-y-0.5 mt-0.5 border-l border-gray-800/80 ml-2">
          `;

          for (const [subKey, subInfo] of Object.entries(domInfo.sub_categories || {})) {
            const count = domStats[subKey] || 0;
            const isSubActive = currentDomain === domKey && currentSubCategory === subKey;
            html += `
              <div onclick="selectCategory('${domKey}', '${subKey}', '${subInfo.name}')" 
                class="px-2 py-1 rounded-lg cursor-pointer text-[11px] flex items-center justify-between transition hover:bg-gray-800/50 ${isSubActive ? 'active-nav-item' : 'text-gray-400 hover:text-gray-200'}">
                <span class="flex items-center gap-1.5 truncate">
                  <span class="text-[10px]">${subInfo.icon || '📌'}</span>
                  <span class="truncate">${subInfo.name}</span>
                </span>
                <span class="text-[10px] ${count > 0 ? 'text-indigo-400 font-bold' : 'text-gray-600'} font-mono">${count}</span>
              </div>
            `;
          }

          html += `
              </div>
            </div>
          `;
        }

        treeContainer.innerHTML = html;
      } catch (e) {
        console.error('Failed to load taxonomy:', e);
      }
    }

    function selectCategory(dom, sub, name) {
      currentDomain = dom;
      currentSubCategory = sub;
      currentCategoryName = name;
      loadTaxonomy();
      loadPackages();
    }

    // 2. 加载资产包列表
    async function loadPackages() {
      try {
        let url = '/api/packages';
        const params = [];
        if (currentDomain !== 'all') params.push(`domain=${currentDomain}`);
        if (currentSubCategory !== 'all') params.push(`sub=${currentSubCategory}`);
        if (params.length > 0) url += '?' + params.join('&');

        const res = await fetch(url);
        const data = await res.json();
        const container = document.getElementById('packagesList');
        document.getElementById('currentFilterTitle').innerHTML = `<i class="fa-solid fa-cubes text-indigo-400"></i> ${currentCategoryName}`;
        document.getElementById('pkgListSubTitle').innerText = `包含 ${data.packages.length} 个知识资产包`;

        if (data.packages.length === 0) {
          container.innerHTML = `
            <div class="text-center py-12 px-4 text-gray-500 text-xs">
              <i class="fa-regular fa-folder-open text-2xl mb-2 text-gray-600 block"></i>
              当前分类下暂无资产包<br>
              <button onclick="toggleIngestPanel()" class="mt-3 text-indigo-400 hover:underline">立即录入第一篇资料</button>
            </div>
          `;
          if (!activePackageId) {
            document.getElementById('inspectorContent').innerHTML = `
              <div class="text-center py-32 text-gray-500">
                <h4 class="text-sm font-semibold text-gray-400">当前分类无资产包</h4>
                <p class="text-xs text-gray-500 mt-1">请选择其它分类或录入新知识源</p>
              </div>
            `;
          }
          return;
        }

        container.innerHTML = data.packages.map(p => `
          <div onclick="selectPackage('${p.id}')" 
            class="glass-card hover:border-indigo-500/60 transition p-3.5 rounded-xl cursor-pointer relative group ${activePackageId === p.id ? 'active-pkg-card' : ''}">
            <div class="flex justify-between items-start mb-1">
              <div class="pr-6">
                <div class="flex items-center gap-1.5 text-[10px] text-indigo-400 font-mono">
                  <span>${p.domain_icon || '📁'} ${p.domain_name || '通用'}</span>
                  <span>/</span>
                  <span class="text-gray-400">${p.sub_category_name || p.sub_category || '默认'}</span>
                </div>
                <h4 class="font-bold text-white text-xs mt-0.5 leading-snug">${p.name}</h4>
              </div>
              <span class="text-[10px] px-1.5 py-0.5 bg-indigo-950/70 text-indigo-300 rounded border border-indigo-800/50 shrink-0 font-mono">${p.item_count} 条</span>
            </div>
            <p class="text-[11px] text-gray-400 line-clamp-2 mb-2 leading-relaxed">${p.description}</p>
            <div class="flex items-center justify-between pt-1">
              <div class="flex flex-wrap gap-1">
                ${(p.tags || []).slice(0, 3).map(t => `<span class="text-[9px] bg-gray-900 text-gray-300 px-1.5 py-0.5 rounded border border-gray-800">${t}</span>`).join('')}
              </div>
              <button onclick="deletePackage(event, '${p.id}', '${p.name}')" class="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-rose-400 p-1 transition" title="彻底删除此资产包">
                <i class="fa-regular fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        `).join('');

        // 默认选中第一个
        const exists = data.packages.find(p => p.id === activePackageId);
        if (!exists && data.packages.length > 0) {
          selectPackage(data.packages[0].id);
        }
      } catch (e) {
        console.error('Failed to load packages:', e);
      }
    }

    // 3. 选中并检视单个资产包
    async function selectPackage(pkgId) {
      activePackageId = pkgId;
      document.querySelectorAll('#packagesList > div').forEach(el => {
        el.classList.remove('active-pkg-card');
      });
      loadPackages();

      const container = document.getElementById('inspectorContent');
      container.innerHTML = '<div class="text-center py-20 text-gray-400 text-xs"><i class="fa-solid fa-spinner animate-spin text-lg mb-2 block"></i> 正在加载资产包知识图谱与结构化特性矩阵...</div>';

      try {
        const res = await fetch(`/api/packages/${pkgId}`);
        const data = await res.json();
        const p = data.metadata;
        const matrix = p.knowledge_matrix || [];

        // 构建结构化对比矩阵
        let matrixHtml = '';
        if (matrix.length > 0) {
          matrixHtml = `
            <div class="mb-6">
              <div class="flex justify-between items-center mb-3">
                <h4 class="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <i class="fa-solid fa-microchip text-indigo-400"></i> 结构化特性与对比矩阵 (${matrix.length} 个核心方案/实体 · 智能去重增量融合)
                </h4>
              </div>
              <div class="space-y-4">
                ${matrix.map((m, idx) => `
                  <div class="bg-gray-900/90 border border-gray-800/90 p-4 rounded-xl space-y-3">
                    <div class="flex justify-between items-start border-b border-gray-800 pb-2.5">
                      <div class="flex items-center gap-2">
                        <span class="w-5 h-5 rounded-md bg-indigo-950 text-indigo-400 text-[10px] flex items-center justify-center font-bold border border-indigo-800/50">${idx + 1}</span>
                        <h5 class="text-xs font-bold text-white">${m.entity_name}</h5>
                        ${m.merged_sources_count > 1 ? `<span class="text-[9px] bg-purple-950 text-purple-300 px-1.5 py-0.5 rounded border border-purple-800 flex items-center gap-1"><i class="fa-solid fa-code-merge"></i> 融合 ${m.merged_sources_count} 篇资料</span>` : ''}
                      </div>
                      <span class="text-[10px] px-2 py-0.5 rounded font-medium ${m.local_deployable.includes('纯本地') ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}">
                        ${m.local_deployable}
                      </span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                      <div class="bg-black/30 p-2 rounded-lg border border-gray-800/60">
                        <span class="text-gray-400 block font-semibold mb-0.5"><i class="fa-solid fa-bullseye text-indigo-400 mr-1"></i> 核心功能与定位:</span>
                        <span class="text-gray-200">${m.core_function || '-'}</span>
                      </div>
                      <div class="bg-black/30 p-2 rounded-lg border border-gray-800/60">
                        <span class="text-gray-400 block font-semibold mb-0.5"><i class="fa-solid fa-memory text-yellow-400 mr-1"></i> 硬件配置要求:</span>
                        <span class="text-gray-200">${m.hardware_specs || '-'}</span>
                      </div>
                      <div class="bg-black/30 p-2 rounded-lg border border-gray-800/60">
                        <span class="text-gray-400 block font-semibold mb-0.5"><i class="fa-solid fa-cubes-stacked text-blue-400 mr-1"></i> 运行环境与依赖:</span>
                        <span class="text-gray-200">${m.environment || '-'}</span>
                      </div>
                      <div class="bg-black/30 p-2 rounded-lg border border-gray-800/60">
                        <span class="text-gray-400 block font-semibold mb-0.5"><i class="fa-solid fa-users text-emerald-400 mr-1"></i> 知识贡献来源:</span>
                        <span class="text-gray-200">${(m.sources_contributed || []).join(', ') || '-'}</span>
                      </div>
                    </div>

                    <!-- Advantages & Pitfalls -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] pt-1">
                      <div class="bg-emerald-950/20 border border-emerald-800/30 p-2.5 rounded-lg">
                        <span class="text-emerald-400 font-semibold block mb-1"><i class="fa-solid fa-thumbs-up mr-1"></i> 同类核心优势:</span>
                        <ul class="list-disc list-inside space-y-0.5 text-gray-300">
                          ${(m.competitive_advantages || []).slice(0, 5).map(a => `<li>${a}</li>`).join('')}
                        </ul>
                      </div>
                      <div class="bg-rose-950/20 border border-rose-800/30 p-2.5 rounded-lg">
                        <span class="text-rose-400 font-semibold block mb-1"><i class="fa-solid fa-triangle-exclamation mr-1"></i> 劣势、边界与避坑要点:</span>
                        <ul class="list-disc list-inside space-y-0.5 text-gray-300">
                          ${(m.limitations_and_pitfalls || []).slice(0, 5).map(pt => `<li>${pt}</li>`).join('')}
                        </ul>
                      </div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }

        container.innerHTML = `
          <!-- Breadcrumb & Actions Bar -->
          <div class="border-b border-gray-800/80 pb-4 mb-5">
            <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-3">
              <div>
                <div class="flex items-center gap-1.5 text-[11px] font-mono text-indigo-400 mb-1">
                  <span>${p.domain_icon || '📁'} ${p.domain_name}</span>
                  <span>></span>
                  <span>${p.sub_category_name || p.sub_category}</span>
                  <span>></span>
                  <span class="text-gray-400">#${p.id}</span>
                </div>
                <h2 class="text-lg font-bold text-white tracking-tight">${p.name}</h2>
                <p class="text-xs text-gray-400 mt-0.5">${p.description}</p>
              </div>
              <div class="flex flex-wrap gap-2 shrink-0">
                <button onclick="exportToAgent('${p.id}', 'cursor')" class="btn-agent hover:opacity-90 text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow" title="复制为 Cursor Rule 上下文">
                  <i class="fa-solid fa-code"></i> Cursor Rule (.mdc)
                </button>
                <button onclick="exportToAgent('${p.id}', 'codex')" class="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow" title="复制为 Codex System Prompt">
                  <i class="fa-solid fa-robot"></i> Codex
                </button>
                <button onclick="exportToAgent('${p.id}', 'hermes')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow" title="派发给 Hermes Agent">
                  <i class="fa-solid fa-brain"></i> Hermes
                </button>
                <button onclick="deletePackage(null, '${p.id}', '${p.name}')" class="bg-gray-800 hover:bg-rose-950 text-gray-400 hover:text-rose-400 px-2.5 py-1.5 rounded-lg text-xs font-medium border border-gray-700 transition" title="删除此资产包">
                  <i class="fa-regular fa-trash-can"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Structured Matrix Section -->
          ${matrixHtml}

          <!-- Video Keyframes Section (if any) -->
          ${data.keyframes.length > 0 ? `
            <div class="mb-6">
              <div class="flex justify-between items-center mb-2.5">
                <h4 class="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <i class="fa-solid fa-photo-film text-blue-400"></i> 视频关键帧画廊 (${data.keyframes.length} 张高清画面 · 零原片空间浪费)
                </h4>
                <span class="text-[10px] text-gray-500 font-normal">点击任意关键帧可查看高清大图</span>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-2.5">
                ${data.keyframes.map(k => `
                  <div onclick="viewImageLightbox('${k}')" class="group relative rounded-lg overflow-hidden border border-gray-800 bg-black cursor-pointer">
                    <img src="${k}" class="w-full h-28 object-cover group-hover:scale-105 transition duration-200" loading="lazy">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center text-white text-xs gap-1.5">
                      <i class="fa-solid fa-magnifying-glass-plus"></i> 查看高清大图
                    </div>
                    <div class="absolute bottom-0 inset-x-0 bg-black/80 text-[10px] text-gray-300 px-2 py-0.5 truncate font-mono">${k.split('/').pop()}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <!-- Sources List with 100% Offline Reader & Video Player -->
          <div class="mb-6">
            <h4 class="text-xs font-bold uppercase tracking-wider text-white mb-2.5 flex items-center gap-2">
              <i class="fa-solid fa-book-bookmark text-emerald-400"></i> 知识来源与本地脱机存档 (${(p.sources || []).length} 篇脱机归档)
            </h4>
            <div class="space-y-2">
              ${(p.sources || []).map(s => {
                const isVideo = isVideoSource(s);
                return `
                <div class="bg-gray-900/80 border border-gray-800 p-3 rounded-xl flex flex-col md:flex-row md:justify-between md:items-center gap-2 text-xs">
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-indigo-400 font-mono text-[10px]">[${s.type}]</span>
                      <span class="text-gray-200 font-bold text-xs">${s.title}</span>
                      ${s.incremental_merged ? `<span class="text-[9px] bg-purple-950 text-purple-300 px-1.5 py-0.2 rounded border border-purple-800/80 font-mono"><i class="fa-solid fa-code-merge"></i> 增量融合至: ${s.associated_entity || '核心矩阵'}</span>` : ''}
                    </div>
                    <div class="text-gray-500 text-[10px] mt-1 flex flex-wrap gap-3">
                      <span><i class="fa-solid fa-user-pen mr-1"></i> 作者: ${s.author || '未知'}</span>
                      <span><i class="fa-regular fa-clock mr-1"></i> 录入: ${s.ingested_at}</span>
                      <span class="text-emerald-500 font-mono"><i class="fa-solid fa-file-shield mr-1"></i> ${s.file}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    ${isVideo ? `
                      <button onclick="playVideo('${s.url}', '${encodeURIComponent(s.title)}')" class="px-2.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow transition">
                        <i class="fa-solid fa-circle-play"></i> 播放视频
                      </button>
                    ` : ''}
                    <button onclick="openLocalReader('${p.id}', '${s.file}', '${encodeURIComponent(s.title)}', '${s.url || ''}')" class="px-2.5 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 shadow transition">
                      <i class="fa-solid fa-book-open"></i> 本地脱机阅读
                    </button>
                    ${s.url ? `
                      <a href="${s.url}" target="_blank" class="px-2 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg text-xs flex items-center gap-1">
                        原网 <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                      </a>
                    ` : ''}
                    <button onclick="deleteSource('${p.id}', '${s.file}')" class="text-gray-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-gray-800 transition" title="删除此资料文件">
                      <i class="fa-regular fa-trash-can"></i>
                    </button>
                  </div>
                </div>
              `}).join('')}
            </div>
          </div>

          <!-- SUMMARY.md Preview -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-white mb-2 flex items-center gap-2">
              <i class="fa-solid fa-file-waveform text-purple-400"></i> 资产包聚合体系大纲 (SUMMARY.md 渲染预览)
            </h4>
            <div class="bg-gray-900/90 border border-gray-800 p-4 rounded-xl text-xs text-gray-300 max-h-80 overflow-y-auto leading-relaxed prose-clean">
              ${marked.parse(data.summary)}
            </div>
          </div>
        `;
      } catch (e) {
        console.error(e);
      }
    }

    // 4. 全局检索
    function handleSearch(val) {
      clearTimeout(searchDebounceTimer);
      const btnClear = document.getElementById('btnClearSearch');
      if (val.trim()) {
        btnClear.classList.remove('hidden');
      } else {
        btnClear.classList.add('hidden');
        clearSearch();
        return;
      }

      searchDebounceTimer = setTimeout(async () => {
        const query = val.trim();
        if (!query) return;

        const normalView = document.getElementById('normalHierarchyView');
        const searchView = document.getElementById('searchResultsView');
        const queryLabel = document.getElementById('searchQueryLabel');
        const content = document.getElementById('searchResultsContent');

        normalView.classList.add('hidden');
        searchView.classList.remove('hidden');
        queryLabel.innerText = `"${query}"`;
        content.innerHTML = '<div class="text-center py-20 text-gray-400 text-xs"><i class="fa-solid fa-spinner animate-spin text-lg mb-2 block"></i> 正在全库深度检索...</div>';

        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
          const data = await res.json();
          let html = '';

          // 匹配到的资产包
          if (data.packages && data.packages.length > 0) {
            html += `
              <div>
                <h4 class="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
                  <i class="fa-solid fa-cubes text-indigo-400"></i> 匹配的知识资产包 (${data.packages.length})
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  ${data.packages.map(p => `
                    <div onclick="jumpToPackage('${p.id}')" class="glass-card hover:border-indigo-500/60 p-3.5 rounded-xl cursor-pointer transition">
                      <div class="flex justify-between items-start">
                        <h5 class="text-xs font-bold text-white">${p.name}</h5>
                        <span class="text-[10px] bg-indigo-950 text-indigo-300 px-1.5 py-0.5 rounded font-mono">得分: ${p.score}</span>
                      </div>
                      <p class="text-[11px] text-gray-400 line-clamp-2 mt-1 mb-2">${p.description}</p>
                      <div class="flex flex-wrap gap-1">
                        ${(p.tags || []).map(t => `<span class="text-[9px] bg-gray-900 text-gray-400 px-1.5 py-0.5 rounded border border-gray-800">${t}</span>`).join('')}
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }

          // 匹配到的具体文档片段
          if (data.sources && data.sources.length > 0) {
            html += `
              <div>
                <h4 class="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
                  <i class="fa-solid fa-file-lines text-emerald-400"></i> 匹配的脱机文献与正文片段 (${data.sources.length})
                </h4>
                <div class="space-y-2">
                  ${data.sources.map(s => `
                    <div class="bg-gray-900/90 border border-gray-800 p-3 rounded-xl flex justify-between items-center text-xs">
                      <div class="flex-1 pr-4">
                        <div class="flex items-center gap-2">
                          <span class="text-[10px] text-indigo-400 font-mono">[${s.package_name}]</span>
                          <span class="text-white font-medium">${s.filename}</span>
                        </div>
                        <p class="text-[11px] text-gray-400 mt-1 font-mono bg-black/40 px-2 py-1 rounded border border-gray-800/80">${s.snippet}</p>
                      </div>
                      <button onclick="openLocalReader('${s.package_id}', 'sources/${s.filename}', '${encodeURIComponent(s.filename)}')" class="px-2.5 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 shrink-0">
                        <i class="fa-solid fa-book-open"></i> 本地脱机阅读
                      </button>
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }

          if (!html) {
            html = '<div class="text-center py-20 text-gray-500 text-xs">未找到包含该关键词的内容</div>';
          }

          content.innerHTML = html;
        } catch (e) {
          content.innerHTML = `<div class="text-rose-400 text-xs">检索出错: ${e.message}</div>`;
        }
      }, 300);
    }

    function clearSearch() {
      document.getElementById('globalSearchInput').value = '';
      document.getElementById('btnClearSearch').classList.add('hidden');
      document.getElementById('searchResultsView').classList.add('hidden');
      document.getElementById('normalHierarchyView').classList.remove('hidden');
    }

    function jumpToPackage(pkgId) {
      clearSearch();
      selectCategory('all', 'all', '全部知识资产包');
      selectPackage(pkgId);
    }

    // 5. 极速采集与智能分类交互
    let pendingClfData = null;

    function openClassificationModal(data) {
      pendingClfData = data;
      document.getElementById('clfTitle').innerText = data.item_preview.title;
      document.getElementById('clfSourceType').innerText = data.item_preview.source_type || 'web_page';
      document.getElementById('clfSummary').innerText = data.item_preview.summary || '(暂无内容摘要)';

      if (data.suggested_category) {
        document.getElementById('clfNewDomainName').value = data.suggested_category.domain_name || '综合研究领域';
        document.getElementById('clfNewSubName').value = data.suggested_category.sub_name || '实战方法专题';
      } else {
        document.getElementById('clfNewDomainName').value = '新兴前沿专题';
        document.getElementById('clfNewSubName').value = '核心实践';
      }

      // 渲染现有分类下拉选单
      const selectElem = document.getElementById('clfSelectExisting');
      selectElem.innerHTML = '';
      if (data.existing_taxonomy && data.existing_taxonomy.length > 0) {
        data.existing_taxonomy.forEach(d => {
          const optGroup = document.createElement('optgroup');
          optGroup.label = `${d.domain_icon} ${d.domain_name}`;
          (d.sub_categories || []).forEach(s => {
            const opt = document.createElement('option');
            opt.value = `${d.domain_key}::${s.id}`;
            opt.innerText = `${s.icon || '📌'} ${s.name}`;
            optGroup.appendChild(opt);
          });
          selectElem.appendChild(optGroup);
        });
      }

      document.getElementById('classificationModal').classList.remove('hidden');
    }

    function closeClassificationModal() {
      document.getElementById('classificationModal').classList.add('hidden');
      pendingClfData = null;
    }

    async function confirmCreateNewCategory() {
      if (!pendingClfData) return;
      const newDomainName = document.getElementById('clfNewDomainName').value.trim();
      const newSubName = document.getElementById('clfNewSubName').value.trim();
      if (!newDomainName || !newSubName) {
        showToast('请输入完整的一级领域与二级子方向名称', false);
        return;
      }

      const btn = document.getElementById('btnAllowCreateNew');
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> 创建新类别并沉淀中...';

      try {
        const res = await fetch('/api/ingest', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url: pendingClfData.item_preview.url,
            allow_create_new: true,
            new_domain_name: newDomainName,
            new_sub_name: newSubName,
            force_confirm: true
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`成功创建新分类「${newDomainName} > ${newSubName}」并完成归包！`);
          closeClassificationModal();
          document.getElementById('inputUrl').value = '';
          const statusDiv = document.getElementById('ingestStatus');
          statusDiv.className = 'mt-2 text-xs text-emerald-400 block';
          statusDiv.innerText = `成功以新类别入库《${data.title}》！归属 [📁 ${data.domain_name} > 📌 ${data.sub_category_name}]`;
          await loadTaxonomy();
          await loadPackages();
          selectPackage(data.package_id);
        } else {
          throw new Error(data.detail || '创建新类别录入失败');
        }
      } catch (e) {
        showToast('录入异常: ' + e.message, false);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-folder-plus"></i> 允许并以新类别创建资产包入库';
      }
    }

    async function confirmSelectExistingCategory() {
      if (!pendingClfData) return;
      const selectVal = document.getElementById('clfSelectExisting').value;
      if (!selectVal) {
        showToast('请选择一个现有类别', false);
        return;
      }
      const [domKey, subKey] = selectVal.split('::');

      const btn = document.getElementById('btnSelectExisting');
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> 归入现有分类中...';

      try {
        const res = await fetch('/api/ingest', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url: pendingClfData.item_preview.url,
            domain: domKey,
            sub_category: subKey,
            force_confirm: true
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`成功归入现有类别 [${data.domain_name} > ${data.sub_category_name}]！`);
          closeClassificationModal();
          document.getElementById('inputUrl').value = '';
          const statusDiv = document.getElementById('ingestStatus');
          statusDiv.className = 'mt-2 text-xs text-emerald-400 block';
          statusDiv.innerText = `成功录入《${data.title}》！归属 [${data.domain_icon || '📁'} ${data.domain_name} > ${data.sub_category_name}]`;
          await loadTaxonomy();
          await loadPackages();
          selectPackage(data.package_id);
        } else {
          throw new Error(data.detail || '归入现有类别失败');
        }
      } catch (e) {
        showToast('归入异常: ' + e.message, false);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> 归入所选现有类别';
      }
    }

    async function handleIngest() {
      const urlInput = document.getElementById('inputUrl');
      const statusDiv = document.getElementById('ingestStatus');
      const btn = document.getElementById('btnIngest');
      const url = urlInput.value.trim();

      if (!url) {
        showToast('请输入采集链接或粘贴内容', false);
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> 采集与增量融合中...';
      statusDiv.className = 'mt-2 text-xs text-indigo-400 block';
      statusDiv.innerText = '正在智能路由输入源、清洗正文、提取关键帧与硬件/环境特性...';

      try {
        const domain = document.getElementById('selectDomain').value;
        const subCategory = document.getElementById('selectSubCategory').value;
        const res = await fetch('/api/ingest', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url, 
            domain: domain || null,
            sub_category: subCategory || null
          })
        });
        const data = await res.json();

        // 若无法精准匹配现有分类表，触发用户交互决策弹窗
        if (data.needs_confirmation) {
          statusDiv.className = 'mt-2 text-xs text-yellow-400 block';
          statusDiv.innerText = '⚠️ 该内容未匹配现有分类表，请在弹窗中确认是否创建新类别或指定现有类别...';
          openClassificationModal(data);
          return;
        }

        if (data.success) {
          statusDiv.className = 'mt-2 text-xs text-emerald-400 block';
          if (data.decomposed) {
            statusDiv.innerText = `成功原子化拆解《${data.title}》为 ${data.sub_items_count} 个独立项目实体，并已按领域多路定向归纳至对应资产包！Git: ${data.commit || 'ok'}`;
            showToast(`成功拆解 ${data.sub_items_count} 个技术项目并精准归包！`);
          } else {
            statusDiv.innerText = `成功录入《${data.title}》！归入 [${data.domain_icon || '📁'} ${data.domain_name} > ${data.sub_category_name || '专题'}]，Git: ${data.commit || 'ok'}`;
            showToast(`成功沉淀《${data.title.slice(0, 20)}...》至资产包！`);
          }
          urlInput.value = '';
          await loadTaxonomy();
          await loadPackages();
          selectPackage(data.package_id);
        } else {
          throw new Error(data.detail || '录入失败');
        }
      } catch (e) {
        statusDiv.className = 'mt-2 text-xs text-rose-400 block';
        statusDiv.innerText = '录入异常: ' + e.message;
        showToast('采集失败: ' + e.message, false);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-download"></i> 抓取并增量归包';
      }
    }

    // 6. 删除资产包
    async function deletePackage(event, pkgId, pkgName) {
      if (event) event.stopPropagation();
      if (!confirm(`确定要彻底删除知识资产包「${pkgName}」及其全部离线文件吗？此操作无法撤销！`)) {
        return;
      }

      try {
        const res = await fetch(`/api/packages/${pkgId}`, {method: 'DELETE'});
        const data = await res.json();
        if (data.success) {
          showToast(`已彻底删除资产包: ${pkgName}`);
          if (activePackageId === pkgId) activePackageId = null;
          await loadTaxonomy();
          await loadPackages();
        } else {
          showToast('删除失败: ' + (data.detail || '未知错误'), false);
        }
      } catch (e) {
        showToast('删除异常: ' + e.message, false);
      }
    }

    // 7. 删除单篇源资料并重新增量合成
    async function deleteSource(pkgId, sourceFile) {
      if (!confirm(`确定要从此资产包中删除资料「${sourceFile}」吗？系统将自动重新合成对比矩阵！`)) {
        return;
      }

      try {
        const res = await fetch(`/api/packages/${pkgId}/sources?file=${encodeURIComponent(sourceFile)}`, {method: 'DELETE'});
        const data = await res.json();
        if (data.success) {
          showToast('资料已删除，知识图谱已重新增量合成！');
          selectPackage(pkgId);
          loadTaxonomy();
        } else {
          showToast('删除失败: ' + (data.detail || '未知错误'), false);
        }
      } catch (e) {
        showToast('删除异常: ' + e.message, false);
      }
    }

    // 判断是否为视频类资源
    function isVideoSource(s) {
      if (!s || !s.url) return false;
      const u = s.url.toLowerCase();
      const t = (s.type || '').toLowerCase();
      return t.includes('video') || t.includes('channel') || u.includes('bilibili.com') || u.includes('b23.tv') || u.includes('youtube.com') || u.includes('youtu.be') || u.includes('sph') || u.includes('weixin.qq.com/video');
    }

    // 播放视频 (免流内嵌播放器)
    function playVideo(url, encodedTitle) {
      const modal = document.getElementById('videoModal');
      const titleEl = document.getElementById('videoModalTitle');
      const playerContainer = document.getElementById('videoPlayerContainer');
      const title = decodeURIComponent(encodedTitle);
      titleEl.innerText = title;
      modal.classList.remove('hidden');

      // B站专属内嵌免流播放器 (零体积下载原片)
      if (url.includes('bilibili.com') || url.includes('b23.tv')) {
        const match = url.match(/(BV[a-zA-Z0-9]+)/i);
        const bvid = match ? match[1] : '';
        if (bvid) {
          playerContainer.innerHTML = `
            <div class="w-full h-full flex flex-col items-center">
              <div class="w-full aspect-video bg-black rounded-xl overflow-hidden border border-gray-800 shadow-2xl">
                <iframe src="//player.bilibili.com/player.html?bvid=${bvid}&page=1&high_quality=1&danmaku=0&autoplay=1" 
                  allowfullscreen="allowfullscreen" width="100%" height="100%" scrolling="no" frameborder="0" 
                  sandbox="allow-top-navigation allow-same-origin allow-forms allow-scripts"></iframe>
              </div>
              <div class="w-full flex justify-between items-center text-xs text-gray-400 mt-3 px-1">
                <span class="flex items-center gap-1.5"><i class="fa-brands fa-bilibili text-pink-400"></i> Bilibili 官方高清免流播放器 (零本地大视频占用)</span>
                <a href="${url}" target="_blank" class="hover:text-white text-indigo-400 flex items-center gap-1">在 B站 原站打开 <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i></a>
              </div>
            </div>
          `;
          return;
        }
      }

      // YouTube 播放器
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        let ytid = '';
        const m = url.match(/(?:v=|\/embed\/|\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
        if (m) ytid = m[1];
        if (ytid) {
          playerContainer.innerHTML = `
            <div class="w-full h-full flex flex-col items-center">
              <div class="w-full aspect-video bg-black rounded-xl overflow-hidden border border-gray-800 shadow-2xl">
                <iframe src="https://www.youtube.com/embed/${ytid}?autoplay=1" 
                  allowfullscreen="allowfullscreen" width="100%" height="100%" frameborder="0"></iframe>
              </div>
              <div class="w-full flex justify-between items-center text-xs text-gray-400 mt-3 px-1">
                <span class="flex items-center gap-1.5"><i class="fa-brands fa-youtube text-red-500"></i> YouTube 高清播放器</span>
                <a href="${url}" target="_blank" class="hover:text-white text-indigo-400 flex items-center gap-1">在 YouTube 原站打开 <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i></a>
              </div>
            </div>
          `;
          return;
        }
      }

      // 微信视频号或通用视频页面
      playerContainer.innerHTML = `
        <div class="p-8 text-center bg-gray-950/80 rounded-2xl border border-gray-800 max-w-lg w-full">
          <div class="w-16 h-16 rounded-full bg-rose-950 text-rose-400 border border-rose-800/60 flex items-center justify-center mx-auto mb-4 text-2xl shadow-lg">
            <i class="fa-solid fa-play"></i>
          </div>
          <h4 class="text-sm font-bold text-white mb-2">${title}</h4>
          <p class="text-xs text-gray-400 mb-6 leading-relaxed">该视频来自微信视频号或受保护视频流平台。点击下方按钮即可一键跳转至原视频页面进行全屏、原画质流畅播放：</p>
          <a href="${url}" target="_blank" class="btn-gradient px-6 py-2.5 rounded-xl text-xs font-bold text-white inline-flex items-center gap-2 shadow-lg hover:opacity-95 transition">
            <i class="fa-solid fa-arrow-up-right-from-square"></i> 打开原平台播放原画质完整视频
          </a>
        </div>
      `;
    }

    function closeVideoModal() {
      document.getElementById('videoModal').classList.add('hidden');
      document.getElementById('videoPlayerContainer').innerHTML = '';
    }

    // 关键帧放大检视
    function viewImageLightbox(src) {
      const modal = document.getElementById('lightboxModal');
      const img = document.getElementById('lightboxImg');
      const caption = document.getElementById('lightboxCaption');
      img.src = src;
      caption.innerText = src.split('/').pop();
      modal.classList.remove('hidden');
    }

    function closeLightboxModal() {
      document.getElementById('lightboxModal').classList.add('hidden');
    }

    // 8. 本地脱机阅读器
    async function openLocalReader(pkgId, file, encodedTitle, originalUrl = '') {
      const modal = document.getElementById('readerModal');
      const modalTitle = document.getElementById('modalTitle');
      const modalPath = document.getElementById('modalPath');
      const modalBody = document.getElementById('modalBody');

      modalTitle.innerText = decodeURIComponent(encodedTitle);
      modalPath.innerText = `${pkgId}/${file}`;
      modalBody.innerHTML = '<div class="text-center py-20 text-gray-400"><i class="fa-solid fa-spinner animate-spin text-2xl mb-2 block"></i> 正在从本地磁盘读取 100% 脱机存档文件...</div>';
      modal.classList.remove('hidden');

      try {
        const res = await fetch(`/api/source_content/${pkgId}?file=${encodeURIComponent(file)}`);
        const data = await res.json();
        let content = data.content;

        let topVideoHtml = '';
        if (originalUrl && isVideoSource({url: originalUrl})) {
          topVideoHtml = `
            <div class="bg-rose-950/40 border border-rose-800/60 p-3 rounded-xl flex justify-between items-center mb-4">
              <span class="text-xs text-rose-300 flex items-center gap-2">
                <i class="fa-solid fa-circle-play text-sm"></i> 关联在线视频源，支持原画质流畅播放
              </span>
              <button onclick="playVideo('${originalUrl}', '${encodedTitle}')" class="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow">
                <i class="fa-solid fa-play"></i> 立即内嵌播放视频
              </button>
            </div>
          `;
        }

        let fmHtml = '';
        if (content.startsWith('---')) {
          const parts = content.split('---', 3);
          if (parts.length >= 3) {
            content = parts[2];
            fmHtml = `
              <div class="bg-black/50 p-3 rounded-xl border border-gray-800 mb-4 font-mono text-[11px]">
                <span class="text-indigo-400 font-bold block mb-1"><i class="fa-solid fa-fingerprint mr-1"></i> 本地脱机归档元数据 (YAML Frontmatter):</span>
                <pre class="text-emerald-400 whitespace-pre-wrap">${parts[1].trim()}</pre>
              </div>
            `;
          }
        }

        // 统一本地离线配图路径转换
        content = content.replace(/\(assets\//g, `(/packages/${pkgId}/assets/`);
        content = content.replace(/\(keyframes\//g, `(/packages/${pkgId}/keyframes/`);

        let parsedHtml = marked.parse(content);
        // 为所有图片增加防盗链与懒加载属性
        parsedHtml = parsedHtml.replace(/<img /g, '<img referrerpolicy="no-referrer" loading="lazy" ');

        modalBody.innerHTML = topVideoHtml + fmHtml + `<div class="prose-clean">${parsedHtml}</div>`;
      } catch (e) {
        modalBody.innerHTML = `<div class="text-rose-400 p-4">加载本地脱机文件失败: ${e.message}</div>`;
      }
    }

    function closeReaderModal() {
      document.getElementById('readerModal').classList.add('hidden');
    }

    // 9. 一键派发给 Agent
    async function exportToAgent(pkgId, target) {
      try {
        const res = await fetch(`/api/export/${pkgId}?target=${target}`);
        const data = await res.json();
        await fetch('/api/copy', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: data.content})
        });
        showToast(`已生成并复制专用于 ${target.toUpperCase()} 的知识上下文！直接在项目中粘贴即可。`);
      } catch (e) {
        showToast('导出失败: ' + e, false);
      }
    }

    // 10. 读取剪贴板
    async function readFromClip() {
      try {
        const res = await fetch('/api/clipboard');
        const data = await res.json();
        if (data.text) {
          document.getElementById('inputUrl').value = data.text;
          showToast('已从 macOS 剪贴板自动填入');
        } else {
          showToast('剪贴板中无内容', false);
        }
      } catch (e) {
        console.error(e);
      }
    }

    // 快捷键支持
    window.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        document.getElementById('globalSearchInput').focus();
      }
      if (e.key === 'Escape') {
        closeReaderModal();
        closeVideoModal();
        closeLightboxModal();
      }
    });

    window.onload = async () => {
      await loadTaxonomy();
      await loadPackages();
    };
  </script>
</body>
</html>
"""
