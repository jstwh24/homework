#!/bin/bash
# ============================================================
# 网页2D横版闯关游戏 - 数据库初始化脚本
# 容器首次启动自动执行
# 密码从环境变量 MYSQL_PASSWORD 读取，与 .env 保持同步
# ============================================================
set -e

# 转义 SQL 字符串中的单引号（'' → 在 SQL 中表示一个单引号）
SQL_SAFE_PASSWORD="${MYSQL_PASSWORD//\'/\'\'}"

echo "🔧 正在初始化 game_db 数据库..."

mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<SQL_EOF
-- ============================================================
-- 网页2D横版闯关游戏 - 建表 & 初始数据
-- ============================================================

-- 兼容 PyMySQL：将认证方式改为 mysql_native_password
-- 密码从 .env 的 MYSQL_PASSWORD 自动读取，确保一致性
ALTER USER 'game_user'@'%' IDENTIFIED WITH mysql_native_password BY '${SQL_SAFE_PASSWORD}';
SELECT '✓ game_user 认证方式已更新' AS status;

-- 设置编码
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ----------------------------------------------------------
-- 1. user_account 账号表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_account (
    uid INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（唯一）',
    pwd_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt加密后的密码哈希',
    register_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户账号表';

-- ----------------------------------------------------------
-- 2. player_info 角色属性表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_info (
    pid INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色唯一ID',
    uid INT NOT NULL COMMENT '关联用户ID',
    player_name VARCHAR(50) NOT NULL DEFAULT '冒险者' COMMENT '角色名称',
    max_hp INT NOT NULL DEFAULT 100 COMMENT '最大生命值',
    attack INT NOT NULL DEFAULT 20 COMMENT '攻击力',
    total_clear INT NOT NULL DEFAULT 0 COMMENT '总通关次数',
    FOREIGN KEY (uid) REFERENCES user_account(uid) ON DELETE CASCADE,
    INDEX idx_uid (uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色属性表';

-- ----------------------------------------------------------
-- 3. game_save 存档表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS game_save (
    save_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '存档唯一ID',
    uid INT NOT NULL COMMENT '关联用户ID',
    pid INT NOT NULL COMMENT '关联角色ID',
    save_slot TINYINT NOT NULL COMMENT '存档档位 1/2/3',
    current_level INT NOT NULL DEFAULT 1 COMMENT '当前关卡编号',
    current_hp INT NOT NULL DEFAULT 100 COMMENT '当前生命值',
    pos_x INT NOT NULL DEFAULT 50 COMMENT '角色X坐标',
    pos_y INT NOT NULL DEFAULT 300 COMMENT '角色Y坐标',
    inventory JSON DEFAULT NULL COMMENT '背包物品（JSON格式）',
    unlock_skin JSON DEFAULT NULL COMMENT '已解锁皮肤（JSON格式）',
    save_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '存档时间',
    FOREIGN KEY (uid) REFERENCES user_account(uid) ON DELETE CASCADE,
    FOREIGN KEY (pid) REFERENCES player_info(pid) ON DELETE CASCADE,
    UNIQUE KEY uk_uid_slot (uid, save_slot),
    INDEX idx_uid (uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='游戏存档表';

-- ----------------------------------------------------------
-- 4. level_config 关卡配置表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS level_config (
    level_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关卡编号',
    level_name VARCHAR(50) NOT NULL COMMENT '关卡名称',
    map_w INT NOT NULL DEFAULT 800 COMMENT '地图宽度（像素）',
    map_h INT NOT NULL DEFAULT 600 COMMENT '地图高度（像素）',
    monster_num INT NOT NULL DEFAULT 2 COMMENT '怪物数量',
    reward_item VARCHAR(50) DEFAULT NULL COMMENT '通关奖励物品',
    INDEX idx_level (level_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关卡配置表';

-- ----------------------------------------------------------
-- 插入5个关卡的初始配置数据
-- ----------------------------------------------------------
INSERT INTO level_config (level_id, level_name, map_w, map_h, monster_num, reward_item) VALUES
    (1, '新手森林', 800, 600, 2, '生命药水'),
    (2, '暗黑洞穴', 800, 600, 3, '铁剑'),
    (3, '幽灵走廊', 800, 600, 4, '魔法护盾'),
    (4, '熔岩地牢', 800, 600, 5, '火焰戒指'),
    (5, '魔王城堡', 800, 600, 6, '勇者之剑')
ON DUPLICATE KEY UPDATE level_name = VALUES(level_name);

SELECT '✓ game_db 初始化完成' AS status;
SQL_EOF

echo "✅ 数据库初始化完成"
