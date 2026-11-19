import argparse
import json
import os
import re
import subprocess
import sys
from urllib.parse import quote

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BIB_DIR = os.path.join(APP_DIR, "biblioteca")
CATALOG_JS = os.path.join(BIB_DIR, "catalog.js")
CATALOG_JSON = os.path.join(BIB_DIR, "catalog.json")


def pretty_title_from_filename(name):
    base = os.path.splitext(name)[0]
    base = re.sub(r"^\d+[\s._-]+", "", base)
    return base.replace("_", " ").strip() or name


def url_path(rel_path):
    parts = rel_path.replace("\\", "/").split("/")
    return "./biblioteca/" + "/".join(quote(p) for p in parts)


def scan_folder(abs_dir, rel_parts):
    """Escanea recursivamente biblioteca/ y devuelve árbol de carpetas y videos (reels JSON + .mp4)."""
    node = {
        "name": rel_parts[-1] if rel_parts else "Biblioteca",
        "path": "/".join(rel_parts),
        "folders": [],
        "videos": []
    }

    try:
        entries = sorted(os.listdir(abs_dir), key=lambda s: s.lower())
    except FileNotFoundError:
        return node

    for entry in entries:
        if entry.startswith(".") or entry in ("catalog.js", "catalog.json"):
            continue
        full = os.path.join(abs_dir, entry)

        if os.path.isdir(full):
            reel_json_path = os.path.join(full, "reel.json")
            if os.path.isfile(reel_json_path):
                with open(reel_json_path, encoding="utf-8") as f:
                    reel_data = json.load(f)
                rel_sub = "/".join(rel_parts + [entry])
                node["videos"].append({
                    "kind": "reel",
                    "id": reel_data.get("id") or entry,
                    "title": reel_data.get("title") or pretty_title_from_filename(entry),
                    "subtitle": reel_data.get("work") or reel_data.get("author") or "",
                    "duration": reel_data.get("duration") or 0,
                    "baseUrl": url_path(rel_sub) + "/",
                    "cover": url_path(rel_sub + "/" + reel_data.get("cover", "assets/apertura.jpg")),
                    "reel": reel_data
                })
            else:
                child = scan_folder(full, rel_parts + [entry])
                node["folders"].append(child)
        elif entry.lower().endswith((".mp4", ".webm", ".m4v")):
            rel_file = "/".join(rel_parts + [entry])
            node["videos"].append({
                "kind": "mp4",
                "id": re.sub(r"[^a-zA-Z0-9_-]+", "_", os.path.splitext(entry)[0]),
                "title": pretty_title_from_filename(entry),
                "subtitle": "Video MP4",
                "duration": 0,
                "src": url_path(rel_file),
                "cover": ""
            })

    return node


def main():
    parser = argparse.ArgumentParser(description="Escanea biblioteca/ y genera catalog.js para Reels Estudio PWA")
    parser.add_argument("--push", action="store_true", help="Hace git add, commit y push después de actualizar el catálogo")
    parser.add_argument("-m", "--message", default="Actualizar biblioteca de Reels Estudio", help="Mensaje de commit para --push")
    args = parser.parse_args()

    os.makedirs(BIB_DIR, exist_ok=True)
    tree = scan_folder(BIB_DIR, [])

    with open(CATALOG_JSON, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)

    with open(CATALOG_JS, "w", encoding="utf-8") as f:
        f.write("window.REELS_CATALOG = " + json.dumps(tree, ensure_ascii=False, indent=2) + ";\n")

    def count_videos(n):
        return len(n["videos"]) + sum(count_videos(c) for c in n["folders"])

    print(f"OK: {CATALOG_JS} actualizado ({count_videos(tree)} videos en biblioteca/)")

    if args.push:
        subprocess.run(["git", "add", "."], cwd=APP_DIR, check=True)
        res = subprocess.run(["git", "status", "--porcelain"], cwd=APP_DIR, capture_output=True, text=True)
        if res.stdout.strip():
            subprocess.run(["git", "commit", "-m", args.message], cwd=APP_DIR, check=True)
            subprocess.run(["git", "push"], cwd=APP_DIR, check=True)
            print("OK: Cambios subidos a GitHub.")
        else:
            print("Sin cambios nuevos para subir.")


if __name__ == "__main__":
    main()
