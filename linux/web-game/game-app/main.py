"""
网页2D横版闯关游戏 - Flask 后端主入口
========================================
- Flask HTTP路由：登录、注册、大厅页面
- Flask-SocketIO：实时游戏通信
- 游戏循环：服务端驱动，30FPS推送状态
- 所有游戏逻辑在后端运行（防作弊）
"""

import os
import logging
import socket

# 【关键】在 eventlet 劫持 socket 之前，预解析 MySQL 主机名为 IP 地址
# eventlet.monkey_patch() 会破坏 Docker 内部 DNS (127.0.0.11)
# 提前解析并写入环境变量，db_conn 直接使用 IP 地址连接
_DB_HOST = os.environ.get('DB_HOST', 'mysql-game')
try:
    _DB_IP = socket.gethostbyname(_DB_HOST)
    os.environ['DB_HOST_IP'] = _DB_IP
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logging.getLogger(__name__).info(f"MySQL主机预解析: {_DB_HOST} -> {_DB_IP}")
except socket.gaierror:
    os.environ['DB_HOST_IP'] = _DB_HOST
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logging.getLogger(__name__).warning(f"MySQL主机解析失败，使用原始值: {_DB_HOST}")

# 禁用 eventlet 绿色DNS（双重保险）
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

import eventlet

# eventlet必须在其他导入前打补丁
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, disconnect
import flask_socketio
from account.auth_logic import register_user, login_user, logout_user, get_current_user, require_login
from game_logic.player import Player
from game_logic.monster import Monster
from game_logic.map_loader import (
    get_level_map, get_level_name, get_player_spawn, get_exit_position,
    get_monster_spawns, check_wall_collision, check_monster_wall_collision,
    check_exit_reached, check_item_pickup, remove_picked_item, serialize_map
)
from game_logic.save_manager import (
    get_saves_for_user, create_save, load_save, save_game,
    update_player_clear, get_player_info
)

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask 应用初始化
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'game-secret-key-default')
app.config['SESSION_PERMANENT'] = True

# Flask-SocketIO 初始化（eventlet异步模式）
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", logger=False, engineio_logger=False)

# ---------------------------------------------------------------------------
# 游戏会话管理（内存）
# 存储当前活跃的游戏实例：{uid: game_session_dict}
# ---------------------------------------------------------------------------
active_games = {}


