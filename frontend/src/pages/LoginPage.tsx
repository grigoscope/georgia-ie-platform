import {
  useState,
  type FormEvent,
} from 'react'

import {
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom'

import {
  getApiErrorMessage,
} from '../api/client'

import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const {
    login,
    user,
  } = useAuth()

  const navigate = useNavigate()

  const [email, setEmail] =
    useState('')

  const [password, setPassword] =
    useState('')

  const [error, setError] =
    useState('')

  const [loading, setLoading] =
    useState(false)

  if (user) {
    return (
      <Navigate
        to="/"
        replace
      />
    )
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setError('')
    setLoading(true)

    try {
      await login(
        email,
        password,
      )

      navigate('/')
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

  return (
    <main className="center-page">
      <form
        className="card auth-card"
        onSubmit={handleSubmit}
      >
        <div>
          <p className="eyebrow">
            Georgia IE
          </p>

          <h1>Вход</h1>

          <p className="muted">
            Учёт доходов, налогов
            и инвойсов
          </p>
        </div>

        <label>
          Email

          <input
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value,
              )
            }
            required
          />
        </label>

        <label>
          Пароль

          <input
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value,
              )
            }
            required
          />
        </label>

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
        >
          {loading
            ? 'Входим...'
            : 'Войти'}
        </button>

        <p className="muted">
          Нет аккаунта?{' '}
          <Link to="/register">
            Зарегистрироваться
          </Link>
        </p>
      </form>
    </main>
  )
}