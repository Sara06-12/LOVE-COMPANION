import http.server
import socketserver
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
import threading

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = int(os.environ.get("PORT", 8080))

rooms = {}
rooms_lock = threading.Lock()
room_subscribers = {}
subscribers_lock = threading.Lock()

def create_default_state(code):
    return {
        "code": code,
        # Alarm state for Partner A (e.g. Spain)
        "alarmA": {
            "isRinging": False,
            "time": None,           # "HH:MM"
            "timezone": "Europe/Madrid",
            "enabled": False,
            "message": "Time to wake up my love! ❤️",
            "tone": "romantic_chime"
        },
        # Alarm state for Partner B (e.g. India)
        "alarmB": {
            "isRinging": False,
            "time": None,           # "HH:MM"
            "timezone": "Asia/Kolkata",
            "enabled": False,
            "message": "Good morning handsome! Wake up ❤️",
            "tone": "romantic_chime"
        },
        "music": {
            "isPlaying": False,
            "trackId": "piano_romance",
            "trackTitle": "🌙 Moonlight Romance Piano",
            "voiceAudio": None,
            "target": "all"
        },
        "moodLamp": {
            "color": "#ff4081",
            "name": "Romantic Rose"
        },
        "loveNote": {
            "text": "Thinking of you across the miles ❤️",
            "sentBy": "Spain Partner",
            "timestamp": time.time()
        },
        "heartbeat": {
            "pulseId": 0,
            "sentBy": "Partner",
            "timestamp": time.time()
        },
        "pokeA": 0, # Pokes sent from A to B
        "pokeB": 0, # Pokes sent from B to A
        "partnerAName": "Girlfriend (Spain 🇪🇸)",
        "partnerBName": "Boyfriend (India 🇮🇳)",
        "lastAction": f"Paired to Room {code}",
        "lastActionTime": time.time()
    }

def get_room_state(code):
    code = (code or "LOVE-99").strip().upper()
    with rooms_lock:
        if code not in rooms:
            rooms[code] = create_default_state(code)
        return rooms[code]

def broadcast_room_state(code):
    code = (code or "LOVE-99").strip().upper()
    state = get_room_state(code)
    data = f"data: {json.dumps(state)}\n\n".encode('utf-8')

    with subscribers_lock:
        subs = room_subscribers.get(code, [])
        dead = []
        for wfile in subs:
            try:
                wfile.write(data)
                wfile.flush()
            except Exception:
                dead.append(wfile)
        for d in dead:
            if d in subs:
                subs.remove(d)
        room_subscribers[code] = subs

def check_all_rooms_scheduler():
    # Handled via UTC/Timezone triggers from clients or server clock
    while True:
        try:
            now_utc = datetime.utcnow()
            with rooms_lock:
                room_keys = list(rooms.keys())
            for code in room_keys:
                state = get_room_state(code)
                # Check scheduled alarms
                # (Client sync handles exact local minute triggers)
            time.sleep(2)
        except Exception:
            time.sleep(2)

scheduler_thread = threading.Thread(target=check_all_rooms_scheduler, daemon=True)
scheduler_thread.start()

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="bgGrad" cx="50%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#2a164d"/>
      <stop offset="100%" stop-color="#0b0a14"/>
    </radialGradient>
    <linearGradient id="heartGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff758c"/>
      <stop offset="50%" stop-color="#ff4081"/>
      <stop offset="100%" stop-color="#d81b60"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="128" fill="url(#bgGrad)"/>
  <circle cx="256" cy="256" r="210" fill="none" stroke="#ff4081" stroke-width="6" opacity="0.3"/>
  <path d="M256 420 C256 420, 96 320, 96 200 C96 130, 150 86, 216 86 C246 86, 276 100, 256 126 C236 100, 266 86, 296 86 C362 86, 416 130, 416 200 C416 320, 256 420, 256 420 Z" fill="url(#heartGrad)"/>
