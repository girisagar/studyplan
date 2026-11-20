// End-to-end check of the offline features (Playwright + Chromium) against a
// production build (`npm run build && npm run preview`) and a running backend.
// It creates progress for E2E_USER: point it at a throwaway database, never at
// real data.
//
//   BASE=http://localhost:8083 E2E_USER=e2e E2E_PASS=... RESOURCE_ID=2 npm run e2e
import { chromium } from 'playwright'

const BASE = process.env.BASE ?? 'http://localhost:8083'
const USER = process.env.E2E_USER ?? 'e2e'
const PASS = process.env.E2E_PASS ?? 'e2e-pass-123'
const RESOURCE_ID = process.env.RESOURCE_ID ?? '2'
const SHOTS = process.env.SHOTS // optional folder for screenshots

let failures = 0
const check = (name, ok, detail = '') => {
  if (!ok) failures++
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`)
}
const shot = async (page, name, fullPage = true) =>
  SHOTS && page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage })

const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } })
// Newer browsers return a Promise from scroll methods; an effect that returns
// it crashes React on the next route change. Simulate that everywhere.
await context.addInitScript(() => {
  const scrollTo = window.scrollTo.bind(window)
  window.scrollTo = (...args) => (scrollTo(...args), Promise.resolve())
})
const page = await context.newPage()
page.on('pageerror', (error) => check('no uncaught page errors', false, error.message))

// Sign in, wait for the first sync to make the data available offline.
await page.goto(`${BASE}/login`)
await page.getByLabel('Username').fill(USER)
await page.getByLabel('Password').fill(PASS)
await page.getByRole('button', { name: 'Sign in' }).click()
await page.waitForURL(`${BASE}/`)
// Synced = the user's own progress data has arrived (not just public data).
await page.waitForFunction(async () => {
  const db = await new Promise((resolve) => {
    const request = indexedDB.open('studyplan')
    request.onsuccess = () => resolve(request.result)
  })
  const entry = await new Promise((resolve) => {
    const request = db.transaction('cache').objectStore('cache').get('/progress/enrollments')
    request.onsuccess = () => resolve(request.result)
  })
  return !!entry && !!localStorage.getItem('studyplan.lastSync')
}, null, { timeout: 30_000 })
check('signed in and synced', true)

await page.waitForFunction(async () => (await navigator.serviceWorker.ready).active !== null)
await page.reload() // let the service worker control the page
check('service worker controls the page', await page.evaluate(() => !!navigator.serviceWorker.controller))

// Follow the first roadmap (online).
await page.goto(`${BASE}/roadmaps`)
const firstRoadmap = page.locator('.roadmap-card a.roadmap-card-title').first()
const roadmapHref = await firstRoadmap.getAttribute('href')
await page.goto(`${BASE}${roadmapHref}`)
const start = page.getByRole('button', { name: 'Start this roadmap' })
if (await start.isVisible()) await start.click()
await page.waitForFunction(async () => {
  const db = await new Promise((resolve) => {
    const request = indexedDB.open('studyplan')
    request.onsuccess = () => resolve(request.result)
  })
  const count = await new Promise((resolve) => {
    const request = db.transaction('outbox').objectStore('outbox').count()
    request.onsuccess = () => resolve(request.result)
  })
  return count === 0
}, null, { timeout: 15_000 })
check('follow synced to the server', true)

// Download a PDF for offline use.
await page.goto(`${BASE}/library/${RESOURCE_ID}`)
await page.getByRole('button', { name: 'Download for offline use' }).click()
await page.locator('.offline-row', { hasText: 'Available offline' }).waitFor({ timeout: 60_000 })
check('PDF downloaded for offline use', true)

// ---- Offline ----
await context.setOffline(true)
await page.reload()
await page.getByText("You're offline").waitFor()
check('app shell loads offline', true)

await page.goto(`${BASE}${roadmapHref}`).catch(() => {})
await page.locator('.week').first().waitFor()
check('roadmap outline available offline', (await page.locator('.week').count()) > 0)

const continueLink = page.locator('a.btn-primary', { hasText: /Start|Continue/ }).first()
await continueLink.click()
await page.locator('.player-topic .topic-title').waitFor()
const topicTitle = await page.locator('.player-topic .topic-title').innerText()
check('course player shows topic content offline', (await page.locator('.player-topic .rich').count()) > 0, topicTitle)

const before = await page.locator('.player-outline-head .ring-label').innerText()
await page.getByRole('button', { name: 'Mark as complete' }).click()
const shownImmediately = await page.getByText('Not synced yet').isVisible()
await page.getByText('Not synced yet').waitFor()
check('offline change shows "not synced" only after the sync attempt fails', !shownImmediately)
const after = await page.locator('.player-outline-head .ring-label').innerText()
check('completion recorded offline and shown as pending', true, `course progress ${before} -> ${after}`)
const completedTopicId = Number(new URL(page.url()).searchParams.get('topic'))
await shot(page, 'player-offline')

await page.goto(`${BASE}/progress`).catch(() => {})
await page.locator('.stat-value').first().waitFor()
check('progress page reflects offline completion', (await page.locator('.stat-value').first().innerText()) !== '0')

await page.goto(`${BASE}/library/${RESOURCE_ID}/read`).catch(() => {})
await page.locator('.pdf-page canvas').first().waitFor({ timeout: 30_000 })
await page.waitForTimeout(1500)
const painted = await page.locator('.pdf-page canvas').first().evaluate((canvas) => canvas.width > 0)
check('downloaded PDF opens in the reader offline', painted, await page.locator('.pdf-toolbar span').first().innerText())
await shot(page, 'reader-offline', false)

await page.goto(`${BASE}/library?saved=1`).catch(() => {})
await page.locator('.resource').first().waitFor()
check('library "Downloaded" filter works offline', (await page.locator('.resource').count()) === 1)

// ---- Back online: the pending completion is pushed ----
await context.setOffline(false)
await page.evaluate(() => window.dispatchEvent(new Event('online')))
await page.waitForFunction(async () => {
  const db = await new Promise((resolve) => {
    const request = indexedDB.open('studyplan')
    request.onsuccess = () => resolve(request.result)
  })
  const count = await new Promise((resolve) => {
    const request = db.transaction('outbox').objectStore('outbox').count()
    request.onsuccess = () => resolve(request.result)
  })
  return count === 0
}, null, { timeout: 15_000 })
const serverHasIt = await page.evaluate(async (topicId) => {
  const { access } = JSON.parse(localStorage.getItem('studyplan.session'))
  const response = await fetch('/api/progress/completions', { headers: { Authorization: `Bearer ${access}` } })
  return (await response.json()).some((r) => r.topic_id === topicId)
}, completedTopicId)
check('offline completion synced to the server on reconnect', serverHasIt, `topic ${completedTopicId}`)

// Online: a change syncs without ever showing "not synced".
await page.goto(`${BASE}${roadmapHref}`)
await page.locator('a.btn-primary', { hasText: /Start|Continue/ }).first().click()
await page.getByRole('button', { name: 'Mark as complete' }).waitFor()
let sawUnsynced = false
const watch = setInterval(async () => {
  if (await page.getByText('Not synced yet').isVisible().catch(() => false)) sawUnsynced = true
}, 50)
await page.getByRole('button', { name: 'Mark as complete' }).click()
await page.waitForFunction(async () => {
  const db = await new Promise((resolve) => {
    const request = indexedDB.open('studyplan')
    request.onsuccess = () => resolve(request.result)
  })
  const count = await new Promise((resolve) => {
    const request = db.transaction('outbox').objectStore('outbox').count()
    request.onsuccess = () => resolve(request.result)
  })
  return count === 0
}, null, { timeout: 15_000 })
clearInterval(watch)
check('online change syncs without showing "not synced"', !sawUnsynced)

await browser.close()
console.log(failures ? `\n${failures} check(s) failed` : '\nAll checks passed')
process.exit(failures ? 1 : 0)
