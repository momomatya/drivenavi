import json
import os
import subprocess
import urllib.parse
import urllib.request

OUTPUT_DIR = os.path.join("audio", "kanojo")
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 8  # 春日部つむぎ

os.makedirs(OUTPUT_DIR, exist_ok=True)

MEDIA_VOICES = {
    "sweets_01": "ねぇねぇ！この近くに今話題のスイーツがあるらしいよ！ちょっと甘いもの補給していかない？",
    "sweets_02": "見て見て！すっごく美味しそうなスイーツのお店見つけた！寄り道しちゃお？",
    "cafe_01": "ねぇ、近くにおしゃれなカフェがあるみたい！美味しいコーヒー飲んで一息つこ？",
    "cafe_02": "運転お疲れさま〜！このあたりに落ち着くカフェがあるよ、ちょっと休憩する？",
    "scenic_01": "わぁ、見て！この先、すごく景色が綺麗なスポットなんだって！車停めて写真撮っていこ？",
    "scenic_02": "絶景ポイントが近いよ〜！せっかくだから綺麗な景色、目に焼き付けていこうよ！"
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
    print("=== スイーツ・カフェ・絶景用ボイス生成開始 ===")
    for key, text in MEDIA_VOICES.items():
        out_path = os.path.join(OUTPUT_DIR, f"{key}.mp3")
        print(f"生成中: {key}.mp3")
        synthesize_mp3(text, out_path)
    print("=== 全6件 生成完了！ ===")

if __name__ == "__main__":
    main()