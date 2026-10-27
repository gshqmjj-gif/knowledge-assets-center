"""
Knowledge Distiller (结构化知识特征提取与要点提炼引擎)
负责从非结构化文章/视频/网页中，根据领域特征深度提取：
- 核心功能与定位 (Core Function)
- 硬件配置要求 (Hardware: 显存/GPU/内存/CPU)
- 运行环境与依赖 (Environment: OS/Python/Node/Docker)
- 能否本地离线运行 (Local Deployability: 纯本地 / 混合API / 纯SaaS)
- 同类对比核心优势 (Advantages)
- 劣势与避坑踩坑点 (Limitations & Pitfalls)
- 极简上手实操指令 (Quickstart Commands)
"""
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hermes.distiller")

@dataclass
class StructuredKnowledgeCard:
    entity_name: str                                  # 核心技术/工具/方法/模式名称
    domain: str = "ai_tech"                           # 所属一级领域
    archetype: str = "ai_project"                     # ai_project, business_case, architecture_design, reverse_engineering, general_tech
    core_function: str = ""                           # 核心功能与解决的痛点
    hardware_specs: str = "未明确标注 (常规配置)"     # 硬件配置要求 (如: 16G显存, M系列芯片, 8G内存)
    environment: str = "Python / 容器环境"           # 运行环境 (Docker, Node.js, CUDA 12)
    local_deployable: str = "支持本地运行"             # 能否本地 (纯本地离线 / 依赖API / 纯SaaS)
    competitive_advantages: List[str] = field(default_factory=list) # 同类对比优势
    limitations_and_pitfalls: List[str] = field(default_factory=list) # 劣势、边界与避坑踩坑点
    quickstart_commands: List[str] = field(default_factory=list)    # 上手验证命令
    key_insights: List[str] = field(default_factory=list)           # 关键认知与实战心法
    sources_contributed: List[str] = field(default_factory=list)    # 贡献此卡片的知识源列表

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class KnowledgeDistiller:
    def __init__(self):
        pass

    def distill(self, title: str, text: str, domain: str = "ai_tech", source_label: str = "") -> StructuredKnowledgeCard:
        """
        从文本全文中抽取出结构化知识卡片
        """
        text_clean = text.strip()

        # 1. 提炼核心实体名称 (Entity Name)
        entity_name = self._extract_entity_name(title, text_clean)

        # 2. 判断内容原型 (Archetype)
        archetype = self._determine_archetype(domain, title, text_clean)

        # 3. 提取核心功能与定位 (Core Function)
        core_function = self._extract_core_function(title, text_clean)

        # 4. 提取硬件配置要求 (Hardware Specs)
        hardware_specs = self._extract_hardware_specs(text_clean)

        # 5. 提取运行环境与依赖 (Environment)
        environment = self._extract_environment(text_clean)

        # 6. 提炼能否本地离线运行 (Local Deployability)
        local_deployable = self._extract_local_deployability(text_clean)

        # 7. 提取同类对比优势 (Advantages)
        advantages = self._extract_advantages(text_clean)

        # 8. 提取劣势、边界与踩坑点 (Limitations & Pitfalls)
        pitfalls = self._extract_pitfalls(text_clean)

        # 9. 提取极简上手与验证命令 (Quickstart)
        commands = self._extract_commands(text_clean)

        # 10. 提炼核心关键心法 (Key Insights)
        insights = self._extract_key_insights(text_clean)

        return StructuredKnowledgeCard(
            entity_name=entity_name,
            domain=domain,
            archetype=archetype,
            core_function=core_function,
            hardware_specs=hardware_specs,
            environment=environment,
            local_deployable=local_deployable,
            competitive_advantages=advantages,
            limitations_and_pitfalls=pitfalls,
            quickstart_commands=commands,
            key_insights=insights,
            sources_contributed=[source_label] if source_label else []
        )

    def _extract_entity_name(self, title: str, text: str) -> str:
        # 0. 优先检测行业高频代表性开源项目/工具链组合
        known_canonical = [
            "REA", "Reverse-skill", "PentAGI", "ComfyUI", "Ollama", "Trellis", "Rhino",
            "Grasshopper", "BIM", "Revit", "Blender", "LangChain", "Cursor", "Codex", "Claude"
        ]
        found = [k for k in known_canonical if k.lower() in (title + " " + text[:800]).lower()]
        if len(found) >= 2:
            return " + ".join(found[:3])
        elif len(found) == 1:
            # 结合标题关键词
            return found[0]

        # 1. 常见英文技术项目名匹配
        known_tools = re.findall(r'\b[A-Z][a-zA-Z0-9_\-\+]{2,}\b', title)
        valid_tools = [t for t in known_tools if t.lower() not in ["star", "skill", "wechat", "app", "the", "and", "for"]]
        if valid_tools:
            return " + ".join(valid_tools[:3])

        # 2. 中文标题提取主词
        clean_title = re.sub(r'【.*?】|\[.*?\]|我把|怎么做|复刻任何软件|开源神器|万字长文|全景拆解|保姆级教程', '', title).strip()
        if len(clean_title) > 20:
            clean_title = clean_title[:20]
        return clean_title or title[:25]

    def _determine_archetype(self, domain: str, title: str, text: str) -> str:
        lower_blob = (title + " " + text[:600]).lower()
        if "逆向" in lower_blob or "reverse" in lower_blob or "抓包" in lower_blob or "爬虫" in lower_blob or "hook" in lower_blob:
            return "reverse_engineering"
        if domain == "business" or "变现" in lower_blob or "定价" in lower_blob or "商业模式" in lower_blob or "saas" in lower_blob:
            return "business_case"
        if domain == "architecture" or "建筑" in lower_blob or "bim" in lower_blob or "rhino" in lower_blob or "grasshopper" in lower_blob:
            return "architecture_design"
        if "模型" in lower_blob or "agent" in lower_blob or "llm" in lower_blob or "开源" in lower_blob or "github" in lower_blob:
            return "ai_project"
        return "general_tech"

    def _extract_core_function(self, title: str, text: str) -> str:
        # 匹配总结句："可以实现..."、"负责..."、"主要用于..."、"目标是..."
        func_patterns = [
            r'(?:可以实现|能够实现|负责|主要用于|核心功能是|用来)([^。！？\n]{10,80})[。！？\n]',
            r'(?:通过|借助)([^。！？\n]{10,60})(?:实现|完成|构建)',
            r'看到一个喜欢的软件功能[，,\s]+([^。！？\n]{10,80})[。！？\n]'
        ]
        for pat in func_patterns:
            m = re.search(pat, text)
            if m:
                res = m.group(1).strip()
                if len(res) >= 10:
                    return res
        # 兜底截取前两句
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 15 and not l.startswith(('#', '!', '>'))]
        return lines[0][:90] if lines else title

    def _extract_hardware_specs(self, text: str) -> str:
        specs = []
        # 显存 / GPU
        gpu_match = re.search(r'(\d+G\s*(?:显存|VRAM|显卡)|RTX\s*\d{4}|NVIDIA\s*[A-Z0-9]+|Apple\s*M\d|GPU|纯CPU)', text, re.I)
        if gpu_match:
            specs.append(gpu_match.group(1))

        # 内存
        ram_match = re.search(r'(\d+G\s*内存|RAM|\d+GB\s*RAM)', text, re.I)
        if ram_match:
            specs.append(ram_match.group(1))

        # 磁盘 / 空间
        disk_match = re.search(r'(\d+G\s*存储空间|\d+G\s*磁盘)', text, re.I)
        if disk_match:
            specs.append(disk_match.group(1))

        if specs:
            return " / ".join(specs)
        
        # 启发式推断
        if "大模型" in text or "权重" in text or "llm" in text.lower():
            return "推荐 16GB+ 显存或 Apple Silicon M系列 (16G+统一内存)"
        if "逆向" in text or "mcp" in text.lower() or "cli" in text.lower():
            return "轻量级要求: 任意主流Mac/PC (8G+内存，无需高配独立显卡)"
        return "标准机器配置 (4G~8G 内存即可无痛运行)"

    def _extract_environment(self, text: str) -> str:
        env_items = []
        lower = text.lower()
        if "docker" in lower:
            env_items.append("Docker 容器环境")
        if "node" in lower or "npm" in lower:
            m_node = re.search(r'(node(?:\.js)?\s*(?:>=|v)?\s*\d+)', text, re.I)
            env_items.append(m_node.group(1) if m_node else "Node.js (>= 18)")
        if "python" in lower:
            m_py = re.search(r'(python\s*3\.\d+)', text, re.I)
            env_items.append(m_py.group(1) if m_py else "Python 3.10+")
        if "mcp" in lower:
            env_items.append("MCP (Model Context Protocol) 插件协议客户端")
        if "ghidra" in lower or "ida" in lower:
            env_items.append("反编译分析器 (Ghidra / IDA / Hopper)")
        if "rhino" in lower or "grasshopper" in lower:
            env_items.append("Rhino 7/8 + Grasshopper")
        if "blender" in lower:
            env_items.append("Blender 4.0+")

        return " + ".join(env_items) if env_items else "跨平台标准环境 (支持 macOS / Linux / Windows)"

    def _extract_local_deployability(self, text: str) -> str:
        lower = text.lower()
        if "纯本地" in text or "离线" in text or "本地运行" in text or "无需联网" in text or "local" in lower:
            return "🟢 100% 纯本地离线运行 (无需云端依赖，数据完全私有安全)"
        if "api key" in lower or "openai" in lower or "claude code" in lower or "codex" in lower or "调用模型" in text:
            return "🟡 混合架构 (分析/逆向工具本地运行，推演重写依赖 AI 编程助手 API)"
        if "网页端" in text or "在线体验" in text:
            return "🔴 纯云端/在线服务"
        return "🟢 本地命令行/独立工具 (无强联网依赖)"

    def _extract_advantages(self, text: str) -> List[str]:
        advantages = []
        # 匹配 Star 数
        star_matches = re.findall(r'([A-Za-z0-9_\-\+]+)\s*(?:目前|获得|拿到)?\s*(\d+(?:\.\d+)?万|\d+k|\d+)\s*Star', text, re.I)
        for tool, stars in star_matches:
            advantages.append(f"{tool} 社区背书极强 (GitHub {stars} Star)")

        # 匹配优势与特色表达
        patterns = [
            r'(?:比较实用的一点|核心优势|亮点是|特色在于|好处是)(?:，|,|：|:)?\s*([^。！？\n]{8,60})',
            r'(?:会给结论带证据|有出处的解释|照着理解重写|自动避坑)([^。！？\n]{0,40})',
            r'(?:小白|新手)(?:也可以|无需代码也能)([^。！？\n]{6,40})'
        ]
        for pat in patterns:
            for m in re.finditer(pat, text):
                adv = m.group(0).strip()
                if len(adv) > 6 and adv not in advantages:
                    advantages.append(adv)

        if not advantages:
            advantages.append("模块解耦度高，支持无缝嵌入现有工作流")
            advantages.append("输出带证据链追溯，结论可二次核对验证")
        return advantages[:5]

    def _extract_pitfalls(self, text: str) -> List[str]:
        pitfalls = []
        patterns = [
            r'(?:容易踩的坑|踩坑|别碰|禁止|问题在于|痛点|缺点|限制是)(?:，|,|：|:)?\s*([^。！？\n]{8,70})',
            r'(?:Node 版本不对|MCP 没挂上|Docker 起不来|加混淆|技术对抗)([^。！？\n]{0,50})',
            r'只分析([^。！？\n]{6,50}别碰)'
        ]
        for pat in patterns:
            for m in re.finditer(pat, text):
                pit = m.group(0).strip()
                if len(pit) > 6 and pit not in pitfalls:
                    pitfalls.append(pit)

        # 常见合规与技术边界兜底
        if "逆向" in text:
            if not any("合规" in p or "加密" in p for p in pitfalls):
                pitfalls.append("合规边界：仅限合法研究或已授权目标，禁止碰商业加混淆与加密对抗目标")
            if not any("环境" in p or "Node" in p for p in pitfalls):
                pitfalls.append("依赖链繁琐：涉及多工具串联，需预先配齐 MCP 协议与指定运行时版本")

        if not pitfalls:
            pitfalls.append("依赖外部环境版本一致性，版本漂移可能导致调用失败")
            pitfalls.append("对于超大规模复杂项目，AI 一次性分析可能出现幻觉或切分过粗")
        return pitfalls[:5]

    def _extract_commands(self, text: str) -> List[str]:
        # 提取 bash/cmd 命令块
        cmds = []
        code_blocks = re.findall(r'```(?:bash|shell|sh)?\n(.*?)\n```', text, re.DOTALL)
        for block in code_blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip() and not l.startswith('#')]
            for l in lines:
                if any(l.startswith(k) for k in ["npm ", "npx ", "docker ", "pip ", "git ", "rea ", "codex ", "claude "]):
                    cmds.append(l)
        return cmds[:4]

    def _extract_key_insights(self, text: str) -> List[str]:
        insights = []
        patterns = [
            r'整件事分成([^\n]{10,60})',
            r'四段走完([^\n]{6,40})',
            r'复刻\s*≠\s*抄袭[^\n]{0,40}',
            r'按顺序走一遍[^\n]{6,40}'
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                insights.append(m.group(0).strip())

        if not insights:
            lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 20 and not l.startswith(('#', '!', '>'))]
            for l in lines[:3]:
                if any(k in l for k in ["核心", "原则", "流程", "建议", "注意"]):
                    insights.append(l[:60])
        return insights[:3]
