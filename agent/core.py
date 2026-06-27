"""
AI Agent 核心模块 - 实现感知-思考-决策-执行闭环
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    ERROR = "error"
    COMPLETED = "completed"


class Task:
    """任务对象"""

    def __init__(self, task_id: str, description: str, priority: int = 1):
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result = None
        self.subtasks: List['Task'] = []
        self.created_at = datetime.now()
        self.completed_at = None

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "result": self.result,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class Memory:
    """短期记忆系统"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.visited_urls = set()
        self.collected_data = []
        self.errors = []
        self.decision_log = []

    def add_visited_url(self, url: str):
        self.visited_urls.add(url)

    def is_visited(self, url: str) -> bool:
        return url in self.visited_urls

    def add_data(self, data: Dict):
        self.collected_data.append({
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    def add_error(self, error: str, context: Dict = None):
        self.errors.append({
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })

    def log_decision(self, decision: str, reasoning: str):
        self.decision_log.append({
            "decision": decision,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })

    def get_recent_decisions(self, n: int = 10) -> List[Dict]:
        return self.decision_log[-n:]

    def clear(self):
        """清理记忆（用于新任务）"""
        self.visited_urls.clear()
        self.collected_data.clear()
        self.errors.clear()
        self.decision_log.clear()


class Planner:
    """任务规划器 - 将自然语言需求拆解为可执行步骤"""

    def __init__(self):
        self.task_templates = {
            "search_and_collect": [
                "分析关键词'{keyword}'的搜索策略",
                "在小红书搜索'{keyword}'相关内容",
                "浏览搜索结果列表",
                "点击进入笔记详情页",
                "采集笔记内容、作者、互动数据",
                "判断是否继续浏览（翻页或新的相关推荐）",
                "重复步骤3-6直到满足采集数量或达到时间限制",
                "对采集的数据进行清洗和去重",
                "使用AI分析内容特征",
                "生成结构化数据和报告"
            ]
        }

    def decompose_task(self, user_requirement: str, keywords: List[str]) -> Task:
        """
        将用户需求拆解为任务树
        """
        main_task = Task(
            task_id="main_task",
            description=user_requirement,
            priority=1
        )

        # 基于关键词生成子任务
        for idx, keyword in enumerate(keywords, 1):
            keyword_task = Task(
                task_id=f"keyword_{idx}",
                description=f"调研关键词: {keyword}",
                priority=idx
            )

            # 添加子任务步骤
            steps = self.task_templates["search_and_collect"].copy()
            for step_idx, step_desc in enumerate(steps, 1):
                step_desc = step_desc.replace("{keyword}", keyword)
                subtask = Task(
                    task_id=f"keyword_{idx}_step_{step_idx}",
                    description=step_desc,
                    priority=step_idx
                )
                keyword_task.subtasks.append(subtask)

            main_task.subtasks.append(keyword_task)

        return main_task


class Executor:
    """执行器 - 执行具体行动"""

    def __init__(self, browser_controller, ai_analyzer):
        self.browser = browser_controller
        self.ai = ai_analyzer
        self.current_task = None

    def execute_task(self, task: Task, memory: Memory) -> Any:
        """执行任务"""
        self.current_task = task
        task.status = "in_progress"

        try:
            # 根据任务类型执行不同操作
            if "搜索" in task.description or "search" in task.description.lower():
                result = self._execute_search(task, memory)
            elif "浏览" in task.description or "browse" in task.description.lower():
                result = self._execute_browse(task, memory)
            elif "采集" in task.description or "collect" in task.description.lower():
                result = self._execute_collect(task, memory)
            elif "分析" in task.description or "analyze" in task.description.lower():
                result = self._execute_analyze(task, memory)
            elif "生成" in task.description or "generate" in task.description.lower():
                result = self._execute_generate(task, memory)
            else:
                result = self._execute_generic(task, memory)

            task.status = "completed"
            task.result = result
            return result

        except Exception as e:
            task.status = "failed"
            memory.add_error(str(e), {"task": task.to_dict()})
            raise

    def _execute_search(self, task: Task, memory: Memory) -> Dict:
        """执行搜索任务"""
        # 从任务描述中提取关键词
        keyword = task.description.split(":")[-1].strip() if ":" in task.description else "未知关键词"

        memory.log_decision(
            f"执行搜索任务",
            f"关键词: {keyword}, 任务ID: {task.task_id}"
        )

        # 调用浏览器进行搜索
        search_result = self.browser.search(keyword, memory)

        return {
            "action": "search",
            "keyword": keyword,
            "result": search_result
        }

    def _execute_browse(self, task: Task, memory: Memory) -> Dict:
        """执行浏览任务"""
        memory.log_decision(
            "执行浏览任务",
            f"任务ID: {task.task_id}"
        )

        browse_result = self.browser.browse_feed(memory)

        return {
            "action": "browse",
            "result": browse_result
        }

    def _execute_collect(self, task: Task, memory: Memory) -> Dict:
        """执行采集任务"""
        memory.log_decision(
            "执行数据采集任务",
            f"任务ID: {task.task_id}"
        )

        collect_result = self.browser.collect_current_page(memory)

        return {
            "action": "collect",
            "result": collect_result
        }

    def _execute_analyze(self, task: Task, memory: Memory) -> Dict:
        """执行分析任务"""
        memory.log_decision(
            "执行AI内容分析",
            f"待分析数据量: {len(memory.collected_data)}"
        )

        # 使用AI分析采集的数据
        analysis_result = self.ai.analyze_content(
            [item["data"] for item in memory.collected_data],
            memory
        )

        return {
            "action": "analyze",
            "result": analysis_result
        }

    def _execute_generate(self, task: Task, memory: Memory) -> Dict:
        """执行生成报告任务"""
        memory.log_decision(
            "生成最终报告",
            "整合所有采集和分析结果"
        )

        # 生成结构化数据和报告
        output = self.ai.generate_report(memory)

        return {
            "action": "generate",
            "result": output
        }

    def _execute_generic(self, task: Task, memory: Memory) -> Dict:
        """执行通用任务"""
        memory.log_decision(
            f"执行通用任务: {task.description}",
            f"任务ID: {task.task_id}"
        )

        return {
            "action": "generic",
            "description": task.description,
            "status": "executed"
        }


class Reflector:
    """反思器 - 评估执行结果，决定下一步行动"""

    def __init__(self):
        self.reflection_history = []

    def reflect(self, task: Task, execution_result: Any, memory: Memory) -> Dict:
        """
        反思执行结果，返回下一步行动建议
        """
        reflection = {
            "task_id": task.task_id,
            "execution_status": task.status,
            "has_error": task.status == "failed",
            "next_action": "continue",  # continue, retry, skip, terminate
            "reasoning": ""
        }

        # 判断是否需要重试
        if task.status == "failed":
            reflection["next_action"] = "retry"
            reflection["reasoning"] = f"任务执行失败，建议重试。错误: {memory.errors[-1] if memory.errors else '未知错误'}"
        elif task.status == "completed":
            reflection["next_action"] = "continue"
            reflection["reasoning"] = "任务成功完成，继续下一步"

        # 检查是否达到采集目标
        if len(memory.collected_data) > 0:
            reflection["data_collected"] = True

        self.reflection_history.append({
            "reflection": reflection,
            "timestamp": datetime.now().isoformat()
        })

        memory.log_decision(
            f"反思结果: {reflection['next_action']}",
            reflection["reasoning"]
        )

        return reflection


class XiaohongshuAIAgent:
    """小红书AI调研Agent - 主控制器"""

    def __init__(self, config: Dict):
        self.config = config
        self.state = AgentState.IDLE
        self.memory = Memory(max_size=config.get("memory_size", 100))
        self.planner = Planner()
        self.browser = None  # 将在initialize中设置
        self.ai_analyzer = None  # 将在initialize中设置
        self.executor = None  # 将在initialize中设置
        self.reflector = Reflector()
        self.task_queue: List[Task] = []
        self.current_task: Optional[Task] = None
        self.logs = []
        self.log_callback = None  # 日志回调函数，用于实时推送日志

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

    def initialize(self):
        """初始化Agent"""
        self._log("Agent初始化开始", "info")

        # 导入并初始化浏览器控制器
        from browser.playwright_handler import PlaywrightBrowserController
        self.browser = PlaywrightBrowserController(self.config.get("browser", {}))

        # 导入并初始化AI分析器
        from ai.content_analyzer import ContentAnalyzer
        self.ai_analyzer = ContentAnalyzer(self.config.get("ai", {}))

        # 初始化执行器
        self.executor = Executor(self.browser, self.ai_analyzer)

        self.state = AgentState.PLANNING
        self._log("Agent初始化完成", "info")

    def run(self, user_requirement: str, keywords: List[str]) -> Dict:
        """
        运行Agent的主入口
        """
        self._log(f"开始执行任务: {user_requirement}", "info")
        self._log(f"关键词: {keywords}", "info")

        try:
            # 1. 规划阶段
            self.state = AgentState.PLANNING
            self._log("=== 阶段1: 任务规划 ===", "info")
            main_task = self.planner.decompose_task(user_requirement, keywords)
            self.task_queue = self._flatten_tasks(main_task)

            # 2. 执行阶段
            self.state = AgentState.EXECUTING
            self._log("=== 阶段2: 任务执行 ===", "info")

            for task in self.task_queue:
                self.current_task = task
                self._log(f"开始执行任务: {task.description}", "info")

                # 执行任务
                try:
                    result = self.executor.execute_task(task, self.memory)

                    # 反思
                    self.state = AgentState.REFLECTING
                    reflection = self.reflector.reflect(task, result, self.memory)

                    self._log(f"任务完成: {task.description}", "info")
                    self._log(f"反思结果: {reflection['next_action']}", "debug")

                    # 根据反思结果决定下一步
                    if reflection["next_action"] == "retry":
                        self._log(f"重试任务: {task.description}", "warning")
                        result = self.executor.execute_task(task, self.memory)

                except Exception as e:
                    self._log(f"任务执行失败: {str(e)}", "error")
                    self.state = AgentState.ERROR
                    # 继续下一个任务，不中断整个流程

            # 3. 完成阶段
            self.state = AgentState.COMPLETED
            self._log("=== 阶段3: 生成结果 ===", "info")

            # 生成最终结果
            final_result = self._generate_final_result(main_task)

            self._log("Agent执行完成", "info")
            return final_result

        except Exception as e:
            self.state = AgentState.ERROR
            self._log(f"Agent执行出错: {str(e)}", "error")
            raise
        finally:
            self.cleanup()

    def _flatten_tasks(self, task: Task) -> List[Task]:
        """将任务树扁平化为执行队列"""
        flat_list = []

        if task.subtasks:
            for subtask in task.subtasks:
                flat_list.extend(self._flatten_tasks(subtask))
        else:
            flat_list.append(task)

        return flat_list

    def _generate_final_result(self, main_task: Task) -> Dict:
        """生成最终结果"""
        return {
            "status": "success",
            "main_task": main_task.to_dict(),
            "collected_data_count": len(self.memory.collected_data),
            "errors": self.memory.errors,
            "decision_log": self.memory.get_recent_decisions(50),
            "reflection_history": self.reflector.reflection_history,
            "execution_logs": self.logs
        }

    def _log(self, message: str, level: str = "info"):
        """记录日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "state": self.state.value if self.state else "unknown"
        }
        self.logs.append(log_entry)

        # 同时输出到控制台
        print(f"[{log_entry['timestamp']}] [{level.upper()}] [{self.state.value}] {message}")

        # 调用日志回调函数（用于实时推送）
        if self.log_callback:
            try:
                self.log_callback(log_entry)
            except Exception as e:
                print(f"[WARNING] 日志回调执行失败: {str(e)}")

    def cleanup(self):
        """清理资源"""
        self._log("开始清理资源", "info")

        if self.browser:
            self.browser.close()

        self._log("资源清理完成", "info")

    def get_execution_log(self) -> List[Dict]:
        """获取执行日志"""
        return self.logs

    def save_logs(self, filepath: str):
        """保存日志到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)
