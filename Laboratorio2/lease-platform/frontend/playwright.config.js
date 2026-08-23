import { existsSync, rmSync } from 'node:fs'
import { defineConfig, devices } from '@playwright/test'

// The E2E run gets its own SQLite file so it never pollutes (or is polluted by) the
// demo dev database at backend/data/lease.db, and so a stale run's data can't make the
// next run's role-switch assertions flaky.
const E2E_DB_PATH = new URL('../backend/data/e2e.db', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
for (const suffix of ['', '-shm', '-wal']) {
  try {
    if (existsSync(E2E_DB_PATH + suffix)) rmSync(E2E_DB_PATH + suffix)
  } catch {
    // A prior webServer process may still be releasing its file lock; next run cleans it up.
  }
}

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  fullyParallel: false,
  reporter: 'line',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      command: '"..\\backend\\.venv\\Scripts\\python.exe" -m uvicorn main:app --app-dir "..\\backend" --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: true,
      timeout: 60_000,
      env: { DATABASE_URL: `sqlite:///${E2E_DB_PATH}` },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
