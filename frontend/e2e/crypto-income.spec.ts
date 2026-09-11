import {
  expect,
  test,
  type Page,
} from '@playwright/test'

async function registerAndSetupUser(
  page: Page,
) {
  const unique =
    Date.now()

  const email =
    `crypto-${unique}@example.com`

  const password =
    'StrongTest123!'

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
      `Crypto Test ${unique}`,
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
}

test(
  'создание криптовалютного дохода',
  async ({ page }) => {
    await registerAndSetupUser(
      page,
    )

    await page.goto(
      '/settings',
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Настройки аккаунта',
        },
      ),
    ).toBeVisible()

    await page
      .getByRole(
        'button',
        {
          name:
            '+ Добавить счёт',
        },
      )
      .click()

    const accountEditor =
      page.locator(
        'form.account-editor',
      )

    await expect(
      accountEditor,
    ).toBeVisible()

    await accountEditor
      .getByLabel(
        'Название',
        {
          exact: true,
        },
      )
      .fill(
        'Crypto USDT',
      )

    await accountEditor
      .getByLabel(
        'Тип счёта',
      )
      .selectOption(
        'crypto_wallet',
      )

    const currencySelect =
      accountEditor
        .locator('label')
        .filter({
          hasText: 'Валюта',
        })
        .locator('select')

    await expect(
      currencySelect,
    ).toBeVisible()

    const usdtValue =
      await currencySelect.evaluate(
        (element) => {
          const select =
            element as HTMLSelectElement

          const option =
            Array.from(
              select.options,
            ).find(
              (item) =>
                item.text
                  .trim()
                  .startsWith(
                    'USDT',
                  ),
            )

          return (
            option?.value ??
            null
          )
        },
      )

    expect(
      usdtValue,
    ).not.toBeNull()

    await currencySelect.selectOption(
      usdtValue!,
    )

    await accountEditor
      .getByLabel('Сеть')
      .fill('TRC20')

    await accountEditor
      .getByLabel(
        'Адрес кошелька',
      )
      .fill(
        'TE2ECryptoWalletAddress123456789',
      )

    await accountEditor
      .getByRole(
        'button',
        {
          name:
            'Добавить счёт',
          exact: true,
        },
      )
      .click()

    await expect(
      page.getByText(
        'Финансовый счёт добавлен',
      ),
    ).toBeVisible()

    await page.goto(
      '/incomes',
    )

    await page
      .getByRole(
        'button',
        {
          name:
            '+ Добавить доход',
        },
      )
      .click()

    const incomeForm =
      page.locator(
        '.income-form-card form.form-grid',
      )

    await expect(
      incomeForm,
    ).toBeVisible()

    const accountSelect =
      incomeForm
        .locator('label')
        .filter({
          hasText:
            'Финансовый счёт',
        })
        .locator('select')
        .first()

    await expect(
      accountSelect,
    ).toBeVisible()

    const cryptoAccountValue =
      await accountSelect.evaluate(
        (element) => {
          const select =
            element as HTMLSelectElement

          const option =
            Array.from(
              select.options,
            ).find(
              (item) =>
                item.text.includes(
                  'Crypto USDT',
                ),
            )

          return (
            option?.value ??
            null
          )
        },
      )

    expect(
      cryptoAccountValue,
    ).not.toBeNull()

    await accountSelect.selectOption(
      cryptoAccountValue!,
    )

    await expect(
      incomeForm.getByText(
        'TRC20',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    await expect(
      incomeForm.getByText(
        'TE2ECryptoWalletAddress123456789',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    const description =
      `Crypto income ${Date.now()}`

    const txHash =
      'trx-e2e-12345'

    await incomeForm
      .getByLabel(
        'Описание дохода',
      )
      .fill(description)

    await incomeForm
      .getByLabel(
        'Сумма',
        {
          exact: true,
        },
      )
      .fill('1200')

    await incomeForm
      .getByLabel(
        'Hash транзакции',
      )
      .fill(txHash)

    await incomeForm
      .getByLabel(
        /Курс 1 USDT к GEL/,
      )
      .fill('2.6')

    await incomeForm
      .getByLabel(
        'Источник оценки',
      )
      .fill('Binance')

    const paymentMethod =
      incomeForm.getByLabel(
        'Способ оплаты',
      )

    await expect(
      paymentMethod,
    ).toBeDisabled()

    await expect(
      paymentMethod,
    ).toHaveValue('crypto')

    const declaration =
      incomeForm.getByLabel(
        'Графа декларации',
      )

    await expect(
      declaration,
    ).toBeDisabled()

    await expect(
      declaration,
    ).toHaveValue(
      'other_21',
    )

    await incomeForm
      .getByRole(
        'button',
        {
          name:
            'Рассчитать в GEL',
        },
      )
      .click()

    const preview =
      incomeForm.locator(
        '.income-preview',
      )

    await expect(
      preview,
    ).toBeVisible()

    await expect(
      preview,
    ).toContainText(
      /3120(?:\.0+)?\s*GEL/,
    )

    await expect(
      preview,
    ).toContainText(
      'Графа 21',
    )

    const saveButton =
      incomeForm.getByRole(
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

    const incomeRow =
      page
        .locator(
          '.income-table-row',
        )
        .filter({
          hasText:
            description,
        })

    await expect(
      incomeRow,
    ).toBeVisible()

    await expect(
      incomeRow,
    ).toContainText(
      '1200',
    )

    await expect(
      incomeRow,
    ).toContainText(
      'USDT',
    )

    await expect(
      incomeRow,
    ).toContainText(
      '3120',
    )

    await expect(
      incomeRow,
    ).toContainText(
      'Графа 21',
    )

    await expect(
      incomeRow,
    ).toContainText(
      'TRC20',
    )

    await expect(
      incomeRow,
    ).toContainText(
      txHash,
    )
  },
)