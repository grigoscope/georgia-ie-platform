import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  createAccountRequest,
  getAccountsRequest,
  getCurrenciesRequest,
  setDefaultAccountRequest,
  updateAccountRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

const ACCOUNT_TYPE_LABELS: Record<
  string,
  string
> = {
  bank_account:
    'Банковский счёт',
  bank_card:
    'Банковская карта',
  cash:
    'Наличные',
  cash_register:
    'Кассовый аппарат',
  physical_pos:
    'POS-терминал',
  payment_system:
    'Платёжная система',
  crypto_wallet:
    'Криптокошелёк',
  other:
    'Другое',
}

export function AccountsSection() {
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

  const [
    selectedId,
    setSelectedId,
  ] = useState<
    number | 'new' | null
  >(null)

  const [loading, setLoading] =
    useState(true)

  const [saving, setSaving] =
    useState(false)

  const [error, setError] =
    useState('')

  const [message, setMessage] =
    useState('')

  const [
    accountName,
    setAccountName,
  ] = useState('')

  const [
    accountType,
    setAccountType,
  ] = useState('bank_account')

  const [
    currencyId,
    setCurrencyId,
  ] = useState('')

  const [
    providerName,
    setProviderName,
  ] = useState('')

  const [iban, setIban] =
    useState('')

  const [
    useInInvoices,
    setUseInInvoices,
  ] = useState(false)

  const selectedAccount =
    typeof selectedId === 'number'
      ? accounts.find(
          (account) =>
            account.id ===
            selectedId,
        ) ?? null
      : null

  function fillAccount(
    account: FinancialAccount,
  ) {
    setAccountName(
      account.name,
    )

    setAccountType(
      account.type,
    )

    setCurrencyId(
      String(
        account.default_currency,
      ),
    )

    setProviderName(
      account.provider_name,
    )

    setIban(
      account.iban,
    )

    setUseInInvoices(
      account.use_in_invoices,
    )
  }

  function getDefaultCurrencyId(
    availableCurrencies: Currency[],
  ) {
    const gel =
      availableCurrencies.find(
        (currency) =>
          currency.code === 'GEL',
      )

    return gel
      ? String(gel.id)
      : availableCurrencies[0]
        ? String(
            availableCurrencies[0]
              .id,
          )
        : ''
  }

  async function refreshAccounts() {
    const result =
      await getAccountsRequest()

    setAccounts(result)

    return result
  }

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        if (cancelled) {
          return
        }

        setAccounts(
          accountsResult,
        )

        setCurrencies(
          currenciesResult,
        )

        const initialAccount =
          accountsResult.find(
            (account) =>
              account.is_default &&
              account.is_active,
          ) ??
          accountsResult.find(
            (account) =>
              account.is_active,
          )

        if (initialAccount) {
          setSelectedId(
            initialAccount.id,
          )

          fillAccount(
            initialAccount,
          )
        } else {
          setSelectedId('new')

          setCurrencyId(
            getDefaultCurrencyId(
              currenciesResult,
            ),
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
  }, [])

  function startNewAccount() {
    setSelectedId('new')
    setAccountName('')
    setAccountType('bank_account')

    setCurrencyId(
      getDefaultCurrencyId(
        currencies,
      ),
    )

    setProviderName('')
    setIban('')
    setUseInInvoices(false)
    setError('')
    setMessage('')
  }

  function selectAccount(
    account: FinancialAccount,
  ) {
    setSelectedId(account.id)
    fillAccount(account)
    setError('')
    setMessage('')
  }

  async function saveAccount(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setSaving(true)
    setError('')
    setMessage('')

    try {
      if (!currencyId) {
        throw new Error(
          'Выберите валюту',
        )
      }

      if (selectedId === 'new') {
        const hadActiveAccounts =
          accounts.some(
            (account) =>
              account.is_active,
          )

        const created =
          await createAccountRequest({
            name:
              accountName.trim(),
            type: accountType,
            default_currency:
              Number(currencyId),
            provider_name:
              providerName.trim(),
            account_holder: '',
            iban: iban.trim(),
            swift_bic: '',
            account_identifier: '',
            crypto_asset: '',
            crypto_network: '',
            wallet_address: '',
            memo_tag: '',
            default_declaration_category:
              '',
            payment_instructions: '',
            use_in_invoices:
              useInInvoices,
            is_active: true,
          })

        if (!hadActiveAccounts) {
          await setDefaultAccountRequest(
            created.id,
          )
        }

        const updatedAccounts =
          await refreshAccounts()

        const updated =
          updatedAccounts.find(
            (account) =>
              account.id ===
              created.id,
          )

        if (updated) {
          setSelectedId(
            updated.id,
          )

          fillAccount(updated)
        }

        setMessage(
          'Финансовый счёт добавлен',
        )
      } else if (
        typeof selectedId ===
        'number'
      ) {
        const updated =
          await updateAccountRequest(
            selectedId,
            {
              name:
                accountName.trim(),
              type: accountType,
              default_currency:
                Number(currencyId),
              provider_name:
                providerName.trim(),
              iban:
                iban.trim(),
              use_in_invoices:
                useInInvoices,
            },
          )

        setAccounts(
          (current) =>
            current.map(
              (account) =>
                account.id ===
                updated.id
                  ? updated
                  : account,
            ),
        )

        fillAccount(updated)

        setMessage(
          'Финансовый счёт сохранён',
        )
      }
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

  async function makeDefault(
    account: FinancialAccount,
  ) {
    setError('')
    setMessage('')

    try {
      await setDefaultAccountRequest(
        account.id,
      )

      const updatedAccounts =
        await refreshAccounts()

      const updated =
        updatedAccounts.find(
          (item) =>
            item.id === account.id,
        )

      if (updated) {
        setSelectedId(
          updated.id,
        )

        fillAccount(updated)
      }

      setMessage(
        `${account.name} теперь основной счёт`,
      )
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    }
  }

  if (loading) {
    return (
      <section className="card settings-section">
        Загружаем финансовые счета...
      </section>
    )
  }

  const activeAccounts =
    accounts.filter(
      (account) =>
        account.is_active,
    )

  return (
    <section className="card settings-section">
      <div className="accounts-heading">
        <div>
          <h2>
            Финансовые счета
          </h2>

          <p className="muted">
            Можно добавить несколько
            счетов в разных банках
            и валютах.
          </p>
        </div>

        <button
          type="button"
          onClick={
            startNewAccount
          }
        >
          + Добавить счёт
        </button>
      </div>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {message && (
        <div className="success-box">
          {message}
        </div>
      )}

      <div className="accounts-grid">
        <div className="accounts-list">
          {activeAccounts.length ===
          0 ? (
            <p className="muted">
              Счетов пока нет
            </p>
          ) : (
            activeAccounts.map(
              (account) => (
                <div
                  key={account.id}
                  className={
                    selectedId ===
                    account.id
                      ? 'account-card selected'
                      : 'account-card'
                  }
                >
                  <button
                    type="button"
                    className="account-select"
                    onClick={() =>
                      selectAccount(
                        account,
                      )
                    }
                  >
                    <div>
                      <strong>
                        {account.name}
                      </strong>

                      <p className="muted">
                        {
                          ACCOUNT_TYPE_LABELS[
                            account.type
                          ]
                        }
                      </p>
                    </div>

                    <div className="account-card-right">
                      <strong>
                        {
                          account.default_currency_code
                        }
                      </strong>

                      {account.is_default && (
                        <span className="account-badge">
                          Основной
                        </span>
                      )}
                    </div>
                  </button>

                  {!account.is_default && (
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => {
                        void makeDefault(
                          account,
                        )
                      }}
                    >
                      Сделать основным
                    </button>
                  )}
                </div>
              ),
            )
          )}
        </div>

        <form
          className="account-editor"
          onSubmit={saveAccount}
        >
          <h3>
            {selectedId === 'new'
              ? 'Новый счёт'
              : 'Редактирование счёта'}
          </h3>

          {selectedAccount?.is_default && (
            <p className="account-default-note">
              Основной финансовый счёт
            </p>
          )}

          <label>
            Название

            <input
              value={accountName}
              onChange={(event) =>
                setAccountName(
                  event.target.value,
                )
              }
              placeholder="Например: TBC USD"
              required
            />
          </label>

          <label>
            Тип счёта

            <select
              value={accountType}
              onChange={(event) =>
                setAccountType(
                  event.target.value,
                )
              }
            >
              <option value="bank_account">
                Банковский счёт
              </option>

              <option value="bank_card">
                Банковская карта
              </option>

              <option value="cash">
                Наличные
              </option>

              <option value="cash_register">
                Кассовый аппарат
              </option>

              <option value="physical_pos">
                POS-терминал
              </option>

              <option value="payment_system">
                Платёжная система
              </option>

              <option value="crypto_wallet">
                Криптокошелёк
              </option>

              <option value="other">
                Другое
              </option>
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
              <optgroup label="Обычные валюты">
                {currencies
                  .filter(
                    (currency) =>
                      currency.kind ===
                      'fiat',
                  )
                  .map(
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
              </optgroup>

              <optgroup label="Криптовалюты">
                {currencies
                  .filter(
                    (currency) =>
                      currency.kind ===
                      'crypto',
                  )
                  .map(
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
              </optgroup>
            </select>
          </label>

          <label>
            Банк или провайдер

            <input
              value={providerName}
              onChange={(event) =>
                setProviderName(
                  event.target.value,
                )
              }
              placeholder="Например: TBC Bank"
            />
          </label>

          <label>
            IBAN

            <input
              value={iban}
              onChange={(event) =>
                setIban(
                  event.target.value,
                )
              }
            />
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={useInInvoices}
              onChange={(event) =>
                setUseInInvoices(
                  event.target.checked,
                )
              }
            />

            Использовать в инвойсах
          </label>

          <button
            type="submit"
            disabled={saving}
          >
            {saving
              ? 'Сохраняем...'
              : selectedId === 'new'
                ? 'Добавить счёт'
                : 'Сохранить изменения'}
          </button>
        </form>
      </div>
    </section>
  )
}