# Story 2.4: Data Export & Account Deletion (GDPR/APPI/PDPD)

Status: review

## Story

As a registered user,
I want to export all my personal data or permanently delete my account and all associated data,
So that I can exercise my data privacy rights as required by GDPR, APPI, and PDPD.

## Acceptance Criteria

1. **Data Export Request**
   - Given a user navigates to Settings → Data & Privacy
   - When they request a data export
   - Then the system generates a downloadable archive containing: user profile, all vocabulary terms, review history, learning patterns, collections, and diagnostic data
   - And the export is available within 24 hours (background job)
   - And the user receives notification when export is ready

2. **Account Deletion**
   - Given a user requests account deletion
   - When they confirm via a destructive action dialog (type account email to confirm)
   - Then all user data is permanently deleted: user record, vocabulary, SRS cards, reviews, collections, enrichment jobs, diagnostic data
   - And the Clerk account is deleted
   - And the deletion is irreversible
   - And the user is logged out and redirected to the landing page

## Tasks / Subtasks

### Backend

- [x] Task 1: Data Export Service (AC: #1)
  - [x] 1.1 Add `DataExportService` in `modules/auth/application/services.py` — collects all user data across tables (users, user_preferences, and future: vocabulary_terms, srs_cards, srs_reviews, collections, enrichment_jobs, diagnostics)
  - [x] 1.2 Create `POST /api/v1/users/me/data-export` endpoint in `modules/auth/api/router.py` — triggers background export job via ARQ
  - [x] 1.3 Create `GET /api/v1/users/me/data-export/{export_id}` endpoint — returns export status and download URL when ready
  - [x] 1.4 Add ARQ worker task `process_data_export` in `workers/export_worker.py` — queries all user-owned data, serializes to JSON, generates ZIP archive
  - [x] 1.5 Store export archive temporarily (local filesystem or object storage, configurable) with 7-day TTL
  - [x] 1.6 Add `data_exports` table via Alembic migration: id, user_id (FK), status (pending/processing/ready/expired/failed), file_path, created_at, expires_at
  - [x] 1.7 Add Pydantic schemas: `DataExportResponse`, `DataExportStatusResponse` in `modules/auth/api/schemas.py`

- [x] Task 2: Account Deletion Service (AC: #2)
  - [x] 2.1 Add `AccountDeletionService` in `modules/auth/application/services.py` — orchestrates cascade deletion across all modules
  - [x] 2.2 Create `DELETE /api/v1/users/me` endpoint in `modules/auth/api/router.py` — requires email confirmation in request body
  - [x] 2.3 Implement cascade deletion: delete in order — data_exports → user_preferences → (future tables: srs_reviews, srs_cards, vocabulary_terms, collections, enrichment_jobs, diagnostics) → users
  - [x] 2.4 Call Clerk API to delete user account: `DELETE https://api.clerk.com/v1/users/{clerk_user_id}` using Clerk Backend API secret key
  - [x] 2.5 Add `AccountDeletionRequest` schema with `confirmation_email` field
  - [x] 2.6 Log deletion event (structlog, no PII in logs — only user_id)

- [x] Task 3: Backend Tests (AC: #1, #2)
  - [x] 3.1 Unit tests for `DataExportService` and `AccountDeletionService`
  - [x] 3.2 Integration tests for export and deletion endpoints
  - [x] 3.3 Test cascade deletion completeness
  - [x] 3.4 Test email confirmation validation (mismatch → 400)
  - [x] 3.5 Test Clerk API deletion (mocked httpx)

### Frontend

- [x] Task 4: Data & Privacy Settings Section (AC: #1, #2)
  - [x] 4.1 Add "Data & Privacy" `Card` section to `settings/page.tsx` below existing cards
  - [x] 4.2 Create `DataExportButton.tsx` in `components/settings/` — triggers export, shows toast "Export requested. You'll be notified when ready."
  - [x] 4.3 Create `DeleteAccountDialog.tsx` in `components/settings/` — destructive action dialog with email confirmation input. User must type their email to enable the delete button
  - [x] 4.4 Add TanStack Query mutation for `POST /api/v1/users/me/data-export`
  - [x] 4.5 Add TanStack Query mutation for `DELETE /api/v1/users/me` — on success, call `clerk.signOut()` and redirect to `/`
  - [x] 4.6 Add query keys: `userKeys.dataExport()`, `userKeys.dataExportStatus(id)`
  - [x] 4.7 Frontend Vitest tests for DataExportButton and DeleteAccountDialog

## Dev Notes

### Architecture Compliance

- **Hexagonal layers**: domain → application → infrastructure → api. Domain NEVER imports infrastructure.
- **Module**: All new code goes in `modules/auth/` — data privacy is a user account concern, not a separate module.
- **Dependency injection**: Use `Depends()` for all services. Follow existing pattern in `router.py` (see `get_user_preferences_service`).
- **Pydantic schemas**: All API boundaries use Pydantic v2 models. No raw dicts.
- **Error format**: `{"error": {"code": "...", "message": "...", "details": null}}`
- **Logging**: structlog only. Never `print()`. Never log PII (email, vocabulary content). Log: `user_id`, `request_id`, event name.

### Existing Code to Extend (UPDATE files)

| File | What to Add |
|------|-------------|
| `backend/src/app/modules/auth/api/router.py` | 3 new endpoints: POST data-export, GET data-export status, DELETE users/me |
| `backend/src/app/modules/auth/api/schemas.py` | DataExportResponse, DataExportStatusResponse, AccountDeletionRequest |
| `backend/src/app/modules/auth/application/services.py` | DataExportService, AccountDeletionService classes |
| `backend/src/app/modules/auth/domain/entities.py` | DataExport dataclass |
| `backend/src/app/modules/auth/domain/interfaces.py` | DataExportRepository interface |
| `backend/src/app/modules/auth/domain/exceptions.py` | DataExportNotFoundError, AccountDeletionError |
| `backend/src/app/modules/auth/infrastructure/models.py` | DataExportModel |
| `backend/src/app/modules/auth/infrastructure/repository.py` | DataExport repo methods in SqlAlchemyUserRepository |
| `frontend/src/app/(app)/settings/page.tsx` | Add Data & Privacy card section |
| `frontend/src/lib/query-keys.ts` | Add dataExport keys |

### New Files

| File | Purpose |
|------|---------|
| `backend/src/app/workers/export_worker.py` | ARQ background task for data export |
| `backend/alembic/versions/xxx_add_data_exports_table.py` | Migration |
| `frontend/src/components/settings/DataExportButton.tsx` | Export trigger button |
| `frontend/src/components/settings/DeleteAccountDialog.tsx` | Destructive confirmation dialog |
| `frontend/src/components/settings/index.ts` | Update barrel export |

### Technical Requirements

- **Clerk Backend API**: Use `httpx` to call `DELETE https://api.clerk.com/v1/users/{user_id}` with `Authorization: Bearer {CLERK_SECRET_KEY}`. Add `CLERK_SECRET_KEY` to `core/config.py` settings.
- **ARQ worker**: Follow existing `workers/arq_settings.py` pattern. Export worker connects to Redis, processes export queue.
- **CASCADE behavior**: `user_preferences` already has `ondelete="CASCADE"` on user_id FK. Future tables should too. For MVP, only users + user_preferences + data_exports exist. Delete in reverse FK order to avoid constraint violations.
- **ZIP archive**: Use Python stdlib `zipfile`. Include: `profile.json`, `preferences.json`. Future stories will add vocabulary, SRS data, etc.
- **File storage**: Store in `{backend_root}/data/exports/{user_id}/{export_id}.zip`. Create directory if not exists. Configure path in `core/config.py`.
- **Export TTL**: 7 days. Expired exports cleaned by a periodic ARQ task or on-demand.

### UX Requirements

- **Toast notifications**: Success toast (green border-l-4, 3s auto-dismiss) for export request. Error toast (red, persistent) on failure.
- **Destructive dialog**: Must require typing full email to confirm. Delete button red (`bg-red-600`), disabled until email matches. Use shadcn `AlertDialog` component.
- **Button hierarchy**: Export = secondary (outlined). Delete = ghost with destructive variant.
- **Loading states**: Show spinner on buttons during API calls. Disable buttons while pending.

### Anti-Patterns to Avoid

- Do NOT build a custom confirmation modal — use shadcn `AlertDialog`
- Do NOT use `window.confirm()` for deletion
- Do NOT store export files in the database (BLOB) — use filesystem
- Do NOT call Clerk deletion from frontend — always server-side with backend secret key
- Do NOT delete Clerk account before local DB deletion (if Clerk fails, user can retry; if local fails after Clerk deletion, orphaned data)
- Do NOT create a separate privacy module — this belongs in auth module

### Previous Story Intelligence (Story 2-3)

- **Settings page structure**: Already has `section > Card > CardHeader + CardContent` pattern. Add new Card below existing ones.
- **TanStack Query pattern**: Uses `userKeys.preferences()` query key factory. Extend with `userKeys.dataExport()`.
- **Toast integration**: Already uses `useToast()` from shadcn — reuse same pattern.
- **Barrel exports**: `components/settings/index.ts` exists — add new component exports there.
- **Backend service pattern**: `UserPreferencesService` in `services.py` shows the pattern. New services follow same DI pattern.
- **Repository pattern**: `SqlAlchemyUserRepository` implements both `UserRepository` and `UserPreferencesRepository`. Can add `DataExportRepository` methods to same class or create new repo.
- **Vitest config**: Story 2-3 fixed jsdom dependency. Tests work with `vitest.config.ts` using jsdom environment.

### Git Intelligence

- Recent commits show consistent pattern: one commit per story with descriptive message.
- Frontend workspace is `frontend/` (was renamed from `table-project-web/` in commit 8fd0c6b).
- CI pipelines exist: `ci-backend.yml` and `ci-frontend.yml`.

### Project Structure Notes

- Backend: `backend/src/app/modules/auth/` — all auth-related code
- Frontend: `frontend/src/app/(app)/settings/` — settings pages inside authenticated layout
- Components: `frontend/src/components/settings/` — settings-specific components
- Workers: `backend/src/app/workers/` — ARQ background workers
- Migrations: `backend/alembic/versions/` — Alembic async migrations

### References

- [Source: _out_put/planning-artifacts/epics/epic-2-user-authentication-onboarding-profile.md — Story 2.4]
- [Source: _out_put/planning-artifacts/architecture.md — Authentication & Security, Data Privacy]
- [Source: _out_put/planning-artifacts/architecture.md — API Patterns, Naming Conventions]
- [Source: _out_put/planning-artifacts/architecture.md — Module Structure, Hexagonal Architecture]
- [Source: _out_put/planning-artifacts/ux-design-specification.md — Toast Patterns, Button Hierarchy, Form Patterns]
- [Source: _out_put/implementation-artifacts/2-3-user-profile-settings-management.md — Previous Story Learnings]
- [Source: backend/src/app/modules/auth/ — Existing auth module code]

## Dev Agent Record

### Agent Model Used

gpt-5.4

### Debug Log References

- `cd backend && docker compose up -d postgres redis`
- `cd backend && uv run pytest`
- `cd backend && uv run pytest tests/unit`
- `cd backend && uv run ruff check .`
- `cd backend && uv run mypy`
- `cd frontend && npm test`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

### Completion Notes List

- Added a new `DataExportService`, `DataExport` entity/repository flow, `data_exports` migration, and `process_data_export` ARQ worker so authenticated users can request a background ZIP export, poll status, and download the archive from the same API path when it is ready.
- Added `DELETE /api/v1/users/me` with email confirmation, server-side Clerk deletion, export-file cleanup, and ordered local cascade deletion for `data_exports`, `user_preferences`, and `users`, with structlog-only audit logging that avoids PII.
- Extended the Settings page with a new `Data & Privacy` card, a request-export action, and a destructive `AlertDialog` account deletion flow wired through TanStack Query, Clerk sign-out, and redirect to `/`.
- Updated toast behavior so success notifications auto-dismiss after 3 seconds while error notifications stay persistent, matching the story UX requirements for privacy actions.
- Added backend unit/e2e/integration coverage plus frontend Vitest coverage for export request, archive generation, download, confirmation validation, Clerk deletion mocking, and account deletion redirect flow; backend pytest, backend ruff, backend mypy, frontend test, frontend lint, and frontend build all passed.

### File List

- `_out_put/implementation-artifacts/2-4-data-export-account-deletion.md`
- `_out_put/implementation-artifacts/sprint-status.yaml`
- `backend/alembic/versions/7b1d5f4c2a10_add_data_exports_table.py`
- `backend/src/app/core/config.py`
- `backend/src/app/modules/auth/api/router.py`
- `backend/src/app/modules/auth/api/schemas.py`
- `backend/src/app/modules/auth/application/services.py`
- `backend/src/app/modules/auth/domain/entities.py`
- `backend/src/app/modules/auth/domain/exceptions.py`
- `backend/src/app/modules/auth/domain/interfaces.py`
- `backend/src/app/modules/auth/infrastructure/models.py`
- `backend/src/app/modules/auth/infrastructure/repository.py`
- `backend/src/app/workers/arq_settings.py`
- `backend/src/app/workers/export_worker.py`
- `backend/tests/e2e/test_data_privacy_flow.py`
- `backend/tests/unit/modules/auth/application/test_data_privacy_services.py`
- `backend/tests/unit/modules/auth/application/test_preferences_services.py`
- `backend/tests/unit/modules/auth/application/test_services.py`
- `backend/tests/unit/test_arq_settings.py`
- `frontend/src/app/(app)/settings/page.tsx`
- `frontend/src/components/settings/DataExportButton.test.tsx`
- `frontend/src/components/settings/DataExportButton.tsx`
- `frontend/src/components/settings/DeleteAccountDialog.test.tsx`
- `frontend/src/components/settings/DeleteAccountDialog.tsx`
- `frontend/src/components/settings/index.ts`
- `frontend/src/components/ui/alert-dialog.tsx`
- `frontend/src/components/ui/toast.tsx`
- `frontend/src/lib/query-keys.ts`

### Change Log

- 2026-05-06: Implemented Story 2.4 data export and account deletion across backend API, persistence, ARQ worker, settings UI, destructive confirmation flow, and automated tests; story is ready for review.
