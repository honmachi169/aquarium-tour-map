#!/usr/bin/env python3
"""ぬりえ倉庫（Google Drive）の一覧から nurie_data.json を生成するスクリプト。

使い方:
  1. Claude（Drive MCP）で「ぬりえ倉庫」の各フォルダを一覧化し、
     nurie_src/weekly_p1.tsv と nurie_src/extra.tsv（id<TAB>title<TAB>category）を更新する
     （新しいぬりえは extra.tsv に「id<TAB>タイトル<TAB>weekly」の行を足すだけでもOK）
  2. python3 build_nurie.py  → nurie_data.json を出力
  3. git commit & push → aquarium.yasasea.com/nurie.html に反映

カテゴリ:
  weekly   = 週末おさかな部（毎週のぬりえ）
  calendar = カレンダーぬりえ（月替わり＋時間割・持ち物チェッカー等）
  osusume  = 定番おすすめ
  youtube  = YouTube・水族館コラボ

新しいぬりえが増えたら 1〜2 をやり直すだけ。手書きページは作らない。
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "nurie_src"   # id<TAB>title<TAB>category の元データ（Drive一覧のスナップショット）
OUT = HERE / "nurie_data.json"

# サムネ・ダウンロードのURLパターン（Driveの共有ファイル前提）
def thumb(fid, size=800):
    return f"https://drive.google.com/thumbnail?id={fid}&sz=w{size}"
def dl(fid):
    return f"https://drive.google.com/uc?export=download&id={fid}"

# 動画設定（nurie_src/videos.json）… update_nurie.py が書き換える
#   map:  ぬりえID → そのぬりえを描いたライブ配信のYouTube動画ID
#   next_live: 次回の週末おさかな部ライブの動画ID
_VID = json.loads((Path(__file__).parent / "nurie_src" / "videos.json").read_text(encoding="utf-8")) \
    if (Path(__file__).parent / "nurie_src" / "videos.json").exists() else {"next_live": "", "map": {}}
VIDEOS = _VID.get("map", {})
NEXT_LIVE = _VID.get("next_live", "")
NEXT_LIVE_DATE = _VID.get("next_live_date", "")  # 次回ライブの予定開始（ISO・UTC）
NEXT_LIVE_TITLE = _VID.get("next_live_title", "")  # 次回ライブのテーマ（例：クラゲ大集合）

JUNK = re.compile(r"(IMG_\d+|Scannable|文書\b)", re.I)
EXT = re.compile(r"\.(png|jpg|jpeg)$", re.I)
DATE_FULL = re.compile(r"(20\d{2})[ _\-/](\d{1,2})[ _\-/](\d{1,2})")
DATE_YM = re.compile(r"(20\d{2})[ _\-]?\s*(\d{1,2})月")

def parse(fid, raw_title, category):
    title = raw_title.strip()
    # 壊れた拡張子の破片を掃除（例: "子育てする魚.PNさかな" / "北海道ぬりえ.849Z"）
    title = title.replace("のコピー", "").strip()
    title = re.sub(r"\.PN[GＧ]?[ぁ-ヶー]*", "", title, flags=re.I)
    title = EXT.sub("", title).strip()
    date_disp, date_iso = "", ""

    m = DATE_FULL.search(title)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        date_disp = f"{y}.{mo}.{d}"
        date_iso = f"{y:04d}-{mo:02d}-{d:02d}"
        title = DATE_FULL.sub("", title)
    else:
        m = DATE_YM.search(title)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            date_disp = f"{y}年{mo}月"
            date_iso = f"{y:04d}-{mo:02d}-01"
            title = DATE_YM.sub("", title)

    # 記号・区切りの掃除
    title = title.replace("_", " ").replace("＿", " ").replace("　", " ")
    title = re.sub(r"\.[0-9A-Za-z]+$", "", title)  # 末尾の壊れ拡張子（.849Z 等）
    title = re.sub(r"\s+", " ", title).strip(" ・-_＿")
    if not title or re.fullmatch(r"[\d\s.\-]+", title):
        title = "おさかなぬりえ"

    return {
        "id": fid,
        "title": title,
        "date": date_disp,
        "iso": date_iso,
        "cat": category,
        "thumb": thumb(fid),
        "dl": dl(fid),
        "video": VIDEOS.get(fid, ""),
    }

def load_tsv(path, default_cat=None):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        fid, title = parts[0], parts[1]
        cat = parts[2] if len(parts) > 2 else default_cat
        rows.append((fid, title, cat))
    return rows

def main():
    raw = load_tsv(SRC / "weekly_p1.tsv", "weekly") + load_tsv(SRC / "extra.tsv")
    seen, items = set(), []
    for fid, title, cat in raw:
        if fid in seen or JUNK.search(title):
            continue
        seen.add(fid)
        items.append(parse(fid, title, cat))

    # カテゴリ内は新しい順。日付なしは末尾。
    items.sort(key=lambda x: x["iso"] or "0000", reverse=True)

    counts = {}
    for it in items:
        counts[it["cat"]] = counts.get(it["cat"], 0) + 1

    OUT.write_text(json.dumps({"count": len(items), "nextLive": NEXT_LIVE,
                               "nextLiveDate": NEXT_LIVE_DATE, "nextLiveTitle": NEXT_LIVE_TITLE,
                               "items": items},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"生成: {OUT.name}  合計 {len(items)} 枚")
    for c, n in counts.items():
        print(f"  {c}: {n}")

if __name__ == "__main__":
    main()
