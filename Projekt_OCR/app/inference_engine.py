import os
import cv2
import easyocr
from ultralytics import YOLO
import numpy as np
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ścieżka do modelu - upewnij się, że jest poprawna
MODEL_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "runs", "detect", "plate_detector", "weights", "best.pt"))

# Ładujemy modele raz (globalnie)
model = YOLO(MODEL_PATH)
# Używamy 'en', bo tablice nie mają polskich znaków (ą,ę), a model EN jest szybszy
reader = easyocr.Reader(['en'], gpu=False)


def clean_plate_text(text):
    """Usuwa zbędne znaki i normalizuje tekst."""
    if not text:
        return ""
    # Pozostawiamy tylko litery A-Z i cyfry 0-9
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def get_plate_data(image_path_or_buf):
    if isinstance(image_path_or_buf, str):
        img = cv2.imread(image_path_or_buf)
    else:
        nparr = np.frombuffer(image_path_or_buf, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    h, w, _ = img.shape
    # Przeskalowanie do 640 przyspiesza detekcję YOLO
    results = model(img, imgsz=640, verbose=False)

    if len(results[0].boxes) > 0:
        box = results[0].boxes[0]
        xyxy = box.xyxy.cpu().numpy()[0]

        x1, y1, x2, y2 = map(int, xyxy)

        # Dodajemy margines, żeby OCR lepiej widział krawędzie liter
        margin = 4
        plate_crop = img[max(0, y1 - margin):min(h, y2 + margin), max(0, x1 - margin):min(w, x2 + margin)]

        # OPTYMALIZACJA OCR:
        # detail=0 - zwraca tylko tekst (szybciej)
        # allowlist - szukamy tylko znaków występujących na tablicach
        ocr_res = reader.readtext(plate_crop, detail=0, allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        raw_text = "".join(ocr_res)
        cleaned_text = clean_plate_text(raw_text)

        return {
            "box": xyxy,
            "text": cleaned_text,
            "img_w": w,
            "img_h": h
        }
    return None