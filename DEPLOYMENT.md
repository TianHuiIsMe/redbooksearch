# 小红书AI调研Agent - 部署文档

## 📦 项目简介

小红书AI调研Agent是一个基于AI Agent架构的智能调研系统，能够模拟真实用户行为，自动化完成小红书内容的采集、分析和报告生成。

**核心特性：**
- 🤖 AI Agent智能体：自主决策、自动执行
- 🔍 智能采集：基于Playwright，模拟真实用户行为
- ✅ 双模型校验：DeepSeek-V3（基座） + Qwen3-Max（校验）
- 📊 自动报告生成：结构化数据 + 统计维度 + 可视化结论
- 🌐 Web演示界面：方便测试和分享

---

## 🚀 快速开始

### 方法一：本地部署（推荐）

#### 1. 环境要求

- Python 3.8+
- pip
- 网络连接（访问阿里云百炼平台API）

#### 2. 安装步骤

**Windows:**
```bash
# 1. 解压项目文件
# 2. 双击运行 start.bat
```

**Linux/Mac:**
```bash
# 1. 解压项目文件
# 2. 赋予执行权限
chmod +x start.sh

# 3. 运行启动脚本
./start.sh
```

#### 3. 配置API密钥

编辑 `config/config.json`，填写您的阿里云百炼平台API密钥：

```json
{
  "ai": {
    "model_provider": "dashscope",
    "base_model": "deepseek-v3",
    "validation_model": "qwen-max",
    "api_key": "您的API密钥",
    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "enable_validation": true
  }
}
```

#### 4. 访问Web界面

打开浏览器，访问：<ADDRESS_REMOVED>

---

### 方法二：Docker部署

#### 1. 安装Docker

- Windows/Mac: 安装 Docker Desktop
- Linux: 安装 Docker Engine

#### 2. 构建并运行

```bash
# 构建镜像
docker build -t xiaohongshu-ai-agent .

# 运行容器
docker run -p 5000:5000 xiaohongshu-ai-agent

# 或使用 docker-compose
docker-compose up -d
```

#### 3. 访问Web界面

打开浏览器，访问：<ADDRESS_REMOVED>

---

## 🌐 对外分享方案

### 方案A：本地网络分享（最简单）

1. **启动Web服务**
   ```bash
   python web_app.py
   ```

2. **获取本地IP地址**
   - Windows: `ipconfig`
   - Linux/Mac: `ifconfig`

3. **分享访问地址**
   ```
   <ADDRESS_REMOVED>
   ```

   **注意：** 确保防火墙允许5000端口访问

---

### 方案B：使用内网穿透工具（推荐）

#### 使用 ngrok

1. **安装ngrok**
   - 访问：https://ngrok.com/download
   - 注册账号并获取authtoken

2. **启动ngrok**
   ```bash
   # 启动Web服务
   python web_app.py

   # 另开一个终端，启动ngrok
   ngrok http 5000
   ```

3. **分享ngrok地址**
   ```
   例如: https://abc123.ngrok.io
   ```

#### 使用 frp（国产内网穿透）

1. **下载frp**
   - 访问：https://github.com/fatedier/frp/releases

2. **配置frpc.ini**
   ```ini
   [common]
   server_addr = your-frp-server.com
   server_port = 7000

   [web]
   type = http
   local_port = 5000
   custom_domains = your-domain.com
   ```

3. **启动frpc**
   ```bash
   ./frpc -c frpc.ini
   ```

---

### 方案C：部署到云服务器（最稳定）

#### 1. 购买云服务器

推荐：
- 阿里云ECS
- 腾讯云CVM
- 华为云ECS

#### 2. 部署步骤

```bash
# 1. 上传项目到服务器
scp -r xiaohongshu_ai_agent user@your-server:/home/

# 2. SSH登录服务器
ssh user@your-server

# 3. 安装依赖
cd /home/xiaohongshu_ai_agent
pip install -r requirements.txt
playwright install chromium

# 4. 配置API密钥
vim config/config.json

# 5. 启动服务（使用nohup后台运行）
nohup python web_app.py &

# 6. 配置防火墙，开放5000端口
```

#### 3. 配置域名（可选）

- 购买域名
- 配置DNS解析
- 配置Nginx反向代理（可选）

---

### 方案D：部署到Vercel/Netlify（仅前端）

**注意：** 此方法仅适用于纯前端应用，本项目需要后端API支持。

如果需要在线演示，建议使用：
- **Heroku**
- **Railway**
- **Render**

这些平台支持Python应用部署。

---

## 📖 使用指南

### 1. 通过Web界面使用

1. 打开浏览器，访问 `<ADDRESS_REMOVED>
2. 输入调研关键词（多个关键词用逗号分隔）
3. 点击"开始调研"
4. 等待执行完成
5. 下载报告和数据

### 2. 通过命令行使用

```bash
# 基本用法
python main.py -k "美妆" "护肤"

# 查看帮助
python main.py --help
```

### 3. API接口

项目提供以下API接口：

- `POST /api/start` - 启动任务
- `GET /api/status` - 获取任务状态
- `GET /api/report` - 下载报告
- `GET /api/data` - 下载数据

---

## 🔧 配置说明

### config/config.json

```json
{
  "agent": {
    "name": "XiaohongshuAIAgent",
    "version": "1.0.0",
    "memory_size": 100
  },
  "browser": {
    "headless": false,  // 是否无头模式
    "min_delay": 2,     // 最小延迟（秒）
    "max_delay": 5      // 最大延迟（秒）
  },
  "ai": {
    "model_provider": "dashscope",
    "base_model": "deepseek-v3",       // 基座模型
    "validation_model": "qwen-max",    // 校验模型
    "api_key": "您的API密钥",
    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "enable_validation": true          // 是否启用双模型校验
  },
  "execution": {
    "max_notes_per_keyword": 20,  // 每个关键词最多采集笔记数
    "enable_dedup": true          // 是否启用去重
  }
}
```

---

## 📊 输出文件

执行完成后，会在 `data/outputs/` 目录生成以下文件：

- `report_YYYYMMDD_HHMMSS.md` - Markdown格式报告
- `data_YYYYMMDD_HHMMSS.json` - JSON格式结构化数据
- `execution_log_YYYYMMDD_HHMMSS.json` - 执行日志

---

## ❓ 常见问题

### 1. API密钥错误

**错误：** `AuthenticationError: Incorrect API key`

**解决：**
- 检查 `config/config.json` 中的API密钥是否正确
- 确认API密钥是否已激活
- 确认API密钥是否有足够的额度

### 2. Playwright浏览器未安装

**错误：** `playwright._impl._errors.Error: Executable doesn't exist`

**解决：**
```bash
playwright install chromium
```

### 3. 端口被占用

**错误：** `OSError: [Errno 98] Address already in use`

**解决：**
- 修改 `web_app.py` 中的端口号
- 或终止占用端口的进程

### 4. 采集失败

**可能原因：**
- 网络连接问题
- 小红书反爬虫机制
- 频率过高被限制

**解决：**
- 降低采集频率（增加delay）
- 使用代理
- 更换IP地址

---

## 📞 技术支持

如有问题，请通过以下方式联系：

- 提交Issue：https://github.com/your-repo/issues
- 邮件支持：<EMAIL_REMOVED>

---

## 📄 许可证

MIT License

---

**最后更新：** 2026-06-27
