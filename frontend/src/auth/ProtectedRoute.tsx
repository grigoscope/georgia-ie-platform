import {
  Navigate,
} from 'react-router-dom'

import { useAuth } from './AuthContext'

type ProtectedRouteProps = {
  children: React.ReactNode
}

export function ProtectedRoute({
  children,
}: ProtectedRouteProps) {
  const {
    user,
    loading,
  } = useAuth()

  if (loading) {
    return (
      <main className="center-page">
        <div className="card">
          Загрузка...
        </div>
      </main>
    )
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    )
  }

  return children
}