from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_database_connection(async_session: AsyncSession) -> None:
    result = await async_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
