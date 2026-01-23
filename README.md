# SciData - 科研数据分析平台

智能科研数据分析平台，支持多种科研数据类型的自动识别、图表绑制和 AI 深度分析。

## 功能特性

- **智能数据识别**: AI 自动识别 FTIR、XRD、SEM 等多种科研数据类型
- **美观图表生成**: 预设科研/期刊/演示多种样式，支持 PNG/SVG/PDF 导出
- **AI 深度分析**: 结合 Google Search Grounding 和向量知识库，提供专业分析报告
- **水墨风格界面**: 优雅的中国风设计，与 Mochat 风格统一

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite + Tailwind CSS + Framer Motion |
| 后端 | FastAPI + Pydantic |
| 数据库 | Supabase (PostgreSQL + pgvector) |
| AI | Google Gemini + Search Grounding |
| 部署 | Vercel (前端) + Docker (后端) |

## 项目结构

```
scidata/
├── frontend/                    # React 前端 (水墨风格)
│   ├── src/
│   │   ├── components/          # UI 组件
│   │   ├── pages/               # 页面
│   │   ├── stores/              # Zustand 状态
│   │   └── styles/              # 水墨风格样式
│   └── ...
│
├── backend/                     # FastAPI 后端
│   ├── api/                     # API 路由
│   ├── core/                    # 核心配置
│   └── modules/                 # 三大核心模块
│       ├── data_processor/      # 数据识别与处理
│       ├── chart_renderer/      # 图表绑制引擎
│       └── ai_analyzer/         # AI 深度分析
│
└── docker-compose.dev.yml       # 开发环境配置
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/scidata.git
cd scidata
```

### 2. 配置环境变量

```bash
# 后端
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 Supabase 和 Google AI 密钥

# 前端
# 在 Vercel 或本地 .env 中配置 VITE_API_BASE_URL
```

### 3. 启动开发环境

**使用 Docker (推荐)**:
```bash
docker-compose -f docker-compose.dev.yml up
```

**手动启动**:
```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 9000

# 前端
cd frontend
npm install
npm run dev
```

### 4. 访问服务

- 前端: http://localhost:3000
- 后端 API: http://localhost:9000
- API 文档: http://localhost:9000/docs

## 数据库配置

在 Supabase 控制台的 SQL Editor 中执行 `backend/database/schema.sql`。

## 部署

### 前端 (Vercel)

1. 连接 GitHub 仓库
2. 设置根目录为 `frontend`
3. 配置环境变量:
   - `VITE_API_BASE_URL`: 后端 API 地址
   - `VITE_SUPABASE_URL`: Supabase 项目 URL
   - `VITE_SUPABASE_ANON_KEY`: Supabase 匿名密钥

### 后端 (Docker)

```bash
cd backend
docker build -t scidata-backend .
docker run -d -p 9000:9000 --env-file .env scidata-backend
```

## 支持的数据类型

| 类别 | 类型 |
|------|------|
| 光谱 | FTIR, Raman, UV-Vis, XRD, NMR |
| 成像 | SEM, TEM, AFM, 荧光显微镜 |
| 色谱 | GC, HPLC, MS |
| 通用 | CSV, 时间序列, 统计数据 |

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/analyze/process` | 处理数据 |
| POST | `/api/analyze/render` | 绑制图表 |
| POST | `/api/analyze/full` | 完整分析流程 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |
| GET | `/api/history` | 获取分析历史 |

## License

MIT
