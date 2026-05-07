<script setup lang="ts">
import type { SseEvent } from '../../api'

defineProps<{
  open: boolean
  generationLogic: string[]
  latestEvents: SseEvent[]
  dissectSourceId: string
  fullAutoMode: boolean
}>()

const emit = defineEmits<{
  close: []
  'update:dissectSourceId': [value: string]
  'update:fullAutoMode': [value: boolean]
  exportText: []
  startWriting: []
  pauseWriting: []
  resumeWriting: []
  saveChapter: []
}>()
</script>

<template>
  <aside v-if="open" class="debug-drawer" aria-label="后台札记">
    <header class="debug-drawer__header">
      <div>
        <p class="section-kicker">Backstage Notes</p>
        <h3>后台札记</h3>
      </div>
      <button class="sf-icon-btn" aria-label="关闭后台札记" @click="emit('close')">×</button>
    </header>

    <div class="debug-drawer__body">
      <details class="debug-section" open>
        <summary>写作控制</summary>
        <div class="debug-form debug-form--toolbar">
          <button class="sf-btn sf-btn--success" title="开始写书" @click="emit('startWriting')">▶ 开始</button>
          <button class="sf-btn sf-btn--ghost" title="暂停" @click="emit('pauseWriting')">⏸ 暂停</button>
          <button class="sf-btn sf-btn--ghost" title="继续" @click="emit('resumeWriting')">⏵ 继续</button>
          <button class="sf-btn sf-btn--primary" title="保存本章" @click="emit('saveChapter')">💾 保存</button>
        </div>
      </details>

      <details class="debug-section">
        <summary>生成逻辑 <span>{{ generationLogic.length }}</span></summary>
        <p v-for="(item, index) in generationLogic" :key="index">{{ item }}</p>
        <p v-if="!generationLogic.length" class="debug-empty">暂无生成逻辑记录。</p>
      </details>

      <details class="debug-section">
        <summary>事件 <span>{{ latestEvents.length }}</span></summary>
        <p v-for="event in latestEvents" :key="event.receivedAt + event.type">{{ event.type }} · {{ event.receivedAt }}</p>
        <p v-if="!latestEvents.length" class="debug-empty">暂无事件。</p>
      </details>

      <details class="debug-section">
        <summary>高级配置</summary>
        <div class="debug-form">
          <label>
            对标素材 ID
            <input :value="dissectSourceId" placeholder="可选" @input="emit('update:dissectSourceId', ($event.target as HTMLInputElement).value)" />
          </label>
          <label class="debug-check">
            <input :checked="fullAutoMode" type="checkbox" @change="emit('update:fullAutoMode', ($event.target as HTMLInputElement).checked)" />
            全自动模式：跳过节点审阅
          </label>
          <button class="sf-btn sf-btn--ghost" @click="emit('exportText')">导出全文</button>
        </div>
      </details>
    </div>
  </aside>
</template>
