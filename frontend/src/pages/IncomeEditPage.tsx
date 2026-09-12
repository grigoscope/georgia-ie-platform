import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react'

import {
  Link,
  useNavigate,
  useParams,
} from 'react-router-dom'

import {
  getAccountsRequest,
  getCurrenciesRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

import {
  getIncomeRequest,
  previewIncomeRequest,
  updateIncomeRequest,
  type IncomeEntry,
  type IncomePreview,
} from '../api/incomes'

import {
  DateTimeField,
} from '../components/DateTimeField'

const CATEGORY_LABELS: Record<
  string,
  string
> = {
  cash_register_18:
    'Графа 18 — кассовый аппарат',
  physical_pos_19:
    'Графа 19 — физический POS',
  cashless_20:
    'Графа 20 — безналичные поступления',
  other_21:
    'Графа 21 — прочие доходы и криптовалюта',
}

type RateMode =
  | 'automatic'
  | 'manual'
  | 'ready_gel'

function toTbilisiInput(
  value: string,
) {
  const formatter =
    new Intl.DateTimeFormat(
      'sv-SE',
      {
        timeZone: 'Asia/Tbilisi',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      },
    )

  const parts =
    formatter.formatToParts(
      new Date(value),
    )

  const values: Record<
    string,
    string
  > = {}

  for (const part of parts) {
    values[part.type] =
      part.value
  }

  return (
    `${values.year}-` +
    `${values.month}-` +
    `${values.day}T` +
    `${values.hour}:` +
    `${values.minute}`
  )
}

function toTbilisiIso(
  value: string,
) {
  return `${value}:00+04:00`
}

function getRateMode(
  income: IncomeEntry,
): RateMode {
  if (
    income.exchange_rate_source ===
    'provided_gel_equivalent'
  ) {
    return 'ready_gel'
  }

  if (
    income.exchange_rate_source ===
      'NBG' ||
    income.exchange_rate_source ===
      'GEL' ||
    income.exchange_rate_source ===
      'SYSTEM'
  ) {
    return 'automatic'
  }

  return 'manual'
}

export function IncomeEditPage() {
  const { id } = useParams()

  const navigate = useNavigate()

  const [
    income,
    setIncome,
  ] = useState<IncomeEntry | null>(
    null,
  )

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

  const [loading, setLoading] =
    useState(true)

  const [saving, setSaving] =
    useState(false)

  const [
    previewLoading,
    setPreviewLoading,
  ] = useState(false)

  const [error, setError] =
    useState('')

  const [
    preview,
    setPreview,
  ] = useState<IncomePreview | null>(
    null,
  )

  const [
    receivedAt,
    setReceivedAt,
  ] = useState('')

  const [
    description,
    setDescription,
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
    amount,
    setAmount,
  ] = useState('')

  const [
    declarationCategory,
    setDeclarationCategory,
  ] = useState('')

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState(
    'bank_transfer',
  )

  const [
    documentNumber,
    setDocumentNumber,
  ] = useState('')

  const [
    documentDate,
    setDocumentDate,
  ] = useState('')

  const [
    comment,
    setComment,
  ] = useState('')

  const [
    rateMode,
    setRateMode,
  ] = useState<RateMode>(
    'automatic',
  )

  const [
    manualRate,
    setManualRate,
  ] = useState('')

  const [
    manualRateUnit,
    setManualRateUnit,
  ] = useState('1')

  const [
    manualSource,
    setManualSource,
  ] = useState('')

  const [
    readyAmountGel,
    setReadyAmountGel,
  ] = useState('')

  const [
    cryptoTxHash,
    setCryptoTxHash,
  ] = useState('')

  const selectedAccount =
    useMemo(
      () =>
        accounts.find(
          (account) =>
            account.id ===
            Number(accountId),
        ) ?? null,
      [
        accounts,
        accountId,
      ],
    )

  const selectedCurrency =
    useMemo(
      () =>
        currencies.find(
          (currency) =>
            currency.id ===
            Number(currencyId),
        ) ?? null,
      [
        currencies,
        currencyId,
      ],
    )

  const isCryptoWallet =
    selectedAccount?.type ===
    'crypto_wallet'

  const isCryptoCurrency =
    selectedCurrency?.kind ===
    'crypto'

  const availableCurrencies =
    useMemo(
      () =>
        currencies.filter(
          (currency) => {
            const isCurrent =
              currency.id ===
              Number(currencyId)

            if (
              !currency.is_active &&
              !isCurrent
            ) {
              return false
            }

            if (!isCryptoWallet) {
              return (
                currency.kind ===
                'fiat'
              )
            }

            if (
              currency.kind !==
              'crypto'
            ) {
              return false
            }

            const asset =
              selectedAccount
                ?.crypto_asset
                .trim()
                .toUpperCase()

            return (
              isCurrent ||
              !asset ||
              currency.code
                .toUpperCase() ===
                asset
            )
          },
        ),
      [
        currencies,
        currencyId,
        isCryptoWallet,
        selectedAccount,
      ],
    )

  const usesOriginalAccount =
    income !== null &&
    selectedAccount?.id ===
      income.financial_account

  const displayedCryptoAsset =
    usesOriginalAccount
      ? (
          income?.crypto_asset ||
          selectedAccount
            ?.crypto_asset ||
          selectedAccount
            ?.default_currency_code ||
          '—'
        )
      : (
          selectedAccount
            ?.crypto_asset ||
          selectedAccount
            ?.default_currency_code ||
          '—'
        )

  const displayedCryptoNetwork =
    usesOriginalAccount
      ? (
          income
            ?.crypto_network ||
          selectedAccount
            ?.crypto_network ||
          '—'
        )
      : (
          selectedAccount
            ?.crypto_network ||
          '—'
        )

  const displayedWalletAddress =
    usesOriginalAccount
      ? (
          income
            ?.crypto_wallet_address ||
          selectedAccount
            ?.wallet_address ||
          '—'
        )
      : (
          selectedAccount
            ?.wallet_address ||
          '—'
        )

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const incomeId =
          Number(id)

        if (!incomeId) {
          throw new Error(
            'Некорректный ID дохода',
          )
        }

        const [
          incomeResult,
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getIncomeRequest(
            incomeId,
          ),
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        if (cancelled) {
          return
        }

        setIncome(incomeResult)
        setAccounts(
          accountsResult,
        )
        setCurrencies(
          currenciesResult,
        )

        setReceivedAt(
          toTbilisiInput(
            incomeResult.received_at,
          ),
        )

        setDescription(
          incomeResult.description,
        )

        setAccountId(
          String(
            incomeResult
              .financial_account,
          ),
        )

        setCurrencyId(
          String(
            incomeResult
              .original_currency,
          ),
        )

        setAmount(
          incomeResult.original_amount,
        )

        setDeclarationCategory(
          incomeResult
            .declaration_category,
        )

        setPaymentMethod(
          incomeResult.payment_method ||
            'bank_transfer',
        )

        setDocumentNumber(
          incomeResult.document_number,
        )

        setDocumentDate(
          incomeResult.document_date ??
            '',
        )

        setComment(
          incomeResult.comment,
        )

        setCryptoTxHash(
          incomeResult
            .crypto_tx_hash ||
            '',
        )

        const mode =
          getRateMode(
            incomeResult,
          )

        setRateMode(mode)

        if (
          mode === 'manual'
        ) {
          setManualRate(
            incomeResult
              .exchange_rate_value,
          )

          setManualRateUnit(
            String(
              incomeResult
                .exchange_rate_unit,
            ),
          )

          setManualSource(
            incomeResult
              .exchange_rate_source,
          )
        }

        if (
          mode === 'ready_gel'
        ) {
          setReadyAmountGel(
            incomeResult.amount_gel,
          )
        }
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
  }, [id])

  function invalidatePreview() {
    setPreview(null)
  }

  function clearRateFields() {
    setManualRate('')
    setManualRateUnit('1')
    setManualSource('')
    setReadyAmountGel('')
  }

  function changeAccount(
    value: string,
  ) {
    const account =
      accounts.find(
        (item) =>
          item.id ===
          Number(value),
      )

    if (!account) {
      return
    }

    const currency =
      currencies.find(
        (item) =>
          item.id ===
          account.default_currency,
      )

    setAccountId(value)

    setCurrencyId(
      String(
        account.default_currency,
      ),
    )

    clearRateFields()

    if (
      account.type ===
      'crypto_wallet'
    ) {
      setRateMode('manual')
      setDeclarationCategory(
        'other_21',
      )
      setPaymentMethod(
        'crypto',
      )

      if (
        income &&
        account.id !==
          income.financial_account
      ) {
        setCryptoTxHash('')
      }
    } else {
      setRateMode(
        currency?.code ===
          'GEL'
          ? 'automatic'
          : 'automatic',
      )

      setDeclarationCategory(
        account
          .default_declaration_category ||
          'cashless_20',
      )

      setPaymentMethod(
        'bank_transfer',
      )

      setCryptoTxHash('')
    }

    invalidatePreview()
  }

  function changeCurrency(
    value: string,
  ) {
    const currency =
      currencies.find(
        (item) =>
          item.id ===
          Number(value),
      )

    if (!currency) {
      return
    }

    setCurrencyId(value)
    clearRateFields()

    if (
      currency.kind ===
      'crypto'
    ) {
      setRateMode('manual')
      setDeclarationCategory(
        'other_21',
      )
      setPaymentMethod(
        'crypto',
      )
    } else {
      setRateMode('automatic')
    }

    invalidatePreview()
  }

  function changeRateMode(
    value: RateMode,
  ) {
    setRateMode(value)
    clearRateFields()
    invalidatePreview()
  }

  function getRateFields() {
    if (
      !selectedCurrency ||
      selectedCurrency.code ===
        'GEL'
    ) {
      return {}
    }

    if (
      rateMode === 'manual'
    ) {
      return {
        manual_rate_value:
          manualRate,

        manual_rate_unit:
          isCryptoCurrency
            ? 1
            : Number(
                manualRateUnit,
              ),

        manual_source:
          manualSource.trim() ||
          'Ручной ввод',
      }
    }

    if (
      rateMode === 'ready_gel'
    ) {
      return {
        ready_amount_gel:
          readyAmountGel,
      }
    }

    return {}
  }

  function validateForm() {
    if (!accountId) {
      return (
        'Выберите финансовый счёт'
      )
    }

    if (!currencyId) {
      return 'Выберите валюту'
    }

    if (
      !amount ||
      Number(amount) <= 0
    ) {
      return (
        'Введите сумму больше нуля'
      )
    }

    if (!description.trim()) {
      return (
        'Введите описание дохода'
      )
    }

    if (isCryptoWallet) {
      if (
        !isCryptoCurrency
      ) {
        return (
          'Для криптокошелька выберите криптовалюту'
        )
      }

      if (
        declarationCategory !==
        'other_21'
      ) {
        return (
          'Криптовалютный доход должен относиться к графе 21'
        )
      }

      if (
        !cryptoTxHash.trim()
      ) {
        return (
          'Укажите hash криптотранзакции'
        )
      }

      if (
        rateMode ===
        'automatic'
      ) {
        return (
          'Для криптовалюты укажите курс или GEL-эквивалент'
        )
      }

      if (
        rateMode ===
          'manual' &&
        (
          !manualRate ||
          Number(
            manualRate,
          ) <= 0
        )
      ) {
        return (
          'Укажите курс криптовалюты'
        )
      }

      if (
        rateMode ===
          'manual' &&
        !manualSource.trim()
      ) {
        return (
          'Укажите источник оценки криптовалюты'
        )
      }

      if (
        rateMode ===
          'ready_gel' &&
        (
          !readyAmountGel ||
          Number(
            readyAmountGel,
          ) <= 0
        )
      ) {
        return (
          'Укажите GEL-эквивалент'
        )
      }
    }

    if (
      !isCryptoWallet &&
      isCryptoCurrency
    ) {
      return (
        'Для криптовалюты выберите криптокошелёк'
      )
    }

    if (
      !isCryptoCurrency &&
      selectedCurrency?.code !==
        'GEL' &&
      rateMode ===
        'manual'
    ) {
      if (
        !manualRate ||
        Number(
          manualRate,
        ) <= 0
      ) {
        return (
          'Введите ручной курс'
        )
      }

      if (
        Number(
          manualRateUnit,
        ) <= 0
      ) {
        return (
          'Количество единиц валюты должно быть больше нуля'
        )
      }
    }

    return ''
  }

  async function calculatePreview() {
    const validationError =
      validateForm()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    setError('')
    setPreviewLoading(true)

    try {
      const result =
        await previewIncomeRequest({
          received_at:
            toTbilisiIso(
              receivedAt,
            ),

          financial_account:
            Number(accountId),

          original_amount:
            amount,

          original_currency:
            Number(currencyId),

          declaration_category:
            declarationCategory,

          ...getRateFields(),
        })

      setPreview(result)
    } catch (
      requestError
    ) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      )
    } finally {
      setPreviewLoading(false)
    }
  }

  async function saveIncome(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (!income) {
      return
    }

    const validationError =
      validateForm()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    if (!preview) {
      setError(
        'Перед сохранением пересчитайте сумму в GEL',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      await updateIncomeRequest(
        income.id,
        {
          received_at:
            toTbilisiIso(
              receivedAt,
            ),

          description:
            description.trim(),

          financial_account:
            Number(accountId),

          payment_method:
            paymentMethod,

          document_number:
            documentNumber.trim(),

          document_date:
            documentDate || null,

          original_amount:
            amount,

          original_currency:
            Number(currencyId),

          declaration_category:
            declarationCategory,

          comment:
            comment.trim(),

          ...(isCryptoWallet
            ? {
                crypto_tx_hash:
                  cryptoTxHash.trim(),
              }
            : {
                crypto_tx_hash:
                  '',
              }),

          ...getRateFields(),
        },
      )

      navigate('/incomes')
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
      <main className="page">
        <div className="card">
          Загружаем доход...
        </div>
      </main>
    )
  }

  if (!income) {
    return (
      <main className="page">
        <div className="error-box">
          Доход не найден
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header">
        <p className="eyebrow">
          Доходы
        </p>

        <h1>
          Редактирование дохода
        </h1>

        <Link
          to="/incomes"
          className="text-button"
        >
          ← Вернуться к журналу
        </Link>
      </header>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      <section className="card">
        <form
          className="form-grid"
          onSubmit={saveIncome}
        >
          <DateTimeField
            value={receivedAt}
            onChange={(value) => {
              setReceivedAt(value)
              invalidatePreview()
            }}
          />

          <label>
            Финансовый счёт

            <select
              value={accountId}
              onChange={(event) =>
                changeAccount(
                  event.target.value,
                )
              }
              required
            >
              {accounts
                .filter(
                  (account) =>
                    account.is_active ||
                    account.id ===
                      income
                        .financial_account,
                )
                .map(
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

          {isCryptoWallet &&
            selectedAccount && (
              <div className="income-crypto-info wide">
                <div>
                  <span>
                    Криптовалюта
                  </span>

                  <strong>
                    {
                      displayedCryptoAsset
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Сеть
                  </span>

                  <strong>
                    {
                      displayedCryptoNetwork
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Адрес кошелька
                  </span>

                  <strong>
                    {
                      displayedWalletAddress
                    }
                  </strong>
                </div>
              </div>
          )}

          <label className="wide">
            Описание

            <input
              value={description}
              onChange={(event) =>
                setDescription(
                  event.target.value,
                )
              }
              required
            />
          </label>

          <label>
            Сумма

            <input
              type="number"
              min="0"
              step="any"
              value={amount}
              onChange={(event) => {
                setAmount(
                  event.target.value,
                )

                invalidatePreview()
              }}
              required
            />
          </label>

          <label>
            Валюта

            <select
              value={currencyId}
              onChange={(event) =>
                changeCurrency(
                  event.target.value,
                )
              }
              required
            >
              {availableCurrencies.map(
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
            </select>
          </label>

          {isCryptoWallet && (
            <label className="wide">
              Hash транзакции

              <input
                value={cryptoTxHash}
                onChange={(event) => {
                  setCryptoTxHash(
                    event.target.value,
                  )

                  invalidatePreview()
                }}
                placeholder="0x... или transaction hash"
                required
              />

              <small className="field-hint">
                Идентификатор операции
                в блокчейне
              </small>
            </label>
          )}

          {selectedCurrency &&
            selectedCurrency.code !==
              'GEL' && (
              <label>
                Способ определения курса

                <select
                  value={rateMode}
                  onChange={(event) =>
                    changeRateMode(
                      event.target
                        .value as RateMode,
                    )
                  }
                >
                  {selectedCurrency.kind ===
                    'fiat' && (
                    <option value="automatic">
                      Автоматически NBG
                    </option>
                  )}

                  <option value="manual">
                    Ввести курс вручную
                  </option>

                  {selectedCurrency.kind ===
                    'crypto' && (
                    <option value="ready_gel">
                      Указать готовый GEL-эквивалент
                    </option>
                  )}
                </select>
              </label>
          )}

          {rateMode === 'manual' &&
            selectedCurrency?.code !==
              'GEL' && (
              <>
                {isCryptoCurrency ? (
                  <label>
                    Курс 1{' '}
                    {
                      selectedCurrency.code
                    }{' '}
                    к GEL

                    <input
                      type="number"
                      min="0"
                      step="any"
                      value={manualRate}
                      onChange={(event) => {
                        setManualRate(
                          event.target.value,
                        )

                        invalidatePreview()
                      }}
                      required
                    />

                    <small className="field-hint">
                      Сколько GEL стоит
                      1{' '}
                      {
                        selectedCurrency.code
                      }
                    </small>
                  </label>
                ) : (
                  <>
                    <label>
                      Количество единиц

                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={
                          manualRateUnit
                        }
                        onChange={(event) => {
                          setManualRateUnit(
                            event.target.value,
                          )

                          invalidatePreview()
                        }}
                        required
                      />

                      <small className="field-hint">
                        Например: 1 USD
                        или 100 RUB
                      </small>
                    </label>

                    <label>
                      Курс к GEL

                      <input
                        type="number"
                        min="0"
                        step="any"
                        value={manualRate}
                        onChange={(event) => {
                          setManualRate(
                            event.target.value,
                          )

                          invalidatePreview()
                        }}
                        required
                      />
                    </label>
                  </>
                )}

                <label
                  className={
                    isCryptoCurrency
                      ? ''
                      : 'wide'
                  }
                >
                  {isCryptoCurrency
                    ? 'Источник оценки'
                    : 'Источник курса'}

                  <input
                    value={manualSource}
                    onChange={(event) => {
                      setManualSource(
                        event.target.value,
                      )

                      invalidatePreview()
                    }}
                    placeholder={
                      isCryptoCurrency
                        ? 'Например: Binance'
                        : 'Например: TBC Bank'
                    }
                    required={
                      isCryptoCurrency
                    }
                  />
                </label>
              </>
          )}

          {rateMode ===
            'ready_gel' && (
            <label>
              GEL-эквивалент

              <input
                type="number"
                min="0"
                step="any"
                value={readyAmountGel}
                onChange={(event) => {
                  setReadyAmountGel(
                    event.target.value,
                  )

                  invalidatePreview()
                }}
                required
              />

              <small className="field-hint">
                Итоговая стоимость
                операции в GEL
              </small>
            </label>
          )}

          <label>
            Способ оплаты

            <select
              value={paymentMethod}
              disabled={
                isCryptoWallet
              }
              onChange={(event) =>
                setPaymentMethod(
                  event.target.value,
                )
              }
            >
              <option value="bank_transfer">
                Банковский перевод
              </option>

              <option value="bank_card">
                Банковская карта
              </option>

              <option value="cash">
                Наличные
              </option>

              <option value="pos">
                POS-терминал
              </option>

              <option value="payment_system">
                Платёжная система
              </option>

              <option value="crypto">
                Криптовалюта
              </option>

              <option value="barter">
                Бартер
              </option>

              <option value="other">
                Другое
              </option>
            </select>
          </label>

          <label>
            Номер документа

            <input
              value={documentNumber}
              onChange={(event) =>
                setDocumentNumber(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Дата документа

            <input
              type="date"
              lang="ru"
              value={documentDate}
              onChange={(event) =>
                setDocumentDate(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Графа декларации

            <select
              value={
                declarationCategory
              }
              disabled={
                isCryptoWallet
              }
              onChange={(event) => {
                setDeclarationCategory(
                  event.target.value,
                )

                invalidatePreview()
              }}
            >
              {Object.entries(
                CATEGORY_LABELS,
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

            {isCryptoWallet && (
              <small className="field-hint">
                Криптовалютный доход
                относится к графе 21
              </small>
            )}
          </label>

          <label className="wide">
            Комментарий

            <input
              value={comment}
              onChange={(event) =>
                setComment(
                  event.target.value,
                )
              }
            />
          </label>

          <div className="income-preview wide">
            <div>
              <span className="muted">
                Сохранено сейчас
              </span>

              <strong>
                {income.amount_gel}{' '}
                GEL
              </strong>
            </div>

            <div>
              <span className="muted">
                Сохранённый курс
              </span>

              <strong>
                {
                  income
                    .exchange_rate_unit
                }{' '}
                {
                  selectedCurrency
                    ?.code ?? ''
                }
                {' = '}
                {
                  income
                    .exchange_rate_value
                }{' '}
                GEL
              </strong>
            </div>

            <div>
              <span className="muted">
                Источник
              </span>

              <strong>
                {
                  income
                    .exchange_rate_source
                }
              </strong>
            </div>
          </div>

          <div className="wide preview-actions">
            <button
              type="button"
              className="secondary"
              disabled={
                previewLoading
              }
              onClick={() => {
                void calculatePreview()
              }}
            >
              {previewLoading
                ? 'Считаем...'
                : 'Пересчитать в GEL'}
            </button>
          </div>

          {preview && (
            <div className="income-preview wide">
              <div>
                <span className="muted">
                  Курс
                </span>

                <strong>
                  {
                    preview.data
                      .rate_unit
                  }{' '}
                  {
                    preview.data
                      .currency
                  }
                  {' = '}
                  {
                    preview.data
                      .rate_value
                  }{' '}
                  GEL
                </strong>
              </div>

              <div>
                <span className="muted">
                  Сумма в GEL
                </span>

                <strong className="preview-gel">
                  {
                    preview.data
                      .amount_gel
                  }{' '}
                  GEL
                </strong>
              </div>

              <div>
                <span className="muted">
                  Источник
                </span>

                <strong>
                  {
                    preview.data
                      .source
                  }
                </strong>
              </div>

              <div>
                <span className="muted">
                  Графа
                </span>

                <strong>
                  {
                    CATEGORY_LABELS[
                      declarationCategory ||
                        preview.data
                          .declaration_category
                    ]
                  }
                </strong>
              </div>

              <div>
                <span className="muted">
                  Дата курса
                </span>

                <strong>
                  {
                    preview.data
                      .rate_date
                  }
                </strong>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={
              saving ||
              !preview
            }
          >
            {saving
              ? 'Сохраняем...'
              : 'Сохранить изменения'}
          </button>

          {!preview && (
            <small className="submit-hint">
              После изменения данных
              сначала пересчитайте сумму
              в GEL.
            </small>
          )}
        </form>
      </section>
    </main>
  )
}