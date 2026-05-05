<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CocreationMessage, CocreationTurn, EditorSkill, NodeDraft, RightTab, WritingAnalysis } from '../types'
import type { DaemonState, NovelDetail, SseEvent } from '../api'

const props = defineProps<{
  settingOpen: boolean
  fullAutoMode: boolean
  dissectSourceId: string
  editorChatInput: string
  selectedNovel: NovelDetail | null
  stateTone: string
  stateLabel: string
  writingForm: {
    world_setting: string
    characters: string
    genre: string
    target_word_count: number
    apiKey: string
    apiBaseUrl: string
    model: string
  }
  editorChatMessages: CocreationMessage[]
  editorChatLoading: boolean
  editorChatLastTurn: CocreationTurn | null
  editorSkills: EditorSkill[]
  selectedSkillIds: string[]
  chapters: { title: string; content: string; nodeLabel: string; nodesDone: number; nodesTotal: number; dirty?: boolean }[]
  activeChapter: number
  currentChapterText: string
  selectedNodeId: string
  currentNodeText: string
  nodeDrafts: NodeDraft[]
  saveLoading: boolean
  pendingNode: Record<string, unknown> | null
  pendingNodeTitle: string
  tabs: RightTab[]
  activeRightTab: RightTab
  wordPercent: number
  chapterPercent: number
  progress: DaemonState['progress']
  targetWordCount: number
  daemonState: DaemonState
  reviewEditContent: string
  reviewInstructions: string
  generationLogic: string[]
  latestEvents: SseEvent[]
  writingAnalysis: WritingAnalysis | null
  analysisLoading: boolean
}>()

const emit = defineEmits<{
  'update:settingOpen': [value: boolean]
  'update:fullAutoMode': [value: boolean]
  'update:dissectSourceId': [value: string]
  'update:editorChatInput': [value: string]
  'update:activeChapter': [value: number]
  'update:currentChapterText': [value: string]
  'update:selectedNodeId': [value: string]
  'update:currentNodeText': [value: string]
  'update:activeRightTab': [value: RightTab]
  'update:reviewEditContent': [value: string]
  'update:reviewInstructions': [value: string]
  sendEditorChat: []
  applyEditorPatch: []
  toggleEditorSkill: [skillId: string]
  startWriting: []
  pauseWriting: []
  resumeWriting: []
  exportText: []
  saveChapter: []
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
  analyzeCurrentText: []
}>()

const debugOpen = ref(false)
const currentChapterWords = computed(() => props.currentChapterText.length)
const selectedNode = computed(() => props.nodeDrafts.find((node) => node.id === props.selectedNodeId) || null)
const hasPendingReview = computed(() => Boolean(props.pendingNode))
const assetEntries = computed(() => Object.entries(props.selectedNovel?.assets || {}))
</script>

