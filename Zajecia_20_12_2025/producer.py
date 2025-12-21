from fastapi import FastAPI
import pika
import json
import uuid
import time

app = FastAPI()


class RabbitMQClient:
    def __init__(self):
        # Próba połączenia z rety-em (na wypadek gdyby Rabbit startował wolniej niż API)
        for i in range(10):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host='rabbitmq', heartbeat=600)
                )
                break
            except pika.exceptions.AMQPConnectionError:
                print(f"Oczekiwanie na RabbitMQ... (próba {i + 1}/10)")
                time.sleep(5)

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, url):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps({'url': url}))

        while self.response is None:
            self.connection.process_data_events()

        return json.loads(self.response.decode('utf-8'))


# --- SINGLETON ---
# Zmienna globalna, która przechowa instancję klienta
rabbitmq_client = None


@app.on_event("startup")
def startup_event():
    global rabbitmq_client
    rabbitmq_client = RabbitMQClient()


@app.get("/analyze_img")
async def analyze_img(image_url: str):
    # Teraz 'detections' to lista słowników z koordynatami i pewnością
    detections = rabbitmq_client.call(image_url)

    return {
        "status": "Gotowe",
        "url": image_url,
        "people_count": len(detections),  # Liczymy elementy listy
        "detections": detections  # Zwracamy pełne dane o ramkach
    }