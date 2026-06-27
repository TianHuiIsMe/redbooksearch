# 小红书AI调研Agent

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-repo)
[![Python](https://img.shields.io/badge/python-3.13+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

一个基于AI Agent架构的小红书内容自主调研系统，模拟真实用户行为，自动化完成内容采集、智能分析、报告生成全流程。

---

## ✨ 特性

- 🤖 **AI Agent智能体**: 实现「感知-思考-决策-执行」完整闭环
- 🧠 **任务自主拆解**: 自然语言需求 → 自动拆解为多步骤子任务
- 🌐 **真实用户模拟**: 基于Playwright，随机延迟、鼠标移动、滚动行为
- 🔍 **AI智能分析**: 内容分类、广告甄别、情感分析、关键词提取
- ✅ **双模型校验**: DeepSeek-V3（基座） + Qwen3-Max（校验），提高准确性
- 📊 **自动报告生成**: 结构化数据 + 统计维度 + 可视化结论
- 💾 **去重与增量**: 支持断点续传和增量采集
- 📝 **完整日志**: 记录Agent每一步思考和决策过程
- 🌐 **Web演示界面**: 提供友好的Web界面，方便测试和分享

---

## 📋 目录

- [快速开始](#快速开始)
- [安装](#安装)
- [使用方法](#使用方法)
- [配置说明](#配置说明)
- [架构设计](#架构设计)
- [合规性声明](#合规性声明)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 🚀 快速开始

### 前置要求

- Python 3.13+
- Playwright浏览器驱动
- 阿里云百炼平台API密钥（支持DeepSeek-V3 + Qwen3-Max双模型）

### 方法一：使用一键启动脚本（推荐）

**Windows:**
```bash
# 双击运行
start.bat
```

**Linux/Mac:**
```bash
# 赋予执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh
```

### 方法二：手动安装

```bash
# 1. 克隆项目
cd xiaohongshu_ai_agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装Playwright浏览器
playwright install chromium

# 4. 配置API密钥（编辑 config/config.json）
# 将 "YOUR_API_KEY_HERE" 替换为您的阿里云百炼平台API密钥

# 5. 启动Web演示界面
python web_app.py

# 6. 打开浏览器，访问 <ADDRESS_REMOVED>
```

### 5分钟快速体验（演示模式）

```bash
# 运行演示脚本（使用模拟数据，无需API密钥）
python -X utf8 demo.py
```

---

## 🔧 安装

### 方法一：使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 方法二：使用Conda

```bash
# 创建Conda环境
conda create -n xhs_agent python=3.13
conda activate xhs_agent

# 安装依赖
pip install -r requirements.txt
playwright install chromium
```

---

## 📖 使用方法

### 方法一：通过Web演示界面（推荐）

1. **启动Web服务**
   ```bash
   python web_app.py
   ```

2. **打开浏览器**
   - 访问：<ADDRESS_REMOVED>
   - 或使用手机访问：（获取本地IP后）

3. **使用Web界面**
   - 输入调研关键词（多个关键词用逗号分隔）
   - 点击"开始调研"
   - 查看执行进度
   - 下载报告和数据

### 方法二：通过命令行

```bash
# 调研单个关键词
python main.py -k "美妆"

# 调研多个关键词
python main.py -k "美妆" "护肤" "穿搭"

# 无头模式运行（不显示浏览器窗口）
python main.py -k "美食" --headless

# 限制每个关键词采集数量
python main.py -k "旅行" --max-notes 50

# 指定配置文件
python main.py -k "健身" -c my_config.json

# 指定输出目录
python main.py -k "科技" -o ./my_output
```

### 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|----------|
| `--keywords` | `-k` | 调研关键词（可多个） | 必填 |
| `--config` | `-c` | 配置文件路径 | `config/config.json` |
| `--headless` | - | 无头模式运行 | `False` |
| `--max-notes` | - | 每关键词最多采集笔记数 | `20` |
| `--output` | `-o` | 输出目录 | `data/outputs` |

### 配置文件说明

编辑 `config/config.json`:

```json
{
  "agent": {
    "name": "XiaohongshuAIAgent",
    "version": "1.0.0",
    "memory_size": 100
  },
  "browser": {
    "headless": false,        // 是否无头模式
    "min_delay": 2,          // 最小延迟（秒）
    "max_delay": 5,          // 最大延迟（秒）
    "max_scroll_attempts": 10,
    "max_pages": 5
  },
  "ai": {
    "model_provider": "dashscope",  // 阿里云百炼平台
    "base_model": "deepseek-v3",    // 基座模型
    "validation_model": "qwen-max", // 校验模型
    "api_key": "您的阿里云百炼平台API密钥",
    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "max_tokens": 2000,
    "temperature": 0.3,
    "enable_validation": true       // 是否启用双模型校验
  },
  "data": {
    "output_dir": "data/outputs",
    "raw_dir": "data/raw",
    "processed_dir": "data/processed"
  },
  "execution": {
    "max_notes_per_keyword": 20,
    "enable_dedup": true,
    "save_intermediate_results": true
  }
}
```

**阿里云百炼平台配置说明：**

1. 访问 [阿里云百炼平台](https://dashscope.aliyun.com/)
2. 注册账号并获取API密钥
3. 将API密钥填写到 `config.json` 中的 `api_key` 字段
4. 支持模型：
   - 基座模型：`deepseek-v3`（DeepSeek-V3）
   - 校验模型：`qwen-max`（Qwen3-Max）

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────┐
│           用户接口层 (main.py)                   │
│   命令行参数解析 / 配置加载 / 结果展示             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         AI Agent核心层 (agent/core.py)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 规划器    │→│ 执行器    │→│ 反思器    │  │
│  │ Planner  │  │ Executor  │  │Reflector │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│         ↑____________↓                     │
│              决策闭环                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           能力支撑层                              │
│  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 浏览器控制器       │  │ AI内容分析器      │  │
│  │ (browser/)       │  │ (ai/)           │  │
│  └──────────────────┘  └──────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 数据存储管理器     │  │ 日志系统         │  │
│  │ (data/)          │  │ (logs/)         │  │
│  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 核心模块说明

- **agent/core.py**: AI Agent主控制器，实现感知-思考-决策-执行闭环
- **browser/playwright_handler.py**: 基于Playwright的浏览器控制器，模拟真实用户行为
- **ai/content_analyzer.py**: AI内容分析器，使用大语言模型进行智能分析
- **data/data_manager.py**: 数据存储管理器，支持去重和增量采集
- **main.py**: 主程序入口，处理命令行参数和配置

---

## 🔒 合规性声明

### 严格遵守的底线

本项目**严格执行**以下合规性要求：

1. ✅ **仅模拟普通用户操作**
   - 使用Playwright模拟真实浏览器行为
   - 随机延迟2-5秒，模拟人类思考时间
   - 模拟鼠标移动、滚动等交互行为

2. ✅ **仅采集平台公开可见内容**
   - 不尝试绕过登录墙
   - 不访问需要特殊权限的私有内容
   - 遵守robots.txt规则

3. ✅ **合规、低频次、无暴力爬取**
   - 单次请求间隔 ≥ 2秒
   - 每个关键词默认最多采集20条（可配置）
   - 支持频率限制配置

4. ✅ **不使用任何逆向、抓包、接口破解手段**
   - 仅通过公开Web界面访问内容
   - 不分析或破解平台API
   - 不绕过任何技术保护措施

### 禁止行为

本项目**严格禁止**以下行为：

- ❌ 逆向工程、抓包、接口破解
- ❌ 使用自动化工具绕过平台技术限制
- ❌ 采集用户隐私数据（手机号、邮箱等）
- ❌ 对平台造成性能影响（DDoS攻击）

### 免责声明

- 本项目仅用于**学术研究和合法调研**
- 使用者需自行承担使用本项目产生的风险
- 建议在使用前咨询法律专业人士
- 严格遵守小红书平台的服务条款和robots.txt规则

---

## 🌐 对外分享方案

### 方案A：本地网络分享（最简单）

1. 启动Web服务：`python web_app.py`
2. 获取本地IP地址：
   - Windows: `ipconfig`
   - Linux/Mac: `ifconfig`
3. 分享访问地址：`<ADDRESS_REMOVED>

**注意：** 确保防火墙允许5000端口访问

### 方案B：使用内网穿透工具（推荐）

#### 使用 ngrok

1. 安装ngrok：https://ngrok.com/download
2. 启动ngrok：
   ```bash
   ngrok http 5000
   ```
3. 分享ngrok地址：`https://abc123.ngrok.io`

#### 使用 frp（国产内网穿透）

详见：[DEPLOYMENT.md](DEPLOYMENT.md)

### 方案C：部署到云服务器（最稳定）

详见：[DEPLOYMENT.md](DEPLOYMENT.md)

---

## 📊 输出说明

运行完成后，将在 `data/outputs/` 目录生成以下文件：

1. **结构化数据** (`xiaohongshu_data_YYYYMMDD_HHMMSS.json`)
   - 包含所有采集的笔记数据
   - JSON格式，方便程序处理

2. **CSV数据** (`xiaohongshu_data_YYYYMMDD_HHMMSS.csv`)
   - 结构化数据的CSV格式
   - 可直接用Excel打开

3. **分析报告** (`xiaohongshu_report_YYYYMMDD_HHMMSS.md`)
   - Markdown格式的分析报告
   - 包含分类统计、关键词分析、热门笔记、洞察结论

4. **执行日志** (`execution_log_YYYYMMDD_HHMMSS.json`)
   - 完整的执行日志
   - 记录Agent每一步思考和决策过程

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/

# 运行示例（使用测试关键词）
python main.py -k "测试" --max-notes 5
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境搭建

```bash
# 1. Fork项目并克隆
git clone https://github.com/your-username/xiaohongshu-ai-agent.git

# 2. 创建开发分支
git checkout -b feature/your-feature

# 3. 安装开发依赖
pip install -r requirements-dev.txt

# 4. 运行测试
pytest tests/

# 5. 提交代码
git commit -m "Add: your feature"
git push origin feature/your-feature

# 6. 创建Pull Request
```

### 代码规范

- 遵循PEP 8代码风格
- 添加必要的代码注释
- 编写单元测试
- 更新相关文档

---

## 📝 更新日志

### v1.0.0 (2026-06-27)

- ✨ 初始版本发布
- ✅ 实现AI Agent核心架构
- ✅ 实现Playwright浏览器自动化
- ✅ 实现AI内容分析功能
- ✅ 实现数据存储和去重机制
- ✅ 完成产品设计方案

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 现代化的浏览器自动化工具
- [OpenAI](https://openai.com/) - 强大的大语言模型
- [小红书](https://www.xiaohongshu.com/) - 优质的内容平台

---

## 📧 联系方式

- 作者: [您的名字]
- 邮箱: [您的邮箱]
- GitHub: [您的GitHub]

---

**⚠️ 警告**: 使用本项目前，请确保您已阅读并理解[合规性声明](#合规性声明)。不当使用可能导致IP被封禁或其他法律后果。
