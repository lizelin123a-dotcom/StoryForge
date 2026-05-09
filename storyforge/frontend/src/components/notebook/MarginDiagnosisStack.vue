<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DaemonState } from '../../api'
import type { NodeDraft, WritingAnalysis } from '../../types'

const props = defineProps<{
  writingAnalysis: WritingAnalysis | null
  analysisLoading: boolean
  novelAssets?: Record<string, string>
  daemonState?: DaemonState
  activeChapter?: number
  selectedNode?: NodeDraft | null
  pendingNode?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  analyzeCurrentText: []
}>()

const reviewOpen = ref(false)
const outlineOpen = ref(true)
const bookOutlineOpen = ref(false)

const assets = computed(() => props.novelAssets || {})
const currentFocus = computed(() => parseAssetObject(assets.value.current_focus))
const hooks = computed(() => parseAssetList(assets.value.hooks))
const chapterSummaries = computed(() => parseAssetList(assets.value.chapter_summaries))
const writingCard = computed(() => (props.daemonState?.writing_card || {}) as Record<string, unknown>)
const manualReview = computed(() => (props.daemonState?.manual_review || {}) as Record<string, unknown>)
const rewriteInstruction = computed(() => textOf(manualReview.value.instructions).split('\n')[0])
const lastRejected = computed(() => parseAssetObject(manualReview.value.last_rejected))
const runtimeMemory = computed(() => (props.daemonState?.runtime_memory || {}) as Record<string, unknown>)
const currentOutline = computed(() => parseOutline(props.daemonState?.current_chapter_outline))
const outlineOverride = computed(() => textOf(assets.value[`chapter_outline:${props.activeChapter || 1}`]) || textOf((currentOutline.value as Record<string, unknown>).override_text))
const macroOutline = computed(() => parseOutline(props.daemonState?.macro_outline))
const actPlans = computed(() => Array.isArray(props.daemonState?.act_plans) ? props.daemonState?.act_plans as unknown[] : [])

const bookOutlineItems = computed(() => {
  const macroActs = Array.isArray(macroOutline.value.acts) ? macroOutline.value.acts as unknown[] : []
  const fromActs = actPlans.value.length ? actPlans.value : macroActs
  return fromActs.map((item, index) => {
    const row = item as Record<string, unknown>
    const title = textOf(row.title) || textOf(row.name) || textOf(row.act_name) || `第 ${index + 1} 卷`
    const summary = textOf(row.summary) || textOf(row.core_conflict) || textOf(row.goal) || textOf(row.description)
    const chapters = Array.isArray(row.chapters) ? row.chapters.length : Number(row.chapter_count || 0)
    return { title, summary, chapters }
  }).filter((item) => item.title || item.summary)
})

const outlineNodes = computed(() => {
  const fromState = Array.isArray(currentOutline.value.nodes) ? currentOutline.value.nodes : []
  const nodes = fromState.map((node) => node as Record<string, unknown>).filter(Boolean)
  if (nodes.length) return nodes
  const pending = props.pendingNode || {}
  if (textOf(pending.node_index) || textOf(pending.what_to_write) || textOf(pending.trigger_point)) {
    return [{
      index: textOf(pending.node_index) || textOf(writingCard.value.node_index) || '1',
      node_type: textOf(pending.node_type) || textOf(writingCard.value.status) || '当前节点',
      what_to_write: textOf(pending.what_to_write) || textOf(pending.trigger_point) || textOf(pending.reader_expectation) || textOf(writingCard.value.next_step),
    }]
  }
  return []
})

const chapterGoalLine = computed(() => {
  const pending = props.pendingNode || {}
  const outline = currentOutline.value
  const chapterFunction = textOf(outline.chapter_function) || textOf((outline.outline as Record<string, unknown> | undefined)?.chapter_function)
  const currentNodeTask = textOf(pending.what_to_write) || textOf(pending.trigger_point) || textOf(pending.reader_expectation)
  const fallback = textOf(currentFocus.value.priority) || textOf(writingCard.value.next_step)
  return currentNodeTask || chapterFunction || fallback || '暂无章纲，先生成本章节点。'
})

const currentNodeLine = computed(() => {
  const pending = props.pendingNode || {}
  const nodeType = textOf(pending.node_type) || props.selectedNode?.node_type || textOf(writingCard.value.status)
  const nodeIndex = textOf(pending.node_index) || String(props.selectedNode?.node_index || writingCard.value.node_index || '')
  return nodeType ? `${nodeType}${nodeIndex ? ` · 第 ${nodeIndex} 节` : ''}` : ''
})

