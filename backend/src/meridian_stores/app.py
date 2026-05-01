"""FastAPI app: minimal routes, exception handlers first, CORS outermost."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from meridian_stores.agents.chatbot import CustomerSupportBot
from meridian_stores.agents.chatbot_config import ChatbotConfig
from meridian_stores.agents.conversation_manager import conversation_manager
from meridian_stores.settings import settings


class MeridianStoresError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code


app = FastAPI(title=settings.app_name)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None
    customer_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    metadata: dict = Field(default_factory=dict)


@app.exception_handler(MeridianStoresError)
async def _hello_error(_request: Request, exc: MeridianStoresError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(StarletteHTTPException)
async def _http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
async def _fallback(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {"code": "internal_error", "message": "Internal server error"}
        },
    )


_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
_allow_credentials = "*" not in _origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins != ["*"] else ["*"],
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "project": settings.project_name,
        "service": settings.service_name,
    }


@app.get("/api/hello")
async def hello() -> dict[str, str]:
    return {
        "message": settings.hello_message,
        "project": settings.project_name,
        "service": settings.service_name,
    }


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    if not settings.openai_api_key.strip():
        raise MeridianStoresError(
            code="configuration_error",
            message="OpenAI API key is not configured",
            status_code=503,
        )

    conversation_id = (
        request.conversation_id or conversation_manager.create_conversation()
    )
    history = conversation_manager.get_conversation(conversation_id)

    config = ChatbotConfig(
        mcp_server_url=settings.mcp_server_url,
        openai_api_key=settings.openai_api_key,
        model=settings.chatbot_model,
    )

    try:
        async with streamablehttp_client(
            url=config.mcp_server_url,
            headers=config.mcp_headers,
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                bot = CustomerSupportBot(config, session)
                await bot.initialize()
                try:
                    bot_response, tool_calls, usage = await bot.handle_message(
                        request.message,
                        history,
                    )
                finally:
                    await bot.close()
    except MeridianStoresError:
        raise
    except Exception as e:
        raise MeridianStoresError(
            code="chatbot_error",
            message=f"Failed to process chat message: {type(e).__name__}: {e}",
            status_code=502,
        ) from e

    conversation_manager.add_message(conversation_id, "user", request.message)
    conversation_manager.add_message(conversation_id, "assistant", bot_response)

    metadata: dict = {"tool_calls": tool_calls}
    if usage and usage.get("total_tokens") is not None:
        metadata["tokens_used"] = usage["total_tokens"]

    return ChatResponse(
        response=bot_response,
        conversation_id=conversation_id,
        metadata=metadata,
    )
