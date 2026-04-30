from typing import Any
from uuid import uuid4


class ConversationManager:
    """In-memory conversation history (swap for Redis in production)."""

    def __init__(self) -> None:
        self._conversations: dict[str, list[dict[str, Any]]] = {}

    def get_conversation(self, conversation_id: str) -> list[dict[str, Any]]:
        return list(self._conversations.get(conversation_id, []))

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append({"role": role, "content": content})

    def create_conversation(self) -> str:
        conversation_id = str(uuid4())
        self._conversations[conversation_id] = []
        return conversation_id

    def clear_conversation(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)


conversation_manager = ConversationManager()
