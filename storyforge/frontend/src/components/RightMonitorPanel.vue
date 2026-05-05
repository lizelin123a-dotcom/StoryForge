<script setup lang="ts">
import type { DaemonState, SseEvent } from '../api'
import type { RightTab, WritingAnalysis } from '../types'

defineProps<{
  collapsed: boolean
  tabs: RightTab[]
  activeTab: RightTab
  wordPercent: number
  chapterPercent: number
  progress: DaemonState['progress']
  targetWordCount: number
  daemonState: DaemonState
  pendingNode: Record<string, unknown> | null
  pendingNodeTitle: string
  reviewEditContent: string
  reviewInstructions: string
  generationLogic: string[]
  latestEvents: SseEvent[]
  writingAnalysis: WritingAnalysis | null
  analysisLoading: boolean
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:activeTab': [value: RightTab]
  'update:reviewEditContent': [value: string]
  'update:reviewInstructions': [value: string]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
  analyzeCurrentText: []
}>()
</script>

<template>
  <aside class="border-l border-[#2a2a2a] bg-[#141414] transition-all duration-150" :class="collapsed ? 'w-12' : 'w-[360px]'">
    <button v-if="collapsed" class="h-full w-12 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="emit('update:collapsed', false)">‹</button>
    <div v-else class="h-full overflow-y-auto p-4">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-base font-semibold text-white">监控面板</h2>
        <button class="rounded-lg border border-[#2a2a2a] px-2 text-zinc-500 hover:text-white" @click="emit('update:collapsed', true)">›</button>
      </div>
      <div class="mb-3 flex gap-1 overflow-x-auto rounded-xl bg-[#0f0f0f] p-1 text-xs">
        <button v-for="tab in tabs" :key="tab" class="shrink-0 rounded-lg px-3 py-1.5" :class="activeTab === tab ? 'bg-indigo-500 text-white' : 'text-zinc-500 hover:text-zinc-200'" @click="emit('update:activeTab', tab)">{{ tab }}</button>
      </div>

      <div v-if="activeTab === '检测'" class="space-y-3">
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4">
          <div class="mb-2 flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-white">当前文本教学检测</div>
              <p class="mt-1 text-xs text-zinc-500">检测情绪、钩子、矛盾、爽点、信息差、代入感和角色行动。</p>
            </div>
            <button class="rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-medium text-white" :disabled="analysisLoading" @click="emit('analyzeCurrentText')">{{ analysisLoading ? '检测中' : '检测' }}</button>
          </div>
          <p class="text-sm leading-7 text-zinc-300">{{ writingAnalysis?.summary || '点击检测，或编辑正文后查看当前段落信号。' }}</p>
        </div>
        <div v-if="writingAnalysis" class="space-y-3">
          <div v-for="signal in writingAnalysis.signals" :key="signal.name" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-3">
            <div class="mb-2 flex justify-between text-sm"><span class="font-medium text-zinc-200">{{ signal.name }}</span><span class="text-zinc-500">{{ signal.status }} · {{ signal.score }}</span></div>
            <div class="h-1.5 rounded-full bg-zinc-800"><div class="h-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-blue-400" :style="{ width: Math.min(100, signal.score) + '%' }"></div></div>
            <p class="mt-2 text-xs text-zinc-500">命中：{{ signal.hits?.join('、') || '暂无明显关键词' }}</p>
          </div>
          <div class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
            <div class="mb-2 text-sm font-medium text-amber-200">修改建议</div>
            <ul class="space-y-2 text-sm leading-7 text-amber-100/90"><li v-for="item in writingAnalysis.suggestions" :key="item">• {{ item }}</li></ul>
          </div>
          <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4">
            <div class="mb-2 text-sm font-medium text-white">关联教学资料</div>
            <div v-for="item in writingAnalysis.guidance" :key="item.path" class="mb-3 text-xs leading-6 text-zinc-400"><span class="text-zinc-200">{{ item.title }}</span>：{{ item.content.slice(0, 180) }}...</div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === '监控'" class="space-y-3">
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 shadow-lg shadow-black/20"><div class="mb-2 flex justify-between text-xs text-zinc-500"><span>进度</span><span>{{ wordPercent }}%</span></div><div class="h-2 rounded-full bg-zinc-800"><div class="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-blue-400" :style="{ width: wordPercent + '%' }"></div></div><div class="mt-3 grid grid-cols-2 gap-2 text-sm text-zinc-300"><span>{{ progress.total_words }}/{{ progress.target_words || targetWordCount }} 字</span><span>{{ progress.written_chapters }}/{{ progress.total_chapters }} 章 · {{ chapterPercent }}%</span></div></div>
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4"><div class="mb-2 text-sm font-medium text-white">伏笔台账</div><p class="text-sm text-zinc-400">待回收 {{ daemonState.foreshadowing_ledger?.still_open?.length || 0 }} / 已回收 {{ daemonState.foreshadowing_ledger?.closed_hooks?.length || 0 }}</p></div>
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4"><div class="mb-2 text-sm font-medium text-white">错误</div><p class="text-sm text-zinc-400">{{ daemonState.errors?.join('；') || '暂无错误' }}</p></div>
      </div>

      <div v-else-if="activeTab === '审阅'" class="space-y-3">
        <div v-if="pendingNode" class="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm leading-7 text-amber-100">
          <div class="mb-2 font-medium">正在审阅：{{ pendingNodeTitle }}</div>
          <p class="text-xs text-zinc-400">审阅内容已合并到中间右侧的“节点草稿 / 审阅”。这里仅保留状态提醒，避免重复编辑框。</p>
        </div>
        <div v-else class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm text-zinc-400">当前没有待审阅节点。</div>
      </div>

      <div v-else-if="activeTab === '生成逻辑'" class="space-y-3"><div v-for="(item, index) in generationLogic" :key="index" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm leading-7 text-zinc-300">{{ item }}</div><p v-if="!generationLogic.length" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm text-zinc-500">等待节点生成逻辑。</p></div>
      <div v-else class="space-y-2"><div v-for="event in latestEvents" :key="event.receivedAt + event.type" class="rounded-lg bg-[#0f0f0f] p-2 text-xs text-zinc-500"><span class="text-zinc-300">{{ event.type }}</span> · {{ event.receivedAt }}</div><p v-if="!latestEvents.length" class="text-xs text-zinc-500">等待 SSE 事件。</p></div>
    </div>
  </aside>
</template>
