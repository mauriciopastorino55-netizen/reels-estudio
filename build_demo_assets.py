import json
import os
import re
import shutil
import zipfile
from collections import deque
from PIL import Image, ImageDraw

APP_DIR = r"C:\Users\User\Desktop\Turbo\Reels Estudio PWA"
DEMO_DIR = os.path.join(APP_DIR, "demo")
SRC_HUERTO = r"C:\Users\User\Desktop\Turbo\Piloto Reels Literatura\reparacion_en_el_huerto"
SRC_VIAS = r"C:\Users\User\Desktop\Turbo\Piloto Reels Literatura\tres_vias_misticas"

os.makedirs(DEMO_DIR, exist_ok=True)


def remove_white_bg_floodfill(img, white_thresh=236, soft_band=26):
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    def is_bg(r, g, b):
        mx, mn = max(r, g, b), min(r, g, b)
        return mn >= white_thresh and (mx - mn) <= 24

    visited = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            r, g, b, _ = px[x, y]
            if is_bg(r, g, b) and not visited[y][x]:
                visited[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            r, g, b, _ = px[x, y]
            if is_bg(r, g, b) and not visited[y][x]:
                visited[y][x] = True
                q.append((x, y))

    while q:
        cx, cy = q.popleft()
        px[cx, cy] = (255, 255, 255, 0)
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                r, g, b, _ = px[nx, ny]
                if is_bg(r, g, b):
                    visited[ny][nx] = True
                    q.append((nx, ny))

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if (px[x - 1, y][3] == 0 or px[x + 1, y][3] == 0 or
                    px[x, y - 1][3] == 0 or px[x, y + 1][3] == 0):
                lum = (r + g + b) // 3
                if lum > (white_thresh - soft_band):
                    new_a = max(0, min(255, int(255 * (white_thresh - lum) / soft_band)))
                    px[x, y] = (r, g, b, new_a)

    bbox = rgba.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    rgba.thumbnail((460, 460), Image.Resampling.LANCZOS)
    return rgba


def build_pills_from_timeline(tl_path):
    with open(tl_path, encoding="utf-8") as f:
        tl = json.load(f)
    words = tl["words"]
    scenes = tl["scenes"]
    orig_tokens = " ".join(s["text"] for s in scenes).split()
    aligned = []
    for i, w in enumerate(words):
        txt = w["text"]
        if i < len(orig_tokens):
            orig = orig_tokens[i]
            m_pre = re.match(r'^([«"¿¡]+)', orig)
            m_suf = re.search(r'([.,:;»"?!]+)$', orig)
            if m_pre and not txt.startswith(m_pre.group(1)):
                txt = m_pre.group(1) + txt
            if m_suf and not txt.endswith(m_suf.group(1)):
                txt = txt + m_suf.group(1)
        aligned.append({"start": w["start"], "end": w["end"], "text": txt})

    pills = []
    cur, cur_len = [], 0
    for w in aligned:
        t = w["text"]
        if cur and (len(cur) >= 3 or cur_len + len(t) + 1 > 22):
            pills.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["text"] for x in cur)})
            cur, cur_len = [], 0
        cur.append(w)
        cur_len += len(t) + (1 if cur_len else 0)
        if t.endswith((".", ",", ":", ";", "!", "?")):
            pills.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["text"] for x in cur)})
            cur, cur_len = [], 0
    if cur:
        pills.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["text"] for x in cur)})
    return tl["duration"], pills


# 1. Preparar demo: reparacion_en_el_huerto
huerto_out = os.path.join(DEMO_DIR, "reparacion_en_el_huerto")
os.makedirs(os.path.join(huerto_out, "assets"), exist_ok=True)
shutil.copy2(os.path.join(SRC_HUERTO, "audio.mp3"), os.path.join(huerto_out, "audio.mp3"))
for fname in ("apertura.jpg", "huerto_noche.png", "eva_caida.png", "manzano_luz.png", "alianza_manos.png"):
    shutil.copy2(os.path.join(SRC_HUERTO, "assets", fname), os.path.join(huerto_out, "assets", fname))

