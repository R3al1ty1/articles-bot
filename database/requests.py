from sqlalchemy import create_engine, exists, and_
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import os
from contextlib import contextmanager

from database.models import Session as SessionModel, User, UserSession


DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Base.metadata.create_all(engine)

SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

@contextmanager
def session_scope():
    """Контекстный менеджер для автоматического управления сессиями"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_new_user(username, tg_id):
    """Добавление нового пользователя"""
    with session_scope() as session:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            new_user = User(username=username, tg_id=tg_id)
            session.add(new_user)
            session.flush()

            new_session = SessionModel(length=15, count=2)
            session.add(new_session)
            session.flush()

            user_session = UserSession(
                user_id=new_user.tg_id,
                session_id=new_session.session_id
            )
            session.add(user_session)
            return new_user
        return None


def deduct_session(tg_id, length):
    """Списание сессии"""
    with session_scope() as session:
        user_sessions = session.query(UserSession).join(SessionModel).filter(
            UserSession.user_id == tg_id,
            SessionModel.length == length
        ).all()
        
        if not user_sessions:
            return False
        
        for user_session in user_sessions:
            session_obj = user_session.session
            if session_obj.count > 1:
                session_obj.count -= 1
            else:
                session.delete(user_session)
                session.delete(session_obj)
        return True


def check_user_has_session(tg_id, length):
    """Проверка наличия сессии"""
    with session_scope() as session:
        return session.query(exists().where(
            and_(
                UserSession.user_id == tg_id,
                UserSession.session.has(
                    and_(
                        SessionModel.length == length,
                        SessionModel.count > 0
                    )
                )
            )
        )).scalar()


def get_user_sessions(tg_id):
    """Получение сессий пользователя"""
    with session_scope() as session:
        sessions = session.query(SessionModel).join(UserSession).filter(
            UserSession.user_id == tg_id,
            SessionModel.count > 0
        ).all()

        for s in sessions:
            _ = s.session_id
            _ = s.length
            _ = s.count

        session.expunge_all()

        return sessions


def add_session_to_user(tg_id, length, count):
    """Добавление сессии пользователю"""
    with session_scope() as session:
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if not user:
                return False

            new_session = SessionModel(length=length, count=count)
            session.add(new_session)
            session.flush()
            session_id = new_session.session_id

            user_session = UserSession(user_id=tg_id, session_id=session_id)
            session.add(user_session)
            return True
        except Exception as e:
            return e
