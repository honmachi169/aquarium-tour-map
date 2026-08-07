#!/usr/bin/env python3
# review.html（かわちゃん専用レビューページ）での判定結果をGoogle Sheetsから取得し、
# data.jsonのvisited/verified/hitokoto/ratingsに反映する。
# 使い方: python3 merge_review.py  →  python3 build_pages.py  → git commit/push
import json, urllib.request, time

API = "https://script.google.com/macros/s/AKfycbz6A_7okvNBKrrygHuOgJ4TQV1YlrB_UPx2_c3hMS9fG6YTunOrrOKROeHdHJg2QzXj/exec"
REVIEW_KEY = "yasasea-kawachan-review-2026"


def fetch_json(url, tries=4):
    """Apps Scriptは稀に302リダイレクト後に404/429/5xxを返す（一時的）。
    数回リトライして拾う。ブラウザ風UAを付けないと弾かれることがある。
    ※ここが404で落ちるのは『ネットワーク遮断』ではなく一時エラー。"""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e
            print(f"[retry {i+1}/{tries}] {type(e).__name__}: {e}")
            time.sleep(2 * (i + 1))
    raise SystemExit(f"[fatal] レビュー取得に{tries}回失敗: {last}\n"
                     f"  ※script.google.comは到達可能（遮断ではない）。時間をおいて再実行を。")


review = fetch_json(f"{API}?review=1&key={REVIEW_KEY}")

with open("data.json", encoding="utf-8") as f:
    d = json.load(f)

by_name = {a["name"]: a for a in d["aquariums"] + d["unvisited"]}
changed = []

for name, rs in review.items():
    a = by_name.get(name)
    if not a:
        print(f"[skip] data.jsonに見つからない館名: {name}")
        continue
    touched = False
    if rs.get("visited") is not None and a.get("visited") != rs["visited"]:
        a["visited"] = bool(rs["visited"])
        touched = True
    status = rs.get("status") or ""
    if status in ("ok", "edit"):
        if not a.get("verified"):
            a["verified"] = True
            touched = True
        if status == "edit":
            if rs.get("hitokoto"):
                a["hitokoto"] = rs["hitokoto"]
                touched = True
            if rs.get("ratings"):
                try:
                    new_ratings = json.loads(rs["ratings"])
                    # 空({})のratingsで既存の評価を上書き＝消失させない（空欄送信バグ対策）
                    if new_ratings:
                        a["ratings"] = new_ratings
                        touched = True
                    elif a.get("ratings"):
                        print(f"[keep] {name}: レビュー側が空のため既存評価を維持")
                except json.JSONDecodeError:
                    pass
    elif status == "discard":
        if a.get("verified"):
            a["verified"] = False
            touched = True
    if touched:
        changed.append(name)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)

print(f"更新: {len(changed)}館")
for n in changed:
    print(" -", n)
