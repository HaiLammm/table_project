# Web Application Specific Requirements

## Project-Type Overview

TableProject is a hybrid web application built on Next.js 16 App Router — combining server-side rendering for public-facing pages (landing, blog, SEO content) with single-page application behavior for the authenticated learning experience. The architecture prioritizes zero-friction onboarding, sub-200ms interactions during card review, and offline-capable vocabulary review via Progressive Web App (PWA) patterns.

## Browser Support Matrix

| Browser | Minimum Version | Priority |
|---------|----------------|----------|
| Chrome (Desktop) | Last 2 versions | Primary |
| Firefox (Desktop) | Last 2 versions | Primary |
| Safari (Desktop) | Last 2 versions | Primary |
| Edge (Desktop) | Last 2 versions | Primary |
| Chrome (Android) | Last 2 versions | Primary (mobile web) |
| Safari (iOS) | Last 2 versions | Primary (mobile web) |

No support required for: Internet Explorer, Opera Mini, or browsers older than 2 versions behind current stable release.

## Responsive Design

- **Desktop-first design** for the primary learning experience (Vietnam-based learners studying at home)
- **Mobile-responsive** for commute learners (Hùng persona — train in Tokyo). Card review, quick-add vocabulary, and dashboard summary must be fully functional on mobile viewport (≥375px width).
- **Breakpoints**: Mobile (375–767px), Tablet (768–1023px), Desktop (≥1024px)
- **Touch targets**: Minimum 44×44px for interactive elements on mobile (WCAG 2.1 AA)
- **No native mobile app** in MVP — responsive web + PWA is sufficient

## Performance Targets

| Metric | Target | Context |
|--------|--------|---------|
| Largest Contentful Paint (LCP) | < 2.5s | Landing page and dashboard |
| First Input Delay (FID) | < 100ms | Card review interaction |
| Cumulative Layout Shift (CLS) | < 0.1 | All pages |
| Time to Interactive (TTI) | < 3.5s | Dashboard after login |
| API response (non-LLM) | p95 < 200ms | FSRS review, collection CRUD |
| LLM streaming (TTFT) | < 800ms | Chat-based intent parser |
| Offline card review | Functional | PWA with IndexedDB cache |

## SEO Strategy

- **SEO-optimized pages**: Landing page, pricing page, blog/content marketing articles, public collection pages (future). Server-side rendered via Next.js App Router.
- **No SEO required**: Authenticated app experience (dashboard, card review, collections, settings). These are SPA routes behind authentication.
- **Content marketing SEO**: Vietnamese-language blog posts on SRS techniques, JLPT/TOEIC study strategies. Target thin-competition keywords in Vietnamese edtech niche.
- **Technical SEO**: Sitemap generation, structured data (JSON-LD), Open Graph meta tags for social sharing of diagnostic reports.

## Accessibility Level

- **Target**: WCAG 2.1 Level AA for core learning flows
- **Core flows requiring AA compliance**:
  - Card review (keyboard navigation: space to flip, 1-4 for difficulty rating)
  - Dashboard (screen reader compatible data visualizations, text alternatives for charts)
  - Onboarding (form labels, error messages, focus management)
  - Collection browsing and management
- **Keyboard navigation**: Full keyboard support for card review workflow — no mouse required for the primary learning loop
- **Screen reader**: ARIA labels for interactive components, live regions for dynamic content updates (review queue count, diagnostic alerts)
- **Color contrast**: Minimum 4.5:1 for normal text, 3:1 for large text. Retention status indicators (red/yellow/green) must also use shape/icon differentiation (not color alone)
- **Reduced motion**: Respect `prefers-reduced-motion` media query for animations and transitions

## Implementation Considerations

- **Rendering strategy**: Static Generation (SSG) for landing/blog pages, Server-Side Rendering (SSR) for dashboard initial load, Client-Side Rendering (CSR) for real-time card review interactions
- **PWA capability**: Service Worker for offline card review cache (IndexedDB stores due cards + FSRS state). Background Sync API for queuing reviews completed offline.
- **Bundle optimization**: Code splitting per route. Dictionary data (JMdict) loaded on-demand, not bundled. Lazy load dashboard charts and analytics components.
- **State management**: TanStack Query for server state (API data caching, optimistic updates). Local state for UI interactions. No global state library needed at MVP.
- **Image/asset strategy**: Minimal imagery — vocabulary cards are text-heavy. SVG for icons (shadcn/ui + Lucide). No heavy media assets in MVP.
