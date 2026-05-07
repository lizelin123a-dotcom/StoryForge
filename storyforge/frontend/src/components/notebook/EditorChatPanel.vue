<script setup lang="ts">
import { ref } from 'vue'
import type { CocreationMessage, CocreationTurn, EditorSkill } from '../../types'

defineProps<{
  editorChatInput: string
  editorChatMessages: CocreationMessage[]
  editorChatLoading: boolean
  editorChatLastTurn: CocreationTurn | null
  editorSkills: EditorSkill[]
  selectedSkillIds: string[]
}>()

const emit = defineEmits<{
  'update:editorChatInput': [value: string]
  sendEditorChat: []
  applyEditorPatch: []
  toggleEditorSkill: [skillId: string]
}>()

const toolsOpen = ref(false)
</script>

<template>
  <section class="ai-paper chat-workbench">
    <div class="chat-thread">
      <div v-if="!editorChatMessages.length" class="chat-empty">
        <strong>开始和 AI 聊聊这一章。</strong>
        <span>可以直接说：这一章怎么推进？这个节点哪里弱？能不能加一个反转？</span>
      </div>

      <article
        v-for="(message, index) in editorChatMessages"
        :key="index"
        class="chat-message"
        :class="message.role === 'user' ? 'chat-message--user' : 'chat-message--ai'"
      >
        <div class="chat-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
        <div class="chat-bubble">{{ message.content }}</div>
      </article>
    </div>

    <div v-if="editorChatLastTurn?.edit_patch?.target && editorChatLastTurn.edit_patch.target !== 'none'" class="chat-patch-card">
      <div><strong>可应用修改</strong><span>{{ editorChatLastTurn.edit_patch.reason || 'AI 给出了一段可写入内容。' }}</span></div>
      <button class="sf-btn sf-btn--success" @click="emit('applyEditorPatch')">应用到{{ editorChatLastTurn.edit_patch.target === 'node' ? '节点' : '章节' }}</button>
    </div>

    <div class="chat-tools-panel" :class="toolsOpen ? 'chat-tools-panel--open' : ''">
      <button
        v-for="skill in editorSkills"
        :key="skill.id"
        class="chat-tool-chip"
        :class="selectedSkillIds.includes(skill.id) ? 'chat-tool-chip--active' : ''"
        :title="skill.description"
        @click="emit('toggleEditorSkill', skill.id)"
      >
        {{ skill.title }}
      </button>
      <span v-if="!editorSkills.length" class="chat-tool-empty">暂无可用工具</span>
    </div>

    <div class="chat-input-bar">
      <button class="chat-plus" :class="toolsOpen ? 'chat-plus--active' : ''" title="工具 / Skill" @click="toolsOpen = !toolsOpen">＋</button>
      <textarea
        :value="editorChatInput"
        rows="1"
        placeholder="输入消息，Ctrl+Enter 发送"
        @input="emit('update:editorChatInput', ($event.target as HTMLTextAreaElement).value)"
        @keydown.ctrl.enter.prevent="emit('sendEditorChat')"
      />
      <button class="chat-send" :disabled="editorChatLoading || !editorChatInput.trim()" @click="emit('sendEditorChat')">
        {{ editorChatLoading ? '...' : '发送' }}
      </button>
    </div>
  </section>
</template>
