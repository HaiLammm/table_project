# Epic 2: User Authentication, Onboarding & Profile

Users can register (email/Google/LINE OAuth), log in with persistent sessions, complete a 5-question onboarding survey to receive an AI-generated learning plan, manage profile settings, and exercise data privacy rights (export/delete).

## Story 2.1: User Registration & Login with Clerk

As a **new user**,
I want to register using email/password, Google OAuth, or LINE OAuth, and log in with persistent sessions across browser tabs,
So that I can securely access my learning data from any device.

**Acceptance Criteria:**

**Given** a visitor is on the sign-up page
**When** they register with email/password, Google OAuth, or LINE OAuth
**Then** a Clerk account is created and the user is redirected to the onboarding flow
**And** a corresponding user record is created in the backend database (via Clerk webhook sync)
**And** the user record stores: clerk_id, email, display_name, tier (default: free), created_at

**Given** a registered user is on the sign-in page
**When** they log in with their credentials
**Then** a Clerk session is established with short-lived JWT (15-minute access token + refresh rotation)
**And** the session persists across browser tabs
**And** authenticated API requests include the Clerk JWT in the Authorization header
**And** the backend `get_current_user` dependency verifies the JWT and extracts user identity

**Given** a user is not authenticated
**When** they try to access any `/app/*` route
**Then** they are redirected to the sign-in page via Next.js middleware

## Story 2.2: Onboarding Survey & AI Learning Plan

As a **new user**,
I want to complete a 5-question onboarding survey and receive a personalized AI-generated learning plan,
So that my vocabulary study is tailored to my goals, level, and domain from the first session.

**Acceptance Criteria:**

**Given** a new user completes registration
**When** they land on the onboarding page
**Then** a 5-step survey is presented one question per screen with progress dots per UX-DR9:
  Q1: Primary learning goal (JLPT prep / TOEIC prep / workplace communication / general)
  Q2: Current English level (beginner / intermediate / advanced)
  Q3: Current Japanese level (N5 / N4 / N3 / N2 / N1 / none)
  Q4: Daily study time preference (5 min / 15 min / 30 min / 60 min) — skippable
  Q5: IT domain (web dev / backend / networking / data / general IT) — skippable
**And** selected options fill black (#18181B) for visual feedback
**And** back button is available on Q2–Q5
**And** skipped questions use sensible defaults

**Given** the user completes the survey
**When** the system generates a learning plan
**Then** a personalized plan summary is displayed (recommended collections, daily card target, study schedule)
**And** the user can accept or modify the plan
**And** upon acceptance, an initial collection is seeded from the pre-seeded corpus matching the plan
**And** a mini-session of 5 easy cards starts immediately
**And** the entire onboarding flow completes in under 3 minutes

**Given** a user closes the app mid-onboarding
**When** they return
**Then** the survey resumes from the last answered question

## Story 2.3: User Profile & Settings Management

As a **registered user**,
I want to view and edit my profile settings including languages, level, goals, daily study budget, and notification preferences,
So that I can keep my learning experience aligned with my evolving needs.

**Acceptance Criteria:**

**Given** a user navigates to Settings
**When** the settings page loads
**Then** the user sees their Clerk profile (name, email, avatar) via Clerk UserProfile component
**And** app-specific preferences are displayed: languages, current level, learning goal, daily study budget, notification preferences
**And** all preferences are editable and saved via API (`PUT /api/v1/users/me/preferences`)

**Given** a user updates their daily study budget
**When** they save the change
**Then** the FSRS daily queue adjusts accordingly on the next queue generation
**And** a toast confirms "Settings updated"

## Story 2.4: Data Export & Account Deletion (GDPR/APPI/PDPD)

As a **registered user**,
I want to export all my personal data or permanently delete my account and all associated data,
So that I can exercise my data privacy rights as required by GDPR, APPI, and PDPD.

**Acceptance Criteria:**

**Given** a user navigates to Settings → Data & Privacy
**When** they request a data export
**Then** the system generates a downloadable archive containing: user profile, all vocabulary terms, review history, learning patterns, collections, and diagnostic data
**And** the export is available within 24 hours (background job)
**And** the user receives notification when export is ready

**Given** a user requests account deletion
**When** they confirm via a destructive action dialog (type account email to confirm)
**Then** all user data is permanently deleted: user record, vocabulary, SRS cards, reviews, collections, enrichment jobs, diagnostic data
**And** the Clerk account is deleted
**And** the deletion is irreversible
**And** the user is logged out and redirected to the landing page

## Story 2.5: Warm Return Experience

As a **returning user**,
I want the app to welcome me back without guilt messaging after any absence,
So that I feel comfortable returning to my learning at any time.

**Acceptance Criteria:**

**Given** a returning user opens the app (Today's Queue is the landing page)
**When** they have been absent for 1+ days
**Then** the queue displays a neutral context line: "{N} cards ready. ~{M} min estimated." per UX-DR22
**And** no streak-loss messaging, no "you missed X days" guilt
**And** FSRS has silently rescheduled cards during absence (overdue cards prioritized)

**Given** a returning user has 100+ overdue cards after extended absence
**When** the queue loads
**Then** a "catch-up mode" suggestion appears: "You have {N} cards. We suggest starting with the 30 most overdue."
**And** the user can accept catch-up mode or review the full queue
