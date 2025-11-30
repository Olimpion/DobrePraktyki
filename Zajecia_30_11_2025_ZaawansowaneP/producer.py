import csv
import time
import uuid
import os

DB_FILE = 'tasks.csv'
LOCK_FILE = 'tasks.lock'


def acquire_lock():
    while os.path.exists(LOCK_FILE):
        time.sleep(0.1)
    with open(LOCK_FILE, 'w') as f:
        f.write('LOCKED')


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def main():
    task_id = str(uuid.uuid4())

    acquire_lock()
    try:
        file_exists = os.path.exists(DB_FILE)

        with open(DB_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['id', 'status'])

            writer.writerow([task_id, 'pending'])

        print(f"[Producer] Dodano zadanie ID: {task_id}")
    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        release_lock()


if __name__ == '__main__':
    main()