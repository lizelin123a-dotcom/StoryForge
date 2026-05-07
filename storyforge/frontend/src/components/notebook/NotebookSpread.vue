<script setup lang="ts">
const emit = defineEmits<{
  back: []
  startWriting: []
  pauseWriting: []
  resumeWriting: []
  saveChapter: []
}>()

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    void document.documentElement.requestFullscreen?.()
    return
  }
  void document.exitFullscreen?.()
}
</script>

<template>
  <section class="notebook-workspace">
    <nav class="workspace-fixed-toolbar" aria-label="写作工作台快捷操作">
      <button class="workspace-tool" title="回到书架" @click="emit('back')">书</button>
      <button class="workspace-tool" title="全屏 / 退出全屏" @click="toggleFullscreen">⛶</button>
      <button class="workspace-tool" title="开始写书" @click="emit('startWriting')">▶</button>
      <button class="workspace-tool" title="暂停" @click="emit('pauseWriting')">⏸</button>
      <button class="workspace-tool" title="继续" @click="emit('resumeWriting')">⏵</button>
      <button class="workspace-tool" title="保存本章" @click="emit('saveChapter')">💾</button>
    </nav>
    <div class="notebook-spread">
      <slot />
    </div>
    <slot name="debug" />
  </section>
</template>
