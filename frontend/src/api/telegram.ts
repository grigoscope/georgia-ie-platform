import {
  apiRequest,
  setTokens,
} from './client'

export type TelegramConnection = {
  telegram_user_id: number
  telegram_chat_id: number | null
  username: string
  first_name: string
  last_name: string
  language_code: string
  is_active: boolean
  linked_at: string
}

type TelegramConnectionResponse = {
  data: TelegramConnection
}

type TelegramAuthResponse = {
  access: string
  refresh: string
}

export async function linkTelegramRequest(
  initData: string,
) {
  return apiRequest<TelegramConnectionResponse>(
    '/telegram/link/',
    {
      method: 'POST',
      body: JSON.stringify({
        init_data: initData,
      }),
    },
  )
}

export async function unlinkTelegramRequest() {
  return apiRequest<void>(
    '/telegram/link/',
    {
      method: 'DELETE',
    },
  )
}

export async function telegramMiniAppAuthRequest(
  initData: string,
) {
  const result =
    await apiRequest<TelegramAuthResponse>(
      '/telegram/mini-app/auth/',
      {
        method: 'POST',
        body: JSON.stringify({
          init_data: initData,
        }),
      },
      false,
    )

  setTokens(
    result.access,
    result.refresh,
  )

  return result
}