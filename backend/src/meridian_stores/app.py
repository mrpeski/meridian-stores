"""FastAPI app: minimal routes, exception handlers first, CORS outermost."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from meridian_stores.settings import settings


class HelloWorldError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code


app = FastAPI(title=settings.app_name)


@app.exception_handler(HelloWorldError)
async def _hello_error(_request: Request, exc: HelloWorldError) -> JSONResponse:
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
