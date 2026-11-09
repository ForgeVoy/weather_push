# -*- coding: utf-8 -*-
"""
每日天气提醒 → 微信推送（公众号测试号模板消息版，多用户多城市）
天气源: Open-Meteo（免费、无需注册、无需 API Key）
推送:   微信公众平台测试号

USERS 里 style:
  - romantic  → 老婆专属模板（恋爱天数、结婚年数月日、生日、双语情话）
  - friend    → 自己与朋友模板（箴言、氛围文案、生活指数、日出日落、中文旁白 note_ch）

在测试号「模板消息接口」分别新增/修改模板，字段名须与代码里一致。
模板正文见 friend_template.txt（朋友）、lp_template.txt（情侣）。
调试时可加 --dry-run；校验：python check_template_assign.py [--friend|--lp]
"""

import calendar
import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.parse

# ====== 配置区 ======
APP_ID = "wx6d44cdf506132a3c"
APP_SECRET = "9f82a3e07506a9f087f9352b953eedcd"
Lp_template_id = "VdjJcZfBaLPK2m_NbAvQaKU7Z5mcuUdfdIRQaoCRpR0"
Other_template_id = "_4n3Elc36NwOuBK0lMOEjDp-7rx-4tzmBlpk4H3nuhs"
# style: romantic | friend
USERS = [
    {
        "name": "我",
        "openid": "owhzL58TUVMAc_E2g0xLI2XpZfI0",
        "template_id": Other_template_id,
        "style": "friend",
        "city": "天津市南开区",
        "lat": 39.096257,
        "lon": 117.152432,
    },
    {
    "name": "老婆",
      "openid": "owhzL58PqNb6xecGtKQDGOuQNWZ0",
      "template_id": Lp_template_id,
    "style": "romantic",
    "city": "唐山市路北区",
    "lat": 39.603418,
    "lon": 118.113123,
    "love_start_date": "2021-02-11",
    "marriage_date": "2025-10-02",
    "birthday": "10-29",
    "pet_name": "宝贝",
},
  
    {
        "name": "珍珍",
        "openid": "owhzL55QNW41XYTIfYI8AWaZXAos",
        "template_id": Other_template_id,
        "style": "friend",
        "city": "天津市南开区",
        "lat": 39.096257,
        "lon": 117.152432,
    },
    {
        "name": "田昊",
        "openid": "owhzL572xPdo3qdAAoSNojJcdRSM",
        "template_id": Other_template_id,
        "style": "friend",
        "city": "天津市南开区",
        "lat": 39.096257,
        "lon": 117.152432,
    },
     {
        "name": "子豪",
        "openid": "owhzL5_x19kOr4EjusfzWQH-KJa4",
        "template_id": Other_template_id,
        "style": "friend",
        "city": "天津市南开区",
        "lat": 39.096257,
        "lon": 117.152432,
    },
     {
        "name": "明正",
        "openid": "owhzL57J73tRIl-pitYhcNb7IZiM",
        "template_id": Other_template_id,
        "style": "friend",
        "city": "唐山市路北区",
        "lat": 39.638741,
        "lon": 118.048185,
    },
]
# ====================

WMO_CODE = {
    0: "晴", 1: "基本晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨(小)", 67: "冻雨(大)",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷雨伴冰雹",
}

RAIN_CODES = (51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99)
SNOW_CODES = (71, 73, 75, 77, 85, 86)
SUN_CODES = (0, 1)

