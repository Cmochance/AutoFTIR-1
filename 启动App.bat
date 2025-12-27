@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Checking Python venv...
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo 未找到虚拟环境: .venv\Scripts\python.exe
  echo 请先在项目目录创建 venv 并安装依赖，例如：
  echo   python -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

echo [2/3] Ensuring dependencies...
".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo pip 不可用，请检查 Python 环境。
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -c "import streamlit, pandas, matplotlib" >nul 2>&1
if errorlevel 1 (
  echo 检测到依赖缺失，正在安装 requirements.txt...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo 依赖安装失败，请检查网络或 pip 输出。
    pause
    exit /b 1
  )
)

echo [3/3] Starting Streamlit...
echo 将在浏览器中打开: http://localhost:8501
start "" http://localhost:8501

rem Run Streamlit in this window (keeps server alive)
".venv\Scripts\python.exe" -m streamlit run app.py

echo.
echo Streamlit 已退出。
pause
