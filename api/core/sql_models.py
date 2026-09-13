import os
import uuid
from datetime import UTC, datetime
from enum import Enum
from zoneinfo import ZoneInfo

from sqlalchemy import UUID, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String

from api.core.db import Base

PG_TABLE = os.getenv("PG_TABLE", "voice-bot")
PG_ENUM = os.getenv("PG_ENUM", "voice-file-enum")


def current_time():
    return datetime.now(tz=UTC)


def to_ist(value: datetime | None) -> str | None:
    IST = ZoneInfo(key="Asia/Kolkata")
    if value is None:
        return None
    return value.astimezone(IST).isoformat()


class FileState(Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    # retrying = "retrying"
    # cancel_requested = "cancel_requested"
    # cancelled = "cancelled"


class VoiceFile(Base):
    __tablename__ = PG_TABLE

    transaction_id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    file_name = Column(String, nullable=False)
    status = Column(
        SQLEnum(FileState, name=PG_ENUM, native_enum=True),
        default=FileState.queued,
    )
    created_at = Column(DateTime(timezone=True), default=current_time)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    upload_path = Column(String, nullable=False)
    processed_path = Column(String, nullable=True)
