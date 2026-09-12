import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  createIncomeRequest,
  previewIncomeRequest,
  type IncomePreview,
} from '../api/incomes'

import {
  getAccountsRequest,
  getCurrenciesRequest,
  type Currency,
  type FinancialAccount,
} from '../api/finances'

import {
  getApiErrorMessage,
} from '../api/client'

type Props = {
  onSaved: () => Promise<void>
}

type RateMode =
  | 'automatic'
  | 'manual'
  | 'ready_gel'

const CATEGORIES = [
  {
    value: 'cash_register_18',
    label: '18 — Кассовый аппарат',
  },
  {
    value: 'physical_pos_19',
    label: '19 — POS-терминал',
  },
  {
    value: 'cashless_20',
    label: '20 — Безналичный доход',
  },
  {
    value: 'other_21',
    label:
      '21 — Прочие доходы и криптовалюта',
  },
]

function getTbilisiDateTime() {
  const parts =
    new Intl.DateTimeFormat(
      'en-CA',
      {
        timeZone:
          'Asia/Tbilisi',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
      },
    ).formatToParts(
      new Date(),
    )

  function value(
    type: string,
  ) {
    return (
      parts.find(
        (part) =>
          part.type === type,
      )?.value ?? ''
    )
  }

  return (
    `${value('year')}-` +
    `${value('month')}-` +
    `${value('day')}T` +
    `${value('hour')}:` +
    `${value('minute')}`
  )
}

