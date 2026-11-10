import csv
import json
import requests
import time

# ==========================================
# 設定
# ==========================================
API_KEY = "YOUR_API_KEY_HERE"  # ここにGoogle Maps APIキーを入力
CSV_FILE = "input_spots.csv"
OUTPUT_JSON = "new_spots.json"
START_ID = 1000

# スポット一覧データ（ここから自動でCSVを起こします）
RAW_DATA = """name,address,category,source,url
大涌谷,神奈川県足柄下郡箱根町仙石原1251,scenic,観光情報,https://www.hakone.or.jp/
箱根ロープウェイ 早雲山駅,神奈川県足柄下郡箱根町強羅1300,scenic,観光情報,https://www.hakonenavi.jp/
箱根神社,神奈川県足柄下郡箱根町元箱根80-1,scenic,観光情報,https://hakonejinja.or.jp/
サロン・ド・テ ロザージュ,神奈川県足柄下郡箱根町元箱根90,cafe,G-News,http://www.odakyu-hotel.co.jp/rosage/
NARAYA CAFE,神奈川県足柄下郡箱根町宮ノ下404-13,cafe,G-News,http://naraya-cafe.com/
甘酒茶屋,神奈川県足柄下郡箱根町畑宿二子山395-1,sweets,G-News,http://www.amasake-chaya.jp/
城ヶ崎海岸 門脇吊橋,静岡県伊東市富戸,scenic,観光情報,https://itospa.com/
小室山リッジウォーク MISORA,静岡県伊東市川奈1260-1,scenic,観光情報,https://www.tokaibus.jp/business/misora.html
石廊崎オーシャンパーク,静岡県賀茂郡南伊豆町石廊崎546-5,scenic,観光情報,https://irouzaki.co.jp/
伊豆パノラマパーク,静岡県伊豆の国市長岡260-1,scenic,観光情報,https://www.panoramaterrace-1059.com/
七里ヶ浜海岸,神奈川県鎌倉市七里ガ浜東2-1-12,scenic,観光情報,https://www.trip-kamakura.com/
高徳院（鎌倉大仏）,神奈川県鎌倉市長谷4-2-28,scenic,観光情報,https://www.kotoku-in.jp/
樹ガーデン,神奈川県鎌倉市常盤917,cafe,G-News,https://itsuki-garden.com/
ブルーボトルコーヒー 鎌倉カフェ,神奈川県鎌倉市御成町15-7,cafe,G-News,https://store.bluebottlecoffee.jp/
レ・ザンジュ 鎌倉本店,神奈川県鎌倉市御成町13-35,sweets,G-News,https://www.lesanges.co.jp/
江の島シーキャンドル,神奈川県藤沢市江の島2-3-28,scenic,観光情報,https://enoshima-seacandle.com/
湘南平（高麗山公園）,神奈川県平塚市万田790,scenic,観光情報,http://www.city.hiratsuka.kanagawa.jp/
横浜赤レンガ倉庫,神奈川県横浜市中区新港1-1,scenic,観光情報,https://www.yokohama-akarenga.jp/
横浜港大さん橋国際客船ターミナル,神奈川県横浜市中区海岸通1-1-4,scenic,観光情報,https://osanbashi.jp/
港の見える丘公園,神奈川県横浜市中区山手町114,scenic,観光情報,https://www.city.yokohama.lg.jp/
岡本桟橋（原岡桟橋）,千葉県南房総市富浦町原岡210-1,scenic,観光情報,https://www.mboso-etoko.jp/
野島埼灯台,千葉県南房総市白浜町白浜630,scenic,観光情報,https://www.mboso-etoko.jp/
江川海岸,千葉県木更津市江川576-6,scenic,観光情報,https://kisarazu-kankou.info/
鳥居崎海浜公園,千葉県木更津市富士見3-5,scenic,観光情報,https://toriizaki.jp/
三井アウトレットパーク 木更津,千葉県木更津市金田東3-1-1,scenic,観光情報,https://mitsui-shopping-park.com/mop/kisarazu/
成田山新勝寺,千葉県成田市成田1,scenic,観光情報,https://www.naritasan.or.jp/
成田さくらの山,千葉県成田市駒井野1338-1,scenic,観光情報,https://www.nrtk.jp/
羊山公園（芝桜の丘）,埼玉県秩父市大宮6360,scenic,観光情報,https://navi.city.chichibu.lg.jp/
三峯神社,埼玉県秩父市三峰298-1,scenic,観光情報,https://www.mitsuminejinja.or.jp/
阿左美冷蔵 金崎本店,埼玉県秩父郡皆野町金崎27-1,sweets,G-News,http://asamireizou.blog49.fc2.com/
華厳の滝,栃木県日光市中宮祠2479-2,scenic,観光情報,http://kegon.jp/
中禅寺湖展望台,栃木県日光市中宮祠,scenic,観光情報,http://www.nikko-kankou.org/
日光東照宮,栃木県日光市山内2301,scenic,観光情報,https://www.toushougu.jp/
日光珈琲 御用邸通,栃木県日光市本町3-13,cafe,G-News,http://nikko-coffee.com/
チーズガーデン 那須本店,栃木県那須郡那須町高久甲喰木原2888,sweets,G-News,https://cheesegarden.jp/
NASU SHOZO CAFE,栃木県那須郡那須町高久乙2730-25,cafe,G-News,http://www.shozo.co.jp/
白糸の滝,長野県北佐久郡軽井沢町長倉,scenic,観光情報,https://www.town.karuizawa.lg.jp/
大石公園,山梨県南都留郡富士河口湖町大石2585,scenic,観光情報,http://www.fkchannel.jp/oishipark/
新倉山浅間公園,山梨県富士吉田市浅間2-4-1,scenic,観光情報,https://fujiyoshida.net/spot/12
山中湖パノラマ台,山梨県南都留郡山中湖村平野,scenic,観光情報,https://lake-yamanakako.com/
ペーパームーン 山中湖店,山梨県南都留郡山中湖村平野481-1,cafe,G-News,http://www.papermoon-sweetskitchen.com/"""

