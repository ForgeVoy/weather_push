# -*- coding: utf-8 -*-
"""对比 FRIEND/LP 模板、微信后台与代码 data 字段。"""
import argparse
import json
import re
import sys
import urllib.request

import weather_push_mp as w

ROMANTIC_SAMPLE_USER = {
    "name": "老婆",
    "style": "romantic",
    "city": "唐山市路北区",
    "lat": 39.603418,
    "lon": 118.113123,
    "love_start_date": "2021-02-11",
    "marriage_date": "2025-10-02",
    "birthday": "10-29",
    "pet_name": "宝贝",
}


def norm_content(text):
    return (text or "").replace("\r\n", "\n").strip()


def placeholders_from_content(content):
    return sorted(set(re.findall(r"{{\s*(\w+)\.DATA\s*}}", content)))


def fetch_templates():
    token = w.get_access_token(w.APP_ID, w.APP_SECRET)
    url = (
        "https://api.weixin.qq.com/cgi-bin/template/get_all_private_template"
        f"?access_token={token}"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        r = json.loads(resp.read().decode())
    return {t["template_id"]: t for t in r.get("template_list", [])}


def check_one(
    name,
    template_id,
    expected_wx,
    render_tpl,
    expected_keys,
    build_data,
    strip_fn,
    write_file,
):
    expected_wx = norm_content(expected_wx)
    print(f"\n{'=' * 60}")
    print(f"=== {name} ===")
    print(f"template_id: {template_id}")
    print("--- 代码模板 FRIEND/LP_TEMPLATE_WX ---")
    print(expected_wx)
    print(f"占位符 ({len(expected_keys)}): {expected_keys}")

    try:
        print(f"已同步 → {write_file()}")
    except OSError as e:
        print(f"⚠️ 写入失败: {e}")

    by_id = fetch_templates()
    tpl = by_id.get(template_id)
    if not tpl:
        print(f"\n⚠️ 微信后台未找到该 template_id（请新建模板并粘贴 template.txt）")
        print("当前已有:")
        for tid, t in by_id.items():
            print(f"  {tid} | {t.get('title')}")
        backend = ""
        backend_keys = []
        backend_ok = False
    else:
        backend = norm_content(tpl.get("content", ""))
        backend_keys = placeholders_from_content(backend)
        print(f"\n--- 微信后台「{tpl.get('title')}」---")
        print(backend)
        backend_ok = backend == expected_wx
        if backend_ok:
            print("\n✅ 后台与代码模板一致")
        else:
            print("\n⚠️ 后台与代码模板不一致，请用对应 template.txt 全量替换")
            if backend_keys != expected_keys:
                print("  仅后台:", [k for k in backend_keys if k not in expected_keys] or "无")
                print("  仅代码:", [k for k in expected_keys if k not in backend_keys] or "无")

    data = build_data()
    code_keys = sorted(data.keys())
    print("\n=== 代码赋值 ===")
    ok = True
    for key in expected_keys:
        val = data.get(key, {}).get("value", "")
        over = len(str(val)) > w.WECHAT_FIELD_MAX
        if key not in data or not str(val).strip():
            print(f"  {key}: {val!r} <<< 问题")
            ok = False
        elif over:
            print(f"  {key}: {val!r} <<< 超 {w.WECHAT_FIELD_MAX} 字")
            ok = False
        else:
            print(f"  {key}: {val!r}")

    missing = [p for p in backend_keys if p not in code_keys]
    extra = [k for k in code_keys if k not in backend_keys]
    print("\n推送 API：后台有代码未发", missing or "无")
    print("推送 API：代码多传", extra or "无")
    if missing:
        ok = False

    n = strip_fn(data)
    print(f"\n微信渲染估算: {n} / {w.WECHAT_RENDER_MAX}", end="")
    if n > w.WECHAT_RENDER_MAX:
        print(" <<< 超长")
        ok = False
    else:
        print(" ✅")

    print("\n=== 模拟正文 ===")
    vals = {k: v["value"] for k, v in data.items()}
    print(render_tpl.format(**vals))

    n_strip = w.WECHAT_STRIP_LINES
    lines = render_tpl.format(**vals).splitlines()
    safe = lines[n_strip:-n_strip] if len(lines) > n_strip * 2 else lines
    print(f"\n=== 首屏可见行（裁掉上下各 {n_strip} 行后）===")
    for i, line in enumerate(safe, 1):
        print(f"  [{i}] {line}")

    if ok and backend_ok:
        print(f"\n✅ {name} 检查通过")
        return True
    print(f"\n❌ {name} 检查未通过")
    return False


def build_friend_data():
    u = next((x for x in w.USERS if x.get("style") == "friend"), w.USERS[0])
    weather = w.get_weather(u["lat"], u["lon"])
    return w.build_friend_template(weather, u["city"], u)


def build_romantic_data():
    u = next((x for x in w.USERS if x.get("style") == "romantic"), ROMANTIC_SAMPLE_USER)
    weather = w.get_weather(u["lat"], u["lon"])
    return w.build_romantic_template(weather, u["city"], u)


def main():
    parser = argparse.ArgumentParser(description="检查微信模板与代码赋值")
    parser.add_argument(
        "--lp", action="store_true", help="只检查情侣模板 Lp_template_id"
    )
    parser.add_argument(
        "--friend", action="store_true", help="只检查朋友模板 Other_template_id"
    )
    args = parser.parse_args()
    run_friend = args.friend or (not args.friend and not args.lp)
    run_lp = args.lp or (not args.friend and not args.lp)

    passed = True
    if run_friend:
        passed &= check_one(
            "朋友 Other",
            w.Other_template_id,
            w.FRIEND_TEMPLATE_WX,
            w.FRIEND_TEMPLATE_RENDER,
            w.friend_template_placeholders(),
            build_friend_data,
            w.friend_content_chars,
            w.write_friend_template_file,
        )
    if run_lp:
        passed &= check_one(
            "情侣 Lp",
            w.Lp_template_id,
            w.LP_TEMPLATE_WX,
            w.ROMANTIC_TEMPLATE_RENDER,
            w.lp_template_placeholders(),
            build_romantic_data,
            w.romantic_content_chars,
            w.write_lp_template_file,
        )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
