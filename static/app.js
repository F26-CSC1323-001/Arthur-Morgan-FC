let state = null;       
let filter = "all";      
let waiting = false;    
let settingsFilled = false;
let lastCardCount = null;

function el(id) {
  return document.getElementById(id);
}


async function api(url, method = "GET", body = null) {
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  if (response.status === 401) {          
    location.href = "/login";
    return null;
  }
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || "Something went wrong");
  return data;
}

async function send(url, body, message) {
  try {
    await api(url, "POST", body);
    if (message) toast(message);
    refresh();
    return true;
  } catch (error) {
    toast(error.message, true);
    return false;
  }
}


function toast(text, isError = false) {
  const box = document.createElement("div");
  box.className = isError ? "toast error" : "toast";
  box.textContent = text;
  el("toasts").appendChild(box);
  setTimeout(() => box.remove(), 3000);
}


function render(s) {
  // status box
  if (state && state.locked !== s.locked) waiting = false;     // servo finished
  el("status-box").className = s.locked ? "box status locked" : "box status open";
  el("status-text").textContent = s.locked ? "LOCKED" : "OPEN";

  let sub = "Everything inside is secure.";
  if (!s.locked && s.auto_lock_left !== null) sub = "Locks by itself in " + s.auto_lock_left + " seconds.";
  else if (!s.locked) sub = "Auto-lock is off. Remember to lock it.";
  else if (!s.settings.card_access) sub = "Lockdown: cards are off, only the website can open it.";
  else if (s.lockout_left > 0) sub = "Card reader locked out for " + s.lockout_left + " seconds.";
  el("status-sub").textContent = sub;
  el("distance-text").textContent = s.distance === null ? "Distance: no reading" : "Distance: " + s.distance + " cm";

  const showBar = !s.locked && s.auto_lock_left !== null;
  el("countdown").style.display = showBar ? "block" : "none";
  if (showBar) el("countdown-bar").style.width = (100 * s.auto_lock_left / s.settings.auto_lock_seconds) + "%";

  if (!waiting) {
    el("main-btn").disabled = false;
    el("main-btn").textContent = s.locked ? "Unlock safe" : "Lock safe";
  }


  el("alarm-banner").style.display = s.alarm_active ? "flex" : "none";
  if (s.alarm_active) el("alarm-time").textContent = "Someone shook the safe at " + s.last_alarm + ".";

  
  el("s-unlocks").textContent = s.today.unlocks;
  el("s-denied").textContent = s.today.denied;
  el("s-alarms").textContent = s.today.alarms;
  el("t-alarm").checked = s.settings.alarm_armed;
  el("t-cards").checked = s.settings.card_access;

  
  el("lcd1").textContent = s.lcd[0] || "";
  el("lcd2").textContent = s.lcd[1] || "";


  el("a-lockout").disabled = s.lockout_left <= 0;
  el("lockout-text").textContent = s.lockout_left > 0 ? "Lockout: " + s.lockout_left + " seconds left" : "No lockout right now";

  
  el("learn-modal").style.display = s.learning ? "flex" : "none";
  if (lastCardCount !== null && s.cards.length > lastCardCount) toast("New card added");
  lastCardCount = s.cards.length;

  showCards(s.cards);
  showHistory(s.events);

  
  if (!settingsFilled) {
    el("f-auto").value = s.settings.auto_lock_seconds;
    el("f-wrong").value = s.settings.max_wrong;
    el("f-lockout").value = s.settings.lockout_seconds;
    settingsFilled = true;
  }
  el("uptime").textContent = "Safe running for " + Math.floor(s.uptime / 60) + " min";
}

function showCards(cards) {
  
  let html = "";
  for (const card of cards) {
    html += "<div class='rfid-card'>" +
            "<div class='chip'></div>" +
            "<b>" + clean(card.name) + "</b>" +
            "<span>" + card.id + "</span>" +
            "<div class='card-buttons'>" +
            "<button data-rename='" + card.id + "'>Rename</button>" +
            "<button data-remove='" + card.id + "'>Remove</button>" +
            "</div></div>";
  }
  if (el("cards").innerHTML !== html) el("cards").innerHTML = html;   
}

