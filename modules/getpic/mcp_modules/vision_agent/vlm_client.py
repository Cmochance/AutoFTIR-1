"""
VLM Client - 视觉语言模型客户端

支持 OpenAI GPT-5o、Anthropic Claude 4.5 和 Google Gemini 2.0 Pro 的统一接口。
使用 Structured Outputs 强制模型输出指定 Schema。

2026年1月 - 端到端 VLM 方案，无需传统 OCR
"""
import base64
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Annotated
from pydantic import Field

from schema.chart_standard import ChartStandard, get_chart_json_schema
from core.config import get_settings
from .prompts import get_extraction_prompt, get_dual_axis_detection_prompt


class VLMClientError(Exception):
    """VLM 客户端异常基类"""
    pass


class VLMConnectionError(VLMClientError):
    """VLM 连接异常"""
    pass


class VLMResponseError(VLMClientError):
    """VLM 响应异常"""
    pass


class VLMRateLimitError(VLMClientError):
    """VLM 速率限制异常"""
    pass


class BaseVLMClient(ABC):
    """
    VLM 客户端基类
    
    定义统一的图表提取接口，支持重试机制。
    """
    
    def __init__(self, api_key: str, model: str, max_retries: int = 3):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
    
    @abstractmethod
    async def _call_api(
        self,
        image_bytes: bytes,
        system_prompt: str,
    ) -> ChartStandard:
        """调用 API 的具体实现"""
        pass
    
    async def extract_chart(
        self,
        image_bytes: bytes,
        hinting_text: str | None = None,
        detect_dual_axis: bool = True,
    ) -> ChartStandard:
        """
        提取图表数据
        
        Args:
            image_bytes: 图像字节数据
            hinting_text: 辅助提示文本
            detect_dual_axis: 是否自动检测双Y轴
            
        Returns:
            ChartStandard: 标准化图表数据
        """
        # 构建提示词
        is_dual_axis = False
        if detect_dual_axis:
            is_dual_axis = await self._detect_dual_axis(image_bytes)
        
        system_prompt = get_extraction_prompt(hinting_text, is_dual_axis)
        
        # 带重试的 API 调用
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await self._call_api(image_bytes, system_prompt)
            except VLMRateLimitError as e:
                last_error = e
                # 速率限制时等待后重试
                await asyncio.sleep(2 ** attempt)
            except VLMConnectionError as e:
                last_error = e
                await asyncio.sleep(1)
            except VLMResponseError:
                raise
        
        raise VLMClientError(f"重试 {self.max_retries} 次后仍失败: {last_error}")
    
    async def _detect_dual_axis(self, image_bytes: bytes) -> bool:
        """
        检测图表是否为双Y轴
        
        使用轻量级提示快速判断。
        """
        try:
            # 简化实现：默认不检测，由主提示词处理
            # 实际生产中可以先做一次快速检测
            return False
        except Exception:
            return False


class OpenAIVLMClient(BaseVLMClient):
    """
    OpenAI GPT-5o 客户端
    
    使用 Structured Outputs (json_schema) 强制输出格式。
    """
    
    def __init__(self, api_key: str, model: str = "gpt-5o", max_retries: int = 3):
        super().__init__(api_key, model, max_retries)
        self.base_url = "https://api.openai.com/v1"
    
    async def _call_api(
        self,
        image_bytes: bytes,
        system_prompt: str,
    ) -> ChartStandard:
        """调用 OpenAI API"""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # 检测图像格式
        media_type = self._detect_media_type(image_bytes)
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this chart image and extract all data into the specified JSON schema."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "chart_standard",
                    "schema": get_chart_json_schema(),
                    "strict": True
                }
            },
            "max_tokens": 4096,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=120.0
                )
            except httpx.ConnectError as e:
                raise VLMConnectionError(f"无法连接 OpenAI API: {e}")
            except httpx.TimeoutException:
                raise VLMConnectionError("OpenAI API 请求超时")
            
            if response.status_code == 429:
                raise VLMRateLimitError("OpenAI API 速率限制")
            
            if response.status_code != 200:
                raise VLMResponseError(f"OpenAI API 错误 ({response.status_code}): {response.text}")
            
            result = response.json()
            
            try:
                content = result["choices"][0]["message"]["content"]
                return ChartStandard.model_validate_json(content)
            except (KeyError, IndexError) as e:
                raise VLMResponseError(f"OpenAI 响应格式异常: {e}")
    
    def _detect_media_type(self, image_bytes: bytes) -> str:
        """检测图像 MIME 类型"""
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        elif image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        return "image/webp"  # 默认


