<script setup lang="ts">
defineProps<{
  notice: string
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div v-if="notice" class="fixed right-5 top-5 z-30 max-w-xl rounded-xl border border-[#2a2a2a] bg-[#1a1a1a]/95 px-4 py-3 text-sm text-zinc-200 shadow-2xl shadow-black/40">
    {{ notice }}
    <button class="ml-3 text-zinc-500 hover:text-white" @click="emit('close')">关闭</button>
  </div>
</template>
