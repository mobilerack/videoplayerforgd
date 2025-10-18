import gradio as gr
import os
import json
import re
from gdown import download as gdown_download

# Google Drive API importok
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# --- Fájl- és Beállításkezelés ---
TEMP_DIR = "data"
os.makedirs(TEMP_DIR, exist_ok=True)
VIDEO_PATH = os.path.join(TEMP_DIR, "video.mp4")
SUBTITLE_PATH = os.path.join(TEMP_DIR, "subtitle.vtt")
SETTINGS_FILE = os.path.join(TEMP_DIR, "settings.json")

# A Render a titkos fájlt itt teszi elérhetővé
SERVICE_ACCOUNT_FILE = '/etc/secrets/service_account.json'

# Globális változók a fájlok tárolására
video_file_map = {}
subtitle_file_map = {}
drive = None

# --- Google Drive API Hitelesítés ---

def authenticate_gdrive():
    """Hitelesíti az alkalmazást a Google Drive API-val a Service Account segítségével."""
    global drive
    if drive:
        return drive
    
    try:
        gauth = GoogleAuth()
        # Próbálja meg a szolgáltatásfiók hitelesítést
        gauth.auth_method = 'service'
        gauth.service_config_file = SERVICE_ACCOUNT_FILE
        gauth.Authorize()
        drive = GoogleDrive(gauth)
        return drive
    except Exception as e:
        print(f"Hiba a Google Drive hitelesítés során: {e}")
        return None

# --- Mappa- és Fájlkezelő Függvények ---

def get_id_from_link(link):
    """Kinyeri a Google Drive Mappa ID-t a megosztási linkből."""
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', link)
    if match:
        return match.group(1)
    return None

def list_files_in_folder(folder_id):
    """Listázza az összes fájlt (név, id) egy adott GDrive mappa ID alatt."""
    drive_instance = authenticate_gdrive()
    if not drive_instance:
        raise gr.Error("Google Drive hitelesítés sikertelen. Ellenőrizd a service_account.json fájlt a Render-en.")
        
    file_map = {}
    try:
        # 'q' paraméter: 'FOLDER_ID' in parents (szülő mappa) and trashed=false (nincs a kukában)
        file_list = drive_instance.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        for f in file_list:
            file_map[f['title']] = f['id']
        return file_map
    except Exception as e:
        raise gr.Error(f"Hiba a fájlok listázásakor: {e}. Ellenőrizd, hogy a mappák meg vannak-e osztva a service fiókkal.")

def populate_file_lists(video_folder_link, subtitle_folder_link):
    """Beolvassa a mappákat és feltölti a globális fájllistákat."""
    global video_file_map, subtitle_file_map
    
    video_folder_id = get_id_from_link(video_folder_link)
    subtitle_folder_id = get_id_from_link(subtitle_folder_link)
    
    if not video_folder_id:
        return "❌ Hiba: Érvénytelen videó mappa link.", gr.Dropdown.update(choices=[], interactive=False)
        
    if not subtitle_folder_id:
        return "❌ Hiba: Érvénytelen felirat mappa link.", gr.Dropdown.update(choices=[], interactive=False)

    try:
        video_file_map = list_files_in_folder(video_folder_id)
        subtitle_file_map = list_files_in_folder(subtitle_folder_id)
        
        video_filenames = sorted(list(video_file_map.keys()))
        
        if not video_filenames:
            return "ℹ️ A videó mappa üres vagy nem sikerült beolvasni.", gr.Dropdown.update(choices=[], interactive=False)
            
        return f"✅ Sikeresen beolvasva {len(video_filenames)} videó. Válassz egyet!", gr.Dropdown.update(choices=video_filenames, value=None, interactive=True)
    
    except Exception as e:
        return str(e), gr.Dropdown.update(choices=[], interactive=False)

