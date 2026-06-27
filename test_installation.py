"""
测试安装脚本 - 验证所有依赖和模块是否正确安装
"""

import sys
import traceback
from datetime import datetime


def test_python_version():
    """测试Python版本"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 13:
        print(f"[{datetime.now().isoformat()}] [PASS] Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[{datetime.now().isoformat()}] [FAIL] Python版本过低: {version.major}.{version.minor}.{version.micro}")
        return False


def test_playwright():
    """测试Playwright安装"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        print(f"[{datetime.now().isoformat()}] [PASS] Playwright已安装")
        return True
    except ImportError as e:
        print(f"[{datetime.now().isoformat()}] [FAIL] Playwright未安装: {str(e)}")
        print(f"[{datetime.now().isoformat()}] [INFO] 请运行: pip install playwright && playwright install chromium")
        return False


def test_openai():
    """测试OpenAI SDK安装"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试OpenAI SDK...")
    try:
        import openai
        print(f"[{datetime.now().isoformat()}] [PASS] OpenAI SDK已安装 (版本: {openai.__version__})")
        return True
    except ImportError:
        print(f"[{datetime.now().isoformat()}] [WARN] OpenAI SDK未安装（可选，使用本地模型可跳过）")
        return True  # 非必须


def test_module_imports():
    """测试模块导入"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试模块导入...")

    tests = [
        ("agent.core", "Agent核心模块"),
        ("browser.playwright_handler", "浏览器控制器"),
        ("ai.content_analyzer", "AI内容分析器"),
        ("data.data_manager", "数据管理器"),
    ]

    all_passed = True
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"[{datetime.now().isoformat()}] [PASS] {description} ({module_name})")
        except ImportError as e:
            print(f"[{datetime.now().isoformat()}] [FAIL] {description} ({module_name}): {str(e)}")
            all_passed = False

    return all_passed


def test_config_file():
    """测试配置文件"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试配置文件...")
    try:
        import json
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"[{datetime.now().isoformat()}] [PASS] 配置文件加载成功")
            print(f"[{datetime.now().isoformat()}] [INFO] Agent名称: {config.get('agent', {}).get('name', 'Unknown')}")
            return True
    except FileNotFoundError:
        print(f"[{datetime.now().isoformat()}] [FAIL] 配置文件不存在: config/config.json")
        return False
    except json.JSONDecodeError as e:
        print(f"[{datetime.now().isoformat()}] [FAIL] 配置文件格式错误: {str(e)}")
        return False


def test_directories():
    """测试目录结构"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试目录结构...")
    import os

    required_dirs = [
        "agent",
        "browser",
        "ai",
        "data",
        "data/raw",
        "data/processed",
        "data/outputs",
        "config",
        "logs",
        "docs"
    ]

    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"[{datetime.now().isoformat()}] [PASS] 目录存在: {dir_path}")
        else:
            print(f"[{datetime.now().isoformat()}] [FAIL] 目录不存在: {dir_path}")
            all_exist = False

    return all_exist


def test_ai_agent_initialization():
    """测试AI Agent初始化（不实际启动浏览器）"""
    print(f"[{datetime.now().isoformat()}] [TEST] 测试AI Agent初始化...")

    try:
        # 导入Agent类
        from agent.core import XiaohongshuAIAgent

        # 创建配置
        config = {
            "agent": {"memory_size": 10},
            "browser": {"headless": True},
            "ai": {"model_provider": "local"}
        }

        # 创建Agent实例（不调用initialize）
        agent = XiaohongshuAIAgent(config)
        print(f"[{datetime.now().isoformat()}] [PASS] AI Agent实例化成功")
        print(f"[{datetime.now().isoformat()}] [INFO] Agent状态: {agent.state.value}")

        return True

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] [FAIL] AI Agent初始化失败: {str(e)}")
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print(f"[{datetime.now().isoformat()}] [INFO] 开始运行安装测试...")
    print("=" * 70)
    print()

    test_results = []

    # 运行测试
    tests = [
        ("Python版本", test_python_version),
        ("Playwright安装", test_playwright),
        ("OpenAI SDK安装", test_openai),
        ("模块导入", test_module_imports),
        ("配置文件", test_config_file),
        ("目录结构", test_directories),
        ("AI Agent初始化", test_ai_agent_initialization),
    ]

    for test_name, test_func in tests:
        print("-" * 70)
        result = test_func()
        test_results.append((test_name, result))
        print()
    # 汇总结果
    print("=" * 70)
    print(f"[{datetime.now().isoformat()}] [INFO] 测试汇总:")
    print("-" * 70)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}  {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"[{datetime.now().isoformat()}] [INFO] 总计: {passed + failed} 项, 通过: {passed} 项, 失败: {failed} 项")
    print("=" * 70)
    print()

    # 建议
    if failed > 0:
        print(f"[{datetime.now().isoformat()}] [INFO] 修复建议:")
        print("  1. 如果Playwright未安装，请运行: pip install playwright && playwright install chromium")
        print("  2. 如果模块导入失败，请检查是否在项目根目录运行测试")
        print("  3. 如果配置文件不存在，请复制 config/config.json.example 为 config/config.json")
        print()
        return False
    else:
        print(f"[{datetime.now().isoformat()}] [INFO] 所有测试通过！您可以开始使用小红书AI调研Agent了。")
        print()
        print(f"[{datetime.now().isoformat()}] [INFO] 快速开始:")
        print("  python main.py -k \"美妆\" \"护肤\"")
        print()
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
