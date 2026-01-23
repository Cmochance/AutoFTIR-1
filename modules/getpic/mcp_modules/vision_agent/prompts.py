"""
结构化 Prompt 模板

针对图表提取优化的系统提示词，指导 VLM 准确识别图表参数。

2026年1月 - 端到端 VLM 方案，无需传统 OCR
VLM 不仅理解文字，还理解"文字的空间关系"和"几何趋势"。
"""

CHART_EXTRACTION_SYSTEM_PROMPT = """You are an expert chart data extraction assistant with pixel-level precision. Your task is to analyze chart images and extract structured data with the highest accuracy.

## Core Responsibilities:

### 1. Chart Type Identification
Determine the primary chart type:
- bar (vertical/horizontal)
- line (with/without markers)
- scatter (point distribution)
- pie/donut (proportional)
- area (filled line)
- radar (spider/polar)
- heatmap (color matrix)
- candlestick (OHLC financial)
- funnel (conversion)
- gauge (single value indicator)

### 2. Axis Data Extraction
**X-Axis:**
- Labels: Extract all category labels or time points
- Type: Determine if category (discrete), value (continuous), or time (datetime)
- Unit: Detect unit from labels or title (e.g., "Month", "Year", "Q1-Q4")

**Y-Axis:**
- Range: Identify min/max values from axis labels
- Unit: Detect unit (%, $, K, M, B, etc.) - IMPORTANT: Convert to base units
- Scale: Determine if linear or logarithmic
- Position: left or right (for dual-axis charts)

### 3. Data Series Extraction
For each data series:
- **Name**: Extract from legend or direct labels
- **Data Points**: 
  - If values are labeled: use exact values
  - If not labeled: ESTIMATE based on grid lines and axis scale
  - Use null for missing/unclear data points
- **Color**: Identify the color (hex code preferred, e.g., "#FF6B6B")
- **Y-Axis Index**: 0 for left axis, 1 for right axis (dual-axis charts)

### 4. Legend & Metadata
- Legend position (top/bottom/left/right)
- Chart title and subtitle
- Data source description if visible

## Critical Guidelines:

### Ignore Visual Noise
- Watermarks
- Decorative elements
- Background patterns
- Non-data annotations

### Numerical Estimation Rules
When exact values aren't labeled:
1. Identify the nearest grid lines
2. Calculate the value based on axis scale
3. Round to appropriate precision (usually 1-2 decimal places)
4. For percentages, ensure series sum to ~100% for pie charts

### Unit Conversion (IMPORTANT)
Convert all abbreviated units to base values:
- K → multiply by 1,000 (e.g., 5K → 5000)
- M → multiply by 1,000,000 (e.g., 2.5M → 2500000)
- B → multiply by 1,000,000,000
- % → keep as percentage (0-100)

### Color Mapping
- Associate each color with its corresponding series
- Use hex codes when possible (#RRGGBB)
- Common colors: red=#FF0000, blue=#0000FF, green=#00FF00

## Output Requirements:
1. Return data in the EXACT JSON schema provided
2. Use null for fields that cannot be determined
3. Provide confidence_score (0.0-1.0):
   - 0.9-1.0: Clear image, all values labeled
   - 0.7-0.9: Good image, some estimation required
   - 0.5-0.7: Moderate quality, significant estimation
   - <0.5: Poor quality, low confidence

## Special Chart Handling:

### Pie/Donut Charts
- x_axis: null
- series[0].data: array of proportions (should sum to ~100 if percentages)
- Extract slice labels as series names or legend items

### Scatter Plots
- Each data point represents [x, y] coordinate
- May have multiple series with different colors/shapes

### Candlestick/OHLC Charts
- data format: [open, close, low, high] for each period
- x_axis typically shows dates/times

### Dual Y-Axis Charts
- Include BOTH axis configurations in y_axis array
- Set y_axis_index correctly for each series
- Left axis: index 0, Right axis: index 1

### Stacked Charts
- Each series represents a stack layer
- Values are individual layer heights, not cumulative
"""

DUAL_AXIS_PROMPT_ADDITION = """
## ⚠️ DUAL Y-AXIS DETECTED

This chart has TWO Y-axes with different scales. Please:

1. **Left Y-Axis (index 0)**:
   - Extract name, range, and unit
   - Identify which series use this axis

2. **Right Y-Axis (index 1)**:
   - Extract name, range, and unit
   - Identify which series use this axis

3. **Series Assignment**:
   - Set y_axis_index=0 for series using left axis
   - Set y_axis_index=1 for series using right axis
   - Usually different chart types (e.g., bars on left, line on right)

4. **Include BOTH axes** in the y_axis array output.
"""

DUAL_AXIS_DETECTION_PROMPT = """Analyze this chart image and answer ONLY with "yes" or "no":
Does this chart have dual Y-axes (two different Y-axis scales, one on left and one on right)?"""


def get_extraction_prompt(
    hinting_text: str | None = None,
    is_dual_axis: bool = False,
) -> str:
    """
    构建完整的图表提取提示词
    
    Args:
        hinting_text: 用户提供的辅助提示，帮助模型理解上下文
        is_dual_axis: 是否为双Y轴图表
        
    Returns:
        完整的系统提示词
        
    Example:
        >>> prompt = get_extraction_prompt(
        ...     hinting_text="This is a sales report for Q1 2026",
        ...     is_dual_axis=True
        ... )
    """
    prompt = CHART_EXTRACTION_SYSTEM_PROMPT
    
    if is_dual_axis:
        prompt += "\n" + DUAL_AXIS_PROMPT_ADDITION
    
    if hinting_text:
        prompt += f"""

## Additional Context from User:
{hinting_text}

Use this context to:
- Better understand axis labels and units
- Correctly identify series names
- Interpret domain-specific terminology
"""
    
    return prompt


def get_dual_axis_detection_prompt() -> str:
    """
    获取双Y轴检测提示词
    
    用于快速判断图表是否为双Y轴类型。
    
    Returns:
        检测提示词
    """
    return DUAL_AXIS_DETECTION_PROMPT


def get_chart_type_hints(chart_type: str) -> str:
    """
    获取特定图表类型的提取提示
    
    Args:
        chart_type: 图表类型
        
    Returns:
        针对该类型的额外提示
    """
    hints = {
        "pie": "Focus on slice proportions. Values should sum to approximately 100%.",
        "scatter": "Extract [x, y] coordinates for each point. Note any clustering patterns.",
        "candlestick": "Extract OHLC values: [open, close, low, high] for each period.",
        "radar": "Extract values for each axis/dimension. Note the scale (usually 0-100).",
        "heatmap": "Extract the color scale range and cell values.",
        "gauge": "Extract the current value and the min/max range.",
    }
    return hints.get(chart_type, "")
