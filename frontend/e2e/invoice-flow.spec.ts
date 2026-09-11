import {
  expect,
  test,
  type Page,
} from '@playwright/test'

test.setTimeout(
  90000,
)

async function registerAndSetupUser(
  page: Page,
) {
  const unique =
    Date.now()

  const email =
    `invoice-${unique}@example.com`

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
      `Invoice Test ${unique}`,
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
      'Invoice GEL Account',
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

  return {
    unique,
    email,
  }
}

async function enableInvoiceAccount(
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

  const accountEditor =
    page.locator(
      'form.account-editor',
    )

  await expect(
    accountEditor,
  ).toBeVisible()

  const invoiceCheckbox =
    accountEditor.getByLabel(
      'Использовать в инвойсах',
    )

  await invoiceCheckbox.check()

  await accountEditor
    .getByRole(
      'button',
      {
        name:
          'Сохранить изменения',
      },
    )
    .click()

  await expect(
    page.getByText(
      'Финансовый счёт сохранён',
    ),
  ).toBeVisible()

  await expect(
    invoiceCheckbox,
  ).toBeChecked()
}

async function createInvoice(
  page: Page,
  unique: number,
) {
  await page.goto(
    '/invoices/new',
  )

  await expect(
    page.getByRole(
      'heading',
      {
        name:
          'Новый инвойс',
      },
    ),
  ).toBeVisible()

  const form =
    page.locator(
      'form.invoice-create-form',
    )

  await expect(
    form,
  ).toBeVisible()

  await form
    .getByRole(
      'button',
      {
        name:
          '+ Новый контрагент',
      },
    )
    .click()

  const counterpartyCard =
    form.locator(
      '.quick-counterparty-card',
    )

  await expect(
    counterpartyCard,
  ).toBeVisible()

  const clientName =
    `E2E Client ${unique}`

  await counterpartyCard
    .getByLabel(
      'Название / имя',
    )
    .fill(clientName)

  await counterpartyCard
    .getByLabel('Страна')
    .fill('Georgia')

  await counterpartyCard
    .getByLabel(
      'Налоговый номер',
    )
    .fill(
      `TAX-${unique}`,
    )

  await counterpartyCard
    .getByLabel('Адрес')
    .fill(
      'Tbilisi, Georgia',
    )

  await counterpartyCard
    .getByLabel('Email')
    .fill(
      `client-${unique}@example.com`,
    )

  await counterpartyCard
    .getByRole(
      'button',
      {
        name:
          'Добавить контрагента',
      },
    )
    .click()

  await expect(
    counterpartyCard,
  ).toBeHidden()

  const counterpartySelect =
    form.getByLabel(
      'Контрагент',
    )

  await expect(
    counterpartySelect,
  ).not.toHaveValue('')

  const accountSelect =
    form.getByLabel(
      'Счёт для оплаты',
    )

  await expect(
    accountSelect,
  ).not.toHaveValue('')

  const currencySelect =
    form
      .locator('label')
      .filter({
        hasText: 'Валюта',
      })
      .locator('select')
      .first()

  await expect(
    currencySelect,
  ).toBeVisible()

  await expect(
    currencySelect,
  ).not.toHaveValue('')

  const item =
    form.locator(
      '.invoice-item-card',
    ).first()

  await expect(
    item,
  ).toBeVisible()

  await item
    .getByLabel(
      'Описание',
      {
        exact: true,
      },
    )
    .fill(
      'E2E development service',
    )

  await item
    .getByLabel(
      'Количество',
    )
    .fill('1')

  await item
    .getByLabel(
      'Цена',
    )
    .fill('1000')

  await form
    .getByRole(
      'button',
      {
        name:
          'Создать инвойс',
      },
    )
    .click()

  await expect(
    page,
  ).toHaveURL(
    /\/invoices\/\d+$/,
  )

  await expect(
    page.getByText(
      'Черновик',
      {
        exact: true,
      },
    ),
  ).toBeVisible()

  const summary =
    page.locator(
      '.invoice-detail-summary',
    )

  await expect(
    summary,
  ).toBeVisible()

  const totalCard =
    summary
      .locator('.card')
      .filter({
        hasText: 'Итог',
      })

  await expect(
    totalCard,
  ).toContainText(
    '1000',
  )

  return clientName
}

