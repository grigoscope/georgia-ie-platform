import {
  NavLink,
} from 'react-router-dom'

import {
  useAuth,
} from '../auth/AuthContext'

type AppLayoutProps = {
  children: React.ReactNode
}

export function AppLayout({
  children,
}: AppLayoutProps) {
  const {
    user,
    logout,
  } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">
            Georgia IE
          </p>

          <h2 className="brand">
            Accounting
          </h2>
        </div>

        <nav className="main-nav">
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive
                ? 'nav-link active'
                : 'nav-link'
            }
          >
            Dashboard
          </NavLink>

          <span className="nav-link disabled">
            Доходы
          </span>

          <span className="nav-link disabled">
            Инвойсы
          </span>

          <span className="nav-link disabled">
            Налоги
          </span>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
                isActive
                ? 'nav-link active'
                : 'nav-link'
            }
            >
            Настройки
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-email">
            {user?.email}
          </p>

          <button
            className="secondary full-width"
            type="button"
            onClick={() => {
              void logout()
            }}
          >
            Выйти
          </button>
        </div>
      </aside>

      <div className="app-content">
        {children}
      </div>
    </div>
  )
}