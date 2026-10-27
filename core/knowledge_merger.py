"""
Knowledge Merger & Incremental Deduplication Engine (增量融合与同类知识去重引擎)
负责：
1. 识别多个知识来源是否在阐述同一技术实体/方案/方法 (如 REA + Reverse-skill + PentAGI)
2. 杜绝无意义重复存储，仅提炼与增量合并新出现的参数、优势、环境与避坑要点
3. 输出高纯度、结构化的综合知识图谱与全景对比矩阵
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from core.knowledge_distiller import StructuredKnowledgeCard

logger = logging.getLogger("hermes.merger")

class KnowledgeMerger:
    def __init__(self):
        pass

    def _is_same_topic(self, card_a: Dict[str, Any], card_b: Dict[str, Any]) -> bool:
        """判断两张知识卡片是否讨论的是同一个技术实体或方案"""
        name_a = card_a.get("entity_name", "").lower()
        name_b = card_b.get("entity_name", "").lower()

        # 1. 实体名完全包含或高重合
        if name_a and name_b:
            if name_a in name_b or name_b in name_a:
                return True
            tokens_a = set(re.findall(r'[a-zA-Z0-9_\-]+', name_a))
            tokens_b = set(re.findall(r'[a-zA-Z0-9_\-]+', name_b))
            if tokens_a and tokens_b and len(tokens_a.intersection(tokens_b)) >= 1:
                return True

        # 2. 核心功能关键词高度交叠 (如都涉及 "逆向" + "复刻" 或 "REA")
        blob_a = f"{card_a.get('core_function', '')} {' '.join(card_a.get('competitive_advantages', []))}".lower()
        blob_b = f"{card_b.get('core_function', '')} {' '.join(card_b.get('competitive_advantages', []))}".lower()
        
        core_keywords = ["rea", "reverse-skill", "pentagi", "comfyui", "blender", "trellis", "ollama", "grasshopper", "saas"]
        for kw in core_keywords:
            if kw in blob_a and kw in blob_b:
                return True

        return False

    def merge_card_into_matrix(
        self,
        existing_matrix: List[Dict[str, Any]],
        new_card: StructuredKnowledgeCard,
        source_label: str
    ) -> Tuple[List[Dict[str, Any]], bool, str]:
        """
        增量去重融合核心算法：
        若已存在同类实体，进行属性层级的差分与增量追加 (Diff & Incremental Merge)；
        若为新实体，直接作为新节点存入矩阵。
        返回: (更新后的知识矩阵, 是否为增量合并, 目标实体名称)
        """
        new_dict = new_card.to_dict()
        new_dict["sources_contributed"] = [source_label] if source_label else []

        target_idx = -1
        for idx, exist in enumerate(existing_matrix):
            if self._is_same_topic(exist, new_dict):
                target_idx = idx
                break

        if target_idx == -1:
            # 未找到同类，作为全新知识实体加入
            new_dict["merged_sources_count"] = 1
            existing_matrix.append(new_dict)
            return existing_matrix, False, new_dict["entity_name"]

        # 找到已有实体，执行细粒度属性增量融合！
        base = existing_matrix[target_idx]
        base["merged_sources_count"] = base.get("merged_sources_count", 1) + 1
        
        # 记录来源归属
        if source_label and source_label not in base.get("sources_contributed", []):
            base.setdefault("sources_contributed", []).append(source_label)

        # 1. 硬件配置融合：若新卡片包含更具体的数据，则补充
        if ("常规" in base.get("hardware_specs", "") or "未明确" in base.get("hardware_specs", "")) and "常规" not in new_dict.get("hardware_specs", ""):
            base["hardware_specs"] = new_dict["hardware_specs"]
        elif new_dict.get("hardware_specs") and new_dict["hardware_specs"] not in base.get("hardware_specs", ""):
            base["hardware_specs"] += f" | {new_dict['hardware_specs']} [补充自: {source_label}]"

        # 2. 运行环境融合
        for env_item in new_dict.get("environment", "").split("+"):
            item_strip = env_item.strip()
            if item_strip and item_strip.lower() not in base.get("environment", "").lower():
                base["environment"] += f" + {item_strip}"

        # 3. 本地化能力判定优化 (若有确切的本地或混合标志)
        if "纯本地" in new_dict.get("local_deployable", "") and "纯本地" not in base.get("local_deployable", ""):
            base["local_deployable"] = new_dict["local_deployable"]

        # 4. 优势增量追加 (去重)
        existing_adv_text = " ".join(base.get("competitive_advantages", [])).lower()
        for adv in new_dict.get("competitive_advantages", []):
            # 简单去重：检查核心词是否已存在
            adv_words = [w for w in re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', adv)]
            overlap = sum(1 for w in adv_words if w.lower() in existing_adv_text)
            if overlap < max(1, len(adv_words) // 2):
                base.setdefault("competitive_advantages", []).append(f"{adv} [增量补充: {source_label}]")

        # 5. 劣势与踩坑点增量追加 (特别重要！多篇内容往往在踩坑点上互为补充)
        existing_pit_text = " ".join(base.get("limitations_and_pitfalls", [])).lower()
        for pit in new_dict.get("limitations_and_pitfalls", []):
            pit_words = [w for w in re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', pit)]
            overlap = sum(1 for w in pit_words if w.lower() in existing_pit_text)
            if overlap < max(1, len(pit_words) // 2):
                base.setdefault("limitations_and_pitfalls", []).append(f"{pit} [增量补充: {source_label}]")

        # 6. 命令增量合并
        existing_cmds = set(base.get("quickstart_commands", []))
        for cmd in new_dict.get("quickstart_commands", []):
            if cmd not in existing_cmds:
                base.setdefault("quickstart_commands", []).append(cmd)

        # 7. 心法增量合并
        existing_insights = set(base.get("key_insights", []))
        for ins in new_dict.get("key_insights", []):
            if ins not in existing_insights:
                base.setdefault("key_insights", []).append(f"{ins} (来源: {source_label})")

        existing_matrix[target_idx] = base
        logger.info(f"Incrementally merged knowledge into entity '{base['entity_name']}' from '{source_label}'")
        return existing_matrix, True, base["entity_name"]
