<script setup lang="ts">
import type { Chapter } from '../../types'

defineProps<{
  chapters: Chapter[]
  activeChapter: number
}>()

const emit = defineEmits<{
  'update:activeChapter': [value: number]
  toggleDebug: []
  downloadChapter: [index: number]
  downloadBook: []
}>()
</script>

<template>
  <aside class="book-tabs" aria-label="章节书签和下载">
    <div class="book-tabs__group book-tabs__group--chapters">
      <button
        v-for="(chapter, index) in chapters"
        :key="chapter.title"
        class="book-tab book-tab--chapter"
        :class="activeChapter === index ? 'book-tab--active' : ''"
        :title="chapter.title || `第 ${index + 1} 章`"
        @click="emit('update:activeChapter', index)"
      >
        {{ index + 1 }}
      </button>
    </div>

    <div class="book-tabs__group book-tabs__group--downloads">
      <button class="book-tab book-tab--download" title="下载当前章节" :disabled="!chapters.length" @click="emit('downloadChapter', activeChapter)">章</button>
      <button class="book-tab book-tab--download" title="下载全本正文" :disabled="!chapters.length" @click="emit('downloadBook')">全</button>
    </div>

    <button class="book-tab book-tab--log" title="后台日志" @click="emit('toggleDebug')">志</button>
  </aside>
</template>
