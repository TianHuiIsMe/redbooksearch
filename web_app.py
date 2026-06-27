"""
Web演示界面 - 使用Flask创建简单的Web应用
让用户可以通过浏览器输入关键词、查看进度、下载报告
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import threading
from datetime import datetime
from agent.core import XiaohongshuAIAgent
import sys

app = Flask(__name__)

# 全局变量存储任务状态
task_status = {
    "is_running": False,
    "progress": "",
    "result": None,
    "error": None
}


def run_agent_task(keywords):
    """在后台运行Agent任务"""
    global task_status

    try:
        task_status["is_running"] = True
        task_status["progress"] = "正在初始化Agent..."

        # 加载配置
        import json
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        task_status["progress"] = f"正在启动Agent，采集关键词: {', '.join(keywords)}"

        # 创建Agent
        agent = XiaohongshuAIAgent(config)

        task_status["progress"] = "Agent初始化完成，开始执行任务..."

        # 执行任务
        result = agent.run(keywords)

        task_status["progress"] = "任务执行完成，正在生成报告..."
        task_status["result"] = result
        task_status["is_running"] = False

    except Exception as e:
        task_status["error"] = str(e)
        task_status["is_running"] = False
        print(f"[{datetime.now().isoformat()}] [ERROR] 任务执行失败: {str(e)}")


@app.route("/")
def index():
    """首页"""
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_task():
    """启动任务"""
    global task_status

    if task_status["is_running"]:
        return jsonify({"error": "任务正在运行中，请等待完成"}), 400

    # 获取关键词
    data = request.get_json()
    keywords = data.get("keywords", [])

    if not keywords:
        return jsonify({"error": "请输入至少一个关键词"}), 400

    # 重置状态
    task_status = {
        "is_running": True,
        "progress": "正在启动...",
        "result": None,
        "error": None
    }

    # 在后台线程中运行任务
    thread = threading.Thread(target=run_agent_task, args=(keywords,))
    thread.start()

    return jsonify({"message": "任务已启动"})


@app.route("/api/status")
def get_status():
    """获取任务状态"""
    return jsonify(task_status)


@app.route("/api/report")
def download_report():
    """下载报告"""
    global task_status

    if not task_status["result"]:
        return jsonify({"error": "暂无报告可下载"}), 404

    # 查找生成的报告文件
    output_dir = "data/outputs"
    report_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]

    if not report_files:
        return jsonify({"error": "未找到报告文件"}), 404

    # 返回最新的报告文件
    latest_report = max([os.path.join(output_dir, f) for f in report_files], key=os.path.getmtime)

    return send_file(latest_report, as_attachment=True)


@app.route("/api/data")
def download_data():
    """下载结构化数据"""
    output_dir = "data/outputs"
    data_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]

    if not data_files:
        return jsonify({"error": "未找到数据文件"}), 404

    latest_data = max([os.path.join(output_dir, f) for f in data_files], key=os.path.getmtime)

    return send_file(latest_data, as_attachment=True)


if __name__ == "__main__":
    # 创建templates目录
    if not os.path.exists("templates"):
        os.makedirs("templates")

    # 创建index.html模板
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书AI调研Agent - Web演示</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .input-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            color: #333;
            margin-bottom: 8px;
            font-weight: 500;
        }

        input[type="text"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }

        .hint {
            color: #999;
            font-size: 12px;
            margin-top: 5px;
        }

        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }

        button {
            flex: 1;
            padding: 14px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-primary:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }

        .btn-secondary:hover {
            background: #e0e0e0;
        }

        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
        }

        .status-card.active {
            display: block;
        }

        .status-title {
            color: #333;
            font-weight: 500;
            margin-bottom: 10px;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
            animation: progress-animation 2s ease-in-out infinite;
        }

        @keyframes progress-animation {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 0%; }
        }

        .progress-text {
            color: #666;
            font-size: 14px;
        }

        .result-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            display: none;
        }

        .result-card.active {
            display: block;
        }

        .result-title {
            color: #333;
            font-weight: 500;
            margin-bottom: 15px;
        }

        .result-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 12px;
        }

        .download-buttons {
            display: flex;
            gap: 10px;
        }

        .btn-download {
            flex: 1;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }

        .btn-download:hover {
            background: #5568d3;
        }

        .error-card {
            background: #ffe6e6;
            border: 1px solid #ffcccc;
            border-radius: 8px;
            padding: 15px;
            color: #cc0000;
            display: none;
            margin-bottom: 20px;
        }

        .error-card.active {
            display: block;
        }

        .footer {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .feature-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            color: #666;
        }

        .feature-icon {
            font-size: 24px;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 小红书AI调研Agent</h1>
        <p class="subtitle">基于AI Agent架构的智能调研系统 - 支持双模型校验</p>

        <div class="features">
            <div class="feature-item">
                <div class="feature-icon">🤖</div>
                <strong>AI Agent智能体</strong><br>
                自主决策、自动执行
            </div>
            <div class="feature-item">
                <div class="feature-icon">🔍</div>
                <strong>智能采集</strong><br>
                模拟真实用户行为
            </div>
            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <strong>双模型校验</strong><br>
                DeepSeek-V3 + Qwen3-Max
            </div>
        </div>

        <div class="input-group">
            <label for="keywords">输入调研关键词</label>
            <input type="text" id="keywords" placeholder="例如: 美妆, 护肤, 口红">
            <p class="hint">多个关键词用逗号分隔</p>
        </div>

        <div class="button-group">
            <button class="btn-primary" id="startBtn" onclick="startTask()">开始调研</button>
            <button class="btn-secondary" onclick="loadDemo()">查看演示</button>
        </div>

        <div class="error-card" id="errorCard"></div>

        <div class="status-card" id="statusCard">
            <div class="status-title">执行进度</div>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            <div class="progress-text" id="progressText">正在初始化...</div>
        </div>

        <div class="result-card" id="resultCard">
            <div class="result-title">调研结果</div>
            <div class="result-stats" id="resultStats"></div>
            <div class="download-buttons">
                <button class="btn-download" onclick="downloadReport()">📄 下载报告</button>
                <button class="btn-download" onclick="downloadData()">📊 下载数据</button>
            </div>
        </div>

        <div class="footer">
            <p>小红书AI调研Agent v1.0 | 基于AI Agent架构 | 支持阿里云百炼平台</p>
        </div>
    </div>

    <script>
        let statusInterval = null;

        function startTask() {
            const keywordsInput = document.getElementById('keywords');
            const keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(k => k);

            if (keywords.length === 0) {
                showError('请输入至少一个关键词');
                return;
            }

            // 禁用按钮
            document.getElementById('startBtn').disabled = true;
            document.getElementById('startBtn').textContent = '正在执行...';

            // 隐藏结果卡片
            document.getElementById('resultCard').classList.remove('active');
            document.getElementById('errorCard').classList.remove('active');

            // 显示状态卡片
            document.getElementById('statusCard').classList.add('active');

            // 发送请求
            fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keywords: keywords })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    resetButton();
                } else {
                    // 开始轮询状态
                    statusInterval = setInterval(checkStatus, 2000);
                }
            })
            .catch(error => {
                showError('启动任务失败: ' + error);
                resetButton();
            });
        }

        function checkStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('progressText').textContent = data.progress || '正在执行...';

                if (!data.is_running && data.result) {
                    // 任务完成
                    clearInterval(statusInterval);
                    showResult(data.result);
                    resetButton();
                } else if (!data.is_running && data.error) {
                    // 任务失败
                    clearInterval(statusInterval);
                    showError(data.error);
                    resetButton();
                }
            })
            .catch(error => {
                console.error('检查状态失败:', error);
            });
        }

        function showResult(result) {
            document.getElementById('statusCard').classList.remove('active');
            document.getElementById('resultCard').classList.add('active');

            const statsHtml = `
                <div class="stat-item">
                    <div class="stat-value">${result.data_summary.total_notes_collected}</div>
                    <div class="stat-label">采集笔记数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${result.model_info.base_model}</div>
                    <div class="stat-label">基座模型</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${result.model_info.validation_model}</div>
                    <div class="stat-label">校验模型</div>
                </div>
            `;

            document.getElementById('resultStats').innerHTML = statsHtml;
        }

        function showError(message) {
            const errorCard = document.getElementById('errorCard');
            errorCard.textContent = '错误: ' + message;
            errorCard.classList.add('active');
        }

        function resetButton() {
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').textContent = '开始调研';
        }

        function downloadReport() {
            window.location.href = '/api/report';
        }

        function downloadData() {
            window.location.href = '/api/data';
        }

        function loadDemo() {
            alert('演示模式: 将加载示例报告\\n\\n实际使用时，请配置API密钥后运行。');
        }
    </script>
</body>
</html>"""

    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Web演示界面已创建")
    print("启动命令: python web_app.py")
    print("访问地址: <ADDRESS_REMOVED>

    app.run(debug=True, host="0.0.0.0", port=5000)
