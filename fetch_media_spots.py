import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DATA_DIR = "data"
OUTPUT_PATH = os.path.join(DATA_DIR, "media_spots.json")
os.makedirs(DATA_DIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DriveConcierge/1.0"}

RSS_FEEDS = [
    {"source": "じゃらんニュース", "url": "https://www.jalan.net/news/feed/"},
    {"source": "ことりっぷ", "url": "https://co-trip.jp/feed/"},
    {"source": "Fashion Press", "url": "https://www.fashion-press.net/news/line.rss"},
    {"source": "えん食べ", "url": "https://entabe.jp/news/feed.rss"}
]

# 追加指定エリアをセット
TARGET_AREAS = [
    "箱根", "伊豆", "鎌倉", "横浜", "湘南", "房総", "成田", "木更津", 
    "秩父", "日光", "那須", "軽井沢", "富士五湖", "静岡", "京都", "札幌", "福岡",
    "群馬", "茨城", "富士", "大阪", "御殿場"
]
TARGET_KEYWORDS = ["絶景", "カフェ", "スイーツ"]

for area in TARGET_AREAS:
    for kw in TARGET_KEYWORDS:
        q = f"{area} {kw}"
        enc_q = urllib.parse.quote(q)
        url = f"https://news.google.com/rss/search?q={enc_q}&hl=ja&gl=JP&ceid=JP:ja"
        RSS_FEEDS.append({"source": f"G-News({area})", "url": url})

GSI_GEO_API = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
EXCLUDE_WORDS = ["市町村", "駐車場", "各都市", "中心街", "都市部", "全自治体", "市区町村", "都市型", "全国", "一部", "対象外"]

def get_lat_lng(address_text):
    try:
        q = urllib.parse.quote(address_text)
        req = urllib.request.Request(f"{GSI_GEO_API}{q}", headers=UA)
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data and len(data) > 0:
                coords = data[0].get("geometry", {}).get("coordinates", [])
                if len(coords) >= 2:
                    return float(coords[1]), float(coords[0])
    except Exception:
        pass
    return None, None

def classify_category(text):
    if any(k in text for k in ["パフェ", "ケーキ", "スイーツ", "ジェラート", "プリン", "チョコ", "和菓子", "タルト", "パンケーキ", "アイス", "シュークリーム", "苺", "いちご", "栗", "モンブラン"]):
        return "sweets"
    elif any(k in text for k in ["絶景", "展望", "富士山", "夕日", "海沿い", "滝", "紅葉", "桜", "夜景", "岬", "パノラマ", "峠", "山頂", "海岸", "ドライブ", "温泉", "渓谷"]):
        return "scenic"
    elif any(k in text for k in ["カフェ", "珈琲", "コーヒー", "喫茶", "古民家", "ベーカリー", "スタンド", "ロースタリー", "紅茶", "テラス", "ランチ", "パン"]):
        return "cafe"
    return None

def extract_location(text, area_hint=""):
    m1 = re.search(r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)([^\s、。「」【】\(\)\d]{2,6}[市区町村郡])', text)
    if m1:
        loc = f"{m1.group(1)}{m1.group(2)}"
        if not any(ex in loc for ex in EXCLUDE_WORDS):
            return loc
            
    m2 = re.search(r'([^\s、。「」【】\(\)\d]{2,5}[市区町村])', text)
    if m2:
        loc = m2.group(1)
        if not any(ex in loc for ex in EXCLUDE_WORDS):
            return loc

    # エリア判定リストにも新エリアを追加
    areas = [
        "箱根", "軽井沢", "伊豆", "日光", "那須", "熱海", "鎌倉", "横浜", "湘南",
        "房総", "成田", "木更津", "銚子", "館山", "富士五湖", "秩父", "みなかみ",
        "宇治", "嵐山", "道頓堀", "白浜", "淡路島", "しまなみ海道", "阿蘇", "由布院",
        "小樽", "富良野", "函館", "松島", "金沢", "白川郷", "宮島", "別府",
        "銀座", "表参道", "渋谷", "新宿", "吉祥寺", "浅草", "東京", "京都", "大阪", "福岡", 
        "札幌", "名古屋", "静岡", "千葉", "埼玉", "群馬", "茨城", "長野", "山梨", "神戸", 
        "富士", "御殿場"
    ]
    for a in areas:
        if a in text:
            return a
            
    if area_hint and area_hint in areas:
        return area_hint

    return None

def main():
    print("=== おでかけスポット無制限ブースト（上限なし）を開始 ===")
    print("※制限を外したため、終了まで10〜15分程度かかる場合があります")
    
    spots = []
    seen_titles = set()
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                spots = json.load(f)
                for s in spots:
                    seen_titles.add(s.get("name"))
            print(f"既存の蓄積スポット: {len(spots)} 件を保持")
        except Exception:
            spots = []

    new_count = 0

    for feed in RSS_FEEDS:
        src = feed["source"]
        url = feed["url"]
        
        area_hint = ""
        if "G-News" in src:
            area_hint = src.replace("G-News(", "").replace(")", "")

        print(f"\n[{src}] 取得中...")
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as res:
                xml_data = res.read()
            root = ET.fromstring(xml_data)
        except Exception:
            continue

        items = root.findall(".//item")
        if len(items) == 0:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            title_el = item.find("title")
            if title_el is None:
                title_el = item.find("{http://www.w3.org/2005/Atom}title")

            link_el = item.find("link")
            if link_el is None:
                link_el = item.find("{http://www.w3.org/2005/Atom}link")

            desc_el = item.find("description")
            if desc_el is None:
                desc_el = item.find("{http://www.w3.org/2005/Atom}summary")
            if desc_el is None:
                desc_el = item.find("{http://www.w3.org/2005/Atom}content")

            title = title_el.text if (title_el is not None and title_el.text) else ""
            link = link_el.text if (link_el is not None and link_el.text) else (link_el.get("href", "") if link_el is not None else "")
            desc = desc_el.text if (desc_el is not None and desc_el.text) else ""

            clean_title = re.sub(r'<[^>]+>', '', title).split(" - ")[0].strip()
            clean_desc = re.sub(r'<[^>]+>', '', desc).strip()

            if not clean_title or clean_title in seen_titles:
                continue

            full_text = f"{clean_title} {clean_desc}"
            cat = classify_category(full_text)
            if not cat:
                continue

            loc_query = extract_location(full_text, area_hint)
            if not loc_query:
                continue

            time.sleep(0.5)
            lat, lng = get_lat_lng(loc_query)
            if not lat or not lng:
                continue

            seen_titles.add(clean_title)
            spot_id = f"media_{len(spots) + 1:04d}"
            voice_id = f"{cat}_01" if (len(spots) % 2 == 0) else f"{cat}_02"

            spots.append({
                "id": spot_id,
                "name": clean_title,
                "source": src.split("(")[0], 
                "category": cat,
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "voice_file": f"{voice_id}.mp3",
                "url": link,
                "dialogue": {
                    "kanojo": f"【{src.split('(')[0]}】{clean_title}"
                }
            })
            new_count += 1
            print(f"  -> [{cat.upper()}] {clean_title[:20]}... ({loc_query})")

    print(f"\n=== ブースト完了: 新規 {new_count} 件追加（合計蓄積: {len(spots)} 箇所） ===")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
    print(f"保存先: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()