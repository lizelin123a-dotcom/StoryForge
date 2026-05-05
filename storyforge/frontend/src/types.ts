export type RouteName = 'bookcase' | 'edit' | 'dissect' | 'config' | 'about'
export type StepState = '待执行' | '执行中' | '已完成' | '失败'
export type Chapter = { title: string; content: string; nodeLabel: string; nodesDone: number; nodesTotal: number }
export type RightTab = '检测' | '监控' | '审阅' | '生成逻辑' | '事件'

export type WritingSignal = { name: string; score: number; hits: string[]; status: string }
export type WritingAnalysis = {
  signals: WritingSignal[]
  summary: string
  suggestions: string[]
  guidance: { title: string; category?: string; path: string; content: string }[]
  word_count?: number
}

export type CocreationMessage = { role: 'user' | 'assistant'; content: string }
export type CocreationTurn = {
  reply: string
  asset_patch: Record<string, string>
  next_focus: string
  ready_for_writing: boolean
  fields: { name: string; description: string }[]
}
