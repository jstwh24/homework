"""
存档管理模块
- 每个账号3个独立存档档位
- 支持新建存档、加载存档、保存游戏
- 所有存档操作绑定uid，保证账号隔离
- 存档数据实时写入MySQL
"""

import json
import logging
from datetime import datetime
from db.db_conn import execute_query, execute_insert, execute_update

logger = logging.getLogger(__name__)

MAX_SAVE_SLOTS = 3  # 每个账号最多3个存档


def get_saves_for_user(uid):
    """
    获取某用户的所有存档信息
    返回: 列表，每个元素包含存档摘要（用于大厅展示）
    """
    saves = execute_query(
        """
        SELECT gs.save_id, gs.save_slot, gs.current_level, gs.current_hp,
               gs.pos_x, gs.pos_y, gs.save_time, pi.player_name, pi.max_hp
        FROM game_save gs
        JOIN player_info pi ON gs.pid = pi.pid
        WHERE gs.uid = %s
        ORDER BY gs.save_slot ASC
        """,
        (uid,)
    )

    # 构建3个档位的结果（填充空档位）
    result = []
    existing_slots = {s['save_slot']: s for s in saves}

    for slot in range(1, MAX_SAVE_SLOTS + 1):
        if slot in existing_slots:
            s = existing_slots[slot]
            result.append({
                'save_id': s['save_id'],
                'save_slot': slot,
                'current_level': s['current_level'],
                'current_hp': s['current_hp'],
                'player_name': s['player_name'],
                'max_hp': s['max_hp'],
                'save_time': s['save_time'].strftime('%Y-%m-%d %H:%M:%S') if s['save_time'] else '无',
                'has_data': True,
            })
        else:
            result.append({
                'save_slot': slot,
                'has_data': False,
            })

    return result


def create_save(uid, save_slot):
    """
    创建（或覆盖）指定档位的存档
    - 先删除该档位旧存档
    - 查找用户角色（player_info）
    - 创建初始存档数据
    返回: (success, message, save_dict)
    """
    if save_slot < 1 or save_slot > MAX_SAVE_SLOTS:
        return False, "存档档位无效", None

    # 查找角色
    player = execute_query(
        "SELECT pid, player_name, max_hp, attack FROM player_info WHERE uid = %s",
        (uid,),
        fetch_one=True
    )
    if not player:
        return False, "角色数据不存在", None

    # 删除该档位旧存档
    execute_update(
        "DELETE FROM game_save WHERE uid = %s AND save_slot = %s",
        (uid, save_slot)
    )

    # 创建新存档（初始状态：关卡1，满血，出生点位置）
    save_id = execute_insert(
        """
        INSERT INTO game_save
        (uid, pid, save_slot, current_level, current_hp, pos_x, pos_y, inventory, unlock_skin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            uid,
            player['pid'],
            save_slot,
            1,                              # 初始关卡
            player['max_hp'],               # 满血
            50,                             # 出生X
            300,                            # 出生Y
            json.dumps({'items': []}),      # 空背包
            json.dumps({'skins': []}),      # 空皮肤
        )
    )

    save_dict = {
        'save_id': save_id,
        'uid': uid,
        'pid': player['pid'],
        'save_slot': save_slot,
        'current_level': 1,
        'current_hp': player['max_hp'],
        'pos_x': 50,
        'pos_y': 300,
        'player_name': player['player_name'],
        'max_hp': player['max_hp'],
        'attack': player['attack'],
        'inventory': [],
        'unlock_skin': [],
    }

    logger.info(f"用户{uid}创建存档 slot={save_slot}, save_id={save_id}")
    return True, "存档创建成功", save_dict


def load_save(uid, save_slot):
    """
    加载指定档位的存档
    返回: (success, message, save_dict)
    """
    save = execute_query(
        """
        SELECT gs.*, pi.player_name, pi.max_hp, pi.attack, pi.total_clear
        FROM game_save gs
        JOIN player_info pi ON gs.pid = pi.pid
        WHERE gs.uid = %s AND gs.save_slot = %s
        """,
        (uid, save_slot),
        fetch_one=True
    )

    if not save:
        return False, "存档不存在，请先创建", None

    # 解析JSON字段
    inventory = []
    unlock_skin = []
    if save.get('inventory'):
        try:
            inventory = json.loads(save['inventory']) if isinstance(save['inventory'], str) else save['inventory']
        except json.JSONDecodeError:
            inventory = []
    if save.get('unlock_skin'):
        try:
            unlock_skin = json.loads(save['unlock_skin']) if isinstance(save['unlock_skin'], str) else save['unlock_skin']
        except json.JSONDecodeError:
            unlock_skin = []

    # 如果存档HP<=0（死亡存档），重置为满血并回到关卡出生点
    current_hp = save['current_hp']
    pos_x = save['pos_x']
    pos_y = save['pos_y']
    if current_hp <= 0:
        logger.info(f"存档slot={save_slot}血量为0，自动恢复到满血状态")
        current_hp = save['max_hp']
        pos_x = 50
        pos_y = 300

    save_dict = {
        'save_id': save['save_id'],
        'uid': save['uid'],
        'pid': save['pid'],
        'save_slot': save['save_slot'],
        'current_level': save['current_level'],
        'current_hp': current_hp,
        'pos_x': pos_x,
        'pos_y': pos_y,
        'player_name': save['player_name'],
        'max_hp': save['max_hp'],
        'attack': save['attack'],
        'inventory': inventory,
        'unlock_skin': unlock_skin,
    }

    logger.info(f"用户{uid}加载存档 slot={save_slot}, 关卡={save['current_level']}, HP={current_hp}")
    return True, "存档加载成功", save_dict


def save_game(uid, save_slot, game_state):
    """
    保存游戏状态到数据库
    game_state: dict 包含 current_level, current_hp, pos_x, pos_y, inventory, unlock_skin
    返回: bool
    """
    try:
        rows = execute_update(
            """
            UPDATE game_save
            SET current_level = %s,
                current_hp = %s,
                pos_x = %s,
                pos_y = %s,
                inventory = %s,
                unlock_skin = %s,
                save_time = NOW()
            WHERE uid = %s AND save_slot = %s
            """,
            (
                game_state.get('current_level', 1),
                game_state.get('current_hp', 100),
                game_state.get('pos_x', 50),
                game_state.get('pos_y', 300),
                json.dumps(game_state.get('inventory', {'items': []})),
                json.dumps(game_state.get('unlock_skin', {'skins': []})),
                uid,
                save_slot,
            )
        )

        if rows > 0:
            logger.info(f"用户{uid}存档成功 slot={save_slot}")
            return True
        else:
            logger.warning(f"用户{uid}存档失败：存档记录不存在 slot={save_slot}")
            return False

    except Exception as e:
        logger.error(f"存档异常 uid={uid}, slot={save_slot}: {e}")
        return False


def update_player_clear(uid):
    """
    更新玩家通关次数
    """
    execute_update(
        "UPDATE player_info SET total_clear = total_clear + 1 WHERE uid = %s",
        (uid,)
    )


def get_player_info(uid):
    """
    获取玩家角色信息（大厅展示用）
    """
    return execute_query(
        "SELECT pid, player_name, max_hp, attack, total_clear FROM player_info WHERE uid = %s",
        (uid,),
        fetch_one=True
    )
