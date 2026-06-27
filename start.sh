#!/bin/bash

echo "================================================"
echo "小红书AI调研Agent - 一键启动脚本 (Linux/Mac)"
echo "================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python，请先安装Python 3.8+"
    exit 1
fi

echo "[步骤1] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "[步骤2] 激活虚拟环境..."
source venv/bin/activate

echo "[步骤3] 安装依赖..."
pip install -r requirements.txt

echo "[步骤4] 安装Playwright浏览器..."
playwright install chromium

echo "[步骤5] 检查配置文件..."
if [ ! -f "config/config.json" ]; then
    echo "[警告] 配置文件不存在，请先配置API密钥"
    echo "请编辑 config/config.json，填写您的API密钥"
    exit 1
fi

echo "[步骤6] 启动Web演示界面..."
echo ""
echo "================================================"
echo "启动成功！"
echo "请访问: <ADDRESS_REMOVED>
echo "================================================"
echo ""

python3 web_app.py
