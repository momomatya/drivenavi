// ==========================================
// Drive Concierge - メインスクリプト (音声Lazy Loading & GPS連携版)
// ==========================================

let spots = [];
let watchId = null;
let audioUnlocked = false;
const TRIGGER_DISTANCE_KM = 2.0; // 音声を鳴らす接近距離のしきい値（キロメートル）

// 1. 初期化処理（JSONの読み込みとロック解除イベントの登録）
document.addEventListener('DOMContentLoaded', async () => {
    // 起動時は軽量なJSONテキストデータのみを読み込む（音声はまだ読み込まない）
    try {
        const response = await fetch('./places_spots.json');
        spots = await response.json();
        console.log(`${spots.length}件のスポットデータを読み込みました。`);
    } catch (error) {
        console.error("スポットデータの読み込みに失敗しました:", error);
    }

    // 画面のどこかをタップした時に音声のロックを解除する（iOS/Safari対策）
    document.body.addEventListener('click', unlockAudio, { once: true });
    document.body.addEventListener('touchstart', unlockAudio, { once: true });
    
    // UI上の「ドライブ開始」ボタンがある想定（HTMLのボタンIDに合わせて変更してください）
    const startBtn = document.getElementById('start-btn');
    if(startBtn) {
        startBtn.addEventListener('click', startTracking);
    } else {
        // ボタンがない場合は自動でトラッキングを開始
        startTracking();
    }
});

// 2. iOS/Safari等の自動再生ブロックを解除する処理
function unlockAudio() {
    if (audioUnlocked) return;
    const silentAudio = new Audio();
    // 無音を一度再生してブラウザにオーディオ権限を認識させる
    silentAudio.play().then(() => {
        silentAudio.pause();
        audioUnlocked = true;
        console.log("音声再生のロックを解除しました（走行中の自動再生が可能になります）。");
    }).catch(err => console.log("ロック解除処理をスキップしました:", err));
}

// 3. GPSトラッキングの開始
function startTracking() {
    if (!navigator.geolocation) {
        alert("お使いの端末はGPSをサポートしていません。");
        return;
    }

    console.log("現在地の取得を開始します...");
    
    // watchPositionで現在地を継続的に監視する
    watchId = navigator.geolocation.watchPosition(
        checkProximity,
        (error) => console.error("GPSエラー:", error),
        { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
    );
}

// 4. 現在地とスポットの距離を計算して接近判定
function checkProximity(position) {
    const currentLat = position.coords.latitude;
    const currentLng = position.coords.longitude;

    spots.forEach(spot => {
        // すでに再生済みのスポットは無視する（重複再生防止）
        if (spot.isPlayed) return;

        const distance = calculateDistance(currentLat, currentLng, spot.lat, spot.lng);

        // 2km圏内に入ったスポットを検知
        if (distance <= TRIGGER_DISTANCE_KM) {
            playSpotVoice(spot);
        }
    });
}

// 5. 音声の動的読み込みと再生（Lazy Loading本体）
function playSpotVoice(spot) {
    // 1回のドライブで同じスポットの音声が何度も鳴らないようにフラグを立てる
    spot.isPlayed = true;
    
    // この関数が呼ばれたタイミングで初めてMP3ファイルのパスを指定しフェッチする
    const audioPath = `./audio/${spot.voice_file}`;
    const audio = new Audio(audioPath);
    
    console.log(`【再生実行】${spot.name} まで約2kmです。`);
    
    audio.play().catch(error => {
        console.error(`音声再生エラー (${spot.name}):`, error);
        // ロック解除前に圏内に入ってしまいエラーになった場合は未再生に戻す
        spot.isPlayed = false; 
    });
}

// --- 補助関数: 2点間の緯度経度から距離を計算（ハバサイン公式） ---
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // 地球の半径 (km)
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c; // キロメートル単位で返す
}