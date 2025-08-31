# YouTube转MP3转换器 - Docker版本

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建临时目录
RUN mkdir -p /tmp/youtube_conversions

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=simple_web_converter.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "simple_web_converter.py"]
