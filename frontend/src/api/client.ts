const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  '/api/v1'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

type TokenPair = {
  access: string
  refresh?: string
}

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(
    status: number,
    data: unknown,
  ) {
    super(`API error: ${status}`)

    this.status = status
    this.data = data
  }
}

export function getAccessToken() {
  return localStorage.getItem(
    ACCESS_TOKEN_KEY,
  )
}

export function getRefreshToken() {
  return localStorage.getItem(
    REFRESH_TOKEN_KEY,
  )
}

export function setTokens(
  access: string,
  refresh?: string,
) {
  localStorage.setItem(
    ACCESS_TOKEN_KEY,
    access,
  )

  if (refresh) {
    localStorage.setItem(
      REFRESH_TOKEN_KEY,
      refresh,
    )
  }
}

export function clearTokens() {
  localStorage.removeItem(
    ACCESS_TOKEN_KEY,
  )

  localStorage.removeItem(
    REFRESH_TOKEN_KEY,
  )
}

async function refreshAccessToken() {
  const refresh = getRefreshToken()

  if (!refresh) {
    return false
  }

  const response = await fetch(
    `${API_BASE_URL}/auth/token/refresh/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh,
      }),
    },
  )

  if (!response.ok) {
    clearTokens()

    return false
  }

  const data =
    (await response.json()) as TokenPair

  setTokens(
    data.access,
    data.refresh,
  )

  return true
}

async function readResponse(
  response: Response,
): Promise<unknown> {
  if (response.status === 204) {
    return null
  }

  const contentType =
    response.headers.get(
      'content-type',
    )

  if (
    contentType?.includes(
      'application/json',
    )
  ) {
    return response.json()
  }

  return response.text()
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  useAuth = true,
  retry = true,
): Promise<T> {
  const headers = new Headers(
    options.headers,
  )

  const body = options.body

  if (
    body &&
    !(body instanceof FormData)
  ) {
    headers.set(
      'Content-Type',
      'application/json',
    )
  }

  if (useAuth) {
    const access = getAccessToken()

    if (access) {
      headers.set(
        'Authorization',
        `Bearer ${access}`,
      )
    }
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  )

  if (
    response.status === 401 &&
    useAuth &&
    retry
  ) {
    const refreshed =
      await refreshAccessToken()

    if (refreshed) {
      return apiRequest<T>(
        path,
        options,
        useAuth,
        false,
      )
    }
  }

  const data =
    await readResponse(response)

  if (!response.ok) {
    throw new ApiError(
      response.status,
      data,
    )
  }

  return data as T
}

export async function apiDownloadRequest(
  path: string,
  options: RequestInit = {},
  useAuth = true,
  retry = true,
): Promise<Blob> {
  const headers = new Headers(
    options.headers,
  )

  if (useAuth) {
    const access = getAccessToken()

    if (access) {
      headers.set(
        'Authorization',
        `Bearer ${access}`,
      )
    }
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  )

  if (
    response.status === 401 &&
    useAuth &&
    retry
  ) {
    const refreshed =
      await refreshAccessToken()

    if (refreshed) {
      return apiDownloadRequest(
        path,
        options,
        useAuth,
        false,
      )
    }
  }

  if (!response.ok) {
    const data =
      await readResponse(response)

    throw new ApiError(
      response.status,
      data,
    )
  }

  return response.blob()
}

export function getApiErrorMessage(
  error: unknown,
) {
  if (!(error instanceof ApiError)) {
    if (error instanceof Error) {
      return error.message
    }

    return 'Неизвестная ошибка'
  }

  if (
    typeof error.data === 'object' &&
    error.data !== null
  ) {
    const data = error.data as Record<
      string,
      unknown
    >

    const nestedError = data.error

    if (
      typeof nestedError === 'object' &&
      nestedError !== null
    ) {
      const errorObject =
        nestedError as Record<
          string,
          unknown
        >

      if (
        typeof errorObject.message ===
        'string'
      ) {
        return errorObject.message
      }
    }

    if (
      typeof data.detail === 'string'
    ) {
      return data.detail
    }
  }

  return `Ошибка сервера: ${error.status}`
}