# ---------------------------------------------------------------
# 朋友向：每日箴言（按一年中的第几天轮换）
# ---------------------------------------------------------------
FRIEND_QUOTES = [
    "生活不是等待风暴过去，而是学会在雨中跳舞。",
    "愿你眼里有光，心里有梦，脚下有路。",
    "今天的不开心就到此为止，明天依旧光芒万丈。",
    "明朝即长路，惜取此时心。",
    "知足且坚定，温柔且上进。",
    "凡是过往，皆为序章；所有将来，皆可期待。",
    "你只管努力，剩下的交给时光。",
    "人间清醒：早起上班，晚起也上班。",
    "武功再高，也怕书包忘带。",
    "别让坏情绪有隔夜费，逾期要收利息。",
    "世界很大，先把自己照顾好。",
    "纵有疾风起，人生不言弃。",
    "行到水穷处，坐看云起时。",
    "发财被爱好运常在，祝你祝我也祝。",
    "偷得浮生半日闲，摸鱼也要摸得优雅。",
    "星光不问赶路人，岁月不负有心者。",
    "知难而上，龙舟也怕三天晒网。",
    "一面镜子：你对世界笑，世界便对你笑。",
    "今天的小确幸，值得被认真记录。",
    "路虽远，行则将至；事虽难，做则必成。",
    "闲来无事，且饮一杯人间烟火。",
    "自律给我自由，赖床给我快乐——今日自选套餐。",
    "保持热爱，奔赴下一场山海。",
    "愿你被这世界温柔以待，也温柔以待自己。",
    "心若向阳，无谓悲伤。",
    "认真生活，就能找到生活里藏起来的糖果。",
    "人间值得，今天也值得。",
    "好运藏在努力里，更藏在好心情里。",
    "别慌，月亮也正在大海某处迷茫。",
    "草木蔓发，春山可望。",
    "日子平淡，好在我喜欢。",
    "山有峰顶，海有彼岸；漫漫长途，终有回转。",
    "把日子过成诗，哪怕押韵的是加班。",
    "慢一点没关系，方向对了，走一步算一步。",
    "今天也要好好吃饭，好好睡觉，好好长本事。",
    "你所热爱的，终会反过来拥抱你。",
    "别把时间花在解释上，去做就是了。",
    "情绪是一阵风，你是那棵树。",
    "晴天晒被子，雨天晒心情。",
    "先成为自己的光，再去照亮别人。",
    "别急，好运正在派件中。",
    "允许一切发生，然后继续向前。",
    "与其内耗，不如出门走走。",
    "慢慢来，一切都来得及。",
    "生活给什么，就先接着，再想办法做得漂亮。",
    "做事要认真，做人不较真。",
    "天塌下来有高个子，你先吃好早饭。",
    "早起的人，能捡到城市最安静的那一小时。",
    "前方有光，身后有路，兜里有钱，心里有人。",
    "愿你今天的烦恼，只有「吃什么」。",
    "把自己照顾好，是一件很酷的事。",
    "不必事事完美，及格的人生也很宽敞。",
    "月亮不急，它总在夜里准时上班。",
    "身体是革命的本钱，先把本钱养好。",
    "所有的努力，都会在某个不起眼的日子给你回信。",
    "日拱一卒，功不唐捐。",
    "愿你踏过千重浪，仍觉人间可爱。",
    "心宽一寸，路宽一丈。",
    "今天也要做自己的头号粉丝。",
]

# ---------------------------------------------------------------
# 朋友向：中文旁白（按日轮换，对应模板字段 note_ch）
# ---------------------------------------------------------------
FRIEND_NOTES = [
    "最难走的路，往往风景最好。",
    "把小事做好，就是大写的温柔。",
    "闯荡人间，未必迷途。",
    "把握当下，今日份请用力活。",
    "人生苦短，牙在就要笑。",
    "保持好奇，偶尔犯傻，人生更有趣。",
    "叶落不妨，向光而生。",
    "风平浪静养不出好水手。",
    "咖啡先行，宏图稍后。",
    "相信美好的人，终会与美好相遇。",
    "读万卷书，行万里路；今日先迈一步。",
    "每天一小步，也比原地踏步远。",
    "在哪儿扎根，就在哪儿开花。",
    "要向前，不要完美。",
    "先接受，再放下。",
    "太阳照常升起，日子照常可期。",
    "慢即是稳，稳即是快。",
    "让今天值得被记住。",
    "少一点喧哗，多一点专注。",
    "好东西，都要慢慢来。",
    "把脸朝向阳光，影子就落在身后。",
    "教养，是一个人最好的名片。",
    "成功没有电梯，只能一级一级往上爬。",
    "对每个人温柔些，人人都在打一场硬仗。",
    "你寻找的，也在寻找你。",
    "休息，也是工作的一部分。",
    "是某一天，还是第一天，你说了算。",
    "沉默，有时就是答案。",
    "要么带着热爱做，要么别做。",
    "最好的，还在后头。",
    "走过的路，都会长成你的底气。",
    "比较，是偷走快乐的贼。",
    "知足，即是盛宴。",
]

# ---------------------------------------------------------------
# 情侣向：双语情话
# ---------------------------------------------------------------
# 微信单字段 ≤20 字：推送用精简双语（勿用长句，避免界面出现 …）
ROMANTIC_WECHAT = [
    ("I choose you.", "晴天雨天，我都选你。"),
    ("You are my home.", "你在哪里，哪里就是家。"),
    ("You had me at hello.", "一句你好，我便投降。"),
    ("My heart is yours.", "我的心一直在你这里。"),
    ("Every day with you.", "和你在一起的每一天。"),
    ("Rain or shine—you.", "晴雨不论，你最爱。"),
    ("Grow old with me.", "一起变老，最好的未来。"),
    ("Love you more daily.", "每天都重新喜欢上你。"),
    ("You're my calm.", "风雨再大，你是我的安稳。"),
    ("My favorite place.", "我最喜欢你的怀抱。"),
    ("I'd choose you.", "百次轮回仍选你。"),
    ("Your name, my joy.", "你的名字，我最爱的字。"),
    ("Together is home.", "在一起，是最美的事。"),
    ("You are my tomorrow.", "你是我期待明天。"),
    ("Forever starts now.", "永远从此刻开始。"),
    ("Hug me in the rain.", "雨天为你撑伞。"),
    ("Sunshine or you.", "有光的日子更想你。"),
    ("Missing you.", "今天也很想你。"),
    ("Kiss the cold away.", "降温了，抱紧一点。"),
    ("Drink water, love.", "天热多喝水想我。"),
]

