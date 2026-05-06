# Story 1.3: App Shell Layout (Sidebar, Topbar, Content Area)

Status: review

## Story

As a **user**,
I want a consistent app navigation shell with dark sidebar, topbar with breadcrumb, and centered content area,
so that I can navigate between app sections efficiently on any device.

## Acceptance Criteria

1. **Given** a user is on any authenticated page **When** the page loads **Then** a dark sidebar (240px, `--chrome-bg: #18181B`) displays 4 navigation items: Today's Queue, Collections, Dashboard, Settings — each with icon + label + optional badge (count)

2. **Given** the sidebar is visible **When** the user views the active nav item **Then** it is highlighted with `bg-zinc-800 text-zinc-50 font-medium`; hover state is `bg-zinc-800/50 text-zinc-200`

3. **Given** the app shell is loaded **When** the user views the topbar **Then** a 56px-height topbar displays: breadcrumb (left, format `TableProject / {Current Page}`), `⌘K` search trigger button (right), and user avatar placeholder (right)

4. **Given** the app shell is loaded **When** the user views the main content area **Then** it is max-width 720px and centered horizontally within the remaining space after the sidebar

5. **Given** the viewport is tablet-width (640–1024px) **When** the page loads **Then** the sidebar collapses to icon-only mode (56px wide) with tooltips on hover for each nav label

6. **Given** the viewport is mobile-width (<640px) **When** the page loads **Then** the sidebar is hidden; a hamburger button appears in the topbar; tapping it slides the sidebar in as an overlay with a backdrop

7. **Given** any navigation item in the sidebar **When** the user presses Tab to focus and Enter to activate **Then** the navigation works correctly; all nav items are keyboard accessible with visible focus indicators

8. **Given** the sidebar markup **When** inspected by a screen reader **Then** it uses `<nav>` landmark with `aria-label="Main navigation"`

## Tasks / Subtasks

