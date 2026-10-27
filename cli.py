"""
Hermes Knowledge Base Command Line Interface (CLI)
命令行交互终端：知识极速采集、资产包检索、一键向 Cursor / Codex / Hermes 派发
"""
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

# 将项目根目录置入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import PACKAGES_DIR
from core.agent_exporter import AgentExporter
from core.git_manager import GitManager
from core.package_manager import KnowledgePackageManager
from crawlers.dispatcher import CrawlerDispatcher

app = typer.Typer(
    name="hermes-kb",
    help="⚡ Hermes 知识库创建助手：多模态采集（微信/视频号/B站/网页/图片），结构化资产包拆分与多 Agent 参考派发",
    add_completion=False
)
console = Console()

pm = KnowledgePackageManager()
exporter = AgentExporter(pm)
git_mgr = GitManager()
dispatcher = CrawlerDispatcher()

@app.command("ingest")
def ingest_cmd(
    target: str = typer.Argument(..., help="待采集目标：微信公众号URL、视频号分享文本/链接、B站视频URL、通用网页URL或本地图片路径"),
    package: Optional[str] = typer.Option(None, "--package", "-p", help="指定归属的知识资产包ID (如未指定将自动智能聚类)")
):
    """
    📥 极速采集并归档至知识资产包
    """
    console.print(f"[bold cyan]🔍 正在解析输入目标:[/bold cyan] {target}")
    with console.status("[bold green]正在抓取数据、清洗正文并提取关键帧与代码片段...", spinner="dots"):
        try:
            item = dispatcher.dispatch(target)
            pkg_id, source_path = pm.ingest_item(item, preferred_package=package)
            
            # Git 自动跟踪与版本提交
            commit_msg = f"feat(kb): ingest [{item.source_type}] {item.title[:40]} into '{pkg_id}'"
            commit_hash = git_mgr.commit(commit_msg)
        except Exception as e:
            console.print(f"[bold red]❌ 采集入库失败:[/bold red] {e}")
            raise typer.Exit(code=1)

    # 成果报告卡片
    summary_text = f"""
**标题**: {item.title}
**数据类型**: `{item.source_type}` | **作者**: {item.author or '未知'}
**归属资产包**: `[bold green]{pkg_id}[/bold green]`
**提取成果**:
- 关键帧截图: [bold yellow]{len(item.keyframes)}[/bold yellow] 张 (零原视频存储)
- 代码片段: [bold yellow]{len(item.code_snippets)}[/bold yellow] 段
- 保存文件: `{source_path.relative_to(PACKAGES_DIR)}`
- Git 版本提交: `{commit_hash or '已同步'}`
    """
    console.print(Panel(Markdown(summary_text.strip()), title="🎉 知识资产沉淀成功", border_style="green", box=box.ROUNDED))
    console.print(f"[dim]提示: 可运行 [bold cyan]hermes-kb export {pkg_id} --target cursor --copy[/bold cyan] 一键向 Cursor 派发！[/dim]")

@app.command("ingest-clip")
def ingest_clip_cmd(
    package: Optional[str] = typer.Option(None, "--package", "-p", help="指定归属的知识资产包ID")
):
    """
    📋 从系统剪贴板读取 URL 或文本直接一键录入 (Mac 上刷微信/B站时 Cmd+C 后一键录入)
    """
    clip_text = exporter.read_from_clipboard()
    if not clip_text:
        console.print("[bold yellow]⚠️ 当前剪贴板为空，请先复制微信公众号文章链接、B站链接或网页地址。[/bold yellow]")
        return
    console.print(f"[bold cyan]📋 识别到剪贴板内容:[/bold cyan] {clip_text[:80]}...")
    ingest_cmd(clip_text, package)

@app.command("list")
def list_cmd():
    """
    📚 查看所有知识资产包清单
    """
    packages = pm.list_packages()
    if not packages:
        console.print("[yellow]当前暂无知识资产包。使用 [bold cyan]hermes-kb ingest <url>[/bold cyan] 开始构建！[/yellow]")
        return

    table = Table(title="🗂️ Hermes 知识资产包全景 (Knowledge Asset Packages)", box=box.ROUNDED)
    table.add_column("资产包 ID", style="cyan", no_wrap=True)
    table.add_column("名称", style="bold white")
    table.add_column("领域", style="magenta")
    table.add_column("收录篇数", justify="right", style="green")
    table.add_column("核心标签", style="yellow")
    table.add_column("最后更新", style="dim")

    for p in packages:
        tags_str = ", ".join(p.get("tags", [])[:4])
        table.add_row(
            p.get("id"),
            p.get("name"),
            p.get("domain", "general"),
            str(p.get("item_count", 0)),
            tags_str,
            p.get("updated_at", "")[:16]
        )

    console.print(table)

