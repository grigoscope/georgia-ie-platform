import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react'

import {
  getAccountsRequest,
  getCurrenciesRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  DateTimeField,
} from '../components/DateTimeField'

import {
  createIncomeRequest,
  deleteIncomeRequest,
  getIncomesRequest,
  previewIncomeRequest,
  type IncomeEntry,
  type IncomeFilters,
  type IncomePreview,
} from '../api/incomes'

import {
  Link,
} from 'react-router-dom'

const CATEGORY_LABELS: Record<
  string,
  string
> = {
  cash_register_18:
    'Графа 18 — кассовый аппарат',
  physical_pos_19:
    'Графа 19 — физический POS',
  cashless_20:
    'Графа 20 — безналичные поступления',
  other_21:
    'Графа 21 — прочие доходы и криптовалюта',
}

function formatAmount(value: string | number): string {
  const num = Number(value)

  if (Number.isNaN(num)) {
    return String(value)
  }

  if (Number.isInteger(num)) {
    return String(num)
  }

  return num.toFixed(3).replace(/\.?0+$/, '')
}

function getTbilisiDateTime() {
  const formatter =
    new Intl.DateTimeFormat(
      'sv-SE',
      {
        timeZone: 'Asia/Tbilisi',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      },
    )

  const parts =
    formatter.formatToParts(
      new Date(),
    )

  const values: Record<
    string,
    string
  > = {}

  for (const part of parts) {
    values[part.type] =
      part.value
  }

  return (
    `${values.year}-` +
    `${values.month}-` +
    `${values.day}T` +
    `${values.hour}:` +
    `${values.minute}`
  )
}

function toTbilisiIso(
  value: string,
) {
  return `${value}:00+04:00`
}

function formatReceivedAt(
  value: string,
) {
  return new Intl.DateTimeFormat(
    'ru-RU',
    {
      timeZone: 'Asia/Tbilisi',
      dateStyle: 'medium',
      timeStyle: 'short',
    },
  ).format(
    new Date(value),
  )
}

