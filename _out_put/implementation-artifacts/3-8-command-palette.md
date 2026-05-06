# Story 3.8: Command Palette (⌘K) for Vocabulary Search

Status: review

## Story

As a **user**,
I want a command palette (⌘K / Ctrl+K) for quick full-text search across vocabulary, collections, and navigation,
so that I can find and act on anything in the app without leaving the keyboard.

## Acceptance Criteria (BDD)

1. **Given** a user presses ⌘K or Ctrl+K on any page (UX-DR24)
   **When** the command palette opens
   **Then** a full-screen overlay with backdrop blur appears
   **And** the search input is auto-focused
   **And** results are grouped by category: Pages, Collections, Words
   **And** results stream as the user types (debounced 200ms)
   **And** vocabulary search uses PostgreSQL tsvector full-text search

2. **Given** results are displayed
   **When** the user navigates with arrow keys + Enter
   **Then** the selected result navigates to the corresponding page/term/collection
   **And** Esc closes the palette
   **And** recent searches appear on empty state

## Tasks / Subtasks

- [x] Task 1: Install shadcn/ui Command component and cmdk dependency (AC: 1)
  - [x] 1.1 Run `npx shadcn@latest add command dialog` to install the Command component (wraps cmdk) and Dialog if not present
  - [x] 1.2 Verify `cmdk` is added to `package.json` dependencies

- [x] Task 2: Create the CommandPalette component (AC: 1, 2)
  - [x] 2.1 Create `frontend/src/components/layout/CommandPalette.tsx` using shadcn `CommandDialog` (cmdk + Radix Dialog)
  - [x] 2.2 Implement three result groups: **Pages** (static navigation links), **Collections** (user collections), **Words** (vocabulary tsvector search)
  - [x] 2.3 Debounce search input by 200ms before triggering vocabulary API query (reuse `useVocabularySearch` pattern)
  - [x] 2.4 Show recent searches on empty state using `localStorage` (key: `command-palette-recent`, store last 5 searches)
  - [x] 2.5 Add backdrop blur via Tailwind: `backdrop-blur-sm` on the overlay
  - [x] 2.6 Create `CommandPalette.test.tsx` co-located with component

- [x] Task 3: Wire global keyboard shortcut ⌘K / Ctrl+K (AC: 1)
  - [x] 3.1 Register global `keydown` listener in CommandPalette for `metaKey+k` and `ctrlKey+k`
  - [x] 3.2 Prevent default browser behavior (Ctrl+K focuses browser address bar)
  - [x] 3.3 Ensure shortcut does NOT fire when user is typing in an input/textarea (check `event.target` tagName)

- [x] Task 4: Integrate into app shell and replace placeholder (AC: 1, 2)
  - [x] 4.1 Mount `<CommandPalette />` in `frontend/src/components/layout/AppShell.tsx`
  - [x] 4.2 Replace the disabled Search button in `Topbar.tsx` with a clickable button that opens the palette
  - [x] 4.3 Keep the `⌘K` keyboard hint badge on the button

- [x] Task 5: Navigation and result actions (AC: 2)
  - [x] 5.1 Pages group: Dashboard, Vocabulary, Collections, Review, Diagnostics, Settings — use `next/navigation` `useRouter().push()`
  - [x] 5.2 Words group: navigate to `/vocabulary/{termId}` on selection
  - [x] 5.3 Collections group: navigate to `/collections/{collectionId}` on selection (requires a collections list endpoint or hook)
  - [x] 5.4 Close palette after navigation and store the selected term/page in recent searches
  - [x] 5.5 Arrow keys + Enter navigation is handled natively by cmdk — verify it works

- [x] Task 6: Backend — add unified search endpoint (AC: 1)
  - [x] 6.1 Add `GET /api/v1/search?query=...&limit=10` in a new lightweight `search` router or extend vocabulary router
  - [x] 6.2 Return results from vocabulary terms (tsvector search, existing `search_terms` method) and later collections
  - [x] 6.3 If a collections search is not yet available (no collection module CRUD exists), return only vocabulary + static pages for now and add a TODO for collections search

- [x] Task 7: Mobile responsiveness (AC: 1)
  - [x] 7.1 On mobile (<640px), replace ⌘K with a simplified top search bar per UX spec
  - [x] 7.2 Hide the ⌘K keyboard hint badge on mobile
  - [x] 7.3 Command palette dialog should be full-width on mobile

- [x] Task 8: Tests (AC: all)
  - [x] 8.1 Frontend unit tests: palette opens/closes on ⌘K, Esc closes, typing triggers debounced search, recent searches persist
  - [x] 8.2 Frontend tests: result groups render, arrow key navigation works, Enter navigates
  - [x] 8.3 Backend test: search endpoint returns vocabulary results with correct ranking

