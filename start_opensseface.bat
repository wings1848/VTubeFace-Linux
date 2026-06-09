@echo off
chcp 65001 >nul
title OpenSeeFace

REM ============================================================================
REM OpenSeeFace Windows 启动脚本
REM ============================================================================

cd /d "%~dp0"

REM ---- 1. 检查 Python ----
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 未找到 Python，请安装 Python 3.11+
    pause
    exit /b 1
)

REM ---- 2. 检查/创建虚拟环境 ----
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] 正在创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo [OK]    虚拟环境已激活

REM ---- 3. 检查依赖 ----
python -c "import onnxruntime" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] 正在安装依赖...
    pip install -e ".[gpu]" 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [INFO] GPU 环境不可用，安装 CPU 版...
        pip install -e ".[cpu]"
    )
)

REM ---- 4. 启动 ----
if "%1"=="stop" (
    python -m openseeface stop
    goto :end
)
if "%1"=="configure" (
    python -m openseeface configure
    goto :end
)
if "%1"=="reconfig" (
    python -m openseeface configure
    goto :end
)
if "%1"=="status" (
    python -m openseeface status
    goto :end
)
if "%1"=="start" (
    python -m openseeface start
    goto :end
)

REM 无参数：有配置则启动，否则进入配置向导
if exist "config\config.json" (
    python -m openseeface start
) else (
    python -m openseeface configure
)

:end
pause
