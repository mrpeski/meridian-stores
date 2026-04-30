import pytest
from httpx import ASGITransport, AsyncClient

from meridian_stores.app import app
from meridian_stores.settings import settings


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["project"] == "meridian-stores"
    assert body["service"] == "meridian-stores-svc"


@pytest.mark.asyncio
async def test_hello() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/hello")
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Hello from meridian-stores."
    assert body["project"] == "meridian-stores"
    assert body["service"] == "meridian-stores-svc"


@pytest.mark.asyncio
async def test_chat_requires_message() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/chat", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_chat_rejects_empty_message() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/chat", json={"message": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_openai_key_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/chat", json={"message": "Hi"})
    assert r.status_code == 503
    err = r.json()["error"]
    assert err["code"] == "configuration_error"
