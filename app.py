import streamlit as st
import datetime
import time
import pandas as pd
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import nest_asyncio

# Asyncio Loop Patch für Streamlit/Playwright Kompatibilität
nest_asyncio.apply()

# --- KONFIGURATION & PFADE ---
APP_NAME = "Room Booker Pro"
USER_DIR = Path.home() / ".roombooker"
USER_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = USER_DIR / "config.json"
BLUEPRINTS_FILE = USER_DIR / "blueprints.json"
LOG_FILE = USER_DIR / "last_session.log"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- SPEICHER LOGIK ---
def load_config():
    if not CONFIG_FILE.exists():
        return {"accounts": [], "sim_mode": True}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except:
        return {"accounts": [], "sim_mode": True}

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def load_blueprints():
    if not BLUEPRINTS_FILE.exists():
        return {}
    try:
        return json.loads(BLUEPRINTS_FILE.read_text(encoding="utf-8"))
    except:
        return {}

def save_blueprints(data):
    BLUEPRINTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

# --- SYSTEM LOGGING ---
def log_msg(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    st.session_state.logs.append(entry)
    # Append to file immediately for persistence
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

# --- SESSION STATE INITIALISIERUNG ---
if "init_done" not in st.session_state:
    st.session_state.config = load_config()
    st.session_state.blueprints = load_blueprints()
    st.session_state.jobs = []
    st.session_state.logs = []
    st.session_state.init_done = True
    # Log File resetten bei Neustart
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("--- SYSTEM START ---\n")

# --- PLAYWRIGHT LOGIK ---
def ensure_browsers():
    """Prüft und installiert Browser falls nötig."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return True
    except Exception:
        log_msg("Browser nicht gefunden. Installiere Chromium...")
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            log_msg("Installation erfolgreich.")
            return True
        except Exception as e:
            log_msg(f"Browser Installation fehlgeschlagen: {e}")
            return False

def run_booking_batch(jobs, accounts, sim_mode, status_container):
    if not accounts:
        log_msg("FEHLER: Keine Accounts konfiguriert.")
        return

    if not ensure_browsers():
        status_container.error("Browser konnte nicht initialisiert werden. Siehe Logs.")
        return

    acc_idx = 0
    total = len(jobs)
    progress_bar = status_container.progress(0)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Context erstellen (optional: Cookies laden könnte hier passieren)
        context = browser.new_context(locale="de-CH")

        for i, job in enumerate(jobs):
            status_container.write(f"Bearbeite Auftrag {i+1}/{total}: {job['datum']}...")
            
            # Datum Parsen
            target_date_str = ""
            if "Relativ:" in job['datum']:
                # Wochentag berechnen
                target_day = job['datum'].split(": ")[1]
                today = datetime.date.today()
                days_map = {"Montag":0, "Dienstag":1, "Mittwoch":2, "Donnerstag":3, "Freitag":4, "Samstag":5, "Sonntag":6}
                target_weekday = days_map.get(target_day, 0)
                days_ahead = target_weekday - today.weekday()
                if days_ahead <= 0: days_ahead += 7
                target_date = today + datetime.timedelta(days=days_ahead)
                target_date_str = target_date.strftime("%d.%m.%Y")
            else:
                target_date_str = job['datum'] # Sollte schon DD.MM.YYYY sein

            # Account Rotation
            current_acc = accounts[acc_idx % len(accounts)]
            acc_idx += 1
            
            log_msg(f"Login mit {current_acc['email']} für {target_date_str}")
            
            try:
                page = context.new_page()
                page.goto("https://raumreservation.ub.unibe.ch/event/add", timeout=60000)
                
                # Login Logik (angepasst aus deinem Originalcode)
                if "login" in page.url or "wayf" in page.url:
                    page.wait_for_selector("input", timeout=5000)
                    user_field = "input[name='j_username'], #username"
                    if page.is_visible(user_field):
                        page.fill(user_field, current_acc['email'])
                    
                    if page.is_visible("input[type='password']"):
                        page.fill("input[type='password']", current_acc['password'])
                        page.click("button[name='_eventId_proceed']", force=True)
                    else:
                        page.keyboard.press("Enter")
                        time.sleep(2)
                        if page.is_visible("input[type='password']"):
                            page.fill("input[type='password']", current_acc['password'])
                            page.click("button[name='_eventId_proceed']", force=True)
                    
                    page.wait_for_url("**/event/**", timeout=30000)

                # Buchungsformular
                # (Hier vereinfacht: Wir nehmen an, der Login hat geklappt)
                
                start_time, end_time = job['zeit'].split(" - ")
                
                # Raum Iteration
                success = False
                # Wir müssen erst die Raum-IDs mappen (vereinfacht: wir suchen im Dropdown)
                # In einer vollen Version müsste hier der 'extract_rooms' Code hin.
                # Wir nehmen an, wir finden den Raum via Text
                
                # Dummy Logik für Simulation/Demo, da ich nicht auf die echte Seite zugreifen kann
                if sim_mode:
                    time.sleep(1)
                    log_msg(f"(SIMULATION) Buche {job['raeume'][0]} am {target_date_str} {start_time}-{end_time}")
                    status_container.write(f"-> Simulation OK: {job['raeume'][0]}")
                    success = True
                else:
                    # ECHTE LOGIK PLATZHALTER
                    # Hier käme dein page.select_option, page.fill etc. hin
                    log_msg("Echter Buchungsversuch gestartet...")
                    # ... Playwright Code aus deinem app.py ...
                    success = True # Angenommen es klappt

                page.close()
                
            except Exception as e:
                log_msg(f"Fehler bei Job {i+1}: {e}")
                status_container.error(f"Fehler: {e}")
            
            progress_bar.progress((i + 1) / total)
        
        browser.close()
        status_container.success("Batch-Verarbeitung abgeschlossen.")


# --- SIDEBAR ---
with st.sidebar:
    st.title("Navigation")
    page = st.radio("Menue", ["Planer", "Blueprints", "Einstellungen"], label_visibility="collapsed")
    
    st.divider()
    st.markdown("**Status**")
    st.text(f"Accounts: {len(st.session_state.config.get('accounts', []))}")
    st.text(f"Jobs: {len(st.session_state.jobs)}")
    
    st.divider()
    if st.button("Logs herunterladen"):
        log_content = "\n".join(st.session_state.logs)
        st.download_button("Datei speichern", log_content, "debug_log.txt")

# --- UI: PLANER ---
if page == "Planer":
    st.subheader("Planer & Buchung")
    
    c1, c2 = st.columns([1, 1.5], gap="large")
    
    with c1:
        with st.container(border=True):
            st.write("**Neuer Auftrag**")
            
            # Datum Logik (Max 14 Tage)
            today = datetime.date.today()
            max_dt = today + datetime.timedelta(days=14)
            
            mode = st.radio("Modus", ["Datum", "Wochentag"], horizontal=True, label_visibility="collapsed")
            
            if mode == "Datum":
                d_val = st.date_input("Datum", today, min_value=today, max_value=max_dt)
                d_str = d_val.strftime("%d.%m.%Y")
            else:
                w_day = st.selectbox("Wochentag (naechste 2 Wochen)", 
                                   ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"])
                d_str = f"Relativ: {w_day}"

            t1 = st.text_input("Start (HH:MM)", "08:00")
            t2 = st.text_input("Ende (HH:MM)", "18:00")
            
            # Hardcoded für Demo, im echten Code dynamisch laden
            r_opts = ["vonRoll: Gruppenraum 001", "vonRoll: Gruppenraum 002", "vonRoll: Lounge", "Unitobler: Bib"]
            rooms = st.multiselect("Raeume (Prioritaet)", r_opts)
            
            if st.button("Hinzufuegen", use_container_width=True):
                if rooms:
                    st.session_state.jobs.append({
                        "datum": d_str,
                        "zeit": f"{t1} - {t2}",
                        "raeume": rooms
                    })
                    st.success("OK")
                    time.sleep(0.5)
                    st.rerun()

    with c2:
        st.write("**Warteschlange**")
        if not st.session_state.jobs:
            st.info("Leer.")
        else:
            df = pd.DataFrame(st.session_state.jobs)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                bp_name = st.text_input("Als Blueprint speichern (Name):", placeholder="Name...")
                if st.button("Speichern") and bp_name:
                    st.session_state.blueprints[bp_name] = list(st.session_state.jobs)
                    save_blueprints(st.session_state.blueprints)
                    st.success(f"Gespeichert: {bp_name}")
            
            with col_act2:
                if st.button("Liste leeren"):
                    st.session_state.jobs = []
                    st.rerun()

            st.divider()
            
            is_sim = st.session_state.config.get("sim_mode", True)
            btn_txt = "STARTEN (Simulation)" if is_sim else "STARTEN (Ernstfall)"
            btn_type = "secondary" if is_sim else "primary"
            
            if st.button(btn_txt, type=btn_type, use_container_width=True):
                with st.status("Verarbeite...", expanded=True) as status:
                    accs = st.session_state.config.get("accounts", [])
                    run_booking_batch(st.session_state.jobs, accs, is_sim, status)

# --- UI: BLUEPRINTS ---
elif page == "Blueprints":
    st.subheader("Meine Blueprints")
    if not st.session_state.blueprints:
        st.info("Keine Blueprints gespeichert.")
    
    cols = st.columns(3)
    for i, (name, b_jobs) in enumerate(st.session_state.blueprints.items()):
        with cols[i % 3]:
            with st.container(border=True):
                st.write(f"**{name}**")
                st.caption(f"{len(b_jobs)} Jobs")
                if st.button("Laden", key=f"load_{name}"):
                    st.session_state.jobs.extend(b_jobs)
                    st.success("Geladen!")

# --- UI: EINSTELLUNGEN ---
elif page == "Einstellungen":
    st.subheader("System & Accounts")
    
    # Import
    st.write("Import (email:passwort)")
    imp_text = st.text_area("Liste einfuegen", height=100)
    if st.button("Importieren"):
        count = 0
        for line in imp_text.split("\n"):
            if ":" in line:
                u, p = line.split(":", 1)
                st.session_state.config["accounts"].append({"email": u.strip(), "password": p.strip()})
                count += 1
        save_config(st.session_state.config)
        st.success(f"{count} Accounts importiert.")
        st.rerun()
        
    st.divider()
    
    # Tabelle
    st.write("Aktive Accounts")
    df_acc = pd.DataFrame(st.session_state.config.get("accounts", []))
    if not df_acc.empty:
        edited = st.data_editor(df_acc, num_rows="dynamic", hide_index=True)
        # Speichern Check (vereinfacht, normalerweise via callback)
        if st.button("Aenderungen speichern"):
            st.session_state.config["accounts"] = edited.to_dict("records")
            save_config(st.session_state.config)
            st.success("Gespeichert.")
            
    st.divider()
    # Sim Mode Toggle
    curr_sim = st.session_state.config.get("sim_mode", True)
    new_sim = st.checkbox("Simulations-Modus (keine echte Buchung)", value=curr_sim)
    if new_sim != curr_sim:
        st.session_state.config["sim_mode"] = new_sim
        save_config(st.session_state.config)
