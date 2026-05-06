from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_health_check(client: AsyncClient, async_session: AsyncSession) -> None:
    result = await async_session.execute(text("SELECT 1"))

    response = await client.get("/api/v1/health")

    assert result.scalar_one() == 1
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
