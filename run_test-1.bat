@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo 未找到虚拟环境 .venv\Scripts\python.exe
  echo 请先在项目根目录创建/配置 Python venv。
  pause
  exit /b 1
)

".venv\Scripts\python.exe" "%~dp0测试-1.py"
echo.
pause
