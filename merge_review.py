#!/usr/bin/env python3
# review.html（かわちゃん専用レビューページ）での判定結果をGoogle Sheetsから取得し、
# data.jsonのvisited/verified/hitokoto/ratingsに反映する。
# 使い方: python3 merge_review.py  →  python3 build_pages.py  → git commit/push
import json, urllib.request

API = "https://script.google.com/macros/s/AKfycbz6A_7okvNBKrrygHuOgJ4TQV1YlrB_UPx2_c3hMS9fG6YTunOrrOKROeHdHJg2QzXj/exec"
REVIEW_KEY = "yasasea-kawachan-review-2026"

with urllib.request.urlopen(f"{API}?review=1&key={REVIEW_KEY}", timeout=30) as r:
    review = json.load(r)

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
                    a["ratings"] = json.loads(rs["ratings"])
                    touched = True
                except json.JSONDecodeError:
                    pass
    elif status == "discard":
        if a.get("verified"):
            a["verified"] = False
            touched = True
    if touched:
        changed.append(name)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"更新: {len(changed)}館")
for n in changed:
    print(" -", n)
