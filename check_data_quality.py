#!/usr/bin/env python3
"""data.jsonのデータ品質チェック（外部通信なし・ローカル完結・数秒で終わる）
2026-07-22 かわちゃん報告のバグ（画像の使い回しミス・座標ズレ・URL切れ）の再発防止用。
自動パトロールルーチン（2日に1回）から毎回呼ばれる想定。人間が単体で実行してもOK。
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PREFS = {
    "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県",
    "埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県",
    "岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
    "鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県",
    "佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"
}
# 日本の大まかな範囲（小笠原・南鳥島など極端な離島は除く一般的なbbox）
LAT_MIN, LAT_MAX = 24.0, 46.0
LNG_MIN, LNG_MAX = 122.0, 146.0


def load_spots():
    d = json.load(open(os.path.join(BASE, "data.json"), encoding="utf-8"))
    spots = []
    for a in d.get("aquariums", []):
        spots.append({**a, "_group": "aquariums"})
    for a in d.get("unvisited", []):
        spots.append({**a, "_group": "unvisited"})
    return spots


def check(spots):
    issues = []  # (severity, message)

    # 1. 必須フィールドの欠落
    for s in spots:
        name = s.get("name", "(名前なし)")
        for field in ("name", "pref", "lat", "lng"):
            if s.get(field) in (None, ""):
                issues.append(("ERROR", f"[{name}] 必須項目 '{field}' が空/欠落"))

    # 2. 座標の妥当性（範囲・型）
    for s in spots:
        name = s.get("name", "(名前なし)")
        lat, lng = s.get("lat"), s.get("lng")
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            continue  # 上のチェックで既に報告済み
        if not (LAT_MIN <= lat <= LAT_MAX) or not (LNG_MIN <= lng <= LNG_MAX):
            issues.append(("ERROR", f"[{name}] 座標が日本の範囲外の可能性: lat={lat}, lng={lng}"))

    # 3. 都道府県名の表記ゆれ
    for s in spots:
        name = s.get("name", "(名前なし)")
        pref = s.get("pref")
        if pref and pref not in PREFS:
            issues.append(("WARN", f"[{name}] pref『{pref}』が都道府県名リストに一致しない（表記ゆれの可能性）"))

    # 4. 座標の完全一致（コピペミスの可能性。同じ座標を2館以上が使っている）
    coord_map = {}
    for s in spots:
        lat, lng = s.get("lat"), s.get("lng")
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            continue
        key = (round(lat, 4), round(lng, 4))
        coord_map.setdefault(key, []).append(s.get("name", "(名前なし)"))
    for key, names in coord_map.items():
        if len(names) > 1:
            issues.append(("WARN", f"座標{key}が複数館で完全一致: {', '.join(names)}（コピペミスの可能性）"))

    # 5. 写真パスの使い回しミス検出（今回の実バグと同種）
    photo_map = {}
    for s in spots:
        photo = s.get("photo")
        if not photo:
            continue
        photo_map.setdefault(photo, []).append(s.get("name", "(名前なし)"))
    for photo, names in photo_map.items():
        if len(names) > 1:
            issues.append(("ERROR", f"写真 '{photo}' が複数館で使い回されている: {', '.join(names)}（誤って別館の写真が付いている可能性）"))

    # 6. 写真ファイルの実在確認（ローカルファイルなので通信不要）
    for s in spots:
        name = s.get("name", "(名前なし)")
        photo = s.get("photo")
        if photo and not os.path.exists(os.path.join(BASE, photo)):
            issues.append(("ERROR", f"[{name}] photoで指定されたファイルが存在しない: {photo}"))

    # 7. 公式サイトURLの形式チェック（実際の疎通確認はしない＝軽量チェックのみ）
    for s in spots:
        name = s.get("name", "(名前なし)")
        url = s.get("url")
        if url and not (url.startswith("http://") or url.startswith("https://")):
            issues.append(("WARN", f"[{name}] urlの形式が不正: {url}"))

    # 8. 名前の完全重複（同じ館が2回登録されていないか）
    name_count = {}
    for s in spots:
        name_count[s.get("name")] = name_count.get(s.get("name"), 0) + 1
    for name, cnt in name_count.items():
        if cnt > 1:
            issues.append(("ERROR", f"『{name}』が{cnt}回登録されている（重複掲載の可能性）"))

    return issues


def main():
    spots = load_spots()
    issues = check(spots)
    errors = [m for sev, m in issues if sev == "ERROR"]
    warns = [m for sev, m in issues if sev == "WARN"]

    print(f"データ品質チェック：全{len(spots)}館を検査")
    print(f"ERROR {len(errors)}件 / WARN {len(warns)}件\n")
    for m in errors:
        print(f"[ERROR] {m}")
    for m in warns:
        print(f"[WARN] {m}")
    if not issues:
        print("問題なし。")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
