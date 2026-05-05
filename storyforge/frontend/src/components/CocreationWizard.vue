<script setup lang="ts">
import type { CocreationMessage, CocreationTurn } from '../types'

const props = defineProps<{
  open: boolean
  loading: boolean
  logline: string
  input: string
  messages: CocreationMessage[]
  assets: Record<string, string>
  lastTurn: CocreationTurn | null
}>()

const emit = defineEmits<{
  close: []
  'update:logline': [value: string]
  'update:input': [value: string]
  send: []
  accept: []
}>()

const assetKeys = ['核心灵感', '主角欲望', '世界规则', '核心矛盾', '期待钩子', '爽点模型', '角色关系']
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-6">
    <div class="grid h-[82vh] w-full max-w-6xl grid-cols-[1.1fr_0.9fr] overflow-hidden rounded-3xl border border-[#2a2a2a] bg-[#151515] shadow-2xl shadow-black/50">
      <section class="flex min-h-0 flex-col border-r border-[#2a2a2a]">
        <div class="border-b border-[#2a2a2a] p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-2xl font-semibold text-white">共创构思</h2>
              <p class="mt-1 text-sm text-zinc-500">先对话，不直出。AI 负责追问、归纳和沉淀资产，你决定作品长什么样。</p>
            </div>
            <button class="text-zinc-500 hover:text-white" @click="emit('close')">✕</button>
          </div>
          <textarea :value="logline" rows="2" class="mt-4 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" placeholder="先写一句灵感，例如：一个被流放的阵法师发现皇城地下埋着自己的前世尸骨" @input="emit('update:logline', ($event.target as HTMLTextAreaElement).value)" />
        </div>

        <div class="min-h-0 flex-1 space-y-3 overflow-y-auto p-5">
          <div v-if="!messages.length" class="rounded-2xl border border-dashed border-[#3a3a3a] bg-[#0f0f0f] p-5 text-sm leading-7 text-zinc-400">把你的想法丢进来。这里不会一次性生成一份死设定，而是像编辑一样一轮一轮问：主角想要什么、世界怎么压迫他、读者期待什么、爽点从哪里来。</div>
          <div v-for="(message, index) in messages" :key="index" class="rounded-2xl p-4 text-sm leading-7" :class="message.role === 'user' ? 'ml-12 bg-indigo-500/15 text-indigo-100' : 'mr-12 border border-[#2a2a2a] bg-[#0f0f0f] text-zinc-300'">{{ message.content }}</div>
        </div>

        <div class="border-t border-[#2a2a2a] p-4">
          <textarea :value="input" rows="3" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" placeholder="继续补充你的想法，或者回答 AI 的问题" @input="emit('update:input', ($event.target as HTMLTextAreaElement).value)" @keydown.ctrl.enter.prevent="emit('send')" />
          <div class="mt-3 flex gap-3">
            <button class="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-50" :disabled="loading || (!input.trim() && !logline.trim())" @click="emit('send')">{{ loading ? '讨论中...' : '发送 / 继续追问' }}</button>
            <button class="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950" :disabled="!Object.keys(assets).length" @click="emit('accept')">用这些资产创建作品</button>
          </div>
        </div>
      </section>

      <aside class="min-h-0 overflow-y-auto p-5">
        <h3 class="text-base font-semibold text-white">小说资产库</h3>
        <p class="mt-1 text-xs text-zinc-500">确认过的东西才沉淀，后续可继续编辑。</p>
        <div class="mt-4 space-y-3">
          <div v-for="key in assetKeys" :key="key" class="rounded-2xl border border-[#2a2a2a] bg-[#0f0f0f] p-4">
            <div class="mb-2 text-sm font-medium text-zinc-200">{{ key }}</div>
            <p class="whitespace-pre-wrap text-sm leading-7 text-zinc-400">{{ assets[key] || '待讨论' }}</p>
          </div>
        </div>
        <div v-if="lastTurn" class="mt-4 rounded-2xl border border-indigo-500/30 bg-indigo-500/10 p-4 text-sm text-indigo-100">下一轮重点：{{ lastTurn.next_focus }}</div>
      </aside>
    </div>
  </div>
</template>
