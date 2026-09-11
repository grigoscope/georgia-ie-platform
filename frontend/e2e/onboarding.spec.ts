import {
  expect,
  test,
} from '@playwright/test'

test(
  'регистрация и первичная настройка',
  async ({ page }) => {
    const unique =
      Date.now()

    const email =
      `e2e-${unique}@example.com`

    const password =
      'StrongTest123!'

    await page.goto(
      '/register',
    )

    await page
      .getByLabel(
        'Email',
      )
      .fill(email)

    await page
      .getByLabel(
        'Пароль',
        {
          exact: true,
        },
      )
      .fill(password)

    await page
      .getByLabel(
        'Повторите пароль',
      )
      .fill(password)

    await page
      .getByRole(
        'button',
        {
          name:
            'Создать аккаунт',
        },
      )
      .click()

    await expect(
      page,
    ).toHaveURL(
      /\/onboarding/,
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Настройка аккаунта',
        },
      ),
    ).toBeVisible()

    await page
      .getByLabel(
        'Название бизнеса',
      )
      .fill(
        `E2E Business ${unique}`,
      )

    await page
      .getByLabel(
        'ИНН',
      )
      .fill(
        String(
          100000000 +
            (
              unique %
              899999999
            ),
        ),
      )

    await page
      .getByLabel(
        'Юридический адрес',
      )
      .fill(
        'Tbilisi, Georgia',
      )

    await page
      .getByLabel(
        'Публичный email',
      )
      .fill(email)

    await page
      .getByLabel(
        'Телефон',
      )
      .fill(
        '+995555123456',
      )

    await page
      .getByRole(
        'button',
        {
          name:
            'Продолжить',
        },
      )
      .click()

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Первый финансовый счёт',
        },
      ),
    ).toBeVisible()

    await page
      .getByLabel(
        'Название',
        {
          exact: true,
        },
      )
      .fill(
        'E2E GEL Account',
      )

    await page
      .getByLabel(
        'Тип счёта',
      )
      .selectOption(
        'bank_account',
      )

    await page
      .getByLabel(
        'Банк или провайдер',
      )
      .fill(
        'E2E Bank',
      )

    await page
      .getByLabel(
        'IBAN',
      )
      .fill(
        'GE29NB0000000000000000',
      )

    await page
      .getByRole(
        'button',
        {
          name:
            'Завершить настройку',
        },
      )
      .click()

    await expect(
      page,
    ).toHaveURL(
      /^http:\/\/127\.0\.0\.1:5173\/$/,
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Dashboard',
        },
      ),
    ).toBeVisible()

    await page.reload()

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Dashboard',
        },
      ),
    ).toBeVisible()

    await page.goto(
      '/incomes',
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Доходы',
        },
      ),
    ).toBeVisible()

    await page.goto(
      '/invoices',
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Инвойсы',
        },
      ),
    ).toBeVisible()

    await page.goto(
    '/taxes',
    )

    await expect(
    page,
    ).toHaveURL(
    /\/taxes/,
    )

    await expect(
    page.getByRole(
        'heading',
        {
        name:
            'Налоговые периоды',
        },
    ),
    ).toBeVisible()
  },
)