- [x] Task 1: Create Sidebar component (AC: #1, #2, #5, #6, #7, #8)
  - [x] Create `src/components/layout/Sidebar.tsx`
  - [x] Implement dark sidebar with `#18181B` background, 240px width on desktop
  - [x] Add 4 nav items with lucide-react icons: CalendarCheck (Today's Queue), FolderOpen (Collections), BarChart3 (Dashboard), Settings (Settings)
  - [x] Each nav item: icon + label + optional badge prop
  - [x] Active state: `bg-zinc-800 text-zinc-50 font-medium`; hover: `bg-zinc-800/50 text-zinc-200`
  - [x] Use `usePathname()` from `next/navigation` to determine active item
  - [x] Wrap in `<nav aria-label="Main navigation">`
  - [x] Keyboard accessible: Tab + Enter navigation, visible focus indicators
  - [x] Tablet (640–1024px): collapse to 56px icon-only with Tooltip on hover
  - [x] Mobile (<640px): hidden by default, rendered as overlay via Sheet component

- [x] Task 2: Create Topbar component (AC: #3)
  - [x] Create `src/components/layout/Topbar.tsx`
  - [x] Height: 56px (`h-14`), dark background matching sidebar (`#18181B`)
  - [x] Left: hamburger button (mobile only) + breadcrumb (`TableProject / {Current Page}`)
  - [x] Right: `⌘K` search trigger button (disabled placeholder — command palette is Epic 3) + user avatar circle placeholder
  - [x] Breadcrumb text: `text-zinc-200 font-medium` for current page, `text-zinc-500` for parent

- [x] Task 3: Create AppShell layout component (AC: #4)
  - [x] Create `src/components/layout/AppShell.tsx`
  - [x] Compose Sidebar + Topbar + main content area
  - [x] Main content: `<main id="main-content">` with `max-w-[720px] mx-auto` centered in remaining space
  - [x] Use CSS Grid or Flexbox: sidebar (fixed) + right column (topbar stacked over scrollable content)

- [x] Task 4: Create app route group layout (AC: #1–#8)
  - [x] Create `src/app/(app)/layout.tsx` wrapping authenticated pages with AppShell
  - [x] Move current `page.tsx` content to `src/app/(app)/page.tsx` (or create a placeholder "Today's Queue" page)
  - [x] Ensure the root `layout.tsx` remains untouched (fonts, metadata, providers)
  - [x] Add routes for `/collections`, `/dashboard`, `/settings` as placeholder pages

- [x] Task 5: Install required shadcn/ui components
  - [x] Install Sheet component: `pnpm dlx shadcn@latest add sheet` (for mobile sidebar overlay)
  - [x] Verify Tooltip is already installed (needed for collapsed sidebar labels)

- [x] Task 6: Verify responsive behavior and accessibility (AC: #5, #6, #7, #8)
  - [x] Test desktop (>1024px): full sidebar + centered content
  - [x] Test tablet (640–1024px): icon-only sidebar
  - [x] Test mobile (<640px): hamburger → overlay sidebar
  - [x] Test keyboard navigation: Tab through all nav items, Enter to activate
  - [x] Verify `<nav>` landmark is present for screen readers
  - [x] Run `pnpm lint` and `tsc --noEmit` — no errors

## Dev Notes

### Technical Stack (Verified May 2026)

| Technology | Version | Notes |
|-----------|---------|-------|
| Next.js | 16.2.x | App Router, `usePathname()` for active route |
| React | 19.x | Shipped with Next.js 16 |
| Tailwind CSS | 4.2.x | CSS-only config, use existing design tokens |
| shadcn/ui | CLI v4 | Sheet for mobile sidebar overlay |
| lucide-react | Latest | Icons for nav items |

### Architecture Constraints — MUST FOLLOW

- **Component files**: PascalCase.tsx (`Sidebar.tsx`, `Topbar.tsx`, `AppShell.tsx`)
- **Location**: All layout components in `src/components/layout/`
- **One component per file**, named same as component
- **Import alias**: `@/*` mapping to `src/*`
- **No business logic in layout components** — only presentation and navigation state
- **Barrel export**: Update `src/components/layout/index.ts` to export all new components
- **Color values**: Use CSS custom properties from `globals.css` (e.g., `var(--chrome-bg)`) — never hardcode hex in components. Exception: zinc utility classes (`bg-zinc-800`, `text-zinc-200`) are acceptable for sidebar chrome since they match `--chrome-bg` family
- **Tailwind v4**: No `tailwind.config.ts` — all theme values defined in `globals.css` `@theme` block

### Sidebar Navigation Items (from UX Spec UX-DR11)

| # | Label | Icon (lucide-react) | Route | Badge |
|---|-------|-------------------|-------|-------|
| 1 | Today's Queue | `CalendarCheck` | `/` | Due card count (number, optional) |
| 2 | Collections | `FolderOpen` | `/collections` | — |
| 3 | Dashboard | `BarChart3` | `/dashboard` | — |
| 4 | Settings | `Settings` | `/settings` | — |

### Sidebar Visual Spec (from UX Spec)

```
Desktop (>1024px):
┌──────────────────────────────────────────────────────┐
│ ┌─────────┐ ┌────────────────────────────────────┐   │
│ │ SIDEBAR │ │ TOPBAR (56px, dark)                │   │
│ │ 240px   │ │ Breadcrumb    ⌘K  Avatar          │   │
│ │ dark    │ ├────────────────────────────────────┤   │
│ │         │ │                                    │   │
│ │ Queue ● │ │  Content Area (max 720px centered) │   │
│ │ Collect │ │                                    │   │
│ │ Dashbrd │ │                                    │   │
│ │ Setting │ │                                    │   │
│ │         │ │                                    │   │
│ └─────────┘ └────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘

Tablet (640–1024px):
┌─────────────────────────────────────┐
│ ┌──┐ ┌──────────────────────────┐   │
│ │56│ │ TOPBAR                   │   │
│ │px│ ├──────────────────────────┤   │
│ │  │ │ Content (fills avail.)   │   │
│ │🗓│ │                          │   │
│ │📁│ │                          │   │
│ │📊│ │                          │   │
│ │⚙│ │                          │   │
│ └──┘ └──────────────────────────┘   │
└─────────────────────────────────────┘

Mobile (<640px):
┌──────────────────┐
│ ☰ Topbar         │
├──────────────────┤
│ Content          │
│ (full width,     │
│  16px padding)   │
│                  │
└──────────────────┘
Hamburger → slide-in overlay sidebar with backdrop
```

### Sidebar Styling Details

- Background: `#18181B` (zinc-900, `--chrome-bg`)
- Internal borders: `#27272A` (zinc-800, `--chrome-border`)
- Nav text default: `#A1A1AA` (zinc-400, `--chrome-text`)
- Nav text active: `#FAFAFA` (zinc-50, `--chrome-text-active`)
- Active item bg: `bg-zinc-800` (lighter than sidebar bg)
- Hover item bg: `bg-zinc-800/50`
- Badge: `bg-zinc-700 text-zinc-50 text-xs font-semibold rounded-full px-2`
- Section header (if needed): `text-xs font-semibold text-zinc-500 uppercase tracking-wide`
- Focus indicator: `ring-2 ring-zinc-400 ring-offset-2 ring-offset-zinc-900` (offset matches sidebar bg)

### Topbar Styling Details

- Height: 56px (`h-14`)
- Background: `#18181B` matching sidebar
- Breadcrumb parent text: `text-zinc-500`
- Breadcrumb separator: `/` in `text-zinc-600`
- Breadcrumb current page: `text-zinc-200 font-medium`
- Search trigger: ghost button with `Search` icon + `⌘K` badge
- Avatar: 32px circle, `bg-zinc-700` placeholder

### Route Group Strategy

Use Next.js App Router route groups to separate app shell pages from non-shell pages:

```
src/app/
├── layout.tsx              # Root layout (fonts, metadata, providers) — DO NOT MODIFY
├── page.tsx                # Landing/marketing page (no app shell) — keep or redirect
├── (app)/
│   ├── layout.tsx          # AppShell wrapper (Sidebar + Topbar + content)
│   ├── page.tsx            # Today's Queue (default landing for authenticated users)
│   ├── collections/
│   │   └── page.tsx        # Placeholder
│   ├── dashboard/
│   │   └── page.tsx        # Placeholder
│   └── settings/
│       └── page.tsx        # Placeholder
```

Placeholder pages should show a centered heading with the page name and a brief "Coming soon" message using existing design tokens.

### Mobile Sidebar Implementation

Use shadcn/ui `Sheet` component (side="left") for mobile overlay:

```tsx
// Pattern — NOT exact code
<Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
  <SheetTrigger asChild>
    <Button variant="ghost" size="icon" className="lg:hidden">
      <Menu className="h-5 w-5" />
    </Button>
  </SheetTrigger>
  <SheetContent side="left" className="w-[240px] bg-[#18181B] p-0">
    <SidebarNav onNavigate={() => setMobileOpen(false)} />
  </SheetContent>
</Sheet>
```

Close the sheet when a nav item is clicked (call `setMobileOpen(false)` in onClick handler).

### Previous Story (1.2) Intelligence

- Frontend scaffold lives in `table-project-web/` directory
- shadcn/ui initialized with stone-based palette, NOT zinc (but sidebar chrome uses zinc scale per UX spec — this is intentional: content area = warm stone, app chrome = cool zinc)
- Tailwind v4 CSS-only config — all tokens in `globals.css` `@theme` block
- Font stack already configured: Inter + Noto Sans JP + JetBrains Mono via `next/font/google`
- Button has `primary`, `secondary`, `ghost` variants ready
- Existing `layout.tsx` has skip-to-content link and TooltipProvider
- Components installed: Button, Card, Skeleton, Badge, Tooltip
- `src/components/layout/index.ts` exists but is empty (`export {}`)
- Dev server runs on port 3100: `pnpm dev --hostname 127.0.0.1 --port 3100`
- `turbopack.root` set in `next.config.ts` to prevent workspace root inference
- Note from Story 1.2: "Next.js 16 scaffolds `eslint.config.mjs`" (not `.eslintrc.json`)

### Anti-Patterns to AVOID

- Do NOT create a `tailwind.config.ts` file — Tailwind v4 uses CSS-only config
- Do NOT use `next/link` with `<a>` children — Next.js 16 Link renders `<a>` automatically
- Do NOT implement authentication guards — auth is Epic 2 (Story 2.1)
- Do NOT implement the command palette — that is Epic 3 (Story 3.8). Only add a disabled `⌘K` trigger button placeholder
- Do NOT implement actual page content for collections/dashboard/settings — placeholder pages only
- Do NOT add state management (Zustand) — not needed for static nav, use `usePathname()` for active route
- Do NOT modify `src/app/layout.tsx` root layout — create a route group `(app)/layout.tsx` instead
- Do NOT put sidebar state in a global store — component-local `useState` for mobile open/close is sufficient
- Do NOT add badge counts yet — pass `badge?: number` prop but don't wire to real data
- Do NOT use `router.push()` for navigation — use `<Link>` from `next/link` for client-side nav with prefetching

### Accessibility Requirements

- Sidebar: `<nav aria-label="Main navigation">`
- Active nav item: `aria-current="page"`
- Hamburger button: `aria-label="Open navigation menu"`, `aria-expanded` reflecting state
- Skip-to-content link already exists in root layout — `#main-content` target must be on the `<main>` element in AppShell
- Focus indicators: `ring-2` with appropriate offset, only on `:focus-visible`
- Mobile overlay: Sheet handles focus trap and Esc to close automatically
- Tab order: sidebar items top-to-bottom, then topbar left-to-right

### CSS Additions Needed in globals.css

Add chrome-specific tokens to the `@theme` block and `:root` if not already present:

```css
/* Add to @theme inline block */
--color-chrome-bg: var(--chrome-bg);
--color-chrome-border: var(--chrome-border);
--color-chrome-text: var(--chrome-text);
--color-chrome-text-active: var(--chrome-text-active);

/* Add to :root */
--chrome-bg: #18181B;
--chrome-border: #27272A;
--chrome-text: #A1A1AA;
--chrome-text-active: #FAFAFA;

/* Add to .dark (same values — chrome is always dark) */
--chrome-bg: #18181B;
--chrome-border: #27272A;
--chrome-text: #A1A1AA;
--chrome-text-active: #FAFAFA;
```

### File Structure (Target — NEW files marked)

```
table-project-web/src/
├── app/
│   ├── globals.css               # UPDATE: add chrome tokens
│   ├── layout.tsx                # NO CHANGE
│   ├── page.tsx                  # NO CHANGE (or redirect to /app)
│   └── (app)/
│       ├── layout.tsx            # NEW: AppShell wrapper
│       ├── page.tsx              # NEW: Today's Queue placeholder
│       ├── collections/
│       │   └── page.tsx          # NEW: placeholder
│       ├── dashboard/
│       │   └── page.tsx          # NEW: placeholder
│       └── settings/
│           └── page.tsx          # NEW: placeholder
├── components/
│   └── layout/
│       ├── index.ts              # UPDATE: export Sidebar, Topbar, AppShell
│       ├── Sidebar.tsx           # NEW
│       ├── Topbar.tsx            # NEW
│       └── AppShell.tsx          # NEW
```

### References

- [Source: _out_put/planning-artifacts/epics/epic-1-project-foundation-developer-infrastructure.md#Story 1.3]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Navigation Patterns]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Responsive Strategy]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Accessibility Considerations]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Color System — chrome-bg, chrome-border, chrome-text]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend File Structure]
- [Source: _out_put/implementation-artifacts/1-2-initialize-frontend-scaffold.md]

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `pnpm exec next typegen`
- `pnpm lint`
- `pnpm exec tsc --noEmit`
- `pnpm build`
- Headless Playwright verification against a local `next start` instance on port `3202`

### Completion Notes List

- Implemented a responsive app shell with persistent desktop/tablet sidebar, mobile sheet overlay, and shared topbar breadcrumb/search/avatar chrome.
- Added route-group-backed placeholder pages for Today's Queue, Collections, Dashboard, and Settings without modifying the root `src/app/layout.tsx`.
- Added chrome design tokens in `globals.css` and a local `Sheet` UI primitive after the shadcn CLI prompted for interactive overwrites.
- Verified desktop, tablet, mobile, keyboard navigation, and nav landmark behavior with headless Playwright, plus lint, typecheck, and production build.

### File List

- `table-project-web/src/app/globals.css`
- `table-project-web/src/app/page.tsx` (deleted)
- `table-project-web/src/app/(app)/layout.tsx`
- `table-project-web/src/app/(app)/page.tsx`
- `table-project-web/src/app/(app)/collections/page.tsx`
- `table-project-web/src/app/(app)/dashboard/page.tsx`
- `table-project-web/src/app/(app)/settings/page.tsx`
- `table-project-web/src/components/layout/index.ts`
- `table-project-web/src/components/layout/AppShell.tsx`
- `table-project-web/src/components/layout/Sidebar.tsx`
- `table-project-web/src/components/layout/Topbar.tsx`
- `table-project-web/src/components/ui/sheet.tsx`
- `_out_put/implementation-artifacts/1-3-app-shell-layout.md`
- `_out_put/implementation-artifacts/sprint-status.yaml`
