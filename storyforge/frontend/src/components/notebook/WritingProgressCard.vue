<script setup lang="ts">
import type { WritingCard } from '../../types'

defineProps<{
  card: WritingCard | null
}>()

const statusLabel: Record<string, string> = {
  idle: '待开始',
  chapter_planning: '拆章节',
  writing: '写作中',
  node_writing: '写小节',
  node_review: '等你审',
  node_approved: '已写入',
  chapter_review: '查本章',
  chapter_completed: '已归档',
}
</script>

<template>
  <aside class="writing-progress-card">
    <p class="writing-progress-card__kicker">写作进度卡</p>
    <template v-if="card">
      <div class="writing-progress-card__main">
        <strong>第 {{ card.chapter_index || 1 }} 章</strong>
        <span>{{ statusLabel[card.status] || card.status || '进行中' }}</span>
      </div>
      <div class="writing-progress-card__node">
        <span>当前小节</span>
        <strong>{{ card.node_index || 1 }} / {{ card.nodes_total || '?' }}</strong>
      </div>
      <div class="writing-progress-card__dots" v-if="card.nodes_total">
        <i
          v-for="index in card.nodes_total"
          :key="index"
          :class="[card.completed_nodes?.includes(index) ? 'done' : '', index === card.node_index ? 'current' : '']"
        />
      </div>
      <p>{{ card.next_step || '等待下一步。' }}</p>
    </template>
    <p v-else>还没有开始写作。</p>
  </aside>
</template>
