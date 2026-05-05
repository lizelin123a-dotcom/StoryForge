<script setup lang="ts">
import type { NovelSummary } from '../api'

defineProps<{
  novels: NovelSummary[]
}>()

const emit = defineEmits<{
  create: []
  load: [id: string]
}>()
</script>

<template>
  <section class="bookshelf-room">
    <header class="bookshelf-hero">
      <div>
        <p class="section-kicker">StoryForge Library</p>
        <h1>我的书架</h1>
        <p>每一本书都是一份正在生长的手稿。取下一本继续写，或把新书放上书架。</p>
      </div>
      <button class="sf-btn sf-btn--primary bookshelf-new" @click="emit('create')">把新书放上书架</button>
    </header>

    <div class="bookshelf-frame">
      <div v-if="novels.length" class="bookshelf-grid">
        <article v-for="(novel, index) in novels" :key="novel.id" class="book-cover-card" @click="emit('load', novel.id)">
          <div class="book-cover-card__book" :class="`book-cover-card__book--v${index % 5}`">
            <div class="book-cover-card__spine"></div>
            <div class="book-cover-card__ornament">{{ ['✦', '❖', '✧', '◆', '✹'][index % 5] }}</div>
            <h2>{{ novel.title }}</h2>
            <p>{{ novel.genre || '未分类手稿' }}</p>
          </div>
          <div class="book-cover-card__caption">
            <strong>{{ novel.title }}</strong>
            <span>{{ novel.words || 0 }} 字 · {{ novel.status || '未开始' }}</span>
          </div>
        </article>
        <button class="book-cover-card book-cover-card--new" @click="emit('create')">
          <div class="book-cover-card__book">
            <div class="book-cover-card__ornament">＋</div>
            <h2>新书</h2>
            <p>打开空白扉页</p>
          </div>
          <div class="book-cover-card__caption"><strong>把新书放上书架</strong><span>从扉页开始构思</span></div>
        </button>
      </div>
      <div v-else class="bookshelf-empty">
        <div class="book-cover-card__book">
          <div class="book-cover-card__ornament">＋</div>
          <h2>空白新书</h2>
          <p>等待第一行灵感</p>
        </div>
        <h2>书架还空着</h2>
        <p>先打开一本空白书，在扉页写下灵感与案头设定。</p>
        <button class="sf-btn sf-btn--primary" @click="emit('create')">把新书放上书架</button>
      </div>
      <div class="bookshelf-plank"></div>
    </div>
  </section>
</template>
