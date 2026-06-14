"""
怪物AI逻辑模块
- 怪物状态机：巡逻(PATROL) → 追击(CHASE) → 攻击(ATTACK)
- 自动巡逻（在固定范围内来回移动）
- 检测玩家进入警戒范围后主动追击
- 近身攻击判定
"""

import math
import random

# 怪物常量
MONSTER_SIZE = 30       # 怪物大小（像素）
MONSTER_SPEED = 2       # 巡逻速度
MONSTER_CHASE_SPEED = 3.5  # 追击速度
AGGRO_RANGE = 200       # 警戒范围（像素）
ATTACK_RANGE = 40       # 怪物攻击范围
MONSTER_ATTACK_COOLDOWN = 1.5  # 怪物攻击冷却

# 怪物状态
STATE_PATROL = 'patrol'
STATE_CHASE = 'chase'
STATE_ATTACK = 'attack'


class Monster:
    """怪物类 - 包含AI行为"""

    _id_counter = 0  # 全局怪物ID计数器

    def __init__(self, x, y, hp=30, attack=10, patrol_range=100, monster_type='normal'):
        Monster._id_counter += 1
        self.id = Monster._id_counter
        self.x = x                              # 当前位置X
        self.y = y                              # 当前位置Y
        self.hp = hp                            # 当前生命值
        self.max_hp = hp                        # 最大生命值
        self.attack_power = attack              # 攻击力
        self.monster_type = monster_type        # 类型: 'normal','fast','tank','boss'
        self.state = STATE_PATROL               # 当前AI状态
        self.facing = 'right'                   # 朝向
        self.patrol_origin_x = x                # 巡逻原点X
        self.patrol_range = patrol_range        # 巡逻范围
        self.patrol_target_x = x + patrol_range # 巡逻目标点
        self.attack_cooldown = 0                # 攻击冷却
        self.is_dead = False                    # 是否死亡
        self.damage_flash = 0                   # 受伤闪烁帧

        # 随机初始方向
        if random.random() > 0.5:
            self.patrol_target_x = x - patrol_range

    def update(self, player_dict):
        """
        更新怪物AI（每帧调用）
        player_dict: 玩家状态字典 {'x', 'y', 'is_dead'}
        """
        if self.is_dead:
            return

        # 更新冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1/30
        if self.damage_flash > 0:
            self.damage_flash -= 1

        px = player_dict['x']
        py = player_dict['y']
        player_dead = player_dict.get('is_dead', False)

        # 计算到玩家的距离
        dx = px - self.x
        dy = py - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        # --- AI状态机 ---

        if player_dead:
            # 玩家死亡，回到巡逻状态
            self.state = STATE_PATROL
            self._do_patrol()

        elif dist < ATTACK_RANGE and self.attack_cooldown <= 0:
            # 近身 → 攻击状态
            self.state = STATE_ATTACK
            self.attack_cooldown = MONSTER_ATTACK_COOLDOWN

        elif dist < AGGRO_RANGE:
            # 进入警戒范围 → 追击状态
            self.state = STATE_CHASE
            self._do_chase(px, py)

        else:
            # 超出警戒范围 → 巡逻状态
            self.state = STATE_PATROL
            self._do_patrol()

    def _do_patrol(self):
        """巡逻行为：在原点左右范围内来回移动"""
        target = self.patrol_target_x

        if abs(self.x - target) < 5:
            # 到达目标点，反转方向
            if target >= self.patrol_origin_x:
                self.patrol_target_x = self.patrol_origin_x - self.patrol_range
            else:
                self.patrol_target_x = self.patrol_origin_x + self.patrol_range

        # 向目标移动
        if self.x < self.patrol_target_x:
            self.x += MONSTER_SPEED
            self.facing = 'right'
        else:
            self.x -= MONSTER_SPEED
            self.facing = 'left'

    def _do_chase(self, px, py):
        """追击行为：向玩家位置移动"""
        if self.x < px:
            self.x += MONSTER_CHASE_SPEED
            self.facing = 'right'
        elif self.x > px:
            self.x -= MONSTER_CHASE_SPEED
            self.facing = 'left'

    def get_attack_damage(self, player_x, player_y):
        """
        检查是否能攻击到玩家
        返回: 伤害值（如果命中）或 0（如果未命中）
        """
        if self.is_dead or self.state != STATE_ATTACK:
            return 0

        dx = abs(self.x - player_x)
        dy = abs(self.y - player_y)
        if dx < ATTACK_RANGE and dy < MONSTER_SIZE:
            return self.attack_power
        return 0

    def take_damage(self, damage):
        """受到伤害"""
        if self.is_dead:
            return False

        self.hp -= damage
        self.damage_flash = 5  # 闪烁5帧

        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            return True  # 返回True表示怪物被击杀

        # 受伤后立即进入追击状态
        self.state = STATE_CHASE
        return False

    def to_dict(self):
        """序列化"""
        return {
            'id': self.id,
            'x': int(self.x),
            'y': int(self.y),
            'hp': self.hp,
            'max_hp': self.max_hp,
            'state': self.state,
            'facing': self.facing,
            'is_dead': self.is_dead,
            'damage_flash': self.damage_flash,
            'monster_type': self.monster_type,
        }
