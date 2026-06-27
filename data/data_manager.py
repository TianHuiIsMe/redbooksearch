"""
数据存储管理器 - 负责数据的存储、去重、增量采集
支持多种存储格式（JSON、CSV、SQLite）
"""

import json
import csv
import os
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class DataManager:
    """数据管理器 - 统一数据存取接口"""

    def __init__(self, config: Dict):
        self.config = config
        self.raw_dir = config.get("raw_dir", "data/raw")
        self.processed_dir = config.get("processed_dir", "data/processed")
        self.output_dir = config.get("output_dir", "data/outputs")

        # 去重缓存
        self.content_hashes = set()
        self.load_dedup_cache()

    def load_dedup_cache(self):
        """加载去重缓存"""
        cache_file = os.path.join(self.processed_dir, ".dedup_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.content_hashes = set(cache_data.get("hashes", []))
                print(f"[{datetime.now().isoformat()}] [INFO] 已加载去重缓存: {len(self.content_hashes)} 条")
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] [WARN] 加载去重缓存失败: {str(e)}")

    def save_dedup_cache(self):
        """保存去重缓存"""
        cache_file = os.path.join(self.processed_dir, ".dedup_cache.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "hashes": list(self.content_hashes),
                    "updated_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] 保存去重缓存失败: {str(e)}")

    def _generate_hash(self, data: Dict) -> str:
        """生成数据唯一哈希"""
        # 使用标题+作者+内容生成哈希
        title = data.get("title", "")
        author = data.get("author", "")
        content = data.get("content", "")

        hash_str = f"{title}|{author}|{content}"
        return hashlib.md5(hash_str.encode('utf-8')).hexdigest()

    def is_duplicate(self, data: Dict) -> bool:
        """检查是否重复"""
        if not self.config.get("enable_dedup", True):
            return False

        data_hash = self._generate_hash(data)
        return data_hash in self.content_hashes

    def add_data(self, data: Dict, data_type: str = "raw"):
        """添加数据（自动去重）"""
        # 检查去重
        if self.is_duplicate(data):
            print(f"[{datetime.now().isoformat()}] [DEBUG] 检测到重复数据，跳过: {data.get('title', '')[:30]}")
            return False

        # 添加到缓存
        data_hash = self._generate_hash(data)
        self.content_hashes.add(data_hash)

        # 保存原始数据
        if data_type == "raw":
            self._save_raw_data(data)
        elif data_type == "processed":
            self._save_processed_data(data)

        return True

    def _save_raw_data(self, data: Dict):
        """保存原始数据"""
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"raw_{timestamp}.json"
        filepath = os.path.join(self.raw_dir, filename)

        # 追加模式保存
        existing_data = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = []

        existing_data.append({
            "data": data,
            "collected_at": datetime.now().isoformat()
        })

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    def _save_processed_data(self, data: Dict):
        """保存处理后的数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_{timestamp}.json"
        filepath = os.path.join(self.processed_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_structured_data(self, data: List[Dict], filename: str = None):
        """保存结构化数据（最终输出）"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"xiaohongshu_structured_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[{datetime.now().isoformat()}] [INFO] 结构化数据已保存: {filepath}")
        return filepath

    def save_to_csv(self, data: List[Dict], filename: str = None):
        """保存为CSV格式（方便Excel打开）"""
        if not data:
            print(f"[{datetime.now().isoformat()}] [WARN] 数据为空，不保存CSV")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"xiaohongshu_data_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        # 获取所有可能的字段
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())

        # 写入CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(data)

        print(f"[{datetime.now().isoformat()}] [INFO] CSV数据已保存: {filepath}")
        return filepath

    def load_historical_data(self, days: int = 7) -> List[Dict]:
        """加载历史数据（用于增量采集）"""
        historical_data = []

        # 遍历原始数据目录
        for filename in os.listdir(self.raw_dir):
            if not filename.startswith("raw_") or not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.raw_dir, filename)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    historical_data.extend(data)
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] [WARN] 加载历史数据失败 {filename}: {str(e)}")

        print(f"[{datetime.now().isoformat()}] [INFO] 已加载历史数据: {len(historical_data)} 条")
        return historical_data

    def export_analysis_report(self, analysis_result: Dict, filename: str = None):
        """导出分析报告（Markdown格式）"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"xiaohongshu_analysis_report_{timestamp}.md"

        filepath = os.path.join(self.output_dir, filename)

        # 生成Markdown报告
        md_content = self._generate_markdown_report(analysis_result)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"[{datetime.now().isoformat()}] [INFO] 分析报告已保存: {filepath}")
        return filepath

    def _generate_markdown_report(self, analysis_result: Dict) -> str:
        """生成Markdown格式报告"""
        md = f"""# 小红书AI调研分析报告

