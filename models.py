from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    max_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    group_id: Mapped[int] = mapped_column(BigInteger, default=478015)
    group_name: Mapped[str] = mapped_column(String(64), default="АСУб-23-1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    max_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    query: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)