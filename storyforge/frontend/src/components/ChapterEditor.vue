<script setup lang="ts">
import { computed } from 'vue'
import type { Chapter, NodeDraft } from '../types'

const props = defineProps<{
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

const selectedNode = computed(() => props.nodeDrafts.find((node) => node.id === props.selectedNodeId) || null)
const hasPendingReview = computed(() => Boolean(props.pendingNode))

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
  <section class="flex min-w-[560px] flex-1 flex-col overflow-hidden bg-[#0f0f0f]">
    <div class="border-b border-[#252525] bg-[#141414]/95 px-5 py-3">
      <div v-if="chapters.length" class="flex items-center gap-3">
        <div class="min-w-0 flex-1 overflow-x-auto pb-1">
          <div class="flex min-w-max items-center gap-2">
            <button v-for="(chapter, index) in chapters" :key="chapter.title" class="shrink-0 rounded-full border px-4 py-1.5 text-sm" :class="activeChapter === index ? 'border-indigo-500/50 bg-indigo-500/20 text-white shadow-sm shadow-indigo-950/20' : 'border-[#2a2a2a] bg-[#1a1a1a] text-zinc-400 hover:border-zinc-600 hover:text-white'" @click="emit('update:activeChapter', index)">
              {{ chapter.title }}<span v-if="chapter.dirty" class="ml-1 text-amber-300">●</span>
            </button>
          </div>
        </div>
        <button class="shrink-0 rounded-full bg-emerald-500 px-4 py-1.5 text-sm font-medium text-emerald-950 hover:bg-emerald-400 disabled:opacity-50" :disabled="saveLoading" @click="emit('saveChapter')">{{ saveLoading ? '保存中' : '保存章节' }}</button>
      </div>
      <p v-else class="text-sm text-zinc-500">尚未开始写作</p>
    </div>

    <div class="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_360px] overflow-hidden">
      <div class="min-h-0 overflow-y-auto p-5">
        <textarea v-if="chapters.length" :value="currentChapterText" class="h-full min-h-[520px] w-full resize-none rounded-2xl border border-[#282828] bg-[#151515] p-6 font-mono text-[15px] leading-8 text-zinc-200 shadow-2xl shadow-black/20" @input="emit('update:currentChapterText', ($event.target as HTMLTextAreaElement).value)" />
        <div v-else class="flex h-full items-center justify-center rounded-2xl border border-dashed border-[#3a3a3a] bg-[#151515] px-6 text-center text-zinc-500">尚未开始写作，点击左侧“启动写作”后会自动加载持久化章节。</div>
      </div>

      <aside class="flex min-h-0 flex-col border-l border-[#252525] bg-[#121212]">
        <header class="shrink-0 border-b border-[#252525] p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h3 class="text-sm font-semibold text-white">节点草稿 / 审阅</h3>
              <p class="mt-1 text-xs leading-5 text-zinc-500">节点草稿就是审阅稿，通过后写入正文。</p>
            </div>
            <button class="shrink-0 rounded-lg border border-[#2a2a2a] px-2.5 py-1.5 text-xs text-zinc-400 hover:border-zinc-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-40" :disabled="!selectedNodeId" @click="emit('saveNode')">保存</button>
          </div>
        </header>

        <div class="shrink-0 border-b border-[#252525] p-3">
          <div class="max-h-[34vh] space-y-2 overflow-y-auto pr-1">
            <button v-for="node in nodeDrafts" :key="node.id" class="w-full rounded-xl border p-3 text-left text-xs transition" :class="selectedNodeId === node.id ? 'border-indigo-500/60 bg-indigo-500/15 text-white shadow-sm shadow-indigo-950/20' : 'border-[#2a2a2a] bg-[#1a1a1a] text-zinc-400 hover:border-zinc-600 hover:text-zinc-200'" @click="emit('update:selectedNodeId', node.id)">
              <div class="flex items-center justify-between gap-2">
                <span class="min-w-0 truncate font-medium">节点 {{ node.node_index }} · {{ node.node_type }}</span>
                <span class="shrink-0 rounded-full border px-2 py-0.5 text-[10px]" :class="node.locked ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200' : 'border-zinc-700 text-zinc-500'">{{ node.locked ? '已锁定' : '草稿' }}</span>
              </div>
              <p class="mt-1 line-clamp-2 leading-5 text-zinc-500">{{ node.content || '空节点' }}</p>
            </button>
            <p v-if="!nodeDrafts.length" class="rounded-xl border border-dashed border-[#333] p-4 text-sm leading-7 text-zinc-500">还没有节点草稿。AI 生成节点后会自动沉淀在这里。</p>
          </div>
        </div>

        <div class="flex min-h-0 flex-1 flex-col p-4">
          <div v-if="selectedNodeId" class="flex min-h-0 flex-1 flex-col">
            <div v-if="hasPendingReview" class="mb-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-6 text-amber-100">
              <div class="font-medium text-amber-200">当前待审阅：{{ pendingNodeTitle }}</div>
              <p class="text-zinc-400">在下方直接改稿。通过后才会写入中间正文。</p>
            </div>
            <textarea :value="currentNodeText" class="min-h-[220px] flex-1 resize-none rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm leading-7 text-zinc-200" @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)" />
            <div v-if="hasPendingReview" class="mt-3 space-y-2">
              <button class="w-full rounded-xl bg-emerald-500 px-3 py-2.5 text-sm font-medium text-emerald-950 hover:bg-emerald-400" @click="emit('reviewDecision', 'approve')">通过并写入正文</button>
              <div class="grid grid-cols-2 gap-2">
                <button class="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200 hover:bg-amber-500/15" @click="emit('reviewDecision', 'rewrite')">修改后通过</button>
                <button class="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200 hover:bg-red-500/15" @click="emit('reviewDecision', 'rollback')">回滚节点</button>
              </div>
            </div>
            <button v-if="selectedNode" class="mt-2 w-full rounded-xl border border-[#2a2a2a] bg-[#161616] px-3 py-2 text-xs text-zinc-300 hover:border-amber-500/40 hover:text-amber-200" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁该节点' : '锁定该节点' }}</button>
          </div>
          <div v-else class="flex min-h-[260px] flex-1 items-center justify-center rounded-xl border border-dashed border-[#333] px-6 text-center text-sm leading-7 text-zinc-500">选择一个节点草稿后，可以在这里编辑和审阅。</div>
        </div>
      </aside>
    </div>

    <div class="shrink-0 border-t border-[#252525] bg-[#141414] px-6 py-3 text-sm text-zinc-400">节点 {{ chapters[activeChapter]?.nodesDone || 0 }}/{{ chapters[activeChapter]?.nodesTotal || 0 }}：{{ chapters[activeChapter]?.nodeLabel || '尚未开始' }}</div>
  </section>
</template>