ROMANTIC_NOTES = [
    ("You are my today and all of my tomorrows.", "你是我的今天，也是我所有的明天。"),
    ("I have found the one whom my soul loves.", "我遇见了你，心便找到了归宿。"),
    ("In all the world, there is no heart for me like yours.", "人世间，再没有一颗心如你。"),
    ("Every love story is beautiful, but ours is my favorite.", "爱情故事都动人，而我最爱我们的这一篇。"),
    ("Whatever our souls are made of, yours and mine are the same.", "灵魂的材质若可分，你我的应是同一种。"),
    ("I choose you, in sunshine and in rain.", "晴天雨天，我都选你。"),
    ("You make ordinary moments feel like forever.", "有你在，寻常时刻也像永恒。"),
    ("Distance means nothing when someone means everything.", "你在心里，距离便不是距离。"),
    ("Love is not about how many days, months, or years.", "爱不是数日子，而是每一天都重新喜欢上你。"),
    ("My heart is and always will be yours.", "过去、现在、将来，我的心都在你这里。"),
    ("You're the one I've been wishing for.", "你是愿望成真那一天到来的那个人。"),
    ("Home is wherever I'm with you.", "你在哪里，哪里就是家。"),
    ("You had me at hello.", "一句「你好」，我就缴械投降。"),
    ("I love you not only for what you are, but for what I am when I am with you.", "我爱你，不只因你是你，更因与你在一起时我成了谁。"),
    ("Grow old along with me, the best is yet to be.", "与我一起变老吧，最好的还未来到。"),
    ("You are the poem I never knew how to write.", "你是我一直写不出的那首诗。"),
    ("My favorite place is inside your hug.", "我最喜欢的地方，是你的怀抱。"),
    ("I'd choose you in a hundred lifetimes.", "一百次轮回，我一百次都选你。"),
    ("Your name is my favorite word.", "你的名字，是我最爱的那两个字。"),
    ("Together is a wonderful place to be.", "「在一起」，是最美妙的所在。"),
    ("You are the reason I look forward to tomorrow.", "因为有你，我才期待明天。"),
    ("Rain or shine, you're my kind of weather.", "晴雨不论，你都是我最喜欢的天气。"),
    ("Every day with you is a good day.", "和你在一起的每一天，都是好日子。"),
    ("I fell in love with the way you see the world.", "我爱上的，是你看世界的那个眼神。"),
    ("You are my calm in every storm.", "风雨再大，你是我的安稳。"),
    ("Even the stars are jealous of your light.", "连星星都嫉妒你的光。"),
    ("The best thing to hold onto in life is each other.", "此生最该握紧的，是彼此的手。"),
    ("You're my cup of tea, my slice of cake.", "你是我的茶，也是我的那块甜。"),
    ("My heart beats your name.", "心跳的节奏，念的是你的名字。"),
    ("Loving you is my favorite habit.", "爱你，是我最戒不掉的习惯。"),
    ("You are enough, exactly as you are.", "你本来的样子，就已经很好。"),
    ("With you, ordinary days turn golden.", "有你在，平常的日子也会泛金。"),
    ("I'll be your umbrella in the rain, your shade in the sun.", "雨天为你撑伞，烈日为你遮阳。"),
    ("Forever starts with a simple hello.", "永远，是从一句「你好」开始的。"),
]

# ---------------------------------------------------------------
# 朋友向：氛围文案（按天气/温度分池，逐日轮换）
# ---------------------------------------------------------------
VIBE_SUNNY = [
    "阳光慷慨，宜把日子过得亮一点。",
    "天蓝得很好看，别辜负这份晴朗。",
    "有光的日子，适合把计划往前挪一挪。",
    "晒晒太阳，把心情也晒得蓬松。",
]
VIBE_CLOUDY = [
    "云层厚，心事薄，正好赶路。",
    "不是每天都放晴，但每天都值得。",
    "灰一点的天，适合安静做点事。",
    "云在慢慢走，你也可以慢慢来。",
]
VIBE_RAIN = [
    "雨落成诗，今日宜慢一点。",
    "听雨的人，运气都不错。",
    "雨天路滑，慢行即是稳妥。",
    "雨水洗城，顺便洗洗心里的灰尘。",
]
VIBE_SNOW = [
    "下雪了，世界忽然变得很安静。",
    "雪落无声，走过的每一步都有印。",
    "雪天慢行，好看也要安全。",
    "雪是冬天写给人间的短句。",
]
VIBE_HOT = [
    "热浪上线，宜清凉，忌逞强。",
    "高温天，能不出门就是胜利。",
    "太阳很努力，你也别太拼。",
    "热得认真，就要补水认真。",
]
VIBE_COLD = [
    "天冷了，先穿暖，再谈理想。",
    "降温了，把外套穿好，把心捂热。",
    "冷是暂时的，热汤是及时的。",
    "风有点凉，记得给自己加一层。",
]


