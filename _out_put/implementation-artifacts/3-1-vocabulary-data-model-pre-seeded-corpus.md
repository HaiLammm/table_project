# Story 3.1: Vocabulary Data Model & Pre-seeded Corpus

Status: review

## Story

As a **user**,
I want a pre-seeded vocabulary corpus of 3,000–5,000 IT/TOEIC/JLPT terms available from day one,
so that I can start learning immediately without building my own deck.

## Acceptance Criteria

1. **Given** the system is initialized **When** the seed script runs **Then** `vocabulary_terms` and `vocabulary_definitions` tables are created via Alembic migration
2. `vocabulary_terms` stores: `id`, `term`, `language` (en/jp), `parent_id` (adjacency list), `cefr_level`, `jlpt_level`, `part_of_speech`, `created_at`, `updated_at`
3. `vocabulary_definitions` stores: `id`, `term_id`, `language`, `definition`, `ipa`, `examples` (JSONB), `source` (seed/user/llm), `validated_against_jmdict` (boolean), `created_at`
4. A `tsvector` index exists on `vocabulary_terms` for full-text search
5. 3,000–5,000 terms are seeded via LLM batch job with JMdict cross-validation for all Japanese definitions
6. Seeded terms cover IT, TOEIC, JLPT N3–N2 categories with hierarchical `parent_id` relationships
7. The JMdict dataset (~170K entries) is loaded via `jamdict` and available as LRU-cached in-process lookups

## Tasks / Subtasks

