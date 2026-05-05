<script setup lang="ts">
import type { NovelSummary } from '../api'

defineProps<{
  novels: NovelSummary[]
}>()

const emit = defineEmits<{
  create: []
  load: [id: string]
}>()
</script>

<template>
  <section class="min-h-screen p-8">
    <header class="mb-8 flex items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl font-semibold text-white">我的书架</h1>
        <p class="mt-2 text-zinc-500">所有作品均来自后端 SQLite，不再使用硬编码样例。</p>
      </div>
      <button class="rounded-xl bg-indigo-500 px-5 py-3 text-sm font-medium text-white hover:bg-indigo-400" @click="emit('create')">＋ 新建作品</button>
    </header>
    <div v-if="novels.length" class="grid grid-cols-3 gap-5">
      <article v-for="novel in novels" :key="novel.id" class="group rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5 shadow-lg shadow-black/20 hover:-translate-y-1 hover:border-indigo-500/40" @click="emit('load', novel.id)">
        <div class="mb-5 flex items-center gap-4">
          <div class="flex h-20 w-16 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/35 to-blue-500/10 text-3xl text-white">{{ novel.title.slice(0, 1) || '书' }}</div>
          <div>
            <h2 class="text-xl font-semibold text-white">{{ novel.title }}</h2>
            <p class="mt-1 text-sm text-zinc-500">{{ novel.genre }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <span class="rounded-lg bg-[#0f0f0f] p-3 text-zinc-400">状态<br><b class="text-zinc-200">{{ novel.status }}</b></span>
          <span class="rounded-lg bg-[#0f0f0f] p-3 text-zinc-400">字数<br><b class="text-zinc-200">{{ novel.words }} 字</b></span>
        </div>
        <p class="mt-4 text-xs text-zinc-600">更新：{{ novel.updated_at || '暂无' }}</p>
      </article>
    </div>
    <div v-else class="rounded-3xl border border-dashed border-[#3a3a3a] bg-[#1a1a1a] p-12 text-center">
      <div class="text-5xl">📚</div>
      <h2 class="mt-4 text-xl text-white">书架还没有作品</h2>
      <p class="mt-2 text-zinc-500">点击“新建作品”，用一句话灵感生成设定并进入创作台。</p>
    </div>
  </section>
</template>