const readerExpectations = computed(() => {
  const focus = currentFocus.value
  const fromFocus = asStringList(focus.active_subplots)
  const fromRuntime = asStringList((runtimeMemory.value as Record<string, unknown>).facts).map((item) => compactObjectText(item))
  const pending = props.pendingNode || {}
  const fromPending = [textOf(pending.reader_expectation)].filter(Boolean)
  return [...fromPending, ...fromFocus, ...fromRuntime].filter(Boolean).slice(0, 3)
})

const hookItems = computed(() => {
  const focusHooks = asStringList(currentFocus.value.hooks_to_mention)
  const assetHooks = hooks.value.map((hook) => compactObjectText(hook)).filter(Boolean)
  return [...focusHooks, ...assetHooks].filter(Boolean).slice(0, 3)
})

const characterNotes = computed(() => {
  const raw = assets.value['角色关系'] || assets.value.characters || assets.value.character_states || assets.value['主角欲望'] || ''
  if (!raw) return []
  return splitLines(String(raw)).slice(0, 3)
})

const chapterEndHook = computed(() => {
  const focus = currentFocus.value
  const constraints = asStringList(focus.constraints)
  const pacing = textOf(focus.pacing_intent)
  const firstHook = hookItems.value[0]
  const pending = props.pendingNode || {}
  const nodeEnd = textOf(pending.ends_with)
  return [nodeEnd, pacing, firstHook ? `牵住：${firstHook}` : '', ...constraints].filter(Boolean).slice(0, 3)
})

const recentSummaries = computed(() => {
  const fromAsset = chapterSummaries.value.map((item) => compactObjectText(item)).filter(Boolean)
  const fromState = asStringList(props.daemonState?.chapter_summaries).filter(Boolean)
  return [...fromAsset, ...fromState].slice(-2)
})

function parseOutline(value: unknown): Record<string, unknown> {
  if (!value) return {}
  if (typeof value === 'object') return value as Record<string, unknown>
  try {
    const parsed = JSON.parse(String(value))
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {}
  } catch {
    return {}
  }
}

function parseAssetObject(value: unknown): Record<string, unknown> {
  if (!value) return {}
  if (typeof value === 'object') return value as Record<string, unknown>
  try {
    const parsed = JSON.parse(String(value))
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {}
  } catch {
    return {}
  }
}

function parseAssetList(value: unknown): unknown[] {
  if (!value) return []
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(String(value))
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return splitLines(String(value))
  }
}

function asStringList(value: unknown): string[] {
  if (!value) return []
  if (Array.isArray(value)) return value.map((item) => compactObjectText(item)).filter(Boolean)
  if (typeof value === 'string') return splitLines(value)
  return [compactObjectText(value)].filter(Boolean)
}

function compactObjectText(value: unknown): string {
  if (!value) return ''
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'object') {
    const row = value as Record<string, unknown>
    return String(row.what_to_write || row.trigger_point || row.description || row.summary || row.text || row.chapter_summary || row.reader_expectation || row.priority || JSON.stringify(row, null, 0)).trim()
  }
  return String(value).trim()
}

function splitLines(value: string): string[] {
  return value.split(/\n|；|;/).map((item) => item.trim()).filter(Boolean)
}

function textOf(value: unknown): string {
  return typeof value === 'string' ? value.trim() : value == null ? '' : String(value).trim()
}
</script>

