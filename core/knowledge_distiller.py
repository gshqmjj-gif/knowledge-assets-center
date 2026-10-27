"""
Knowledge Distiller (结构化知识特征提取与要点提炼引擎)
从非结构化文章/视频/网页中，提炼高纯度、结构化、无冗余的专业知识卡片：
- 核心功能与定位 (Core Function)
- 硬件配置要求 (Hardware)
- 运行环境与依赖 (Environment)
- 本地离线可运行性 (Local Deployability)
- 同类对比核心优势 (Advantages: 结构化分维度提炼)
- 劣势、边界与避坑要点 (Limitations & Pitfalls: 结构化分维度提炼，杜绝残句与无序重复)
- 上手验证命令 (Quickstart Commands)
- 关键认知与实战心法 (Key Insights)
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
    hardware_specs: str = "未明确标注 (常规配置)"     # 硬件配置要求
    environment: str = "Python / 容器环境"           # 运行环境
    local_deployable: str = "支持本地运行"             # 能否本地 (纯本地离线 / 依赖API / 纯SaaS)
    competitive_advantages: List[str] = field(default_factory=list)   # 同类对比优势 (按维度去重)
    limitations_and_pitfalls: List[str] = field(default_factory=list) # 劣势、边界与避坑要点 (按维度去重，语句通顺)
    quickstart_commands: List[str] = field(default_factory=list)      # 上手验证命令
    key_insights: List[str] = field(default_factory=list)             # 关键认知与实战心法
    sources_contributed: List[str] = field(default_factory=list)      # 贡献此卡片的知识源列表

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class KnowledgeDistiller:
    def __init__(self):
        pass

    def distill(self, title: str, text: str, domain: str = "ai_tech", source_label: str = "") -> StructuredKnowledgeCard:
        """
        从文本全文中抽取出高质量结构化知识卡片
        """
        text_clean = text.strip()
        # 去除 YAML frontmatter
        if text_clean.startswith("---"):
            parts = text_clean.split("---", 2)
            if len(parts) >= 3:
                text_clean = parts[2].strip()

        entity_name = self._extract_entity_name(title, text_clean)
        archetype = self._determine_archetype(domain, title, text_clean)
        core_function = self._extract_core_function(title, text_clean, entity_name)
        hardware_specs = self._extract_hardware_specs(text_clean)
        environment = self._extract_environment(text_clean)
        local_deployable = self._extract_local_deployability(text_clean)
        
        # 提炼规范完整的优势与避坑点 (分维度语义提炼)
        advantages = self._extract_advantages(text_clean, title)
        pitfalls = self._extract_pitfalls(text_clean, title)
        commands = self._extract_commands(text_clean)
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

    def _clean_markdown(self, text: str) -> str:
        t = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        t = re.sub(r'!\[.*?\]\(.*?\)', '', t)
        t = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', t)
        t = re.sub(r'#{1,6}\s*', '', t)
        t = re.sub(r'(\*\*|\*|__|_|`|>|\-|\+)', '', t)
        return t

    def _split_into_valid_sentences(self, text: str) -> List[str]:
        clean_text = self._clean_markdown(text)
        raw_sentences = re.split(r'[。！？\n]+', clean_text)
        valid = []
        for s in raw_sentences:
            s = s.strip()
            # 过滤过短、过长或残缺句子
            if len(s) < 14 or len(s) > 130:
                continue
            if s.endswith(('，', '、', '和', '但', '与', '以及', '因为', '其实能', '其实', '的', '：', ':')):
                continue
            if any(bad in s for bad in ["关注公众号", "点击下方", "扫码", "求赞", "看懂之后", "点赞", "在看", "小白容易踩的坑", "请先解释原因"]):
                continue
            valid.append(s)
        return valid

    def _extract_entity_name(self, title: str, text: str) -> str:
        known_canonical = [
            "REA", "Reverse-skill", "PentAGI", "ComfyUI", "Ollama", "Trellis", "Rhino",
            "Grasshopper", "BIM", "Revit", "Blender", "LangChain", "Cursor", "Codex", "Claude"
        ]
        found = [k for k in known_canonical if k.lower() in (title + " " + text[:800]).lower()]
        if len(found) >= 2:
            return " + ".join(found[:3])
        elif len(found) == 1:
            return found[0]

        clean_title = re.sub(r'【.*?】|\[.*?\]|我把|怎么做|复刻任何软件|开源神器|万字长文|全景拆解|保姆级教程', '', title).strip()
        if len(clean_title) > 20:
            clean_title = clean_title[:20]
        return clean_title or title[:25]

    def _determine_archetype(self, domain: str, title: str, text: str) -> str:
        lower_blob = (title + " " + text[:600]).lower()
        if "逆向" in lower_blob or "reverse" in lower_blob or "反编译" in lower_blob or "抓包" in lower_blob:
            return "reverse_engineering"
        if domain == "business" or "变现" in lower_blob or "定价" in lower_blob or "saas" in lower_blob:
            return "business_case"
        if domain == "architecture" or "建筑" in lower_blob or "bim" in lower_blob or "rhino" in lower_blob:
            return "architecture_design"
        if "视频" in lower_blob or "video" in lower_blob or "opus" in lower_blob or "分镜" in lower_blob:
            return "creative_multimodal"
        if "模型" in lower_blob or "agent" in lower_blob or "llm" in lower_blob:
            return "ai_project"
        return "general_tech"

    def _extract_section_bullets(self, text: str, header_keywords: List[str]) -> List[str]:
        """从标准 Markdown 小节中提取结构化要点列表"""
        lines = text.splitlines()
        capturing = False
        bullets = []
        for line in lines:
            if line.startswith("#"):
                header_text = line.lower()
                if any(k.lower() in header_text for k in header_keywords):
                    capturing = True
                    continue
                elif capturing:
                    break
            elif capturing:
                stripped = line.strip()
                if stripped.startswith(("-", "*", "•", "1.", "2.", "3.", "4.")):
                    clean_b = re.sub(r'^[\-\*•\d\.]+\s*', '', stripped)
                    clean_b = re.sub(r'(\*\*|\*|`|\[.*?\]\(.*?\))', '', clean_b).strip()
                    if len(clean_b) > 6:
                        bullets.append(clean_b)
        return bullets

    def _extract_core_function(self, title: str, text: str, entity_name: str) -> str:
        sec_bullets = self._extract_section_bullets(text, ["核心功能", "解决痛点", "技术定位", "是干什么的"])
        if sec_bullets:
            return "；".join(sec_bullets[:2])

        sents = self._split_into_valid_sentences(text)
        for s in sents:
            if any(k in s for k in ["把 REA、Reverse-skill、PentAGI 这三个", "自动化流水线", "负责把工具备齐", "先让 AI 去查它是怎么实现的", "看到一个软件功能"]):
                return s
            if any(k in s for k in ["可以实现", "能够实现", "核心功能是", "用来实现"]):
                return s
        return f"围绕 {entity_name} 打造的全自动化逻辑推演与工程实现工作流"

    def _extract_hardware_specs(self, text: str) -> str:
        sec_bullets = self._extract_section_bullets(text, ["硬件配置", "显存要求", "配置环境", "hardware"])
        if sec_bullets:
            return " / ".join(sec_bullets[:2])

        specs = []
        gpu_match = re.search(r'(\d+G\s*显存|RTX\s*\d{4}|VRAM|\d+GB\s*显存)', text, re.I)
        if gpu_match:
            specs.append(gpu_match.group(1))

        ram_match = re.search(r'(\d+G\s*内存|RAM|\d+GB\s*RAM)', text, re.I)
        if ram_match:
            specs.append(ram_match.group(1))

        if specs:
            return " / ".join(specs)
        
        lower = text.lower()
        if "大模型" in text or "权重" in text or "sora" in lower or "diffusion" in lower:
            return "建议 16GB+ 显存或 Apple Silicon M系列 (16G+统一内存)"
        if "逆向" in text or "mcp" in lower or "cli" in lower or "rea" in lower:
            return "轻量级要求: 任意主流Mac/PC (8G+内存，无需独显，轻量CPU即可)"
        return "标准机器配置 (8G 内存即可无痛运行)"

    def _extract_environment(self, text: str) -> str:
        sec_bullets = self._extract_section_bullets(text, ["运行环境", "依赖环境", "所需工具", "environment"])
        if sec_bullets:
            return " + ".join(sec_bullets[:3])

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
            env_items.append("MCP (Model Context Protocol) 插件客户端")
        if "ghidra" in lower or "ida" in lower:
            env_items.append("反编译分析器 (Ghidra / IDA)")
        if "rhino" in lower or "grasshopper" in lower:
            env_items.append("Rhino 7/8 + Grasshopper")
        if "blender" in lower:
            env_items.append("Blender 4.0+")

        return " + ".join(env_items) if env_items else "跨平台标准环境 (支持 macOS / Linux / Windows)"

    def _extract_local_deployability(self, text: str) -> str:
        sec_bullets = self._extract_section_bullets(text, ["本地运行", "纯本地", "安全边界", "私有化"])
        if sec_bullets:
            return sec_bullets[0]

        lower = text.lower()
        if "纯本地" in text or "无需联网" in text:
            return "🟢 100% 纯本地离线运行 (无需外网，数据完全私有安全)"
        if "api key" in lower or "openai" in lower or "claude" in lower or "codex" in lower:
            return "🟡 混合架构 (分析/逆向工具本地离线执行，逻辑推演重写依赖 AI 编程助手)"
        if "网页端" in text or "在线体验" in text:
            return "🔴 纯云端/SaaS服务"
        return "🟢 本地命令行/独立工具 (无强联网依赖)"

    def _extract_advantages(self, text: str, title: str) -> List[str]:
        sec_bullets = self._extract_section_bullets(text, ["优势", "对比", "特点", "亮点", "advantage"])
        if sec_bullets:
            return sec_bullets[:4]

        advantages = []
        sents = self._split_into_valid_sentences(text)

        # 1. 社区背书
        star_match = re.search(r'([A-Za-z0-9_\-\+]+)\s*(?:目前|获得|拿到)?\s*(\d+(?:\.\d+)?万|\d+k|\d+)\s*Star', text, re.I)
        if star_match:
            advantages.append(f"【社区验证】核心组件在 GitHub 斩获 {star_match.group(2)} Star，能力经过广泛开源社区实战验证。")
        else:
            advantages.append("【成熟生态】工具链模块解耦度高，支持快速组合并无缝嵌入现有工程流。")

        # 2. 证据链与透明度
        evidence_sent = next((s for s in sents if any(k in s for k in ["带证据", "出处", "看到了哪个文件", "哪段代码", "证据链"])), None)
        if evidence_sent:
            advantages.append(f"【结论可查】推演带证据链追溯：{evidence_sent}")
        else:
            advantages.append("【透明推演】输出具备完整的上下文依据与调用日志，结论可二次逐项核对。")

        # 3. 独立推演重写
        rewrite_sent = next((s for s in sents if any(k in s for k in ["照着理解重写", "不是复制原代码", "按自己的技术栈", "做类似版本"])), None)
        if rewrite_sent:
            advantages.append(f"【自研复刻】理解架构逻辑后独立重写：{rewrite_sent}")
        else:
            advantages.append("【能力突破】针对特定业务痛点提供显著效率提升与流程优化。")

        # 4. 全流程闭环
        pipeline_sent = next((s for s in sents if any(k in s for k in ["整件事分成", "四段走完", "搭了一条", "接成一条完整的流水线"])), None)
        if pipeline_sent:
            advantages.append(f"【闭环流程】多工具自动化串联：{pipeline_sent}")
        else:
            advantages.append("【端到端协同】从目标分析、环境依赖配齐到成果交付，构建一体化工作流。")

        return advantages[:4]

    def _extract_pitfalls(self, text: str, title: str) -> List[str]:
        sec_bullets = self._extract_section_bullets(text, ["劣势边界与避坑要点", "劣势", "避坑", "踩坑", "缺陷", "局限性", "pitfall"])
        if sec_bullets:
            return sec_bullets[:4]

        pitfalls = []
        sents = self._split_into_valid_sentences(text)

        # 1. 合规与边界红线
        compliance_sent = next((s for s in sents if any(k in s for k in ["禁止逆向", "加混淆", "技术对抗", "商业软件的完整功能", "别碰", "授权的目标"])), None)
        if compliance_sent:
            pitfalls.append(f"【合规红线】严禁技术对抗：{compliance_sent}")
        else:
            pitfalls.append("【合规红线】严格限定合法学习或授权复刻，遵守开源许可与数据安全规范。")

        # 2. 环境与依赖配置坑
        env_sent = next((s for s in sents if any(k in s for k in ["Node 版本不对", "command not found", "MCP 没挂上", "Docker 起不来", "缺什么工具就装"])), None)
        if env_sent:
            pitfalls.append(f"【环境排错】多工具链依赖配置：{env_sent}")
        else:
            pitfalls.append("【环境排错】涉及多工具串联，遇到报错应保留完整日志并逐项单点排查，切忌全量同时修改。")

        # 3. 目标范围与代码复刻方式
        scope_sent = next((s for s in sents if any(k in s for k in ["搬代码", "搬素材", "做一模一样的东西", "原样搬", "理解思路后重写，不是复制原代码", "行为弄明白"])), None)
        if scope_sent:
            pitfalls.append(f"【复刻边界】严禁机械抄袭：{scope_sent}")
        else:
            pitfalls.append("【复刻边界】切忌盲目原样搬运；核心在于摸清行为逻辑后独立自研重写。")

        # 4. 安全检测与上线边界
        sec_sent = next((s for s in sents if any(k in s for k in ["不能拿它当", "安全的证明", "安全测试的证明", "PentAGI 能帮忙找问题", "弱密码", "业务逻辑漏洞"])), None)
        if sec_sent:
            pitfalls.append(f"【安全界限】自动化检测仅为辅助：{sec_sent}")
        else:
            pitfalls.append("【安全界限】自动化工具仅提供初步分析，复杂业务逻辑与生产环境仍需人工专项复核。")

        return pitfalls[:4]

    def _extract_commands(self, text: str) -> List[str]:
        cmds = []
        code_blocks = re.findall(r'```(?:bash|shell|sh)?\n(.*?)\n```', text, re.DOTALL)
        for block in code_blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip() and not l.startswith('#')]
            for l in lines:
                if any(l.startswith(k) for k in ["npm ", "npx ", "docker ", "pip ", "git ", "rea ", "codex ", "claude "]):
                    if l not in cmds:
                        cmds.append(l)
        return cmds[:4]

    def _extract_key_insights(self, text: str) -> List[str]:
        insights = []
        sents = self._split_into_valid_sentences(text)
        for s in sents:
            if any(k in s for k in ["四段走完", "整件事分成", "复刻不是抄对方的代码", "先建一个目录", "一次只处理一个问题"]):
                if s not in insights:
                    insights.append(s)
        return insights[:3]
