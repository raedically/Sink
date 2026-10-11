# raedeker.eu short links

This fork runs Sink independently of the Julsprint Django application. It uses
Cloudflare Workers, D1 (authoritative links), KV (redirect cache), and Analytics
Engine. It does not use Northflank containers or PostgreSQL.

## Production status — 2026-10-11

The twelve `l.raedeker.eu` links have been imported and the domain is connected
to Sink. All twelve redirects were checked against the original Dub export,
including exact destinations, case and timestamps. HTTPS, unauthenticated API
rejection, and authenticated create/edit/delete operations passed on the new
production endpoint. Analytics ingestion and the dashboard were verified with
one synthetic test visit.

- Dashboard: <https://l.raedeker.eu/dashboard>
- Alternate dashboard during DNS propagation:
  <https://raedeker-links.nameless-fog-4c15.workers.dev/dashboard>
- Local checkout: `/Users/lbr/PycharmProjects/raedeker_links`
- Setup PR: <https://github.com/raedically/Sink/pull/1>
- Initial D1 backup: `private/sink-after-import-2026-10-11.sql`
- Verified production export: `private/sink-export-production.json`

Cloudflare's authoritative DNS and 1.1.1.1 return the Worker. Some local DNS
caches still return Dub because the previous record had a one-day TTL. Both
services retain the same twelve links during propagation. Avoid changing link
destinations until the old TTL has elapsed. The six `dub.sh` links stay at Dub.
Historic Dub statistics remain in the private export; Sink records new visits.

## Deployment profile

- Worker and D1 name: `raedeker-links`
- KV namespace: `raedeker-links-cache`
- Analytics dataset: `raedeker_links`
- Main domain: `l.raedeker.eu`
- Upstream baseline: `bafa4e1f7e3ec034929e11e5542c4c3e116d69da` (Sink 0.3.1)
- Node 24; pnpm version is pinned in `package.json`.
- Free Workers plan; optional AI and R2 features are disabled.
- Case-sensitive slugs preserve existing Dub links, including capital letters.
- Redirects use **302** and **Cache-Control: no-store**, allowing destinations to
  change without browsers permanently retaining an old destination.
- Incoming query parameters are forwarded, matching the previous Dub behavior.
- Demo mode, permissive API CORS, and reverse proxy links are disabled.
- API and dashboard access require the private administrator token.
- A separate **Account Analytics: Read** token allows statistics queries.

Additional custom domains can point to the same Worker, but all domains share
one slug namespace: `/example` has the same destination on every domain.
Independent link collections need independent instances and storage.

## Local setup and checks

```sh
corepack enable
pnpm install --frozen-lockfile
pnpm lint
pnpm types:check
NUXT_SITE_TOKEN=local-tests-only-change-me pnpm build
NUXT_SITE_TOKEN=local-tests-only-change-me pnpm test --run
python3 -m unittest discover -s scripts -p 'test_dub_to_sink.py' -v
```

The test token must match the build token. Tests explicitly disable remote
bindings and use local D1/KV/R2 simulation, without production credentials.
GitHub CI performs these checks; it does not deploy or receive production secrets.
The fork also fixes an upstream heatmap type annotation and declares Vue and
Vue I18n explicitly, using the same versions as the upstream lockfile.

## Deploy an update

Keep the local `.env` with `DEPLOY_D1_DATABASE_ID`, `DEPLOY_KV_NAMESPACE_ID`,
`DEPLOY_D1_DATABASE_NAME=raedeker-links`, and
`DEPLOY_ANALYTICS_DATASET=raedeker_links`. Set `NUXT_API_CORS=false` and leave
`NUXT_PUBLIC_PREVIEW_MODE` empty. Never commit resource exports or secrets.

After reviewing and testing an update:

```sh
pnpm build
pnpm deploy:raedeker
```