</svg>"""

MANIFEST_JSON = json.dumps({
  "name": "Love Companion",
  "short_name": "LoveSync",
  "description": "Long-distance companion with dual timezones, remote music, mood lamp, heartbeat hugs, and partner-locked alarm.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0b0a14",
  "theme_color": "#ff4081",
  "orientation": "portrait-primary",
  "icons": [{"src": "/icon.svg", "sizes": "192x192 512x512", "type": "image/svg+xml"}]
})

SW_JS = """self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
self.addEventListener('fetch', e => { if (e.request.url.includes('/api/')) return; e.respondWith(fetch(e.request).catch(() => caches.match(e.request))); });"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>Love Companion ❤️ Spain & India</title>
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#ff4081">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <style>
    :root {
      --bg-primary: #0b0a14;
      --bg-secondary: #161426;
      --card-bg: rgba(26, 23, 44, 0.85);
      --card-border: rgba(255, 105, 180, 0.2);
      --accent-pink: #ff4081;
      --accent-rose: #ff758c;
      --accent-cyan: #00e5ff;
      --text-main: #ffffff;
      --text-muted: #a09cb0;
      --gold-glow: #ffd54f;
      --danger-red: #ff1744;
      --success-green: #00e676;
      --lamp-color: #ff4081;
      --lamp-glow: rgba(255, 64, 129, 0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
    body { background: radial-gradient(circle at 50% 15%, #25183e 0%, var(--bg-primary) 85%); color: var(--text-main); min-height: 100vh; padding-bottom: 60px; transition: background 0.5s ease; overflow-x: hidden; }
    header { text-align: center; padding: 14px 16px 6px; }
    .top-bar { display: flex; align-items: center; justify-content: space-between; max-width: 980px; margin: 0 auto 10px; padding: 0 8px; }
    .pairing-badge { background: rgba(255, 64, 129, 0.15); border: 1px solid var(--lamp-color); color: #fff; padding: 6px 14px; border-radius: 100px; font-size: 0.82rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 6px; }
    .role-selector { display: flex; justify-content: center; gap: 8px; margin: 10px auto; max-width: 500px; padding: 0 16px; }
    .role-btn { flex: 1; background: var(--bg-secondary); color: var(--text-muted); border: 1px solid rgba(255, 255, 255, 0.15); padding: 10px; border-radius: 14px; cursor: pointer; font-size: 0.9rem; font-weight: 700; transition: all 0.2s; }
    .role-btn.active { background: linear-gradient(135deg, rgba(255, 64, 129, 0.3), rgba(255, 117, 140, 0.2)); border-color: var(--lamp-color); color: #fff; box-shadow: 0 0 14px var(--lamp-glow); }
    
    /* Dual Timezone Clock Bar */
    .dual-clocks { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; max-width: 980px; margin: 0 auto 16px; padding: 0 16px; }
    .tz-card { background: rgba(18, 15, 33, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 18px; padding: 14px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
    .tz-card.me { border-color: var(--accent-cyan); box-shadow: 0 0 16px rgba(0, 229, 255, 0.25); }
    .tz-card.partner { border-color: var(--accent-pink); box-shadow: 0 0 16px var(--lamp-glow); }
    .tz-label { font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; justify-content: center; gap: 6px; }
    .tz-time { font-family: 'Courier New', monospace; font-size: 2.2rem; font-weight: 900; color: #fff; letter-spacing: 1px; }
    .tz-date { font-size: 0.75rem; color: #a5a0b8; margin-top: 2px; }

    .container { max-width: 980px; margin: 0 auto; padding: 0 16px; }
    .card { background: var(--card-bg); backdrop-filter: blur(16px); border: 1px solid var(--card-border); border-radius: 24px; padding: 22px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4); margin-bottom: 16px; }
    .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 10px; }
    .card-title { font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }

    /* Ringing Screen */
    .ringing-box { background: linear-gradient(135deg, rgba(255, 23, 68, 0.35), rgba(255, 64, 129, 0.45)); border: 2px solid var(--danger-red); border-radius: 20px; padding: 22px; text-align: center; animation: pulse 1s infinite; margin-bottom: 16px; }
    .ringing-title { font-size: 1.4rem; font-weight: 900; color: #fff; margin-bottom: 8px; }

    .feature-block { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 18px; padding: 15px; margin-bottom: 14px; }
    .feature-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; color: #f1f0f7; }

    /* Desk Clock Display */
    .desk-clock { background: #05040a; border-radius: 22px; padding: 20px 16px; text-align: center; border: 2px solid var(--lamp-color); box-shadow: 0 0 35px var(--lamp-glow); transition: all 0.4s ease; margin-bottom: 14px; }
    .desk-clock.ringing { border-color: var(--danger-red); animation: shake 0.5s infinite; }
    @keyframes shake { 0%, 100% { transform: translate(1px, 1px); } 50% { transform: translate(-2px, -1px); } }

    .equalizer { display: flex; align-items: flex-end; gap: 2px; height: 12px; }
    .eq-bar { width: 3px; background: var(--accent-cyan); border-radius: 2px; animation: equalize 1s infinite alternate; }
    .eq-bar:nth-child(1) { height: 60%; } .eq-bar:nth-child(2) { height: 100%; animation-delay: 0.2s; } .eq-bar:nth-child(3) { height: 40%; animation-delay: 0.4s; }
    @keyframes equalize { 0% { height: 20%; } 100% { height: 100%; } }

    .color-chips { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
    .chip { width: 32px; height: 32px; border-radius: 50%; cursor: pointer; border: 2px solid rgba(255, 255, 255, 0.3); }
    .btn { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 0.95rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; border: none; transition: transform 0.15s; }
    .btn:active { transform: scale(0.98); }
    .btn-primary { background: linear-gradient(135deg, #ff4081, #ff758c); color: #fff; box-shadow: 0 4px 16px rgba(255, 64, 129, 0.35); }
    .btn-music { background: linear-gradient(135deg, #00b0ff, #00e5ff); color: #000; font-weight: 800; }
    .btn-hug { background: linear-gradient(135deg, #ff758c, #ff4081); color: #fff; }
    .btn-danger-glow { background: linear-gradient(135deg, #ff1744, #ff5252); color: #fff; font-size: 1.15rem; padding: 16px; box-shadow: 0 0 30px rgba(255, 23, 68, 0.7); animation: pulse 1s infinite; }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: #fff; border: 1px solid rgba(255, 255, 255, 0.15); margin-top: 8px; }
    .btn-poke { background: rgba(255, 215, 0, 0.15); border: 1px solid var(--gold-glow); color: #fff; margin-top: 8px; }
    .heart-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; opacity: 0; transition: opacity 0.3s; background: radial-gradient(circle, rgba(255, 64, 129, 0.45) 0%, rgba(0,0,0,0) 70%); }
    .heart-overlay.active { opacity: 1; }
    .heart-overlay-icon { font-size: 5rem; animation: pulse 0.7s infinite; }
    .modal-backdrop { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.8); z-index: 10000; display: none; align-items: center; justify-content: center; padding: 16px; }
    .modal-backdrop.open { display: flex; }
    .modal-content { background: #18152b; border: 1px solid var(--lamp-color); border-radius: 24px; padding: 22px; max-width: 420px; width: 100%; text-align: center; }
    input[type="time"], input[type="text"], select { width: 100%; background: rgba(10, 8, 20, 0.8); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; padding: 10px 12px; border-radius: 12px; font-size: 0.95rem; outline: none; margin-bottom: 8px; }
  </style>
</head>
<body>

  <div id="heartOverlay" class="heart-overlay">
    <div class="heart-overlay-icon">💖</div>
    <div id="heartSenderText" style="font-size: 1.3rem; font-weight: 800; color: #fff; margin-top: 10px;">Warm Hug Received!</div>
  </div>

  <div id="pairingModal" class="modal-backdrop">
    <div class="modal-content">
      <div style="font-size: 2.5rem; margin-bottom: 6px;">🔐</div>
      <h2>Couple Pairing Code</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin: 8px 0 14px;">Share this code with your partner so both phones connect privately!</p>
      <div id="modalCodeDisplay" style="font-family: monospace; font-size: 2rem; font-weight: 900; background: rgba(255,255,255,0.08); border: 2px dashed var(--lamp-color); padding: 10px; border-radius: 14px; letter-spacing: 3px; color: #fff; margin-bottom: 14px;">LOVE-99</div>
      <input type="text" id="customRoomInput" placeholder="Enter Room Code" style="text-transform: uppercase; font-weight: 700; text-align: center;">
      <button type="button" class="btn btn-primary" onclick="handleSaveRoomCode()">💖 Connect & Save</button>
      <button type="button" class="btn btn-secondary" onclick="closePairingModal()">Cancel</button>
    </div>
  </div>

  <header>
    <div class="top-bar">
      <div class="pairing-badge" onclick="openPairingModal()">
        <span>🔐 Room:</span>
        <span id="activeRoomCodeDisplay" style="color: var(--accent-pink);">LOVE-99</span>
        <span>✏️</span>
      </div>
      <div style="font-size: 0.85rem; color: var(--accent-cyan);">🌍 Spain 🇪🇸 $\leftrightarrow$ India 🇮🇳</div>
    </div>
    <h1 style="font-size: 1.8rem; background: linear-gradient(45deg, #ff758c, #ff4081); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Love Companion</h1>
  </header>

  <!-- Role Picker -->
  <div class="role-selector">
    <button id="roleBtnA" class="role-btn active" onclick="setMyRole('A')">🇪🇸 I am in Spain (Girlfriend)</button>
    <button id="roleBtnB" class="role-btn" onclick="setMyRole('B')">🇮🇳 I am in India (Boyfriend)</button>
  </div>

  <!-- Dual Timezone Clocks -->
  <div class="dual-clocks">
    <div id="tzCardA" class="tz-card me">
      <div class="tz-label">🇪🇸 Spain (Europe/Madrid)</div>
      <div id="tzTimeA" class="tz-time">--:--:--</div>
      <div id="tzDateA" class="tz-date">Loading...</div>
    </div>
    <div id="tzCardB" class="tz-card partner">
      <div class="tz-label">🇮🇳 India (Asia/Kolkata)</div>
      <div id="tzTimeB" class="tz-time">--:--:--</div>
      <div id="tzDateB" class="tz-date">Loading...</div>
    </div>
  </div>

  <div class="container">
    
    <!-- MY ACTIVE RINGING ALARM (LOCKED - NO TURN OFF BUTTON FOR ME!) -->
    <div id="myRingingBox" class="ringing-box" style="display: none;">
      <div style="font-size: 3rem;">⏰🚨</div>
      <div class="ringing-title">YOUR ALARM IS RINGING!</div>
      <p id="myAlarmMsg" style="color: #fff; font-size: 0.95rem; margin-bottom: 12px;">"Wake up my love!"</p>
      <div style="background: rgba(0,0,0,0.4); padding: 10px; border-radius: 12px; font-size: 0.85rem; color: #ffe082;">
        🔒 <b>LOCKED:</b> You cannot turn off your own alarm!<br>Waiting for your partner to turn it off from their phone...
      </div>
      <button type="button" class="btn btn-poke" onclick="handleSendPoke()">💌 Poke Partner: "Please Turn It Off!"</button>
    </div>

    <!-- PARTNER'S ALARM IS RINGING (I HAVE THE TURN-OFF POWER!) -->
    <div id="partnerRingingBox" class="card" style="display: none; text-align: center; border-color: var(--danger-red); box-shadow: 0 0 35px rgba(255, 23, 68, 0.6);">
      <div style="font-size: 3rem;">🚨</div>
      <h2 style="color: #ff1744; font-size: 1.3rem; margin-bottom: 8px;">Your Partner's Alarm is RINGING!</h2>
      <p style="color: #cfcbdd; font-size: 0.9rem; margin-bottom: 16px;">Only YOU can silence their alarm and let them wake up!</p>
      <button type="button" class="btn btn-danger-glow" onclick="handleDismissPartnerAlarm()">💖 Turn Off My Partner's Alarm</button>
    </div>

    <!-- MAIN DASHBOARD -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <span>💖</span>
          <span id="dashboardTitle">Partner Controls</span>
        </div>
        <span id="roleBadge" class="pairing-badge" style="font-size: 0.75rem;">Active Role</span>
      </div>

      <!-- 1. HUG -->
      <div class="feature-block">
        <div class="feature-title"><span>💓</span><span>Send Heartbeat Hug</span></div>
        <button type="button" class="btn btn-hug" onclick="handleSendHeartbeat()">✨ Send Warm Heartbeat Hug Across the Miles</button>
      </div>

      <!-- 2. MUSIC -->
      <div class="feature-block">
        <div class="feature-title"><span>🎵</span><span>Play Music / Voice Note for Partner</span></div>
        <select id="musicSelect">
          <option value="piano_romance">🌙 Moonlight Romance Piano</option>
          <option value="lofi_cozy">☕ Cozy Lo-Fi Rain Beats</option>
          <option value="lullaby_dream">✨ Starlight Music Box Lullaby</option>
          <option value="ocean_calm">🌊 Peaceful Ocean Waves</option>
        </select>
        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
          <button id="btnPlayMusic" type="button" class="btn btn-music" onclick="handlePlayMusic()">▶️ Play on Partner's Phone</button>
          <button id="btnPauseMusic" type="button" class="btn btn-secondary" style="display: none; margin-top: 0;" onclick="handlePauseMusic()">⏸️ Pause</button>
        </div>
        <button id="btnVoice" type="button" class="btn btn-secondary" onclick="toggleVoiceRecord()">🎙️ Record & Send Voice Note</button>
        <div id="voiceStatus" style="font-size: 0.8rem; color: #ff758c; text-align: center; margin-top: 4px;"></div>
      </div>

      <!-- 3. MOOD LAMP -->
      <div class="feature-block">
        <div class="feature-title"><span>🎨</span><span>Change Partner's Ambient Lamp Glow</span></div>
        <div class="color-chips">
          <div class="chip" style="background: #ff4081;" onclick="handleSetLamp('#ff4081', 'Romantic Rose')"></div>
          <div class="chip" style="background: #ff9800;" onclick="handleSetLamp('#ff9800', 'Sunset Gold')"></div>
          <div class="chip" style="background: #ffd54f;" onclick="handleSetLamp('#ffd54f', 'Warm Candle')"></div>
          <div class="chip" style="background: #b388ff;" onclick="handleSetLamp('#b388ff', 'Midnight Lavender')"></div>
          <div class="chip" style="background: #00e5ff;" onclick="handleSetLamp('#00e5ff', 'Ocean Cyan')"></div>
          <div class="chip" style="background: #00e676;" onclick="handleSetLamp('#00e676', 'Mint Serenity')"></div>
        </div>
      </div>

      <!-- 4. LOVE NOTE -->
      <div class="feature-block">
        <div class="feature-title"><span>💌</span><span>Send Digital Love Note</span></div>
        <form onsubmit="handleSendNote(event)" style="display: flex; gap: 8px;">
          <input type="text" id="noteInput" placeholder="Write something sweet..." required style="margin-bottom: 0;">
          <button type="submit" class="btn btn-primary" style="width: auto; padding: 0 16px;">Send</button>
        </form>
      </div>

      <!-- 5. SCHEDULE PARTNER'S ALARM -->
      <div class="feature-block">
        <div class="feature-title"><span>⏰</span><span id="alarmSectionTitle">Schedule Alarm for Partner</span></div>
        <form onsubmit="handleSchedulePartnerAlarm(event)">
          <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;" id="alarmTimeLabel">
            Wake-Up Time (in Partner's Local Time):
          </label>
          <input type="time" id="partnerAlarmTimeInput" required>
          <select id="partnerAlarmToneSelect">
            <option value="romantic_chime">✨ Romantic Chime</option>
            <option value="heartbeat_bells">🔔 Heartbeat Bells</option>
            <option value="sweet_morning">🌸 Sweet Morning</option>
            <option value="classic_beep">🚨 Classic Digital Beep</option>
          </select>
          <input type="text" id="partnerAlarmMsgInput" value="Good morning my love! Time to wake up ❤️">
          <button type="submit" class="btn btn-primary">💾 Schedule Partner's Alarm</button>
        </form>
        <button type="button" class="btn btn-secondary" onclick="handleInstantTriggerPartner()">⚡ Instant Test Ring on Partner's Phone</button>
      </div>

    </div>
  </div>

  <script>
    let myRole = localStorage.getItem('love_role') || 'A'; // 'A' = Spain, 'B' = India
    let currentRoomCode = localStorage.getItem('love_room_code') || 'LOVE-99';
    let audioCtx = null, alarmIntervalId = null, musicIntervalId = null, currentVoiceAudio = null;
    let eventSource = null, lastPulseId = 0;

    function setMyRole(role) {
      myRole = role;
      localStorage.setItem('love_role', role);
      document.getElementById('roleBtnA').className = role === 'A' ? 'role-btn active' : 'role-btn';
      document.getElementById('roleBtnB').className = role === 'B' ? 'role-btn active' : 'role-btn';
      document.getElementById('tzCardA').className = role === 'A' ? 'tz-card me' : 'tz-card partner';
      document.getElementById('tzCardB').className = role === 'B' ? 'tz-card me' : 'tz-card partner';
      
      const title = role === 'A' ? "Controls for Boyfriend (India 🇮🇳)" : "Controls for Girlfriend (Spain 🇪🇸)";
      document.getElementById('dashboardTitle').innerText = title;
      document.getElementById('roleBadge').innerText = role === 'A' ? "🇪🇸 Spain Role" : "🇮🇳 India Role";
      document.getElementById('alarmSectionTitle').innerText = role === 'A' ? "Schedule Alarm for Boyfriend (India Time)" : "Schedule Alarm for Girlfriend (Spain Time)";
      document.getElementById('alarmTimeLabel').innerText = role === 'A' ? "Wake-Up Time in India (IST):" : "Wake-Up Time in Spain (CET):";
      fetchStatus();
    }

    function updateDualClocks() {
      const now = new Date();
      const timeA = now.toLocaleTimeString('en-GB', { timeZone: 'Europe/Madrid', hour12: false });
      const dateA = now.toLocaleDateString('en-US', { timeZone: 'Europe/Madrid', weekday: 'short', month: 'short', day: 'numeric' });
      const timeB = now.toLocaleTimeString('en-GB', { timeZone: 'Asia/Kolkata', hour12: false });
      const dateB = now.toLocaleDateString('en-US', { timeZone: 'Asia/Kolkata', weekday: 'short', month: 'short', day: 'numeric' });

      document.getElementById('tzTimeA').innerText = timeA;
      document.getElementById('tzDateA').innerText = dateA;
      document.getElementById('tzTimeB').innerText = timeB;
      document.getElementById('tzDateB').innerText = dateB;

      // Check local trigger for my alarm
      if (currentState) {
        const myAlarm = myRole === 'A' ? currentState.alarmA : currentState.alarmB;
        const myCurrentTime = myRole === 'A' ? timeA.slice(0, 5) : timeB.slice(0, 5);
        if (myAlarm && myAlarm.enabled && myAlarm.time === myCurrentTime && !myAlarm.isRinging) {
          triggerMyAlarmLocally();
        }
      }
    }

    function triggerMyAlarmLocally() {
      fetch(`/api/trigger-alarm?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, target: myRole })
      }).catch(e => {});
    }

    function unlockAudio() {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    }

    function playTone(f, type = 'sine', duration = 0.3, start = 0, gain = 0.2) {
      try {
        unlockAudio();
        const osc = audioCtx.createOscillator(), g = audioCtx.createGain();
        osc.type = type; osc.frequency.setValueAtTime(f, audioCtx.currentTime + start);
        g.gain.setValueAtTime(0.001, audioCtx.currentTime + start);
        g.gain.linearRampToValueAtTime(gain, audioCtx.currentTime + start + 0.04);
        g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + start + duration);
        osc.connect(g); g.connect(audioCtx.destination);
        osc.start(audioCtx.currentTime + start); osc.stop(audioCtx.currentTime + start + duration);
      } catch (e) {}
    }

    const ALARM_MELODIES = {
      romantic_chime: () => [659.25, 830.61, 987.77, 1318.51].forEach((f, i) => playTone(f, 'sine', 0.5, i * 0.15, 0.25)),
      heartbeat_bells: () => { playTone(523.25, 'triangle', 0.6, 0, 0.2); playTone(659.25, 'triangle', 0.6, 0.08, 0.2); playTone(783.99, 'triangle', 0.7, 0.16, 0.25); playTone(1046.5, 'sine', 0.9, 0.24, 0.3); },
      sweet_morning: () => [{f:587.33,t:0},{f:739.99,t:0.15},{f:880,t:0.3},{f:1174.66,t:0.45}].forEach(n => playTone(n.f, 'triangle', 0.4, n.t, 0.25)),
      classic_beep: () => { playTone(880, 'square', 0.12, 0, 0.15); playTone(880, 'square', 0.12, 0.2, 0.15); playTone(880, 'square', 0.12, 0.4, 0.15); }
    };

    function startRingingAudio(k) {
      unlockAudio();
      if (alarmIntervalId) clearInterval(alarmIntervalId);
      const fn = ALARM_MELODIES[k] || ALARM_MELODIES.romantic_chime;
      fn();
      alarmIntervalId = setInterval(fn, 1600);
    }
    function stopRingingAudio() { if (alarmIntervalId) { clearInterval(alarmIntervalId); alarmIntervalId = null; } }

    let currentState = null;
    function applyState(state) {
      currentState = state;
      document.getElementById('activeRoomCodeDisplay').innerText = state.code || currentRoomCode;

      if (state.moodLamp) {
        document.documentElement.style.setProperty('--lamp-color', state.moodLamp.color);
        document.documentElement.style.setProperty('--lamp-glow', state.moodLamp.color + '66');
      }

      // Check My Alarm vs Partner Alarm
      const myAlarm = myRole === 'A' ? state.alarmA : state.alarmB;
      const partnerAlarm = myRole === 'A' ? state.alarmB : state.alarmA;

      const myBox = document.getElementById('myRingingBox');
      const partnerBox = document.getElementById('partnerRingingBox');

      // 1. If MY alarm is ringing -> Locked Screen + Sound
      if (myAlarm && myAlarm.isRinging) {
        myBox.style.display = 'block';
        document.getElementById('myAlarmMsg').innerText = `"${myAlarm.message}"`;
        startRingingAudio(myAlarm.tone);
      } else {
        myBox.style.display = 'none';
        stopRingingAudio();
      }

      // 2. If PARTNER's alarm is ringing -> I get the OFF button!
      if (partnerAlarm && partnerAlarm.isRinging) {
        partnerBox.style.display = 'block';
      } else {
        partnerBox.style.display = 'none';
      }

      // 3. Heartbeat Pulse
      if (state.heartbeat && state.heartbeat.pulseId > lastPulseId) {
        lastPulseId = state.heartbeat.pulseId;
        playTone(70, 'sine', 0.2, 0, 0.5); playTone(65, 'sine', 0.25, 0.22, 0.5);
        const o = document.getElementById('heartOverlay');
        document.getElementById('heartSenderText').innerText = `${state.heartbeat.sentBy} sent you a warm hug!`;
        o.classList.add('active');
        setTimeout(() => o.classList.remove('active'), 2500);
      }
    }

    function connectSSE() {
      if (eventSource) eventSource.close();
      try {
        eventSource = new EventSource(`/api/events?code=${currentRoomCode}`);
        eventSource.onmessage = e => applyState(JSON.parse(e.data));
        eventSource.onerror = () => { eventSource.close(); setTimeout(fetchStatus, 2000); };
      } catch (e) { setInterval(fetchStatus, 2000); }
    }

    async function fetchStatus() {
      try {
        const res = await fetch(`/api/status?code=${currentRoomCode}`);
        const data = await res.json();
        applyState(data);
      } catch (e) {}
    }

    // Handlers
    async function handleSchedulePartnerAlarm(e) {
      e.preventDefault();
      const targetRole = myRole === 'A' ? 'B' : 'A';
      const time = document.getElementById('partnerAlarmTimeInput').value;
      const tone = document.getElementById('partnerAlarmToneSelect').value;
      const message = document.getElementById('partnerAlarmMsgInput').value;

      await fetch(`/api/set-alarm?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, target: targetRole, time, tone, message, enabled: true })
      });
      alert("💖 Alarm scheduled for your partner!");
    }

    async function handleInstantTriggerPartner() {
      const targetRole = myRole === 'A' ? 'B' : 'A';
      const tone = document.getElementById('partnerAlarmToneSelect').value;
      const message = document.getElementById('partnerAlarmMsgInput').value;
      await fetch(`/api/trigger-alarm?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, target: targetRole, tone, message })
      });
    }

    async function handleDismissPartnerAlarm() {
      const targetRole = myRole === 'A' ? 'B' : 'A';
      await fetch(`/api/dismiss-alarm?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, target: targetRole })
      });
    }

    async function handleSendPoke() {
      playTone(987.77, 'triangle', 0.2, 0, 0.2);
      await fetch(`/api/poke?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, sender: myRole })
      });
    }

    async function handleSendHeartbeat() {
      const name = myRole === 'A' ? "Girlfriend in Spain 🇪🇸" : "Boyfriend in India 🇮🇳";
      await fetch(`/api/heartbeat?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, sentBy: name })
      });
    }

    async function handleSetLamp(color, name) {
      await fetch(`/api/mood?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, color, name })
      });
    }

    async function handleSendNote(e) {
      e.preventDefault();
      const input = document.getElementById('noteInput');
      const text = input.value.trim(); if (!text) return;
      const sender = myRole === 'A' ? "Spain 🇪🇸" : "India 🇮🇳";
      await fetch(`/api/note?code=${currentRoomCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentRoomCode, text, sentBy: sender })
      });
      input.value = '';
    }

    function openPairingModal() { document.getElementById('pairingModal').classList.add('open'); }
    function closePairingModal() { document.getElementById('pairingModal').classList.remove('open'); }
    function handleSaveRoomCode() {
      let c = (document.getElementById('customRoomInput').value || "LOVE-99").trim().toUpperCase();
      if (c) { currentRoomCode = c; localStorage.setItem('love_room_code', c); closePairingModal(); fetchStatus(); connectSSE(); }
    }

    document.addEventListener('DOMContentLoaded', () => {
      setMyRole(myRole);
      updateDualClocks();
      setInterval(updateDualClocks, 1000);
      document.body.addEventListener('click', unlockAudio, { once: true });
      document.body.addEventListener('touchstart', unlockAudio, { once: true });
      fetchStatus();
      connectSSE();
    });
  </script>
</body>
</html>"""

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class LoveCompanionHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        code = query.get("code", ["LOVE-99"])[0].strip().upper()

        if path == "/api/status":
            state = get_room_state(code)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        elif path == "/api/events":
            state = get_room_state(code)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            with subscribers_lock:
                if code not in room_subscribers:
                    room_subscribers[code] = []
                room_subscribers[code].append(self.wfile)

            init_data = f"data: {json.dumps(state)}\n\n".encode('utf-8')
            try:
                self.wfile.write(init_data)
                self.wfile.flush()
                while True:
                    time.sleep(10)
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except Exception:
                with subscribers_lock:
                    if code in room_subscribers and self.wfile in room_subscribers[code]:
                        room_subscribers[code].remove(self.wfile)
            return

        elif path == "/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/manifest+json")
            self.end_headers()
            self.wfile.write(MANIFEST_JSON.encode("utf-8"))
            return

        elif path == "/sw.js":
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            self.wfile.write(SW_JS.encode("utf-8"))
            return

        elif path == "/icon.svg" or path.endswith(".svg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.end_headers()
            self.wfile.write(ICON_SVG.encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(INDEX_HTML.encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        code = payload.get("code", "LOVE-99").strip().upper()
        state = get_room_state(code)

        if path == "/api/set-alarm":
            target = payload.get("target", "B") # 'A' or 'B'
            alarm_obj = state["alarmA"] if target == "A" else state["alarmB"]
            alarm_obj["time"] = payload.get("time", alarm_obj["time"])
            alarm_obj["enabled"] = payload.get("enabled", True)
            if "message" in payload: alarm_obj["message"] = payload["message"]
            if "tone" in payload: alarm_obj["tone"] = payload["tone"]
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/trigger-alarm":
            target = payload.get("target", "B")
            alarm_obj = state["alarmA"] if target == "A" else state["alarmB"]
            alarm_obj["isRinging"] = True
            if "message" in payload: alarm_obj["message"] = payload["message"]
            if "tone" in payload: alarm_obj["tone"] = payload["tone"]
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/dismiss-alarm":
            target = payload.get("target", "B")
            alarm_obj = state["alarmA"] if target == "A" else state["alarmB"]
            alarm_obj["isRinging"] = False
            alarm_obj["enabled"] = False
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/poke":
            sender = payload.get("sender", "A")
            if sender == "A": state["pokeA"] += 1
            else: state["pokeB"] += 1
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/heartbeat":
            state["heartbeat"]["pulseId"] += 1
            state["heartbeat"]["sentBy"] = payload.get("sentBy", "Partner")
            state["heartbeat"]["timestamp"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/mood":
            state["moodLamp"]["color"] = payload.get("color", "#ff4081")
            state["moodLamp"]["name"] = payload.get("name", "Custom")
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/note":
            state["loveNote"]["text"] = payload.get("text", "")
            state["loveNote"]["sentBy"] = payload.get("sentBy", "Partner")
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        else:
            self.send_error(404, "Endpoint not found")

    def respond_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def run():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), LoveCompanionHandler)
    print("="*60)
    print(f"   💖 LOVE COMPANION (SPAIN & INDIA) RUNNING ON PORT {PORT}! 💖")
    print("="*60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")

if __name__ == "__main__":
    run()
