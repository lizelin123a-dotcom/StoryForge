<script setup lang="ts">
defineProps<{
  side: 'left' | 'right'
  className?: string
}>()
</script>

<template>
  <section class="notebook-page" :class="[`notebook-page--${side}`, className]">
    <slot />
  </section>
</template>
