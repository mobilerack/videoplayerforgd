import gradio as gr
import os
import json
from gdown import download as gdown_download

# --- Fájl- és Beállításkezelés ---
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

# A kezdeti beállítások betöltése
subtitle_settings = load_settings()

# --- Függvények ---

def download_files(video_link, subtitle_link):
    """
    Letölti a videót és a feliratfájlt a nyilvános Google Drive linkekről.
    """
    results = []
    
    # 1. Töröljük a korábbi fájlokat (helytakarékosság miatt)
    if os.path.exists(VIDEO_PATH): os.remove(VIDEO_PATH)
    if os.path.exists(SUBTITLE_PATH): os.remove(SUBTITLE_PATH)
    
    # 2. Videó letöltése
    try:
        gdown_download(video_link, VIDEO_PATH, quiet=True)
        results.append(f"✅ Videó letöltve.")
    except Exception as e:
        results.append(f"❌ Hiba a videó letöltésekor: Ellenőrizd a linket és a jogosultságokat.")

    # 3. Felirat letöltése
    if subtitle_link:
        try:
            gdown_download(subtitle_link, SUBTITLE_PATH, quiet=True)
            results.append(f"✅ Felirat letöltve.")
        except Exception as e:
            results.append(f"❌ Hiba a felirat letöltésekor.")
    else:
         results.append("ℹ️ Felirat link nem lett megadva.")

    # A lejátszó frissítéséhez szükséges adatok:
    video_file = VIDEO_PATH if os.path.exists(VIDEO_PATH) else None
    subtitle_file = SUBTITLE_PATH if os.path.exists(SUBTITLE_PATH) else None
    
    return "\n".join(results), gr.Video.update(value=video_file, subtitles=subtitle_file)

def set_subtitle_style(color, size, background, position):
    """
    Elmenti a felhasználó felirat beállításait a JSON fájlba.
    """
    global subtitle_settings
    subtitle_settings.update({
        "color": color,
        "size": size,
        "background": background,
        "position": position
    })
    save_settings(subtitle_settings)
    
    # Mivel a Gradio natív lejátszója nem támogatja a dinamikus CSS-t,
    # ez a lépés csak a beállítások perzisztens mentését biztosítja.
    # A felhasználó láthatja, hogy a beállítás mentve lett.
    return f"✅ Feliratstílus mentve! Ez a beállítás legközelebb is elérhető lesz (de a megjelenítés a böngésző beállításaitól függ)."

# --- Gradio UI felépítése ---

with gr.Blocks(title="Render Videólejátszó") as demo:
    gr.Markdown("# 🎬 Render Állandó Videólejátszó")
    gr.Markdown("Ez az alkalmazás állandóan elérhető a Render-en. Másold be a **nyilvános** Google Drive linkeket.")
    
    # 1. Beviteli mezők
    with gr.Row():
        video_input = gr.Textbox(label="Google Drive Videó Nyilvános Linkje", placeholder="Pl. https://drive.google.com/file/d/...")
        subtitle_input = gr.Textbox(label="Google Drive Felirat Nyilvános Linkje (Opcionális)", placeholder="Pl. https://drive.google.com/file/d/...")
        
    download_btn = gr.Button("⬇️ Fájlok Letöltése és Lejátszó Frissítése")
    download_output = gr.Textbox(label="Letöltés Állapota", interactive=False)
    
    # 2. Videólejátszó
    player = gr.Video(
        label="A Videólejátszó (A felirat automatikusan megjelenik, ha létezik)",
        width=800,
        subtitles=SUBTITLE_PATH if os.path.exists(SUBTITLE_PATH) else None # Kezdeti felirat betöltése
    )
    
    # Kapcsolódás
    download_btn.click(
        fn=download_files,
        inputs=[video_input, subtitle_input],
        outputs=[download_output, player]
    )

    gr.Markdown("---")
    
    # 3. Felirat Beállítások (Perzisztens Mentéssel)
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


# Az alkalmazás elindítása
if __name__ == "__main__":
    # Renderen a portot a környezeti változó (PORT) határozza meg
    port = int(os.environ.get("PORT", 7860))
    # A Gradio a '0.0.0.0' címen kell, hogy fusson a Render-en
    demo.launch(server_name="0.0.0.0", server_port=port)