def http_json(url, data=None):
    if data is not None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "weather-push/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": ("weather_code,temperature_2m_max,temperature_2m_min,"
                  "precipitation_probability_max,uv_index_max,sunrise,sunset"),
        "timezone": "auto",
        "forecast_days": 2,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    return http_json(url)


def wdesc(code):
    return WMO_CODE.get(code, f"未知({code})")


def date_cn():
    t = datetime.date.today()
    wd = "一二三四五六日"[t.weekday()]
    return f"{t:%Y-%m-%d} 星期{wd}"


def compact_loc(city):
    """日期+城市压到 20 字内，装在必定可见的天气行。"""
    t = datetime.date.today()
    wd = "一二三四五六日"[t.weekday()]
    short = str(city or "").replace("市", "").replace("区", "").replace("县", "")
    label = f"{t:%m-%d}星期{wd}·{short}"
    if len(label) > 20:
        label = f"{t:%m-%d}·{short}"
    if len(label) > 20:
        label = label[:20]
    return label


def merge_vibe_note(vibe, note_ch, max_len=20):
    """旁白并入 vibe 行，避免单独一行被裁掉。"""
    vibe, note_ch = str(vibe or "").strip(), str(note_ch or "").strip()
    if not note_ch:
        return vibe[:max_len]
    if not vibe:
        return note_ch[:max_len]
    sep = "｜"
    merged = f"{vibe}{sep}{note_ch}"
    if len(merged) <= max_len:
        return merged
    note_fit = note_ch[:max_len]
    budget = max_len - len(sep) - len(note_ch)
    if budget >= 2:
        head = vibe[:budget]
        for punct in "，。、":
            idx = head.rfind(punct)
            if idx >= 2:
                head = head[:idx]
                break
        else:
            head = head.rstrip("，。、 ")
        if head:
            return f"{head}{sep}{note_ch}"
    return note_fit


def pick_daily(items, salt=0):
    """按日期轮换。salt 让不同文案池错开，不至于每天同进同退。"""
    doy = datetime.date.today().timetuple().tm_yday
    return items[(doy + salt) % len(items)]


def love_day_count(start_iso):
    start = datetime.date.fromisoformat(start_iso)
    return (datetime.date.today() - start).days + 1


def marriage_duration_ymd(marriage_iso):
    """自结婚日起至今天，格式 x年x月x天（结婚当天为 0年0月0天）。"""
    start = datetime.date.fromisoformat(marriage_iso)
    end = datetime.date.today()
    if end < start:
        return "0年0月0天"

    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day

    if days < 0:
        months -= 1
        prev_month = end.month - 1 or 12
        prev_year = end.year if end.month > 1 else end.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]

    if months < 0:
        years -= 1
        months += 12

    return f"{years}年{months}月{days}天"


def birthday_message(mm_dd, pet_name="宝贝"):
    """情侣模板用：全程控制在 20 字内，避免微信截断。"""
    today = datetime.date.today()
    try:
        month, day = map(int, mm_dd.split("-"))
    except ValueError:
        return f"记得{pet_name}生日哦"

    bday = datetime.date(today.year, month, day)
    if today == bday:
        return f"今天{pet_name}生日，爱你"
    if today > bday:
        bday = datetime.date(today.year + 1, month, day)
    days_left = (bday - today).days
    if days_left <= 7:
        return f"{days_left}天后{pet_name}生日啦"
    return f"距{pet_name}生日{days_left}天"


def weather_summary(today_code, tomorrow_code, cur_temp, hi, lo, pp, compact=False):
    if compact:
        return f"今{wdesc(today_code)}/明{wdesc(tomorrow_code)} {cur_temp}°"
    parts = [f"今{wdesc(today_code)}", f"明{wdesc(tomorrow_code)}"]
    if today_code in RAIN_CODES:
        parts.append(f"降水{pp}%")
    parts.append(f"此刻{cur_temp}°")
    return " · ".join(parts)


