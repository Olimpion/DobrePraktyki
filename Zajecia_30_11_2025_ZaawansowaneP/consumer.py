import csv
import time
import os
import shutil

DB_FILE = 'tasks.csv'
LOCK_FILE = 'tasks.lock'
TEMP_FILE = 'tasks_temp.csv'


def acquire_lock():
    while os.path.exists(LOCK_FILE):
        time.sleep(0.1)
    with open(LOCK_FILE, 'w') as f:
        f.write('LOCKED')


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def get_and_start_task():
    if not os.path.exists(DB_FILE):
        return None

    task_id_to_process = None
    rows = []

    acquire_lock()
    try:
        with open(DB_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                rows.append(header)

            found = False
            for row in reader:
                # row[0] -> id, row[1] -> status
                if not found and row[1] == 'pending':
                    row[1] = 'in_progress'
                    task_id_to_process = row[0]
                    found = True
                rows.append(row)

        if task_id_to_process:
            with open(TEMP_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            shutil.move(TEMP_FILE, DB_FILE)

    finally:
        release_lock()

    return task_id_to_process


def finish_task(task_id):
    acquire_lock()
    try:
        rows = []
        with open(DB_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 0 and row[0] == task_id:
                    row[1] = 'done'
                rows.append(row)

        with open(TEMP_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        shutil.move(TEMP_FILE, DB_FILE)
    finally:
        release_lock()


def main():
    print("[Consumer] Start pracy...")
    while True:
        task_id = get_and_start_task()

        if task_id:
            print(f"[Consumer] Pobrana praca: {task_id}. Wykonywanie (30s)...")
            time.sleep(30)

            finish_task(task_id)
            print(f"[Consumer] Zakończono pracę: {task_id}. Status: done.")
        else:
            time.sleep(5)


if __name__ == '__main__':
    main()