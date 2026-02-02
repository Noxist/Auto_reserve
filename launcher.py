import streamlit.web.cli as stcli
import os, sys
import threading
import time
import webbrowser

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

def open_browser():
    """Wartet kurz und öffnet dann den Browser"""
    time.sleep(2)
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    # Pfad zur app.py innerhalb der EXE finden
    app_path = resolve_path("app.py")
    
    # Browser im Hintergrund öffnen
    threading.Thread(target=open_browser, daemon=True).start()

    # Argumente für Streamlit setzen (Headless = kein Popup, wir öffnen Browser selbst)
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.port=8501",
    ]
    
    # Streamlit starten
    sys.exit(stcli.main())
