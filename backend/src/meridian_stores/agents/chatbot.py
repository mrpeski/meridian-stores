from types import SimpleNamespace

from mcp import ClientSession

from meridian_stores.agents.chatbot_config import ChatbotConfig
from meridian_stores.agents.llm_clients import OpenAIClient
from meridian_stores.agents.system_prompt import CUSTOMER_SUPPORT_PROMPT

_MAX_TOOL_ROUNDS = 24


def _tool_output_text(result: object) -> str:
    chunks: list[str] = []
    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if text is not None:
            chunks.append(text)
        else:
            chunks.append(str(block))
    return "\n".join(chunks) if chunks else ""


def _merge_usage(
    acc: dict[str, int] | None, part: dict[str, int] | None
) -> dict[str, int] | None:
    if not part:
        return acc
    if acc is None:
        return dict(part)
    out = dict(acc)
    for k, v in part.items():
        out[k] = out.get(k, 0) + v
    return out


class CustomerSupportBot:
    """Customer support chatbot: OpenAI tool calls against an MCP session."""

    def __init__(self, config: ChatbotConfig, session: ClientSession) -> None:
        self.config = config
        self.session = session
        self.llm: OpenAIClient | None = None
        self.tools: list = []

    async def initialize(self) -> None:
        await self.session.initialize()
        mcp_tools = (await self.session.list_tools()).tools
        llm_cfg = SimpleNamespace(
            model=self.config.model,
            system_prompt=CUSTOMER_SUPPORT_PROMPT,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        self.llm = OpenAIClient(llm_cfg, api_key=self.config.openai_api_key)
        self.tools = self.llm.convert_tools(mcp_tools)

    async def handle_message(
        self,
        user_message: str,
        conversation_history: list[dict],
    ) -> tuple[str, list[str], dict[str, int] | None]:
        if self.llm is None:
            raise RuntimeError("CustomerSupportBot.initialize() must be called first")

        messages: list = [*conversation_history, {"role": "user", "content": user_message}]
        final_messages, tool_names, usage = await self._run_llm_loop(messages)

        last = final_messages[-1]
        if not isinstance(last, dict) or last.get("role") != "assistant":
            return "Sorry, something went wrong. Please try again.", tool_names, usage

        text = last.get("content")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        return text, tool_names, usage

    async def _run_llm_loop(self, messages: list) -> tuple[list, list[str], dict[str, int] | None]:
        assert self.llm is not None
        tool_calls_made: list[str] = []
        usage_total: dict[str, int] | None = None
        rounds = 0

        while rounds < _MAX_TOOL_ROUNDS:
            rounds += 1
            response = await self.llm.complete(messages, self.tools)
            usage_total = _merge_usage(usage_total, response.get("usage"))

            messages.append(self.llm.assistant_message(response["raw"]))

            if not response["tool_calls"]:
                break

            tool_results: list[dict] = []
            for tc in response["tool_calls"]:
                tool_calls_made.append(tc["name"])
                out = await self._execute_tool(tc["name"], tc["args"])
                tool_results.append({"id": tc["id"], "output": out})

            tool_msgs = self.llm.user_message(tool_results)
            messages.extend(tool_msgs if isinstance(tool_msgs, list) else [tool_msgs])
        else:
            raise RuntimeError("Tool loop exceeded maximum rounds")

        return messages, tool_calls_made, usage_total

    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        result = await self.session.call_tool(tool_name, args)
        return _tool_output_text(result)

    async def close(self) -> None:
        if self.llm is not None:
            await self.llm.close()
