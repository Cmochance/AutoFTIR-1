"""
核心业务编排器

负责协调各 MCP 模块，实现完整的图表提取流程：
接收 -> 预处理 -> 识别 -> 验证 -> 返回

2026年1月 - 解耦式架构，支持多种前端框架输出
"""
import logging
from typing import Literal
from pydantic import BaseModel, Field

from schema.chart_standard import ChartStandard, ChartType
from mcp_modules.img_processor import normalize_image, normalize_image_with_info, ImageProcessingError
from mcp_modules.vision_agent import analyze_chart_image, ChartExtractionError
from core.config import get_settings


logger = logging.getLogger(__name__)


class OrchestrationError(Exception):
    """编排异常"""
    pass


class ProcessingMetadata(BaseModel):
    """处理元数据"""
    original_size: tuple[int, int] | None = Field(default=None, description="原始图像尺寸")
    processed_size: tuple[int, int] | None = Field(default=None, description="处理后尺寸")
    preprocessing_skipped: bool = Field(default=False, description="是否跳过预处理")
    vlm_provider: str | None = Field(default=None, description="使用的 VLM 提供商")


class ExtractionResult(BaseModel):
    """完整的提取结果"""
    chart: ChartStandard = Field(description="标准化图表数据")
    metadata: ProcessingMetadata = Field(description="处理元数据")


