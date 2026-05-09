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
    planningModel: string
    writingModel: string
    reviewModel: string
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
  <aside class="writer-side writer-side--left" :class="collapsed ? 'writer-side--collapsed' : ''">
    <button v-if="collapsed" class="side-collapse-button" @click="emit('update:collapsed', false)">AI</button>
    <div v-else class="writer-side__inner">
      <header class="side-header">
        <div class="min-w-0">
          <p class="section-kicker">Editor</p>
          <h2>AI 编辑</h2>
          <p>{{ selectedNovel?.genre || '创作辅助' }} · {{ selectedSkillIds.length }} 个 Skill</p>
        </div>
        <button class="sf-icon-btn" aria-label="收起左侧面板" @click="emit('update:collapsed', true)">‹</button>
      </header>

      <section class="side-card side-card--chat">
        <div class="side-card__header">
          <div>
            <h3>创作对话</h3>
            <p>讨论当前章节、节点、角色动机和读者期待。</p>
          </div>
        </div>
        <div v-if="editorSkills.length" class="skill-row">
          <button v-for="skill in editorSkills" :key="skill.id" class="skill-chip" :class="selectedSkillIds.includes(skill.id) ? 'skill-chip--active' : ''" :title="skill.description" @click="emit('toggleEditorSkill', skill.id)">{{ skill.title }}</button>
        </div>
        <div class="chat-stream">
          <div v-if="!editorChatMessages.length" class="empty-hint">可以直接问：这一章怎么推进？这个角色动机弱不弱？这里缺不缺爽点？我想加一个反转行不行？</div>
          <article v-for="(message, index) in editorChatMessages" :key="index" class="chat-bubble" :class="message.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--ai'">{{ message.content }}</article>
        </div>
        <div class="chat-composer">
          <textarea :value="editorChatInput" rows="3" placeholder="边写边聊，Ctrl+Enter 发送" @input="emit('update:editorChatInput', ($event.target as HTMLTextAreaElement).value)" @keydown.ctrl.enter.prevent="emit('sendEditorChat')" />
          <button class="sf-btn sf-btn--primary w-full" :disabled="editorChatLoading || !editorChatInput.trim()" @click="emit('sendEditorChat')">{{ editorChatLoading ? '思考中...' : '发送给 AI 编辑' }}</button>
        </div>
      </section>

      <section class="side-card side-card--assets">
        <button class="side-card__toggle" @click="emit('update:settingOpen', !settingOpen)">
          <span>作品资产与操作</span>
          <span>{{ settingOpen ? '收起' : '展开' }}</span>
        </button>
        <div v-if="settingOpen" class="asset-panel">
          <div v-if="selectedNovel?.assets && Object.keys(selectedNovel.assets).length" class="asset-list">
            <p class="section-kicker">Living Assets</p>
            <p v-for="(value, key) in selectedNovel.assets" :key="key"><strong>{{ key }}</strong><span>{{ value }}</span></p>
          </div>
          <div v-if="editorChatLastTurn?.edit_patch?.target && editorChatLastTurn.edit_patch.target !== 'none'" class="patch-card">
            <strong>AI 可应用修改 · {{ editorChatLastTurn.edit_patch.target }} / {{ editorChatLastTurn.edit_patch.mode }}</strong>
            <p>{{ editorChatLastTurn.edit_patch.content }}</p>
            <button class="sf-btn sf-btn--success w-full" @click="emit('applyEditorPatch')">应用到当前{{ editorChatLastTurn.edit_patch.target === 'node' ? '节点' : editorChatLastTurn.edit_patch.target === 'span' ? '段落' : '章节' }}</button>
          </div>
          <div class="field-grid">
            <label>目标字数<input v-model.number="writingForm.target_word_count" type="number" /></label>
            <label>类型<input v-model="writingForm.genre" readonly /></label>
          </div>
          <section class="model-connect-panel">
            <p class="section-kicker">模型接入</p>
            <label>DeepSeek API Key<input v-model="writingForm.apiKey" type="password" placeholder="sk-..." /></label>
            <label>DeepSeek API Base URL<input v-model="writingForm.apiBaseUrl" placeholder="https://api.deepseek.com/v1" /></label>
            <div class="field-grid">
              <label>默认模型<input v-model="writingForm.model" placeholder="deepseek-chat" /></label>
              <label>正文模型<input v-model="writingForm.writingModel" placeholder="deepseek-chat" /></label>
            </div>
            <p class="muted-line">正文建议用 deepseek-chat。GPT 不建议写正文。</p>
          </section>
          <label class="danger-toggle"><input :checked="fullAutoMode" type="checkbox" @change="emit('update:fullAutoMode', ($event.target as HTMLInputElement).checked)" /> 全自动模式：跳过节点审阅并直接写入正文</label>
          <details class="advanced-config">
            <summary>高级配置</summary>
            <label>规划模型<input v-model="writingForm.planningModel" placeholder="deepseek-chat" /></label>
            <label>审稿模型<input v-model="writingForm.reviewModel" placeholder="deepseek-chat" /></label>
            <label>对标素材 ID<input :value="dissectSourceId" @input="emit('update:dissectSourceId', ($event.target as HTMLInputElement).value)" /></label>
          </details>
        </div>
      </section>

      <footer class="side-actions">
        <button class="sf-btn sf-btn--success" @click="emit('startWriting')">启动写作</button>
        <button class="sf-btn sf-btn--warning" @click="emit('pauseWriting')">暂停</button>
        <button class="sf-btn sf-btn--ghost" @click="emit('resumeWriting')">继续</button>
        <button class="sf-btn sf-btn--ghost" @click="emit('exportText')">导出</button>
      </footer>
    </div>
  </aside>
</template>
