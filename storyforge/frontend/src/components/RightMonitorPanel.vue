<script setup lang="ts">
import type { DaemonState, SseEvent } from '../api'
import type { RightTab, WritingAnalysis } from '../types'

defineProps<{
  collapsed: boolean
  tabs: RightTab[]
  activeTab: RightTab
  wordPercent: number
  chapterPercent: number
  progress: DaemonState['progress']
  targetWordCount: number
  daemonState: DaemonState
  pendingNode: Record<string, unknown> | null
  pendingNodeTitle: string
  reviewEditContent: string
  reviewInstructions: string
  generationLogic: string[]
  latestEvents: SseEvent[]
  writingAnalysis: WritingAnalysis | null
  analysisLoading: boolean
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:activeTab': [value: RightTab]
  'update:reviewEditContent': [value: string]
  'update:reviewInstructions': [value: string]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
  analyzeCurrentText: []
}>()
</script>

<template>
  <aside class="writer-side writer-side--right" :class="collapsed ? 'writer-side--collapsed' : ''">
    <button v-if="collapsed" class="side-collapse-button" @click="emit('update:collapsed', false)">检</button>
    <div v-else class="writer-side__inner">
      <header class="side-header">
        <div>
          <p class="section-kicker">Inspector</p>
          <h2>检测与监控</h2>
          <p>只保留写作时需要看的信号。</p>
        </div>
        <button class="sf-icon-btn" aria-label="收起右侧面板" @click="emit('update:collapsed', true)">›</button>
      </header>

      <nav class="inspector-tabs" aria-label="监控标签">
        <button v-for="tab in tabs" :key="tab" :class="activeTab === tab ? 'inspector-tabs__item--active' : ''" @click="emit('update:activeTab', tab)">{{ tab }}</button>
      </nav>

      <div class="inspector-scroll">
        <section v-if="activeTab === '检测'" class="inspector-stack">
          <article class="metric-card">
            <div class="metric-card__header">
              <div>
                <h3>当前文本教学检测</h3>
                <p>情绪、钩子、矛盾、爽点、信息差、代入感和角色行动。</p>
              </div>
              <button class="sf-btn sf-btn--primary" :disabled="analysisLoading" @click="emit('analyzeCurrentText')">{{ analysisLoading ? '检测中' : '检测' }}</button>
            </div>
            <p class="metric-card__body">{{ writingAnalysis?.summary || '点击检测，或编辑正文后查看当前段落信号。' }}</p>
          </article>
          <template v-if="writingAnalysis">
            <article v-for="signal in writingAnalysis.signals" :key="signal.name" class="signal-card">
              <div class="signal-card__top"><strong>{{ signal.name }}</strong><span>{{ signal.status }} · {{ signal.score }}</span></div>
              <div class="signal-meter"><span :style="{ width: Math.min(100, signal.score) + '%' }"></span></div>
              <p>命中：{{ signal.hits?.join('、') || '暂无明显关键词' }}</p>
            </article>
            <article class="note-card note-card--warning">
              <h3>修改建议</h3>
              <ul><li v-for="item in writingAnalysis.suggestions" :key="item">{{ item }}</li></ul>
            </article>
            <article class="note-card">
              <h3>关联教学资料</h3>
              <p v-for="item in writingAnalysis.guidance" :key="item.path"><strong>{{ item.title }}</strong>：{{ item.content.slice(0, 180) }}...</p>
            </article>
          </template>
        </section>

        <section v-else-if="activeTab === '监控'" class="inspector-stack">
          <article class="metric-card">
            <div class="metric-line"><span>总字数</span><strong>{{ wordPercent }}%</strong></div>
            <div class="signal-meter"><span :style="{ width: wordPercent + '%' }"></span></div>
            <div class="metric-grid"><p><strong>{{ progress.total_words }}</strong><span>/ {{ progress.target_words || targetWordCount }} 字</span></p><p><strong>{{ progress.written_chapters }}</strong><span>/ {{ progress.total_chapters }} 章 · {{ chapterPercent }}%</span></p></div>
          </article>
          <article class="note-card"><h3>伏笔台账</h3><p>待回收 {{ daemonState.foreshadowing_ledger?.still_open?.length || 0 }} / 已回收 {{ daemonState.foreshadowing_ledger?.closed_hooks?.length || 0 }}</p></article>
          <article class="note-card"><h3>错误</h3><p>{{ daemonState.errors?.join('；') || '暂无错误' }}</p></article>
        </section>

        <section v-else-if="activeTab === '审阅'" class="inspector-stack">
          <article v-if="pendingNode" class="note-card note-card--warning"><h3>正在审阅：{{ pendingNodeTitle }}</h3><p>审阅内容已合并到中间右侧的“节点草稿”。这里仅保留状态提醒，避免重复编辑框。</p></article>
          <article v-else class="note-card"><p>当前没有待审阅节点。</p></article>
        </section>

        <section v-else-if="activeTab === '生成逻辑'" class="inspector-stack">
          <article v-for="(item, index) in generationLogic" :key="index" class="note-card"><p>{{ item }}</p></article>
          <article v-if="!generationLogic.length" class="note-card"><p>等待节点生成逻辑。</p></article>
        </section>

        <section v-else class="inspector-stack">
          <article v-for="event in latestEvents" :key="event.receivedAt + event.type" class="event-card"><strong>{{ event.type }}</strong><span>{{ event.receivedAt }}</span></article>
          <article v-if="!latestEvents.length" class="note-card"><p>等待 SSE 事件。</p></article>
        </section>
      </div>
    </div>
  </aside>
</template>