huerto_dur, huerto_pills = build_pills_from_timeline(os.path.join(SRC_HUERTO, "timeline.json"))
huerto_reel = {
    "id": "reparacion_en_el_huerto",
    "title": "Reparación en el huerto",
    "work": "Cántico espiritual · Estrofa 23",
    "author": "San Juan de la Cruz",
    "folder": "Española",
    "critics": "Jauralde Pou · Disalvo",
    "duration": huerto_dur,
    "audio": "audio.mp3",
    "cover": "assets/apertura.jpg",
    "scenes": [
        {
            "type": "apertura",
            "start": 0.0,
            "end": 6.35,
            "img": "assets/apertura.jpg",
            "badgeTitle": "Reparación en el huerto",
            "badgeSub": "Cántico espiritual · Estrofa 23",
            "badgeAt": 1.95
        },
        {
            "type": "duelo",
            "start": 6.35,
            "end": 18.05,
            "title": "El <span>quiebre</span> alegórico",
            "left": {"img": "assets/huerto_noche.png", "aura": "night", "title": "Plano profano", "sub": "Aves, leones y miedos de la noche", "at": 6.75, "dimAt": 14.10},
            "right": {"img": "assets/manzano_luz.png", "aura": "gold", "title": "Clave religiosa", "sub": "Alegoría sagrada en la estrofa 23", "at": 14.35},
            "arrow": {"label": "Quiebre", "at": 13.80},
            "pill": {"text": "Pablo Jauralde Pou · Giro decisivo", "at": 12.40}
        },
        {
            "type": "contraste",
            "start": 18.05,
            "end": 31.45,
            "title": "De <span>Eva</span> al manzano",
            "verse": {"text": "«Debajo del manzano: / allí conmigo fuiste desposada… / y fuiste reparada / donde tu madre fuera violada»", "work": "Cántico espiritual · Estrofa 23", "at": 18.45},
            "left": {"img": "assets/eva_caida.png", "aura": "crimson", "title": "«Tu madre» = Eva", "sub": "Pecado original bajo el árbol", "at": 23.70},
            "right": {"img": "assets/manzano_luz.png", "aura": "gold", "title": "Debajo del manzano", "sub": "Redención en el huerto", "at": 19.75},
            "arrow": {"label": "Repara", "at": 27.90},
            "pill": {"text": "Disalvo · Lectura tipológica", "at": 26.30}
        },
        {
            "type": "convergencia",
            "start": 31.45,
            "end": 40.55,
            "title": "La <span>alianza</span> restaurada",
            "left": {"img": "assets/manzano_luz.png", "aura": "gold", "title": "Debajo del manzano", "sub": "Desposorio del alma", "at": 31.80},
            "right": {"img": "assets/alianza_manos.png", "aura": "gold", "title": "Cristo da la mano", "sub": "Restaura la alianza", "at": 34.10},
            "arrow": {"label": "Unión", "at": 35.00},
            "convergeAt": 36.20,
            "pill": {"text": "Dios ⟷ Humanidad · Caída revertida", "at": 37.20}
        },
        {
            "type": "duelo",
            "start": 40.55,
            "end": huerto_dur,
            "title": "Caída y <span>reparación</span>",
            "left": {"img": "assets/eva_caida.png", "aura": "crimson", "title": "Eva · Paraíso", "sub": "Pecado original", "at": 41.00, "dimAt": 46.80},
            "right": {"img": "assets/alianza_manos.png", "aura": "gold", "title": "Cristo · Alma", "sub": "Reparación alegórica", "at": 43.20},
            "arrow": {"label": "En el huerto", "at": 42.60},
            "footer": {"text": "Cántico espiritual (est. 23) · Jauralde Pou · Disalvo", "at": 44.50}
        }
    ],
    "subtitles": huerto_pills
}
with open(os.path.join(huerto_out, "reel.json"), "w", encoding="utf-8") as f:
    json.dump(huerto_reel, f, ensure_ascii=False, indent=2)

# 2. Preparar demo: tres_vias_misticas (con PNGs transparentes para modo oscuro)
vias_out = os.path.join(DEMO_DIR, "tres_vias_misticas")
os.makedirs(os.path.join(vias_out, "assets"), exist_ok=True)
shutil.copy2(os.path.join(SRC_VIAS, "audio.mp3"), os.path.join(vias_out, "audio.mp3"))
shutil.copy2(os.path.join(SRC_VIAS, "assets", "apertura.jpg"), os.path.join(vias_out, "assets", "apertura.jpg"))

for base in ("via_purgativa", "via_iluminativa", "via_unitiva"):
    src_img = Image.open(os.path.join(SRC_VIAS, "assets", f"{base}.jpg"))
    cleaned = remove_white_bg_floodfill(src_img)
    cleaned.save(os.path.join(vias_out, "assets", f"{base}.png"), "PNG", optimize=True)

