import {
  useEffect,
  useState,
} from 'react'

import {
  createInvoiceRequest,
  type Invoice,
} from '../api/invoices'

import {
  createCounterpartyRequest,
  getAccountsRequest,
  getCounterpartiesRequest,
  getCurrenciesRequest,
  type Counterparty,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

type Props = {
  onCreated: (
    invoice: Invoice,
  ) => Promise<void>
  onCancel: () => void
}

type InvoiceItemForm = {
  id: string
  description: string
  quantity: string
  unit: string
  unit_price: string
}

function createItem(): InvoiceItemForm {
  return {
    id: crypto.randomUUID(),
    description: '',
    quantity: '1',
    unit: 'service',
    unit_price: '',
  }
}

function today() {
  return new Intl.DateTimeFormat(
    'sv-SE',
    {
      timeZone: 'Asia/Tbilisi',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    },
  ).format(
    new Date(),
  )
}

export function MiniInvoiceCreateForm({
  onCreated,
  onCancel,
}: Props) {
  const [
    counterparties,
    setCounterparties,
  ] = useState<Counterparty[]>([])

  const [
    accounts,
    setAccounts,
  ] = useState<
    FinancialAccount[]
  >([])

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>([])

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState('')

  const [
    issueDate,
    setIssueDate,
  ] = useState(today())

  const [
    dueDate,
    setDueDate,
  ] = useState('')

  const [
    counterpartyId,
    setCounterpartyId,
  ] = useState('')

  const [
    accountId,
    setAccountId,
  ] = useState('')

  const [
    currencyId,
    setCurrencyId,
  ] = useState('')

  const [
    language,
    setLanguage,
  ] = useState('en')

  const [
    items,
    setItems,
  ] = useState<InvoiceItemForm[]>([
    createItem(),
  ])

  const [
    showCounterpartyForm,
    setShowCounterpartyForm,
  ] = useState(false)

  const [
    counterpartySaving,
    setCounterpartySaving,
  ] = useState(false)

  const [
    newCounterpartyName,
    setNewCounterpartyName,
  ] = useState('')

  const [
    newCounterpartyType,
    setNewCounterpartyType,
  ] = useState<
    | 'individual'
    | 'entrepreneur'
    | 'company'
  >('company')

  const [
    newCounterpartyCountry,
    setNewCounterpartyCountry,
  ] = useState('')

  const [
    newCounterpartyTaxId,
    setNewCounterpartyTaxId,
  ] = useState('')

  const [
    newCounterpartyAddress,
    setNewCounterpartyAddress,
  ] = useState('')

  const [
    newCounterpartyEmail,
    setNewCounterpartyEmail,
  ] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [
          accountsResult,
          currenciesResult,
          counterpartiesResult,
        ] = await Promise.all([
          getAccountsRequest(),
          getCurrenciesRequest(),
          getCounterpartiesRequest(),
        ])

        if (cancelled) {
          return
        }

        const availableAccounts =
          accountsResult.filter(
            (account) =>
              account.is_active &&
              account.use_in_invoices,
          )

        const availableCurrencies =
          currenciesResult.filter(
            (currency) =>
              currency.is_active,
          )

        setAccounts(
          availableAccounts,
        )

        setCurrencies(
          availableCurrencies,
        )

        setCounterparties(
          counterpartiesResult.results,
        )

        const defaultAccount =
          availableAccounts.find(
            (account) =>
              account.is_default,
          ) ??
          availableAccounts[0]

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

        if (
          counterpartiesResult
            .results.length > 0
        ) {
          setCounterpartyId(
            String(
              counterpartiesResult
                .results[0].id,
            ),
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

  function updateItem(
    id: string,
    field:
      | 'description'
      | 'quantity'
      | 'unit'
      | 'unit_price',
    value: string,
  ) {
    setItems(
      (current) =>
        current.map(
          (item) =>
            item.id === id
              ? {
                  ...item,
                  [field]:
                    value,
                }
              : item,
        ),
    )
  }

  function addItem() {
    setItems(
      (current) => [
        ...current,
        createItem(),
      ],
    )
  }

  function removeItem(
    id: string,
  ) {
    setItems(
      (current) =>
        current.length === 1
          ? current
          : current.filter(
              (item) =>
                item.id !== id,
            ),
    )
  }

  function changeAccount(
    value: string,
  ) {
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
    }
  }

  async function addCounterparty() {
    if (
      !newCounterpartyName.trim()
    ) {
      setError(
        'Введите имя или название контрагента',
      )

      return
    }

    setCounterpartySaving(true)
    setError('')

    try {
      const created =
        await createCounterpartyRequest(
          {
            name:
              newCounterpartyName.trim(),

            type:
              newCounterpartyType,

            country:
              newCounterpartyCountry.trim(),

            tax_id:
              newCounterpartyTaxId.trim(),

            address:
              newCounterpartyAddress.trim(),

            email:
              newCounterpartyEmail.trim(),

            phone: '',

            comment: '',
          },
        )

      setCounterparties(
        (current) => [
          ...current,
          created,
        ],
      )

      setCounterpartyId(
        String(created.id),
      )

      setNewCounterpartyName('')
      setNewCounterpartyCountry('')
      setNewCounterpartyTaxId('')
      setNewCounterpartyAddress('')
      setNewCounterpartyEmail('')

      setShowCounterpartyForm(
        false,
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
      setCounterpartySaving(
        false,
      )
    }
  }

  function validate() {
    if (!counterpartyId) {
      return 'Выберите контрагента'
    }

    if (!accountId) {
      return 'Выберите счёт для оплаты'
    }

    if (!currencyId) {
      return 'Выберите валюту'
    }

    if (!issueDate) {
      return 'Укажите дату выставления'
    }

    for (const item of items) {
      if (!item.description.trim()) {
        return 'Заполните описание позиции'
      }

      if (
        !item.quantity ||
        Number(item.quantity) <= 0
      ) {
        return 'Количество должно быть больше нуля'
      }

      if (
        !item.unit_price ||
        Number(item.unit_price) < 0
      ) {
        return 'Укажите цену позиции'
      }
    }

    return ''
  }

  async function saveInvoice() {
    const validationError =
      validate()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      const invoice =
        await createInvoiceRequest(
          {
            issue_date:
              issueDate,

            due_date:
              dueDate || null,

            service_period_start:
              null,

            service_period_end:
              null,

            currency:
              Number(currencyId),

            language,

            counterparty:
              Number(
                counterpartyId,
              ),

            financial_account:
              Number(accountId),

            items:
              items.map(
                (item) => ({
                  description:
                    item.description.trim(),

                  quantity:
                    item.quantity,

                  unit:
                    item.unit.trim() ||
                    'service',

                  unit_price:
                    item.unit_price,
                }),
              ),

            discount_amount:
              '0',

            extra_charge_amount:
              '0',

            tax_note: '',

            tax_reference_amount:
              null,

            payment_purpose:
              '',

            notes: '',
          },
        )

      await onCreated(
        invoice,
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
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <section className="mini-app-card">
        Загружаем форму...
      </section>
    )
  }

  return (
    <section className="mini-app-card mini-invoice-create">
      <div className="mini-invoice-detail-header">
        <button
          type="button"
          className="mini-back-button"
          onClick={onCancel}
        >
          ← Назад
        </button>
      </div>

      <div>
        <p className="eyebrow">
          Инвойсы
        </p>

        <h2>
          Новый инвойс
        </h2>

        <p className="muted">
          Создание счёта
          прямо из Telegram
        </p>
      </div>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      <div className="mini-invoice-create-grid">
        <label>
          Дата выставления

          <input
            type="date"
            value={issueDate}
            onChange={(
              event,
            ) =>
              setIssueDate(
                event.target.value,
              )
            }
          />
        </label>

        <label>
          Срок оплаты

          <input
            type="date"
            min={issueDate}
            value={dueDate}
            onChange={(
              event,
            ) =>
              setDueDate(
                event.target.value,
              )
            }
          />
        </label>

        <label>
          Контрагент

          <select
            value={
              counterpartyId
            }
            onChange={(
              event,
            ) =>
              setCounterpartyId(
                event.target.value,
              )
            }
          >
            <option value="">
              Выберите
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

        <button
          type="button"
          className="secondary"
          onClick={() =>
            setShowCounterpartyForm(
              (current) =>
                !current,
            )
          }
        >
          {showCounterpartyForm
            ? 'Закрыть'
            : '+ Новый контрагент'}
        </button>

        {showCounterpartyForm && (
          <div className="mini-counterparty-create">
            <h3>
              Новый контрагент
            </h3>

            <label>
              Название / имя

              <input
                value={
                  newCounterpartyName
                }
                onChange={(
                  event,
                ) =>
                  setNewCounterpartyName(
                    event.target
                      .value,
                  )
                }
              />
            </label>

            <label>
              Тип

              <select
                value={
                  newCounterpartyType
                }
                onChange={(
                  event,
                ) =>
                  setNewCounterpartyType(
                    event.target
                      .value as
                      | 'individual'
                      | 'entrepreneur'
                      | 'company',
                  )
                }
              >
                <option value="company">
                  Компания
                </option>

                <option value="entrepreneur">
                  Предприниматель
                </option>

                <option value="individual">
                  Физическое лицо
                </option>
              </select>
            </label>

            <label>
              Страна

              <input
                value={
                  newCounterpartyCountry
                }
                onChange={(
                  event,
                ) =>
                  setNewCounterpartyCountry(
                    event.target
                      .value,
                  )
                }
              />
            </label>

            <label>
              Налоговый номер

              <input
                value={
                  newCounterpartyTaxId
                }
                onChange={(
                  event,
                ) =>
                  setNewCounterpartyTaxId(
                    event.target
                      .value,
                  )
                }
              />
            </label>

            <label>
              Адрес

              <input
                value={
                  newCounterpartyAddress
                }
                onChange={(
                  event,
                ) =>
                  setNewCounterpartyAddress(
                    event.target
                      .value,
                  )
                }
              />
            </label>

            <label>
              Email

              <input
                type="email"
                value={
                  newCounterpartyEmail
                }
                onChange={(
                  event,
                ) =>
                  setNewCounterpartyEmail(
                    event.target
                      .value,
                  )
                }
              />
            </label>

            <button
              type="button"
              disabled={
                counterpartySaving
              }
              onClick={() => {
                void addCounterparty()
              }}
            >
              {counterpartySaving
                ? 'Сохраняем...'
                : 'Добавить контрагента'}
            </button>
          </div>
        )}

        <label>
          Счёт для оплаты

          <select
            value={accountId}
            onChange={(
              event,
            ) =>
              changeAccount(
                event.target.value,
              )
            }
          >
            <option value="">
              Выберите
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
                  {account.name}
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
          Валюта инвойса

          <select
            value={currencyId}
            onChange={(
              event,
            ) =>
              setCurrencyId(
                event.target.value,
              )
            }
          >
            <option value="">
              Выберите
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
                  {
                    currency.code
                  }
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          Язык инвойса

          <select
            value={language}
            onChange={(
              event,
            ) =>
              setLanguage(
                event.target.value,
              )
            }
          >
            <option value="en">
              English
            </option>

            <option value="ru">
              Русский
            </option>
          </select>
        </label>
      </div>

      <div className="mini-invoice-items-create">
        <div className="mini-section-heading">
          <div>
            <h3>
              Позиции
            </h3>

            <p className="muted">
              Товары или услуги
            </p>
          </div>

          <button
            type="button"
            className="mini-text-button"
            onClick={addItem}
          >
            + Добавить
          </button>
        </div>

        {items.map(
          (
            item,
            index,
          ) => (
            <div
              key={item.id}
              className="mini-invoice-item-create"
            >
              <div className="mini-invoice-item-create-header">
                <strong>
                  Позиция{' '}
                  {index + 1}
                </strong>

                {items.length > 1 && (
                  <button
                    type="button"
                    className="mini-remove-item"
                    onClick={() =>
                      removeItem(
                        item.id,
                      )
                    }
                  >
                    Удалить
                  </button>
                )}
              </div>

              <label>
                Описание

                <input
                  value={
                    item.description
                  }
                  onChange={(
                    event,
                  ) =>
                    updateItem(
                      item.id,
                      'description',
                      event.target
                        .value,
                    )
                  }
                />
              </label>

              <div className="mini-invoice-item-row">
                <label>
                  Количество

                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={
                      item.quantity
                    }
                    onChange={(
                      event,
                    ) =>
                      updateItem(
                        item.id,
                        'quantity',
                        event.target
                          .value,
                      )
                    }
                  />
                </label>

                <label>
                  Единица

                  <input
                    value={
                      item.unit
                    }
                    onChange={(
                      event,
                    ) =>
                      updateItem(
                        item.id,
                        'unit',
                        event.target
                          .value,
                      )
                    }
                  />
                </label>
              </div>

              <label>
                Цена за единицу

                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={
                    item.unit_price
                  }
                  onChange={(
                    event,
                  ) =>
                    updateItem(
                      item.id,
                      'unit_price',
                      event.target
                        .value,
                    )
                  }
                />
              </label>
            </div>
          ),
        )}
      </div>

      <button
        type="button"
        disabled={saving}
        onClick={() => {
          void saveInvoice()
        }}
      >
        {saving
          ? 'Создаём...'
          : 'Создать инвойс'}
      </button>
    </section>
  )
}