def load_selected_video(video_filename):
    """
    Letölti a kiválasztott videót és a hozzá (név alapján) illő feliratot.
    """
    if not video_filename:
        return "Válassz egy videót.", gr.Video.update(value=None, subtitles=None)

    # 1. Töröljük a korábbi fájlokat
    if os.path.exists(VIDEO_PATH): os.remove(VIDEO_PATH)
    if os.path.exists(SUBTITLE_PATH): os.remove(SUBTITLE_PATH)

    results = []
    
    # 2. Videó ID és letöltés
    video_id = video_file_map.get(video_filename)
    if not video_id:
        return "❌ Hiba: A videó ID nem található.", gr.Video.update()
        
    try:
        gdown_download(id=video_id, output=VIDEO_PATH, quiet=True)
        results.append(f"✅ Videó letöltve: {video_filename}")
    except Exception as e:
        results.append(f"❌ Hiba a videó letöltésekor: {e}")
        return "\n".join(results), gr.Video.update(value=None, subtitles=None)

    # 3. Megfelelő felirat keresése és letöltése
    video_name_without_ext = os.path.splitext(video_filename)[0]
    
    # Keresünk egyező nevű feliratot (pl. .vtt, .srt)
    subtitle_id = None
    for subtitle_filename, s_id in subtitle_file_map.items():
        if os.path.splitext(subtitle_filename)[0] == video_name_without_ext:
            subtitle_id = s_id
            break
            
    if subtitle_id:
        try:
            # A SUBTITLE_PATH nevű fájlba mentjük, függetlenül az eredeti névtől
            gdown_download(id=subtitle_id, output=SUBTITLE_PATH, quiet=True)
            results.append(f"✅ Hozzáillő felirat megtalálva és letöltve.")
        except Exception as e:
            results.append(f"❌ Hiba a felirat letöltésekor: {e}")
    else:
        results.append("ℹ️ Nem található hozzáillő felirat.")

    # 4. Lejátszó frissítése
    video_file = VIDEO_PATH if os.path.exists(VIDEO_PATH) else None
    subtitle_file = SUBTITLE_PATH if os.path.exists(SUBTITLE_PATH) else None

    return "\n".join(results), gr.Video.update(value=video_file, subtitles=subtitle_file)


# --- Felirat Stílus (Változatlan) ---

DEFAULT_SETTINGS = {
    "color": "#FFFFFF", "size": "medium", "background": "transparent", "position": "bottom"
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def set_subtitle_style(color, size, background, position):
    settings = load_settings()
    settings.update({
        "color": color, "size": size, "background": background, "position": position
    })
    save_settings(settings)
    return f"✅ Feliratstílus mentve! (A megjelenés a böngészőtől függ)"

# --- Gradio UI felépítése ---

with gr.Blocks(title="Render Videólejátszó (Mappás)") as demo:
    gr.Markdown("# 🎬 Render Videólejátszó (Mappa Böngészővel)")
    gr.Markdown("Add meg a **nyilvános Google Drive mappa linkeket**. A mappáknak meg kell lenniük osztva a háttérben futó szolgáltatásfiókkal (lásd a beállítási útmutatót).")
    
    with gr.Row():
        video_folder_input = gr.Textbox(label="Videó Mappa Linkje", placeholder="https://drive.google.com/drive/folders/...")
        subtitle_folder_input = gr.Textbox(label="Felirat Mappa Linkje", placeholder="https://drive.google.com/drive/folders/...")
        
    list_files_btn = gr.Button("📁 Mappák Beolvasása")
    
    gr.Markdown("---")
    
    with gr.Row():
        video_dropdown = gr.Dropdown(label="Válassz egy videót", interactive=False)
        download_output = gr.Textbox(label="Letöltés Állapota", interactive=False, scale=2)
        
    player = gr.Video(
        label="A Videólejátszó",
        width=800
    )
    
    # --- UI Eseménykezelők ---
    
    # 1. Gombnyomásra beolvassa a mappákat és frissíti a dropdown listát
    list_files_btn.click(
        fn=populate_file_lists,
        inputs=[video_folder_input, subtitle_folder_input],
        outputs=[download_output, video_dropdown]
    )
    
    # 2. Amikor a felhasználó választ a listából, elindul a letöltés és a lejátszó frissítése
    video_dropdown.change(
        fn=load_selected_video,
        inputs=[video_dropdown],
        outputs=[download_output, player]
    )

    gr.Markdown("---")
    
    # 3. Felirat Beállítások (Változatlan)
    settings = load_settings()
    gr.Markdown("## 🎨 Felirat Stílus Beállítások (Perzisztens Mentés)")

    with gr.Row():
        color_input = gr.Textbox(label="Betűszín (CSS kód)", value=settings["color"])
        size_input = gr.Radio(["small", "medium", "large"], label="Méret", value=settings["size"])
        background_input = gr.Textbox(label="Háttér (CSS kód)", value=settings["background"])
        position_input = gr.Radio(["top", "bottom"], label="Elhelyezkedés", value=settings["position"])
        
    style_btn = gr.Button("💾 Felirat Stílus Mentése")
    style_output = gr.Textbox(label="Stílus Mentés Állapota", interactive=False)

    style_btn.click(
        fn=set_subtitle_style,
        inputs=[color_input, size_input, background_input, position_input],
        outputs=style_output
    )

# --- Alkalmazás Indítása ---
if __name__ == "__main__":
    # Előre hitelesítünk indításkor, hogy gyorsabb legyen az első kérés
    authenticate_gdrive()
    
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
