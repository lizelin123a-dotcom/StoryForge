<script setup lang="ts">
import type { Chapter, NodeDraft } from '../types'

defineProps<{
  chapters: Chapter[]
  activeChapter: number
  currentChapterText: string
  nodeDrafts: NodeDraft[]
  selectedNodeId: string
  currentNodeText: string
  saveLoading: boolean
  pendingNode: Record<string, unknown> | null
  pendingNodeTitle: string
}>()

const emit = defineEmits<{
  'update:activeChapter': [value: number]
  'update:currentChapterText': [value: string]
  'update:selectedNodeId': [value: string]
  'update:currentNodeText': [value: string]
  saveChapter: []
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
}>()
</script>

<template>
  <section class="flex min-w-[400px] flex-1 flex-col bg-[#0f0f0f]">
    <div class="border-b border-[#2a2a2a] bg-[#141414]/80 px-5 py-3">
      <div v-if="chapters.length" class="flex items-center gap-2 overflow-x-auto pb-1">
        <button v-for="(chapter, index) in chapters" :key="chapter.title" class="shrink-0 rounded-full border px-4 py-1.5 text-sm" :class="activeChapter === index ? 'border-indigo-500/50 bg-indigo-500/20 text-white' : 'border-[#2a2a2a] bg-[#1a1a1a] text-zinc-400 hover:text-white'" @click="emit('update:activeChapter', index)">{{ chapter.title }}<span v-if="chapter.dirty" class="ml-1 text-amber-300">●</span></button>
        <button class="ml-auto shrink-0 rounded-full bg-emerald-500 px-4 py-1.5 text-sm font-medium text-emerald-950 disabled:opacity-50" :disabled="saveLoading" @click="emit('saveChapter')">{{ saveLoading ? '保存中' : '保存章节' }}</button>
      </div>
      <p v-else class="text-sm text-zinc-500">尚未开始写作</p>
    </div>

    <div class="grid min-h-0 flex-1 grid-cols-[1fr_300px]">
      <div class="min-h-0 overflow-y-auto p-6">
        <textarea v-if="chapters.length" :value="currentChapterText" class="min-h-full w-full resize-none rounded-2xl border border-[#2a2a2a] bg-[#151515] p-6 font-mono text-[15px] leading-8 text-zinc-200 shadow-2xl shadow-black/20" @input="emit('update:currentChapterText', ($event.target as HTMLTextAreaElement).value)" />
        <div v-else class="flex h-full items-center justify-center rounded-2xl border border-dashed border-[#3a3a3a] bg-[#151515] text-zinc-500">尚未开始写作，点击左侧“启动写作”后会自动加载持久化章节。</div>
      </div>

      <aside class="min-h-0 overflow-y-auto border-l border-[#2a2a2a] bg-[#121212] p-4">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-white">节点草稿 / 审阅</h3>
          <button class="rounded-lg border border-[#2a2a2a] px-2 py-1 text-xs text-zinc-400 hover:text-white" :disabled="!selectedNodeId" @click="emit('saveNode')">保存草稿</button>
        </div>
        <div class="space-y-2">
          <button v-for="node in nodeDrafts" :key="node.id" class="w-full rounded-xl border p-3 text-left text-xs" :class="selectedNodeId === node.id ? 'border-indigo-500/50 bg-indigo-500/15 text-white' : 'border-[#2a2a2a] bg-[#1a1a1a] text-zinc-400 hover:text-zinc-200'" @click="emit('update:selectedNodeId', node.id)">
            <div class="flex justify-between"><span>节点 {{ node.node_index }} · {{ node.node_type }}</span><span>{{ node.locked ? '🔒' : '未锁' }}</span></div>
            <p class="mt-1 line-clamp-2 leading-5 text-zinc-500">{{ node.content || '空节点' }}</p>
          </button>
          <p v-if="!nodeDrafts.length" class="rounded-xl border border-dashed border-[#333] p-4 text-sm leading-7 text-zinc-500">还没有节点草稿。AI 生成节点后会自动沉淀；你也可以先保存整章正文。</p>
        </div>
        <div v-if="selectedNodeId" class="mt-4">
          <div v-if="pendingNode" class="mb-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">当前待审阅：{{ pendingNodeTitle }}。直接在下面编辑草稿，通过后才会写入中间正文。</div>
          <textarea :value="currentNodeText" rows="10" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm leading-7 text-zinc-200" @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)" />
          <div v-if="pendingNode" class="mt-2 grid grid-cols-3 gap-2">
            <button class="rounded-xl bg-emerald-500 px-3 py-2 text-xs font-medium text-emerald-950" @click="emit('reviewDecision', 'approve')">通过写入</button>
            <button class="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200" @click="emit('reviewDecision', 'rewrite')">修改后通过</button>
            <button class="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200" @click="emit('reviewDecision', 'rollback')">回滚</button>
          </div>
          <button v-if="nodeDrafts.find((node) => node.id === selectedNodeId)" class="mt-2 w-full rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200" @click="emit('toggleNodeLock', nodeDrafts.find((node) => node.id === selectedNodeId)!)">{{ nodeDrafts.find((node) => node.id === selectedNodeId)?.locked ? '解锁该节点' : '锁定该节点' }}</button>
        </div>
      </aside>
    </div>

    <div class="border-t border-[#2a2a2a] bg-[#141414] px-6 py-3 text-sm text-zinc-400">节点 {{ chapters[activeChapter]?.nodesDone || 0 }}/{{ chapters[activeChapter]?.nodesTotal || 0 }}：{{ chapters[activeChapter]?.nodeLabel || '尚未开始' }}</div>
  </section>
</template>
