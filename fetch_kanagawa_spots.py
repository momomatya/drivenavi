import json
import requests
import time

# === 設定 ===
# ここに制限を解除した（または新しく作った）APIキーを入れてね！
API_KEY = "AIzaSyB0gNJvf344WTEQUxsw5BXC3gd3hhSpLLU"
INPUT_FILE = "places_spots.json"

# 検索するキーワード（15キーワード × 各20件 ＝ 最大300件抽出）
SEARCH_QUERIES = [
    "神奈川県 厚木市 絶景スポット", "神奈川県 厚木市 カフェ 駐車場あり", "神奈川県 厚木市 ドライブイン",
    "神奈川県 秦野市 ヤビツ峠 展望", "神奈川県 秦野市 絶景", "神奈川県 秦野市 カフェ 駐車場",
    "静岡県 御殿場市 富士山 絶景", "静岡県 御殿場市 ドライブ 休憩", "静岡県 御殿場市 カフェ",
    "神奈川県 清川村 宮ヶ瀬湖 絶景", "神奈川県 愛川町 ドライブ", "神奈川県 箱根町 絶景 ドライブ",
    "神奈川県 山北町 丹沢 絶景", "神奈川県 足柄上郡 松田町 絶景", "神奈川県 伊勢原市 大山 観光"
]

def get_max_spot_id(spots):
    """既存のスポットから最大のID番号を探す"""
    max_id = 5000
    for s in spots:
        s_id = s.get("id", "")
        if s_id.startswith("spot_"):
            try:
                num = int(s_id.replace("spot_", ""))
                if num > max_id:
                    max_id = num
            except ValueError:
                pass
    return max_id

def search_places(query):
    """Google Places API (New) を使ってスポットを検索"""
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types"
    }
    payload = {
        "textQuery": query,
        "languageCode": "ja",
        "maxResultCount": 20
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()
        if "places" in data:
            return data["places"]
        else:
            print(f"  [WARN] 結果なし または エラー: {data}")
            return []
    except Exception as e:
        print(f"  [ERROR] 通信エラー: {e}")
        return []

def main():
    if API_KEY == "あなたのAPIキーをここに入力":
        print("【エラー】API_KEY を実際のものに書き換えてね！")
        return

    print("Google Places API から神奈川・御殿場エリアのスポットを取得中...")

    # 既存のJSONを読み込み
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        spots = json.load(f)

    next_id_num = get_max_spot_id(spots) + 1
    existing_names = {s.get("name") for s in spots}
    
    new_spots = []
    
    # セリフのテンプレート（ランダムで割り当て）
    dialogues = [
        ("おっ、ここ良さそうだな！ちょっと車停めて休んでくか。", "Awesome stop! ドライブの疲れを癒やすナイスなプレイス！", "ここすごく良さそう！少し寄り道していかない？"),
        ("この辺り、走ってて気持ちいいな！景色も最高だぜ。", "Driving groove! ロケーション抜群のエリアをクルージング！", "綺麗な景色だね！ドライブ気分がすっごく盛り上がるよ！"),
        ("いい雰囲気の場所見つけたぜ！コーヒーでも飲みたい気分だな。", "Chill out time! リラックスできる極上の空間でひと休み！", "わぁ、素敵な場所！写真撮ってもいいかな？"),
        ("ナビのおすすめスポットだ！せっかくだし見ていこうぜ！", "Check it out! 近くのホットなスポットに到着だ！", "ナビがここをおすすめしてるよ！一緒に行ってみよっ！")
    ]

    for query in SEARCH_QUERIES:
        print(f"検索中: {query}")
        results = search_places(query)
        
        for place in results:
            name = place.get("displayName", {}).get("text", "")
            address = place.get("formattedAddress", "")
            loc = place.get("location", {})
            lat, lng = loc.get("latitude"), loc.get("longitude")
            
            # 住所に「日本、」が含まれていたら削る
            address = address.replace("日本、", "").strip()

            # 座標がない、または既に登録済みの名前ならスキップ
            if not lat or not lng or name in existing_names:
                continue
                
            # ランダムにセリフを選択
            import random
            t_msg, d_msg, k_msg = random.choice(dialogues)

            spot_obj = {
                "id": f"spot_{next_id_num}",
                "name": name,
                "address": address,
                "source": "Google Places API (Kanagawa/Gotemba)",
                "category": "scenic" if "park" in place.get("types", []) else "cafe" if "cafe" in place.get("types", []) else "route",
                "lat": lat,
                "lng": lng,
                "voice_file": f"spot_{next_id_num}.mp3",
                "dialogue": {
                    "tsure": f"「{t_msg}」",
                    "dj": f"「{d_msg}」",
                    "kanojo": f"「{k_msg}」"
                }
            }
            
            new_spots.append(spot_obj)
            existing_names.add(name)
            next_id_num += 1
            
        time.sleep(1) # API制限対策

    print(f"\n取得完了！ 新しく {len(new_spots)} 件のリアルなスポットを追加するよ。")
    
    # 結合して保存
    spots.extend(new_spots)
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

    print("places_spots.json への保存が完了したよ！")

if __name__ == "__main__":
    main()