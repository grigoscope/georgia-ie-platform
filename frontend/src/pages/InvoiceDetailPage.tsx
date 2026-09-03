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
  cancelInvoiceRequest,
  createInvoiceIncomeRequest,
  downloadInvoicePdfRequest,
  generateInvoicePdfRequest,
  markInvoiceSentRequest,
  previewInvoiceRequest,
  type Invoice,
  type InvoicePaymentSummary,
} from '../api/invoices'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  getAccountsRequest,
  type FinancialAccount,
} from '../api/finances'

const STATUS_LABELS: Record<
  string,
  string
> = {
  draft: 'Черновик',
  pending: 'Ожидает оплаты',
  partially_paid:
    'Частично оплачен',
  paid: 'Оплачен',
  cancelled: 'Отменён',
}

function formatAmount(
  value: string | number,
) {
  const amount = Number(value)

  if (Number.isNaN(amount)) {
    return String(value)
  }

  if (Number.isInteger(amount)) {
    return String(amount)
  }

  return amount
    .toFixed(2)
    .replace(/\.?0+$/, '')
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

function getCurrentTbilisiDateTime() {
  return new Intl.DateTimeFormat(
    'sv-SE',
    {
      timeZone: 'Asia/Tbilisi',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    },
  )
    .format(new Date())
    .replace(' ', 'T')
}

function snapshotValue(
  snapshot: Record<
    string,
    unknown
  >,
  key: string,
) {
  const value =
    snapshot[key]

  if (
    value === undefined ||
    value === null ||
    value === ''
  ) {
    return '—'
  }

  return String(value)
}

export function InvoiceDetailPage() {
  const { id } =
    useParams()

  const invoiceId =
    Number(id)

  const [
    invoice,
    setInvoice,
  ] = useState<Invoice | null>(
    null,
  )

  const [
    paymentSummary,
    setPaymentSummary,
  ] = useState<
    InvoicePaymentSummary | null
  >(null)

  const [
    accounts,
    setAccounts,
  ] = useState<
    FinancialAccount[]
  >([])

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
    showPaymentForm,
    setShowPaymentForm,
  ] = useState(false)

  const [
    paymentAmount,
    setPaymentAmount,
  ] = useState('')

  const [
    paymentAccountId,
    setPaymentAccountId,
  ] = useState('')

  const [
    paymentReceivedAt,
    setPaymentReceivedAt,
  ] = useState('')

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState(
    'bank_transfer',
  )

  const [
    paymentComment,
    setPaymentComment,
  ] = useState('')

  const [
    paymentSaving,
    setPaymentSaving,
  ] = useState(false)

  const loadInvoice =
    useCallback(
      async () => {
        if (
          !Number.isInteger(
            invoiceId,
          )
        ) {
          setError(
            'Некорректный ID инвойса',
          )

          setLoading(false)

          return
        }

        try {
          const result =
            await previewInvoiceRequest(
              invoiceId,
            )

          setInvoice(
            result.data.invoice,
          )

          setPaymentSummary(
            result.data
              .payment_summary,
          )

          setPaymentAmount(
            result.data
              .payment_summary
              .remaining_amount,
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
      [invoiceId],
    )

  useEffect(() => {
    void loadInvoice()
  }, [loadInvoice])

  useEffect(() => {
    let cancelled = false

    async function loadAccounts() {
      try {
        const result =
          await getAccountsRequest()

        if (cancelled) {
          return
        }

        setAccounts(
          result.filter(
            (account) =>
              account.is_active,
          ),
        )
      } catch (
        requestError
      ) {
        if (!cancelled) {
          setError(
            getApiErrorMessage(
              requestError,
            ),
          )
        }
      }
    }

    void loadAccounts()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (
      !invoice ||
      accounts.length === 0 ||
      paymentAccountId
    ) {
      return
    }

    const snapshotAccountId =
      Number(
        invoice
          .payment_details_snapshot
          .account_id,
      )

    const invoiceAccount =
      accounts.find(
        (account) =>
          account.id ===
          snapshotAccountId,
      )

    const defaultAccount =
      invoiceAccount ??
      accounts.find(
        (account) =>
          account.is_default,
      ) ??
      accounts[0]

    if (defaultAccount) {
      setPaymentAccountId(
        String(
          defaultAccount.id,
        ),
      )
    }
  }, [
    invoice,
    accounts,
    paymentAccountId,
  ])

  async function generatePdf() {
    setActionLoading(
      'generate-pdf',
    )

    setError('')

    try {
      await generateInvoicePdfRequest(
        invoiceId,
      )

      await loadInvoice()
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

  async function downloadPdf() {
    setActionLoading(
      'download-pdf',
    )

    setError('')

    try {
      const blob =
        await downloadInvoicePdfRequest(
          invoiceId,
        )

      const url =
        URL.createObjectURL(
          blob,
        )

      const link =
        document.createElement(
          'a',
        )

      link.href = url

      link.download =
        `invoice-${invoice?.number ?? invoiceId}.pdf`

      document.body.appendChild(
        link,
      )

      link.click()
      link.remove()

      window.setTimeout(
        () => {
          URL.revokeObjectURL(
            url,
          )
        },
        0,
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
      setActionLoading('')
    }
  }

  async function markSent() {
    setActionLoading(
      'mark-sent',
    )

    setError('')

    try {
      await markInvoiceSentRequest(
        invoiceId,
      )

      await loadInvoice()
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

  async function cancelInvoice() {
    const confirmed =
      window.confirm(
        'Отменить этот инвойс?',
      )

    if (!confirmed) {
      return
    }

    setActionLoading(
      'cancel',
    )

    setError('')

    try {
      await cancelInvoiceRequest(
        invoiceId,
      )

      setShowPaymentForm(false)

      await loadInvoice()
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

  function togglePaymentForm() {
    setShowPaymentForm(
      (current) => !current,
    )

    if (
      !paymentReceivedAt
    ) {
      setPaymentReceivedAt(
        getCurrentTbilisiDateTime(),
      )
    }

    if (
      paymentSummary
        ?.remaining_amount
    ) {
      setPaymentAmount(
        paymentSummary
          .remaining_amount,
      )
    }
  }

  async function registerPayment() {
    if (
      !paymentAccountId
    ) {
      setError(
        'Выберите счёт получения',
      )

      return
    }

    if (
      !paymentAmount ||
      Number(paymentAmount) <= 0
    ) {
      setError(
        'Введите сумму оплаты',
      )

      return
    }

    if (
      paymentSummary &&
      Number(paymentAmount) >
        Number(
          paymentSummary
            .remaining_amount,
        )
    ) {
      setError(
        'Сумма оплаты превышает остаток по инвойсу',
      )

      return
    }

    if (
      !paymentReceivedAt
    ) {
      setError(
        'Укажите дату и время оплаты',
      )

      return
    }

    setPaymentSaving(true)
    setError('')

    try {
      await createInvoiceIncomeRequest(
        invoiceId,
        {
          received_at:
            `${paymentReceivedAt}:00+04:00`,
          financial_account:
            Number(
              paymentAccountId,
            ),
          amount:
            paymentAmount,
          payment_method:
            paymentMethod,
          comment:
            paymentComment.trim(),
        },
      )

      setShowPaymentForm(false)
      setPaymentComment('')

      await loadInvoice()
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setPaymentSaving(false)
    }
  }

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем инвойс...
        </div>
      </main>
    )
  }

  if (!invoice) {
    return (
      <main className="page">
        <div className="error-box">
          {error ||
            'Инвойс не найден'}
        </div>
      </main>
    )
  }

  const seller =
    invoice.seller_snapshot

  const buyer =
    invoice.buyer_snapshot

  const paymentDetails =
    invoice
      .payment_details_snapshot

  const canReceivePayment =
    invoice.status !== 'paid' &&
    invoice.status !==
      'cancelled'

  return (
    <main className="page">
      <header className="page-header invoice-detail-header">
        <div>
          <p className="eyebrow">
            Инвойс
          </p>

          <h1>
            {invoice.number}
          </h1>

          <div className="invoice-detail-meta">
            <span
              className={
                `invoice-status ` +
                `invoice-status-${invoice.status}`
              }
            >
              {STATUS_LABELS[
                invoice.status
              ] ??
                invoice.status}
            </span>

            <span className="muted">
              от{' '}
              {formatDate(
                invoice.issue_date,
              )}
            </span>
          </div>
        </div>

        <Link
          to="/invoices"
          className="secondary-link-button"
        >
          ← К журналу
        </Link>
      </header>

      {error && (
        <div className="error-box invoice-message">
          {error}
        </div>
      )}

      <section className="invoice-detail-summary">
        <div className="card">
          <span className="muted">
            Итог
          </span>

          <strong className="invoice-big-money">
            {formatAmount(
              invoice.total_amount,
            )}
          </strong>
        </div>

        <div className="card">
          <span className="muted">
            Оплачено
          </span>

          <strong className="invoice-big-money">
            {formatAmount(
              paymentSummary
                ?.paid_amount ??
                '0',
            )}
          </strong>
        </div>

        <div className="card">
          <span className="muted">
            Осталось
          </span>

          <strong className="invoice-big-money">
            {formatAmount(
              paymentSummary
                ?.remaining_amount ??
                invoice.total_amount,
            )}
          </strong>
        </div>
      </section>

      <section className="card invoice-detail-card">
        <div className="section-heading">
          <div>
            <h2>
              Действия
            </h2>

            <p className="muted">
              Работа с документом
              и его статусом
            </p>
          </div>
        </div>

        <div className="invoice-detail-actions">
          <button
            type="button"
            className="secondary"
            disabled={
              actionLoading !== ''
            }
            onClick={() => {
              void generatePdf()
            }}
          >
            {actionLoading ===
            'generate-pdf'
              ? 'Генерируем...'
              : invoice.pdf_file
                ? 'Обновить PDF'
                : 'Создать PDF'}
          </button>

          {invoice.pdf_file && (
            <button
              type="button"
              className="secondary"
              disabled={
                actionLoading !== ''
              }
              onClick={() => {
                void downloadPdf()
              }}
            >
              {actionLoading ===
              'download-pdf'
                ? 'Скачиваем...'
                : 'Скачать PDF'}
            </button>
          )}

          {invoice.status ===
            'draft' && (
            <button
              type="button"
              disabled={
                actionLoading !== ''
              }
              onClick={() => {
                void markSent()
              }}
            >
              {actionLoading ===
              'mark-sent'
                ? 'Сохраняем...'
                : 'Отметить отправленным'}
            </button>
          )}

          {canReceivePayment && (
            <button
              type="button"
              disabled={
                actionLoading !== '' ||
                paymentSaving
              }
              onClick={
                togglePaymentForm
              }
            >
              {showPaymentForm
                ? 'Закрыть оплату'
                : 'Зарегистрировать оплату'}
            </button>
          )}

          {invoice.status !==
            'paid' &&
            invoice.status !==
              'cancelled' && (
              <button
                type="button"
                className="invoice-delete-button"
                disabled={
                  actionLoading !== '' ||
                  paymentSaving
                }
                onClick={() => {
                  void cancelInvoice()
                }}
              >
                {actionLoading ===
                'cancel'
                  ? 'Отменяем...'
                  : 'Отменить инвойс'}
              </button>
            )}
        </div>

        {showPaymentForm &&
          canReceivePayment && (
            <div className="invoice-payment-form">
              <div>
                <h3>
                  Фактическая оплата
                </h3>

                <p className="muted">
                  После сохранения
                  оплата автоматически
                  появится в журнале
                  доходов.
                </p>
              </div>

              <div className="form-grid">
                <label>
                  Дата и время
                  получения

                  <input
                    type="datetime-local"
                    value={
                      paymentReceivedAt
                    }
                    onChange={(
                      event,
                    ) =>
                      setPaymentReceivedAt(
                        event.target
                          .value,
                      )
                    }
                    required
                  />
                </label>

                <label>
                  Сумма оплаты

                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    max={
                      paymentSummary
                        ?.remaining_amount
                    }
                    value={
                      paymentAmount
                    }
                    onChange={(
                      event,
                    ) =>
                      setPaymentAmount(
                        event.target
                          .value,
                      )
                    }
                    required
                  />

                  <small className="field-hint">
                    Осталось:{' '}
                    {formatAmount(
                      paymentSummary
                        ?.remaining_amount ??
                        '0',
                    )}
                  </small>
                </label>

                <label>
                  Счёт получения

                  <select
                    value={
                      paymentAccountId
                    }
                    onChange={(
                      event,
                    ) =>
                      setPaymentAccountId(
                        event.target
                          .value,
                      )
                    }
                    required
                  >
                    <option value="">
                      Выберите счёт
                    </option>

                    {accounts.map(
                      (
                        account,
                      ) => (
                        <option
                          key={
                            account.id
                          }
                          value={
                            account.id
                          }
                        >
                          {
                            account.name
                          }
                          {' — '}
                          {
                            account
                              .default_currency_code
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
                      Банковский
                      перевод
                    </option>

                    <option value="card">
                      Карта
                    </option>

                    <option value="cash">
                      Наличные
                    </option>

                    <option value="crypto">
                      Криптовалюта
                    </option>

                    <option value="other">
                      Другое
                    </option>
                  </select>
                </label>

                <label className="wide">
                  Комментарий

                  <input
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
                    placeholder="Оплата получена"
                  />
                </label>
              </div>

              <div>
                <button
                  type="button"
                  disabled={
                    paymentSaving
                  }
                  onClick={() => {
                    void registerPayment()
                  }}
                >
                  {paymentSaving
                    ? 'Сохраняем...'
                    : 'Подтвердить оплату'}
                </button>
              </div>
            </div>
          )}
      </section>

      <section className="card invoice-detail-card">
        <h2>
          Позиции
        </h2>

        <div className="invoice-detail-items">
          <div className="invoice-detail-item invoice-detail-item-header">
            <span>
              Описание
            </span>

            <span>
              Кол-во
            </span>

            <span>
              Цена
            </span>

            <span>
              Итого
            </span>
          </div>

          {invoice.invoice_items.map(
            (item) => (
              <div
                key={item.id}
                className="invoice-detail-item"
              >
                <strong>
                  {item.description}
                </strong>

                <span>
                  {formatAmount(
                    item.quantity,
                  )}{' '}
                  {item.unit}
                </span>

                <span>
                  {formatAmount(
                    item.unit_price,
                  )}
                </span>

                <strong>
                  {formatAmount(
                    item.line_total,
                  )}
                </strong>
              </div>
            ),
          )}
        </div>

        <div className="invoice-totals">
          <div>
            <span>
              Подытог
            </span>

            <strong>
              {formatAmount(
                invoice.subtotal,
              )}
            </strong>
          </div>

          <div>
            <span>
              Скидка
            </span>

            <strong>
              {formatAmount(
                invoice
                  .discount_amount,
              )}
            </strong>
          </div>

          <div>
            <span>
              Наценка
            </span>

            <strong>
              {formatAmount(
                invoice
                  .extra_charge_amount,
              )}
            </strong>
          </div>

          <div className="invoice-total-final">
            <span>
              Итого
            </span>

            <strong>
              {formatAmount(
                invoice.total_amount,
              )}
            </strong>
          </div>
        </div>
      </section>

      {invoice.payments.length >
        0 && (
        <section className="card invoice-detail-card">
          <h2>
            Оплаты
          </h2>

          <div className="invoice-payment-history">
            {invoice.payments.map(
              (payment) => (
                <div
                  key={payment.id}
                  className="invoice-payment-history-row"
                >
                  <div>
                    <strong>
                      {formatAmount(
                        payment.amount,
                      )}{' '}
                      {
                        payment.currency_code
                      }
                    </strong>

                    <p className="muted">
                      {formatDateTime(
                        payment.paid_at,
                      )}
                    </p>
                  </div>

                  <span className="muted">
                    Доход #
                    {
                      payment.income_entry_id
                    }
                  </span>
                </div>
              ),
            )}
          </div>
        </section>
      )}

      <section className="invoice-detail-columns">
        <div className="card">
          <h2>
            Продавец
          </h2>

          <p>
            <strong>
              {snapshotValue(
                seller,
                'business_name',
              )}
            </strong>
          </p>

          <p className="muted">
            TIN:{' '}
            {snapshotValue(
              seller,
              'tin',
            )}
          </p>

          <p className="muted">
            {snapshotValue(
              seller,
              'legal_address',
            )}
          </p>

          <p className="muted">
            {snapshotValue(
              seller,
              'email',
            )}
          </p>
        </div>

        <div className="card">
          <h2>
            Покупатель
          </h2>

          <p>
            <strong>
              {snapshotValue(
                buyer,
                'name',
              )}
            </strong>
          </p>

          <p className="muted">
            {snapshotValue(
              buyer,
              'country',
            )}
          </p>

          <p className="muted">
            Tax ID:{' '}
            {snapshotValue(
              buyer,
              'tax_id',
            )}
          </p>

          <p className="muted">
            {snapshotValue(
              buyer,
              'email',
            )}
          </p>
        </div>
      </section>

      <section className="card invoice-detail-card">
        <h2>
          Реквизиты для оплаты
        </h2>

        <div className="invoice-payment-details">
          <div>
            <span className="muted">
              Счёт
            </span>

            <strong>
              {snapshotValue(
                paymentDetails,
                'name',
              )}
            </strong>
          </div>

          <div>
            <span className="muted">
              Банк
            </span>

            <strong>
              {snapshotValue(
                paymentDetails,
                'provider_name',
              )}
            </strong>
          </div>

          <div>
            <span className="muted">
              IBAN
            </span>

            <strong>
              {snapshotValue(
                paymentDetails,
                'iban',
              )}
            </strong>
          </div>

          <div>
            <span className="muted">
              SWIFT/BIC
            </span>

            <strong>
              {snapshotValue(
                paymentDetails,
                'swift_bic',
              )}
            </strong>
          </div>

          <div>
            <span className="muted">
              Валюта
            </span>

            <strong>
              {snapshotValue(
                paymentDetails,
                'currency',
              )}
            </strong>
          </div>
        </div>

        {invoice.payment_purpose && (
          <p>
            <strong>
              Назначение:
            </strong>{' '}
            {
              invoice.payment_purpose
            }
          </p>
        )}

        {invoice.notes && (
          <p className="muted">
            {invoice.notes}
          </p>
        )}
      </section>
    </main>
  )
}