# Story 1.2: Initialize Frontend Scaffold with Next.js 16 & shadcn/ui

Status: review

## Story

As a **developer**,
I want a fully configured Next.js 16 App Router frontend with shadcn/ui, Tailwind CSS v4, TypeScript strict mode, and the project file structure,
so that all frontend development starts from a consistent, accessible foundation.

## Acceptance Criteria

1. **Given** the frontend directory does not exist **When** the developer runs `create-next-app` and `shadcn/ui init` **Then** the project is created with TypeScript, Tailwind, ESLint, App Router, src directory

2. **Given** the project is initialized **When** shadcn/ui is initialized **Then** it uses the project theme configuration (warm stone-based palette, not default zinc)

3. **Given** the project is initialized **When** the developer inspects `globals.css` **Then** the warm stone-based monochromatic design system CSS custom properties are configured:
   - `--background`, `--surface`, `--surface-hover`, `--border`, `--text-primary`, `--text-secondary`, `--text-muted`, `--accent`, `--accent-hover`, `--accent-subtle`
   - Rating feedback colors: `--rating-again`, `--rating-hard`, `--rating-good`, `--rating-easy`
   - Status colors: `--success`, `--warning`, `--error`, `--info`
   - Both light and dark mode values per UX spec

4. **Given** the project is initialized **When** the developer inspects font configuration **Then** the multi-script font stack is configured:
   - Inter Variable (Latin + Vietnamese)
   - Noto Sans JP Variable (Japanese)
   - JetBrains Mono (IPA/code)
   - CSS `unicode-range` for automatic script switching

5. **Given** the project is initialized **When** the developer inspects responsive config **Then** breakpoints are configured: mobile (<640px), tablet (640-1024px), desktop (>1024px)

6. **Given** shadcn/ui is installed **When** the developer checks available components **Then** the 3-tier button hierarchy is available (Primary/Secondary/Ghost variants)

7. **Given** the project is initialized **When** the developer checks for loading patterns **Then** Skeleton loading component from shadcn/ui is installed and ready to use

8. **Given** the project is initialized **When** the developer inspects the directory structure **Then** it matches: `components/ui/`, `components/review/`, `components/layout/`, `hooks/`, `stores/`, `lib/`, `types/`

9. **Given** the project is initialized **When** one page renders **Then** it displays a shadcn/ui component with design tokens applied correctly

10. **Given** the project is initialized **When** `pnpm lint` and `tsc --noEmit` are run **Then** ESLint and TypeScript compilation pass without errors

## Tasks / Subtasks

