import http.server
import socketserver
import json
import os
import sys
import mimetypes
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

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

def find_file(filename):
    candidates = [
        os.path.join(STATIC_DIR, filename),
        os.path.join(BASE_DIR, filename),
        os.path.join(STATIC_DIR, os.path.basename(filename)),
        os.path.join(BASE_DIR, os.path.basename(filename))
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.isfile(path):
            return path
    return None

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

        elif path == "/" or path == "/index.html":
            file_path = find_file("index.html")
            if file_path:
                self.serve_file(file_path, "text/html; charset=utf-8")
                return

        elif path == "/manifest.json":
            file_path = find_file("manifest.json")
            if file_path:
                self.serve_file(file_path, "application/manifest+json")
                return

        elif path == "/sw.js":
            file_path = find_file("sw.js")
            if file_path:
                self.serve_file(file_path, "application/javascript")
                return

        clean_name = path.replace("/static/", "").lstrip("/")
        file_path = find_file(clean_name)
        if file_path:
            mime, _ = mimetypes.guess_type(file_path)
            if file_path.endswith(".svg"):
                mime = "image/svg+xml"
            elif file_path.endswith(".css"):
                mime = "text/css"
            elif file_path.endswith(".js"):
                mime = "application/javascript"
            self.serve_file(file_path, mime or "application/octet-stream")
            return

        self.send_error(404, f"File not found: {path}")

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

    def serve_file(self, file_path, content_type):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

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
