import time
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URI = 'sqlite:///tasks.db'
Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    status = Column(String)

engine = create_engine(DB_URI, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_and_start_task():

    session = Session()
    try:
        candidate = session.query(Task).filter_by(status='pending').first()

        if not candidate:
            return None

        task_id = candidate.id

        rows_updated = session.query(Task).filter(
            Task.id == task_id,
            Task.status == 'pending'
        ).update({'status': 'in_progress'})

        session.commit()

        if rows_updated == 1:
            return task_id
        else:
            return None

    except Exception as e:
        print(f"Błąd bazy danych: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def finish_task(task_id):
    session = Session()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            task.status = 'done'
            session.commit()
    except Exception as e:
        print(f"Błąd podczas kończenia zadania: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    print("[Consumer] Start pracy (SQLite + SQLAlchemy)...")
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