- [x] Task 1: Create Next.js 16 project (AC: #1)
  - [x] Run `pnpm create next-app table-project-web --typescript --tailwind --eslint --app --src-dir`
  - [x] Verify App Router with `src/app/` directory structure created
  - [x] Verify TypeScript strict mode in `tsconfig.json`

- [x] Task 2: Initialize shadcn/ui (AC: #2, #6, #7)
  - [x] Run `npx shadcn@latest init` with project theme (stone-based palette, not default zinc)
  - [x] Install core components: `npx shadcn@latest add button card skeleton badge tooltip`
  - [x] Verify Button has Primary/Secondary/Ghost variants
  - [x] Verify Skeleton component is available

- [x] Task 3: Configure design system tokens in CSS (AC: #3, #5)
  - [x] **CRITICAL — Tailwind v4 uses CSS-only config, NOT `tailwind.config.ts`**
  - [x] Configure all semantic color tokens in `globals.css` using `@theme` directive (Tailwind v4 pattern)
  - [x] Add light mode tokens under `:root`
  - [x] Add dark mode tokens under `.dark` class
  - [x] Add rating feedback color tokens
  - [x] Add status color tokens (success, warning, error, info)
  - [x] Configure responsive breakpoints (Tailwind v4 default breakpoints: sm=640px, lg=1024px suffice)
  - [x] Set max-content-width: 720px
  - [x] Set sidebar-width: 240px, sidebar-collapsed: 56px

- [x] Task 4: Configure typography and fonts (AC: #4)
  - [x] Add Inter Variable font (via `next/font/google` or local woff2)
  - [x] Add Noto Sans JP Variable font
  - [x] Add JetBrains Mono font
  - [x] Configure CSS `@font-face` with `unicode-range` for automatic script switching:
    - Inter: Latin, Vietnamese ranges (`U+0000-024F, U+1E00-1EFF, U+0300-036F`)
    - Noto Sans JP: CJK ranges (`U+3000-9FFF, U+F900-FAFF, U+FF00-FFEF`)
    - JetBrains Mono: only for `.font-mono` class
  - [x] Configure type scale matching UX spec (display/h1/h2/h3/body/body-sm/caption/vocab-term/vocab-reading/vocab-definition)
  - [x] Add bilingual typography rule: JP text +2px line-height adjustment

- [x] Task 5: Create frontend directory structure (AC: #8)
  - [x] Create `src/components/ui/` (shadcn/ui auto-generates here)
  - [x] Create `src/components/review/` with `index.ts`
  - [x] Create `src/components/collections/` with `index.ts`
  - [x] Create `src/components/dashboard/` with `index.ts`
  - [x] Create `src/components/onboarding/` with `index.ts`
  - [x] Create `src/components/layout/` with `index.ts`
  - [x] Create `src/hooks/`
  - [x] Create `src/stores/`
  - [x] Create `src/lib/` with `utils.ts` (cn() helper from shadcn/ui)
  - [x] Create `src/types/`

- [x] Task 6: Create initial page with design tokens (AC: #9)
  - [x] Create a landing/placeholder page in `src/app/page.tsx`
  - [x] Use shadcn/ui Button and Card components
  - [x] Verify design tokens (colors, fonts, spacing) render correctly
  - [x] Verify font switching works: Latin text uses Inter, Japanese text uses Noto Sans JP

- [x] Task 7: Verify build and lint (AC: #10)
  - [x] Run `pnpm lint` — passes
  - [x] Run `tsc --noEmit` — passes
  - [x] Run `pnpm build` — builds successfully

## Dev Notes

### CRITICAL: Tailwind CSS v4 Breaking Change

Tailwind CSS v4 (shipped with Next.js 16) **no longer uses `tailwind.config.ts`**. Configuration is now CSS-only using `@theme` directive:

```css
/* globals.css */
@import "tailwindcss";

@theme {
  --color-accent: #2563EB;
  --color-surface: #FFFFFF;
  /* ... all custom tokens here */
}
```

Do NOT create a `tailwind.config.ts` file. All tokens go in CSS. If upgrading from an existing config, use `npx @tailwindcss/upgrade@next`.

### CRITICAL: Color Palette is Stone, NOT Zinc

The architecture doc mentions "zinc-based" palette but the UX spec (which is the authoritative source for design) specifies **warm stone tones** (Tailwind `stone` scale). Use UX spec values:

- Background: `#FAFAF9` (stone-50) / Dark: `#1C1C1E`
- Surface: `#FFFFFF` / Dark: `#2C2C2E`
- Border: `#E7E5E4` (stone-200) / Dark: `#3A3A3C`
- Text primary: `#1C1917` (stone-900) / Dark: `#FAFAF9`
- Text secondary: `#78716C` (stone-500) / Dark: `#A8A29E`
- Text muted: `#A8A29E` (stone-400) / Dark: `#78716C`
- Accent: `#2563EB` (blue-600) / Dark: `#3B82F6`

### Previous Story (1.1) Intelligence

Story 1.1 created the backend scaffold. Key learnings for this story:
- Project root is `table_project/` — frontend goes in `table-project-web/` subdirectory (sibling to `backend/`)
- Monorepo structure: both frontend and backend at project root level
- `docker-compose.yml` already exists in `backend/` for Postgres + Redis
- No shared code between frontend and backend yet

### Technical Stack (Verified May 2026)

| Technology | Version | Notes |
|-----------|---------|-------|
| Next.js | 16.2.x | Stable, Turbopack default, React Compiler stable |
| React | 19.x | Shipped with Next.js 16 |
| Tailwind CSS | 4.2.x | **CSS-only config** — no tailwind.config.ts |
| shadcn/ui | CLI v4 | March 2026, supports presets |
| TypeScript | 5.x strict | Shipped with create-next-app |
| pnpm | Latest | Package manager per architecture |

### Font Loading Strategy

Use `next/font` for optimal loading (auto-subsetting, self-hosting, no layout shift):

```tsx
// src/app/layout.tsx
import { Inter, Noto_Sans_JP, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin', 'vietnamese'],
  variable: '--font-inter',
  display: 'swap',
});

const notoSansJP = Noto_Sans_JP({
  subsets: ['latin'],
  variable: '--font-noto-jp',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});
```

Then in CSS, configure `unicode-range` for automatic script switching:

```css
:root {
  --font-sans: var(--font-inter), var(--font-noto-jp), system-ui, sans-serif;
  --font-mono: var(--font-mono), 'Fira Code', monospace;
}
```

### CSS Custom Properties Pattern (Tailwind v4)

```css
/* src/app/globals.css */
@import "tailwindcss";

@theme {
  /* Spacing */
  --spacing-sidebar: 240px;
  --spacing-sidebar-collapsed: 56px;
  --spacing-topbar: 56px;
  --spacing-content-max: 720px;
}

:root {
  --background: #FAFAF9;
  --surface: #FFFFFF;
  --surface-hover: #F5F5F4;
  --border: #E7E5E4;
  --text-primary: #1C1917;
  --text-secondary: #78716C;
  --text-muted: #A8A29E;
  --accent: #2563EB;
  --accent-hover: #1D4ED8;
  --accent-subtle: #EFF6FF;
  
  /* Rating feedback */
  --rating-again: #FEF2F2;
  --rating-hard: #FFFBEB;
  --rating-good: #F0FDF4;
  --rating-easy: #EFF6FF;
  
  /* Status */
  --success: #16A34A;
  --warning: #D97706;
  --error: #DC2626;
  --info: #2563EB;
}

.dark {
  --background: #1C1C1E;
  --surface: #2C2C2E;
  --surface-hover: #3A3A3C;
  --border: #3A3A3C;
  --text-primary: #FAFAF9;
  --text-secondary: #A8A29E;
  --text-muted: #78716C;
  --accent: #3B82F6;
  --accent-hover: #60A5FA;
  --accent-subtle: #1E3A5F;
  
  --rating-again: #3B1C1C;
  --rating-hard: #3B2E1C;
  --rating-good: #1C3B2E;
  --rating-easy: #1C2E3B;
  
  --success: #4ADE80;
  --warning: #FBBF24;
  --error: #F87171;
  --info: #60A5FA;
}
```

### Type Scale CSS

```css
/* Add to globals.css */
.text-display { font-size: 1.875rem; line-height: 1.2; font-weight: 700; }
.text-vocab-term { font-size: 1.25rem; line-height: 1.4; font-weight: 600; }
.text-vocab-reading { font-size: 1rem; line-height: 1.5; font-weight: 400; }
.text-vocab-definition { font-size: 1rem; line-height: 1.6; font-weight: 400; }

/* Bilingual adjustment: JP text gets extra line-height */
[lang="ja"] { line-height: calc(1em + 2px); }
```

### Frontend File Structure (Target)

```
table-project-web/
├── package.json
├── pnpm-lock.yaml
├── next.config.ts
├── tsconfig.json
├── components.json          # shadcn/ui config
├── .env.local.example
├── .eslintrc.json
├── public/
│   └── icons/
│       └── favicon.ico
├── src/
│   ├── app/
│   │   ├── globals.css      # Tailwind v4 + design tokens + font-face
│   │   ├── layout.tsx       # Root: fonts, metadata
│   │   └── page.tsx         # Placeholder with design token demo
│   ├── components/
│   │   ├── ui/              # shadcn/ui generated (Button, Card, Skeleton, etc.)
│   │   ├── review/
│   │   │   └── index.ts     # Barrel export (empty for now)
│   │   ├── collections/
│   │   │   └── index.ts
│   │   ├── dashboard/
│   │   │   └── index.ts
│   │   ├── onboarding/
│   │   │   └── index.ts
│   │   └── layout/
│   │       └── index.ts
│   ├── hooks/
│   ├── stores/
│   ├── lib/
│   │   └── utils.ts         # cn() helper from shadcn/ui
│   └── types/
```

### Architecture Constraints — MUST FOLLOW

- **Component files**: PascalCase.tsx (e.g., `ReviewCard.tsx`)
- **Hook files**: camelCase.ts with `use` prefix (e.g., `useReviewSession.ts`)
- **Barrel exports**: `index.ts` per feature folder
- **One component per file**, named same as component
- **Tests co-located**: `.test.tsx` next to `.tsx`
- **No business logic in `components/ui/`** — only shadcn/ui primitives
- **Import alias**: `@/*` mapping to `src/*`

### Anti-Patterns to AVOID

- Do NOT create `tailwind.config.ts` — Tailwind v4 uses CSS-only config
- Do NOT use zinc palette — use stone (warm) palette per UX spec
- Do NOT use yarn or npm — use pnpm per architecture
- Do NOT self-host fonts in `public/fonts/` — use `next/font/google` for auto-optimization
- Do NOT put business logic in UI components
- Do NOT skip empty barrel `index.ts` files — they set up the import pattern
- Do NOT hardcode color values in components — always use CSS custom properties
- Do NOT create a global state store yet — that's for later stories (Zustand)

### Accessibility Requirements (from UX spec)

- Focus indicators: 2px blue outline (`--accent`) with 2px offset on all focusable elements
- Minimum touch target: 44x44px
- All text rem-based, scales with browser font-size
- `prefers-reduced-motion` respected for animations
- `prefers-color-scheme` for dark mode detection
- Skip-to-content link in layout

### References

- [Source: _out_put/planning-artifacts/architecture.md#Selected Frontend Starter]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend File Structure]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Color System]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Typography System]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Spacing & Layout Foundation]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Accessibility Considerations]
- [Source: _out_put/planning-artifacts/epics/epic-1-project-foundation-developer-infrastructure.md#Story 1.2]

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `pnpm create next-app@latest table-project-web --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-pnpm --yes`
- `pnpm dlx shadcn@latest init -y --template next --base radix --no-monorepo --preset nova`
- `pnpm dlx shadcn@latest add button card skeleton badge tooltip -y`
- `pnpm lint`
- `pnpm exec tsc --noEmit`
- `pnpm build`
- `pnpm dev --hostname 127.0.0.1 --port 3100`
- `rg -n "unicode-range|inter_|noto_sans_jp|jetbrains_mono" .next`

### Completion Notes List

- Initialized `table-project-web/` with Next.js 16 App Router, TypeScript strict mode, Tailwind CSS v4, ESLint, and the `src/` directory structure.
- Initialized `shadcn/ui`, switched the theme base color to `stone`, installed `button`, `card`, `skeleton`, `badge`, and `tooltip`, and updated `Button` to expose explicit `primary`, `secondary`, and `ghost` variants with 44px touch targets.
- Replaced the default starter styling with a warm stone design system in `src/app/globals.css`, including semantic light/dark tokens, rating/status tokens, responsive breakpoint/theme spacing values, reduced-motion handling, and focus-visible styling.
- Configured Inter, Noto Sans JP, and JetBrains Mono through `next/font/google`, mapped them into the shared font stack, added the requested type scale helpers, and verified Next emitted `@font-face` rules with `unicode-range` in the build output.
- Built a placeholder landing page using shadcn/ui `Badge`, `Button`, `Card`, `Skeleton`, and `Tooltip`, plus a skip link and bilingual sample copy to verify design tokens and font switching.
- Set `turbopack.root` in `next.config.ts` to keep Next.js 16 from inferring an external workspace root because of unrelated lockfiles outside this repo.
- Note: Next.js 16 currently scaffolds `eslint.config.mjs` and `src/app/favicon.ico` rather than the older `.eslintrc.json` and `public/icons/favicon.ico` shapes referenced in the target structure notes.

### File List

- `table-project-web/.gitignore`
- `table-project-web/AGENTS.md`
- `table-project-web/CLAUDE.md`
- `table-project-web/README.md`
- `table-project-web/components.json`
- `table-project-web/eslint.config.mjs`
- `table-project-web/next-env.d.ts`
- `table-project-web/next.config.ts`
- `table-project-web/package.json`
- `table-project-web/pnpm-lock.yaml`
- `table-project-web/pnpm-workspace.yaml`
- `table-project-web/postcss.config.mjs`
- `table-project-web/public/file.svg`
- `table-project-web/public/globe.svg`
- `table-project-web/public/next.svg`
- `table-project-web/public/vercel.svg`
- `table-project-web/public/window.svg`
- `table-project-web/src/app/favicon.ico`
- `table-project-web/src/app/globals.css`
- `table-project-web/src/app/layout.tsx`
- `table-project-web/src/app/page.tsx`
- `table-project-web/src/components/collections/index.ts`
- `table-project-web/src/components/dashboard/index.ts`
- `table-project-web/src/components/layout/index.ts`
- `table-project-web/src/components/onboarding/index.ts`
- `table-project-web/src/components/review/index.ts`
- `table-project-web/src/components/ui/badge.tsx`
- `table-project-web/src/components/ui/button.tsx`
- `table-project-web/src/components/ui/card.tsx`
- `table-project-web/src/components/ui/skeleton.tsx`
- `table-project-web/src/components/ui/tooltip.tsx`
- `table-project-web/src/hooks/.gitkeep`
- `table-project-web/src/lib/utils.ts`
- `table-project-web/src/stores/.gitkeep`
- `table-project-web/src/types/.gitkeep`
- `table-project-web/tsconfig.json`

### Change Log

- 2026-05-05: Implemented Story 1.2 frontend scaffold with Next.js 16, shadcn/ui, Tailwind v4 design tokens, bilingual typography, and validation checks.
