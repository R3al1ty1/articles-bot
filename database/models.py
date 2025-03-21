import os
from sqlalchemy import create_engine, Column, Integer, BigInteger, Text, ForeignKey, exists, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Base.metadata.create_all(engine)


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(Text)
    tg_id = Column(BigInteger, unique=True)
    
    # Relationship is now through tg_id, not user_id
    sessions = relationship("UserSession", back_populates="user", foreign_keys="UserSession.user_id")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', tg_id={self.tg_id})>"


class Session(Base):
    __tablename__ = 'sessions'
    
    session_id = Column(BigInteger, primary_key=True)
    length = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False)

    users = relationship("UserSession", back_populates="session")
    
    def __repr__(self):
        return f"<Session(session_id={self.session_id}, length={self.length}, count={self.count})>"


class UserSession(Base):
    __tablename__ = 'users_sessions'
    
    id = Column(BigInteger, primary_key=True)
    # This references tg_id in the database, not user_id
    user_id = Column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    session_id = Column(BigInteger, ForeignKey('sessions.session_id'), nullable=False)

    user = relationship("User", back_populates="sessions", foreign_keys=[user_id])
    session = relationship("Session", back_populates="users")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"
