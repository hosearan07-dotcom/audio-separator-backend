FROM python:3.10-slim

# Installer les dépendances système requises (FFmpeg pour l'audio et git)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Installer Pytorch version CPU et Demucs + FastAPI
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir demucs fastapi uvicorn python-multipart

# Donner les droits d'écriture sur le dossier temporaire
RUN mkdir -p /tmp && chmod 777 /tmp

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
