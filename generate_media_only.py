import json
import os
import subprocess
import urllib.parse
import urllib.request

MEDIA_SPOTS_PATH = os.path.join("data", "media_spots.json")
OUTPUT_DIR = os.path.join("audio", "kanojo")
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 8  # 春日部つむぎ

os.makedirs(OUTPUT_DIR, exist_ok=True)

def synthesize_mp3(text, out_mp3_path):
    q_params = urllib.parse.urlencode({"text": text, "speaker": SPEAKER_ID})
    req_query = urllib.request.Request(f"{VOICEVOX_URL}/audio_query?{q_params}", method="POST")
    with urllib.request.urlopen(req_query) as res:
        query_data = res.read()

    s_params = urllib.parse.urlencode({"speaker": SPEAKER_ID})
    req_synth = urllib.request.Request(
        f"{VOICEVOX_URL}/synthesis?{s_params}",
        data=query_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    temp_wav = out_mp3_path.replace(".mp3", "_temp.wav")
    with urllib.request.urlopen(req_synth) as res:
        with open(temp_wav, "wb") as f:
            f.write(res.read())

    cmd = [
        "ffmpeg", "-y", "-i", temp_wav,
        "-filter:a", "volume=1.8",
        "-ac", "1", "-b:a", "64k",
        out_mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(temp_wav):
        os.remove(temp_wav)

def main():
    if not os.path.exists(MEDIA_SPOTS_PATH):
        print(f"エラー: {MEDIA_SPOTS_PATH} が見つかりません。")
        return

    with open(MEDIA_SPOTS_PATH, "r", encoding="utf-8") as f:
        spots = json.load(f)

    total = len(spots)
    print(f"=== メディアスポット用 音声生成開始 (全 {total} 件) ===")
    skip_cnt = 0

    for i, spot in enumerate(spots, 1):
        spot_id = spot.get("id")
        name = spot.get("name")
        text = spot.get("dialogue", {}).get("kanojo")
        
        # セリフが無い場合はデフォルト文を設定
        if not text:
            text = f"まもなく、{name}です。寄っていきますか？"

        if not spot_id:
            continue

        out_path = os.path.join(OUTPUT_DIR, f"{spot_id}.mp3")
        if os.path.exists(out_path):
            skip_cnt += 1
            continue

        print(f"[{i}/{total}] 生成中: {name} ({spot_id})")
        try:
            synthesize_mp3(text, out_path)
        except Exception as e:
            print(f"  -> エラー ({spot_id}): {e}")
            break

    print(f"\n=== 完了！ (既存スキップ: {skip_cnt} 件) ===")

if __name__ == "__main__":
    main()