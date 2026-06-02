"""In-memory conversation repository implementation."""
from app.domain.model.conversation import Conversation
from app.domain.repository.interfaces import ConversationRepository


class InMemoryConversationRepository(ConversationRepository):
    """In-memory implementation of ConversationRepository."""

    def __init__(self):
        self._conversations: dict[str, Conversation] = {}

    async def save(self, conversation: Conversation) -> Conversation:
        """Save a conversation."""
        self._conversations[conversation.id] = conversation
        return conversation

    async def find_by_id(self, id: str) -> Conversation | None:
        """Find a conversation by ID."""
        return self._conversations.get(id)

    async def find_by_platform_id(
        self, platform: str, platform_conversation_id: str
    ) -> Conversation | None:
        """Find a conversation by platform ID."""
        for conv in self._conversations.values():
            if conv.platform.value == platform and conv.platform_conversation_id == platform_conversation_id:
                return conv
        return None