"""
地图加载 & 碰撞检测模块
- 5个关卡的手工设计地图（20×15网格，每格40px = 800×600）
- 瓦片类型: 0=天空, 1=墙壁, 2=地面, 3=出口, 4=平台, 5=血瓶, 6=攻击强化
- 墙壁碰撞、平台碰撞、道具拾取检测
"""

# 瓦片大小
TILE = 40
MAP_COLS = 20   # 800 / 40
MAP_ROWS = 15   # 600 / 40

# 瓦片类型
EMPTY = 0
WALL = 1
GROUND = 2
EXIT = 3
PLATFORM = 4      # 平台：从下方可穿过，从上方站立
HP_POTION = 5     # 生命药水：恢复30HP
ATK_BOOST = 6     # 攻击强化：+10攻击力持续30秒
KEY = 7           # 钥匙：收集后才能通过传送门

# 关卡名称
LEVEL_NAMES = {
    1: '新手森林',
    2: '暗黑洞穴',
    3: '幽灵走廊',
    4: '熔岩地牢',
    5: '魔王城堡',
}

# ============================================================
# 5个手工关卡地图 (20列 × 15行)
# 0=天空, 1=墙壁(实心), 2=地面, 3=出口, 4=平台, 5=血瓶, 6=攻击强化
# ============================================================

