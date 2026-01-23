# -*- coding: utf-8 -*-
"""
AI 分析服务

封装 AI 模型调用逻辑，支持智谱和 OpenAI 兼容接口。
"""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

import httpx

from api.config import get_settings


logger = logging.getLogger(__name__)


class AIService:
    """AI 分析服务"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def fetch_models_from_remote(self, base_url: str, api_key: str) -> List[str]:
        """从远端获取模型列表"""
        headers = {"Authorization": f"Bearer {api_key}"}
        candidate_urls = [
            f"{base_url.rstrip('/')}/models",
            f"{base_url.rstrip('/')}/v1/models",
        ]
        
        for url in candidate_urls:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, headers=headers)
                if resp.status_code >= 400:
                    continue
                data = resp.json()
                
                models: List[str] = []
                if isinstance(data, dict) and isinstance(data.get("data"), list):
                    for item in data["data"]:
                        if isinstance(item, dict):
                            mid = item.get("id")
                            if isinstance(mid, str) and mid.strip():
                                models.append(mid.strip())
                
                if models:
                    return models
            except Exception:
                continue
        
        return []
    
    def analyze_image(
        self,
        model: str,
        prompt: str,
        image_base64: str,
        image_mime: str = "image/png",
    ) -> str:
        """
        分析图像
        
        Args:
            model: 模型名称
            prompt: 提示词
            image_base64: Base64 编码的图像
            image_mime: 图像 MIME 类型
            
        Returns:
            str: 分析结果文本
        """
        provider = self.settings.ai_provider
        
        # GLM-4V-Flash 不支持 base64
        if provider != "openai_compat" and model.strip() == "glm-4v-flash":
            raise ValueError("glm-4v-flash 不支持 base64 图片输入")
        
        data_url = f"data:{image_mime};base64,{image_base64}"
        candidate_urls = [data_url, image_base64]
        
        if provider == "openai_compat":
            return self._call_openai_compat(model, prompt, candidate_urls)
        else:
            return self._call_zhipuai(model, prompt, candidate_urls)
    
    def _call_openai_compat(
        self,
        model: str,
        prompt: str,
        image_urls: List[str],
    ) -> str:
        """调用 OpenAI 兼容接口"""
        api_key = self.settings.effective_ai_api_key
        if not api_key:
            raise RuntimeError("未设置 API Key")
        
        base_url = self.settings.effective_ai_base_url
        candidate_endpoints = [
            f"{base_url}/chat/completions",
            f"{base_url}/v1/chat/completions",
        ]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        for endpoint in candidate_endpoints:
            for img_url in image_urls:
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": img_url}},
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                }
                
                try:
                    with httpx.Client(timeout=120.0) as client:
                        r = client.post(endpoint, headers=headers, json=payload)
                    
                    if r.status_code >= 400:
                        continue
                    
                    resp = r.json()
                    text = self._extract_text_from_response(resp)
                    if text:
                        return text
                except Exception:
                    continue
        
        raise RuntimeError("所有尝试均失败")
    
    def _call_zhipuai(
        self,
        model: str,
        prompt: str,
        image_urls: List[str],
    ) -> str:
        """调用智谱 AI"""
        try:
            from zhipuai import ZhipuAI
        except ImportError:
            raise RuntimeError("缺少 zhipuai 依赖")
        
        api_key = self.settings.zhipuai_api_key
        if not api_key:
            raise RuntimeError("未设置 ZHIPUAI_API_KEY")
        
        base_url = self.settings.zhipuai_base_url
        client = ZhipuAI(api_key=api_key, base_url=base_url)
        
        for img_url in image_urls:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": img_url}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            
            try:
                resp = client.chat.completions.create(model=model, messages=messages)
                text = self._extract_text_from_response(resp)
                if text:
                    return text
            except Exception as e:
                if "1210" in str(e) and "参数" in str(e):
                    continue
                raise
        
        raise RuntimeError("所有尝试均失败")
    
    def _extract_text_from_response(self, resp: Any) -> Optional[str]:
        """从响应中提取文本"""
        def _from_content(content: Any) -> Optional[str]:
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, str) and item.strip():
                        parts.append(item)
                    elif isinstance(item, dict):
                        t = item.get("text")
                        if isinstance(t, str) and t.strip():
                            parts.append(t.strip())
                    elif hasattr(item, "text"):
                        text_attr = getattr(item, "text", None)
                        if isinstance(text_attr, str) and text_attr.strip():
                            parts.append(text_attr.strip())
                return "\n".join(parts) if parts else None
            return None
        
        # dict 风格
        if isinstance(resp, dict):
            try:
                choices = resp.get("choices")
                if isinstance(choices, list) and choices:
                    msg = choices[0].get("message") if isinstance(choices[0], dict) else None
                    if isinstance(msg, dict):
                        return _from_content(msg.get("content"))
            except Exception:
                return None
        
        # SDK 对象风格
        try:
            choices = getattr(resp, "choices", None)
            if isinstance(choices, list) and choices:
                msg = getattr(choices[0], "message", None)
                content = getattr(msg, "content", None) if msg else None
                return _from_content(content)
        except Exception:
            return None
        
        return None