vias_dur, vias_pills = build_pills_from_timeline(os.path.join(SRC_VIAS, "timeline.json"))
vias_reel = {
    "id": "tres_vias_misticas",
    "title": "Tres vías místicas",
    "work": "Noche oscura · Cántico espiritual",
    "author": "San Juan de la Cruz",
    "folder": "Española",
    "critics": "Edición B.A.C. · Nápoli · Disalvo",
    "duration": vias_dur,
    "audio": "audio.mp3",
    "cover": "assets/apertura.jpg",
    "scenes": [
        {
            "type": "apertura",
            "start": 0.0,
            "end": 8.05,
            "img": "assets/apertura.jpg",
            "badgeTitle": "Tres vías místicas",
            "badgeSub": "Itinerario espiritual progresivo",
            "badgeAt": 5.20
        },
        {
            "type": "foco",
            "start": 8.05,
            "end": 19.85,
            "step": 1,
            "totalSteps": 3,
            "title": "1. Vía <span>Purgativa</span>",
            "img": "assets/via_purgativa.png",
            "aura": "night",
            "caption": {"text": "Principiantes", "at": 10.10},
            "pill": {"text": "Ascesis · Calma de los apetitos", "at": 12.40},
            "verse": {"text": "«estando ya mi casa sosegada»", "work": "Noche oscura", "at": 16.00}
        },
        {
            "type": "foco",
            "start": 19.85,
            "end": 31.10,
            "step": 2,
            "totalSteps": 3,
            "title": "2. Vía <span>Iluminativa</span>",
            "img": "assets/via_iluminativa.png",
            "aura": "gold",
            "caption": {"text": "Aprovechados", "at": 22.10},
            "pill": {"text": "Luz de la fe en el corazón", "at": 25.40},
            "arrowAt": 27.90,
            "verse": {"text": "Desposorio espiritual", "work": "Cántico espiritual", "at": 28.20}
        },
        {
            "type": "foco",
            "start": 31.10,
            "end": 41.70,
            "step": 3,
            "totalSteps": 3,
            "title": "3. Vía <span>Unitiva</span>",
            "img": "assets/via_unitiva.png",
            "aura": "gold",
            "caption": {"text": "Perfectos", "at": 33.20},
            "pill": {"text": "La voluntad individual cede", "at": 35.50},
            "arrowAt": 37.90,
            "verse": {"text": "Alma ⟷ Dios · Matrimonio espiritual", "work": "Unión consumada", "at": 38.20}
        },
        {
            "type": "escalera",
            "start": 41.70,
            "end": vias_dur,
            "title": "Itinerario <span>espiritual</span>",
            "steps": [
                {"img": "assets/via_purgativa.png", "name": "1. Vía Purgativa", "sub": "Principiantes · Casa sosegada", "at": 42.10},
                {"img": "assets/via_iluminativa.png", "name": "2. Vía Iluminativa", "sub": "Aprovechados · Luz de la fe", "at": 42.95},
                {"img": "assets/via_unitiva.png", "name": "3. Vía Unitiva", "sub": "Perfectos · Unión total con Dios", "at": 43.80, "highlightAt": 47.50}
            ],
            "footer": {"text": "Edición B.A.C. · Nápoli · Disalvo", "at": 44.30}
        }
    ],
    "subtitles": vias_pills
}
with open(os.path.join(vias_out, "reel.json"), "w", encoding="utf-8") as f:
    json.dump(vias_reel, f, ensure_ascii=False, indent=2)

# 3. Escribir demo/manifest.js (compatible 100% con file:// y https://)
manifest_js = "window.BUILTIN_DEMO_REELS = " + json.dumps([
    {"basePath": "./demo/reparacion_en_el_huerto/", "reel": huerto_reel},
    {"basePath": "./demo/tres_vias_misticas/", "reel": vias_reel}
], ensure_ascii=False, indent=2) + ";\n"

with open(os.path.join(DEMO_DIR, "manifest.js"), "w", encoding="utf-8") as f:
    f.write(manifest_js)

# 4. Crear también un .zip de ejemplo listo para probar Importar .zip
zip_path = os.path.join(DEMO_DIR, "San_Juan_de_la_Cruz_pack.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for slug in ("reparacion_en_el_huerto", "tres_vias_misticas"):
        folder = os.path.join(DEMO_DIR, slug)
        for root, _, files in os.walk(folder):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, DEMO_DIR).replace("\\", "/")
                zf.write(full, rel)

# 5. Generar íconos PWA limpios (192x192 y 512x512)
def make_icon(size, out_path):
    img = Image.new("RGBA", (size, size), (12, 16, 24, 255))
    draw = ImageDraw.Draw(img)
    pad = int(size * 0.14)
    # Borde dorado sutil
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=int(size * 0.2), outline=(230, 184, 92, 230), width=max(4, size // 36), fill=(20, 27, 41, 255))
    # Triángulo Play dorado centrado
    cx, cy = size * 0.52, size * 0.50
    r = size * 0.20
    pts = [(cx - r * 0.72, cy - r * 0.85), (cx - r * 0.72, cy + r * 0.85), (cx + r * 0.92, cy)]
    draw.polygon(pts, fill=(230, 184, 92, 255))
    img.save(out_path, "PNG")

make_icon(192, os.path.join(APP_DIR, "icon-192.png"))
make_icon(512, os.path.join(APP_DIR, "icon-512.png"))

print(f"OK! Demo assets + manifest.js + zip ({os.path.getsize(zip_path)} bytes) + icons ready in {APP_DIR}")
