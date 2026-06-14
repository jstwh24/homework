"""
账号认证逻辑模块
- 用户注册（用户名唯一校验 + bcrypt密码哈希）
- 用户登录（密码验证 + session会话）
- 用户登出
"""

import bcrypt
from flask import session
from db.db_conn import execute_query, execute_insert


def register_user(username, password):
    """
    注册新用户
    - 检查用户名是否已存在
    - bcrypt加密密码后写入数据库
    - 同时创建对应的角色记录
    返回: (success: bool, message: str)
    """
    # 参数校验
    username = username.strip()
    if not username or len(username) < 2 or len(username) > 50:
        return False, "用户名长度需在2-50个字符之间"
    if not password or len(password) < 4:
        return False, "密码长度至少4位"

    # 检查用户名唯一性
    existing = execute_query(
        "SELECT uid FROM user_account WHERE username = %s",
        (username,),
        fetch_one=True
    )
    if existing:
        return False, "用户名已被注册，请换一个"

    # bcrypt加密密码（生成盐 + 哈希）
    pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 插入账号记录
    uid = execute_insert(
        "INSERT INTO user_account (username, pwd_hash) VALUES (%s, %s)",
        (username, pwd_hash)
    )

    # 创建对应的角色记录
    execute_insert(
        "INSERT INTO player_info (uid, player_name) VALUES (%s, %s)",
        (uid, username)
    )

    return True, "注册成功！请登录"


def login_user(username, password):
    """
    用户登录
    - 查询账号记录
    - bcrypt验证密码哈希
    - 设置session会话
    返回: (success: bool, message: str)
    """
    username = username.strip()
    if not username or not password:
        return False, "请输入用户名和密码"

    # 查询用户记录
    user = execute_query(
        "SELECT uid, username, pwd_hash FROM user_account WHERE username = %s",
        (username,),
        fetch_one=True
    )
    if not user:
        return False, "账号不存在"

    # bcrypt验证密码
    if not bcrypt.checkpw(password.encode('utf-8'), user['pwd_hash'].encode('utf-8')):
        return False, "密码错误"

    # 设置会话
    session['uid'] = user['uid']
    session['username'] = user['username']
    session.permanent = True

    return True, "登录成功"


def logout_user():
    """
    用户登出，清除session
    """
    session.clear()
    return True, "已退出登录"


def get_current_user():
    """
    获取当前登录用户信息
    返回: dict 或 None
    """
    uid = session.get('uid')
    if not uid:
        return None
    return {
        'uid': uid,
        'username': session.get('username', '')
    }


def require_login():
    """
    检查是否已登录，用于路由保护
    返回: (is_logged_in: bool, user_info: dict or None)
    """
    user = get_current_user()
    if user:
        return True, user
    return False, None