## Dev Notes

### Story Intent

This is the final story in Epic 3. It replaces the disabled placeholder search button in the Topbar (added in Story 1-3) with a fully functional command palette. The backend search infrastructure (PostgreSQL tsvector, `search_terms` repository method) already exists from Story 3.2.

### Current Code You Must Extend

**`frontend/src/components/layout/Topbar.tsx`**
- Current state: lines 59-71 contain a `disabled` Button with Search icon and ⌘K badge
- Story 3.8 change: make the button clickable to open CommandPalette
- Preserve: the visual style (ghost variant, zinc colors, ⌘K badge)

**`frontend/src/components/layout/AppShell.tsx`**
- Current state: renders Sidebar + Topbar + main content area
- Story 3.8 change: mount `<CommandPalette />` here (it renders as a Dialog, so placement within the tree is flexible)

**`frontend/src/hooks/useVocabularySearch.ts`**
- Current state: debounced vocabulary search hook using `vocabularyKeys.search(query)` and `GET /vocabulary_terms/search`
- Story 3.8 change: reuse this hook inside CommandPalette for the Words group. Do NOT duplicate the search logic.

**`frontend/src/lib/query-keys.ts`**
- Current state: has `vocabularyKeys.search(query)` already defined
- Story 3.8 change: add `collectionKeys` if collections search is added; otherwise no change needed

**`backend/src/app/modules/vocabulary/infrastructure/repository.py`**
- Current state: `search_terms()` already implements tsvector search with `ts_rank_cd` ranking (lines 123-141)
- Story 3.8 change: no change needed — this is already sufficient for the command palette vocabulary search

**`backend/src/app/modules/vocabulary/api/router.py`**
- Current state: `GET /vocabulary_terms/search` endpoint exists (lines 48-63) with query, language, limit params
- Story 3.8 change: may reuse as-is. If a unified `/search` endpoint is preferred, create a thin wrapper that delegates to existing search methods.

### Architecture Guardrails

1. Use shadcn/ui `Command` component (wraps `cmdk`) — do NOT build a custom command palette from scratch
2. Keep search logic in hooks, not in the component. CommandPalette should compose existing hooks.
3. All keyboard shortcut handling should check that no input/textarea is focused to avoid conflicts
4. The palette is a client component (`"use client"`) since it manages local state and keyboard events
5. Follow the existing Topbar/Sidebar component patterns for file location and naming
6. Mobile: simplified search bar, not a command palette dialog (per UX spec)
7. Recent searches: use `localStorage`, not server state. Keep it simple — last 5 items.

### Technology Notes

**cmdk library** — shadcn/ui's Command component wraps this. Key features:
- Built-in fuzzy search and filtering
- Keyboard navigation (arrow keys, Enter, Esc) handled automatically
- Group support (`Command.Group`) for Pages / Collections / Words sections
- Empty state support for showing recent searches
- Accessible: ARIA roles and keyboard management built in

**Installation:** `npx shadcn@latest add command` installs both the shadcn wrapper and the `cmdk` peer dependency. The component lands in `frontend/src/components/ui/command.tsx`.

### Files to Create

- `frontend/src/components/layout/CommandPalette.tsx`
- `frontend/src/components/layout/CommandPalette.test.tsx`

### Files to Update

- `frontend/src/components/layout/Topbar.tsx` — replace disabled button with clickable trigger
- `frontend/src/components/layout/AppShell.tsx` — mount CommandPalette
- `frontend/src/components/layout/index.ts` — export CommandPalette
- `frontend/package.json` — cmdk dependency added automatically by shadcn CLI

### Current Project Structure Notes

- The architecture document refers to the frontend as `table-project-web/` but the actual repo uses `frontend/`. Follow **real repo paths**.
- shadcn/ui components live in `frontend/src/components/ui/`. The Command component will be auto-generated there.
- Layout components live in `frontend/src/components/layout/`.

### Testing Requirements

**Frontend unit tests:**
- ⌘K / Ctrl+K opens the palette
- Esc closes the palette
- Clicking the Topbar search button opens the palette
- Typing triggers debounced vocabulary search (200ms)
- Results are grouped into Pages, Collections (if available), Words
- Arrow keys + Enter navigates to selected result
- Recent searches appear on empty state
- Recent searches update after selecting a result
- Palette does NOT open when focused on an input field

**Backend tests:**
- Existing search endpoint tests should already cover vocabulary search
- If a new unified `/search` endpoint is created, add integration test

### Previous Story Intelligence

**From Story 3.7 (previous story):**
- Recent work established the LLM gateway and enrichment pipeline
- ARQ workers pattern is now well-established
- Frontend hooks follow the `useApiClient()` + TanStack Query pattern consistently

