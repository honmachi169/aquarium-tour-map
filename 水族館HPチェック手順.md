# 水族館HPチェック（定型セット）

かわちゃんが「水族館HPチェックして」と言ったら、以下①〜③をセットで実行して1つのレポートにまとめる。
対象サイト：https://aquarium.yasasea.com/ （GitHub Pages: honmachi169/aquarium-tour-map）
作業フォルダ：`/Users/kawata/Documents/AI用作業/水族館マップサイト`

---

## ① 更新（パトロール）
1. `python3 patrol_writeback.py feedback-list` … 未報告のご意見箱を確認
   - 内容を要約し、対応済みにしてよいものは `feedback-mark 行…` で既読化（明示行指定）
2. `python3 patrol_writeback.py photos-list` … 未承認の写真投稿を確認
   - **写真承認＝公開なのでかわちゃん判断**。一覧を見せて、承認OKの行だけ `photos-approve 行…`
   - 既知の重複スキップ行は承認しない（`patrol_state/sheet_comments_seen.json` の photos_skipped_note 参照）
3. 新規リクエスト館・情報修正があれば data.json を編集 → `python3 build_pages.py` で再生成
4. 変更があれば `git add -A && git commit && git push origin main`（コミットメッセージに内容を明記）

## ② 確認（ライブ疎通）
- `curl -s -o /dev/null -w "%{http_code}" https://aquarium.yasasea.com/` が 200
- data.json / 主要ページ（index.html, aquarium-list.html 等）が 200
- push後はGitHub Pages反映まで1〜2分。反映後にトップの `updated` 日付が最新か確認

## ③ アクセス分析（GA4）
- **本番デプロイURL（稼働中）**：
  `https://script.google.com/macros/s/AKfycbyuG5VK3l8WUliuBspaQxNC111u6ZJy7lJ5DseYMuWnn-Dk5L_Ng2Mdjrat_JNjRzpR/exec`
  合言葉 `key=yasasea-analytics-2026`。取得は必ず **Bashのcurl -L**（WebFetchは使わない）。
  ※ローカルの `analytics_api.gs` はPROPERTY_ID空のテンプレなので惑わされないこと。実体は上のデプロイ済みGAS。
- 取得コマンド例：
  - 直近30日：`curl -sL "<URL>?key=yasasea-analytics-2026&days=30"`
  - 週次比較：`?days=7` と `?start=14daysAgo&end=8daysAgo`（前週）の2本
  - 任意期間：`?start=YYYY-MM-DD&end=YYYY-MM-DD`
- JSONの構造：`totals`(activeUsers/newUsers/sessions/screenPageViews/averageSessionDuration)・`byDate`・`topPages`(pagePath,pageTitle)・`sources`(sessionSource/medium)・`devices`・`outbound`(linkDomain=外部クリック)。
- **ページパス→館名変換**：`/spot/NNN.html` の NNN は `data.json` の aquariums[].no と対応。館名に直して報告する。
- **読み解きの定番ポイント**：
  - GA計測開始は2026-07-12。それ以前にかかる比較は「データなし」と添える。
  - スパイク日（1日だけ跳ねてる）は流入元(sources)で原因を推定（t.co=X、l.instagram=IG、youtube.com=YT、google/yahoo=検索）。バズが前週枠に入ると週次比較が大きくマイナスに見えるが、それは自然な落ち着きで異常ではない旨を明記する。
  - `outbound` の `drive.google.com` は**ぬりえのダウンロード**（nurie_data.jsonの`dl`がDrive直リンク）。`youtube.com`はYT送客、`lin.ee`はLINE、`sakana-bro.com`は公式HP。
- **【重要】ぬりえ(nurie.html)はコアファン向けなので本体HPと分けて集計する**：
  - レポートを2バケットに分ける。
    - (A) 水族館HP本体：`/nurie.html` を除いた数字で語る（PVは 総PV − nurie.htmlのPV。人気ページTOPからもnurieは外す）。
    - (B) ぬりえ（コアファン向け）：`/nurie.html` の PV・ユーザーと、`outbound` の `drive.google.com` クリック数（＝ぬりえDL数）をまとめて別枠で報告。
  - 本体とぬりえは指標を混ぜない。前週比もそれぞれで出す。ユーザー数は本体とぬりえで重複しうるので、厳密な差引が要るときは注記を添える（PVはクリーンに差引可）。
  - 将来コアファン向けページが増えたら（例：passport等）同じ要領で切り出せる。ぬりえは必ず別枠。
- **前週比・気づき（伸びたページ/流入元・当たりコンテンツ）を一言添える**。数字の羅列で終わらせない。
- 補足：週次レポート（毎週日曜・7〜8月限定 `trig_01MHFwzHKbMVojbUALUYsDEr`）と月次レポート（毎月1日 `trig_011dGadZ2rvLu2Nkbepo8z5W`）のクラウドルーチンが同じ数字をGmail下書きで info@ に届けている。

---

## レポート形式
```
【水族館HPチェック YYYY-MM-DD】
① 更新：ご意見◯件 / 写真未承認◯件（うち新規◯件・要判断）／コミット有無
② 確認：サイト HTTP◯◯◯ / 反映◯
③ アクセス：主要数値と気づき（or 未設定の旨）
```
