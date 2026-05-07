<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const props = defineProps<{
  daemonStatus: string
  saveLoading: boolean
  hasNovel: boolean
}>()

const emit = defineEmits<{
  back: []
  startWriting: []
  pauseWriting: []
  resumeWriting: []
  saveChapter: []
}>()

const isFullscreen = ref(Boolean(document.fullscreenElement))

function updateFullscreenState() {
  isFullscreen.value = Boolean(document.fullscreenElement)
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    void document.documentElement.requestFullscreen?.()
    return
  }
  void document.exitFullscreen?.()
}

onMounted(() => document.addEventListener('fullscreenchange', updateFullscreenState))
onUnmounted(() => document.removeEventListener('fullscreenchange', updateFullscreenState))
</script>

<template>
  <section class="notebook-workspace">
    <nav class="workspace-fixed-toolbar" aria-label="写作工作台快捷操作">
      <button class="workspace-tool" title="回到书架" @click="emit('back')">书</button>
      <button class="workspace-tool" :title="isFullscreen ? '退出全屏' : '进入全屏'" @click="toggleFullscreen">{{ isFullscreen ? '×' : '⛶' }}</button>
      <button class="workspace-tool" :disabled="!props.hasNovel || props.daemonStatus === 'running'" title="开始写书" @click="emit('startWriting')">▶</button>
      <button class="workspace-tool" :disabled="props.daemonStatus !== 'running'" title="暂停" @click="emit('pauseWriting')">⏸</button>
      <button class="workspace-tool" :disabled="props.daemonStatus !== 'paused'" title="继续" @click="emit('resumeWriting')">⏵</button>
      <button class="workspace-tool" :disabled="!props.hasNovel || props.saveLoading" :title="props.saveLoading ? '保存中' : '保存正文'" @click="emit('saveChapter')">💾</button>
    </nav>
    <div class="notebook-spread">
      <slot />
    </div>
    <slot name="tabs" />
    <slot name="debug" />
  </section>
</template>
