import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.mark.asyncio
async def test_get_worklogs(client: AsyncClient):
    resp = await client.get("/api/worklog/worklogs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_get_freelancers(client: AsyncClient):
    resp = await client.get("/api/worklog/freelancers")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_get_worklog_detail_not_found(client: AsyncClient):
    resp = await client.get("/api/worklog/worklogs/99999")
    assert resp.status_code == 404