**From Story 1.3 (App Shell Layout):**
- The disabled search button placeholder was explicitly created for this story
- The Topbar follows shadcn Button component patterns with Lucide icons
- AppShell wraps Sidebar + Topbar + main area

**From Story 3.2 (Browse & Search):**
- `useVocabularySearch` hook already handles debounced search with the vocabulary search API
- PostgreSQL tsvector full-text search is production-ready
- Search results include term, language, cefr_level, definitions

### Git Intelligence

- Commit prefix pattern: `feat#3-8` for this story
- Recent commits show cross-layer implementation (backend + frontend together)
- The vocabulary search infrastructure has been stable since Story 3.2

### References

- [Source: _out_put/planning-artifacts/epics/epic-3-vocabulary-management-enrichment-pipeline.md - Story 3.8]
- [Source: _out_put/planning-artifacts/architecture.md - Frontend Architecture, Command Palette, shadcn/ui, tsvector search]
- [Source: _out_put/planning-artifacts/ux-design-specification.md - Command Palette UX, keyboard shortcuts, responsive behavior]
- [Source: frontend/src/components/layout/Topbar.tsx - disabled search button placeholder]
- [Source: frontend/src/hooks/useVocabularySearch.ts - existing vocabulary search hook]
- [Source: frontend/src/lib/query-keys.ts - vocabularyKeys.search]
- [Source: backend/src/app/modules/vocabulary/api/router.py - GET /vocabulary_terms/search endpoint]
- [Source: backend/src/app/modules/vocabulary/infrastructure/repository.py - search_terms with tsvector]
- [External: shadcn/ui Command component - https://ui.shadcn.com/docs/components/command]
- [External: cmdk library - https://github.com/pacocoursey/cmdk]

## Dev Agent Record

### Agent Model Used

gpt-5.4

### Debug Log References

- `pnpm exec vitest run src/components/layout/CommandPalette.test.tsx src/components/layout/Topbar.test.tsx src/hooks/useVocabularySearch.test.tsx`
- `pnpm exec eslint src/components/layout/CommandPalette.tsx src/components/layout/Topbar.tsx src/components/layout/AppShell.tsx src/components/layout/CommandPalette.test.tsx src/components/layout/Topbar.test.tsx src/hooks/useVocabularySearch.test.tsx src/components/ui/command.tsx src/components/ui/dialog.tsx src/app/(app)/review/page.tsx src/app/(app)/diagnostics/page.tsx`
- `uv run ruff check src/app/main.py src/app/modules/search tests/integration/modules/search/test_api.py`
- `uv run pytest tests/integration/modules/search/test_api.py`
- `pnpm test -- src/components/layout/CommandPalette.test.tsx src/components/layout/Topbar.test.tsx src/hooks/useVocabularySearch.test.tsx` also surfaced existing unrelated failures in `AddTermForm`, `TermAutoSuggest`, and `VocabularyRequestForm`

### Completion Notes List

- Added `cmdk` plus new `ui/command` and `ui/dialog` wrappers without overwriting the repo's existing `button.tsx`
- Implemented `CommandPalette` with grouped Pages / Collections / Words results, recent searches in `localStorage`, keyboard shortcuts, and mobile full-width behavior
- Integrated the palette into `AppShell` and replaced the disabled Topbar search button with an active trigger that preserves the `⌘K` hint on desktop
- Added placeholder `/review` and `/diagnostics` pages so all page navigation targets from the palette resolve in-app
- Added a lightweight backend `GET /api/v1/search` endpoint that returns static pages plus ranked vocabulary results and leaves a TODO for real collection search
- Frontend targeted tests, frontend lint, backend ruff, and backend search integration tests all passed

### File List

- `frontend/package.json`
- `frontend/pnpm-lock.yaml`
- `frontend/src/components/ui/dialog.tsx`
- `frontend/src/components/ui/command.tsx`
- `frontend/src/components/layout/CommandPalette.tsx`
- `frontend/src/components/layout/CommandPalette.test.tsx`
- `frontend/src/components/layout/Topbar.tsx`
- `frontend/src/components/layout/Topbar.test.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/index.ts`
- `frontend/src/hooks/useVocabularySearch.test.tsx`
- `frontend/src/app/(app)/review/page.tsx`
- `frontend/src/app/(app)/diagnostics/page.tsx`
- `backend/src/app/main.py`
- `backend/src/app/modules/search/__init__.py`
- `backend/src/app/modules/search/api/__init__.py`
- `backend/src/app/modules/search/api/router.py`
- `backend/src/app/modules/search/api/schemas.py`
- `backend/tests/integration/modules/search/__init__.py`
- `backend/tests/integration/modules/search/test_api.py`

### Change Log

- 2026-05-06: Implemented Story 3.8 command palette UI, app-shell integration, mobile trigger behavior, and backend unified search route.
