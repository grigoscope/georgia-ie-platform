import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  loginRequest,
} from '../api/auth'

import {
  linkTelegramRequest,
  telegramMiniAppAuthRequest,
} from '../api/telegram'

import {
  getIncomesRequest,
  type IncomeEntry,
} from '../api/incomes'

import {
  getInvoicesRequest,
  type Invoice,
} from '../api/invoices'

import {
  getTaxPeriodsRequest,
  type TaxPeriod,
} from '../api/taxes'

import {
  getCurrenciesRequest,
  type Currency,
} from '../api/finances'

import {
  MiniIncomeForm,
} from '../components/MiniIncomeForm'

import {
  getDashboardRequest,
  type DashboardData,
} from '../api/reports'

import {
  MiniInvoicesSection,
} from '../components/MiniInvoicesSection'

type MiniAppState =
  | 'loading'
  | 'login'
  | 'ready'
  | 'error'

type MiniSection =
  | 'home'
  | 'incomes'
  | 'invoices'
  | 'taxes'

const INVOICE_STATUS_LABELS:
  Record<string, string> = {
    draft: 'Черновик',
    pending: 'Ожидает оплаты',
    partially_paid:
      'Частично оплачен',
    paid: 'Оплачен',
    cancelled: 'Отменён',
  }

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