class GameSession:
    """
    单个玩家的游戏会话
    包含玩家对象、怪物列表、关卡状态
    """

    def __init__(self, uid, save_data, sid=None):
        self.uid = uid
        self.save_slot = save_data['save_slot']
        self.save_id = save_data['save_id']
        self.pid = save_data['pid']
        self.sid = sid  # WebSocket session ID，用于定向推送
        self.picked_items = set()  # 已拾取道具 (level_id, col, row)

        # 创建玩家对象
        self.player = Player(
            pid=save_data['pid'],
            player_name=save_data['player_name'],
            max_hp=save_data['max_hp'],
            attack=save_data['attack'],
            x=save_data['pos_x'],
            y=save_data['pos_y'],
            current_hp=save_data['current_hp'],
        )
        self.player.current_level = save_data['current_level']

        # 游戏状态
        self.status = 'playing'  # playing | paused | won | dead
        self.keys_pressed = set()  # 当前按下的按键
        self.monsters = []
        self.level_id = save_data['current_level']
        self.message = ''
        self.message_timer = 0
        self.auto_save_timer = 0
        self.game_loop_active = False

        # 加载关卡和怪物
        self._load_level()

    def _load_level(self):
        """加载当前关卡的地图和怪物"""
        self.level_id = self.player.current_level
        level_map = get_level_map(self.level_id)

        # 设置玩家出生位置
        spawn_x, spawn_y = get_player_spawn(self.level_id)
        self.player.x = spawn_x
        self.player.y = spawn_y
        self.player.has_key = False  # 重置钥匙状态

        # 生成多样化怪物
        self.monsters = []
        monster_count = min(self.level_id + 1, 6)
        spawns = get_monster_spawns(self.level_id, monster_count)

        for i, (mx, my) in enumerate(spawns):
            # 每关配置不同怪物类型
            if self.level_id == 5 and i == 0:
                # Boss关第一只是Boss
                monster = Monster(x=mx, y=my, hp=200, attack=25, patrol_range=60, monster_type='boss')
            elif self.level_id >= 3 and i % 3 == 1:
                # 从第三关开始出现坦克型
                monster = Monster(x=mx, y=my, hp=80, attack=15, patrol_range=50, monster_type='tank')
            elif i % 2 == 1:
                # 每隔一个刷一只快速型
                monster = Monster(x=mx, y=my, hp=20, attack=8, patrol_range=120, monster_type='fast')
            else:
                # 普通型
                hp = 25 + self.level_id * 5
                atk = 8 + self.level_id * 2
                monster = Monster(x=mx, y=my, hp=hp, attack=atk, patrol_range=80, monster_type='normal')

            self.monsters.append(monster)

        logger.info(f"关卡{self.level_id}加载：{len(self.monsters)}个怪物")

    def next_level(self):
        """进入下一关"""
        if self.player.current_level >= 5:
            # 已通关所有关卡
            self.status = 'won'
            update_player_clear(self.uid)
            self._auto_save()
            return False

        self.player.current_level += 1
        self.player.hp = min(self.player.hp + 20, self.player.max_hp)  # 通关恢复部分血量
        self._load_level()
        self.status = 'playing'
        self.message = f'进入 {get_level_name(self.level_id)}！'
        self.message_timer = 90  # 显示3秒（90帧）
        self._auto_save()
        return True

    def _auto_save(self):
        """自动存档（死亡时不存档，防止0血覆盖存档）"""
        if self.player.is_dead:
            return
        game_state = {
            'current_level': self.player.current_level,
            'current_hp': self.player.hp,
            'pos_x': int(self.player.x),
            'pos_y': int(self.player.y),
            'inventory': {
                'items': [],
                'picked': [list(p) for p in self.picked_items]  # 已拾取道具持久化
            },
            'unlock_skin': {'skins': []},
        }
        save_game(self.uid, self.save_slot, game_state)

    def get_game_state(self):
        """构建完整的游戏状态快照"""
        return {
            'player': self.player.to_dict(),
            'monsters': [m.to_dict() for m in self.monsters],
            'map': serialize_map(self.level_id, self.picked_items),
            'status': self.status,
            'message': self.message if self.message_timer > 0 else '',
            'level_name': get_level_name(self.level_id),
        }

    def update(self):
        """
        游戏主循环（每帧调用，约30FPS）
        1. 更新玩家输入 & 物理
        2. 墙壁/平台碰撞检测与位置修正
        3. 道具拾取检测
        4. 更新怪物AI
        5. 攻击判定
        6. 胜利/死亡判定
        """
        if self.status != 'playing':
            return

        # 更新消息计时器
        if self.message_timer > 0:
            self.message_timer -= 1

        # 自动存档计时器（每900帧≈30秒存一次）
        self.auto_save_timer += 1
        if self.auto_save_timer >= 900:
            self._auto_save()
            self.auto_save_timer = 0

        # ---- 1. 玩家物理更新 ----
        self.player.set_input(self.keys_pressed)
        # 先假设不在地面（让重力生效），碰撞检测会修正
        self.player.on_ground = False
        self.player.update()

        # 地图边界限制
        if self.player.x < 0:
            self.player.x = 0
        if self.player.x > 770:
            self.player.x = 770

        # ---- 2. 墙壁/平台碰撞检测（传入vy用于单向平台判定）----
        new_x, new_y, on_ground = check_wall_collision(
            self.player.x, self.player.y, 30, 40, self.level_id, self.player.vy
        )
        self.player.x = new_x
        self.player.y = new_y
        self.player.on_ground = on_ground
        # 如果落地，清零垂直速度
        if on_ground and self.player.vy > 0:
            self.player.vy = 0

        # ---- 3. 道具拾取检测（传入已拾取集合，避免重复拾取）----
        pickups = check_item_pickup(self.player.x, self.player.y, 30, 40, self.level_id, self.picked_items)
        for item_type, col, row in pickups:
            # 记录已拾取（持久化到存档 + 内存去重）
            self.picked_items.add((self.level_id, col, row))
            if item_type == 'hp_potion':
                self.player.heal(30)
                self.message = '💚 捡到生命药水！恢复30HP'
                self.message_timer = 90
            elif item_type == 'atk_boost':
                self.player.apply_atk_boost(bonus=10, duration_sec=30)
                self.message = '⚡ 捡到攻击强化！+10攻击持续30秒'
                self.message_timer = 90
            elif item_type == 'key':
                self.player.has_key = True
                self.message = '🔑 获得钥匙！现在可以进入传送门了'
                self.message_timer = 120

        # ---- 4. 更新怪物AI & 怪物碰撞 ----
        player_dict = self.player.to_dict()
        for monster in self.monsters:
            monster.update(player_dict)
            # 怪物与墙壁碰撞
            mx, my = check_monster_wall_collision(monster.x, monster.y, 30, 30, self.level_id)
            monster.x = mx
            monster.y = my

        # ---- 5. 玩家攻击判定 ----
        attack_rect = self.player.get_attack_rect()
        if attack_rect:
            for monster in self.monsters:
                if monster.is_dead:
                    continue
                if self._rect_collide(attack_rect, {
                    'x': monster.x, 'y': monster.y,
                    'w': 30, 'h': 30
                }):
                    killed = monster.take_damage(self.player.attack_power)
                    if killed:
                        self.message = '击败了怪物！'
                        self.message_timer = 60

        # ---- 6. 怪物攻击判定 ----
        for monster in self.monsters:
            if monster.is_dead:
                continue
            damage = monster.get_attack_damage(self.player.x, self.player.y)
            if damage > 0:
                hit = self.player.take_damage(damage)
                if hit:
                    self.message = f'受到 {damage} 点伤害！'
                    self.message_timer = 60

        # ---- 7. 通关判定（需钥匙 + 消灭所有怪物）----
        if check_exit_reached(self.player.x, self.player.y, 30, 40, self.level_id):
            all_dead = all(m.is_dead for m in self.monsters)
            if not self.player.has_key:
                self.message = '🔑 需要钥匙才能通过传送门！'
                self.message_timer = 90
            elif not all_dead:
                self.message = '请先消灭所有怪物！'
                self.message_timer = 90
            else:
                if self.level_id >= 5:
                    self.status = 'won'
                    update_player_clear(self.uid)
                    self._auto_save()
                    self.message = '恭喜通关全部关卡！'
                    self.message_timer = 180
                else:
                    self.next_level()

        # 6. 死亡判定
        if self.player.is_dead:
            self.status = 'dead'
            self.message = '你阵亡了...请返回大厅重新开始'
            self.message_timer = 180

    @staticmethod
    def _rect_collide(r1, r2):
        """AABB矩形碰撞检测"""
        return (
            r1['x'] < r2['x'] + r2['w'] and
            r1['x'] + r1['w'] > r2['x'] and
            r1['y'] < r2['y'] + r2['h'] and
            r1['y'] + r1['h'] > r2['y']
        )


