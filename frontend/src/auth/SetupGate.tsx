import {
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  Navigate,
} from 'react-router-dom'

import {
  getAccountsRequest,
} from '../api/finances'

import {
  getProfileRequest,
} from '../api/profile'

type SetupGateProps = {
  children: ReactNode
}

export function SetupGate({
  children,
}: SetupGateProps) {
  const [loading, setLoading] =
    useState(true)

  const [ready, setReady] =
    useState(false)

  useEffect(() => {
    let cancelled = false

    async function checkSetup() {
      try {
        const [
          profile,
          accounts,
        ] = await Promise.all([
          getProfileRequest(),
          getAccountsRequest(),
        ])

        if (!cancelled) {
          setReady(
            profile.profile_exists &&
                accounts.some(
                    (account) =>
                    account.is_active,
            )
          )
        }
      } catch {
        if (!cancelled) {
          setReady(false)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void checkSetup()

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <main className="center-page">
        <div className="card">
          Проверяем настройки...
        </div>
      </main>
    )
  }

  if (!ready) {
    return (
      <Navigate
        to="/onboarding"
        replace
      />
    )
  }

  return children
}