export function MiniIncomeForm({
  onSaved,
}: Props) {
  const [
    open,
    setOpen,
  ] = useState(false)

  const [
    accounts,
    setAccounts,
  ] = useState<
    FinancialAccount[]
  >([])

  const [
    currencies,
    setCurrencies,
  ] = useState<Currency[]>(
    [],
  )

  const [
    loadingSettings,
    setLoadingSettings,
  ] = useState(false)

  const [
    description,
    setDescription,
  ] = useState('')

  const [
    receivedAt,
    setReceivedAt,
  ] = useState(
    getTbilisiDateTime(),
  )

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
    category,
    setCategory,
  ] = useState(
    'cashless_20',
  )

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState(
    'bank_transfer',
  )

  const [
    cryptoTxHash,
    setCryptoTxHash,
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
    preview,
    setPreview,
  ] = useState<
    IncomePreview['data'] | null
  >(null)

  const [
    previewing,
    setPreviewing,
  ] = useState(false)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState('')

  const activeAccounts =
    useMemo(
      () =>
        accounts.filter(
          (account) =>
            account.is_active,
        ),
      [accounts],
    )

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
    currencies.filter(
      (currency) => {
        if (!currency.is_active) {
          return false
        }

        if (!isCryptoWallet) {
          return (
            currency.kind !==
            'crypto'
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
          !asset ||
          currency.code
            .toUpperCase() ===
            asset
        )
      },
    )

  useEffect(() => {
    if (
      !open ||
      accounts.length > 0
    ) {
      return
    }

    async function loadSettings() {
      setLoadingSettings(true)
      setError('')

      try {
        const [
          accountsResult,
          currenciesResult,
        ] = await Promise.all([
          getAccountsRequest(),
          getCurrenciesRequest(),
        ])

        setAccounts(
          accountsResult,
        )

        setCurrencies(
          currenciesResult,
        )

        const available =
          accountsResult.filter(
            (account) =>
              account.is_active,
          )

        const preferred =
          available.find(
            (account) =>
              account.is_default,
          ) ??
          available[0]

        if (preferred) {
          applyAccount(
            preferred,
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
        setLoadingSettings(
          false,
        )
      }
    }

    void loadSettings()
  }, [
    open,
    accounts.length,
  ])

  function clearRateFields() {
    setManualRate('')
    setManualRateUnit('1')
    setManualSource('')
    setReadyAmountGel('')
  }

  function applyAccount(
    account:
      FinancialAccount,
  ) {
    setAccountId(
      String(account.id),
    )

    setCurrencyId(
      String(
        account.default_currency,
      ),
    )

    setCryptoTxHash('')
    clearRateFields()
    setPreview(null)

    if (
      account.type ===
      'crypto_wallet'
    ) {
      setCategory(
        'other_21',
      )

      setPaymentMethod(
        'crypto',
      )

      setRateMode(
        'manual',
      )

      return
    }

    setCategory(
      account
        .default_declaration_category ||
        'cashless_20',
    )

    setPaymentMethod(
      'bank_transfer',
    )

    setRateMode(
      'automatic',
    )
  }

  function changeAccount(
    newAccountId: string,
  ) {
    const account =
      accounts.find(
        (item) =>
          item.id ===
          Number(
            newAccountId,
          ),
      )

    if (!account) {
      setAccountId('')
      setCurrencyId('')
      setPreview(null)

      return
    }

    applyAccount(account)
  }

  function changeCurrency(
    newCurrencyId: string,
  ) {
    setCurrencyId(
      newCurrencyId,
    )

    setPreview(null)
    clearRateFields()

    const currency =
      currencies.find(
        (item) =>
          item.id ===
          Number(
            newCurrencyId,
          ),
      )

    if (!currency) {
      return
    }

    if (
      currency.kind ===
      'crypto'
    ) {
      setRateMode(
        'manual',
      )

      setCategory(
        'other_21',
      )

      setPaymentMethod(
        'crypto',
      )

      return
    }

    setRateMode(
      'automatic',
    )
  }

  function changeRateMode(
    newMode: RateMode,
  ) {
    setRateMode(
      newMode,
    )

    clearRateFields()
    setPreview(null)
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
      rateMode ===
      'ready_gel'
    ) {
      return {
        ready_amount_gel:
          readyAmountGel,
      }
    }

    if (
      rateMode ===
      'manual'
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
          'manual',
      }
    }

    return {}
  }

  function validate() {
    if (!description.trim()) {
      return (
        'Введите описание дохода'
      )
    }

    if (!accountId) {
      return 'Выберите счёт'
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

    if (!receivedAt) {
      return (
        'Укажите дату дохода'
      )
    }

    if (
      isCryptoWallet
    ) {
      if (
        !isCryptoCurrency
      ) {
        return (
          'Для криптокошелька выберите криптовалюту'
        )
      }

      if (
        category !==
        'other_21'
      ) {
        return (
          'Криптовалюта должна относиться к графе 21'
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
        'manual'
      ) {
        if (
          !manualRate ||
          Number(
            manualRate,
          ) <= 0
        ) {
          return (
            'Введите курс криптовалюты'
          )
        }

        if (
          Number(
            manualRateUnit,
          ) <= 0
        ) {
          return (
            'Количество единиц должно быть больше нуля'
          )
        }

        if (
          !manualSource.trim()
        ) {
          return (
            'Укажите источник оценки криптовалюты'
          )
        }
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
    }

    return ''
  }

  async function calculate() {
    const validationError =
      validate()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    setPreviewing(true)
    setError('')
    setPreview(null)

    try {
      const result =
        await previewIncomeRequest(
          {
            received_at:
              `${receivedAt}:00+04:00`,

            financial_account:
              Number(accountId),

            original_amount:
              amount,

            original_currency:
              Number(currencyId),

            declaration_category:
              category,

            ...getRateFields(),
          },
        )

      setPreview(
        result.data,
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
      setPreviewing(false)
    }
  }

  async function saveIncome() {
    const validationError =
      validate()

    if (validationError) {
      setError(
        validationError,
      )

      return
    }

    if (!preview) {
      setError(
        'Сначала рассчитайте сумму в GEL',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      await createIncomeRequest(
        {
          received_at:
            `${receivedAt}:00+04:00`,

          description:
            description.trim(),

          additional_info: '',

          financial_account:
            Number(accountId),

          payment_method:
            paymentMethod,

          document_number: '',

          document_date: null,

          original_amount:
            amount,

          original_currency:
            Number(currencyId),

          declaration_category:
            category,

          vat_amount: '0.00',

          comment: '',

          ...(isCryptoWallet
            ? {
                crypto_tx_hash:
                  cryptoTxHash.trim(),
              }
            : {}),

          ...getRateFields(),
        },
      )

      setDescription('')
      setAmount('')
      setCryptoTxHash('')
      clearRateFields()
      setPreview(null)

      setReceivedAt(
        getTbilisiDateTime(),
      )

      const preferred =
        activeAccounts.find(
          (account) =>
            account.is_default,
        ) ??
        activeAccounts[0]

      if (preferred) {
        applyAccount(
          preferred,
        )
      }

      setOpen(false)

      await onSaved()
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

  return (
    <div className="mini-income-create">
      <button
        type="button"
        className="mini-income-toggle"
        onClick={() => {
          setOpen(
            (current) =>
              !current,
          )

          setError('')
        }}
      >
        {open
          ? 'Закрыть форму'
          : '+ Добавить доход'}
      </button>

      {open && (
        <div className="mini-income-form">
          <div>
            <h3>
              Новый доход
            </h3>

            <p className="muted">
              Обычный или
              криптовалютный доход
            </p>
          </div>

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

          {loadingSettings ? (
            <div className="mini-empty">
              Загружаем счета...
            </div>
          ) : (
            <>
              <label>
                Описание

                <input
                  type="text"
                  value={
                    description
                  }
                  placeholder="Например: Оплата за разработку"
                  onChange={(
                    event,
                  ) => {
                    setDescription(
                      event.target
                        .value,
                    )

                    setPreview(
                      null,
                    )
                  }}
                />
              </label>

              <label>
                Дата и время

                <input
                  type="datetime-local"
                  value={
                    receivedAt
                  }
                  onChange={(
                    event,
                  ) => {
                    setReceivedAt(
                      event.target
                        .value,
                    )

                    setPreview(
                      null,
                    )
                  }}
                />
              </label>

              <label>
                Счёт

                <select
                  value={
                    accountId
                  }
                  onChange={(
                    event,
                  ) =>
                    changeAccount(
                      event.target
                        .value,
                    )
                  }
                >
                  <option value="">
                    Выберите счёт
                  </option>

                  {activeAccounts.map(
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

              {activeAccounts.length ===
                0 && (
                <div className="mini-tax-alert mini-tax-alert-warning">
                  Нет активных
                  финансовых
                  счетов.
                </div>
              )}

              {isCryptoWallet &&
                selectedAccount && (
                <div className="mini-crypto-account">
                  <div className="mini-crypto-account-header">
                    <strong>
                      Криптокошелёк
                    </strong>

                    <span className="mini-crypto-badge">
                      {
                        selectedAccount
                          .crypto_asset ||
                        selectedAccount
                          .default_currency_code
                      }
                    </span>
                  </div>

                  <div className="mini-crypto-details">
                    <div>
                      <span>
                        Сеть
                      </span>

                      <strong>
                        {selectedAccount
                          .crypto_network ||
                          '—'}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Адрес
                      </span>

                      <strong>
                        {selectedAccount
                          .wallet_address ||
                          '—'}
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              <div className="mini-income-money-row">
                <label>
                  Сумма

                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={
                      amount
                    }
                    onChange={(
                      event,
                    ) => {
                      setAmount(
                        event.target
                          .value,
                      )

                      setPreview(
                        null,
                      )
                    }}
                    placeholder="0"
                  />
                </label>

                <label>
                  Валюта

                  <select
                    value={
                      currencyId
                    }
                    onChange={(
                      event,
                    ) =>
                      changeCurrency(
                        event.target
                          .value,
                      )
                    }
                  >
                    <option value="">
                      —
                    </option>

                    {availableCurrencies.map(
                      (
                        currency,
                      ) => (
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
              </div>

              {isCryptoWallet && (
                <label>
                  Hash транзакции

                  <input
                    type="text"
                    value={
                      cryptoTxHash
                    }
                    placeholder="0x... или transaction hash"
                    onChange={(
                      event,
                    ) => {
                      setCryptoTxHash(
                        event.target
                          .value,
                      )

                      setPreview(
                        null,
                      )
                    }}
                  />

                  <small className="field-hint">
                    Идентификатор
                    операции в
                    блокчейне
                  </small>
                </label>
              )}

              {selectedCurrency &&
                selectedCurrency.code !==
                  'GEL' && (
                  <label>
                    Способ оценки

                    <select
                      value={
                        rateMode
                      }
                      onChange={(
                        event,
                      ) =>
                        changeRateMode(
                          event.target
                            .value as
                            RateMode,
                        )
                      }
                    >
                      {!isCryptoCurrency && (
                        <option value="automatic">
                          Автоматически
                          по NBG
                        </option>
                      )}

                      <option value="manual">
                        Ввести курс
                        вручную
                      </option>

                      {isCryptoCurrency && (
                        <option value="ready_gel">
                          Указать
                          готовый GEL
                        </option>
                      )}
                    </select>
                  </label>
                )}

              {selectedCurrency &&
                selectedCurrency.code !==
                  'GEL' &&
                rateMode ===
                  'manual' && (
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
                          value={
                            manualRate
                          }
                          onChange={(
                            event,
                          ) => {
                            setManualRate(
                              event.target
                                .value,
                            )

                            setPreview(
                              null,
                            )
                          }}
                          placeholder="Например: 2.70"
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
                      <div className="mini-income-money-row">
                        <label>
                          Единиц валюты

                          <input
                            type="number"
                            min="1"
                            step="1"
                            value={
                              manualRateUnit
                            }
                            onChange={(
                              event,
                            ) => {
                              setManualRateUnit(
                                event.target
                                  .value,
                              )

                              setPreview(
                                null,
                              )
                            }}
                          />

                          <small className="field-hint">
                            Например 1 USD
                            или 100 RUB
                          </small>
                        </label>

                        <label>
                          Курс к GEL

                          <input
                            type="number"
                            min="0"
                            step="any"
                            value={
                              manualRate
                            }
                            onChange={(
                              event,
                            ) => {
                              setManualRate(
                                event.target
                                  .value,
                              )

                              setPreview(
                                null,
                              )
                            }}
                            placeholder="0"
                          />
                        </label>
                      </div>
                    )}

                    <label>
                      {isCryptoCurrency
                        ? 'Источник оценки'
                        : 'Источник курса'}

                      <input
                        type="text"
                        value={
                          manualSource
                        }
                        onChange={(
                          event,
                        ) => {
                          setManualSource(
                            event.target
                              .value,
                          )

                          setPreview(
                            null,
                          )
                        }}
                        placeholder={
                          isCryptoCurrency
                            ? 'Например: Binance'
                            : 'Например: TBC Bank'
                        }
                      />
                    </label>
                  </>
              )}

              {isCryptoCurrency &&
                rateMode ===
                  'ready_gel' && (
                  <label>
                    GEL-эквивалент

                    <input
                      type="number"
                      min="0"
                      step="any"
                      value={
                        readyAmountGel
                      }
                      onChange={(
                        event,
                      ) => {
                        setReadyAmountGel(
                          event.target
                            .value,
                        )

                        setPreview(
                          null,
                        )
                      }}
                      placeholder="0.00"
                    />

                    <small className="field-hint">
                      Готовая стоимость
                      всей операции
                      в GEL
                    </small>
                  </label>
                )}

              <label>
                Категория декларации

                <select
                  value={
                    category
                  }
                  disabled={
                    isCryptoWallet
                  }
                  onChange={(
                    event,
                  ) => {
                    setCategory(
                      event.target
                        .value,
                    )

                    setPreview(
                      null,
                    )
                  }}
                >
                  {CATEGORIES.map(
                    (item) => (
                      <option
                        key={
                          item.value
                        }
                        value={
                          item.value
                        }
                      >
                        {
                          item.label
                        }
                      </option>
                    ),
                  )}
                </select>

                {isCryptoWallet && (
                  <small className="field-hint">
                    Для криптовалюты
                    используется
                    графа 21
                  </small>
                )}
              </label>

              <label>
                Способ оплаты

                <select
                  value={
                    paymentMethod
                  }
                  disabled={
                    isCryptoWallet
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

                  <option value="bank_card">
                    Банковская
                    карта
                  </option>

                  <option value="cash">
                    Наличные
                  </option>

                  <option value="payment_system">
                    Платёжная
                    система
                  </option>

                  <option value="crypto">
                    Криптовалюта
                  </option>

                  <option value="other">
                    Другое
                  </option>
                </select>
              </label>

              <button
                type="button"
                className="secondary"
                disabled={
                  previewing ||
                  saving
                }
                onClick={() => {
                  void calculate()
                }}
              >
                {previewing
                  ? 'Считаем...'
                  : 'Рассчитать в GEL'}
              </button>

              {preview && (
                <div className="mini-income-preview">
                  <span>
                    Получится
                  </span>

                  <strong>
                    {
                      preview.amount_gel
                    }{' '}
                    GEL
                  </strong>

                  <small>
                    Курс:{' '}
                    {
                      preview.rate_value
                    }{' '}
                    за{' '}
                    {
                      preview.rate_unit
                    }{' '}
                    {
                      preview.currency
                    }
                  </small>

                  <small>
                    Источник:{' '}
                    {
                      preview.source
                    }
                  </small>

                  <small>
                    Графа:{' '}
                    {
                      preview
                        .declaration_category
                    }
                  </small>

                  {preview.warnings.map(
                    (
                      warning,
                      index,
                    ) => (
                      <small
                        key={
                          `${warning}-${index}`
                        }
                        className="mini-income-warning"
                      >
                        {warning}
                      </small>
                    ),
                  )}
                </div>
              )}

              <button
                type="button"
                disabled={
                  saving ||
                  !preview
                }
                onClick={() => {
                  void saveIncome()
                }}
              >
                {saving
                  ? 'Сохраняем...'
                  : 'Сохранить доход'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}