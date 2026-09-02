import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  getProfileRequest,
  updateProfileRequest,
} from '../api/profile'

import {
  AccountsSection,
} from '../components/AccountsSection'

export function SettingsPage() {
  const [loading, setLoading] =
    useState(true)

  const [
    savingProfile,
    setSavingProfile,
  ] = useState(false)

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

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const profile =
          await getProfileRequest()

        if (cancelled) {
          return
        }

        setBusinessName(
          profile.business_name,
        )

        setTin(
          profile.tin,
        )

        setEntrepreneurStatus(
          profile.entrepreneur_status ||
            'small_business',
        )

        setLegalAddress(
          profile.legal_address,
        )

        setEmail(
          profile.email,
        )

        setPhone(
          profile.phone,
        )

        setTaxRate(
          profile.tax_rate,
        )

        setAccountingStartDate(
          profile.accounting_start_date ??
            '',
        )

        setLanguage(
          profile.language,
        )

        setInvoicePrefix(
          profile.invoice_prefix,
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
          accountingStartDate ||
          null,
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
          Профиль предпринимателя
          и финансовые счета.
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
            disabled={savingProfile}
          >
            {savingProfile
              ? 'Сохраняем...'
              : 'Сохранить профиль'}
          </button>
        </form>
      </section>

      <AccountsSection />
    </main>
  )
}