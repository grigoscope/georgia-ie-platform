import {
  expect,
  test,
  type Locator,
  type Page,
} from '@playwright/test'

async function selectOptionByText(
  select: Locator,
  text: string,
) {
  const value =
    await select.evaluate(
      (
        element,
        expectedText,
      ) => {
        const typedSelect =
          element as HTMLSelectElement

        const option =
          Array.from(
            typedSelect.options,
          ).find(
            (item) =>
              item.text.includes(
                expectedText,
              ),
          )

        return (
          option?.value ??
          null
        )
      },
      text,
    )

  expect(
    value,
  ).not.toBeNull()

  await select.selectOption(
    value!,
  )
}

async function registerAndSetupUser(
  page: Page,
) {
  const unique =
    Date.now()

  const email =
    `crypto-edit-${unique}@example.com`

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
      `Crypto Edit ${unique}`,
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

async function createCryptoWallet(
  page: Page,
) {
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

  await selectOptionByText(
    currencySelect,
    'USDT',
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
}

async function createCryptoIncome(
  page: Page,
  description: string,
) {
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

  await selectOptionByText(
    accountSelect,
    'Crypto USDT',
  )

  await expect(
    incomeForm.getByText(
      'TRC20',
      {
        exact: true,
      },
    ),
  ).toBeVisible()

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
    .fill(
      'tx-original-e2e',
    )

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

  await incomeForm
    .getByRole(
      'button',
      {
        name:
          'Сохранить доход',
      },
    )
    .click()

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
    '3120',
  )

  await expect(
    incomeRow,
  ).toContainText(
    'Графа 21',
  )

  return incomeRow
}

test(
  'редактирование криптовалютного дохода',
  async ({ page }) => {
    await registerAndSetupUser(
      page,
    )

    await createCryptoWallet(
      page,
    )

    const originalDescription =
      `Crypto income ${Date.now()}`

    const incomeRow =
      await createCryptoIncome(
        page,
        originalDescription,
      )

    await incomeRow
      .getByRole(
        'link',
        {
          name:
            'Редактировать',
        },
      )
      .click()

    await expect(
      page,
    ).toHaveURL(
      /\/incomes\/\d+\/edit/,
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            'Редактирование дохода',
        },
      ),
    ).toBeVisible()

    const editForm =
      page.locator(
        'main.page section.card form.form-grid',
      )

    await expect(
      editForm,
    ).toBeVisible()

    await expect(
      editForm.getByText(
        'TRC20',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    await expect(
      editForm.getByText(
        'TE2ECryptoWalletAddress123456789',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    const updatedDescription =
      `Edited crypto income ${Date.now()}`

    await editForm
      .getByLabel(
        'Описание',
        {
          exact: true,
        },
      )
      .fill(
        updatedDescription,
      )

    await editForm
      .getByLabel(
        'Сумма',
        {
          exact: true,
        },
      )
      .fill('1500')

    await editForm
      .getByLabel(
        'Hash транзакции',
      )
      .fill(
        'tx-edited-e2e',
      )

    await editForm
      .getByLabel(
        /Курс 1 USDT к GEL/,
      )
      .fill('2.7')

    await editForm
      .getByLabel(
        'Источник оценки',
      )
      .fill(
        'Binance E2E',
      )

    const paymentMethod =
      editForm.getByLabel(
        'Способ оплаты',
      )

    await expect(
      paymentMethod,
    ).toBeDisabled()

    await expect(
      paymentMethod,
    ).toHaveValue('crypto')

    const declaration =
      editForm.getByLabel(
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

    await editForm
      .getByRole(
        'button',
        {
          name:
            'Пересчитать в GEL',
        },
      )
      .click()

    const previews =
      editForm.locator(
        '.income-preview',
      )

    await expect(
      previews,
    ).toHaveCount(2)

    const recalculatedPreview =
      previews.last()

    await expect(
      recalculatedPreview,
    ).toContainText(
      /4050(?:\.0+)?\s*GEL/,
    )

    await expect(
      recalculatedPreview,
    ).toContainText(
      'Графа 21',
    )

    await expect(
      recalculatedPreview,
    ).toContainText(
      'Binance E2E',
    )

    const saveButton =
      editForm.getByRole(
        'button',
        {
          name:
            'Сохранить изменения',
        },
      )

    await expect(
      saveButton,
    ).toBeEnabled()

    await saveButton.click()

    await expect(
      page,
    ).toHaveURL(
      /\/incomes$/,
    )

    const updatedRow =
      page
        .locator(
          '.income-table-row',
        )
        .filter({
          hasText:
            updatedDescription,
        })

    await expect(
      updatedRow,
    ).toBeVisible()

    await expect(
      updatedRow,
    ).toContainText(
      '1500',
    )

    await expect(
      updatedRow,
    ).toContainText(
      'USDT',
    )

    await expect(
      updatedRow,
    ).toContainText(
      '4050',
    )

    await expect(
      updatedRow,
    ).toContainText(
      'Графа 21',
    )

    await expect(
      updatedRow,
    ).toContainText(
      'TRC20',
    )

    await expect(
      updatedRow,
    ).toContainText(
      'tx-edited-e2e',
    )
  },
)