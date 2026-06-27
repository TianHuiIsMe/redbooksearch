"""
小红书AI调研Agent - 主程序入口
支持命令行参数、配置文件、完整日志记录
"""

import json
import argparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """加载配置文件"""
    default_config = {
        "agent": {
            "name": "XiaohongshuAIAgent",
            "version": "1.0.0",
            "memory_size": 100
        },
        "browser": {
            "headless": False,  # 设为True可在后台运行
            "min_delay": 2,
            "max_delay": 5,
            "max_scroll_attempts": 10,
            "max_pages": 5
        },
        "ai": {
            "model_provider": "openai",  # openai, azure, local
            "model_name": "gpt-3.5-turbo",
            "api_key": "",  # 请配置您的API密钥
            "api_base": "",  # 可选：自定义API地址
            "max_tokens": 2000,
            "temperature": 0.3
        },
        "data": {
            "output_dir": "data/outputs",
            "raw_dir": "data/raw",
            "processed_dir": "data/processed"
        },
        "execution": {
            "max_notes_per_keyword": 20,
            "enable_dedup": True,
            "save_intermediate_results": True
        }
    }

    # 如果提供了配置文件路径，则加载
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并配置
                for key in user_config:
                    if key in default_config:
                        default_config[key].update(user_config[key])
                    else:
                        default_config[key] = user_config[key]
            print(f"[{datetime.now().isoformat()}] [INFO] 已加载配置文件: {config_path}")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [WARN] 加载配置文件失败: {str(e)}")
            print(f"[{datetime.now().isoformat()}] [INFO] 使用默认配置")

    return default_config


def setup_directories(config: Dict):
    """创建必要的目录"""
    dirs = [
        config["data"]["output_dir"],
        config["data"]["raw_dir"],
        config["data"]["processed_dir"],
        "logs",
        "docs"
    ]

    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

    print(f"[{datetime.now().isoformat()}] [INFO] 目录结构已创建")


def save_results(result: Dict, config: Dict, keywords: List[str]):
    """保存结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = config["data"]["output_dir"]

    # 1. 保存结构化数据（JSON）
    json_file = os.path.join(output_dir, f"xiaohongshu_data_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now().isoformat()}] [INFO] 结构化数据已保存: {json_file}")

    # 2. 保存分析报告（Markdown）
    if "report" in result:
        md_file = os.path.join(output_dir, f"xiaohongshu_report_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(result["report"])
        print(f"[{datetime.now().isoformat()}] [INFO] 分析报告已保存: {md_file}")

    # 3. 保存执行日志
    if "execution_logs" in result:
        log_file = os.path.join("logs", f"execution_log_{timestamp}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result["execution_logs"], f, ensure_ascii=False, indent=2)
        print(f"[{datetime.now().isoformat()}] [INFO] 执行日志已保存: {log_file}")

    return {
        "json_file": json_file,
        "md_file": md_file if "report" in result else None,
        "log_file": log_file if "execution_logs" in result else None
    }


def print_banner():
    """打印欢迎信息"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                  小红书AI调研Agent v1.0.0                      ║
║                  ----------------------                          ║
║          基于AI Agent的自主调研系统                              ║
║          支持任务拆解、智能采集、AI分析、自动报告                  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_keywords(keywords: List[str]) -> bool:
    """验证关键词"""
    if not keywords:
        print("[ERROR] 请提供至少一个关键词")
        return False

    if len(keywords) > 10:
        print("[WARN] 关键词数量过多（>10），建议分批执行")

    for keyword in keywords:
        if len(keyword) < 2:
            print(f"[WARN] 关键词'{keyword}'过短，可能影响搜索效果")

    return True


def main():
    """主函数"""
    print_banner()

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="小红书AI调研Agent - 自主调研系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py -k "美妆" "护肤" -c config.json
  python main.py --keywords "旅行" "美食" --headless
  python main.py -k "穿搭" --max-notes 50
        """
    )

    parser.add_argument(
        '-k', '--keywords',
        nargs='+',
        required=True,
        help='调研关键词（可多个）'
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        help='配置文件路径（JSON格式）'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='无头模式运行（不显示浏览器窗口）'
    )

    parser.add_argument(
        '--max-notes',
        type=int,
        default=20,
        help='每个关键词最多采集笔记数（默认20）'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出目录'
    )

    args = parser.parse_args()

    # 验证关键词
    if not validate_keywords(args.keywords):
        sys.exit(1)

    # 加载配置
    config = load_config(args.config)

    # 应用命令行参数
    if args.headless:
        config["browser"]["headless"] = True
    if args.max_notes:
        config["execution"]["max_notes_per_keyword"] = args.max_notes
    if args.output:
        config["data"]["output_dir"] = args.output

    # 创建目录
    setup_directories(config)

    # 打印执行信息
    print(f"[{datetime.now().isoformat()}] [INFO] 执行信息:")
    print(f"  关键词: {args.keywords}")
    print(f"  无头模式: {config['browser']['headless']}")
    print(f"  每关键词最多采集: {config['execution']['max_notes_per_keyword']} 条")
    print(f"  输出目录: {config['data']['output_dir']}")
    print()

    # 初始化并运行Agent
    print(f"[{datetime.now().isoformat()}] [INFO] 开始初始化AI Agent...")
    print("-" * 60)

    try:
        # 导入Agent核心模块
        from agent.core import XiaohongshuAIAgent

        # 创建Agent实例
        agent = XiaohongshuAIAgent(config)

        # 初始化（启动浏览器、加载AI模型等）
        agent.initialize()

        # 构造用户需求
        user_requirement = f"调研小红书平台关于{', '.join(args.keywords)}的内容，采集公开笔记并进行智能分析"

        # 运行Agent
        print(f"[{datetime.now().isoformat()}] [INFO] Agent开始执行...")
        print("=" * 60)
        result = agent.run(user_requirement, args.keywords)
        print("=" * 60)

        # 生成报告
        print(f"[{datetime.now().isoformat()}] [INFO] 生成最终报告...")
        report = agent.ai_analyzer.generate_report(agent.memory)

        # 合并结果
        final_result = {
            "status": "success",
            "user_requirement": user_requirement,
            "keywords": args.keywords,
            "execution_result": result,
            "report": report.get("summary", ""),
            "structured_data": report.get("structured_data", []),
            "statistics": report.get("statistics", {}),
            "recommendations": report.get("recommendations", []),
            "execution_logs": agent.get_execution_log()
        }

        # 保存结果
        print(f"[{datetime.now().isoformat()}] [INFO] 保存结果...")
        saved_files = save_results(final_result, config, args.keywords)

        # 打印完成信息
        print()
        print("=" * 60)
        print(f"[{datetime.now().isoformat()}] [INFO] ✅ 执行完成！")
        print(f"  采集笔记数: {result.get('collected_data_count', 0)}")
        print(f"  执行决策数: {len(result.get('decision_log', []))}")
        print(f"  遇到错误数: {len(result.get('errors', []))}")
        print()
        print("  输出文件:")
        for file_type, file_path in saved_files.items():
            if file_path:
                print(f"    - {file_type}: {file_path}")
        print("=" * 60)

        # 清理资源
        agent.cleanup()

        return final_result

    except KeyboardInterrupt:
        print(f"\n[{datetime.now().isoformat()}] [WARN] 用户中断执行")
        sys.exit(0)

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] [ERROR] 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
