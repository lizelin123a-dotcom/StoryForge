<script setup lang="ts">
import type { StepState } from '../types'

type DissectTab = '爽点分析' | '节奏分析' | '置换表'

defineProps<{
  steps: Record<string, StepState>
  activeTab: DissectTab
  dissectBook: { title: string; author: string; genre: string; wordCount: number }
  uploadedFileName: string
  shuangStats: { type: string; count: number }[]
  replacementRows: { group: string; old: string; next: string }[]
}>()

const emit = defineEmits<{
  fileSelected: [file?: File]
  runStep: [key: 'first' | 'second' | 'third']
  'update:activeTab': [tab: DissectTab]
}>()
</script>

<template>
  <section class="min-h-screen p-8">
    <header class="mb-6">
      <h1 class="text-2xl font-semibold text-white">对标拆解</h1>
      <p class="text-zinc-500">上传 .txt 对标书，执行三遍拆解并生成素材库。</p>
    </header>
    <div class="rounded-2xl border border-dashed border-[#3a3a3a] bg-[#1a1a1a] p-10 text-center" @dragover.prevent @drop.prevent="emit('fileSelected', $event.dataTransfer?.files[0])">
      <div class="text-4xl">📄</div>
      <p class="mt-3 text-zinc-300">拖拽上传或点击上传 .txt 文件</p>
      <input type="file" accept=".txt" class="mt-4 text-sm text-zinc-500" @change="emit('fileSelected', ($event.target as HTMLInputElement).files?.[0])" />
    </div>
    <div class="mt-6 grid grid-cols-[360px_1fr] gap-6">
      <div class="rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5">
        <h2 class="text-lg font-medium text-white">{{ uploadedFileName || dissectBook.title }}</h2>
        <p class="mt-2 text-sm text-zinc-500">作者：{{ dissectBook.author }} · 类型：{{ dissectBook.genre }} · {{ dissectBook.wordCount }} 字</p>
        <div class="mt-5 space-y-3">
          <button class="w-full rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white" @click="emit('runStep', 'first')">第一遍阅读模式 · {{ steps.first }}</button>
          <button class="w-full rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white" @click="emit('runStep', 'second')">第二遍拆解模式 · {{ steps.second }}</button>
          <button class="w-full rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white" @click="emit('runStep', 'third')">第三遍单元结构 · {{ steps.third }}</button>
        </div>
      </div>
      <div class="rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5">
        <div class="mb-4 flex gap-2">
          <button v-for="tab in ['爽点分析','节奏分析','置换表'] as DissectTab[]" :key="tab" class="rounded-full border px-4 py-1.5 text-sm" :class="activeTab === tab ? 'border-indigo-500/50 bg-indigo-500/20 text-white' : 'border-[#2a2a2a] text-zinc-400'" @click="emit('update:activeTab', tab)">{{ tab }}</button>
        </div>
        <div v-if="activeTab === '爽点分析'" class="space-y-4">
          <div v-for="item in shuangStats" :key="item.type" class="rounded-xl bg-[#0f0f0f] p-4 text-sm text-zinc-300">{{ item.type }} · {{ item.count }}</div>
        </div>
        <div v-else-if="activeTab === '节奏分析'" class="rounded-xl bg-[#0f0f0f] p-4 text-sm text-zinc-300">等待拆解结果。</div>
        <div v-else class="grid grid-cols-2 gap-3">
          <div v-for="row in replacementRows" :key="row.group" class="rounded-xl bg-[#0f0f0f] p-4">
            <div class="text-sm text-indigo-300">{{ row.group }}</div>
            <p class="mt-2 text-sm text-zinc-400">{{ row.old }} → {{ row.next }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
