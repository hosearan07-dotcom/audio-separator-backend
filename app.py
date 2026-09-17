import os
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

app = FastAPI(title="Audio Separator API")

# Dossiers temporaires
UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/separated"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def cleanup(paths):
    for p in paths:
        if os.path.exists(p):
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)

@app.post("/separate")
async def separate_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    stems: str = Form("4")
):
    # 1. Sauvegarder le fichier audio reçu
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Déterminer le modèle Demucs (htdemucs pour 4 pistes, htdemucs_6 pour 6 pistes)
    model = "htdemucs" if stems == "4" else "htdemucs_6"
    
    # 2. Exécuter la commande Demucs pour séparer les pistes
    try:
        cmd = ["demucs", "-n", model, "-o", OUTPUT_DIR, input_path]
        subprocess.run(cmd, check=True)
    except Exception as e:
        cleanup([input_path])
        raise HTTPException(status_code=500, detail=f"Erreur de séparation: {str(e)}")

    # 3. Trouver le dossier des pistes générées
    filename_without_ext = os.path.splitext(file.filename)[0]
    separated_folder = os.path.join(OUTPUT_DIR, model, filename_without_ext)
    
    if not os.path.exists(separated_folder):
        cleanup([input_path])
        raise HTTPException(status_code=500, detail="Les pistes n'ont pas pu être générées.")

    # 4. Compresser les pistes en un fichier ZIP
    zip_output_name = os.path.join("/tmp", f"tracks_{filename_without_ext}")
    shutil.make_archive(zip_output_name, 'zip', separated_folder)
    zip_file_path = f"{zip_output_name}.zip"

    # Ajouter le nettoyage en tâche de fond après l'envoi du fichier
    background_tasks.add_task(cleanup, [input_path, separated_folder, zip_file_path])

    return FileResponse(zip_file_path, media_type="application/zip", filename="tracks.zip")

@app.get("/")
def read_root():
    return {"status": "L'API de séparation audio fonctionne correctement ! Route active: /separate"}
