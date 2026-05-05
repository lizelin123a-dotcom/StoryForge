<script setup lang="ts">
import type { NovelSummary } from '../api'

defineProps<{
  novels: NovelSummary[]
  writingForm: {
    backendApiBaseUrl: string
    apiKey: string
    apiBaseUrl: string
    model: string
  }
}>()

const emit = defineEmits<{
  load: [id: string]
  delete: [id: string]
  testConnection: []
  exportAll: []
}>()
</script>

<template>
  <section class="min-h-screen p-8">
    <header class="mb-6">
      <h1 class="text-2xl font-semibold text-white">配置</h1>
      <p class="text-zinc-500">管理作品、LLM 配置与数据导出。</p>
    </header>
    <div class="grid grid-cols-[1fr_360px] gap-6">
      <div class="rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5">
        <h2 class="mb-4 text-lg font-medium text-white">作品列表</h2>
        <div class="space-y-3">
          <div v-for="novel in novels" :key="novel.id" class="grid grid-cols-[1.4fr_0.8fr_0.8fr_0.8fr_120px] items-center gap-3 rounded-xl bg-[#0f0f0f] p-4 text-sm text-zinc-400">
            <button class="text-left text-white hover:text-indigo-300" @click="emit('load', novel.id)">{{ novel.title }}</button>
            <span>{{ novel.genre }}</span>
            <span>{{ novel.status }}</span>
            <span>{{ novel.words }} 字</span>
            <button class="rounded-lg bg-red-500/80 px-3 py-2 text-xs text-white" @click="emit('delete', novel.id)">删除</button>
          </div>
          <p v-if="!novels.length" class="text-sm text-zinc-500">暂无作品。</p>
        </div>
      </div>
      <div class="space-y-6">
        <div class="rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5">
          <h2 class="mb-4 text-lg font-medium text-white">后端连接</h2>
          <input v-model="writingForm.backendApiBaseUrl" placeholder="后端 API Base URL" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm" />
        </div>
        <div class="rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5">
          <h2 class="mb-4 text-lg font-medium text-white">LLM 配置</h2>
          <div class="space-y-3">
            <input v-model="writingForm.apiKey" type="password" placeholder="API Key" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm" />
            <input v-model="writingForm.apiBaseUrl" placeholder="LLM API Base URL" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm" />
            <input v-model="writingForm.model" placeholder="模型名称" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm" />
            <button class="w-full rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white" @click="emit('testConnection')">测试连接</button>
          </div>
        </div>
        <div class="rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-5">
          <h2 class="mb-4 text-lg font-medium text-white">数据管理</h2>
          <button class="w-full rounded-xl bg-zinc-700 px-4 py-2 text-sm text-white" @click="emit('exportAll')">导出作品列表</button>
        </div>
      </div>
    </div>
  </section>
</template>
