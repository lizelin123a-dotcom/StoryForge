<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CocreationMessage, CocreationTurn, EditorSkill, NodeDraft, RightTab, WritingAnalysis } from '../types'
import type { DaemonState, NovelDetail, SseEvent } from '../api'
import DebugDrawer from './notebook/DebugDrawer.vue'
import DeskNotesPanel from './notebook/DeskNotesPanel.vue'
import EditorChatPanel from './notebook/EditorChatPanel.vue'
import ManuscriptPage from './notebook/ManuscriptPage.vue'
import NotebookPage from './notebook/NotebookPage.vue'
import NotebookSpread from './notebook/NotebookSpread.vue'
import PageTabs from './notebook/PageTabs.vue'

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
  backToBookcase: []
}>()

const debugOpen = ref(false)
const selectedNode = computed(() => props.nodeDrafts.find((node) => node.id === props.selectedNodeId) || null)
const hasPendingReview = computed(() => Boolean(props.pendingNode))
const assetEntries = computed(() => Object.entries(props.selectedNovel?.assets || {}))
</script>

<template>
  <NotebookSpread
    :daemon-status="daemonState.status"
    :save-loading="saveLoading"
    :has-novel="Boolean(selectedNovel)"
    @back="emit('backToBookcase')"
    @start-writing="emit('startWriting')"
    @pause-writing="emit('pauseWriting')"
    @resume-writing="emit('resumeWriting')"
    @save-chapter="emit('saveChapter')"
  >
    <NotebookPage side="left" class-name="writing-left-page">
      <EditorChatPanel
        :editor-chat-input="editorChatInput"
        :editor-chat-messages="editorChatMessages"
        :editor-chat-loading="editorChatLoading"
        :editor-chat-last-turn="editorChatLastTurn"
        :editor-skills="editorSkills"
        :selected-skill-ids="selectedSkillIds"
        @update:editor-chat-input="emit('update:editorChatInput', $event)"
        @send-editor-chat="emit('sendEditorChat')"
        @apply-editor-patch="emit('applyEditorPatch')"
        @toggle-editor-skill="emit('toggleEditorSkill', $event)"
      />
    </NotebookPage>

    <NotebookPage side="right" class-name="writing-right-page">
      <ManuscriptPage
        :chapters="chapters"
        :active-chapter="activeChapter"
        :current-chapter-text="currentChapterText"
        :save-loading="saveLoading"
        :progress="progress"
        :state-label="stateLabel"
        :writing-analysis="writingAnalysis"
        :analysis-loading="analysisLoading"
        :selected-node-id="selectedNodeId"
        :selected-node="selectedNode"
        :has-pending-review="hasPendingReview"
        :pending-node-title="pendingNodeTitle"
        :current-node-text="currentNodeText"
        @update:current-chapter-text="emit('update:currentChapterText', $event)"
        @update:current-node-text="emit('update:currentNodeText', $event)"
        @analyze-current-text="emit('analyzeCurrentText')"
        @save-node="emit('saveNode')"
        @toggle-node-lock="emit('toggleNodeLock', $event)"
        @review-decision="emit('reviewDecision', $event)"
      />
    </NotebookPage>

    <DeskNotesPanel
      :setting-open="settingOpen"
      :title="selectedNovel?.title || ''"
      :asset-entries="assetEntries"
      @toggle="emit('update:settingOpen', !settingOpen)"
    />

    <template #tabs>
      <PageTabs
        :chapters="chapters"
        :active-chapter="activeChapter"
        @update:active-chapter="emit('update:activeChapter', $event)"
        @toggle-debug="debugOpen = !debugOpen"
      />
    </template>

    <template #debug>
      <DebugDrawer
        :open="debugOpen"
        :generation-logic="generationLogic"
        :latest-events="latestEvents"
        :dissect-source-id="dissectSourceId"
        :full-auto-mode="fullAutoMode"
        @close="debugOpen = false"
        @update:dissect-source-id="emit('update:dissectSourceId', $event)"
        @update:full-auto-mode="emit('update:fullAutoMode', $event)"
        @export-text="emit('exportText')"
        @start-writing="emit('startWriting')"
        @pause-writing="emit('pauseWriting')"
        @resume-writing="emit('resumeWriting')"
        @save-chapter="emit('saveChapter')"
      />
    </template>
  </NotebookSpread>
</template>
