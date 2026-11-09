import json
import os
import time
import subprocess
import requests

SPOTS_JSON_PATH = "data/spots.json"
OUTPUT_DIR = "audio/kanojo"
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 8  # 春日部つむぎ (ノーマル)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_and_save_mp3(text, output_mp3_path, speaker_id=SPEAKER_ID, max_retries=3):
    for attempt in range(max_retries):
        try:
            # 1. 音声合成クエリ作成
            params = {"text": text, "speaker": speaker_id}
            res_query = requests.post(f"{VOICEVOX_URL}/audio_query", params=params, timeout=15)
            if res_query.status_code != 200:
                time.sleep(1)
                continue
            query_data = res_query.json()
            query_data["speedScale"] = 1.08
            query_data["intonationScale"] = 1.15

            # 2. 音声合成
            res_synth = requests.post(
                f"{VOICEVOX_URL}/synthesis",
                params={"speaker": speaker_id},
                json=query_data,
                timeout=40
            )
            if res_synth.status_code != 200:
                time.sleep(1)
                continue

            # 3. ffmpegで音量1.8倍ブースト＋64kbpsモノラルMP3化
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i", "pipe:0",
                "-af", "volume=1.8",
                "-ac", "1",
                "-b:a", "64k",
                output_mp3_path
            ]
            
            proc = subprocess.run(
                ffmpeg_cmd,
                input=res_synth.content,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            if proc.returncode == 0:
                return True
        except Exception as e:
            time.sleep(1)
            
    print(f"失敗: {output_mp3_path}")
    return False

def main():
    # 登場ボイス (unlock.mp3)
    unlock_path = os.path.join(OUTPUT_DIR, "unlock.mp3")
    if not os.path.exists(unlock_path):
        print("=== 登場ボイス (unlock.mp3) 作成 ===")
        unlock_text = "……呼んだ？内緒のドライブ、連れてってくれるの？"
        generate_and_save_mp3(unlock_text, unlock_path)

    # spots.json の読み込み
    json_path = SPOTS_JSON_PATH
    if not os.path.exists(json_path):
        alt_path = os.path.join("drivenavi-main", SPOTS_JSON_PATH)
        if os.path.exists(alt_path):
            json_path = alt_path
        else:
            print("エラー: spots.json が見つかりません。")
            return

    with open(json_path, "r", encoding="utf-8") as f:
        spots = json.load(f)

    total = len(spots)
    print(f"=== 音声生成開始 (全 {total} 件) ===")

    success_cnt = 0
    skip_cnt = 0

    for i, spot in enumerate(spots):
        spot_id = spot["id"]
        kanojo_text = spot.get("dialogue", {}).get("kanojo")
        if not kanojo_text:
            continue

        output_mp3 = os.path.join(OUTPUT_DIR, f"{spot_id}.mp3")

        # 既に作成済みのファイルはスキップ（途中で止まっても再開可能）
        if os.path.exists(output_mp3):
            skip_cnt += 1
            continue

        print(f"[{i+1}/{total}] 生成中: {spot['name']} ({spot_id})")
        if generate_and_save_mp3(kanojo_text, output_mp3):
            success_cnt += 1
        
        # 負荷軽減ウェイト
        time.sleep(0.05)

    print("========================================")
    print(f"完了！ 新規作成: {success_cnt} 件 / スキップ済: {skip_cnt} 件")
    print(f"保存先: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()