import {
  apiDownloadRequest,
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

export type InvoicePaymentSummary = {
  total_amount: string
  paid_amount: string
  remaining_amount: string
  is_paid: boolean
}

export type InvoicePreview = {
  data: {
    invoice: Invoice
    payment_summary:
      InvoicePaymentSummary
  }
}

export type InvoiceItemInput = {
  description: string
  quantity: string
  unit: string
  unit_price: string
}

export type InvoiceCreateInput = {
  issue_date: string
  due_date: string | null
  service_period_start: string | null
  service_period_end: string | null
  currency: number
  language: string
  counterparty: number
  financial_account: number
  items: InvoiceItemInput[]
  discount_amount: string
  extra_charge_amount: string
  tax_note: string
  tax_reference_amount: string | null
  payment_purpose: string
  notes: string
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

export type InvoicePaymentInput = {
  received_at: string
  financial_account: number
  amount: string
  declaration_category?: string | null
  payment_method?: string
  manual_rate_value?: string | null
  manual_rate_unit?: number
  manual_source?: string
  ready_amount_gel?: string | null
  comment?: string
}

export type InvoicePaymentResult = {
  data: {
    invoice_id: number
    invoice_status: string
    income_id: number
    payment_id: number
    payment_amount: string
    paid_amount: string
    remaining_amount: string
    is_paid: boolean
  }
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

export async function previewInvoiceRequest(
  invoiceId: number,
) {
  return apiRequest<InvoicePreview>(
    `/invoices/${invoiceId}/preview/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export async function generateInvoicePdfRequest(
  invoiceId: number,
) {
  return apiRequest<Invoice>(
    `/invoices/${invoiceId}/generate-pdf/`,
    {
      method: 'POST',
      headers: {
        'Idempotency-Key':
          crypto.randomUUID(),
      },
      body: JSON.stringify({}),
    },
  )
}

export async function downloadInvoicePdfRequest(
  invoiceId: number,
) {
  return apiDownloadRequest(
    `/invoices/${invoiceId}/pdf/`,
  )
}

export async function markInvoiceSentRequest(
  invoiceId: number,
) {
  return apiRequest<Invoice>(
    `/invoices/${invoiceId}/mark-sent/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export async function cancelInvoiceRequest(
  invoiceId: number,
) {
  return apiRequest<Invoice>(
    `/invoices/${invoiceId}/cancel/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export async function createInvoiceRequest(
  data: InvoiceCreateInput,
) {
  return apiRequest<Invoice>(
    '/invoices/',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
  )
}

export async function createInvoiceIncomeRequest(
  invoiceId: number,
  data: InvoicePaymentInput,
) {
  return apiRequest<InvoicePaymentResult>(
    `/invoices/${invoiceId}/create-income/`,
    {
      method: 'POST',
      headers: {
        'Idempotency-Key':
          crypto.randomUUID(),
      },
      body: JSON.stringify(data),
    },
  )
}