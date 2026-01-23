# AutoFTIR 设计文档

## 项目概述

AutoFTIR 是一个智能 FTIR（傅里叶变换红外光谱）分析平台。将 CSV 光谱数据绘制成图表，并通过 AI 视觉模型进行智能分析，输出分析结果和可复用的 Python 绑定脚本。

## 功能特性

| 功能 | 描述 |
|------|------|
| 多文件对比 | 支持同时上传多个光谱数据文件，生成瀑布图对比 |
| 自定义样式 | 支持自定义颜色、线宽、图例、坐标轴等绑定参数 |
| AI 分析 | 调用 AI 视觉模型（智谱/OpenAI 兼容）对图谱进行智能分析 |
| 峰识别 | 自动识别光谱中的特征峰及其半高宽 |
| 图表提取 | 从图表图片中提取结构化参数数据（GetPic 模块） |

## 技术栈

| 类型 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.10+ | 全栈 Python |
| Web 框架 | FastAPI | ≥0.109 | 后端 REST API |
| 前端框架 | Streamlit | ≥1.31 | Web UI |
| 数据处理 | NumPy/Pandas | ≥1.24/≥2.0 | 光谱数据处理 |
| 绘图 | Matplotlib | ≥3.7 | 图表生成 |
| HTTP 客户端 | httpx | ≥0.26 | 异步 HTTP 请求 |
| 数据验证 | Pydantic | ≥2.5 | 请求/响应模型 |
| AI SDK | zhipuai | ≥2.0 | 智谱 AI 调用 |

## 项目架构

```
AutoFTIR/
├── api/                        # 统一后端 API
│   ├── main.py                 # FastAPI 主入口
│   ├── config.py               # 配置管理
│   └── services/               # 服务层
│       ├── ai_service.py       # AI 分析服务
│       └── chart_service.py    # 图表提取服务
│
├── core/                       # 核心业务模块
│   └── spectrum/               # 光谱数据处理
│       ├── reader.py           # 数据读取（CSV/TXT）
│       ├── peaks.py            # 峰识别算法
│       └── plotter.py          # 图表绑定
│
├── modules/                    # 子模块
│   ├── getpic/                 # 图表参数提取引擎（MCP 架构）
│   │   ├── core/               # 核心逻辑与编排
│   │   ├── mcp_modules/        # MCP 工具模块
│   │   │   ├── img_processor/  # 图像预处理
│   │   │   └── vision_agent/   # VLM 图表识别
│   │   └── schema/             # 数据模型
│   └── getpic_adapter.py       # GetPic 适配器（解耦接口）
│
├── frontend/                   # Web 前端
│   ├── streamlit_app.py        # Streamlit 入口
│   ├── api_client.py           # API 客户端
│   ├── constants.py            # UI 常量
│   └── components/             # UI 组件
│       ├── sidebar.py          # 侧边栏
│       └── main_view.py        # 主视图
│
├── templates/                  # 模板文件
│   └── ftir_template.py        # FTIR 分析模板
│
├── nginx/                      # Nginx 配置
│   ├── default.conf            # HTTP 配置
│   └── default.conf.https      # HTTPS 配置
│
├── streamlit_app.py            # 前端入口
├── run_api.py                  # 后端入口
├── run_getpic.py               # GetPic 独立服务入口
├── docker-compose.yml          # Docker 编排
├── Dockerfile                  # 容器构建
└── requirements.txt            # Python 依赖
```

## 数据流向

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面 (Streamlit)                      │
│  上传文件 → 参数配置 → 预览图表 → 触发分析 → 显示结果            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP API
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                     后端 API (FastAPI)                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  /api/health │  │ /api/models  │  │ /analyze-img │           │
│  └──────────────┘  └──────────────┘  └──────┬───────┘           │
│                                             │                    │
│  ┌──────────────────────────────────────────┴──────────────┐    │
│  │                   服务层 (Services)                      │    │
│  │  ┌─────────────────┐        ┌─────────────────────┐     │    │
│  │  │   AIService     │        │    ChartService     │     │    │
│  │  │  (VLM 调用)     │        │   (GetPic 适配)     │     │    │
│  │  └────────┬────────┘        └──────────┬──────────┘     │    │
│  └───────────┼────────────────────────────┼────────────────┘    │
└──────────────┼────────────────────────────┼─────────────────────┘
               │                            │
               ↓                            ↓
