"""
玩家角色逻辑模块
- 玩家状态管理（位置、血量、朝向、攻击状态）
- 移动、攻击、受伤等核心操作
- 所有逻辑在服务端执行（防作弊）
"""

import time

# 游戏常量
TILE_SIZE = 40          # 每个格子40像素
PLAYER_WIDTH = 30       # 玩家碰撞宽度
PLAYER_HEIGHT = 40      # 玩家碰撞高度
PLAYER_SPEED = 5        # 移动速度（像素/帧）
JUMP_VELOCITY = -17     # 跳跃初速度（约170px高度，适中）
GRAVITY = 0.85          # 重力加速度
ATTACK_RANGE = 50       # 攻击范围（像素）
ATTACK_COOLDOWN = 0.5   # 攻击冷却时间（秒）
DAMAGE_COOLDOWN = 1.0   # 受伤无敌时间（秒）


class Player:
    """玩家角色类 - 服务端游戏逻辑"""

    def __init__(self, pid, player_name, max_hp=100, attack=20, x=50, y=300, current_hp=None):
        self.pid = pid
        self.player_name = player_name
        self.max_hp = max_hp
        self.base_attack = attack          # 基础攻击力
        self.attack_power = attack         # 当前攻击力（含buff）
        self.x = x                          # 当前X坐标
        self.y = y                          # 当前Y坐标
        self.hp = current_hp if current_hp is not None else max_hp
        self.facing = 'right'               # 朝向: 'left' / 'right'
        self.is_attacking = False           # 是否正在攻击
        self.attack_timer = 0               # 攻击冷却计时器
        self.attack_frame = 0               # 攻击动画帧（0-5）
        self.damage_timer = 0               # 受伤无敌计时器
        self.atk_boost_timer = 0            # 攻击强化剩余时间（帧数）
        self.has_key = False                # 是否持有钥匙
        self.is_dead = False                # 是否死亡
        self.vx = 0                         # X方向速度
        self.vy = 0                         # Y方向速度
        self.on_ground = False              # 是否在地面上
        self.current_level = 1              # 当前关卡

    def set_input(self, keys_pressed):
        """
        根据当前按下的键设置速度
        keys_pressed: set of key strings ('left', 'right', 'up', 'down', 'attack')
        """
        if self.is_dead:
            return

        # 水平移动
        self.vx = 0
        if 'left' in keys_pressed:
            self.vx = -PLAYER_SPEED
            self.facing = 'left'
        if 'right' in keys_pressed:
            self.vx = PLAYER_SPEED
            self.facing = 'right'
        # 左右同时按时不移动
        if 'left' in keys_pressed and 'right' in keys_pressed:
            self.vx = 0

        # 垂直移动（跳跃）
        # 在地面上时清零垂直速度；按下↑触发跳跃抛物线
        if self.on_ground:
            self.vy = 0
            if 'up' in keys_pressed:
                self.vy = JUMP_VELOCITY  # 跳跃初速度（-24，约340px高）

        # 攻击
        if 'attack' in keys_pressed and self.attack_timer <= 0:
            self.is_attacking = True
            self.attack_timer = ATTACK_COOLDOWN
            self.attack_frame = 5  # 攻击动画持续5帧

    def update(self, gravity=0.85, ground_y=440):
        """
        更新玩家状态（每帧调用）
        - 应用重力
        - 更新位置
        - 地面检测由 tile-based 碰撞系统处理
        - 更新计时器
        """
        if self.is_dead:
            return

        # 应用重力（不在地面时）
        if not self.on_ground:
            self.vy += gravity

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 更新攻击计时器
        if self.attack_timer > 0:
            self.attack_timer -= 1/30  # 假设30FPS
            if self.attack_frame > 0:
                self.attack_frame -= 1
            if self.attack_frame <= 0:
                self.is_attacking = False

        # 更新受伤无敌计时器
        if self.damage_timer > 0:
            self.damage_timer -= 1/30

        # 更新攻击强化计时器
        if self.atk_boost_timer > 0:
            self.atk_boost_timer -= 1
            if self.atk_boost_timer <= 0:
                self.attack_power = self.base_attack  # 强化到期

        # 边界限制（不超出地图）
        if self.x < 0:
            self.x = 0
        if self.x > 800 - PLAYER_WIDTH:
            self.x = 800 - PLAYER_WIDTH
        if self.y < 0:
            self.y = 0

    def attack(self):
        """执行攻击，返回攻击范围矩形"""
        if self.is_dead:
            return None

        if self.facing == 'right':
            return {
                'x': self.x + PLAYER_WIDTH,
                'y': self.y,
                'w': ATTACK_RANGE,
                'h': PLAYER_HEIGHT
            }
        else:
            return {
                'x': self.x - ATTACK_RANGE,
                'y': self.y,
                'w': ATTACK_RANGE,
                'h': PLAYER_HEIGHT
            }

    def take_damage(self, damage):
        """受到伤害（含无敌时间判定）"""
        if self.is_dead or self.damage_timer > 0:
            return False

        self.hp -= damage
        self.damage_timer = DAMAGE_COOLDOWN

        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True

        return True

    def heal(self, amount):
        """恢复生命值"""
        if self.is_dead:
            return
        self.hp = min(self.hp + amount, self.max_hp)

    def apply_atk_boost(self, bonus=10, duration_sec=30):
        """攻击力强化（临时）"""
        self.attack_power = self.base_attack + bonus
        self.atk_boost_timer = duration_sec * 30  # 转换为帧数

    def get_attack_rect(self):
        """获取当前攻击碰撞矩形"""
        if not self.is_attacking or self.attack_frame < 2:
            return None
        return self.attack()

    def to_dict(self):
        """序列化为字典（发送给前端）"""
        return {
            'x': int(self.x),
            'y': int(self.y),
            'hp': self.hp,
            'max_hp': self.max_hp,
            'facing': self.facing,
            'attacking': self.is_attacking,
            'attack_frame': self.attack_frame,
            'is_dead': self.is_dead,
            'on_ground': self.on_ground,
            'atk_boosted': self.atk_boost_timer > 0,
            'atk_boost_sec': int(self.atk_boost_timer / 30),
            'has_key': self.has_key,
        }

    def load_from_dict(self, data):
        """从字典恢复状态（读档用）"""
        self.x = data.get('pos_x', 50)
        self.y = data.get('pos_y', 300)
        self.hp = data.get('current_hp', self.max_hp)
        self.current_level = data.get('current_level', 1)
