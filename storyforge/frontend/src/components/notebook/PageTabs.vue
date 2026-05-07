<script setup lang="ts">
import type { Chapter } from '../../types'

defineProps<{
  chapters: Chapter[]
  activeChapter: number
}>()

const emit = defineEmits<{
  'update:activeChapter': [value: number]
  toggleDebug: []
}>()
</script>

<template>
  <aside class="book-tabs" aria-label="章节书签">
    <button class="book-tab book-tab--toc">目录</button>
    <button
      v-for="(chapter, index) in chapters"
      :key="chapter.title"
      class="book-tab"
      :class="activeChapter === index ? 'book-tab--active' : ''"
      @click="emit('update:activeChapter', index)"
    >
      {{ index + 1 }}
    </button>
    <button class="book-tab" @click="emit('toggleDebug')">日志</button>
  </aside>
</template>
