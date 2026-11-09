// Drive Concierge - Roadster Edition (Full Integrated Logic & GPS Fixed)

document.addEventListener('DOMContentLoaded', () => {
    console.log("Drive Concierge initialized for Roadster.");

    // DOM Elements Mapping (HTML側のIDと完全一致)
    const toggleNavBtn = document.getElementById('toggleNavBtn');
    const modeToggleBtn = document.getElementById('modeToggleBtn');
    const statusBadge = document.getElementById('statusBadge');
    const spotDistance = document.getElementById('spotDistance');
    const gaugeActive = document.getElementById('gaugeActive');
    const spotName = document.getElementById('spotName');
    const speechText = document.getElementById('speechText');
    const micStatus = document.getElementById('micStatus');
    const speedStatus = document.getElementById('speedStatus');
    const btnReplay = document.getElementById('btnReplay');
    const btnYes = document.getElementById('btnYes');
    const btnNo = document.getElementById('btnNo');

    let isRunning = false;
    let watchId = null;
    let currentSpeed = 0;
    
    // データ格納用
    let spotsData = [];
    let mediaSpotsData = [];
    let currentNearestSpot = null;
    let currentMode = "通常"; // 通常 / メディア特化 など

    // 1. 全データ（道の駅 1200件＋メディアスポット）の読み込み
    async function loadDatasets() {
        try {
            statusBadge.textContent = "読込中...";
            const [resSpots, resMedia] = await Promise.all([
                fetch('./data/spots.json'),
                fetch('./data/media_spots.json')
            ]);
            
            spotsData = await resSpots.json();
            mediaSpotsData = await resMedia.json();

            const total = spotsData.length + mediaSpotsData.length;
            console.log(`データロード成功: 道の駅 ${spotsData.length}件, メディア ${mediaSpotsData.length}件 (計: ${total}件)`);
            
            statusBadge.textContent = "待機中";
            statusBadge.classList.add('active');
            spotName.textContent = `待機中 (全 ${total} 件連携)`;
        } catch (e) {
            console.error("データ読み込みエラー:", e);
            statusBadge.textContent = "読込失敗";
            spotName.textContent = "データ読込エラー";
        }
    }

    loadDatasets();

    // 2. つむぎちゃんボイス（MP3）の再生関数
    function playTsumugiVoice(category, filename, displayMessage = "") {
        const audioPath = `./audio/${category}/${filename}.mp3`;
        const audio = new Audio(audioPath);

        if (displayMessage && speechText) {
            speechText.textContent = displayMessage;
        }

        audio.play().then(() => {
            console.log(`音声再生成功: ${audioPath}`);
            if (micStatus) micStatus.textContent = "🔊 発話中...";
        }).catch(err => {
            console.warn(`音声ファイル再生失敗 (${audioPath})、フォールバック実行:`, err);
            // フォールバック（ブラウザ標準音声）
            if ('speechSynthesis' in window && displayMessage) {
                const uttr = new SpeechSynthesisUtterance(displayMessage);
                uttr.lang = 'ja-JP';
                window.speechSynthesis.speak(uttr);
            }
        });

        audio.onended = () => {
            if (micStatus) micStatus.textContent = "🎤 音声スタンバイ";
        };
    }

    // 3. モード切替ボタンの処理
    if (modeToggleBtn) {
        modeToggleBtn.addEventListener('click', () => {
            if (currentMode === "通常") {
                currentMode = "メディア";
                modeToggleBtn.textContent = "MODE: メディア";
                modeToggleBtn.style.color = "#00ffcc";
            } else {
                currentMode = "通常";
                modeToggleBtn.textContent = "MODE: 通常";
                modeToggleBtn.style.color = "#5588aa";
            }
            console.log("モード切替:", currentMode);
        });
    }

    // 4. ドライブ開始 / 停止 トグルボタン
    if (toggleNavBtn) {
        toggleNavBtn.addEventListener('click', () => {
            isRunning = !isRunning;

            if (isRunning) {
                toggleNavBtn.textContent = "■ ドライブを終了";
                toggleNavBtn.classList.add('running');
                statusBadge.textContent = "GPS測位中...";
                if (spotName) spotName.textContent = "現在地を測位中...";
                
                playTsumugiVoice('kanojo', 'welcome', '「ドライブを開始します。安全運転で行きましょう！」');

                startGeolocation();
            } else {
                stopGeolocation();
                toggleNavBtn.textContent = "▶ ドライブを開始";
                toggleNavBtn.classList.remove('running');
                statusBadge.textContent = "待機中";
                if (speechText) speechText.textContent = "ドライブを一時停止しました。";
                if (spotName) spotName.textContent = "一時停止中";
            }
        });
    }

    // 5. GPS位置情報の監視開始（スマホ向け高精度化＆初回誤作動防止）
    function startGeolocation() {
        if (!('geolocation' in navigator)) {
            alert("このブラウザは位置情報に対応していません。");
            return;
        }

        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                currentSpeed = position.coords.speed ? position.coords.speed * 3.6 : 0; // km/h変換

                statusBadge.textContent = "追跡中";

                // スピード表示の更新
                const roundedSpeed = Math.round(currentSpeed);
                
                // 速度に応じた索敵半径の動的変更
                let searchRadius = 5.0; // km
                if (currentSpeed >= 80) searchRadius = 20.0;
                else if (currentSpeed >= 50) searchRadius = 10.0;

                if (speedStatus) {
                    speedStatus.textContent = `${roundedSpeed} km/h | 索敵: ${searchRadius.toFixed(1)}km`;
                }

                // 周辺スポットの検索と最寄りの抽出
                processNearbySpots(lat, lng, searchRadius);
            },
            (error) => {
                console.error("GPS取得エラー:", error);
                statusBadge.textContent = "GPSエラー";
                if (speechText) speechText.textContent = "GPS信号を探索中... 空の見晴らしの良い場所でお試しください。";
            },
            {
                enableHighAccuracy: true, // スマホのGPSを高精度モードに
                maximumAge: 0,            // キャッシュされた古い位置情報を使わない
                timeout: 15000            // タイムアウトを15秒に設定
            }
        );
    }

    function stopGeolocation() {
        if (watchId !== null) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }
        if (speedStatus) speedStatus.textContent = "0 km/h | 索敵: 5.0km";
    }

    // 6. 周辺スポットの計算と最寄り抽出
    function processNearbySpots(lat, lng, radiusKm) {
        // 現在のモードに応じてデータソースを選択
        let targetData = spotsData;
        if (currentMode === "メディア" && mediaSpotsData.length > 0) {
            targetData = mediaSpotsData;
        }

        if (!targetData || targetData.length === 0) return;

        let nearest = null;
        let minDistance = 999999; // km

        for (const spot of targetData) {
            if (!spot.lat || !spot.lng) continue;
            const dist = calcDistance(lat, lng, spot.lat, spot.lng);
            if (dist < minDistance) {
                minDistance = dist;
                nearest = spot;
            }
        }

        // ちゃんと計算できた場合のみ表示（変な初期値や遠すぎる場所を弾く）
        if (nearest && minDistance <= radiusKm) {
            currentNearestSpot = nearest;
            const distMeters = Math.round(minDistance * 1000);
            
            // 画面反映
            if (spotName) spotName.textContent = nearest.name || "名称不明スポット";
            if (spotDistance) {
                spotDistance.textContent = minDistance < 1 ? `${distMeters}m` : `${minDistance.toFixed(1)}km`;
            }

            // ゲージのアニメーション制御
            let gaugePercent = Math.max(0, Math.min(100, (1 - (minDistance / radiusKm)) * 100));
            if (gaugeActive) {
                gaugeActive.style.clipPath = `inset(${100 - gaugePercent}% 0 0 0)`;
            }
        } else {
            currentNearestSpot = null;
            if (spotName) spotName.textContent = "周辺にスポットなし (索敵中)";
            if (spotDistance) spotDistance.textContent = "---";
            if (gaugeActive) gaugeActive.style.clipPath = `inset(100% 0 0 0)`;
        }
    }

    // 2点間の距離計算 (Haversine公式)
    function calcDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // 地球の半径 (km)
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
            Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    // 7. アクションボタンのイベント
    if (btnYes) {
        btnYes.addEventListener('click', () => {
            if (currentNearestSpot && currentNearestSpot.lat && currentNearestSpot.lng) {
                // Google Mapsの経路案内を開く
                const mapUrl = `https://www.google.com/maps/dir/?api=1&destination=${currentNearestSpot.lat},${currentNearestSpot.lng}`;
                window.open(mapUrl, '_blank');
            } else {
                alert("現在案内中のスポットがありません。");
            }
        });
    }

    if (btnNo) {
        btnNo.addEventListener('click', () => {
            playTsumugiVoice('kanojo', 'next', '「了解しました。次のスポットを探しますね」');
        });
    }

    if (btnReplay) {
        btnReplay.addEventListener('click', () => {
            if (currentNearestSpot) {
                playTsumugiVoice('kanojo', 'spot_info', `「まもなく、${currentNearestSpot.name} です。寄っていきますか？」`);
            } else {
                playTsumugiVoice('kanojo', 'welcome', '「システム正常稼働中。安全運転で行きましょう！」');
            }
        });
    }
});
