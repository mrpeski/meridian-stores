import os
import asyncio
from agent_config import AgentConfig
from agent import run_agent
from config import MCP_SERVER_URL, player_name

MCP_URL = MCP_SERVER_URL

AGENT_SPECS = {player_name: {"provider": "openai", "personality": ()}}


def ollama_agent(name, system_prompt):
    return AgentConfig(
        player_name=name,
        mcp_server_url=MCP_URL,
        llm_provider="ollama",
        api_key="",
        model="gpt-oss:120b-cloud",
    )


def openai_agent(name, system_prompt):
    return AgentConfig(
        player_name=name,
        mcp_server_url=MCP_URL,
        llm_provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-5.4-nano",
    )


def anthropic_agent(name, system_prompt):
    return AgentConfig(
        player_name=name,
        mcp_server_url=MCP_URL,
        llm_provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        model="claude-haiku-4-5-20251001",
    )


def make_agent(name: str, spec: dict) -> AgentConfig:
    """Factory that builds an AgentConfig from a spec dict."""
    provider = spec.get("provider", "ollama")
    system_prompt = spec.get("system_prompt", "")

    if provider == "ollama":
        return ollama_agent(name, system_prompt)
    if provider == "openai":
        return openai_agent(name, system_prompt)
    if provider == "anthropic":
        return anthropic_agent(name, system_prompt)

    return ollama_agent(name, system_prompt)


configs = [make_agent(name, spec) for name, spec in AGENT_SPECS.items()]


async def main():
    await asyncio.gather(*[run_agent(cfg) for cfg in configs], return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
