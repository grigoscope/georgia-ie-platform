import {
  useEffect,
  useState,
} from 'react'

import {
  createIncomeRequest,
  previewIncomeRequest,
  type IncomePreview,
} from '../api/incomes'

import {
  getAccountsRequest,
  getCurrenciesRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

type Props = {
  onSaved: () => Promise<void>
}

const CATEGORIES = [
  {
    value: 'cash_register_18',
    label: '18 — Кассовый аппарат',
  },
  {
    value: 'physical_pos_19',
    label: '19 — POS-терминал',
  },
  {
    value: 'cashless_20',
    label: '20 — Безналичный доход',
  },
  {
    value: 'other_21',
    label: '21 — Прочие доходы',
  },
]

function getTbilisiDateTime() {
  const parts =
    new Intl.DateTimeFormat(
      'en-CA',
      {
        timeZone: 'Asia/Tbilisi',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
      },
    ).formatToParts(
      new Date(),
    )

  function value(
    type: string,
  ) {
    return (
      parts.find(
        (part) =>
          part.type === type,
      )?.value ?? ''
    )
  }

  return (
    `${value('year')}-` +
    `${value('month')}-` +
    `${value('day')}T` +
    `${value('hour')}:` +
    `${value('minute')}`
  )
}

export function MiniIncomeForm({
  onSaved,
}: Props) {
  const [
    open,
    setOpen,
  ] = useState(false)

  const [
    accounts,
    setAccounts,
  ] = useState<
    FinancialAccount[]
  >([])

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>(
    [],
  )

  const [
    loadingSettings,
    setLoadingSettings,
  ] = useState(false)

  const [
    description,
    setDescription,
  ] = useState('')

  const [
    receivedAt,
    setReceivedAt,
  ] = useState(
    getTbilisiDateTime(),
  )

  const [
    accountId,
    setAccountId,
  ] = useState('')

  const [
    currencyId,
    setCurrencyId,
  ] = useState('')

  const [
    amount,
    setAmount,
  ] = useState('')

  const [
    category,
    setCategory,
  ] = useState(
    'cashless_20',
  )

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState(
    'bank_transfer',
  )

  const [
    preview,
    setPreview,
  ] = useState<
    IncomePreview['data'] | null
  >(null)

  const [
    previewing,
    setPreviewing,
  ] = useState(false)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState('')

  const activeAccounts =
    accounts.filter(
      (account) =>
        account.is_active &&
        account.type !==
          'crypto',
    )

  useEffect(() => {
    if (
      !open ||
      accounts.length > 0
    ) {
      return
    }

    async function loadSettings() {
      setLoadingSettings(true)
      setError('')

      try {
        const [
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        setAccounts(
          accountsResult,
        )

        setCurrencies(
          currenciesResult,
        )

        const available =
          accountsResult.filter(
            (account) =>
              account.is_active &&
              account.type !==
                'crypto',
          )

        const preferred =
          available.find(
            (account) =>
              account.is_default,
          ) ??
          available[0]

        if (preferred) {
          setAccountId(
            String(
              preferred.id,
            ),
          )

          setCurrencyId(
            String(
              preferred
                .default_currency,
            ),
          )

          setCategory(
            preferred
              .default_declaration_category ||
              'cashless_20',
          )
        }
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
          ),
        )
      } finally {
        setLoadingSettings(
          false,
        )
      }
    }

    void loadSettings()
  }, [
    open,
    accounts.length,
  ])

  function changeAccount(
    newAccountId: string,
  ) {
    setAccountId(
      newAccountId,
    )

    setPreview(null)

    const account =
      accounts.find(
        (item) =>
          item.id ===
          Number(
            newAccountId,
          ),
      )

    if (!account) {
      return
    }

    setCurrencyId(
      String(
        account.default_currency,
      ),
    )

    setCategory(
      account
        .default_declaration_category ||
        'cashless_20',
    )
  }

  function validate() {
    if (!description.trim()) {
      return 'Введите описание дохода'
    }

    if (!accountId) {
      return 'Выберите счёт'
    }

    if (!currencyId) {
      return 'Выберите валюту'
    }

    if (
      !amount ||
      Number(amount) <= 0
    ) {
      return 'Введите сумму больше нуля'
    }

    if (!receivedAt) {
      return 'Укажите дату дохода'
    }

    return ''
  }

  async function calculate() {
    const validationError =
      validate()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    setPreviewing(true)
    setError('')
    setPreview(null)

    try {
      const result =
        await previewIncomeRequest(
          {
            received_at:
              `${receivedAt}:00+04:00`,

            financial_account:
              Number(accountId),

            original_amount:
              amount,

            original_currency:
              Number(currencyId),

            declaration_category:
              category,
          },
        )

      setPreview(
        result.data,
      )
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setPreviewing(false)
    }
  }

  async function saveIncome() {
    const validationError =
      validate()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    if (!preview) {
      setError(
        'Сначала рассчитайте сумму в GEL',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      await createIncomeRequest(
        {
          received_at:
            `${receivedAt}:00+04:00`,

          description:
            description.trim(),

          additional_info: '',

          financial_account:
            Number(accountId),

          payment_method:
            paymentMethod,

          document_number: '',

          document_date: null,

          original_amount:
            amount,

          original_currency:
            Number(currencyId),

          declaration_category:
            category,

          vat_amount: '0.00',

          comment: '',
        },
      )

      setDescription('')
      setAmount('')
      setPreview(null)

      setReceivedAt(
        getTbilisiDateTime(),
      )

      setOpen(false)

      await onSaved()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mini-income-create">
      <button
        type="button"
        className="mini-income-toggle"
        onClick={() => {
          setOpen(
            (current) =>
              !current,
          )

          setError('')
        }}
      >
        {open
          ? 'Закрыть форму'
          : '+ Добавить доход'}
      </button>

      {open && (
        <div className="mini-income-form">
          <div>
            <h3>
              Новый доход
            </h3>

            <p className="muted">
              Добавление прямо
              из Telegram
            </p>
          </div>

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

          {loadingSettings ? (
            <div className="mini-empty">
              Загружаем счета...
            </div>
          ) : (
            <>
              <label>
                Описание

                <input
                  type="text"
                  value={description}
                  placeholder="Например: Оплата за разработку"
                  onChange={(
                    event,
                  ) => {
                    setDescription(
                      event.target
                        .value,
                    )

                    setPreview(
                      null,
                    )
                  }}
                />
              </label>

              <label>
                Дата и время

                <input
                  type="datetime-local"
                  value={receivedAt}
                  onChange={(
                    event,
                  ) => {
                    setReceivedAt(
                      event.target
                        .value,
                    )

                    setPreview(
                      null,
                    )
                  }}
                />
              </label>

              <label>
                Счёт

                <select
                  value={accountId}
                  onChange={(
                    event,
                  ) =>
                    changeAccount(
                      event.target
                        .value,
                    )
                  }
                >
                  <option value="">
                    Выберите счёт
                  </option>

                  {activeAccounts.map(
                    (account) => (
                      <option
                        key={
                          account.id
                        }
                        value={
                          account.id
                        }
                      >
                        {account.name}
                      </option>
                    ),
                  )}
                </select>
              </label>

              {activeAccounts.length ===
                0 && (
                <div className="tax-detail-alert tax-detail-alert-warning">
                  Нет активных
                  обычных счетов.
                </div>
              )}

              <div className="mini-income-money-row">
                <label>
                  Сумма

                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={amount}
                    onChange={(
                      event,
                    ) => {
                      setAmount(
                        event.target
                          .value,
                      )

                      setPreview(
                        null,
                      )
                    }}
                    placeholder="0.00"
                  />
                </label>

                <label>
                  Валюта

                  <select
                    value={currencyId}
                    onChange={(
                      event,
                    ) => {
                      setCurrencyId(
                        event.target
                          .value,
                      )

                      setPreview(
                        null,
                      )
                    }}
                  >
                    <option value="">
                      —
                    </option>

                    {currencies
                      .filter(
                        (currency) =>
                          currency
                            .is_active &&
                          currency.kind !==
                            'crypto',
                      )
                      .map(
                        (
                          currency,
                        ) => (
                          <option
                            key={
                              currency.id
                            }
                            value={
                              currency.id
                            }
                          >
                            {
                              currency.code
                            }
                          </option>
                        ),
                      )}
                  </select>
                </label>
              </div>

              <label>
                Категория декларации

                <select
                  value={category}
                  onChange={(
                    event,
                  ) => {
                    setCategory(
                      event.target
                        .value,
                    )

                    setPreview(
                      null,
                    )
                  }}
                >
                  {CATEGORIES.map(
                    (item) => (
                      <option
                        key={
                          item.value
                        }
                        value={
                          item.value
                        }
                      >
                        {
                          item.label
                        }
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label>
                Способ оплаты

                <select
                  value={
                    paymentMethod
                  }
                  onChange={(
                    event,
                  ) =>
                    setPaymentMethod(
                      event.target
                        .value,
                    )
                  }
                >
                  <option value="bank_transfer">
                    Банковский перевод
                  </option>

                  <option value="card">
                    Карта
                  </option>

                  <option value="cash">
                    Наличные
                  </option>

                  <option value="other">
                    Другое
                  </option>
                </select>
              </label>

              <button
                type="button"
                className="secondary"
                disabled={
                  previewing ||
                  saving
                }
                onClick={() => {
                  void calculate()
                }}
              >
                {previewing
                  ? 'Считаем...'
                  : 'Рассчитать в GEL'}
              </button>

              {preview && (
                <div className="mini-income-preview">
                  <span>
                    Получится
                  </span>

                  <strong>
                    {
                      preview.amount_gel
                    }{' '}
                    GEL
                  </strong>

                  <small>
                    Курс:{' '}
                    {
                      preview.rate_value
                    }{' '}
                    за{' '}
                    {
                      preview.rate_unit
                    }{' '}
                    {
                      preview.currency
                    }
                  </small>

                  <small>
                    Источник:{' '}
                    {
                      preview.source
                    }
                  </small>

                  {preview.warnings.map(
                    (
                      warning,
                      index,
                    ) => (
                      <small
                        key={
                          `${warning}-${index}`
                        }
                        className="mini-income-warning"
                      >
                        {warning}
                      </small>
                    ),
                  )}
                </div>
              )}

              <button
                type="button"
                disabled={
                  saving ||
                  !preview
                }
                onClick={() => {
                  void saveIncome()
                }}
              >
                {saving
                  ? 'Сохраняем...'
                  : 'Сохранить доход'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}