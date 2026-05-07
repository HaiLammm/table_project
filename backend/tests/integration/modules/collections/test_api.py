from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.app.db.base import Base
from src.app.db.session import get_async_session
from src.app.main import app
from src.app.modules.auth.api.dependencies import get_current_user
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.value_objects import UserTier
from src.app.modules.auth.infrastructure.models import UserModel
from src.app.modules.collections.infrastructure.models import CollectionModel, CollectionTermModel
from src.app.modules.srs.infrastructure.models import SrsCardModel
from src.app.modules.vocabulary.infrastructure.models import VocabularyTermModel


@pytest_asyncio.fixture
async def collections_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    assert UserModel.__table__ is not None
    assert VocabularyTermModel.__table__ is not None
    assert SrsCardModel.__table__ is not None
    assert CollectionModel.__table__ is not None
    assert CollectionTermModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def collections_client(
    collections_schema: None,
    async_engine: AsyncEngine,
) -> AsyncGenerator[tuple[AsyncClient, User], None]:
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        user_model = UserModel(
            clerk_id="collections_user",
            email="collections@example.com",
            display_name="Collections User",
        )
        session.add(user_model)
        await session.commit()
        await session.refresh(user_model)

    user = User(
        id=user_model.id,
        clerk_id=user_model.clerk_id,
        email=user_model.email,
        display_name=user_model.display_name,
        tier=UserTier.FREE,
    )

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client, user

    app.dependency_overrides.clear()