class ChartExtractOrchestrator:
    """
    图表提取编排器
    
    核心业务流：
    1. User uploads Image -> Core API
    2. Core invokes `img_processor` MCP -> Returns Clean Image
    3. Core invokes `vision_agent` MCP -> Returns structured Chart Data
    4. Core validates Data against `chart_standard`
    5. Returns JSON to User
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def process_image(
        self,
        image_bytes: bytes,
        hinting_text: str | None = None,
        skip_preprocessing: bool = False,
        collect_metadata: bool = False,
    ) -> ChartStandard | ExtractionResult:
        """
        完整的图表提取流程
        
        Args:
            image_bytes: 原始图像数据
            hinting_text: 辅助提示文本
            skip_preprocessing: 是否跳过预处理
            collect_metadata: 是否收集处理元数据
            
        Returns:
            ChartStandard: 验证后的标准化图表数据
            或 ExtractionResult: 包含元数据的完整结果
            
        Raises:
            OrchestrationError: 编排过程中的异常
        """
        metadata = ProcessingMetadata(preprocessing_skipped=skip_preprocessing)
        
        try:
            # Step 1: 图像预处理
            if not skip_preprocessing:
                logger.info("开始图像预处理...")
                if collect_metadata:
                    result = normalize_image_with_info(
                        image_bytes,
                        max_dimension=self.settings.max_image_dimension,
                        output_format=self.settings.output_format,
                    )
                    processed_image = result.image_data
                    metadata.original_size = result.info.original_size
                    metadata.processed_size = result.info.processed_size
                else:
                    processed_image = normalize_image(
                        image_bytes,
                        max_dimension=self.settings.max_image_dimension,
                        output_format=self.settings.output_format,
                    )
                logger.info("图像预处理完成")
            else:
                processed_image = image_bytes
                logger.info("跳过图像预处理")
            
            # Step 2: VLM 图表识别
            logger.info("开始 VLM 图表识别...")
            metadata.vlm_provider = self.settings.vlm_provider
            chart_data = await analyze_chart_image(processed_image, hinting_text)
            logger.info(f"图表识别完成，类型: {chart_data.chart_type}")
            
            # Step 3: 数据验证（Pydantic 已在 analyze_chart_image 中完成）
            
            if collect_metadata:
                return ExtractionResult(chart=chart_data, metadata=metadata)
            return chart_data
            
        except ImageProcessingError as e:
            logger.error(f"图像预处理失败: {e}")
            raise OrchestrationError(f"图像预处理失败: {e}") from e
        except ChartExtractionError as e:
            logger.error(f"图表识别失败: {e}")
            raise OrchestrationError(f"图表识别失败: {e}") from e
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise OrchestrationError(f"处理失败: {e}") from e
    
    def to_echarts_option(self, chart: ChartStandard) -> dict:
        """
        转换为 ECharts 配置格式
        
        展示解耦设计：Internal Schema -> Frontend Schema (ECharts)
        
        Args:
            chart: 标准化图表数据
            
        Returns:
            dict: ECharts option 配置
        """
        option = {
            "title": {},
            "tooltip": {"trigger": "axis" if chart.chart_type != ChartType.PIE else "item"},
            "legend": {},
            "grid": {"containLabel": True},
            "series": []
        }
        
        # 标题
        if chart.title:
            option["title"]["text"] = chart.title
        if chart.subtitle:
            option["title"]["subtext"] = chart.subtitle
        
        # 饼图特殊处理
        if chart.chart_type == ChartType.PIE:
            return self._to_echarts_pie(chart, option)
        
        # X轴
        if chart.x_axis:
            option["xAxis"] = {
                "type": chart.x_axis.type.value,
                "data": chart.x_axis.data,
            }
            if chart.x_axis.name:
                option["xAxis"]["name"] = chart.x_axis.name
            if chart.x_axis.unit:
                option["xAxis"]["axisLabel"] = {"formatter": f"{{value}} {chart.x_axis.unit}"}
        else:
            option["xAxis"] = {"type": "category"}
        
        # Y轴（支持多轴）
        option["yAxis"] = []
        for i, y_axis in enumerate(chart.y_axis):
            axis_config = {
                "type": y_axis.type.value,
                "position": y_axis.position or ("left" if i == 0 else "right"),
            }
            if y_axis.name:
                axis_config["name"] = y_axis.name
            if y_axis.min_value is not None:
                axis_config["min"] = y_axis.min_value
            if y_axis.max_value is not None:
                axis_config["max"] = y_axis.max_value
            if y_axis.unit:
                axis_config["axisLabel"] = {"formatter": f"{{value}} {y_axis.unit}"}
            option["yAxis"].append(axis_config)
        
        # 如果没有 Y 轴配置，添加默认
        if not option["yAxis"]:
            option["yAxis"] = [{"type": "value"}]
        
        # 数据系列
        legend_data = []
        for series in chart.series:
            series_config = {
                "name": series.name,
                "type": (series.type or chart.chart_type).value,
                "data": series.data,
            }
            if series.color:
                series_config["itemStyle"] = {"color": series.color}
            if series.y_axis_index > 0:
                series_config["yAxisIndex"] = series.y_axis_index
            
            # 面积图特殊处理
            if (series.type or chart.chart_type) == ChartType.AREA:
                series_config["type"] = "line"
                series_config["areaStyle"] = {}
            
            option["series"].append(series_config)
            legend_data.append(series.name)
        
        option["legend"]["data"] = legend_data
        
        # 图例位置
        if chart.legend:
            option["legend"]["show"] = chart.legend.show
            if chart.legend.position == "bottom":
                option["legend"]["bottom"] = 0
            elif chart.legend.position == "left":
                option["legend"]["left"] = 0
                option["legend"]["orient"] = "vertical"
            elif chart.legend.position == "right":
                option["legend"]["right"] = 0
                option["legend"]["orient"] = "vertical"
        
        # 样式
        if chart.style:
            if chart.style.background_color:
                option["backgroundColor"] = chart.style.background_color
            if not chart.style.grid_show:
                option["xAxis"]["splitLine"] = {"show": False}
                for y in option["yAxis"]:
                    y["splitLine"] = {"show": False}
            option["animation"] = chart.style.animation
        
        return option
    
    def _to_echarts_pie(self, chart: ChartStandard, option: dict) -> dict:
        """饼图特殊转换"""
        if chart.series:
            series = chart.series[0]
            pie_data = []
            
            # 从 x_axis.data 获取名称，或使用 legend
            names = []
            if chart.x_axis and chart.x_axis.data:
                names = chart.x_axis.data
            elif chart.legend and chart.legend.items:
                names = chart.legend.items
            else:
                names = [f"Item {i+1}" for i in range(len(series.data))]
            
            for i, value in enumerate(series.data):
                name = names[i] if i < len(names) else f"Item {i+1}"
                pie_data.append({"name": str(name), "value": value})
            
            option["series"] = [{
                "type": "pie",
                "radius": "50%",
                "data": pie_data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }]
            
            option["legend"]["data"] = [d["name"] for d in pie_data]
        
        # 移除不需要的轴配置
        option.pop("xAxis", None)
        option.pop("yAxis", None)
        option.pop("grid", None)
        
        return option
    
    def to_highcharts_option(self, chart: ChartStandard) -> dict:
        """
        转换为 Highcharts 配置格式
        
        展示解耦设计：Internal Schema -> Frontend Schema (Highcharts)
        
        Args:
            chart: 标准化图表数据
            
        Returns:
            dict: Highcharts options 配置
        """
        # Highcharts 图表类型映射
        type_mapping = {
            ChartType.BAR: "column",
            ChartType.LINE: "line",
            ChartType.SCATTER: "scatter",
            ChartType.PIE: "pie",
            ChartType.AREA: "area",
            ChartType.RADAR: "line",  # Highcharts 用 polar line
            ChartType.HEATMAP: "heatmap",
            ChartType.CANDLESTICK: "candlestick",
            ChartType.FUNNEL: "funnel",
            ChartType.GAUGE: "solidgauge",
        }
        
        hc_type = type_mapping.get(chart.chart_type, "line")
        
        option = {
            "chart": {"type": hc_type},
            "title": {"text": chart.title or ""},
            "subtitle": {"text": chart.subtitle or ""},
            "credits": {"enabled": False},
            "series": []
        }
        
        # X轴
        if chart.x_axis and chart.x_axis.data:
            option["xAxis"] = {
                "categories": [str(x) for x in chart.x_axis.data],
                "title": {"text": chart.x_axis.name or ""}
            }
        
        # Y轴
        option["yAxis"] = []
        for i, y_axis in enumerate(chart.y_axis):
            axis_config = {
                "title": {"text": y_axis.name or ""},
                "opposite": i > 0,  # 第二个轴在右侧
            }
            if y_axis.min_value is not None:
                axis_config["min"] = y_axis.min_value
            if y_axis.max_value is not None:
                axis_config["max"] = y_axis.max_value
            option["yAxis"].append(axis_config)
        
        if not option["yAxis"]:
            option["yAxis"] = [{"title": {"text": ""}}]
        
        # 数据系列
        for series in chart.series:
            series_config = {
                "name": series.name,
                "data": series.data,
            }
            if series.color:
                series_config["color"] = series.color
            if series.y_axis_index > 0:
                series_config["yAxis"] = series.y_axis_index
            
            option["series"].append(series_config)
        
        # 图例
        option["legend"] = {"enabled": True}
        if chart.legend:
            option["legend"]["enabled"] = chart.legend.show
            if chart.legend.position == "bottom":
                option["legend"]["verticalAlign"] = "bottom"
            elif chart.legend.position == "left":
                option["legend"]["align"] = "left"
                option["legend"]["layout"] = "vertical"
            elif chart.legend.position == "right":
                option["legend"]["align"] = "right"
                option["legend"]["layout"] = "vertical"
        
        return option
    
    def to_chartjs_config(self, chart: ChartStandard) -> dict:
        """
        转换为 Chart.js 配置格式
        
        Args:
            chart: 标准化图表数据
            
        Returns:
            dict: Chart.js config 配置
        """
        # Chart.js 图表类型映射
        type_mapping = {
            ChartType.BAR: "bar",
            ChartType.LINE: "line",
            ChartType.SCATTER: "scatter",
            ChartType.PIE: "pie",
            ChartType.AREA: "line",  # 使用 fill
            ChartType.RADAR: "radar",
            ChartType.HEATMAP: "matrix",  # 需要插件
            ChartType.CANDLESTICK: "candlestick",  # 需要插件
            ChartType.FUNNEL: "funnel",  # 需要插件
            ChartType.GAUGE: "doughnut",  # 模拟
        }
        
        cjs_type = type_mapping.get(chart.chart_type, "line")
        
        config = {
            "type": cjs_type,
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": bool(chart.title),
                        "text": chart.title or ""
                    },
                    "legend": {
                        "display": True,
                        "position": "top"
                    }
                }
            }
        }
        
        # Labels (X轴数据)
        if chart.x_axis and chart.x_axis.data:
            config["data"]["labels"] = [str(x) for x in chart.x_axis.data]
        
        # 数据集
        for series in chart.series:
            dataset = {
                "label": series.name,
                "data": series.data,
            }
            if series.color:
                dataset["backgroundColor"] = series.color
                dataset["borderColor"] = series.color
            
            # 面积图填充
            if (series.type or chart.chart_type) == ChartType.AREA:
                dataset["fill"] = True
            
            config["data"]["datasets"].append(dataset)
        
        # 图例位置
        if chart.legend:
            config["options"]["plugins"]["legend"]["display"] = chart.legend.show
            config["options"]["plugins"]["legend"]["position"] = chart.legend.position
        
        return config
