from dataclasses import dataclass


@dataclass
class ChatbotConfig:
    """Configuration for the customer support chatbot."""

    mcp_server_url: str
    openai_api_key: str
    model: str = "gpt-4o"
    max_tokens: int = 2000
    temperature: float = 0.7

    @property
    def mcp_headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}
