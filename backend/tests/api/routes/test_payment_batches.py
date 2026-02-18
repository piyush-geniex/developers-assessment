import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_create_payment_batch_returns_201(
    async_client: AsyncClient,
    async_superuser_token_headers: dict[str, str],
) -> None:
    resp = await async_client.post(
        f"{settings.API_V1_STR}/payment-batches/",
        headers=async_superuser_token_headers,
        json={
            "worklog_ids": None,
            "exclude_worklog_ids": None,
            "exclude_freelancer_ids": None,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "worklog_count" in data
    assert "total_amount" in data
    assert data["worklog_count"] == 0
    assert data["total_amount"] == 0.0


@pytest.mark.asyncio
async def test_create_payment_batch_with_empty_lists_returns_201(
    async_client: AsyncClient,
    async_superuser_token_headers: dict[str, str],
) -> None:
    resp = await async_client.post(
        f"{settings.API_V1_STR}/payment-batches/",
        headers=async_superuser_token_headers,
        json={
            "worklog_ids": [],
            "exclude_worklog_ids": [],
            "exclude_freelancer_ids": [],
        },
    )
    assert resp.status_code == 201
