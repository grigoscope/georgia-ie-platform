import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  getMeRequest,
  loginRequest,
  logoutRequest,
  registerRequest,
  type User,
} from '../api/auth'

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
} from '../api/client'

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (
    email: string,
    password: string,
  ) => Promise<void>
  register: (
    email: string,
    password: string,
    passwordConfirm: string,
  ) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext =
  createContext<AuthContextValue | null>(
    null,
  )

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] =
    useState<User | null>(null)

  const [loading, setLoading] =
    useState(true)

  useEffect(() => {
    async function loadUser() {
      const hasToken =
        getAccessToken() ||
        getRefreshToken()

      if (!hasToken) {
        setLoading(false)

        return
      }

      try {
        const currentUser =
          await getMeRequest()

        setUser(currentUser)
      } catch {
        clearTokens()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    void loadUser()
  }, [])

  async function login(
    email: string,
    password: string,
  ) {
    await loginRequest(
      email,
      password,
    )

    const currentUser =
      await getMeRequest()

    setUser(currentUser)
  }

  async function register(
    email: string,
    password: string,
    passwordConfirm: string,
  ) {
    await registerRequest({
      email,
      password,
      password_confirm:
        passwordConfirm,
    })

    await login(
      email,
      password,
    )
  }

  async function logout() {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context =
    useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth must be used inside AuthProvider',
    )
  }

  return context
}