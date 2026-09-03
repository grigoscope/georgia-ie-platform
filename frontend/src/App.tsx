import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import {
  ProtectedRoute,
} from './auth/ProtectedRoute'

import {
  SetupGate,
} from './auth/SetupGate'

import {
  AppLayout,
} from './components/AppLayout'

import {
  DashboardPage,
} from './pages/DashboardPage'

import {
  IncomesPage,
} from './pages/IncomesPage'

import {
  LoginPage,
} from './pages/LoginPage'

import {
  OnboardingPage,
} from './pages/OnboardingPage'

import {
  RegisterPage,
} from './pages/RegisterPage'

import {
  SettingsPage,
} from './pages/SettingsPage'

import {
  IncomeEditPage,
} from './pages/IncomeEditPage'

import {
  InvoicesPage,
} from './pages/InvoicesPage'

import {
  InvoiceDetailPage,
} from './pages/InvoiceDetailPage'

import {
  InvoiceCreatePage,
} from './pages/InvoiceCreatePage'

import {
  TaxesPage,
} from './pages/TaxesPage'

import {
  TaxPeriodDetailPage,
} from './pages/TaxPeriodDetailPage'

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/register"
        element={<RegisterPage />}
      />

      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <DashboardPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/incomes"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <IncomesPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/incomes/:id/edit"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <IncomeEditPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/invoices"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <InvoicesPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/invoices/new"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <InvoiceCreatePage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/invoices/:id"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <InvoiceDetailPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/taxes"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <TaxesPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/taxes/:id"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <TaxPeriodDetailPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SetupGate>
              <AppLayout>
                <SettingsPage />
              </AppLayout>
            </SetupGate>
          </ProtectedRoute>
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />
    </Routes>
  )
}

export default App