def get_coordinates(target, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": target, "key": api_key, "language": "ja"}
    response = requests.get(url, params=params)
    data = response.json()
    if data["status"] == "OK":
        loc = data["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    return None, None

def generate_dialogue(name, category):
    if category == "michinoeki":
        return f"近くに、{name}があるよ！ちょっと休憩していこっか？"
    elif category == "scenic":
        return f"もうすぐ、{name}だよ。景色が良いみたいだから寄ってみない？"
    elif category in ["cafe", "sweets"]:
        return f"近くの{name}ってお店、ちょっと気になるかも！"
    return f"近くに、{name}があるみたいだよ。"

def main():
    # 1. まず input_spots.csv を自動生成して保存
    with open(CSV_FILE, "w", encoding="utf-8") as f:
        f.write(RAW_DATA.strip())
    print(f"'{CSV_FILE}' を自動生成しました。")

    # 2. 生成したCSVを読み込んでGoogle Maps APIで座標取得
    spots = []
    current_id = START_ID
    
    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"合計 {len(rows)} 件のスポットを処理開始...")
        
        for row in rows:
            name = row["name"].strip()
            address = row["address"].strip()
            category = row.get("category", "spot")
            search_target = address if address else name
            
            print(f"取得中: {name}")
            lat, lng = get_coordinates(search_target, API_KEY)
            
            if lat and lng:
                spot_id = f"spot_{current_id:04d}"
                spot_data = {
                    "id": spot_id,
                    "name": name,
                    "address": address,
                    "source": row.get("source", "").strip(),
                    "category": category,
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "voice_file": f"{spot_id}.mp3",
                    "url": row.get("url", "").strip(),
                    "dialogue": {
                        "kanojo": generate_dialogue(name, category)
                    }
                }
                spots.append(spot_data)
                current_id += 1
                print(f"  -> 成功: {round(lat, 4)}, {round(lng, 4)}")
            else:
                print(f"  -> 失敗: 座標取得エラー")
            
            time.sleep(0.2)

    # 3. new_spots.json に保存
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
        
    print(f"\n完了！ '{OUTPUT_JSON}' に保存されたよ！")

if __name__ == "__main__":
    main()