@echo off
REM MCP服务器启动脚本 (Windows)

echo 启动MCP服务器...
echo.

REM 设置工作目录
cd /d "%~dp0"

REM 设置Python路径
set PYTHONPATH=%~dp0..

REM 启动服务器
python start_server.py %*

REM 如果出错，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo 服务器启动失败，请检查错误信息
    pause
)