function showHistory(events) {
  
  let html = "";
  for (const event of events) {
    if (filter !== "all" && !filter.split(" ").includes(event.kind)) continue;
    html += "<li class='" + event.kind + "'><span class='time'>" + event.time.slice(5) + "</span>" +
            clean(event.text) + "</li>";
  }
  if (html === "") html = "<li>Nothing yet</li>";
  if (el("log").innerHTML !== html) el("log").innerHTML = html;
}


function clean(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}


async function refresh() {
  try {
    const s = await api("/api/state");
    if (!s) return;
    render(s);
    state = s;
    el("conn").textContent = "Online";
    el("conn").className = "online";
  } catch (error) {
    el("conn").textContent = "Offline";
    el("conn").className = "offline";
  }
}


el("main-btn").onclick = function () {
  if (!state) return;
  const action = state.locked ? "unlock" : "lock";
  waiting = true;
  el("main-btn").disabled = true;
  el("main-btn").textContent = action === "unlock" ? "Unlocking..." : "Locking...";
  setTimeout(() => (waiting = false), 4000);      
  send("/api/command", { action: action });
};

el("ack-btn").onclick = () => send("/api/alarm/ack", {}, "Alarm cleared");
el("a-beep").onclick = () => send("/api/command", { action: "beep" }, "Beeping");
el("a-test").onclick = () => send("/api/command", { action: "test_alarm" }, "Testing alarm");
el("a-lockout").onclick = () => send("/api/lockout/clear", {}, "Lockout cleared");
el("a-learn").onclick = () => send("/api/command", { action: "learn_on" });
el("add-card-btn").onclick = () => send("/api/command", { action: "learn_on" });
el("learn-cancel").onclick = () => send("/api/command", { action: "learn_off" });

el("t-alarm").onchange = (e) => send("/api/settings", { alarm_armed: e.target.checked }, "Saved");
el("t-cards").onchange = (e) => send("/api/settings", { card_access: e.target.checked }, "Saved");

el("msg-form").onsubmit = async (e) => {
  e.preventDefault();
  if (await send("/api/command", { action: "message", text: el("msg-input").value }, "Sent")) {
    el("msg-input").value = "";
  }
};

el("settings-form").onsubmit = (e) => {
  e.preventDefault();
  send("/api/settings", {
    auto_lock_seconds: el("f-auto").value,
    max_wrong: el("f-wrong").value,
    lockout_seconds: el("f-lockout").value,
  }, "Settings saved");
};

el("pw-form").onsubmit = async (e) => {
  e.preventDefault();
  if (await send("/api/password", { old: el("pw-old").value, new: el("pw-new").value }, "Password changed")) {
    el("pw-old").value = "";
    el("pw-new").value = "";
  }
};

el("clear-log").onclick = () => {
  if (confirm("Clear all history?")) send("/api/events/clear", {}, "History cleared");
};

el("chips").onclick = (e) => {
  if (e.target.tagName !== "BUTTON") return;
  for (const b of el("chips").children) b.classList.remove("active");
  e.target.classList.add("active");
  filter = e.target.dataset.f;
  if (state) showHistory(state.events);
};

el("cards").onclick = async (e) => {
  const id = e.target.dataset.rename || e.target.dataset.remove;
  if (!id) return;
  try {
    if (e.target.dataset.rename) {
      const name = prompt("New name for this card:");
      if (name) await api("/api/cards/" + id, "PATCH", { name: name });
    } else if (confirm("Remove this card?")) {
      await api("/api/cards/" + id, "DELETE");
    }
    refresh();
  } catch (error) {
    toast(error.message, true);
  }
};


function showThemeButton() {
  const light = document.documentElement.dataset.theme === "light";
  el("theme-btn").textContent = light ? "Dark mode" : "Light mode";
}

el("theme-btn").onclick = () => {
  const light = document.documentElement.dataset.theme === "light";
  const next = light ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch (e) {}   // remember it for next time
  showThemeButton();
};

showThemeButton();
refresh();
setInterval(refresh, 1000);