# ===================================================================
# Flask HTTP 路由（页面 & API）
# ===================================================================

@app.route('/')
def index():
    """首页 - 已登录跳转大厅，未登录跳转登录页"""
    user = get_current_user()
    if user:
        return redirect(url_for('hall'))
    return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    """登录/注册页面"""
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    """注册API"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效请求'}), 400

    username = data.get('username', '')
    password = data.get('password', '')
    success, message = register_user(username, password)
    return jsonify({'success': success, 'message': message})


@app.route('/login', methods=['POST'])
def login():
    """登录API"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效请求'}), 400

    username = data.get('username', '')
    password = data.get('password', '')
    success, message = login_user(username, password)
    return jsonify({'success': success, 'message': message})


@app.route('/logout')
def logout():
    """登出"""
    user = get_current_user()
    if user:
        # 清理活跃游戏会话
        uid = user['uid']
        if uid in active_games:
            del active_games[uid]
    logout_user()
    return redirect(url_for('login_page'))


@app.route('/hall')
def hall():
    """游戏大厅页面（需登录）"""
    is_logged, user = require_login()
    if not is_logged:
        return redirect(url_for('login_page'))
    return render_template('hall.html')


@app.route('/game')
def game_page():
    """游戏页面（需登录）"""
    is_logged, user = require_login()
    if not is_logged:
        return redirect(url_for('login_page'))
    return render_template('game.html')


@app.route('/api/user')
def api_user():
    """获取当前用户信息"""
    user = get_current_user()
    if not user:
        return jsonify({'logged_in': False})
    player = get_player_info(user['uid'])
    return jsonify({
        'logged_in': True,
        'username': user['username'],
        'uid': user['uid'],
        'total_clear': player['total_clear'] if player else 0,
    })


@app.route('/api/saves')
def api_saves():
    """获取当前用户的3个存档信息"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    saves = get_saves_for_user(user['uid'])
    return jsonify({'saves': saves})


@app.route('/api/save/create', methods=['POST'])
def api_create_save():
    """创建/覆盖存档"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.get_json()
    save_slot = data.get('save_slot', 1)
    success, message, save_data = create_save(user['uid'], save_slot)
    return jsonify({'success': success, 'message': message})


# ===================================================================
# WebSocket 事件处理（实时游戏通信）
# ===================================================================

@socketio.on('connect')
def on_connect():
    """WebSocket连接建立"""
    user = get_current_user()
    if not user:
        logger.warning("WebSocket连接被拒绝：未登录")
        return False  # 拒绝连接
    logger.info(f"用户 {user['username']} WebSocket已连接")


@socketio.on('disconnect')
def on_disconnect():
    """WebSocket连接断开"""
    user = get_current_user()
    if user and user['uid'] in active_games:
        game = active_games[user['uid']]
        game.game_loop_active = False  # 停止游戏循环
        logger.info(f"用户 {user['username']} 断开连接，游戏循环已停止")


