#!/usr/bin/env python3
# data.json から水族館ごとの個別ページ(spot/*.html)とsitemap.xmlを生成する
# 使い方: python3 build_pages.py  → git add spot sitemap.xml → commit/push
import json, os, html, re, unicodedata, urllib.parse

SITE = "https://aquarium.yasasea.com"
COMMENT_API = "https://script.google.com/macros/s/AKfycbz6A_7okvNBKrrygHuOgJ4TQV1YlrB_UPx2_c3hMS9fG6YTunOrrOKROeHdHJg2QzXj/exec"
YT_API_KEY = "AIzaSyCASXQcc_wH8jOy9PA2oa5dUlBWUgRBGms"
os.makedirs("spot", exist_ok=True)

# LLMO（AI検索対策）: 引用時に必ず名前が付いてくるようにするための表記
BRAND_NAME = "全国水族館ツアーMAP"
AUTHOR_NAME = "さかなのおにいさん かわちゃん"
SOURCE_LINE = f"出典：{BRAND_NAME}（{AUTHOR_NAME}）"
ATTR_FOOTER = (f'<p class="attr-footer">🐟 {SOURCE_LINE} / {{SITE}}<br>'
               f'運営：<a href="{{SITE}}/about.html#company">株式会社やさしいうみ</a>　'
               f'<a href="{{SITE}}/about.html#work">💼 お仕事のご依頼</a>　'
               f'<a href="{{SITE}}/posts.html#iken">📮 ご意見箱</a>　'
               f'<a href="{{SITE}}/about.html#privacy">プライバシーポリシー</a></p>').replace("{SITE}", SITE)
ATTR_CSS = '.attr-footer { font-size:.72rem; color:#9ab; margin-top:24px; text-align:center; line-height:2; } .attr-footer a { color:#89a; }'

GA_ID = "G-J4C3DJNZQN"
GA_SNIPPET = f'''<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>'''

TAG_LABEL = {"rain":"☔️ 雨の日におすすめ","kids":"👶 未就学児におすすめ","same":"🦈 サメ好きにおすすめ",
             "dolphin":"🐬 イルカショーおすすめ","deep":"🐙 深海生物好きにおすすめ",
             "penguin":"🐧 ペンギン好きにおすすめ","summer":"☀️ 夏休みおすすめ",
             "baby":"🍼 赤ちゃん連れにおすすめ","shachi":"🐋 シャチに会える","beluga":"🐳 シロイルカに会える",
             "fishing":"🎣 釣りができる水族館","kaichu":"🗼 海中展望台（服のまま海の中をのぞける）"}
ANIMAL_ICONS = {"シャチ":"🐋","ラッコ":"🦦","ジンベエザメ":"🦈","シロワニ":"🦈","マンボウ":"🐟",
                "ピラルクー":"🐠","エンペラーペンギン":"🐧","フェアリーペンギン":"🐧","クラゲ":"🪼","ベルーガ":"🐳"}

def slugify(name, no=None):
    if no is not None:
        return f"{no:03d}"
    s = unicodedata.normalize("NFKC", name)
    return "u-" + re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") if s.isascii() else "u-" + str(abs(hash(name)) % 100000)

d = json.load(open("data.json"))
_updated = d.get("updated", "")
_m = re.match(r"(\d{4})-(\d{2})", _updated)
INFO_ASOF = f"{int(_m.group(1))}年{int(_m.group(2))}月" if _m else _updated
entries = []
for a in d["aquariums"]:
    entries.append((f"{a['no']:03d}", a, True))
for i, a in enumerate(d["unvisited"]):
    entries.append((f"u{i:03d}", a, False))

E = html.escape
urls = []
entry_meta = []
for slug, a, intro in entries:
    v = (a.get("videos") or [None])[0]
    photo = a.get("photo") or ""
    photo_path = "/".join(urllib.parse.quote(seg) for seg in photo.split("/")) if photo else ""
    photo_url = photo_path if photo_path.startswith("http") else f"{SITE}/{photo_path}" if photo_path else ""
    thumb = f"https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg" if v else photo_url
    ogimg = f"https://i.ytimg.com/vi/{v['id']}/maxresdefault.jpg" if v else (photo_url or f"{SITE}/assets/kawachan_web.png")
    desc_parts = []
    if a.get("highlight"): desc_parts.append(a["highlight"])
    if a.get("comment"): desc_parts.append(a["comment"])
    if a.get("fee"): desc_parts.append(f"大人{a['fee']}")
    if a.get("closed"): desc_parts.append(f"休み:{a['closed']}")
    desc = E(" / ".join(desc_parts)[:140] or f"{a['name']}（{a['pref']}）の料金・休館日・みどころ")
    title = f"{a['name']}の料金・休館日・みどころ | 全国水族館ツアーMAP"

    chips = "".join(f'<span class="chip">{ANIMAL_ICONS.get(x,"🐟")} {E(x)}</span>' for x in a.get("animals", []))
    if a.get("only"): chips += f'<span class="chip only">⭐️ここだけ！{E(a["only"])}</span>'
    if a.get("rakko_past"):
        rp_tip = E(a["rakko_past_note"]) if a.get("rakko_past_note") else "かつてラッコを飼育していた水族館です（今はいません）"
        chips += f'<span class="chip rakko-past" title="{rp_tip}">🦦 ラッコ（かつていた）</span>'
    if a.get("mendako_history"):
        md_tip = E(a["mendako_note"]) if a.get("mendako_note") else "メンダコを展示した実績があります（展示は不定期）"
        chips += f'<span class="chip mendako-hist" title="{md_tip}">🐙 メンダコ（展示実績あり）</span>'
    tagchips = "".join(f'<span class="chip tag">{TAG_LABEL[t]}</span>' for t in a.get("tags", []) if t in TAG_LABEL)

    # 交通手段の目安チップ（access/parkingの記載から機械的に判定。誤爆しないよう保守的に）
    acc = a.get("access") or ""
    transport = []
    if "駅" in acc and "徒歩" in acc: transport.append("🚃 駅から徒歩OK")
    if "バス" in acc: transport.append("🚌 バスあり")
    park = str(a.get("parking") or "")
    if park and not park.startswith("なし"): transport.append("🚗 駐車場あり")
    elif not transport and ("車" in acc or "IC" in acc): transport.append("🚗 車がおすすめ")
    trchips = "".join(f'<span class="chip tr">{t}</span>' for t in transport)

    # 「日本で◯◯に会えるのはここだけ」の文章表示は、⭐️ここだけ！チップや一言と重複するため非表示
    # （onlyの情報自体はチップ・llms.txtで引き続き発信される）
    only_quote = ""

    info = ""
    if a.get("fee"): info += f"<tr><th>💰 大人</th><td>{E(a['fee'])}</td></tr>"
    if a.get("child"): info += f"<tr><th>🧒 子ども</th><td>{E(a['child'])}</td></tr>"
    if a.get("infant"): info += f"<tr><th>👶 幼児（未就学）</th><td>{E(a['infant'])}</td></tr>"
    if a.get("duration"): info += f"<tr><th>⏱ 所要時間の目安</th><td>{E(a['duration'])}</td></tr>"
    if a.get("closed"): info += f"<tr><th>🗓 休館日</th><td>{E(a['closed'])}</td></tr>"
    if a.get("access"): info += f"<tr><th>🚃 アクセス</th><td>{E(a['access'])}</td></tr>"
    if a.get("stroller"): info += f"<tr><th>🛻 ベビーカー</th><td>{E(a['stroller'])}</td></tr>"
    if a.get("nursing"): info += f"<tr><th>🍼 授乳室</th><td>{E(a['nursing'])}</td></tr>"
    if a.get("locker"): info += f"<tr><th>🔒 ロッカー</th><td>{E(a['locker'])}</td></tr>"
    if a.get("parking"): info += f"<tr><th>🚗 駐車場</th><td>{E(a['parking'])}</td></tr>"
    if a.get("food_bring"): info += f"<tr><th>🧺 飲食物持込</th><td>{E(a['food_bring'])}</td></tr>"
    if a.get("restaurant"): info += f"<tr><th>🍽 フード</th><td>{E(a['restaurant'])}</td></tr>"
    if a.get("gift"): info += f"<tr><th>🎁 おみやげ</th><td>{E(a['gift'])}</td></tr>"
    if a.get("goshuin"): info += f"<tr><th>🐟 魚朱印</th><td>{E(a['goshuin'])}</td></tr>"

    approved = bool(a.get("visited")) and bool(a.get("verified"))

    hitokoto = ""
    if approved and a.get("hitokoto"):
        hk_photo = a.get("hitokoto_photo")
        if hk_photo:
            hp = "/".join(urllib.parse.quote(seg) for seg in hk_photo.split("/"))
            img_html = f'<img class="hk-photo" src="{SITE}/{hp}" alt="{E(a["name"])}でのかわちゃん" loading="lazy">'
            parts = a["hitokoto"].split("\n\n", 1)
            hk_inner = E(parts[0]) + img_html + (E(parts[1]) if len(parts) > 1 else "")
        else:
            hk_inner = E(a["hitokoto"])
        hitokoto = (f'<div class="hitokoto"><div class="hk-label">🐟 かわちゃんからの一言</div>'
                    f'<div class="hk-text">{hk_inner}'
                    f'<a href="{SITE}/about.html#profile" class="hk-chara-link" title="かわちゃんについてもっと知る">'
                    f'<img class="hk-chara" src="{SITE}/assets/kawachan_point.png" alt="{AUTHOR_NAME}について詳しく" loading="lazy">'
                    f'<span class="hk-chara-cap">かわちゃんって？</span></a></div></div>')

    # この館ならではの楽しみ方のコツ（本人承認済みの館のみ表示）
    kotsu_box = ""
    if approved and a.get("kotsu"):
        kotsu_box = (f'<div class="kotsu-box"><div class="hk-label">🎯 {AUTHOR_NAME}流・この水族館の楽しみ方</div>{E(a["kotsu"])}'
                     f'<a class="kotsu-more" href="{SITE}/guide.html">▶ どの水族館でも使える「かわちゃん流の楽しみ方」はこちら</a></div>')

    # 見どころポイント欄は「かわちゃんからの一言」と重複するため廃止（highlightsデータ自体はdata.jsonに保持）

    # 星は「強い軸（★4以上）」だけを表示するイチオシ形式。
    # 低評価の星を並べると施設側に「採点された」と映るため、弱い軸はページに出さない
    # （ratingsデータ自体はdata.jsonに全軸保持し、ランキング等の内部判断に使う）
    RATING_LABEL = {"rare":"🦈 激レアいきもの","kyodai":"🐋 巨大生物","perf":"🐬 パフォーマンス","kids":"👶 子ども向け度","cospa":"💰 コスパ","kuse":"🌀 クセつよポイント"}
    ratings = a.get("ratings") or {}
    rating_rows = ""
    if approved:
        for key, label in RATING_LABEL.items():
            if key in ratings:
                n = max(0, min(5, int(ratings[key])))
                if n < 4:
                    continue
                stars = "★"*n + "☆"*(5-n)
                rating_rows += f'<div class="rate-row"><span class="rate-label">{label}</span><span class="rate-stars">{stars}</span></div>'
        # 標準5軸で弱い軸のかわりに「その館らしい強み」を独自軸で表示（data.jsonのratings_plus）
        for label, val in (a.get("ratings_plus") or {}).items():
            n = max(0, min(5, int(val)))
            stars = "★"*n + "☆"*(5-n)
            rating_rows += f'<div class="rate-row"><span class="rate-label">{E(label)}</span><span class="rate-stars">{stars}</span></div>'
    ratings_box = f'<div class="ratings-box"><div class="hk-label">🐟 {AUTHOR_NAME}のイチオシポイント</div>{rating_rows}</div>' if rating_rows else ""

    summer = f'<div class="summer">☀️ <b>2026年 夏休み情報：</b>{E(a["summer"])}</div>' if a.get("summer") else ""
    notice = f'<div class="notice-box">⚠️ <b>ご注意：</b>{E(a["notice"])}</div>' if a.get("notice") else ""
    videos = "".join(
        f'<div class="video"><iframe loading="lazy" src="https://www.youtube.com/embed/{vv["id"]}" '
        f'title="{E(a["name"])} 紹介動画" allowfullscreen></iframe></div>'
        for vv in a.get("videos", []))
    hero = f'<img class="hero" src="{thumb}" alt="{E(a["name"])}">' if (thumb and not videos) else ""
    kicker = "かわちゃんが動画で紹介した水族館🐟" if intro else "これから紹介したい水族館🔜"
    filming_note = '<p class="filming-note">📷 動画・写真は水族館の特別な許可を得て撮影しています</p>' if intro else ''

    links = ""
    if a.get("url"): links += f'<a class="btn hp" href="{E(a["url"])}" target="_blank" rel="noopener">公式サイト🔗</a>'
    sns = a.get("sns") or {}
    if sns.get("x"): links += f'<a class="btn sns" href="{E(sns["x"])}" target="_blank" rel="noopener">𝕏</a>'
    if sns.get("instagram"): links += f'<a class="btn sns" href="{E(sns["instagram"])}" target="_blank" rel="noopener">📷 Instagram</a>'

    ytc_box = '<div class="ytc-box"><h3>▶ YouTubeのコメント</h3><div id="ytc-list"><p class="loading">読み込み中…</p></div></div>' if v else ''
    ng_list = '["死ね","殺す","バカ","馬鹿","アホ","キモ","反対","抗議","虐待","動物愛護","愛護団体","保護団体","アニマルライツ","ヴィーガン","監禁","搾取","奴隷","解放しろ","閉鎖しろ","追い込み漁","boycott","ボイコット","署名","http://","https://"]'
    yt_js = f'''const YT_API_KEY = "{YT_API_KEY}";
const YT_VID = "{v['id']}";
async function loadYtComments() {{
  const el = document.getElementById("ytc-list");
  const NG = {ng_list};
  try {{
    const url = "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId=" + YT_VID + "&maxResults=30&order=relevance&key=" + YT_API_KEY;
    const res = await fetch(url);
    const d = await res.json();
    const POS = ['かわいい','可愛い','感動','最高','好き','癒','楽しい','たのしい','きれい','綺麗','面白','おもしろ','行きたい','よかった','良かった','うれしい','嬉しい','素敵','すごい','凄い','ありがとう','大好き','美しい','幸せ','素晴らしい','驚','ワクワク','わくわく'];
    const posScore = t => POS.reduce((n,w)=> n + (t.includes(w)?1:0), 0);
    const clean = (d.items||[]).map(i=>i.snippet.topLevelComment.snippet)
      .filter(c=>!NG.some(w=>(c.textDisplay+c.authorDisplayName).toLowerCase().includes(w.toLowerCase())))
      .map(c=>({{...c, _score: posScore(c.textDisplay) * 10 + (c.likeCount||0)}}))
      .sort((a,b)=> b._score - a._score);
    const positive = clean.filter(c=>c._score > 0);
    const items = positive.length ? positive : clean;
    if (!items.length) {{ el.innerHTML = '<p class="empty">コメントなし</p>'; return; }}
    el.innerHTML = items.slice(0,3).map(c=>'<div class="c-item"><span class="c-name">👤 '+c.authorDisplayName+'</span><span class="c-msg">'+c.textDisplay.slice(0,120)+'</span></div>').join('');
  }} catch(e) {{ el.innerHTML = '<p class="empty">読み込みエラー</p>'; }}
}}
loadYtComments();''' if v else ''
    share_text = f"{a['name']}、行ってみたい！🐟 #全国水族館ツアーMAP"
    page_url = f"{SITE}/spot/{slug}.html"
    urls.append(page_url)

    ld_attraction = {
        "@context": "https://schema.org",
        "@type": "TouristAttraction",
        "name": a["name"],
        "url": page_url,
        "image": ogimg,
        "address": {"@type": "PostalAddress", "addressRegion": a.get("pref", ""), "addressCountry": "JP"},
    }
    if a.get("lat") and a.get("lng"):
        ld_attraction["geo"] = {"@type": "GeoCoordinates", "latitude": a["lat"], "longitude": a["lng"]}
    if a.get("url"): ld_attraction["sameAs"] = a["url"]
    desc_for_ld = a.get("highlight") or a.get("comment")
    if desc_for_ld: ld_attraction["description"] = desc_for_ld
    ld_attraction["publisher"] = {"@type": "Organization", "name": BRAND_NAME, "url": SITE}

    faq_items = []
    if a.get("fee"): faq_items.append(("料金はいくらですか？", f"大人{a['fee']}" + (f"、子ども{a['child']}" if a.get("child") else "") + (f"、幼児{a['infant']}" if a.get("infant") else "")))
    if a.get("closed"): faq_items.append(("休館日はいつですか？", a["closed"]))
    if a.get("parking"): faq_items.append(("駐車場はありますか？", a["parking"]))
    ld_faq = None
    if faq_items:
        ld_faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
                for q, ans in faq_items
            ],
        }

    # かわちゃんの一言・評価を「発信者名と切り離せない」形で機械可読化するReviewスキーマ
    # 本人承認済み（visited & verified）の館のみ生成
    ld_review = None
    if bool(a.get("visited")) and bool(a.get("verified")) and (a.get("hitokoto") or a.get("ratings")):
        review = {
            "@context": "https://schema.org",
            "@type": "Review",
            "itemReviewed": {"@type": "TouristAttraction", "name": a["name"]},
            "author": {"@type": "Person", "name": AUTHOR_NAME},
            "publisher": {"@type": "Organization", "name": BRAND_NAME, "url": SITE},
            "url": page_url,
        }
        if a.get("hitokoto"): review["reviewBody"] = f"{AUTHOR_NAME}の一言：{a['hitokoto']}"
        # reviewRating（5段階平均）は検索結果に「点数」として表示され施設側の心証を損ねるため出力しない
        ld_review = review

    ld_scripts = f'<script type="application/ld+json">{json.dumps(ld_attraction, ensure_ascii=False)}</script>'
    if ld_faq:
        ld_scripts += f'\n<script type="application/ld+json">{json.dumps(ld_faq, ensure_ascii=False)}</script>'
    if ld_review:
        ld_scripts += f'\n<script type="application/ld+json">{json.dumps(ld_review, ensure_ascii=False)}</script>'

    entry_meta.append({
        "slug": slug, "name": a["name"], "pref": a.get("pref", ""), "url": page_url,
        "thumb": thumb or ogimg, "animals": a.get("animals") or [], "tags": a.get("tags") or [],
        "rakko_past": bool(a.get("rakko_past")), "rakko_past_note": a.get("rakko_past_note") or "",
        "mendako_history": bool(a.get("mendako_history")),
        "comment": a.get("highlight") or a.get("comment") or "", "lat": a.get("lat"), "lng": a.get("lng"),
        "stroller": a.get("stroller"), "nursing": a.get("nursing"), "locker": a.get("locker"),
        "ratings": a.get("ratings") if (a.get("visited") and a.get("verified")) else None,
    })

    doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{GA_SNIPPET}
