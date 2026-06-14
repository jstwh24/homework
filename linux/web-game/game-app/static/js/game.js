/**
 * 游戏客户端 JavaScript
 * ============================================================
 * - Canvas 分层渲染（地图 → 怪物 → 玩家 → UI）
 * - 键盘 + 触屏双适配输入
 * - WebSocket 实时接收游戏状态
 * - 暂停/通关/死亡弹窗
 */

// ============================================================
// 全局状态
// ============================================================
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');

let socket = null;           // Socket.IO 连接
let gameState = null;        // 最新服务端游戏状态
let saveSlot = 1;            // 当前存档档位
let isMobile = false;        // 是否是触屏设备
let animFrameId = null;      // requestAnimationFrame ID

// 按键状态（本地追踪，也发送给服务端）
const keysDown = new Set();

// ============================================================
// 初始化
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取存档档位
    const params = new URLSearchParams(window.location.search);
    saveSlot = parseInt(params.get('slot')) || 1;

    // 检测触屏设备
    isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

    // 移动端显示虚拟按键
    if (isMobile) {
        document.getElementById('mobile-controls').style.display = 'flex';
    } else {
        // 桌面端显示键盘提示
        const hint = document.createElement('div');
        hint.className = 'keyboard-hint';
        hint.textContent = '方向键移动 | 空格攻击 | S存档 | ESC暂停';
        document.querySelector('.game-wrapper').appendChild(hint);
    }

    // 连接WebSocket
    connectSocket();
});

// ============================================================
// WebSocket 连接
// ============================================================
function connectSocket() {
    socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 10,
    });

    socket.on('connect', function() {
        console.log('WebSocket已连接');
        // 请求加入游戏
        socket.emit('join_game', { save_slot: saveSlot });
    });

    socket.on('disconnect', function() {
        console.log('WebSocket已断开');
        cancelAnimationFrame(animFrameId);
    });

    socket.on('connect_error', function(err) {
        console.error('WebSocket连接失败:', err);
        showOverlay('连接失败', '无法连接到游戏服务器，请刷新页面重试。', [
            { text: '返回大厅', cls: 'hall', action: function() { window.location.href = '/hall'; } },
            { text: '刷新重试', cls: 'resume', action: function() { location.reload(); } },
        ]);
    });

    // 接收游戏状态
    socket.on('game_state', function(state) {
        gameState = state;
    });

    // 接收游戏事件
    socket.on('game_event', function(event) {
        console.log('游戏事件:', event);

        if (event.type === 'dead') {
            showOverlay('你阵亡了！', event.message, [
                { text: '返回大厅', cls: 'hall', action: returnToHall },
            ]);
        } else if (event.type === 'won') {
            showOverlay('恭喜通关！', event.message, [
                { text: '返回大厅', cls: 'hall', action: returnToHall },
            ]);
        }
    });

    // 接收重定向
    socket.on('redirect', function(data) {
        window.location.href = data.url;
    });

    // 接收错误
    socket.on('error', function(data) {
        console.error('服务端错误:', data.message);
        alert(data.message);
    });
}

// ============================================================
// 输入处理
// ============================================================

// --- 键盘事件（桌面端） ---
document.addEventListener('keydown', function(e) {
    if (isMobile) return; // 移动端忽略键盘

    const key = keyMap(e.key);
    if (key && !keysDown.has(key)) {
        keysDown.add(key);
        sendInput('keydown', key);
    }

    // ESC暂停
    if (e.key === 'Escape') {
        togglePause();
    }

    // S键存档
    if (e.key === 's' || e.key === 'S') {
        manualSave();
    }

    // Q键返回大厅
    if (e.key === 'q' || e.key === 'Q') {
        returnToHallConfirm();
    }

    // 阻止方向键滚动页面
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(e.key)) {
        e.preventDefault();
    }
});

document.addEventListener('keyup', function(e) {
    if (isMobile) return;

    const key = keyMap(e.key);
    if (key) {
        keysDown.delete(key);
        sendInput('keyup', key);
    }
});

