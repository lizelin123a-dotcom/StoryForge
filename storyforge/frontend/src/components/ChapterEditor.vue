<script setup lang="ts">
import type { Chapter } from '../types'

defineProps<{
  chapters: Chapter[]
  activeChapter: number
  currentChapterText: string
}>()

const emit = defineEmits<{
  'update:activeChapter': [value: number]
  'update:currentChapterText': [value: string]
}>()
</script>

<template>
  <section class="flex min-w-[400px] flex-1 flex-col bg-[#0f0f0f]">
    <div class="border-b border-[#2a2a2a] bg-[#141414]/80 px-5 py-3">
      <div v-if="chapters.length" class="flex gap-2 overflow-x-auto pb-1">
        <button v-for="(chapter, index) in chapters" :key="chapter.title" class="shrink-0 rounded-full border px-4 py-1.5 text-sm" :class="activeChapter === index ? 'border-indigo-500/50 bg-indigo-500/20 text-white' : 'border-[#2a2a2a] bg-[#1a1a1a] text-zinc-400 hover:text-white'" @click="emit('update:activeChapter', index)">{{ chapter.title }}</button>
      </div>
      <p v-else class="text-sm text-zinc-500">尚未开始写作</p>
    </div>
    <div class="flex-1 overflow-y-auto p-6">
      <textarea v-if="chapters.length" :value="currentChapterText" class="min-h-full w-full resize-none rounded-2xl border border-[#2a2a2a] bg-[#151515] p-6 font-mono text-[15px] leading-8 text-zinc-200 shadow-2xl shadow-black/20" @input="emit('update:currentChapterText', ($event.target as HTMLTextAreaElement).value)" />
      <div v-else class="flex h-full items-center justify-center rounded-2xl border border-dashed border-[#3a3a3a] bg-[#151515] text-zinc-500">尚未开始写作，点击左侧“启动写作”后会自动加载持久化章节。</div>
    </div>
    <div class="border-t border-[#2a2a2a] bg-[#141414] px-6 py-3 text-sm text-zinc-400">节点 {{ chapters[activeChapter]?.nodesDone || 0 }}/{{ chapters[activeChapter]?.nodesTotal || 0 }}：{{ chapters[activeChapter]?.nodeLabel || '尚未开始' }}</div>
  </section>
</template>
