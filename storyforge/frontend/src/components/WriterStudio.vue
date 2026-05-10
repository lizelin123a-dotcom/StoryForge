<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CocreationMessage, CocreationTurn, EditorSkill, NodeDraft, RightTab, WritingAnalysis, WritingCard } from '../types'
import type { DaemonState, NovelDetail, SseEvent } from '../api'
import DebugDrawer from './notebook/DebugDrawer.vue'
import DeskNotesPanel from './notebook/DeskNotesPanel.vue'
import EditorChatPanel from './notebook/EditorChatPanel.vue'
import ManuscriptPage from './notebook/ManuscriptPage.vue'
import NotebookPage from './notebook/NotebookPage.vue'
import NotebookSpread from './notebook/NotebookSpread.vue'
import PageTabs from './notebook/PageTabs.vue'
import WritingProgressCard from './notebook/WritingProgressCard.vue'

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
    planningModel: string
    writingModel: string
    writingApiKey: string
    writingApiBaseUrl: string
    reviewModel: string
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
  exportChapter: [index: number]
  saveChapter: []
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
  rewriteChapter: []
  regenerateOutline: []
  rollbackNode: [reason: string]
  analyzeCurrentText: []
  backToBookcase: []
  saveDeskAsset: [key: string, value: string]
}>()

const debugOpen = ref(false)
const selectedNode = computed(() => props.nodeDrafts.find((node) => node.id === props.selectedNodeId) || null)
const hasPendingReview = computed(() => Boolean(props.pendingNode))
const assetEntries = computed(() => Object.entries(props.selectedNovel?.assets || {}))
const writingCard = computed(() => (props.daemonState.writing_card as WritingCard | undefined) || null)
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
      <WritingProgressCard :card="writingCard" />
      <EditorChatPanel
        :editor-chat-input="editorChatInput"
        :editor-chat-messages="editorChatMessages"
        :editor-chat-loading="editorChatLoading"
        :editor-chat-last-turn="editorChatLastTurn"
        :editor-skills="editorSkills"
        :selected-skill-ids="selectedSkillIds"
        :writing-form="writingForm"
        :full-auto-mode="fullAutoMode"
        @update:editor-chat-input="emit('update:editorChatInput', $event)"
        @send-editor-chat="emit('sendEditorChat')"
        @apply-editor-patch="emit('applyEditorPatch')"
        @toggle-editor-skill="emit('toggleEditorSkill', $event)"
        @update:full-auto-mode="emit('update:fullAutoMode', $event)"
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
        :review-instructions="reviewInstructions"
        :pending-node="pendingNode"
        :novel-assets="selectedNovel?.assets || {}"
        :daemon-state="daemonState"
        @update:current-chapter-text="emit('update:currentChapterText', $event)"
        @update:current-node-text="emit('update:currentNodeText', $event)"
        @update:review-instructions="emit('update:reviewInstructions', $event)"
        @analyze-current-text="emit('analyzeCurrentText')"
        @save-node="emit('saveNode')"
        @toggle-node-lock="emit('toggleNodeLock', $event)"
        @review-decision="emit('reviewDecision', $event)"
        @rewrite-chapter="emit('rewriteChapter')"
        @regenerate-outline="emit('regenerateOutline')"
        @rollback-node="emit('rollbackNode', $event)"
      />
    </NotebookPage>

    <DeskNotesPanel
      :setting-open="settingOpen"
      :title="selectedNovel?.title || ''"
      :asset-entries="assetEntries"
      @toggle="emit('update:settingOpen', !settingOpen)"
      @save-asset="(key, value) => emit('saveDeskAsset', key, value)"
    />

    <template #tabs>
      <PageTabs
        :chapters="chapters"
        :active-chapter="activeChapter"
        @update:active-chapter="emit('update:activeChapter', $event)"
        @download-chapter="emit('exportChapter', $event)"
        @download-book="emit('exportText')"
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
