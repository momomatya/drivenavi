import json
import os
import requests
import time

VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 3  # 春日部つむぎ
AUDIO_DIR = "audio"
JSON_FILE = "places_spots.json"

def main():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        spots = json.load(f)

    print(f"JSON内の総スポット数: {len(spots)} 件")
    
    missing_spots = []
    for spot in spots:
        voice_file = spot.get("voice_file")
        if not voice_file:
            continue
        audio_path = os.path.join(AUDIO_DIR, voice_file)
        if not os.path.exists(audio_path):
            missing_spots.append(spot)

    print(f"未作成の音声ファイル（生成対象）: {len(missing_spots)} 件")

    if len(missing_spots) == 0:
        print("すべての音声ファイルが既に存在しています！")
        return

    # VOICEVOXの稼働確認
    try:
        res = requests.get(f"{VOICEVOX_URL}/version", timeout=3)
        if res.status_code != 200:
            print("【エラー】VOICEVOXが起動していません。アプリを起動してください。")
            return
    except Exception:
        print("【エラー】VOICEVOXに接続できません。アプリを起動してください。")
        return

    generated_count = 0
    for idx, spot in enumerate(missing_spots):
        voice_file = spot.get("voice_file")
        audio_path = os.path.join(AUDIO_DIR, voice_file)
        
        # 彼女モードのセリフを優先
        dialogue = spot.get("dialogue", {})
        text = dialogue.get("kanojo", "") or dialogue.get("tsure", "") or spot.get("name", "")
        text = text.replace("「", "").replace("」", "").strip()

        # 修正箇所: {len(missing_spots)}] に変更済み
        print(f"[{idx+1}/{len(missing_spots)}] 生成中: {spot.get('name')} -> {text}")

        try:
            # 1. audio_query
            q_res = requests.post(f"{VOICEVOX_URL}/audio_query", params={"text": text, "speaker": SPEAKER_ID}, timeout=10)
            if q_res.status_code != 200:
                print(f"  [WARN] クエリ作成失敗: {q_res.status_code}")
                continue
            query_data = q_res.json()

            # 2. synthesis
            s_res = requests.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": SPEAKER_ID}, json=query_data, timeout=30)
            if s_res.status_code == 200:
                with open(audio_path, "wb") as f_out:
                    f_out.write(s_res.content)
                generated_count += 1
            else:
                print(f"  [WARN] 音声合成失敗: {s_res.status_code}")
        except Exception as e:
            print(f"  [ERROR] エラー: {e}")

        time.sleep(0.2)

    print("\n==========================================")
    print(f"処理完了！ 新規生成: {generated_count} 件")
    print("==========================================")

if __name__ == "__main__":
    main()