- [x] Task 1: Alembic migration for `vocabulary_terms` table (AC: #1, #2, #4)
  - [x] Create migration file with all columns, constraints, indexes
  - [x] Add `tsvector` GIN index for full-text search on `term` column
  - [x] Add index on `parent_id` for hierarchy queries (`ix_vocabulary_terms_parent_id`)
  - [x] Add index on `language` (`ix_vocabulary_terms_language`)
  - [x] Add composite unique constraint on `(term, language)` to prevent duplicates
- [x] Task 2: Alembic migration for `vocabulary_definitions` table (AC: #1, #3)
  - [x] Create migration with FK to `vocabulary_terms.id` (CASCADE delete)
  - [x] Add index on `term_id` (`ix_vocabulary_definitions_term_id`)
  - [x] `source` column: string enum `seed`/`user`/`llm` with CHECK constraint
- [x] Task 3: SQLAlchemy ORM models (AC: #2, #3)
  - [x] `VocabularyTermModel` in `backend/src/app/modules/vocabulary/infrastructure/models.py`
  - [x] `VocabularyDefinitionModel` in same file
  - [x] Use `TimestampMixin` from `src.app.db.base` for `created_at`/`updated_at`
- [x] Task 4: Domain entities and interfaces (AC: #2, #3)
  - [x] `VocabularyTerm` entity in `backend/src/app/modules/vocabulary/domain/entities.py`
  - [x] `VocabularyDefinition` entity in same file
  - [x] `VocabularyRepository` interface in `backend/src/app/modules/vocabulary/domain/interfaces.py`
- [x] Task 5: Repository implementation (AC: #2, #3)
  - [x] `VocabularyRepositoryImpl` in `backend/src/app/modules/vocabulary/infrastructure/repository.py`
  - [x] Methods: `create_term`, `create_definition`, `get_term_by_id`, `search_terms` (tsvector), `get_children` (parent_id), `bulk_create_terms`
- [x] Task 6: JMdict dictionary module (AC: #7)
  - [x] Create `backend/src/app/modules/dictionary/` module structure (domain/application/infrastructure/api)
  - [x] Install `jamdict` + `jamdict-data` as dependencies
  - [x] Implement `JMdictService` with LRU-cached lookups in `backend/src/app/modules/dictionary/application/services.py`
  - [x] Unit test: verify LRU cache works, verify lookup returns correct entries
- [x] Task 7: Seed script (AC: #5, #6)
  - [x] Create `backend/scripts/seed_corpus.py`
  - [x] Define category hierarchy: IT (Networking, Security, Database, DevOps...), TOEIC (Business, Finance...), JLPT N3-N2
  - [x] Generate terms via LLM batch (Claude Haiku or similar) with structured Pydantic output
  - [x] Cross-validate ALL Japanese definitions against JMdict via `JMdictService`
  - [x] Set `validated_against_jmdict=true/false` on each definition
  - [x] Bulk insert via `VocabularyRepository.bulk_create_terms`
  - [x] Idempotent: skip existing terms on re-run
- [x] Task 8: Unit + integration tests
  - [x] Unit tests for domain entities (no DB)
  - [x] Integration tests for repository (async Postgres)
  - [x] Integration test for seed script (small subset)
  - [x] Test tsvector search returns correct results
  - [x] Test hierarchy queries via parent_id

## Dev Notes

### Existing Codebase Patterns (MUST FOLLOW)

**ORM Model Pattern** — see `backend/src/app/modules/auth/infrastructure/models.py`:
- Extend `Base` from `src.app.db.base`
- Use `TimestampMixin` for `created_at`/`updated_at`
- Use `Mapped[]` + `mapped_column()` (SQLAlchemy 2.0 style)
- Define `__table_args__` for indexes
- FK pattern: `ForeignKey("table.id", ondelete="CASCADE")`

**Migration Pattern** — see `backend/alembic/versions/5c2e3a4f9b11_add_srs_cards_table.py`:
- Use `op.create_table()` with explicit `sa.Column()` definitions
- Use `sa.text()` for server_default
- JSONB: `postgresql.JSONB(astext_type=sa.Text())`
- Create indexes separately via `op.create_index()`
- Include `downgrade()` with `drop_index` + `drop_table`

**Module Structure** — every module follows hexagonal pattern:
```
modules/vocabulary/
├── domain/
│   ├── entities.py       # Pure Python, no framework imports
│   ├── value_objects.py
│   ├── exceptions.py
│   └── interfaces.py     # Abstract repository
├── application/
│   └── services.py       # Use cases
├── infrastructure/
│   ├── models.py         # SQLAlchemy models
│   └── repository.py     # Repo implementation
└── api/
    ├── router.py
    ├── schemas.py         # Pydantic request/response
    └── dependencies.py
```

**Existing `__init__.py` files** are already created for vocabulary module subdirs — they are empty placeholders.

**Database session** — use `get_async_session` from `src.app.db.session` via FastAPI `Depends()`.

**SRS `term_id` FK note** — `srs_cards.term_id` is currently `Integer, nullable=True` with NO FK constraint to any vocabulary table. Story 4.x will add this FK once vocabulary tables exist. Do NOT add the FK from srs_cards in this story — that's a separate migration.

### Database Schema Details

**`vocabulary_terms` table:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, autoincrement |
| term | String(500) | NOT NULL |
| language | String(5) | NOT NULL, CHECK (language IN ('en', 'jp')) |
| parent_id | Integer | FK → vocabulary_terms.id (self-referential), nullable |
| cefr_level | String(5) | nullable (A1-C2) |
| jlpt_level | String(5) | nullable (N5-N1) |
| part_of_speech | String(30) | nullable |
| created_at | DateTime(tz) | server_default=now() |
| updated_at | DateTime(tz) | server_default=now(), onupdate=now() |

Indexes:
- `ix_vocabulary_terms_parent_id` on `parent_id`
- `ix_vocabulary_terms_language` on `language`
- `ix_vocabulary_terms_search` — GIN index on `to_tsvector('simple', term)`
- `uq_vocabulary_terms_term_language` — UNIQUE on `(term, language)`

**`vocabulary_definitions` table:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, autoincrement |
| term_id | Integer | FK → vocabulary_terms.id CASCADE, NOT NULL |
| language | String(5) | NOT NULL |
| definition | Text | NOT NULL |
| ipa | String(255) | nullable |
| examples | JSONB | server_default='[]'::jsonb |
| source | String(10) | NOT NULL, CHECK (source IN ('seed', 'user', 'llm')) |
| validated_against_jmdict | Boolean | NOT NULL, default=false |
| created_at | DateTime(tz) | server_default=now() |

Indexes:
- `ix_vocabulary_definitions_term_id` on `term_id`

### Naming Conventions (from architecture)

- Tables: snake_case, plural (`vocabulary_terms`, `vocabulary_definitions`)
- Columns: snake_case
- FK: `{referenced_table_singular}_id` → `term_id`, `parent_id`
- Indexes: `ix_{table}_{column(s)}`
- Unique: `uq_{table}_{column(s)}`

### tsvector Implementation

Use PostgreSQL `'simple'` text search config (not language-specific) since terms span EN/JP. The GIN index:

```sql
CREATE INDEX ix_vocabulary_terms_search
ON vocabulary_terms
USING GIN (to_tsvector('simple', term));
```

In SQLAlchemy migration, use `op.execute()` for the GIN index since it requires raw SQL.

### JMdict / jamdict Setup

- Install: `uv add jamdict jamdict-data`
- Usage: `from jamdict import Jamdict; jam = Jamdict(); result = jam.lookup("protocol")`
- LRU cache: `@functools.lru_cache(maxsize=10000)` on the lookup method
- ~170K entries loaded on first call, cached in-process for process lifetime
- The dictionary module is **read-only** — no DB tables needed, just in-process lookups

### Seed Script Architecture

`backend/scripts/seed_corpus.py` should:
1. Define category hierarchy as Python dict (IT subcategories, TOEIC topics, JLPT levels)
2. For each category, generate terms via LLM (batch mode preferred for cost)
3. Validate JP definitions against JMdict
4. Use async SQLAlchemy session for bulk insert
5. Be runnable standalone: `python -m scripts.seed_corpus`
6. Log progress: categories processed, terms created, JMdict validation stats
7. Be idempotent: `ON CONFLICT (term, language) DO NOTHING`

**LLM output schema** (Pydantic):
```python
class SeedTerm(BaseModel):
    term: str
    language: Literal["en", "jp"]
    cefr_level: str | None
    jlpt_level: str | None
    part_of_speech: str
    definitions: list[SeedDefinition]

class SeedDefinition(BaseModel):
    language: str
    definition: str
    ipa: str | None
    examples: list[str]
```

### Dependencies to Add

```bash
uv add jamdict jamdict-data
```

No other new dependencies required — SQLAlchemy, asyncpg, Pydantic already in pyproject.toml.

### Testing Standards

- Unit tests in `backend/tests/unit/modules/vocabulary/` — domain entities, value objects
- Integration tests in `backend/tests/integration/modules/vocabulary/` — repository with real Postgres
- Use `pytest-asyncio` with `asyncio_mode = "auto"`
- Use `httpx.AsyncClient` for any API endpoint tests (not needed this story — no API routes yet)
- Test fixtures: create async session factory pointing to test DB

### What This Story Does NOT Include

- No API endpoints (Story 3.2 adds browse/search endpoints)
- No frontend components
- No FK from `srs_cards.term_id` → `vocabulary_terms.id` (future story)
- No enrichment pipeline (Story 3.7)
- No CSV import (Story 3.6)

### Project Structure Notes

- Vocabulary module skeleton already exists at `backend/src/app/modules/vocabulary/` with empty `__init__.py` files
- Dictionary module needs to be created at `backend/src/app/modules/dictionary/`
- Seed script goes in `backend/scripts/` (create dir if needed)
- Alembic migrations in `backend/alembic/versions/`
- Latest migration head: `5c2e3a4f9b11` (srs_cards table)

### References

- [Source: _out_put/planning-artifacts/epics/epic-3-vocabulary-management-enrichment-pipeline.md#Story 3.1]
- [Source: _out_put/planning-artifacts/architecture.md#Data Architecture]
- [Source: _out_put/planning-artifacts/architecture.md#Naming Patterns]
- [Source: _out_put/planning-artifacts/architecture.md#Structure Patterns]
- [Source: backend/src/app/modules/auth/infrastructure/models.py — ORM model pattern]
- [Source: backend/src/app/modules/srs/infrastructure/models.py — SRS card model with JSONB]
- [Source: backend/alembic/versions/5c2e3a4f9b11_add_srs_cards_table.py — migration pattern]
- [Source: backend/src/app/db/base.py — Base + TimestampMixin]

## Dev Agent Record

### Agent Model Used

openai/gpt-5.4

### Debug Log References

- `uv add jamdict jamdict-data`
- `uv run pytest tests/unit/modules/vocabulary/test_entities.py tests/unit/modules/dictionary/application/test_services.py tests/integration/modules/vocabulary/test_repository.py tests/integration/modules/vocabulary/test_seed_corpus.py`
- `uv run ruff check src tests scripts`
- `uv run mypy`
- `uv run pytest`
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/table_project_migration_check uv run alembic upgrade head`

### Completion Notes List

- Added Alembic migration `9f2d4b7c6a11_add_vocabulary_tables.py` with the two vocabulary tables, FK constraints, GIN search index, and downgrade coverage.
- Implemented vocabulary domain entities, ORM models, and `VocabularyRepositoryImpl` with create, lookup, search, hierarchy, and idempotent bulk insert behavior.
- Added `JMdictService` with per-instance LRU-cached lookups and definition validation helpers, plus seeded `jamdict` dependencies in `backend/pyproject.toml` and `backend/uv.lock`.
- Created `backend/scripts/seed_corpus.py` with hierarchical category seeding, Anthropic batch generation contract, JMdict cross-validation for Japanese terms, and rerun-safe duplicate skipping.
- Added unit and integration coverage for entities, JMdict caching, repository search/hierarchy behavior, and a seed-script subset path.
- Validation passed: `uv run pytest` (37 passed), `uv run ruff check src tests scripts`, `uv run mypy`, and Alembic upgrade on `table_project_migration_check` with expected vocabulary indexes present.

### File List

- `_out_put/implementation-artifacts/3-1-vocabulary-data-model-pre-seeded-corpus.md`
- `_out_put/implementation-artifacts/sprint-status.yaml`
- `backend/alembic/versions/9f2d4b7c6a11_add_vocabulary_tables.py`
- `backend/pyproject.toml`
- `backend/scripts/__init__.py`
- `backend/scripts/seed_corpus.py`
- `backend/src/app/modules/dictionary/application/services.py`
- `backend/src/app/modules/vocabulary/domain/entities.py`
- `backend/src/app/modules/vocabulary/domain/interfaces.py`
- `backend/src/app/modules/vocabulary/infrastructure/models.py`
- `backend/src/app/modules/vocabulary/infrastructure/repository.py`
- `backend/tests/integration/__init__.py`
- `backend/tests/integration/modules/__init__.py`
- `backend/tests/integration/modules/auth/__init__.py`
- `backend/tests/integration/modules/vocabulary/__init__.py`
- `backend/tests/integration/modules/vocabulary/test_repository.py`
- `backend/tests/integration/modules/vocabulary/test_seed_corpus.py`
- `backend/tests/unit/__init__.py`
- `backend/tests/unit/modules/__init__.py`
- `backend/tests/unit/modules/auth/__init__.py`
- `backend/tests/unit/modules/auth/application/__init__.py`
- `backend/tests/unit/modules/auth/domain/__init__.py`
- `backend/tests/unit/modules/dictionary/__init__.py`
- `backend/tests/unit/modules/dictionary/application/__init__.py`
- `backend/tests/unit/modules/dictionary/application/test_services.py`
- `backend/tests/unit/modules/srs/__init__.py`
- `backend/tests/unit/modules/srs/application/__init__.py`
- `backend/tests/unit/modules/vocabulary/__init__.py`
- `backend/tests/unit/modules/vocabulary/test_entities.py`
- `backend/uv.lock`

## Change Log

- 2026-05-06: Implemented Story 3.1 vocabulary schema, repository, JMdict service, seed script, and automated validation coverage; story is ready for review.
