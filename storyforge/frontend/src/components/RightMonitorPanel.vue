<script setup lang="ts">
import type { DaemonState, SseEvent } from '../api'
import type { RightTab } from '../types'

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
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:activeTab': [value: RightTab]
  'update:reviewEditContent': [value: string]
  'update:reviewInstructions': [value: string]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
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
      <div class="mb-3 grid grid-cols-4 gap-1 rounded-xl bg-[#0f0f0f] p-1 text-xs">
        <button v-for="tab in tabs" :key="tab" class="rounded-lg px-2 py-1.5" :class="activeTab === tab ? 'bg-indigo-500 text-white' : 'text-zinc-500 hover:text-zinc-200'" @click="emit('update:activeTab', tab)">{{ tab }}</button>
      </div>

      <div v-if="activeTab === '监控'" class="space-y-3">
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 shadow-lg shadow-black/20">
          <div class="mb-2 flex justify-between text-xs text-zinc-500"><span>进度</span><span>{{ wordPercent }}%</span></div>
          <div class="h-2 rounded-full bg-zinc-800"><div class="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-blue-400" :style="{ width: wordPercent + '%' }"></div></div>
          <div class="mt-3 grid grid-cols-2 gap-2 text-sm text-zinc-300"><span>{{ progress.total_words }}/{{ progress.target_words || targetWordCount }} 字</span><span>{{ progress.written_chapters }}/{{ progress.total_chapters }} 章 · {{ chapterPercent }}%</span></div>
        </div>
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4"><div class="mb-2 text-sm font-medium text-white">伏笔台账</div><p class="text-sm text-zinc-400">待回收 {{ daemonState.foreshadowing_ledger?.still_open?.length || 0 }} / 已回收 {{ daemonState.foreshadowing_ledger?.closed_hooks?.length || 0 }}</p></div>
        <div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4"><div class="mb-2 text-sm font-medium text-white">错误</div><p class="text-sm text-zinc-400">{{ daemonState.errors?.join('；') || '暂无错误' }}</p></div>
      </div>

      <div v-else-if="activeTab === '审阅'" class="space-y-3">
        <div v-if="pendingNode" class="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4">
          <div class="mb-2 text-sm font-medium text-amber-200">半自动审阅：{{ pendingNodeTitle }}</div>
          <textarea :value="reviewEditContent" rows="10" class="mt-3 w-full rounded-xl border border-amber-500/30 bg-[#0f0f0f] p-3 text-sm leading-7 text-zinc-200" @input="emit('update:reviewEditContent', ($event.target as HTMLTextAreaElement).value)" />
          <textarea :value="reviewInstructions" rows="3" placeholder="给后续内容或重写使用的修改意见" class="mt-2 w-full rounded-xl border border-amber-500/30 bg-[#0f0f0f] p-3 text-sm text-zinc-200" @input="emit('update:reviewInstructions', ($event.target as HTMLTextAreaElement).value)" />
          <div class="mt-3 grid grid-cols-3 gap-2 text-xs font-medium">
            <button class="rounded-xl bg-emerald-500 px-3 py-2 text-emerald-950" @click="emit('reviewDecision', 'approve')">通过并同步</button>
            <button class="rounded-xl bg-amber-500 px-3 py-2 text-amber-950" @click="emit('reviewDecision', 'rewrite')">替换/重写</button>
            <button class="rounded-xl bg-red-500 px-3 py-2 text-white" @click="emit('reviewDecision', 'rollback')">回滚节点</button>
          </div>
        </div>
        <div v-else class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm text-zinc-400">当前没有待审阅节点。</div>
      </div>

      <div v-else-if="activeTab === '生成逻辑'" class="space-y-3">
        <div v-for="(item, index) in generationLogic" :key="index" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm leading-7 text-zinc-300">{{ item }}</div>
        <p v-if="!generationLogic.length" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm text-zinc-500">等待节点生成逻辑。</p>
      </div>

      <div v-else class="space-y-2">
        <div v-for="event in latestEvents" :key="event.receivedAt + event.type" class="rounded-lg bg-[#0f0f0f] p-2 text-xs text-zinc-500"><span class="text-zinc-300">{{ event.type }}</span> · {{ event.receivedAt }}</div>
        <p v-if="!latestEvents.length" class="text-xs text-zinc-500">等待 SSE 事件。</p>
      </div>
    </div>
  </aside>
</template>
