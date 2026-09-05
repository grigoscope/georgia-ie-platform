import {
  useState,
} from 'react'

import {
  createInvoiceIncomeRequest,
  previewInvoiceRequest,
  type Invoice,
  type InvoicePaymentSummary,
} from '../api/invoices'

import {
  getAccountsRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  MiniInvoiceCreateForm,
} from './MiniInvoiceCreateForm'

type Props = {
  invoices: Invoice[]
  currencies: Currency[]
  onRefresh: () => Promise<void>
}

const STATUS_LABELS:
  Record<string, string> = {
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
  value: string,
) {
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

function buyerName(
  invoice: Invoice,
) {
  const value =
    invoice.buyer_snapshot.name

  if (
    typeof value === 'string' &&
    value
  ) {
    return value
  }

  return 'Контрагент'
}

export function MiniInvoicesSection({
  invoices,
  currencies,
  onRefresh,
}: Props) {
  const [
    selectedInvoice,
    setSelectedInvoice,
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
  ] = useState(false)

  const [
    error,
    setError,
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
  ] = useState(
    getCurrentTbilisiDateTime(),
  )

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

  const [
    creating,
    setCreating,
  ] = useState(false)

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

  async function loadInvoice(
    invoiceId: number,
  ) {
    setLoading(true)
    setError('')

    try {
      const [
        invoiceResult,
        accountsResult,
      ] = await Promise.all([
        previewInvoiceRequest(
          invoiceId,
        ),

        getAccountsRequest(),
      ])

      const invoice =
        invoiceResult.data.invoice

      const summary =
        invoiceResult
          .data
          .payment_summary

      const availableAccounts =
        accountsResult.filter(
          (account) =>
            account.is_active &&
            account.type !==
              'crypto',
        )

      setSelectedInvoice(
        invoice,
      )

      setPaymentSummary(
        summary,
      )

      setAccounts(
        availableAccounts,
      )

      setPaymentAmount(
        summary.remaining_amount,
      )

      const snapshotAccountId =
        Number(
          invoice
            .payment_details_snapshot
            .account_id,
        )

      const snapshotAccount =
        availableAccounts.find(
          (account) =>
            account.id ===
            snapshotAccountId,
        )

      const defaultAccount =
        snapshotAccount ??
        availableAccounts.find(
          (account) =>
            account.is_default,
        ) ??
        availableAccounts[0]

      setPaymentAccountId(
        defaultAccount
          ? String(
              defaultAccount.id,
            )
          : '',
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
  }

  async function openInvoice(
    invoiceId: number,
  ) {
    setShowPaymentForm(false)

    setPaymentComment('')

    setPaymentReceivedAt(
      getCurrentTbilisiDateTime(),
    )

    await loadInvoice(
      invoiceId,
    )
  }

  function closeInvoice() {
    setSelectedInvoice(null)
    setPaymentSummary(null)
    setShowPaymentForm(false)
    setError('')
  }

  function openPaymentForm() {
    if (!paymentSummary) {
      return
    }

    setPaymentAmount(
      paymentSummary
        .remaining_amount,
    )

    setPaymentReceivedAt(
      getCurrentTbilisiDateTime(),
    )

    setPaymentComment('')
    setError('')

    setShowPaymentForm(true)
  }

  async function registerPayment() {
    if (!selectedInvoice) {
      return
    }

    if (!paymentAccountId) {
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

    if (!paymentReceivedAt) {
      setError(
        'Укажите дату и время оплаты',
      )

      return
    }

    setPaymentSaving(true)
    setError('')

    try {
      await createInvoiceIncomeRequest(
        selectedInvoice.id,
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

      await loadInvoice(
        selectedInvoice.id,
      )

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
      setPaymentSaving(false)
    }
  }

  if (loading) {
    return (
      <section className="mini-app-card">
        Загружаем инвойс...
      </section>
    )
  }

  if (creating) {
    return (
        <MiniInvoiceCreateForm
        onCancel={() => {
            setCreating(false)
        }}
        onCreated={async (
            invoice,
        ) => {
            setCreating(false)

            await onRefresh()

            await openInvoice(
            invoice.id,
            )
        }}
        />
    )
  }

  if (selectedInvoice) {
    const canReceivePayment =
      selectedInvoice.status !==
        'paid' &&
      selectedInvoice.status !==
        'cancelled'

    const invoiceCurrency =
      currencyCode(
        selectedInvoice.currency,
      )

    return (
      <section className="mini-app-card mini-invoice-detail">
        <div className="mini-invoice-detail-header">
          <button
            type="button"
            className="mini-back-button"
            onClick={closeInvoice}
          >
            ← Назад
          </button>

          <span
            className={
              `mini-status ` +
              `mini-status-${selectedInvoice.status}`
            }
          >
            {STATUS_LABELS[
              selectedInvoice.status
            ] ??
              selectedInvoice.status}
          </span>
        </div>

        <div>
          <p className="eyebrow">
            Инвойс
          </p>

          <h2>
            {selectedInvoice.number}
          </h2>

          <p className="muted">
            {buyerName(
              selectedInvoice,
            )}
          </p>
        </div>

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        <div className="mini-invoice-summary">
          <div>
            <span>
              Сумма
            </span>

            <strong>
              {formatAmount(
                selectedInvoice
                  .total_amount,
              )}{' '}
              {invoiceCurrency}
            </strong>
          </div>

          <div>
            <span>
              Оплачено
            </span>

            <strong>
              {formatAmount(
                paymentSummary
                  ?.paid_amount ??
                  '0',
              )}{' '}
              {invoiceCurrency}
            </strong>
          </div>

          <div>
            <span>
              Осталось
            </span>

            <strong>
              {formatAmount(
                paymentSummary
                  ?.remaining_amount ??
                  selectedInvoice
                    .total_amount,
              )}{' '}
              {invoiceCurrency}
            </strong>
          </div>
        </div>

        <div className="mini-invoice-info">
          <div>
            <span>
              Дата выставления
            </span>

            <strong>
              {formatDate(
                selectedInvoice
                  .issue_date,
              )}
            </strong>
          </div>

          <div>
            <span>
              Оплатить до
            </span>

            <strong>
              {formatDate(
                selectedInvoice
                  .due_date,
              )}
            </strong>
          </div>

          <div>
            <span>
              Назначение
            </span>

            <strong>
              {selectedInvoice
                .payment_purpose ||
                '—'}
            </strong>
          </div>
        </div>

        <div>
          <h3>
            Позиции
          </h3>

          <div className="mini-invoice-items">
            {selectedInvoice
              .invoice_items
              .map(
                (item) => (
                  <div
                    key={item.id}
                    className="mini-invoice-item"
                  >
                    <div>
                      <strong>
                        {
                          item.description
                        }
                      </strong>

                      <span>
                        {formatAmount(
                          item.quantity,
                        )}{' '}
                        {item.unit} ×{' '}
                        {formatAmount(
                          item.unit_price,
                        )}
                      </span>
                    </div>

                    <strong>
                      {formatAmount(
                        item.line_total,
                      )}{' '}
                      {invoiceCurrency}
                    </strong>
                  </div>
                ),
              )}
          </div>
        </div>

        <div>
          <h3>
            История оплат
          </h3>

          {selectedInvoice
            .payments.length ===
          0 ? (
            <div className="mini-empty">
              Оплат пока нет
            </div>
          ) : (
            <div className="mini-payment-list">
              {selectedInvoice
                .payments
                .map(
                  (payment) => (
                    <div
                      key={
                        payment.id
                      }
                      className="mini-payment-row"
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

                        <span>
                          {formatDateTime(
                            payment.paid_at,
                          )}
                        </span>
                      </div>

                      <span>
                        Доход #
                        {
                          payment.income_entry_id
                        }
                      </span>
                    </div>
                  ),
                )}
            </div>
          )}
        </div>

        {canReceivePayment &&
          !showPaymentForm && (
          <button
            type="button"
            onClick={
              openPaymentForm
            }
          >
            Зарегистрировать оплату
          </button>
        )}

        {showPaymentForm && (
          <div className="mini-payment-form">
            <div>
              <h3>
                Оплата инвойса
              </h3>

              <p className="muted">
                Будет создан
                фактический доход
              </p>
            </div>

            <label>
              Сумма

              <input
                type="number"
                min="0.01"
                step="0.01"
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
              />
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
              >
                <option value="">
                  Выберите счёт
                </option>

                {accounts.map(
                  (account) => (
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
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Дата и время

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
              />
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
                placeholder="Необязательно"
              />
            </label>

            <div className="mini-payment-actions">
              <button
                type="button"
                className="secondary"
                disabled={
                  paymentSaving
                }
                onClick={() =>
                  setShowPaymentForm(
                    false,
                  )
                }
              >
                Отмена
              </button>

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
    )
  }

  return (
    <section className="mini-app-card">
     <div className="mini-section-heading">
        <div>
            <p className="eyebrow">
            Журнал
            </p>

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
            onClick={() => {
            setCreating(true)
            }}
        >
            + Новый
        </button>
       </div>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {invoices.length === 0 ? (
        <div className="mini-empty">
          Инвойсов пока нет
        </div>
      ) : (
        <div className="mini-invoices-list">
          {invoices.map(
            (invoice) => (
              <button
                key={invoice.id}
                type="button"
                className="mini-invoice-open"
                onClick={() => {
                  void openInvoice(
                    invoice.id,
                  )
                }}
              >
                <div className="mini-invoice-open-top">
                  <div>
                    <strong>
                      {
                        invoice.number
                      }
                    </strong>

                    <span>
                      {buyerName(
                        invoice,
                      )}
                    </span>
                  </div>

                  <span
                    className={
                      `mini-status ` +
                      `mini-status-${invoice.status}`
                    }
                  >
                    {STATUS_LABELS[
                      invoice.status
                    ] ??
                      invoice.status}
                  </span>
                </div>

                <div className="mini-invoice-open-bottom">
                  <span>
                    {formatDate(
                      invoice.issue_date,
                    )}
                  </span>

                  <strong>
                    {formatAmount(
                      invoice.total_amount,
                    )}{' '}
                    {currencyCode(
                      invoice.currency,
                    )}
                  </strong>
                </div>
              </button>
            ),
          )}
        </div>
      )}
    </section>
  )
}