import {
  defineConfig,
  devices,
} from '@playwright/test'

export default defineConfig({
  testDir: './e2e',

  fullyParallel: false,

  timeout: 30_000,

  expect: {
    timeout: 10_000,
  },

  use: {
    baseURL:
      'http://127.0.0.1:5173',

    trace:
      'retain-on-failure',

    screenshot:
      'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',

      use: {
        ...devices[
          'Desktop Chrome'
        ],
      },
    },
  ],

  webServer: [
    {
      command:
        'python manage.py runserver 127.0.0.1:8000',

      cwd:
        '..',

      url:
        'http://127.0.0.1:8000/api/v1/auth/me/',

      reuseExistingServer:
        true,

      timeout:
        120_000,
    },

    {
      command:
        'npm run dev -- --host 127.0.0.1',

      url:
        'http://127.0.0.1:5173',

      reuseExistingServer:
        true,

      timeout:
        120_000,
    },
  ],
})