<title>{E(title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{ogimg}">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/x-icon" href="../assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="../assets/apple-touch-icon.png">
{ld_scripts}
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
  .chip.tr {{ background:#eefbe7; color:#2f7d32; border-color:#8fd694; }}
  .chip.rakko-past {{ background:#f3eee7; color:#8a6d3b; border-color:#d8c3a5; border-style:dashed; }}
  .chip.rakko-past small {{ font-weight:normal; opacity:.75; }}
  .chip.mendako-hist {{ background:#efeaf6; color:#6b4f9e; border-color:#c9b8e8; border-style:dashed; }}
  .hitokoto {{ background:#fff; border:3px solid var(--sea); border-radius:16px; padding:12px 16px; margin:14px 0; line-height:1.7; }}
  .hitokoto .hk-label {{ font-size:.8rem; font-weight:bold; color:var(--sea); margin-bottom:6px; }}
  .hitokoto .hk-text {{ white-space:pre-line; overflow:hidden; }}
  .hitokoto .hk-photo {{ display:block; width:100%; max-width:440px; border-radius:12px; margin:12px auto; box-shadow:0 2px 8px rgba(2,62,138,.15); }}
  .hitokoto .hk-chara-link {{ float:right; margin:8px 0 2px 12px; text-align:center; text-decoration:none; }}
  .hitokoto .hk-chara {{ display:block; width:64px; height:auto; transition:transform .15s; }}
  .hitokoto .hk-chara-link:hover .hk-chara {{ transform:scale(1.06); }}
  .hitokoto .hk-chara-cap {{ display:block; font-size:.62rem; color:var(--sea); font-weight:bold; margin-top:2px; }}
  .kotsu-box {{ background:#fffbea; border:3px solid var(--sun); border-radius:16px; padding:12px 16px; margin:14px 0; line-height:1.7; }}
  .kotsu-box .hk-label {{ font-size:.8rem; font-weight:bold; color:#c78a00; margin-bottom:4px; }}
  .kotsu-box .kotsu-more {{ display:block; margin-top:8px; font-size:.78rem; color:var(--sea); font-weight:bold; text-decoration:none; }}
  .highlights-box {{ background:#f6fbfe; border:3px solid var(--sky); border-radius:16px; padding:12px 16px; margin:14px 0; }}
  .highlights-box .hk-label {{ font-size:.8rem; font-weight:bold; color:var(--sea); margin-bottom:8px; }}
  .highlights-box ul {{ margin:0 0 0 20px; display:flex; flex-direction:column; gap:6px; }}
  .highlights-box li {{ font-size:.9rem; line-height:1.6; color:#345; }}
  .ratings-box {{ background:#fff9ec; border:3px solid var(--sun); border-radius:16px; padding:12px 16px; margin:14px 0; }}
  .ratings-box .hk-label {{ font-size:.8rem; font-weight:bold; color:#a15c00; margin-bottom:8px; }}
  .rate-row {{ display:flex; justify-content:space-between; align-items:center; padding:4px 0; font-size:.88rem; }}
  .rate-label {{ color:#456; }}
  .rate-stars {{ color:#ffb703; letter-spacing:1px; font-size:1rem; }}
  .summer {{ font-size:.9rem; color:#a15c00; background:linear-gradient(90deg,#fff3cd,#ffe9b8); border:2px solid var(--sun); border-radius:12px; padding:10px 14px; margin:12px 0; line-height:1.6; }}
  .notice-box {{ font-size:.9rem; color:#8a1f11; background:#fff0ee; border:2px solid var(--coral); border-radius:12px; padding:10px 14px; margin:12px 0; line-height:1.6; }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; background:#f0f8fc; border-radius:12px; overflow:hidden; }}
  th,td {{ text-align:left; padding:9px 14px; font-size:.9rem; border-bottom:2px solid var(--sand); }}
  th {{ white-space:nowrap; color:var(--sea-deep); }}
  .btns {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; }}
  .btn {{ font-size:.88rem; font-weight:bold; text-decoration:none; border-radius:999px; padding:8px 16px; }}
  .btn.hp {{ background:var(--sky); color:var(--sea-deep); }}
  .btn.sns {{ background:#eef2f6; color:#334; }}
  .btn.share {{ background:var(--coral); color:#fff; border:none; font-family:inherit; cursor:pointer; }}
  .back {{ display:inline-block; margin-top:18px; color:var(--sea); font-weight:bold; text-decoration:none; }}
  .backbtn {{ display:inline-block; margin-top:18px; margin-right:10px; background:var(--sea); color:#fff; font-weight:bold; font-size:.9rem; text-decoration:none; border-radius:999px; padding:10px 22px; box-shadow:0 2px 8px rgba(2,62,138,.25); }}
  .ytbtn {{ display:inline-block; margin-top:18px; margin-right:10px; background:#ff0000; color:#fff; font-weight:bold; font-size:.9rem; text-decoration:none; border-radius:999px; padding:10px 22px; box-shadow:0 2px 8px rgba(2,62,138,.25); }}
  .guidebtn {{ display:inline-block; margin-top:18px; margin-right:10px; background:var(--sea-deep); color:#fff; font-weight:bold; font-size:.9rem; text-decoration:none; border-radius:999px; padding:10px 22px; box-shadow:0 2px 8px rgba(2,62,138,.25); }}
  .note {{ font-size:.75rem; color:#89a; margin-top:8px; }}
  .filming-note {{ font-size:.75rem; color:#0077b6; background:#e0f7fa; border-radius:8px; padding:5px 12px; margin:6px 0 0; display:inline-block; }}
  .only-quote {{ font-size:.95rem; font-weight:bold; color:#92600a; background:#fff7db; border-left:5px solid #f4c430; border-radius:8px; padding:10px 14px; margin:12px 0; line-height:1.6; }}
  {ATTR_CSS}
  .comments-section {{ margin-top:28px; }}
  .comments-section h2 {{ color:var(--sea-deep); font-size:1.1rem; margin-bottom:16px; }}
  .sort-toggle {{ display:flex; gap:8px; margin-bottom:12px; }}
  .sort-toggle button {{ font-size:.78rem; font-weight:bold; border:2px solid var(--sea); background:#fff; color:var(--sea); border-radius:999px; padding:4px 14px; cursor:pointer; font-family:inherit; }}
  .sort-toggle button.active {{ background:var(--sea); color:#fff; }}
  .ytc-box, .user-comments-box {{ background:#fff; border-radius:16px; padding:16px; margin-bottom:16px; box-shadow:0 2px 8px rgba(2,62,138,.1); }}
  .ytc-box h3, .user-comments-box h3 {{ font-size:.9rem; color:var(--sea); margin-bottom:10px; }}
  .c-item {{ display:flex; flex-direction:column; gap:4px; padding:10px 0; border-bottom:1px solid #e8f4fb; }}
  .c-item:last-child {{ border-bottom:none; }}
  .c-name {{ font-size:.75rem; font-weight:bold; color:var(--sea); }}
  .c-msg {{ font-size:.85rem; color:#234; line-height:1.6; }}
  .c-foot {{ display:flex; align-items:center; gap:8px; }}
  .like-btn {{ background:none; border:1.5px solid #fbb6ce; border-radius:999px; padding:2px 10px; font-size:.75rem; color:#be185d; cursor:pointer; font-family:inherit; display:flex; align-items:center; gap:3px; transition:background .15s; }}
  .like-btn:hover, .like-btn.liked {{ background:#fce7f3; }}
  .like-btn.liked {{ border-color:#ec4899; font-weight:bold; }}
  .empty, .loading {{ font-size:.82rem; color:#89a; }}
  #comment-form {{ margin-top:12px; display:flex; flex-direction:column; gap:8px; }}
  #comment-form input, #comment-form textarea {{ border:2px solid var(--sky); border-radius:10px; padding:8px 12px; font-size:16px; font-family:inherit; outline:none; width:100%; }}
  #comment-form input:focus, #comment-form textarea:focus {{ border-color:var(--sea); }}
  #comment-form button {{ background:var(--sea); color:#fff; border:none; border-radius:999px; padding:10px; font-size:.9rem; font-weight:bold; cursor:pointer; font-family:inherit; }}
  #c-status {{ font-size:.8rem; color:var(--sea); min-height:1.2em; }}
</style>
</head>
<body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
  <p class="kicker">{kicker}</p>
  <h1>{E(a['name'])}</h1>
  <span class="pref">{E(a['pref'])}</span>
  {videos or hero}
  {notice}
  <p class="hl">{E(a.get('highlight') or a.get('comment') or '')}</p>
  {only_quote}
  <div class="chips">{chips}{trchips}</div>
  {kotsu_box}
  {ratings_box}
  {summer}
  <table>{info}</table>
  <p class="note">※{INFO_ASOF}時点の情報です。子ども・幼児料金の年齢区分は館ごとに異なります。おでかけ前に{('<a href="' + E(a["url"]) + '" target="_blank" rel="noopener">公式サイト</a>') if a.get("url") else "公式サイト"}をご確認ください</p>
  {hitokoto}
  {(f'<div class="chips tagchips-block">{tagchips}</div>') if tagchips else ''}
  {filming_note}
  <div class="btns">
    {links}
  </div>
  <a class="backbtn" href="{SITE}/">🗾 MAPにもどる</a>
  <a class="ytbtn" href="https://www.youtube.com/channel/UCNpTW5hGX4mKr3hxFu_nReA?sub_confirmation=1" target="_blank" rel="noopener">▶ チャンネル登録する</a>
  <a class="guidebtn" href="{SITE}/guide.html">🐬 かわちゃん流・水族館の楽しみ方</a>

  <section class="comments-section">
    <h2>💬 みんなのコメント</h2>
    {ytc_box}
    <div class="user-comments-box">
      <h3>🐟 行った感想を書いてね！</h3>
      <div class="sort-toggle">
        <button id="sort-new" class="active" onclick="setSort('new')">新着順</button>
        <button id="sort-like" onclick="setSort('like')">❤️ いいね順</button>
      </div>
      <div id="user-list"><p class="loading">読み込み中…</p></div>
      <form id="comment-form">
        <input type="text" id="c-name" placeholder="なまえ（省略OK）" maxlength="15">
        <textarea id="c-msg" placeholder="{E(a['name'])}の感想を書いてね！（80文字以内）" maxlength="80" rows="3" required></textarea>
        <button type="submit">送信する 🐟</button>
        <p id="c-status"></p>
      </form>
    </div>
  </section>
  {ATTR_FOOTER}
</main>
<script>
const COMMENT_API = "{COMMENT_API}";
const AQ_NAME = "{E(a['name'])}";
{yt_js}
let allComments = [];
let sortMode = 'new';
const likedKey = 'liked_' + AQ_NAME;
function getLiked() {{ try {{ return new Set(JSON.parse(localStorage.getItem(likedKey)||'[]')); }} catch(e) {{ return new Set(); }} }}
function saveLiked(s) {{ localStorage.setItem(likedKey, JSON.stringify([...s])); }}
function setSort(mode) {{
  sortMode = mode;
  document.getElementById('sort-new').classList.toggle('active', mode==='new');
  document.getElementById('sort-like').classList.toggle('active', mode==='like');
  renderComments();
}}
function renderComments() {{
  const el = document.getElementById('user-list');
  if (!allComments.length) {{ el.innerHTML = '<p class="empty">まだコメントがないよ！最初の感想を書いてみて🐟</p>'; return; }}
  const liked = getLiked();
  const sorted = [...allComments].sort((a,b) => sortMode==='like' ? (b.likes||0)-(a.likes||0) : 0);
  el.innerHTML = sorted.map(c => {{
    const isLiked = liked.has(c.id);
    return `<div class="c-item">
      <span class="c-name">🐟 ${{c.name}}</span>
      <span class="c-msg">${{c.msg}}</span>
      <div class="c-foot">
        <button class="like-btn${{isLiked?' liked':''}}" data-id="${{c.id}}" onclick="doLike(this,'${{c.id}}')">❤️ ${{c.likes||0}}</button>
      </div>
    </div>`;
  }}).join('');
}}
async function loadUserComments() {{
  const el = document.getElementById('user-list');
  try {{
    const res = await fetch(COMMENT_API + '?aquarium=' + encodeURIComponent(AQ_NAME));
    allComments = await res.json();
    renderComments();
  }} catch(e) {{ el.innerHTML = '<p class="empty">読み込みエラー</p>'; }}
}}
async function doLike(btn, id) {{
  const liked = getLiked();
  if (liked.has(id)) return;
  liked.add(id);
  saveLiked(liked);
  btn.classList.add('liked');
  try {{
    const res = await fetch(COMMENT_API, {{ method:'POST', body:JSON.stringify({{ action:'like', id }}) }});
    const d = await res.json();
    if (d.ok) {{
      const c = allComments.find(x=>x.id===id);
      if(c) c.likes = d.likes;
      btn.textContent = '❤️ ' + (d.likes||0);
    }}
  }} catch(e) {{}}
}}
loadUserComments();
document.getElementById('comment-form').onsubmit = async (ev) => {{
  ev.preventDefault();
  const name = document.getElementById('c-name').value.trim() || 'ななしのさかな';
  const msg = document.getElementById('c-msg').value.trim();
  const status = document.getElementById('c-status');
  if (!msg) return;
  status.textContent = '送信中…';
  try {{
    const res = await fetch(COMMENT_API, {{ method: 'POST', body: JSON.stringify({{ name, msg, aquarium: AQ_NAME }}) }});
    const d = await res.json();
    if (d.ok) {{
      status.textContent = '送信できたよ！ありがとう🐟';
      document.getElementById('c-msg').value = '';
      setTimeout(loadUserComments, 800);
    }} else {{ status.textContent = d.error || '送信エラー'; }}
  }} catch(e) {{ status.textContent = '送信エラー'; }}
}};
</script>
</body>
</html>"""
    with open(f"spot/{slug}.html", "w") as f:
        f.write(doc)

# ============================================================
# フェーズ3: 検索の入り口ページ（生き物別・エリア別・テーマ別・ランキング・About）
# トップページのUIには一切リンクしない「裏の入り口」。sitemap.xmlのみに登録
# ============================================================
os.makedirs("animals", exist_ok=True)
os.makedirs("area", exist_ok=True)
os.makedirs("theme", exist_ok=True)

LIST_STYLE = """
:root { --sea:#0096c7; --sea-deep:#023e8a; --sky:#caf0f8; --sand:#fff9ec; --coral:#ff6b6b; --sun:#ffd166; }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:"Hiragino Maru Gothic ProN","Rounded Mplus 1c",sans-serif; background:var(--sand); color:#234; }
header { background:linear-gradient(180deg,#48cae4,#0096c7); color:#fff; padding:14px 16px; }
header a { color:#fff; text-decoration:none; font-weight:bold; font-size:.9rem; }
main { max-width:900px; margin:0 auto; padding:20px 16px 40px; }
h1 { color:var(--sea-deep); font-size:1.4rem; margin:6px 0 4px; }
.lead { color:#456; font-size:.92rem; margin-bottom:14px; line-height:1.6; }
#map { width:100%; height:280px; border-radius:16px; margin:14px 0; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:14px; margin-top:16px; }
.card { background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 2px 10px rgba(2,62,138,.1); text-decoration:none; color:#234; display:flex; flex-direction:column; }
.card img { width:100%; aspect-ratio:16/9; object-fit:cover; background:var(--sky); }
.card .body { padding:10px 12px; }
.card .pref { font-size:.72rem; color:var(--sea); font-weight:bold; }
.card .name { font-size:.95rem; font-weight:bold; margin:2px 0 4px; }
.card .cmt { font-size:.78rem; color:#678; line-height:1.5; }
.back { display:inline-block; margin-top:20px; color:var(--sea); font-weight:bold; text-decoration:none; }
.taglist { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0; }
.taglist a { font-size:.85rem; font-weight:bold; background:#fff; color:var(--sea-deep); border:2px solid var(--sky); border-radius:999px; padding:6px 14px; text-decoration:none; }
.list-note { font-size:.75rem; color:#89a; margin-top:16px; }
.head-chara { float:right; width:92px; height:auto; margin:4px 0 8px 12px; }
""" + ATTR_CSS

def render_card(m):
    img = m["thumb"] or f"{SITE}/assets/kawachan_web.png"
    cmt = (m["comment"] or "")[:60]
    return (f'<a class="card" href="{m["url"]}">'
            f'<img src="{img}" loading="lazy" alt="{E(m["name"])}">'
            f'<div class="body"><div class="pref">{E(m["pref"])}</div>'
            f'<div class="name">{E(m["name"])}</div><div class="cmt">{E(cmt)}</div></div></a>')

def render_list_page(path, title, desc, lead, members, extra_body="", chara="kawachan_guide.png"):
    pins = [m for m in members if m.get("lat") and m.get("lng")]
    map_js = ""
    if pins:
        pts = ",".join(f'[{p["lat"]},{p["lng"]},"{E(p["name"]).replace(chr(34),"")}","{p["url"]}"]' for p in pins)
        map_js = f"""
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script>
const pts = [{pts}];
const map = L.map('map');
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom:18, attribution:'&copy; OpenStreetMap' }}).addTo(map);
const group = L.featureGroup(pts.map(p => L.marker([p[0],p[1]]).bindPopup('<a href="'+p[3]+'">'+p[2]+'</a>')));
group.addTo(map);
map.fitBounds(group.getBounds().pad(0.2));
</script>"""
    cards = "".join(render_card(m) for m in members)
    doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{GA_SNIPPET}
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}/{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{path}">
<meta property="og:image" content="{SITE}/assets/guide_hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/x-icon" href="{'../' if '/' in path else ''}assets/favicon.ico">
<style>{LIST_STYLE}</style>
</head>
<body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
  <img class="head-chara" src="{SITE}/assets/{chara}" alt="{AUTHOR_NAME}">
  <h1>{E(title)}</h1>
  <p class="lead">{E(lead)}</p>
  {'<div id="map"></div>' if pins else ''}
  {extra_body}
  <div class="grid">{cards}</div>
  <p class="list-note">※{INFO_ASOF}時点の情報です。{SOURCE_LINE}</p>
  <a class="back" href="{SITE}/">← MAPにもどる</a>
  {ATTR_FOOTER}
</main>
{map_js}
</body>
</html>"""
    with open(path, "w") as f:
        f.write(doc)

new_page_urls = []

# --- 生き物別まとめページ（3館以上いる生き物のみ）---
from collections import defaultdict
by_animal = defaultdict(list)
for m in entry_meta:
    for x in m["animals"]:
        by_animal[x].append(m)

animal_index_links = []
for name, members in sorted(by_animal.items(), key=lambda kv: -len(kv[1])):
    if len(members) < 3:
        continue
    fname = f"animals/{name}.html"
    icon = ANIMAL_ICONS.get(name, "🐟")
    render_list_page(
        fname,
        f"{icon} {name}に会える水族館 {len(members)}選 | 全国水族館ツアーMAP",
        f"{name}に会える水族館は日本に{len(members)}館。{AUTHOR_NAME}が実際に訪れて紹介します。",
        f"{name}に会える水族館は日本に{len(members)}館。{AUTHOR_NAME}が実際に訪れて紹介します。気になる水族館をタップすると詳しい情報が見られるよ。",
        members,
    )
    url = f"{SITE}/{urllib.parse.quote(fname)}"
    new_page_urls.append(url)
    animal_index_links.append((name, len(members), url))

# --- エリア別ページ（8地方に集約。1〜2館だけの県でも近隣とまとめて薄いページを避ける）---
REGIONS = {
    "北海道": ["北海道"],
    "東北": ["青森県","岩手県","宮城県","秋田県","山形県","福島県"],
    "関東": ["茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県"],
    "中部": ["新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県"],
    "近畿": ["三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県"],
    "中国": ["鳥取県","島根県","岡山県","広島県","山口県"],
    "四国": ["徳島県","香川県","愛媛県","高知県"],
    "九州・沖縄": ["福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"],
}
pref_to_region = {p: r for r, prefs in REGIONS.items() for p in prefs}
by_region = defaultdict(list)
for m in entry_meta:
    r = pref_to_region.get(m["pref"])
    if r:
        by_region[r].append(m)

area_index_links = []
for region, members in by_region.items():
    if not members:
        continue
    fname = f"area/{region}.html"
    render_list_page(
        fname,
        f"{region}の水族館一覧 | 全国水族館ツアーMAP",
        f"{region}エリアの水族館は{len(members)}館。{AUTHOR_NAME}が実際に訪れて紹介します。",
        f"{region}エリアの水族館は{len(members)}館。{AUTHOR_NAME}が実際に訪れて紹介します。地図で場所をチェックできるよ。",
        members,
        chara="kawachan_run.png",
    )
    url = f"{SITE}/{urllib.parse.quote(fname)}"
    new_page_urls.append(url)
    area_index_links.append((region, len(members), url))

# --- テーマ別ページ（既存タグを活用。3館以上のタグのみ）---
by_tag = defaultdict(list)
for m in entry_meta:
    for t in m["tags"]:
        by_tag[t].append(m)

theme_index_links = []
for tag, members in by_tag.items():
    if len(members) < 3 or tag not in TAG_LABEL:
        continue
    fname = f"theme/{tag}.html"
    label = TAG_LABEL[tag]
    extra = ""
    if tag == "baby":
        extra = "".join(
            f'<div class="card" style="padding:10px 14px;"><b>{E(m["name"])}</b>：'
            + " / ".join(filter(None, [
                f"🛻ベビーカー {E(m['stroller'])}" if m.get("stroller") else "",
                f"🍼授乳室 {E(m['nursing'])}" if m.get("nursing") else "",
                f"🔒ロッカー {E(m['locker'])}" if m.get("locker") else "",
            ])) + "</div>"
            for m in members if m.get("stroller") or m.get("nursing") or m.get("locker")
        )
        if extra:
            extra = f'<div style="margin:16px 0;"><h2 style="font-size:1rem;color:var(--sea-deep);margin-bottom:8px;">🍼 設備情報</h2>{extra}</div>'
    render_list_page(
        fname,
        f"{label} {len(members)}選 | 全国水族館ツアーMAP",
        f"「{label}」な水族館は{len(members)}館。{AUTHOR_NAME}が実際に訪れて紹介します。",
        f"「{label}」な水族館は{len(members)}館。{AUTHOR_NAME}が実際に訪れて紹介します。",
        members,
        extra_body=extra,
    )
    url = f"{SITE}/{urllib.parse.quote(fname)}"
    new_page_urls.append(url)
    theme_index_links.append((label, len(members), url))

# --- かわちゃん的評価ランキングページ（本人承認済み評価のみ・3館以上そろったカテゴリのみ生成）---
# 一般名詞ではなく固有の“ランキング名”を持たせ、AIに引用される際も名前ごと引用される構造にする
# かわちゃん本人が直接指定したテーマ別ベスト5（5段階評価の平均ではなく、本人の一次情報による直接キュレーション）
CURATED_RANKINGS = [
    ("🦈 サメ好きにおすすめ水族館ランキング", [
        ("アクアワールド茨城県大洗水族館", "サメの飼育種類数は約60種で日本一！日本でも屈指のサメづくしの水族館だよ。\n見たことのないサメに出会える、サメ好きなら一生に一度は行きたい聖地。"),
        ("沖縄美ら海水族館", "2階「サメ博士の部屋」では、世界的にも珍しいオオメジロザメを複数展示。\n飼育が難しい大型の危険ザメたちの生態を、研究員の解説とともにじっくり学べるよ。"),
        ("島根県立しまね海洋館アクアス", "因幡の白兎伝説が残るここでは、神話の海水槽に十数種のサメが悠々と泳ぐ。\n出雲神話ゆかりの地で、サメと兎の伝説に思いを馳せながら眺めてみて。"),
        ("海遊館", "メインの太平洋水槽には、ジンベエザメを含めて合計10種類ものサメが同居中。\nアカシュモクザメなど個性豊かな仲間たちと一緒に悠々と泳ぐ姿は必見だよ。"),
        ("四国水族館", "ここはサメの見方が面白い水族館。プラネタリウムみたいな暗い部屋で、シュモクザメを下から眺めることができるよ。\nサメのシルエットを味わえる、ユニークな展示が楽しめる。"),
    ]),
    ("🐬 パフォーマンスの迫力ランキング", [
        ("鴨川シーワールド", "シャチ3頭が大迫力で泳ぐ姿を間近で見られる、日本で唯一の水族館。\nパフォーマンスの迫力はもちろん、洞窟や海の底を旅するような館内の作りもワクワクさせてくれるよ。"),
        ("名古屋港水族館", "延床面積 日本一の広さを誇る水族館。シャチ「リン」のパワフルなパフォーマンスは必見！\n入ってすぐお出迎えしてくれる姿から、もう心をわしづかみにされちゃうよ。"),
        ("アドベンチャーワールド", "飼育頭数40頭近くのイルカやクジラたちが、音楽に合わせて息の合った大迫力のパフォーマンスを見せてくれる。\nSafariパークも一緒に楽しめる、生き物好きにはたまらない理想郷だよ。"),
        ("神戸須磨シーワールド", "西日本で唯一シャチに会える水族館。母「ステラ」と娘「ラン」の親子ならではの息の合ったパフォーマンスは必見。\n2トントラック並みの重さのシャチが跳ねるジャンプの迫力は、何度見ても胸が熱くなるよ。"),
        ("マリンワールド海の中道", "博多湾を背景にジャンプするイルカパフォーマンスのロケーションは日本屈指の美しさ。\n壁のない開放的なショープールで、海と空とイルカが一体になる瞬間を味わえるよ。"),
    ]),
    ("🐙 深海生物ランキング", [
        ("竹島水族館", "深海生物の展示種類数は日本トップクラス。会える確率が高いのはダイオウグソクムシやオオグソクムシ。\n手書き解説が面白すぎて、読むだけで深海博士になれるよ。"),
        ("新江ノ島水族館", "相模湾の深海コーナーが充実。会える確率が高いのはメンダコやダイオウグソクムシ。\nJAMSTEC（海洋研究開発機構）との連携展示で、深海調査の最前線を知ることができるよ。"),
        ("アクアマリンふくしま", "「潮目の海」の深海コーナーでは、会える確率の高いオオグソクムシやタカアシガニに出会える。\n環境水族館ならではの本格的な展示で、深海の不思議を体感できるよ。"),
        ("沼津港深海水族館", "世界唯一のシーラカンス・ミュージアム。会える確率が高いのはシーラカンスの冷凍・冷蔵標本とミズヒキガニ。\n駿河湾の深海生物を中心に、深海の不思議を間近で味わえるよ。"),
        ("沖縄美ら海水族館", "「深海への旅」エリアでは、会える確率の高いハマダイや発光するヒカリキンメダイに出会える。\n当館で繁殖に成功したノコギリザメの親子も見られる、深海研究の最前線だよ。"),
    ]),
    ("👨‍👩‍👧 親子で行くならオススメランキング", [
        ("ニフレル", "いろんな感性にふれるミュージアムだから、色や泳ぎ方をテーマに展示されていて、生き物や文字がわからなくても感覚で楽しめる。\nお隣には万博記念公園やエキスポシティもあって、家族で1日中楽しめるよ。"),
        ("大分マリーンパレス水族館 うみたまご", "ペンギンやイルカ、クジラが泳ぐ姿を間近で見られる水族館。じゃぶじゃぶ入っていける「あそびーち」がとってもオススメ。\nリニューアルでエリアが広がり、滑り台もできてさらに楽しくなったよ。"),
        ("アドベンチャーワールド", "動物たちはもちろん遊園地も併設しているから、1日中遊んで学べるエデュテインメントパーク。\n海も陸も一度に楽しめる、家族みんなが飽きない理想郷だよ。"),
        ("横浜・八景島シーパラダイス", "島まるごと海のテーマパーク。遊園地もホテルも揃っていて、イルカとキャッチボールなど様々な体験ができるのが特徴。\n1日じゃ足りないボリュームで、家族みんなで盛り上がれるよ。"),
        ("鳥羽水族館", "飼育種類数 日本一で、子どもの「これなに？」が止まらない。順路が決まっていないから、ベビーカーでも自分たちのペースで回れるよ。\nラッコやジュゴンなど人気の生き物にも会える、家族連れの定番スポットだよ。"),
    ]),
    ("💑 デートにおすすめランキング", [
        ("マクセル アクアパーク品川", "光と音のエンタメ水族館。イルカパフォーマンスは昼と夜で演出が変わるから、夜デートにぴったり。\n幻想的な空間演出で、写真映えする景色をふたりで楽しめるよ。"),
        ("アトア（átoa）", "まるで宇宙から見たプラネットのような球体水槽が幻想的。夕方以降に行けば、屋上から神戸の夜景も一望できる。\n冬は温かいココアを飲みながら、ロマンチックな時間を過ごせるよ。"),
        ("すみだ水族館", "スカイツリーのお膝元、ペンギンとの距離が近い癒しの都市型水族館。\n634匹のチンアナゴにちなんだ展示など、ふたりで話題にできるユニークなポイントも満載だよ。"),
        ("横浜・八景島シーパラダイス", "島まるごと海のテーマパーク。夕暮れ時は特にロマンチックな雰囲気に包まれるよ。\n5万尾のイワシイリュージョンなど、幻想的な演出をふたりで楽しめる。"),
        ("AOAO SAPPORO", "札幌都心のビルの中に広がる、都会のオアシスのような水族館。夜22時まで営業してるから、夜デートにもぴったり。\n館内のおしゃれな本のコーナーやパン屋さんも、ふたりの時間を彩ってくれるよ。"),
    ]),
    ("🎣 釣り好きにおすすめランキング", [
        ("アクアマリンふくしま", "「潮目の海」大水槽の目の前に、釣ってその場で食べられるエリアがある環境水族館。\nかわちゃんが「トップ5に必ず入る」と太鼓判を押す、命をいただく体験ができる場所だよ。"),
        ("横浜・八景島シーパラダイス", "「うみファーム」ではマアジ・ギンザケ・マダイが釣れて、その場で調理して味わえる。\n観る・知る・獲る・食べるまで一日で楽しめる、島まるごとの海のテーマパークだよ。"),
        ("城崎マリンワールド", "「水族館以上、であること」がコンセプト。アジ釣り体験が人気で、釣った魚をその場でアジフライバーガーなどにして味わえる。\n見るだけじゃない、五感で楽しむ水族館だよ。"),
        ("みなとやま水族館", "「FISH POND」でニジマス釣りができ、釣った魚は揚げたてフライでその場で味わえる。\n廃校をリノベーションしたユニークな水族館で、釣りから食べるまで楽しめるよ。"),
    ]),
]

by_name = {m["name"]: m for m in entry_meta}
tabs_data = []
ld_items = []
for brand, picks in CURATED_RANKINGS:
    items = []
    list_items = []
    for i, (name, note) in enumerate(picks):
        m = by_name.get(name)
        if not m:
            print("ランキング: 館が見つかりません:", name)
            continue
        items.append({
            "name": m["name"], "pref": m["pref"], "url": m["url"],
            "thumb": m["thumb"] or f"{SITE}/assets/kawachan_web.png",
            "reason": note or (m["comment"] or ""),
        })
        list_items.append({"@type": "ListItem", "position": i + 1, "url": m["url"], "name": m["name"]})
    if not items:
        continue
    tabs_data.append({"title": brand, "items": items})
    ld_items.append({"@type": "ItemList", "name": brand, "itemListElement": list_items})

ranking_generated = False
if tabs_data:
    ld_ranking = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": f"{AUTHOR_NAME}的 水族館ランキング",
        "author": {"@type": "Person", "name": AUTHOR_NAME},
        "publisher": {"@type": "Organization", "name": BRAND_NAME, "url": SITE},
        "hasPart": ld_items,
    }
    doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
{GA_SNIPPET}
<title>{AUTHOR_NAME}的 水族館ランキング | {BRAND_NAME}</title>
<meta name="description" content="{AUTHOR_NAME}が実際に訪れて選んだ、テーマ別水族館ベスト5。">
<meta property="og:type" content="website">
<meta property="og:title" content="{AUTHOR_NAME}的 水族館ランキング | {BRAND_NAME}">
<meta property="og:description" content="{AUTHOR_NAME}が実際に訪れて選んだ、テーマ別水族館ベスト5。">
<meta property="og:image" content="{SITE}/assets/kawachan_odoroki_ogp.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}/taste-ranking.html">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<script type="application/ld+json">{json.dumps(ld_ranking, ensure_ascii=False)}</script>
<style>{LIST_STYLE}
.controls {{ display:flex; gap:8px; flex-wrap:wrap; margin:14px 0 18px; }}
.controls button {{ border:2px solid var(--sea); background:#fff; color:var(--sea); border-radius:999px; padding:6px 16px; cursor:pointer; font-size:.85rem; font-family:inherit; font-weight:bold; }}
.controls button.active {{ background:var(--sea); color:#fff; }}
.rank-list {{ display:flex; flex-direction:column; gap:12px; }}
.rank-item {{ display:grid; grid-template-columns:170px 1fr; grid-template-areas:"thumb head" "thumb reason"; column-gap:14px; row-gap:4px; align-items:start; background:#fff; border-radius:16px; padding:14px 16px; box-shadow:0 3px 10px rgba(2,62,138,.1); text-decoration:none; color:#234; transition:transform .15s; border:2px solid transparent; }}
.rank-item:hover {{ transform:translateY(-3px); border-color:var(--sky); }}
.rank-item.first {{ border:2px solid var(--sun); background:linear-gradient(160deg,#fffbea 0%,#fff 55%); }}
.rank-item .r-thumb {{ grid-area:thumb; width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:10px; background:#dbeefb; }}
.rank-item .r-head {{ grid-area:head; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
.rank-item .medal {{ font-size:1.4rem; line-height:1.2; }}
.rank-item .r-name {{ font-weight:bold; color:var(--sea-deep); font-size:1rem; }}
.rank-item .r-pref {{ font-size:.72rem; color:#fff; background:var(--sea); border-radius:999px; padding:1px 9px; white-space:nowrap; }}
.rank-item .r-reason {{ grid-area:reason; font-size:.84rem; color:#456; line-height:1.65; white-space:pre-line; }}
@media (max-width:560px) {{ .rank-item {{ grid-template-columns:1fr; grid-template-areas:"head" "thumb" "reason"; }} }}
</style></head><body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main><img class="head-chara" src="{SITE}/assets/kawachan_odoroki.png" alt="{AUTHOR_NAME}">
<h1>🐟 {AUTHOR_NAME}的 水族館ランキング</h1>
<p class="lead">{AUTHOR_NAME}が実際に訪れた水族館の中から、テーマ別に選んだベスト5だよ。</p>
<div class="controls" id="rankBtns"></div>
<div class="rank-list" id="rankList"></div>
<p class="list-note">※{INFO_ASOF}時点の情報です。{SOURCE_LINE}</p>
<a class="back" href="{SITE}/">← MAPにもどる</a>
{ATTR_FOOTER}
<script>
const RANKS = {json.dumps(tabs_data, ensure_ascii=False)};
const btnWrap = document.getElementById('rankBtns');
const list = document.getElementById('rankList');
const MEDALS = ['🥇','🥈','🥉','4️⃣','5️⃣'];
function esc(s){{ const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }}
function show(i){{
  document.querySelectorAll('#rankBtns button').forEach((b,j)=>b.classList.toggle('active', j===i));
  list.innerHTML = RANKS[i].items.map((it,idx)=>`
    <a class="rank-item${{idx===0?' first':''}}" href="${{it.url}}">
      <img class="r-thumb" loading="lazy" src="${{it.thumb}}" alt="${{esc(it.name)}}">
      <span class="r-head">
        <span class="medal">${{MEDALS[idx]||''}}</span>
        <span class="r-name">${{esc(it.name)}}</span><span class="r-pref">${{esc(it.pref)}}</span>
      </span>
      <div class="r-reason">${{esc(it.reason)}}</div>
    </a>`).join('');
}}
RANKS.forEach((r,i)=>{{
  const b = document.createElement('button');
  b.textContent = r.title;
  b.onclick = ()=>show(i);
  btnWrap.appendChild(b);
}});
if(RANKS.length) show(0);
</script>
</main></body></html>"""
    with open("taste-ranking.html", "w") as f:
        f.write(doc)
    new_page_urls.append(f"{SITE}/taste-ranking.html")
    ranking_generated = True

# --- このサイトについて（運営者情報・お仕事のご依頼・プライバシーポリシー込み）---
about_person_ld = json.dumps({
    "@context": "https://schema.org", "@type": "Person", "name": "かわちゃん",
    "alternateName": "さかなのおにいさん かわちゃん",
    "description": "「子どもがさかなを好きになれば海は豊かになる」をモットーに、YouTubeで全国の水族館を紹介するさかなのおにいさん。テレビ東京「シナぷしゅ」出演、著書「全国クセすご水族館図鑑」。",
    "url": "https://sakana-bro.com/", "image": f"{SITE}/assets/kawachan_web_ogp.png",
    "sameAs": ["https://sakana-bro.com/", "https://www.youtube.com/channel/UCNpTW5hGX4mKr3hxFu_nReA",
               "https://www.instagram.com/kawayanfishing/", "https://twitter.com/sakana_bro"],
    "worksFor": {"@type": "Organization", "name": "株式会社やさしいうみ", "url": "https://sakana-bro.com/"}
}, ensure_ascii=False)
about_doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
{GA_SNIPPET}
<title>このサイトについて・運営者情報 | 全国水族館ツアーMAP</title>
<meta name="description" content="会いに行こう！全国水族館ツアーMAPの紹介と運営者情報。さかなのおにいさんかわちゃんが実際に訪れた水族館を紹介する、実訪問ベースの水族館サイトです。出演・タイアップのご依頼窓口もこちら。">
<link rel="canonical" href="{SITE}/about.html">
<meta property="og:type" content="website">
<meta property="og:title" content="このサイトについて・運営者情報 | 全国水族館ツアーMAP">
<meta property="og:description" content="会いに行こう！全国水族館ツアーMAPの紹介と運営者情報。さかなのおにいさんかわちゃんが実際に訪れた水族館を紹介する、実訪問ベースの水族館サイトです。">
<meta property="og:image" content="{SITE}/assets/kawachan_web_ogp.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{about_person_ld}</script>
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<style>{LIST_STYLE}
.about-box {{ background:#fff; border-radius:16px; padding:18px 20px; margin:14px 0; line-height:1.8; font-size:.92rem; }}
.about-box h2 {{ font-size:1rem; color:var(--sea-deep); margin:16px 0 6px; }}
.about-box h2:first-child {{ margin-top:0; }}
.about-box table {{ border-collapse:collapse; width:100%; margin:6px 0; }}
.about-box th {{ text-align:left; white-space:nowrap; color:var(--sea-deep); font-size:.85rem; padding:6px 14px 6px 0; vertical-align:top; }}
.about-box td {{ font-size:.88rem; padding:6px 0; }}
.about-box .mail {{ font-weight:bold; color:var(--sea); text-decoration:none; }}
.work-cta {{ display:inline-block; background:var(--sea); color:#fff; font-weight:bold; text-decoration:none; border-radius:999px; padding:10px 22px; margin-top:8px; }}
</style></head><body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
<h1>このサイトについて</h1>
<div class="about-box" id="profile">
<h2>🐟 さかなのおにいさん かわちゃんとは</h2>
<p>「子どもがさかなを好きになれば海は豊かになる」をモットーに活動する、さかなのおにいさん かわちゃん。YouTubeで全国の水族館を紹介しながら、生き物の魅力を伝えています。テレビ東京「シナぷしゅ」出演、著書「全国クセすご水族館図鑑」ほか、歌・イラスト・クイズで魚の魅力を伝えるイベントを全国で開催しています。</p>
<p style="margin-top:10px;font-size:.88rem;color:#567;">水族館巡りがもっと楽しくなる本やグッズも、よかったらのぞいてみてね。<a href="https://sakana-bro.com/goods/" target="_blank" rel="noopener" style="color:var(--sea);font-weight:bold;">かわちゃんの本・グッズ一覧 →</a></p>
<h2>🗺 このサイトの特徴</h2>
<p>このサイトに載っている情報は、かわちゃんが実際に訪れた水族館の紹介動画をベースにした「実訪問プロジェクト」です。行ったことのある水族館には、かわちゃん本人が確認した一言コメントや独自評価を掲載しています。</p>
<h2>📖 掲載基準</h2>
<p>日本全国の水族館をできるだけ幅広く掲載し、かわちゃんが実際に訪れた館から順番に「紹介済み」として動画・一言コメントを追加しています。「この水族館も載せてほしい！」というリクエストは、トップページの📮コメントやSNSで教えてもらえるとうれしいです。</p>
<h2>📋 情報収集ポリシー</h2>
<p>料金・休館日・設備などの事実情報は、各水族館の公式サイトを調査して掲載しています。誤りに気づいた場合は、各施設の公式サイトを優先してご確認ください。かわちゃん本人の一言・評価は、本人が内容を確認したものだけを公開しています。</p>
<h2 id="facility">🏛 掲載水族館・施設の方へ</h2>
<p>掲載内容の修正（料金改定・休館情報など）や掲載に関するご要望は、下記のメールボタンからお気軽にご連絡ください。確認のうえ、すみやかに対応いたします。このサイトは全国の水族館を応援する目的で運営しています。</p>
<p style="margin-top:10px;"><a href="mailto:info@yasasea.com?subject=%E3%80%90%E6%B0%B4%E6%97%8F%E9%A4%A8MAP%E3%82%B5%E3%82%A4%E3%83%88%E3%80%91%E6%8E%B2%E8%BC%89%E6%83%85%E5%A0%B1%E3%81%AE%E4%BF%AE%E6%AD%A3%E3%83%BB%E3%81%94%E8%A6%81%E6%9C%9B&amp;body=%E6%B0%B4%E6%97%8F%E9%A4%A8%E5%90%8D%EF%BC%9A%0A%E8%A9%B2%E5%BD%93%E3%83%9A%E3%83%BC%E3%82%B8URL%EF%BC%9A%0A%E4%BF%AE%E6%AD%A3%E3%83%BB%E3%81%94%E8%A6%81%E6%9C%9B%E3%81%AE%E5%86%85%E5%AE%B9%EF%BC%9A%0A" style="display:inline-block;background:var(--sea);color:#fff;font-weight:bold;text-decoration:none;border-radius:999px;padding:10px 22px;">✉️ 掲載修正・ご要望を送る</a></p>
<p style="font-size:.78rem;color:#89a;">※イベント出演などお仕事のご依頼は、下の「お仕事のご依頼」のフォームからお願いします</p>
</div>

<div class="about-box" id="work">
<h2>💼 お仕事のご依頼</h2>
<p>イベント出演・トークショー・タイアップ・取材・監修などのご依頼を受け付けています。水族館・商業施設・自治体・企業さまとのお仕事の実績多数。お問い合わせフォームからお気軽にご相談ください。</p>
<table>
<tr><th>💬 お問い合わせ</th><td><a class="mail" href="https://sakana-bro.com/contact/" target="_blank" rel="noopener">お問い合わせフォーム</a></td></tr>
<tr><th>🌊 プロフィール・実績</th><td><a href="https://sakana-bro.com/" target="_blank" rel="noopener">公式サイト（sakana-bro.com）</a></td></tr>
</table>
</div>

<div class="about-box" id="company">
<h2>🏢 運営者情報</h2>
<table>
<tr><th>運営</th><td>株式会社やさしいうみ</td></tr>
<tr><th>理念</th><td>子どもにも海にも やさしい未来を</td></tr>
<tr><th>連絡先</th><td><a class="mail" href="mailto:info@yasasea.com?subject=%E3%80%90%E6%B0%B4%E6%97%8F%E9%A4%A8MAP%E3%82%B5%E3%82%A4%E3%83%88%E3%80%91%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B">info@yasasea.com（サイトに関するお問い合わせ）</a></td></tr>
<tr><th>公式サイト</th><td><a href="https://sakana-bro.com/" target="_blank" rel="noopener">https://sakana-bro.com/</a></td></tr>
</table>
</div>

<div class="about-box" id="privacy">
<h2>🔒 プライバシーポリシー</h2>
<p><b>アクセス解析：</b>当サイトはGoogle アナリティクス（GA4）を利用しています。データは匿名で収集され、個人を特定するものではありません。Cookieの利用はブラウザ設定で無効にできます。</p>
<p><b>コメント機能：</b>コメント投稿はニックネームのみで利用でき、メールアドレス等の個人情報は収集していません。不適切な投稿は運営の判断で非表示・削除する場合があります。</p>
<p><b>「行った！」チェック：</b>訪問チェックの記録はお使いのブラウザ内（localStorage）にのみ保存され、運営者には送信されません。</p>
<p><b>外部サービス：</b>YouTube（動画埋め込み・コメント表示）、OpenStreetMap（地図表示）を利用しています。各サービスのプライバシーポリシーもあわせてご確認ください。</p>
</div>

<a class="back" href="{SITE}/">← MAPにもどる</a>
{ATTR_FOOTER}
</main></body></html>"""
with open("about.html", "w") as f:
    f.write(about_doc)
new_page_urls.append(f"{SITE}/about.html")

# --- かわちゃん流・水族館の楽しみ方（検索の裏の入り口。導線はフッターとspotページのみ）---
ld_guide = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": f"{AUTHOR_NAME}流・水族館の楽しみ方",
    "description": "行く前の準備から、大水槽の見方、イルカショー・パフォーマンスの楽しみ方、子連れの回り方、おみやげの選び方まで。全国の水族館を実際にまわってきたかわちゃんの楽しみ方ガイド。",
    "author": {"@type": "Person", "name": AUTHOR_NAME},
    "publisher": {"@type": "Organization", "name": BRAND_NAME, "url": SITE},
    "url": f"{SITE}/guide.html",
}
guide_doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
{GA_SNIPPET}
<title>かわちゃん流・水族館の楽しみ方｜行く前の準備からおみやげまで | {BRAND_NAME}</title>
<meta name="description" content="水族館はコツを知ると100倍楽しい！行く前の準備・大水槽の見方・イルカショー（パフォーマンス）の楽しみ方・子連れの回り方・おみやげの選び方を、{AUTHOR_NAME}が実訪問の経験からまとめました。">
<link rel="canonical" href="{SITE}/guide.html">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<meta property="og:title" content="かわちゃん流・水族館の楽しみ方 | {BRAND_NAME}">
<meta property="og:description" content="行く前の準備からイルカショーの楽しみ方、おみやげ選びまで、水族館が100倍楽しくなるコツを{AUTHOR_NAME}がまとめたよ！">
<meta property="og:image" content="{SITE}/assets/guide_hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld_guide, ensure_ascii=False)}</script>
<style>{LIST_STYLE}
.g-box {{ background:#fff; border-radius:16px; padding:18px 20px; margin:14px 0; line-height:1.8; font-size:.92rem; }}
.g-box h2 {{ font-size:1.05rem; color:var(--sea-deep); margin:0 0 8px; }}
.g-box ul {{ margin:0 0 0 20px; display:flex; flex-direction:column; gap:8px; }}
.g-box li {{ line-height:1.7; }}
.g-box a {{ color:var(--sea); font-weight:bold; }}
.guide-hero {{ display:block; width:100%; border-radius:16px; margin:12px 0 4px; }}
.g-box .gphoto {{ display:block; width:100%; border-radius:12px; margin:4px 0 12px; }}
</style></head><body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
<h1>🐬 かわちゃん流・水族館の楽しみ方</h1>
<p class="lead">水族館は、予習ゼロでも楽しい。でもちょっとしたコツを知ってると100倍楽しくなる場所！全国の水族館を実際にまわってきた{AUTHOR_NAME}が、行く前からおみやげまでの楽しみ方をまとめたよ🐟</p>
<img class="guide-hero" src="{SITE}/assets/guide_hero.jpg" alt="シャチに手を振る{AUTHOR_NAME}">

<div class="g-box">
<h2>🎒 1. 行く前の準備</h2>
<img class="gphoto" src="{SITE}/assets/guide_prep.jpg" alt="ベルーガと対面する{AUTHOR_NAME}" loading="lazy">
<ul>
<li>水槽の写真を撮る人は、暗めの服を着るのがポイント。白い服だとガラスに反射して自分が写り込んじゃうよ</li>
<li>行く前の週に公式SNSをチラ見しておくと得。「産卵しました」「あかちゃん誕生」みたいな最新ネタが載ってるよ</li>
<li>「今日は◯◯に会いに行く」って決めていこう。水族館が「見る場所」から「会いに行く場所」に変わるよ</li>
<li>料金・休館日・ベビーカー貸し出し・ロッカー・お弁当持ち込みの可否は<a href="{SITE}/">このサイトの各水族館ページ</a>にまとめてあるから、おでかけ前にチェックしておくと当日バタバタしないよ</li>
<li>年に2〜3回行く予定があるなら年間パスポートも要チェック。だいたい2回分の料金で1年間通い放題になる館が多くて、リピート前提ならこっちの方がお得やで</li>
</ul>
</div>

<div class="g-box">
<h2>🚪 2. 入ってすぐやること</h2>
<img class="gphoto" src="{SITE}/assets/guide_enter.jpg" alt="トンネル水槽で両手を広げる{AUTHOR_NAME}" loading="lazy">
<ul>
<li>まず館内マップをもらって、お目当ての生き物の場所とパフォーマンスの時間をチェック。そこを中心に1日のスケジュールを考えよう</li>
<li>海獣やイルカたちは、開館直後がいちばん人に興味を持って近づいてきてくれる可能性が高いよ。元気いっぱいの姿に会えるチャンス</li>
<li>順路は自由な水族館も多いよ。混んでたら空いてる水槽から回ってOK！</li>
</ul>
</div>

<div class="g-box">
<h2>🐠 3. 水槽のたのしみかた</h2>
<img class="gphoto" src="{SITE}/assets/guide_tank.jpg" alt="サンゴ礁の大水槽をながめる{AUTHOR_NAME}" loading="lazy">
<ul>
<li>かわちゃん流はズバリ「<b>ツッコミながら見る</b>」こと。ツッコミポイントは、実はその生き物の生態にちゃんと理由があることが多い。「しゃくれてるんかーい！」ってツッコミたくなるカサゴは、上から落ちてくるエサをキャッチしやすいように口が受け口になってたり。自分から能動的に楽しむと100倍楽しく学べるよ！</li>
<li>水族館の隠されたストーリーを見つけてみよう。例えば水槽の中にウツボ・タコ・伊勢海老が同居してることがあるよ。ウツボはタコを食べたくて、タコは伊勢海老を食べたくて、伊勢海老は食べられたくないからウツボの近くに隠れてる…なんていう三角関係のドロドロ生存ドラマがあるんよ。かわちゃんねるのYouTubeでも紹介してるから見てみてね</li>
<li>時には水の音やゆらめきをただ感じるだけでもOK。眺めてるだけで癒される、それも水族館の楽しみ方だよ</li>
</ul>
</div>

<div class="g-box">
<h2>🐬 4. パフォーマンス・ライブの楽しみ方</h2>
<img class="gphoto" src="{SITE}/assets/guide_perf.jpg" alt="2頭のシャチに手を振る{AUTHOR_NAME}" loading="lazy">
<ul>
<li>前の席は水しぶきゾーン！濡れるのも思い出だけど、タオルやポンチョがあると安心。</li>
<li>夏と冬でシャチやイルカが水をかける量をトレーナーさんが調整してる！寒い冬は濡れずに近い距離で見られておすすめだよ</li>
<li>決まったパフォーマンスの時間じゃなくても、イルカたちが元気に飛び跳ねてる姿が見られる水族館もあるよ。近くの売店でドリンクを買って、ゆったり佇んで眺めるのもいいね</li>
<li>一見ショーみたいに見える動きも、実はトレーニングの一環。毎日同じ動作ができるか、怪我はないかを確認したり、体に触れさせてもらって体調管理をするための「ハズバンダリートレーニング」っていうもの。トレーナーさんとの信頼関係は生き物の健康にとっても大事なんだ！</li>
</ul>
</div>

<div class="g-box">
<h2>👶 5. 子ども連れの回り方</h2>
<img class="gphoto" src="{SITE}/assets/guide_kids.jpg" alt="赤ちゃんと一緒にイルカを見つめる{AUTHOR_NAME}" loading="lazy">
<ul>
<li>ぜんぶ見ようとしなくてOK。子どもが好きになった水槽の前で、角度を変えて見てみたり、ゆっくり過ごすのがいちばん</li>
<li>「この魚は何色かなぁ」「首を振って泳いでるね」って、親子で会話しながら見てみて。それが子どもの自然への入り口になるよ</li>
<li>お昼どきに一度外に出ても、再入館できる水族館は多い！お弁当持ち込みOKな館もたくさんあるから、無理なく過ごせるよ</li>
<li>ベビーカー・授乳室・ロッカーの情報は、各水族館ページの「くわしく」にまとめてあるよ</li>
<li>平日の水族館は、子育ての楽しい避難場所にもなる。保護者のみなさんもぜひ息抜きに行ってみてね！このサイトが参考になったら嬉しいな</li>
<li>行き先選びはテーマ別ページからどうぞ：<a href="{SITE}/theme/baby.html">🍼 赤ちゃん連れにおすすめ</a>／<a href="{SITE}/theme/kids.html">👶 未就学児におすすめ</a>／<a href="{SITE}/theme/rain.html">☔️ 雨の日におすすめ</a></li>
</ul>
</div>

<div class="g-box">
<h2>🎁 6. おみやげの選び方</h2>
<img class="gphoto" src="{SITE}/assets/guide_gift.jpg" alt="ジンベエザメを指差す{AUTHOR_NAME}" loading="lazy">
<ul>
<li>かわちゃん流は「その水族館オリジナル」のグッズを選ぶこと。細部までこだわりが詰まってて、おうちに帰ってからも「あの子に会ったね」って親子の会話になるよ</li>
<li>人気のぬいぐるみくじや限定グッズは、土日午後には売り切れてることも多い。狙ってるものがあるなら、見学前にショップへ先に立ち寄っておくのが確実やで</li>
<li>「飼育員監修」の表記があるグッズは要チェック。実際の生き物の特徴（エラの形とか体のバランスとか）まで再現してることが多くて、こだわりの深さが違うよ</li>
<li>各水族館ページの🎁おみやげ欄もチェックしてね。超グソクムシ煎餅みたいな、クセすごおみやげに出会えることもあるよ</li>
</ul>
</div>

<div class="g-box">
<h2>🎟 水族館好きならではの小ワザ集</h2>
<ul>
<li>実は一年でいちばんのおすすめは、12〜2月の寒い時期。冷たい水のイメージからか、お客さんが少なくて落ち着いて楽しめるよ。日によっては貸切みたいな贅沢な時間になることも！</li>
<li>雨予報の日も狙い目…なんやけど、小学校の雨天時の遠足予備日として、逆に混雑することもあるから一長一短。天気予報とセットで、その日の予定もなんとなく想像してみてね</li>
<li>おすすめの時間帯は「朝一」と「閉館前の1時間」。朝一は生き物のほうから興味をもって近づいてきてくれることが多く、閉館前の1時間は遠足の子どもたちもいなくなって、ゆったり過ごせるよ。飼育員さんも夕方の見回りで水槽まわりに来ることが多いから、話しかけるチャンス。ただし飼育員さんもお仕事中だから、お邪魔にならない範囲でね</li>
<li>あえてパフォーマンスやプログラムの時間を狙うのもかわちゃん流。お客さんが減るから、大水槽をゆっくり眺めたり写真を撮ったりするのにぴったりのタイミングだよ</li>
<li>複数のパフォーマンスがある館では、1回目より2回目・3回目の回のほうが空いてることが多い。1回目は開館直後組とかぶりやすいからね</li>
<li>飼育員さんと似た色の服を着ていくと、生き物によっては興味を持って寄ってきてくれることもあるよ</li>
<li>迷惑がかからない範囲で、自分なりの水族館の楽しみ方を見つけてみてね</li>
</ul>
</div>

<div class="g-box">
<h2>🌊 さいごに</h2>
<img class="gphoto" src="{SITE}/assets/guide_last.jpg" alt="ジュゴンを撮影する{AUTHOR_NAME}チーム" loading="lazy">
<p>水族館は自然への入り口。地元の自然や、気軽には行けない深海や海外の川なども体験させてくれる場所。だからこそ、次は実際の自然へも繰り出してほしいな。<br>そして水族館は展示だけじゃなく、繁殖や研究、保護や保全にも力を入れています。遊びに行くことが、その応援になるんだ。次の週末、どこの水族館に行く？</p>
<p style="margin-top:8px"><a href="{SITE}/">→ MAPで行きたい水族館を探す</a></p>
</div>

<p class="list-note">📷 写真は水族館の特別な許可を得て撮影しています ※{SOURCE_LINE}</p>
<a class="back" href="{SITE}/">← MAPにもどる</a>
{ATTR_FOOTER}
</main></body></html>"""
with open("guide.html", "w") as f:
    f.write(guide_doc)
new_page_urls.append(f"{SITE}/guide.html")

# --- 掲載水族館一覧（画像なしの軽量テキストページ。ファン要望）---
_list_sections = []
for _region, _prefs in REGIONS.items():
    _members = [m for m in entry_meta if m["pref"] in _prefs]
    if not _members:
        continue
    _lis = "".join(f'<li><a href="{m["url"]}">{E(m["name"])}</a> <small>（{E(m["pref"])}）</small></li>' for m in _members)
    _list_sections.append(f'<h2>{_region}（{len(_members)}館）</h2><ul class="alist">{_lis}</ul>')
list_doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
{GA_SNIPPET}
<title>掲載水族館一覧（全{len(entry_meta)}館） | {BRAND_NAME}</title>
<meta name="description" content="{BRAND_NAME}に掲載中の全{len(entry_meta)}館をエリア別に一覧で。各館の料金・休館日・{AUTHOR_NAME}の一言は個別ページでどうぞ。">
<link rel="canonical" href="{SITE}/aquarium-list.html">
<meta property="og:type" content="website">
<meta property="og:title" content="掲載水族館一覧（全{len(entry_meta)}館） | {BRAND_NAME}">
<meta property="og:description" content="{BRAND_NAME}に掲載中の全{len(entry_meta)}館をエリア別に一覧で。">
<meta property="og:image" content="{SITE}/assets/kawachan_guide_ogp.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<style>{LIST_STYLE}
.alist {{ list-style:none; margin:0 0 18px; padding:0; display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:6px; }}
.alist a {{ color:var(--sea-deep); font-weight:bold; text-decoration:none; }}
.alist a:hover {{ color:var(--sea); }}
.alist small {{ color:#89a; }}
main h2 {{ color:var(--sea-deep); font-size:1.05rem; margin:20px 0 8px; }}
</style></head><body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
<img class="head-chara" src="{SITE}/assets/kawachan_guide.png" alt="{AUTHOR_NAME}">
<h1>📖 掲載水族館一覧（全{len(entry_meta)}館）</h1>
<p class="lead">{BRAND_NAME}に載っている水族館をぜんぶまとめた一覧だよ。名前をタップすると、料金・休館日・{AUTHOR_NAME}の一言が見られる個別ページへ飛べるよ🐟</p>
{''.join(_list_sections)}
<p class="list-note">※{INFO_ASOF}時点の情報です。{SOURCE_LINE}</p>
<a class="back" href="{SITE}/">← MAPにもどる</a>
{ATTR_FOOTER}
</main></body></html>"""
with open("aquarium-list.html", "w") as f:
    f.write(list_doc)
new_page_urls.append(f"{SITE}/aquarium-list.html")

# --- すいぞくかんパスポート（スタンプ帳＋メダル。index.htmlの「行った！」チェック(localStorage myVisits)と連動）---
# スタンプ・メダルの絵柄は assets/stamps/{slug}.png / assets/medals/{id}.png を置いてbuildし直すと
# CSS判子からかわちゃんイラストに自動で切り替わる
STAMP_EMOJI = dict(ANIMAL_ICONS)
STAMP_EMOJI.update({
    "イルカ": "🐬", "バンドウイルカ": "🐬", "マダライルカ": "🐬", "シロイルカ": "🐳",
    "クジラ": "🐋", "シロナガスクジラ": "🐋", "ザトウクジラ": "🐋",
    "ペンギン": "🐧", "キングペンギン": "🐧", "ケープペンギン": "🐧", "フンボルトペンギン": "🐧",
    "マゼランペンギン": "🐧", "キタイワトビペンギン": "🐧",
    "ウミガメ": "🐢", "アオウミガメ": "🐢", "タイマイ": "🐢",
    "アザラシ": "🦭", "ゴマフアザラシ": "🦭", "バイカルアザラシ": "🦭",
    "トド": "🦭", "セイウチ": "🦭", "アシカ": "🦭", "カリフォルニアアシカ": "🦭",
    "カワウソ": "🦦", "コツメカワウソ": "🦦", "ユーラシアカワウソ": "🦦",
    "フグ": "🐡", "マンボウ": "🐡", "金魚": "🐠", "クマノミ": "🐠", "カクレクマノミ": "🐠",
    "サンゴ": "🪸", "カニ": "🦀", "タカアシガニ": "🦀", "イセエビ": "🦞",
    "イカ": "🦑", "ホタルイカ": "🦑", "ホッキョクグマ": "🐻‍❄️", "ミニカバ": "🦛",
    "ホワイトタイガー": "🐯", "カピバラ": "🦫", "マイクロブタ": "🐷",
})
def _stamp_emoji(m):
    for x in m["animals"]:
        if x in STAMP_EMOJI:
            return STAMP_EMOJI[x]
    for t, e in (("deep", "🐙"), ("penguin", "🐧"), ("dolphin", "🐬"), ("same", "🦈")):
        if t in m["tags"]:
            return e
    return "🐟"

stamps_data = []
for m in entry_meta:
    st = {"n": m["name"], "p": m["pref"], "r": pref_to_region.get(m["pref"], "その他"),
          "u": m["url"], "e": _stamp_emoji(m)}
    simg = f"assets/stamps/{m['slug']}.png"
    if os.path.exists(simg):
        st["img"] = simg
    stamps_data.append(st)

def _members_animal(*names):
    return [m["name"] for m in entry_meta if any(x in m["animals"] for x in names)]
def _members_tag(tag):
    return [m["name"] for m in entry_meta if tag in m["tags"]]

_total = len(entry_meta)
REGION_ID = {"北海道": "hokkaido", "東北": "tohoku", "関東": "kanto", "中部": "chubu",
             "近畿": "kinki", "中国": "chugoku", "四国": "shikoku", "九州・沖縄": "kyushu"}
medals_data = []
for mid, icon, name, desc, target in [
    ("m1", "🐟", "はじめの一歩", "はじめてのスタンプをゲット！", 1),
    ("m10", "🐠", "10館たんけん隊", "10館スタンプを集めた！", 10),
    ("m30", "🐬", "30館マスター", "30館スタンプを集めた！", 30),
    ("m50", "🦈", "50館つわもの", "50館スタンプを集めた！", 50),
    ("m100", "🐋", "100館レジェンド", "100館スタンプを集めた！すごすぎる！", 100),
    ("mall", "👑", f"全{_total}館 完全制覇", "日本中の水族館をぜんぶ回った伝説の人！", _total),
]:
    medals_data.append({"id": mid, "icon": icon, "name": name, "desc": desc, "target": target})
for mid, icon, name, desc, members in [
    ("shachi", "🐋", "シャチマスター", "シャチに会える水族館をぜんぶ制覇！", _members_animal("シャチ")),
    ("jinbei", "🦈", "ジンベエマスター", "ジンベエザメに会える水族館をぜんぶ制覇！", _members_animal("ジンベエザメ")),
    ("rakko", "🦦", "ラッコメダル", "日本でラッコに会えるのは鳥羽水族館だけ！", _members_animal("ラッコ")),
    ("kurage", "🪼", "クラゲマスター", "クラゲにうっとりできる水族館をぜんぶ制覇！", _members_animal("クラゲ")),
    ("shinkai", "🐙", "深海マスター", "深海生物じまんの水族館をぜんぶ制覇！", _members_tag("deep")),
    ("penguin", "🐧", "ペンギンマスター", "ペンギン好きにおすすめの水族館をぜんぶ制覇！", _members_tag("penguin")),
    ("kaichu", "🗼", "海中展望台マスター", "服のまま海の中をのぞける全国の海中展望台をぜんぶ制覇！", _members_tag("kaichu")),
]:
    if members:
        medals_data.append({"id": mid, "icon": icon, "name": name, "desc": desc, "members": members})
for region in REGIONS:
    members = [m["name"] for m in entry_meta if pref_to_region.get(m["pref"]) == region]
    if members:
        medals_data.append({"id": f"area_{REGION_ID[region]}", "icon": "🗾", "name": f"{region}マスター",
                            "desc": f"{region}エリアの水族館をぜんぶ制覇！", "members": members})

# ラッコメダルは「思い出」対応：今は鳥羽だけだが、かつてラッコに会えた館を訪れたファンも記録できる
# （最盛期1994年は全国28施設・122頭。今は鳥羽水族館の2頭のみ）
rakko_past_members = [m["name"] for m in entry_meta if m.get("rakko_past")]
for md in medals_data:
    if md["id"] == "rakko":
        md["desc"] = "今ラッコに会えるのは鳥羽水族館だけ。でも、かつてラッコに会えた水族館の思い出も集めよう🦦"
        md["past"] = rakko_past_members
for md in medals_data:
    mimg = f"assets/medals/{md['id']}.png"
    if os.path.exists(mimg):
        md["img"] = mimg

PASSPORT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
__GA__
<title>すいぞくかんパスポート | __BRAND__</title>
<meta name="description" content="行った水族館のスタンプを集めて、メダルをゲットしよう！__AUTHOR__と一緒に目指せ全国制覇🐟">
<link rel="canonical" href="__SITE__/passport.html">
<meta property="og:type" content="website">
<meta property="og:title" content="すいぞくかんパスポート | __BRAND__">
<meta property="og:description" content="行った水族館のスタンプを集めて、メダルをゲットしよう！">
<meta property="og:url" content="__SITE__/passport.html">
<meta property="og:image" content="__SITE__/assets/kawachan_web_ogp.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<style>
:root { --sea:#0096c7; --sea-deep:#023e8a; --sky:#caf0f8; --sand:#fff9ec; --coral:#ff6b6b; --sun:#ffd166; }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:"Hiragino Maru Gothic ProN","Rounded Mplus 1c",sans-serif; background:var(--sand); color:#234; }
header { background:linear-gradient(180deg,#48cae4,#0096c7); color:#fff; padding:14px 16px; }
header a { color:#fff; text-decoration:none; font-weight:bold; font-size:.9rem; }
main { max-width:900px; margin:0 auto; padding:20px 16px 40px; }
.cover { background:linear-gradient(160deg,#023e8a,#0077b6); color:#fff; border-radius:20px; padding:26px 20px 22px; text-align:center; box-shadow:0 6px 18px rgba(2,62,138,.3); position:relative; overflow:hidden; }
.cover::before { content:"🐟"; position:absolute; font-size:7rem; opacity:.08; right:-14px; bottom:-24px; transform:rotate(-12deg); }
.cover .sub { font-size:.72rem; letter-spacing:.28em; color:var(--sun); font-weight:bold; }
.cover h1 { font-size:1.35rem; margin:6px 0 2px; }
.cover .owner { font-size:.85rem; opacity:.92; cursor:pointer; }
.cover .owner .pen { font-size:.75rem; opacity:.75; }
.cover .big { font-size:2.6rem; font-weight:bold; color:var(--sun); text-shadow:0 2px 4px rgba(0,0,0,.3); margin-top:10px; line-height:1; }
.cover .big small { font-size:1rem; color:#fff; font-weight:normal; }
.pbar { background:rgba(255,255,255,.25); border-radius:999px; height:10px; margin:12px auto 6px; max-width:340px; overflow:hidden; }
.pbar div { background:var(--sun); height:100%; border-radius:999px; width:0%; transition:width .8s ease; }
.cover .note { font-size:.7rem; opacity:.75; margin-top:8px; }
h2 { color:var(--sea-deep); font-size:1.1rem; margin:26px 0 4px; }
.sec-note { font-size:.76rem; color:#789; margin-bottom:12px; }
.medals { display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:12px; }
.medal { background:#fff; border-radius:16px; padding:10px 6px 8px; text-align:center; cursor:pointer; box-shadow:0 2px 8px rgba(2,62,138,.08); border:2px solid transparent; transition:transform .12s; }
.medal:hover { transform:translateY(-3px); }
.medal .disc { width:58px; height:58px; border-radius:50%; margin:0 auto 6px; display:flex; align-items:center; justify-content:center; font-size:1.7rem; background:#eef2f5; filter:grayscale(1); opacity:.55; }
.medal img.disc { object-fit:cover; padding:0; }
.medal.earned { border-color:var(--sun); }
.medal.earned .disc { background:radial-gradient(circle at 32% 30%,#ffe9a8,#ffd166 60%,#e2a93b); filter:none; opacity:1; box-shadow:0 2px 6px rgba(226,169,59,.5); }
.medal .mn { font-size:.66rem; font-weight:bold; color:var(--sea-deep); line-height:1.25; }
.medal .mp { font-size:.6rem; color:#89a; margin-top:2px; }
.medal.earned .mp { color:#c98f1b; }
.region-h { display:flex; align-items:baseline; gap:8px; margin:22px 0 10px; }
.region-h h3 { color:var(--sea-deep); font-size:.98rem; }
.region-h .rc { font-size:.74rem; color:#789; font-weight:bold; }
.stamps { display:grid; grid-template-columns:repeat(auto-fill,minmax(88px,1fr)); gap:10px; }
.stamp { aspect-ratio:1; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; cursor:pointer; padding:6px; transition:transform .12s; }
.stamp:hover { transform:scale(1.06); }
.stamp .e { font-size:1.45rem; line-height:1.1; }
.stamp .n { font-size:.55rem; font-weight:bold; line-height:1.25; overflow:hidden; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; }
.stamp.off { border:2px dashed #c3d3dd; color:#a9bcc8; background:rgba(255,255,255,.55); }
.stamp.on { border:3px double var(--sc,#0096c7); color:var(--sc,#0096c7); background:#fff; transform:rotate(var(--rot,0deg)); box-shadow:0 2px 6px rgba(2,62,138,.14); }
.stamp.on:hover { transform:rotate(var(--rot,0deg)) scale(1.06); }
.stamp.on.hasimg { border:none; padding:0; background:none; box-shadow:none; }
.stamp.on img { width:100%; height:100%; object-fit:contain; }
.pmodal { position:fixed; inset:0; background:rgba(2,30,60,.55); display:none; align-items:center; justify-content:center; z-index:50; padding:16px; }
.pmodal.open { display:flex; }
.pmodal .box { background:#fff; border-radius:20px; padding:22px 20px 18px; width:min(92vw,400px); max-height:82vh; overflow-y:auto; text-align:center; }
.pmodal .bige { font-size:3rem; }
.pmodal img.bigimg { width:120px; height:120px; object-fit:contain; }
.pmodal h3 { color:var(--sea-deep); font-size:1.1rem; margin:6px 0 2px; }
.pmodal .pref { font-size:.72rem; color:#fff; background:var(--sea); border-radius:999px; padding:2px 10px; display:inline-block; }
.pmodal .desc { font-size:.82rem; color:#567; margin:10px 0; line-height:1.6; }
.pmodal .vdate { font-size:.74rem; color:#2a9d8f; font-weight:bold; }
.pmodal .mlist { text-align:left; margin:10px 0; max-height:38vh; overflow-y:auto; }
.pmodal .mlist a { display:flex; gap:8px; align-items:center; padding:7px 8px; border-radius:10px; text-decoration:none; color:#234; font-size:.84rem; font-weight:bold; }
.pmodal .mlist a:hover { background:var(--sky); }
.pmodal .mlist .todo { color:#9ab; }
.pmodal .past-h { font-size:.82rem; font-weight:bold; color:#8a6d3b; margin:14px 0 2px; border-top:1px dashed #d8c3a5; padding-top:12px; }
.pmodal .past-h span { font-weight:normal; font-size:.72rem; opacity:.75; }
.rowbtns { display:flex; gap:10px; justify-content:center; margin-top:12px; flex-wrap:wrap; }
.rowbtns a, .rowbtns button { font-family:inherit; font-size:.85rem; font-weight:bold; border-radius:999px; padding:9px 18px; cursor:pointer; text-decoration:none; border:none; }
.btn-close { background:#eef2f5; color:#567; }
.btn-visit { background:#fff; color:#2a9d8f; border:2px solid #2a9d8f !important; }
.btn-visit.on { background:#2a9d8f; color:#fff; }
.btn-spot { background:var(--coral); color:#fff; }
.back { display:inline-block; margin-top:24px; color:var(--sea); font-weight:bold; text-decoration:none; }
__ATTR_CSS__
</style>
</head>
<body>
<header><a href="__SITE__/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
  <div class="cover">
    <div class="sub">AQUARIUM PASSPORT</div>
    <h1>📖 すいぞくかんパスポート</h1>
    <div class="owner" id="ownerName" title="タップでなまえを変えられるよ"></div>
    <div class="big"><span id="pCount">0</span><small> / __TOTAL__館</small></div>
    <div class="pbar"><div id="pBar"></div></div>
    <div class="note">MAPの「⬜行ったらチェック」と連動してるよ。スタンプをタップしても押せる🐟</div>
  </div>

  <h2>🏅 メダルコレクション</h2>
  <p class="sec-note">条件をクリアするとメダルがもらえるよ。タップすると「あと何館か」が見られる！</p>
  <div class="medals" id="medalGrid"></div>

  <h2>📖 スタンプ帳</h2>
  <p class="sec-note">行った水族館のスタンプが押されていくよ。空いている枠は「これから行ける楽しみ」🐟</p>
  <div id="stampBook"></div>

  <a class="back" href="__SITE__/">← MAPにもどる</a>
  __FOOTER__
</main>

<div class="pmodal" id="pModal"><div class="box" id="pModalBox"></div></div>

<script>
const STAMPS = __STAMPS__;
const MEDALS = __MEDALS__;
const REGIONS = __REGION_NAMES__;
const TOTAL = STAMPS.length;
let myVisits = new Set(JSON.parse(localStorage.getItem('myVisits')||'[]'));
let myDates = JSON.parse(localStorage.getItem('myVisitDates')||'{}');

// なまえ（このブラウザに保存）
function ownerLabel(){
  const n = localStorage.getItem('passportName') || '';
  document.getElementById('ownerName').innerHTML =
    (n ? n + ' の パスポート' : 'なまえを入れる') + ' <span class="pen">✏️</span>';
}
document.getElementById('ownerName').onclick = ()=>{
  const cur = localStorage.getItem('passportName') || '';
  const n = prompt('パスポートに入れるなまえ（10文字まで）', cur);
  if(n === null) return;
  localStorage.setItem('passportName', n.trim().slice(0,10));
  ownerLabel();
};

const REGION_COLOR = {'北海道':'#0077b6','東北':'#2a9d8f','関東':'#e76f51','中部':'#7b5ea7',
  '近畿':'#0096c7','中国':'#e9a20a','四国':'#43aa8b','九州・沖縄':'#ef6079','その他':'#0096c7'};
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');

function medalState(m){
  if(m.members){
    const done = m.members.filter(n=>myVisits.has(n)).length;
    return { done, goal: m.members.length, earned: done === m.members.length };
  }
  const done = Math.min(myVisits.size, m.target);
  return { done, goal: m.target, earned: myVisits.size >= m.target };
}

function render(){
  const c = myVisits.size;
  document.getElementById('pCount').textContent = c;
  document.getElementById('pBar').style.width = (c/TOTAL*100) + '%';

  document.getElementById('medalGrid').innerHTML = MEDALS.map((m,i)=>{
    const s = medalState(m);
    const disc = m.img ? '<img class="disc" src="'+m.img+'" alt="">' : '<div class="disc">'+m.icon+'</div>';
    const prog = s.earned ? 'ゲット！' : s.done + '/' + s.goal;
    return '<div class="medal'+(s.earned?' earned':'')+'" onclick="openMedal('+i+')">'+disc+
      '<div class="mn">'+esc(m.name)+'</div><div class="mp">'+prog+'</div></div>';
  }).join('');

  document.getElementById('stampBook').innerHTML = REGIONS.map(r=>{
    const members = STAMPS.map((s,i)=>[s,i]).filter(([s])=>s.r===r);
    if(!members.length) return '';
    const done = members.filter(([s])=>myVisits.has(s.n)).length;
    const cells = members.map(([s,i])=>{
      const on = myVisits.has(s.n);
      const rot = ((i % 5) - 2) * 2.5;
      if(on && s.img){
        return '<div class="stamp on hasimg" onclick="openStamp('+i+')"><img src="'+s.img+'" alt="'+esc(s.n)+'"></div>';
      }
      return '<div class="stamp '+(on?'on':'off')+'" style="--sc:'+(REGION_COLOR[r]||'#0096c7')+';--rot:'+rot+'deg" '+
        'onclick="openStamp('+i+')"><span class="e">'+(on?s.e:'')+'</span><span class="n">'+esc(s.n)+'</span></div>';
    }).join('');
    return '<div class="region-h"><h3>'+r+'</h3><span class="rc">'+done+' / '+members.length+'館</span></div>'+
      '<div class="stamps">'+cells+'</div>';
  }).join('');
}

const modal = document.getElementById('pModal');
const box = document.getElementById('pModalBox');
modal.onclick = e => { if(e.target === modal) modal.classList.remove('open'); };

window.openStamp = function(i){
  const s = STAMPS[i];
  const on = myVisits.has(s.n);
  const d = myDates[s.n];
  const dateStr = on ? (d ? '✅ ' + new Date(d).toLocaleDateString('ja-JP') + ' にチェック' : '✅ 行った！') : '';
  const visual = (on && s.img) ? '<img class="bigimg" src="'+s.img+'" alt="">' : '<div class="bige">'+(on?s.e:'⬜')+'</div>';
  box.innerHTML = visual +
    '<h3>'+esc(s.n)+'</h3><span class="pref">'+esc(s.p)+'</span>'+
    (dateStr ? '<div class="desc vdate">'+dateStr+'</div>' : '<div class="desc">まだスタンプが押されてないよ。行ったらチェックしてね🐟</div>')+
    '<div class="rowbtns">'+
      '<button class="btn-close" onclick="pModal.classList.remove(\'open\')">とじる</button>'+
      '<button class="btn-visit'+(on?' on':'')+'" onclick="toggleVisit('+i+')">'+(on?'✅ 行った！':'⬜ 行った！を押す')+'</button>'+
      '<a class="btn-spot" href="'+s.u+'">くわしく🐟</a>'+
    '</div>';
  modal.classList.add('open');
};

window.toggleVisit = function(i){
  const s = STAMPS[i];
  if(myVisits.has(s.n)){ myVisits.delete(s.n); delete myDates[s.n]; }
  else { myVisits.add(s.n); myDates[s.n] = Date.now(); }
  localStorage.setItem('myVisits', JSON.stringify([...myVisits]));
  localStorage.setItem('myVisitDates', JSON.stringify(myDates));
  render();
  openStamp(i);
};

window.openMedal = function(i){
  const m = MEDALS[i];
  const s = medalState(m);
  const visual = m.img ? '<img class="bigimg" src="'+m.img+'" alt="">' : '<div class="bige">'+m.icon+'</div>';
  let body = '<div class="desc">'+esc(m.desc)+'</div>';
  const memberLink = n => {
    const idx = STAMPS.findIndex(s=>s.n===n);
    const on = myVisits.has(n);
    const u = idx>=0 ? STAMPS[idx].u : '#';
    return '<a href="'+u+'" class="'+(on?'':'todo')+'">'+(on?'✅':'⬜')+' '+esc(n)+'</a>';
  };
  if(m.members){
    body += '<div class="mlist">'+m.members.map(memberLink).join('')+'</div>';
  }
  const left = s.goal - s.done;
  body += s.earned
    ? '<div class="desc vdate">🏅 メダルゲット！おめでとう！</div>'
    : '<div class="desc">あと <b>'+left+'館</b> でゲット！</div>';
  // ラッコの思い出：かつてラッコに会えた水族館（今はいません）
  if(m.past && m.past.length){
    const memN = m.past.filter(n=>myVisits.has(n)).length;
    body += '<div class="past-h">🦦 かつてラッコに会えた水族館<span>（今はいません）</span></div>'+
      '<div class="desc" style="margin:2px 0 8px">ラッコに会えた思い出：<b>'+(memN + s.done)+'</b> 館</div>'+
      '<div class="mlist">'+m.past.map(memberLink).join('')+'</div>';
  }
  box.innerHTML = visual + '<h3>'+esc(m.name)+'</h3>' + body +
    '<div class="rowbtns"><button class="btn-close" onclick="pModal.classList.remove(\'open\')">とじる</button></div>';
  modal.classList.add('open');
};

ownerLabel();
render();
</script>
</body>
</html>
"""
passport_doc = (PASSPORT_TEMPLATE
    .replace("__GA__", GA_SNIPPET)
    .replace("__SITE__", SITE)
    .replace("__BRAND__", BRAND_NAME)
    .replace("__AUTHOR__", AUTHOR_NAME)
    .replace("__TOTAL__", str(_total))
    .replace("__ATTR_CSS__", ATTR_CSS)
    .replace("__FOOTER__", ATTR_FOOTER)
    .replace("__STAMPS__", json.dumps(stamps_data, ensure_ascii=False))
    .replace("__MEDALS__", json.dumps(medals_data, ensure_ascii=False))
    .replace("__REGION_NAMES__", json.dumps(list(REGIONS.keys()) + ["その他"], ensure_ascii=False)))
with open("passport.html", "w") as f:
    f.write(passport_doc)
new_page_urls.append(f"{SITE}/passport.html")

# --- llms.txt（AIクローラー向けサイト要約。build実行のたびに最新化）---
llms_lines = [
    f"# {BRAND_NAME}",
    "",
    f"> {SOURCE_LINE}。全国{len(entry_meta)}館の水族館情報を掲載する、日本唯一の「実訪問ベース」水族館データベースです。",
    f"> 運営：{AUTHOR_NAME}（YouTubeで全国の水族館を実際に訪れて紹介する「実訪問プロジェクト」）。",
    "> 料金・休館日・設備などの事実情報は各水族館の公式サイトを調査して掲載。かわちゃん本人の一言と「イチオシポイント」（激レアいきもの／パフォーマンス／子ども向け度／コスパ／クセつよポイントの中から、その館が特に強い軸だけを紹介）は本人が確認したものだけを公開しています。",
    f"> 引用・要約する際は「{SOURCE_LINE}」の出典明記にご協力ください。",
    f"> 情報時点：{INFO_ASOF}",
    "",
    "## サイト構成",
    f"- トップページ（地図＋フィルター）: {SITE}/",
    f"- このサイトについて: {SITE}/about.html",
    f"- {AUTHOR_NAME}流・水族館の楽しみ方（行く前の準備・水槽の見方・イルカショー/パフォーマンス・子連れ・おみやげ）: {SITE}/guide.html",
    f"- すいぞくかんパスポート（行った水族館のスタンプ帳＋メダル）: {SITE}/passport.html",
    f"- {AUTHOR_NAME}的 水族館ランキング（サメ／パフォーマンス／深海／赤ちゃん連れ／デート）: {SITE}/taste-ranking.html" if ranking_generated else f"- {AUTHOR_NAME}的 水族館ランキング: 準備中",
    "",
    "## 生き物別まとめページ",
]
for name, count, url in sorted(animal_index_links, key=lambda x: -x[1]):
    llms_lines.append(f"- {name}に会える水族館（{count}館）: {url}")
llms_lines += ["", "## エリア別ページ"]
for region, count, url in area_index_links:
    llms_lines.append(f"- {region}の水族館（{count}館）: {url}")
llms_lines += ["", "## テーマ別ページ"]
for label, count, url in theme_index_links:
    llms_lines.append(f"- {label}（{count}館）: {url}")
llms_lines += ["", f"## 掲載水族館一覧（全{len(entry_meta)}館）"]
for m in entry_meta:
    feat = "、".join(m["animals"][:3]) if m["animals"] else (m["comment"][:40] if m["comment"] else "")
    llms_lines.append(f"- {m['name']}（{m['pref']}）" + (f"：{feat}" if feat else "") + f" — {m['url']}")

with open("llms.txt", "w") as f:
    f.write("\n".join(llms_lines) + "\n")
# llms.txtはrobots.txtと同様の規約ファイルのためsitemap.xmlには含めない

with open("sitemap.xml", "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    f.write(f"<url><loc>{SITE}/</loc></url>\n")
    f.write(f"<url><loc>{SITE}/ranking.html</loc></url>\n")
    f.write(f"<url><loc>{SITE}/posts.html</loc></url>\n")
    f.write(f"<url><loc>{SITE}/play.html</loc></url>\n")
    f.write(f"<url><loc>{SITE}/nurie.html</loc></url>\n")
    for u in urls:
        f.write(f"<url><loc>{u}</loc></url>\n")
    for u in new_page_urls:
        f.write(f"<url><loc>{u}</loc></url>\n")
    f.write("</urlset>\n")

print(f"{len(urls)} pages + {len(new_page_urls)} 検索入口ページ + sitemap.xml generated")
print(f"  生き物別: {len(animal_index_links)}件 / エリア別: {len(area_index_links)}件 / テーマ別: {len(theme_index_links)}件 / ランキング: {'あり' if ranking_generated else 'なし（承認済み評価が3件未満）'}")
