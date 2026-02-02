import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Pfad zur app.py innerhalb der EXE finden
    app_path = resolve_path("app.py")
    
    # Argumente fuer Streamlit setzen
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
    ]
    
    # Streamlit starten
    sys.exit(stcli.main())