@socketio.on('join_game')
def on_join_game(data):
    """
    玩家请求进入游戏
    data: {'save_slot': 1}
    """
    user = get_current_user()
    if not user:
        emit('error', {'message': '未登录'})
        return

    uid = user['uid']
    save_slot = data.get('save_slot', 1)

    # 加载存档
    success, message, save_data = load_save(uid, save_slot)
    if not success:
        emit('error', {'message': message})
        return

    # 如果已有活跃游戏会话，先停止
    if uid in active_games:
        active_games[uid].game_loop_active = False

    # 创建新游戏会话（保存sid用于定向推送）
    game = GameSession(uid, save_data, sid=request.sid)
    # 恢复已拾取道具记录
    inventory = save_data.get('inventory', {})
    if isinstance(inventory, dict) and 'picked' in inventory:
        for item in inventory['picked']:
            game.picked_items.add(tuple(item))
    active_games[uid] = game

    # 发送初始游戏状态
    emit('game_state', game.get_game_state())
    emit('game_event', {'type': 'info', 'message': f'进入 {get_level_name(game.level_id)}！'})

    # 启动游戏循环（后台协程）
    game.game_loop_active = True
    socketio.start_background_task(game_loop, uid)


def game_loop(uid):
    """
    游戏主循环（后台协程）
    以约30FPS频率运行，推送状态给对应客户端
    """
    game = active_games.get(uid)
    if not game:
        return

    logger.info(f"游戏循环启动: uid={uid}")
    sid = game.sid  # 获取保存的WebSocket session ID

    while game.game_loop_active and game.status == 'playing':
        # 更新游戏逻辑
        game.update()

        # 推送状态给客户端（定向到该客户端房间）
        try:
            socketio.emit('game_state', game.get_game_state(), room=sid)

            # 状态变化事件
            if game.status == 'dead':
                socketio.emit('game_event', {'type': 'dead', 'message': '你阵亡了！'}, room=sid)
            elif game.status == 'won':
                socketio.emit('game_event', {'type': 'won', 'message': '恭喜通关全部关卡！'}, room=sid)
            elif game.message_timer == 60:
                socketio.emit('game_event', {'type': 'message', 'message': game.message}, room=sid)

        except Exception as e:
            logger.error(f"游戏循环推送异常: {e}")
            break

        # 控制帧率（约30FPS）
        eventlet.sleep(1/30)

    logger.info(f"游戏循环结束: uid={uid}")


@socketio.on('player_input')
def on_player_input(data):
    """
    接收玩家按键输入
    data: {'keys': ['left', 'attack']} 或 {'action': 'keydown', 'key': 'left'}
    """
    user = get_current_user()
    if not user:
        return

    uid = user['uid']
    game = active_games.get(uid)
    if not game or game.status != 'playing':
        return

    action = data.get('action', 'update')
    key = data.get('key', '')

    if action == 'keydown':
        game.keys_pressed.add(key)
    elif action == 'keyup':
        game.keys_pressed.discard(key)
    elif action == 'update':
        # 直接设置完整的按键集合（兼容移动端按钮模式）
        keys = data.get('keys', [])
        game.keys_pressed = set(keys)


@socketio.on('save_game')
def on_save_game():
    """手动存档"""
    user = get_current_user()
    if not user:
        return

    uid = user['uid']
    game = active_games.get(uid)
    if not game:
        emit('game_event', {'type': 'error', 'message': '游戏会话不存在'})
        return

    if game.player.is_dead:
        emit('game_event', {'type': 'error', 'message': '已阵亡，无法存档！'})
        return

    game._auto_save()
    emit('game_event', {'type': 'info', 'message': '存档成功！'})


@socketio.on('pause_game')
def on_pause_game():
    """暂停/继续游戏"""
    user = get_current_user()
    if not user:
        return

    uid = user['uid']
    game = active_games.get(uid)
    if not game:
        return

    if game.status == 'playing':
        game.status = 'paused'
        socketio.emit('game_state', game.get_game_state(), room=request.sid)
    elif game.status == 'paused':
        game.status = 'playing'
        # 保存最新的sid（可能已刷新）
        game.sid = request.sid
        socketio.emit('game_state', game.get_game_state(), room=request.sid)
        # 重启游戏循环
        game.game_loop_active = True
        socketio.start_background_task(game_loop, uid)


@socketio.on('return_hall')
def on_return_hall():
    """返回大厅"""
    user = get_current_user()
    if not user:
        return

    uid = user['uid']
    game = active_games.get(uid)
    if game:
        # 返回前自动存档（死亡状态不存档）
        if not game.player.is_dead:
            game._auto_save()
        game.game_loop_active = False
        del active_games[uid]

    emit('redirect', {'url': '/hall'})


# ===================================================================
# 应用启动
# ===================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("网页2D横版闯关游戏 - 服务端启动")
    logger.info("访问地址: http://localhost:5000")
    logger.info("WebSocket实时通信已启用 (eventlet)")
    logger.info("=" * 60)

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
    )
