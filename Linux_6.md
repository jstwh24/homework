好的，我重新调用一次，把完整响应展示出来。

拿到 token，接下来调用 `get_system_info`：

---

## 📋 完整调用结果

### 🔧 工具一：`get_auth_token`

**原始返回（JSON）：**
```json
{
  "token": "af9154bfc962c8caed89d38d1178c015",
  "note": "请在调用 get_system_info 时将 token 作为 api_key 参数传入"
}
```

| 字段 | 值 |
|------|-----|
| `token` | `af9154bfc962c8caed89d38d1178c015` |
| `note` | 请在调用 get_system_info 时将 token 作为 api_key 参数传入 |

`isError`: ❌ `false`

---

### 🔧 工具二：`get_system_info`

**参数：**
```json
{
  "api_key": "af9154bfc962c8caed89d38d1178c015"
}
```

**原始返回（JSON）：**
```json
{
  "cpu": {
    "percent": 9.7
  },
  "memory": {
    "total_gb": 15.7,
    "used_gb": 11.6,
    "percent": 74.1
  },
  "disk": {
    "total_gb": 300.0,
    "used_gb": 217.3,
    "percent": 72.4
  }
}
```

| 类别 | 指标 | 数值 |
|------|------|------|
| 🖥️ **CPU** | 使用率 | **9.7%** |
| 🧠 **内存** | 总量 | **15.7 GB** |
| | 已用 | **11.6 GB** |
| | 使用率 | **74.1%** |
| 💾 **磁盘** | 总量 | **300.0 GB** |
| | 已用 | **217.3 GB** |
| | 使用率 | **72.4%** |

`isError`: ❌ `false`

---

✅ 两个工具均调用成功，无任何错误。