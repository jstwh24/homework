/**
 * 游戏大厅页面逻辑
 * - 加载用户信息 & 3个存档档位
 * - 创建/覆盖存档
 * - 读取存档进入游戏
 */

// ============================================================
// 页面初始化
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
    loadSaves();
});

// ============================================================
// 加载用户信息
// ============================================================
async function loadUserInfo() {
    try {
        const response = await fetch('/api/user');
        const data = await response.json();

        if (data.logged_in) {
            document.getElementById('username-display').textContent = data.username;
            document.getElementById('total-clear').textContent = data.total_clear;
        } else {
            // 未登录，跳转登录页
            window.location.href = '/login';
        }
    } catch (err) {
        console.error('加载用户信息失败:', err);
    }
}

// ============================================================
// 加载存档列表
// ============================================================
async function loadSaves() {
    try {
        const response = await fetch('/api/saves');
        const data = await response.json();
        const saves = data.saves;

        saves.forEach(function(save) {
            const slot = save.save_slot;
            const infoEl = document.getElementById('slot-info-' + slot);
            const playBtn = document.getElementById('btn-play-' + slot);

            if (save.has_data) {
                // 显示存档信息
                infoEl.innerHTML =
                    '<p><strong>' + save.player_name + '</strong></p>' +
                    '<p>关卡: ' + save.current_level + '</p>' +
                    '<p>HP: ' + save.current_hp + ' / ' + save.max_hp + '</p>' +
                    '<p>存档时间: ' + save.save_time + '</p>';
                playBtn.disabled = false;
                playBtn.textContent = '读取存档';
            } else {
                // 空档位
                infoEl.innerHTML = '<p class="slot-empty">空档位</p>';
                playBtn.disabled = true;
                playBtn.textContent = '读取存档';
            }
        });
    } catch (err) {
        console.error('加载存档失败:', err);
        showMsg('加载存档信息失败');
    }
}

// ============================================================
// 创建（覆盖）存档
// ============================================================
async function createSlot(saveSlot) {
    if (!confirm('确定要在存档' + saveSlot + '创建新存档吗？\n旧存档将被覆盖！')) {
        return;
    }

    try {
        const response = await fetch('/api/save/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ save_slot: saveSlot }),
        });

        const data = await response.json();

        if (data.success) {
            showMsg('存档' + saveSlot + '创建成功！');
            loadSaves(); // 刷新存档列表
        } else {
            showMsg(data.message || '创建失败');
        }
    } catch (err) {
        console.error('创建存档失败:', err);
        showMsg('创建存档失败');
    }
}

// ============================================================
// 读取存档进入游戏
// ============================================================
function loadOrCreate(saveSlot) {
    const playBtn = document.getElementById('btn-play-' + saveSlot);

    if (playBtn.disabled) {
        // 空档位，提示先创建
        showMsg('请先创建存档');
        return;
    }

    // 跳转游戏页面，携带存档档位参数
    window.location.href = '/game?slot=' + saveSlot;
}

// ============================================================
// 退出登录
// ============================================================
function doLogout() {
    if (confirm('确定要退出登录吗？')) {
        window.location.href = '/logout';
    }
}

// ============================================================
// 提示消息
// ============================================================
function showMsg(message) {
    const el = document.getElementById('hall-msg');
    el.textContent = message;
    el.className = 'msg-text';
    setTimeout(function() {
        el.textContent = '';
    }, 3000);
}
