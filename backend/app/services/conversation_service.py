"""
Conversation session management for Ask Quran chat experience.

Stores conversation history in Redis with 24-hour TTL for follow-up questions.
"""
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from app.services.redis_cache import RedisCache
from app.core.config import settings

logger = logging.getLogger(__name__)

# Session TTL: 24 hours
SESSION_TTL_SECONDS = 86400


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    role: str  # "user" | "assistant"
    content: str
    timestamp: str  # ISO format
    verses_referenced: List[str] = field(default_factory=list)  # e.g., ["2:255", "3:18"]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            verses_referenced=data.get("verses_referenced", []),
        )


@dataclass
class ConversationSession:
    """A conversation session with history."""
    session_id: str
    messages: List[ConversationMessage]
    language: str
    preferred_sources: List[str]
    created_at: str  # ISO format
    last_activity: str  # ISO format

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "language": self.language,
            "preferred_sources": self.preferred_sources,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        return cls(
            session_id=data["session_id"],
            messages=[ConversationMessage.from_dict(m) for m in data["messages"]],
            language=data["language"],
            preferred_sources=data.get("preferred_sources", []),
            created_at=data["created_at"],
            last_activity=data["last_activity"],
        )

    def get_context_for_llm(self, max_messages: int = 6) -> str:
        """
        Build context string from recent conversation history for LLM.

        Args:
            max_messages: Maximum number of recent messages to include

        Returns:
            Formatted context string for the LLM prompt
        """
        if not self.messages:
            return ""

        # Get recent messages (excluding the current question)
        recent = self.messages[-(max_messages + 1):-1] if len(self.messages) > 1 else []

        if not recent:
            return ""

        context_parts = ["=== CONVERSATION HISTORY ==="]
        for msg in recent:
            role_label = "User" if msg.role == "user" else "Assistant"
            # Truncate long messages
            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            context_parts.append(f"\n[{role_label}]: {content}")

            if msg.verses_referenced:
                context_parts.append(f"  (Referenced: {', '.join(msg.verses_referenced)})")

        context_parts.append("\n=== END HISTORY ===\n")
        return "\n".join(context_parts)


class ConversationService:
    """
    Service for managing conversation sessions.

    Uses Redis for storage with 24-hour TTL.
    """

    def __init__(self):
        self._cache: Optional[RedisCache] = None
        self._key_prefix = "tadabbur:conversation:"

    @property
    def cache(self) -> RedisCache:
        """Lazy initialization of Redis cache."""
        if self._cache is None:
            self._cache = RedisCache(
                url=settings.redis_url,
                key_prefix=self._key_prefix,
                default_ttl=SESSION_TTL_SECONDS,
            )
        return self._cache

    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"sess_{uuid.uuid4().hex[:16]}"

    async def create_session(
        self,
        language: str = "en",
        preferred_sources: List[str] = None,
    ) -> ConversationSession:
        """
        Create a new conversation session.

        Args:
            language: Session language (ar/en)
            preferred_sources: List of preferred tafseer source IDs

        Returns:
            New ConversationSession
        """
        now = datetime.utcnow().isoformat()
        session = ConversationSession(
            session_id=self.generate_session_id(),
            messages=[],
            language=language,
            preferred_sources=preferred_sources or [],
            created_at=now,
            last_activity=now,
        )

        # Store in Redis
        await self.cache.set(
            session.session_id,
            json.dumps(session.to_dict()),
            ttl=SESSION_TTL_SECONDS,
        )

        logger.info(f"Created conversation session: {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Retrieve a conversation session.

        Args:
            session_id: The session ID to retrieve

        Returns:
            ConversationSession if found, None otherwise
        """
        data = await self.cache.get(session_id)
        if not data:
            return None

        try:
            session_dict = json.loads(data)
            return ConversationSession.from_dict(session_dict)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse session {session_id}: {e}")
            return None

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        verses_referenced: List[str] = None,
    ) -> Optional[ConversationSession]:
        """
        Add a message to a conversation session.

        Args:
            session_id: The session ID
            role: Message role ("user" or "assistant")
            content: Message content
            verses_referenced: List of verse references mentioned

        Returns:
            Updated ConversationSession if found, None otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            verses_referenced=verses_referenced or [],
        )

        session.messages.append(message)
        session.last_activity = datetime.utcnow().isoformat()

        # Keep only last 20 messages to prevent unbounded growth
        if len(session.messages) > 20:
            session.messages = session.messages[-20:]

        # Update in Redis with refreshed TTL
        await self.cache.set(
            session.session_id,
            json.dumps(session.to_dict()),
            ttl=SESSION_TTL_SECONDS,
        )

        logger.debug(f"Added {role} message to session {session_id}")
        return session

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            await self.cache.delete(session_id)
            logger.info(f"Deleted conversation session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    async def get_or_create_session(
        self,
        session_id: Optional[str],
        language: str = "en",
        preferred_sources: List[str] = None,
    ) -> ConversationSession:
        """
        Get existing session or create a new one.

        Args:
            session_id: Optional existing session ID
            language: Language for new session
            preferred_sources: Preferred sources for new session

        Returns:
            Existing or new ConversationSession
        """
        if session_id:
            session = await self.get_session(session_id)
            if session:
                # Update preferred sources if provided
                if preferred_sources:
                    session.preferred_sources = preferred_sources
                return session

        # Create new session
        return await self.create_session(language, preferred_sources)


# Singleton instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get the singleton ConversationService instance."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
