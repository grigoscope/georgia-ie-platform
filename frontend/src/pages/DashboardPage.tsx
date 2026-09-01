import {
  useEffect,
  useState,
} from 'react'

import {
  apiRequest,
  getApiErrorMessage,
} from '../api/client'

import { useAuth } from '../auth/AuthContext'

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
  const {
    user,
    logout,
  } = useAuth()

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
        Загрузка dashboard...
      </main>
    )
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">
            Georgia IE
          </p>

          <h1>Dashboard</h1>

          <p className="muted">
            {user?.email}
          </p>
        </div>

        <button
          className="secondary"
          type="button"
          onClick={() => {
            void logout()
          }}
        >
          Выйти
        </button>
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
                {data.current_month
                  .total_gel}{' '}
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
                {data.current_year
                  .total_gel}{' '}
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
            <h2>
              Последние доходы
            </h2>

            {data.recent_incomes
              .length === 0 ? (
              <p className="muted">
                Доходов пока нет
              </p>
            ) : (
              <div className="income-list">
                {data.recent_incomes.map(
                  (income) => (
                    <div
                      key={income.id}
                      className="income-row"
                    >
                      <span>
                        {
                          income.description
                        }
                      </span>

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