test(
  'инвойс: PDF, отправка и полная оплата частями',
  async ({ page }) => {
    const {
      unique,
    } =
      await registerAndSetupUser(
        page,
      )

    await enableInvoiceAccount(
      page,
    )

    const clientName =
      await createInvoice(
        page,
        unique,
      )

    await expect(
      page.getByText(
        clientName,
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    await page
      .getByRole(
        'button',
        {
          name:
            'Создать PDF',
        },
      )
      .click()

    const downloadButton =
      page.getByRole(
        'button',
        {
          name:
            'Скачать PDF',
        },
      )

    await expect(
      downloadButton,
    ).toBeVisible()

    const downloadPromise =
      page.waitForEvent(
        'download',
      )

    await downloadButton.click()

    const download =
      await downloadPromise

    expect(
      download.suggestedFilename(),
    ).toMatch(
      /\.pdf$/i,
    )

    await page
      .getByRole(
        'button',
        {
          name:
            'Отметить отправленным',
        },
      )
      .click()

    await expect(
      page.getByText(
        'Ожидает оплаты',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    await page
      .getByRole(
        'button',
        {
          name:
            'Зарегистрировать оплату',
        },
      )
      .click()

    let paymentForm =
      page.locator(
        '.invoice-payment-form',
      )

    await expect(
      paymentForm,
    ).toBeVisible()

    await paymentForm
      .getByLabel(
        'Сумма оплаты',
      )
      .fill('400')

    await paymentForm
      .getByRole(
        'button',
        {
          name:
            'Подтвердить оплату',
        },
      )
      .click()

    await expect(
      paymentForm,
    ).toBeHidden()

    await expect(
      page.getByText(
        'Частично оплачен',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    const summaryAfterPartial =
      page.locator(
        '.invoice-detail-summary',
      )

    const paidAfterPartial =
      summaryAfterPartial
        .locator('.card')
        .filter({
          hasText:
            'Оплачено',
        })

    const remainingAfterPartial =
      summaryAfterPartial
        .locator('.card')
        .filter({
          hasText:
            'Осталось',
        })

    await expect(
      paidAfterPartial,
    ).toContainText(
      '400',
    )

    await expect(
      remainingAfterPartial,
    ).toContainText(
      '600',
    )

    await page
      .getByRole(
        'button',
        {
          name:
            'Зарегистрировать оплату',
        },
      )
      .click()

    paymentForm =
      page.locator(
        '.invoice-payment-form',
      )

    await expect(
      paymentForm,
    ).toBeVisible()

    await paymentForm
      .getByLabel(
        'Сумма оплаты',
      )
      .fill('600')

    await paymentForm
      .getByRole(
        'button',
        {
          name:
            'Подтвердить оплату',
        },
      )
      .click()

    await expect(
      paymentForm,
    ).toBeHidden()

    await expect(
      page.getByText(
        'Оплачен',
        {
          exact: true,
        },
      ),
    ).toBeVisible()

    const summaryAfterFull =
      page.locator(
        '.invoice-detail-summary',
      )

    const paidAfterFull =
      summaryAfterFull
        .locator('.card')
        .filter({
          hasText:
            'Оплачено',
        })

    const remainingAfterFull =
      summaryAfterFull
        .locator('.card')
        .filter({
          hasText:
            'Осталось',
        })

    await expect(
      paidAfterFull,
    ).toContainText(
      '1000',
    )

    await expect(
      remainingAfterFull,
    ).toContainText(
      '0',
    )

    await expect(
      page.getByRole(
        'button',
        {
          name:
            'Зарегистрировать оплату',
        },
      ),
    ).toHaveCount(0)
  },
)