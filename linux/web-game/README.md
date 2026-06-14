# ⚔️ 勇者冒险 - 网页2D横版闯关游戏

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](game-app/main.py)

纯网页运行、无需客户端、Docker一键部署的2D横版闯关小游戏。  
浏览器打开即玩，支持**电脑 + 手机**双端操作，包含完整**账号系统、三档存档、数据库持久化**。

---

## 📋 目录

- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [部署步骤](#部署步骤)
- [局域网访问方法](#局域网访问方法)
- [手机电脑游玩方法](#手机电脑游玩方法)
- [按键操作说明](#按键操作说明)
- [游戏玩法](#游戏玩法)
- [重置数据方法](#重置数据方法)
- [项目结构](#项目结构)
- [API接口](#api接口)
- [常见问题](#常见问题)

---

## 🛠 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端渲染 | HTML5 Canvas + JavaScript | 游戏画面全部Canvas渲染 |
| 实时通信 | Flask-SocketIO + WebSocket | 低延迟游戏状态同步 |
| 后端逻辑 | Python Flask | 碰撞、AI、战斗、存档计算 |
| 数据库 | MySQL 8.0 | Docker容器化持久化存储 |
| 密码安全 | bcrypt | 哈希加密，禁止明文 |
| 部署 | Docker + docker-compose | 一键启动 |

---

## 🚀 快速开始

### 前提条件

- 已安装 [Docker](https://www.docker.com/) 和 docker-compose
- 端口 `5000` 未被占用

### 一键启动

```bash
# 1. 进入项目目录
cd web-game

# 2. 启动所有服务（首次启动会自动构建镜像）
docker-compose up -d

# 3. 查看运行日志
docker-compose logs -f

# 4. 浏览器打开
# http://localhost:5000
```

启动成功后：
1. 打开浏览器访问 `http://localhost:5000`
2. 注册账号 → 登录 → 创建存档 → 开始游戏！

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

---

## 📦 部署步骤（详细）

### 1. 确保 Docker 环境就绪

```bash
# 查看Docker版本
docker --version
docker-compose --version
```

### 2. 构建并启动

```bash
cd web-game

# 构建镜像并后台启动
docker-compose up -d --build

# 查看容器状态
docker-compose ps
```

应该看到两个容器都在运行：
- `mysql-game` — MySQL 数据库
- `game-app` — Flask 游戏服务

### 3. 访问游戏

浏览器打开：`http://localhost:5000`

### 4. 查看日志（排错用）

```bash
# 查看所有容器日志
docker-compose logs -f

# 只看游戏服务日志
docker-compose logs -f game-app

# 只看数据库日志
docker-compose logs -f mysql-game
```

---

## 🌐 局域网访问方法

让同一局域网内的其他设备（室友、同学、手机）也能访问你的游戏：

### 步骤

1. **查看你电脑的局域网IP地址**

   Windows：打开CMD，输入 `ipconfig`，找到 `IPv4 地址`（例如 `192.168.1.105`）

2. **其他设备在浏览器输入**

   ```
   http://你的局域网IP:5000
   ```

   例如：`http://192.168.1.105:5000`

3. **确保防火墙放行5000端口**

   Windows防火墙通常会自动提示，点击"允许访问"即可。  
   如果没有提示，手动添加入站规则：控制面板 → Windows Defender防火墙 → 高级设置 → 入站规则 → 新建规则 → 端口5000 → 允许连接。

### 注意

- 所有设备必须在**同一局域网**内（连接同一个WiFi）
- 主机电脑的防火墙需要放行5000端口
- 如果使用公网穿透工具（如 ngrok、frp），可以实现外网访问

---

## 👥 分享给他人游玩

### 方法一：局域网分享（同WiFi）

这是最简单的方式，适合宿舍、教室、家里同一网络环境：

1. 你的电脑启动游戏：`docker-compose up -d`
2. 告诉对方你的局域网IP（`ipconfig` 查看 IPv4 地址）
3. 对方浏览器输入 `http://你的IP:5000` 即可

> ⚠️ 你关电脑后对方就无法访问了

### 方法二：ngrok 内网穿透（临时外网分享）

免费、快速，适合临时给朋友演示：

```bash
# 1. 下载 ngrok (https://ngrok.com/download)
# 2. 注册账号获取 authtoken
# 3. 启动穿透
ngrok http 5000

# 4. ngrok 会给你一个公网地址，例如：
#    https://xxxx.ngrok-free.app
# 5. 把这个地址发给任何人，全球都能访问
```

> 免费版 ngrok 地址每次重启会变化，有速率限制

### 方法三：frp 内网穿透（长期稳定）

需要一台有公网IP的云服务器：

```bash
# 服务器端 (frps.ini)
[common]
bind_port = 7000
vhost_http_port = 8080

# 你电脑端 (frpc.ini)
[web-game]
type = http
local_port = 5000
custom_domains = game.你的域名.com
```

### 方法四：部署到云服务器（最稳定）

买一台云服务器（阿里云/腾讯云/华为云，学生优惠几十块/月），把项目上传部署：

```bash
# 在云服务器上
git clone <你的项目>
cd web-game
docker-compose up -d
# 配置安全组放行5000端口
# 访问 http://服务器公网IP:5000
```

**推荐配置**：2核2G，CentOS/Ubuntu，安装 Docker 即可

### 分享清单

| 需要给对方的东西 | 说明 |
|-----------------|------|
| 访问地址 | `http://IP:5000` 或 ngrok地址 |
| 操作说明 | [`docs/GAME_GUIDE.md`](docs/GAME_GUIDE.md)（游戏玩法手册） |
| 无需安装 | 对方的手机/电脑浏览器打开即可 |

---

## 📱💻 手机电脑游玩方法

### 电脑端

直接用浏览器打开 `http://localhost:5000`（或局域网IP），使用键盘操作。

### 手机端

1. 确保手机和电脑连接**同一WiFi**
2. 手机浏览器打开 `http://电脑局域网IP:5000`
3. 登录后，游戏页面会自动显示**屏幕底部虚拟按键**
4. 使用虚拟方向键 + 攻击/存档/暂停按钮游玩

### 触屏适配说明

- 系统自动检测触屏设备，显示虚拟按键
- 桌面端自动隐藏虚拟按键，显示键盘提示
- 画布自适应屏幕宽度（最大800px）

---

## 🎮 按键操作说明

### 电脑键盘

| 按键 | 功能 |
|------|------|
| ← → 方向键 | 左右移动 |
| ↑ 方向键 | 跳跃 |
| 空格键 | 攻击 |
| S 键 | 手动存档 |
| ESC | 暂停/继续 |

### 手机触屏

| 虚拟按键 | 功能 |
|----------|------|
| ▲▼◀▶ 方向键 | 移动/跳跃 |
| ⚔️ 攻击 | 攻击怪物 |
| 💾 存档 | 手动存档 |
| ⏯️ 暂停 | 暂停/继续 |

---

## 🎯 游戏玩法

### 目标

消灭关卡中所有怪物，到达地图右侧的绿色出口（🏁），即可通关进入下一关。

### 关卡

共 **5个关卡**，难度递增：

1. **新手森林** — 2只怪物，简单地形
2. **暗黑洞穴** — 3只怪物，有障碍物
3. **幽灵走廊** — 4只怪物，多条路径
4. **熔岩地牢** — 5只怪物，复杂地形
5. **魔王城堡** — 6只怪物（含Boss），最终关卡

### 战斗

- 靠近怪物按攻击键（空格/攻击按钮）
- 怪物有血条，消灭后不再刷新
- 被怪物碰到会扣血，有无敌时间保护
- 通关后自动恢复部分血量

### 存档

- 每个账号拥有 **3个独立存档档位**
- **手动存档**：按S键 / 点存档按钮
- **自动存档**：每30秒自动存档 + 通关时自动存档
- 死亡后可从大厅重新读取存档
- 存档保存在MySQL数据库，重启不丢失

---

## 🔄 重置数据方法

### 方法一：清空数据库（彻底重置所有数据）

```bash
cd web-game

# 停止并删除容器和数据卷
docker-compose down -v

# 重新启动（数据库将重新初始化）
docker-compose up -d --build
```

> ⚠️ `-v` 参数会删除所有游戏数据，包括所有账号和存档！

### 方法二：仅删除某个存档

在大厅页面点击对应档位的"新建存档"按钮，确认覆盖即可。

### 方法三：仅删除MySQL数据卷

```bash
# 查看数据卷
docker volume ls | grep game

# 删除数据卷
docker volume rm web-game_mysql_data

# 重启
docker-compose up -d
```

---

## 📂 项目结构

```
web-game/
├── .gitignore                   # Git 忽略规则
├── .env.example                 # 环境变量模板（需复制为 .env 并修改）
├── .env                         # 环境变量（敏感信息，不纳入版本控制）
├── LICENSE                      # MIT 开源许可证
├── README.md                    # 项目说明 & 部署教程
├── docker-compose.yml           # Docker 编排配置
├── docs/
│   ├── GAME_GUIDE.md            # 游戏玩法手册
│   └── report/                  # 课程实验报告 & 截图
│       ├── HOMEWORK_REPORT.md
│       └── *.png
├── mysql-db/
│   └── init.sql                 # 数据库建表脚本（自动执行）
└── game-app/
    ├── Dockerfile               # Flask 应用 Docker 镜像
    ├── requirements.txt         # Python 依赖
    ├── main.py                  # Flask 主入口 + SocketIO + 游戏循环
    ├── db/
    │   └── db_conn.py           # 数据库连接 & 参数化查询
    ├── account/
    │   └── auth_logic.py        # 注册/登录/登出 + bcrypt
    ├── game_logic/
    │   ├── player.py            # 玩家类（移动、攻击、受伤）
    │   ├── monster.py           # 怪物类（AI 巡逻/追击/攻击）
    │   ├── map_loader.py        # 5 关卡地图 & 碰撞检测
    │   └── save_manager.py      # 3 档位存档管理
    ├── templates/
    │   ├── login.html           # 登录/注册页面
    │   ├── hall.html            # 游戏大厅（3 存档卡片）
    │   └── game.html            # Canvas 游戏页面
    └── static/
        ├── css/
        │   └── style.css        # 全局样式
        └── js/
            ├── login.js         # 登录/注册逻辑
            ├── hall.js          # 大厅逻辑
            └── game.js          # Canvas 渲染 + 输入处理
```

---

## 📡 API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（自动跳转） |
| GET | `/login` | 登录/注册页面 |
| POST | `/login` | 登录API |
| POST | `/register` | 注册API |
| GET | `/logout` | 退出登录 |
| GET | `/hall` | 游戏大厅（需登录） |
| GET | `/game` | 游戏页面（需登录） |
| GET | `/api/user` | 获取当前用户信息 |
| GET | `/api/saves` | 获取3个存档信息 |
| POST | `/api/save/create` | 创建/覆盖存档 |

### WebSocket事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `join_game` | 客户端→服务端 | 进入游戏（携带存档档位） |
| `player_input` | 客户端→服务端 | 按键输入 |
| `save_game` | 客户端→服务端 | 手动存档 |
| `pause_game` | 客户端→服务端 | 暂停/继续 |
| `return_hall` | 客户端→服务端 | 返回大厅 |
| `game_state` | 服务端→客户端 | 游戏状态推送（30FPS） |
| `game_event` | 服务端→客户端 | 游戏事件（受伤/死亡/通关） |

---

## ❓ 常见问题

### Q: 启动失败，端口被占用？

修改 `docker-compose.yml` 中的端口映射，例如将 `5000:5000` 改为 `8080:5000`，然后访问 `http://localhost:8080`。

### Q: MySQL启动很慢？

首次启动需要初始化数据库，等待约30秒。可以用 `docker-compose logs mysql-game` 查看MySQL启动状态。

### Q: 网页显示"无法连接到游戏服务器"？

1. 检查容器是否都在运行：`docker-compose ps`
2. 等待MySQL完全就绪（game-app会在MySQL就绪后启动）
3. 查看日志：`docker-compose logs game-app`

### Q: 手机访问不了？

1. 确认手机和电脑在同一WiFi
2. 检查电脑防火墙是否放行5000端口
3. 确保使用电脑的局域网IP（不是127.0.0.1）

### Q: 数据存在哪里？

- MySQL数据存储在Docker数据卷 `web-game_mysql_data` 中
- 执行 `docker-compose down` 不会删除数据
- 只有 `docker-compose down -v` 会删除所有数据

### Q: 如何修改数据库密码？

编辑 `.env` 文件中的密码配置，然后重启：
```bash
docker-compose down -v
docker-compose up -d --build
```

> ⚠️ 修改密码后需要删除旧数据卷，因为旧密码已写入数据库初始化脚本。

---

## 📝 开发说明

### 项目特点

- ✅ 纯网页运行，无需客户端，无需Pygame
- ✅ 服务端权威游戏逻辑（防作弊）
- ✅ WebSocket实时双向通信（30FPS游戏循环）
- ✅ bcrypt密码加密 + 参数化SQL查询（防注入）
- ✅ 电脑键盘 + 手机触屏双适配
- ✅ Docker容器化部署，一键启动
- ✅ 5个手工设计关卡 + 怪物AI状态机
- ✅ 3档位存档 + 自动/手动存档 + 数据持久化

---

**🎉 祝你游戏愉快！如有问题，请检查日志或联系开发者。**
