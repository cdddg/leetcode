from contextlib import ContextDecorator

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

_engine = None
_Session = None


def get_engine(datebase='sqlite:///splite.db'):
    global _engine
    if _engine is None:
        _engine = create_engine(datebase, pool_pre_ping=True, echo=False)

    return _engine


def get_session():
    global _Session
    if _Session is None:
        _Session = scoped_session(sessionmaker(bind=get_engine()))

    return _Session()


class transaction(ContextDecorator):
    def __init__(self):
        self._session = None

    def __enter__(self):
        self._session = get_session()
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if not (exc_type and exc_value and traceback):
                self._session.commit()
        finally:
            self._session.close()