export function IncomesPage() {
  const [
    incomes,
    setIncomes,
  ] = useState<IncomeEntry[]>([])

  const [
    accounts,
    setAccounts,
  ] = useState<FinancialAccount[]>([])

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>([])

  const [loading, setLoading] =
    useState(true)

  const [showForm, setShowForm] =
    useState(false)

  const [error, setError] =
    useState('')

  const [saving, setSaving] =
    useState(false)

  const [
    deletingId,
    setDeletingId,
    ] = useState<number | null>(
    null,
  )

  const [
    journalLoading,
    setJournalLoading,
  ] = useState(false)

  const [
    totalCount,
    setTotalCount,
  ] = useState(0)

  const [
    hasNextPage,
    setHasNextPage,
  ] = useState(false)

  const [
    hasPreviousPage,
    setHasPreviousPage,
  ] = useState(false)

  const [
    journalReload,
    setJournalReload,
  ] = useState(0)

  const [
    activeFilters,
    setActiveFilters,
  ] = useState<IncomeFilters>({
    page: 1,
    page_size: 20,
    ordering: '-received_at',
  })

  const [
    searchQuery,
    setSearchQuery,
  ] = useState('')

  const [
    dateFrom,
    setDateFrom,
  ] = useState('')

  const [
    dateTo,
    setDateTo,
  ] = useState('')

  const [
    filterAccount,
    setFilterAccount,
  ] = useState('')

  const [
    filterCurrency,
    setFilterCurrency,
  ] = useState('')

  const [
    filterCategory,
    setFilterCategory,
  ] = useState('')

  const [
    filterOrdering,
    setFilterOrdering,
  ] = useState(
    '-received_at',
  )

  const [
    previewLoading,
    setPreviewLoading,
  ] = useState(false)

  const [
    preview,
    setPreview,
  ] = useState<IncomePreview | null>(
    null,
  )

  const [
    receivedAt,
    setReceivedAt,
  ] = useState(
    getTbilisiDateTime(),
  )

  const [
    description,
    setDescription,
  ] = useState('')

  const [
    accountId,
    setAccountId,
  ] = useState('')

  const [
    currencyId,
    setCurrencyId,
  ] = useState('')

  const [amount, setAmount] =
    useState('')

  const [
    declarationCategory,
    setDeclarationCategory,
  ] = useState('')

  const [
    paymentMethod,
    setPaymentMethod,
    ] = useState(
    'bank_transfer',
   )

  const [
    documentNumber,
    setDocumentNumber,
  ] = useState('')

  const [
    documentDate,
    setDocumentDate,
  ] = useState('')

  const [comment, setComment] =
    useState('')

  const [
    rateMode,
    setRateMode,
  ] = useState<
    'automatic' |
    'manual' |
    'ready_gel'
  >('automatic')

  const [
    readyAmountGel,
    setReadyAmountGel,
  ] = useState('')

  const [
    manualRate,
    setManualRate,
  ] = useState('')

  const [
    manualRateUnit,
    setManualRateUnit,
  ] = useState('1')

  const [
    manualSource,
    setManualSource,
  ] = useState('')

  const [
    showFilters, 
    setShowFilters
  ] = useState(false)

  const activeFilterCount =
    useMemo(() => {
      let count = 0

      if (searchQuery.trim()) {
        count += 1
      }

      if (dateFrom) {
        count += 1
      }

      if (dateTo) {
        count += 1
      }

      if (filterAccount) {
        count += 1
      }

      if (filterCurrency) {
        count += 1
      }

      if (filterCategory) {
        count += 1
      }

      if (
        filterOrdering !==
        '-received_at'
      ) {
        count += 1
      }

      return count
    }, [
      searchQuery,
      dateFrom,
      dateTo,
      filterAccount,
      filterCurrency,
      filterCategory,
      filterOrdering,
    ])

  const selectedCurrency =
    useMemo(
      () =>
        currencies.find(
          (currency) =>
            currency.id ===
            Number(currencyId),
        ) ?? null,
      [
        currencies,
        currencyId,
      ],
    )

  const selectedAccount =
    useMemo(
      () =>
        accounts.find(
          (account) =>
            account.id ===
            Number(accountId),
        ) ?? null,
      [
        accounts,
        accountId,
      ],
    )

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        if (cancelled) {
          return
        }

        setAccounts(
          accountsResult,
        )

        setCurrencies(
          currenciesResult,
        )

        const defaultAccount =
          accountsResult.find(
            (account) =>
              account.is_default &&
              account.is_active,
          ) ??
          accountsResult.find(
            (account) =>
              account.is_active,
          )

        if (defaultAccount) {
          setAccountId(
            String(
              defaultAccount.id,
            ),
          )

          setCurrencyId(
            String(
              defaultAccount
                .default_currency,
            ),
          )
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(
            getApiErrorMessage(
              requestError,
            ),
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadJournal() {
      setJournalLoading(true)

      try {
        const result =
          await getIncomesRequest(
            activeFilters,
          )

        if (cancelled) {
          return
        }

        setIncomes(
          result.results,
        )

        setTotalCount(
          result.count,
        )

        setHasNextPage(
          Boolean(result.next),
        )

        setHasPreviousPage(
          Boolean(result.previous),
        )
      } catch (requestError) {
        if (!cancelled) {
          setError(
            getApiErrorMessage(
              requestError,
            ),
          )
        }
      } finally {
        if (!cancelled) {
          setJournalLoading(false)
        }
      }
    }

    void loadJournal()

    return () => {
      cancelled = true
    }
  }, [
    activeFilters,
    journalReload,
  ])

  function invalidatePreview() {
    setPreview(null)
  }

  function resetForm() {
    setReceivedAt(
      getTbilisiDateTime(),
    )

    setDescription('')
    setAmount('')
    setDeclarationCategory('')
    setPaymentMethod(
        'bank_transfer',
    )
    setDocumentNumber('')
    setDocumentDate('')
    setComment('')
    setReadyAmountGel('')
    setManualRate('')
    setManualRateUnit('1')
    setManualSource('')
    setRateMode('automatic')
    setPreview(null)

    const defaultAccount =
      accounts.find(
        (account) =>
          account.is_default &&
          account.is_active,
      ) ??
      accounts.find(
        (account) =>
          account.is_active,
      )

    if (defaultAccount) {
      setAccountId(
        String(defaultAccount.id),
      )

      setCurrencyId(
        String(
          defaultAccount
            .default_currency,
        ),
      )
    }
  }

  function getRateFields() {
    if (
        !selectedCurrency ||
        selectedCurrency.code === 'GEL'
    ) {
        return {}
    }

    if (rateMode === 'ready_gel') {
        return {
        ready_amount_gel:
            readyAmountGel,
        }
    }

    if (rateMode === 'manual') {
        return {
        manual_rate_value:
            manualRate,
        manual_rate_unit:
            Number(manualRateUnit),
        manual_source:
            manualSource.trim() ||
            'Ручной ввод',
        }
    }

    return {}
  }

  async function calculatePreview() {
    setError('')
    setPreviewLoading(true)

    try {
      if (!accountId) {
        throw new Error(
          'Выберите финансовый счёт',
        )
      }

      if (!currencyId) {
        throw new Error(
          'Выберите валюту',
        )
      }

      if (!amount) {
        throw new Error(
          'Введите сумму дохода',
        )
      }

      if (
        rateMode === 'manual' &&
        selectedCurrency?.code !==
            'GEL' &&
        !manualRate
        ) {
        throw new Error(
            'Введите ручной курс',
        )
        }

        if (
        rateMode === 'manual' &&
        selectedCurrency?.code !==
            'GEL' &&
        Number(manualRateUnit) <= 0
        ) {
        throw new Error(
            'Количество единиц валюты должно быть больше нуля',
        )
        }

        if (
        rateMode === 'ready_gel' &&
        !readyAmountGel
        ) {
        throw new Error(
            'Укажите GEL-эквивалент',
        )
      }

      const result =
        await previewIncomeRequest({
          received_at:
            toTbilisiIso(
              receivedAt,
            ),
          financial_account:
            Number(accountId),
          original_amount:
            amount,
          original_currency:
            Number(currencyId),
          ...(declarationCategory
            ? {
                declaration_category:
                  declarationCategory,
              }
            : {}),
          ...getRateFields(),
        })

      setPreview(result)

      if (
        !declarationCategory
      ) {
        setDeclarationCategory(
          result.data
            .suggested_category,
        )
      }
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setPreviewLoading(false)
    }
  }

  async function saveIncome(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (!preview) {
      setError(
        'Сначала рассчитайте GEL-эквивалент',
      )

      return
    }

    if (!declarationCategory) {
      setError(
        'Выберите графу декларации',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      await createIncomeRequest({
          received_at:
            toTbilisiIso(
              receivedAt,
            ),
          description:
            description.trim(),
          additional_info: '',
          financial_account:
            Number(accountId),
          payment_method:
            paymentMethod.trim(),
          document_number:
            documentNumber.trim(),
          document_date:
            documentDate || null,
          original_amount:
            amount,
          original_currency:
            Number(currencyId),
          declaration_category:
            declarationCategory,
          vat_amount: '0.00',
          comment:
            comment.trim(),
          ...getRateFields(),
        })

      setJournalReload(
        (current) =>
          current + 1,
      )

      resetForm()
      setShowForm(false)

    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setSaving(false)
    }
  }

  async function deleteIncome(
    income: IncomeEntry,
    ) {
    const confirmed =
        window.confirm(
        `Удалить доход «${income.description}»?`,
        )

    if (!confirmed) {
        return
    }

    setDeletingId(income.id)
    setError('')

    try {
        await deleteIncomeRequest(
        income.id,
        )

        setJournalReload(
          (current) =>
            current + 1,
        )
    } catch (requestError) {
        setError(
        getApiErrorMessage(
            requestError,
        ),
        )
    } finally {
        setDeletingId(null)
    }
  }
  
  function applyJournalFilters(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setActiveFilters({
      page: 1,
      page_size: 20,
      ordering:
        filterOrdering as
          IncomeFilters['ordering'],
      ...(searchQuery.trim()
        ? {
            search:
              searchQuery.trim(),
          }
        : {}),
      ...(dateFrom
        ? {
            date_from: dateFrom,
          }
        : {}),
      ...(dateTo
        ? {
            date_to: dateTo,
          }
        : {}),
      ...(filterAccount
        ? {
            account:
              Number(filterAccount),
          }
        : {}),
      ...(filterCurrency
        ? {
            currency:
              Number(filterCurrency),
          }
        : {}),
      ...(filterCategory
        ? {
            declaration_category:
              filterCategory,
          }
        : {}),
    })

    setShowFilters(false)
  }

  function clearJournalFilters() {
    setSearchQuery('')
    setDateFrom('')
    setDateTo('')
    setFilterAccount('')
    setFilterCurrency('')
    setFilterCategory('')
    setFilterOrdering(
      '-received_at',
    )

    setActiveFilters({
      page: 1,
      page_size: 20,
      ordering: '-received_at',
    })
  }

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем доходы...
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header incomes-header">
        <div>
          <p className="eyebrow">
            Финансы
          </p>

          <h1>Доходы</h1>

          <p className="muted">
            Журнал полученных доходов
            и GEL-эквивалентов
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setShowForm(
              (current) =>
                !current,
            )

            setError('')
          }}
        >
          {showForm
            ? 'Закрыть'
            : '+ Добавить доход'}
        </button>
      </header>

      {error && (
        <div className="error-box income-message">
          {error}
        </div>
      )}

      {showForm && (
        <section className="card income-form-card">
          <div className="section-heading">
            <div>
              <h2>
                Новый доход
              </h2>

              <p className="muted">
                Сначала рассчитаем
                сумму в GEL, затем
                сохраним запись.
              </p>
            </div>
          </div>

          <form
            className="form-grid"
            onSubmit={saveIncome}
          >
            <DateTimeField
                value={receivedAt}
                onChange={(value) => {
                    setReceivedAt(value)
                    invalidatePreview()
                }}
            />

            <label>
              Финансовый счёт

              <select
                value={accountId}
                onChange={(event) => {
                  const value =
                    event.target.value

                  setAccountId(value)

                  const account =
                    accounts.find(
                      (item) =>
                        item.id ===
                        Number(value),
                    )

                  if (account) {
                    setCurrencyId(
                        String(
                        account.default_currency,
                        ),
                    )

                    const accountCurrency =
                        currencies.find(
                        (currency) =>
                            currency.id ===
                            account.default_currency,
                        )

                    if (
                        accountCurrency?.kind ===
                        'crypto'
                    ) {
                        setRateMode('manual')
                    } else {
                        setRateMode('automatic')
                    }

                    setReadyAmountGel('')
                    setManualRate('')
                    setManualRateUnit('1')
                    setManualSource('')
                  }

                  invalidatePreview()
                }}
                required
              >
                {accounts
                  .filter(
                    (account) =>
                      account.is_active,
                  )
                  .map(
                    (account) => (
                      <option
                        key={account.id}
                        value={account.id}
                      >
                        {account.name}
                        {' — '}
                        {
                          account.default_currency_code
                        }
                      </option>
                    ),
                  )}
              </select>
            </label>

            <label className="wide">
              Описание дохода

              <input
                value={description}
                onChange={(event) =>
                  setDescription(
                    event.target.value,
                  )
                }
                placeholder="Например: Оплата за разработку сайта"
                required
              />
            </label>

            <label>
              Сумма

              <input
                type="number"
                min="0"
                step="any"
                value={amount}
                onChange={(event) => {
                  setAmount(
                    event.target.value,
                  )

                  invalidatePreview()
                }}
                required
              />
            </label>

            <label>
              Валюта

              <select
                value={currencyId}
                onChange={(event) => {
                    const value =
                        event.target.value

                    const currency =
                        currencies.find(
                        (item) =>
                            item.id ===
                            Number(value),
                        )

                    setCurrencyId(value)

                    setReadyAmountGel('')
                    setManualRate('')
                    setManualRateUnit('1')
                    setManualSource('')

                    if (
                        currency?.kind === 'crypto'
                    ) {
                        setRateMode('manual')
                    } else {
                        setRateMode('automatic')
                    }

                    invalidatePreview()
                }}
                required
              >
                <optgroup label="Обычные валюты">
                  {currencies
                    .filter(
                      (currency) =>
                        currency.kind ===
                        'fiat',
                    )
                    .map(
                      (currency) => (
                        <option
                          key={currency.id}
                          value={currency.id}
                        >
                          {currency.code}
                          {' — '}
                          {currency.name}
                        </option>
                      ),
                    )}
                </optgroup>

                <optgroup label="Криптовалюты">
                  {currencies
                    .filter(
                      (currency) =>
                        currency.kind ===
                        'crypto',
                    )
                    .map(
                      (currency) => (
                        <option
                          key={currency.id}
                          value={currency.id}
                        >
                          {currency.code}
                          {' — '}
                          {currency.name}
                        </option>
                      ),
                    )}
                </optgroup>
              </select>
            </label>

            {selectedCurrency &&
                selectedCurrency.code !==
                    'GEL' && (
                    <label>
                    Способ определения курса

                    <select
                        value={rateMode}
                        onChange={(event) => {
                        setRateMode(
                            event.target.value as
                            | 'automatic'
                            | 'manual'
                            | 'ready_gel',
                        )

                        setReadyAmountGel('')
                        setManualRate('')
                        setManualRateUnit('1')
                        setManualSource('')

                        invalidatePreview()
                        }}
                    >
                        {selectedCurrency.kind ===
                        'fiat' && (
                        <option value="automatic">
                            Автоматически по курсу NBG
                        </option>
                        )}

                        <option value="manual">
                        Ввести курс вручную
                        </option>

                        {selectedCurrency.kind ===
                        'crypto' && (
                        <option value="ready_gel">
                            Указать готовый GEL-эквивалент
                        </option>
                        )}
                    </select>
                    </label>
                )}

                {selectedCurrency &&
                selectedCurrency.code !==
                    'GEL' &&
                rateMode === 'manual' && (
                    <>
                    <label>
                        Количество единиц валюты

                        <input
                        type="number"
                        min="1"
                        step="1"
                        value={manualRateUnit}
                        onChange={(event) => {
                            setManualRateUnit(
                            event.target.value,
                            )

                            invalidatePreview()
                        }}
                        required
                        />

                        <small className="field-hint">
                        Например: 1 USD или
                        100 RUB
                        </small>
                    </label>

                    <label>
                        Курс к GEL

                        <input
                        type="number"
                        min="0"
                        step="any"
                        value={manualRate}
                        onChange={(event) => {
                            setManualRate(
                            event.target.value,
                            )

                            invalidatePreview()
                        }}
                        required
                        />

                        <small className="field-hint">
                        Сколько GEL соответствует
                        указанному количеству валюты
                        </small>
                    </label>

                    <label className="wide">
                        Источник курса

                        <input
                        value={manualSource}
                        onChange={(event) => {
                            setManualSource(
                            event.target.value,
                            )

                            invalidatePreview()
                        }}
                        placeholder="Например: TBC Bank"
                        />

                        <small className="field-hint">
                        Банк, биржа или другой
                        источник курса
                        </small>
                    </label>
                    </>
                )}

                {selectedCurrency &&
                selectedCurrency.code !==
                    'GEL' &&
                rateMode === 'ready_gel' && (
                    <label>
                    GEL-эквивалент

                    <input
                        type="number"
                        min="0"
                        step="any"
                        value={readyAmountGel}
                        onChange={(event) => {
                        setReadyAmountGel(
                            event.target.value,
                        )

                        invalidatePreview()
                        }}
                        required
                    />

                    <small className="field-hint">
                        Итоговая стоимость дохода
                        в грузинских лари
                    </small>
                    </label>
            )}

            <label>
                Способ оплаты

                <select
                    value={paymentMethod}
                    onChange={(event) =>
                    setPaymentMethod(
                        event.target.value,
                    )
                    }
                >
                    <option value="bank_transfer">
                    Банковский перевод
                    </option>

                    <option value="bank_card">
                    Банковская карта
                    </option>

                    <option value="cash">
                    Наличные
                    </option>

                    <option value="pos">
                    POS-терминал
                    </option>

                    <option value="payment_system">
                    Платёжная система
                    </option>

                    <option value="crypto">
                    Криптовалюта
                    </option>

                    <option value="barter">
                    Бартер
                    </option>

                    <option value="other">
                    Другое
                    </option>
                </select>
            </label>

            <label>
                Номер документа

                <input
                    value={documentNumber}
                    onChange={(event) =>
                    setDocumentNumber(
                        event.target.value,
                    )
                    }
                    placeholder="Например: INV-42"
                />

                <small className="field-hint">
                    Номер инвойса, акта, чека
                    или другого документа.
                    Позже доход можно будет
                    связать с соответствующим
                    инвойсом.
                </small>
            </label>

            <label>
                Дата документа

                <input
                    type="date"
                    lang="ru"
                    value={documentDate}
                    onChange={(event) =>
                    setDocumentDate(
                        event.target.value,
                    )
                    }
                />
            </label>

            <label>
              Графа декларации

              <select
                value={
                  declarationCategory
                }
                onChange={(event) => {
                  setDeclarationCategory(
                    event.target.value,
                  )

                  invalidatePreview()
                }}
              >
                <option value="">
                  Определить автоматически
                </option>

                {Object.entries(
                  CATEGORY_LABELS,
                ).map(
                  ([
                    value,
                    label,
                  ]) => (
                    <option
                      key={value}
                      value={value}
                    >
                      {label}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label className="wide">
              Комментарий

              <input
                value={comment}
                onChange={(event) =>
                  setComment(
                    event.target.value,
                  )
                }
              />
            </label>

            <div className="wide preview-actions">
              <button
                className="secondary"
                type="button"
                disabled={
                  previewLoading
                }
                onClick={() => {
                  void calculatePreview()
                }}
              >
                {previewLoading
                  ? 'Считаем...'
                  : 'Рассчитать в GEL'}
              </button>
            </div>

            {preview && (
              <div className="income-preview wide">
                <div>
                  <span className="muted">
                    Исходная сумма
                  </span>

                  <strong>
                    {
                      preview.data
                        .original_amount
                    }{' '}
                    {
                      preview.data
                        .currency
                    }
                  </strong>
                </div>

                <div>
                  <span className="muted">
                    Курс
                  </span>

                  <strong>
                    {
                      preview.data
                        .rate_unit
                    }{' '}
                    {
                      preview.data
                        .currency
                    }
                    {' = '}
                    {
                      preview.data
                        .rate_value
                    }{' '}
                    GEL
                  </strong>
                </div>

                <div>
                  <span className="muted">
                    Сумма в GEL
                  </span>

                  <strong className="preview-gel">
                    {
                      preview.data
                        .amount_gel
                    }{' '}
                    GEL
                  </strong>
                </div>

                <div>
                  <span className="muted">
                    Графа
                  </span>

                  <strong>
                    {
                      CATEGORY_LABELS[
                        declarationCategory ||
                          preview.data
                            .declaration_category
                      ]
                    }
                  </strong>
                </div>

                <div>
                  <span className="muted">
                    Источник
                  </span>

                  <strong>
                    {
                      preview.data
                        .source
                    }
                  </strong>
                </div>
              </div>
            )}

            <button
              className="form-submit"
              type="submit"
              disabled={
                saving ||
                !preview
              }
            >
              {saving
                ? 'Сохраняем...'
                : 'Сохранить доход'}
            </button>

            {!preview && (
              <small className="submit-hint">
                Перед сохранением сначала
                нажмите «Рассчитать в GEL».
              </small>
            )}
          </form>
        </section>
      )}

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>
              Журнал доходов
            </h2>

            <p className="muted">
              Всего записей:{' '}
              {totalCount}
            </p>
          </div>

          <div className="section-actions">
            <button
              type="button"
              className="secondary icon-button"
              onClick={() =>
                setShowFilters(
                  (current) => !current,
                )
              }
              aria-label="Открыть фильтры"
              title="Фильтры и поиск"
            >
              🔍
              {activeFilterCount > 0 &&
                ` ${activeFilterCount}`}
            </button>
          </div>
        </div>

        {showFilters && (
          <form
            className="income-filters"
            onSubmit={
              applyJournalFilters
            }
          >
            <label className="filter-search">
              Поиск

              <input
                value={searchQuery}
                onChange={(event) =>
                  setSearchQuery(
                    event.target.value,
                  )
                }
                placeholder="Описание, документ, комментарий..."
              />
            </label>

            <label>
              Дата от

              <input
                type="date"
                lang="ru"
                value={dateFrom}
                onChange={(event) =>
                  setDateFrom(
                    event.target.value,
                  )
                }
              />
            </label>

            <label>
              Дата до

              <input
                type="date"
                lang="ru"
                value={dateTo}
                onChange={(event) =>
                  setDateTo(
                    event.target.value,
                  )
                }
              />
            </label>

            <label>
              Финансовый счёт

              <select
                value={filterAccount}
                onChange={(event) =>
                  setFilterAccount(
                    event.target.value,
                  )
                }
              >
                <option value="">
                  Все счета
                </option>

                {accounts.map(
                  (account) => (
                    <option
                      key={account.id}
                      value={account.id}
                    >
                      {account.name}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Валюта

              <select
                value={filterCurrency}
                onChange={(event) =>
                  setFilterCurrency(
                    event.target.value,
                  )
                }
              >
                <option value="">
                  Все валюты
                </option>

                {currencies.map(
                  (currency) => (
                    <option
                      key={currency.id}
                      value={currency.id}
                    >
                      {currency.code}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Графа

              <select
                value={filterCategory}
                onChange={(event) =>
                  setFilterCategory(
                    event.target.value,
                  )
                }
              >
                <option value="">
                  Все графы
                </option>

                {Object.entries(
                  CATEGORY_LABELS,
                ).map(
                  ([
                    value,
                    label,
                  ]) => (
                    <option
                      key={value}
                      value={value}
                    >
                      {label}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Сортировка

              <select
                value={filterOrdering}
                onChange={(event) =>
                  setFilterOrdering(
                    event.target.value,
                  )
                }
              >
                <option value="-received_at">
                  Сначала новые
                </option>

                <option value="received_at">
                  Сначала старые
                </option>

                <option value="-amount_gel">
                  GEL: по убыванию
                </option>

                <option value="amount_gel">
                  GEL: по возрастанию
                </option>

                <option value="-original_amount">
                  Сумма: по убыванию
                </option>

                <option value="original_amount">
                  Сумма: по возрастанию
                </option>
              </select>
            </label>

            <div className="filter-actions">
              <button type="submit">
                Применить
              </button>

              <button
                type="button"
                className="secondary"
                onClick={
                  clearJournalFilters
                }
              >
                Сбросить
              </button>
            </div>
          </form>
        )}

        {journalLoading ? (
          <div className="empty-state">
            Загружаем журнал...
          </div>
        ) : incomes.length === 0 ? (
          <div className="empty-state">
            <h3>
              Доходов пока нет
            </h3>

            <p className="muted">
              Нажмите «Добавить доход»,
              чтобы создать первую
              запись.
            </p>
          </div>
        ) : (
          <div className="income-table">
            <div className="income-table-header">
              <span>Дата</span>
              <span>Описание</span>
              <span>Счёт</span>
              <span>Сумма</span>
              <span>GEL</span>
              <span>Графа</span>
              <span>Действия</span>
            </div>

            {incomes.map(
              (income) => {
                const currency =
                  currencies.find(
                    (item) =>
                      item.id ===
                      income.original_currency,
                  )

                const account =
                  accounts.find(
                    (item) =>
                      item.id ===
                      income.financial_account,
                  )

                return (
                  <div
                    key={income.id}
                    className="income-table-row"
                  >
                    <span>
                      {formatReceivedAt(
                        income.received_at,
                      )}
                    </span>

                    <strong>
                      {income.description}
                    </strong>

                    <span>
                      {account?.name ??
                        '—'}
                    </span>

                    <span>
                      {formatAmount(
                        income.original_amount,
                      )}{' '}
                      {currency?.code ?? ''}
                    </span>

                    <strong>
                      {formatAmount(
                        income.amount_gel,
                      )}{' '}
                      GEL
                    </strong>

                    <span>
                      {
                        CATEGORY_LABELS[
                          income
                            .declaration_category
                        ]
                      }
                    </span>

                    <div className="income-actions">
                        <Link
                            className="income-edit-button"
                            to={`/incomes/${income.id}/edit`}
                        >
                            Редактировать
                        </Link>

                        <button
                            type="button"
                            className="income-delete-button"
                            disabled={
                            deletingId === income.id
                            }
                            onClick={() => {
                            void deleteIncome(
                                income,
                            )
                            }}
                        >
                            {deletingId === income.id
                            ? 'Удаляем...'
                            : 'Удалить'}
                        </button>
                    </div>
                  </div>
                )
              },
            )}
          </div>
        )}
        {totalCount > 0 && (
          <div className="journal-pagination">
            <button
              type="button"
              className="secondary"
              disabled={
                !hasPreviousPage ||
                journalLoading
              }
              onClick={() =>
                setActiveFilters(
                  (current) => ({
                    ...current,
                    page: Math.max(
                      1,
                      (current.page ?? 1) -
                        1,
                    ),
                  }),
                )
              }
            >
              ← Назад
            </button>

            <span>
              Страница{' '}
              {activeFilters.page ?? 1}
              {' из '}
              {Math.max(
                1,
                Math.ceil(
                  totalCount /
                    (
                      activeFilters.page_size ??
                      20
                    ),
                ),
              )}
            </span>

            <button
              type="button"
              className="secondary"
              disabled={
                !hasNextPage ||
                journalLoading
              }
              onClick={() =>
                setActiveFilters(
                  (current) => ({
                    ...current,
                    page:
                      (current.page ?? 1) +
                      1,
                  }),
                )
              }
            >
              Далее →
            </button>
          </div>
        )}
      </section>

      {selectedAccount &&
        selectedCurrency && (
          <p className="muted income-footnote">
            Текущий счёт:{' '}
            {selectedAccount.name}.
            Валюта:{' '}
            {selectedCurrency.code}.
          </p>
        )}
    </main>
  )
}