@app.command("show")
def show_cmd(
    package_id: str = typer.Argument(..., help="资产包 ID")
):
    """
    🔍 深度查看资产包详情、关键帧画廊与收录明细
    """
    pkg = pm.get_package(package_id)
    if not pkg:
        console.print(f"[bold red]❌ 找不到资产包:[/bold red] {package_id}")
        return

    console.print(f"\n[bold green]📦 资产包:[/bold green] [bold white]{pkg.get('name')}[/bold white] ({package_id})")
    console.print(f"[dim]{pkg.get('description')}[/dim]")
    console.print(f"[dim]领域: {pkg.get('domain')} | 标签: {', '.join(pkg.get('tags', []))}[/dim]\n")

    # 来源列表
    sources = pkg.get("sources", [])
    if sources:
        s_table = Table(title=f"📑 收录知识源 ({len(sources)} 条)", box=box.SIMPLE)
        s_table.add_column("类型", style="cyan")
        s_table.add_column("标题", style="bold")
        s_table.add_column("作者", style="magenta")
        s_table.add_column("关键帧", justify="right")
        s_table.add_column("原始链接", style="dim")

        for s in sources:
            s_table.add_row(
                s.get("type"),
                s.get("title")[:35],
                s.get("author") or "-",
                str(s.get("keyframes_count", 0)),
                s.get("url")[:40] + ("..." if len(s.get("url", "")) > 40 else "")
            )
        console.print(s_table)

    # 关键帧画廊
    pkg_dir = Path(pkg.get("path"))
    kf_dir = pkg_dir / "keyframes"
    if kf_dir.exists():
        kfs = [f.name for f in kf_dir.glob("*.jpg")]
        if kfs:
            console.print(f"[bold cyan]🖼️ 已沉淀关键帧 ({len(kfs)} 张):[/bold cyan] {', '.join(kfs[:6])}")

    console.print(f"\n[dim]提示: 运行 [bold cyan]hermes-kb export {package_id} --target cursor --copy[/bold cyan] 导出为 Agent 规则[/dim]")

@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="检索关键词（支持搜资产包、正文技术点、代码片段）")
):
    """
    🔎 全库语义与关键词检索
    """
    results = exporter.search(query)
    pkgs = results.get("packages", [])
    sources = results.get("sources", [])
    snippets = results.get("snippets", [])

    console.print(f"\n[bold cyan]🔎 检索关键词:[/bold cyan] '{query}'\n")

    if pkgs:
        table = Table(title="📦 匹配的知识资产包", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("名称", style="bold white")
        table.add_column("相关标签", style="yellow")
        for p in pkgs:
            table.add_row(p["id"], p["name"], ", ".join(p.get("tags", [])))
        console.print(table)

    if sources:
        console.print(f"[bold green]📄 命中来源文档 ({len(sources)} 个):[/bold green]")
        for s in sources[:8]:
            console.print(f"- [cyan]{s['package_name']}[/cyan] > [bold]{s['filename']}[/bold]")
            console.print(f"  [dim]{s['snippet']}[/dim]")

    if snippets:
        console.print(f"\n[bold yellow]💻 命中提取代码段 ({len(snippets)} 个):[/bold yellow]")
        for sn in snippets[:5]:
            console.print(f"- [cyan]{sn['package_name']}[/cyan] > `{sn['filename']}`")

    if not pkgs and not sources and not snippets:
        console.print("[dim]未找到匹配的内容，可尝试更短的通用关键词。[/dim]")

@app.command("export")
def export_cmd(
    package_id: str = typer.Argument(..., help="待导出的知识资产包 ID"),
    target: str = typer.Option("cursor", "--target", "-t", help="目标 Agent 平台: cursor | codex | hermes"),
    copy: bool = typer.Option(False, "--copy", "-c", help="是否自动复制到系统剪贴板 (macOS pbcopy)"),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="输出到指定文件路径 (例如 .cursorrules 或 prompt.md)")
):
    """
    🚀 将资产包转化为 Cursor Rule、Codex Prompt 或 Hermes Agent 参考上下文
    """
    try:
        if target.lower() == "cursor":
            content = exporter.export_for_cursor(package_id, format_type="mdc")
        elif target.lower() == "codex":
            content = exporter.export_for_codex(package_id)
        elif target.lower() == "hermes":
            content = exporter.export_for_hermes(package_id)
        else:
            console.print(f"[bold red]不支持的 target: {target}[/bold red], 仅支持 cursor / codex / hermes")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]导出失败: {e}[/bold red]")
        raise typer.Exit(1)

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✅ 已成功导出至文件:[/bold green] {out_path.resolve()}")

    if copy:
        exporter.copy_to_clipboard(content)
        console.print(f"[bold green]📋 已成功将专用于 {target.upper()} 的知识上下文复制到系统剪贴板！可以直接粘贴给 Agent 使用。[/bold green]")
    elif not out:
        # 终端预览
        console.print(Panel(content[:1500] + ("\n...(已截断，使用 --copy 复制完整内容)" if len(content) > 1500 else ""),
                            title=f"🚀 {target.upper()} 适配上下文预览", border_style="blue"))

@app.command("serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="监听主机地址"),
    port: int = typer.Option(8765, "--port", "-p", help="监听端口号")
):
    """
    🌐 启动本地可视化操作台 (Web Dashboard)
    """
    import uvicorn
    console.print(f"[bold green]🚀 正在启动 Hermes 知识资产中心可视化控制台...[/bold green]")
    console.print(f"👉 访问地址: [bold cyan]http://{host}:{port}[/bold cyan]")
    uvicorn.run("core.web_server:app", host=host, port=port, reload=False)

@app.command("git-log")
def git_log_cmd(
    limit: int = typer.Option(8, "--limit", "-n", help="展示最近提交条数")
):
    """
    📜 查看知识资产库的 Git 版本演进历史
    """
    commits = git_mgr.get_recent_commits(limit)
    if not commits:
        console.print("[dim]暂无 Git 提交记录。[/dim]")
        return

    table = Table(title="📜 Git 知识资产版本记录", box=box.ROUNDED)
    table.add_column("Commit", style="yellow")
    table.add_column("日期", style="dim")
    table.add_column("作者", style="cyan")
    table.add_column("提交信息", style="bold white")

    for c in commits:
        table.add_row(c["hash"], c["date"], c["author"], c["message"])
    console.print(table)

if __name__ == "__main__":
    app()
