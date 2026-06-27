"""
演示脚本 - 使用模拟数据展示AI Agent的功能
无需实际访问小红书，用于快速体验系统功能
"""

import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any


def print_banner():
    """打印欢迎信息"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                  小红书AI调研Agent v1.0.0                      ║
║                  ----------------------                          ║
║               演示模式 - 使用模拟数据                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def load_sample_data() -> List[Dict]:
    """加载示例数据"""
    sample_data = [
        {
            "url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "干皮救星！这几款面霜真的太好用了",
            "author": "美妆达人小A",
            "content": "大家好，今天给大家分享几款适合干皮的面霜。我是大干皮，冬天脸上总是起皮，试过很多面霜都不管用。直到我遇到了这几款，真的太好用了！1. 兰蔻菁纯面霜：质地滋润但不油腻，吸收很快...",
            "tags": ["面霜", "干皮", "护肤", "推荐"],
            "likes": 1234,
            "comments": 56,
            "collects": 78,
            "publish_time": "2026-06-20",
            "category": "美妆护肤",
            "is_ad": False,
            "sentiment": "positive"
        },
        {
            "url": "https://www.xiaohongshu.com/explore/def456",
            "title": "夏日必备！防晒霜测评TOP5",
            "author": "护肤小能手",
            "content": "夏天到了，防晒霜一定要选好！今天给大家测评5款热门防晒。1. 安热沙小金瓶：防晒力超强，但是有点油腻...2. 碧柔水感防晒：性价比之王，清爽不油腻...",
            "tags": ["防晒", "测评", "夏日", "美妆"],
            "likes": 2345,
            "comments": 123,
            "collects": 456,
            "publish_time": "2026-06-22",
            "category": "美妆护肤",
            "is_ad": False,
            "sentiment": "positive"
        },
        {
            "url": "https://www.xiaohongshu.com/explore/ghi789",
            "title": "学生党平价护肤品推荐",
            "author": "省钱小能手",
            "content": "作为学生党，性价比是最重要的！今天给大家推荐几款平价好用的护肤品。1. 大宝SOD蜜：国货之光，便宜大碗...2. 完美芦荟胶：万能胶，镇静修复...",
            "tags": ["平价", "学生党", "护肤", "推荐"],
            "likes": 987,
            "comments": 45,
            "collects": 123,
            "publish_time": "2026-06-18",
            "category": "美妆护肤",
            "is_ad": False,
            "sentiment": "positive"
        },
        {
            "url": "https://www.xiaohongshu.com/explore/jkl012",
            "title": "这款精华液真的绝了！",
            "author": "美妆品牌方",
            "content": "今天给大家推荐我们家的新品精华液，含有独家成分XXX，使用7天就能看到明显效果！现在购买还有优惠哦~",
            "tags": ["精华液", "新品", "优惠"],
            "likes": 56,
            "comments": 234,
            "collects": 12,
            "publish_time": "2026-06-25",
            "category": "广告推广",
            "is_ad": True,
            "sentiment": "neutral"
        },
        {
            "url": "https://www.xiaohongshu.com/explore/mno345",
            "title": "化妆师教你如何正确护肤",
            "author": "专业化妆师",
            "content": "很多人护肤步骤都做错了！今天教大家正确的护肤顺序。1. 清洁：选择温和的洁面...2. 爽肤水：轻拍至吸收...3. 精华：根据肤质选择...",
            "tags": ["护肤", "教程", "化妆师"],
            "likes": 1567,
            "comments": 89,
            "collects": 234,
            "publish_time": "2026-06-15",
            "category": "美妆护肤",
            "is_ad": False,
            "sentiment": "positive"
        }
    ]

    return sample_data


def simulate_agent_execution(keywords: List[str]):
    """模拟Agent执行过程"""
    print(f"[{datetime.now().isoformat()}] [INFO] 开始执行任务: 调研小红书平台关于{', '.join(keywords)}的内容")
    print(f"[{datetime.now().isoformat()}] [INFO] 关键词: {keywords}")
    print()
    print("=" * 70)
    print(f"[{datetime.now().isoformat()}] [INFO] 注意：当前为演示模式，使用模拟数据")
    print("=" * 70)
    print()

    # 阶段1：任务规划
    print(f"[{datetime.now().isoformat()}] [INFO] === 阶段1: 任务规划 ===")
    print(f"[{datetime.now().isoformat()}] [INFO] 规划任务：调研 {len(keywords)} 个关键词")
    for idx, keyword in enumerate(keywords, 1):
        print(f"[{datetime.now().isoformat()}] [INFO]   子任务 {idx}: 调研关键词 '{keyword}'")
        print(f"[{datetime.now().isoformat()}] [DEBUG]     - 步骤1: 搜索 '{keyword}' 相关内容")
        print(f"[{datetime.now().isoformat()}] [DEBUG]     - 步骤2: 浏览搜索结果")
        print(f"[{datetime.now().isoformat()}] [DEBUG]     - 步骤3: 采集笔记内容")
        print(f"[{datetime.now().isoformat()}] [DEBUG]     - 步骤4: AI分析内容")
    print()

    # 阶段2：数据采集
    print(f"[{datetime.now().isoformat()}] [INFO] === 阶段2: 数据采集 ===")
    sample_data = load_sample_data()
    print(f"[{datetime.now().isoformat()}] [INFO] 模拟采集到 {len(sample_data)} 条笔记")
    print()

    # 阶段3：AI分析
    print(f"[{datetime.now().isoformat()}] [INFO] === 阶段3: AI智能分析 ===")
    print(f"[{datetime.now().isoformat()}] [INFO] 步骤1: 内容分类")
    print(f"[{datetime.now().isoformat()}] [INFO]    - 美妆护肤: 4 条")
    print(f"[{datetime.now().isoformat()}] [INFO]    - 广告推广: 1 条")
    print(f"[{datetime.now().isoformat()}] [INFO] 步骤2: 广告检测")
    print(f"[{datetime.now().isoformat()}] [INFO]    - 检测到广告内容: 1 条")
    print(f"[{datetime.now().isoformat()}] [INFO] 步骤3: 关键词提取")
    print(f"[{datetime.now().isoformat()}] [INFO]    - TOP关键词: 面霜, 防晒, 测评, 推荐")
    print(f"[{datetime.now().isoformat()}] [INFO] 步骤4: 情感分析")
    print(f"[{datetime.now().isoformat()}] [INFO]    - 正面: 4 条, 中性: 1 条, 负面: 0 条")
    print(f"[{datetime.now().isoformat()}] [INFO] 步骤5: 热度分级")
    print(f"[{datetime.now().isoformat()}] [INFO]    - 热门笔记: 2 条")
    print()

    # 阶段4：生成报告
    print(f"[{datetime.now().isoformat()}] [INFO] === 阶段4: 生成报告 ===")
    print(f"[{datetime.now().isoformat()}] [INFO] 生成结构化数据...")
    print(f"[{datetime.now().isoformat()}] [INFO] 生成统计报告...")
    print(f"[{datetime.now().isoformat()}] [INFO] 生成调研总结...")
    print()

    # 完成
    print("=" * 70)
    print(f"[{datetime.now().isoformat()}] [INFO] [完成] 执行完成！")
    print(f"  采集笔记数: {len(sample_data)}")
    print(f"  内容分类: 2 个类别")
    print(f"  广告检测: 1 条广告")
    print(f"  情感分析: 80% 正面")
    print()
    print("  输出文件:")
    print(f"    - 结构化数据: data/outputs/demo_data.json")
    print(f"    - 分析报告: data/outputs/demo_report.md")
    print(f"    - 执行日志: logs/demo_log.json")
    print("=" * 70)
    print()

    return sample_data


def save_demo_results(data: List[Dict]):
    """保存演示结果"""
    # 创建输出目录
    os.makedirs("data/outputs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # 保存结构化数据
    output_data = {
        "report_metadata": {
            "report_title": "小红书AI调研报告（演示）",
            "generated_at": datetime.now().isoformat(),
            "is_demo": True,
            "keywords": ["美妆", "护肤"],
            "total_notes_collected": len(data)
        },
        "structured_data": [{"type": "note", "data": note} for note in data],
        "statistics": {
            "categories": {"美妆护肤": 4, "广告推广": 1},
            "sentiment": {"positive": 4, "neutral": 1, "negative": 0},
            "ad_detection": {"is_ad": 1, "not_ad": 4}
        },
        "insights": [
            "最受欢迎的内容类型是：美妆护肤",
            "广告内容占比：20%",
            "整体情感倾向正面，用户满意度较高"
        ]
    }

    with open("data/outputs/demo_data.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 保存Markdown报告
    md_content = generate_markdown_report(output_data)
    with open("data/outputs/demo_report.md", 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 保存执行日志
    log_data = [
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": "演示模式启动"},
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": f"采集到 {len(data)} 条模拟数据"},
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": "AI分析完成"},
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": "报告生成完成"}
    ]

    with open("logs/demo_log.json", 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now().isoformat()}] [INFO] 演示结果已保存")


def generate_markdown_report(data: Dict) -> str:
    """生成Markdown报告"""
    md = f"""# 小红书AI调研分析报告（演示）

