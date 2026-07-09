#!/usr/bin/env python3
# data.json から水族館ごとの個別ページ(spot/*.html)とsitemap.xmlを生成する
# 使い方: python3 build_pages.py  → git add spot sitemap.xml → commit/push
import json, os, html, re, unicodedata

SITE = "https://aquarium.yasasea.com"
os.makedirs("spot", exist_ok=True)

TAG_LABEL = {"rain":"☔️ 雨の日におすすめ","kids":"👶 未就学児におすすめ","same":"🦈 サメ好きにおすすめ",
             "dolphin":"🐬 イルカショーおすすめ","deep":"🐙 深海生物好きにおすすめ",
             "penguin":"🐧 ペンギン好きにおすすめ","summer":"☀️ 夏休みおすすめ"}
ANIMAL_ICONS = {"シャチ":"🐋","ラッコ":"🦦","ジンベエザメ":"🦈","シロワニ":"🦈","マンボウ":"🐟",
                "ピラルクー":"🐠","エンペラーペンギン":"🐧","フェアリーペンギン":"🐧","クラゲ":"🪼"}

def slugify(name, no=None):
    if no is not None:
        return f"{no:03d}"
    s = unicodedata.normalize("NFKC", name)
    return "u-" + re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") if s.isascii() else "u-" + str(abs(hash(name)) % 100000)

d = json.load(open("data.json"))
entries = []
for a in d["aquariums"]:
    entries.append((f"{a['no']:03d}", a, True))
for i, a in enumerate(d["unvisited"]):
    entries.append((f"u{i:03d}", a, False))

