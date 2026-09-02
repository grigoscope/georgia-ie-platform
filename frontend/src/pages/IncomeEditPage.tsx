import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  Link,
  useNavigate,
  useParams,
} from 'react-router-dom'

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
  getIncomeRequest,
  previewIncomeRequest,
  updateIncomeRequest,
  type IncomeEntry,
  type IncomePreview,
} from '../api/incomes'

import {
  DateTimeField,
} from '../components/DateTimeField'

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

type RateMode =
  | 'automatic'
  | 'manual'
  | 'ready_gel'

function toTbilisiInput(
  value: string,
) {
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
      new Date(value),
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

function getRateMode(
  income: IncomeEntry,
): RateMode {
  if (
    income.exchange_rate_source ===
    'provided_gel_equivalent'
  ) {
    return 'ready_gel'
  }

  if (
    income.exchange_rate_source ===
      'NBG' ||
    income.exchange_rate_source ===
      'GEL' ||
    income.exchange_rate_source ===
      'SYSTEM'
  ) {
    return 'automatic'
  }

  return 'manual'
}

export function IncomeEditPage() {
  const { id } = useParams()

  const navigate = useNavigate()

  const [
    income,
    setIncome,
  ] = useState<IncomeEntry | null>(
    null,
  )

  const [
    accounts,
    setAccounts,
  ] = useState<FinancialAccount[]>(
    [],
  )

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>([])

  const [loading, setLoading] =
    useState(true)

  const [saving, setSaving] =
    useState(false)

  const [
    previewLoading,
    setPreviewLoading,
  ] = useState(false)

  const [error, setError] =
    useState('')

  const [
    preview,
    setPreview,
  ] = useState<IncomePreview | null>(
    null,
  )

  const [
    receivedAt,
    setReceivedAt,
  ] = useState('')

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
  ] = useState<RateMode>(
    'automatic',
  )

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
    readyAmountGel,
    setReadyAmountGel,
  ] = useState('')

  const selectedCurrency =
    currencies.find(
      (currency) =>
        currency.id ===
        Number(currencyId),
    ) ?? null

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const incomeId =
          Number(id)

        if (!incomeId) {
          throw new Error(
            'Некорректный ID дохода',
          )
        }

        const [
          incomeResult,
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getIncomeRequest(
            incomeId,
          ),
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        if (cancelled) {
          return
        }

        setIncome(incomeResult)
        setAccounts(accountsResult)
        setCurrencies(
          currenciesResult,
        )

        setReceivedAt(
          toTbilisiInput(
            incomeResult.received_at,
          ),
        )

        setDescription(
          incomeResult.description,
        )

        setAccountId(
          String(
            incomeResult
              .financial_account,
          ),
        )

        setCurrencyId(
          String(
            incomeResult
              .original_currency,
          ),
        )

        setAmount(
          incomeResult.original_amount,
        )

        setDeclarationCategory(
          incomeResult
            .declaration_category,
        )

        setPaymentMethod(
          incomeResult.payment_method ||
            'bank_transfer',
        )

        setDocumentNumber(
          incomeResult.document_number,
        )

        setDocumentDate(
          incomeResult.document_date ??
            '',
        )

        setComment(
          incomeResult.comment,
        )

        const mode =
          getRateMode(
            incomeResult,
          )

        setRateMode(mode)

        if (mode === 'manual') {
          setManualRate(
            incomeResult
              .exchange_rate_value,
          )

          setManualRateUnit(
            String(
              incomeResult
                .exchange_rate_unit,
            ),
          )

          setManualSource(
            incomeResult
              .exchange_rate_source,
          )
        }

        if (
          mode === 'ready_gel'
        ) {
          setReadyAmountGel(
            incomeResult.amount_gel,
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
  }, [id])

  function invalidatePreview() {
    setPreview(null)
  }

  function getRateFields() {
    if (
      !selectedCurrency ||
      selectedCurrency.code ===
        'GEL'
    ) {
      return {}
    }

    if (
      rateMode === 'manual'
    ) {
      return {
        manual_rate_value:
          manualRate,
        manual_rate_unit:
          Number(
            manualRateUnit,
          ),
        manual_source:
          manualSource.trim() ||
          'Ручной ввод',
      }
    }

    if (
      rateMode === 'ready_gel'
    ) {
      return {
        ready_amount_gel:
          readyAmountGel,
      }
    }

    return {}
  }

  async function calculatePreview() {
    setError('')
    setPreviewLoading(true)

    try {
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
          declaration_category:
            declarationCategory,
          ...getRateFields(),
        })

      setPreview(result)
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

    if (!income) {
      return
    }

    if (!preview) {
      setError(
        'Перед сохранением пересчитайте сумму в GEL',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      await updateIncomeRequest(
        income.id,
        {
          received_at:
            toTbilisiIso(
              receivedAt,
            ),
          description:
            description.trim(),
          financial_account:
            Number(accountId),
          payment_method:
            paymentMethod,
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
          comment:
            comment.trim(),
          ...getRateFields(),
        },
      )

      navigate('/incomes')
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

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем доход...
        </div>
      </main>
    )
  }

  if (!income) {
    return (
      <main className="page">
        <div className="error-box">
          Доход не найден
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header">
        <p className="eyebrow">
          Доходы
        </p>

        <h1>
          Редактирование дохода
        </h1>

        <Link
          to="/incomes"
          className="text-button"
        >
          ← Вернуться к журналу
        </Link>
      </header>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      <section className="card">
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
                setAccountId(
                  event.target.value,
                )

                invalidatePreview()
              }}
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
                    </option>
                  ),
                )}
            </select>
          </label>

          <label className="wide">
            Описание

            <input
              value={description}
              onChange={(event) =>
                setDescription(
                  event.target.value,
                )
              }
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

                setCurrencyId(value)

                const currency =
                  currencies.find(
                    (item) =>
                      item.id ===
                      Number(value),
                  )

                setRateMode(
                  currency?.kind ===
                    'crypto'
                    ? 'manual'
                    : 'automatic',
                )

                invalidatePreview()
              }}
            >
              {currencies.map(
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
                      event.target
                        .value as RateMode,
                    )

                    invalidatePreview()
                  }}
                >
                  {selectedCurrency.kind ===
                    'fiat' && (
                    <option value="automatic">
                      Автоматически NBG
                    </option>
                  )}

                  <option value="manual">
                    Вручную
                  </option>

                  {selectedCurrency.kind ===
                    'crypto' && (
                    <option value="ready_gel">
                      Готовый GEL-эквивалент
                    </option>
                  )}
                </select>
              </label>
            )}

          {rateMode === 'manual' &&
            selectedCurrency?.code !==
              'GEL' && (
              <>
                <label>
                  Количество единиц

                  <input
                    type="number"
                    min="1"
                    value={
                      manualRateUnit
                    }
                    onChange={(event) => {
                      setManualRateUnit(
                        event.target.value,
                      )

                      invalidatePreview()
                    }}
                  />
                </label>

                <label>
                  Курс к GEL

                  <input
                    type="number"
                    step="any"
                    value={manualRate}
                    onChange={(event) => {
                      setManualRate(
                        event.target.value,
                      )

                      invalidatePreview()
                    }}
                  />
                </label>

                <label>
                  Источник курса

                  <input
                    value={manualSource}
                    onChange={(event) => {
                      setManualSource(
                        event.target.value,
                      )

                      invalidatePreview()
                    }}
                  />
                </label>
              </>
            )}

          {rateMode ===
            'ready_gel' && (
            <label>
              GEL-эквивалент

              <input
                type="number"
                step="any"
                value={readyAmountGel}
                onChange={(event) => {
                  setReadyAmountGel(
                    event.target.value,
                  )

                  invalidatePreview()
                }}
              />
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
            />
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
              onChange={(event) =>
                setDeclarationCategory(
                  event.target.value,
                )
              }
            >
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
              type="button"
              className="secondary"
              disabled={
                previewLoading
              }
              onClick={() => {
                void calculatePreview()
              }}
            >
              {previewLoading
                ? 'Считаем...'
                : 'Пересчитать в GEL'}
            </button>
          </div>

          {preview && (
            <div className="income-preview wide">
              <div>
                <span className="muted">
                  Курс
                </span>

                <strong>
                  {preview.data.rate_unit}{' '}
                  {preview.data.currency}
                  {' = '}
                  {preview.data.rate_value}{' '}
                  GEL
                </strong>
              </div>

              <div>
                <span className="muted">
                  Сумма в GEL
                </span>

                <strong className="preview-gel">
                  {preview.data.amount_gel}{' '}
                  GEL
                </strong>
              </div>

              <div>
                <span className="muted">
                  Дата курса
                </span>

                <strong>
                  {
                    preview.data
                      .rate_date
                  }
                </strong>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={
              saving ||
              !preview
            }
          >
            {saving
              ? 'Сохраняем...'
              : 'Сохранить изменения'}
          </button>

          {!preview && (
            <small className="submit-hint">
              После изменения данных
              сначала пересчитайте сумму
              в GEL.
            </small>
          )}
        </form>
      </section>
    </main>
  )
}