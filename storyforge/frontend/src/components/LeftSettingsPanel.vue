<script setup lang="ts">
import type { NovelDetail } from '../api'

defineProps<{
  collapsed: boolean
  selectedNovel: NovelDetail | null
  stateTone: string
  stateLabel: string
  settingOpen: boolean
  writingForm: {
    world_setting: string
    characters: string
    genre: string
    target_word_count: number
    apiKey: string
    apiBaseUrl: string
    model: string
  }
  semiAutoMode: boolean
  dissectSourceId: string
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:settingOpen': [value: boolean]
  'update:semiAutoMode': [value: boolean]
  'update:dissectSourceId': [value: string]
  startWriting: []
  pauseWriting: []
  resumeWriting: []
  exportText: []
}>()
</script>

<template>
  <aside class="border-r border-[#2a2a2a] bg-[#141414] transition-all duration-150" :class="collapsed ? 'w-12' : 'w-[320px]'">
    <button v-if="collapsed" class="h-full w-12 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="emit('update:collapsed', false)">›</button>
    <div v-else class="flex h-full flex-col p-4">
      <div class="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 class="text-xl font-semibold tracking-tight text-white">{{ selectedNovel?.title || '未选择作品' }}</h1>
          <span class="mt-2 inline-flex rounded-full border px-2.5 py-1 text-xs" :class="stateTone">{{ stateLabel }}</span>
        </div>
        <button class="rounded-lg border border-[#2a2a2a] px-2 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="emit('update:collapsed', true)">‹</button>
      </div>
      <div class="overflow-y-auto pr-1">
        <section class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] shadow-lg shadow-black/20">
          <button class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-white" @click="emit('update:settingOpen', !settingOpen)">设定区 <span class="text-zinc-500">{{ settingOpen ? '−' : '+' }}</span></button>
          <div v-if="settingOpen" class="space-y-3 border-t border-[#2a2a2a] p-4">
            <label class="block text-xs text-zinc-500">世界观<textarea v-model="writingForm.world_setting" rows="4" readonly class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-300" /></label>
            <label class="block text-xs text-zinc-500">人物设定<textarea v-model="writingForm.characters" rows="5" readonly class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-300" /></label>
            <label class="block text-xs text-zinc-500">类型<input v-model="writingForm.genre" readonly class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-300" /></label>
            <div v-if="selectedNovel?.assets && Object.keys(selectedNovel.assets).length" class="rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-3">
              <div class="mb-2 text-xs font-medium text-indigo-200">共创资产</div>
              <div class="space-y-2 text-xs leading-6 text-zinc-300">
                <p v-for="(value, key) in selectedNovel.assets" :key="key"><span class="text-zinc-500">{{ key }}：</span>{{ value }}</p>
              </div>
            </div>
            <label class="block text-xs text-zinc-500">目标字数<input v-model.number="writingForm.target_word_count" type="number" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
            <label class="flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-200"><input :checked="semiAutoMode" type="checkbox" @change="emit('update:semiAutoMode', ($event.target as HTMLInputElement).checked)" /> 半自动模式：每个节点生成后暂停审阅</label>
            <label class="block text-xs text-zinc-500">API Key<input v-model="writingForm.apiKey" type="password" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
            <label class="block text-xs text-zinc-500">LLM API Base URL<input v-model="writingForm.apiBaseUrl" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
            <label class="block text-xs text-zinc-500">模型选择<input v-model="writingForm.model" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
          </div>
        </section>
        <section class="mt-4 rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 shadow-lg shadow-black/20">
          <h2 class="mb-3 text-sm font-medium text-white">对标拆解引用</h2>
          <input :value="dissectSourceId" placeholder="可选：拆解素材 ID" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" @input="emit('update:dissectSourceId', ($event.target as HTMLInputElement).value)" />
        </section>
      </div>
      <div class="mt-auto grid grid-cols-2 gap-2 pt-4">
        <button class="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-medium text-emerald-950 hover:bg-emerald-400" @click="emit('startWriting')">▶ 启动写作</button>
        <button class="rounded-xl bg-amber-500 px-3 py-2 text-sm font-medium text-amber-950 hover:bg-amber-400" @click="emit('pauseWriting')">⏸ 暂停</button>
        <button class="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500" @click="emit('resumeWriting')">▶ 继续</button>
        <button class="rounded-xl bg-zinc-700 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-600" @click="emit('exportText')">📥 导出文本</button>
      </div>
    </div>
  </aside>
</template>
