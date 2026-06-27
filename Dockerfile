# 小红书AI调研Agent - Docker配置

FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN playwright install chromium

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p data/outputs data/raw data/processed logs

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "web_app.py"]
