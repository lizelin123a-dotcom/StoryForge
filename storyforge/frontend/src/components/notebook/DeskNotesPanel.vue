<script setup lang="ts">
defineProps<{
  settingOpen: boolean
  title: string
  assetEntries: [string, string][]
}>()

const emit = defineEmits<{
  toggle: []
}>()
</script>

<template>
  <aside class="desk-notes-drawer" :class="settingOpen ? 'desk-notes-drawer--open' : ''">
    <button class="desk-notes-tab" @click="emit('toggle')">案头</button>
    <div v-if="settingOpen" class="desk-notes-sheet">
      <header>
        <p class="section-kicker">Desk Notes</p>
        <h2>案头设定</h2>
        <p>{{ title || '未选择作品' }}</p>
      </header>
      <div v-if="assetEntries.length" class="desk-note-grid">
        <article v-for="([key, value]) in assetEntries" :key="key">
          <strong>{{ key }}</strong>
          <span>{{ value }}</span>
        </article>
      </div>
      <div v-else class="paper-empty">还没有沉淀设定。和 AI 编辑聊几轮，确认的信息会写到这里。</div>
    </div>
  </aside>
</template>
