import json
import os
import subprocess
import urllib.parse
import urllib.request

OUTPUT_DIR = os.path.join("audio", "kanojo")
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 8  # 春日部つむぎ

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 音声コマンドへの返事（システムボイス）
SYSTEM_VOICES = {
    "sys_mute": "わかった、しばらく静かにしてるね！",
    "sys_resume": "案内を再開するね！",
    "sys_nav_ok": "わかった！ナビを開くね！",
    "sys_nav_err": "まだスポットを案内してないよ！",
    "sys_tired": "運転お疲れさま！無理せずパーキングで休もうね。",
    "sys_thanks": "どういたしまして！まかせて！"
}

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
    print("=== 音声コマンド用 システムボイス生成開始 ===")
    for key, text in SYSTEM_VOICES.items():
        out_path = os.path.join(OUTPUT_DIR, f"{key}.mp3")
        print(f"生成中: {key}.mp3")
        synthesize_mp3(text, out_path)
    print("=== 全6件 生成完了！ ===")

if __name__ == "__main__":
    main()