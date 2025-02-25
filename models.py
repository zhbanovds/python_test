from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Таблица пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # Роли: user, admin, etc.
    chat_id = Column(String, nullable=True)  # ➡️ Добавлено поле chat_id
    login_history = relationship("LoginHistory", back_populates="user")

# Таблица для истории логинов
class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    login_time = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    login_method = Column(String)  # JWT, OAuth и т.д.

    user = relationship("User", back_populates="login_history")
