"""
Knowledge Merger & Incremental Deduplication Engine (增量融合与同类知识去重引擎)
负责：
1. 精准识别多篇知识来源是否属于同一核心技术/工具链/方案实体 (如 REA + Reverse-skill + PentAGI)
2. 执行维度级语义去重，杜绝语句重复、意思重合或语义断裂
3. 提炼并增量追加差异化的实战补充，输出高纯度、通顺严谨的对比矩阵
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
        """判断两张知识卡片是否属于同一技术实体或方案"""
        name_a = card_a.get("entity_name", "").lower()
        name_b = card_b.get("entity_name", "").lower()

        # 1. 实体名包含或高重合
        if name_a and name_b:
            if name_a in name_b or name_b in name_a:
                return True
            tokens_a = set(re.findall(r'[a-zA-Z0-9_\-]+', name_a))
            tokens_b = set(re.findall(r'[a-zA-Z0-9_\-]+', name_b))
            if tokens_a and tokens_b and len(tokens_a.intersection(tokens_b)) >= 1:
                return True

        # 2. 核心特征关键词高重合
        blob_a = f"{card_a.get('core_function', '')} {' '.join(card_a.get('competitive_advantages', []))}".lower()
        blob_b = f"{card_b.get('core_function', '')} {' '.join(card_b.get('competitive_advantages', []))}".lower()
        
        core_keywords = ["rea", "reverse-skill", "pentagi", "comfyui", "blender", "trellis", "ollama", "grasshopper", "saas", "claude"]
        for kw in core_keywords:
            if kw in blob_a and kw in blob_b:
                return True

        return False

    def _extract_dimension_tag(self, text: str) -> str:
        """提取诸如【合规红线】、【环境排错】等维度标签"""
        m = re.match(r'【(.*?)】', text)
        return m.group(1) if m else ""

    def _is_semantically_similar(self, s1: str, s2: str) -> bool:
        """判断两句话是否表达同一层意思"""
        clean_1 = re.sub(r'【.*?】|\[.*?\]', '', s1).strip()
        clean_2 = re.sub(r'【.*?】|\[.*?\]', '', s2).strip()
        
        # 1. 包含关系
        if clean_1 in clean_2 or clean_2 in clean_1:
            return True

        # 2. 核心关键词交叠度
        words_1 = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', clean_1))
        words_2 = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', clean_2))
        if not words_1 or not words_2:
            return False
            
        overlap = len(words_1.intersection(words_2))
        min_len = min(len(words_1), len(words_2))
        return (overlap / min_len) >= 0.55

    def merge_card_into_matrix(
        self,
        existing_matrix: List[Dict[str, Any]],
        new_card: StructuredKnowledgeCard,
        source_label: str
    ) -> Tuple[List[Dict[str, Any]], bool, str]:
        """
        维度级去重融合算法：
        若同类实体已存在，对各维度进行严谨去重与语义增量合并；
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
            new_dict["merged_sources_count"] = 1
            existing_matrix.append(new_dict)
            return existing_matrix, False, new_dict["entity_name"]

        base = existing_matrix[target_idx]
        base["merged_sources_count"] = base.get("merged_sources_count", 1) + 1
        
        # 记录来源
        if source_label and source_label not in base.get("sources_contributed", []):
            base.setdefault("sources_contributed", []).append(source_label)

        # 1. 硬件配置融合
        if ("常规" in base.get("hardware_specs", "") or "未明确" in base.get("hardware_specs", "")) and "常规" not in new_dict.get("hardware_specs", ""):
            base["hardware_specs"] = new_dict["hardware_specs"]

        # 2. 运行环境融合 (去重合并)
        base_env_parts = [e.strip() for e in base.get("environment", "").split("+") if e.strip()]
        for env_item in new_dict.get("environment", "").split("+"):
            item_strip = env_item.strip()
            if item_strip and not any(item_strip.lower() in b.lower() for b in base_env_parts):
                base_env_parts.append(item_strip)
        base["environment"] = " + ".join(base_env_parts)

        # 3. 本地化能力判定
        if "纯本地" in new_dict.get("local_deployable", "") and "纯本地" not in base.get("local_deployable", ""):
            base["local_deployable"] = new_dict["local_deployable"]

        # 4. 优势增量追加 (按维度与语义严格去重)
        base_advs = base.get("competitive_advantages", [])
        for new_adv in new_dict.get("competitive_advantages", []):
            dim = self._extract_dimension_tag(new_adv)
            
            # 检查是否已存在同维度或语义高度相近的优势
            is_dup = False
            for exist_adv in base_advs:
                exist_dim = self._extract_dimension_tag(exist_adv)
                if dim and exist_dim and dim == exist_dim:
                    is_dup = True
                    break
                if self._is_semantically_similar(exist_adv, new_adv):
                    is_dup = True
                    break

            if not is_dup:
                clean_adv = new_adv
                if source_label:
                    clean_adv += f" [补充: {source_label}]"
                base_advs.append(clean_adv)
        base["competitive_advantages"] = base_advs[:5]

        # 5. 劣势与避坑要点增量追加 (按维度严格去重，杜绝同一含义说多遍)
        base_pits = base.get("limitations_and_pitfalls", [])
        for new_pit in new_dict.get("limitations_and_pitfalls", []):
            dim = self._extract_dimension_tag(new_pit)
            
            is_dup = False
            for exist_pit in base_pits:
                exist_dim = self._extract_dimension_tag(exist_pit)
                # 同一维度（如都是【合规红线】或都是【环境排错】）保留已有的最详细一条，不再重复追加
                if dim and exist_dim and dim == exist_dim:
                    is_dup = True
                    break
                if self._is_semantically_similar(exist_pit, new_pit):
                    is_dup = True
                    break

            if not is_dup:
                clean_pit = new_pit
                if source_label:
                    clean_pit += f" [补充: {source_label}]"
                base_pits.append(clean_pit)
        base["limitations_and_pitfalls"] = base_pits[:5]

        # 6. 命令增量合并
        existing_cmds = set(base.get("quickstart_commands", []))
        for cmd in new_dict.get("quickstart_commands", []):
            if cmd not in existing_cmds:
                base.setdefault("quickstart_commands", []).append(cmd)

        # 7. 关键心法增量合并
        existing_insights = set(base.get("key_insights", []))
        for ins in new_dict.get("key_insights", []):
            if ins not in existing_insights:
                base.setdefault("key_insights", []).append(f"{ins} (来源: {source_label})")

        existing_matrix[target_idx] = base
        logger.info(f"Incrementally merged knowledge into entity '{base['entity_name']}' from '{source_label}'")
        return existing_matrix, True, base["entity_name"]
