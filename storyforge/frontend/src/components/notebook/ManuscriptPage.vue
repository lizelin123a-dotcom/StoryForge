<script setup lang="ts">
import { computed } from 'vue'
import type { DaemonState } from '../../api'
import type { Chapter, NodeDraft, WritingAnalysis } from '../../types'
import MarginDiagnosisStack from './MarginDiagnosisStack.vue'
import ReviewPanel from './ReviewPanel.vue'

const props = defineProps<{
  chapters: Chapter[]
  activeChapter: number
  currentChapterText: string
  saveLoading: boolean
  progress: DaemonState['progress']
  stateLabel: string
  writingAnalysis: WritingAnalysis | null
  analysisLoading: boolean
  selectedNodeId: string
  selectedNode: NodeDraft | null
  hasPendingReview: boolean
  pendingNodeTitle: string
  currentNodeText: string
  novelAssets?: Record<string, string>
  daemonState?: DaemonState
  pendingNode?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  'update:currentChapterText': [value: string]
  'update:currentNodeText': [value: string]
  analyzeCurrentText: []
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
  rewriteChapter: []
}>()

const currentChapterWords = computed(() => props.currentChapterText.length)
</script>

<template>
  <div class="chapter-page-body chapter-page-body--clean">
    <div class="chapter-manuscript-stack">
      <ReviewPanel
        class="review-paper--inline"
        :selected-node-id="selectedNodeId"
        :selected-node="selectedNode"
        :has-pending-review="hasPendingReview"
        :pending-node-title="pendingNodeTitle"
        :current-node-text="currentNodeText"
        @update:current-node-text="emit('update:currentNodeText', $event)"
        @save-node="emit('saveNode')"
        @toggle-node-lock="emit('toggleNodeLock', $event)"
        @review-decision="emit('reviewDecision', $event)"
        @rewrite-chapter="emit('rewriteChapter')"
      />

      <div class="chapter-editor-fill">
        <textarea
          :value="currentChapterText"
          class="paper-textarea paper-textarea--chapter"
          placeholder="正文从这里开始。"
          @input="emit('update:currentChapterText', ($event.target as HTMLTextAreaElement).value)"
        />
      </div>

      <footer class="word-footer">
        <span>本章 {{ currentChapterWords }} 字</span>
        <span>全书 {{ progress.total_words || 0 }} 字</span>
        <span>{{ stateLabel }}</span>
      </footer>
    </div>

    <MarginDiagnosisStack
      :writing-analysis="writingAnalysis"
      :analysis-loading="analysisLoading"
      :novel-assets="novelAssets"
      :daemon-state="daemonState"
      :active-chapter="activeChapter"
      :selected-node="selectedNode"
      :pending-node="pendingNode"
      @analyze-current-text="emit('analyzeCurrentText')"
    />
  </div>
</template>
