import pika
import os
from app.inference_engine import get_plate_data
from app.database import save_result


def callback(ch, method, properties, body):
    print(" [x] Odebrano zdjęcie z kolejki. Przetwarzam...")

    result = get_plate_data(body)

    if result:
        plate_text = result['text']
        save_result(plate_text)
        print(f" [v] Zapisano tablicę: {plate_text}")
    else:
        print(" [!] Nie wykryto tablicy na zdjęciu z kolejki.")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='plates_queue')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='plates_queue', on_message_callback=callback)

    print(' [*] Worker uruchomiony. Czekam na dane. Ctrl+C by wyjść.')
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()