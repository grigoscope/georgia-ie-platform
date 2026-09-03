import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  Link,
  useParams,
} from 'react-router-dom'

import {
  getTaxPeriodRequest,
  markTaxPaidRequest,
  markTaxSubmittedRequest,
  recalculateTaxPeriodRequest,
  unmarkTaxPaidRequest,
  unmarkTaxSubmittedRequest,
  type TaxPeriod,
} from '../api/taxes'

import {
  getApiErrorMessage,
} from '../api/client'

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
  const amount = Number(value)

  if (Number.isNaN(amount)) {
    return value
  }

  return new Intl.NumberFormat(
    'ru-RU',
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(amount)
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

function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return '—'
  }

  return new Intl.DateTimeFormat(
    'ru-RU',
    {
      dateStyle: 'short',
      timeStyle: 'short',
      timeZone: 'Asia/Tbilisi',
    },
  ).format(
    new Date(value),
  )
}

export function TaxPeriodDetailPage() {
  const { id } =
    useParams()

  const periodId =
    Number(id)

  const [
    period,
    setPeriod,
  ] = useState<TaxPeriod | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    error,
    setError,
  ] = useState('')

  const [
    actionLoading,
    setActionLoading,
  ] = useState('')

  const [
    showSubmissionForm,
    setShowSubmissionForm,
  ] = useState(false)

  const [
    submissionComment,
    setSubmissionComment,
  ] = useState('')

  const [
    submissionFile,
    setSubmissionFile,
  ] = useState<File | null>(
    null,
  )

  const [
    showPaymentForm,
    setShowPaymentForm,
  ] = useState(false)

  const [
    paidAmount,
    setPaidAmount,
  ] = useState('')

  const [
    paymentComment,
    setPaymentComment,
  ] = useState('')

  const [
    paymentFile,
    setPaymentFile,
  ] = useState<File | null>(
    null,
  )

  const loadPeriod =
    useCallback(
      async () => {
        if (
          !Number.isInteger(
            periodId,
          )
        ) {
          setError(
            'Некорректный ID периода',
          )

          setLoading(false)

          return
        }

        try {
          const result =
            await getTaxPeriodRequest(
              periodId,
            )

          setPeriod(result)

          setPaidAmount(
            result.field_26,
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
          setLoading(false)
        }
      },
      [periodId],
    )

  useEffect(() => {
    void loadPeriod()
  }, [loadPeriod])

  async function recalculate() {
    setActionLoading(
      'recalculate',
    )

    setError('')

    try {
      await recalculateTaxPeriodRequest(
        periodId,
      )

      await loadPeriod()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading('')
    }
  }

  async function markSubmitted() {
    setActionLoading(
      'submit',
    )

    setError('')

    try {
      await markTaxSubmittedRequest(
        periodId,
        {
          comment:
            submissionComment.trim(),
          confirmation_file:
            submissionFile,
        },
      )

      setShowSubmissionForm(
        false,
      )

      setSubmissionComment('')
      setSubmissionFile(null)

      await loadPeriod()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading('')
    }
  }

  async function unmarkSubmitted() {
    const confirmed =
      window.confirm(
        'Отменить отметку о подаче декларации?',
      )

    if (!confirmed) {
      return
    }

    setActionLoading(
      'unsubmit',
    )

    setError('')

    try {
      await unmarkTaxSubmittedRequest(
        periodId,
      )

      await loadPeriod()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading('')
    }
  }

  async function markPaid() {
    if (
      paidAmount === '' ||
      Number(paidAmount) < 0
    ) {
      setError(
        'Укажите сумму оплаты',
      )

      return
    }

    setActionLoading(
      'pay',
    )

    setError('')

    try {
      await markTaxPaidRequest(
        periodId,
        {
          paid_amount:
            paidAmount,
          comment:
            paymentComment.trim(),
          confirmation_file:
            paymentFile,
        },
      )

      setShowPaymentForm(
        false,
      )

      setPaymentComment('')
      setPaymentFile(null)

      await loadPeriod()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading('')
    }
  }

  async function unmarkPaid() {
    const confirmed =
      window.confirm(
        'Отменить отметку об оплате налога?',
      )

    if (!confirmed) {
      return
    }

    setActionLoading(
      'unpay',
    )

    setError('')

    try {
      await unmarkTaxPaidRequest(
        periodId,
      )

      await loadPeriod()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setActionLoading('')
    }
  }

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем налоговый
          период...
        </div>
      </main>
    )
  }

  if (!period) {
    return (
      <main className="page">
        <div className="error-box">
          {error ||
            'Налоговый период не найден'}
        </div>
      </main>
    )
  }

  const isSubmitted =
    period.declaration_status ===
    'submitted'

  const isPaid =
    period.payment_status ===
    'paid'

  return (
    <main className="page">
      <header className="page-header tax-detail-header">
        <div>
          <p className="eyebrow">
            Налоги
          </p>

          <h1>
            {
              MONTHS[
                period.month - 1
              ]
            }{' '}
            {period.year}
          </h1>

          <p className="muted">
            Срок подачи и оплаты:{' '}
            {formatDate(
              period.deadline,
            )}
          </p>
        </div>

        <Link
          to="/taxes"
          className="secondary-link-button"
        >
          ← К периодам
        </Link>
      </header>

      {error && (
        <div className="error-box tax-message">
          {error}
        </div>
      )}

      {period.is_overdue && (
        <div className="tax-detail-alert tax-detail-alert-danger">
          Этот налоговый период
          просрочен.
        </div>
      )}

      {period.changed_after_submission && (
        <div className="tax-detail-alert tax-detail-alert-warning">
          Доходы изменились после
          подачи декларации.
          Необходимо проверить
          декларацию повторно.
        </div>
      )}

      <section className="tax-detail-summary">
        <div className="card tax-summary-card">
            <span className="muted tax-summary-label">
            Доход за месяц
            </span>

            <strong className="tax-summary-value">
            {formatAmount(
                period.field_17,
            )}{' '}
            GEL
            </strong>
        </div>

        <div className="card tax-summary-card">
            <span className="muted tax-summary-label">
            Нарастающий итог
            </span>

            <strong className="tax-summary-value">
            {formatAmount(
                period.field_15,
            )}{' '}
            GEL
            </strong>
        </div>

        <div className="card tax-summary-card">
            <span className="muted tax-summary-label">
            Налог
            </span>

            <strong className="tax-summary-value">
            {formatAmount(
                period.field_26,
            )}{' '}
            GEL
            </strong>
        </div>
      </section>

      <section className="card tax-detail-card">
        <div className="section-heading">
          <div>
            <h2>
              Декларация
            </h2>

            <p className="muted">
              Значения для
              налоговой декларации
            </p>
          </div>

          <button
            type="button"
            className="secondary"
            disabled={
              actionLoading !== ''
            }
            onClick={() => {
              void recalculate()
            }}
          >
            {actionLoading ===
            'recalculate'
              ? 'Пересчитываем...'
              : 'Пересчитать'}
          </button>
        </div>

        <div className="tax-declaration-grid">
          <div>
            <span>
              Поле 15
            </span>

            <strong>
              {formatAmount(
                period.field_15,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Доход нарастающим
              итогом с начала года
            </small>
          </div>

          <div>
            <span>
              Поле 17
            </span>

            <strong>
              {formatAmount(
                period.field_17,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Общий доход за месяц
            </small>
          </div>

          <div>
            <span>
              Поле 18
            </span>

            <strong>
              {formatAmount(
                period.field_18,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Кассовый аппарат
            </small>
          </div>

          <div>
            <span>
              Поле 19
            </span>

            <strong>
              {formatAmount(
                period.field_19,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Физический POS
            </small>
          </div>

          <div>
            <span>
              Поле 20
            </span>

            <strong>
              {formatAmount(
                period.field_20,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Безналичные
              поступления
            </small>
          </div>

          <div>
            <span>
              Поле 21
            </span>

            <strong>
              {formatAmount(
                period.field_21,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Прочие доходы
              и криптовалюта
            </small>
          </div>

          <div>
            <span>
              Ставка
            </span>

            <strong>
              {period.tax_rate}%
            </strong>
          </div>

          <div>
            <span>
              Поле 26
            </span>

            <strong>
              {formatAmount(
                period.field_26,
              )}{' '}
              GEL
            </strong>

            <small className="field-hint">
              Сумма налога
            </small>
          </div>
        </div>
      </section>

      <section className="tax-detail-columns">
        <div className="card tax-detail-card">
          <div className="tax-status-heading">
            <div>
              <h2>
                Подача декларации
              </h2>

              <span
                className={
                  isSubmitted
                    ? 'tax-state tax-state-success'
                    : 'tax-state'
                }
              >
                {isSubmitted
                  ? 'Подана'
                  : 'Не подана'}
              </span>
            </div>
          </div>

          {isSubmitted ? (
            <>
              <div className="tax-lifecycle-info">
                <span className="muted">
                  Дата подачи
                </span>

                <strong>
                  {formatDateTime(
                    period.submitted_at,
                  )}
                </strong>
              </div>

              {period.submission_comment && (
                <p>
                  {
                    period.submission_comment
                  }
                </p>
              )}

              {period.submission_confirmation && (
                <p className="muted">
                  Подтверждающий файл
                  сохранён
                </p>
              )}

              <button
                type="button"
                className="secondary"
                disabled={
                  actionLoading !== ''
                }
                onClick={() => {
                  void unmarkSubmitted()
                }}
              >
                {actionLoading ===
                'unsubmit'
                  ? 'Отменяем...'
                  : 'Отменить отметку'}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() =>
                  setShowSubmissionForm(
                    (current) =>
                      !current,
                  )
                }
              >
                {showSubmissionForm
                  ? 'Закрыть'
                  : 'Отметить поданной'}
              </button>

              {showSubmissionForm && (
                <div className="tax-action-form">
                  <label>
                    Комментарий

                    <textarea
                      value={
                        submissionComment
                      }
                      onChange={(
                        event,
                      ) =>
                        setSubmissionComment(
                          event.target
                            .value,
                        )
                      }
                      placeholder="Номер декларации или комментарий"
                    />
                  </label>

                  <label>
                    Подтверждение

                    <input
                      type="file"
                      onChange={(
                        event,
                      ) =>
                        setSubmissionFile(
                          event.target
                            .files?.[0] ??
                            null,
                        )
                      }
                    />
                  </label>

                  <button
                    type="button"
                    disabled={
                      actionLoading !==
                      ''
                    }
                    onClick={() => {
                      void markSubmitted()
                    }}
                  >
                    {actionLoading ===
                    'submit'
                      ? 'Сохраняем...'
                      : 'Подтвердить подачу'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <div className="card tax-detail-card">
          <div className="tax-status-heading">
            <div>
              <h2>
                Оплата налога
              </h2>

              <span
                className={
                  isPaid
                    ? 'tax-state tax-state-success'
                    : 'tax-state'
                }
              >
                {isPaid
                  ? 'Оплачено'
                  : 'Не оплачено'}
              </span>
            </div>
          </div>

          {isPaid ? (
            <>
              <div className="tax-lifecycle-info">
                <span className="muted">
                  Оплачено
                </span>

                <strong>
                  {formatAmount(
                    period.paid_amount,
                  )}{' '}
                  GEL
                </strong>
              </div>

              <div className="tax-lifecycle-info">
                <span className="muted">
                  Дата оплаты
                </span>

                <strong>
                  {formatDateTime(
                    period.paid_at,
                  )}
                </strong>
              </div>

              {period.payment_comment && (
                <p>
                  {
                    period.payment_comment
                  }
                </p>
              )}

              {period.payment_confirmation && (
                <p className="muted">
                  Подтверждающий файл
                  сохранён
                </p>
              )}

              <button
                type="button"
                className="secondary"
                disabled={
                  actionLoading !== ''
                }
                onClick={() => {
                  void unmarkPaid()
                }}
              >
                {actionLoading ===
                'unpay'
                  ? 'Отменяем...'
                  : 'Отменить отметку'}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() =>
                  setShowPaymentForm(
                    (current) =>
                      !current,
                  )
                }
              >
                {showPaymentForm
                  ? 'Закрыть'
                  : 'Отметить оплаченным'}
              </button>

              {showPaymentForm && (
                <div className="tax-action-form">
                  <label>
                    Сумма оплаты

                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={
                        paidAmount
                      }
                      onChange={(
                        event,
                      ) =>
                        setPaidAmount(
                          event.target
                            .value,
                        )
                      }
                    />
                  </label>

                  <label>
                    Комментарий

                    <textarea
                      value={
                        paymentComment
                      }
                      onChange={(
                        event,
                      ) =>
                        setPaymentComment(
                          event.target
                            .value,
                        )
                      }
                      placeholder="Комментарий к оплате"
                    />
                  </label>

                  <label>
                    Подтверждение

                    <input
                      type="file"
                      onChange={(
                        event,
                      ) =>
                        setPaymentFile(
                          event.target
                            .files?.[0] ??
                            null,
                        )
                      }
                    />
                  </label>

                  <button
                    type="button"
                    disabled={
                      actionLoading !==
                      ''
                    }
                    onClick={() => {
                      void markPaid()
                    }}
                  >
                    {actionLoading ===
                    'pay'
                      ? 'Сохраняем...'
                      : 'Подтвердить оплату'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </main>
  )
}