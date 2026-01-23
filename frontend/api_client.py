# -*- coding: utf-8 -*-
"""
API 客户端

封装与后端 API 的通信逻辑。
前端模块通过此客户端与后端交互，实现完全解耦。
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from base64 import b64encode
from typing import Any, Dict, List, Optional, Tuple


class APIClient:
    """后端 API 客户端"""
    
    def __init__(self, base_url: str):
        """
        初始化客户端
        
        Args:
            base_url: 后端 API 地址
        """
        self.base_url = base_url.rstrip("/")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self._get("/api/health")
    
    def fetch_models(self) -> Tuple[List[str], str]:
        """
        获取可用模型列表
        
        Returns:
            Tuple[List[str], str]: (模型列表, 来源)
        """
        try:
            data = self._get("/api/models")
            models = data.get("models") if isinstance(data, dict) else []
            source = data.get("source", "") if isinstance(data, dict) else ""
            return (models if isinstance(models, list) else [], str(source))
        except Exception:
            return ([], "")
    
    def analyze_image(
        self,
        model: str,
        prompt: str,
        png_bytes: bytes,
    ) -> str:
        """
        AI 图像分析
        
        Args:
            model: 模型名称
            prompt: 提示词
            png_bytes: PNG 图像字节
            
        Returns:
            str: 分析结果文本
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "image_mime": "image/png",
            "image_base64": b64encode(png_bytes).decode("ascii"),
        }
        
        data = self._post("/api/analyze-image", payload)
        
        if isinstance(data, dict):
            text = data.get("text")
            if isinstance(text, str):
                return text.strip()
        
        return str(data).strip() if data else ""
    
    def extract_chart(
        self,
        image_bytes: bytes,
        hinting_text: Optional[str] = None,
        include_echarts: bool = True,
        include_highcharts: bool = False,
        include_chartjs: bool = False,
    ) -> Dict[str, Any]:
        """
        从图像提取图表数据
        
        Args:
            image_bytes: 图像字节数据
            hinting_text: 辅助提示文本
            include_echarts: 是否包含 ECharts 配置
            include_highcharts: 是否包含 Highcharts 配置
            include_chartjs: 是否包含 Chart.js 配置
            
        Returns:
            dict: 提取结果
        """
        # 使用 multipart/form-data 上传文件
        import io
        
        url = f"{self.base_url}/api/v1/chart/extract"
        params = []
        if hinting_text:
            params.append(f"hinting_text={urllib.parse.quote(hinting_text)}")
        params.append(f"include_echarts={str(include_echarts).lower()}")
        params.append(f"include_highcharts={str(include_highcharts).lower()}")
        params.append(f"include_chartjs={str(include_chartjs).lower()}")
        
        if params:
            url += "?" + "&".join(params)
        
        # 简化实现：使用 base64
        payload = {
            "image_base64": b64encode(image_bytes).decode("ascii"),
            "hinting_text": hinting_text,
            "include_echarts": include_echarts,
            "include_highcharts": include_highcharts,
            "include_chartjs": include_chartjs,
        }
        
        return self._post("/api/v1/chart/extract", payload)
    
    def get_chart_schema(self) -> dict:
        """获取图表标准 JSON Schema"""
        data = self._get("/api/v1/chart/schema")
        return data.get("schema", {}) if isinstance(data, dict) else {}
    
    def _get(self, path: str) -> Any:
        """发送 GET 请求"""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            raise RuntimeError(f"HTTP 错误 {exc.code}: {raw}") from exc
        except Exception as exc:
            raise RuntimeError(f"请求失败: {exc}") from exc
    
    def _post(self, path: str, payload: dict) -> Any:
        """发送 POST 请求"""
        url = f"{self.base_url}{path}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            raise RuntimeError(f"HTTP 错误 {exc.code}: {raw}") from exc
        except Exception as exc:
            raise RuntimeError(f"请求失败: {exc}") from exc


# 便捷函数
def create_client(base_url: str) -> APIClient:
    """创建 API 客户端"""
    return APIClient(base_url)
