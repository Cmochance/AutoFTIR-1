# AutoFTIR

## 数据文件格式

- 支持：`.txt` / `.csv`（自动读取前两列为 x/y；会自动跳过表头等非数字行）
- `.txt`：空格/Tab 等空白符分隔
- `.csv`：逗号/分号/Tab 分隔（会自动识别）

## AI 分析增强

- 发送图谱图片给 AI 时，会从原始数据自动提取“前五个最强峰”的中心位置与范围，并附加到 Prompt 中，提升官能团/峰指认的精度。

## 本地配置（API Key / Base URL）

为符合“前端 → 后端 → 厂商”的安全约束，本项目不会在前端或生成脚本中保存厂商 API Key。

推荐做法：在项目根目录使用本地配置文件 `.env` 存放敏感信息（不要提交到仓库）。

1) 复制示例文件

- 将 `.env.example` 复制为 `.env`

2) 编辑 `.env`，填写：

- `ZHIPUAI_API_KEY=你的key`
- `ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/`（可选，不填则用默认）

可选（为后续更换模型/厂商准备，默认不需要）：

- `AI_PROVIDER=zhipuai_sdk`（默认）或 `AI_PROVIDER=openai_compat`
- `AI_API_KEY=...`（不填则回退使用 `ZHIPUAI_API_KEY`）
- `AI_BASE_URL=...`（不填则回退使用 `ZHIPUAI_BASE_URL`）
- `AI_DEBUG=1` 打开后端调试打印（会输出 response 类型与截断预览）

建议：将 `.env` 保存为 **UTF-8 无 BOM**，避免首行变量名带不可见字符导致读取失败。

3) 启动后端

- 双击 `启动后端.bat`

说明：后端启动时会自动读取项目根目录的 `.env`（同时也支持系统环境变量注入，便于云部署）。
