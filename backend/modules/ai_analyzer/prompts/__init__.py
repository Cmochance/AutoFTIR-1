# -*- coding: utf-8 -*-
"""
系统提示词模板

根据数据类型加载对应的分析提示词
"""
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

def load_prompt(data_type: str) -> str:
    """
    加载提示词模板
    
    Args:
        data_type: 数据类型（如 spectroscopy.ftir）
        
    Returns:
        str: 提示词内容
    """
    category = data_type.split(".")[0] if "." in data_type else "general"
    
    prompt_file = PROMPTS_DIR / f"{category}.md"
    if not prompt_file.exists():
        prompt_file = PROMPTS_DIR / "general.md"
    
    return prompt_file.read_text(encoding="utf-8")

__all__ = ["load_prompt"]
