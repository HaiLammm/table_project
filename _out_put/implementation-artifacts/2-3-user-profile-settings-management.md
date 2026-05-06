# Story 2.3: User Profile & Settings Management

Status: review

## Story

As a **registered user**,
I want to view and edit my profile settings including languages, level, goals, daily study budget, and notification preferences,
so that I can keep my learning experience aligned with my evolving needs.

## Acceptance Criteria

1. **Given** a user navigates to Settings **When** the settings page loads **Then** the user sees their Clerk profile (name, email, avatar) via Clerk `<UserProfile />` component **And** app-specific preferences are displayed: languages, current level, learning goal, daily study budget, notification preferences **And** all preferences are editable and saved via API (`PUT /api/v1/users/me/preferences`)

2. **Given** a user updates their daily study budget **When** they save the change **Then** the FSRS daily queue adjusts accordingly on the next queue generation **And** a toast confirms "Settings updated"

## Tasks / Subtasks

- [x] Task 1: Backend — Preferences update endpoint (AC: #1, #2)
  - [x] Add `PUT /api/v1/users/me/preferences` endpoint in `modules/auth/api/router.py` (or `modules/onboarding/api/router.py` if onboarding module exists)
  - [x] Create `UserPreferencesUpdateRequest` Pydantic schema: learning_goal?, english_level?, japanese_level?, daily_study_minutes?, it_domain?, notification_email? (bool), notification_review_reminder? (bool)
  - [x] Create `UserPreferencesResponse` Pydantic schema returning all preference fields
  - [x] Add `GET /api/v1/users/me/preferences` endpoint to fetch current preferences
  - [x] Service layer: `update_preferences()` — validate input, update `user_preferences` table, return updated preferences
  - [x] If `user_preferences` row doesn't exist yet (user skipped onboarding), create it with defaults on first update

- [x] Task 2: Frontend — Settings page layout (AC: #1)
  - [x] Replace placeholder `src/app/(app)/settings/page.tsx` with full settings page
  - [x] Two sections:
    - **Profile** section: embed Clerk `<UserProfile />` component for name/email/avatar/password management
    - **Learning Preferences** section: app-specific settings form
  - [x] Use `Card` (shadcn/ui) for each section grouping
  - [x] Page title: "Settings" in breadcrumb via Topbar

- [x] Task 3: Frontend — Learning Preferences form (AC: #1, #2)
  - [x] Create `src/components/settings/PreferencesForm.tsx`
  - [x] Fields: learning goal (select), English level (select), Japanese level (select), daily study budget (select: 5/15/30/60 min), IT domain (select), notification preferences (toggles)
  - [x] Pre-populate from `GET /api/v1/users/me/preferences` via TanStack Query
  - [x] On save: `PUT /api/v1/users/me/preferences` via TanStack Mutation
  - [x] On success: show toast "Settings updated", invalidate preferences query
  - [x] On error: show toast with error message
  - [x] Use shadcn/ui `Select`, `Switch`, `Button`, `Label` components

- [x] Task 4: Write tests (AC: #1, #2)
  - [x] Backend unit: preferences update service (validate + save)
  - [x] Backend e2e: GET + PUT preferences endpoints
  - [x] Frontend: PreferencesForm renders, submits, shows toast

## Dev Notes

### Technical Stack (This Story)

| Technology | Version | Purpose |
|-----------|---------|---------|
| @clerk/nextjs `<UserProfile />` | Latest | Clerk profile management UI (name, email, avatar, password) |
| shadcn/ui Select, Switch, Label, Button, Card, Toast | Latest | Form components |
| TanStack Query + Mutation | Existing | Data fetching + update |
| Existing api-client.ts | — | Backend API calls with Clerk JWT |

### Architecture Constraints — MUST FOLLOW

- **Hexagonal layers**: domain/ NEVER imports infrastructure/ or api/
- **Naming**: snake_case Python, PascalCase React components, snake_case DB/API
- **Error format**: `{error: {code, message, details}}` for all API errors
- **Pydantic models**: Required for all API boundaries
- **Dependencies**: Use `Depends()` for all injectables
- **Logging**: structlog — never `print()`
- **Settings page IS inside `(app)/` layout** — has sidebar + AppShell (unlike onboarding)

### Current Codebase State (Files Being Modified)

**`frontend/src/app/(app)/settings/page.tsx`** — Currently a placeholder with "Coming soon" text. REPLACE entirely with settings page containing Clerk UserProfile + PreferencesForm.

**`backend/src/app/modules/auth/api/router.py`** — Currently has `GET /users/me` and `POST /auth/webhook`. ADD: `GET /users/me/preferences` and `PUT /users/me/preferences` endpoints. Alternatively, if `modules/onboarding/` exists by the time this story runs, put preference endpoints there since `user_preferences` table belongs to onboarding module.

**`backend/src/app/modules/auth/api/schemas.py`** — ADD `UserPreferencesUpdateRequest` and `UserPreferencesResponse` schemas. Or add to onboarding schemas if module exists.

### Dependency on Story 2.2 (Onboarding)

Story 2.2 creates the `user_preferences` table and the `modules/onboarding/` module. This story READS and UPDATES that same table.

**If onboarding module exists** (`modules/onboarding/`):
- Add preference endpoints to `modules/onboarding/api/router.py`
- Reuse `UserPreferencesRepository` from onboarding infrastructure
- Import enums (LearningGoal, EnglishLevel, JapaneseLevel, ITDomain) from `modules/onboarding/domain/value_objects.py`

**If onboarding module does NOT exist yet** (story 2.2 not implemented):
- Create the `user_preferences` table + migration yourself (see schema in story 2.2 Dev Notes)
- Put preference endpoints in `modules/auth/api/router.py` temporarily
- When onboarding module lands later, refactor to move there

### Database Schema (from Story 2.2)

The `user_preferences` table already defined in story 2.2:
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    learning_goal VARCHAR(50) NOT NULL,
    english_level VARCHAR(20) NOT NULL,
    japanese_level VARCHAR(10) NOT NULL,
    daily_study_minutes INTEGER NOT NULL DEFAULT 15,
    it_domain VARCHAR(30) NOT NULL DEFAULT 'general_it',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**New columns for this story** (add via migration if not in 2.2):
- `notification_email BOOLEAN NOT NULL DEFAULT TRUE`
- `notification_review_reminder BOOLEAN NOT NULL DEFAULT TRUE`

### Clerk UserProfile Integration

Use Clerk's `<UserProfile />` component for profile management (name, email, avatar, connected accounts, password). Do NOT build custom profile editing UI — Clerk handles this.

```tsx
import { UserProfile } from '@clerk/nextjs'

// In settings page:
<UserProfile
  appearance={{
    elements: {
      rootBox: "w-full",
      card: "shadow-none border border-zinc-200 rounded-[10px]",
    }
  }}
/>
```

The `<UserProfile />` component handles its own routing internally. Embed it directly in the settings page — no catch-all route needed when using it inline (not as a dedicated page).

### Frontend Component Structure

```
src/
├── app/(app)/settings/
│   └── page.tsx                    # UPDATE: Settings page with Clerk + PreferencesForm
├── components/settings/
│   ├── PreferencesForm.tsx         # NEW: Learning preferences form
│   └── index.ts                   # NEW: Barrel export
```

### API Endpoints

**`GET /api/v1/users/me/preferences`**
- Auth: requires Clerk JWT
- Response 200: `{ learning_goal, english_level, japanese_level, daily_study_minutes, it_domain, notification_email, notification_review_reminder }`
- Response 404: if no preferences exist yet → return defaults

**`PUT /api/v1/users/me/preferences`**
- Auth: requires Clerk JWT
- Body: partial update — only include fields being changed
- Response 200: full preferences object after update
- Creates `user_preferences` row if not exists (upsert behavior)

### TanStack Query Pattern

```typescript
// In lib/query-keys.ts — add:
export const userKeys = {
  all: ['user'] as const,
  me: () => [...userKeys.all, 'me'] as const,
  preferences: () => [...userKeys.all, 'preferences'] as const,
}

// In PreferencesForm.tsx:
const { data } = useQuery({
  queryKey: userKeys.preferences(),
  queryFn: () => apiClient.get('/users/me/preferences'),
})

const mutation = useMutation({
  mutationFn: (data) => apiClient.put('/users/me/preferences', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: userKeys.preferences() })
    toast.success('Settings updated')
  },
})
```

### Previous Story Intelligence

**From Story 2.1 (Auth):**
- `api-client.ts` handles Clerk JWT injection — reuse for preferences API calls
- `query-client.ts` TanStack Query config exists
- `get_current_user` dependency extracts user from JWT — use in preference endpoints
- Backend uses `uv add` for dependencies, NOT pip
- Frontend uses pnpm

**From Story 2.2 (Onboarding):**
- `user_preferences` table and domain model defined — reuse, don't recreate
- Enums (LearningGoal, EnglishLevel, etc.) defined in onboarding value_objects — import them
- `UserPreferencesRepository` exists — reuse for update operations

**From Story 1.3 (App Shell):**
- Settings page is inside `(app)/` route group — gets sidebar + topbar automatically
- Sidebar already has Settings nav item pointing to `/settings`

### Anti-Patterns to AVOID

- Do NOT build custom profile editing UI for name/email/avatar — use Clerk `<UserProfile />`
- Do NOT create a new module for settings — reuse onboarding module's repository and entities
- Do NOT use localStorage for preference state — server-side via API
- Do NOT skip toast feedback on save — UX spec requires "Settings updated" confirmation
- Do NOT create a separate settings layout — it's inside `(app)/` with AppShell
- Do NOT use `pip install` — use `uv add` for backend dependencies
- Do NOT hardcode preference options — use the same enums from onboarding domain

### References

- [Source: _out_put/planning-artifacts/epics/epic-2-user-authentication-onboarding-profile.md#Story 2.3]
- [Source: _out_put/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _out_put/planning-artifacts/architecture.md#Backend Module Structure - auth/]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend File Structure - settings/]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Feedback Patterns - Toast]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _out_put/implementation-artifacts/2-1-user-registration-login-with-clerk.md]
- [Source: _out_put/implementation-artifacts/2-2-onboarding-survey-ai-learning-plan.md]
- [Clerk UserProfile Component](https://clerk.com/docs/nextjs/reference/components/user/user-profile)
- [Clerk UserProfile Custom Pages](https://clerk.com/docs/nextjs/guides/customizing-clerk/adding-items/user-profile)

## Dev Agent Record

### Agent Model Used

gpt-5.4

### Debug Log References

- `cd backend && uv sync --group dev`
- `cd backend && uv run pytest tests/unit/modules/auth/application/test_preferences_services.py tests/e2e/test_auth_flow.py`
- `cd backend && uv run pytest`
- `cd backend && uv run ruff check`
- `cd frontend && pnpm install --frozen-lockfile`
- `cd frontend && pnpm test -- src/components/settings/PreferencesForm.test.tsx next.config.test.ts`
- `cd frontend && pnpm test`
- `cd frontend && pnpm lint`
- `cd frontend && pnpm build`

### Completion Notes List

- Added `user_preferences` persistence inside the current `auth` module because `modules/onboarding/` is not present yet, including enums, domain entity, repository methods, service validation, API schemas, and GET/PUT `/api/v1/users/me/preferences` endpoints.
- Added Alembic migration `fd8f2d8f4f73_add_user_preferences_table.py` to create `user_preferences` with notification flags and defaults for skipped-onboarding users.
- Replaced the placeholder Settings page with Clerk `UserProfile` plus a new `PreferencesForm` that loads preferences with TanStack Query, saves with mutation, invalidates the preferences query, and shows success/error toasts.
- Added lightweight UI primitives (`Label`, `Select`, `Switch`, `ToastProvider`) and `userKeys.preferences()` to support the new settings workflow without introducing extra packages.
- Added backend unit/e2e coverage and frontend Vitest coverage for rendering, submitting, and toast behavior; full backend pytest, backend ruff, frontend test, frontend lint, and frontend build all passed.

### File List

- `_out_put/implementation-artifacts/2-3-user-profile-settings-management.md`
- `_out_put/implementation-artifacts/sprint-status.yaml`
- `backend/alembic/versions/fd8f2d8f4f73_add_user_preferences_table.py`
- `backend/src/app/modules/auth/api/router.py`
- `backend/src/app/modules/auth/api/schemas.py`
- `backend/src/app/modules/auth/application/services.py`
- `backend/src/app/modules/auth/domain/entities.py`
- `backend/src/app/modules/auth/domain/exceptions.py`
- `backend/src/app/modules/auth/domain/interfaces.py`
- `backend/src/app/modules/auth/domain/value_objects.py`
- `backend/src/app/modules/auth/infrastructure/models.py`
- `backend/src/app/modules/auth/infrastructure/repository.py`
- `backend/tests/e2e/test_auth_flow.py`
- `backend/tests/unit/modules/auth/application/test_preferences_services.py`
- `frontend/src/app/(app)/settings/page.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/components/settings/PreferencesForm.test.tsx`
- `frontend/src/components/settings/PreferencesForm.tsx`
- `frontend/src/components/settings/index.ts`
- `frontend/src/components/ui/label.tsx`
- `frontend/src/components/ui/select.tsx`
- `frontend/src/components/ui/switch.tsx`
- `frontend/src/components/ui/toast.tsx`
- `frontend/src/lib/query-keys.ts`
- `frontend/vitest.config.ts`

### Change Log

- 2026-05-06: Implemented Story 2.3 settings management across backend API, persistence, frontend settings UI, toast feedback, and automated tests; story is ready for review.