function keyMap(key) {
    const map = {
        'ArrowLeft': 'left',
        'ArrowRight': 'right',
        'ArrowUp': 'up',
        'ArrowDown': 'down',
        ' ': 'attack',
    };
    return map[key] || null;
}

// --- 触屏事件（移动端） ---
function mobileKeyDown(key) {
    keysDown.add(key);
    sendInput('keydown', key);
}

function mobileKeyUp(key) {
    keysDown.delete(key);
    sendInput('keyup', key);
}

// --- 发送输入到服务端 ---
function sendInput(action, key) {
    if (socket && socket.connected) {
        socket.emit('player_input', { action: action, key: key });
    }
}

// ============================================================
// 游戏操作
// ============================================================

function manualSave() {
    if (socket && socket.connected) {
        socket.emit('save_game');
        // 在Canvas上短暂显示"已保存"提示
        flashMessage('💾 已存档');
    }
}

function togglePause() {
    if (socket && socket.connected) {
        socket.emit('pause_game');
    }
}

function returnToHall() {
    if (socket && socket.connected) {
        socket.emit('return_hall');
    }
}

function returnToHallConfirm() {
    showOverlay('返回大厅', '确定要返回大厅吗？\n游戏会自动存档。', [
        { text: '确定返回', cls: 'hall', action: returnToHall },
        { text: '继续游戏', cls: 'resume', action: hideOverlay },
    ]);
}

function flashMessage(msg) {
    // 简单实现：利用gameState中的message字段
    // 或在渲染中单独处理
    window._flashMsg = msg;
    setTimeout(function() { window._flashMsg = null; }, 2000);
}

// ============================================================
// Canvas 渲染循环
// ============================================================
function renderLoop() {
    animFrameId = requestAnimationFrame(renderLoop);

    if (!gameState) {
        // 还未收到游戏状态，显示加载中
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, 800, 600);
        ctx.fillStyle = '#aaa';
        ctx.font = '20px "Microsoft YaHei"';
        ctx.textAlign = 'center';
        ctx.fillText('正在连接游戏服务器...', 400, 300);
        return;
    }

    // 清屏
    ctx.clearRect(0, 0, 800, 600);

    // 分层渲染
    drawBackground();
    drawMap(gameState.map);
    drawMonsters(gameState.monsters);
    drawPlayer(gameState.player);
    drawUI(gameState);

    // 显示闪存消息
    if (window._flashMsg) {
        ctx.fillStyle = '#f5c842';
        ctx.font = 'bold 16px "Microsoft YaHei"';
        ctx.textAlign = 'center';
        ctx.fillText(window._flashMsg, 400, 100);
    }
}

// ============================================================
// 背景渲染
// ============================================================
function drawBackground() {
    // 天空渐变
    const grad = ctx.createLinearGradient(0, 0, 0, 600);
    grad.addColorStop(0, '#1a1a3e');
    grad.addColorStop(0.5, '#2d1b4e');
    grad.addColorStop(1, '#1a0a2e');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 800, 600);

    // 装饰星星
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    for (let i = 0; i < 30; i++) {
        const sx = (i * 137 + 50) % 800;
        const sy = (i * 97 + 20) % 400;
        ctx.fillRect(sx, sy, 2, 2);
    }
}

