// Drive Concierge - Main Application Logic (Tsumugi Voice & Speed Radar Integrated)

document.addEventListener('DOMContentLoaded', () => {
    console.log("Drive Concierge initialized.");

    // DOM Elements
    const startBtn = document.getElementById('start-btn');
    const speedDisplay = document.getElementById('speed-display');
    const statusDisplay = document.getElementById('status-display');
    const spotListContainer = document.getElementById('spot-list');

    let watchId = null;
    let currentSpeed = 0;
    let spotsData = [];
    let mediaSpotsData = [];

    // つむぎちゃんボイス（MP3）を再生する核心関数
    function playTsumugiVoice(category, filename) {
        // 例: audio/kanojo/info_spot.mp3 などのパスを構築
        const audioPath = `./audio/${category}/${filename}.mp3`;
        const audio = new Audio(audioPath);
        
        audio.play().then(() => {
            console.log(`音声再生成功: ${audioPath}`);
        }).catch(err => {
            console.warn(`音声再生失敗 (${audioPath}):`, err);
            // フォールバックとしてブラウザ標準音声を使う場合
            fallbackSpeech(filename);
        });
    }

    // 万が一音声ファイルが見つからない場合のブラウザ標準音声フォールバック
    function fallbackSpeech(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ja-JP';
            window.speechSynthesis.speak(utterance);
        }
    }

    // スポットデータの読み込み (JSON)
    async function loadData() {
        try {
            const resSpots = await fetch('./data/spots.json');
            spotsData = await resSpots.json();

            const resMedia = await fetch('./data/media_spots.json');
            mediaSpotsData = await resMedia.json();

            console.log(`スポット読み込み完了: 道の駅 ${spotsData.length}件, メディア ${mediaSpotsData.length}件`);
        } catch (e) {
            console.error("データ読み込みエラー:", e);
        }
    }

    loadData();

    // ドライブ開始ボタンの処理
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            // 音声の初期化（ブラウザのブロック解除用）
            playTsumugiVoice('kanojo', 'welcome'); // 「ドライブを開始します。安全運転で行きましょう！」などの音声ファイル名に対応
            
            if (statusDisplay) statusDisplay.textContent = "GPS測位中...";
            
            // 位置情報の監視スタート
            if ('geolocation' in navigator) {
                watchId = navigator.geolocation.watchPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        // 速度 (m/s を km/h に変換)
                        currentSpeed = position.coords.speed ? position.coords.speed * 3.6 : 0;
                        
                        if (speedDisplay) {
                            speedDisplay.textContent = Math.round(currentSpeed);
                        }
                        if (statusDisplay) {
                            statusDisplay.textContent = `追跡中 (緯度: ${lat.toFixed(4)}, 経度: ${lng.toFixed(4)})`;
                        }

                        // 速度に応じたスポット検索の実行
                        updateNearbySpots(lat, lng, currentSpeed);
                    },
                    (error) => {
                        console.error("GPSエラー:", error);
                        if (statusDisplay) statusDisplay.textContent = "GPS取得エラー: " + error.message;
                    },
                    {
                        enableHighAccuracy: true,
                        maximumAge: 1000,
                        timeout: 5000
                    }
                );
            } else {
                alert("このブラウザは位置情報に対応していません。");
            }
        });
    }

    // 速度に応じた検索範囲の変更とスポット抽出
    function updateNearbySpots(lat, lng, speed) {
        // 速度が早いほど検索半径を広げる（例: 速度(km/h) × 100m など、または固定ロジック）
        let searchRadiusKm = 5; 
        if (speed > 80) {
            searchRadiusKm = 15;
        } else if (speed > 40) {
            searchRadiusKm = 10;
        }

        // ここに距離計算とリスト描画のロジックが入ります
        // 例として簡易的な表示更新
    }
});
