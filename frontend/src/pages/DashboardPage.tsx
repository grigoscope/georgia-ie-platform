import {
  useEffect,
  useState,
} from 'react'

import {
  apiRequest,
  getApiErrorMessage,
} from '../api/client'

type DashboardData = {
  current_month: {
    year: number
    month: number
    total_gel: string
    count: number
  }
  current_year: {
    year: number
    total_gel: string
    count: number
  }
  recent_incomes: {
    id: number
    description: string
    amount_gel: string
    currency: string
    original_amount: string
  }[]
}

export function DashboardPage() {
  const [data, setData] =
    useState<DashboardData | null>(
      null,
    )

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')

  useEffect(() => {
    let cancelled = false

    async function loadDashboard() {
      try {
        const result =
          await apiRequest<DashboardData>(
            '/reports/dashboard/',
          )

        if (!cancelled) {
          setData(result)
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

    void loadDashboard()

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <main className="page">
        <div className="card">
          Загружаем dashboard...
        </div>
      </main>
    )
  }

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Обзор
          </p>

          <h1>Dashboard</h1>

          <p className="muted">
            Основные показатели
            вашего бизнеса
          </p>
        </div>
      </header>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {data && (
        <>
          <section className="stats">
            <article className="card">
              <p className="muted">
                Этот месяц
              </p>

              <strong className="money">
                {
                  data.current_month
                    .total_gel
                }{' '}
                GEL
              </strong>

              <p>
                Доходов:{' '}
                {
                  data.current_month
                    .count
                }
              </p>
            </article>

            <article className="card">
              <p className="muted">
                Этот год
              </p>

              <strong className="money">
                {
                  data.current_year
                    .total_gel
                }{' '}
                GEL
              </strong>

              <p>
                Доходов:{' '}
                {
                  data.current_year
                    .count
                }
              </p>
            </article>
          </section>

          <section className="card">
            <div className="section-heading">
              <div>
                <h2>
                  Последние доходы
                </h2>

                <p className="muted">
                  Последние операции
                  журнала
                </p>
              </div>
            </div>

            {data.recent_incomes
              .length === 0 ? (
              <div className="empty-state">
                <h3>
                  Доходов пока нет
                </h3>

                <p className="muted">
                  Следующим шагом
                  подключим форму
                  добавления дохода.
                </p>
              </div>
            ) : (
              <div className="income-list">
                {data.recent_incomes.map(
                  (income) => (
                    <div
                      key={income.id}
                      className="income-row"
                    >
                      <div>
                        <strong>
                          {
                            income.description
                          }
                        </strong>

                        <p className="muted">
                          {
                            income.original_amount
                          }{' '}
                          {
                            income.currency
                          }
                        </p>
                      </div>

                      <strong>
                        {
                          income.amount_gel
                        }{' '}
                        GEL
                      </strong>
                    </div>
                  ),
                )}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}