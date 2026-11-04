
import threading
import time
from functools import wraps

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for

import safe_state
import camera

PORT = 5000
MAX_LOGIN_TRIES = 5      
LOGIN_WAIT_SECONDS = 60

app = Flask(__name__)
login_fails = {"count": 0, "wait_until": 0}



def login_required(page):
    
    @wraps(page)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify(ok=False, error="Please log in"), 401
            return redirect(url_for("login"))
        return page(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if time.time() < login_fails["wait_until"]:
            seconds = int(login_fails["wait_until"] - time.time())
            error = "Too many tries. Wait " + str(seconds) + " seconds."
        elif safe_state.check_password(request.form.get("password", "")):
            login_fails["count"] = 0
            session["logged_in"] = True
            session.permanent = True
            safe_state.add_event("system", "Website login from " + request.remote_addr)
            return redirect(url_for("home"))
        else:
            login_fails["count"] += 1
            error = "Wrong password."
            if login_fails["count"] >= MAX_LOGIN_TRIES:
                login_fails["count"] = 0
                login_fails["wait_until"] = time.time() + LOGIN_WAIT_SECONDS
                safe_state.add_event("alarm", "Too many wrong website passwords from "
                                     + request.remote_addr)
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/")
@login_required
def home():
    return render_template("index.html")



@app.route("/camera")
@login_required
def camera_feed():
    return Response(camera.video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/state")
@login_required
def get_state():
    return jsonify(safe_state.snapshot())


@app.route("/api/command", methods=["POST"])
@login_required
def command():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    allowed = ["unlock", "lock", "beep", "test_alarm", "learn_on", "learn_off", "message"]
    if action not in allowed:
        return jsonify(ok=False, error="Unknown action"), 400

    if action == "message":
        text = str(data.get("text", "")).strip()
        if not text:
            return jsonify(ok=False, error="Type a message first"), 400
        safe_state.add_command("message", text[:16] + "\n" + text[16:32])
        safe_state.add_event("system", "LCD message: " + text[:32])
    else:
        safe_state.add_command(action)
    return jsonify(ok=True)


@app.route("/api/alarm/ack", methods=["POST"])
@login_required
def acknowledge_alarm():
    safe_state.live["alarm_active"] = False
    safe_state.add_event("system", "Alarm acknowledged")
    return jsonify(ok=True)


@app.route("/api/lockout/clear", methods=["POST"])
@login_required
def clear_lockout():
    safe_state.live["lockout_end"] = 0
    safe_state.live["wrong_count"] = 0
    safe_state.add_event("system", "Lockout cleared from website")
    safe_state.add_command("refresh_lcd")
    return jsonify(ok=True)


@app.route("/api/settings", methods=["POST"])
@login_required
def change_settings():
    data = request.get_json(silent=True) or {}
    try:
        safe_state.update_settings(data)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Settings must be numbers"), 400
    changed = ", ".join(key.replace("_", " ") for key in data)
    safe_state.add_event("settings", "Changed: " + changed)
    safe_state.add_command("refresh_lcd")       
    return jsonify(ok=True)


@app.route("/api/cards/<card_id>", methods=["PATCH", "DELETE"])
@login_required
def edit_card(card_id):
    if request.method == "DELETE":
        if len(safe_state.cards) <= 1:
            return jsonify(ok=False, error="Keep at least one card"), 400
        name = safe_state.card_name(card_id)
        if not safe_state.remove_card(card_id):
            return jsonify(ok=False, error="Card not found"), 404
        safe_state.add_event("card", "Card removed: " + name)
        return jsonify(ok=True)

    new_name = str((request.get_json(silent=True) or {}).get("name", "")).strip()
    if not new_name:
        return jsonify(ok=False, error="Name can't be empty"), 400
    if not safe_state.rename_card(card_id, new_name):
        return jsonify(ok=False, error="Card not found"), 404
    return jsonify(ok=True)


@app.route("/api/events/clear", methods=["POST"])
@login_required
def clear_events():
    safe_state.clear_events()
    safe_state.add_event("system", "Activity log cleared")
    return jsonify(ok=True)


@app.route("/api/password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    if not safe_state.check_password(data.get("old", "")):
        return jsonify(ok=False, error="Current password is wrong"), 400
    new = data.get("new", "")
    if len(new) < 6:
        return jsonify(ok=False, error="New password needs 6+ characters"), 400
    safe_state.set_password(new)
    safe_state.add_event("settings", "Website password changed")
    return jsonify(ok=True)


def start_server():
    camera.start_camera()
   
    app.secret_key = safe_state.secret_key
    app.permanent_session_lifetime = 60 * 60 * 24 * 7      
    server = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=PORT, threaded=True),
        daemon=True,
    )
    server.start()
    print("[web] Website running on port", PORT, "- open http://<pi-ip>:" + str(PORT))
