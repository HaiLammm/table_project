# Epic 5: Personal Collections

Users can create, rename, and delete personal vocabulary collections, add/remove terms, browse collection contents, and start focused learning sessions from a collection (bridge to SRS).

## Story 5.1: Collection CRUD & Data Model

As a **user**,
I want to create, rename, and delete personal vocabulary collections,
So that I can organize my vocabulary by topic, exam, or project.

**Acceptance Criteria:**

**Given** the collections module is initialized
**When** Alembic migration runs
**Then** `collections` table is created with: id, user_id, name, icon, created_at, updated_at
**And** `collection_terms` table is created with: id, collection_id, term_id, added_at

**Given** a user navigates to Collections page
**When** the page loads
**Then** collections display in a 2-column grid (1-column on mobile) with CollectionCard components per UX-DR6
**And** each card shows: icon, name, term count, mastery percentage, progress bar (zinc-600 fill)
**And** a "+" card with dashed border appears at the end for creating new collections

**Given** no collections exist
**When** the page loads
**Then** the empty state displays: "No collections yet" with "+ New Collection" action per UX-DR16

**Given** a user clicks "+ New Collection"
**When** the dialog opens
**Then** they enter a name + choose an icon → collection is created via `POST /api/v1/collections`
**And** the new CollectionCard appears in the grid immediately

**Given** a user wants to rename or delete a collection
**When** they open the dropdown menu on a CollectionCard
**Then** "Rename" opens inline edit (click name → edit → Enter/Esc)
**And** "Delete" shows confirmation dialog: "Delete '{name}'? The {N} terms will remain in your library but won't be grouped."
**And** deletion removes the collection and collection_terms associations, but NOT the vocabulary terms themselves

## Story 5.2: Add & Remove Terms from Collections

As a **user**,
I want to add and remove vocabulary terms from my collections,
So that I can curate focused study sets for specific learning goals.

**Acceptance Criteria:**

**Given** a user is on a collection detail page
**When** they click "Add Words"
**Then** they can add terms via 3 methods:
  1. Manual: type term → auto-suggest from corpus → Enter to add
  2. Browse corpus: search Database Waterfall → select terms → add
  3. CSV import: upload file → preview → confirm (reuses Epic 3 CSV import flow)
**And** each added term creates a collection_terms record via `POST /api/v1/collections/{id}/terms`
**And** duplicate detection warns if a term already exists in this collection

**Given** a user wants to remove a term from a collection
**When** they select remove on a term
**Then** the collection_terms association is deleted (the term and its SRS card remain)
**And** a toast with undo option appears: "Term removed from collection — Undo"

## Story 5.3: Browse Collection Contents & Detail View

As a **user**,
I want to browse the terms within a collection and see per-collection stats,
So that I can track mastery progress for each study group.

**Acceptance Criteria:**

**Given** a user clicks a CollectionCard
**When** the collection detail page loads (`GET /api/v1/collections/{id}`)
**Then** the page shows: collection name, icon, total terms, mastery percentage, progress bar
**And** terms are listed with: term, language, CEFR/JLPT level, mastery status (new/learning/mastered)
**And** terms are paginated (`page_size=20`) with search/filter capability

**Given** a user clicks a term in the collection
**When** the term detail loads
**Then** it navigates to the vocabulary term detail page (reuses Story 3.3 view)

## Story 5.4: Start Learning Session from Collection

As a **user**,
I want to start a focused review session from a specific collection,
So that I can study vocabulary grouped by topic rather than the full mixed queue.

**Acceptance Criteria:**

**Given** a user is on a collection detail page (FR25)
**When** they click "Start Learning"
**Then** the review flow starts with only cards from this collection that are due
**And** the review uses the same ReviewCard/RatingButton/session flow from Epic 4
**And** the breadcrumb shows: "Reviewing · {collection name} · 3 / 12"

**Given** a collection has terms not yet in the SRS
**When** the user clicks "Start Learning"
**Then** SRS cards are created for unadded terms (FSRS default state)
**And** these new cards join the session queue

**Given** a user wants to pause or archive a collection's learning
**When** they select "Pause Learning" on a collection
**Then** cards from this collection are excluded from the daily global queue (but remain reviewable via collection-specific session)
**And** the collection shows a "Paused" badge
