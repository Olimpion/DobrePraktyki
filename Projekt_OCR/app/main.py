from fastapi import FastAPI, UploadFile, File
import pika
import json
from app.inference_engine import get_plate_data
from app.database import init_db

app = FastAPI()

init_db()


@app.post("/analyze-now")
async def analyze_now(file: UploadFile = File(...)):
    contents = await file.read()
    result = get_plate_data(contents)

    if result:
        return {"status": "success", "plate": result['text'], "box": result['box'].tolist()}
    return {"status": "not_found", "message": "Nie wykryto tablicy"}


@app.post("/analyze-later")
async def analyze_later(file: UploadFile = File(...)):
    contents = await file.read()

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='plates_queue')

        channel.basic_publish(exchange='', routing_key='plates_queue', body=contents)
        connection.close()
        return {"status": "queued", "message": "Zadanie dodane do kolejki RabbitMQ"}
    except Exception as e:
        return {"status": "error", "message": str(e)}