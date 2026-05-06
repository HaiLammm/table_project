# Story 2.2: Onboarding Survey & AI Learning Plan

Status: ready-for-dev

## Story

As a **new user**,
I want to complete a 5-question onboarding survey and receive a personalized AI-generated learning plan,
so that my vocabulary study is tailored to my goals, level, and domain from the first session.

## Acceptance Criteria

1. **Given** a new user completes registration **When** they land on the onboarding page **Then** a 5-step survey is presented one question per screen with progress dots:
   - Q1: Primary learning goal (JLPT prep / TOEIC prep / workplace communication / general)
   - Q2: Current English level (beginner / intermediate / advanced)
   - Q3: Current Japanese level (N5 / N4 / N3 / N2 / N1 / none)
   - Q4: Daily study time preference (5 min / 15 min / 30 min / 60 min) — skippable, default 15 min
   - Q5: IT domain (web dev / backend / networking / data / general IT) — skippable, default general IT
   **And** selected options fill black (`#18181B`) for visual feedback
   **And** back button is available on Q2–Q5
   **And** skipped questions use sensible defaults

2. **Given** the user completes the survey **When** the system generates a learning plan **Then** a personalized plan summary is displayed (recommended collections, daily card target, study schedule) **And** the user can accept or modify the plan **And** upon acceptance, an initial collection is seeded from the pre-seeded corpus matching the plan **And** a mini-session of 5 easy cards starts immediately **And** the entire onboarding flow completes in under 3 minutes

3. **Given** a user closes the app mid-onboarding **When** they return **Then** the survey resumes from the last answered question

## Tasks / Subtasks

