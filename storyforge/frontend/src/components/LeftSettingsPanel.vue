<script setup lang="ts">
import type { CocreationMessage, CocreationTurn, EditorSkill } from '../types'
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
  fullAutoMode: boolean
  dissectSourceId: string
  editorChatInput: string
  editorChatMessages: CocreationMessage[]
  editorChatLoading: boolean
  editorChatLastTurn: CocreationTurn | null
  editorSkills: EditorSkill[]
  selectedSkillIds: string[]
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:settingOpen': [value: boolean]
  'update:fullAutoMode': [value: boolean]
  'update:dissectSourceId': [value: string]
  'update:editorChatInput': [value: string]
  sendEditorChat: []
  startWriting: []
  pauseWriting: []
  resumeWriting: []
  exportText: []
  applyEditorPatch: []
  toggleEditorSkill: [skillId: string]
}>()
</script>

<template>
  <aside class="border-r border-[#2a2a2a] bg-[#141414] transition-all duration-150" :class="collapsed ? 'w-12' : 'w-[360px]'">
    <button v-if="collapsed" class="h-full w-12 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="emit('update:collapsed', false)">›</button>
    <div v-else class="flex h-full flex-col p-4">
      <div class="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 class="text-xl font-semibold tracking-tight text-white">{{ selectedNovel?.title || '未选择作品' }}</h1>
          <span class="mt-2 inline-flex rounded-full border px-2.5 py-1 text-xs" :class="stateTone">{{ stateLabel }}</span>
        </div>
        <button class="rounded-lg border border-[#2a2a2a] px-2 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="emit('update:collapsed', true)">‹</button>
      </div>

      <section class="mb-3 flex min-h-0 flex-1 flex-col rounded-xl border border-[#2a2a2a] bg-[#101010] shadow-lg shadow-black/20">
        <div class="border-b border-[#2a2a2a] px-4 py-3">
          <div class="flex items-center justify-between gap-2">
            <div class="text-sm font-medium text-white">创作对话</div>
            <span class="rounded-full border border-indigo-500/30 px-2 py-0.5 text-[11px] text-indigo-200">Skill {{ selectedSkillIds.length }}</span>
          </div>
          <p class="mt-1 text-xs text-zinc-500">写作过程中继续聊思路。AI 会归纳并写入资产，不需要你手动填表。</p>
          <div v-if="editorSkills.length" class="mt-3 flex gap-2 overflow-x-auto pb-1">
            <button v-for="skill in editorSkills" :key="skill.id" class="shrink-0 rounded-full border px-3 py-1 text-[11px]" :class="selectedSkillIds.includes(skill.id) ? 'border-indigo-500/50 bg-indigo-500/20 text-white' : 'border-[#2a2a2a] bg-[#0f0f0f] text-zinc-500 hover:text-zinc-200'" :title="skill.description" @click="emit('toggleEditorSkill', skill.id)">{{ skill.title }}</button>
          </div>
        </div>
        <div class="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
          <div v-if="!editorChatMessages.length" class="rounded-xl border border-dashed border-[#333] p-4 text-sm leading-7 text-zinc-500">可以直接问：这一章怎么推进？这个角色动机弱不弱？这里缺不缺爽点？我想加一个反转行不行？</div>
          <div v-for="(message, index) in editorChatMessages" :key="index" class="rounded-xl p-3 text-sm leading-7" :class="message.role === 'user' ? 'ml-8 bg-indigo-500/15 text-indigo-100' : 'mr-8 border border-[#2a2a2a] bg-[#171717] text-zinc-300'">{{ message.content }}</div>
        </div>
        <div class="border-t border-[#2a2a2a] p-3">
          <textarea :value="editorChatInput" rows="3" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" placeholder="边写边聊，Ctrl+Enter 发送" @input="emit('update:editorChatInput', ($event.target as HTMLTextAreaElement).value)" @keydown.ctrl.enter.prevent="emit('sendEditorChat')" />
          <button class="mt-2 w-full rounded-xl bg-indigo-500 px-3 py-2 text-sm font-medium text-white disabled:opacity-50" :disabled="editorChatLoading || !editorChatInput.trim()" @click="emit('sendEditorChat')">{{ editorChatLoading ? '思考中...' : '发送给 AI 编辑' }}</button>
        </div>
      </section>

      <section class="max-h-[32vh] overflow-y-auto rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] shadow-lg shadow-black/20">
        <button class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-white" @click="emit('update:settingOpen', !settingOpen)">资产与操作 <span class="text-zinc-500">{{ settingOpen ? '−' : '+' }}</span></button>
        <div v-if="settingOpen" class="space-y-3 border-t border-[#2a2a2a] p-4">
          <div v-if="selectedNovel?.assets && Object.keys(selectedNovel.assets).length" class="rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-3">
            <div class="mb-2 text-xs font-medium text-indigo-200">AI 已沉淀资产</div>
            <div class="space-y-2 text-xs leading-6 text-zinc-300">
              <p v-for="(value, key) in selectedNovel.assets" :key="key"><span class="text-zinc-500">{{ key }}：</span>{{ value }}</p>
            </div>
            <div v-if="editorChatLastTurn?.edit_patch?.target && editorChatLastTurn.edit_patch.target !== 'none'" class="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
              <div class="text-xs font-medium text-emerald-200">AI 可应用修改 · {{ editorChatLastTurn.edit_patch.target }} / {{ editorChatLastTurn.edit_patch.mode }}</div>
              <p class="mt-2 line-clamp-4 whitespace-pre-wrap text-xs leading-6 text-zinc-300">{{ editorChatLastTurn.edit_patch.content }}</p>
              <p v-if="editorChatLastTurn.edit_patch.reason" class="mt-2 text-xs text-zinc-500">{{ editorChatLastTurn.edit_patch.reason }}</p>
              <button class="mt-2 w-full rounded-lg bg-emerald-500 px-3 py-2 text-xs font-medium text-emerald-950" @click="emit('applyEditorPatch')">应用到当前{{ editorChatLastTurn.edit_patch.target === 'node' ? '节点' : '章节' }}</button>
            </div>
            <p v-if="editorChatLastTurn" class="mt-2 border-t border-indigo-500/20 pt-2 text-xs text-indigo-200">下一轮重点：{{ editorChatLastTurn.next_focus }}</p>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <label class="text-zinc-500">目标字数<input v-model.number="writingForm.target_word_count" type="number" class="mt-1 w-full rounded-lg border border-[#2a2a2a] bg-[#0f0f0f] p-2 text-zinc-200" /></label>
            <label class="text-zinc-500">类型<input v-model="writingForm.genre" readonly class="mt-1 w-full rounded-lg border border-[#2a2a2a] bg-[#0f0f0f] p-2 text-zinc-300" /></label>
          </div>
          <label class="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-200"><input :checked="fullAutoMode" type="checkbox" @change="emit('update:fullAutoMode', ($event.target as HTMLInputElement).checked)" /> 全自动模式：跳过节点审阅并直接写入正文</label>
          <details class="rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-xs text-zinc-500">
            <summary class="cursor-pointer text-zinc-300">高级配置</summary>
            <div class="mt-3 space-y-2">
              <label class="block">API Key<input v-model="writingForm.apiKey" type="password" class="mt-1 w-full rounded-lg border border-[#2a2a2a] bg-[#151515] p-2 text-zinc-200" /></label>
              <label class="block">LLM API Base URL<input v-model="writingForm.apiBaseUrl" class="mt-1 w-full rounded-lg border border-[#2a2a2a] bg-[#151515] p-2 text-zinc-200" /></label>
              <label class="block">模型选择<input v-model="writingForm.model" class="mt-1 w-full rounded-lg border border-[#2a2a2a] bg-[#151515] p-2 text-zinc-200" /></label>
              <label class="block">对标素材 ID<input :value="dissectSourceId" class="mt-1 w-full rounded-lg border border-[#2a2a2a] bg-[#151515] p-2 text-zinc-200" @input="emit('update:dissectSourceId', ($event.target as HTMLInputElement).value)" /></label>
            </div>
          </details>
        </div>
      </section>

      <div class="mt-3 grid grid-cols-2 gap-2">
        <button class="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-medium text-emerald-950 hover:bg-emerald-400" @click="emit('startWriting')">▶ 启动写作</button>
        <button class="rounded-xl bg-amber-500 px-3 py-2 text-sm font-medium text-amber-950 hover:bg-amber-400" @click="emit('pauseWriting')">⏸ 暂停</button>
        <button class="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500" @click="emit('resumeWriting')">▶ 继续</button>
        <button class="rounded-xl bg-zinc-700 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-600" @click="emit('exportText')">📥 导出</button>
      </div>
    </div>
  </aside>
</template>