E = html.escape
urls = []
for slug, a, intro in entries:
    v = (a.get("videos") or [None])[0]
    thumb = f"https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg" if v else ""
    ogimg = f"https://i.ytimg.com/vi/{v['id']}/maxresdefault.jpg" if v else f"{SITE}/assets/kawachan_web.png"
    desc_parts = []
    if a.get("highlight"): desc_parts.append(a["highlight"])
    if a.get("comment"): desc_parts.append(a["comment"])
    if a.get("fee"): desc_parts.append(f"大人{a['fee']}")
    if a.get("closed"): desc_parts.append(f"休み:{a['closed']}")
    desc = E(" / ".join(desc_parts)[:140] or f"{a['name']}（{a['pref']}）の料金・休館日・みどころ")
    title = f"{a['name']}の料金・休館日・みどころ | 全国水族館ツアーMAP"

    chips = "".join(f'<span class="chip">{ANIMAL_ICONS.get(x,"🐟")} {E(x)}</span>' for x in a.get("animals", []))
    if a.get("only"): chips += f'<span class="chip only">⭐️ここだけ！{E(a["only"])}</span>'
    tagchips = "".join(f'<span class="chip tag">{TAG_LABEL[t]}</span>' for t in a.get("tags", []) if t in TAG_LABEL)

    info = ""
    if a.get("fee"): info += f"<tr><th>💰 大人</th><td>{E(a['fee'])}</td></tr>"
    if a.get("child"): info += f"<tr><th>🧒 子ども</th><td>{E(a['child'])}</td></tr>"
    if a.get("closed"): info += f"<tr><th>🗓 休館日</th><td>{E(a['closed'])}</td></tr>"
    if a.get("gift"): info += f"<tr><th>🎁 おみやげ</th><td>{E(a['gift'])}</td></tr>"
    if a.get("access"): info += f"<tr><th>🚃 アクセス</th><td>{E(a['access'])}</td></tr>"

    hitokoto = ""
    if a.get("hitokoto"):
        hitokoto = f'<div class="hitokoto"><div class="hk-label">🐟 かわちゃんからの一言</div>{E(a["hitokoto"])}</div>'

    summer = f'<div class="summer">☀️ <b>夏休み情報：</b>{E(a["summer"])}</div>' if a.get("summer") else ""
    videos = "".join(
        f'<div class="video"><iframe loading="lazy" src="https://www.youtube.com/embed/{vv["id"]}" '
        f'title="{E(a["name"])} 紹介動画" allowfullscreen></iframe></div>'
        for vv in a.get("videos", []))
    hero = f'<img class="hero" src="{thumb}" alt="{E(a["name"])}">' if (thumb and not videos) else ""
    kicker = "かわちゃんが動画で紹介した水族館🐟" if intro else "これから紹介したい水族館🔜"

    links = ""
    if a.get("url"): links += f'<a class="btn hp" href="{E(a["url"])}" target="_blank" rel="noopener">公式サイト🔗</a>'
    sns = a.get("sns") or {}
    if sns.get("x"): links += f'<a class="btn sns" href="{E(sns["x"])}" target="_blank" rel="noopener">𝕏</a>'
    if sns.get("instagram"): links += f'<a class="btn sns" href="{E(sns["instagram"])}" target="_blank" rel="noopener">📷 Instagram</a>'

    share_text = f"{a['name']}、行ってみたい！🐟 #全国水族館ツアーMAP"
    page_url = f"{SITE}/spot/{slug}.html"
    urls.append(page_url)

    doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{E(title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{ogimg}">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary_large_image">
<style>
  :root {{ --sea:#0096c7; --sea-deep:#023e8a; --sky:#caf0f8; --sand:#fff9ec; --coral:#ff6b6b; --sun:#ffd166; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"Hiragino Maru Gothic ProN","Rounded Mplus 1c",sans-serif; background:var(--sand); color:#234; }}
  header {{ background:linear-gradient(180deg,#48cae4,#0096c7); color:#fff; padding:14px 16px; }}
  header a {{ color:#fff; text-decoration:none; font-weight:bold; font-size:.9rem; }}
  main {{ max-width:720px; margin:0 auto; padding:20px 16px 40px; }}
  .kicker {{ color:var(--sea); font-weight:bold; font-size:.85rem; }}
  h1 {{ color:var(--sea-deep); font-size:1.5rem; margin:4px 0 2px; }}
  .pref {{ font-size:.8rem; color:#fff; background:var(--sea); border-radius:999px; padding:2px 12px; }}
  .hl {{ margin:12px 0; line-height:1.7; }}
  .hero {{ width:100%; border-radius:16px; margin:10px 0; }}
  .video {{ aspect-ratio:16/9; margin:12px 0; }}
  .video iframe {{ width:100%; height:100%; border:0; border-radius:16px; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:6px; margin:10px 0; }}
  .chip {{ font-size:.78rem; font-weight:bold; background:#e8f6fb; color:#075985; border:1.5px solid #7dd3fc; border-radius:999px; padding:3px 10px; }}
  .chip.only {{ background:#fff7db; color:#92600a; border-color:#f4c430; }}
  .chip.tag {{ background:#fdf1e3; color:#c9660a; border-color:#f4a261; }}
  .hitokoto {{ background:#fff; border:3px solid var(--sea); border-radius:16px; padding:12px 16px; margin:14px 0; line-height:1.7; position:relative; }}
  .hitokoto .hk-label {{ font-size:.8rem; font-weight:bold; color:var(--sea); margin-bottom:4px; }}
  .summer {{ font-size:.9rem; color:#a15c00; background:linear-gradient(90deg,#fff3cd,#ffe9b8); border:2px solid var(--sun); border-radius:12px; padding:10px 14px; margin:12px 0; line-height:1.6; }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; background:#f0f8fc; border-radius:12px; overflow:hidden; }}
  th,td {{ text-align:left; padding:9px 14px; font-size:.9rem; border-bottom:2px solid var(--sand); }}
  th {{ white-space:nowrap; color:var(--sea-deep); }}
  .btns {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; }}
  .btn {{ font-size:.88rem; font-weight:bold; text-decoration:none; border-radius:999px; padding:8px 16px; }}
  .btn.hp {{ background:var(--sky); color:var(--sea-deep); }}
  .btn.sns {{ background:#eef2f6; color:#334; }}
  .btn.share {{ background:var(--coral); color:#fff; border:none; font-family:inherit; cursor:pointer; }}
  .back {{ display:inline-block; margin-top:18px; color:var(--sea); font-weight:bold; text-decoration:none; }}
  .note {{ font-size:.75rem; color:#89a; margin-top:8px; }}
</style>
</head>
<body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
  <p class="kicker">{kicker}</p>
  <h1>{E(a['name'])}</h1>
  <span class="pref">{E(a['pref'])}</span>
  {videos or hero}
  <p class="hl">{E(a.get('highlight') or a.get('comment') or '')}</p>
  <div class="chips">{chips}{tagchips}</div>
  {hitokoto}
  {summer}
  <table>{info}</table>
  <p class="note">※最新の料金・営業情報は公式サイトでチェックしてね</p>
  <div class="btns">
    {links}
    <a class="btn share" href="https://twitter.com/intent/tweet?text={html.escape(share_text)}&url={page_url}" target="_blank" rel="noopener">🕊 シェアする</a>
  </div>
  <a class="back" href="{SITE}/">← MAPにもどる</a>
</main>
</body>
</html>"""
    with open(f"spot/{slug}.html", "w") as f:
        f.write(doc)

with open("sitemap.xml", "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    f.write(f"<url><loc>{SITE}/</loc></url>\n")
    for u in urls:
        f.write(f"<url><loc>{u}</loc></url>\n")
    f.write("</urlset>\n")

print(f"{len(urls)} pages + sitemap.xml generated")
