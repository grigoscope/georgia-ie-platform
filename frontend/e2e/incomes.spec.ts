import {
  expect,
  test,
} from '@playwright/test'

test(
  'создание обычного дохода',
  async ({ page }) => {
    const unique =
      Date.now()

    const email =
      `income-${unique}@example.com`

    const password =
      'StrongTest123!'

    const description =
      `E2E income ${unique}`

    await page.goto(
      '/register',
    )

    await page
      .getByLabel('Email')
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

    await page
      .getByLabel(
        'Название бизнеса',
      )
      .fill(
        `Income Test ${unique}`,
      )

    await page
      .getByLabel('ИНН')
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
      .getByLabel('Телефон')
      .fill(
        '+995555123456',
      )

    await page
      .getByRole(
        'button',
        {
          name: 'Продолжить',
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
        'Main GEL Account',
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
      .getByLabel('IBAN')
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
      page.getByRole(
        'heading',
        {
          name: 'Dashboard',
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
          name: 'Доходы',
        },
      ),
    ).toBeVisible()

    await page
      .getByRole(
        'button',
        {
          name:
            '+ Добавить доход',
        },
      )
      .click()

    await page
      .getByLabel(
        'Описание дохода',
      )
      .fill(description)

    await page
      .getByLabel(
        'Сумма',
        {
          exact: true,
        },
      )
      .fill('100')

    await page
      .getByRole(
        'button',
        {
          name:
            'Рассчитать в GEL',
        },
      )
      .click()

    const saveButton =
      page.getByRole(
        'button',
        {
          name:
            'Сохранить доход',
        },
      )

    await expect(
      saveButton,
    ).toBeEnabled()

    await saveButton.click()

    await expect(
      page.getByText(
        description,
      ),
    ).toBeVisible()

    await expect(
      page.getByText(
        '100 GEL',
      ).first(),
    ).toBeVisible()

    await page.goto('/')

    await expect(
      page.getByRole(
        'heading',
        {
          name: 'Dashboard',
        },
      ),
    ).toBeVisible()

    await expect(
      page.getByText(
        description,
      ),
    ).toBeVisible()

    await expect(
      page.getByText(
        '100 GEL',
      ).first(),
    ).toBeVisible()
  },
)