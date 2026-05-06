# Epic 3: Vocabulary Management & Enrichment Pipeline

Users can browse/search the pre-seeded vocabulary corpus, view terms in single-language or parallel bilingual mode, add terms manually, request LLM-enriched vocabulary sets via structured form, import from CSV, and view the hierarchical vocabulary tree. The system auto-enriches terms via LLM, cross-validates Japanese definitions against JMdict, and syncs validated results to the central corpus (Database Waterfall).

## Story 3.1: Vocabulary Data Model & Pre-seeded Corpus

As a **user**,
I want a pre-seeded vocabulary corpus of 3,000–5,000 IT/TOEIC/JLPT terms available from day one,
So that I can start learning immediately without building my own deck.

**Acceptance Criteria:**

**Given** the system is initialized
**When** the seed script runs
**Then** the `vocabulary_terms` and `vocabulary_definitions` tables are created via Alembic migration
**And** vocabulary_terms stores: id, term, language (en/jp), parent_id (adjacency list), cefr_level, jlpt_level, part_of_speech, created_at, updated_at
**And** vocabulary_definitions stores: id, term_id, language, definition, ipa, examples (JSONB), source (seed/user/llm), validated_against_jmdict (boolean), created_at
**And** a tsvector index exists on vocabulary_terms for full-text search
**And** 3,000–5,000 terms are seeded via LLM batch job with JMdict cross-validation for all Japanese definitions
**And** seeded terms cover IT, TOEIC, JLPT N3–N2 categories with hierarchical parent_id relationships
**And** the JMdict dataset (~170K entries) is loaded via jamdict and available as LRU-cached in-process lookups

## Story 3.2: Browse & Search Vocabulary Corpus

As a **user**,
I want to browse and search the vocabulary corpus by topic, CEFR level, and JLPT level,
So that I can discover relevant vocabulary for my learning goals.

**Acceptance Criteria:**

**Given** a user navigates to the Vocabulary page
**When** the page loads
**Then** vocabulary terms are displayed in a paginated list (`GET /api/v1/vocabulary_terms?page=1&page_size=20`)
**And** filters are available for: topic (hierarchical category), CEFR level (A1–C2), JLPT level (N5–N1)
**And** a search bar accepts text queries that search via PostgreSQL tsvector full-text search
**And** search results return matching terms with highlighted match context

**Given** a user views the hierarchical vocabulary tree (FR13)
**When** they expand a category (e.g., IT → Networking)
**Then** child terms are loaded and displayed with parent-child indentation
**And** recursive CTEs retrieve the hierarchy efficiently

## Story 3.3: View Vocabulary Term (Single-Language & Parallel Mode)

As a **user**,
I want to view a vocabulary term with its definition, IPA, examples, and level in single-language or parallel bilingual mode,
So that I can study terms with the appropriate cognitive load for my learning stage.

**Acceptance Criteria:**

**Given** a user selects a vocabulary term
**When** the term detail page loads (`GET /api/v1/vocabulary_terms/{term_id}`)
**Then** the term is displayed in single-language view (default) showing: term, definition, IPA (JetBrains Mono font), example sentences, CEFR level, JLPT level, part of speech, related terms (FR8)
**And** Japanese text renders in Noto Sans JP, Latin in Inter, IPA in JetBrains Mono (automatic via unicode-range)

**Given** a user toggles parallel mode (FR9)
**When** they click the parallel toggle or press Tab
**Then** both English and Japanese definitions are displayed side-by-side
**And** the toggle state persists for the session

**Given** a definition has not been cross-validated against JMdict (FR37)
**When** it is displayed
**Then** a warning indicator icon appears next to the definition

## Story 3.4: Add Vocabulary Term Manually

As a **user**,
I want to add a new vocabulary term manually with basic information,
So that I can include words I encounter outside the pre-seeded corpus.

**Acceptance Criteria:**

**Given** a user is on the Add Words interface
**When** they type a term (2+ characters)
**Then** an auto-suggest dropdown shows matching terms from the corpus (term + reading + level)
**And** arrow keys navigate suggestions, Enter selects, Esc closes

**Given** a user enters a new term not in the corpus (FR10)
**When** they submit with term, language, and optional definition
**Then** the term is created in vocabulary_terms via `POST /api/v1/vocabulary_terms`
**And** the system triggers auto-enrichment (FR14) as a background job to fill definitions, IPA, CEFR, examples
**And** the term appears in the user's vocabulary immediately (with pending enrichment indicator)
**And** a toast confirms "Term added — enriching..."

