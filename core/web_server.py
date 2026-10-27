"""
Hermes Knowledge Base Web Server & API
提供本地可视化操作台：一键采集、多渠道知识库浏览、关键帧视觉预览、一键导出给 Cursor / Codex / Hermes
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import PACKAGES_DIR
from core.agent_exporter import AgentExporter
from core.git_manager import GitManager
from core.package_manager import KnowledgePackageManager
from crawlers.dispatcher import CrawlerDispatcher

logger = logging.getLogger("hermes.web")

app = FastAPI(title="Hermes Knowledge Base Assistant", version="1.0.0")

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

class CopyRequest(BaseModel):
    text: str

@app.get("/api/packages")
def list_packages():
    return {"packages": pm.list_packages()}

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
        item = dispatcher.dispatch(req.url)
        pkg_id, source_path = pm.ingest_item(item, preferred_package=req.package)
        
        # Git 自动提交
        commit_hash = git_mgr.commit(f"feat(kb): ingest [{item.source_type}] {item.title[:40]} into package '{pkg_id}'")

        return {
            "success": True,
            "title": item.title,
            "source_type": item.source_type,
            "package_id": pkg_id,
            "source_file": source_path.name,
            "keyframes_count": len(item.keyframes),
            "snippets_count": len(item.code_snippets),
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

@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTML_DASHBOARD

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hermes 知识资产中心 & 知识库创建助手</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    .glass-card { background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(8px); border: 1px solid #30363d; }
    .btn-gradient { background: linear-gradient(135deg, #238636 0%, #2ea043 100%); }
    .btn-agent { background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%); }
  </style>
</head>
<body class="min-h-screen">
  <div class="max-w-7xl mx-auto px-4 py-8">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8 border-b border-gray-800 pb-5">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-white font-bold text-xl shadow-lg">
          H
        </div>
        <div>
          <h1 class="text-2xl font-bold text-white tracking-tight">Hermes 知识资产中心</h1>
          <p class="text-xs text-gray-400">微信公众号 / 视频号 / 网页 / B站视频 / 图片多模态资产打包与 Agent 协同中枢</p>
        </div>
      </div>
      <div class="flex items-center space-x-3 text-sm">
        <span class="px-3 py-1 bg-gray-800 rounded-full text-emerald-400 border border-emerald-800/40 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Git 资产库已同步
        </span>
      </div>
    </header>

    <!-- Quick Ingestion Box -->
    <div class="glass-card rounded-2xl p-6 mb-8 shadow-xl">
      <h2 class="text-lg font-semibold text-white mb-3 flex items-center gap-2">
        <i class="fa-solid fa-plus-circle text-emerald-400"></i> 一键录入新知识源
      </h2>
      <div class="flex flex-col md:flex-row gap-3">
        <input id="inputUrl" type="text" placeholder="粘贴微信公众号文章链接、微信视频号分享、B站视频地址、技术网页 URL 或图片路径..." 
          class="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm">
        <button onclick="readFromClip()" class="px-4 py-3 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-xl text-sm font-medium border border-gray-700 transition flex items-center gap-2 justify-center">
          <i class="fa-regular fa-clipboard"></i> 粘贴剪贴板
        </button>
        <button id="btnIngest" onclick="handleIngest()" class="btn-gradient hover:opacity-95 text-white px-6 py-3 rounded-xl text-sm font-semibold transition flex items-center gap-2 justify-center shadow-lg">
          <i class="fa-solid fa-bolt"></i> 采集并归包
        </button>
      </div>
      <div id="ingestStatus" class="mt-3 text-xs hidden"></div>
      <div class="mt-3 text-xs text-gray-500 flex flex-wrap gap-4">
        <span><i class="fa-brands fa-weixin text-green-500 mr-1"></i> 支持微信公众号正文与代码解析</span>
        <span><i class="fa-solid fa-video text-blue-400 mr-1"></i> B站视频：无损抽取关键帧截图，免存大体积原视频</span>
        <span><i class="fa-solid fa-layer-group text-purple-400 mr-1"></i> 自动智能聚类至同类知识资产包</span>
      </div>
    </div>

    <!-- Main Workspace -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Left: Packages List -->
      <div class="lg:col-span-4 space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-base font-semibold text-white flex items-center gap-2">
            <i class="fa-solid fa-cubes text-indigo-400"></i> 知识资产包 (<span id="pkgCount">0</span>)
          </h3>
          <button onclick="loadPackages()" class="text-xs text-gray-400 hover:text-white"><i class="fa-solid fa-arrows-rotate"></i> 刷新</button>
        </div>
        <div id="packagesContainer" class="space-y-3">
          <div class="p-8 text-center text-gray-500 text-sm">加载资产包中...</div>
        </div>
      </div>

      <!-- Right: Package Viewer & Agent Export Panel -->
      <div class="lg:col-span-8">
        <div id="detailsCard" class="glass-card rounded-2xl p-6 min-h-[500px]">
          <div class="text-center py-20 text-gray-500">
            <i class="fa-solid fa-arrow-left text-3xl mb-3 text-gray-600 block"></i>
            请在左侧选择一个知识资产包，查看知识脉络、关键帧画面及向 Cursor / Codex / Hermes 一键派发
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let activePackageId = null;

    async function loadPackages() {
      try {
        const res = await fetch('/api/packages');
        const data = await res.json();
        const container = document.getElementById('packagesContainer');
        document.getElementById('pkgCount').innerText = data.packages.length;
        if (data.packages.length === 0) {
          container.innerHTML = '<div class="glass-card p-6 rounded-xl text-center text-gray-400 text-sm">暂无资产包，请在上方录入第一条知识！</div>';
          return;
        }
        container.innerHTML = data.packages.map(p => `
          <div onclick="selectPackage('${p.id}')" class="glass-card hover:border-indigo-500/60 transition p-4 rounded-xl cursor-pointer ${activePackageId === p.id ? 'border-indigo-500 bg-gray-800/90' : ''}">
            <div class="flex justify-between items-start mb-1">
              <h4 class="font-semibold text-white text-sm">${p.name}</h4>
              <span class="text-xs px-2 py-0.5 bg-indigo-950/70 text-indigo-300 rounded border border-indigo-800/50">${p.item_count} 条</span>
            </div>
            <p class="text-xs text-gray-400 line-clamp-2 mb-2">${p.description}</p>
            <div class="flex flex-wrap gap-1">
              ${(p.tags || []).slice(0, 4).map(t => `<span class="text-[10px] bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded">${t}</span>`).join('')}
            </div>
          </div>
        `).join('');

        if (!activePackageId && data.packages.length > 0) {
          selectPackage(data.packages[0].id);
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function selectPackage(pkgId) {
      activePackageId = pkgId;
      loadPackages();
      const container = document.getElementById('detailsCard');
      container.innerHTML = '<div class="text-center py-20 text-gray-400">加载资产包详情与知识图谱...</div>';
      try {
        const res = await fetch(`/api/packages/${pkgId}`);
        const data = await res.json();
        const p = data.metadata;

        container.innerHTML = `
          <div class="border-b border-gray-800 pb-4 mb-6">
            <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
              <div>
                <span class="text-xs font-mono text-indigo-400"># PACKAGE: ${p.id}</span>
                <h2 class="text-xl font-bold text-white mt-1">${p.name}</h2>
                <p class="text-xs text-gray-400 mt-1">${p.description}</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button onclick="exportToAgent('${p.id}', 'cursor')" class="btn-agent hover:opacity-90 text-white px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow">
                  <i class="fa-solid fa-code"></i> 复制为 Cursor Rule
                </button>
                <button onclick="exportToAgent('${p.id}', 'codex')" class="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow">
                  <i class="fa-solid fa-robot"></i> 复制为 Codex Prompt
                </button>
                <button onclick="exportToAgent('${p.id}', 'hermes')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow">
                  <i class="fa-solid fa-brain"></i> 派发给 Hermes Agent
                </button>
              </div>
            </div>
          </div>

          <!-- Video Keyframes Section (if any) -->
          ${data.keyframes.length > 0 ? `
            <div class="mb-6">
              <h4 class="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <i class="fa-solid fa-photo-film text-blue-400"></i> 视频关键帧画廊 (${data.keyframes.length} 张高清画面，零原视频空间占用)
              </h4>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                ${data.keyframes.map(k => `
                  <div class="group relative rounded-lg overflow-hidden border border-gray-800 bg-black">
                    <img src="${k}" class="w-full h-32 object-cover group-hover:scale-105 transition duration-200">
                    <div class="absolute bottom-0 inset-x-0 bg-black/70 text-[10px] text-gray-300 px-2 py-1 truncate">${k.split('/').pop()}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <!-- Sources Accordion -->
          <div class="mb-6">
            <h4 class="text-sm font-semibold text-white mb-2 flex items-center gap-2">
              <i class="fa-solid fa-book-bookmark text-emerald-400"></i> 收录知识源与拆分明细 (${(p.sources || []).length} 条)
            </h4>
            <div class="space-y-2">
              ${(p.sources || []).map(s => `
                <div class="bg-gray-900/80 border border-gray-800 p-3 rounded-lg flex justify-between items-center text-xs">
                  <div>
                    <span class="text-indigo-400 font-semibold mr-1">[${s.type}]</span>
                    <span class="text-gray-200 font-medium">${s.title}</span>
                    <div class="text-gray-500 text-[11px] mt-0.5">作者: ${s.author || '未知'} | 录入: ${s.ingested_at}</div>
                  </div>
                  <a href="${s.url}" target="_blank" class="text-indigo-400 hover:underline text-[11px] flex items-center gap-1">
                    原链接 <i class="fa-solid fa-arrow-up-right-from-square"></i>
                  </a>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Knowledge Synthesis Markdown -->
          <div>
            <h4 class="text-sm font-semibold text-white mb-2 flex items-center gap-2">
              <i class="fa-solid fa-file-waveform text-purple-400"></i> 知识资产包沉淀大纲 (SUMMARY.md)
            </h4>
            <pre class="bg-gray-900/90 border border-gray-800 p-4 rounded-xl text-xs text-gray-300 font-mono whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">${data.summary}</pre>
          </div>
        `;
      } catch (e) {
        console.error(e);
      }
    }

    async function exportToAgent(pkgId, target) {
      try {
        const res = await fetch(`/api/export/${pkgId}?target=${target}`);
        const data = await res.json();
        await fetch('/api/copy', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: data.content})
        });
        alert(`已成功生成并复制专用于 ${target.toUpperCase()} 的知识参考上下文！直接在 ${target} 聊天框或项目中粘贴即可。`);
      } catch (e) {
        alert('导出失败: ' + e);
      }
    }

    async function readFromClip() {
      try {
        const res = await fetch('/api/clipboard');
        const data = await res.json();
        if (data.text) {
          document.getElementById('inputUrl').value = data.text;
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function handleIngest() {
      const urlInput = document.getElementById('inputUrl');
      const statusDiv = document.getElementById('ingestStatus');
      const btn = document.getElementById('btnIngest');
      const url = urlInput.value.trim();

      if (!url) {
        alert('请输入或粘贴链接内容');
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> 正在爬取与沉淀资产...';
      statusDiv.className = 'mt-3 text-xs text-indigo-400 block';
      statusDiv.innerText = '正在智能识别输入源、抓取内容并提取关键帧与代码片段...';

      try {
        const res = await fetch('/api/ingest', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({url})
        });
        const data = await res.json();
        if (data.success) {
          statusDiv.className = 'mt-3 text-xs text-emerald-400 block';
          statusDiv.innerText = `成功录入《${data.title}》！已归类至资产包 [${data.package_id}]，Git 提交: ${data.commit || 'ok'}`;
          urlInput.value = '';
          await loadPackages();
          selectPackage(data.package_id);
        } else {
          throw new Error(data.detail || '录入失败');
        }
      } catch (e) {
        statusDiv.className = 'mt-3 text-xs text-rose-400 block';
        statusDiv.innerText = '录入异常: ' + e.message;
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> 采集并归包';
      }
    }

    window.onload = loadPackages;
  </script>
</body>
</html>
"""
