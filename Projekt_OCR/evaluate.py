import os
import cv2
import json
import time
from app.inference_engine import get_plate_data, clean_plate_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAL_IMAGES_DIR = os.path.join(BASE_DIR, "dataset_yolo", "val", "images")
VAL_LABELS_DIR = os.path.join(BASE_DIR, "dataset_yolo", "val", "labels")
GT_JSON_PATH = os.path.join(BASE_DIR, "val_ground_truth.json")

def calculate_iou(box1, box2):
    x1, y1, x2, y2 = box1
    x3, y3, x4, y4 = box2
    x_inter1, y_inter1 = max(x1, x3), max(y1, y3)
    x_inter2, y_inter2 = min(x2, x4), min(y2, y4)
    inter_area = max(0, x_inter2 - x_inter1) * max(0, y_inter2 - y_inter1)
    union_area = (x2 - x1) * (y2 - y1) + (x4 - x3) * (y4 - y3) - inter_area
    return inter_area / union_area if union_area > 0 else 0

def get_gt_box_pixels(label_path, img_w, img_h):
    if not os.path.exists(label_path): return None
    with open(label_path, 'r') as f:
        line = f.readline().split()
        if len(line) < 5: return None
        _, xc, yc, wn, hn = map(float, line)
        return [(xc - wn / 2) * img_w, (yc - hn / 2) * img_h, (xc + wn / 2) * img_w, (yc + hn / 2) * img_h]

def calculate_final_grade(acc, t_100):
    if acc < 60 or t_100 > 60: return 2.0
    score = 0.7 * ((acc - 60) / 40) + 0.3 * ((60 - t_100) / 50)
    return round((2.0 + 3.0 * score) * 2) / 2

def run_evaluation():
    if not os.path.exists(GT_JSON_PATH): return print("Brak pliku GT!")

    with open(GT_JSON_PATH, "r") as f:
        gt_data = json.load(f)

    test_images = list(gt_data.keys())[:100]
    correct, total_iou, count = 0, 0, 0
    debug_logs = []

    print(f"Rozpoczynam test na {len(test_images)} zdjęciach...")
    start_time = time.time()

    for img_name in test_images:
        img_path = os.path.join(VAL_IMAGES_DIR, img_name)
        label_path = os.path.join(VAL_LABELS_DIR, os.path.splitext(img_name)[0] + ".txt")

        result = get_plate_data(img_path)

        # Pobranie wymiarów obrazu do obliczenia IoU
        img_cv = cv2.imread(img_path)
        if img_cv is None: continue
        h, w, _ = img_cv.shape

        true_text = clean_plate_text(gt_data[img_name])
        gt_box = get_gt_box_pixels(label_path, w, h)

        if result:
            pred_text = result['text']
            if gt_box: total_iou += calculate_iou(result['box'], gt_box)
            if pred_text == true_text:
                correct += 1
            else:
                debug_logs.append(f"BŁĄD {img_name}: Prawda='{true_text}', Odczyt='{pred_text}'")
        else:
            debug_logs.append(f"BŁĄD {img_name}: YOLO FAIL")

        count += 1
        if count % 20 == 0: print(f"Postęp: {count}...")

    total_time = time.time() - start_time

    print("Test zakończony. Zapisywanie logów tekstowych...")
    with open("bledy_debug.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(debug_logs))

    accuracy = (correct / count) * 100 if count > 0 else 0
    time_100 = (total_time / count) * 100 if count > 0 else 999

    print("\n" + "=" * 40 + "\nRAPORT KOŃCOWY\n" + "=" * 40)
    print(f"Dokładność OCR:          {accuracy:.2f}% (Cel: >60%)")
    print(f"Czas na 100 zdjęć:       {time_100:.2f}s (Cel: <60s)")
    print(f"Średnie IoU:             {total_iou / count:.4f}")
    print("-" * 40)
    print(f"OCENA KOŃCOWA:           {calculate_final_grade(accuracy, time_100)}")
    print("=" * 40)

if __name__ == "__main__":
    run_evaluation()