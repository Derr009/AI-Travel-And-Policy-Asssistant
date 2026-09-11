"""Persistent conversation memory backed by PostgreSQL."""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from sqlalchemy import BigInteger, DateTime, String, Text, create_engine, delete, select, update
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class MemoryBase(DeclarativeBase):
    pass


class Conversation(MemoryBase):
    __tablename__ = "conversations"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class ConversationMessage(MemoryBase):
    __tablename__ = "conversation_messages"

    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ConversationState(MemoryBase):
    __tablename__ = "conversation_state"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    state_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for PostgreSQL conversation memory.")
    return database_url


def _engine():
    return create_engine(_database_url(), pool_pre_ping=True)


def _conversation_uuid(conversation_id: str | uuid.UUID) -> uuid.UUID:
    return conversation_id if isinstance(conversation_id, uuid.UUID) else uuid.UUID(conversation_id)


class ConversationMemory:
    """Read and write bounded conversation context for one conversation."""

    def __init__(self, recent_message_limit: int = 6) -> None:
        if recent_message_limit < 1:
            raise ValueError("recent_message_limit must be at least 1.")
        self.recent_message_limit = recent_message_limit
        self.engine = _engine()

    def create_conversation(self, user_id: str | None = None) -> str:
        now = datetime.now().astimezone()
        conversation = Conversation(
            user_id=user_id,
            created_at=now,
            updated_at=now,
            status="active",
        )
        with Session(self.engine) as session:
            session.add(conversation)
            session.commit()
            return str(conversation.conversation_id)

    def list_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent conversations for an employee in the open training environment."""
        if not user_id or limit < 1:
            return []
        with Session(self.engine) as session:
            conversations = list(
                session.scalars(
                    select(Conversation)
                    .where(Conversation.user_id == user_id.strip().upper())
                    .order_by(Conversation.updated_at.desc())
                    .limit(limit)
                )
            )
        return [
            {
                "conversation_id": str(conversation.conversation_id),
                "user_id": conversation.user_id,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "status": conversation.status,
            }
            for conversation in conversations
        ]

    def add_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError("Invalid message role.")
        if not content or not content.strip():
            raise ValueError("Message content must not be empty.")
        conversation_uuid = _conversation_uuid(conversation_id)
        now = datetime.now().astimezone()
        with Session(self.engine) as session:
            message = ConversationMessage(
                conversation_id=conversation_uuid,
                role=role,
                content=content.strip(),
                created_at=now,
            )
            session.add(message)
            session.execute(
                update(Conversation)
                .where(Conversation.conversation_id == conversation_uuid)
                .values(updated_at=now)
            )
            session.commit()
            return {
                "message_id": message.message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content.strip(),
                "created_at": now.isoformat(),
            }

    def get_recent_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        conversation_uuid = _conversation_uuid(conversation_id)
        with Session(self.engine) as session:
            messages = list(
                session.scalars(
                    select(ConversationMessage)
                    .where(ConversationMessage.conversation_id == conversation_uuid)
                    .order_by(ConversationMessage.created_at.desc())
                    .limit(self.recent_message_limit)
                )
            )
        return [
            {
                "message_id": message.message_id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in reversed(messages)
        ]

    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        conversation_uuid = _conversation_uuid(conversation_id)
        with Session(self.engine) as session:
            state = session.get(ConversationState, conversation_uuid)
        return dict(state.state_json) if state else {}

    def update_state(self, conversation_id: str, state_json: Dict[str, Any]) -> None:
        conversation_uuid = _conversation_uuid(conversation_id)
        now = datetime.now().astimezone()
        with Session(self.engine) as session:
            state = session.get(ConversationState, conversation_uuid)
            if state:
                state.state_json = state_json
                state.updated_at = now
            else:
                session.add(
                    ConversationState(
                        conversation_id=conversation_uuid,
                        state_json=state_json,
                        updated_at=now,
                    )
                )
            session.commit()

    def clear_conversation(self, conversation_id: str) -> None:
        """Delete stored messages and state while keeping the conversation ID."""
        conversation_uuid = _conversation_uuid(conversation_id)
        with Session(self.engine) as session:
            session.execute(
                delete(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation_uuid
                )
            )
            session.execute(
                delete(ConversationState).where(
                    ConversationState.conversation_id == conversation_uuid
                )
            )
            session.commit()

    def delete_conversation(self, conversation_id: str) -> None:
        """Permanently remove a conversation and its related records."""
        conversation_uuid = _conversation_uuid(conversation_id)
        with Session(self.engine) as session:
            conversation = session.get(Conversation, conversation_uuid)
            if conversation is None:
                raise ValueError("Conversation was not found.")
            session.delete(conversation)
            session.commit()