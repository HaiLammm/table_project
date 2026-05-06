# Table Project Web

## Local Development

1. Copy `.env.local.example` to `.env.local`.
2. Install dependencies with `pnpm install --frozen-lockfile`.
3. Start the app with `pnpm dev --hostname 127.0.0.1 --port 3100`.
4. Open `http://127.0.0.1:3100`.

## Quality Gates

- Lint: `pnpm lint`
- Type check: `pnpm exec tsc --noEmit`
- Tests: `pnpm test`
- Production build: `pnpm build`

The GitHub Actions workflow at `.github/workflows/ci-frontend.yml` runs the same checks on pushes and pull requests that touch `frontend/**`.

## Vercel Deployment

Vercel should be configured from the dashboard with this repository connected to GitHub.

- Framework preset: Next.js
- Root directory: `frontend`
- Install command: `pnpm install --frozen-lockfile`
- Build command: `pnpm build`
- Output directory: `.next`
- Node.js version: `22.x`

### Required Vercel environment variables

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`

Preview deployments are created automatically for pull requests once the project is linked in Vercel.
