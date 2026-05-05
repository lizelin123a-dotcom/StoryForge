<script setup lang="ts">
import type { GeneratedSettings } from '../api'

defineProps<{
  open: boolean
  loading: boolean
  logline: string
  settings: GeneratedSettings | null
}>()

const emit = defineEmits<{
  close: []
  'update:logline': [value: string]
  'update:settings': [value: GeneratedSettings | null]
  generate: []
  accept: []
}>()

function patchSettings(patch: Partial<GeneratedSettings>) {
  // Parent owns the object. This keeps extraction small while preserving existing v-model behavior.
  emit('update:settings', patch as GeneratedSettings)
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-6">
    <div class="w-full max-w-3xl rounded-3xl border border-[#2a2a2a] bg-[#151515] p-6 shadow-2xl shadow-black/50">
      <div class="mb-5 flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-semibold text-white">新建作品</h2>
          <p class="text-sm text-zinc-500">输入不超过 100 字的一句话灵感，由后端 LLM 生成设定。</p>
        </div>
        <button class="text-zinc-500 hover:text-white" @click="emit('close')">✕</button>
      </div>
      <label class="block text-sm text-zinc-400">
        一句话灵感（{{ logline.length }}/100）
        <textarea :value="logline" maxlength="100" rows="3" class="mt-2 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-zinc-200" placeholder="例如：退役调查员在星际禁航区收到十年前自己的求救信号" @input="emit('update:logline', ($event.target as HTMLTextAreaElement).value)" />
      </label>
      <div class="mt-4 flex gap-3">
        <button class="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white" :disabled="loading || !logline.trim()" @click="emit('generate')">{{ loading ? '生成中...' : settings ? '重新生成设定' : '生成设定' }}</button>
        <button v-if="settings" class="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950" @click="emit('accept')">接受并进入创作台</button>
      </div>
      <div v-if="settings" class="mt-5 grid gap-4 rounded-2xl border border-[#2a2a2a] bg-[#0f0f0f] p-5">
        <label class="text-xs text-zinc-500">标题<input v-model="settings.title" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" @input="patchSettings(settings)" /></label>
        <label class="text-xs text-zinc-500">世界观<textarea v-model="settings.world_setting" rows="4" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" @input="patchSettings(settings)" /></label>
        <label class="text-xs text-zinc-500">类型<input v-model="settings.genre" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" @input="patchSettings(settings)" /></label>
        <label class="text-xs text-zinc-500">目标字数<input v-model.number="settings.target_word_count" type="number" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" @input="patchSettings(settings)" /></label>
        <div>
          <div class="mb-2 text-xs text-zinc-500">角色</div>
          <div class="space-y-2">
            <div v-for="(character, index) in settings.characters" :key="index" class="grid grid-cols-3 gap-2">
              <input v-model="character.name" class="rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" placeholder="姓名" @input="patchSettings(settings)" />
              <input v-model="character.role" class="rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" placeholder="定位" @input="patchSettings(settings)" />
              <input v-model="character.description" class="rounded-xl border border-[#2a2a2a] bg-[#151515] p-3 text-sm text-zinc-200" placeholder="描述" @input="patchSettings(settings)" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
