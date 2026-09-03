import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  generateTaxPeriodRequest,
  getTaxPeriodsRequest,
  recalculateTaxPeriodRequest,
  type TaxPeriod,
} from '../api/taxes'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  Link,
} from 'react-router-dom'

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
  value: string,
) {
  const number = Number(value)

  if (Number.isNaN(number)) {
    return value
  }

  return new Intl.NumberFormat(
    'ru-RU',
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(number)
}

function getTbilisiDate() {
  const parts =
    new Intl.DateTimeFormat(
      'en-CA',
      {
        timeZone: 'Asia/Tbilisi',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
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

export function TaxesPage() {
  const current =
    getTbilisiDate()

  const [
    periods,
    setPeriods,
  ] = useState<TaxPeriod[]>([])

  const [
    year,
    setYear,
  ] = useState(
    current.year,
  )

  const [
    month,
    setMonth,
  ] = useState(
    current.month,
  )

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    actionLoading,
    setActionLoading,
  ] = useState<
    number | 'generate' | null
  >(null)

  const [
    error,
    setError,
  ] = useState('')

  async function loadPeriods() {
    try {
      const result =
        await getTaxPeriodsRequest()

      setPeriods(result)
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadPeriods()
  }, [])

  async function generatePeriod(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setActionLoading(
      'generate',
    )

    setError('')

    try {
      await generateTaxPeriodRequest(
        year,
        month,
      )

      await loadPeriods()
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading(null)
    }
  }

  async function recalculate(
    periodId: number,
  ) {
    setActionLoading(
      periodId,
    )

    setError('')

    try {
      await recalculateTaxPeriodRequest(
        periodId,
      )

      await loadPeriods()
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем налоговые
          периоды...
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header">
        <p className="eyebrow">
          Налоги
        </p>

        <h1>
          Налоговые периоды
        </h1>

        <p className="muted">
          Расчёт декларации
          по доходам
        </p>
      </header>

      {error && (
        <div className="error-box tax-message">
          {error}
        </div>
      )}

      <section className="card tax-generate-card">
        <div>
          <h2>
            Рассчитать месяц
          </h2>

          <p className="muted">
            Данные берутся из
            журнала доходов.
          </p>
        </div>

        <form
          className="tax-generate-form"
          onSubmit={
            generatePeriod
          }
        >
          <label>
            Месяц

            <select
              value={month}
              onChange={(event) =>
                setMonth(
                  Number(
                    event.target.value,
                  ),
                )
              }
            >
              {MONTHS.map(
                (
                  name,
                  index,
                ) => (
                  <option
                    key={name}
                    value={index + 1}
                  >
                    {name}
                  </option>
                ),
              )}
            </select>
          </label>

          <label>
            Год

            <input
              type="number"
              min="2000"
              max="2200"
              value={year}
              onChange={(event) =>
                setYear(
                  Number(
                    event.target.value,
                  ),
                )
              }
            />
          </label>

          <button
            type="submit"
            disabled={
              actionLoading ===
              'generate'
            }
          >
            {actionLoading ===
            'generate'
              ? 'Считаем...'
              : 'Рассчитать'}
          </button>
        </form>
      </section>

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>
              История периодов
            </h2>

            <p className="muted">
              Всего:{' '}
              {periods.length}
            </p>
          </div>
        </div>

        {periods.length === 0 ? (
          <div className="empty-state">
            <h3>
              Периодов пока нет
            </h3>

            <p className="muted">
              Рассчитайте первый
              месяц выше.
            </p>
          </div>
        ) : (
          <div className="tax-period-list">
            {periods.map(
              (period) => (
                <div
                  key={period.id}
                  className={
                    `tax-period-card ` +
                    (
                      period.is_overdue
                        ? 'overdue'
                        : ''
                    )
                  }
                >
                  <div className="tax-period-title">
                    <div>
                      <h3>
                        {
                          MONTHS[
                            period.month -
                              1
                          ]
                        }{' '}
                        {
                          period.year
                        }
                      </h3>

                      <p className="muted">
                        Срок:{' '}
                        {
                          period.deadline
                        }
                      </p>
                    </div>

                    {period.is_overdue && (
                      <span className="tax-overdue">
                        Просрочено
                      </span>
                    )}
                  </div>

                  <div className="tax-period-stats">
                    <div>
                      <span className="muted">
                        Доход за месяц
                      </span>

                      <strong>
                        {formatAmount(
                          period.field_17,
                        )}{' '}
                        GEL
                      </strong>
                    </div>

                    <div>
                      <span className="muted">
                        Нарастающий итог
                      </span>

                      <strong>
                        {formatAmount(
                          period.field_15,
                        )}{' '}
                        GEL
                      </strong>
                    </div>

                    <div>
                      <span className="muted">
                        Ставка
                      </span>

                      <strong>
                        {
                          period.tax_rate
                        }
                        %
                      </strong>
                    </div>

                    <div>
                      <span className="muted">
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

                  <div className="tax-period-categories">
                    <span>
                      18:{' '}
                      {formatAmount(
                        period.field_18,
                      )}
                    </span>

                    <span>
                      19:{' '}
                      {formatAmount(
                        period.field_19,
                      )}
                    </span>

                    <span>
                      20:{' '}
                      {formatAmount(
                        period.field_20,
                      )}
                    </span>

                    <span>
                      21:{' '}
                      {formatAmount(
                        period.field_21,
                      )}
                    </span>
                  </div>

                  <div className="tax-period-footer">
                    <div className="tax-statuses">
                        <span>
                        Декларация:{' '}
                        {period.declaration_status ===
                        'submitted'
                            ? 'Подана'
                            : 'Не подана'}
                        </span>

                        <span>
                        Оплата:{' '}
                        {period.payment_status ===
                        'paid'
                            ? 'Оплачено'
                            : 'Не оплачено'}
                        </span>
                    </div>

                    <div className="tax-period-actions">
                        <Link
                        to={`/taxes/${period.id}`}
                        className="income-edit-button"
                        >
                        Открыть
                        </Link>

                        <button
                        type="button"
                        className="secondary"
                        disabled={
                            actionLoading ===
                            period.id
                        }
                        onClick={() => {
                            void recalculate(
                            period.id,
                            )
                        }}
                        >
                        {actionLoading ===
                        period.id
                            ? 'Пересчитываем...'
                            : 'Пересчитать'}
                        </button>
                    </div>
                  </div>

                  {period.changed_after_submission && (
                    <div className="tax-warning">
                      Данные изменились
                      после подачи
                      декларации.
                    </div>
                  )}
                </div>
              ),
            )}
          </div>
        )}
      </section>
    </main>
  )
}