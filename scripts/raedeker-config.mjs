import { execFileSync } from 'node:child_process'
import { readFile, writeFile } from 'node:fs/promises'

// Keep the upstream resource-ID generator and apply this installation's profile.
execFileSync(process.execPath, ['scripts/cloudflare-deploy-config.mjs'], { stdio: 'inherit' })
const path = new URL('../wrangler.deploy.jsonc', import.meta.url)
const config = JSON.parse(await readFile(path, 'utf8'))
config.name = 'raedeker-links'
config.account_id = '9fd40fed9d563f740452a5f02c9defd7'
config.workers_dev = true
config.preview_urls = false
config.routes = [{ pattern: 'l.raedeker.eu', custom_domain: true }]
config.vars = {
  ...config.vars,
  NUXT_PUBLIC_PREVIEW_MODE: '',
  NUXT_PUBLIC_LINK_PROXY_ENABLED: 'false',
  NUXT_CASE_SENSITIVE: 'true',
  NUXT_REDIRECT_STATUS_CODE: '302',
  NUXT_REDIRECT_NO_STORE: 'true',
  NUXT_REDIRECT_WITH_QUERY: 'true',
  NUXT_DISABLE_BOT_ACCESS_LOG: 'true',
  NUXT_DISABLE_AUTO_BACKUP: 'true',
  NUXT_CF_ACCOUNT_ID: config.account_id,
  NUXT_DATASET: config.analytics_engine_datasets[0].dataset,
}
// AI and R2 are optional; enabling them is a separate operational choice.
delete config.ai
delete config.triggers
delete config.r2_buckets
await writeFile(path, `${JSON.stringify(config, null, 2)}\n`)
