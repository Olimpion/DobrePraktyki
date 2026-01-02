import os
import shutil
import random
import xml.etree.ElementTree as ET
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_IMAGES_DIR = os.path.join(BASE_DIR, "raw_data", "photos")
ANNOTATIONS_FILE = os.path.join(BASE_DIR, "raw_data", "annotations.xml")
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset_yolo")
TRAIN_RATIO = 0.7


def convert_to_yolo(img_width, img_height, coords):
    xmin, ymin, xmax, ymax = coords
    dw = 1. / img_width
    dh = 1. / img_height
    x = (xmin + xmax) / 2.0
    y = (ymin + ymax) / 2.0
    w = xmax - xmin
    h = ymax - ymin
    return (x * dw, y * dh, w * dw, h * dh)


def prepare_data():
    if not os.path.exists(ANNOTATIONS_FILE):
        print(f"BŁĄD: Nie znaleziono pliku {ANNOTATIONS_FILE}")
        return

    tree = ET.parse(ANNOTATIONS_FILE)
    root = tree.getroot()
    images_data = root.findall('image')

    print(f"Znaleziono {len(images_data)} wpisów w pliku adnotacji.")
    random.seed(42)
    random.shuffle(images_data)

    split_idx = int(len(images_data) * TRAIN_RATIO)
    train_data = images_data[:split_idx]
    val_data = images_data[split_idx:]
    splits = {'train': train_data, 'val': val_data}

    for s in ['train', 'val']:
        os.makedirs(os.path.join(OUTPUT_DIR, s, 'images'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUT_DIR, s, 'labels'), exist_ok=True)

    # Tutaj będziemy zbierać poprawne numery tablic dla zbioru walidacyjnego
    ground_truth_val = {}

    for split_name, data_list in splits.items():
        print(f"Przetwarzanie {split_name}...")
        for img_entry in data_list:
            file_name = img_entry.get('name')
            img_w = float(img_entry.get('width'))
            img_h = float(img_entry.get('height'))
            src_img_path = os.path.join(RAW_IMAGES_DIR, file_name)

            if not os.path.exists(src_img_path):
                continue

            # YOLO LABELS
            box = img_entry.find('box')
            if box is not None:
                xtl = float(box.get('xtl'))
                ytl = float(box.get('ytl'))
                xbr = float(box.get('xbr'))
                ybr = float(box.get('ybr'))

                # Wyciąganie tekstu tablicy (atrybutu)
                plate_text = ""
                attr = box.find(".//attribute[@name='plate number']")
                if attr is not None:
                    plate_text = attr.text

                # Zapisujemy do ground_truth tylko dla zbioru walidacyjnego (testowego)
                if split_name == 'val':
                    ground_truth_val[file_name] = plate_text

                yolo_coords = convert_to_yolo(img_w, img_h, (xtl, ytl, xbr, ybr))
                label_name = os.path.splitext(file_name)[0] + ".txt"
                label_path = os.path.join(OUTPUT_DIR, split_name, 'labels', label_name)

                with open(label_path, "w") as f:
                    f.write(f"0 {yolo_coords[0]:.6f} {yolo_coords[1]:.6f} {yolo_coords[2]:.6f} {yolo_coords[3]:.6f}")

                shutil.copy(src_img_path, os.path.join(OUTPUT_DIR, split_name, 'images', file_name))

    # Zapisz plik z poprawnymi odpowiedziami (ground truth)
    with open(os.path.join(BASE_DIR, "val_ground_truth.json"), "w") as f:
        json.dump(ground_truth_val, f)

    # Generowanie data.yaml
    with open(os.path.join(BASE_DIR, "data.yaml"), "w") as f:
        f.write(f"path: {os.path.abspath(OUTPUT_DIR)}\n")
        f.write(f"train: train/images\n")
        f.write(f"val: val/images\n\n")
        f.write(f"names:\n  0: license_plate\n")

    print(f"Sukces! Przygotowano {len(ground_truth_val)} obrazów do testów.")


if __name__ == "__main__":
    prepare_data()