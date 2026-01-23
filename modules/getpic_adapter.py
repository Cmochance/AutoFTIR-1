# -*- coding: utf-8 -*-
"""
GetPic 适配器

将 getpic 模块作为独立服务与主项目对接。
只传递数据，不修改 getpic 内部结构。

使用方式：
1. 直接调用（同进程）：通过 adapter 函数调用
2. MCP 服务（独立进程）：启动 getpic 服务后通过 HTTP 调用
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 将 getpic 添加到路径
GETPIC_PATH = Path(__file__).parent / "getpic"
if str(GETPIC_PATH) not in sys.path:
    sys.path.insert(0, str(GETPIC_PATH))


class GetPicAdapter:
    """
    GetPic 适配器
    
    提供两种调用模式：
    1. local: 直接在进程内调用 getpic 模块
    2. remote: 通过 HTTP 调用独立运行的 getpic MCP 服务
    """
    
    def __init__(self, mode: str = "local", remote_url: str = "http://localhost:8000"):
        """
        初始化适配器
        
        Args:
            mode: 调用模式，"local" 或 "remote"
            remote_url: 远程 getpic 服务地址（mode="remote" 时使用）
        """
        self.mode = mode
        self.remote_url = remote_url.rstrip("/")
        self._orchestrator = None
    
    def _get_orchestrator(self):
        """获取本地编排器实例"""
        if self._orchestrator is None:
            from core.orchestrator import ChartExtractOrchestrator
            self._orchestrator = ChartExtractOrchestrator()
        return self._orchestrator
    
    async def extract_chart_from_image(
        self,
        image_bytes: bytes,
        hinting_text: Optional[str] = None,
        skip_preprocessing: bool = False,
    ) -> Dict[str, Any]:
        """
        从图像提取图表数据
        
        Args:
            image_bytes: 图像字节数据
            hinting_text: 辅助提示文本
            skip_preprocessing: 是否跳过预处理
            
        Returns:
            dict: 包含 success, data, error 等字段的结果
        """
        if self.mode == "remote":
            return await self._remote_extract(image_bytes, hinting_text, skip_preprocessing)
        else:
            return await self._local_extract(image_bytes, hinting_text, skip_preprocessing)
    
    async def _local_extract(
        self,
        image_bytes: bytes,
        hinting_text: Optional[str],
        skip_preprocessing: bool,
    ) -> Dict[str, Any]:
        """本地调用 getpic"""
        try:
            orchestrator = self._get_orchestrator()
            chart_data = await orchestrator.process_image(
                image_bytes,
                hinting_text,
                skip_preprocessing,
            )
            
            # 转换为字典
            from schema.chart_standard import ChartStandard
            from core.orchestrator import ExtractionResult
            
            if isinstance(chart_data, ExtractionResult):
                data = chart_data.chart.model_dump()
            elif isinstance(chart_data, ChartStandard):
                data = chart_data.model_dump()
            else:
                data = chart_data
            
            return {
                "success": True,
                "data": data,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
            }
    
    async def _remote_extract(
        self,
        image_bytes: bytes,
        hinting_text: Optional[str],
        skip_preprocessing: bool,
    ) -> Dict[str, Any]:
        """通过 HTTP 调用远程 getpic 服务"""
        import httpx
        
        url = f"{self.remote_url}/api/v1/extract/image"
        
        try:
            async with httpx.AsyncClient() as client:
                files = {"file": ("image.png", image_bytes, "image/png")}
                params = {}
                if hinting_text:
                    params["hinting_text"] = hinting_text
                if skip_preprocessing:
                    params["skip_preprocessing"] = "true"
                
                response = await client.post(url, files=files, params=params, timeout=120.0)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "data": None,
                        "error": f"HTTP {response.status_code}: {response.text}",
                    }
                
                return response.json()
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"远程调用失败: {str(e)}",
            }
    
    def to_echarts_option(self, chart_data: dict) -> dict:
        """转换为 ECharts 配置"""
        orchestrator = self._get_orchestrator()
        from schema.chart_standard import ChartStandard
        chart = ChartStandard.model_validate(chart_data)
        return orchestrator.to_echarts_option(chart)
    
    def to_highcharts_option(self, chart_data: dict) -> dict:
        """转换为 Highcharts 配置"""
        orchestrator = self._get_orchestrator()
        from schema.chart_standard import ChartStandard
        chart = ChartStandard.model_validate(chart_data)
        return orchestrator.to_highcharts_option(chart)
    
    def to_chartjs_config(self, chart_data: dict) -> dict:
        """转换为 Chart.js 配置"""
        orchestrator = self._get_orchestrator()
        from schema.chart_standard import ChartStandard
        chart = ChartStandard.model_validate(chart_data)
        return orchestrator.to_chartjs_config(chart)
    
    def get_schema(self) -> dict:
        """获取图表标准 JSON Schema"""
        from schema.chart_standard import get_chart_json_schema
        return get_chart_json_schema()


# 便捷函数
def create_adapter(mode: str = "local", remote_url: str = "http://localhost:8000") -> GetPicAdapter:
    """创建适配器实例"""
    return GetPicAdapter(mode=mode, remote_url=remote_url)


# 同步包装器（用于非异步环境）
class GetPicAdapterSync:
    """同步版本的适配器"""
    
    def __init__(self, mode: str = "local", remote_url: str = "http://localhost:8000"):
        self._async_adapter = GetPicAdapter(mode=mode, remote_url=remote_url)
    
    def extract_chart_from_image(
        self,
        image_bytes: bytes,
        hinting_text: Optional[str] = None,
        skip_preprocessing: bool = False,
    ) -> Dict[str, Any]:
        """同步版本的图表提取"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._async_adapter.extract_chart_from_image(
                image_bytes, hinting_text, skip_preprocessing
            )
        )
    
    def to_echarts_option(self, chart_data: dict) -> dict:
        return self._async_adapter.to_echarts_option(chart_data)
    
    def to_highcharts_option(self, chart_data: dict) -> dict:
        return self._async_adapter.to_highcharts_option(chart_data)
    
    def to_chartjs_config(self, chart_data: dict) -> dict:
        return self._async_adapter.to_chartjs_config(chart_data)
    
    def get_schema(self) -> dict:
        return self._async_adapter.get_schema()