**生成时间**: {datetime.now().isoformat()}

---

## 📊 执行概况

- **采集笔记总数**: {analysis_result.get('total_notes', 0)}
- **内容分类统计**: {len(analysis_result.get('categories', {}))} 个类别
- **广告内容占比**: {analysis_result.get('ad_detection', {}).get('is_ad', 0) / max(analysis_result.get('total_notes', 1), 1) * 100:.1f}%
- **情感倾向**: {self._format_sentiment(analysis_result.get('sentiment', {}))}

---

## 📂 内容分类统计

"""

        # 分类统计
        categories = analysis_result.get('categories', {})
        if categories:
            md += "| 分类 | 数量 | 占比 |\n"
            md += "|------|------|------|\n"
            total = sum(categories.values())
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total * 100 if total > 0 else 0
                md += f"| {cat} | {count} | {percentage:.1f}% |\n"
        else:
            md += "暂无分类数据\n"

        md += "\n---\n\n## 🔍 关键词分析\n\n"

        # 关键词分析
        keywords = analysis_result.get('keywords', [])
        if keywords:
            md += "**TOP 10 关键词**:\n\n"
            for idx, kw in enumerate(keywords[:10], 1):
                md += f"{idx}. **{kw.get('keyword', '')}** (重要性: {kw.get('score', 0)}/10)\n"
        else:
            md += "暂无关键词数据\n"

        md += "\n---\n\n## 🔥 热门笔记TOP 10\n\n"

        # 热门笔记
        hot_notes = analysis_result.get('hot_notes', [])
        if hot_notes:
            md += "| 排名 | 标题 | 作者 | 点赞数 | 评论数 | 收藏数 |\n"
            md += "|------|------|------|--------|--------|--------|\n"
            for idx, note in enumerate(hot_notes[:10], 1):
                md += f"| {idx} | {note.get('title', '')[:30]}... | {note.get('author', '')} | {note.get('likes', 0)} | {note.get('comments', 0)} | {note.get('collects', 0)} |\n"
        else:
            md += "暂无热门笔记数据\n"

        md += "\n---\n\n## 💡 洞察结论\n\n"
        insights = analysis_result.get('insights', [])
        if insights:
            for insight in insights:
                md += f"- {insight}\n"
        else:
            md += "暂无洞察结论\n"

        md += "\n---\n\n## 📝 建议与展望\n\n"
        md += "1. 建议扩大采集范围，覆盖更多关键词维度\n"
        md += "2. 建议定期执行增量采集，跟踪内容趋势变化\n"
        md += "3. 建议结合评论区内容进行深度情感分析\n"
        md += "4. 建议添加竞品对比分析功能\n"

        md += "\n---\n\n*报告由小红书AI调研Agent自动生成*\n"

        return md

    def _format_sentiment(self, sentiment: Dict) -> str:
        """格式化情感分析结果"""
        total = sum(sentiment.values())
        if total == 0:
            return "未知"

        positive = sentiment.get('positive', 0)
        negative = sentiment.get('negative', 0)

        if positive > negative:
            return f"正面为主 ({positive}/{total})"
        elif negative > positive:
            return f"负面为主 ({negative}/{total})"
        else:
            return f"中性为主 ({sentiment.get('neutral', 0)}/{total})"

    def cleanup(self):
        """清理资源"""
        self.save_dedup_cache()
        print(f"[{datetime.now().isoformat()}] [INFO] 数据管理器清理完成")
