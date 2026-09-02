import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  useNavigate,
} from 'react-router-dom'

import {
  createAccountRequest,
  getAccountsRequest,
  getCurrenciesRequest,
  setDefaultAccountRequest,
  type Currency,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  getProfileRequest,
  updateProfileRequest,
  type EntrepreneurProfile,
} from '../api/profile'

export function OnboardingPage() {
  const navigate = useNavigate()

  const [profile, setProfile] =
    useState<EntrepreneurProfile | null>(
      null,
    )

  const [hasAccount, setHasAccount] =
    useState(false)

  const [currencies, setCurrencies] =
    useState<Currency[]>([])

  const [loading, setLoading] =
    useState(true)

  const [saving, setSaving] =
    useState(false)

  const [error, setError] =
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
  ] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [
          profileResult,
          accountsResult,
          currencyResult,
        ] = await Promise.all([
          getProfileRequest(),
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        if (cancelled) {
          return
        }

        setProfile(profileResult)

        setHasAccount(
          accountsResult.length > 0,
        )

        setCurrencies(
          currencyResult,
        )

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
          profileResult
            .accounting_start_date ??
            '',
        )

        setLanguage(
          profileResult.language,
        )

        setInvoicePrefix(
          profileResult.invoice_prefix,
        )

        const gel =
          currencyResult.find(
            (currency) =>
              currency.code === 'GEL',
          )

        if (gel) {
          setCurrencyId(
            String(gel.id),
          )
        } else if (
          currencyResult.length > 0
        ) {
          setCurrencyId(
            String(
              currencyResult[0].id,
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

  async function saveProfile(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setSaving(true)
    setError('')

    try {
      const result =
        await updateProfileRequest({
          business_name:
            businessName.trim(),
          entrepreneur_status:
            entrepreneurStatus.trim(),
          tin: tin.trim(),
          legal_address:
            legalAddress.trim(),
          email: email.trim(),
          phone: phone.trim(),
          tax_rate: taxRate,
          accounting_start_date:
            accountingStartDate ||
            null,
          timezone: 'Asia/Tbilisi',
          language,
          invoice_prefix:
            invoicePrefix.trim() ||
            'INV-',
        })

      setProfile(result)
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

  async function saveAccount(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setSaving(true)
    setError('')

    try {
      const selectedCurrency =
        Number(currencyId)

      if (!selectedCurrency) {
        setError(
          'Выберите валюту счёта',
        )

        return
      }

      const account =
        await createAccountRequest({
          name: accountName.trim(),
          type: accountType,
          default_currency:
            selectedCurrency,
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

      await setDefaultAccountRequest(
        account.id,
      )

      setHasAccount(true)

      navigate('/')
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
      <main className="center-page">
        <div className="card">
          Загружаем настройки...
        </div>
      </main>
    )
  }

  if (
    profile?.profile_exists &&
    hasAccount
  ) {
    return (
      <main className="center-page">
        <section className="card onboarding-card">
          <p className="eyebrow">
            Georgia IE
          </p>

          <h1>
            Всё готово
          </h1>

          <p className="muted">
            Профиль и финансовый
            счёт уже настроены.
          </p>

          <button
            type="button"
            onClick={() =>
              navigate('/')
            }
          >
            Перейти в Dashboard
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="center-page onboarding-page">
      <section className="card onboarding-card">
        <p className="eyebrow">
          Georgia IE
        </p>

        <h1>
          Настройка аккаунта
        </h1>

        <div className="steps">
          <div
            className={
              profile?.profile_exists
                ? 'step complete'
                : 'step active'
            }
          >
            <span>1</span>
            Профиль
          </div>

          <div
            className={
              profile?.profile_exists
                ? 'step active'
                : 'step'
            }
          >
            <span>2</span>
            Финансовый счёт
          </div>
        </div>

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        {!profile?.profile_exists ? (
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

            <p className="field-hint">
                Статус, зарегистрированный
                в Revenue Service Грузии
            </p>

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
                required
              />
            </label>

            <label>
              Начало учёта

              <input
                type="date"
                value={
                  accountingStartDate
                }
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
              disabled={saving}
            >
              {saving
                ? 'Сохраняем...'
                : 'Продолжить'}
            </button>
          </form>
        ) : (
          <form
            className="form-grid"
            onSubmit={saveAccount}
          >
            <div className="form-heading">
              <h2>
                Первый финансовый счёт
              </h2>

              <p className="muted">
                Он будет установлен
                счётом по умолчанию.
              </p>
            </div>

            <label>
              Название

              <input
                value={accountName}
                onChange={(event) =>
                  setAccountName(
                    event.target.value,
                  )
                }
                placeholder="Например: TBC GEL"
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
                            currency.kind === 'fiat',
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
                            currency.kind === 'crypto',
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
                placeholder="TBC Bank"
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

              Использовать этот счёт
              в инвойсах
            </label>

            <button
              className="form-submit"
              type="submit"
              disabled={saving}
            >
              {saving
                ? 'Создаём...'
                : 'Завершить настройку'}
            </button>
          </form>
        )}
      </section>
    </main>
  )
}