<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

const props = defineProps<{
  settingOpen: boolean
  title: string
  assetEntries: [string, string][]
}>()

const emit = defineEmits<{
  toggle: []
  saveAsset: [key: string, value: string]
}>()

const editing = reactive<Record<string, boolean>>({})
const drafts = reactive<Record<string, string>>({})
const newKey = ref('')
const newValue = ref('')

watch(
  () => props.assetEntries,
  (entries) => {
    entries.forEach(([key, value]) => {
      if (!(key in drafts) || !editing[key]) drafts[key] = value
    })
  },
  { immediate: true },
)

function startEdit(key: string, value: string) {
  drafts[key] = value
  editing[key] = true
}

function cancelEdit(key: string, value: string) {
  drafts[key] = value
  editing[key] = false
}

function saveExisting(key: string) {
  emit('saveAsset', key, drafts[key] || '')
  editing[key] = false
}

function addAsset() {
  const key = newKey.value.trim()
  const value = newValue.value.trim()
  if (!key || !value) return
  emit('saveAsset', key, value)
  newKey.value = ''
  newValue.value = ''
}
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

      <div v-if="assetEntries.length" class="desk-note-grid desk-note-grid--editable">
        <article v-for="([key, value]) in assetEntries" :key="key" class="desk-note-card">
          <div class="desk-note-card__head">
            <strong>{{ key }}</strong>
            <button v-if="!editing[key]" class="sf-btn sf-btn--ghost" @click="startEdit(key, value)">编辑</button>
          </div>

          <template v-if="editing[key]">
            <textarea
              v-model="drafts[key]"
              class="paper-textarea desk-note-editor"
              spellcheck="false"
              placeholder="直接改这里。你写的版本会覆盖 AI 的理解。"
            />
            <div class="review-actions desk-note-actions">
              <button class="sf-btn sf-btn--success" @click="saveExisting(key)">保存</button>
              <button class="sf-btn sf-btn--ghost" @click="cancelEdit(key, value)">取消</button>
            </div>
          </template>

          <span v-else>{{ value }}</span>
        </article>
      </div>
      <div v-else class="paper-empty">还没有沉淀设定。你可以直接在下面新增，也可以和 AI 编辑聊几轮。</div>

      <section class="desk-note-add">
        <p class="section-kicker">Manual Note</p>
        <strong>手动新增设定</strong>
        <input v-model="newKey" class="paper-input" placeholder="设定名，比如：主角底线" />
        <textarea v-model="newValue" class="paper-textarea desk-note-editor" placeholder="写下你确认的设定。这里以你为准。" />
        <button class="sf-btn sf-btn--primary" :disabled="!newKey.trim() || !newValue.trim()" @click="addAsset">加入案头</button>
      </section>
    </div>
  </aside>
</template>
