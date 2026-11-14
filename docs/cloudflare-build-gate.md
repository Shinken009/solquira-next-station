# Cloudflare Pages build gate — supplemental, not the NASA deployment

**Purpose:** replace GitHub Actions for browser/frontend build verification while GitHub reports
`The job was not started because your account is locked due to a billing issue.`

**Canonical, NASA-submitted production:** https://solquira-next-station.vercel.app  
**Do not change this URL** to a Cloudflare Pages `pages.dev` preview until authentication,
NASA POWER proxy, sessions, CSRF, geospatial assets and Field Shift HTTP evaluations have
been fully ported and independently tested. The existing Python Vercel Function
`api/field_shift.py` **does not run natively on Pages**.

## Cloudflare Pages setup (one-time account authorization)

1. Open https://dash.cloudflare.com/ → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
2. Authorize the Cloudflare GitHub App for the **Shinken009/solquira-next-station** repository.
   This is a separate integration from GitHub Actions. The GitHub Actions billing lock
   does not run or pay for Cloudflare's own builds.
3. Select this repository with **production branch `main`**, and set the following settings.

| Cloudflare setting | Exact value |
|---|---|
| Framework preset | None (custom build) |
| Root directory | Repository root (leave unset) |
| Build command | `pnpm install --frozen-lockfile && pnpm run typecheck && pnpm --filter @workspace/solquira build` |
| Output directory | `artifacts/solquira/dist/public` |
| Environment variable `NODE_VERSION` | `22.23.4` |
| Environment variable `PNPM_VERSION` | `11.0.0` |

The lockfile and package manifests live at the monorepo root, so **do not change the root
directory to `artifacts/solquira`**. The Cloudflare Pages v3 image default pnpm
version is older than this repository's locked `pnpm@11.0.0`; pin the exact value.
The GitHub integration builds on Cloudflare's own infrastructure, shows
logs and status checks, and requires no GitHub Actions runner.

## What the resulting signal proves

**PASS** verifies a frozen, reproducible Node install, TypeScript typecheck,
and a full production frontend build with Cesium static assets. **It does not
prove** the Python Vercel Function, Akamai delegated authentication/CSRF,
NASA POWER HTTP availability or visual/browser correctness.

- Use Vercel's production and function logs and the real end-to-end browser
  test for these.
- For scientific Python regressions, run the independent isolated test suite
  outside GitHub Actions:
  `python -m pip install -r artifacts/solquira/backend/requirements.lock.txt`,
  install the test-only optional `numpy>=2.0,<3`, and
  `python -m unittest discover -s artifacts/solquira/backend -p 'test_*.py'`.
- In the latest independent validation, 386 Python tests and the frontend
  build/typecheck passed; Next Station's live Coquimbo and Chiloé comparisons
  returned HTTP 200 with NASA historical evidence.

## Release gate checklist

- [ ] Cloudflare Pages build succeeds with exact `main` commit.
- [ ] Vercel production remains `READY` at the same reviewed commit.
- [ ] Anonymous browser opens the Vercel domain without password or login.
- [ ] Studio bootstrap + territory confirmation + CSRF-protected Field Shift
      evaluation each work in an anonymous session.
- [ ] Both Coquimbo and Chiloé NASA POWER comparisons show source provenance,
      complete-window controls and unverified illustrative assumptions.
- [ ] Public NASA submission uses the **Vercel production URL** until a
      separate, fully authenticated Cloudflare backend migration is validated.

## References

- Cloudflare Pages Git integration: https://developers.cloudflare.com/pages/configuration/git-integration/
- Cloudflare Pages build image and pnpm version: https://developers.cloudflare.com/pages/configuration/build-image/
- Cloudflare Pages build settings: https://developers.cloudflare.com/pages/configuration/build-configuration/
