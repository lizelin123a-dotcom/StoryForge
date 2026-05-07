export type RouteName = 'bookcase' | 'edit' | 'new-book' | 'dissect' | 'config' | 'about'
export type StepState = '待执行' | '执行中' | '已完成' | '失败'
export type Chapter = { title: string; content: string; nodeLabel: string; nodesDone: number; nodesTotal: number; dirty?: boolean }
export type NodeDraft = { id: string; chapter_index: number; node_index: number; node_type: string; content: string; locked: boolean; source: string; status?: string; appended_to_chapter?: boolean; target_words?: number; actual_words?: number; updated_at?: string }
export type RightTab = '检测' | '监控' | '审阅' | '生成逻辑' | '事件'
export type WritingCard = { chapter_index: number; node_index: number; nodes_total: number; completed_nodes: number[]; status: string; chapter_title: string; next_step: string }

export type WritingSignal = { name: string; score: number; hits: string[]; status: string }
export type WritingAnalysis = {
  signals: WritingSignal[]
  summary: string
  suggestions: string[]
  guidance: { title: string; category?: string; path: string; content: string }[]
  word_count?: number
}

export type CocreationMessage = { role: 'user' | 'assistant'; content: string }
export type EditorSkill = { id: string; title: string; description: string }
export type EditPatch = { target: 'node' | 'chapter' | 'none'; mode: 'replace' | 'append' | 'none'; content: string; reason?: string; lock_node?: boolean }
export type CocreationTurn = {
  reply: string
  asset_patch: Record<string, string>
  edit_patch?: EditPatch
  next_focus: string
  ready_for_writing: boolean
  fields: { name: string; description: string }[]
}
