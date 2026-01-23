"""
Unified Chart JSON Schema - 统一图表数据结构

这是所有模块的"通用语言"，定义了图表参数的标准化表示。
兼容 ECharts/Highcharts 逻辑但保持框架无关性。

GetPic 核心数据模型。

使用 Pydantic V3 配合 TypeAdapter 实现高性能序列化/反序列化。
"""
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, TypeAdapter, ConfigDict


class ChartType(str, Enum):
    """
    图表类型枚举
    
    支持的图表类型，用于指导前端渲染引擎选择正确的可视化方式。
    """
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    AREA = "area"
    RADAR = "radar"
    HEATMAP = "heatmap"
    CANDLESTICK = "candlestick"
    FUNNEL = "funnel"
    GAUGE = "gauge"


class AxisType(str, Enum):
    """
    坐标轴类型
    
    - category: 类目轴，适用于离散数据
    - value: 数值轴，适用于连续数据
    - time: 时间轴，适用于时间序列数据
    - log: 对数轴，适用于跨度较大的数值
    """
    CATEGORY = "category"
    VALUE = "value"
    TIME = "time"
    LOG = "log"


class AxisConfig(BaseModel):
    """
    坐标轴配置
    
    定义单个坐标轴的完整参数，包括类型、标签、范围等。
    支持双Y轴场景。
    """
    name: str | None = Field(default=None, description="坐标轴名称/标题")
    type: AxisType = Field(default=AxisType.CATEGORY, description="坐标轴类型")
    data: list[str | float] | None = Field(default=None, description="类目轴的标签数据")
    min_value: float | None = Field(default=None, description="数值轴最小值")
    max_value: float | None = Field(default=None, description="数值轴最大值")
    unit: str | None = Field(default=None, description="数值单位，如 '%', '万', 'USD'")
    position: str | None = Field(default=None, description="坐标轴位置: left/right/top/bottom")


class SeriesData(BaseModel):
    """
    数据系列
    
    表示图表中的一条数据线/柱/区域。
    每个系列包含名称、数据点、样式等信息。
    """
    name: str = Field(description="系列名称，通常对应图例")
    data: list[float | int | None] = Field(description="数据点列表，None表示缺失值")
    type: ChartType | None = Field(default=None, description="系列特定的图表类型（用于混合图表）")
    color: str | None = Field(default=None, description="系列颜色，如 '#FF6B6B' 或 'red'")
    y_axis_index: int = Field(default=0, description="关联的Y轴索引，用于双Y轴图表")


class LegendConfig(BaseModel):
    """
    图例配置
    
    定义图例的显示方式和位置。
    """
    show: bool = Field(default=True, description="是否显示图例")
    position: str = Field(default="top", description="图例位置: top/bottom/left/right")
    items: list[str] | None = Field(default=None, description="图例项列表")


class ChartStyle(BaseModel):
    """
    图表样式配置
    
    基础样式推断，用于还原图表的视觉特征。
    """
    background_color: str | None = Field(default=None, description="背景色")
    grid_show: bool = Field(default=True, description="是否显示网格线")
    animation: bool = Field(default=True, description="是否启用动画")


class ChartStandard(BaseModel):
    """
    统一图表数据结构 (Unified Chart JSON)
    
    这是 GetPic 的核心数据模型，所有图表识别结果
    都将转换为此格式。设计目标：
    
    1. 完整性：覆盖常见图表的所有关键参数
    2. 兼容性：可无损转换为 ECharts/Highcharts 配置
    3. 可扩展：预留字段支持未来图表类型
    
    VLM 将被强制输出此 Schema 格式的 JSON。
    
    Example:
        >>> chart = ChartStandard(
        ...     title="Monthly Sales",
        ...     chart_type=ChartType.BAR,
        ...     x_axis=AxisConfig(type=AxisType.CATEGORY, data=["Jan", "Feb", "Mar"]),
        ...     y_axis=[AxisConfig(type=AxisType.VALUE, unit="USD")],
        ...     series=[SeriesData(name="Revenue", data=[100, 150, 200])]
        ... )
        >>> json_str = ChartStandardAdapter.dump_json(chart)
    """
    model_config = ConfigDict(
        json_schema_extra={
            "title": "Unified Chart JSON Schema",
            "description": "Standard schema for chart data extraction, compatible with ECharts/Highcharts"
        }
    )
    
    # 图表基本信息
    title: str | None = Field(default=None, description="图表主标题")
    subtitle: str | None = Field(default=None, description="图表副标题")
    chart_type: ChartType = Field(description="主图表类型")
    
    # 坐标轴配置
    x_axis: AxisConfig | None = Field(default=None, description="X轴配置")
    y_axis: list[AxisConfig] = Field(default_factory=list, description="Y轴配置列表，支持双Y轴")
    
    # 数据系列
    series: list[SeriesData] = Field(default_factory=list, description="数据系列列表")
    
    # 图例与样式
    legend: LegendConfig | None = Field(default=None, description="图例配置")
    style: ChartStyle | None = Field(default=None, description="样式配置")
    
    # 元数据
    source_description: str | None = Field(default=None, description="数据来源描述")
    confidence_score: float | None = Field(default=None, ge=0, le=1, description="识别置信度 0-1")


# TypeAdapter for high-performance serialization/deserialization
# 2026年标准：使用 TypeAdapter 替代直接的 model_validate/model_dump
ChartStandardAdapter: TypeAdapter[ChartStandard] = TypeAdapter(ChartStandard)
AxisConfigAdapter: TypeAdapter[AxisConfig] = TypeAdapter(AxisConfig)
SeriesDataAdapter: TypeAdapter[SeriesData] = TypeAdapter(SeriesData)


def get_chart_json_schema() -> dict:
    """
    获取 ChartStandard 的 JSON Schema
    
    用于 VLM Structured Outputs 的 response_format 配置。
    
    Returns:
        dict: 完整的 JSON Schema 定义
    """
    return ChartStandard.model_json_schema()


def validate_chart_json(json_str: str) -> ChartStandard:
    """
    验证并解析 JSON 字符串为 ChartStandard
    
    Args:
        json_str: JSON 格式的图表数据字符串
        
    Returns:
        ChartStandard: 验证后的图表数据对象
        
    Raises:
        ValidationError: JSON 格式或数据不符合 Schema
    """
    return ChartStandardAdapter.validate_json(json_str)


def serialize_chart(chart: ChartStandard) -> bytes:
    """
    序列化 ChartStandard 为 JSON bytes
    
    使用 TypeAdapter 实现高性能序列化。
    
    Args:
        chart: 图表数据对象
        
    Returns:
        bytes: JSON 格式的字节数据
    """
    return ChartStandardAdapter.dump_json(chart)
