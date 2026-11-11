import json
import requests
import time
import os

# --- 設定 ---
API_KEY = "AIzaSyB0gNJvf344WTEQUxsw5BXC3gd3hhSpLLU"
INPUT_FILE = "places_spots.json"
TARGET_START_ID = 5001  # このID以降のスポットを修正対象にする

def get_real_location(name, address):
    """Google Maps Geocoding APIを使って正確な座標を取得"""
    # 検索精度を上げるため、住所とスポット名を組み合わせて検索
    query = f"{address} {name}"
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": API_KEY,
        "language": "ja"
    }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        
        if data["status"] == "OK" and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            print(f"  [WARN] 座標取得失敗 ({data['status']})")
            return None, None
    except Exception as e:
        print(f"  [ERROR] API通信エラー: {e}")
        return None, None

def main():
    if API_KEY == "ここにあなたのGoogle Maps APIキーを入力してください":
        print("【エラー】スクリプト内の API_KEY を実際のものに書き換えてください。")
        return

    print("Google Maps APIを使った座標の自動修正を開始します...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        spots = json.load(f)

    fixed_count = 0
    error_count = 0

    for idx, spot in enumerate(spots):
        spot_id = spot.get("id", "")
        # spot_5001 以降のカスタム追加分のみを対象にする
        if spot_id.startswith("spot_"):
            try:
                num = int(spot_id.replace("spot_", ""))
                if num >= TARGET_START_ID:
                    name = spot.get("name", "")
                    address = spot.get("address", "")
                    
                    print(f"[{idx+1}/{len(spots)}] 座標検索中: {name} ({address})")
                    
                    real_lat, real_lng = get_real_location(name, address)
                    
                    if real_lat and real_lng:
                        spot["lat"] = real_lat
                        spot["lng"] = real_lng
                        fixed_count += 1
                    else:
                        error_count += 1
                        
                    # API制限対策で少し待機
                    time.sleep(0.1)

            except ValueError:
                continue

    # 元のファイルに上書き保存
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

    print("\n==========================================")
    print(f"修正完了！ 正確な座標に更新: {fixed_count}件 / 取得失敗: {error_count}件")
    print("==========================================")

if __name__ == "__main__":
    main()