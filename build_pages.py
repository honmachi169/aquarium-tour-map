#!/usr/bin/env python3
# data.json から水族館ごとの個別ページ(spot/*.html)とsitemap.xmlを生成する
# 使い方: python3 build_pages.py  → git add spot sitemap.xml → commit/push
import json, os, html, re, unicodedata, urllib.parse

SITE = "https://aquarium.yasasea.com"
COMMENT_API = "https://script.google.com/macros/s/AKfycbz6A_7okvNBKrrygHuOgJ4TQV1YlrB_UPx2_c3hMS9fG6YTunOrrOKROeHdHJg2QzXj/exec"
YT_API_KEY = "AIzaSyCASXQcc_wH8jOy9PA2oa5dUlBWUgRBGms"
os.makedirs("spot", exist_ok=True)

TAG_LABEL = {"rain":"☔️ 雨の日におすすめ","kids":"👶 未就学児におすすめ","same":"🦈 サメ好きにおすすめ",
             "dolphin":"🐬 イルカショーおすすめ","deep":"🐙 深海生物好きにおすすめ",
             "penguin":"🐧 ペンギン好きにおすすめ","summer":"☀️ 夏休みおすすめ",
             "baby":"🍼 赤ちゃん連れにおすすめ","beluga":"🐳 シロイルカに会える"}
ANIMAL_ICONS = {"シャチ":"🐋","ラッコ":"🦦","ジンベエザメ":"🦈","シロワニ":"🦈","マンボウ":"🐟",
                "ピラルクー":"🐠","エンペラーペンギン":"🐧","フェアリーペンギン":"🐧","クラゲ":"🪼","ベルーガ":"🐳"}

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
    tagchips = "".join(f'<span class="chip tag">{TAG_LABEL[t]}</span>' for t in a.get("tags", []) if t in TAG_LABEL)

    info = ""
    if a.get("fee"): info += f"<tr><th>💰 大人</th><td>{E(a['fee'])}</td></tr>"
    if a.get("child"): info += f"<tr><th>🧒 子ども</th><td>{E(a['child'])}</td></tr>"
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

    hitokoto = ""
    if a.get("hitokoto"):
        hitokoto = f'<div class="hitokoto"><div class="hk-label">🐟 かわちゃんからの一言</div>{E(a["hitokoto"])}</div>'

    highlights_box = ""
    if a.get("highlights"):
        rows = "".join(f"<li>{E(h)}</li>" for h in a["highlights"])
        highlights_box = f'<div class="highlights-box"><div class="hk-label">🔍 かわちゃん見どころポイント！</div><ul>{rows}</ul></div>'

    RATING_LABEL = {"kuse":"🌀 クセつよポイント","suzu":"❄️ 涼しさ","kids":"👶 子ども向け度","hakuryoku":"💥 迫力","cospa":"💰 コスパ"}
    ratings = a.get("ratings") or {}
    rating_rows = ""
    for key, label in RATING_LABEL.items():
        if key in ratings:
            n = max(0, min(5, int(ratings[key])))
            stars = "★"*n + "☆"*(5-n)
            rating_rows += f'<div class="rate-row"><span class="rate-label">{label}</span><span class="rate-stars">{stars}</span></div>'
    ratings_box = f'<div class="ratings-box"><div class="hk-label">🐟 かわちゃん的 5段階評価</div>{rating_rows}</div>' if rating_rows else ""

    summer = f'<div class="summer">☀️ <b>夏休み情報：</b>{E(a["summer"])}</div>' if a.get("summer") else ""
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
<link rel="icon" type="image/x-icon" href="../assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="../assets/apple-touch-icon.png">
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
  .filming-note {{ font-size:.75rem; color:#0077b6; background:#e0f7fa; border-radius:8px; padding:5px 12px; margin:6px 0 0; display:inline-block; }}
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
  #comment-form input, #comment-form textarea {{ border:2px solid var(--sky); border-radius:10px; padding:8px 12px; font-size:.88rem; font-family:inherit; outline:none; width:100%; }}
  #comment-form input:focus, #comment-form textarea:focus {{ border-color:var(--sea); }}
  #comment-form button {{ background:var(--sea); color:#fff; border:none; border-radius:999px; padding:10px; font-size:.9rem; font-weight:bold; cursor:pointer; font-family:inherit; }}
  #c-status {{ font-size:.8rem; color:var(--sea); min-height:1.2em; }}
</style>
</head>
<body>
<header><a href="{SITE}/">🐟 会いに行こう！全国水族館ツアーMAP</a></header>
<main>
  <p class="kicker">{kicker}</p>
  {filming_note}
  <h1>{E(a['name'])}</h1>
  <span class="pref">{E(a['pref'])}</span>
  {videos or hero}
  <p class="hl">{E(a.get('highlight') or a.get('comment') or '')}</p>
  <div class="chips">{chips}{tagchips}</div>
  {hitokoto}
  {highlights_box}
  {summer}
  <table>{info}</table>
  {ratings_box}
  <p class="note">※最新の料金・営業情報は公式サイトでチェックしてね</p>
  <div class="btns">
    {links}
    <a class="btn share" href="https://twitter.com/intent/tweet?text={html.escape(share_text)}&url={page_url}" target="_blank" rel="noopener">🕊 シェアする</a>
  </div>
  <a class="back" href="{SITE}/">← MAPにもどる</a>

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

with open("sitemap.xml", "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    f.write(f"<url><loc>{SITE}/</loc></url>\n")
    f.write(f"<url><loc>{SITE}/ranking.html</loc></url>\n")
    f.write(f"<url><loc>{SITE}/posts.html</loc></url>\n")
    f.write(f"<url><loc>{SITE}/play.html</loc></url>\n")
    for u in urls:
        f.write(f"<url><loc>{u}</loc></url>\n")
    f.write("</urlset>\n")

print(f"{len(urls)} pages + sitemap.xml generated")
