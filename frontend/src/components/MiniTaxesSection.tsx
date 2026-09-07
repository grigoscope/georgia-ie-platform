import {
  useState,
} from 'react'

import {
  generateTaxPeriodRequest,
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

type Props = {
  taxPeriods: TaxPeriod[]
  onRefresh: () => Promise<void>
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

function getCurrentPeriod() {
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

export function MiniTaxesSection({
  taxPeriods,
  onRefresh,
}: Props) {
  const current =
    getCurrentPeriod()

  const [
    selectedPeriod,
    setSelectedPeriod,
  ] = useState<TaxPeriod | null>(
    null,
  )

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
  ] = useState(false)

  const [
    actionLoading,
    setActionLoading,
  ] = useState('')

  const [
    error,
    setError,
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

  function updatePeriod(
    period: TaxPeriod,
  ) {
    setSelectedPeriod(period)

    setPaidAmount(
      period.field_26,
    )
  }

  async function openPeriod(
    periodId: number,
  ) {
    setLoading(true)
    setError('')
    setShowSubmissionForm(false)
    setShowPaymentForm(false)

    try {
      const result =
        await getTaxPeriodRequest(
          periodId,
        )

      updatePeriod(result)
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
  }

  function closePeriod() {
    setSelectedPeriod(null)
    setError('')
    setShowSubmissionForm(false)
    setShowPaymentForm(false)
    setSubmissionComment('')
    setSubmissionFile(null)
    setPaymentComment('')
    setPaymentFile(null)
  }

  async function generatePeriod() {
    if (
      year < 2000 ||
      year > 2200
    ) {
      setError(
        'Укажите корректный год',
      )

      return
    }

    if (
      month < 1 ||
      month > 12
    ) {
      setError(
        'Укажите корректный месяц',
      )

      return
    }

    setActionLoading(
      'generate',
    )

    setError('')

    try {
      const result =
        await generateTaxPeriodRequest(
          year,
          month,
        )

      updatePeriod(result)

      await onRefresh()
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

  async function recalculate() {
    if (!selectedPeriod) {
      return
    }

    setActionLoading(
      'recalculate',
    )

    setError('')

    try {
      const result =
        await recalculateTaxPeriodRequest(
          selectedPeriod.id,
        )

      updatePeriod(result)

      await onRefresh()
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
    if (!selectedPeriod) {
      return
    }

    setActionLoading(
      'submit',
    )

    setError('')

    try {
      const result =
        await markTaxSubmittedRequest(
          selectedPeriod.id,
          {
            comment:
              submissionComment.trim(),

            confirmation_file:
              submissionFile,
          },
        )

      updatePeriod(result)

      setShowSubmissionForm(
        false,
      )

      setSubmissionComment('')
      setSubmissionFile(null)

      await onRefresh()
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
    if (!selectedPeriod) {
      return
    }

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
      const result =
        await unmarkTaxSubmittedRequest(
          selectedPeriod.id,
        )

      updatePeriod(result)

      await onRefresh()
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
    if (!selectedPeriod) {
      return
    }

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
      const result =
        await markTaxPaidRequest(
          selectedPeriod.id,
          {
            paid_amount:
              paidAmount,

            comment:
              paymentComment.trim(),

            confirmation_file:
              paymentFile,
          },
        )

      updatePeriod(result)

      setShowPaymentForm(
        false,
      )

      setPaymentComment('')
      setPaymentFile(null)

      await onRefresh()
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
    if (!selectedPeriod) {
      return
    }

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
      const result =
        await unmarkTaxPaidRequest(
          selectedPeriod.id,
        )

      updatePeriod(result)

      await onRefresh()
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
      <section className="mini-app-card">
        Загружаем налоговый
        период...
      </section>
    )
  }

  if (selectedPeriod) {
    const isSubmitted =
      selectedPeriod
        .declaration_status ===
      'submitted'

    const isPaid =
      selectedPeriod
        .payment_status ===
      'paid'

    const isZeroMonth =
      Number(
        selectedPeriod.field_17,
      ) === 0

    return (
      <section className="mini-app-card mini-tax-detail">
        <div className="mini-tax-detail-header">
          <button
            type="button"
            className="mini-back-button"
            onClick={
              closePeriod
            }
          >
            ← Назад
          </button>

          <div className="mini-tax-badges">
            {isZeroMonth && (
              <span className="mini-zero-badge">
                Нулевой месяц
              </span>
            )}

            {selectedPeriod
              .is_overdue && (
              <span className="mini-overdue">
                Просрочено
              </span>
            )}
          </div>
        </div>

        <div>
          <p className="eyebrow">
            Налоговый период
          </p>

          <h2>
            {
              MONTHS[
                selectedPeriod.month -
                  1
              ]
            }{' '}
            {selectedPeriod.year}
          </h2>

          <p className="muted">
            Срок подачи и оплаты:{' '}
            {formatDate(
              selectedPeriod.deadline,
            )}
          </p>
        </div>

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        {selectedPeriod
          .is_overdue && (
          <div className="mini-tax-alert mini-tax-alert-danger">
            Этот налоговый период
            просрочен.
          </div>
        )}

        {selectedPeriod
          .changed_after_submission && (
          <div className="mini-tax-alert mini-tax-alert-warning">
            Доходы изменились после
            подачи декларации.
            Необходимо пересчитать
            период и проверить
            декларацию.
          </div>
        )}

        <div className="mini-tax-summary">
          <div>
            <span>
              Доход за месяц
            </span>

            <strong>
              {formatAmount(
                selectedPeriod
                  .field_17,
              )}{' '}
              GEL
            </strong>
          </div>

          <div>
            <span>
              Нарастающий итог
            </span>

            <strong>
              {formatAmount(
                selectedPeriod
                  .field_15,
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
                selectedPeriod
                  .field_26,
              )}{' '}
              GEL
            </strong>
          </div>
        </div>

        <div className="mini-tax-actions-card">
          <div>
            <h3>
              Расчёт
            </h3>

            <p className="muted">
              Значения берутся
              из журнала доходов
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

        <div>
          <h3>
            Поля декларации
          </h3>

          <div className="mini-tax-declaration">
            <div>
              <span>
                Поле 15
              </span>

              <strong>
                {formatAmount(
                  selectedPeriod
                    .field_15,
                )}{' '}
                GEL
              </strong>

              <small>
                Нарастающий итог
              </small>
            </div>

            <div>
              <span>
                Поле 17
              </span>

              <strong>
                {formatAmount(
                  selectedPeriod
                    .field_17,
                )}{' '}
                GEL
              </strong>

              <small>
                Доход за месяц
              </small>
            </div>

            <div>
              <span>
                Поле 18
              </span>

              <strong>
                {formatAmount(
                  selectedPeriod
                    .field_18,
                )}{' '}
                GEL
              </strong>

              <small>
                Кассовый аппарат
              </small>
            </div>

            <div>
              <span>
                Поле 19
              </span>

              <strong>
                {formatAmount(
                  selectedPeriod
                    .field_19,
                )}{' '}
                GEL
              </strong>

              <small>
                Физический POS
              </small>
            </div>

            <div>
              <span>
                Поле 20
              </span>

              <strong>
                {formatAmount(
                  selectedPeriod
                    .field_20,
                )}{' '}
                GEL
              </strong>

              <small>
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
                  selectedPeriod
                    .field_21,
                )}{' '}
                GEL
              </strong>

              <small>
                Прочие и крипто
              </small>
            </div>

            <div>
              <span>
                Ставка
              </span>

              <strong>
                {
                  selectedPeriod
                    .tax_rate
                }
                %
              </strong>
            </div>

            <div>
              <span>
                Поле 26
              </span>

              <strong>
                {formatAmount(
                  selectedPeriod
                    .field_26,
                )}{' '}
                GEL
              </strong>

              <small>
                Сумма налога
              </small>
            </div>
          </div>
        </div>

        <div className="mini-tax-lifecycle">
          <div className="mini-tax-lifecycle-card">
            <div className="mini-tax-lifecycle-heading">
              <div>
                <span>
                  Декларация
                </span>

                <strong>
                  {isSubmitted
                    ? 'Подана'
                    : 'Не подана'}
                </strong>
              </div>

              <span
                className={
                  isSubmitted
                    ? 'mini-tax-state mini-tax-state-success'
                    : 'mini-tax-state'
                }
              >
                {isSubmitted
                  ? '✓'
                  : '—'}
              </span>
            </div>

            {isSubmitted ? (
              <>
                <div className="mini-tax-meta">
                  <span>
                    Дата подачи
                  </span>

                  <strong>
                    {formatDateTime(
                      selectedPeriod
                        .submitted_at,
                    )}
                  </strong>
                </div>

                {selectedPeriod
                  .submission_comment && (
                  <p>
                    {
                      selectedPeriod
                        .submission_comment
                    }
                  </p>
                )}

                {selectedPeriod
                  .submission_confirmation && (
                  <p className="muted">
                    Подтверждающий
                    файл сохранён
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
                  disabled={
                    actionLoading !== ''
                  }
                  onClick={() => {
                    setShowSubmissionForm(
                      (currentValue) =>
                        !currentValue,
                    )
                  }}
                >
                  {showSubmissionForm
                    ? 'Закрыть'
                    : 'Отметить поданной'}
                </button>

                {showSubmissionForm && (
                  <div className="mini-tax-form">
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
                        accept=".pdf,image/*"
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

          <div className="mini-tax-lifecycle-card">
            <div className="mini-tax-lifecycle-heading">
              <div>
                <span>
                  Оплата налога
                </span>

                <strong>
                  {isPaid
                    ? 'Оплачено'
                    : 'Не оплачено'}
                </strong>
              </div>

              <span
                className={
                  isPaid
                    ? 'mini-tax-state mini-tax-state-success'
                    : 'mini-tax-state'
                }
              >
                {isPaid
                  ? '✓'
                  : '—'}
              </span>
            </div>

            {isPaid ? (
              <>
                <div className="mini-tax-meta">
                  <span>
                    Сумма
                  </span>

                  <strong>
                    {formatAmount(
                      selectedPeriod
                        .paid_amount,
                    )}{' '}
                    GEL
                  </strong>
                </div>

                <div className="mini-tax-meta">
                  <span>
                    Дата оплаты
                  </span>

                  <strong>
                    {formatDateTime(
                      selectedPeriod
                        .paid_at,
                    )}
                  </strong>
                </div>

                {selectedPeriod
                  .payment_comment && (
                  <p>
                    {
                      selectedPeriod
                        .payment_comment
                    }
                  </p>
                )}

                {selectedPeriod
                  .payment_confirmation && (
                  <p className="muted">
                    Подтверждающий
                    файл сохранён
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
                  disabled={
                    actionLoading !== ''
                  }
                  onClick={() => {
                    setShowPaymentForm(
                      (currentValue) =>
                        !currentValue,
                    )
                  }}
                >
                  {showPaymentForm
                    ? 'Закрыть'
                    : 'Отметить оплаченным'}
                </button>

                {showPaymentForm && (
                  <div className="mini-tax-form">
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
                        accept=".pdf,image/*"
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
        </div>
      </section>
    )
  }

  return (
    <section className="mini-app-card">
      <div className="mini-section-heading">
        <div>
          <p className="eyebrow">
            Декларации
          </p>

          <h2>
            Налоги
          </h2>

          <p className="muted">
            Расчёт и статус
            налоговых периодов
          </p>
        </div>
      </div>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      <div className="mini-tax-generate">
        <div>
          <strong>
            Рассчитать месяц
          </strong>

          <span>
            Данные будут взяты
            из журнала доходов
          </span>
        </div>

        <div className="mini-tax-generate-grid">
          <label>
            Месяц

            <select
              value={month}
              onChange={(
                event,
              ) =>
                setMonth(
                  Number(
                    event.target
                      .value,
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
                    value={
                      index + 1
                    }
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
              onChange={(
                event,
              ) =>
                setYear(
                  Number(
                    event.target
                      .value,
                  ),
                )
              }
            />
          </label>
        </div>

        <button
          type="button"
          disabled={
            actionLoading !== ''
          }
          onClick={() => {
            void generatePeriod()
          }}
        >
          {actionLoading ===
          'generate'
            ? 'Считаем...'
            : 'Рассчитать'}
        </button>
      </div>

      {taxPeriods.length === 0 ? (
        <div className="mini-empty">
          Налоговых периодов
          пока нет
        </div>
      ) : (
        <div className="mini-tax-list">
          {taxPeriods
            .slice(0, 12)
            .map(
              (period) => (
                <div
                  key={period.id}
                  className="mini-tax-open"
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
                        {period.year}
                      </strong>

                      <span>
                        Срок:{' '}
                        {formatDate(
                          period.deadline,
                        )}
                      </span>
                    </div>

                    <div className="mini-tax-badges">
                      {Number(
                        period.field_17,
                      ) === 0 && (
                        <span className="mini-zero-badge">
                          Нулевой
                        </span>
                      )}

                      {period.is_overdue && (
                        <span className="mini-overdue">
                          Просрочено
                        </span>
                      )}
                    </div>
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
                      {period
                        .declaration_status ===
                      'submitted'
                        ? 'подана'
                        : 'не подана'}
                    </span>

                    <span>
                      Оплата:{' '}
                      {period
                        .payment_status ===
                      'paid'
                        ? 'оплачено'
                        : 'не оплачено'}
                    </span>
                  </div>

                  {period
                    .changed_after_submission && (
                    <div className="mini-tax-warning">
                      Данные изменились
                      после подачи
                    </div>
                  )}

                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      void openPeriod(
                        period.id,
                      )
                    }}
                  >
                    Открыть период
                  </button>
                </div>
              ),
            )}
        </div>
      )}
    </section>
  )
}