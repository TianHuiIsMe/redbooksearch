@echo off
chcp 65001 >nul
echo ================================================
echo 小红书AI调研Agent - 一键启动脚本 (Windows)
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [步骤1] 检查虚拟环境...
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

echo [步骤2] 激活虚拟环境...
call venv\Scripts\activate

echo [步骤3] 安装依赖...
pip install -r requirements.txt

echo [步骤4] 安装Playwright浏览器...
playwright install chromium

echo [步骤5] 检查配置文件...
if not exist config\config.json (
    echo [警告] 配置文件不存在，请先配置API密钥
    echo 请编辑 config\config.json，填写您的API密钥
    pause
    exit /b 1
)

echo [步骤6] 启动Web演示界面...
echo.
echo ================================================
echo 启动成功！
echo 请访问: <ADDRESS_REMOVED>
echo ================================================
echo.

python web_app.py

pause
