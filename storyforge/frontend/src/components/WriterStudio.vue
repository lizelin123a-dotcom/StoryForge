<script setup lang="ts">
import type { CocreationMessage, CocreationTurn, EditorSkill, NodeDraft, RightTab, WritingAnalysis } from '../types'
import type { DaemonState, NovelDetail, SseEvent } from '../api'
import LeftSettingsPanel from './LeftSettingsPanel.vue'
import ChapterEditor from './ChapterEditor.vue'
import RightMonitorPanel from './RightMonitorPanel.vue'

defineProps<{
  leftCollapsed: boolean
  rightCollapsed: boolean
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
  'update:leftCollapsed': [value: boolean]
  'update:rightCollapsed': [value: boolean]
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
</script>

<template>
  <section class="writer-studio">
    <div class="writer-studio__topbar">
      <div class="min-w-0">
        <p class="text-[11px] font-medium uppercase tracking-[0.28em] text-[var(--sf-text-faint)]">StoryForge Writer Studio</p>
        <h1 class="truncate text-lg font-semibold text-[var(--sf-text)]">{{ selectedNovel?.title || '未选择作品' }}</h1>
      </div>
      <div class="flex shrink-0 items-center gap-3 text-xs text-[var(--sf-text-muted)]">
        <span class="rounded-full border px-3 py-1" :class="stateTone">{{ stateLabel }}</span>
        <span>{{ progress.total_words || 0 }}/{{ progress.target_words || targetWordCount }} 字</span>
        <span>第 {{ activeChapter + 1 }} 章</span>
      </div>
    </div>

    <div class="writer-studio__body">
      <LeftSettingsPanel
        :collapsed="leftCollapsed"
        :setting-open="settingOpen"
        :full-auto-mode="fullAutoMode"
        :dissect-source-id="dissectSourceId"
        :editor-chat-input="editorChatInput"
        :selected-novel="selectedNovel"
        :state-tone="stateTone"
        :state-label="stateLabel"
        :writing-form="writingForm"
        :editor-chat-messages="editorChatMessages"
        :editor-chat-loading="editorChatLoading"
        :editor-chat-last-turn="editorChatLastTurn"
        :editor-skills="editorSkills"
        :selected-skill-ids="selectedSkillIds"
        @update:collapsed="emit('update:leftCollapsed', $event)"
        @update:setting-open="emit('update:settingOpen', $event)"
        @update:full-auto-mode="emit('update:fullAutoMode', $event)"
        @update:dissect-source-id="emit('update:dissectSourceId', $event)"
        @update:editor-chat-input="emit('update:editorChatInput', $event)"
        @send-editor-chat="emit('sendEditorChat')"
        @apply-editor-patch="emit('applyEditorPatch')"
        @toggle-editor-skill="emit('toggleEditorSkill', $event)"
        @start-writing="emit('startWriting')"
        @pause-writing="emit('pauseWriting')"
        @resume-writing="emit('resumeWriting')"
        @export-text="emit('exportText')"
      />
      <ChapterEditor
        :active-chapter="activeChapter"
        :current-chapter-text="currentChapterText"
        :selected-node-id="selectedNodeId"
        :current-node-text="currentNodeText"
        :chapters="chapters"
        :node-drafts="nodeDrafts"
        :save-loading="saveLoading"
        :pending-node="pendingNode"
        :pending-node-title="pendingNodeTitle"
        @update:active-chapter="emit('update:activeChapter', $event)"
        @update:current-chapter-text="emit('update:currentChapterText', $event)"
        @update:selected-node-id="emit('update:selectedNodeId', $event)"
        @update:current-node-text="emit('update:currentNodeText', $event)"
        @save-chapter="emit('saveChapter')"
        @save-node="emit('saveNode')"
        @toggle-node-lock="emit('toggleNodeLock', $event)"
        @review-decision="emit('reviewDecision', $event)"
      />
      <RightMonitorPanel
        :collapsed="rightCollapsed"
        :active-tab="activeRightTab"
        :review-edit-content="reviewEditContent"
        :review-instructions="reviewInstructions"
        :tabs="tabs"
        :word-percent="wordPercent"
        :chapter-percent="chapterPercent"
        :progress="progress"
        :target-word-count="targetWordCount"
        :daemon-state="daemonState"
        :pending-node="pendingNode"
        :pending-node-title="pendingNodeTitle"
        :generation-logic="generationLogic"
        :latest-events="latestEvents"
        :writing-analysis="writingAnalysis"
        :analysis-loading="analysisLoading"
        @update:collapsed="emit('update:rightCollapsed', $event)"
        @update:active-tab="emit('update:activeRightTab', $event)"
        @update:review-edit-content="emit('update:reviewEditContent', $event)"
        @update:review-instructions="emit('update:reviewInstructions', $event)"
        @review-decision="emit('reviewDecision', $event)"
        @analyze-current-text="emit('analyzeCurrentText')"
      />
    </div>
  </section>
</template>
