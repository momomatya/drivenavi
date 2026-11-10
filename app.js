// ==========================================
// Drive Concierge - メインスクリプト (UI制御 & 音声Lazy Loading & GPS連携)
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
  console.log("Drive Concierge initialized (External script app.js mode).");

  // --- UI 要素取得 ---
  const toggleNavBtn = document.getElementById('toggleNavBtn');
  const statusBadge = document.getElementById('statusBadge');
  const spotDistance = document.getElementById('spotDistance');
  const gaugeActive = document.getElementById('gaugeActive');
  const spotName = document.getElementById('spotName');
  const speechText = document.getElementById('speechText');
  const btnReplay = document.getElementById('btnReplay');
  const btnYes = document.getElementById('btnYes');
  const btnNo = document.getElementById('btnNo');

  const mainHeader = document.getElementById('mainHeader');
  const appTitle = document.getElementById('appTitle');
  const btnPersonaTsure = document.getElementById('btnPersonaTsure');
  const btnPersonaDj = document.getElementById('btnPersonaDj');
  const btnPersonaKanojo = document.getElementById('btnPersonaKanojo');

  // --- 状態管理 ---
  let isRunning = false;
  let watchId = null;
  let currentSpeed = 0;
  
  let allSpots = [];
  let currentNearestSpot = null;
  let announcedSpotId = null;
  let skippedSpotIds = new Set();
  let currentPersona = "tsure"; 

  // --- iOS Safari / PWA 自動再生制限解除（Autoplay Policy Unlock） ---
  let isAudioUnlocked = false;
  const SILENT_WAV = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA";

  function unlockAudio() {
    if (isAudioUnlocked) return;
    const dummy = new Audio(SILENT_WAV);
    dummy.play().then(() => {
      dummy.pause();
      dummy.currentTime = 0;
      isAudioUnlocked = true;
      console.log("【Audio Unlocked】ブラウザの音声制限を解除しました。");
    }).catch(() => {});
  }

  // 初回タップで音声制限解除
  document.body.addEventListener('touchstart', unlockAudio, { once: true, passive: true });
  document.body.addEventListener('click', unlockAudio, { once: true });

  // --- 1. 全国スポットデータ (places_spots.json) の読み込み ---
  async function loadDatasets() {
    try {
      statusBadge.textContent = "読込中...";
      const res = await fetch('./places_spots.json');
      allSpots = await res.json();
      statusBadge.textContent = `${allSpots.length}件`;
      statusBadge.classList.add('active');
      console.log(`${allSpots.length}件のスポットデータを読み込みました。`);
    } catch (e) {
      console.error("データロードエラー:", e);
      statusBadge.textContent = "読込失敗";
    }
  }
  loadDatasets();

  // --- 2. タイトル5回タップによるシークレット機能解放 ---
  let tapCount = 0;
  let tapTimer = null;

  appTitle.addEventListener('click', () => {
    tapCount++;
    clearTimeout(tapTimer);
    tapTimer = setTimeout(() => { tapCount = 0; }, 2500);

    if (tapCount >= 5) {
      tapCount = 0;
      unlockKanojoSecret();
    }
  });

  function unlockKanojoSecret() {
    if (!mainHeader.classList.contains('secret-unlocked')) {
      mainHeader.classList.add('secret-unlocked');
      setPersona('kanojo', true);
    } else {
      setPersona('kanojo');
    }
  }

  // --- 3. ペルソナ切り替え ---
  function setPersona(persona, isSecretUnlock = false) {
    unlockAudio();
    currentPersona = persona;
    
    btnPersonaTsure.classList.toggle('selected', persona === 'tsure');
    btnPersonaDj.classList.toggle('selected', persona === 'dj');
    btnPersonaKanojo.classList.toggle('selected', persona === 'kanojo');

    if (persona === 'tsure') {
      playVoice('sys_unlock.mp3', '「おっ、野郎ドライブだな！安全第一で行くぞ！」');
    } else if (persona === 'dj') {
      playVoice('sys_unlock.mp3', '「Yo! Drive Conciergeへようこそ。最高のグルーブを届けちゃうぜ！」');
    } else if (persona === 'kanojo') {
      if (isSecretUnlock) {
        playVoice('sys_unlock.mp3', '「【シークレット解除】お待たせ！つむぎだよ！内緒で一緒にドライブ行こ？」');
      } else {
        playVoice('sys_unlock.mp3', '「お待たせ！ドライブコンシェルジュ、つむぎだよ！今日も安全運転で楽しく行こうね！」');
      }
    }
  }

  btnPersonaTsure.addEventListener('click', () => setPersona('tsure'));
  btnPersonaDj.addEventListener('click', () => setPersona('dj'));
  btnPersonaKanojo.addEventListener('click', () => setPersona('kanojo'));

  // --- 4. 音声再生処理（Lazy Loading & ブラウザ音声フォールバック） ---
  function playVoice(voiceFile, displayMessage = "") {
    if (displayMessage) {
      speechText.textContent = displayMessage;
    }

    const audioPath = `./audio/${voiceFile}`;
    const audio = new Audio(audioPath);
    
    audio.play().then(() => {
      console.log(`音声再生成功: ${audioPath}`);
    }).catch(err => {
      console.warn(`音声ファイル再生不可 (${audioPath})、ブラウザ音声でフォールバック:`, err);
      if ('speechSynthesis' in window && displayMessage) {
        window.speechSynthesis.cancel();
        const textToSpeak = displayMessage.replace(/^[「『]|[!！?？]*[」』]$/g, '');
        const uttr = new SpeechSynthesisUtterance(textToSpeak);
        uttr.lang = 'ja-JP';
        window.speechSynthesis.speak(uttr);
      }
    });
  }

  // --- 5. 走行案内スタート / 停止 ---
  toggleNavBtn.addEventListener('click', () => {
    unlockAudio();
    isRunning = !isRunning;

    if (isRunning) {
      toggleNavBtn.textContent = "走行案内を停止";
      toggleNavBtn.classList.add('running');
      statusBadge.textContent = "追従中";
      spotName.textContent = "現在地を測位中...";
      
      if (currentPersona === 'kanojo') {
        playVoice('sys_unlock.mp3', '「今日も安全運転で楽しく行こうね！」');
      } else if (currentPersona === 'dj') {
        playVoice('sys_unlock.mp3', '「ナビゲーション・スタート！グッドバイブスで行こう！」');
      } else {
        playVoice('sys_unlock.mp3', '「よし、出発だな！飛ばしすぎんなよー！」');
      }

      startGeolocation();
    } else {
      stopGeolocation();
      toggleNavBtn.textContent = "走行案内をスタート";
      toggleNavBtn.classList.remove('running');
      statusBadge.textContent = `${allSpots.length}件`;
      speechText.textContent = "走行案内を一時停止しました。";
      spotName.textContent = "待機中";
    }
  });

  // --- 6. GPSトラッキング ---
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
        
        // 巡航速度に応じた検索半径（高速巡航時は探索範囲を拡張）
        let searchRadius = currentSpeed >= 80 ? 25.0 : (currentSpeed >= 50 ? 15.0 : 10.0);
        processNearbySpots(lat, lng, searchRadius);
      },
      (error) => {
        console.error("GPSエラー:", error);
        statusBadge.textContent = "GPSエラー";
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 }
    );
  }

  function stopGeolocation() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
  }

  // --- 7. 周辺スポット探索 & 接近判定 ---
  function processNearbySpots(lat, lng, radiusKm) {
    if (!allSpots || allSpots.length === 0) return;

    let nearest = null;
    let minDistance = 999999;

    for (const spot of allSpots) {
      if (!spot.lat || !spot.lng || skippedSpotIds.has(spot.id)) continue;
      const dist = calcDistance(lat, lng, spot.lat, spot.lng);
      if (dist < minDistance) {
        minDistance = dist;
        nearest = spot;
      }
    }

    if (nearest && minDistance <= radiusKm) {
      currentNearestSpot = nearest;
      const distMeters = Math.round(minDistance * 1000);
      
      spotName.textContent = nearest.name || "名称不明スポット";
      spotDistance.textContent = minDistance < 1 ? `${distMeters}m` : `${minDistance.toFixed(1)}km`;

      // メーターゲージ更新
      let gaugePercent = Math.max(0, Math.min(100, (1 - (minDistance / radiusKm)) * 100));
      if (gaugeActive) gaugeActive.style.clipPath = `inset(${100 - gaugePercent}% 0 0 0)`;

      // 新しいスポットに接近したら音声アナウンス
      if (announcedSpotId !== nearest.id) {
        announcedSpotId = nearest.id;
        announceCurrentSpot(nearest);
      }
    } else {
      currentNearestSpot = null;
      spotName.textContent = "周辺にスポットなし";
      spotDistance.textContent = "---";
      if (gaugeActive) gaugeActive.style.clipPath = `inset(100% 0 0 0)`;
    }
  }

  function announceCurrentSpot(spot) {
    if (!spot) return;
    const dialogueText = spot.dialogue?.[currentPersona] || spot.dialogue?.kanojo || `「まもなく、${spot.name} です。寄っていきますか？」`;
    const voiceFile = spot.voice_file || `${spot.id}.mp3`;
    playVoice(voiceFile, dialogueText);
  }

  // ハバサイン公式による距離計算 (km)
  function calcDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  // --- 8. アクションボタン ---
  btnYes.addEventListener('click', () => {
    unlockAudio();
    if (currentNearestSpot && currentNearestSpot.lat && currentNearestSpot.lng) {
      playVoice('sys_nav_ok.mp3', '「わかった！ナビを開くね！」');
      setTimeout(() => {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${currentNearestSpot.lat},${currentNearestSpot.lng}`, '_blank');
      }, 1200);
    } else {
      playVoice('sys_nav_err.mp3', '「まだスポットを案内してないよ！」');
    }
  });

  btnNo.addEventListener('click', () => {
    unlockAudio();
    if (currentNearestSpot) {
      skippedSpotIds.add(currentNearestSpot.id); 
      currentNearestSpot = null; 
      announcedSpotId = null;
    }
    playVoice('sys_mute.mp3', '「わかった、しばらく静かにしてるね！」');
  });

  btnReplay.addEventListener('click', () => {
    unlockAudio();
    if (currentNearestSpot) { 
      announceCurrentSpot(currentNearestSpot); 
    } else { 
      playVoice('sys_unlock.mp3', '「今日も安全運転で楽しく行こうね！」'); 
    }
  });
});
