#!/usr/bin/env python3
"""ぬりえHP を「3つのURL」だけで更新するスクリプト。

かわちゃんが毎週ライブ後に出す3点：
  ① この回のライブ配信URL（そのぬりえを描いた配信）
  ② 新しいぬりえの Google Drive URL
  ③ 次回のライブURL

使い方（順不同でOK・YouTubeとDriveを見分けて自動判定）：
  python3 update_nurie.py \
    "https://youtu.be/pOk-vpzOFBc" \
    "https://drive.google.com/file/d/1ltNcE.../view" \
    "https://youtu.be/0Y7WIrtv9sY"

やること：
  - 3つのURLからID抽出（YouTube2本＝配信＋次回、Drive1本＝ぬりえ）
  - Driveの公開ページから ぬりえの名前を自動取得（共有=リンクを知る全員 前提）
  - nurie_src/extra.tsv に新ぬりえを追記（週末おさかな部）
  - nurie_src/videos.json を更新（ぬりえ→配信 の対応・次回ライブ）
  - build_nurie.py で nurie_data.json を再生成
  - git add/commit/push（--no-push で止められる）

注意：
  - Driveのぬりえは「リンクを知っている全員が閲覧可」で共有されていること（表示・DLに必須）
  - どのYouTubeが「この回」でどれが「次回」か紛らわしいときは順番どおり（①配信 ②Drive ③次回）で渡す
"""
import sys, re, json, subprocess, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "nurie_src"
EXTRA = SRC / "extra.tsv"
VIDEOS_JSON = SRC / "videos.json"

YT = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|live/|shorts/))([A-Za-z0-9_-]{11})")
DRIVE = re.compile(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)?([A-Za-z0-9_-]{25,})")
DRIVE2 = re.compile(r"[?&]id=([A-Za-z0-9_-]{25,})")


def yt_id(u):
    m = YT.search(u); return m.group(1) if m else None

def drive_id(u):
    m = DRIVE.search(u) or DRIVE2.search(u)
    return m.group(1) if m else None

def fetch_title(fid):
    """Drive公開ページから元のファイル名を取得（共有ファイルのみ）。"""
    url = f"https://drive.google.com/file/d/{fid}/view"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    m = re.search(r'itemprop="name"\s+content="([^"]+)"', html) or \
        re.search(r'og:title"\s+content="([^"]+)"', html) or \
        re.search(r"<title>(.*?)</title>", html, re.S)
    if not m:
        return None
    t = m.group(1)
    return re.sub(r"\s*-\s*Google\s*(ドライブ|Drive)\s*$", "", t).strip()

def check_public(fid):
    url = f"https://drive.google.com/thumbnail?id={fid}&sz=w400"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status == 200 and r.headers.get_content_type().startswith("image/")
    except Exception:
        return False


def main(argv):
    push = "--no-push" not in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 3:
        print(__doc__); sys.exit(1)

    yts, drives = [], []
    for a in args:
        if drive_id(a) and "drive.google" in a:
            drives.append(drive_id(a))
        elif yt_id(a):
            yts.append(yt_id(a))
    if len(drives) != 1 or len(yts) != 2:
        print(f"❌ URLを判定できませんでした（Drive×1・YouTube×2 が必要）。Drive={drives} YT={yts}")
        print("   順番どおり ①配信 ②Drive ③次回 で渡してみてください。")
        sys.exit(1)

    coloring_id = drives[0]
    live_id = yts[0]        # ① この回の配信（引数の並び順で先に来たYouTube）
    next_id = yts[1]        # ③ 次回ライブ

    print(f"🎨 ぬりえ    : {coloring_id}")
    print(f"🔴 この回配信 : {live_id}")
    print(f"📅 次回ライブ : {next_id}")

    if not check_public(coloring_id):
        print("⚠️  このDriveぬりえは公開（リンクを知る全員が閲覧可）になっていないようです。")
        print("    共有設定を確認してください。処理は続行しますが、表示されない可能性があります。")

    title = fetch_title(coloring_id) or "おさかなぬりえ"
    print(f"📝 タイトル   : {title}")

    # extra.tsv に追記（重複IDはスキップ）
    lines = EXTRA.read_text(encoding="utf-8").splitlines()
    ids = {ln.split("\t")[0] for ln in lines if ln.strip()}
    if coloring_id in ids:
        print("ℹ️  すでに登録済みのぬりえIDです（extra.tsvは変更なし）。")
    else:
        with EXTRA.open("a", encoding="utf-8") as f:
            f.write(f"{coloring_id}\t{title}\tweekly\n")
        print("✅ extra.tsv に追記しました。")

    # videos.json を更新
    vid = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    vid["map"][coloring_id] = live_id
    vid["next_live"] = next_id
    VIDEOS_JSON.write_text(json.dumps(vid, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("✅ videos.json を更新しました。")

    # 再生成
    subprocess.run([sys.executable, str(HERE / "build_nurie.py")], check=True)

    if push:
        subprocess.run(["git", "-C", str(HERE), "add",
                        "nurie_data.json", "nurie_src/extra.tsv", "nurie_src/videos.json"], check=True)
        subprocess.run(["git", "-C", str(HERE), "commit", "-q", "-m",
                        f"ぬりえHP更新：{title}（配信{live_id}／次回{next_id}）"], check=True)
        subprocess.run(["git", "-C", str(HERE), "push", "-q", "origin", "HEAD"], check=True)
        print("🚀 コミット＆プッシュ完了。1〜2分で aquarium.yasasea.com/nurie.html に反映されます。")
    else:
        print("（--no-push のためコミットはしていません）")


if __name__ == "__main__":
    main(sys.argv[1:])
