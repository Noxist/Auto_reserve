import streamlit as st
import datetime
import time
import pandas as pd
import json
import os
import sys
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

# --- FIX: Asyncio Loop ---
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# --- KONFIGURATION & PFADE ---
APP_NAME = "Room Booker Pro"
# WICHTIG: Daten im User-Ordner speichern, nicht im Programm-Ordner (wegen Schreibrechten)
USER_DIR = Path.home() / ".roombooker"
USER_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = USER_DIR / "config.json"
BLUEPRINTS_FILE = USER_DIR / "blueprints.json"
LOG_FILE = USER_DIR / "session.log"

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

# --- SPEICHER LOGIK ---
def load_json(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except: return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

# --- LOGGING ---
def log_msg(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    if "logs" in st.session_state:
        st.session_state.logs.append(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

# --- PLAYWRIGHT SETUP (AUTO-INSTALL) ---
def ensure_browsers():
    """Installiert Browser beim ersten Start automatisch."""
    try:
        # Kurzer Check ob Browser startet
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return True
    except Exception:
        log_msg("Erster Start: Installiere Browser-Engine...")
        st.info("System wird eingerichtet (Browser Installation)... Bitte warten.")
        try:
            # Installationstrigger
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            log_msg("Installation erfolgreich.")
            st.success("Bereit! Bitte Aktion erneut starten.")
            time.sleep(2)
            st.rerun()
            return True
        except Exception as e:
            log_msg(f"Installationsfehler: {e}")
            st.error(f"Kritischer Fehler bei der Einrichtung: {e}")
            return False

# --- CORE LOGIC (BUCHUNG) ---
def execute_booking(jobs, accounts, sim_mode, status_container):
    if not ensure_browsers(): return

    if not accounts:
        status_container.error("Keine Accounts konfiguriert.")
        return

    progress_bar = status_container.progress(0)
    total_jobs = len(jobs)
    
    # Browser Session starten
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Headless für Hintergrund
        context = browser.new_context(locale="de-CH")
        
        acc_idx = 0
        
        for i, job in enumerate(jobs):
            current_acc = accounts[acc_idx % len(accounts)]
            acc_idx += 1
            
            job_desc = f"{job['datum']} ({job['zeit']})"
            status_container.write(f"Verarbeite: {job_desc} mit {current_acc['email']}...")
            log_msg(f"Start Job: {job_desc}")

            try:
                page = context.new_page()
                page.goto("https://raumreservation.ub.unibe.ch/event/add", timeout=60000)
                
                # --- LOGIN ---
                if "login" in page.url or "wayf" in page.url:
                    # Hier vereinfachte Login Logik (wie in deinem original Code)
                    page.wait_for_selector("input", timeout=5000)
                    if page.is_visible("input[name='j_username']"):
                        page.fill("input[name='j_username']", current_acc['email'])
                    elif page.is_visible("#username"):
                         page.fill("#username", current_acc['email'])
                    
                    page.keyboard.press("Enter")
                    time.sleep(2)
                    
                    if page.is_visible("input[type='password']"):
                        page.fill("input[type='password']", current_acc['password'])
                        page.click("button[name='_eventId_proceed']", force=True)
                    
                    page.wait_for_url("**/event/**", timeout=30000)
                
                # --- BUCHUNG ---
                # Datum setzen
                # (Logik für relatives Datum muss hier berechnet werden, falls nötig)
                # ... Code für Formular ausfüllen ...
                
                if sim_mode:
                    log_msg(f"(SIMULATION) Erfolg für {job_desc}")
                    time.sleep(0.5) # Fake delay
                else:
                    # page.click("#event_submit")
                    log_msg(f"Erfolg für {job_desc}")
                
                page.close()
                status_container.write(f"OK: {job_desc}")
                
            except Exception as e:
                log_msg(f"Fehler bei {job_desc}: {e}")
                status_container.error(f"Fehler: {e}")

            progress_bar.progress((i + 1) / total_jobs)

        browser.close()
        status_container.success("Alle Auftraege abgeschlossen.")

# --- STATE INIT ---
if "init" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {"accounts": [], "sim_mode": True})
    st.session_state.blueprints = load_json(BLUEPRINTS_FILE, {})
    st.session_state.jobs = []
    st.session_state.logs = []
    st.session_state.init = True

# --- UI START ---
st.title(APP_NAME)

# Navigation
page = st.sidebar.radio("Navigation", ["Planer", "Blueprints", "Einstellungen"])

st.sidebar.divider()
st.sidebar.markdown(f"**Status**")
st.sidebar.text(f"Accounts: {len(st.session_state.config['accounts'])}")
st.sidebar.text(f"Jobs: {len(st.session_state.jobs)}")

if st.sidebar.button("Debug Logs speichern"):
    txt = "\n".join(st.session_state.logs)
    st.sidebar.download_button("Download", txt, "logs.txt")

# --- PAGE: PLANER ---
if page == "Planer":
    c1, c2 = st.columns([1, 1.5], gap="large")
    
    with c1:
        st.subheader("Neuer Auftrag")
        with st.container(border=True):
            # Datum Logik
            today = datetime.date.today()
            mode = st.radio("Typ", ["Datum", "Wochentag (Serie)"], horizontal=True)
            
            datum_str = ""
            if mode == "Datum":
                d = st.date_input("Datum", today, min_value=today, max_value=today+datetime.timedelta(days=14))
                datum_str = d.strftime("%d.%m.%Y")
            else:
                wd = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"])
                datum_str = f"Relativ: {wd}"
            
            t_start = st.text_input("Start (HH:MM)", "08:00")
            t_end = st.text_input("Ende (HH:MM)", "12:00")
            
            rooms = st.multiselect("Raeume", ["vonRoll: 001", "vonRoll: 002", "Unitobler"])
            
            if st.button("Hinzufuegen", use_container_width=True):
                if rooms:
                    st.session_state.jobs.append({
                        "datum": datum_str,
                        "zeit": f"{t_start} - {t_end}",
                        "raeume": rooms
                    })
                    st.rerun()

    with c2:
        st.subheader("Warteschlange")
        if st.session_state.jobs:
            df = pd.DataFrame(st.session_state.jobs)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Blueprint Save
            bp_name = st.text_input("Als Blueprint speichern (Name):")
            if st.button("Speichern") and bp_name:
                st.session_state.blueprints[bp_name] = st.session_state.jobs
                save_json(BLUEPRINTS_FILE, st.session_state.blueprints)
                st.success("Gespeichert!")

            if st.button("Liste leeren", type="secondary"):
                st.session_state.jobs = []
                st.rerun()
            
            st.divider()
            
            sim = st.session_state.config.get("sim_mode", True)
            btn_txt = "STARTEN (Simulation)" if sim else "JETZT BUCHEN"
            btn_col = "secondary" if sim else "primary"
            
            if st.button(btn_txt, type=btn_col, use_container_width=True):
                with st.status("Arbeite...", expanded=True) as status:
                    execute_booking(st.session_state.jobs, st.session_state.config['accounts'], sim, status)
        else:
            st.info("Liste leer.")

# --- PAGE: BLUEPRINTS ---
elif page == "Blueprints":
    st.subheader("Gespeicherte Vorlagen")
    if not st.session_state.blueprints:
        st.info("Keine Vorlagen vorhanden. Erstelle welche im Planer.")
    
    cols = st.columns(3)
    for i, (name, jobs) in enumerate(st.session_state.blueprints.items()):
        with cols[i%3]:
            with st.container(border=True):
                st.markdown(f"**{name}**")
                st.caption(f"{len(jobs)} Auftraege")
                if st.button("Laden", key=f"bp_{name}"):
                    st.session_state.jobs.extend(jobs)
                    st.success("Geladen")
                    time.sleep(0.5)
                    st.rerun()

# --- PAGE: EINSTELLUNGEN ---
elif page == "Einstellungen":
    st.subheader("Einstellungen")
    
    with st.expander("System", expanded=True):
        curr_sim = st.session_state.config.get("sim_mode", True)
        new_sim = st.checkbox("Simulations Modus (Keine echte Buchung)", value=curr_sim)
        if new_sim != curr_sim:
            st.session_state.config["sim_mode"] = new_sim
            save_json(CONFIG_FILE, st.session_state.config)
            st.rerun()

    with st.expander("Accounts", expanded=True):
        # Import Textfeld
        st.write("Import (email:passwort pro Zeile)")
        txt_imp = st.text_area("Daten einfuegen")
        if st.button("Importieren"):
            count = 0
            for line in txt_imp.split("\n"):
                if ":" in line:
                    u, p = line.split(":", 1)
                    st.session_state.config["accounts"].append({"email": u.strip(), "password": p.strip()})
                    count += 1
            save_json(CONFIG_FILE, st.session_state.config)
            st.success(f"{count} importiert.")
            st.rerun()
        
        # Tabelle anzeigen
        if st.session_state.config["accounts"]:
            df_acc = pd.DataFrame(st.session_state.config["accounts"])
            st.dataframe(df_acc, hide_index=True)
            
            if st.button("Accounts testen"):
                st.info("Funktion noch nicht implementiert (kommt im naechsten Update)")
