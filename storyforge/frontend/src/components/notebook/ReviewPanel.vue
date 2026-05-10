<script setup lang="ts">
import type { NodeDraft } from '../../types'

defineProps<{
  selectedNodeId: string
  selectedNode: NodeDraft | null
  hasPendingReview: boolean
  pendingNodeTitle: string
  currentNodeText: string
  reviewInstructions: string
}>()

const emit = defineEmits<{
  'update:currentNodeText': [value: string]
  'update:reviewInstructions': [value: string]
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
  rewriteChapter: []
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

      <div class="review-reason-row">
        <button class="reason-chip" @click="emit('update:reviewInstructions', '文风不对：不要文艺氛围，写动作、对话、冲突')">文风</button>
        <button class="reason-chip" @click="emit('update:reviewInstructions', '节奏太慢：开头给冲突，每段推进压迫或反击')">节奏</button>
        <button class="reason-chip" @click="emit('update:reviewInstructions', '角色行为不对：主角要主动选择和反压，不要被动观察')">角色</button>
        <button class="reason-chip" @click="emit('update:reviewInstructions', '章纲目标不对：校正本节点剧情方向，不要沿用上一版重心')">章纲</button>
        <button class="reason-chip" @click="emit('update:reviewInstructions', '重复上一版：换开头、换场景调度、换信息顺序')">重复</button>
      </div>
      <input
        :value="reviewInstructions"
        class="review-instruction-input"
        placeholder="换一版原因，可不填。例：主角太被动，直接逼对方接退婚书"
        @input="emit('update:reviewInstructions', ($event.target as HTMLInputElement).value)"
      />

      <div class="review-actions review-actions--top">
        <button class="sf-btn sf-btn--danger" title="清空本章正文和已通过小节，从第 1 节重来" @click="emit('rewriteChapter')">重写本章</button>
        <button class="sf-btn sf-btn--success review-actions__primary" @click="emit('reviewDecision', 'approve')">写入</button>
        <button class="sf-btn sf-btn--warning" @click="emit('reviewDecision', 'rewrite')">改后写入</button>
        <button class="sf-btn sf-btn--danger" @click="emit('reviewDecision', 'rollback')">换一版</button>
        <button v-if="selectedNode" class="sf-btn sf-btn--ghost" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁' : '锁定' }}</button>
        <button class="sf-btn sf-btn--ghost" :disabled="!selectedNodeId" @click="emit('saveNode')">保存草稿</button>
      </div>

      <textarea
        :value="currentNodeText"
        class="paper-textarea paper-textarea--node"
        placeholder="当前节点草稿会显示在这里。"
        @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)"
      />
    </template>

    <template v-else-if="selectedNode">
      <div class="review-inline-meta review-inline-meta--draft">
        <span class="review-inline-kicker">草稿</span>
        <strong>当前节点草稿</strong>
        <span>可编辑保存，不会直接写入正文。</span>
      </div>

      <div class="review-actions review-actions--top">
        <button class="sf-btn sf-btn--danger" title="清空本章正文和已通过小节，从第 1 节重来" @click="emit('rewriteChapter')">重写本章</button>
        <button class="sf-btn sf-btn--ghost" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁' : '锁定' }}</button>
        <button class="sf-btn sf-btn--ghost" @click="emit('saveNode')">保存草稿</button>
      </div>

      <textarea
        :value="currentNodeText"
        class="paper-textarea paper-textarea--node"
        placeholder="当前节点草稿会显示在这里。"
        @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)"
      />
    </template>

    <div v-else class="paper-empty review-empty">
      <span>暂无待审节点。AI 生成后会贴在正文上方。</span>
      <button class="sf-btn sf-btn--danger" title="清空本章正文和已通过小节，从第 1 节重来" @click="emit('rewriteChapter')">重写本章</button>
    </div>
  </section>
</template>
