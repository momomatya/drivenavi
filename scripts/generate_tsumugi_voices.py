import json
import os
import time
import io
import requests
from pydub import AudioSegment

# 設定
SPOTS_JSON_PATH = "data/spots.json"
OUTPUT_DIR = "audio/kanojo"
VOICEVOX_URL = "http://127.0.0.1:50021"

# 春日部つむぎ（ノーマル: 8）
SPEAKER_ID = 8

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_and_save_mp3(text, output_mp3_path, speaker_id=SPEAKER_ID):
    try:
        # 1. 音声合成クエリ作成
        params = {"text": text, "speaker": speaker_id}
        res_query = requests.post(f"{VOICEVOX_URL}/audio_query", params=params, timeout=10)
        if res_query.status_code != 200:
            print(f"クエリ生成エラー: {res_query.text}")
            return False
        query_data = res_query.json()

        # ドライブのノリに合わせてテンポ・イントネーションを微調整（お好みで変更可）
        query_data["speedScale"] = 1.08  # ほんの少し早口で元気よく
        query_data["intonationScale"] = 1.15  # 抑揚を少しアップ

        # 2. 音声合成 (WAVバイナリ取得)
        res_synth = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": speaker_id},
            json=query_data,
            timeout=30
        )
        if res_synth.status_code != 200:
            print(f"音声合成エラー: {res_synth.text}")
            return False

        # 3. メモリ上でWAVからMP3へ軽量圧縮 (64kbps モノラル)
        wav_audio = AudioSegment.from_file(io.BytesIO(res_synth.content), format="wav")
        wav_audio = wav_audio.set_channels(1)  # モノラル化
        wav_audio.export(output_mp3_path, format="mp3", bitrate="64k")
        return True

    except Exception as e:
        print(f"例外エラー発生: {e}")
        return False

def main():
    if not os.path.exists(SPOTS_JSON_PATH):
        print(f"エラー: {SPOTS_JSON_PATH} が見つかりません。")
        return

    with open(SPOTS_JSON_PATH, "r", encoding="utf-8") as f:
        spots = json.load(f)

    print(f"=== 春日部つむぎ 彼女モード音声生成開始 (全 {len(spots)} 件) ===")

    success_count = 0
    skip_count = 0

    for i, spot in enumerate(spots):
        spot_id = spot["id"]
        kanojo_text = spot.get("dialogue", {}).get("kanojo")

        if not kanojo_text:
            continue

        output_mp3 = os.path.join(OUTPUT_DIR, f"{spot_id}.mp3")

        # 既に作成済みの場合はスキップ
        if os.path.exists(output_mp3):
            skip_count += 1
            continue

        print(f"[{i+1}/{len(spots)}] 生成中: {spot['name']}（ID: {spot_id}）")
        print(f"  セリフ: 「{kanojo_text}」")
        
        ok = generate_and_save_mp3(kanojo_text, output_mp3)
        if ok:
            success_count += 1
        
        # 連続リクエストでVOICEVOXが詰まらないようわずかにウェイト
        time.sleep(0.08)

    print("========================================")
    print(f"完了！ 新規生成: {success_count} 件 / スキップ: {skip_count} 件")
    print(f"出力先: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