class AnthropicVLMClient(BaseVLMClient):
    """
    Anthropic Claude 4.5 客户端
    
    使用 tool_use 实现结构化输出。
    """
    
    def __init__(self, api_key: str, model: str = "claude-4.5-sonnet", max_retries: int = 3):
        super().__init__(api_key, model, max_retries)
        self.base_url = "https://api.anthropic.com/v1"
    
    async def _call_api(
        self,
        image_bytes: bytes,
        system_prompt: str,
    ) -> ChartStandard:
        """调用 Anthropic API"""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._detect_media_type(image_bytes)
        
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "tools": [{
                "name": "output_chart_data",
                "description": "Output the extracted chart data in the standardized format",
                "input_schema": get_chart_json_schema()
            }],
            "tool_choice": {"type": "tool", "name": "output_chart_data"},
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this chart image and extract all data. Use the output_chart_data tool to return the structured result."
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    }
                ]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2024-01-01",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=120.0
                )
            except httpx.ConnectError as e:
                raise VLMConnectionError(f"无法连接 Anthropic API: {e}")
            except httpx.TimeoutException:
                raise VLMConnectionError("Anthropic API 请求超时")
            
            if response.status_code == 429:
                raise VLMRateLimitError("Anthropic API 速率限制")
            
            if response.status_code != 200:
                raise VLMResponseError(f"Anthropic API 错误 ({response.status_code}): {response.text}")
            
            result = response.json()
            
            try:
                tool_use = next(
                    (block for block in result["content"] if block["type"] == "tool_use"),
                    None
                )
                if not tool_use:
                    raise VLMResponseError("Claude 未返回 tool_use 响应")
                
                return ChartStandard.model_validate(tool_use["input"])
            except (KeyError, StopIteration) as e:
                raise VLMResponseError(f"Anthropic 响应格式异常: {e}")
    
    def _detect_media_type(self, image_bytes: bytes) -> str:
        """检测图像 MIME 类型"""
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        elif image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        return "image/webp"


class GeminiVLMClient(BaseVLMClient):
    """
    Google Gemini 2.0 Pro 客户端
    
    使用 generationConfig 的 responseSchema 实现结构化输出。
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-pro", max_retries: int = 3):
        super().__init__(api_key, model, max_retries)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def _call_api(
        self,
        image_bytes: bytes,
        system_prompt: str,
    ) -> ChartStandard:
        """调用 Gemini API"""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._detect_media_type(image_bytes)
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"{system_prompt}\n\nAnalyze this chart and extract all data."},
                    {
                        "inline_data": {
                            "mime_type": media_type,
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": get_chart_json_schema(),
                "maxOutputTokens": 4096,
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    headers={"Content-Type": "application/json"},
                    params={"key": self.api_key},
                    json=payload,
                    timeout=120.0
                )
            except httpx.ConnectError as e:
                raise VLMConnectionError(f"无法连接 Gemini API: {e}")
            except httpx.TimeoutException:
                raise VLMConnectionError("Gemini API 请求超时")
            
            if response.status_code == 429:
                raise VLMRateLimitError("Gemini API 速率限制")
            
            if response.status_code != 200:
                raise VLMResponseError(f"Gemini API 错误 ({response.status_code}): {response.text}")
            
            result = response.json()
            
            try:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                return ChartStandard.model_validate_json(content)
            except (KeyError, IndexError) as e:
                raise VLMResponseError(f"Gemini 响应格式异常: {e}")
    
    def _detect_media_type(self, image_bytes: bytes) -> str:
        """检测图像 MIME 类型"""
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        elif image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        return "image/webp"


def get_vlm_client(provider: str | None = None) -> BaseVLMClient:
    """
    获取 VLM 客户端实例
    
    Args:
        provider: 指定提供商 (openai/anthropic/gemini)，None 则使用配置
        
    Returns:
        BaseVLMClient: VLM 客户端实例
    """
    settings = get_settings()
    provider = provider or settings.vlm_provider
    
    if provider == "openai":
        return OpenAIVLMClient(settings.openai_api_key, settings.vlm_model)
    elif provider == "anthropic":
        return AnthropicVLMClient(settings.anthropic_api_key, settings.vlm_model)
    elif provider == "gemini":
        return GeminiVLMClient(settings.gemini_api_key, settings.vlm_model)
    else:
        raise ValueError(f"不支持的 VLM 提供商: {provider}。支持: openai, anthropic, gemini")
