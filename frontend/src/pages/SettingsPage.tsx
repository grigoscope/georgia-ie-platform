import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  getAccountsRequest,
  getCurrenciesRequest,
  updateAccountRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  getProfileRequest,
  updateProfileRequest,
} from '../api/profile'

export function SettingsPage() {

  const [
    account,
    setAccount,
  ] = useState<FinancialAccount | null>(
    null,
  )

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>([])

  const [loading, setLoading] =
    useState(true)

  const [savingProfile, setSavingProfile] =
    useState(false)

  const [savingAccount, setSavingAccount] =
    useState(false)

  const [error, setError] =
    useState('')

  const [message, setMessage] =
    useState('')

  const [
    businessName,
    setBusinessName,
  ] = useState('')

  const [tin, setTin] =
    useState('')

  const [
    entrepreneurStatus,
    setEntrepreneurStatus,
  ] = useState('small_business')

  const [
    legalAddress,
    setLegalAddress,
  ] = useState('')

  const [email, setEmail] =
    useState('')

  const [phone, setPhone] =
    useState('')

  const [taxRate, setTaxRate] =
    useState('1.00')

  const [
    accountingStartDate,
    setAccountingStartDate,
  ] = useState('')

  const [language, setLanguage] =
    useState('ru')

  const [
    invoicePrefix,
    setInvoicePrefix,
  ] = useState('INV-')

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

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [
          profileResult,
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getProfileRequest(),
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        if (cancelled) {
          return
        }

        setCurrencies(currenciesResult)

        setBusinessName(
          profileResult.business_name,
        )

        setTin(
          profileResult.tin,
        )

        setEntrepreneurStatus(
          profileResult.entrepreneur_status ||
            'small_business',
        )

        setLegalAddress(
          profileResult.legal_address,
        )

        setEmail(
          profileResult.email,
        )

        setPhone(
          profileResult.phone,
        )

        setTaxRate(
          profileResult.tax_rate,
        )

        setAccountingStartDate(
          profileResult.accounting_start_date ??
            '',
        )

        setLanguage(
          profileResult.language,
        )

        setInvoicePrefix(
          profileResult.invoice_prefix,
        )

        const currentAccount =
          accountsResult.find(
            (item) => item.is_default,
          ) ??
          accountsResult[0] ??
          null

        setAccount(currentAccount)

        if (currentAccount) {
          setAccountName(
            currentAccount.name,
          )

          setAccountType(
            currentAccount.type,
          )

          setCurrencyId(
            String(
              currentAccount.default_currency,
            ),
          )

          setProviderName(
            currentAccount.provider_name,
          )

          setIban(
            currentAccount.iban,
          )

          setUseInInvoices(
            currentAccount.use_in_invoices,
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

  async function saveProfile(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setSavingProfile(true)
    setError('')
    setMessage('')

    try {
        await updateProfileRequest({
            business_name:
                businessName.trim(),
            entrepreneur_status:
                entrepreneurStatus,
            tin: tin.trim(),
            legal_address:
                legalAddress.trim(),
            email: email.trim(),
            phone: phone.trim(),
            tax_rate: taxRate,
            accounting_start_date:
                accountingStartDate || null,
            timezone: 'Asia/Tbilisi',
            language,
            invoice_prefix:
                invoicePrefix.trim() ||
                'INV-',
            })

      setMessage(
        'Профиль сохранён',
      )
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setSavingProfile(false)
    }
  }

  async function saveAccount(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (!account) {
      return
    }

    setSavingAccount(true)
    setError('')
    setMessage('')

    try {
      const result =
        await updateAccountRequest(
          account.id,
          {
            name: accountName.trim(),
            type: accountType,
            default_currency:
              Number(currencyId),
            provider_name:
              providerName.trim(),
            iban: iban.trim(),
            use_in_invoices:
              useInInvoices,
          },
        )

      setAccount(result)

      setMessage(
        'Финансовый счёт сохранён',
      )
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setSavingAccount(false)
    }
  }

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем настройки...
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header">
        <p className="eyebrow">
          Настройки
        </p>

        <h1>
          Настройки аккаунта
        </h1>

        <p className="muted">
          Здесь можно изменить
          данные предпринимателя
          и финансового счёта.
        </p>
      </header>

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

      <section className="card settings-section">
        <h2>
          Профиль предпринимателя
        </h2>

        <form
          className="form-grid"
          onSubmit={saveProfile}
        >
          <label>
            Название бизнеса

            <input
              value={businessName}
              onChange={(event) =>
                setBusinessName(
                  event.target.value,
                )
              }
              required
            />
          </label>

          <label>
            ИНН

            <input
              value={tin}
              onChange={(event) =>
                setTin(
                  event.target.value,
                )
              }
              required
            />
          </label>

          <label>
            Налоговый статус

            <select
              value={entrepreneurStatus}
              onChange={(event) =>
                setEntrepreneurStatus(
                  event.target.value,
                )
              }
            >
              <option value="small_business">
                Малый бизнес
              </option>

              <option value="micro_business">
                Микробизнес
              </option>

              <option value="general">
                Без специального статуса
              </option>
            </select>
          </label>

          <label>
            Налоговая ставка, %

            <input
              type="number"
              min="0"
              step="0.01"
              value={taxRate}
              onChange={(event) =>
                setTaxRate(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Юридический адрес

            <input
              value={legalAddress}
              onChange={(event) =>
                setLegalAddress(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Телефон

            <input
              value={phone}
              onChange={(event) =>
                setPhone(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Публичный email

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Начало учёта

            <input
              type="date"
              value={accountingStartDate}
              onChange={(event) =>
                setAccountingStartDate(
                  event.target.value,
                )
              }
            />
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
              <option value="ru">
                Русский
              </option>

              <option value="en">
                English
              </option>

              <option value="ka">
                ქართული
              </option>
            </select>
          </label>

          <label>
            Префикс инвойса

            <input
              value={invoicePrefix}
              onChange={(event) =>
                setInvoicePrefix(
                  event.target.value,
                )
              }
            />
          </label>

          <button
            className="form-submit"
            type="submit"
            disabled={savingProfile}
          >
            {savingProfile
              ? 'Сохраняем...'
              : 'Сохранить профиль'}
          </button>
        </form>
      </section>

      <section className="card settings-section">
        <h2>
          Финансовый счёт
        </h2>

        {account ? (
          <form
            className="form-grid"
            onSubmit={saveAccount}
          >
            <label>
              Название

              <input
                value={accountName}
                onChange={(event) =>
                  setAccountName(
                    event.target.value,
                  )
                }
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
              />
            </label>

            <label className="wide">
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

            <label className="checkbox-row wide">
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
              className="form-submit"
              type="submit"
              disabled={savingAccount}
            >
              {savingAccount
                ? 'Сохраняем...'
                : 'Сохранить счёт'}
            </button>
          </form>
        ) : (
          <p className="muted">
            Финансовый счёт не найден.
          </p>
        )}
      </section>
    </main>
  )
}