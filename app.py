import streamlit as st
import os
import json
import gdown # A felirat letöltéséhez továbbra is kell
import re    # Ezt az új modult használjuk az ID kinyeréséhez

# --- Fájl- és Beállításkezelés ---
TEMP_DIR = "data"
os.makedirs(TEMP_DIR, exist_ok=True)
SUBTITLE_PATH = os.path.join(TEMP_DIR, "subtitle.vtt") 
SETTINGS_FILE = os.path.join(TEMP_DIR, "settings.json")

# Alapértelmezett beállítások
DEFAULT_SETTINGS = {
    "color": "#FFFFFF", "size": "medium", "background": "transparent", "position": "bottom"
}

# --- Beállításkezelő Függvények (Változatlan) ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

# --- Link-kezelő Függvény (Javítva) ---

def get_id_from_url(url):
    """
    Manuálisan kinyeri a Google Drive fájl ID-t a linkből regex segítségével.
    Ez kiváltja a 'gdown.get_id' funkciót.
    """
    # Ez a regex minta megkeresi az ID-t a /d/ es /file/id/ linkekben is
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    
    match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
        
    return None

def process_links(video_link, subtitle_link):
    """
    Megszerzi a videó streamelhető URL-jét és letölti a feliratfájlt.
    """
    global SUBTITLE_PATH
    results = []
    video_url_to_play = None
    subtitle_path_to_play = None
    
    # 1. Töröljük a korábbi feliratfájlt
    if os.path.exists(SUBTITLE_PATH): os.remove(SUBTITLE_PATH)
    
    # 2. Videó URL megszerzése (NEM letöltés!)
    if not video_link:
        results.append("❌ Hiba: A videó link megadása kötelező.")
        return results, None, None

    try:
        # --- JAVÍTÁS ITT (Manuális módszer) ---
        
        # 1. LÉPÉS: Manuálisan kinyerjük a fájl ID-t a linkből
        file_id = get_id_from_url(video_link)
        
        if not file_id:
            raise Exception("Nem sikerült kinyerni a Google Drive Fájl ID-t a linkből. Ellenőrizd a linket.")
            
        # 2. LÉPÉS: Manuálisan létrehozzuk a közvetlen streamelési URL-t
        video_url_to_play = f"https://drive.google.com/uc?id={file_id}"
        
        # --- JAVÍTÁS VÉGE ---
        
        if video_url_to_play:
            results.append(f"✅ Videó stream URL sikeresen megszerezve.")
        else:
            raise Exception("Nem sikerült a letöltési link kinyerése (lehet, hogy a link nem nyilvános?).")
    except Exception as e:
        results.append(f"❌ Hiba a videó URL megszerzésekor: {e}")
        return results, None, None

    # 3. Felirat letöltése (Ez kicsi, ezt letölthetjük, ehhez a régi gdown is jó)
    if subtitle_link:
        try:
            gdown.download(subtitle_link, SUBTITLE_PATH, quiet=True, fuzzy=True)
            subtitle_path_to_play = SUBTITLE_PATH
            results.append(f"✅ Felirat letöltve.")
        except Exception as e:
            results.append(f"❌ Hiba a felirat letöltésekor: {e}")
    else:
         results.append("ℹ️ Felirat link nem lett megadva.")
         
    return results, video_url_to_play, subtitle_path_to_play

# --- Streamlit Munkamenet Állapot (Session State) Inicializálása ---
if 'status_message' not in st.session_state:
    st.session_state.status_message = "Még nem történt művelet."
if 'video_url' not in st.session_state:
    st.session_state.video_url = None
if 'subtitle_path' not in st.session_state:
    st.session_state.subtitle_path = None
if 'subtitle_settings' not in st.session_state:
    st.session_state.subtitle_settings = load_settings()

# --- Streamlit UI Felépítése ---
st.set_page_config(page_title="Streamlit Videólejátszó", layout="wide")
st.title("🎬 Streamlit Állandó Videólejátszó")
st.markdown("Add meg a **nyilvános** Google Drive linkeket. A videó streamelve lesz, nem letöltve a szerverre.")

# 1. Beviteli mezők
with st.container(border=True):
    video_input = st.text_input("Google Drive Videó Nyilvános Linkje", placeholder="Pl. https://drive.google.com/file/d/...")
    subtitle_input = st.text_input("Google Drive Felirat Nyilvános Linkje (Opcionális)", placeholder="Pl. https://drive.google.com/file/d/...")
    
    process_btn = st.button("▶️ Videó Betöltése")
    
    # Gomb logikája
    if process_btn:
        with st.spinner("Linkek feldogozása..."):
            results, video_url, sub_path = process_links(video_input, subtitle_input)
            
            # Eltároljuk az eredményt a session state-ben
            st.session_state.status_message = "\n".join(results)
            st.session_state.video_url = video_url
            st.session_state.subtitle_path = sub_path

# 2. Státusz és Videólejátszó
st.info(st.session_state.status_message) # Mindig kiírjuk az utolsó státuszt

# Csak akkor jelenítjük meg a lejátszót, ha van érvényes videó URL
if st.session_state.video_url:
    st.video(st.session_state.video_url, subtitles=st.session_state.subtitle_path)
else:
    st.write("A videó a sikeres link-feldgozás után jelenik meg itt.")

st.divider()

# 3. Felirat Beállítások (Változatlan)
with st.expander("🎨 Felirat Stílus Beállítások (Perzisztens Mentés)"):
    settings = st.session_state.subtitle_settings
    
    color_input = st.text_input("Betűszín (CSS kód)", value=settings["color"])
    
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
        st.session_state.subtitle_settings = new_settings
        st.success("✅ Feliratstílus mentve! (A megjelenés a böngészőtől függ)")
