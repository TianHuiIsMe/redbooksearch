"""
Web演示界面 - 使用Flask创建简单的Web应用
让用户可以通过浏览器输入关键词、查看进度、下载报告
支持实时日志推送（SSE）
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import os
import json
import threading
from datetime import datetime
from queue import Queue
import time

app = Flask(__name__)

# 全局变量存储任务状态
task_status = {
    "is_running": False,
    "progress": "",
    "result": None,
    "error": None
}

# 日志队列 - 用于存储实时日志
log_queue = Queue()
# 用于存储所有日志（供前端获取）
all_logs = []


def run_agent_task(keywords):
    """在后台运行Agent任务"""
    global task_status, all_logs

    try:
        task_status["is_running"] = True
        task_status["progress"] = "正在初始化Agent..."

        # 清空日志
        global all_logs
        all_logs = []

        # 加载配置
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        # 优化速度 - 减少延时
        if "browser" in config:
            config["browser"]["min_delay"] = 1  # 从2改为1
            config["browser"]["max_delay"] = 2  # 从5改为2
            config["browser"]["headless"] = True  # 使用无头模式提升速度

        task_status["progress"] = f"正在启动Agent，采集关键词: {', '.join(keywords)}"

        # 导入Agent
        from agent.core import XiaohongshuAIAgent

        # 创建Agent
        agent = XiaohongshuAIAgent(config)

        # 设置日志回调
        def log_callback(log_entry):
            """日志回调函数 - 将日志推送到队列"""
            global all_logs
            all_logs.append(log_entry)
            # 将日志放入队列
            log_queue.put(log_entry)

        agent.set_log_callback(log_callback)

        task_status["progress"] = "Agent初始化完成，开始执行任务..."

        # 构造用户需求
        user_requirement = f"调研小红书平台关于{', '.join(keywords)}的内容，采集公开笔记并进行智能分析"

        # 执行任务（需要传两个参数）
        result = agent.run(user_requirement, keywords)

        # 检查是否采集到数据
        if result.get("collected_data_count", 0) == 0:
            task_status["progress"] = "未采集到数据，使用AI生成模拟数据..."
            log_queue.put({
                "timestamp": datetime.now().isoformat(),
                "level": "warning",
                "message": "未采集到真实数据，使用AI生成模拟帖子数据",
                "state": "executing"
            })

            # 使用AI生成模拟数据
            simulated_data = generate_simulated_posts(keywords, config)
            result["simulated_data"] = simulated_data
            result["data_source"] = "simulated"
            result["collected_data_count"] = len(simulated_data)

            log_queue.put({
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": f"已生成 {len(simulated_data)} 条模拟帖子",
                "state": "executing"
            })

        task_status["progress"] = "任务执行完成，正在生成报告..."
        task_status["result"] = result
        task_status["is_running"] = False

    except Exception as e:
        error_msg = str(e)
        task_status["error"] = error_msg
        task_status["is_running"] = False
        print(f"[{datetime.now().isoformat()}] [ERROR] 任务执行失败: {error_msg}")

        # 推送错误日志
        log_queue.put({
            "timestamp": datetime.now().isoformat(),
            "level": "error",
            "message": f"任务执行失败: {error_msg}",
            "state": "error"
        })


def generate_simulated_posts(keywords, config):
    """使用AI生成模拟的小红书帖子"""
    try:
        from ai.content_analyzer import ContentAnalyzer

        # 初始化AI分析器
        ai_analyzer = ContentAnalyzer(config.get("ai", {}))

        simulated_posts = []
        for keyword in keywords:
            # 使用AI生成模拟帖子
            prompt = f"""
            请生成5条关于"{keyword}"的小红书风格帖子。

            要求：
            1. 标题要吸引人，符合小红书标题党风格（如"亲测有效！", "后悔没早点知道"等）
            2. 内容要真实，像普通用户的体验分享（200-400字）
            3. 包含emoji表情
            4. 符合小红书社区氛围

            返回严格的JSON格式，包含posts数组，每条帖子包含：
            - title: 标题
            - content: 内容
            - author: 作者昵称（真实感的中文昵称）
            - likes: 点赞数（100-5000的随机整数）
            - comments: 评论数（10-500的随机整数）
            - collects: 收藏数（50-2000的随机整数）
            - tags: 标签数组（3-5个标签）
            - publish_time: 发布时间（2026-06-01到2026-06-20之间的随机日期）

            只返回JSON，不要有其他文字。
            """

            # 调用AI生成
            response = ai_analyzer._call_ai_model(prompt)

            # 解析AI返回的JSON
            try:
                # 提取JSON（AI可能在JSON前后有额外文字）
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)
                    posts = data.get("posts", [])

                    # 添加到结果
                    for post in posts:
                        post["keyword"] = keyword
                        post["is_simulated"] = True

                    simulated_posts.extend(posts)
                else:
                    # JSON解析失败，使用基础模拟数据
                    simulated_posts.extend(generate_basic_simulated_data([keyword]))
            except Exception as parse_error:
                print(f"[WARNING] 解析AI生成的模拟数据失败: {str(parse_error)}")
                # 使用基础模拟数据
                simulated_posts.extend(generate_basic_simulated_data([keyword]))

        return simulated_posts

    except Exception as e:
        print(f"[WARNING] AI生成模拟数据失败: {str(e)}")
        # 返回基础的模拟数据
        return generate_basic_simulated_data(keywords)


def parse_ai_response(response, keyword):
    """解析AI生成的响应"""
    # 简化处理 - 实际应该解析JSON
    posts = []
    for i in range(5):
        posts.append({
            "title": f"{keyword}分享 | 亲测有效！第{i+1}次尝试",
            "content": f"大家好，今天想和大家分享一下关于{keyword}的心得体会。经过这段时间的试用，真的有很大的改善！\n\n首先，我要说的是...\n\n其次...\n\n最后总结一下，推荐给大家！",
            "author": f"用户{i+1}号",
            "likes": 1000 + i * 500,
            "comments": 100 + i * 50,
            "collects": 500 + i * 200,
            "tags": [keyword, "分享", "亲测"],
            "publish_time": "2026-06-15",
            "is_ad": False
        })
    return posts


def generate_basic_simulated_data(keywords):
    """生成基础的模拟数据（当AI生成失败时使用）"""
    posts = []
    for keyword in keywords:
        for i in range(10):
            posts.append({
                "title": f"{keyword}体验分享 | 第{i+1}篇",
                "content": f"今天和大家分享关于{keyword}的使用心得，真的很有帮助！推荐给大家。",
                "author": f"小红书用户{i+1}",
                "likes": 500 + i * 100,
                "comments": 50 + i * 10,
                "collects": 200 + i * 50,
                "tags": [keyword, "好物分享", "推荐"],
                "publish_time": "2026-06-10",
                "is_ad": i % 3 == 0  # 每3条有1条是广告
            })
    return posts


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


@app.route("/api/logs")
def get_logs():
    """SSE端点 - 实时推送日志"""
    def generate():
        """生成SSE事件流"""
        while True:
            # 从队列中获取日志
            try:
                # 非阻塞获取
                log_entry = log_queue.get_nowait()

                # 格式化为SSE事件
                yield f"data: {json.dumps(log_entry, ensure_ascii=False)}\n\n"
            except:
                # 队列为空
                # 如果任务还在运行，继续等待
                if task_status["is_running"]:
                    time.sleep(0.1)
                else:
                    # 任务已完成，发送结束信号
                    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                    break

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/all_logs")
def get_all_logs():
    """获取所有日志（用于页面刷新时恢复）"""
    global all_logs
    return jsonify(all_logs)


@app.route("/api/report")
def download_report():
    """下载报告"""
    global task_status

    if not task_status["result"]:
        return jsonify({"error": "暂无报告可下载"}), 404

    # 查找生成的报告文件
    output_dir = "data/outputs"
    if not os.path.exists(output_dir):
        return jsonify({"error": "输出目录不存在"}), 404

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
    if not os.path.exists(output_dir):
        return jsonify({"error": "输出目录不存在"}), 404

    data_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]

    if not data_files:
        return jsonify({"error": "未找到数据文件"}), 404

    latest_data = max([os.path.join(output_dir, f) for f in data_files], key=os.path.getmtime)

    return send_file(latest_data, as_attachment=True)


if __name__ == "__main__":
    # 创建templates目录
    if not os.path.exists("templates"):
        os.makedirs("templates")

    # 创建index.html模板（支持实时日志）
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
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 1200px;
            width: 100%;
            padding: 40px;
            margin: 0 auto;
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

        .logs-card {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
            max-height: 500px;
            overflow-y: auto;
        }

        .logs-card.active {
            display: block;
        }

        .logs-title {
            color: #fff;
            font-weight: 500;
            margin-bottom: 15px;
            font-size: 16px;
        }

        .log-entry {
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin-bottom: 8px;
            line-height: 1.4;
        }

        .log-timestamp {
            color: #888;
        }

        .log-level-info {
            color: #4fc3f7;
        }

        .log-level-warning {
            color: #ffb74d;
        }

        .log-level-error {
            color: #ef5350;
        }

        .log-level-debug {
            color: #a5d6a7;
        }

        .log-message {
            color: #e0e0e0;
        }

        .log-state {
            color: #ce93d8;
            font-size: 11px;
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

        .toggle-logs {
            background: #333;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 10px;
            font-size: 13px;
        }

        .toggle-logs:hover {
            background: #444;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 小红书AI调研Agent</h1>
        <p class="subtitle">基于AI Agent架构的智能调研系统 - 支持双模型校验 + 实时日志</p>

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
            <div class="feature-item">
                <div class="feature-icon">📊</div>
                <strong>实时日志</strong><br>
                执行过程透明可见
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

        <button class="toggle-logs" id="toggleLogsBtn" onclick="toggleLogs()" style="display: none;">显示执行日志</button>

        <div class="logs-card" id="logsCard">
            <div class="logs-title">执行日志</div>
            <div id="logsContent"></div>
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
            <p>小红书AI调研Agent v2.0 | 基于AI Agent架构 | 支持阿里云百炼平台 | 实时日志推送</p>
        </div>
    </div>

    <script>
        let statusInterval = null;
        let logsInterval = null;
        let eventSource = null;
        let logsVisible = false;

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

            // 清空日志
            document.getElementById('logsContent').innerHTML = '';

            // 显示状态卡片和日志按钮
            document.getElementById('statusCard').classList.add('active');
            document.getElementById('toggleLogsBtn').style.display = 'block';

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
                    // 开始接收实时日志
                    startReceivingLogs();

                    // 开始轮询状态
                    statusInterval = setInterval(checkStatus, 2000);
                }
            })
            .catch(error => {
                showError('启动任务失败: ' + error);
                resetButton();
            });
        }

        function startReceivingLogs() {
            // 使用SSE接收实时日志
            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource('/api/logs');

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.type === 'done') {
                    // 日志推送结束
                    eventSource.close();
                    return;
                }

                // 显示日志
                appendLog(data);
            };

            eventSource.onerror = function(error) {
                console.error('SSE连接错误:', error);
                eventSource.close();
            };
        }

        function appendLog(logEntry) {
            const logsContent = document.getElementById('logsContent');

            const logDiv = document.createElement('div');
            logDiv.className = 'log-entry';

            const timestamp = new Date(logEntry.timestamp).toLocaleTimeString();
            const levelClass = 'log-level-' + logEntry.level;

            logDiv.innerHTML = `
                <span class="log-timestamp">[${timestamp}]</span>
                <span class="${levelClass}"> [${logEntry.level.toUpperCase()}]</span>
                <span class="log-state"> [${logEntry.state}]</span>
                <span class="log-message"> ${logEntry.message}</span>
            `;

            logsContent.appendChild(logDiv);

            // 自动滚动到底部
            const logsCard = document.getElementById('logsCard');
            logsCard.scrollTop = logsCard.scrollHeight;
        }

        function toggleLogs() {
            const logsCard = document.getElementById('logsCard');
            const toggleBtn = document.getElementById('toggleLogsBtn');

            logsVisible = !logsVisible;

            if (logsVisible) {
                logsCard.classList.add('active');
                toggleBtn.textContent = '隐藏执行日志';
            } else {
                logsCard.classList.remove('active');
                toggleBtn.textContent = '显示执行日志';
            }
        }

        function checkStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('progressText').textContent = data.progress || '正在执行...';

                if (!data.is_running && data.result) {
                    // 任务完成
                    clearInterval(statusInterval);
                    if (eventSource) {
                        eventSource.close();
                    }
                    showResult(data.result);
                    resetButton();
                } else if (!data.is_running && data.error) {
                    // 任务失败
                    clearInterval(statusInterval);
                    if (eventSource) {
                        eventSource.close();
                    }
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

            const dataSummary = result.execution_result || result;
            const dataSource = result.data_source || 'real';

            let statsHtml = `
                <div class="stat-item">
                    <div class="stat-value">${dataSummary.collected_data_count || 0}</div>
                    <div class="stat-label">采集笔记数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${dataSource === 'simulated' ? '模拟' : '真实'}</div>
                    <div class="stat-label">数据来源</div>
                </div>
            `;

            if (result.model_info) {
                statsHtml += `
                    <div class="stat-item">
                        <div class="stat-value">${result.model_info.base_model || 'N/A'}</div>
                        <div class="stat-label">基座模型</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${result.model_info.validation_model || 'N/A'}</div>
                        <div class="stat-label">校验模型</div>
                    </div>
                `;
            }

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

    print("Web演示界面已创建（支持实时日志）")
    print("启动命令: python web_app.py")

    app.run(debug=True, host="0.0.0.0", port=5000)

