import os
import cv2
import pytesseract
from ultralytics import YOLO
import numpy as np
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "runs", "detect", "plate_detector", "weights", "best.pt"))

model = YOLO(MODEL_PATH)

def clean_plate_text(text):
    if not text: return ""
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())

    while len(cleaned) > 7 and cleaned[0] in ('B', 'E', 'I', 'L', 'A', 'H', 'R', 'Z', 'W', 'F'):
        cleaned = cleaned[1:]

    while len(cleaned) > 7 and cleaned[-1] in ('I', '1', 'L', 'J', 'H'):
        cleaned = cleaned[:-1]

    if len(cleaned) < 4: return cleaned

    chars = list(cleaned)
    for i in range(len(chars)):
        if i < 2:
            m = {'5': 'S', '0': 'O', '1': 'I', '2': 'Z', '4': 'A', '8': 'B', '6': 'G', '7': 'T'}
            if chars[i] in m: chars[i] = m[chars[i]]
        else:
            if i < len(chars) - 1:
                m_num = {'S': '5', 'O': '0', 'D': '0', 'G': '6', 'B': '8', 'Z': '7'}
                if chars[i] in m_num:
                    chars[i] = m_num[chars[i]]
            if chars[i] == 'T' and i >= 2: chars[i] = '7'
            if chars[i] == '7' and i < 2: chars[i] = 'T'

    return "".join(chars)

def get_plate_data(image_path_or_buf):
    if isinstance(image_path_or_buf, str):
        img = cv2.imread(image_path_or_buf)
    else:
        nparr = np.frombuffer(image_path_or_buf, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None: return None

    results = model(img, imgsz=640, verbose=False)

    if len(results[0].boxes) > 0:
        box = results[0].boxes[0]
        xyxy = box.xyxy.cpu().numpy()[0]
        x1, y1, x2, y2 = map(int, xyxy)

        h_orig, w_orig = img.shape[:2]
        plate_crop = img[max(0, y1 - 2):min(h_orig, y2 + 2), max(0, x1 - 2):min(w_orig, x2 + 2)]

        if plate_crop.size > 0:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            resized = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LANCZOS4)
            blurred = cv2.bilateralFilter(resized, 9, 75, 75)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            if np.mean(thresh) < 127:
                thresh = cv2.bitwise_not(thresh)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            dilated = cv2.dilate(cv2.bitwise_not(thresh), kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                best_cnt = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(best_cnt)
                margin = 10
                final_roi = thresh[max(0, y - margin):min(thresh.shape[0], y + h + margin),
                                   max(0, x - margin):min(thresh.shape[1], x + w + margin)]
            else:
                final_roi = thresh

            custom_config_8 = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            raw_text = pytesseract.image_to_string(final_roi, config=custom_config_8).strip()

            return {
                "box": xyxy,
                "text": clean_plate_text(raw_text)
            }
    return None