Deployment keeps `l.raedeker.eu` as a Worker custom domain, retains the stable
workers.dev address, and disables version preview URLs. It uses
`scripts/raedeker-config.mjs`, which generates ignored
`wrangler.deploy.jsonc`, applies D1 migrations, and uploads the Worker and assets.
Use **deploy:raedeker**, not upstream's generic deployment command. Existing
encrypted Worker secrets are preserved. An expired CLI session needs a fresh
Cloudflare login; the initial session intentionally has no offline refresh access.
Do not accept Wrangler's broad default scopes without reviewing them.

For a new Cloudflare account, Analytics Engine may need to be activated by
adding the `ANALYTICS` binding (dataset `raedeker_links`) in the Worker dashboard
and deploying that binding once. This resolved Cloudflare error 10089 during
initial setup; it is not needed on every deployment.

Git pushes alone currently run validation, not production deployment. Git-based
automatic deployment would require a separately scoped persistent deploy token.

## Secrets and 1Password

The private local `private/1password-zugangsdaten.txt` contains the dashboard
password and analytics API token, ready to copy into a Login and an API Credential
or Secure Note in 1Password. The directory is Git-ignored and owner-only.
Local copies are not a substitute for the password manager; remove unnecessary
plaintext copies once the items are safely stored. Do not share the administrator
token: it also authorizes API writes and exports.

Encrypted runtime secrets are `NUXT_SITE_TOKEN` and `NUXT_CF_API_TOKEN`.
The analytics token has read-only access to account analytics, no write access.
Revoking it stops dashboard statistics queries but does not break redirects.

## Dub migration and rollback

The private directory preserves the original CSV, a converted Sink JSON file,
and a baseline of the twelve live redirect destinations. The converter retains
case, exact destination query strings, and creation/update timestamps. It skips
the domain's empty root entry and the six `dub.sh` links. Those links must remain
at Dub because their domain is not ours.

Conversion is repeatable and refuses duplicate/reserved slugs, unsupported
destinations, archived links, or tags needing a reviewed mapping:

```sh
python3 scripts/dub-to-sink.py private/dub-links-before-migration.csv \
  private/sink-import-new.json --domain l.raedeker.eu
```

Dub's CSV does not contain every advanced routing or protection option. Check
these separately for any future migration. Historic click totals remain in the
private CSV; they are not fabricated as new Sink events.

Before switching DNS, import and verify every link on the Workers preview host,
verify unauthenticated API requests fail, and test destination editing. Keep the
Dub workspace and custom domain intact during DNS propagation.

The original DNS entry was a **DNS-only CNAME** `l.raedeker.eu` → `cname.dub.co`,
TTL 86400 (one day), comment `Dub.co configuration`. Its private backup is
`private/dns-before-migration.json`. To roll back, remove the Sink domain/route
association and restore that record. Do not modify apex, www, or mail records.

## Backups and statistics

Export links from the authenticated Sink dashboard after important changes.
Take a full D1 backup before updates:

```sh
pnpm deploy:raedeker:config
pnpm exec wrangler d1 export DB --remote --config wrangler.deploy.jsonc \
  --output private/links-backup-YYYY-MM-DD.sql
```

Store a copy somewhere independent of this Mac and Cloudflare. JSON imports
restore links, not all internal migration markers. D1 SQL exports are the full
database backup. R2 automatic backups are currently disabled; enabling R2 and
its billing setup is a separate decision.

Analytics Engine retains raw events for about three months. Long-term history
requires periodic exports or a later aggregation/archive feature. Detected bots
are excluded; anonymous metrics and geographic/device breakdowns still depend
on Cloudflare's signals. Link records themselves do not expire with analytics.

## Upstream updates

The `upstream` remote points to `miantiao-me/Sink`; `origin` is `raedically/Sink`.
Merge reviewed upstream changes into a branch, run CI, back up D1, and deploy.
Keep installation-specific changes confined to this profile where possible.
Consult upstream migration notes before database schema changes.
