import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react'

import {
  getCounterpartiesRequest,
  getCurrenciesRequest,
  type Counterparty,
  type Currency,
} from '../api/finances'

import {
  deleteInvoiceRequest,
  getInvoicesRequest,
  type Invoice,
  type InvoiceFilters,
} from '../api/invoices'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  Link,
} from 'react-router-dom'

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
  value: string,
) {
  const amount = Number(value)

  if (Number.isNaN(amount)) {
    return value
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

export function InvoicesPage() {
  const [
    invoices,
    setInvoices,
  ] = useState<Invoice[]>([])

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>([])

  const [
    counterparties,
    setCounterparties,
  ] = useState<Counterparty[]>([])

  const [loading, setLoading] =
    useState(true)

  const [
    journalLoading,
    setJournalLoading,
  ] = useState(false)

  const [error, setError] =
    useState('')

  const [
    deletingId,
    setDeletingId,
  ] = useState<number | null>(
    null,
  )

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
    reload,
    setReload,
  ] = useState(0)

  const [
    showFilters,
    setShowFilters,
  ] = useState(false)

  const [
    searchQuery,
    setSearchQuery,
  ] = useState('')

  const [
    statusFilter,
    setStatusFilter,
  ] = useState('')

  const [
    counterpartyFilter,
    setCounterpartyFilter,
  ] = useState('')

  const [
    currencyFilter,
    setCurrencyFilter,
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
    overdueFilter,
    setOverdueFilter,
  ] = useState('')

  const [
    ordering,
    setOrdering,
  ] = useState('-issue_date')

  const [
    activeFilters,
    setActiveFilters,
  ] = useState<InvoiceFilters>({
    page: 1,
    page_size: 20,
    ordering: '-issue_date',
  })

  const activeFilterCount =
    useMemo(() => {
      let count = 0

      if (searchQuery.trim()) {
        count += 1
      }

      if (statusFilter) {
        count += 1
      }

      if (counterpartyFilter) {
        count += 1
      }

      if (currencyFilter) {
        count += 1
      }

      if (dateFrom) {
        count += 1
      }

      if (dateTo) {
        count += 1
      }

      if (overdueFilter) {
        count += 1
      }

      if (
        ordering !==
        '-issue_date'
      ) {
        count += 1
      }

      return count
    }, [
      searchQuery,
      statusFilter,
      counterpartyFilter,
      currencyFilter,
      dateFrom,
      dateTo,
      overdueFilter,
      ordering,
    ])

  useEffect(() => {
    let cancelled = false

    async function loadReferences() {
      try {
        const [
          currenciesResult,
          counterpartiesResult,
        ] = await Promise.all([
          getCurrenciesRequest(),
          getCounterpartiesRequest(),
        ])

        if (cancelled) {
          return
        }

        setCurrencies(
          currenciesResult,
        )

        setCounterparties(
          counterpartiesResult.results,
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
          setLoading(false)
        }
      }
    }

    void loadReferences()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadInvoices() {
      setJournalLoading(true)

      try {
        const result =
          await getInvoicesRequest(
            activeFilters,
          )

        if (cancelled) {
          return
        }

        setInvoices(
          result.results,
        )

        setTotalCount(
          result.count,
        )

        setHasNextPage(
          Boolean(result.next),
        )

        setHasPreviousPage(
          Boolean(
            result.previous,
          ),
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
          setJournalLoading(
            false,
          )
        }
      }
    }

    void loadInvoices()

    return () => {
      cancelled = true
    }
  }, [
    activeFilters,
    reload,
  ])

  function applyFilters(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setActiveFilters({
      page: 1,
      page_size: 20,
      ordering:
        ordering as
          InvoiceFilters['ordering'],
      ...(searchQuery.trim()
        ? {
            search:
              searchQuery.trim(),
          }
        : {}),
      ...(statusFilter
        ? {
            status:
              statusFilter,
          }
        : {}),
      ...(counterpartyFilter
        ? {
            counterparty:
              Number(
                counterpartyFilter,
              ),
          }
        : {}),
      ...(currencyFilter
        ? {
            currency:
              Number(
                currencyFilter,
              ),
          }
        : {}),
      ...(dateFrom
        ? {
            date_from:
              dateFrom,
          }
        : {}),
      ...(dateTo
        ? {
            date_to:
              dateTo,
          }
        : {}),
      ...(overdueFilter
        ? {
            overdue:
              overdueFilter ===
              'true',
          }
        : {}),
    })

    setShowFilters(false)
  }

  function clearFilters() {
    setSearchQuery('')
    setStatusFilter('')
    setCounterpartyFilter('')
    setCurrencyFilter('')
    setDateFrom('')
    setDateTo('')
    setOverdueFilter('')
    setOrdering('-issue_date')

    setActiveFilters({
      page: 1,
      page_size: 20,
      ordering: '-issue_date',
    })
  }

  async function deleteInvoice(
    invoice: Invoice,
  ) {
    const confirmed =
      window.confirm(
        `Удалить инвойс ${invoice.number}?`,
      )

    if (!confirmed) {
      return
    }

    setDeletingId(invoice.id)
    setError('')

    try {
      await deleteInvoiceRequest(
        invoice.id,
      )

      setReload(
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

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем инвойсы...
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header invoices-header">
        <div>
          <p className="eyebrow">
            Документы
          </p>

          <h1>
            Инвойсы
          </h1>

          <p className="muted">
            Выставленные счета
            и состояние их оплаты
          </p>
        </div>

        <Link
          to="/invoices/new"
          className="primary-link-button"
        >
          + Новый инвойс
        </Link>
      </header>

      {error && (
        <div className="error-box invoice-message">
          {error}
        </div>
      )}

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>
              Журнал инвойсов
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
                  (current) =>
                    !current,
                )
              }
              title="Фильтры и поиск"
              aria-label="Фильтры и поиск"
            >
              🔍

              {activeFilterCount > 0 &&
                ` ${activeFilterCount}`}
            </button>
          </div>
        </div>

        {showFilters && (
          <form
            className="invoice-filters"
            onSubmit={
              applyFilters
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
                placeholder="Номер, контрагент, назначение..."
              />
            </label>

            <label>
              Статус

              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(
                    event.target.value,
                  )
                }
              >
                <option value="">
                  Все статусы
                </option>

                {Object.entries(
                  STATUS_LABELS,
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
              Контрагент

              <select
                value={
                  counterpartyFilter
                }
                onChange={(event) =>
                  setCounterpartyFilter(
                    event.target.value,
                  )
                }
              >
                <option value="">
                  Все контрагенты
                </option>

                {counterparties.map(
                  (counterparty) => (
                    <option
                      key={
                        counterparty.id
                      }
                      value={
                        counterparty.id
                      }
                    >
                      {
                        counterparty.name
                      }
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Валюта

              <select
                value={
                  currencyFilter
                }
                onChange={(event) =>
                  setCurrencyFilter(
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
                      key={
                        currency.id
                      }
                      value={
                        currency.id
                      }
                    >
                      {currency.code}
                    </option>
                  ),
                )}
              </select>
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
              Оплата

              <select
                value={overdueFilter}
                onChange={(event) =>
                  setOverdueFilter(
                    event.target.value,
                  )
                }
              >
                <option value="">
                  Все
                </option>

                <option value="true">
                  Просроченные
                </option>

                <option value="false">
                  Не просроченные
                </option>
              </select>
            </label>

            <label>
              Сортировка

              <select
                value={ordering}
                onChange={(event) =>
                  setOrdering(
                    event.target.value,
                  )
                }
              >
                <option value="-issue_date">
                  Сначала новые
                </option>

                <option value="issue_date">
                  Сначала старые
                </option>

                <option value="-total_amount">
                  Сумма по убыванию
                </option>

                <option value="total_amount">
                  Сумма по возрастанию
                </option>

                <option value="number">
                  По номеру
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
                  clearFilters
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
        ) : invoices.length === 0 ? (
          <div className="empty-state">
            <h3>
              Инвойсов пока нет
            </h3>

            <p className="muted">
              Создадим первый
              инвойс следующим шагом.
            </p>
          </div>
        ) : (
          <div className="invoice-table">
            <div className="invoice-table-header">
              <span>Номер</span>
              <span>Дата</span>
              <span>Контрагент</span>
              <span>Сумма</span>
              <span>Срок</span>
              <span>Статус</span>
              <span>Действия</span>
            </div>

            {invoices.map(
              (invoice) => {
                const currency =
                  currencies.find(
                    (item) =>
                      item.id ===
                      invoice.currency,
                  )

                const counterparty =
                  counterparties.find(
                    (item) =>
                      item.id ===
                      invoice.counterparty,
                  )

                return (
                  <div
                    key={invoice.id}
                    className="invoice-table-row"
                  >
                    <Link
                      to={`/invoices/${invoice.id}`}
                      className="invoice-number-link"
                    >
                      {invoice.number}
                    </Link>

                    <span>
                      {formatDate(
                        invoice.issue_date,
                      )}
                    </span>

                    <span>
                      {counterparty?.name ??
                        '—'}
                    </span>

                    <strong>
                      {formatAmount(
                        invoice.total_amount,
                      )}{' '}
                      {currency?.code ??
                        ''}
                    </strong>

                    <span>
                      {formatDate(
                        invoice.due_date,
                      )}
                    </span>

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

                    <div className="invoice-actions">

                      <Link
                        to={`/invoices/${invoice.id}`}
                        className="income-edit-button"
                      >
                        Открыть
                      </Link>

                      {invoice.status ===
                        'draft' && (
                        <button
                          type="button"
                          className="income-delete-button"
                          disabled={
                            deletingId ===
                            invoice.id
                          }
                          onClick={() => {
                            void deleteInvoice(
                              invoice,
                            )
                          }}
                        >
                          {deletingId ===
                          invoice.id
                            ? 'Удаляем...'
                            : 'Удалить'}
                        </button>
                      )}
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
                      (current.page ??
                        1) - 1,
                    ),
                  }),
                )
              }
            >
              ← Назад
            </button>

            <span>
              Страница{' '}
              {activeFilters.page ??
                1}
              {' из '}
              {Math.max(
                1,
                Math.ceil(
                  totalCount /
                    (
                      activeFilters
                        .page_size ??
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
                      (current.page ??
                        1) + 1,
                  }),
                )
              }
            >
              Далее →
            </button>
          </div>
        )}
      </section>
    </main>
  )
}