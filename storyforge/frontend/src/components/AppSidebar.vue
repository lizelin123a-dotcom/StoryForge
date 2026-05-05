<script setup lang="ts">
import type { RouteName } from '../types'

defineProps<{
  route: RouteName
  sseStatus: string
}>()

const emit = defineEmits<{
  go: [key: RouteName]
}>()
</script>

<template>
  <aside class="storybook-menu">
    <button class="storybook-menu__brand" title="回到书架" @click="emit('go', 'bookcase')">架</button>
    <nav class="storybook-menu__nav" aria-label="StoryForge 导航">
      <button title="书架" :class="route === 'bookcase' ? 'is-active' : ''" @click="emit('go', 'bookcase')">📚</button>
      <button title="拆书工坊" :class="route === 'dissect' ? 'is-active' : ''" @click="emit('go', 'dissect')">🔍</button>
      <button title="设置" :class="route === 'config' ? 'is-active' : ''" @click="emit('go', 'config')">⚙️</button>
      <button title="关于" :class="route === 'about' ? 'is-active' : ''" @click="emit('go', 'about')">?</button>
    </nav>
    <div class="storybook-menu__signal" :class="sseStatus === 'connected' ? 'is-on' : sseStatus === 'error' ? 'is-error' : ''" title="连接状态"></div>
  </aside>
</template>
