import os
import requests
import time

VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 8  # 春日部つむぎ
AUDIO_DIR = "audio"

# アプリ内で使われているシステム音声一覧
SYS_VOICES = {
    "sys_start.mp3": "今日も安全運転で楽しく行こうね！",
    "unlock.mp3": "お待たせ！ドライブコンシェルジュ、つむぎだよ！内緒で一緒にドライブ行こ？",
    "sys_nav_ok.mp3": "わかった！ナビを開くね！",
    "sys_nav_err.mp3": "まだスポットを案内してないよ！",
    "sys_mute.mp3": "わかった、しばらく静かにしてるね！"
}

def main():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    print("VOICEVOXでシステム音声を生成します...")

    for filename, text in SYS_VOICES.items():
        audio_path = os.path.join(AUDIO_DIR, filename)
        print(f"生成中: {filename} -> {text}")

        try:
            # 1. 音声クエリ作成
            q_res = requests.post(
                f"{VOICEVOX_URL}/audio_query",
                params={"text": text, "speaker": SPEAKER_ID},
                timeout=10
            )
            if q_res.status_code != 200:
                print(f"  [WARN] クエリ作成失敗: {q_res.status_code}")
                continue

            # 2. 音声合成
            s_res = requests.post(
                f"{VOICEVOX_URL}/synthesis",
                params={"speaker": SPEAKER_ID},
                json=q_res.json(),
                timeout=30
            )
            if s_res.status_code == 200:
                with open(audio_path, "wb") as f_out:
                    f_out.write(s_res.content)
                print(f"  -> 保存完了: {filename}")
            else:
                print(f"  [WARN] 音声合成失敗: {s_res.status_code}")

        except Exception as e:
            print(f"  [ERROR] {e}")

        time.sleep(0.2)

    print("\nシステム音声の生成が完了しました！")

if __name__ == "__main__":
    main()