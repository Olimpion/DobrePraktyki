import time

import pika
import json
from detection import count_people


def on_request(ch, method, props, body):
    data = json.loads(body)
    url = data['url']
    print(f"Przetwarzanie: {url}")

    try:
        detections = count_people(url)
    except Exception as e:
        print(f"Błąd: {e}")
        detections = []

    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        # ZAMIANA: wysyłamy JSON, a nie zwykły string/int
        body=json.dumps(detections)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        break
    except pika.exceptions.AMQPConnectionError:
        print("Worker: RabbitMQ nie jest gotowy, czekam 5 sekund...")
        time.sleep(5)

channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=on_request)

print("Worker gotowy...")
channel.start_consuming()