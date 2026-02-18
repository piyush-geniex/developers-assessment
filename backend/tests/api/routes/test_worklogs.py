import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_list_worklogs_returns_200(
    async_client: AsyncClient,
    async_superuser_token_headers: dict[str, str],
) -> None:
    resp = await async_client.get(
        f"{settings.API_V1_STR}/worklogs/",
        headers=async_superuser_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_list_worklogs_with_date_filter_returns_200(
    async_client: AsyncClient,
    async_superuser_token_headers: dict[str, str],
) -> None:
    resp = await async_client.get(
        f"{settings.API_V1_STR}/worklogs/",
        headers=async_superuser_token_headers,
        params={"date_from": "2025-01-01", "date_to": "2025-12-31"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_worklog_not_found_returns_404(
    async_client: AsyncClient,
    async_superuser_token_headers: dict[str, str],
) -> None:
    resp = await async_client.get(
        f"{settings.API_V1_STR}/worklogs/{uuid.uuid4()}",
        headers=async_superuser_token_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Worklog not found"


@pytest.mark.asyncio
async def test_list_worklogs_invalid_date_from_returns_400(
    async_client: AsyncClient,
    async_superuser_token_headers: dict[str, str],
) -> None:
    resp = await async_client.get(
        f"{settings.API_V1_STR}/worklogs/",
        headers=async_superuser_token_headers,
        params={"date_from": "not-a-date"},
    )
    assert resp.status_code == 400
