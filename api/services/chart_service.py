# -*- coding: utf-8 -*-
"""
图表提取服务

通过 GetPic 适配器调用 getpic 模块。
getpic 保持独立，只通过适配器传递数据。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from api.config import get_settings
from modules.getpic_adapter import GetPicAdapter


logger = logging.getLogger(__name__)


class ChartService:
    """图表提取服务"""
    
    def __init__(self):
        self.settings = get_settings()
        # 默认使用本地模式，也可配置为远程调用独立的 getpic 服务
        self._adapter = GetPicAdapter(
            mode="local",
            remote_url=getattr(self.settings, 'getpic_url', 'http://localhost:8000')
        )
    
    def get_schema(self) -> dict:
        """获取图表标准 JSON Schema"""
        return self._adapter.get_schema()
    
    async def extract_from_image(
        self,
        image_bytes: bytes,
        hinting_text: Optional[str] = None,
        skip_preprocessing: bool = False,
        include_echarts: bool = True,
        include_highcharts: bool = False,
        include_chartjs: bool = False,
    ) -> Dict[str, Any]:
        """
        从图像提取图表数据
        
        通过 getpic 适配器调用，保持 getpic 独立性。
        """
        try:
            # 调用 getpic 适配器
            result = await self._adapter.extract_chart_from_image(
                image_bytes,
                hinting_text,
                skip_preprocessing,
            )
            
            if not result.get("success"):
                return result
            
            chart_data = result.get("data")
            
            # 转换为各种前端框架格式
            if include_echarts and chart_data:
                result["echarts_option"] = self._adapter.to_echarts_option(chart_data)
            if include_highcharts and chart_data:
                result["highcharts_option"] = self._adapter.to_highcharts_option(chart_data)
            if include_chartjs and chart_data:
                result["chartjs_config"] = self._adapter.to_chartjs_config(chart_data)
            
            logger.info(f"提取成功: {chart_data.get('chart_type') if chart_data else 'unknown'}")
            return result
            
        except Exception as e:
            logger.exception(f"未知错误: {e}")
            return {"success": False, "error": f"服务器内部错误: {str(e)}"}
    
    def convert_to_echarts(self, chart_data: dict) -> dict:
        """转换为 ECharts 配置"""
        return self._adapter.to_echarts_option(chart_data)
    
    def convert_to_highcharts(self, chart_data: dict) -> dict:
        """转换为 Highcharts 配置"""
        return self._adapter.to_highcharts_option(chart_data)
    
    def convert_to_chartjs(self, chart_data: dict) -> dict:
        """转换为 Chart.js 配置"""
        return self._adapter.to_chartjs_config(chart_data)