<template>
  <section class="storybook-writing-room">
    <div class="open-book open-book--writing">
      <section class="book-page book-page--left writing-left-page">
        <header class="book-page__header">
          <div>
            <p class="section-kicker">Desk Notes</p>
            <h1>案头设定</h1>
            <p>{{ selectedNovel?.title || '未选择作品' }}</p>
          </div>
          <button class="paper-chip" @click="emit('update:settingOpen', !settingOpen)">{{ settingOpen ? '收起' : '展开' }}</button>
        </header>

        <section v-if="settingOpen" class="desk-notes">
          <div v-if="assetEntries.length" class="desk-note-grid">
            <article v-for="([key, value]) in assetEntries" :key="key"><strong>{{ key }}</strong><span>{{ value }}</span></article>
          </div>
          <div v-else class="paper-empty">还没有沉淀设定。和 AI 编辑聊几轮，确认的信息会写到这里。</div>
        </section>

        <section class="review-paper">
          <div class="review-paper__title">
            <p class="section-kicker">Draft Review</p>
            <h2>当前审稿</h2>
          </div>
          <template v-if="selectedNodeId || hasPendingReview">
            <div v-if="hasPendingReview" class="review-banner"><strong>{{ pendingNodeTitle }}</strong><span>先在这里改，再决定是否写入正文。</span></div>
            <textarea :value="currentNodeText" class="paper-textarea paper-textarea--node" placeholder="当前节点草稿会显示在这里。" @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)" />
            <div class="review-actions">
              <button v-if="hasPendingReview" class="sf-btn sf-btn--success review-actions__primary" @click="emit('reviewDecision', 'approve')">通过并写入正文</button>
              <button v-if="hasPendingReview" class="sf-btn sf-btn--warning" @click="emit('reviewDecision', 'rewrite')">修改后通过</button>
              <button v-if="hasPendingReview" class="sf-btn sf-btn--danger" @click="emit('reviewDecision', 'rollback')">回滚节点</button>
              <button v-if="selectedNode" class="sf-btn sf-btn--ghost" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁节点' : '锁定节点' }}</button>
              <button class="sf-btn sf-btn--ghost" :disabled="!selectedNodeId" @click="emit('saveNode')">保存草稿</button>
            </div>
          </template>
          <div v-else class="paper-empty">AI 生成节点后，当前待审草稿会放在这里。你可以先问 AI 怎么改，再通过。</div>
        </section>

        <section class="ai-paper">
          <header>
            <div><p class="section-kicker">Editor Chat</p><h2>AI 编辑</h2></div>
            <span>{{ selectedSkillIds.length }} Skill</span>
          </header>
          <div v-if="editorSkills.length" class="skill-row">
            <button v-for="skill in editorSkills" :key="skill.id" class="skill-chip" :class="selectedSkillIds.includes(skill.id) ? 'skill-chip--active' : ''" :title="skill.description" @click="emit('toggleEditorSkill', skill.id)">{{ skill.title }}</button>
          </div>
          <div class="chat-stream chat-stream--paper">
            <div v-if="!editorChatMessages.length" class="paper-empty">可以问：这一章怎么推进？这个节点哪里弱？能不能加一个反转？</div>
            <article v-for="(message, index) in editorChatMessages" :key="index" class="chat-bubble" :class="message.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--ai'">{{ message.content }}</article>
          </div>
          <div v-if="editorChatLastTurn?.edit_patch?.target && editorChatLastTurn.edit_patch.target !== 'none'" class="patch-card"><strong>AI 可应用修改</strong><p>{{ editorChatLastTurn.edit_patch.content }}</p><button class="sf-btn sf-btn--success w-full" @click="emit('applyEditorPatch')">应用到当前{{ editorChatLastTurn.edit_patch.target === 'node' ? '节点' : '章节' }}</button></div>
          <div class="chat-composer chat-composer--paper"><textarea :value="editorChatInput" rows="3" placeholder="边写边聊，Ctrl+Enter 发送" @input="emit('update:editorChatInput', ($event.target as HTMLTextAreaElement).value)" @keydown.ctrl.enter.prevent="emit('sendEditorChat')" /><button class="sf-btn sf-btn--primary w-full" :disabled="editorChatLoading || !editorChatInput.trim()" @click="emit('sendEditorChat')">{{ editorChatLoading ? '思考中...' : '发送给 AI 编辑' }}</button></div>
        </section>
      </section>

      <section class="book-page book-page--right writing-right-page">
        <header class="chapter-page-header">
          <div>
            <p class="section-kicker">Manuscript</p>
            <h1>{{ chapters[activeChapter]?.title || '正文页' }}</h1>
          </div>
          <div class="chapter-page-actions"><button class="sf-btn sf-btn--success" @click="emit('startWriting')">开始写书</button><button class="sf-btn sf-btn--ghost" @click="emit('pauseWriting')">暂停</button><button class="sf-btn sf-btn--ghost" @click="emit('resumeWriting')">继续</button><button class="sf-btn sf-btn--primary" :disabled="saveLoading" @click="emit('saveChapter')">{{ saveLoading ? '保存中' : '保存本章' }}</button></div>
        </header>

        <div class="chapter-page-body">
          <div class="chapter-manuscript">
            <textarea :value="currentChapterText" class="paper-textarea paper-textarea--chapter" placeholder="这里是一章正文。每个通过审阅的节点都会写入这页。" @input="emit('update:currentChapterText', ($event.target as HTMLTextAreaElement).value)" />
            <footer class="word-footer"><span>本章 {{ currentChapterWords }} 字</span><span>全书 {{ progress.total_words || 0 }} 字</span><span>{{ stateLabel }}</span></footer>
          </div>
          <aside class="margin-notes">
            <header><p class="section-kicker">Margin Notes</p><h2>页边批注</h2><button class="sf-btn sf-btn--primary" :disabled="analysisLoading" @click="emit('analyzeCurrentText')">{{ analysisLoading ? '检查中' : '检查本章' }}</button></header>
            <article v-if="writingAnalysis" class="note-card"><h3>本章诊断</h3><p>{{ writingAnalysis.summary }}</p></article>
            <article v-for="signal in writingAnalysis?.signals || []" :key="signal.name" class="signal-card"><div class="signal-card__top"><strong>{{ signal.name }}</strong><span>{{ signal.status }} · {{ signal.score }}</span></div><div class="signal-meter"><span :style="{ width: Math.min(100, signal.score) + '%' }"></span></div><p>命中：{{ signal.hits?.join('、') || '暂无明显关键词' }}</p></article>
            <article v-if="writingAnalysis?.suggestions?.length" class="note-card note-card--warning"><h3>修改建议</h3><ul><li v-for="item in writingAnalysis.suggestions" :key="item">{{ item }}</li></ul></article>
            <article v-if="!writingAnalysis" class="paper-empty">批注固定在当前章节页边。点击“检查本章”后，情绪、钩子、爽点和矛盾会显示在这里。</article>
          </aside>
        </div>
      </section>

      <aside class="book-tabs" aria-label="章节书签">
        <button class="book-tab book-tab--toc">目录</button>
        <button v-for="(chapter, index) in chapters" :key="chapter.title" class="book-tab" :class="activeChapter === index ? 'book-tab--active' : ''" @click="emit('update:activeChapter', index)">{{ index + 1 }}</button>
        <button class="book-tab" @click="debugOpen = !debugOpen">日志</button>
      </aside>
    </div>

    <div v-if="debugOpen" class="debug-drawer">
      <div><h3>调试抽屉</h3><button class="sf-icon-btn" @click="debugOpen = false">×</button></div>
      <details><summary>生成逻辑</summary><p v-for="(item, index) in generationLogic" :key="index">{{ item }}</p></details>
      <details><summary>事件</summary><p v-for="event in latestEvents" :key="event.receivedAt + event.type">{{ event.type }} · {{ event.receivedAt }}</p></details>
      <details><summary>高级配置</summary><label>对标素材 ID<input :value="dissectSourceId" @input="emit('update:dissectSourceId', ($event.target as HTMLInputElement).value)" /></label><label><input :checked="fullAutoMode" type="checkbox" @change="emit('update:fullAutoMode', ($event.target as HTMLInputElement).checked)" /> 全自动模式：跳过节点审阅</label><button class="sf-btn sf-btn--ghost" @click="emit('exportText')">导出全文</button></details>
    </div>
  </section>
</template>