┌──────────────────────┐       ┌────────────────────────────────┐
│  外部 AI API          │       │        GetPic 模块              │
│  - 智谱 AI           │       │  ┌─────────────────────────┐   │
│  - OpenAI 兼容       │       │  │   img_processor        │   │
└──────────────────────┘       │  │   (图像预处理)          │   │
                               │  └───────────┬─────────────┘   │
                               │              ↓                  │
                               │  ┌─────────────────────────┐   │
                               │  │   vision_agent         │   │
                               │  │   (VLM 图表识别)        │   │
                               │  └───────────┬─────────────┘   │
                               │              ↓                  │
                               │  ┌─────────────────────────┐   │
                               │  │   chart_standard       │   │
                               │  │   (标准化输出)          │   │
                               │  └─────────────────────────┘   │
                               └────────────────────────────────┘
```

## 核心模块说明

### 1. 光谱数据处理 (`core/spectrum/`)

**reader.py** - 数据读取
- 支持格式：CSV、TXT（空格分隔）
- 自动编码检测（UTF-8、GBK、GB18030）
- 输出：标准化的 `SpectrumData` 结构

**peaks.py** - 峰识别
- 算法：基于局部极值和显著性的峰检测
- 功能：自动识别峰位置、半高宽
- 模式：max（吸收峰）、min（吸收谷）、auto（自动判断）

**plotter.py** - 图表绘制
- 瀑布图对比
- 自定义样式（颜色、线宽、标签）

### 2. AI 服务 (`api/services/ai_service.py`)

支持两种 AI Provider：
- **zhipuai_sdk**：使用智谱官方 SDK
- **openai_compat**：兼容 OpenAI API 格式的服务

核心功能：
- 图像分析（VLM 多模态）
- 模型列表获取
- 多端点自动探测

### 3. GetPic 图表提取 (`modules/getpic/`)

采用 MCP（Model Context Protocol）架构的独立模块：

**核心组件：**
- `orchestrator.py`：业务编排器
- `img_processor/`：图像预处理（归一化、格式转换）
- `vision_agent/`：VLM 图表识别
- `chart_standard.py`：统一的图表数据模型

**调用方式：**
```python
# 本地调用
adapter = GetPicAdapter(mode="local")
result = await adapter.extract_chart_from_image(image_bytes)

# 远程调用（独立服务）
adapter = GetPicAdapter(mode="remote", remote_url="http://localhost:8000")
result = await adapter.extract_chart_from_image(image_bytes)
```

**输出格式：**
- 标准 JSON Schema
- ECharts 配置
- Highcharts 配置
- Chart.js 配置

## API 端点

### 系统

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/models` | 获取可用模型列表 |

### AI 分析

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/analyze-image` | AI 图像分析 |

### 图表提取

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/chart/schema` | 获取图表 JSON Schema |
| POST | `/api/v1/chart/extract` | 从图像提取图表数据 |
| POST | `/api/v1/chart/convert/echarts` | 转换为 ECharts 配置 |
| POST | `/api/v1/chart/convert/highcharts` | 转换为 Highcharts 配置 |
| POST | `/api/v1/chart/convert/chartjs` | 转换为 Chart.js 配置 |

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_PROVIDER` | AI 提供商 (`zhipuai_sdk` / `openai_compat`) | zhipuai_sdk |
| `ZHIPUAI_API_KEY` | 智谱 AI API 密钥 | - |
| `ZHIPUAI_BASE_URL` | 智谱 API 地址 | https://open.bigmodel.cn/api/paas/v4 |
| `AI_API_KEY` | OpenAI 兼容 API 密钥 | - |
| `AI_BASE_URL` | OpenAI 兼容 API 地址 | - |
| `VLM_PROVIDER` | VLM 提供商 | openai |
| `VLM_MODEL` | VLM 模型名称 | gpt-4o |
| `PORT` | API 服务端口 | 9000 |
| `HOST` | API 服务地址 | 0.0.0.0 |

### 配置文件

- `.env`：环境变量（从 `.env.example` 复制）
- `api/config.py`：应用配置管理

## 部署方式

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 3. 启动后端
python run_api.py

# 4. 启动前端（新终端）
streamlit run streamlit_app.py
```

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重建镜像
docker-compose up -d --build
```

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8501 |
| 后端 API | http://localhost:9000 |
| API 文档 | http://localhost:9000/docs |
| GetPic API | http://localhost:8000 |

## 多端支持

项目采用前后端分离架构，通过 REST API 通信：

- **Web**：Streamlit（当前实现）
- **小程序**：调用后端 API
- **App**：调用后端 API

前端只需实现 UI 层，核心逻辑由后端 API 提供。

## 扩展点

1. **新增数据格式**：在 `core/spectrum/reader.py` 中添加解析函数
2. **新增 AI Provider**：在 `api/services/ai_service.py` 中添加调用逻辑
3. **新增图表输出格式**：在 GetPic 的 `orchestrator.py` 中添加转换方法
4. **新增前端组件**：在 `frontend/components/` 中添加 Streamlit 组件
