<script setup lang="ts">
import type { WritingAnalysis } from '../../types'

defineProps<{
  writingAnalysis: WritingAnalysis | null
  analysisLoading: boolean
}>()

const emit = defineEmits<{
  analyzeCurrentText: []
}>()

const defaultSignals = [
  { name: '情绪', hint: '等待检测情绪浓度与代入感。' },
  { name: '钩子', hint: '等待检测悬念、期待和信息差。' },
  { name: '爽点', hint: '等待检测兑现、压迫与反击节奏。' },
  { name: '矛盾', hint: '等待检测冲突是否清晰推进。' },
]
</script>

<template>
  <aside class="margin-notes">
    <header>
      <p class="section-kicker">Margin Notes</p>
      <h2>页边批注</h2>
      <button class="sf-btn sf-btn--primary" :disabled="analysisLoading" @click="emit('analyzeCurrentText')">
        {{ analysisLoading ? '检查中' : '检查本章' }}
      </button>
    </header>

    <article v-if="writingAnalysis" class="note-card diagnosis-summary-card">
      <h3>本章诊断</h3>
      <p>{{ writingAnalysis.summary }}</p>
    </article>

    <template v-if="writingAnalysis">
      <article v-for="signal in writingAnalysis.signals || []" :key="signal.name" class="signal-card">
        <div class="signal-card__top">
          <strong>{{ signal.name }}</strong>
          <span>{{ signal.status }} · {{ signal.score }}</span>
        </div>
        <div class="signal-meter"><span :style="{ width: Math.min(100, signal.score) + '%' }"></span></div>
        <p>命中：{{ signal.hits?.join('、') || '暂无明显关键词' }}</p>
      </article>

      <article v-if="writingAnalysis.suggestions?.length" class="note-card note-card--warning">
        <h3>修改建议</h3>
        <ul>
          <li v-for="item in writingAnalysis.suggestions" :key="item">{{ item }}</li>
        </ul>
      </article>
    </template>

    <template v-else>
      <article v-for="item in defaultSignals" :key="item.name" class="signal-card signal-card--empty">
        <div class="signal-card__top">
          <strong>{{ item.name }}</strong>
          <span>待检测</span>
        </div>
        <div class="signal-meter"><span style="width: 0%"></span></div>
        <p>{{ item.hint }}</p>
      </article>
    </template>
  </aside>
</template>
