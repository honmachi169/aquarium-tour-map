#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ご意見箱の既読化・写真投稿の承認を Apps Script(doPost) に書き戻すツール。

【重要な前提／なぜ作ったか】
2026-07-27〜08-06 のパトロールで「script.google.com がネットワークポリシーで
403遮断されているため書き戻せない」と8回続けて報告されていたが、これは誤診断。
実際には script.google.com は到達可能（GET/POSTとも200が返る）。
過去に失敗していた本当の原因は:
  (1) Apps Scriptが稀に302後に404を返す一時エラーを『遮断』と誤認していた
  (2) WebFetchツール（環境で制限あり）に頼り、Bashのpython/curlを試していなかった
  (3) curl -L のPOSTは302でメソッドがGETに落ちて405になる
      → python urllib なら 302 を追っても正しく結果を拾える（下の post_json 方式）

【使い方】
  python3 patrol_writeback.py feedback-list                 # 未報告のご意見を一覧
  python3 patrol_writeback.py feedback-mark 24 25 26        # 指定行を「報告済み」に
  python3 patrol_writeback.py photos-list                   # 未承認の写真投稿を一覧
  python3 patrol_writeback.py photos-approve 12 34          # 指定行のF列に○（＝公開）

※ photos-approve は投稿写真を公開サイトに載せる行為。承認はかわちゃん判断。
  一覧で内容を確認してから、公開してよい行だけを明示指定すること（全承認はしない）。
"""
import json
import sys
import time
import urllib.request

API = "https://script.google.com/macros/s/AKfycbz6A_7okvNBKrrygHuOgJ4TQV1YlrB_UPx2_c3hMS9fG6YTunOrrOKROeHdHJg2QzXj/exec"
KEY = "yasasea-kawachan-review-2026"
UA = {"User-Agent": "Mozilla/5.0"}


def get_json(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e
            print(f"[retry {i+1}/{tries}] {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(2 * (i + 1))
    raise SystemExit(f"[fatal] GET {tries}回失敗: {last}")


def post_json(payload, tries=4):
    # Content-Type は text/plain にする（CORSプリフライト回避・Apps Script標準）。
    # urllib は 302 を GET で追い、doPost の実行結果JSONを拾う（curl -L はここで405になる）。
    body = json.dumps(payload).encode("utf-8")
    hdr = dict(UA); hdr["Content-Type"] = "text/plain;charset=utf-8"
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(API, data=body, headers=hdr)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e
            print(f"[retry {i+1}/{tries}] {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(2 * (i + 1))
    raise SystemExit(f"[fatal] POST {tries}回失敗: {last}")


def feedback_list():
    rows = get_json(f"{API}?feedback=1&key={KEY}")
    if not rows:
        print("未報告のご意見はありません。")
        return
    print(f"未報告のご意見 {len(rows)}件:")
    for r in rows:
        print(f"  行{r['row']} | {r['date'][:10]} | {r['name']} | {r['msg'][:60]}")


def feedback_mark(rows):
    res = post_json({"action": "markFeedbackReported", "key": KEY, "rows": rows})
    print("結果:", res)


def photos_list():
    rows = get_json(f"{API}?photosAll=1&key={KEY}")
    pend = [r for r in rows if not r.get("approved")]
    print(f"未承認の写真投稿 {len(pend)}件（全{len(rows)}件中）:")
    for r in pend:
        print(f"  行{r['row']} | {r['date'][:10]} | {r['name']} | {r['aquarium']} | {r.get('msg','')[:40]}")


def photos_approve(rows):
    res = post_json({"action": "approvePhotos", "key": KEY, "rows": rows})
    print("結果:", res)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    args = [int(x) for x in sys.argv[2:] if x.isdigit()]
    if cmd == "feedback-list":
        feedback_list()
    elif cmd == "feedback-mark":
        if not args:
            raise SystemExit("行番号を指定してください（例: feedback-mark 24 25）")
        feedback_mark(args)
    elif cmd == "photos-list":
        photos_list()
    elif cmd == "photos-approve":
        if not args:
            raise SystemExit("行番号を指定してください（例: photos-approve 12 34）")
        photos_approve(args)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
