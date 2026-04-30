import json
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def convert_tools(self, mcp_tools: list) -> list:
        pass

    @abstractmethod
    async def complete(self, messages: list, tools: list) -> dict:
        """Return normalized response: {content, stop_reason, tool_calls}"""
        pass


class AnthropicClient(LLMClient):
    def __init__(self, config):
        import httpx

        self.http = httpx.AsyncClient(
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        )
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.system_prompt = config.system_prompt
        self._cached_tools = None  # built once, reused every call

    def convert_tools(self, mcp_tools: list) -> list:
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in mcp_tools
        ]
        # Mark the LAST tool with cache_control — caches all tools as a prefix
        if tools:
            tools[-1]["cache_control"] = {"type": "ephemeral"}
        self._cached_tools = tools
        return tools

    def _build_system(self) -> list:
        """System as a list of blocks so we can attach cache_control."""
        if not self.system_prompt:
            return []
        return [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},  # cache system prompt too
            }
        ]

    async def complete(self, messages: list, tools: list) -> dict:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "tools": self._cached_tools or tools,  # always use cached tool list
            "messages": messages,
        }
        system = self._build_system()
        if system:
            payload["system"] = system

        response = await self.http.post(
            "https://api.anthropic.com/v1/messages", json=payload
        )
        response.raise_for_status()
        data = response.json()

        # Log cache usage so you can see savings
        usage = data.get("usage", {})
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)
        if cache_read or cache_write:
            print(
                f"  [cache] read={cache_read} write={cache_write} normal={usage.get('input_tokens', 0)}"
            )

        tool_calls = [
            {
                "id": b["id"],
                "name": b["name"],
                "args": b["input"],
            }
            for b in data["content"]
            if b["type"] == "tool_use"
        ]

        return {
            "raw": data["content"],
            "done": data["stop_reason"] == "end_turn",
            "tool_calls": tool_calls,
        }

    def user_message(self, tool_results: list) -> dict:
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": r["id"],
                    "content": r["output"],
                }
                for r in tool_results
            ],
        }

    def assistant_message(self, raw) -> dict:
        return {"role": "assistant", "content": raw}

    async def close(self):
        await self.http.aclose()


class OpenAIClient(LLMClient):
    def __init__(self, config, base_url: str = None, api_key: str = None):
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = config.model
        self.system_prompt = config.system_prompt
        self.max_tokens = getattr(config, "max_tokens", None)
        self.temperature = getattr(config, "temperature", None)

    def convert_tools(self, mcp_tools: list) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_tools
        ]

    async def complete(self, messages: list, tools: list) -> dict:
        full_messages = messages
        if self.system_prompt:
            full_messages = [
                {"role": "system", "content": self.system_prompt},
                *messages,
            ]

        kwargs: dict = {
            "model": self.model,
            "messages": full_messages,
        }
        if tools:
            kwargs["tools"] = tools
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        response = await self.client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        tool_calls = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": args,
                }
            )

        usage_info = None
        if response.usage is not None:
            usage_info = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "raw": msg,
            "done": finish_reason == "stop",
            "tool_calls": tool_calls,
            "usage": usage_info,
        }

    def user_message(self, tool_results: list) -> list:
        out = []
        for r in tool_results:
            content = r["output"]
            if not isinstance(content, str):
                content = json.dumps(content)
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": r["id"],
                    "content": content,
                }
            )
        return out

    def assistant_message(self, raw) -> dict:
        msg_dict: dict = {"role": "assistant", "content": raw.content}
        tcalls = getattr(raw, "tool_calls", None)
        if tcalls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments or "{}",
                    },
                }
                for tc in tcalls
            ]
        return msg_dict

    async def close(self):
        pass


def make_llm_client(config) -> LLMClient:
    provider = config.llm_provider
    if provider == "anthropic":
        return AnthropicClient(config)
    elif provider == "openai":
        return OpenAIClient(config)
    elif provider == "ollama":
        return OpenAIClient(
            config,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
    elif provider == "groq":
        return OpenAIClient(config, base_url="https://api.groq.com/openai/v1")
    else:
        raise ValueError(f"Unknown provider: {provider}")
