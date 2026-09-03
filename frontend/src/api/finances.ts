import { apiRequest } from './client'

export type Currency = {
  id: number
  code: string
  name: string
  kind: string
  decimal_places: number
  is_active: boolean
}

export type FinancialAccount = {
  id: number
  name: string
  type: string
  default_currency: number
  default_currency_code: string
  provider_name: string
  account_holder: string
  iban: string
  swift_bic: string
  account_identifier: string
  crypto_asset: string
  crypto_network: string
  wallet_address: string
  memo_tag: string
  default_declaration_category: string
  payment_instructions: string
  is_default: boolean
  use_in_invoices: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export type Counterparty = {
  id: number
  name: string
  type: string
  country: string
  tax_id: string
  address: string
  email: string
  phone: string
  comment: string
  created_at: string
  updated_at: string
}

export type PaginatedCounterparties = {
  count: number
  next: string | null
  previous: string | null
  results: Counterparty[]
}

export type FinancialAccountInput = {
  name: string
  type: string
  default_currency: number
  provider_name: string
  account_holder: string
  iban: string
  swift_bic: string
  account_identifier: string
  crypto_asset: string
  crypto_network: string
  wallet_address: string
  memo_tag: string
  default_declaration_category: string
  payment_instructions: string
  use_in_invoices: boolean
  is_active: boolean
}

export async function getCurrenciesRequest() {
  return apiRequest<Currency[]>(
    '/currencies/',
  )
}

export async function getAccountsRequest() {
  return apiRequest<FinancialAccount[]>(
    '/accounts/',
  )
}

export async function createAccountRequest(
  data: FinancialAccountInput,
) {
  return apiRequest<FinancialAccount>(
    '/accounts/',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
  )
}

export async function updateAccountRequest(
  accountId: number,
  data: Partial<FinancialAccountInput>,
) {
  return apiRequest<FinancialAccount>(
    `/accounts/${accountId}/`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
  )
}

export async function setDefaultAccountRequest(
  accountId: number,
) {
  return apiRequest<FinancialAccount>(
    `/accounts/${accountId}/set-default/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export async function getCounterpartiesRequest() {
  return apiRequest<PaginatedCounterparties>(
    '/counterparties/?page_size=100',
  )
}