<script setup lang="ts">
import type { GeneratedSettings } from '../api'

defineProps<{
  loading: boolean
  logline: string
  settings: GeneratedSettings | null
}>()

const emit = defineEmits<{
  'update:logline': [value: string]
  'update:settings': [value: GeneratedSettings | null]
  generate: []
  accept: []
  back: []
}>()

function patchSettings(settings: GeneratedSettings | null, key: keyof GeneratedSettings, value: unknown) {
  if (!settings) return
  emit('update:settings', { ...settings, [key]: value })
}
</script>

<template>
  <section class="frontmatter-room">
    <div class="open-book open-book--frontmatter">
      <section class="book-page book-page--left">
        <button class="paper-link" @click="emit('back')">← 回到书架</button>
        <p class="section-kicker">Frontispiece</p>
        <h1>新书扉页</h1>
        <p class="frontmatter-lead">先别急着生成一本书。把它像一颗种子一样写在扉页上，再让 AI 帮你长出案头设定。</p>
        <label class="frontmatter-field frontmatter-field--large">
          <span>一句话灵感</span>
          <textarea :value="logline" maxlength="100" placeholder="例如：姐姐厄难毒体，弟弟百毒不侵……" @input="emit('update:logline', ($event.target as HTMLTextAreaElement).value)" />
          <small>{{ logline.length }}/100</small>
        </label>
        <button class="sf-btn sf-btn--primary" :disabled="loading || !logline.trim()" @click="emit('generate')">{{ loading ? '正在誊写扉页...' : '生成案头设定' }}</button>
      </section>

      <section class="book-page book-page--right">
        <p class="section-kicker">Desk Notes</p>
        <h2>案头设定</h2>
        <div v-if="settings" class="frontmatter-form">
          <label class="frontmatter-field"><span>书名</span><input :value="settings.title" @input="patchSettings(settings, 'title', ($event.target as HTMLInputElement).value)" /></label>
          <label class="frontmatter-field"><span>类型</span><input :value="settings.genre" @input="patchSettings(settings, 'genre', ($event.target as HTMLInputElement).value)" /></label>
          <label class="frontmatter-field"><span>目标字数</span><input :value="settings.target_word_count" type="number" @input="patchSettings(settings, 'target_word_count', Number(($event.target as HTMLInputElement).value))" /></label>
          <label class="frontmatter-field"><span>世界与矛盾</span><textarea :value="settings.world_setting" @input="patchSettings(settings, 'world_setting', ($event.target as HTMLTextAreaElement).value)" /></label>
          <div class="frontmatter-characters">
            <h3>人物小传</h3>
            <article v-for="(character, index) in settings.characters" :key="index">
              <strong>{{ character.name || '未命名' }} · {{ character.role || '角色' }}</strong>
              <p>{{ character.description || '待补充' }}</p>
            </article>
          </div>
          <button class="sf-btn sf-btn--success w-full" @click="emit('accept')">把这本书放上书架</button>
        </div>
        <div v-else class="frontmatter-placeholder">
          <p>这里会出现书名、世界、人物、核心矛盾和读者期待。确认后，它会成为书架上的一本书。</p>
        </div>
      </section>
    </div>
  </section>
</template>