LEVEL_MAPS = {
    # 关卡1：新手森林 - 简单教学关，1钥匙在平台上，1血瓶在平台上方
    1: [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0],  # 血瓶在平台上空
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0,0,0,0],  # 平台
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],  # 墙壁
        [2,2,2,2,2,2,2,2,2,2,2,2,2,7,2,2,2,2,2,3],  # 钥匙在地面，出口在右侧
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],

    # 关卡2：暗黑洞穴 - 有障碍，1钥匙，1攻击强化
    2: [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,4,4,4,0,4,4,4,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,1,0,0,7,0,0,0,0,0,0,0],
        [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],

    # 关卡3：幽灵走廊 - 多路径，1钥匙，1血瓶
    3: [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,4,4,0,0,0,4,4,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,7,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],

    # 关卡4：熔岩地牢 - 复杂地形，1钥匙，1攻击强化
    4: [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,4,4,0,0,4,4,4,0,0,4,4,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,4,4,0,0,1,1,0,0,0,1,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0,0],
        [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],

    # 关卡5：魔王城堡 - Boss关，1钥匙，1血瓶+1强化在平台高处
    5: [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,6,0,0,0,5,0,0,0,0,0,0,0],
        [0,0,1,0,0,0,4,4,4,0,0,0,4,4,4,0,0,0,1,0],
        [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
        [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
        [0,0,1,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0,1,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,4,4,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,7,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,1,4,1,0,0,0,0,0,0,0,0],
        [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],
}


def get_level_map(level_id):
    """获取指定关卡的瓦片地图"""
    if level_id not in LEVEL_MAPS:
        level_id = 1
    return LEVEL_MAPS[level_id]


def get_level_name(level_id):
    """获取关卡名称"""
    return LEVEL_NAMES.get(level_id, '未知关卡')


def get_player_spawn(level_id):
    """获取玩家出生点坐标（左侧地面上）"""
    level_map = get_level_map(level_id)
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            if level_map[row][col] == GROUND:
                spawn_y = row * TILE - 40
                return 50, max(0, spawn_y)
    return 50, 300


def get_exit_position(level_id):
    """获取出口位置（像素坐标）"""
    level_map = get_level_map(level_id)
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            if level_map[row][col] == EXIT:
                return col * TILE, row * TILE
    return 760, 400


def get_monster_spawns(level_id, count):
    """获取怪物出生点列表"""
    spawns = []
    level_map = get_level_map(level_id)
    ground_row = None
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            if level_map[row][col] == GROUND:
                ground_row = row
                break
        if ground_row is not None:
            break
    if ground_row is None:
        ground_row = 11
    ground_y = ground_row * TILE - 30
    section_width = 700 / (count + 1)
    for i in range(count):
        spawn_x = int(section_width * (i + 1)) + 50
        spawns.append((spawn_x, ground_y))
    return spawns


# ============================================================
# 碰撞检测
# ============================================================

def check_wall_collision(x, y, w, h, level_id, vy=0):
    """
    检测与墙壁/平台/地面的碰撞，修正位置
    返回: (new_x, new_y, on_ground)
    - 墙壁(WALL): 实心，全方向阻挡
    - 平台(PLATFORM): 从下方通过（vy<0时穿越），从上方站立（vy>=0时实心）
    - 地面(GROUND): 可站立
    """
    level_map = get_level_map(level_id)
    on_ground = False
    new_x, new_y = x, y

    # 检测的瓦片范围
    left_tile = max(0, int(x // TILE))
    right_tile = min(MAP_COLS - 1, int((x + w - 1) // TILE))
    top_tile = max(0, int(y // TILE))
    bottom_tile = min(MAP_ROWS - 1, int((y + h - 1) // TILE))

    for row in range(top_tile, bottom_tile + 1):
        for col in range(left_tile, right_tile + 1):
            tile = level_map[row][col]
            if tile not in (WALL, GROUND, PLATFORM):
                continue

            tile_left = col * TILE
            tile_right = tile_left + TILE
            tile_top = row * TILE
            tile_bottom = tile_top + TILE

            # 平台（单向碰撞）：玩家在平台上方向下时站立，从下方跳起时穿过
            if tile == PLATFORM:
                # 玩家脚底在平台下方 → 允许穿过（从下往上或在下方的状态）
                if y + h <= tile_top + 4:
                    continue
                # 玩家向上升（vy < 0）且身体还未完全越过平台 → 允许穿过
                if vy < 0 and y + h < tile_bottom:
                    continue
                    # 玩家在平台下方 → 允许穿过
                    continue

            # 计算各方向重叠深度
            overlap_left = (x + w) - tile_left
            overlap_right = tile_right - x
            overlap_top = (y + h) - tile_top      # 脚底重叠
            overlap_bottom = tile_bottom - y       # 头顶重叠

            # 找最小重叠方向来推动（忽略<=0的重叠）
            candidates = []
            if overlap_left > 0:
                candidates.append(('left', overlap_left))
            if overlap_right > 0:
                candidates.append(('right', overlap_right))
            if overlap_top >= -2:  # 允许2px容差（脚底刚好接触地面）
                candidates.append(('top', max(overlap_top, 0)))
            if overlap_bottom >= -2:
                candidates.append(('bottom', max(overlap_bottom, 0)))

            if not candidates:
                continue

            # 选最小重叠方向
            direction, _ = min(candidates, key=lambda c: c[1])

            if direction == 'top':
                new_y = tile_top - h
                on_ground = True
            elif direction == 'bottom':
                new_y = tile_bottom
            elif direction == 'left':
                new_x = tile_left - w
            elif direction == 'right':
                new_x = tile_right

    return new_x, new_y, on_ground


def check_monster_wall_collision(x, y, w, h, level_id, vy=0):
    """
    怪物与墙壁碰撞检测（简化版 — 不检测平台穿透）
    返回: (new_x, new_y)
    """
    level_map = get_level_map(level_id)
    new_x, new_y = x, y

    left_tile = max(0, int(x // TILE))
    right_tile = min(MAP_COLS - 1, int((x + w - 1) // TILE))
    top_tile = max(0, int(y // TILE))
    bottom_tile = min(MAP_ROWS - 1, int((y + h - 1) // TILE))

    for row in range(top_tile, bottom_tile + 1):
        for col in range(left_tile, right_tile + 1):
            tile = level_map[row][col]
            if tile not in (WALL, GROUND):
                continue

            tile_left = col * TILE
            tile_right = tile_left + TILE
            tile_top = row * TILE
            tile_bottom = tile_top + TILE

            overlap_left = (x + w) - tile_left
            overlap_right = tile_right - x
            overlap_top = (y + h) - tile_top
            overlap_bottom = tile_bottom - y

            candidates = []
            if overlap_left > 0:
                candidates.append(('left', overlap_left))
            if overlap_right > 0:
                candidates.append(('right', overlap_right))
            if overlap_top >= -2:
                candidates.append(('top', max(overlap_top, 0)))
            if overlap_bottom >= -2:
                candidates.append(('bottom', max(overlap_bottom, 0)))

            if not candidates:
                continue

            direction, _ = min(candidates, key=lambda c: c[1])

            if direction == 'top':
                new_y = tile_top - h
            elif direction == 'bottom':
                new_y = tile_bottom
            elif direction == 'left':
                new_x = tile_left - w
            elif direction == 'right':
                new_x = tile_right

    return new_x, new_y


def check_exit_reached(x, y, w, h, level_id):
    """检查是否到达出口，使用AABB含边缘接触"""
    exit_pos = get_exit_position(level_id)
    ex, ey = exit_pos[0], exit_pos[1]

    px1, py1 = x, y
    px2, py2 = x + w, y + h

    # 检测区向上延伸一个瓦片，含边缘
    ex1, ey1 = ex, ey - TILE
    ex2, ey2 = ex + TILE, ey + TILE

    return (px1 <= ex2 and px2 >= ex1 and py1 <= ey2 and py2 >= ey1)


def check_item_pickup(x, y, w, h, level_id, picked_items=None):
    """
    检测玩家是否碰到了道具
    picked_items: set of (level_id, col, row) 已拾取的道具，这些将被跳过
    返回: list of (item_type, tile_col, tile_row)
    """
    level_map = get_level_map(level_id)
    pickups = []
    if picked_items is None:
        picked_items = set()

    left_tile = max(0, int(x // TILE))
    right_tile = min(MAP_COLS - 1, int((x + w) // TILE))
    top_tile = max(0, int(y // TILE))
    bottom_tile = min(MAP_ROWS - 1, int((y + h) // TILE))

    for row in range(top_tile, bottom_tile + 1):
        for col in range(left_tile, right_tile + 1):
            tile = level_map[row][col]
            # 跳过已拾取的道具
            if (level_id, col, row) in picked_items:
                continue
            if tile == HP_POTION:
                pickups.append(('hp_potion', col, row))
            elif tile == ATK_BOOST:
                pickups.append(('atk_boost', col, row))
            elif tile == KEY:
                pickups.append(('key', col, row))

    return pickups


def remove_picked_item(level_id, col, row):
    """移除已被拾取的道具（已废弃，改用 picked_items set）"""
    pass  # 不再修改共享地图，改用 per-session picked_items 集合


def get_ground_tiles(level_id):
    """获取所有地面和平台瓦片的位置（供渲染参考）"""
    level_map = get_level_map(level_id)
    tiles = []
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            t = level_map[row][col]
            if t in (GROUND, WALL, PLATFORM, EXIT):
                tiles.append({'col': col, 'row': row, 'type': t})
    return tiles


def serialize_map(level_id, picked_items=None):
    """序列化地图数据发送给前端，已拾取道具替换为空白"""
    level_map = get_level_map(level_id)
    # 构建发送给前端的副本（不修改原始地图）
    tiles = [row[:] for row in level_map]
    if picked_items:
        for (lv, col, row) in picked_items:
            if lv == level_id and 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
                tiles[row][col] = EMPTY
    exit_pos = get_exit_position(level_id)
    return {
        'tiles': tiles,
        'cols': MAP_COLS,
        'rows': MAP_ROWS,
        'tile_size': TILE,
        'exit_x': exit_pos[0],
        'exit_y': exit_pos[1],
        'level_name': get_level_name(level_id),
    }