def sun_line(daily, compact=True):
    """日出日落；默认紧凑格式以节省模板总长额度。"""
    try:
        sunrise = datetime.datetime.fromisoformat(daily["sunrise"][0])
        sunset = datetime.datetime.fromisoformat(daily["sunset"][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return ""
    delta = sunset - sunrise
    total = int(delta.total_seconds())
    if total <= 0:
        return ""
    hours, rem = divmod(total, 3600)
    if compact:
        return f"出{sunrise:%H:%M}落{sunset:%H:%M} {hours}h{rem // 60}m"
    return f"日出{sunrise:%H:%M}日落{sunset:%H:%M}昼{hours}h{rem // 60}m"


def care_tips(today_code, hi, lo, pp, uv, wind):
    """穿衣 / 带伞 / 防晒 / 补水 —— 压缩成一行生活指数。"""
    tips = []
    if hi >= 30:
        tips.append("短袖")
    elif hi >= 24:
        tips.append("长袖薄衫")
    elif hi >= 18:
        tips.append("薄外套")
    elif hi >= 10:
        tips.append("夹克风衣")
    elif hi >= 3:
        tips.append("毛衣外套")
    else:
        tips.append("厚羽绒")

    if lo <= 2:
        tips.append("早晚加衣")
    if today_code in RAIN_CODES or (pp is not None and pp >= 50):
        tips.append("带伞")
    if today_code in SNOW_CODES:
        tips.append("防滑")
    if uv is not None:
        if uv >= 8:
            tips.append("强防晒SPF50")
        elif uv >= 5:
            tips.append("防晒SPF30")
    if hi >= 33:
        tips.append("多补水")
    if wind is not None and wind >= 30:
        tips.append("风大")

    return " · ".join(tips[:2])


def vibe_call(today_code, hi, lo):
    if today_code in RAIN_CODES:
        pool = VIBE_RAIN
    elif today_code in SNOW_CODES:
        pool = VIBE_SNOW
    elif hi >= 33:
        pool = VIBE_HOT
    elif lo <= 2:
        pool = VIBE_COLD
    elif today_code in SUN_CODES:
        pool = VIBE_SUNNY
    else:
        pool = VIBE_CLOUDY
    return pick_daily(pool, salt=5)


def parse_weather(d):
    cur, daily = d["current"], d["daily"]
    hi = round(daily["temperature_2m_max"][0])
    lo = round(daily["temperature_2m_min"][0])
    pp = daily["precipitation_probability_max"][0]
    today_code = daily["weather_code"][0]
    tomorrow_code = daily["weather_code"][1]
    cur_temp = round(cur["temperature_2m"])
    uv = daily.get("uv_index_max", [None])[0]
    wind = cur.get("wind_speed_10m")
    return cur, hi, lo, pp, today_code, tomorrow_code, cur_temp, uv, wind


def pick_romantic_wechat(salt=1):
    return pick_daily(ROMANTIC_WECHAT, salt=salt)


def compact_heart(love_n, marriage):
    """恋爱+婚龄合并一行，超 20 字时优先保留婚龄。"""
    full = f"恋{love_n}天·婚{marriage}"
    if len(full) <= WECHAT_FIELD_MAX:
        return full
    short = f"恋爱{love_n}天"
    if len(short) <= WECHAT_FIELD_MAX:
        return short
    return str(love_n)


def build_romantic_template(d, city, user):
    _, hi, lo, pp, today_code, tomorrow_code, cur_temp, _, _ = parse_weather(d)
    note_en, note_ch = pick_romantic_wechat(salt=1)
    love_n = love_day_count(user["love_start_date"])
    marriage = marriage_duration_ymd(user["marriage_date"])
    heart = compact_heart(love_n, marriage)
    pad = "·"
    return fit_romantic_data_for_wechat(
        {
            "pad1": {"value": pad},
            "pad2": {"value": pad},
            "loc": {"value": compact_loc(city)},
            "weather": {
                "value": weather_summary(
                    today_code, tomorrow_code, cur_temp, hi, lo, pp, compact=True
                )
            },
            "min_temperature": {"value": f"{lo}°"},
            "max_temperature": {"value": f"{hi}°"},
            "heart": {"value": heart},
            "birthday1": {
                "value": birthday_message(
                    user.get("birthday", "01-01"), user.get("pet_name", "宝贝")
                )
            },
            "note_en": {"value": note_en},
            "note_ch": {"value": note_ch},
            "pad3": {"value": pad},
            "pad4": {"value": pad},
        }
    )


def build_friend_template(d, city, _user):
    _, hi, lo, pp, today_code, tomorrow_code, cur_temp, uv, wind = parse_weather(d)
    daily = d["daily"]

    # 按昵称生成偏移量：同一天不同好友收到的箴言/旁白各不相同
    person_salt = sum(ord(c) for c in str(_user.get("name", ""))) % 97

    quote = pick_daily(FRIEND_QUOTES, salt=2 + person_salt)
    note_ch = pick_daily(FRIEND_NOTES, salt=7 + person_salt * 3)
    vibe = vibe_call(today_code, hi, lo)
    tip = care_tips(today_code, hi, lo, pp, uv, wind)
    sun = sun_line(daily)
    rain = f"{pp}%" if pp is not None else "—"

    loc = compact_loc(city)
    vibe_line = merge_vibe_note(vibe, note_ch)
    pad = "·"
    data = {
        # 首尾各 WECHAT_STRIP_LINES 行占位，真内容夹在中间。
        "pad1": {"value": pad},
        "pad2": {"value": pad},
        "loc": {"value": loc},
        "weather": {
            "value": weather_summary(
                today_code, tomorrow_code, cur_temp, hi, lo, pp, compact=True
            )
        },
        "min_temperature": {"value": f"{lo}°"},
        "max_temperature": {"value": f"{hi}°"},
        "rain": {"value": rain},
        "sun": {"value": sun},
        "tip": {"value": tip},
        "quote": {"value": quote},
        "vibe": {"value": vibe_line},
        "pad3": {"value": pad},
        "pad4": {"value": pad},
    }
    return fit_friend_data_for_wechat(data)


def build_template_data(d, user):
    style = user.get("style", "friend")
    city = user["city"]
    if style == "romantic":
        return build_romantic_template(d, city, user)
    return build_friend_template(d, city, user)


# 公众号模板消息（测试号实测）：
# - 正文首尾约裁 WECHAT_STRIP_LINES 行，用 pad1..pad4 占位（上下各 2 行）；
# - loc / 旁白并入 vibe；单字段 ≤20 字，总长约 ≤200 字。
FRIEND_TEMPLATE_RENDER = (
    "{pad1}\n"
    "{pad2}\n"
    "📍{loc}\n"
    "☁️ {weather} · 💧 {rain}\n"
    "🌡 {min_temperature}～{max_temperature}\n"
    "🌅 {sun}\n"
    "🧥 {tip}\n"
    "📖 {quote}\n"
    "🍃 {vibe}\n"
    "{pad3}\n"
    "{pad4}\n"
)
# 与 friend_template.txt 一致；运行 --dry-run 会覆盖写入该文件。
FRIEND_TEMPLATE_WX = (
    "{{pad1.DATA}}\n"
    "{{pad2.DATA}}\n"
    "📍{{loc.DATA}}\n"
    "☁️ {{weather.DATA}} · 💧 {{rain.DATA}}\n"
    "🌡 {{min_temperature.DATA}}～{{max_temperature.DATA}}\n"
    "🌅 {{sun.DATA}}\n"
    "🧥 {{tip.DATA}}\n"
    "📖 {{quote.DATA}}\n"
    "🍃 {{vibe.DATA}}\n"
    "{{pad3.DATA}}\n"
    "{{pad4.DATA}}\n"
)


def friend_template_placeholders():
    return sorted(set(re.findall(r"{{\s*(\w+)\.DATA\s*}}", FRIEND_TEMPLATE_WX)))


def write_friend_template_file():
    """把 FRIEND_TEMPLATE_WX 写入 friend_template.txt（供测试号后台复制）。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "friend_template.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(FRIEND_TEMPLATE_WX)
    return path


# 情侣向（Lp_template_id）：字段与长度规则与朋友版相同
ROMANTIC_TEMPLATE_RENDER = (
    "{pad1}\n"
    "{pad2}\n"
    "📍{loc}\n"
    "☁️ {weather}\n"
    "🌡 {min_temperature}～{max_temperature}\n"
    "💕 {heart}\n"
    "🎂 {birthday1}\n"
    "💬 {note_ch}\n"
    "💌 {note_en}\n"
    "{pad3}\n"
    "{pad4}\n"
)
LP_TEMPLATE_WX = (
    "{{pad1.DATA}}\n"
    "{{pad2.DATA}}\n"
    "📍{{loc.DATA}}\n"
    "☁️ {{weather.DATA}}\n"
    "🌡 {{min_temperature.DATA}}～{{max_temperature.DATA}}\n"
    "💕 {{heart.DATA}}\n"
    "🎂 {{birthday1.DATA}}\n"
    "💬 {{note_ch.DATA}}\n"
    "💌 {{note_en.DATA}}\n"
    "{{pad3.DATA}}\n"
    "{{pad4.DATA}}\n"
)


def lp_template_placeholders():
    return sorted(set(re.findall(r"{{\s*(\w+)\.DATA\s*}}", LP_TEMPLATE_WX)))


def write_lp_template_file():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lp_template.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(LP_TEMPLATE_WX)
    return path


WECHAT_FIELD_MAX = 20
WECHAT_RENDER_MAX = 198  # 略小于 200，给平台计数与 emoji 处理留余量
# 测试号正文首尾大约裁掉的行数；与占位行数 pad1..padN 对齐，不够再加大
WECHAT_STRIP_LINES = 2


def truncate_wechat_value(text, max_len=WECHAT_FIELD_MAX):
    text = str(text or "").replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def friend_render_len(values):
    return len(FRIEND_TEMPLATE_RENDER.format(**values))


def fit_friend_data_for_wechat(data):
    """在赋值后压缩各字段，保证渲染总长与单字段不触顶。"""
    values = {k: v.get("value", "") for k, v in data.items()}

    def apply_values():
        for k, val in values.items():
            data[k]["value"] = val

    # 单字段上限
    for k in list(values):
        values[k] = truncate_wechat_value(values[k], WECHAT_FIELD_MAX)

    # 总长超限：优先压缩靠前、信息可省的字段，保住尾部箴言/旁白
    shrink_steps = [
        ("sun", lambda v: truncate_wechat_value(v, 14)),
        ("sun", lambda v: truncate_wechat_value(v, 11)),
        ("sun", ""),
        ("weather", lambda v: truncate_wechat_value(v, 14)),
        ("tip", lambda v: truncate_wechat_value(v, 12)),
        ("tip", lambda v: truncate_wechat_value(v, 9)),
        ("loc", lambda v: truncate_wechat_value(v, 14)),
        ("quote", lambda v: truncate_wechat_value(v, 16)),
        ("vibe", lambda v: truncate_wechat_value(v, 18)),
    ]
    for key, new_val in shrink_steps:
        if friend_render_len(values) <= WECHAT_RENDER_MAX:
            break
        if callable(new_val):
            values[key] = new_val(values.get(key, ""))
        else:
            values[key] = new_val

    apply_values()
    return data


def content_chars(data):
    """各字段 value 字符数之和（不含模板固定文案）。"""
    return sum(len(str(v.get("value", ""))) for v in data.values())


def friend_content_chars(data):
    """朋友模板按微信规则估算的渲染总长。"""
    values = {k: v.get("value", "") for k, v in data.items()}
    return friend_render_len(values)


def romantic_render_len(values):
    return len(ROMANTIC_TEMPLATE_RENDER.format(**values))


def clip_wechat_plain(text, max_len=WECHAT_FIELD_MAX):
    """超长时在标点处截断，尽量不用省略号。"""
    text = str(text or "").replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    head = text[:max_len]
    for punct in "，。、!. ":
        idx = head.rfind(punct)
        if idx >= max(4, max_len // 2):
            return head[:idx].rstrip(punct)
    return head.rstrip()


def fit_romantic_data_for_wechat(data):
    values = {k: v.get("value", "") for k, v in data.items()}

    def apply_values():
        for k, val in values.items():
            data[k]["value"] = val

    for k in list(values):
        values[k] = clip_wechat_plain(values[k], WECHAT_FIELD_MAX)

    shrink_steps = [
        ("birthday1", lambda v: clip_wechat_plain(v, 16)),
        ("note_en", lambda v: clip_wechat_plain(v, 16)),
        ("note_ch", lambda v: clip_wechat_plain(v, 16)),
        ("heart", lambda v: clip_wechat_plain(v, 16)),
        ("weather", lambda v: clip_wechat_plain(v, 14)),
    ]
    for key, new_val in shrink_steps:
        if romantic_render_len(values) <= WECHAT_RENDER_MAX:
            break
        if callable(new_val):
            values[key] = new_val(values.get(key, ""))
        else:
            values[key] = new_val

    apply_values()
    return data


def romantic_content_chars(data):
    values = {k: v.get("value", "") for k, v in data.items()}
    return romantic_render_len(values)


def get_access_token(app_id, app_secret):
    url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
           f"&appid={app_id}&secret={app_secret}")
    r = http_json(url)
    if "access_token" not in r:
        raise RuntimeError(f"获取 access_token 失败: {r}")
    return r["access_token"]


def send_template(token, touser, template_id, data):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    body = {
        "touser": touser,
        "template_id": template_id,
        "data": data,
    }
    r = http_json(url, body)
    if r.get("errcode") == 0:
        return True, r
    return False, r


# 常见错误码 → 排查方向
WX_ERR_CN = {
    -1: "微信系统繁忙，稍后重试即可",
    40001: "access_token 已失效（脚本会自动刷新重试一次）",
    40003: "openid 不合法：该用户未关注测试号，或 openid 属于其他公众号",
    40013: "appid 不合法：检查 APP_ID",
    40037: "template_id 不合法：模板被删除或重新新增后 ID 会变，请同步改代码",
    42001: "access_token 已过期（脚本会自动刷新重试一次）",
    42901: "请求过于频繁，稍后再试",
    45002: "消息内容超过长度限制，请精简字段值",
    45009: "接口调用次数达到上限",
    47001: "请求体 JSON 解析失败",
    47003: "模板参数不匹配：代码字段名与后台模板内容里的占位符不一致",
    48001: "API 功能未授权",
}


def push_one(token, user, data):
    """发送一次；token 失效则刷新后自动重试一次。返回 (ok, result, token)。"""
    ok, result = send_template(token, user["openid"], user["template_id"], data)
    if not ok and result.get("errcode") in (40001, 42001):
        token = get_access_token(APP_ID, APP_SECRET)
        ok, result = send_template(token, user["openid"], user["template_id"], data)
    return ok, result, token


def dry_run():
    """只组装内容并打印，不发送。改完模板先用它自检。"""
    weather_cache = {}
    for user in USERS:
        key = (user["lat"], user["lon"])
        if key not in weather_cache:
            weather_cache[key] = get_weather(user["lat"], user["lon"])
        data = build_template_data(weather_cache[key], user)
        print(f"\n===== {user['name']}｜{user.get('style')}｜{user['city']} =====")
        print(f"字段合计：{content_chars(data)} 字")
        if user.get("style", "friend") == "friend":
            print(f"微信渲染估算：{friend_content_chars(data)} / {WECHAT_RENDER_MAX}")
            print("预览：")
            print(FRIEND_TEMPLATE_RENDER.format(**{k: v["value"] for k, v in data.items()}))
            print(f"模板内容（复制）：{FRIEND_TEMPLATE_WX}")
        elif user.get("style") == "romantic":
            print(f"微信渲染估算：{romantic_content_chars(data)} / {WECHAT_RENDER_MAX}")
            print("预览：")
            print(ROMANTIC_TEMPLATE_RENDER.format(**{k: v["value"] for k, v in data.items()}))
            print(f"模板内容（复制）：{LP_TEMPLATE_WX}")
        for k, v in data.items():
            print(f"  {k:<18}{v['value']}")
    print()

    try:
        print(f"已写入 friend_template.txt → {write_friend_template_file()}")
        print(f"已写入 lp_template.txt → {write_lp_template_file()}")
    except OSError as e:
        print(f"⚠️ 模板文件写入失败：{e}")


def main():
    if not USERS:
        print("请在 USERS 列表里配置接收人")
        return

    # Windows 控制台默认 GBK，直接 print emoji 会报编码错
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if "--dry-run" in sys.argv:
        dry_run()
        return

    for user in USERS:
        if not user.get("openid") or not user.get("template_id"):
            print(f"用户「{user.get('name', '?')}」缺少 openid 或 template_id")
            return
        if user.get("style") == "romantic":
            if not user.get("love_start_date"):
                print(f"用户「{user['name']}」为 romantic，请填写 love_start_date")
                return
            if not user.get("marriage_date"):
                print(f"用户「{user['name']}」为 romantic，请填写 marriage_date")
                return

    token = get_access_token(APP_ID, APP_SECRET)
    weather_cache = {}
    ok_count, fail_count = 0, 0

    for user in USERS:
        key = (user["lat"], user["lon"])
        try:
            if key not in weather_cache:
                weather_cache[key] = get_weather(user["lat"], user["lon"])
            data = build_template_data(weather_cache[key], user)
        except Exception as e:
            fail_count += 1
            print(f"❌ {user['name']}（{user['city']}）获取天气失败：{e}")
            continue

        if user.get("style", "friend") == "friend":
            n = friend_content_chars(data)
            if n > WECHAT_RENDER_MAX:
                print(f"⚠️ {user['name']} 微信渲染约 {n} 字，仍偏长，尾部字段可能被省略")
        elif user.get("style") == "romantic":
            n = romantic_content_chars(data)
            if n > WECHAT_RENDER_MAX:
                print(f"⚠️ {user['name']} 微信渲染约 {n} 字，仍偏长，尾部字段可能被省略")

        try:
            ok, result, token = push_one(token, user, data)
        except Exception as e:
            fail_count += 1
            print(f"❌ {user['name']}（{user['city']}）网络异常：{e}")
            continue

        if ok:
            ok_count += 1
            print(f"✅ {user['name']}（{user['city']}）推送成功")
        else:
            fail_count += 1
            err = result.get("errcode")
            print(f"❌ {user['name']}（{user['city']}）推送失败 "
                  f"[{err} {result.get('errmsg', '')}] {WX_ERR_CN.get(err, '')}")

    print(f"\n完成：成功 {ok_count} 人，失败 {fail_count} 人")


if __name__ == "__main__":
    main()
