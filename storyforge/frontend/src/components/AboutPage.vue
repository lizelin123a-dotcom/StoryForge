<script setup lang="ts">
defineProps<{
  version: string
}>()
</script>

<template>
  <section class="flex min-h-screen items-center justify-center p-8">
    <div class="max-w-2xl rounded-2xl border border-[#2a2a2a] bg-[#1a1a1a] p-8 text-center shadow-2xl shadow-black/30">
      <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/15 text-2xl text-indigo-300">S</div>
      <h1 class="text-3xl font-semibold text-white">StoryForge</h1>
      <p class="mt-3 text-zinc-400">版本 {{ version }} · 书架、创作台、对标拆解与自动写作一体化系统。</p>
      <p class="mt-4 text-sm text-zinc-500">作者：StoryForge Team</p>
    </div>
  </section>
</template>