- [ ] Task 1: Backend — Onboarding domain & data model (AC: #1, #3)
  - [ ] Add `onboarding_completed` (bool, default false) and `onboarding_step` (int, default 0) columns to `users` table
  - [ ] Add `user_preferences` table: id (PK), user_id (FK → users.id, unique), learning_goal, english_level, japanese_level, daily_study_minutes (default 15), it_domain (default 'general_it'), created_at, updated_at
  - [ ] Create Alembic migration for above schema changes
  - [ ] Add `OnboardingPreferences` domain entity and value objects (LearningGoal, EnglishLevel, JapaneseLevel, ITDomain enums)
  - [ ] Add `UserPreferencesRepository` interface and SQLAlchemy implementation

- [ ] Task 2: Backend — Onboarding API endpoints (AC: #1, #2, #3)
  - [ ] `GET /api/v1/onboarding/status` — returns current step and whether completed (protected)
  - [ ] `POST /api/v1/onboarding/answers` — saves survey answers incrementally (step-by-step, for resume support)
  - [ ] `POST /api/v1/onboarding/complete` — marks onboarding complete, triggers learning plan generation
  - [ ] `GET /api/v1/onboarding/plan` — returns generated learning plan
  - [ ] `POST /api/v1/onboarding/plan/accept` — accepts plan, seeds initial collection
  - [ ] Request/response Pydantic schemas: `OnboardingStatusResponse`, `SurveyAnswerRequest`, `LearningPlanResponse`, etc.

- [ ] Task 3: Backend — AI Learning Plan generation service (AC: #2)
  - [ ] `modules/onboarding/application/services.py` — `LearningPlanService`
  - [ ] For MVP: deterministic plan generation based on survey answers (no LLM call yet — map goal+level+domain to predefined plan templates)
  - [ ] Plan output: recommended_collections (list of corpus tags), daily_card_target (int), study_schedule (description), estimated_duration (string)
  - [ ] NOTE: LLM-based plan generation deferred to Epic 3 (LLM gateway). Use simple mapping logic for now.

- [ ] Task 4: Frontend — OnboardingStep component (AC: #1)
  - [ ] Create `src/components/onboarding/OnboardingStep.tsx` per UX spec:
    - Props: `stepNumber`, `totalSteps`, `question`, `options` (icon + label + value), `selectedValue`, `onSelect`, `onContinue`, `onBack?`, `skippable?`
    - Progress dots at top showing 5 steps
    - Selected state: `bg-zinc-900 border-zinc-900 border-2 text-zinc-50 font-medium`
    - Single-question-per-screen, no scrolling
    - No sidebar during onboarding (full focus)
  - [ ] Create `src/components/onboarding/LearningPlanCard.tsx` — displays generated plan summary

- [ ] Task 5: Frontend — Onboarding page & flow (AC: #1, #2, #3)
  - [ ] Create `src/app/onboarding/page.tsx` — full onboarding flow
  - [ ] State machine: 5 survey steps → plan generation → plan display → accept/modify → redirect to first review
  - [ ] Persist answers to backend incrementally (POST /onboarding/answers per step)
  - [ ] On mount, check `GET /onboarding/status` — resume from last step if incomplete
  - [ ] On plan accept, call `POST /onboarding/plan/accept` then redirect to `/(app)/review` (or Today's Queue)
  - [ ] Add `/onboarding` to public routes in `middleware.ts` (authenticated but not inside `(app)` layout)

- [ ] Task 6: Frontend — Redirect logic for new users (AC: #1)
  - [ ] After Clerk sign-up/sign-in, check if `onboarding_completed === false`
  - [ ] If not completed, redirect to `/onboarding`
  - [ ] Options: check via `GET /api/v1/users/me` response (add `onboarding_completed` field to `UserResponse`) or via Clerk metadata
  - [ ] Add redirect logic in middleware or in `(app)/layout.tsx`

- [ ] Task 7: Write tests (AC: #1, #2, #3)
  - [ ] Backend unit: OnboardingPreferences entity, LearningPlanService (deterministic mapping)
  - [ ] Backend integration: UserPreferencesRepository CRUD
  - [ ] Backend e2e: full onboarding flow — create user → save answers → generate plan → accept
  - [ ] Frontend: OnboardingStep component renders correctly, handles selection, back/skip

## Dev Notes

### Technical Stack (This Story)

| Technology | Version | Purpose |
|-----------|---------|---------|
| shadcn/ui Progress | Latest | Progress dots indicator |
| React state (useState/useReducer) | — | Survey step machine |
| Existing api-client.ts | — | Backend API calls with Clerk JWT |
| SQLAlchemy + Alembic | Existing | New tables/columns |

### Architecture Constraints — MUST FOLLOW

- **Hexagonal layers**: domain/ NEVER imports infrastructure/ or api/
- **New module**: Create `modules/onboarding/` with domain/, application/, infrastructure/, api/ subdirectories — do NOT put onboarding logic inside `modules/auth/`
- **Naming**: snake_case Python, PascalCase React components, snake_case DB/API
- **Error format**: `{error: {code, message, details}}` for all API errors
- **Pydantic models**: Required for all API boundaries
- **Dependencies**: Use `Depends()` for all injectables
- **Logging**: structlog — never `print()`
- **Frontend route**: `/onboarding` is OUTSIDE `(app)/` route group — no sidebar, no AppShell

### Current Codebase State (Files Being Modified)

**`backend/src/app/modules/auth/infrastructure/models.py`** — Currently has `UserModel` with id, clerk_id, email, display_name, tier + TimestampMixin. ADD: `onboarding_completed` (Boolean, default False) and `onboarding_step` (Integer, default 0) columns.

**`backend/src/app/modules/auth/api/schemas.py`** — Currently has `UserResponse`, `WebhookPayload`, `WebhookSyncResponse`. ADD: `onboarding_completed` and `onboarding_step` fields to `UserResponse`.

**`backend/src/app/modules/auth/domain/entities.py`** — Currently has User dataclass with id, clerk_id, email, display_name, tier, timestamps. ADD: `onboarding_completed: bool = False` and `onboarding_step: int = 0` fields.

**`frontend/src/middleware.ts`** — Currently protects all non-public routes. ADD: `/onboarding(.*)` to public route matcher (or handle as authenticated-but-not-app route).

**`backend/src/app/main.py`** — Currently mounts auth_router. ADD: onboarding_router mount.

### New Module Structure (Create)

```
modules/onboarding/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py          # OnboardingPreferences dataclass
│   ├── value_objects.py     # LearningGoal, EnglishLevel, JapaneseLevel, ITDomain enums
│   └── interfaces.py        # AbstractUserPreferencesRepository
├── application/
│   ├── __init__.py
│   └── services.py          # LearningPlanService (deterministic MVP)
├── infrastructure/
│   ├── __init__.py
│   ├── models.py            # UserPreferencesModel (SQLAlchemy)
│   └── repository.py        # SqlAlchemyUserPreferencesRepository
└── api/
    ├── __init__.py
    ├── router.py             # /api/v1/onboarding/* endpoints
    ├── schemas.py            # Request/response Pydantic models
    └── dependencies.py       # Onboarding-specific dependencies
```

### Frontend Routes (Create)

```
src/
├── app/
│   └── onboarding/
│       └── page.tsx              # Full onboarding flow page
├── components/
│   └── onboarding/
│       ├── OnboardingStep.tsx    # Single-question survey step
│       ├── LearningPlanCard.tsx  # AI plan display
│       └── index.ts
```

### Database Schema: `user_preferences` Table

```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    learning_goal VARCHAR(50) NOT NULL,        -- 'jlpt_prep', 'toeic_prep', 'workplace', 'general'
    english_level VARCHAR(20) NOT NULL,        -- 'beginner', 'intermediate', 'advanced'
    japanese_level VARCHAR(10) NOT NULL,       -- 'n5', 'n4', 'n3', 'n2', 'n1', 'none'
    daily_study_minutes INTEGER NOT NULL DEFAULT 15,
    it_domain VARCHAR(30) NOT NULL DEFAULT 'general_it',  -- 'web_dev', 'backend', 'networking', 'data', 'general_it'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```sql
-- Add to users table
ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN onboarding_step INTEGER NOT NULL DEFAULT 0;
```

### Onboarding Flow State Machine

```
START → Q1 (learning_goal) → Q2 (english_level) → Q3 (japanese_level)
  → Q4 (daily_study_time, skippable) → Q5 (it_domain, skippable)
  → GENERATING_PLAN → SHOW_PLAN → ACCEPT/MODIFY
  → SEEDING_COLLECTION → MINI_SESSION (5 cards) → COMPLETE → redirect to /(app)
```

**Resume logic**: On page mount, call `GET /onboarding/status`. If `onboarding_step > 0 && !onboarding_completed`, jump to step `onboarding_step + 1`.

### Learning Plan Generation (MVP — Deterministic)

No LLM call in this story. Map survey answers to predefined templates:

```python
# Example mapping logic
PLAN_TEMPLATES = {
    "jlpt_prep": {"collections": ["jlpt_n3", "jlpt_n2"], "focus": "kanji + grammar vocab"},
    "toeic_prep": {"collections": ["toeic_600", "business_en"], "focus": "business English"},
    "workplace": {"collections": ["it_workplace", "meeting_vocab"], "focus": "professional communication"},
    "general": {"collections": ["core_en_jp", "daily_vocab"], "focus": "general bilingual"},
}
# Cross with it_domain to add domain-specific collections
# Cross with level to adjust difficulty
```

**IMPORTANT**: Collections and corpus don't exist yet (Epic 3). The plan should reference collection *tags/names* that will be created in Epic 3. For this story, the `POST /onboarding/plan/accept` endpoint saves preferences and marks onboarding complete — actual collection seeding and mini-session are **stubs** that return success. Add TODO comments for Epic 3 integration.

### Middleware / Redirect Strategy

The `/onboarding` route needs special handling:
- It IS authenticated (user must be logged in via Clerk)
- It is NOT inside `(app)/` layout (no sidebar/AppShell)
- Middleware should NOT redirect `/onboarding` to sign-in (it's after sign-up)

**Approach**: Add `/onboarding` as a separate route outside `(app)/`. In `middleware.ts`, keep it as a protected route (Clerk auth required). In `(app)/layout.tsx` or a client component, check `onboarding_completed` from `/users/me` and redirect to `/onboarding` if false.

### Previous Story Intelligence

**From Story 2.1 (User Registration & Login):**
- User entity at `modules/auth/domain/entities.py` — extend with onboarding fields
- UserModel at `modules/auth/infrastructure/models.py` — add columns
- UserResponse schema needs `onboarding_completed` field
- `api-client.ts` already handles Clerk JWT injection — reuse for onboarding API calls
- `query-client.ts` TanStack Query config exists — use for onboarding data fetching
- Backend uses `uv add` for dependencies, NOT pip
- Frontend uses pnpm
- `get_current_user` dependency already extracts user from JWT — use it in onboarding endpoints
- Story 2.1 remains `in-progress` (manual Clerk config pending) but code is functional

**From Story 1.3 (App Shell):**
- AppShell at `src/components/layout/` — onboarding page must NOT use AppShell
- Route group `(app)/` wraps authenticated app pages in AppShell layout

### Anti-Patterns to AVOID

- Do NOT put onboarding logic inside `modules/auth/` — create separate `modules/onboarding/`
- Do NOT call LLM for plan generation in this story — use deterministic mapping (LLM gateway = Epic 3)
- Do NOT implement actual collection seeding or mini-review-session — those require Epic 3 (vocabulary) and Epic 4 (SRS). Stub them.
- Do NOT show sidebar/AppShell during onboarding — dedicated full-screen layout
- Do NOT use localStorage for survey state persistence — use backend API for resume support
- Do NOT create custom auth middleware — reuse existing `get_current_user` dependency
- Do NOT use `pip install` — use `uv add` for backend dependencies
- Do NOT skip checking Next.js 16 docs in `node_modules/next/dist/docs/` before implementing routes

### References

- [Source: _out_put/planning-artifacts/epics/epic-2-user-authentication-onboarding-profile.md#Story 2.2]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend File Structure - onboarding/]
- [Source: _out_put/planning-artifacts/architecture.md#Backend Module Structure - auth/]
- [Source: _out_put/planning-artifacts/architecture.md#Requirements Coverage - Onboarding]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#First-Time Onboarding Flow]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#OnboardingStep Component]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#LearningPlanCard Component]
- [Source: _out_put/planning-artifacts/product-brief-table_project.md#Time-to-first-review < 3 min]
- [Source: _out_put/implementation-artifacts/2-1-user-registration-login-with-clerk.md]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
