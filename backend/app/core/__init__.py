from sqlmodel import Session, create_engine

from app.settings import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)


class DatabaseSession:
    def __init__(self):
        self.session = Session(engine)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
