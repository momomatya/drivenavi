import json
import requests
import time

# ==========================================
# 設定
# ==========================================
API_KEY = "AIzaSyB0gNJvf344WTEQUxsw5BXC3gd3hhSpLLU"  # お使いのAPIキー
OUTPUT_JSON = "places_spots.json"
START_ID = 2000

# 検索したいカテゴリとキーワードの組み合わせ
TARGETS = [
    {"category": "scenic", "keyword": "絶景 展望台", "phrase": "絶景スポットの{name}が近いよ！寄り道してみる？"},
    {"category": "route", "keyword": "ドライブルート スカイライン パークウェイ", "phrase": "走りごたえのありそうな{name}の近くに来たよ！"},
    {"category": "cafe", "keyword": "カフェ", "phrase": "近くの{name}ってカフェ、ちょっと気にならない？"}
]

# 全国の主要ドライブ・ツーリングエリア（47都道府県・主要観光山間部）
AREAS = [
    # 北海道・東北
    "北海道 美瑛", "北海道 富良野", "北海道 ニセコ", "北海道 函館", "北海道 知床",
    "青森県 奥入瀬", "青森県 八甲田", "岩手県 八幡平", "秋田県 鳥海山", "秋田県 男鹿",
    "宮城県 蔵王", "山形県 蔵王", "山形県 出羽三山", "福島県 磐梯高原", "福島県 猪苗代",
    # 関東
    "茨城県 筑波山", "栃木県 日光", "栃木県 那須", "群馬県 赤城山", "群馬県 榛名山", "群馬県 草津",
    "埼玉県 秩父", "千葉県 房総スカイライン", "千葉県 館山", "東京都 奥多摩",
    "神奈川県 箱根", "神奈川県 湘南", "神奈川県 三浦半島",
    # 中部・北陸
    "山梨県 富士五湖", "山梨県 清里", "長野県 ビーナスライン", "長野県 志賀高原", "長野県 軽井沢",
    "新潟県 妙高", "新潟県 佐渡", "富山県 雨晴海岸", "石川県 能登半島", "福井県 三方五湖",
    "静岡県 伊豆スカイライン", "静岡県 朝霧高原", "岐阜県 白川郷", "岐阜県 せせらぎ街道", "愛知県 知多半島",
    # 近畿
    "三重県 伊勢志摩スカイライン", "滋賀県 琵琶湖", "京都府 天橋立", "京都府 嵐山",
    "兵庫県 六甲山", "兵庫県 淡路島", "奈良県 吉野", "和歌山県 高野山", "和歌山県 白浜",
    # 中国・四国
    "鳥取県 大山", "島根県 出雲", "岡山県 蒜山高原", "広島県 しまなみ海道", "山口県 角島", "山口県 秋吉台",
    "徳島県 祖谷", "香川県 屋島", "愛媛県 佐田岬", "高知県 室戸岬", "高知県 四国カルスト",
    # 九州・沖縄
    "福岡県 糸島", "佐賀県 唐津", "長崎県 雲仙", "熊本県 阿蘇", "大分県 やまなみハイウェイ",
    "宮崎県 日南海岸", "鹿児島県 霧島", "鹿児島県 指宿", "沖縄県 古宇利島"
]

def search_places_new(query, api_key):
    """Google Places API (New) でスポットを検索"""
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location"
    }
    payload = {
        "textQuery": query,
        "languageCode": "ja"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        if "places" in data:
            return data["places"]
        return []
    except Exception as e:
        print(f"  -> リクエスト失敗: {e}")
        return []

def main():
    all_spots = []
    current_id = START_ID
    seen_place_ids = set()
    
    total_searches = len(AREAS) * len(TARGETS)
    print(f"全国 {len(AREAS)} エリア × {len(TARGETS)} カテゴリ（計 {total_searches} 回）の検索を開始します...")
    
    count = 0
    for area in AREAS:
        for target in TARGETS:
            count += 1
            query = f"{area} {target['keyword']}"
            print(f"[{count}/{total_searches}] 検索中: {query}")
            
            places = search_places_new(query, API_KEY)
            print(f"  -> {len(places)} 件取得")
            
            for place in places:
                place_id = place.get("id")
                if not place_id or place_id in seen_place_ids:
                    continue
                seen_place_ids.add(place_id)
                
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
                    "source": "Google Places (Nationwide)",
                    "category": target["category"],
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "voice_file": f"{spot_id}.mp3",
                    "url": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                    "dialogue": {
                        "kanojo": target["phrase"].format(name=name)
                    }
                }
                all_spots.append(spot_data)
                current_id += 1
                
            time.sleep(0.5)  # レートリミット回避のための待機
            
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_spots, f, ensure_ascii=False, indent=2)
        
    print(f"\n完了！ 重複を除き、合計 {len(all_spots)} 件の全国スポットを '{OUTPUT_JSON}' に保存しました。")

if __name__ == "__main__":
    main()