async def test_collections_api_crud_flow(
    collections_client: tuple[AsyncClient, User],
) -> None:
    client, _user = collections_client

    create_response = await client.post(
        "/api/v1/collections",
        json={"name": "TOEIC", "icon": "📚"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "TOEIC"
    assert created["icon"] == "📚"
    assert created["term_count"] == 0
    assert created["mastery_percent"] == 0

    list_response = await client.get("/api/v1/collections")
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    collection_id = created["id"]
    detail_response = await client.get(f"/api/v1/collections/{collection_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == collection_id

    update_response = await client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"name": "TOEIC Writing"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "TOEIC Writing"

    delete_response = await client.delete(f"/api/v1/collections/{collection_id}")
    assert delete_response.status_code == 204

    final_list_response = await client.get("/api/v1/collections")
    assert final_list_response.status_code == 200
    assert final_list_response.json()["items"] == []


async def test_collections_api_returns_mastery_percent(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {
                    "id": 1001,
                    "term": "protocol",
                    "language": "en",
                    "part_of_speech": "noun",
                    "created_at": now,
                },
                {
                    "id": 1002,
                    "term": "deploy",
                    "language": "en",
                    "part_of_speech": "verb",
                    "created_at": now,
                },
            ],
        )
        session.add(CollectionModel(id=2001, user_id=user.id or 0, name="Backend", icon="💻"))
        await session.commit()
        await session.execute(
            insert(CollectionTermModel),
            [
                {"collection_id": 2001, "term_id": 1001},
                {"collection_id": 2001, "term_id": 1002},
            ],
        )
        await session.execute(
            insert(SrsCardModel),
            [
                {
                    "user_id": user.id,
                    "term_id": 1001,
                    "language": "en",
                    "due_at": now - timedelta(days=1),
                    "fsrs_state": {"state": 2},
                    "stability": 24.0,
                    "difficulty": 3.0,
                    "reps": 5,
                    "lapses": 0,
                },
                {
                    "user_id": user.id,
                    "term_id": 1002,
                    "language": "en",
                    "due_at": now - timedelta(days=1),
                    "fsrs_state": {"state": 2},
                    "stability": 10.0,
                    "difficulty": 4.0,
                    "reps": 3,
                    "lapses": 1,
                },
            ],
        )
        await session.commit()

    response = await client.get("/api/v1/collections")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["term_count"] == 2
    assert item["mastery_percent"] == 50


async def test_collections_api_delete_keeps_terms_and_removes_associations(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel).values(
                id=3001,
                term="invoice",
                language="en",
                part_of_speech="noun",
                created_at=now,
            )
        )
        session.add(CollectionModel(id=3002, user_id=user.id or 0, name="Work", icon="💼"))
        await session.commit()
        await session.execute(insert(CollectionTermModel).values(collection_id=3002, term_id=3001))
        await session.commit()

    response = await client.delete("/api/v1/collections/3002")
    assert response.status_code == 204

    async with session_factory() as session:
        collection_count = await session.scalar(select(func.count(CollectionModel.id)))
        association_count = await session.scalar(select(func.count(CollectionTermModel.id)))
        term_count = await session.scalar(select(func.count(VocabularyTermModel.id)))

    assert collection_count == 0
    assert association_count == 0
    assert term_count == 1


async def test_collections_api_rejects_duplicate_names_per_user(
    collections_client: tuple[AsyncClient, User],
) -> None:
    client, _user = collections_client

    first_response = await client.post(
        "/api/v1/collections",
        json={"name": "Networking", "icon": "🌍"},
    )
    duplicate_response = await client.post(
        "/api/v1/collections",
        json={"name": "Networking", "icon": "💻"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "duplicate_collection"


async def test_collections_api_adds_lists_and_removes_terms(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {
                    "id": 4001,
                    "term": "protocol",
                    "language": "en",
                    "cefr_level": "B2",
                    "created_at": now,
                },
                {
                    "id": 4002,
                    "term": "deploy",
                    "language": "en",
                    "part_of_speech": "verb",
                    "created_at": now,
                },
            ],
        )
        session.add(CollectionModel(id=4100, user_id=user.id or 0, name="Backend", icon="💻"))
        await session.commit()
        await session.execute(
            insert(SrsCardModel).values(
                user_id=user.id,
                term_id=4001,
                language="en",
                due_at=now,
                fsrs_state={"state": 2},
                stability=24.0,
                difficulty=3.0,
                reps=5,
                lapses=0,
            )
        )
        await session.commit()

    add_response = await client.post("/api/v1/collections/4100/terms", json={"term_id": 4001})
    assert add_response.status_code == 201
    assert add_response.json() == {"added": 1, "skipped": 0}

    duplicate_response = await client.post(
        "/api/v1/collections/4100/terms", json={"term_id": 4001}
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "term_already_in_collection"

    bulk_response = await client.post(
        "/api/v1/collections/4100/terms",
        json={"term_ids": [4001, 4002, 4002]},
    )
    assert bulk_response.status_code == 201
    assert bulk_response.json() == {"added": 1, "skipped": 2}

    list_response = await client.get("/api/v1/collections/4100/terms?page=1&page_size=1")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 2
    assert payload["has_next"] is True
    assert payload["items"][0]["mastery_status"] in {"mastered", "new", "learning"}

    remove_response = await client.delete("/api/v1/collections/4100/terms/4001")
    assert remove_response.status_code == 204

    async with session_factory() as session:
        association_count = await session.scalar(
            select(func.count(CollectionTermModel.id)).where(CollectionTermModel.term_id == 4001)
        )
        term_count = await session.scalar(
            select(func.count(VocabularyTermModel.id)).where(VocabularyTermModel.id == 4001)
        )
        srs_card_count = await session.scalar(
            select(func.count(SrsCardModel.id)).where(SrsCardModel.term_id == 4001)
        )

    assert association_count == 0
    assert term_count == 1
    assert srs_card_count == 1


async def test_collections_api_reports_mastery_statuses_in_term_list(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {"id": 5001, "term": "fresh", "language": "en", "created_at": now},
                {"id": 5002, "term": "active", "language": "en", "created_at": now},
                {"id": 5003, "term": "mastered", "language": "en", "created_at": now},
            ],
        )
        session.add(CollectionModel(id=5000, user_id=user.id or 0, name="Statuses", icon="📚"))
        await session.commit()
        await session.execute(
            insert(CollectionTermModel),
            [
                {"collection_id": 5000, "term_id": 5001},
                {"collection_id": 5000, "term_id": 5002},
                {"collection_id": 5000, "term_id": 5003},
            ],
        )
        await session.execute(
            insert(SrsCardModel),
            [
                {
                    "user_id": user.id,
                    "term_id": 5002,
                    "language": "en",
                    "due_at": now,
                    "fsrs_state": {"state": 1},
                    "stability": 12.0,
                    "difficulty": 4.0,
                    "reps": 2,
                    "lapses": 0,
                },
                {
                    "user_id": user.id,
                    "term_id": 5003,
                    "language": "en",
                    "due_at": now,
                    "fsrs_state": {"state": 2},
                    "stability": 25.0,
                    "difficulty": 2.0,
                    "reps": 6,
                    "lapses": 0,
                },
            ],
        )
        await session.commit()

    response = await client.get("/api/v1/collections/5000/terms")
    assert response.status_code == 200

    statuses = {item["term"]: item["mastery_status"] for item in response.json()["items"]}
    assert statuses == {
        "fresh": "new",
        "active": "learning",
        "mastered": "mastered",
    }


async def test_collections_api_imports_csv_terms_into_collection(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {"id": 6001, "term": "protocol", "language": "en", "created_at": now},
                {"id": 6002, "term": "deploy", "language": "en", "created_at": now},
            ],
        )
        session.add(CollectionModel(id=6000, user_id=user.id or 0, name="CSV", icon="📥"))
        await session.commit()

    files = {
        "file": (
            "terms.csv",
            b"term,language\nprotocol,en\ndeploy,en\nprotocol,en\nmissing,en\n",
            "text/csv",
        )
    }
    response = await client.post("/api/v1/collections/6000/import", files=files)

    assert response.status_code == 200
    assert response.json() == {
        "added": 2,
        "skipped": 1,
        "errors": [{"row": 4, "error": 'Term "missing" was not found in the corpus'}],
    }


async def test_collections_api_blocks_other_users_from_modifying_collection(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, owner = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        intruder_model = UserModel(
            clerk_id="collections_intruder",
            email="intruder@example.com",
            display_name="Intruder",
        )
        session.add(intruder_model)
        session.add(CollectionModel(id=7000, user_id=owner.id or 0, name="Private", icon="🔒"))
        await session.execute(
            insert(VocabularyTermModel).values(
                id=7001,
                term="secret",
                language="en",
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()
        await session.refresh(intruder_model)

    intruder = User(
        id=intruder_model.id,
        clerk_id=intruder_model.clerk_id,
        email=intruder_model.email,
        display_name=intruder_model.display_name,
        tier=UserTier.FREE,
    )

    async def override_intruder() -> User:
        return intruder

    app.dependency_overrides[get_current_user] = override_intruder

    try:
        response = await client.post("/api/v1/collections/7000/terms", json={"term_id": 7001})
    finally:
        app.dependency_overrides[get_current_user] = lambda: owner

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "collection_not_found"


async def test_collections_api_searches_terms_by_name(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {"id": 8001, "term": "protocol", "language": "en", "created_at": now},
                {"id": 8002, "term": "deploy", "language": "en", "created_at": now},
                {"id": 8003, "term": "prototype", "language": "en", "created_at": now},
                {"id": 8004, "term": "iteration", "language": "en", "created_at": now},
            ],
        )
        session.add(CollectionModel(id=8000, user_id=user.id or 0, name="Search", icon="🔍"))
        await session.commit()
        await session.execute(
            insert(CollectionTermModel),
            [
                {"collection_id": 8000, "term_id": 8001},
                {"collection_id": 8000, "term_id": 8002},
                {"collection_id": 8000, "term_id": 8003},
                {"collection_id": 8000, "term_id": 8004},
            ],
        )
        await session.commit()

    response = await client.get("/api/v1/collections/8000/terms?search=proto")
    assert response.status_code == 200
    items = response.json()["items"]
    terms = [item["term"] for item in items]
    assert "protocol" in terms
    assert "prototype" in terms
    assert "deploy" not in terms
    assert "iteration" not in terms


async def test_collections_api_searches_terms_returns_empty_when_no_match(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel).values(
                id=8101,
                term="protocol",
                language="en",
                created_at=now,
            ),
        )
        session.add(CollectionModel(id=8100, user_id=user.id or 0, name="SearchEmpty", icon="📭"))
        await session.commit()
        await session.execute(
            insert(CollectionTermModel).values(collection_id=8100, term_id=8101),
        )
        await session.commit()

    response = await client.get("/api/v1/collections/8100/terms?search=xyznonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_collections_api_filters_terms_by_mastery_status(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {"id": 9001, "term": "fresh", "language": "en", "created_at": now},
                {"id": 9002, "term": "active", "language": "en", "created_at": now},
                {"id": 9003, "term": "mastered", "language": "en", "created_at": now},
            ],
        )
        session.add(
            CollectionModel(id=9000, user_id=user.id or 0, name="MasteryFilter", icon="🎯")
        )
        await session.commit()
        await session.execute(
            insert(CollectionTermModel),
            [
                {"collection_id": 9000, "term_id": 9001},
                {"collection_id": 9000, "term_id": 9002},
                {"collection_id": 9000, "term_id": 9003},
            ],
        )
        await session.execute(
            insert(SrsCardModel),
            [
                {
                    "user_id": user.id,
                    "term_id": 9002,
                    "language": "en",
                    "due_at": now,
                    "fsrs_state": {"state": 1},
                    "stability": 12.0,
                    "difficulty": 4.0,
                    "reps": 2,
                    "lapses": 0,
                },
                {
                    "user_id": user.id,
                    "term_id": 9003,
                    "language": "en",
                    "due_at": now,
                    "fsrs_state": {"state": 2},
                    "stability": 25.0,
                    "difficulty": 2.0,
                    "reps": 6,
                    "lapses": 0,
                },
            ],
        )
        await session.commit()

    mastered_response = await client.get("/api/v1/collections/9000/terms?mastery_status=mastered")
    assert mastered_response.status_code == 200
    mastered_items = mastered_response.json()["items"]
    assert len(mastered_items) == 1
    assert mastered_items[0]["term"] == "mastered"

    learning_response = await client.get("/api/v1/collections/9000/terms?mastery_status=learning")
    assert learning_response.status_code == 200
    learning_items = learning_response.json()["items"]
    assert len(learning_items) == 1
    assert learning_items[0]["term"] == "active"

    new_response = await client.get("/api/v1/collections/9000/terms?mastery_status=new")
    assert new_response.status_code == 200
    new_items = new_response.json()["items"]
    assert len(new_items) == 1
    assert new_items[0]["term"] == "fresh"


async def test_collections_api_combines_search_and_pagination(
    collections_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = collections_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    terms_data = [
        {"id": 9501 + i, "term": f"proto_{chr(97 + i)}", "language": "en", "created_at": now}
        for i in range(5)
    ]

    async with session_factory() as session:
        await session.execute(insert(VocabularyTermModel), terms_data)
        session.add(
            CollectionModel(id=9500, user_id=user.id or 0, name="SearchPaginate", icon="📄")
        )
        await session.commit()
        await session.execute(
            insert(CollectionTermModel),
            [{"collection_id": 9500, "term_id": 9501 + i} for i in range(5)],
        )
        await session.commit()

    response = await client.get("/api/v1/collections/9500/terms?search=proto&page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["has_next"] is True
