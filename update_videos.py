#!/usr/bin/env python3
"""全国すいぞくかんツアー再生リストをチェックして data.json に新着動画を反映するスクリプト。

使い方:  python3 update_videos.py
- YouTubeの再生リストページから全動画を取得（APIキー不要）
- data.json に未登録の動画があれば「新着」として表示し、
  既存館にマッチすれば videos に追加、マッチしなければ手動追加を促す
"""
import json, re, urllib.request, datetime
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data.json"

def fetch_playlist(playlist_id):
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    req = urllib.request.Request(url, headers={"Accept-Language": "ja", "User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req).read().decode("utf-8")
    m = re.search(r"ytInitialData\s*=\s*({.+?});\s*</script>", html, re.S)
    data = json.loads(m.group(1))
    out = []
    def walk(d):
        if isinstance(d, dict):
            if d.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO":
                vid = d.get("contentId")
                titles = []
                def grab(x):
                    if isinstance(x, dict):
                        if isinstance(x.get("content"), str): titles.append(x["content"])
                        for v in x.values(): grab(v)
                    elif isinstance(x, list):
                        for v in x: grab(v)
                grab(d.get("metadata", {}))
                if vid and titles: out.append({"id": vid, "title": titles[0]})
            for v in d.values(): walk(v)
        elif isinstance(d, list):
            for v in d: walk(v)
    walk(data)
    return out

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    known = {v["id"] for a in data["aquariums"] for v in a["videos"]}
    videos = fetch_playlist(data["playlist_id"])
    print(f"再生リスト動画数: {len(videos)} / 登録済み: {len(known)}")
    new = [v for v in videos if v["id"] not in known]
    if not new:
        print("新着なし。data.jsonは最新です。")
        return
    changed = False
    for v in new:
        matched = None
        for a in data["aquariums"]:
            # 館名（括弧や法人表記を除いた主要部分）がタイトルに含まれるか
            key = re.sub(r"[（(].*?[)）]", "", a["name"]).strip()
            parts = [key] + key.split()
            if any(p and p in v["title"] for p in parts):
                matched = a
                break
        if matched:
            matched["videos"].append(v)
            matched.pop("upcoming", None)
            if matched.get("highlight", "").startswith("【近日公開予定】"):
                matched["highlight"] = matched["highlight"].replace("【近日公開予定】", "").strip() or "新着！"
            changed = True
            print(f"✅ 追加: {matched['name']} ← {v['title']}")
        else:
            print(f"⚠️ 新しい水族館の可能性（手動でdata.jsonに追加してね）: {v['title']}  https://www.youtube.com/watch?v={v['id']}")
    if changed:
        data["updated"] = datetime.date.today().isoformat()
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("data.json を更新しました。")

if __name__ == "__main__":
    main()
