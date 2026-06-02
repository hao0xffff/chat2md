"""Repository interfaces - define repository contracts for the domain layer."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.domain.model.conversation import Conversation
from app.domain.model.image_resource import ImageResource

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save an entity."""
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> T | None:
        """Find an entity by ID."""
        pass


class ConversationRepository(Repository[Conversation], ABC):
    """Repository interface for Conversation entities."""

    @abstractmethod
    async def find_by_platform_id(self, platform: str, platform_conversation_id: str) -> Conversation | None:
        """
        Find a conversation by its platform ID.

        Args:
            platform: The platform identifier (e.g., 'chatgpt').
            platform_conversation_id: The conversation ID on the platform.

        Returns:
            The Conversation if found, None otherwise.
        """
        pass


class ImageRepository(Repository[ImageResource], ABC):
    """Repository interface for ImageResource entities."""

    @abstractmethod
    async def find_by_conversation_id(self, conversation_id: str) -> list[ImageResource]:
        """
        Find all images for a conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            A list of ImageResource entities.
        """
        pass