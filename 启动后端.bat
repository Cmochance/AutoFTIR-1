@echo off
setlocal
cd /d %~dp0

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] 未找到 .venv\Scripts\python.exe
  echo 请先在项目目录创建虚拟环境并安装依赖。
  echo.
  pause
  exit /b 1
)

echo [INFO] 检查/安装依赖...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo [INFO] 启动后端: http://localhost:8000
echo.

rem 说明：后端会在启动时自动读取项目根目录的 .env（无需 bat 解析，避免 BOM/编码问题）
if exist ".env" (
  echo [INFO] 已检测到 .env，后端启动时将自动读取。
) else (
  echo [INFO] 未检测到 .env，将仅使用系统环境变量。
)

".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
