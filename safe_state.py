import json
import os
import secrets
import threading
import time

from werkzeug.security import check_password_hash, generate_password_hash

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safe_data.json")
DEFAULT_PASSWORD = "arthur123"       
MAX_EVENTS = 300

_lock = threading.RLock()             

settings = {
    "auto_lock_seconds": 120,  
    "max_wrong": 3,            
    "lockout_seconds": 30,     
    "alarm_armed": True,       
    "card_access": True,       
}
cards = []                      
events = []                     
password_hash = ""
secret_key = ""

live = {
    "locked": True,
    "unlocked_at": 0,
    "wrong_count": 0,
    "lockout_end": 0,
    "alarm_active": False,      
    "last_alarm": None,
    "learning": False,         
    "learning_until": 0,
    "lcd": ["Starting...", ""],
    "started": time.time(),
    "hardware": "starting",
    "distance": None,          
}

commands = []                  



def load(default_cards):
    global cards, events, password_hash, secret_key
    with _lock:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
            settings.update(data.get("settings", {}))
            cards = data.get("cards", [])
            events = data.get("events", [])
            password_hash = data.get("password_hash", "")
            secret_key = data.get("secret_key", "")

        if not cards:                        
            for number, card_id in enumerate(default_cards, start=1):
                cards.append({"id": str(card_id), "name": "Card " + str(number), "added": _now()})
        if not password_hash:
            password_hash = generate_password_hash(DEFAULT_PASSWORD)
        if not secret_key:
            secret_key = secrets.token_hex(32)
        save()


def save():
    with _lock:
        data = {
            "settings": settings,
            "cards": cards,
            "events": events,
            "password_hash": password_hash,
            "secret_key": secret_key,
        }
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, DATA_FILE)     


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")



def add_event(kind, text):
   
    with _lock:
        events.append({"time": _now(), "stamp": time.time(), "kind": kind, "text": text})
        del events[:-MAX_EVENTS]              
        save()


def clear_events():
    with _lock:
        events.clear()
        save()



def add_command(name, value=None):
    with _lock:
        commands.append((name, value))


def pop_commands():
    with _lock:
        waiting = list(commands)
        commands.clear()
        return waiting



def is_allowed(card_id):
    with _lock:
        return any(card["id"] == str(card_id) for card in cards)


def card_name(card_id):
    with _lock:
        for card in cards:
            if card["id"] == str(card_id):
                return card["name"]
        return "Unknown card"


def add_card(card_id):
    with _lock:
        if is_allowed(card_id):
            return False
        cards.append({"id": str(card_id), "name": "Card " + str(len(cards) + 1), "added": _now()})
        save()
        return True


def rename_card(card_id, new_name):
    with _lock:
        for card in cards:
            if card["id"] == str(card_id):
                card["name"] = new_name[:30]
                save()
                return True
        return False


def remove_card(card_id):
    global cards
    with _lock:
        before = len(cards)
        cards = [card for card in cards if card["id"] != str(card_id)]
        save()
        return len(cards) < before



LIMITS = {
    "auto_lock_seconds": (0, 3600),
    "max_wrong": (1, 10),
    "lockout_seconds": (5, 600),
}


def update_settings(new_values):
    numbers = {}
    for key, (low, high) in LIMITS.items():        
        if key in new_values:
            numbers[key] = max(low, min(high, int(new_values[key])))
    with _lock:                                     
        settings.update(numbers)
        for key in ("alarm_armed", "card_access"):
            if key in new_values:
                settings[key] = bool(new_values[key])
        save()


def check_password(password):
    return check_password_hash(password_hash, password)


def set_password(new_password):
    global password_hash
    with _lock:
        password_hash = generate_password_hash(new_password)
        save()



def snapshot():
    with _lock:
        now = time.time()
        auto_lock_left = None
        if not live["locked"] and settings["auto_lock_seconds"] > 0:
            auto_lock_left = max(0, int(live["unlocked_at"] + settings["auto_lock_seconds"] - now))

        today = time.strftime("%Y-%m-%d")
        todays = [event for event in events if event["time"].startswith(today)]
        return {
            "locked": live["locked"],
            "auto_lock_left": auto_lock_left,
            "lockout_left": max(0, int(live["lockout_end"] - now)),
            "wrong_count": live["wrong_count"],
            "alarm_active": live["alarm_active"],
            "last_alarm": live["last_alarm"],
            "learning": live["learning"],
            "lcd": live["lcd"],
            "hardware": live["hardware"],
            "distance": live["distance"],
            "uptime": int(now - live["started"]),
            "settings": dict(settings),
            "cards": [dict(card) for card in cards],
            "events": list(reversed(events[-100:])),       # newest first
            "today": {
                "unlocks": sum(1 for e in todays if e["kind"] == "unlock"),
                "denied": sum(1 for e in todays if e["kind"] == "denied"),
                "alarms": sum(1 for e in todays if e["kind"] == "alarm"),
            },
        }