import {
  apiRequest,
} from './client'

export type TaxPeriod = {
  id: number
  year: number
  month: number

  field_15: string
  field_17: string
  field_18: string
  field_19: string
  field_20: string
  field_21: string

  tax_rate: string
  field_26: string

  calculation_status: string

  declaration_status: string

  submitted_at: string | null
  submission_comment: string
  submission_confirmation:
    string | null

  payment_status: string

  paid_at: string | null
  paid_amount: string
  payment_comment: string
  payment_confirmation:
    string | null

  deadline: string
  is_overdue: boolean

  changed_after_submission:
    boolean

  calculated_at:
    string | null

  created_at: string
  updated_at: string
}

export type TaxPeriodFilters = {
  year?: number
  month?: number
  declaration_status?: string
  payment_status?: string
  is_overdue?: boolean
}

function buildTaxQuery(
  filters: TaxPeriodFilters,
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

export async function getTaxPeriodsRequest(
  filters: TaxPeriodFilters = {},
) {
  const query =
    buildTaxQuery(filters)

  return apiRequest<TaxPeriod[]>(
    query
      ? `/tax-periods/?${query}`
      : '/tax-periods/',
  )
}

export async function generateTaxPeriodRequest(
  year: number,
  month: number,
) {
  return apiRequest<TaxPeriod>(
    '/tax-periods/generate/',
    {
      method: 'POST',
      body: JSON.stringify({
        year,
        month,
      }),
    },
  )
}

export async function recalculateTaxPeriodRequest(
  periodId: number,
) {
  return apiRequest<TaxPeriod>(
    `/tax-periods/${periodId}/recalculate/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export type MarkTaxSubmittedInput = {
  comment?: string
  confirmation_file?: File | null
}

export type MarkTaxPaidInput = {
  paid_amount: string
  comment?: string
  confirmation_file?: File | null
}

export async function getTaxPeriodRequest(
  periodId: number,
) {
  return apiRequest<TaxPeriod>(
    `/tax-periods/${periodId}/`,
  )
}

export async function markTaxSubmittedRequest(
  periodId: number,
  data: MarkTaxSubmittedInput,
) {
  const formData =
    new FormData()

  if (data.comment) {
    formData.append(
      'comment',
      data.comment,
    )
  }

  if (data.confirmation_file) {
    formData.append(
      'confirmation_file',
      data.confirmation_file,
    )
  }

  return apiRequest<TaxPeriod>(
    `/tax-periods/${periodId}/mark-submitted/`,
    {
      method: 'POST',
      body: formData,
    },
  )
}

export async function unmarkTaxSubmittedRequest(
  periodId: number,
) {
  return apiRequest<TaxPeriod>(
    `/tax-periods/${periodId}/unmark-submitted/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export async function markTaxPaidRequest(
  periodId: number,
  data: MarkTaxPaidInput,
) {
  const formData =
    new FormData()

  formData.append(
    'paid_amount',
    data.paid_amount,
  )

  if (data.comment) {
    formData.append(
      'comment',
      data.comment,
    )
  }

  if (data.confirmation_file) {
    formData.append(
      'confirmation_file',
      data.confirmation_file,
    )
  }

  return apiRequest<TaxPeriod>(
    `/tax-periods/${periodId}/mark-paid/`,
    {
      method: 'POST',
      body: formData,
    },
  )
}

export async function unmarkTaxPaidRequest(
  periodId: number,
) {
  return apiRequest<TaxPeriod>(
    `/tax-periods/${periodId}/unmark-paid/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}