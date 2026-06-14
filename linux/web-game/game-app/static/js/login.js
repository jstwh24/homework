/**
 * 登录/注册页面逻辑
 * - 标签切换（登录/注册）
 * - 表单提交API调用
 * - 响应处理 & 页面跳转
 */

// ============================================================
// 标签切换
// ============================================================
let currentTab = 'login';

function switchTab(tab) {
    currentTab = tab;
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabs = document.querySelectorAll('.tab-btn');

    tabs.forEach(btn => btn.classList.remove('active'));

    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabs[0].classList.add('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabs[1].classList.add('active');
    }

    // 清除消息
    document.getElementById('login-msg').textContent = '';
    document.getElementById('login-msg').className = 'msg-text';
    document.getElementById('reg-msg').textContent = '';
    document.getElementById('reg-msg').className = 'msg-text';
}

// ============================================================
// 登录
// ============================================================
async function doLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const msgEl = document.getElementById('login-msg');

    // 前端校验
    if (!username || !password) {
        showMsg(msgEl, '请输入用户名和密码', 'error');
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (data.success) {
            showMsg(msgEl, data.message, 'success');
            // 跳转大厅
            setTimeout(() => {
                window.location.href = '/hall';
            }, 500);
        } else {
            showMsg(msgEl, data.message, 'error');
        }
    } catch (err) {
        showMsg(msgEl, '网络错误，请稍后重试', 'error');
        console.error('Login error:', err);
    }
}

// ============================================================
// 注册
// ============================================================
async function doRegister() {
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value;
    const msgEl = document.getElementById('reg-msg');

    // 前端校验
    if (!username || username.length < 2) {
        showMsg(msgEl, '用户名至少2个字符', 'error');
        return;
    }
    if (!password || password.length < 4) {
        showMsg(msgEl, '密码至少4个字符', 'error');
        return;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (data.success) {
            showMsg(msgEl, data.message + ' 请切换到登录页面。', 'success');
            // 清空表单
            document.getElementById('reg-username').value = '';
            document.getElementById('reg-password').value = '';
            // 自动切换到登录
            setTimeout(() => switchTab('login'), 1500);
        } else {
            showMsg(msgEl, data.message, 'error');
        }
    } catch (err) {
        showMsg(msgEl, '网络错误，请稍后重试', 'error');
        console.error('Register error:', err);
    }
}

// ============================================================
// 工具函数
// ============================================================
function showMsg(el, message, type) {
    el.textContent = message;
    el.className = 'msg-text ' + type;
}

// ============================================================
// 回车键提交
// ============================================================
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        if (currentTab === 'login') {
            doLogin();
        } else {
            doRegister();
        }
    }
});
