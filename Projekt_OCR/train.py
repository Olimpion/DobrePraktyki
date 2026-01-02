import os
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_YAML_PATH = os.path.join(BASE_DIR, "data.yaml")

def train_model():
    if not os.path.exists(DATA_YAML_PATH):
        print(f"BŁĄD: Nie znaleziono pliku {DATA_YAML_PATH}")
        return

    model = YOLO('yolov8n.pt')
    model.train(
        data=DATA_YAML_PATH,
        epochs=100,
        imgsz=640,
        batch=16,
        name='plate_detector'
    )

if __name__ == "__main__":
    train_model()