import io
import json
import os
import re
import urllib.parse
import urllib.request
import zipfile

DATA_DIR = "data"
OUTPUT_JSON_PATH = os.path.join(DATA_DIR, "spots.json")
os.makedirs(DATA_DIR, exist_ok=True)

UA = {"User-Agent": "DriveConciergeApp/1.0 (https://github.com/)"}


def generate_kanojo_dialogue(name):
    templates = [
        f"ねぇねぇ、「{name}」があるよ！ちょっと寄ってソフトクリームでも食べない？",
        f"見て、「{name}」だって！ご当地のお土産見に行こ？",
        f"「{name}」が近いよ〜！運転お疲れさま、ここで少し休憩しよ？",
        f"あそこ、「{name}」だよ！美味しいもの売ってそうじゃない？寄ってこ！",
        f"「{name}」発見！ねぇ、スタンプ押していこうよ〜！"
    ]
    idx = sum(ord(c) for c in name) % len(templates)
    return templates[idx]


def add_spot(spots, seen, raw_name, lat, lng):
    if not raw_name:
        return
    clean = str(raw_name).split("（")[0].split("(")[0].strip()
    if not clean.startswith("道の駅"):
        clean = f"道の駅 {clean}"
    norm_key = clean.replace(" ", "").replace(" ", "")
    if norm_key in seen:
        return
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (ValueError, TypeError):
        return
    if not (20.0 <= lat_f <= 46.0 and 122.0 <= lng_f <= 146.0):
        return

    seen.add(norm_key)
    spots.append({
        "id": f"m_{len(spots) + 1:04d}",
        "name": clean,
        "lat": round(lat_f, 6),
        "lng": round(lng_f, 6),
        "dialogue": {
            "kanojo": generate_kanojo_dialogue(clean),
            "friend": f"おっ、「{clean}」があるぞ。休憩するか？",
            "dj": f"Approaching {clean}. Enjoy your drive."
        }
    })


def fetch_from_mlit_zip(spots, seen):
    url = "https://nlftp.mlit.go.jp/ksj/gml/data/P35/P35-18/P35-18_GML.zip"
    print("1. 国土交通省（国土数値情報 P35）公式ZIPを取得中...")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as res:
            zbytes = res.read()
        with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
            for fname in zf.namelist():
                if fname.endswith(".geojson"):
                    raw = zf.read(fname).decode("utf-8", errors="ignore")
                    data = json.loads(raw)
                    for feat in data.get("features", []):
                        p = feat.get("properties", {})
                        g = feat.get("geometry", {})
                        name = p.get("P35_006") or p.get("name")
                        lat = p.get("P35_001")
                        lng = p.get("P35_002")
                        if (not lat or not lng) and g:
                            coords = g.get("coordinates", [])
                            if len(coords) >= 2:
                                lng, lat = coords[0], coords[1]
                        add_spot(spots, seen, name, lat, lng)
        print(f"   -> 国交省データ読み込み完了 (累計: {len(spots)} 駅)")
    except Exception as e:
        print(f"   -> 国交省ZIPスキップ: {e}")


def fetch_from_gist(spots, seen):
    gist_api = "https://api.github.com/gists/6ebbd9d4a396a1483e98a477201f5f36"
    print("2. 国土数値情報 GeoJSONミラーを確認中...")
    try:
        req = urllib.request.Request(gist_api, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as res:
            gdata = json.loads(res.read().decode("utf-8"))
        for fobj in gdata.get("files", {}).values():
            raw_url = fobj.get("raw_url")
            if not raw_url:
                continue
            r2 = urllib.request.Request(raw_url, headers=UA)
            with urllib.request.urlopen(r2, timeout=30) as res2:
                geo = json.loads(res2.read().decode("utf-8"))
            for feat in geo.get("features", []):
                p = feat.get("properties", {})
                g = feat.get("geometry", {})
                name = p.get("P35_006") or p.get("name") or p.get("名称")
                coords = g.get("coordinates", [])
                lat = p.get("P35_001") or (coords[1] if len(coords) >= 2 else None)
                lng = p.get("P35_002") or (coords[0] if len(coords) >= 2 else None)
                add_spot(spots, seen, name, lat, lng)
        print(f"   -> ミラー読み込み完了 (累計: {len(spots)} 駅)")
    except Exception as e:
        print(f"   -> ミラースキップ: {e}")


def fetch_from_wikidata(spots, seen):
    print("3. Wikidata SPARQL から最新の道の駅データを取得中...")
    sparql = """
    SELECT ?itemLabel ?coord WHERE {
      ?class rdfs:label "道の駅"@ja .
      ?item wdt:P31 ?class ;
            wdt:P625 ?coord .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ja". }
    }
    """
    q = urllib.parse.urlencode({"query": sparql, "format": "json"})
    url = f"https://query.wikidata.org/sparql?{q}"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as res:
            wdata = json.loads(res.read().decode("utf-8"))
        bindings = wdata.get("results", {}).get("bindings", [])
        for b in bindings:
            name = b.get("itemLabel", {}).get("value", "")
            c_str = b.get("coord", {}).get("value", "")
            m = re.search(r"Point\(([-\d\.]+)\s+([-\d\.]+)\)", c_str)
            if name and m:
                lng, lat = m.group(1), m.group(2)
                add_spot(spots, seen, name, lat, lng)
        print(f"   -> Wikidata統合完了 (累計: {len(spots)} 駅)")
    except Exception as e:
        print(f"   -> Wikidataスキップ: {e}")


def main():
    print("=== 全国の道の駅（約1,200駅）統合取得を開始 ===")
    spots = []
    seen = set()

    fetch_from_mlit_zip(spots, seen)
    fetch_from_gist(spots, seen)
    fetch_from_wikidata(spots, seen)

    print(f"\n=== 取得・統合完了: 合計 {len(spots)} 箇所 ===")
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()