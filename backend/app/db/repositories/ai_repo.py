"""
SQLAlchemy repository for AI Assistant conversations and messages.

Enforces strict user isolation across all conversation and message queries.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import AIConversationModel, AIMessageModel


class SQLAIRepository:
    """Repository for managing AI conversations and grounded message history."""

    def __init__(self, session: Session):
        self.session = session

    def create_conversation(
        self, user_id: str, title: str = "Financial Assistant Conversation"
    ) -> AIConversationModel:
        """Create a new conversational thread scoped to user_id."""
        conv = AIConversationModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title.strip() if title else "Financial Assistant Conversation",
        )
        self.session.add(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[AIConversationModel]:
        """Fetch a conversation by ID, strictly verifying ownership."""
        stmt = (
            select(AIConversationModel)
            .where(
                AIConversationModel.id == conversation_id,
                AIConversationModel.user_id == user_id,
            )
            .options(joinedload(AIConversationModel.messages))
        )
        return self.session.scalars(stmt).unique().first()

    def list_conversations(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[AIConversationModel]:
        """List active conversations for user_id ordered by latest update."""
        stmt = (
            select(AIConversationModel)
            .where(AIConversationModel.user_id == user_id)
            .options(joinedload(AIConversationModel.messages))
            .order_by(AIConversationModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).unique().all())

    def update_conversation_title(
        self, conversation_id: str, user_id: str, title: str
    ) -> Optional[AIConversationModel]:
        """Update conversation title."""
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return None
        conv.title = title.strip()
        conv.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation thread and all its messages."""
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return False
        self.session.delete(conv)
        self.session.commit()
        return True

    def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        data_sources: Optional[List[str]] = None,
    ) -> AIMessageModel:
        """Append a message to a conversation thread and touch thread updated_at."""
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            raise ValueError(f"Conversation '{conversation_id}' not found or access denied.")

        msg = AIMessageModel(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            role=role.strip().lower(),
            content=content.strip(),
            data_sources=data_sources or [],
        )
        self.session.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def get_recent_messages(
        self, conversation_id: str, user_id: str, limit: int = 10
    ) -> List[AIMessageModel]:
        """Retrieve bounded recent message history for context window."""
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return []
        stmt = (
            select(AIMessageModel)
            .where(
                AIMessageModel.conversation_id == conversation_id,
                AIMessageModel.user_id == user_id,
            )
            .order_by(AIMessageModel.created_at.desc())
            .limit(limit)
        )
        recent = list(self.session.scalars(stmt).all())
        # Return in chronological order
        recent.reverse()
        return recent
