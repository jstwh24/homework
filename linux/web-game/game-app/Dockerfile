# ============================================================
# 网页2D闯关游戏 - Flask 后端 Dockerfile
# 基于 Python 3.11 官方镜像
# ============================================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制Python依赖文件并安装
# 注意：所有依赖包均有预编译wheel，无需安装gcc等编译工具
# 使用清华PyPI镜像加速（国内环境）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY . .

# 暴露端口 5000
EXPOSE 5000

# 启动 Flask 应用（使用 eventlet 支持 WebSocket）
CMD ["python", "main.py"]
