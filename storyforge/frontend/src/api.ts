export type JsonRecord = Record<string, unknown>

export type DaemonStartPayload = {
  novel_id?: string | null
  title: string
  world_setting: string
  characters: string
  genre: string
  target_word_count: number
  quality_threshold?: number
  dissect_source_id?: string | null
  api_key?: string
  api_base_url?: string
  model?: string
  semi_auto?: boolean
}

export type TestLlmPayload = {
  api_key: string
  api_base_url: string
  model: string
}

export type CharacterSetting = {
  name: string
  role: string
  description: string
}

export type NovelSummary = {
  id: string
  title: string
  genre: string
  status: string
  raw_status?: string
  words: number
  word_count?: number
  target_word_count?: number
  updated_at: string
}

export type NovelDetail = NovelSummary & {
  author?: string
  summary?: string
  world_setting: string
  characters: CharacterSetting[]
  status_label?: string
  created_at?: string
  chapter_texts?: string[]
}

export type GeneratedSettings = {
  title: string
  world_setting: string
  characters: CharacterSetting[]
  genre: string
  target_word_count: number
}

export type DaemonState = {
  novel_id: string
  status: string
  current_phase: string
  progress: {
    total_chapters: number
    written_chapters: number
    total_words: number
    target_words: number
  }
  foreshadowing_ledger?: {
    new_hooks: unknown[]
    closed_hooks: unknown[]
    still_open: unknown[]
  }
  chapter_summaries?: string[]
  chapter_texts?: string[]
  baseline_texts?: string[]
  conflicts?: unknown[]
  errors?: string[]
  retry_count?: number
  max_retries?: number
  quality_threshold?: number
  manual_review?: JsonRecord
  runtime_memory?: JsonRecord
  runtime_state_deltas?: JsonRecord[]
  hook_health_records?: JsonRecord[]
  [key: string]: unknown
}

export type SseEvent = {
  type: string
  data?: JsonRecord
  state?: DaemonState
  receivedAt?: string
}

export const API_BASE_STORAGE_KEY = 'storyforge.backendApiBaseUrl'
export const LEGACY_API_BASE_STORAGE_KEY = 'storyforge.apiBaseUrl'
export const OLD_API_BASE_STORAGE_KEY = 'plotsys.backendApiBaseUrl'
export const DEFAULT_BACKEND_API_BASE = 'http://localhost:8000'

function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/$/, '')
}

function isLikelyLlmBaseUrl(value: string) {
  return /deepseek|openai|anthropic|moonshot|siliconflow|dashscope|volces/i.test(value)
}

export const getApiBase = () => {
  const stored = localStorage.getItem(API_BASE_STORAGE_KEY)
  if (stored) return normalizeBaseUrl(stored)

  const legacy = localStorage.getItem(LEGACY_API_BASE_STORAGE_KEY) || localStorage.getItem(OLD_API_BASE_STORAGE_KEY)
  if (legacy && !isLikelyLlmBaseUrl(legacy)) return normalizeBaseUrl(legacy)

  return normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || DEFAULT_BACKEND_API_BASE)
}

export const setApiBase = (value: string) => {
  localStorage.setItem(API_BASE_STORAGE_KEY, normalizeBaseUrl(value || DEFAULT_BACKEND_API_BASE))
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = getApiBase().replace(/\/$/, '')
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${text}`)
  }

  return response.json() as Promise<T>
}

const query = (params: Record<string, string | number | boolean | null | undefined>) => {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  })
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  listNovels: () => request<{ items: NovelSummary[] }>('/api/v1/novel/list'),
  getNovel: (id: string) => request<NovelDetail>(`/api/v1/novel/${encodeURIComponent(id)}`),
  createNovel: (data: GeneratedSettings) =>
    request<NovelDetail>('/api/v1/novel/create', { method: 'POST', body: JSON.stringify(data) }),
  updateNovel: (id: string, data: { target_word_count?: number }) =>
    request<NovelDetail>(`/api/v1/novel/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteNovel: (id: string) => request<{ status: string }>(`/api/v1/novel/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  generateSettings: (data: { logline: string; api_key?: string; api_base_url?: string; model?: string }) =>
    request<GeneratedSettings>('/api/v1/novel/generate-settings', { method: 'POST', body: JSON.stringify(data) }),
  cocreationTurn: (data: JsonRecord) => request<JsonRecord>('/api/v1/cocreation/turn', { method: 'POST', body: JSON.stringify(data) }),

  uploadNovel: (data: JsonRecord) => request<JsonRecord>('/api/v1/dissect/upload', { method: 'POST', body: JSON.stringify(data) }),
  firstPass: (id: string) => request<JsonRecord>(`/api/v1/dissect/${id}/first-pass`, { method: 'POST' }),
  secondPass: (id: string) => request<JsonRecord>(`/api/v1/dissect/${id}/second-pass`, { method: 'POST' }),
  thirdPass: (id: string) => request<JsonRecord>(`/api/v1/dissect/${id}/third-pass`, { method: 'POST' }),
  result: (id: string) => request<JsonRecord>(`/api/v1/dissect/${id}/result`),
  generateReplacement: (id: string, data: JsonRecord) =>
    request<JsonRecord>(`/api/v1/dissect/${id}/generate-replacement`, { method: 'POST', body: JSON.stringify(data) }),

  macroOutline: (data: JsonRecord) => request<JsonRecord>('/api/v1/planner/macro-outline', { method: 'POST', body: JSON.stringify(data) }),
  chapterOutline: (actIndex: number, data: JsonRecord) =>
    request<JsonRecord>(`/api/v1/planner/act/${actIndex}/chapter-outline`, { method: 'POST', body: JSON.stringify(data) }),
  generateNode: (data: JsonRecord) => request<JsonRecord>('/api/v1/writer/generate-node', { method: 'POST', body: JSON.stringify(data) }),
  writingSignals: (data: { text: string }) => request<JsonRecord>('/api/v1/analyst/writing-signals', { method: 'POST', body: JSON.stringify(data) }),

  startDaemon: (data: DaemonStartPayload) =>
    request<{ status: string; novel_id: string }>('/api/v1/daemon/start', { method: 'POST', body: JSON.stringify(data) }),
  daemonStatus: (novelId?: string) => request<DaemonState>(`/api/v1/daemon/status${query({ novel_id: novelId })}`),
  testLlm: (data: TestLlmPayload) =>
    request<{ status: string; message: string }>('/api/v1/daemon/test-llm', { method: 'POST', body: JSON.stringify(data) }),
  pauseDaemon: (novelId?: string) => request<{ status: string }>(`/api/v1/daemon/pause${query({ novel_id: novelId })}`, { method: 'POST' }),
  resumeDaemon: (novelId?: string) => request<{ status: string }>(`/api/v1/daemon/resume${query({ novel_id: novelId })}`, { method: 'POST' }),
  approveNode: (data: JsonRecord) => request<JsonRecord>('/api/v1/daemon/review/approve', { method: 'POST', body: JSON.stringify(data) }),
  rewriteNode: (data: JsonRecord) => request<JsonRecord>('/api/v1/daemon/review/rewrite', { method: 'POST', body: JSON.stringify(data) }),
  rollbackNode: (data: JsonRecord) => request<JsonRecord>('/api/v1/daemon/review/rollback', { method: 'POST', body: JSON.stringify(data) }),

  events: () => `${getApiBase().replace(/\/$/, '')}/api/v1/daemon/events`,
}
