"""
浏览器自动化控制器 - 使用Playwright模拟真实用户行为
严格遵守合规要求：仅访问公开内容，模拟人类操作，低频访问
"""

import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime


class PlaywrightBrowserController:
    """基于Playwright的浏览器控制器 - 模拟真实用户行为"""

    def __init__(self, config: Dict):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.base_url = "https://www.xiaohongshu.com"
        self.search_url = "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"

        # 人类行为模拟配置 - 优化速度
        self.min_delay = config.get("min_delay", 1)  # 从2改为1秒
        self.max_delay = config.get("max_delay", 2)  # 从5改为2秒
        self.max_scroll_attempts = config.get("max_scroll_attempts", 10)
        self.max_pages = config.get("max_pages", 5)  # 最多翻页数
        self.fast_mode = config.get("fast_mode", True)  # 快速模式开关

        # 用户代理列表（模拟不同设备）
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]

    def initialize(self):
        """初始化浏览器"""
        try:
            from playwright.sync_api import sync_playwright

            self.playwright = sync_playwright().start()

            # 启动浏览器（使用headless=False可以看到操作过程，调试时有用）
            self.browser = self.playwright.chromium.launch(
                headless=self.config.get("headless", False),
                slow_mo=50  # 减慢操作速度，更像人类
            )

            # 创建浏览器上下文（模拟真实用户环境）
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.user_agents),
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )

            # 添加人类行为模拟的初始化脚本
            self.context.add_init_script("""
                // 覆盖navigator属性，使其更像是真实浏览器
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 添加一些随机的浏览器插件信息
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)

            self.page = self.context.new_page()

            print(f"[{datetime.now().isoformat()}] [INFO] 浏览器初始化成功")
            return True

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 浏览器初始化失败: {str(e)}")
            return False

    def _random_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        """随机延迟 - 模拟人类思考时间（支持快速模式）"""
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay

        # 快速模式：减少延时
        if self.fast_mode:
            min_d = min_d * 0.5
            max_d = max_d * 0.5

        delay = random.uniform(min_d, max_d)
        time.sleep(delay)

    def _simulate_human_scroll(self, scroll_distance: int = None):
        """模拟人类滚动行为"""
        if not scroll_distance:
            scroll_distance = random.randint(300, 800)

        # 分多次小滚动，而不是一次滚到底
        steps = random.randint(3, 8)
        step_distance = scroll_distance // steps

        for _ in range(steps):
            self.page.evaluate(f"window.scrollBy(0, {step_distance})")
            self._random_delay(0.1, 0.3)  # 短延迟 between scrolls

    def _simulate_mouse_movement(self, x: int, y: int):
        """模拟鼠标移动"""
        # 分多步移动鼠标，形成曲线
        steps = random.randint(5, 15)
        current_x, current_y = 0, 0

        for i in range(steps):
            # 添加一些随机偏移，使移动更自然
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)

            new_x = int(x * (i + 1) / steps) + offset_x
            new_y = int(y * (i + 1) / steps) + offset_y

            self.page.mouse.move(new_x, new_y)
            time.sleep(random.uniform(0.01, 0.05))

    def search(self, keyword: str, memory: Any) -> Dict:
        """
        搜索关键词 - 模拟真实用户搜索行为
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始搜索关键词: {keyword}")

        try:
            # 检查URL是否已访问
            search_url = self.search_url.format(keyword=keyword)
            if hasattr(memory, 'is_visited') and memory.is_visited(search_url):
                print(f"[{datetime.now().isoformat()}] [WARN] URL已访问过: {search_url}")
                return {"status": "already_visited", "url": search_url}

            # 访问搜索页面 - 优化加载策略
            print(f"[{datetime.now().isoformat()}] [INFO] 访问搜索页面: {search_url}")
            # 使用较短超时，快速失败
            self.page.goto(search_url, timeout=20000, wait_until='domcontentloaded')

            # 快速模式：减少等待时间
            if self.fast_mode:
                self._random_delay(1, 2)
            else:
                self._random_delay(3, 6)

            # 模拟滚动浏览搜索结果 - 快速模式减少滚动
            if self.fast_mode:
                self._simulate_human_scroll(300)
                self._random_delay(0.5, 1)
            else:
                self._simulate_human_scroll(500)
                self._random_delay(2, 4)

            # 记录已访问
            if hasattr(memory, 'add_visited_url'):
                memory.add_visited_url(search_url)

            # 提取搜索结果
            search_results = self._extract_search_results()

            print(f"[{datetime.now().isoformat()}] [INFO] 搜索完成，找到 {len(search_results)} 条结果")
            return {
                "status": "success",
                "keyword": keyword,
                "result_count": len(search_results),
                "results": search_results
            }

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 搜索失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _extract_search_results(self) -> List[Dict]:
        """提取搜索结果 - 仅采集公开可见内容"""
        results = []

        try:
            # 等待搜索结果加载
            self.page.wait_for_selector('section a[href*="/explore/"]', timeout=10000)

            # 提取笔记卡片信息
            note_cards = self.page.query_selector_all('section a[href*="/explore/"]')

            for card in note_cards[:20]:  # 限制采集数量，避免过于频繁
                try:
                    # 提取笔记链接
                    href = card.get_attribute('href')
                    if not href:
                        continue

                    note_url = href if href.startswith('http') else f"https://www.xiaohongshu.com{href}"

                    # 提取封面图片alt文本（通常是标题）
                    img_elem = card.query_selector('img')
                    title = img_elem.get_attribute('alt') if img_elem else ""

                    # 提取作者信息（如果有）
                    author_elem = card.query_selector('.author-name')
                    author = author_elem.inner_text() if author_elem else ""

                    results.append({
                        "note_url": note_url,
                        "title": title,
                        "author": author,
                        "collected_at": datetime.now().isoformat()
                    })

                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [WARN] 提取单个搜索结果失败: {str(e)}")
                    continue

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 提取搜索结果失败: {str(e)}")

        return results

    def browse_feed(self, memory: Any) -> Dict:
        """
        浏览推荐流 - 模拟用户刷首页行为
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始浏览推荐流")

        try:
            # 访问首页
            self.page.goto(self.base_url, timeout=30000, wait_until='domcontentloaded')
            self._random_delay(3, 5)

            # 模拟用户滚动浏览
            for i in range(random.randint(3, 6)):
                self._simulate_human_scroll(random.randint(400, 900))
                self._random_delay(2, 4)

                # 随机点击某个笔记（模拟用户兴趣）
                if random.random() < 0.3:  # 30%概率点击
                    self._random_click_note()
                    self._random_delay(5, 10)
                    self._go_back()

            return {"status": "success", "action": "browse_feed"}

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 浏览推荐流失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _random_click_note(self):
        """随机点击一个笔记"""
        try:
            note_links = self.page.query_selector_all('a[href*="/explore/"]')
            if note_links:
                random_link = random.choice(note_links)
                self._simulate_mouse_movement(
                    random.randint(100, 500),
                    random.randint(100, 500)
                )
                random_link.click()
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [WARN] 随机点击笔记失败: {str(e)}")

    def _go_back(self):
        """返回上一页"""
        self.page.go_back()
        self._random_delay(2, 4)

    def collect_current_page(self, memory: Any) -> Dict:
        """
        采集当前页面的笔记内容 - 仅采集公开可见信息
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始采集当前页面内容")

        try:
            # 判断当前页面类型
            current_url = self.page.url

            if "/explore/" in current_url:
                # 笔记详情页
                return self._collect_note_detail()
            elif "search_result" in current_url:
                # 搜索结果页
                return self._collect_search_page()
            else:
                # 其他页面
                return self._collect_generic_page()

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 采集当前页面失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _collect_note_detail(self) -> Dict:
        """采集笔记详情页内容 - 优化速度"""
        note_data = {
            "url": self.page.url,
            "collected_at": datetime.now().isoformat()
        }

        try:
            # 快速模式：减少等待时间
            if self.fast_mode:
                self._random_delay(1, 2)
            else:
                self._random_delay(2, 4)

            # 使用更高效的选择器 - 一次性提取所有数据
            note_data = {**note_data, **self._extract_note_data_fast()}

            print(f"[{datetime.now().isoformat()}] [INFO] 采集笔记成功: {note_data.get('title', '未知标题')[:30]}...")

            return {
                "status": "success",
                "data_type": "note_detail",
                "data": note_data
            }

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 采集笔记详情失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _extract_note_data_fast(self) -> Dict:
        """快速提取笔记数据 - 使用JavaScript一次性提取"""
        # 使用JavaScript一次性提取所有数据，比逐个查询快
        js_script = """
        () => {
            const data = {};
            
            // 提取标题
            const titleElem = document.querySelector('h1, .title, [class*="title"]');
            data.title = titleElem ? titleElem.innerText : '';
            
            // 提取作者
            const authorElem = document.querySelector('.author, [class*="author"]');
            data.author = authorElem ? authorElem.innerText : '';
            
            // 提取内容
            const contentElem = document.querySelector('.content, [class*="content"], .desc, article');
            data.content = contentElem ? contentElem.innerText : '';
            
            // 提取标签
            const tagElems = document.querySelectorAll('.tag, [class*="tag"]');
            data.tags = Array.from(tagElems).map(t => t.innerText);
            
            // 提取互动数据
            const likeElem = document.querySelector('.like, [class*="like"]');
            data.likes = likeElem ? likeElem.innerText : '0';
            
            const commentElem = document.querySelector('.comment, [class*="comment"]');
            data.comments = commentElem ? commentElem.innerText : '0';
            
            const collectElem = document.querySelector('.collect, [class*="collect"]');
            data.collects = collectElem ? collectElem.innerText : '0';
            
            // 提取发布时间
            const timeElem = document.querySelector('.time, [class*="time"], time');
            data.publish_time = timeElem ? timeElem.innerText : '';
            
            return data;
        }
        """

        return self.page.evaluate(js_script)

    def _collect_search_page(self) -> Dict:
        """采集搜索结果页面"""
        results = self._extract_search_results()
        return {
            "status": "success",
            "data_type": "search_results",
            "data": results
        }

    def _collect_generic_page(self) -> Dict:
        """采集通用页面"""
        return {
            "status": "success",
            "data_type": "generic",
            "url": self.page.url,
            "title": self.page.title()
        }

    def click_and_collect_note(self, note_url: str, memory: Any) -> Dict:
        """
        点击并采集特定笔记
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始采集笔记: {note_url}")

        try:
            # 检查是否已访问
            if hasattr(memory, 'is_visited') and memory.is_visited(note_url):
                print(f"[{datetime.now().isoformat()}] [WARN] 笔记已采集过: {note_url}")
                return {"status": "already_collected", "url": note_url}

            # 访问笔记页面
            self.page.goto(note_url, timeout=30000, wait_until='domcontentloaded')
            self._random_delay(3, 6)

            # 采集笔记内容
            note_data = self._collect_note_detail()

            # 记录已访问
            if hasattr(memory, 'add_visited_url'):
                memory.add_visited_url(note_url)

            # 模拟阅读行为：滚动查看完整内容
            self._simulate_human_scroll(1000)
            self._random_delay(3, 5)

            return note_data

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 采集笔记失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def close(self):
        """关闭浏览器"""
        print(f"[{datetime.now().isoformat()}] [INFO] 关闭浏览器")
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 关闭浏览器失败: {str(e)}")


if __name__ == "__main__":
    # 测试代码
    config = {
        "headless": False,
        "min_delay": 2,
        "max_delay": 5
    }

    controller = PlaywrightBrowserController(config)
    if controller.initialize():
        print("浏览器初始化成功，开始测试...")
        # 这里可以添加测试代码
        controller.close()