function formatAmount(
  value: string | number,
) {
  const amount = Number(value)

  if (Number.isNaN(amount)) {
    return String(value)
  }

  return new Intl.NumberFormat(
    'ru-RU',
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(amount)
}

function formatDateTime(
  value: string,
) {
  return new Intl.DateTimeFormat(
    'ru-RU',
    {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Tbilisi',
    },
  ).format(
    new Date(value),
  )
}

function formatDate(
  value: string | null,
) {
  if (!value) {
    return '—'
  }

  return new Intl.DateTimeFormat(
    'ru-RU',
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}

function getBuyerName(
  invoice: Invoice,
) {
  const name =
    invoice
      .buyer_snapshot
      .name

  if (
    typeof name === 'string' &&
    name
  ) {
    return name
  }

  return 'Контрагент'
}

export function MiniAppPage() {
  const [
    state,
    setState,
  ] = useState<MiniAppState>(
    'loading',
  )

  const [
    section,
    setSection,
  ] = useState<MiniSection>(
    'home',
  )

  const [
    email,
    setEmail,
  ] = useState('')

  const [
    password,
    setPassword,
  ] = useState('')

  const [
    error,
    setError,
  ] = useState('')

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    dataLoading,
    setDataLoading,
  ] = useState(false)

  const [
    incomes,
    setIncomes,
  ] = useState<IncomeEntry[]>(
    [],
  )

  const [
    invoices,
    setInvoices,
  ] = useState<Invoice[]>(
    [],
  )

  const [
    taxPeriods,
    setTaxPeriods,
  ] = useState<TaxPeriod[]>(
    [],
  )

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>(
    [],
  )

  const [
  dashboard,
  setDashboard,
] = useState<DashboardData | null>(
  null,
)

  const loadData =
    useCallback(
      async () => {
        setDataLoading(true)
        setError('')

        try {
          const [
            incomesResult,
            invoicesResult,
            taxesResult,
            currenciesResult,
            dashboardResult,
          ] = await Promise.all([
            getIncomesRequest({
              page: 1,
              page_size: 5,
              ordering:
                '-received_at',
            }),

            getInvoicesRequest({
              page: 1,
              page_size: 5,
              ordering:
                '-issue_date',
            }),

            getTaxPeriodsRequest(),

            getCurrenciesRequest(),

            getDashboardRequest(),
          ])

          setIncomes(
            incomesResult.results,
          )

          setInvoices(
            invoicesResult.results,
          )

          setTaxPeriods(
            taxesResult,
          )

          setCurrencies(
            currenciesResult,
          )

          setDashboard(
            dashboardResult,
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
          setDataLoading(false)
        }
      },
      [],
    )

  useEffect(() => {
    async function bootstrap() {
      const webApp =
        window.Telegram?.WebApp

      if (!webApp) {
        setError(
          'Страница открыта не внутри Telegram',
        )

        setState('error')

        return
      }

      webApp.ready()
      webApp.expand()

      const initData =
        webApp.initData

      if (!initData) {
        setError(
          'Telegram не передал initData',
        )

        setState('error')

        return
      }

      try {
        await telegramMiniAppAuthRequest(
          initData,
        )

        setState('ready')
      } catch {
        setState('login')
      }
    }

    void bootstrap()
  }, [])

  useEffect(() => {
    if (state === 'ready') {
      void loadData()
    }
  }, [
    state,
    loadData,
  ])

  useEffect(() => {
    if (state !== 'ready') {
      return
    }

    const intervalId =
      window.setInterval(
        () => {
          void loadData()
        },
        15000,
      )

    return () => {
      window.clearInterval(
        intervalId,
      )
    }
  }, [
    state,
    loadData,
  ])

  async function loginAndLink(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const initData =
      window
        .Telegram
        ?.WebApp
        .initData ?? ''

    if (!initData) {
      setError(
        'Telegram не передал initData',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      await loginRequest(
        email.trim(),
        password,
      )

      await linkTelegramRequest(
        initData,
      )

      setState('ready')
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

  function currencyCode(
    currencyId: number,
  ) {
    return (
      currencies.find(
        (currency) =>
          currency.id ===
          currencyId,
      )?.code ?? ''
    )
  }

  if (
    state === 'loading'
  ) {
    return (
      <main className="mini-app-page">
        <div className="mini-app-card">
          Подключаем Telegram...
        </div>
      </main>
    )
  }

  if (
    state === 'error'
  ) {
    return (
      <main className="mini-app-page">
        <div className="mini-app-card">
          <p className="eyebrow">
            Georgia IE
          </p>

          <h1>
            Mini App
          </h1>

          <div className="error-box">
            {error}
          </div>
        </div>
      </main>
    )
  }

  if (
    state === 'login'
  ) {
    return (
      <main className="mini-app-page">
        <form
          className="mini-app-card mini-login-card"
          onSubmit={
            loginAndLink
          }
        >
          <div>
            <p className="eyebrow">
              Telegram
            </p>

            <h1>
              Georgia IE
            </h1>

            <p className="muted">
              Войдите в аккаунт,
              чтобы привязать
              Telegram.
            </p>
          </div>

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

          <label>
            Email

            <input
              type="email"
              value={email}
              onChange={(
                event,
              ) =>
                setEmail(
                  event.target
                    .value,
                )
              }
              required
            />
          </label>

          <label>
            Пароль

            <input
              type="password"
              value={password}
              onChange={(
                event,
              ) =>
                setPassword(
                  event.target
                    .value,
                )
              }
              required
            />
          </label>

          <button
            type="submit"
            disabled={saving}
          >
            {saving
              ? 'Подключаем...'
              : 'Войти'}
          </button>
        </form>
      </main>
    )
  }

  const nowInTbilisi =
    new Date(
      new Date().toLocaleString(
        'en-US',
        {
          timeZone:
            'Asia/Tbilisi',
        },
      ),
    )

  const currentYear =
    nowInTbilisi.getFullYear()

  const currentMonth =
    nowInTbilisi.getMonth() + 1

  const currentTaxPeriod =
    taxPeriods.find(
      (period) =>
        period.year ===
          currentYear &&
        period.month ===
          currentMonth,
    ) ?? null

  const unpaidInvoices =
    invoices.filter(
      (invoice) =>
        invoice.status ===
          'pending' ||
        invoice.status ===
          'partially_paid',
    ).length

  return (
    <main className="mini-app-page">
      <header className="mini-app-header">
        <div>
          <p className="eyebrow">
            Georgia IE
          </p>

          <h1>
            Accounting
          </h1>
        </div>

        <button
          type="button"
          className="mini-refresh-button"
          disabled={
            dataLoading
          }
          onClick={() => {
            void loadData()
          }}
        >
          {dataLoading
            ? '...'
            : '↻'}
        </button>
      </header>

      {error && (
        <div className="error-box mini-message">
          {error}
        </div>
      )}

      <nav className="mini-nav">
        <button
          type="button"
          className={
            section === 'home'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection('home')
          }
        >
          Главная
        </button>

        <button
          type="button"
          className={
            section ===
            'incomes'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection(
              'incomes',
            )
          }
        >
          Доходы
        </button>

        <button
          type="button"
          className={
            section ===
            'invoices'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection(
              'invoices',
            )
          }
        >
          Инвойсы
        </button>

        <button
          type="button"
          className={
            section === 'taxes'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection('taxes')
          }
        >
          Налоги
        </button>
      </nav>

      {dataLoading &&
      incomes.length === 0 ? (
        <section className="mini-app-card">
          Загружаем данные...
        </section>
      ) : (
        <>
          {section ===
            'home' && (
            <section className="mini-section">
              <div className="mini-summary-grid">
                <div className="mini-summary-card">
                  <span>
                    Доход за месяц
                  </span>

                  <strong>
                    {dashboard
                      ? formatAmount(
                          dashboard
                            .current_month
                            .total_gel,
                        )
                      : '—'}{' '}
                    {dashboard
                      ? 'GEL'
                      : ''}
                  </strong>
                </div>

                <div className="mini-summary-card">
                  <span>
                    Налог
                  </span>

                  <strong>
                    {currentTaxPeriod
                      ? `${formatAmount(
                          currentTaxPeriod
                            .field_26,
                        )} GEL`
                      : 'Не рассчитан'}
                  </strong>
                </div>

                <div className="mini-summary-card">
                  <span>
                    Ждут оплаты
                  </span>

                  <strong>
                    {
                      unpaidInvoices
                    }
                  </strong>
                </div>
              </div>

              <div className="mini-app-card">
                <div className="mini-section-heading">
                  <div>
                    <h2>
                      Последние доходы
                    </h2>

                    <p className="muted">
                      Последние
                      поступления
                    </p>
                  </div>

                  <button
                    type="button"
                    className="mini-text-button"
                    onClick={() =>
                      setSection(
                        'incomes',
                      )
                    }
                  >
                    Все
                  </button>
                </div>

                {incomes.length ===
                0 ? (
                  <div className="mini-empty">
                    Доходов пока нет
                  </div>
                ) : (
                  <div className="mini-list">
                    {incomes
                      .slice(0, 3)
                      .map(
                        (
                          income,
                        ) => (
                          <div
                            key={
                              income.id
                            }
                            className="mini-list-row"
                          >
                            <div>
                              <strong>
                                {
                                  income.description
                                }
                              </strong>

                              <span>
                                {formatDateTime(
                                  income.received_at,
                                )}
                              </span>
                            </div>

                            <strong className="mini-money">
                              {formatAmount(
                                income.original_amount,
                              )}{' '}
                              {currencyCode(
                                income.original_currency,
                              )}
                            </strong>
                          </div>
                        ),
                      )}
                  </div>
                )}
              </div>

              <div className="mini-app-card">
                <div className="mini-section-heading">
                  <div>
                    <h2>
                      Инвойсы
                    </h2>

                    <p className="muted">
                      Последние счета
                    </p>
                  </div>

                  <button
                    type="button"
                    className="mini-text-button"
                    onClick={() =>
                      setSection(
                        'invoices',
                      )
                    }
                  >
                    Все
                  </button>
                </div>

                {invoices.length ===
                0 ? (
                  <div className="mini-empty">
                    Инвойсов пока нет
                  </div>
                ) : (
                  <div className="mini-list">
                    {invoices
                      .slice(0, 3)
                      .map(
                        (
                          invoice,
                        ) => (
                          <div
                            key={
                              invoice.id
                            }
                            className="mini-list-row"
                          >
                            <div>
                              <strong>
                                {
                                  invoice.number
                                }
                              </strong>

                              <span>
                                {getBuyerName(
                                  invoice,
                                )}
                              </span>
                            </div>

                            <div className="mini-list-right">
                              <strong>
                                {formatAmount(
                                  invoice.total_amount,
                                )}{' '}
                                {currencyCode(
                                  invoice.currency,
                                )}
                              </strong>

                              <span
                                className={
                                  `mini-status ` +
                                  `mini-status-${invoice.status}`
                                }
                              >
                                {INVOICE_STATUS_LABELS[
                                  invoice.status
                                ] ??
                                  invoice.status}
                              </span>
                            </div>
                          </div>
                        ),
                      )}
                  </div>
                )}
              </div>
            </section>
          )}

          {section ===
            'incomes' && (
            <section className="mini-app-card">
              <div className="mini-section-heading">
                <div>
                  <p className="eyebrow">
                    Журнал
                  </p>

                  <h2>
                    Доходы
                  </h2>
                </div>
              </div>

              <MiniIncomeForm
                onSaved={loadData}
              />

              {incomes.length ===
              0 ? (
                <div className="mini-empty">
                  Доходов пока нет
                </div>
              ) : (
                <div className="mini-list">
                  {incomes.map(
                    (
                      income,
                    ) => (
                      <div
                        key={
                          income.id
                        }
                        className="mini-list-row"
                      >
                        <div>
                          <strong>
                            {
                              income.description
                            }
                          </strong>

                          <span>
                            {formatDateTime(
                              income.received_at,
                            )}
                          </span>

                          <span>
                            В GEL:{' '}
                            {formatAmount(
                              income.amount_gel,
                            )}
                          </span>
                        </div>

                        <strong className="mini-money">
                          {formatAmount(
                            income.original_amount,
                          )}{' '}
                          {currencyCode(
                            income.original_currency,
                          )}
                        </strong>
                      </div>
                    ),
                  )}
                </div>
              )}
            </section>
          )}

          {section ===
            'invoices' && (
            <MiniInvoicesSection
              invoices={invoices}
              currencies={currencies}
              onRefresh={loadData}
            />
          )}

          {section ===
            'taxes' && (
            <section className="mini-app-card">
              <div className="mini-section-heading">
                <div>
                  <p className="eyebrow">
                    Декларации
                  </p>

                  <h2>
                    Налоги
                  </h2>
                </div>
              </div>

              {taxPeriods.length ===
              0 ? (
                <div className="mini-empty">
                  Налоговых периодов
                  пока нет
                </div>
              ) : (
                <div className="mini-list">
                  {taxPeriods
                    .slice(0, 6)
                    .map(
                      (
                        period,
                      ) => (
                        <div
                          key={
                            period.id
                          }
                          className="mini-tax-card"
                        >
                          <div className="mini-tax-heading">
                            <div>
                              <strong>
                                {
                                  MONTHS[
                                    period.month -
                                      1
                                  ]
                                }{' '}
                                {
                                  period.year
                                }
                              </strong>

                              <span>
                                Срок:{' '}
                                {formatDate(
                                  period.deadline,
                                )}
                              </span>
                            </div>

                            {period.is_overdue && (
                              <span className="mini-overdue">
                                Просрочено
                              </span>
                            )}
                          </div>

                          <div className="mini-tax-values">
                            <div>
                              <span>
                                Доход
                              </span>

                              <strong>
                                {formatAmount(
                                  period.field_17,
                                )}{' '}
                                GEL
                              </strong>
                            </div>

                            <div>
                              <span>
                                Налог
                              </span>

                              <strong>
                                {formatAmount(
                                  period.field_26,
                                )}{' '}
                                GEL
                              </strong>
                            </div>
                          </div>

                          <div className="mini-tax-statuses">
                            <span>
                              Декларация:{' '}
                              {period.declaration_status ===
                              'submitted'
                                ? 'подана'
                                : 'не подана'}
                            </span>

                            <span>
                              Оплата:{' '}
                              {period.payment_status ===
                              'paid'
                                ? 'оплачено'
                                : 'не оплачено'}
                            </span>
                          </div>
                        </div>
                      ),
                    )}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </main>
  )
}