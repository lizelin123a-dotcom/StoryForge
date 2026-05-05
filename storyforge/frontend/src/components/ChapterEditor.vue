<script setup lang="ts">
import { computed } from 'vue'
import type { Chapter, NodeDraft } from '../types'

const props = defineProps<{
  chapters: Chapter[]
  activeChapter: number
  currentChapterText: string
  nodeDrafts: NodeDraft[]
  selectedNodeId: string
  currentNodeText: string
  saveLoading: boolean
  pendingNode: Record<string, unknown> | null
  pendingNodeTitle: string
}>()

const selectedNode = computed(() => props.nodeDrafts.find((node) => node.id === props.selectedNodeId) || null)
const hasPendingReview = computed(() => Boolean(props.pendingNode))

const emit = defineEmits<{
  'update:activeChapter': [value: number]
  'update:currentChapterText': [value: string]
  'update:selectedNodeId': [value: string]
  'update:currentNodeText': [value: string]
  saveChapter: []
  saveNode: []
  toggleNodeLock: [node: NodeDraft]
  reviewDecision: [action: 'approve' | 'rewrite' | 'rollback']
}>()
</script>

<template>
  <section class="writer-desk">
    <header class="writer-desk__chapters">
      <div v-if="chapters.length" class="chapter-strip" aria-label="章节列表">
        <button v-for="(chapter, index) in chapters" :key="chapter.title" class="chapter-pill" :class="activeChapter === index ? 'chapter-pill--active' : ''" @click="emit('update:activeChapter', index)">
          <span>{{ chapter.title }}</span>
          <span v-if="chapter.dirty" class="chapter-pill__dirty">●</span>
        </button>
      </div>
      <p v-else class="text-sm text-[var(--sf-text-faint)]">尚未开始写作</p>
      <button class="sf-btn sf-btn--primary shrink-0" :disabled="saveLoading || !chapters.length" @click="emit('saveChapter')">{{ saveLoading ? '保存中' : '保存章节' }}</button>
    </header>

    <div class="writer-desk__body">
      <main class="manuscript-panel" aria-label="章节正文编辑区">
        <div v-if="chapters.length" class="manuscript-card">
          <textarea :value="currentChapterText" class="manuscript-textarea" placeholder="章节正文会在这里沉淀。通过审阅的节点才会进入正文。" @input="emit('update:currentChapterText', ($event.target as HTMLTextAreaElement).value)" />
        </div>
        <div v-else class="manuscript-empty">尚未开始写作。点击左侧“启动写作”后，章节正文会在这里展开。</div>
      </main>

      <aside class="node-board" aria-label="节点草稿与审阅">
        <header class="node-board__header">
          <div>
            <p class="section-kicker">Draft Review</p>
            <h2>节点草稿</h2>
            <p>节点草稿就是审阅稿，通过后写入正文。</p>
          </div>
          <button class="sf-btn sf-btn--ghost" :disabled="!selectedNodeId" @click="emit('saveNode')">保存</button>
        </header>

        <div class="node-list" aria-label="当前章节节点">
          <button v-for="node in nodeDrafts" :key="node.id" class="node-card" :class="selectedNodeId === node.id ? 'node-card--active' : ''" @click="emit('update:selectedNodeId', node.id)">
            <span class="node-card__meta">节点 {{ node.node_index }} · {{ node.node_type }}</span>
            <span class="node-card__badge" :class="node.locked ? 'node-card__badge--locked' : ''">{{ node.locked ? '已锁定' : '草稿' }}</span>
            <span class="node-card__preview">{{ node.content || '空节点' }}</span>
          </button>
          <p v-if="!nodeDrafts.length" class="node-empty">这一章还没有节点草稿。AI 生成后会沉淀在这里。</p>
        </div>

        <section class="node-editor" aria-label="当前节点编辑器">
          <template v-if="selectedNodeId">
            <div v-if="hasPendingReview" class="review-banner">
              <strong>待审阅：{{ pendingNodeTitle }}</strong>
              <span>直接改下面这份稿。通过后才会写入正文。</span>
            </div>
            <textarea :value="currentNodeText" class="node-textarea" placeholder="选择节点后在这里编辑草稿。" @input="emit('update:currentNodeText', ($event.target as HTMLTextAreaElement).value)" />
            <div v-if="hasPendingReview" class="review-actions">
              <button class="sf-btn sf-btn--success review-actions__primary" @click="emit('reviewDecision', 'approve')">通过并写入正文</button>
              <button class="sf-btn sf-btn--warning" @click="emit('reviewDecision', 'rewrite')">修改后通过</button>
              <button class="sf-btn sf-btn--danger" @click="emit('reviewDecision', 'rollback')">回滚节点</button>
            </div>
            <button v-if="selectedNode" class="sf-btn sf-btn--ghost w-full" @click="emit('toggleNodeLock', selectedNode)">{{ selectedNode.locked ? '解锁该节点' : '锁定该节点' }}</button>
          </template>
          <div v-else class="node-editor__empty">选中一个节点，开始审阅或微调。</div>
        </section>
      </aside>
    </div>

    <footer class="writer-desk__footer">
      <span>节点 {{ chapters[activeChapter]?.nodesDone || 0 }}/{{ chapters[activeChapter]?.nodesTotal || 0 }}</span>
      <span>{{ chapters[activeChapter]?.nodeLabel || '尚未开始' }}</span>
    </footer>
  </section>
</template>
