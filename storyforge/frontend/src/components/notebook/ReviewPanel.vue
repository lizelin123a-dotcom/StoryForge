<script setup lang="ts">
import type { NodeDraft } from '../../types'

defineProps<{
  selectedNodeId: string
  selectedNode: NodeDraft | null
  hasPendingReview: boolean
  pendingNodeTitle: string
  currentNodeText: string
}>()

const emit = defineEmits<{
  'update:currentNodeText': [value: string]
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
}>()
</script>

<template>
  <section class="review-paper">
    <template v-if="hasPendingReview">
      <div class="review-inline-meta">
        <span class="review-inline-kicker">待审</span>
        <strong>{{ pendingNodeTitle }}</strong>
        <span>先改，再写入正文。</span>
      </div>

      <textarea
        :value="currentNodeText"
        class="paper-textarea paper-textarea--node"
        placeholder="当前节点草稿会显示在这里。"
        @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)"
      />

      <div class="review-actions">
        <button class="sf-btn sf-btn--success review-actions__primary" @click="emit('reviewDecision', 'approve')">写入</button>
        <button class="sf-btn sf-btn--warning" @click="emit('reviewDecision', 'rewrite')">改后写入</button>
        <button class="sf-btn sf-btn--danger" @click="emit('reviewDecision', 'rollback')">换一版</button>
        <button v-if="selectedNode" class="sf-btn sf-btn--ghost" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁' : '锁定' }}</button>
        <button class="sf-btn sf-btn--ghost" :disabled="!selectedNodeId" @click="emit('saveNode')">保存草稿</button>
      </div>
    </template>

    <template v-else-if="selectedNode">
      <div class="review-inline-meta review-inline-meta--draft">
        <span class="review-inline-kicker">草稿</span>
        <strong>当前节点草稿</strong>
        <span>可编辑保存，不会直接写入正文。</span>
      </div>

      <textarea
        :value="currentNodeText"
        class="paper-textarea paper-textarea--node"
        placeholder="当前节点草稿会显示在这里。"
        @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)"
      />

      <div class="review-actions">
        <button class="sf-btn sf-btn--ghost" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁' : '锁定' }}</button>
        <button class="sf-btn sf-btn--ghost" @click="emit('saveNode')">保存草稿</button>
      </div>
    </template>

    <div v-else class="paper-empty review-empty">暂无待审节点。AI 生成后会贴在正文上方。</div>
  </section>
</template>
