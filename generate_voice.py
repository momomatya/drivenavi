import os
import json
import time
import requests
import subprocess

# ==========================================
# 設定
# ==========================================
VOICEVOX_URL = "http://localhost:50021"
INPUT_JSON = "places_spots.json"
AUDIO_DIR = "audio"  # 音声ファイルを保存するフォルダ

# VOICEVOXのキャラクター指定（Speaker ID）
SPEAKER_ID = 8

def generate_voice_as_mp3(text, speaker_id, output_path):
    """VOICEVOXから取得した音声をffmpegで直接MP3に変換して保存する"""
    temp_wav = "temp_voice.wav"
    try:
        # 1. 音声合成用のクエリを作成
        query_res = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=10
        )
        if query_res.status_code != 200:
            print(f"    [エラー] クエリ作成失敗: {query_res.text}")
            return False
            
        query_data = query_res.json()
        query_data["speedScale"] = 1.05

        # 2. 音声データを合成（WAVバイナリ）
        synth_res = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            headers={"Content-Type": "application/json"},
            params={"speaker": speaker_id},
            data=json.dumps(query_data),
            timeout=30
        )
        if synth_res.status_code != 200:
            print(f"    [エラー] 音声合成失敗: {synth_res.text}")
            return False

        # 一時的にWAVとして書き出す
        with open(temp_wav, "wb") as f:
            f.write(synth_res.content)

        # 3. ffmpegを使ってWAVをMP3に超軽量圧縮（64kbps）して出力
        # ※ -y は同名ファイルの上書き許可
        cmd = [
            "ffmpeg", "-y", "-i", temp_wav,
            "-codec:a", "libmp3lame", "-b:a", "64k",
            output_path
        ]
        
        # 実行時のログが邪魔な場合は subprocess.PIPE で隠せます
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"    [エラー] ffmpeg変換失敗: {result.stderr.decode('utf-8', errors='ignore')}")
            return False

        return True
    except Exception as e:
        print(f"    [例外エラー]: {e}")
        return False
    finally:
        # 一時ファイルの掃除
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

def main():
    if not os.path.exists(INPUT_JSON):
        print(f"エラー: {INPUT_JSON} が見つかりません。")
        return

    os.makedirs(AUDIO_DIR, exist_ok=True)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        spots = json.load(f)

    total = len(spots)
    print(f"全 {total} 件のスポットの音声生成（MP3圧縮）を開始します...")
    print(f"保存先: ./{AUDIO_DIR}/")

    success_count = 0
    skip_count = 0

    for idx, spot in enumerate(spots, start=1):
        spot_id = spot.get("id")
        dialogue = spot.get("dialogue", {}).get("kanojo", "")
        
        if not spot_id or not dialogue:
            continue

        raw_filename = spot.get("voice_file", f"{spot_id}.mp3")
        filename = os.path.splitext(raw_filename)[0] + ".mp3"
        output_filepath = os.path.join(AUDIO_DIR, filename)

        if os.path.exists(output_filepath):
            skip_count += 1
            continue

        print(f"[{idx}/{total}] 生成中: {spot.get('name')} -> {filename}")
        print(f"  セリフ: 「{dialogue}」")

        ok = generate_voice_as_mp3(dialogue, SPEAKER_ID, output_filepath)
        if ok:
            success_count += 1
            spot["voice_file"] = filename
        else:
            print(f"  -> 生成失敗")

        time.sleep(0.1)

    with open(INPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

    print("\n==========================================")
    print(f"処理完了！")
    print(f"新規生成 (MP3): {success_count} 件")
    print(f"スキップ（既存）: {skip_count} 件")
    print(f"合計: {success_count + skip_count} / {total} 件")
    print("==========================================")

if __name__ == "__main__":
    main()