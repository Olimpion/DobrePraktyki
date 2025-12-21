from ultralytics import YOLO

# Inicjalizacja modelu (pobierze się automatycznie za pierwszym razem)
# yolov8n.pt to wersja "nano" - bardzo szybka i lekka
model = YOLO('yolov8n.pt')


def count_people(image_url):
    """
    Wykrywa osoby na obrazie i zwraca listę wyników.
    Każdy element to słownik z koordynatami i pewnością.
    """
    # Wykonujemy detekcję
    # conf=0.3 - próg pewności (30%)
    # classes=[0] - interesuje nas tylko klasa 'person' (indeks 0 w YOLO)
    # verbose=False - wyłącza logi w konsoli
    results = model.predict(source=image_url, conf=0.3, classes=[0], verbose=False)

    detected_people = []

    # results[0] zawiera wyniki dla przesłanego obrazu
    for box in results[0].boxes:
        # Pobieramy współrzędne ramki (x1, y1, x2, y2)
        coords = box.xyxy[0].tolist()
        # Pobieramy pewność (confidence)
        confidence = float(box.conf[0])

        detected_people.append({
            "box": [round(x, 2) for x in coords],  # [lewo, góra, prawo, dół]
            "confidence": round(confidence, 4)
        })

    return detected_people