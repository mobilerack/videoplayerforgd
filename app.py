import streamlit as st
import os
import json
from gdown import download as gdown_download

# --- Fájl- és Beállításkezelés (Változatlan) ---
TEMP_DIR = "data"
os.makedirs(TEMP_DIR, exist_ok=True)
VIDEO_PATH = os.path.join(TEMP_DIR, "video.mp4")
SUBTITLE_PATH = os.path.join(TEMP_DIR, "subtitle.vtt")
SETTINGS_FILE = os.path.join(TEMP_DIR, "settings.json")

# Alapértelmezett beállítások
DEFAULT_SETTINGS = {
    "color": "#FFFFFF",
    "size": "medium",
    "background": "transparent",
    "position": "bottom"
}

# --- Beállításkezelő Függvények (Változatlan) ---

def load_settings():
    """Beolvassa a mentett felirat beállításokat a JSON fájlból."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_SETTINGS

def save_settings(settings):
    """Elmenti a felirat beállításokat a JSON fájlba."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

# --- Letöltő Függvény (Módosítva) ---

def download_files(video_link, subtitle_link):
    """
    Letölti a videót és a feliratfájlt.
    A státusz üzeneteket egy listában adja vissza.
    """
    results = []
    
    # 1. Töröljük a korábbi fájlokat
    if os.path.exists(VIDEO_PATH): os.remove(VIDEO_PATH)
    if os.path.exists(SUBTITLE_PATH): os.remove(SUBTITLE_PATH)
    
    # 2. Videó letöltése
    if not video_link:
        results.append("❌ Hiba: A videó link megadása kötelező.")
        return results

    try:
        gdown_download(video_link, VIDEO_PATH, quiet=True, fuzzy=True)
        results.append(f"✅ Videó letöltve.")
    except Exception as e:
        results.append(f"❌ Hiba a videó letöltésekor: {e}")
        return results # Ha a videó sikertelen, a feliratot már nem is próbáljuk

    # 3. Felirat letöltése
    if subtitle_link:
        try:
            gdown_download(subtitle_link, SUBTITLE_PATH, quiet=True, fuzzy=True)
            results.append(f"✅ Felirat letöltve.")
        except Exception as e:
            results.append(f"❌ Hiba a felirat letöltésekor: {e}")
    else:
         results.append("ℹ️ Felirat link nem lett megadva.")
         
    return results

# --- Streamlit Munkamenet Állapot (Session State) Inicializálása ---
# Ez tárolja az adatokat a szkript újrafuttatásai között

if 'status_message' not in st.session_state:
    st.session_state.status_message = "Még nem történt letöltés."

if 'subtitle_settings' not in st.session_state:
    st.session_state.subtitle_settings = load_settings()

# --- Streamlit UI Felépítése ---

st.set_page_config(page_title="Streamlit Videólejátszó", layout="wide")
st.title("🎬 Streamlit Állandó Videólejátszó")
st.markdown("Ez az alkalmazás állandóan elérhető a Render-en. Másold be a **nyilvános** Google Drive linkeket.")

# 1. Beviteli mezők
with st.container(border=True):
    video_input = st.text_input("Google Drive Videó Nyilvános Linkje", placeholder="Pl. https://drive.google.com/file/d/...")
    subtitle_input = st.text_input("Google Drive Felirat Nyilvános Linkje (Opcionális)", placeholder="Pl. https://drive.google.com/file/d/...")
    
    download_btn = st.button("⬇️ Fájlok Letöltése és Lejátszó Frissítése")
    
    # Letöltés gomb logikája
    if download_btn:
        with st.spinner("Letöltés folyamatban... Ez eltarthat egy ideig."):
            results = download_files(video_input, subtitle_input)
            # Elmentjük az eredményt a session state-be, hogy az újrafuttatás után is meglegyen
            st.session_state.status_message = "\n".join(results)
        # st.rerun() helyett a Streamlit automatikusan újra fog futni
        # a gombnyomás után, és frissíti a UI-t.

# 2. Státusz és Videólejátszó
st.info(st.session_state.status_message) # Mindig kiírjuk az utolsó státuszt

video_file = VIDEO_PATH if os.path.exists(VIDEO_PATH) else None
subtitle_file = SUBTITLE_PATH if os.path.exists(SUBTITLE_PATH) else None

if video_file:
    st.video(video_file, subtitles=subtitle_file)
else:
    st.write("A videó a sikeres letöltés után jelenik meg itt.")

st.divider()

# 3. Felirat Beállítások (Perzisztens Mentéssel)
with st.expander("🎨 Felirat Stílus Beállítások (Perzisztens Mentés)"):
    settings = st.session_state.subtitle_settings
    
    # A Streamlit UI elemek
    color_input = st.text_input("Betűszín (CSS kód)", value=settings["color"])
    
    # A 'radio' indexét be kell állítani
    size_options = ["small", "medium", "large"]
    size_index = size_options.index(settings["size"]) if settings["size"] in size_options else 1
    size_input = st.radio("Méret", size_options, index=size_index)
    
    background_input = st.text_input("Háttér (CSS kód)", value=settings["background"])

    pos_options = ["top", "bottom"]
    pos_index = pos_options.index(settings["position"]) if settings["position"] in pos_options else 1
    position_input = st.radio("Elhelyezkedés", pos_options, index=pos_index)
        
    style_btn = st.button("💾 Felirat Stílus Mentése")

    if style_btn:
        new_settings = {
            "color": color_input,
            "size": size_input,
            "background": background_input,
            "position": position_input
        }
        save_settings(new_settings)
        # Frissítjük a session state-et is
        st.session_state.subtitle_settings = new_settings
        st.success("✅ Feliratstílus mentve! (A megjelenés a böngészőtől függ)")
