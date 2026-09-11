import {
  expect,
  test,
  type Locator,
  type Page,
} from '@playwright/test'

test.setTimeout(
  90000,
)

const MONTHS = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
]

function getTbilisiPeriod() {
  const parts =
    new Intl.DateTimeFormat(
      'en-CA',
      {
        timeZone:
          'Asia/Tbilisi',
        year: 'numeric',
        month: '2-digit',
      },
    ).formatToParts(
      new Date(),
    )

  const year =
    Number(
      parts.find(
        (part) =>
          part.type === 'year',
      )?.value,
    )

  const month =
    Number(
      parts.find(
        (part) =>
          part.type === 'month',
      )?.value,
    )

  return {
    year,
    month,
  }
}

function getOlderPeriod() {
  const current =
    getTbilisiPeriod()

  const date =
    new Date(
      Date.UTC(
        current.year,
        current.month - 3,
        1,
      ),
    )

  return {
    year:
      date.getUTCFullYear(),
    month:
      date.getUTCMonth() + 1,
  }
}

async function registerAndSetupUser(
  page: Page,
) {
  const unique =
    Date.now()

  const email =
    `tax-${unique}@example.com`

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
      `Tax Test ${unique}`,
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
      'Tax GEL Account',
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

  return unique
}

async function createIncome(
  page: Page,
  unique: number,
) {
  const description =
    `Tax E2E income ${unique}`

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

  const form =
    page.locator(
      '.income-form-card form.form-grid',
    )

  await expect(
    form,
  ).toBeVisible()

  await form
    .getByLabel(
      'Описание дохода',
    )
    .fill(description)

  await form
    .getByLabel(
      'Сумма',
      {
        exact: true,
      },
    )
    .fill('100')

  await form
    .getByRole(
      'button',
      {
        name:
          'Рассчитать в GEL',
      },
    )
    .click()

  const preview =
    form.locator(
      '.income-preview',
    )

  await expect(
    preview,
  ).toBeVisible()

  await expect(
    preview,
  ).toContainText(
    /100(?:[,.]0+)?\s*GEL/,
  )

  const saveButton =
    form.getByRole(
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

  const row =
    page
      .locator(
        '.income-table-row',
      )
      .filter({
        hasText:
          description,
      })

  await expect(
    row,
  ).toBeVisible()

  await expect(
    row,
  ).toContainText(
    '100',
  )

  await expect(
    row,
  ).toContainText(
    'Графа 20',
  )
}

function getTaxPeriodCard(
  page: Page,
  year: number,
  month: number,
) {
  return page
    .locator(
      '.tax-period-card',
    )
    .filter({
      hasText:
        `${MONTHS[month - 1]} ${year}`,
    })
}

function getTaxStatusCard(
  page: Page,
  heading: string,
): Locator {
  return page
    .locator(
      '.tax-detail-card',
    )
    .filter({
      has: page.getByRole(
        'heading',
        {
          name: heading,
        },
      ),
    })
}

test(
  'налоговый период: расчёт, подача, оплата и нулевой просроченный месяц',
  async ({ page }) => {
    const unique =
      await registerAndSetupUser(
        page,
      )

    await createIncome(
      page,
      unique,
    )

    const current =
      getTbilisiPeriod()

    await page.goto(
      '/taxes',
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

    const currentCard =
      getTaxPeriodCard(
        page,
        current.year,
        current.month,
      )

    await expect(
      currentCard,
    ).toBeVisible()

    await expect(
      currentCard,
    ).toContainText(
      /100[,\s.]?00\s*GEL/,
    )

    await expect(
      currentCard,
    ).toContainText(
      '20:',
    )

    await expect(
      currentCard,
    ).toContainText(
      'Декларация: Не подана',
    )

    await expect(
      currentCard,
    ).toContainText(
      'Оплата: Не оплачено',
    )

    await currentCard
      .getByRole(
        'button',
        {
          name:
            'Пересчитать',
        },
      )
      .click()

    await expect(
      currentCard,
    ).toContainText(
      /100[,\s.]?00\s*GEL/,
    )

    await currentCard
      .getByRole(
        'link',
        {
          name: 'Открыть',
        },
      )
      .click()

    await expect(
      page,
    ).toHaveURL(
      /\/taxes\/\d+$/,
    )

    await expect(
      page.getByRole(
        'heading',
        {
          name:
            `${MONTHS[current.month - 1]} ${current.year}`,
        },
      ),
    ).toBeVisible()

    const declarationGrid =
      page.locator(
        '.tax-declaration-grid',
      )

    await expect(
      declarationGrid,
    ).toContainText(
      'Поле 17',
    )

    const field17 =
      declarationGrid
        .locator('div')
        .filter({
          hasText: 'Поле 17',
        })
        .first()

    await expect(
      field17,
    ).toContainText(
      /100[,\s.]?00\s*GEL/,
    )

    const field20 =
      declarationGrid
        .locator('div')
        .filter({
          hasText: 'Поле 20',
        })
        .first()

    await expect(
      field20,
    ).toContainText(
      /100[,\s.]?00\s*GEL/,
    )

    const field26 =
      declarationGrid
        .locator('div')
        .filter({
          hasText: 'Поле 26',
        })
        .first()

    await expect(
      field26,
    ).toContainText(
      /1[,.]00\s*GEL/,
    )

    await page
      .getByRole(
        'button',
        {
          name:
            'Пересчитать',
        },
      )
      .click()

    await expect(
      field26,
    ).toContainText(
      /1[,.]00\s*GEL/,
    )

    const declarationCard =
      getTaxStatusCard(
        page,
        'Подача декларации',
      )

    await expect(
      declarationCard,
    ).toContainText(
      'Не подана',
    )

    await declarationCard
      .getByRole(
        'button',
        {
          name:
            'Отметить поданной',
        },
      )
      .click()

    const submissionForm =
      declarationCard.locator(
        '.tax-action-form',
      )

    await expect(
      submissionForm,
    ).toBeVisible()

    await submissionForm
      .getByPlaceholder(
        'Номер декларации или комментарий',
      )
      .fill(
        'E2E declaration',
      )

    await submissionForm
      .getByRole(
        'button',
        {
          name:
            'Подтвердить подачу',
        },
      )
      .click()

    await expect(
      declarationCard,
    ).toContainText(
      'Подана',
    )

    await expect(
      declarationCard,
    ).toContainText(
      'E2E declaration',
    )

    const paymentCard =
      getTaxStatusCard(
        page,
        'Оплата налога',
      )

    await expect(
      paymentCard,
    ).toContainText(
      'Не оплачено',
    )

    await paymentCard
      .getByRole(
        'button',
        {
          name:
            'Отметить оплаченным',
        },
      )
      .click()

    const paymentForm =
      paymentCard.locator(
        '.tax-action-form',
      )

    await expect(
      paymentForm,
    ).toBeVisible()

    await paymentForm
      .getByLabel(
        'Сумма оплаты',
      )
      .fill('1')

    await paymentForm
      .getByPlaceholder(
        'Комментарий к оплате',
      )
      .fill(
        'E2E tax payment',
      )

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
      paymentCard,
    ).toContainText(
      'Оплачено',
    )

    await expect(
      paymentCard,
    ).toContainText(
      /1[,.]00\s*GEL/,
    )

    page.once(
      'dialog',
      async (dialog) => {
        await dialog.accept()
      },
    )

    await paymentCard
      .getByRole(
        'button',
        {
          name:
            'Отменить отметку',
        },
      )
      .click()

    await expect(
      paymentCard,
    ).toContainText(
      'Не оплачено',
    )

    page.once(
      'dialog',
      async (dialog) => {
        await dialog.accept()
      },
    )

    await declarationCard
      .getByRole(
        'button',
        {
          name:
            'Отменить отметку',
        },
      )
      .click()

    await expect(
      declarationCard,
    ).toContainText(
      'Не подана',
    )

    await page.goto(
      '/taxes',
    )

    const old =
      getOlderPeriod()

    const generateForm =
      page.locator(
        'form.tax-generate-form',
      )

    await expect(
      generateForm,
    ).toBeVisible()

    await generateForm
      .getByLabel('Месяц')
      .selectOption(
        String(old.month),
      )

    await generateForm
      .getByLabel('Год')
      .fill(
        String(old.year),
      )

    await generateForm
      .getByRole(
        'button',
        {
          name:
            'Рассчитать',
        },
      )
      .click()

    const oldCard =
      getTaxPeriodCard(
        page,
        old.year,
        old.month,
      )

    await expect(
      oldCard,
    ).toBeVisible()

    await expect(
      oldCard,
    ).toContainText(
      'Просрочено',
    )

    await expect(
      oldCard,
    ).toContainText(
      /0[,.]00\s*GEL/,
    )

    await expect(
      oldCard,
    ).toContainText(
      'Декларация: Не подана',
    )

    await expect(
      oldCard,
    ).toContainText(
      'Оплата: Не оплачено',
    )
  },
)