## Story 3.5: Structured Vocabulary Request (LLM-Enriched)

As a **user**,
I want to request a vocabulary set by topic, level, and count and receive LLM-enriched terms to preview and confirm,
So that I can efficiently build vocabulary in specific domains without manual card creation.

**Acceptance Criteria:**

**Given** a user opens the structured vocabulary request form (FR11)
**When** they submit a request (topic: "networking", level: "B2", count: 30)
**Then** the system queries the corpus for existing matches
**And** for gaps, the LLM Gateway generates enriched terms (definition, IPA, CEFR, examples) via the enrichment pipeline
**And** all Japanese definitions are cross-validated against JMdict before display (FR15)
**And** a preview list shows all generated terms with enrichment data

**Given** a user reviews the preview
**When** they confirm (select all or deselect individual terms)
**Then** confirmed terms are added to vocabulary_terms and the user's active vocabulary
**And** terms sync to the central corpus via Database Waterfall after deduplication (FR16)
**And** enrichment results are cached in Redis (key: hash of term+lang+level, TTL: 30 days)

## Story 3.6: CSV Import with Error Handling

As a **user**,
I want to import vocabulary from CSV files with error preview and partial import capability,
So that I can migrate my existing vocabulary from Anki or other tools.

**Acceptance Criteria:**

**Given** a user navigates to the CSV Import page
**When** they upload a CSV file (drag-drop or file picker)
**Then** the system parses the file supporting UTF-8 with BOM, tab-separated values, and hierarchical tag notation (Subject::Unit::Topic) per NFR26
**And** a preview shows the first 10 rows with parsing status

**Given** the CSV contains malformed records (FR12)
**When** the preview displays
**Then** successfully parsed records show green checkmark with count
**And** problematic records show warning with specific error (missing fields, encoding issues, HTML tags)
**And** the user can import clean records immediately and place problematic records in a "Review Later" queue

**Given** the user confirms import
**When** the import processes
**Then** up to 5,000 records process within 30 seconds (NFR6)
**And** progress indication appears for imports > 500 records
**And** imported terms trigger auto-enrichment as background jobs (FR14)
**And** the system recalibrates FSRS scheduling for imported cards within 3–5 days (FR21)
**And** a summary shows: X imported, Y need review, Z duplicates skipped

## Story 3.7: LLM Gateway & Auto-Enrichment Pipeline

As the **system**,
I want an LLM Gateway that routes enrichment requests to multiple providers with caching, cost tracking, and JMdict validation,
So that vocabulary enrichment is reliable, cost-effective, and accurate.

**Acceptance Criteria:**

**Given** a term needs enrichment (FR14)
**When** the enrichment worker processes the job
**Then** the LLM Gateway checks Redis cache first (key: hash of term+lang+level)
**And** on cache miss, routes to the configured provider (Claude Haiku → Gemini Flash → DeepSeek fallback)
**And** the LLM returns structured output validated against a Pydantic schema (definition, IPA, CEFR level, examples, related terms)
**And** Japanese definitions are cross-validated against JMdict via the dictionary module (FR15)
**And** validated results are stored in vocabulary_definitions with source='llm' and validated_against_jmdict=true/false
**And** results are cached in Redis (TTL: 30 days)

**Given** enrichment results pass validation
**When** the corpus sync worker runs (Database Waterfall — FR16)
**Then** enriched terms are deduplicated against the central corpus
**And** new validated terms are merged into the central corpus

**Given** an LLM provider fails
**When** the gateway detects the failure
**Then** it retries up to 3 times with exponential backoff (NFR33)
**And** falls back to the next configured provider
**And** failed jobs route to a dead-letter queue for admin review
**And** per-user daily cost is tracked and remains below $0.02 (NFR19)

## Story 3.8: Command Palette (⌘K) for Vocabulary Search

As a **user**,
I want a command palette (⌘K / Ctrl+K) for quick full-text search across vocabulary, collections, and navigation,
So that I can find and act on anything in the app without leaving the keyboard.

**Acceptance Criteria:**

**Given** a user presses ⌘K or Ctrl+K on any page (UX-DR24)
**When** the command palette opens
**Then** a full-screen overlay with backdrop blur appears
**And** the search input is auto-focused
**And** results are grouped by category: Pages, Collections, Words
**And** results stream as the user types (debounced 200ms)
**And** vocabulary search uses PostgreSQL tsvector full-text search

**Given** results are displayed
**When** the user navigates with arrow keys + Enter
**Then** the selected result navigates to the corresponding page/term/collection
**And** Esc closes the palette
**And** recent searches appear on empty state
