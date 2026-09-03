import {
  apiRequest,
} from './client'

export type InvoiceItem = {
  id: number
  position: number
  description: string
  quantity: string
  unit: string
  unit_price: string
  line_total: string
}

export type InvoicePayment = {
  id: number
  income_entry_id: number
  amount: string
  currency: number
  currency_code: string
  paid_at: string
  created_at: string
}

export type Invoice = {
  id: number
  number: string
  issue_date: string
  service_period_start:
    | string
    | null
  service_period_end:
    | string
    | null
  due_date: string | null
  currency: number
  language: string
  status: string
  counterparty: number
  invoice_items: InvoiceItem[]
  payments: InvoicePayment[]
  seller_snapshot:
    Record<string, unknown>
  buyer_snapshot:
    Record<string, unknown>
  payment_details_snapshot:
    Record<string, unknown>
  subtotal: string
  discount_amount: string
  extra_charge_amount: string
  total_amount: string
  tax_note: string
  tax_reference_amount:
    | string
    | null
  payment_purpose: string
  notes: string
  pdf_file: string | null
  pdf_checksum: string
  generated_at: string | null
  sent_at: string | null
  paid_at: string | null
  cancelled_at: string | null
  created_at: string
  updated_at: string
}

export type PaginatedInvoices = {
  count: number
  next: string | null
  previous: string | null
  results: Invoice[]
}

export type InvoiceFilters = {
  page?: number
  page_size?: number
  status?: string
  date_from?: string
  date_to?: string
  counterparty?: number
  currency?: number
  overdue?: boolean
  search?: string
  ordering?:
    | 'issue_date'
    | '-issue_date'
    | 'due_date'
    | '-due_date'
    | 'total_amount'
    | '-total_amount'
    | 'number'
    | '-number'
}

function buildInvoiceQuery(
  filters: InvoiceFilters,
) {
  const params =
    new URLSearchParams()

  Object.entries(filters).forEach(
    ([key, value]) => {
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

export async function getInvoicesRequest(
  filters: InvoiceFilters = {},
) {
  const query =
    buildInvoiceQuery(filters)

  return apiRequest<PaginatedInvoices>(
    query
      ? `/invoices/?${query}`
      : '/invoices/',
  )
}

export async function getInvoiceRequest(
  invoiceId: number,
) {
  return apiRequest<Invoice>(
    `/invoices/${invoiceId}/`,
  )
}

export async function deleteInvoiceRequest(
  invoiceId: number,
) {
  return apiRequest<void>(
    `/invoices/${invoiceId}/`,
    {
      method: 'DELETE',
    },
  )
}