import {
  apiRequest,
  clearTokens,
  getRefreshToken,
  setTokens,
} from './client'

export type User = {
  id: number
  email: string
  date_joined: string
}

type LoginResponse = {
  access: string
  refresh: string
}

type RegisterData = {
  email: string
  password: string
  password_confirm: string
}

export async function loginRequest(
  email: string,
  password: string,
) {
  const data =
    await apiRequest<LoginResponse>(
      '/auth/login/',
      {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
        }),
      },
      false,
    )

  setTokens(
    data.access,
    data.refresh,
  )

  return data
}

export async function registerRequest(
  data: RegisterData,
) {
  return apiRequest<User>(
    '/auth/register/',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    false,
  )
}

export async function getMeRequest() {
  return apiRequest<User>(
    '/auth/me/',
  )
}

export async function logoutRequest() {
  const refresh = getRefreshToken()

  try {
    if (refresh) {
      await apiRequest(
        '/auth/logout/',
        {
          method: 'POST',
          body: JSON.stringify({
            refresh,
          }),
        },
      )
    }
  } finally {
    clearTokens()
  }
}