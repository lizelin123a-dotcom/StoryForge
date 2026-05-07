<script setup lang="ts">
import { ref } from 'vue'
import type { WritingCard } from '../../types'

defineProps<{
  card: WritingCard | null
}>()

const expanded = ref(false)

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
  <aside class="writing-progress-card" :class="expanded ? 'writing-progress-card--expanded' : ''">
    <button class="writing-progress-card__summary" type="button" @click="expanded = !expanded">
      <span class="writing-progress-card__kicker">写作进度</span>
      <template v-if="card">
        <strong>第 {{ card.chapter_index || 1 }} 章 · 正在写第 {{ card.node_index || 1 }} 节</strong>
        <em>{{ statusLabel[card.status] || card.status || '进行中' }}</em>
      </template>
      <strong v-else>还没有开始写作</strong>
    </button>

    <template v-if="card">
      <div class="writing-progress-card__dots" v-if="card.planned_nodes || card.nodes_total">
        <i
          v-for="index in (card.planned_nodes || card.nodes_total)"
          :key="index"
          :class="[card.completed_nodes?.includes(index) ? 'done' : '', index === card.node_index ? 'current' : '']"
        />
      </div>

      <div class="writing-progress-card__meta">
        <span>已写入 {{ card.completed_nodes?.length || 0 }} 节</span>
        <span v-if="card.planned_nodes || card.nodes_total">计划约 {{ card.planned_nodes || card.nodes_total }} 节</span>
      </div>

      <p v-if="expanded" class="writing-progress-card__detail">{{ card.next_step || '等待下一步。' }}</p>
    </template>
  </aside>
</template>
