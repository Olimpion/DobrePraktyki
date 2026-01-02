import os
import cv2
import json
import time
# Importujemy funkcję z Twojego silnika
from app.inference_engine import get_plate_data, clean_plate_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAL_IMAGES_DIR = os.path.join(BASE_DIR, "dataset_yolo", "val", "images")
VAL_LABELS_DIR = os.path.join(BASE_DIR, "dataset_yolo", "val", "labels")
GT_JSON_PATH = os.path.join(BASE_DIR, "val_ground_truth.json")


def calculate_iou(box1, box2):
    x1, y1, x2, y2 = box1
    x3, y3, x4, y4 = box2
    x_inter1 = max(x1, x3)
    y_inter1 = max(y1, y3)
    x_inter2 = min(x2, x4)
    y_inter2 = min(y2, y4)
    inter_area = max(0, x_inter2 - x_inter1) * max(0, y_inter2 - y_inter1)
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x4 - x3) * (y4 - y3)
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0


def get_gt_box_pixels(label_path, img_w, img_h):
    if not os.path.exists(label_path): return None
    with open(label_path, 'r') as f:
        content = f.readline().split()
        if len(content) < 5: return None
        _, x_c, y_c, w_norm, h_norm = map(float, content)
        x1 = (x_c - w_norm / 2) * img_w
        y1 = (y_c - h_norm / 2) * img_h
        x2 = (x_c + w_norm / 2) * img_w
        y2 = (y_c + h_norm / 2) * img_h
        return [x1, y1, x2, y2]


def calculate_final_grade(accuracy_percent: float, processing_time_sec: float) -> float:
    if accuracy_percent < 60 or processing_time_sec > 60:
        return 2.0
    accuracy_norm = (accuracy_percent - 60) / 40
    time_norm = (60 - processing_time_sec) / 50
    score = 0.7 * accuracy_norm + 0.3 * time_norm
    grade = 2.0 + 3.0 * score
    return round(grade * 2) / 2


def run_evaluation():
    if not os.path.exists(GT_JSON_PATH):
        print(f"Błąd: Brak pliku {GT_JSON_PATH}")
        return

    with open(GT_JSON_PATH, "r") as f:
        gt_data = json.load(f)

    # Bierzemy 100 zdjęć (lub wszystkie jeśli mniej)
    test_images = list(gt_data.keys())[:100]

    correct_ocr_count = 0
    total_iou = 0
    count = 0

    print(f"Rozpoczynam analizę {len(test_images)} zdjęć przy użyciu inference_engine...")
    start_time = time.time()

    for img_name in test_images:
        img_path = os.path.join(VAL_IMAGES_DIR, img_name)
        label_path = os.path.join(VAL_LABELS_DIR, os.path.splitext(img_name)[0] + ".txt")

        # Wywołujemy funkcję z Twojego silnika
        result = get_plate_data(img_path)

        img_cv = cv2.imread(img_path)
        if img_cv is None: continue
        h, w, _ = img_cv.shape

        gt_box = get_gt_box_pixels(label_path, w, h)
        true_text = clean_plate_text(gt_data[img_name])

        if result:
            # IoU
            if gt_box:
                total_iou += calculate_iou(result['box'], gt_box)

            # OCR Accuracy (porównujemy wyczyszczone teksty)
            if result['text'] == true_text:
                correct_ocr_count += 1

        count += 1
        if count % 10 == 0:
            print(f"Przetworzono: {count}/{len(test_images)}...")

    total_time = time.time() - start_time
    accuracy = (correct_ocr_count / count) * 100 if count > 0 else 0
    avg_iou = total_iou / count if count > 0 else 0
    time_for_100 = (total_time / count) * 100 if count > 0 else 999

    print("\n" + "=" * 40)
    print("RAPORT KOŃCOWY (ZOPTYMALIZOWANY)")
    print("=" * 40)
    print(f"Dokładność OCR:          {accuracy:.2f}% (Cel: >60%)")
    print(f"Czas na 100 zdjęć:       {time_for_100:.2f}s (Cel: <60s)")
    print(f"Średnie IoU:             {avg_iou:.4f}")
    print("-" * 40)
    print(f"OCENA KOŃCOWA:           {calculate_final_grade(accuracy, time_for_100)}")
    print("=" * 40)


if __name__ == "__main__":
    run_evaluation()