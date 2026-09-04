import {
  apiRequest,
} from './client'

export type DashboardData = {
  current_month: {
    year: number
    month: number
    total_gel: string
    count: number
  }

  current_year: {
    year: number
    total_gel: string
    count: number
  }

  recent_incomes: {
    id: number
    description: string
    amount_gel: string
    currency: string
    original_amount: string
  }[]
}

export async function getDashboardRequest() {
  return apiRequest<DashboardData>(
    '/reports/dashboard/',
  )
}