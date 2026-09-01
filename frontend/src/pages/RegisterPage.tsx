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

export function RegisterPage() {
  const {
    register,
    user,
  } = useAuth()

  const navigate = useNavigate()

  const [email, setEmail] =
    useState('')

  const [password, setPassword] =
    useState('')

  const [
    passwordConfirm,
    setPasswordConfirm,
  ] = useState('')

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

    if (
      password !==
      passwordConfirm
    ) {
      setError(
        'Пароли не совпадают',
      )

      return
    }

    setLoading(true)
    setError('')

    try {
      await register(
        email,
        password,
        passwordConfirm,
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

          <h1>Регистрация</h1>

          <p className="muted">
            Создайте аккаунт
            предпринимателя
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

        <label>
          Повторите пароль

          <input
            type="password"
            value={passwordConfirm}
            onChange={(event) =>
              setPasswordConfirm(
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
            ? 'Создаём...'
            : 'Создать аккаунт'}
        </button>

        <p className="muted">
          Уже есть аккаунт?{' '}
          <Link to="/login">
            Войти
          </Link>
        </p>
      </form>
    </main>
  )
}