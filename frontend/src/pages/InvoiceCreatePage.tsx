import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  Link,
  useNavigate,
} from 'react-router-dom'

import {
  createInvoiceRequest,
} from '../api/invoices'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  createCounterpartyRequest,
  getAccountsRequest,
  getCounterpartiesRequest,
  getCurrenciesRequest,
  type Counterparty,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

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
  ).format(new Date())
}

export function InvoiceCreatePage() {
  const navigate = useNavigate()

  const [
    counterparties,
    setCounterparties,
  ] = useState<Counterparty[]>([])

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

  const [saving, setSaving] =
    useState(false)

  const [error, setError] =
    useState('')

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

        setAccounts(
          accountsResult.filter(
            (account) =>
              account.is_active &&
              account.use_in_invoices,
          ),
        )

        setCurrencies(
          currenciesResult.filter(
            (currency) =>
              currency.is_active,
          ),
        )

        setCounterparties(
          counterpartiesResult.results,
        )

        const defaultAccount =
          accountsResult.find(
            (account) =>
              account.is_active &&
              account.use_in_invoices &&
              account.is_default,
          ) ??
          accountsResult.find(
            (account) =>
              account.is_active &&
              account.use_in_invoices,
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

    void load()
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
                  [field]: value,
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

    async function addCounterparty() {
    if (!newCounterpartyName.trim()) {
        setError(
        'Введите имя или название контрагента',
        )

        return
    }

    setCounterpartySaving(true)
    setError('')

    try {
        const created =
        await createCounterpartyRequest({
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
        })

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

        setShowCounterpartyForm(false)
    } catch (requestError) {
        setError(
        getApiErrorMessage(
            requestError,
        ),
        )
    } finally {
        setCounterpartySaving(false)
    }
    }

  async function submit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setError('')

    if (!counterpartyId) {
      setError(
        'Выберите контрагента',
      )

      return
    }

    if (!accountId) {
      setError(
        'Выберите счёт для оплаты',
      )

      return
    }

    if (!currencyId) {
      setError(
        'Выберите валюту',
      )

      return
    }

    setSaving(true)

    try {
      const invoice =
        await createInvoiceRequest({
          issue_date: issueDate,
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
          items: items.map(
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
          discount_amount: '0',
          extra_charge_amount: '0',
          tax_note: '',
          tax_reference_amount:
            null,
          payment_purpose: '',
          notes: '',
        })

      navigate(
        `/invoices/${invoice.id}`,
      )
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
          Загружаем форму...
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header invoice-detail-header">
        <div>
          <p className="eyebrow">
            Инвойсы
          </p>

          <h1>
            Новый инвойс
          </h1>

          <p className="muted">
            Создание нового счёта
          </p>
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

      <form
        onSubmit={submit}
        className="card invoice-create-form"
      >
        <div className="form-grid">
          <label>
            Дата выставления

            <input
              type="date"
              lang="ru"
              value={issueDate}
              onChange={(event) =>
                setIssueDate(
                  event.target.value,
                )
              }
              required
            />
          </label>

          <label>
            Срок оплаты

            <input
              type="date"
              lang="ru"
              min={issueDate}
              value={dueDate}
              onChange={(event) =>
                setDueDate(
                  event.target.value,
                )
              }
            />
          </label>

          <div className="counterparty-field">
  <label>
    Контрагент

    <select
      value={counterpartyId}
      onChange={(event) =>
        setCounterpartyId(
          event.target.value,
        )
      }
      required
    >
      <option value="">
        Выберите
      </option>

      {counterparties.map(
        (counterparty) => (
          <option
            key={counterparty.id}
            value={counterparty.id}
          >
            {counterparty.name}
          </option>
        ),
      )}
    </select>
  </label>

  <button
    type="button"
    className="secondary counterparty-add-button"
    onClick={() =>
      setShowCounterpartyForm(
        (current) => !current,
      )
    }
  >
    {showCounterpartyForm
      ? 'Закрыть'
      : '+ Новый контрагент'}
  </button>
</div>

{showCounterpartyForm && (
  <div className="quick-counterparty-card">
    <div className="quick-counterparty-header">
      <div>
        <h3>
          Новый контрагент
        </h3>

        <p className="muted">
          Добавьте клиента,
          которому выставляете счёт
        </p>
      </div>
    </div>

    <div className="form-grid">
      <label>
        Название / имя

        <input
          value={
            newCounterpartyName
          }
          onChange={(event) =>
            setNewCounterpartyName(
              event.target.value,
            )
          }
          placeholder="ООО Компания"
        />
      </label>

      <label>
        Тип

        <select
          value={
            newCounterpartyType
          }
          onChange={(event) =>
            setNewCounterpartyType(
              event.target.value as
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
          onChange={(event) =>
            setNewCounterpartyCountry(
              event.target.value,
            )
          }
          placeholder="Georgia"
        />
      </label>

      <label>
        Налоговый номер

        <input
          value={
            newCounterpartyTaxId
          }
          onChange={(event) =>
            setNewCounterpartyTaxId(
              event.target.value,
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
          onChange={(event) =>
            setNewCounterpartyAddress(
              event.target.value,
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
          onChange={(event) =>
            setNewCounterpartyEmail(
              event.target.value,
            )
          }
        />
      </label>
    </div>

    <button
      type="button"
      disabled={
        counterpartySaving ||
        !newCounterpartyName.trim()
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
                      account
                        .default_currency,
                    ),
                  )
                }
              }}
              required
            >
              <option value="">
                Выберите
              </option>

              {accounts.map(
                (account) => (
                  <option
                    key={account.id}
                    value={account.id}
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
            Валюта

            <select
              value={currencyId}
              onChange={(event) =>
                setCurrencyId(
                  event.target.value,
                )
              }
              required
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
                    {currency.code}
                    {' — '}
                    {currency.name}
                  </option>
                ),
              )}
            </select>
          </label>

          <label>
            Язык

            <select
              value={language}
              onChange={(event) =>
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

              <option value="ka">
                ქართული
              </option>
            </select>
          </label>
        </div>

        <div className="invoice-items-heading">
          <div>
            <h2>
              Позиции
            </h2>

            <p className="muted">
              Сумму рассчитает сервер
            </p>
          </div>

          <button
            type="button"
            className="secondary"
            onClick={addItem}
          >
            + Добавить позицию
          </button>
        </div>

        <div className="invoice-items">
          {items.map(
            (item, index) => (
              <div
                key={item.id}
                className="invoice-item-card"
              >
                <strong>
                  Позиция {index + 1}
                </strong>

                <label>
                  Описание

                  <input
                    value={
                      item.description
                    }
                    onChange={(event) =>
                      updateItem(
                        item.id,
                        'description',
                        event.target.value,
                      )
                    }
                    placeholder="Разработка сайта"
                    required
                  />
                </label>

                <div className="invoice-item-fields">
                  <label>
                    Количество

                    <input
                      type="number"
                      min="0.001"
                      step="0.001"
                      value={
                        item.quantity
                      }
                      onChange={(event) =>
                        updateItem(
                          item.id,
                          'quantity',
                          event.target.value,
                        )
                      }
                      required
                    />
                  </label>

                  <label>
                    Единица

                    <input
                      value={
                        item.unit
                      }
                      onChange={(event) =>
                        updateItem(
                          item.id,
                          'unit',
                          event.target.value,
                        )
                      }
                    />
                  </label>

                  <label>
                    Цена

                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={
                        item.unit_price
                      }
                      onChange={(event) =>
                        updateItem(
                          item.id,
                          'unit_price',
                          event.target.value,
                        )
                      }
                      required
                    />
                  </label>
                </div>

                {items.length > 1 && (
                  <button
                    type="button"
                    className="income-delete-button"
                    onClick={() =>
                      removeItem(
                        item.id,
                      )
                    }
                  >
                    Удалить позицию
                  </button>
                )}
              </div>
            ),
          )}
        </div>

        <button
          type="submit"
          className="form-submit"
          disabled={saving}
        >
          {saving
            ? 'Создаём...'
            : 'Создать инвойс'}
        </button>
      </form>
    </main>
  )
}