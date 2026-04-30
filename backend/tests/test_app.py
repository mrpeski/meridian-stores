import pytest
from httpx import ASGITransport, AsyncClient

from meridian_stores.app import app


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
