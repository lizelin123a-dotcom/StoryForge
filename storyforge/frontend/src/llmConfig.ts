export const LLM_CONFIG_STORAGE_KEY = 'storyforge.llmConfig'

export type LlmConfig = {
  provider_alias: string
  api_base_url: string
  api_key: string
  models: string[]
  active_model: string
}

export const defaultLlmConfig = (): LlmConfig => ({
  provider_alias: 'DeepSeek',
  api_base_url: 'https://api.deepseek.com/v1',
  api_key: '',
  models: ['deepseek-chat'],
  active_model: 'deepseek-chat',
})

export function normalizeOpenAiBaseUrl(value: string) {
  return (value || defaultLlmConfig().api_base_url).trim().replace(/\/$/, '')
}

export function loadLlmConfig(): LlmConfig {
  const legacy = {
    api_key: localStorage.getItem('storyforge.apiKey') || localStorage.getItem('plotsys.apiKey') || '',
    api_base_url: localStorage.getItem('storyforge.llmApiBaseUrl') || localStorage.getItem('plotsys.llmApiBaseUrl') || '',
    active_model: localStorage.getItem('storyforge.model') || localStorage.getItem('plotsys.model') || '',
  }

  try {
    const raw = localStorage.getItem(LLM_CONFIG_STORAGE_KEY) || localStorage.getItem('plotsys.llmConfig')
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<LlmConfig>
      const models = Array.isArray(parsed.models) && parsed.models.length ? parsed.models.map(String) : [String(parsed.active_model || legacy.active_model || 'deepseek-chat')]
      const active = String(parsed.active_model || models[0] || legacy.active_model || 'deepseek-chat')
      return {
        provider_alias: String(parsed.provider_alias || 'OpenAI Compatible'),
        api_base_url: normalizeOpenAiBaseUrl(String(parsed.api_base_url || legacy.api_base_url || 'https://api.deepseek.com/v1')),
        api_key: String(parsed.api_key || legacy.api_key || ''),
        models: models.includes(active) ? models : [active, ...models],
        active_model: active,
      }
    }
  } catch {
    localStorage.removeItem(LLM_CONFIG_STORAGE_KEY)
  }

  const fallback = defaultLlmConfig()
  return {
    ...fallback,
    api_key: legacy.api_key,
    api_base_url: normalizeOpenAiBaseUrl(legacy.api_base_url || fallback.api_base_url),
    models: legacy.active_model ? [legacy.active_model] : fallback.models,
    active_model: legacy.active_model || fallback.active_model,
  }
}

export function saveLlmConfigLocal(config: LlmConfig) {
  const normalized = normalizeLlmConfig(config)
  localStorage.setItem(LLM_CONFIG_STORAGE_KEY, JSON.stringify(normalized, null, 2))
  localStorage.setItem('storyforge.apiKey', normalized.api_key)
  localStorage.setItem('storyforge.llmApiBaseUrl', normalized.api_base_url)
  localStorage.setItem('storyforge.model', normalized.active_model)
  return normalized
}

export function normalizeLlmConfig(config: LlmConfig): LlmConfig {
  const active = (config.active_model || config.models[0] || 'deepseek-chat').trim()
  const models = Array.from(new Set([active, ...config.models.map((model) => model.trim()).filter(Boolean)]))
  return {
    provider_alias: (config.provider_alias || 'OpenAI Compatible').trim(),
    api_base_url: normalizeOpenAiBaseUrl(config.api_base_url),
    api_key: config.api_key.trim(),
    models,
    active_model: active,
  }
}

export function toTestPayload(config: LlmConfig) {
  const normalized = normalizeLlmConfig(config)
  return {
    api_key: normalized.api_key,
    api_base_url: normalized.api_base_url,
    model: normalized.active_model,
  }
}
