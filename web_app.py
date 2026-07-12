# -*- coding: utf-8 -*-
"""
Web应用 - 小红书AI调研Agent
集成会员系统（爱发电支付）
"""

from flask import Flask, render_template, request, jsonify, send_file, Response, make_response
import os
import json
import threading
import uuid
from datetime import datetime
from queue import Queue
import time

app = Flask(__name__)
app.secret_key = "xiaohongshu_ai_agent_secret_2026"

# ========== 全局状态 ==========
task_status = {
    "is_running": False,
    "progress": "",
    "result": None,
    "error": None
}

log_queue = Queue()
all_logs = []

# ========== 会员系统初始化 ==========
from membership.membership_manager import MembershipManager
membership_mgr = MembershipManager()


def get_session_id():
    """从Cookie获取或创建session_id"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())[:16]
    return session_id


def set_session_cookie(response, session_id):
    """设置session cookie"""
    response.set_cookie("session_id", session_id, max_age=86400 * 365, httponly=True)


# ========== Agent任务相关 ==========

def run_agent_task(keywords, session_id):
    """在后台运行Agent任务"""
    global task_status, all_logs

    try:
        task_status["is_running"] = True
        task_status["progress"] = "正在初始化Agent..."

        all_logs = []

        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        if "browser" in config:
            config["browser"]["min_delay"] = 1
            config["browser"]["max_delay"] = 2
            config["browser"]["headless"] = True

        task_status["progress"] = "正在启动Agent，采集关键词: " + ", ".join(keywords)

        from agent.core import XiaohongshuAIAgent
        agent = XiaohongshuAIAgent(config)

        def log_callback(log_entry):
            all_logs.append(log_entry)
            log_queue.put(log_entry)

        agent.set_log_callback(log_callback)

        task_status["progress"] = "Agent初始化完成，开始执行任务..."

        user_requirement = "调研小红书平台关于" + ", ".join(keywords) + "的内容，采集公开笔记并进行智能分析"
        result = agent.run(user_requirement, keywords)

        if result.get("collected_data_count", 0) == 0:
            task_status["progress"] = "未采集到数据，使用AI生成模拟数据..."
            log_queue.put({
                "timestamp": datetime.now().isoformat(),
                "level": "warning",
                "message": "未采集到真实数据，使用AI生成模拟帖子数据",
                "state": "executing"
            })
            simulated_data = generate_simulated_posts(keywords, config)
            result["simulated_data"] = simulated_data
            result["data_source"] = "simulated"
            result["collected_data_count"] = len(simulated_data)
            log_queue.put({
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": "已生成 " + str(len(simulated_data)) + " 条模拟帖子",
                "state": "executing"
            })

        task_status["progress"] = "任务执行完成，正在生成报告..."
        task_status["result"] = result
        task_status["is_running"] = False

    except Exception as e:
        error_msg = str(e)
        task_status["error"] = error_msg
        task_status["is_running"] = False
        log_queue.put({
            "timestamp": datetime.now().isoformat(),
            "level": "error",
            "message": "任务执行失败: " + error_msg,
            "state": "error"
        })


def generate_simulated_posts(keywords, config):
    """使用AI生成模拟的小红书帖子"""
    try:
        from ai.content_analyzer import ContentAnalyzer
        ai_analyzer = ContentAnalyzer(config.get("ai", {}))

        simulated_posts = []
        for keyword in keywords:
            prompt = '请生成5条关于"' + keyword + '"的小红书风格帖子。要求标题吸引人，内容真实(200-400字)，包含emoji。返回严格JSON格式：{"posts":[{"title":"","content":"","author":"","likes":100,"comments":10,"collects":50,"tags":[],"publish_time":"2026-06-15"}]}。只返回JSON。'
            response = ai_analyzer._call_ai_model(prompt)

            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    posts = data.get("posts", [])
                    for post in posts:
                        post["keyword"] = keyword
                        post["is_simulated"] = True
                    simulated_posts.extend(posts)
                else:
                    simulated_posts.extend(generate_basic_simulated_data([keyword]))
            except:
                simulated_posts.extend(generate_basic_simulated_data([keyword]))

        return simulated_posts
    except Exception as e:
        print("[WARNING] AI生成模拟数据失败: " + str(e))
        return generate_basic_simulated_data(keywords)


def generate_basic_simulated_data(keywords):
    """生成基础模拟数据"""
    posts = []
    for keyword in keywords:
        for i in range(10):
            posts.append({
                "title": keyword + "体验分享 | 第" + str(i + 1) + "篇",
                "content": "今天和大家分享关于" + keyword + "的使用心得，真的很有帮助！推荐给大家。",
                "author": "小红书用户" + str(i + 1),
                "likes": 500 + i * 100,
                "comments": 50 + i * 10,
                "collects": 200 + i * 50,
                "tags": [keyword, "好物分享", "推荐"],
                "publish_time": "2026-06-10",
                "is_ad": i % 3 == 0
            })
    return posts


# ========== 页面路由 ==========

@app.route("/")
def index():
    """首页"""
    session_id = get_session_id()
    resp = make_response(render_template("index.html"))
    set_session_cookie(resp, session_id)
    return resp


# ========== 会员系统API ==========

@app.route("/api/membership/plans")
def get_plans():
    """获取会员方案列表"""
    plans = membership_mgr.get_plans()
    return jsonify({
        "success": True,
        "plans": plans,
        "afdian_profile": membership_mgr.afdian.profile_url
    })


@app.route("/api/membership/status")
def get_membership_status():
    """获取当前用户会员状态"""
    session_id = get_session_id()
    member_info = membership_mgr.get_member_info(session_id)
    return jsonify({
        "success": True,
        "session_id": session_id,
        "member_info": member_info
    })


@app.route("/api/membership/verify", methods=["POST"])
def verify_membership():
    """通过订单号验证会员"""
    session_id = get_session_id()
    data = request.get_json()
    order_no = data.get("order_no", "").strip()

    if not order_no:
        return jsonify({"success": False, "message": "请输入爱发电订单号"})

    result = membership_mgr.verify_order(session_id, order_no)

    resp = make_response(jsonify(result))
    set_session_cookie(resp, session_id)
    return resp


@app.route("/api/membership/purchase-url")
def get_purchase_url():
    """获取购买链接"""
    session_id = get_session_id()
    plan_id = request.args.get("plan_id", "")

    url = membership_mgr.get_purchase_url(plan_id, session_id)
    return jsonify({
        "success": True,
        "url": url,
        "session_id": session_id
    })


@app.route("/api/membership/check-permission")
def check_permission():
    """检查搜索权限"""
    session_id = get_session_id()
    result = membership_mgr.check_search_permission(session_id)
    resp = make_response(jsonify(result))
    set_session_cookie(resp, session_id)
    return resp


@app.route("/api/webhook/afdian", methods=["POST"])
def afdian_webhook():
    """爱发电Webhook回调"""
    try:
        data = request.get_json()
        print("[Webhook] 收到爱发电回调: " + json.dumps(data, ensure_ascii=False))

        result = membership_mgr.handle_webhook(data)
        return jsonify(result)
    except Exception as e:
        print("[Webhook] 处理失败: " + str(e))
        return jsonify({"ec": 200, "em": "ok"})


# ========== Agent任务API ==========

@app.route("/api/start", methods=["POST"])
def start_task():
    """启动调研任务（增加会员权限检查）"""
    global task_status
    session_id = get_session_id()

    # 检查会员权限
    permission = membership_mgr.check_search_permission(session_id)
    if not permission["allowed"]:
        return jsonify({
            "error": permission["reason"],
            "need_upgrade": True
        }), 403

    # 检查关键词数量限制
    data = request.get_json()
    keywords = data.get("keywords", [])
    member_info = permission.get("member_info", {})
    max_keywords = member_info.get("max_keywords", 1)

    if len(keywords) > max_keywords:
        return jsonify({
            "error": "当前会员等级最多支持" + str(max_keywords) + "个关键词，请升级会员",
            "need_upgrade": True,
            "current_limit": max_keywords
        }), 403

    if task_status["is_running"]:
        return jsonify({"error": "任务正在运行中，请等待完成"}), 400

    if not keywords:
        return jsonify({"error": "请输入至少一个关键词"}), 400

    task_status = {
        "is_running": True,
        "progress": "正在启动...",
        "result": None,
        "error": None
    }

    thread = threading.Thread(target=run_agent_task, args=(keywords, session_id))
    thread.start()

    resp = make_response(jsonify({"message": "任务已启动"}))
    set_session_cookie(resp, session_id)
    return resp


@app.route("/api/status")
def get_status():
    return jsonify(task_status)


@app.route("/api/logs")
def get_logs():
    """SSE端点 - 实时推送日志"""
    def generate():
        while True:
            try:
                log_entry = log_queue.get_nowait()
                yield "data: " + json.dumps(log_entry, ensure_ascii=False) + "\n\n"
            except:
                if task_status["is_running"]:
                    time.sleep(0.1)
                else:
                    yield "data: " + json.dumps({"type": "done"}, ensure_ascii=False) + "\n\n"
                    break

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/all_logs")
def get_all_logs():
    return jsonify(all_logs)


@app.route("/api/report")
def download_report():
    if not task_status["result"]:
        return jsonify({"error": "暂无报告可下载"}), 404
    output_dir = "data/outputs"
    if not os.path.exists(output_dir):
        return jsonify({"error": "输出目录不存在"}), 404
    report_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]
    if not report_files:
        return jsonify({"error": "未找到报告文件"}), 404
    latest_report = max([os.path.join(output_dir, f) for f in report_files], key=os.path.getmtime)
    return send_file(latest_report, as_attachment=True)


@app.route("/api/data")
def download_data():
    output_dir = "data/outputs"
    if not os.path.exists(output_dir):
        return jsonify({"error": "输出目录不存在"}), 404
    data_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    if not data_files:
        return jsonify({"error": "未找到数据文件"}), 404
    latest_data = max([os.path.join(output_dir, f) for f in data_files], key=os.path.getmtime)
    return send_file(latest_data, as_attachment=True)


if __name__ == "__main__":
    if not os.path.exists("templates"):
        os.makedirs("templates")
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("data/outputs"):
        os.makedirs("data/outputs")

    print("=" * 60)
    print("  小红书AI调研Agent v3.0")
    print("  集成会员系统（爱发电支付）")
    print("=" * 60)
    print()
    print("  会员方案:")
    for plan in membership_mgr.get_plans():
        tag = " [推荐]" if plan.get("highlight") else ""
        print("    - " + plan["name"] + ": " + str(plan["price"]) + "元/" + plan["period"] + tag)
    print()
    print("  爱发电主页: " + membership_mgr.afdian.profile_url)
    print("  API状态: " + ("已配置" if membership_mgr.afdian.user_id else "未配置(使用本地验证模式)"))
    print()
    print("  启动成功！访问: localhost:5000")
    print("=" * 60)

    app.run(debug=True, host="0.0.0.0", port=5000)
