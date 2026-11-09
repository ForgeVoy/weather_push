# 🌤️ 每日天气微信推送

> ☀️ 用 Python 拉取免费天气预报，准时送到微信 —— 自己、朋友、家人各一份。

用 Python 从 [Open-Meteo](https://open-meteo.com/) 拉取免费天气预报，并推送到微信。仓库提供两种推送方式：**Server 酱（方糖）** 单通道版，以及 **微信公众平台测试号模板消息** 多用户多城市版。

<p align="center">
  🐍 Python 3 &nbsp;·&nbsp; 📦 零依赖 &nbsp;·&nbsp; 🌍 Open-Meteo &nbsp;·&nbsp; 💬 微信推送
</p>

## 📁 项目结构

```text
weather/
├── 🔔 weather_push.py           # Server 酱版：单城市、Markdown 推送
├── 📱 weather_push_mp.py        # 测试号版：多用户、朋友/情侣两套模板
├── ✅ check_template_assign.py  # 校验模板占位符、字段长度与后台一致性
├── 👥 friend_template.txt       # 朋友向模板正文（同步自代码，供后台复制）
├── 💕 lp_template.txt           # 情侣向模板正文
└── 📖 README.md
```

---

## ✨ 功能概览

| 能力       | `weather_push.py` 🍬              | `weather_push_mp.py` 📲                                                           |
| ---------- | --------------------------------- | --------------------------------------------------------------------------------- |
| 天气数据源 | 🌐 Open-Meteo                     | 🌐 Open-Meteo                                                                     |
| 推送渠道   | [Server 酱](https://sct.ftqq.com) | 微信公众平台测试号                                                                |
| 用户规模   | 👤 单 SendKey                     | 👥 多 `openid`，每人可不同城市                                                    |
| 消息样式   | 📝 Markdown 富文本                | 📋 模板消息（字段有长度限制）                                                     |
| 额外内容   | 🧥 穿衣/带伞等简短提示            | 🤝 朋友：箴言、氛围、生活指数、日出日落 · 💑 情侣：恋爱天数、婚龄、生日、双语情话 |

---

## 🛠️ 环境要求

- 🐍 **Python 3**（仅标准库：`json`、`urllib`、`datetime` 等，无需 `pip install`）
- 🌐 可访问 `api.open-meteo.com`；测试号版还需访问 `api.weixin.qq.com`

---

## 🍬 方案一：Server 酱 · `weather_push.py`

> ⚡ 适合个人快速试用，免费档约每天 **5 条** 推送。

### ⚙️ 配置

在 `weather_push.py` 顶部修改：

| 变量             | 说明                                                                             |
| ---------------- | -------------------------------------------------------------------------------- |
| `SENDKEY` 🔑     | 在 [方糖 SendKey](https://sct.ftqq.com/sendkey) 微信扫码登录后获取（`SCT` 开头） |
| `CITY` 📍        | 城市名                                                                           |
| `LAT` / `LON` 🗺️ | 经纬度（Open-Meteo 按坐标查询）                                                  |

### ▶️ 运行

```bash
python weather_push.py
```

脚本会打印推送标题与正文，并通过 Server 酱发到微信。若 `SENDKEY` 仍为占位符，会提示先完成配置。

### 📬 推送内容说明

- 🕐 **当前**：天气现象、温度、湿度、风速
- 📅 **今天 / 明天**：现象、温度区间、降水概率、UV
- 💡 **温馨提示**：带伞 ☔、防晒 🧴、保暖 🧣 等（按天气自动生成）

---

## 📲 方案二：测试号模板消息 · `weather_push_mp.py`

> 👥 支持为每位关注者配置不同城市与消息风格；同一经纬度的用户会 **共用一次** 天气请求（缓存）。

### 📋 前置准备

1. 🔐 登录 [微信公众平台测试号](https://mp.weixin.qq.com/debug/cgi-bin/sandboxinfo?action=showinfo&t=sandbox/index)
2. 📝 记录 **appID**、**appsecret**
3. 📱 让接收者扫码关注测试号，在「用户列表」中复制各人的 **openid**
4. 📄 在「模板消息接口」中新增两条模板，正文分别与 `friend_template.txt`、`lp_template.txt` 一致（可用 `--dry-run` 自动回写这两个文件后再复制）
5. 🆔 将得到的 **template_id** 填入代码中的 `Other_template_id`、`Lp_template_id`

### ⚙️ 配置说明

在 `weather_push_mp.py` 的「配置区」填写：

- `APP_ID`、`APP_SECRET`
- `Lp_template_id`（情侣 💕）、`Other_template_id`（朋友 🤝）
- `USERS` 列表，每项常见字段：

| 字段              | 说明                                   |
| ----------------- | -------------------------------------- |
| `name`            | 🏷️ 备注名（日志用）                    |
| `openid`          | 测试号用户 openid                      |
| `template_id`     | 使用的模板 ID                          |
| `style`           | `friend` 🤝 或 `romantic` 💕           |
| `city`            | 📍 展示用城市名                        |
| `lat` / `lon`     | 🗺️ 经纬度                              |
| `love_start_date` | 仅 `romantic`：恋爱起始日 `YYYY-MM-DD` |
| `marriage_date`   | 仅 `romantic`：结婚日 `YYYY-MM-DD`     |
| `birthday`        | 仅 `romantic`：`MM-DD` 🎂              |
| `pet_name`        | 仅 `romantic`：称呼，用于生日文案      |

### 🎨 两种模板风格

#### 🤝 朋友（`friend`）

- 📍 日期位置、☁️ 今明天气、🌡️ 温区、💧 降水、🌅 日出日落
- 🧥 穿衣 / 带伞等生活指数（`tip`）
- 📖 按日轮换的箴言（`quote`）与氛围 + 旁白（`vibe`）

#### 💕 情侣（`romantic`）

- ☁️ 天气与温区
- 💕 恋爱天数与婚龄（`heart`）
- 🎂 生日倒计时或当天祝福（`birthday1`）
- 💬 精简双语情话（`note_en` / `note_ch`）

> ⚠️ 微信模板对单字段约 **20 字**、全文渲染约 **200 字** 有限制；代码内 `fit_*_data_for_wechat` 会自动截断与压缩。首尾各 2 行占位（`pad1`～`pad4`）用于抵消部分客户端对正文首尾的裁切。

### ▶️ 运行

```bash
# 👀 仅组装并预览，不发送；并更新 friend_template.txt / lp_template.txt
python weather_push_mp.py --dry-run

# 🚀 正式推送
python weather_push_mp.py
```

### ✅ 模板校验

```bash
# 同时检查朋友 + 情侣模板
python check_template_assign.py

# 只检查其中一套
python check_template_assign.py --friend
python check_template_assign.py --lp
```

校验脚本会：对比代码中的模板字符串与微信后台、检查占位符与赋值字段是否一致、标注超长字段，并模拟「裁掉首尾各 2 行」后的首屏可见内容。

---

## 🌐 天气数据

- 🔗 API：`https://api.open-meteo.com/v1/forecast`
- 🏷️ 使用 WMO 天气代码映射为中文描述（两套脚本共用同类映射表）
- 🌅 朋友版额外请求 `sunrise`、`sunset` 用于昼长与日出日落行

---

## ⏰ 定时任务建议

可用系统计划任务每日固定时间执行，例如 Windows 任务计划程序或 Linux `cron`：

```text
# 示例：每天 7:00 推送（路径按本机修改）
0 7 * * * /usr/bin/python3 /path/to/weather/weather_push_mp.py
```

| 平台             | 方式                        |
| ---------------- | --------------------------- |
| 🪟 Windows       | 任务计划程序 → 创建基本任务 |
| 🐧 Linux / macOS | `crontab -e`                |

---

## ❓ 常见问题（测试号）

| errcode | 含义 / 处理                                                            |
| ------- | ---------------------------------------------------------------------- |
| `40003` | 👤 openid 无效或未关注本测试号                                         |
| `40037` | 📄 template_id 失效，需在后台重建模板并更新代码                        |
| `45002` | 📏 内容过长，用 `--dry-run` 查看渲染字数                               |
| `47003` | 🧩 模板字段名与 `{{xxx.DATA}}` 不一致，运行 `check_template_assign.py` |

更完整的说明见 `weather_push_mp.py` 中的 `WX_ERR_CN` 字典。

---

## 🔒 安全提示

> 🚨 公开仓库前请务必检查密钥与隐私信息。

- ❌ **勿将** 含真实 `APP_SECRET`、`SendKey`、`openid` 的代码提交到公开仓库；生产环境建议改用环境变量或独立配置文件（且加入 `.gitignore`）。
- 🔄 当前仓库中的凭证仅作本地自用示例，公开分享前请 **轮换密钥**。

---

## 📎 文件职责速查

| 文件                          | 职责                                                                 |
| ----------------------------- | -------------------------------------------------------------------- |
| `weather_push.py` 🍬          | 拉取天气 → 拼 Markdown → `sctapi.ftqq.com` 推送                      |
| `weather_push_mp.py` 📱       | 多用户天气缓存、组装模板 data、获取 `access_token`、调用模板消息 API |
| `check_template_assign.py` ✅ | 模板与后台、字段赋值的集成检查                                       |
| `friend_template.txt` 👥      | 朋友模板微信后台粘贴用                                               |
| `lp_template.txt` 💕          | 情侣模板微信后台粘贴用                                               |

---

## 🙏 许可证与致谢

- 🌍 天气数据：[Open-Meteo](https://open-meteo.com/)
- 💬 推送：`weather_push.py` 使用 Server 酱；`weather_push_mp.py` 使用微信测试号接口

---

<p align="center">
  <strong>愿你每天出门前，都有一条恰到好处的天气提醒。</strong> 🙂<br/>
  按上文配置任一方案，即可开启每日自动推送。
</p>
