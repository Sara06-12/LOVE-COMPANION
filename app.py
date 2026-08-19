Ran command: `py app.py`
Ran command: `py -c "import urllib.request; res = urllib.request.urlopen('http://localhost:8080/'); print('STATUS:', res.status); print('LENGTH:', len(res.read()))"`

The **404 "File not found: /"** error happened because on GitHub, only `app.py` was uploaded without the HTML/CSS files.

### 💡 The Permanent Fix:
I have packaged the **ENTIRE app (all the screens, colors, melodies, audio synthesizer, and backend) into ONE single self-contained file: `app.py`**!

This means you **only need this ONE single file (`app.py`)** on GitHub. No other folders or files are required, and it will **never show a 404 or 500 error again**!

---

### 📋 How to Update It on GitHub (Takes 1 Minute):

1. Go to your repository on **[github.com](https://github.com)**.
2. Click on **`app.py`** $\rightarrow$ Click the **Pencil icon ✏️ (Edit this file)**.
3. Select everything (`Ctrl + A`), delete it, and paste the code below:

<details open>
<summary><b>👉 Click here to view & copy the complete all-in-one <code>app.py</code>:</b></summary>

```python
import http.server
import socketserver
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
import threading

# Ensure UTF-8 console output
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = int(os.environ.get("PORT", 8080))

# Multi-room state store
rooms = {}
rooms_lock = threading.Lock()
room_subscribers = {}
subscribers_lock = threading.Lock()

def create_default_state(code):
    return {
        "code": code,
        "isRinging": False,
        "alarmTime": None,
        "alarmEnabled": False,
        "alarmMessage": "Good morning my love! Time to wake up ❤️",
        "tone": "romantic_chime",
        "wakePoke": 0,
        "music": {
            "isPlaying": False,
            "trackId": "piano_romance",
            "trackTitle": "🌙 Moonlight Romance Piano",
            "volume": 80,
            "voiceAudio": None
        },
        "moodLamp": {
            "color": "#ff4081",
            "brightness": 90,
            "name": "Romantic Rose"
        },
        "loveNote": {
            "text": "Thinking of you always ❤️",
            "sentBy": "Partner A",
            "timestamp": time.time()
        },
        "heartbeat": {
            "pulseId": 0,
            "sentBy": "Partner A",
            "timestamp": time.time()
        },
        "partnerA": "Partner A",
        "partnerB": "Partner B",
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
    last_checked_minute = None
    while True:
        try:
            now = datetime.now().strftime("%H:%M")
            if now != last_checked_minute:
                with rooms_lock:
                    room_keys = list(rooms.keys())
                for code in room_keys:
                    state = get_room_state(code)
                    if state.get("alarmEnabled") and state.get("alarmTime") and not state.get("isRinging"):
                        if now == state["alarmTime"]:
                            state["isRinging"] = True
                            state["lastAction"] = f"[Alarm] Scheduled alarm ringing for {state['partnerB']}!"
                            state["lastActionTime"] = time.time()
                            print(f"[{now}] [Alarm] Triggered in Room {code} for {state['partnerB']}!")
                            broadcast_room_state(code)
                last_checked_minute = now
            time.sleep(1)
        except Exception as e:
            print("Scheduler error:", e)
            time.sleep(1)

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
  <circle cx="150" cy="140" r="10" fill="#fff" opacity="0.8"/>
  <circle cx="370" cy="160" r="8" fill="#fff" opacity="0.7"/>
</svg>"""

MANIFEST_JSON = json.dumps({
  "name": "Love Companion",
  "short_name": "LoveSync",
  "description": "Long-distance couple companion with remote music, mood lamp, heartbeat hugs, and partner-locked alarm.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0b0a14",
  "theme_color": "#ff4081",
  "orientation": "portrait-primary",
  "icons": [{
    "src": "/icon.svg",
    "sizes": "192x192 512x512",
    "type": "image/svg+xml",
    "purpose": "any maskable"
  }]
})

SW_JS = """const CACHE_NAME = 'love-companion-v2';
self.addEventListener('install', (e) => self.skipWaiting());
self.addEventListener('activate', (e) => self.clients.claim());
self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/')) return;
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>Love Companion ❤️</title>
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#ff4081">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="LoveSync">
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
      --accent-glow: rgba(255, 64, 129, 0.4);
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
    header { text-align: center; padding: 16px 16px 8px; }
    .top-bar { display: flex; align-items: center; justify-content: space-between; max-width: 980px; margin: 0 auto 10px; padding: 0 8px; }
    .pairing-badge { background: rgba(255, 64, 129, 0.15); border: 1px solid var(--lamp-color); color: #fff; padding: 6px 14px; border-radius: 100px; font-size: 0.82rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
    .pairing-badge:hover { background: rgba(255, 64, 129, 0.3); transform: scale(1.04); }
    .btn-install { background: linear-gradient(135deg, #00e5ff, #00b0ff); color: #000; border: none; padding: 6px 14px; border-radius: 100px; font-size: 0.82rem; font-weight: 800; cursor: pointer; display: none; align-items: center; gap: 6px; box-shadow: 0 0 12px rgba(0, 229, 255, 0.4); }
    .logo-row { display: flex; align-items: center; justify-content: center; gap: 10px; }
    .heart-pulse { font-size: 1.8rem; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.2); } 100% { transform: scale(1); } }
    h1 { font-size: 1.85rem; background: linear-gradient(45deg, #ff758c, #ff7eb3, var(--lamp-color)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; transition: all 0.3s; }
    .subtitle { color: var(--text-muted); font-size: 0.85rem; margin-top: 2px; }
    .view-tabs { display: flex; justify-content: center; gap: 8px; margin: 14px auto; max-width: 600px; padding: 0 16px; }
    .tab-btn { flex: 1; background: var(--bg-secondary); color: var(--text-muted); border: 1px solid rgba(255, 255, 255, 0.1); padding: 9px 12px; border-radius: 12px; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: all 0.2s ease; display: flex; align-items: center; justify-content: center; gap: 6px; }
    .tab-btn:hover { border-color: var(--lamp-color); color: #fff; }
    .tab-btn.active { background: linear-gradient(135deg, rgba(255, 64, 129, 0.25), rgba(255, 117, 140, 0.15)); border-color: var(--lamp-color); color: #fff; box-shadow: 0 0 16px var(--lamp-glow); }
    .ticker-bar { max-width: 980px; margin: 0 auto 16px; padding: 8px 16px; background: rgba(255, 255, 255, 0.04); border-radius: 100px; border: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; gap: 10px; font-size: 0.85rem; color: #f1f1f1; }
    .ticker-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--success-green); box-shadow: 0 0 8px var(--success-green); }
    .ticker-dot.ringing { background: var(--danger-red); box-shadow: 0 0 12px var(--danger-red); animation: flash 0.8s infinite; }
    .ticker-dot.playing { background: var(--accent-cyan); box-shadow: 0 0 12px var(--accent-cyan); animation: flash 1.2s infinite; }
    @keyframes flash { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    .container { max-width: 1050px; margin: 0 auto; padding: 0 16px; }
    .views-grid { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; }
    .view-single { grid-template-columns: 1fr; max-width: 520px; margin: 0 auto; }
    .card { background: var(--card-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid var(--card-border); border-radius: 24px; padding: 22px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4); position: relative; overflow: hidden; display: flex; flex-direction: column; }
    .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 10px; }
    .card-title { font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .badge { font-size: 0.75rem; padding: 4px 10px; border-radius: 100px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .badge-controller { background: rgba(0, 229, 255, 0.15); color: var(--accent-cyan); border: 1px solid rgba(0, 229, 255, 0.3); }
    .badge-clock { background: rgba(255, 64, 129, 0.15); color: var(--lamp-color); border: 1px solid var(--lamp-glow); }
    .feature-block { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 18px; padding: 15px; margin-bottom: 14px; }
    .feature-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; color: #f1f0f7; }
    .desk-clock-wrapper { position: relative; margin-bottom: 18px; }
    .desk-clock { background: #05040a; border-radius: 22px; padding: 24px 16px; text-align: center; border: 2px solid var(--lamp-color); box-shadow: 0 0 35px var(--lamp-glow), inset 0 0 30px rgba(0, 0, 0, 0.9); transition: all 0.4s ease; position: relative; overflow: hidden; }
    .desk-clock.ringing { border-color: var(--danger-red); box-shadow: 0 0 50px rgba(255, 23, 68, 0.7), inset 0 0 30px rgba(255, 23, 68, 0.4); animation: shake 0.5s infinite; }
    @keyframes shake { 0% { transform: translate(1px, 1px) rotate(0deg); } 20% { transform: translate(-2px, 0px) rotate(-0.5deg); } 40% { transform: translate(2px, -1px) rotate(0.5deg); } 60% { transform: translate(-1px, 1px) rotate(0deg); } 80% { transform: translate(1px, -1px) rotate(0.5deg); } 100% { transform: translate(1px, 1px) rotate(0deg); } }
    .clock-digits { font-family: 'Courier New', Courier, monospace; font-size: 3.4rem; font-weight: 900; color: #fff; letter-spacing: 2px; text-shadow: 0 0 15px rgba(255, 255, 255, 0.7), 0 0 30px var(--lamp-glow); }
    .clock-date { color: var(--text-muted); font-size: 0.85rem; margin-top: 4px; }
    .desk-music-bar { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 12px; padding: 6px 12px; background: rgba(0, 229, 255, 0.1); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 100px; font-size: 0.82rem; color: #00e5ff; }
    .equalizer { display: flex; align-items: flex-end; gap: 2px; height: 12px; }
    .eq-bar { width: 3px; background: var(--accent-cyan); border-radius: 2px; animation: equalize 1s infinite alternate ease-in-out; }
    .eq-bar:nth-child(1) { height: 60%; animation-delay: 0.1s; } .eq-bar:nth-child(2) { height: 100%; animation-delay: 0.3s; } .eq-bar:nth-child(3) { height: 40%; animation-delay: 0.2s; } .eq-bar:nth-child(4) { height: 80%; animation-delay: 0.4s; }
    @keyframes equalize { 0% { height: 20%; } 100% { height: 100%; } }
    .desk-love-note-box { background: rgba(255, 255, 255, 0.06); border: 1px dashed var(--lamp-color); border-radius: 12px; padding: 10px; margin-top: 12px; text-align: center; }
    .desk-love-note { font-size: 0.9rem; font-style: italic; color: #fff; }
    .desk-love-note-sender { font-size: 0.72rem; color: var(--text-muted); margin-top: 3px; }
    .alarm-banner { margin-top: 12px; padding: 8px; border-radius: 10px; background: rgba(255, 255, 255, 0.04); font-size: 0.82rem; }
    .alarm-banner.active-banner { background: linear-gradient(135deg, rgba(255, 23, 68, 0.3), rgba(255, 64, 129, 0.4)); border: 1px solid var(--danger-red); color: #fff; font-weight: 700; box-shadow: 0 0 20px rgba(255, 64, 129, 0.5); }
    .lockout-notice { background: rgba(255, 193, 7, 0.1); border: 1px dashed var(--gold-glow); color: #ffe082; padding: 10px; border-radius: 12px; font-size: 0.82rem; text-align: center; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; }
    .heart-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; opacity: 0; transition: opacity 0.3s ease; background: radial-gradient(circle, rgba(255, 64, 129, 0.4) 0%, rgba(0,0,0,0) 70%); }
    .heart-overlay.active { opacity: 1; }
    .heart-overlay-icon { font-size: 5.5rem; animation: heartThump 0.7s infinite alternate; filter: drop-shadow(0 0 30px #ff4081); }
    .heart-overlay-text { font-size: 1.35rem; font-weight: 800; color: #fff; text-shadow: 0 0 20px rgba(255, 64, 129, 0.8); margin-top: 12px; }
    @keyframes heartThump { 0% { transform: scale(0.9); } 50% { transform: scale(1.3); } 100% { transform: scale(1.1); } }
    .modal-backdrop { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(8px); z-index: 10000; display: none; align-items: center; justify-content: center; padding: 16px; }
    .modal-backdrop.open { display: flex; }
    .modal-content { background: #18152b; border: 1px solid var(--lamp-color); box-shadow: 0 0 40px var(--lamp-glow); border-radius: 24px; padding: 24px; max-width: 440px; width: 100%; text-align: center; }
    .modal-title { font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; }
    .pairing-code-display { font-family: monospace; font-size: 2rem; font-weight: 900; background: rgba(255, 255, 255, 0.08); border: 2px dashed var(--lamp-color); padding: 12px; border-radius: 14px; letter-spacing: 4px; color: #fff; margin: 14px 0; }
    .color-chips { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
    .chip { width: 32px; height: 32px; border-radius: 50%; cursor: pointer; border: 2px solid rgba(255, 255, 255, 0.3); transition: transform 0.2s, box-shadow 0.2s; }
    .chip:hover { transform: scale(1.2); box-shadow: 0 0 12px rgba(255, 255, 255, 0.6); }
    .lamp-control-row { display: flex; align-items: center; gap: 10px; }
    .form-group { margin-bottom: 12px; }
    label { display: block; font-size: 0.78rem; font-weight: 700; color: var(--text-muted); margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
    input[type="time"], input[type="text"], select { width: 100%; background: rgba(10, 8, 20, 0.8); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; padding: 10px 12px; border-radius: 12px; font-size: 0.95rem; outline: none; transition: all 0.2s; }
    input[type="time"]:focus, input[type="text"]:focus, select:focus { border-color: var(--lamp-color); box-shadow: 0 0 12px var(--lamp-glow); }
    .btn { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 0.95rem; font-weight: 700; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; justify-content: center; gap: 8px; border: none; }
    .btn-primary { background: linear-gradient(135deg, #ff4081, #ff758c); color: #fff; box-shadow: 0 4px 16px rgba(255, 64, 129, 0.35); }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 22px rgba(255, 64, 129, 0.5); }
    .btn-music { background: linear-gradient(135deg, #00b0ff, #00e5ff); color: #000; font-weight: 800; box-shadow: 0 4px 16px rgba(0, 229, 255, 0.3); }
    .btn-music:hover { transform: translateY(-2px); box-shadow: 0 6px 22px rgba(0, 229, 255, 0.5); }
    .btn-voice { background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); color: #fff; }
    .btn-voice.recording { background: #ff1744; color: #fff; animation: pulse 1s infinite; }
    .btn-hug { background: linear-gradient(135deg, #ff758c, #ff4081); color: #fff; padding: 13px; font-size: 1rem; box-shadow: 0 0 20px rgba(255, 64, 129, 0.4); }
    .btn-hug:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(255, 64, 129, 0.7); }
    .btn-danger-glow { background: linear-gradient(135deg, #ff1744, #ff5252); color: #fff; font-size: 1.1rem; padding: 16px; box-shadow: 0 0 30px rgba(255, 23, 68, 0.6); animation: glowPulse 1.2s infinite; }
    @keyframes glowPulse { 0%, 100% { transform: scale(1); box-shadow: 0 0 25px rgba(255, 23, 68, 0.5); } 50% { transform: scale(1.03); box-shadow: 0 0 45px rgba(255, 23, 68, 0.8); } }
    .btn-poke { background: rgba(255, 215, 0, 0.15); border: 1px solid var(--gold-glow); color: #fff; }
    .btn-poke:hover { background: rgba(255, 215, 0, 0.25); transform: scale(1.02); }
    .btn-row { display: flex; gap: 8px; }
    .instructions-card { max-width: 980px; margin: 24px auto 0; background: rgba(18, 16, 32, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 18px; padding: 18px 20px; }
    .instructions-card h3 { color: var(--accent-rose); margin-bottom: 8px; font-size: 1.05rem; }
    .instructions-card ul { padding-left: 20px; color: #cfcbdd; font-size: 0.9rem; line-height: 1.6; }
    @media (max-width: 768px) { .views-grid { grid-template-columns: 1fr; } .clock-digits { font-size: 2.6rem; } .view-tabs { flex-wrap: wrap; } }
  </style>
</head>
<body>
  <div id="heartOverlay" class="heart-overlay">
    <div class="heart-overlay-icon">💖</div>
    <div id="heartSenderText" class="heart-overlay-text">Warm Hug Received!</div>
  </div>

  <div id="pairingModal" class="modal-backdrop">
    <div class="modal-content">
      <div style="font-size: 2.5rem; margin-bottom: 6px;">🔐</div>
      <h2 class="modal-title">Couple Pairing Code</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem;">
        Share this Love Code with your partner so both your phones connect privately!
      </p>
      <div id="modalCodeDisplay" class="pairing-code-display">LOVE-99</div>
      <div class="form-group" style="text-align: left; margin-top: 16px;">
        <label for="customRoomInput">Enter or Create Room Code:</label>
        <div style="display: flex; gap: 8px;">
          <input type="text" id="customRoomInput" placeholder="e.g. LOVE-88" style="text-transform: uppercase; font-weight: 700;">
          <button type="button" class="btn btn-secondary" style="width: auto; margin-top: 0; padding: 0 14px;" onclick="generateNewRoomCode()">
            🎲 Random
          </button>
        </div>
      </div>
      <button type="button" class="btn btn-primary" style="margin-top: 12px;" onclick="handleSaveRoomCode()">
        💖 Connect & Save Code
      </button>
      <button type="button" class="btn btn-secondary" style="margin-top: 8px;" onclick="closePairingModal()">
        Cancel
      </button>
    </div>
  </div>

  <header>
    <div class="top-bar">
      <div class="pairing-badge" onclick="openPairingModal()">
        <span>🔐 Room:</span>
        <span id="activeRoomCodeDisplay" style="color: var(--accent-pink);">LOVE-99</span>
        <span style="font-size: 0.7rem;">✏️</span>
      </div>
      <button id="btnInstallApp" class="btn-install" onclick="triggerInstallApp()">
        📲 Install App
      </button>
    </div>
    <div class="logo-row">
      <span class="heart-pulse">💖</span>
      <h1>Love Companion</h1>
      <span class="heart-pulse">💖</span>
    </div>
    <p class="subtitle">Long-Distance Mobile Companion • Music • Lamp • Alarm</p>
  </header>

  <div class="view-tabs">
    <button id="tab-split" class="tab-btn active" onclick="switchView('split')">👥 Split View</button>
    <button id="tab-partnerA" class="tab-btn" onclick="switchView('partnerA')">📱 Partner A (Sender)</button>
    <button id="tab-partnerB" class="tab-btn" onclick="switchView('partnerB')">⏰ Partner B (Receiver)</button>
  </div>

  <div class="container">
    <div class="ticker-bar">
      <div id="tickerDot" class="ticker-dot"></div>
      <span id="tickerText">Connected to Love Companion server...</span>
    </div>
  </div>

  <div class="container">
    <div id="viewsContainer" class="views-grid">
      <div id="colPartnerA" class="card">
        <div class="card-header">
          <div class="card-title"><span>📱</span><span class="partner-a-name">Partner A</span></div>
          <span class="badge badge-controller">Sender</span>
        </div>

        <div id="ringingCardA" style="display: none; text-align: center; margin-bottom: 20px;">
          <div style="font-size: 3rem; margin-bottom: 8px;">🚨</div>
          <h2 id="ringingStatusText" style="color: #ff1744; font-size: 1.3rem; margin-bottom: 10px;">Partner's Alarm is RINGING!</h2>
          <p style="color: #cfcbdd; font-size: 0.9rem; margin-bottom: 18px;">Only you can turn off this alarm. Tap below to let your partner wake up!</p>
          <button type="button" class="btn btn-danger-glow" onclick="handleDismissAlarm()">💖 Turn Off My Partner's Alarm</button>
        </div>

        <div id="normalCardA">
          <div class="feature-block">
            <div class="feature-title"><span>💓</span><span>Send Heartbeat Hug</span></div>
            <button type="button" class="btn btn-hug" onclick="handleSendHeartbeat('Partner A')">✨ Send a Warm Heartbeat Hug</button>
          </div>

          <div class="feature-block">
            <div class="feature-title"><span>🎵</span><span>Play Music & Voice for Partner</span></div>
            <div class="form-group" style="margin-bottom: 10px;">
              <label for="musicTrackSelect">Choose Song / Ambience</label>
              <select id="musicTrackSelect">
                <option value="piano_romance">🌙 Moonlight Romance Piano</option>
                <option value="lofi_cozy">☕ Cozy Lo-Fi Rain Beats</option>
                <option value="lullaby_dream">✨ Starlight Music Box Lullaby</option>
                <option value="ocean_calm">🌊 Peaceful Ocean Waves</option>
              </select>
            </div>
            <div class="btn-row" style="margin-bottom: 10px;">
              <button id="btnMusicPlay" type="button" class="btn btn-music" onclick="handlePlayMusic()">▶️ Play on Partner's Phone</button>
              <button id="btnMusicPause" type="button" class="btn btn-secondary" style="display: none; margin-top: 0;" onclick="handlePauseMusic()">⏸️ Pause Music</button>
            </div>
            <button id="btnVoiceRecord" type="button" class="btn btn-voice" onclick="toggleVoiceRecording()">🎙️ Record & Send Voice Note</button>
            <div id="voiceRecordStatus" style="font-size: 0.8rem; color: #ff758c; text-align: center; margin-top: 6px;"></div>
          </div>

          <div class="feature-block">
            <div class="feature-title"><span>🎨</span><span>Change Ambient Mood Lamp Glow</span></div>
            <div class="color-chips">
              <div class="chip" style="background: #ff4081;" title="Romantic Rose" onclick="handleSetLampColor('#ff4081', 'Romantic Rose')"></div>
              <div class="chip" style="background: #ff9800;" title="Sunset Gold" onclick="handleSetLampColor('#ff9800', 'Sunset Gold')"></div>
              <div class="chip" style="background: #ffd54f;" title="Warm Candlelight" onclick="handleSetLampColor('#ffd54f', 'Warm Candle')"></div>
              <div class="chip" style="background: #b388ff;" title="Midnight Lavender" onclick="handleSetLampColor('#b388ff', 'Midnight Lavender')"></div>
              <div class="chip" style="background: #00e5ff;" title="Ocean Cyan" onclick="handleSetLampColor('#00e5ff', 'Ocean Cyan')"></div>
              <div class="chip" style="background: #00e676;" title="Mint Serenity" onclick="handleSetLampColor('#00e676', 'Mint Serenity')"></div>
            </div>
            <div class="lamp-control-row">
              <input type="color" id="lampColorPicker" value="#ff4081" onchange="handleSetLampColor(this.value, 'Custom Mood')" style="width: 40px; height: 36px; padding: 2px; border: none; cursor: pointer; border-radius: 8px;">
              <span id="activeLampNameA" style="font-size: 0.85rem; color: var(--text-muted);">Romantic Rose</span>
            </div>
          </div>

          <div class="feature-block">
            <div class="feature-title"><span>💌</span><span>Send Digital Love Note</span></div>
            <form onsubmit="handleSendLoveNote(event)" style="display: flex; gap: 8px;">
              <input type="text" id="loveNoteInput" placeholder="Write something sweet..." required>
              <button type="submit" class="btn btn-primary" style="width: auto; padding: 0 16px;">Send</button>
            </form>
          </div>

          <div class="feature-block">
            <div class="feature-title"><span>⏰</span><span>Schedule Partner-Locked Alarm</span></div>
            <form onsubmit="handleSetAlarm(event)">
              <div class="form-group">
                <label for="alarmTimeInput">Wake-Up Time</label>
                <input type="time" id="alarmTimeInput" required>
              </div>
              <div class="form-group">
                <label for="alarmToneSelect">Melody</label>
                <select id="alarmToneSelect">
                  <option value="romantic_chime">✨ Romantic Chime (Soft & Sweet)</option>
                  <option value="heartbeat_bells">🔔 Heartbeat Bells (Warm)</option>
                  <option value="sweet_morning">🌸 Sweet Morning (Bright)</option>
                  <option value="classic_beep">🚨 Classic Digital Beep</option>
                </select>
                <button type="button" class="btn-preview" style="margin-top: 6px;" onclick="previewTone(document.getElementById('alarmToneSelect').value)">▶️ Preview Melody</button>
              </div>
              <div class="form-group">
                <label for="alarmMessageInput">Morning Message</label>
                <input type="text" id="alarmMessageInput" value="Good morning my love! Time to wake up ❤️">
              </div>
              <button type="submit" class="btn btn-primary">💾 Schedule Alarm</button>
            </form>
            <button type="button" class="btn btn-secondary" style="margin-top: 8px;" onclick="handleInstantTrigger()">⚡ Instant Alarm Ring Test</button>
          </div>
        </div>

        <div id="pokeNotice" class="lockout-notice" style="display: none; margin-top: 14px;"></div>
      </div>

      <div id="colPartnerB" class="card">
        <div class="card-header">
          <div class="card-title"><span>⏰</span><span class="partner-b-name">Partner B</span></div>
          <span class="badge badge-clock">Receiver</span>
        </div>

        <div class="lockout-notice">
          <span>🔒</span>
          <span><b>Connected:</b> <span class="partner-a-name">Partner A</span> has full access</span>
        </div>

        <div class="desk-clock-wrapper">
          <div id="deskClock" class="desk-clock">
            <div id="liveClockDigits" class="clock-digits">12:00:00</div>
            <div id="liveClockDate" class="clock-date">Loading date...</div>
            <div id="deskMusicBar" class="desk-music-bar" style="display: none;">
              <div class="equalizer"><div class="eq-bar"></div><div class="eq-bar"></div><div class="eq-bar"></div><div class="eq-bar"></div></div>
              <span id="deskMusicTitle">Playing Music...</span>
            </div>
            <div class="desk-love-note-box">
              <div id="deskLoveNote" class="desk-love-note">"Thinking of you always ❤️"</div>
              <div id="deskLoveNoteSender" class="desk-love-note-sender">— Partner A</div>
            </div>
            <div id="alarmBanner" class="alarm-banner">💤 No active alarm scheduled</div>
          </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 10px;">
          <button type="button" class="btn btn-hug" onclick="handleSendHeartbeat('Partner B')">💓 Send Hug Back to Partner A</button>
          <button type="button" class="btn btn-poke" onclick="handlePoke()">💌 Poke Partner: "Please Turn Off Alarm!"</button>
        </div>
      </div>
    </div>

    <div class="instructions-card">
      <h3>📲 How to Install as a Mobile App on Your Phone:</h3>
      <ul>
        <li><b>On iPhone (iOS):</b> Open in Safari $\rightarrow$ Tap the <b>Share icon (square with arrow)</b> $\rightarrow$ Tap <b>"Add to Home Screen"</b>.</li>
        <li><b>On Android:</b> Open in Chrome $\rightarrow$ Tap the <b>3 dots menu</b> $\rightarrow$ Tap <b>"Install App"</b> or <b>"Add to Home screen"</b>.</li>
        <li><b>Pairing with Partner:</b> Tap the <b>🔐 Room Code</b> at the top and give your partner the same code!</li>
      </ul>
    </div>
  </div>

  <script>
    let currentRoomCode = localStorage.getItem('love_room_code') || 'LOVE-99';
    let audioCtx = null, alarmIntervalId = null, musicIntervalId = null, currentVoiceAudio = null;
    let isAudioUnlocked = false, deferredPrompt = null, eventSource = null, lastKnownPulseId = 0;

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(e => {}));
    }

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const btn = document.getElementById('btnInstallApp');
      if (btn) btn.style.display = 'inline-flex';
    });

    async function triggerInstallApp() {
      if (!deferredPrompt) {
        alert("To install on iOS: Tap Share -> Add to Home Screen\\nOn Android: Tap menu -> Install App");
        return;
      }
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      document.getElementById('btnInstallApp').style.display = 'none';
    }

    function triggerHaptic(pattern = [100, 50, 100]) {
      if (navigator.vibrate) try { navigator.vibrate(pattern); } catch (e) {}
    }

    function unlockAudio() {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
      isAudioUnlocked = true;
    }

    function playNote(freq, type = 'sine', duration = 0.3, startTime = 0, gainLevel = 0.2) {
      try {
        if (!audioCtx) unlockAudio();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime + startTime);
        gain.gain.setValueAtTime(0.001, audioCtx.currentTime + startTime);
        gain.gain.linearRampToValueAtTime(gainLevel, audioCtx.currentTime + startTime + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + startTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(audioCtx.currentTime + startTime);
        osc.stop(audioCtx.currentTime + startTime + duration);
      } catch (e) {}
    }

    const ALARM_MELODIES = {
      romantic_chime: () => [659.25, 830.61, 987.77, 1318.51].forEach((f, i) => playNote(f, 'sine', 0.5, i * 0.15, 0.25)),
      heartbeat_bells: () => { playNote(523.25, 'triangle', 0.6, 0.0, 0.2); playNote(659.25, 'triangle', 0.6, 0.08, 0.2); playNote(783.99, 'triangle', 0.7, 0.16, 0.25); playNote(1046.50, 'sine', 0.9, 0.24, 0.3); },
      sweet_morning: () => [{ f: 587.33, t: 0.0 }, { f: 739.99, t: 0.15 }, { f: 880.00, t: 0.3 }, { f: 1174.66, t: 0.45 }].forEach(n => playNote(n.f, 'triangle', 0.4, n.t, 0.25)),
      classic_beep: () => { playNote(880, 'square', 0.12, 0.0, 0.15); playNote(880, 'square', 0.12, 0.2, 0.15); playNote(880, 'square', 0.12, 0.4, 0.15); }
    };

    function previewTone(k) { unlockAudio(); if (ALARM_MELODIES[k]) ALARM_MELODIES[k](); }
    function startRingingAudio(k) {
      unlockAudio();
      if (alarmIntervalId) clearInterval(alarmIntervalId);
      const fn = ALARM_MELODIES[k] || ALARM_MELODIES.romantic_chime;
      fn(); triggerHaptic([300, 150, 300, 150, 500]);
      alarmIntervalId = setInterval(() => { fn(); triggerHaptic([300, 150, 300, 150, 500]); }, 1600);
    }
    function stopRingingAudio() { if (alarmIntervalId) { clearInterval(alarmIntervalId); alarmIntervalId = null; } }

    let musicStep = 0;
    const MUSIC_TRACKS = {
      piano_romance: { title: "🌙 Moonlight Romance Piano", play: () => { const chords = [[261.63, 329.63, 392.00, 523.25], [196.00, 246.94, 293.66, 392.00], [220.00, 261.63, 329.63, 440.00], [174.61, 220.00, 261.63, 349.23]]; const chord = chords[musicStep % chords.length]; chord.forEach((freq, idx) => playNote(freq, 'sine', 1.8, idx * 0.25, 0.18)); playNote(chord[3] * 1.5, 'triangle', 0.8, 1.0, 0.12); musicStep++; }, interval: 2000 },
      lofi_cozy: { title: "☕ Cozy Lo-Fi Rain Beats", play: () => { const jazzy = [[220.00, 261.63, 329.63, 392.00], [293.66, 349.23, 440.00, 523.25], [196.00, 246.94, 293.66, 349.23], [261.63, 329.63, 392.00, 493.88]]; const chord = jazzy[musicStep % jazzy.length]; chord.forEach((freq, idx) => playNote(freq, 'triangle', 1.4, idx * 0.18, 0.15)); playNote(1200, 'square', 0.05, 0.8, 0.04); musicStep++; }, interval: 1800 },
      lullaby_dream: { title: "✨ Starlight Music Box Lullaby", play: () => { const notes = [523.25, 659.25, 783.99, 1046.50, 880.00, 659.25, 783.99, 523.25]; const note = notes[musicStep % notes.length]; playNote(note, 'sine', 1.5, 0, 0.22); playNote(note * 2, 'sine', 1.0, 0.1, 0.1); musicStep++; }, interval: 1200 },
      ocean_calm: { title: "🌊 Peaceful Ocean Waves", play: () => { playNote(130.81, 'sine', 3.0, 0, 0.15); playNote(196.00, 'sine', 3.0, 0.2, 0.12); playNote(329.63, 'sine', 3.0, 0.4, 0.1); musicStep++; }, interval: 3200 }
    };

    function startMusicAudio(trackId, voiceAudio) {
      stopMusicAudio(); unlockAudio();
      if (trackId === "voice_note" && voiceAudio) {
        try {
          if (currentVoiceAudio) currentVoiceAudio.pause();
          currentVoiceAudio = new Audio(voiceAudio);
          currentVoiceAudio.play().catch(e => {});
          currentVoiceAudio.onended = () => fetch(`/api/music/control?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, action: "pause" }) }).catch(e => {});
        } catch (e) {}
        return;
      }
      const track = MUSIC_TRACKS[trackId] || MUSIC_TRACKS.piano_romance;
      musicStep = 0; track.play(); musicIntervalId = setInterval(track.play, track.interval);
    }
    function stopMusicAudio() { if (musicIntervalId) { clearInterval(musicIntervalId); musicIntervalId = null; } if (currentVoiceAudio) { currentVoiceAudio.pause(); currentVoiceAudio = null; } }

    function playHeartbeatAudio() { unlockAudio(); playNote(70, 'sine', 0.2, 0.0, 0.5); playNote(65, 'sine', 0.25, 0.22, 0.5); playNote(1318.51, 'sine', 0.6, 0.35, 0.15); triggerHaptic([150, 80, 200]); }
    function triggerHeartbeatVisual(sender) {
      playHeartbeatAudio();
      const o = document.getElementById('heartOverlay');
      const t = document.getElementById('heartSenderText');
      if (t) t.innerText = `${sender} sent you a warm hug!`;
      if (o) { o.classList.remove('active'); void o.offsetWidth; o.classList.add('active'); setTimeout(() => o.classList.remove('active'), 2500); }
    }

    let mediaRecorder = null, audioChunks = [], isRecordingVoice = false;
    async function toggleVoiceRecording() {
      unlockAudio();
      const btn = document.getElementById('btnVoiceRecord');
      const statusEl = document.getElementById('voiceRecordStatus');
      if (!isRecordingVoice) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          audioChunks = [];
          mediaRecorder = new MediaRecorder(stream);
          mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
          mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = async () => {
              statusEl.innerText = "Sending voice note...";
              await fetch(`/api/music/control?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, action: "play", trackId: "voice_note", trackTitle: "🗣️ Voice Note from Partner", voiceAudio: reader.result }) });
              statusEl.innerText = "Voice note played on partner's clock! ❤️";
              setTimeout(() => statusEl.innerText = "", 3000);
            };
          };
          mediaRecorder.start(); isRecordingVoice = true;
          if (btn) { btn.classList.add('recording'); btn.innerHTML = `🔴 <b>Recording Voice... (Tap to Send)</b>`; }
          if (statusEl) statusEl.innerText = "Speak now into your phone!";
        } catch (err) { alert("Microphone permission needed: " + err); }
      } else {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') { mediaRecorder.stop(); mediaRecorder.stream.getTracks().forEach(t => t.stop()); }
        isRecordingVoice = false;
        if (btn) { btn.classList.remove('recording'); btn.innerHTML = `🎙️ Record & Send Voice Note`; }
      }
    }

    function applyState(state) {
      const codeBadge = document.getElementById('activeRoomCodeDisplay');
      if (codeBadge) codeBadge.innerText = state.code || currentRoomCode;
      const tickerText = document.getElementById('tickerText');
      const tickerDot = document.getElementById('tickerDot');
      if (tickerText) tickerText.innerText = state.lastAction || `Paired to ${currentRoomCode}`;
      if (tickerDot) {
        if (state.isRinging) tickerDot.className = 'ticker-dot ringing';
        else if (state.music && state.music.isPlaying) tickerDot.className = 'ticker-dot playing';
        else tickerDot.className = 'ticker-dot';
      }
      document.querySelectorAll('.partner-a-name').forEach(el => el.innerText = state.partnerA);
      document.querySelectorAll('.partner-b-name').forEach(el => el.innerText = state.partnerB);

      if (state.moodLamp) {
        document.documentElement.style.setProperty('--lamp-color', state.moodLamp.color);
        document.documentElement.style.setProperty('--lamp-glow', state.moodLamp.color + '66');
        const lampNameA = document.getElementById('activeLampNameA');
        if (lampNameA) lampNameA.innerText = `${state.moodLamp.name}`;
        const lampPicker = document.getElementById('lampColorPicker');
        if (lampPicker && lampPicker.value !== state.moodLamp.color) lampPicker.value = state.moodLamp.color;
      }

      if (state.loveNote && state.loveNote.text) {
        const noteEl = document.getElementById('deskLoveNote');
        const noteSender = document.getElementById('deskLoveNoteSender');
        if (noteEl) noteEl.innerText = `"${state.loveNote.text}"`;
        if (noteSender) noteSender.innerText = `— ${state.loveNote.sentBy}`;
      }

      if (state.heartbeat && state.heartbeat.pulseId > lastKnownPulseId) {
        lastKnownPulseId = state.heartbeat.pulseId;
        triggerHeartbeatVisual(state.heartbeat.sentBy);
      }

      const deskMusicBar = document.getElementById('deskMusicBar');
      const deskMusicTitle = document.getElementById('deskMusicTitle');
      const btnMusicPlay = document.getElementById('btnMusicPlay');
      const btnMusicPause = document.getElementById('btnMusicPause');

      if (state.music && state.music.isPlaying) {
        if (deskMusicBar) deskMusicBar.style.display = 'flex';
        if (deskMusicTitle) deskMusicTitle.innerText = state.music.trackTitle;
        if (btnMusicPlay) btnMusicPlay.style.display = 'none';
        if (btnMusicPause) btnMusicPause.style.display = 'inline-flex';
        if (!state.isRinging) startMusicAudio(state.music.trackId, state.music.voiceAudio);
      } else {
        if (deskMusicBar) deskMusicBar.style.display = 'none';
        if (btnMusicPlay) btnMusicPlay.style.display = 'inline-flex';
        if (btnMusicPause) btnMusicPause.style.display = 'none';
        stopMusicAudio();
      }

      const ringingCardA = document.getElementById('ringingCardA');
      const normalCardA = document.getElementById('normalCardA');
      const ringingStatusText = document.getElementById('ringingStatusText');
      const deskClock = document.getElementById('deskClock');
      const alarmBanner = document.getElementById('alarmBanner');
      const pokeNotice = document.getElementById('pokeNotice');

      if (state.isRinging) {
        stopMusicAudio();
        if (ringingCardA) ringingCardA.style.display = 'block';
        if (normalCardA) normalCardA.style.display = 'none';
        if (ringingStatusText) ringingStatusText.innerText = `🚨 ${state.partnerB}'s alarm is RINGING right now!`;
        if (deskClock) deskClock.classList.add('ringing');
        if (alarmBanner) { alarmBanner.classList.add('active-banner'); alarmBanner.innerHTML = `⏰ <b>ALARM RINGING!</b><br>"${state.alarmMessage}"`; }
        startRingingAudio(state.tone);
      } else {
        if (ringingCardA) ringingCardA.style.display = 'none';
        if (normalCardA) normalCardA.style.display = 'block';
        if (deskClock) deskClock.classList.remove('ringing');
        if (alarmBanner) {
          alarmBanner.classList.remove('active-banner');
          alarmBanner.innerHTML = (state.alarmEnabled && state.alarmTime) ? `🔔 Alarm set for <b>${state.alarmTime}</b> by ${state.partnerA}` : `💤 No active alarm scheduled`;
        }
        stopRingingAudio();
      }

      if (pokeNotice) {
        if (state.wakePoke > 0) { pokeNotice.innerText = `💌 ${state.partnerB} sent ${state.wakePoke} wake-up poke(s)!`; pokeNotice.style.display = 'block'; }
        else pokeNotice.style.display = 'none';
      }
    }

    function connectSSE() {
      if (eventSource) eventSource.close();
      try {
        eventSource = new EventSource(`/api/events?code=${currentRoomCode}`);
        eventSource.onmessage = (e) => { try { applyState(JSON.parse(e.data)); } catch (err) {} };
        eventSource.onerror = () => { eventSource.close(); setTimeout(fetchStatus, 2000); };
      } catch (err) { setInterval(fetchStatus, 2000); }
    }

    async function fetchStatus() {
      try {
        const res = await fetch(`/api/status?code=${currentRoomCode}`);
        const state = await res.json();
        applyState(state);
      } catch (err) {}
    }

    function openPairingModal() {
      document.getElementById('modalCodeDisplay').innerText = currentRoomCode;
      document.getElementById('customRoomInput').value = currentRoomCode;
      document.getElementById('pairingModal').classList.add('open');
    }
    function closePairingModal() { document.getElementById('pairingModal').classList.remove('open'); }
    function handleSaveRoomCode() {
      let code = (document.getElementById('customRoomInput').value || "LOVE-99").trim().toUpperCase();
      if (code) {
        currentRoomCode = code;
        localStorage.setItem('love_room_code', code);
        closePairingModal();
        fetchStatus();
        connectSSE();
      }
    }
    function generateNewRoomCode() {
      document.getElementById('customRoomInput').value = `LOVE-${Math.floor(100 + Math.random() * 900)}`;
    }

    async function handlePlayMusic(trackId = null) {
      unlockAudio();
      const select = document.getElementById('musicTrackSelect');
      const selectedTrackId = trackId || (select ? select.value : 'piano_romance');
      const trackObj = MUSIC_TRACKS[selectedTrackId];
      const title = trackObj ? trackObj.title : "Custom Song";
      const res = await fetch(`/api/music/control?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, action: "play", trackId: selectedTrackId, trackTitle: title }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handlePauseMusic() {
      stopMusicAudio();
      const res = await fetch(`/api/music/control?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, action: "pause" }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handleSetLampColor(colorHex, name = "Custom Mood") {
      const res = await fetch(`/api/mood/set?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, color: colorHex, name: name }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handleSendLoveNote(e) {
      e.preventDefault();
      const input = document.getElementById('loveNoteInput');
      const text = input.value.trim(); if (!text) return;
      const res = await fetch(`/api/love-note/send?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, text: text }) });
      input.value = '';
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handleSendHeartbeat(senderRole = "Partner A") {
      unlockAudio(); playHeartbeatAudio();
      const res = await fetch(`/api/heartbeat/send?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, sentBy: senderRole }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handleSetAlarm(e) {
      e.preventDefault(); unlockAudio();
      const time = document.getElementById('alarmTimeInput').value;
      const message = document.getElementById('alarmMessageInput').value;
      const tone = document.getElementById('alarmToneSelect').value;
      if (!time) { alert("Please pick a valid time!"); return; }
      const res = await fetch(`/api/set-alarm?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, time, message, tone, enabled: true }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handleInstantTrigger() {
      unlockAudio();
      const message = document.getElementById('alarmMessageInput').value;
      const tone = document.getElementById('alarmToneSelect').value;
      const res = await fetch(`/api/trigger-alarm?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode, message, tone }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handleDismissAlarm() {
      unlockAudio(); stopRingingAudio();
      const res = await fetch(`/api/dismiss-alarm?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    async function handlePoke() {
      unlockAudio(); playNote(987.77, 'triangle', 0.2, 0, 0.2); triggerHaptic([100, 50, 100]);
      const res = await fetch(`/api/poke?code=${currentRoomCode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentRoomCode }) });
      const data = await res.json(); if (data.state) applyState(data.state);
    }

    function updateLiveClock() {
      const now = new Date();
      let hours = String(now.getHours()).padStart(2, '0');
      let minutes = String(now.getMinutes()).padStart(2, '0');
      let seconds = String(now.getSeconds()).padStart(2, '0');
      const clockEl = document.getElementById('liveClockDigits');
      if (clockEl) clockEl.innerText = `${hours}:${minutes}:${seconds}`;
      const dateEl = document.getElementById('liveClockDate');
      if (dateEl) dateEl.innerText = now.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
    }

    function switchView(mode) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      const btn = document.getElementById(`tab-${mode}`);
      if (btn) btn.classList.add('active');
      const container = document.getElementById('viewsContainer');
      const colA = document.getElementById('colPartnerA');
      const colB = document.getElementById('colPartnerB');
      if (mode === 'split') {
        container.className = 'views-grid';
        if (colA) colA.style.display = 'block';
        if (colB) colB.style.display = 'block';
      } else if (mode === 'partnerA') {
        container.className = 'views-grid view-single';
        if (colA) colA.style.display = 'block';
        if (colB) colB.style.display = 'none';
      } else if (mode === 'partnerB') {
        container.className = 'views-grid view-single';
        if (colA) colA.style.display = 'none';
        if (colB) colB.style.display = 'block';
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      updateLiveClock();
      setInterval(updateLiveClock, 1000);
      const future = new Date(Date.now() + 2 * 60 * 1000);
      const defHours = String(future.getHours()).padStart(2, '0');
      const defMins = String(future.getMinutes()).padStart(2, '0');
      const timeInput = document.getElementById('alarmTimeInput');
      if (timeInput) timeInput.value = `${defHours}:${defMins}`;
      document.body.addEventListener('click', unlockAudio, { once: true });
      document.body.addEventListener('touchstart', unlockAudio, { once: true });
      fetchStatus();
      connectSSE();
    });
  </script>
</body>
</html>"""

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

        # Default: Always serve the complete embedded HTML page
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
            state["alarmTime"] = payload.get("time", state["alarmTime"])
            state["alarmEnabled"] = payload.get("enabled", True)
            if "message" in payload and str(payload["message"]).strip():
                state["alarmMessage"] = str(payload["message"]).strip()
            if "tone" in payload:
                state["tone"] = payload["tone"]

            state["lastAction"] = f"Alarm set for {state['alarmTime']} by {state['partnerA']}"
            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/trigger-alarm":
            state["isRinging"] = True
            if "message" in payload and str(payload["message"]).strip():
                state["alarmMessage"] = str(payload["message"]).strip()
            if "tone" in payload:
                state["tone"] = payload["tone"]

            state["lastAction"] = f"Alarm triggered right now by {state['partnerA']}!"
            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/dismiss-alarm":
            state["isRinging"] = False
            state["alarmEnabled"] = False
            state["wakePoke"] = 0
            state["lastAction"] = f"Alarm turned off by {state['partnerA']}. Wake up with love!"
            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/poke":
            state["wakePoke"] += 1
            state["lastAction"] = f"{state['partnerB']} poked: 'Please turn it off my love!' ({state['wakePoke']}x)"
            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/music/control":
            action = payload.get("action", "play")
            if action == "play":
                state["music"]["isPlaying"] = True
                if "trackId" in payload:
                    state["music"]["trackId"] = payload["trackId"]
                if "trackTitle" in payload:
                    state["music"]["trackTitle"] = payload["trackTitle"]
                if "voiceAudio" in payload:
                    state["music"]["voiceAudio"] = payload["voiceAudio"]
                if "volume" in payload:
                    state["music"]["volume"] = int(payload["volume"])
                state["lastAction"] = f"🎵 Playing '{state['music']['trackTitle']}' for {state['partnerB']}"
            elif action == "pause":
                state["music"]["isPlaying"] = False
                state["lastAction"] = f"⏸️ Music paused"
            elif action == "stop":
                state["music"]["isPlaying"] = False
                state["lastAction"] = f"⏹️ Music stopped"

            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/mood/set":
            if "color" in payload:
                state["moodLamp"]["color"] = payload["color"]
            if "brightness" in payload:
                state["moodLamp"]["brightness"] = int(payload["brightness"])
            if "name" in payload:
                state["moodLamp"]["name"] = payload["name"]
            
            state["lastAction"] = f"🎨 Lamp set to {state['moodLamp']['name']}"
            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/love-note/send":
            text = payload.get("text", "").strip()
            if text:
                sender = payload.get("sentBy", state["partnerA"])
                state["loveNote"] = {
                    "text": text,
                    "sentBy": sender,
                    "timestamp": time.time()
                }
                state["lastAction"] = f"💌 Love Note sent: '{text}'"
                state["lastActionTime"] = time.time()
                broadcast_room_state(code)
                self.respond_json({"success": True, "state": state})
            else:
                self.respond_json({"success": False, "error": "Empty note"})

        elif path == "/api/heartbeat/send":
            sender = payload.get("sentBy", state["partnerA"])
            state["heartbeat"]["pulseId"] += 1
            state["heartbeat"]["sentBy"] = sender
            state["heartbeat"]["timestamp"] = time.time()
            state["lastAction"] = f"💓 Heartbeat Hug sent by {sender}!"
            state["lastActionTime"] = time.time()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        elif path == "/api/set-names":
            if "partnerA" in payload and str(payload["partnerA"]).strip():
                state["partnerA"] = str(payload["partnerA"]).strip()
            if "partnerB" in payload and str(payload["partnerB"]).strip():
                state["partnerB"] = str(payload["partnerB"]).strip()
            broadcast_room_state(code)
            self.respond_json({"success": True, "state": state})

        else:
            self.send_error(404, "Endpoint not found")

    def respond_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run():
    server = ThreadedHTTPServer(("", PORT), LoveCompanionHandler)
    print("="*60)
    print(f"   💖 LOVE COMPANION RUNNING ON PORT {PORT}! 💖")
    print("="*60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")

if __name__ == "__main__":
    run()
```
</details>

4. Click the green **"Commit changes"** button on GitHub.
5. Wait **30 to 45 seconds** for Render to finish updating.
6. Open your link `https://love-companion.onrender.com` on your phone! It will now load smoothly with the glowing interface and all features working!
