"""
小红书AI调研Agent - Python包初始化文件
"""

__version__ = "1.0.0"
__author__ = "AI Agent"
__description__ = "基于AI Agent的小红书内容自主调研系统"

# 导出核心类
from agent.core import XiaohongshuAIAgent
from browser.playwright_handler import PlaywrightBrowserController
from ai.content_analyzer import ContentAnalyzer
from data.data_manager import DataManager

__all__ = [
    "XiaohongshuAIAgent",
    "PlaywrightBrowserController",
    "ContentAnalyzer",
    "DataManager"
]