// ============================================================
// 地图渲染
// ============================================================
function drawMap(mapData) {
    if (!mapData || !mapData.tiles) return;

    const tiles = mapData.tiles;
    const ts = mapData.tile_size || 40;

    for (let row = 0; row < tiles.length; row++) {
        for (let col = 0; col < tiles[row].length; col++) {
            const tile = tiles[row][col];
            const x = col * ts;
            const y = row * ts;

            if (tile === 0) continue; // 空白

            if (tile === 1) {
                // 墙壁 - 深灰色砖块（实心碰撞）
                ctx.fillStyle = '#555568';
                ctx.fillRect(x, y, ts, ts);
                ctx.strokeStyle = '#6a6a7e';
                ctx.lineWidth = 1;
                ctx.strokeRect(x + 1, y + 1, ts - 2, ts - 2);
                ctx.strokeStyle = '#404050';
                ctx.beginPath();
                ctx.moveTo(x, y + ts / 2);
                ctx.lineTo(x + ts, y + ts / 2);
                ctx.moveTo(x + ts / 2, y);
                ctx.lineTo(x + ts / 2, y + ts / 2);
                ctx.stroke();
            } else if (tile === 2) {
                // 地面 - 棕色泥土
                ctx.fillStyle = '#6b4423';
                ctx.fillRect(x, y, ts, ts);
                ctx.fillStyle = '#7d5a34';
                ctx.fillRect(x, y, ts, 5);
                ctx.fillStyle = '#4a7c3f';
                for (let g = 0; g < 3; g++) {
                    ctx.fillRect(x + g * 12 + 6, y - 3, 3, 8);
                }
            } else if (tile === 3) {
                // 出口 - 绿色发光传送门
                const pulse = 0.7 + 0.3 * Math.sin(Date.now() / 500);
                ctx.fillStyle = '#1a5c1a';
                ctx.fillRect(x, y, ts, ts);
                ctx.fillStyle = `rgba(50, 255, 50, ${pulse})`;
                ctx.fillRect(x + 4, y - 36, ts - 8, ts + 32);
                ctx.fillStyle = '#fff';
                ctx.font = '18px "Microsoft YaHei"';
                ctx.textAlign = 'center';
                ctx.fillText('🏁', x + ts / 2, y + ts / 2 + 6);
            } else if (tile === 4) {
                // 平台 - 木质平台，可从下方穿过
                ctx.fillStyle = '#8B6914';
                ctx.fillRect(x, y, ts, 8);
                ctx.fillStyle = '#A07818';
                ctx.fillRect(x, y, ts, 3);
                ctx.strokeStyle = '#6B4F10';
                ctx.lineWidth = 1;
                ctx.strokeRect(x, y, ts, 8);
            } else if (tile === 5) {
                // 生命药水 - 红色闪烁
                const bob = Math.sin(Date.now() / 300 + col) * 3;
                ctx.fillStyle = '#ff4466';
                ctx.beginPath();
                ctx.arc(x + ts / 2, y + ts / 2 + bob, 12, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#fff';
                ctx.font = '14px "Microsoft YaHei"';
                ctx.textAlign = 'center';
                ctx.fillText('❤️', x + ts / 2, y + ts / 2 + 5 + bob);
            } else if (tile === 6) {
                // 攻击强化 - 金色闪烁
                const bob = Math.sin(Date.now() / 300 + col + 1) * 3;
                ctx.fillStyle = '#ffaa00';
                ctx.beginPath();
                ctx.arc(x + ts / 2, y + ts / 2 + bob, 12, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#fff';
                ctx.font = '14px "Microsoft YaHei"';
                ctx.textAlign = 'center';
                ctx.fillText('⚡', x + ts / 2, y + ts / 2 + 5 + bob);
            } else if (tile === 7) {
                // 钥匙 - 金色闪烁
                const bob = Math.sin(Date.now() / 300 + col + 2) * 3;
                ctx.fillStyle = '#ffd700';
                ctx.beginPath();
                ctx.arc(x + ts / 2, y + ts / 2 + bob, 12, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#fff';
                ctx.font = '16px "Microsoft YaHei"';
                ctx.textAlign = 'center';
                ctx.fillText('🔑', x + ts / 2, y + ts / 2 + 6 + bob);
            }
        }
    }
}

// ============================================================
// 怪物渲染
// ============================================================
function drawMonsters(monsters) {
    if (!monsters) return;

    monsters.forEach(function(m) {
        if (m.is_dead) return;

        const mx = m.x;
        const my = m.y;
        let size = 30;

        // 不同种类不同颜色和大小
        let bodyColor = '#e74c3c';  // 普通 - 红
        if (m.monster_type === 'fast') {
            bodyColor = '#f39c12';   // 快速 - 黄，较小
            size = 24;
        } else if (m.monster_type === 'tank') {
            bodyColor = '#8e44ad';   // 坦克 - 紫，较大
            size = 38;
        } else if (m.monster_type === 'boss') {
            bodyColor = '#e74c3c';   // Boss - 暗红，巨大
            size = 50;
        }

        // 受伤闪烁
        if (m.damage_flash > 0) {
            bodyColor = '#fff';
        }

        // 怪物身体
        ctx.fillStyle = bodyColor;
        ctx.fillRect(mx, my, size, size);

        // 眼睛（位置随大小调整）
        ctx.fillStyle = '#fff';
        const eyeOffset = m.facing === 'right' ? 3 : -3;
        const eyeSize = Math.max(5, size / 4);
        ctx.fillRect(mx + size * 0.25 + eyeOffset, my + size * 0.2, eyeSize, eyeSize);
        ctx.fillRect(mx + size * 0.6 + eyeOffset, my + size * 0.2, eyeSize, eyeSize);
        ctx.fillStyle = '#000';
        ctx.fillRect(mx + size * 0.25 + eyeOffset + 2, my + size * 0.2 + 2, eyeSize / 2, eyeSize / 2);
        ctx.fillRect(mx + size * 0.6 + eyeOffset + 2, my + size * 0.2 + 2, eyeSize / 2, eyeSize / 2);

        // Boss头顶标记
        if (m.monster_type === 'boss') {
            ctx.fillStyle = '#f5c842';
            ctx.font = 'bold 14px "Microsoft YaHei"';
            ctx.textAlign = 'center';
            ctx.fillText('👑BOSS', mx + size / 2, my - 14);
        }

        // 血条
        const hpRatio = m.hp / m.max_hp;
        const barW = size;
        const barH = m.monster_type === 'boss' ? 6 : 4;
        const barY = my - 8;
        ctx.fillStyle = '#333';
        ctx.fillRect(mx, barY, barW, barH);
        ctx.fillStyle = hpRatio > 0.5 ? '#27ae60' : hpRatio > 0.25 ? '#f39c12' : '#e74c3c';
        ctx.fillRect(mx, barY, barW * hpRatio, barH);

        // AI状态标签
        if (m.state === 'chase') {
            ctx.fillStyle = '#f39c12';
            ctx.font = '10px "Microsoft YaHei"';
            ctx.textAlign = 'center';
            ctx.fillText('!', mx + size / 2, my - 12);
        }
    });
}

// ============================================================
// 玩家渲染
// ============================================================
function drawPlayer(player) {
    if (!player || player.is_dead) return;

    const px = player.x;
    const py = player.y;
    const pw = 30;
    const ph = 40;

    // 受伤无敌闪烁
    if (player.damage_timer && Math.floor(player.damage_timer * 10) % 2 === 0) {
        ctx.globalAlpha = 0.5;
    }

    // 攻击强化光环
    if (player.atk_boosted) {
        const glowAlpha = 0.3 + 0.15 * Math.sin(Date.now() / 200);
        ctx.fillStyle = `rgba(255, 170, 0, ${glowAlpha})`;
        ctx.fillRect(px - 5, py - 5, pw + 10, ph + 10);
    }

    // 身体
    ctx.fillStyle = player.atk_boosted ? '#ff8800' : '#4a90d9';
    ctx.fillRect(px, py, pw, ph);

    // 头部
    ctx.fillStyle = '#ffddaa';
    ctx.fillRect(px + 5, py, 20, 16);

    // 眼睛
    ctx.fillStyle = '#fff';
    const eyeX = player.facing === 'right' ? px + 16 : px + 8;
    ctx.fillRect(eyeX, py + 4, 6, 6);
    ctx.fillStyle = '#000';
    ctx.fillRect(eyeX + 2, py + 5, 3, 3);

    // 武器（攻击时闪烁）
    if (player.attacking && player.attack_frame > 0) {
        ctx.fillStyle = '#f5c842';
        const weaponX = player.facing === 'right' ? px + pw : px - 20;
        ctx.fillRect(weaponX, py + 10, 20, 8);
    }

    // 朝向指示器
    ctx.fillStyle = player.facing === 'right' ? '#4af' : '#f4a';
    ctx.fillRect(px + 10, py + ph, 10, 4);

    ctx.globalAlpha = 1.0;
}

// ============================================================
// UI渲染（血条、关卡信息、状态文字）
// ============================================================
function drawUI(state) {
    const player = state.player;
    if (!player) return;

    // --- 血条 ---
    const barX = 20;
    const barY = 15;
    const barW = 200;
    const barH = 20;

    // 背景
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(barX - 2, barY - 2, barW + 4, barH + 4);

    // 血量条
    const hpRatio = player.hp / player.max_hp;
    const hpColor = hpRatio > 0.5 ? '#27ae60' : hpRatio > 0.25 ? '#f39c12' : '#e74c3c';
    ctx.fillStyle = '#333';
    ctx.fillRect(barX, barY, barW, barH);
    ctx.fillStyle = hpColor;
    ctx.fillRect(barX, barY, barW * hpRatio, barH);

    // HP文字
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px "Microsoft YaHei"';
    ctx.textAlign = 'left';
    ctx.fillText('HP: ' + player.hp + ' / ' + player.max_hp, barX + 5, barY + 15);

    // --- 攻击强化指示器 ---
    if (player.atk_boosted) {
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(barX - 2, barY + barH + 4, barW + 4, 18);
        ctx.fillStyle = '#ffaa00';
        ctx.fillRect(barX, barY + barH + 6, barW, 14);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 11px "Microsoft YaHei"';
        ctx.fillText('⚡ ATK UP ' + player.atk_boost_sec + 's', barX + 5, barY + barH + 17);
    }

    // --- 关卡信息 ---
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(600, 10, 180, 65);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 14px "Microsoft YaHei"';
    ctx.textAlign = 'right';
    ctx.fillText(state.level_name || '未知关卡', 770, 30);
    ctx.font = '12px "Microsoft YaHei"';
    ctx.fillText('存档档位: ' + saveSlot, 770, 46);
    // 钥匙状态
    ctx.fillStyle = player.has_key ? '#ffd700' : '#888';
    ctx.fillText(player.has_key ? '🔑 钥匙已获得' : '🔑 未获得钥匙', 770, 65);

    // --- 状态消息 ---
    if (state.message) {
        ctx.fillStyle = 'rgba(0,0,0,0.5)';
        ctx.fillRect(250, 560, 300, 30);
        ctx.fillStyle = '#f5c842';
        ctx.font = 'bold 14px "Microsoft YaHei"';
        ctx.textAlign = 'center';
        ctx.fillText(state.message, 400, 582);
    }

    // --- 暂停/胜利/死亡状态文字 ---
    if (state.status === 'paused') {
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(0, 0, 800, 600);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 40px "Microsoft YaHei"';
        ctx.textAlign = 'center';
        ctx.fillText('⏸ 游戏暂停', 400, 300);
        ctx.font = '18px "Microsoft YaHei"';
        ctx.fillText('按ESC继续', 400, 340);
    }
}

// ============================================================
// 浮层弹窗
// ============================================================
function showOverlay(title, message, buttons) {
    const overlay = document.getElementById('overlay');
    const titleEl = document.getElementById('overlay-title');
    const msgEl = document.getElementById('overlay-message');
    const btnsEl = document.getElementById('overlay-buttons');

    titleEl.textContent = title;
    titleEl.className = title.includes('通关') ? 'won' : title.includes('阵亡') ? 'dead' : 'pause';
    msgEl.textContent = message;

    // 构建按钮
    btnsEl.innerHTML = '';
    buttons.forEach(function(btn) {
        const btnEl = document.createElement('button');
        btnEl.className = 'overlay-btn ' + (btn.cls || 'resume');
        btnEl.textContent = btn.text;
        btnEl.onclick = function() {
            hideOverlay();
            if (btn.action) btn.action();
        };
        btnsEl.appendChild(btnEl);
    });

    overlay.style.display = 'flex';
}

function hideOverlay() {
    document.getElementById('overlay').style.display = 'none';
}

// ============================================================
// 启动渲染循环
// ============================================================
animFrameId = requestAnimationFrame(renderLoop);

// ============================================================
// 页面卸载时清理
// ============================================================
window.addEventListener('beforeunload', function() {
    if (animFrameId) {
        cancelAnimationFrame(animFrameId);
    }
    if (socket) {
        socket.disconnect();
    }
});
