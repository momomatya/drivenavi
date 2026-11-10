// Drive Concierge - Roadster Edition (Fully Integrated with Custom VOICEVOX Assets)

document.addEventListener('DOMContentLoaded', () => {
    console.log("Drive Concierge initialized for Roadster (v5).");

    // DOM Elements Mapping
    const toggleNavBtn = document.getElementById('toggleNavBtn');
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

    // ペルソナ切替ボタン
    const btnPersonaTsure = document.getElementById('btnPersonaTsure');
    const btnPersonaDj = document.getElementById('btnPersonaDj');
    const btnPersonaKanojo = document.getElementById('btnPersonaKanojo');

    let isRunning = false;
    let watchId = null;
    let currentSpeed = 0;
    
    // データ格納用
    let spotsData = [];
    let mediaSpotsData = [];
    let currentNearestSpot = null;
    let announcedSpotId = null; // 同じスポットを連続で何度も喋らないように記憶
    let skippedSpotIds = new Set(); // 「パス」したスポットの一時スキップ用
    let currentPersona = "kanojo"; // 初期値: 彼女

    // 1. 全データ（道の駅＋メディアスポット）の読み込み
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

    // 2. ペルソナ切り替え処理
    function setPersona(persona) {
        currentPersona = persona;
        
        if (btnPersonaTsure) btnPersonaTsure.classList.remove('selected');
        if (btnPersonaDj) btnPersonaDj.classList.remove('selected');
        if (btnPersonaKanojo) btnPersonaKanojo.classList.remove('selected');

        if (persona === 'tsure') {
            if (btnPersonaTsure) btnPersonaTsure.classList.add('selected');
            playVoice('tsure', 'unlock', '「おっ、野郎ドライブだな！安全第一で行くぞ！」');
        } else if (persona === 'dj') {
            if (btnPersonaDj) btnPersonaDj.classList.add('selected');
            playVoice('dj', 'unlock', '「Yo! Drive Conciergeへようこそ。最高のグルーブを届けちゃうぜ！」');
        } else {
            if (btnPersonaKanojo) btnPersonaKanojo.classList.add('selected');
            playVoice('kanojo', 'unlock', '「お待たせ！ドライブコンシェルジュ、つむぎだよ！今日も安全運転で楽しく行こうね！」');
        }
    }

    if (btnPersonaTsure) btnPersonaTsure.addEventListener('click', () => setPersona('tsure'));
    if (btnPersonaDj) btnPersonaDj.addEventListener('click', () => setPersona('dj'));
    if (btnPersonaKanojo) btnPersonaKanojo.addEventListener('click', () => setPersona('kanojo'));

    // 3. 音声再生関数（生成スクリプトの配置 audio/kanojo/{name}.mp3 に完全準拠）
    function playVoice(category, filename, displayMessage = "") {
        const audioPath = `audio/${category}/${filename}.mp3`;
        const audio = new Audio(audioPath);

        if (displayMessage && speechText) {
            speechText.textContent = displayMessage;
        }

        audio.play().then(() => {
            console.log(`音声再生成功: ${audioPath}`);
            if (micStatus) micStatus.textContent = "🔊 発話中...";
        }).catch(err => {
            console.warn(`音声再生失敗 (${audioPath})、フォールバック実行:`, err);
            // ファイルが無い場合のみブラウザ標準音声で読み上げ
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

    // 4. ドライブ開始 / 停止 トグルボタン
    if (toggleNavBtn) {
        toggleNavBtn.addEventListener('click', () => {
            isRunning = !isRunning;

            if (isRunning) {
                toggleNavBtn.textContent = "■ ドライブを終了";
                toggleNavBtn.classList.add('running');
                statusBadge.textContent = "GPS測位中...";
                if (spotName) spotName.textContent = "現在地を測位中...";
                
                // unlock.mp3（起動ボイス）を再生
                playVoice(currentPersona, 'unlock', '「お待たせ！ドライブコンシェルジュ、つむぎだよ！今日も安全運転で楽しく行こうね！」');

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

    // 5. GPS位置情報の監視開始
    function startGeolocation() {
        if (!('geolocation' in navigator)) {
            alert("このブラウザは位置情報に対応していません。");
            return;
        }

        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                currentSpeed = position.coords.speed ? position.coords.speed * 3.6 : 0;

                statusBadge.textContent = "追跡中";
                const roundedSpeed = Math.round(currentSpeed);
                
                // 速度に応じた索敵半径
                let searchRadius = 5.0; // km
                if (currentSpeed >= 80) searchRadius = 20.0;
                else if (currentSpeed >= 50) searchRadius = 10.0;

                if (speedStatus) {
                    speedStatus.textContent = `${roundedSpeed} km/h | 索敵: ${searchRadius.toFixed(1)}km`;
                }

                processNearbySpots(lat, lng, searchRadius);
            },
            (error) => {
                console.error("GPS取得エラー:", error);
                statusBadge.textContent = "GPSエラー";
                if (speechText) speechText.textContent = "GPS信号を探索中... 空の開けた場所でお試しください。";
            },
            {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 15000
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

    // 6. 周辺スポットの計算と案内判定
    function processNearbySpots(lat, lng, radiusKm) {
        const allSpots = [...spotsData, ...mediaSpotsData];
        if (!allSpots || allSpots.length === 0) return;

        let nearest = null;
        let minDistance = 999999;

        for (const spot of allSpots) {
            if (!spot.lat || !spot.lng) continue;
            // パスしたスポットは除外
            if (skippedSpotIds.has(spot.id)) continue;

            const dist = calcDistance(lat, lng, spot.lat, spot.lng);
            if (dist < minDistance) {
                minDistance = dist;
                nearest = spot;
            }
        }

        if (nearest && minDistance <= radiusKm) {
            currentNearestSpot = nearest;
            const distMeters = Math.round(minDistance * 1000);
            
            // 画面反映
            if (spotName) spotName.textContent = nearest.name || "名称不明スポット";
            if (spotDistance) {
                spotDistance.textContent = minDistance < 1 ? `${distMeters}m` : `${minDistance.toFixed(1)}km`;
            }

            // ゲージのアニメーション
            let gaugePercent = Math.max(0, Math.min(100, (1 - (minDistance / radiusKm)) * 100));
            if (gaugeActive) {
                gaugeActive.style.clipPath = `inset(${100 - gaugePercent}% 0 0 0)`;
            }

            // 新しいスポット圏内に入ったら、そのスポット専用のMP3を自動発話！
            if (announcedSpotId !== nearest.id) {
                announcedSpotId = nearest.id;
                announceCurrentSpot(nearest);
            }
        } else {
            currentNearestSpot = null;
            if (spotName) spotName.textContent = "周辺にスポットなし (索敵中)";
            if (spotDistance) spotDistance.textContent = "---";
            if (gaugeActive) gaugeActive.style.clipPath = `inset(100% 0 0 0)`;
        }
    }

    // スポット案内を発話（スポットID.mp3 を再生）
    function announceCurrentSpot(spot) {
        if (!spot) return;
        // dialogue に登録されたセリフ、なければデフォルト文
        const dialogueText = spot.dialogue?.[currentPersona] || spot.dialogue?.kanojo || `「まもなく、${spot.name} です。寄っていきますか？」`;
        
        // 生成スクリプトで作った {spot.id}.mp3 を再生！
        playVoice(currentPersona, spot.id, dialogueText);
    }

    // 距離計算 (Haversine公式)
    function calcDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
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
                // sys_nav_ok.mp3（ナビ起動ボイス）を再生
                playVoice(currentPersona, 'sys_nav_ok', '「わかった！ナビを開くね！」');

                setTimeout(() => {
                    const mapUrl = `https://www.google.com/maps/dir/?api=1&destination=${currentNearestSpot.lat},${currentNearestSpot.lng}`;
                    window.open(mapUrl, '_blank');
                }, 1200);
            } else {
                // sys_nav_err.mp3（エラーボイス）を再生
                playVoice(currentPersona, 'sys_nav_err', '「まだスポットを案内してないよ！」');
            }
        });
    }

    if (btnNo) {
        btnNo.addEventListener('click', () => {
            if (currentNearestSpot) {
                // 現在のスポットを一時スキップリストに入れて次の候補を探す
                skippedSpotIds.add(currentNearestSpot.id);
                currentNearestSpot = null;
                announcedSpotId = null;
            }
            playVoice(currentPersona, 'sys_mute', '「わかった、しばらく静かにしてるね！」');
        });
    }

    if (btnReplay) {
        btnReplay.addEventListener('click', () => {
            if (currentNearestSpot) {
                announceCurrentSpot(currentNearestSpot);
            } else {
                playVoice(currentPersona, 'unlock', '「お待たせ！ドライブコンシェルジュ、つむぎだよ！今日も安全運転で楽しく行こうね！」');
            }
        });
    }
});
