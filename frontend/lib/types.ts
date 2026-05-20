export interface User {
  id: number
  email: string
  name: string | null
  role: string
  created_at: string
  deleted_at: string | null
}

export interface StatsOverview {
  total_sessions: number
  total_messages: number
  avg_latency_ms: number
  p95_latency_ms: number
  total_cost_eur: number
  avg_messages_per_session: number
  cost_per_message: number
}

export interface DailyPoint {
  date: string
  count: number
}

export interface HeatmapPoint {
  day: number
  hour: number
  count: number
}

export interface ApiUsageRow {
  model: string
  prompt_tokens: number
  completion_tokens: number
  cost_eur: number
  avg_latency_ms: number
}

export interface TopSourceRow {
  source: string
  hit_count: number
}
