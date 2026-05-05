<script setup lang="ts">
import type { RouteName } from '../types'

defineProps<{
  route: RouteName
  sseStatus: string
  navItems: { key: RouteName; icon: string; label: string }[]
}>()

const emit = defineEmits<{
  go: [key: RouteName]
}>()
</script>

<template>
  <aside class="fixed inset-y-0 left-0 z-20 flex w-[60px] flex-col items-center border-r border-[#2a2a2a] bg-[#111111]/95 py-4 shadow-2xl shadow-black/30 backdrop-blur">
    <div class="mb-6 flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/15 text-lg text-indigo-300 ring-1 ring-indigo-500/25">S</div>
    <nav class="flex flex-1 flex-col gap-3">
      <button
        v-for="item in navItems"
        :key="item.key"
        :title="item.label"
        class="flex h-10 w-10 items-center justify-center rounded-xl border text-xl hover:-translate-y-0.5"
        :class="route === item.key ? 'border-indigo-500/40 bg-indigo-500/20 text-white shadow-lg shadow-indigo-950/30' : 'border-transparent bg-transparent text-zinc-500 hover:border-[#2a2a2a] hover:bg-[#1a1a1a] hover:text-zinc-200'"
        @click="emit('go', item.key)"
      >
        {{ item.icon }}
      </button>
    </nav>
    <div class="h-2 w-2 rounded-full" :class="sseStatus === 'connected' ? 'bg-emerald-400' : sseStatus === 'error' ? 'bg-red-400' : 'bg-amber-400'"></div>
  </aside>
</template>