**生成时间**: {data['report_metadata']['generated_at']}
**模式**: 演示模式（使用模拟数据）

---

## 📊 执行概况

- **采集笔记总数**: {data['report_metadata']['total_notes_collected']}
- **内容分类**: 2 个类别
- **广告内容占比**: 20%
- **情感倾向**: 正面为主

---

## 📂 内容分类统计

| 分类 | 数量 | 占比 |
|------|------|------|
| 美妆护肤 | 4 | 80% |
| 广告推广 | 1 | 20% |

---

## 🔥 热门笔记TOP 3

| 排名 | 标题 | 点赞数 | 评论数 | 收藏数 |
|------|------|--------|--------|--------|
| 1 | 夏日必备！防晒霜测评TOP5 | 2345 | 123 | 456 |
| 2 | 化妆师教你如何正确护肤 | 1567 | 89 | 234 |
| 3 | 干皮救星！这几款面霜真的太好用了 | 1234 | 56 | 78 |

---

## 💡 洞察结论

"""
    for insight in data.get("insights", []):
        md += f"- {insight}\n"

    md += """
---

## 📝 建议

1. 建议扩大采集范围，覆盖更多关键词维度
2. 建议定期执行增量采集，跟踪内容趋势变化
3. 建议结合评论区内容进行深度情感分析

---

*本报告由小红书AI调研Agent演示模式生成*
*使用模拟数据，仅用于功能展示*
"""

    return md


def main():
    """主函数"""
    print_banner()

    # 模拟关键词
    keywords = ["美妆", "护肤"]

    print(f"[{datetime.now().isoformat()}] [INFO] 演示模式启动...")
    print(f"[{datetime.now().isoformat()}] [INFO] 将使用模拟数据展示系统功能")
    print()

    # 模拟执行
    sample_data = simulate_agent_execution(keywords)

    # 保存结果
    save_demo_results(sample_data)

    print()
    print(f"[{datetime.now().isoformat()}] [INFO] 🎉 演示完成！")
    print()
    print(f"[{datetime.now().isoformat()}] [INFO] 下一步:")
    print(f"  1. 查看生成的报告: cat data/outputs/demo_report.md")
    print(f"  2. 查看结构化数据: cat data/outputs/demo_data.json")
    print(f"  3. 运行实际采集（需要配置API密钥）: python main.py -k '美妆'")


if __name__ == "__main__":
    main()
