import json
import requests
import time

# ==========================================
# 設定
# ==========================================
API_KEY = "YOUR_API_KEY_HERE"  # ここにGoogle Maps APIキーを入力
OUTPUT_JSON = "places_spots.json"
START_ID = 2000  # 既存データとIDが被らないように2000番台からスタート

# 検索するキーワードとカテゴリ
KEYWORD = "カフェ"
CATEGORY = "cafe"

# 検索する地域（市町村を細かく分けるほど大量に取得できます）
CITIES = [
    "千葉県木更津市", "千葉県君津市", "千葉県袖ケ浦市", "千葉県富津市",
    "千葉県館山市", "千葉県南房総市", "千葉県鴨川市", "千葉県勝浦市",
    "千葉県市原市", "千葉県千葉市", "千葉県船橋市", "千葉県成田市",
    "神奈川県箱根町", "神奈川県小田原市", "静岡県御殿場市", "静岡県伊東市"
]

def generate_dialogue(name, category):
    return f"近くの{name}ってお店、ちょっと気になるかも！"

def search_places_new(query, api_key):
    """Google Places API (New) でスポットを検索"""
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # 取得したいフィールドを明示的に指定（これをしないとエラーになります）
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location"
    }
    
    # Places API (New) は日本語言語コードをJSONボディに含めます
    payload = {
        "textQuery": query,
        "languageCode": "ja"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    # 検索結果があれば "places" リストとして返ってくる
    if "places" in data:
        return data["places"]
    else:
        print(f"  -> レスポンスエラー または 0件: {data}")
        return []

def main():
    all_spots = []
    current_id = START_ID
    seen_place_ids = set() # 重複登録を防ぐためのセット
    
    print(f"全 {len(CITIES)} エリアの検索を開始します (Places API New)...")
    
    for city in CITIES:
        search_query = f"{city} {KEYWORD}"
        print(f"検索中: {search_query}")
        
        places = search_places_new(search_query, API_KEY)
        print(f"  -> {len(places)} 件取得")
        
        for place in places:
            # (New) APIはIDのキーが "id" になっています
            place_id = place.get("id")
            
            if not place_id or place_id in seen_place_ids:
                continue 
            seen_place_ids.add(place_id)
            
            # (New) APIは名前の構造が異なります
            name = place.get("displayName", {}).get("text", "")
            address = place.get("formattedAddress", "").replace("日本、", "")
            
            location = place.get("location", {})
            lat = location.get("latitude")
            lng = location.get("longitude")
            
            if not name or not lat or not lng:
                continue
            
            spot_id = f"spot_{current_id:04d}"
            spot_data = {
                "id": spot_id,
                "name": name,
                "address": address,
                "source": "Google Places",
                "category": CATEGORY,
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "voice_file": f"{spot_id}.mp3",
                "url": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                "dialogue": {
                    "kanojo": generate_dialogue(name, CATEGORY)
                }
            }
            all_spots.append(spot_data)
            current_id += 1
            
        time.sleep(1)
        
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_spots, f, ensure_ascii=False, indent=2)
        
    print(f"\n完了！ 重複を除き、合計 {len(all_spots)} 件のスポットを '{OUTPUT_JSON}' に保存しました。")

if __name__ == "__main__":
    main()