<template>
  <aside class="margin-notes margin-notes--writing margin-notes--compact">
    <header class="margin-compact-head">
      <div class="margin-title-row">
        <h2>案边提示</h2>
        <button class="sf-btn sf-btn--primary" :disabled="analysisLoading" @click="emit('analyzeCurrentText'); reviewOpen = true">
          {{ analysisLoading ? '检查中' : '红笔审稿' }}
        </button>
      </div>
      <p class="chapter-goal-line" :title="chapterGoalLine">本章：{{ chapterGoalLine }}</p>
      <p v-if="currentNodeLine" class="chapter-goal-line chapter-goal-line--muted">当前：{{ currentNodeLine }}</p>
    </header>

    <section class="outline-panel note-card note-card--compact">
      <button class="outline-panel__title" @click="bookOutlineOpen = !bookOutlineOpen">
        <strong>全书大纲</strong>
        <span>{{ bookOutlineItems.length ? `${bookOutlineItems.length} 段` : '暂无' }}</span>
      </button>
      <ol v-if="bookOutlineOpen && bookOutlineItems.length" class="outline-list">
        <li v-for="item in bookOutlineItems" :key="item.title">
          <span>{{ item.title }}{{ item.chapters ? ` · ${item.chapters} 章` : '' }}</span>
          <p>{{ item.summary || '暂无概述' }}</p>
        </li>
      </ol>
      <p v-else-if="bookOutlineOpen" class="muted-line">大纲生成后会显示在这里。</p>
    </section>

    <section class="outline-panel note-card note-card--compact">
      <button class="outline-panel__title" @click="outlineOpen = !outlineOpen">
        <strong>当前章纲</strong>
        <span>{{ outlineNodes.length ? `${outlineNodes.length} 节` : '暂无' }}</span>
      </button>
      <p v-if="outlineOpen && outlineOverride" class="outline-override-text">{{ outlineOverride }}</p>
      <ol v-if="outlineOpen && !outlineOverride && outlineNodes.length" class="outline-list">
        <li v-for="node in outlineNodes" :key="String(node.index || node.node_index)">
          <span>第 {{ textOf(node.index || node.node_index) }} 节</span>
          <p>{{ textOf(node.what_to_write) || textOf(node.trigger_point) || textOf(node.reader_expectation) || textOf(node.node_type) }}</p>
        </li>
      </ol>
      <p v-else-if="outlineOpen && !outlineOverride" class="muted-line">完整章纲还没同步到前端。新生成或重写本章后会显示全部小节。</p>
    </section>

    <article v-if="rewriteInstruction || textOf(lastRejected.reason)" class="note-card note-card--warning note-card--compact">
      <h3>本轮改写要求</h3>
      <p>{{ rewriteInstruction || textOf(lastRejected.reason) }}</p>
      <p v-if="textOf(lastRejected.content)" class="muted-line">已拒绝上一版，下一版会避开其写法。</p>
    </article>

    <article class="note-card note-card--compact">
      <h3>当前伏笔</h3>
      <ul v-if="hookItems.length">
        <li v-for="item in hookItems" :key="item">{{ item }}</li>
      </ul>
      <p v-else>暂无明确伏笔。</p>
    </article>

    <article class="note-card note-card--compact">
      <h3>角色此刻状态</h3>
      <ul v-if="characterNotes.length">
        <li v-for="item in characterNotes" :key="item">{{ item }}</li>
      </ul>
      <p v-else>案头里还没有可用的角色状态。</p>
    </article>

    <article class="note-card note-card--compact">
      <h3>读者正在等什么</h3>
      <ul v-if="readerExpectations.length">
        <li v-for="item in readerExpectations" :key="item">{{ item }}</li>
      </ul>
      <p v-else>还没有沉淀读者期待。</p>
    </article>

    <article class="note-card note-card--warning note-card--compact">
      <h3>章尾要吊在哪里</h3>
      <ul v-if="chapterEndHook.length">
        <li v-for="item in chapterEndHook" :key="item">{{ item }}</li>
      </ul>
      <p v-else>至少留下一个新目标、异常细节或未解问题。</p>
    </article>

    <article v-if="recentSummaries.length" class="note-card note-card--compact">
      <h3>近章记忆</h3>
      <ul>
        <li v-for="item in recentSummaries" :key="item">{{ item }}</li>
      </ul>
    </article>

    <section class="review-diagnosis" :class="reviewOpen || writingAnalysis ? 'review-diagnosis--open' : ''">
      <button class="sf-btn sf-btn--ghost w-full" @click="reviewOpen = !reviewOpen">
        {{ reviewOpen || writingAnalysis ? '收起红笔诊断' : '展开红笔诊断' }}
      </button>

      <template v-if="reviewOpen || writingAnalysis">
        <article v-if="writingAnalysis" class="note-card diagnosis-summary-card note-card--compact">
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

          <article v-if="writingAnalysis.suggestions?.length" class="note-card note-card--warning note-card--compact">
            <h3>修改建议</h3>
            <ul>
              <li v-for="item in writingAnalysis.suggestions" :key="item">{{ item }}</li>
            </ul>
          </article>
        </template>

        <div v-else class="paper-empty">写完一段后点“红笔审稿”。</div>
      </template>
    </section>
  </aside>
</template>
