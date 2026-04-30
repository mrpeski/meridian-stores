from types import SimpleNamespace

import pytest

from meridian_stores.agents.chatbot_config import ChatbotConfig
from meridian_stores.agents.llm_clients import OpenAIClient


def test_chatbot_config_mcp_headers() -> None:
    cfg = ChatbotConfig(
        mcp_server_url="https://example.com/mcp",
        openai_api_key="test-key",
        model="gpt-4o",
    )
    assert cfg.model == "gpt-4o"
    assert cfg.mcp_headers["Accept"] == "application/json"


def test_openai_client_tool_conversion() -> None:
    cfg = SimpleNamespace(model="gpt-4o", system_prompt="test")

    client = OpenAIClient(cfg, api_key="test-key")

    mock_tool = SimpleNamespace(
        name="test_tool",
        description="A test tool",
        inputSchema={"type": "object", "properties": {}},
    )

    converted = client.convert_tools([mock_tool])

    assert len(converted) == 1
    assert converted[0]["type"] == "function"
    assert converted[0]["function"]["name"] == "test_tool"


@pytest.mark.asyncio
async def test_openai_assistant_message_is_plain_dict() -> None:
    cfg = SimpleNamespace(model="gpt-4o", system_prompt=None)

    client = OpenAIClient(cfg, api_key="test-key")

    raw = SimpleNamespace(content="Hello", tool_calls=None)
    msg = client.assistant_message(raw)

    assert msg == {"role": "assistant", "content": "Hello"}
