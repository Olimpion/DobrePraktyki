import uuid
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


def main():
    task_id = str(uuid.uuid4())
    session = Session()

    try:
        new_task = Task(id=task_id, status='pending')

        session.add(new_task)
        session.commit()

        print(f"[Producer] Dodano zadanie ID: {task_id}")
    except Exception as e:
        session.rollback()
        print(f"Błąd: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    main()