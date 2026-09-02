import {
  apiDownloadRequest,
  apiRequest,
} from './client'

export type IncomeEntry = {
  id: number
  received_at: string
  description: string
  additional_info: string
  counterparty: number | null
  financial_account: number
  payment_method: string
  document_number: string
  document_date: string | null
  invoice: number | null
  original_amount: string
  original_currency: number
  exchange_rate_value: string
  exchange_rate_unit: number
  exchange_rate_source: string
  exchange_rate_date: string
  exchange_rate_time: string | null
  amount_gel: string
  declaration_category: string
  vat_amount: string
  comment: string
  attachment: string | null
  created_at: string
  updated_at: string
}

export type PaginatedIncomes = {
  count: number
  next: string | null
  previous: string | null
  results: IncomeEntry[]
}

export type IncomePreviewInput = {
  received_at: string
  financial_account: number
  original_amount: string
  original_currency: number
  declaration_category?: string
  manual_rate_value?: string
  manual_rate_unit?: number
  manual_source?: string
  ready_amount_gel?: string
}

export type IncomePreview = {
  data: {
    original_amount: string
    currency: string
    rate_value: string
    rate_unit: number
    rate_date: string
    source: string
    amount_gel: string
    is_manual: boolean
    warnings: string[]
    suggested_category: string
    declaration_category: string
  }
}

export type IncomeCreateInput = {
  received_at: string
  description: string
  additional_info: string
  financial_account: number
  payment_method: string
  document_number: string
  document_date: string | null
  original_amount: string
  original_currency: number
  declaration_category: string
  vat_amount: string
  comment: string
  manual_rate_value?: string
  manual_rate_unit?: number
  manual_source?: string
  ready_amount_gel?: string
}

export type IncomeFilters = {
  page?: number
  page_size?: number
  search?: string
  date_from?: string
  date_to?: string
  account?: number
  currency?: number
  declaration_category?: string
  ordering?:
    | 'received_at'
    | '-received_at'
    | 'amount_gel'
    | '-amount_gel'
    | 'original_amount'
    | '-original_amount'
}

function buildIncomeQuery(
  filters: IncomeFilters,
  includePagination = true,
) {
  const params =
    new URLSearchParams()

  Object.entries(filters).forEach(
    ([key, value]) => {
      if (
        !includePagination &&
        (
          key === 'page' ||
          key === 'page_size'
        )
      ) {
        return
      }

      if (
        value !== undefined &&
        value !== null &&
        value !== ''
      ) {
        params.set(
          key,
          String(value),
        )
      }
    },
  )

  return params.toString()
}

export async function getIncomesRequest(
  filters: IncomeFilters = {},
) {
  const query =
    buildIncomeQuery(filters)

  return apiRequest<PaginatedIncomes>(
    query
      ? `/incomes/?${query}`
      : '/incomes/',
  )
}

export async function previewIncomeRequest(
  data: IncomePreviewInput,
) {
  return apiRequest<IncomePreview>(
    '/incomes/preview/',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
  )
}

export async function createIncomeRequest(
  data: IncomeCreateInput,
) {
  const idempotencyKey =
    crypto.randomUUID()

  return apiRequest<IncomeEntry>(
    '/incomes/',
    {
      method: 'POST',
      headers: {
        'Idempotency-Key':
          idempotencyKey,
      },
      body: JSON.stringify(data),
    },
  )
}

export type IncomeUpdateInput = {
  received_at?: string
  description?: string
  financial_account?: number
  payment_method?: string
  document_number?: string
  document_date?: string | null
  original_amount?: string
  original_currency?: number
  declaration_category?: string
  comment?: string
  manual_rate_value?: string
  manual_rate_unit?: number
  manual_source?: string
  ready_amount_gel?: string
}

export async function getIncomeRequest(
  incomeId: number,
) {
  return apiRequest<IncomeEntry>(
    `/incomes/${incomeId}/`,
  )
}

export async function updateIncomeRequest(
  incomeId: number,
  data: IncomeUpdateInput,
) {
  return apiRequest<IncomeEntry>(
    `/incomes/${incomeId}/`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
  )
}

export async function deleteIncomeRequest(
  incomeId: number,
) {
  return apiRequest<void>(
    `/incomes/${incomeId}/`,
    {
      method: 'DELETE',
    },
  )
}

export type IncomeExportFormat =
  | 'csv'
  | 'xlsx'

export async function exportIncomesRequest(
  format: IncomeExportFormat,
  filters: IncomeFilters = {},
) {
  const query =
    buildIncomeQuery(
      filters,
      false,
    )

  const path =
    `/incomes/export.${format}` +
    (
      query
        ? `?${query}`
        : ''
    )

  return apiDownloadRequest(path)
}