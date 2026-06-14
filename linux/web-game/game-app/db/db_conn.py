"""
数据库连接模块
- 使用 PyMySQL 连接 MySQL 8.0
- 提供参数化查询辅助函数，防止SQL注入
- 支持连接重试机制（等待MySQL容器就绪）
- 使用 main.py 预解析的 IP 地址，绕过 eventlet DNS 问题
"""

import pymysql
import os
import time
import logging

logger = logging.getLogger(__name__)

# main.py 在 eventlet 打补丁前已预解析主机名为 IP，存入 DB_HOST_IP 环境变量
# 优先使用 IP 地址，回退到主机名
_DB_HOST = os.environ.get('DB_HOST_IP', os.environ.get('DB_HOST', 'localhost'))
logger.info(f"数据库目标地址: {_DB_HOST}")

DB_CONFIG = {
    'host': _DB_HOST,  # 使用预解析的IP地址，彻底绕过DNS
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'game_user'),
    'password': os.environ.get('DB_PASSWORD', 'game_pass_2024'),
    'database': os.environ.get('DB_NAME', 'game_db'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,  # 返回字典格式结果
    'autocommit': True,  # 自动提交事务
}

# 全局数据库连接
_connection = None


def get_connection():
    """
    获取数据库连接（带重试机制）
    等待MySQL容器完全就绪后建立连接
    """
    global _connection
    max_retries = 5
    retry_delay = 1  # 秒

    # 检查现有连接是否有效
    if _connection is not None:
        try:
            _connection.ping(reconnect=True)
            return _connection
        except Exception:
            _connection = None

    for attempt in range(max_retries):
        try:
            _connection = pymysql.connect(**DB_CONFIG)
            logger.info(f"数据库连接成功: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return _connection
        except pymysql.Error as e:
            logger.warning(f"数据库连接失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise RuntimeError(f"无法连接到数据库，已重试{max_retries}次") from e


def execute_query(sql, params=None, fetch_one=False):
    """
    执行查询语句（SELECT），使用参数化查询防注入
    返回: 字典列表 或 单个字典
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()


def execute_update(sql, params=None):
    """
    执行更新语句（INSERT/UPDATE/DELETE），使用参数化查询防注入
    返回: 受影响行数
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.rowcount


def execute_insert(sql, params=None):
    """
    执行插入语句，返回自增主键ID
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid
