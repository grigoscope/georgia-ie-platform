import { apiRequest } from './client'

export type EntrepreneurProfile = {
  profile_exists: boolean
  business_name: string
  entrepreneur_status: string
  tin: string
  legal_address: string
  email: string
  phone: string
  tax_rate: string
  accounting_start_date: string | null
  timezone: string
  language: string
  invoice_prefix: string
  next_invoice_number: number
  telegram_connected: boolean
  signature_url: string | null
  logo_url: string | null
}

export type ProfileInput = {
  business_name: string
  entrepreneur_status: string
  tin: string
  legal_address: string
  email: string
  phone: string
  tax_rate: string
  accounting_start_date: string | null
  timezone: string
  language: string
  invoice_prefix: string
}

export async function getProfileRequest() {
  return apiRequest<EntrepreneurProfile>(
    '/profile/',
  )
}

export async function updateProfileRequest(
  data: ProfileInput,
) {
  return apiRequest<EntrepreneurProfile>(
    '/profile/',
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
  )
}