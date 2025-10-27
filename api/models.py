from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, JSON, Integer, ForeignKey, DateTime, func, Index, Enum
import enum

class Base(DeclarativeBase):
    pass

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    traces: Mapped[list["Trace"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sessions_created_at", "created_at"),
    )

class DecisionEnum(str, enum.Enum):
    allow = "allow"
    warn = "warn"
    block = "block"

class Trace(Base):
    __tablename__ = "traces"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32))  # "user" | "assistant" | "tool"
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decision: Mapped[DecisionEnum] = mapped_column(Enum(DecisionEnum), default=DecisionEnum.allow)
    reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="traces")

    __table_args__ = (
        Index("ix_traces_session_created", "session_id", "created_at"),
    )

class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern: Mapped[str] = mapped_column(Text)  # regex or glob
    severity: Mapped[str] = mapped_column(String(16))  # "info" | "warning" | "critical"
    decision: Mapped[str] = mapped_column(String(16), default="warn")  # "allow" | "warn" | "block"
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(128))
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())