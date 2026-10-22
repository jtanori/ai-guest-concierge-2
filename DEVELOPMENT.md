# Development Setup

One-command dev environment:

```bash
pnpm setup
pnpm dev
```

`pnpm setup` = `pnpm install` + `supabase db reset` (starts local Supabase, applies
`supabase/migrations/`, then `supabase/seeds/`).

## Prerequisites

- Node.js >= 20 (`package.json` `engines` enforces it)
- pnpm 11 (`packageManager` pin — corepack handles it)
- Supabase CLI **installed globally** (ADR-0003 amendment: not a devDependency —
  the binary is large and platform-specific; CI uses `supabase/setup-cli@v1`):
  - macOS: `brew install supabase/tap/supabase`
  - Windows: `scoop bucket add supabase https://github.com/supabase/scoop-bucket.git`; `scoop install supabase`
  - Linux: see https://supabase.com/docs/guides/local-dev/cli/getting-started
  - Requires Docker running (`supabase start` runs Postgres/Auth/Storage/etc. in containers).

## Environment

```bash
cp .env.example .env.local
```

Fill in the two Supabase values from `pnpm db:status` (URL + anon key). Leave
Sentry and LLM keys blank locally — code degrades gracefully without them.

- Local Supabase runs on the **544xx port range** (`supabase/config.toml`) because
  54321/54322 are occupied by the founder's other local Supabase project.
- Local analytics (Logflare) is disabled on Windows (needs Docker on
  tcp://localhost:2375); it works normally in cloud.
- `SUPABASE_SERVICE_ROLE_KEY` is **server-only** (webhook/queue workers).
  `pnpm check:security` fails the build if it's referenced outside `src/lib/server/`.

First run: `pnpm setup` may take a while (Docker image pulls + DB init). If
`supabase start` is interrupted mid-initdb, run `supabase stop --no-backup` then
`supabase start` again.

## Daily commands

| Command | What it does |
| --- | --- |
| `pnpm dev` | Next.js dev server (Turbopack) on :3000 |
| `pnpm lint` / `pnpm typecheck` | ESLint (flat config) / `tsc --noEmit` |
| `pnpm test` | Vitest (one-shot) |
| `pnpm check:security` | CI security gates, locally |
| `pnpm db:reset` | Recreate local DB: drop, migrate, seed |
| `pnpm db:status` | Print local Supabase URLs + keys |
| `pnpm build` | Production build |

## CI (`.github/workflows/ci.yml`)

Every PR runs: lint, typecheck, vitest, security gates, production build,
`supabase db reset` (schema is migratable from empty), and a **negative
control** proving the security gate fails on an injected violation.

`main` is protected: PRs required, status checks required, **zero human
approvals** — CI is the approver.
