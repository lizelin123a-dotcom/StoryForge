<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, getApiBase, setApiBase, type CharacterSetting, type DaemonState, type GeneratedSettings, type NovelDetail, type NovelSummary, type SseEvent } from './api'
import AboutPage from './components/AboutPage.vue'
import AppSidebar from './components/AppSidebar.vue'
import BookcasePage from './components/BookcasePage.vue'
import ConfigPage from './components/ConfigPage.vue'
import DissectPage from './components/DissectPage.vue'
import NoticeToast from './components/NoticeToast.vue'
import NovelWizard from './components/NovelWizard.vue'
import type { Chapter, RightTab, RouteName, StepState } from './types'
import { useSSE } from './useSSE'

const APP_VERSION = '0.3.3'
const navItems: { key: RouteName; icon: string; label: string }[] = [
  { key: 'bookcase', icon: '📂', label: '书架' },
  { key: 'edit', icon: '✍️', label: '创作台' },
  { key: 'config', icon: '🛠', label: '配置' },
  { key: 'about', icon: 'ℹ️', label: '关于' },
]
const rightTabs: RightTab[] = ['监控', '审阅', '生成逻辑', '事件']

const emptyState = (novelId = ''): DaemonState => ({
  novel_id: novelId,
  status: 'idle',
  current_phase: 'idle',
  progress: { total_chapters: 0, written_chapters: 0, total_words: 0, target_words: 0 },
  foreshadowing_ledger: { new_hooks: [], closed_hooks: [], still_open: [] },
  chapter_summaries: [],
  chapter_texts: [],
  baseline_texts: [],
  conflicts: [],
  errors: [],
  retry_count: 0,
  max_retries: 3,
  quality_threshold: 50,
  manual_review: { enabled: false, pending: null, history: [], instructions: '' },
  runtime_memory: { chapter_summaries: [], hooks: [], facts: [] },
  runtime_state_deltas: [],
  hook_health_records: [],
})

const route = ref<RouteName>('bookcase')
const routeNovelId = ref('')
const appNotice = ref('')
const novels = ref<NovelSummary[]>([])
const selectedNovel = ref<NovelDetail | null>(null)
const selectedNovelId = computed(() => selectedNovel.value?.id || routeNovelId.value || '')
const chapters = ref<Chapter[]>([])
const activeChapter = ref(0)
const daemonState = ref<DaemonState>(emptyState())
const { events, status: sseStatus, connect } = useSSE()

const leftCollapsed = ref(false)
const rightCollapsed = ref(false)
const settingOpen = ref(true)
const activeRightTab = ref<RightTab>('监控')
const semiAutoMode = ref(false)
const reviewEditContent = ref('')
const reviewInstructions = ref('')
const generationLogic = ref<string[]>([])
const dissectSourceId = ref('')

const wizardOpen = ref(false)
const wizardLoading = ref(false)
const wizardLogline = ref('')
const wizardSettings = ref<GeneratedSettings | null>(null)

const writingForm = reactive({
  title: '',
  world_setting: '',
  characters: '',
  genre: '',
  target_word_count: 120000,
  apiKey: localStorage.getItem('storyforge.apiKey') || localStorage.getItem('plotsys.apiKey') || '',
  backendApiBaseUrl: getApiBase(),
  apiBaseUrl: localStorage.getItem('storyforge.llmApiBaseUrl') || localStorage.getItem('plotsys.llmApiBaseUrl') || 'https://api.deepseek.com/v1',
  model: localStorage.getItem('storyforge.model') || localStorage.getItem('plotsys.model') || 'deepseek-chat',
  quality_threshold: 50,
})

const steps = reactive<Record<string, StepState>>({ first: '待执行', second: '待执行', third: '待执行' })
const activeDissectTab = ref<'爽点分析' | '节奏分析' | '置换表'>('爽点分析')
const dissectBook = reactive({ title: '尚未上传', author: '未知作者', genre: '待识别', wordCount: 0 })
const uploadedFileName = ref('')
const shuangStats = ref([{ type: '等待拆解', count: 1 }])
const replacementRows = ref([{ group: '提示', old: '上传对标书', next: '执行三遍拆解后生成置换表' }])

const stateLabel = computed(() => {
  const map: Record<string, string> = { idle: '未开始', running: '写作中', paused: '已暂停', completed: '已完成', error: '错误' }
  return map[daemonState.value.status] || selectedNovel.value?.status_label || daemonState.value.status || '未开始'
})
const stateTone = computed(() => {
  const map: Record<string, string> = {
    idle: 'bg-zinc-800 text-zinc-300 border-zinc-700',
    running: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    paused: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    completed: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    error: 'bg-red-500/15 text-red-300 border-red-500/30',
  }
  return map[daemonState.value.status] || map.idle
})
const progress = computed(() => daemonState.value.progress || emptyState().progress)
const wordPercent = computed(() => Math.min(100, Math.round(((progress.value.total_words || 0) / (progress.value.target_words || writingForm.target_word_count || 1)) * 100)))
const chapterPercent = computed(() => Math.min(100, Math.round(((progress.value.written_chapters || 0) / (progress.value.total_chapters || chapters.value.length || 1)) * 100)))
const latestEvents = computed(() => events.value.slice(0, 20))
const manualReview = computed(() => (daemonState.value.manual_review as Record<string, unknown> | undefined) || {})
const pendingNode = computed(() => (manualReview.value.enabled ? ((manualReview.value.pending as Record<string, unknown> | null) || null) : null))
const pendingNodeTitle = computed(() => (pendingNode.value ? `第 ${pendingNode.value.chapter_index} 章 / 节点 ${pendingNode.value.node_index} · ${pendingNode.value.node_type}` : ''))
const currentChapter = computed(() => chapters.value[activeChapter.value] || chapters.value[0])
const currentChapterText = computed({
  get: () => currentChapter.value?.content || '',
  set: (value: string) => {
    if (currentChapter.value) currentChapter.value.content = value
  },
})
const characterLines = computed(() => selectedNovel.value?.characters?.map(formatCharacter).join('\n') || '')

function formatCharacter(character: CharacterSetting) {
  return `${character.name || '未命名'}（${character.role || '角色'}）：${character.description || '暂无描述'}`
}

function hashToRoute() {
  const hash = window.location.hash.replace(/^#\/?/, '')
  if (!hash) return { name: 'bookcase' as RouteName, id: '' }
  const [name, id] = hash.split('/')
  if (name === 'edit') return { name: 'edit' as RouteName, id: id || '' }
  if (['bookcase', 'dissect', 'config', 'about'].includes(name)) return { name: name as RouteName, id: '' }
  return { name: 'bookcase' as RouteName, id: '' }
}

function syncRouteFromHash() {
  const parsed = hashToRoute()
  route.value = parsed.name
  routeNovelId.value = parsed.id
  if (parsed.name === 'edit' && parsed.id && parsed.id !== selectedNovel.value?.id) void loadNovel(parsed.id)
  if (parsed.name === 'bookcase' || parsed.name === 'config') void refreshNovels()
}

function go(key: RouteName, id = '') {
  if (key === 'edit') {
    const targetId = id || selectedNovelId.value
    if (!targetId) {
      window.location.hash = '/bookcase'
      return
    }
    window.location.hash = `/edit/${targetId}`
    return
  }
  window.location.hash = `/${key}`
}

async function refreshNovels() {
  try {
    const result = await api.listNovels()
    novels.value = result.items
  } catch (error) {
    appNotice.value = `作品列表加载失败：${String(error)}`
  }
}

async function loadNovel(id: string) {
  try {
    const novel = await api.getNovel(id)
    selectedNovel.value = novel
    routeNovelId.value = novel.id
    writingForm.title = novel.title
    writingForm.world_setting = novel.world_setting || ''
    writingForm.characters = novel.characters?.map(formatCharacter).join('\n') || ''
    writingForm.genre = novel.genre || ''
    writingForm.target_word_count = Number(novel.target_word_count || 120000)
    if (novel.chapter_texts?.length) {
      syncChaptersFromTexts(novel.chapter_texts)
    }
    await refreshStatus(novel.id)
    if (window.location.hash !== `#/edit/${novel.id}`) window.location.hash = `/edit/${novel.id}`
  } catch (error) {
    appNotice.value = `作品加载失败：${String(error)}`
    go('bookcase')
  }
}

function syncChaptersFromTexts(texts: string[]) {
  chapters.value = texts.map((text, index) => ({
    title: `第 ${index + 1} 章`,
    content: text || '',
    nodeLabel: '已完成',
    nodesDone: 7,
    nodesTotal: 7,
  }))
  if (!chapters.value.length) activeChapter.value = 0
  if (activeChapter.value >= chapters.value.length) activeChapter.value = Math.max(0, chapters.value.length - 1)
}

function syncChaptersFromState(state: DaemonState) {
  syncChaptersFromTexts(state.chapter_texts || [])
}

function syncPendingEdit() {
  if (!pendingNode.value) {
    reviewEditContent.value = ''
    reviewInstructions.value = ''
    return
  }
  if (pendingNode.value.content && !reviewEditContent.value) reviewEditContent.value = String(pendingNode.value.content)
}

async function refreshStatus(novelId = selectedNovelId.value) {
  try {
    daemonState.value = await api.daemonStatus(novelId || undefined)
    syncChaptersFromState(daemonState.value)
    syncPendingEdit()
  } catch (error) {
    appNotice.value = `状态刷新失败：${String(error)}`
  }
}

function applyEvent(event: SseEvent) {
  if (event.state) {
    const eventNovelId = event.state.novel_id || ''
    if (!selectedNovelId.value || eventNovelId === selectedNovelId.value) {
      daemonState.value = event.state
      syncChaptersFromState(event.state)
    }
  }
  if (event.type === 'node_generated' && event.data?.content && (!selectedNovelId.value || event.state?.novel_id === selectedNovelId.value)) {
    const index = Math.max(0, (Number(event.data.chapter_index) || 1) - 1)
    while (chapters.value.length <= index) chapters.value.push({ title: `第 ${chapters.value.length + 1} 章`, content: '', nodeLabel: '写作中', nodesDone: 0, nodesTotal: 7 })
    chapters.value[index].content += `${chapters.value[index].content ? '\n\n' : ''}${String(event.data.content)}`
    chapters.value[index].nodesDone = Number(event.data.node_index) || chapters.value[index].nodesDone + 1
    chapters.value[index].nodeLabel = String(event.data.node_type || '节点生成')
    activeChapter.value = index
  }
  if (event.data?.generation_logic) generationLogic.value.unshift(String(event.data.generation_logic))
  if (event.type === 'llm_fallback_used') {
    appNotice.value = `LLM 调用失败，已使用本地兜底模板：${String(event.data?.stage || 'unknown')}`
  }
  if (event.type === 'node_review_required') {
    reviewEditContent.value = String(event.data?.content || pendingNode.value?.content || '')
    activeRightTab.value = '审阅'
  }
  if (event.type === 'node_review_resolved') {
    reviewEditContent.value = ''
    reviewInstructions.value = ''
  }
  syncPendingEdit()
}

function persistConfig() {
  localStorage.setItem('storyforge.apiKey', writingForm.apiKey)
  localStorage.setItem('storyforge.llmApiBaseUrl', writingForm.apiBaseUrl)
  localStorage.setItem('storyforge.model', writingForm.model)
  setApiBase(writingForm.backendApiBaseUrl)
}

async function generateNovelSettings() {
  if (wizardLogline.value.trim().length > 100) {
    appNotice.value = '一句话灵感最多 100 个字。'
    return
  }
  try {
    wizardLoading.value = true
    persistConfig()
    wizardSettings.value = await api.generateSettings({ logline: wizardLogline.value.trim(), api_key: writingForm.apiKey, api_base_url: writingForm.apiBaseUrl, model: writingForm.model })
  } catch (error) {
    appNotice.value = `生成设定失败：${String(error)}`
  } finally {
    wizardLoading.value = false
  }
}

async function createNovelFromWizard() {
  if (!wizardSettings.value) return
  try {
    const novel = await api.createNovel(wizardSettings.value)
    wizardOpen.value = false
    wizardLogline.value = ''
    wizardSettings.value = null
    await refreshNovels()
    await loadNovel(novel.id)
  } catch (error) {
    appNotice.value = `创建作品失败：${String(error)}`
  }
}

async function startWriting() {
  if (!selectedNovel.value) {
    appNotice.value = '请先在书架中选择或新建作品。'
    return
  }
  try {
    persistConfig()
    const updated = await api.updateNovel(selectedNovel.value.id, { target_word_count: Number(writingForm.target_word_count) })
    selectedNovel.value = updated
    const result = await api.startDaemon({
      novel_id: selectedNovel.value.id,
      title: selectedNovel.value.title,
      world_setting: selectedNovel.value.world_setting,
      characters: characterLines.value,
      genre: selectedNovel.value.genre,
      target_word_count: Number(writingForm.target_word_count),
      quality_threshold: Number(writingForm.quality_threshold),
      dissect_source_id: dissectSourceId.value || null,
      api_key: writingForm.apiKey,
      api_base_url: writingForm.apiBaseUrl,
      model: writingForm.model,
      semi_auto: semiAutoMode.value,
    })
    appNotice.value = `守护进程已启动：${result.novel_id}`
    await refreshStatus(selectedNovel.value.id)
  } catch (error) {
    appNotice.value = `启动失败：${String(error)}`
  }
}

async function pauseWriting() {
  try {
    await api.pauseDaemon(selectedNovelId.value || undefined)
    await refreshStatus()
  } catch (error) {
    appNotice.value = `暂停失败：${String(error)}`
  }
}

async function resumeWriting() {
  try {
    await api.resumeDaemon(selectedNovelId.value || undefined)
    await refreshStatus()
  } catch (error) {
    appNotice.value = `继续失败：${String(error)}`
  }
}

async function submitReviewDecision(action: 'approve' | 'rewrite' | 'rollback') {
  try {
    const payload = { content: reviewEditContent.value, instructions: reviewInstructions.value }
    if (action === 'approve') await api.approveNode(payload)
    if (action === 'rewrite') await api.rewriteNode(payload)
    if (action === 'rollback') await api.rollbackNode({ instructions: reviewInstructions.value })
    appNotice.value = action === 'approve' ? '审阅已通过，内容已同步。' : action === 'rewrite' ? '已按当前编辑内容提交重写/替换。' : '已回滚该节点。'
    reviewEditContent.value = ''
    reviewInstructions.value = ''
    await refreshStatus()
  } catch (error) {
    appNotice.value = `审阅提交失败：${String(error)}`
  }
}

async function testConnection() {
  try {
    persistConfig()
    const result = await api.testLlm({ api_key: writingForm.apiKey, api_base_url: writingForm.apiBaseUrl, model: writingForm.model })
    appNotice.value = `LLM 连接成功：${result.message}`
  } catch (error) {
    appNotice.value = `连接失败：${String(error)}`
  }
}

async function deleteNovel(id: string) {
  const title = novels.value.find((item) => item.id === id)?.title || '该作品'
  if (!window.confirm(`确认删除《${title}》？相关写作状态也会删除。`)) return
  try {
    await api.deleteNovel(id)
    if (selectedNovel.value?.id === id) {
      selectedNovel.value = null
      chapters.value = []
      daemonState.value = emptyState()
      go('bookcase')
    }
    await refreshNovels()
  } catch (error) {
    appNotice.value = `删除失败：${String(error)}`
  }
}

function exportText() {
  const body = chapters.value.length ? chapters.value.map((chapter) => `${chapter.title}\n\n${chapter.content}`).join('\n\n---\n\n') : '尚未开始写作'
  const blob = new Blob([body], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedNovel.value?.title || 'storyforge-novel'}.txt`
  link.click()
  URL.revokeObjectURL(url)
}

function exportAllNovels() {
  const blob = new Blob([JSON.stringify(novels.value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'storyforge-novels.json'
  link.click()
  URL.revokeObjectURL(url)
}

function onFileSelected(file?: File) {
  if (!file) return
  uploadedFileName.value = file.name
  dissectBook.title = file.name.replace(/\.txt$/i, '')
  dissectBook.wordCount = Math.round(file.size / 2)
}

async function runStep(key: 'first' | 'second' | 'third') {
  steps[key] = '执行中'
  try {
    if (dissectSourceId.value) {
      if (key === 'first') await api.firstPass(dissectSourceId.value)
      if (key === 'second') await api.secondPass(dissectSourceId.value)
      if (key === 'third') await api.thirdPass(dissectSourceId.value)
    } else {
      await new Promise((resolve) => window.setTimeout(resolve, 650))
    }
    steps[key] = '已完成'
  } catch (error) {
    steps[key] = '失败'
    appNotice.value = `拆解步骤失败：${String(error)}`
  }
}

onMounted(async () => {
  window.onhashchange = syncRouteFromHash
  syncRouteFromHash()
  await refreshNovels()
  connect(applyEvent)
})
</script>

<template>
  <div class="min-h-screen min-w-[1024px] bg-[#0f0f0f] text-[#e0e0e0]">
    <AppSidebar :route="route" :sse-status="sseStatus" :nav-items="navItems" @go="go" />

    <main class="ml-[60px] min-h-screen">
      <NoticeToast :notice="appNotice" @close="appNotice = ''" />

      <BookcasePage v-if="route === 'bookcase'" :novels="novels" @create="wizardOpen = true" @load="loadNovel" />

      <section v-else-if="route === 'edit'" class="flex h-screen overflow-hidden">
        <aside class="border-r border-[#2a2a2a] bg-[#141414] transition-all duration-150" :class="leftCollapsed ? 'w-12' : 'w-[320px]'">
          <button v-if="leftCollapsed" class="h-full w-12 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="leftCollapsed = false">›</button>
          <div v-else class="flex h-full flex-col p-4">
            <div class="mb-4 flex items-start justify-between gap-3"><div><h1 class="text-xl font-semibold tracking-tight text-white">{{ selectedNovel?.title || '未选择作品' }}</h1><span class="mt-2 inline-flex rounded-full border px-2.5 py-1 text-xs" :class="stateTone">{{ stateLabel }}</span></div><button class="rounded-lg border border-[#2a2a2a] px-2 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="leftCollapsed = true">‹</button></div>
            <div class="overflow-y-auto pr-1">
              <section class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] shadow-lg shadow-black/20">
                <button class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-white" @click="settingOpen = !settingOpen">设定区 <span class="text-zinc-500">{{ settingOpen ? '−' : '+' }}</span></button>
                <div v-if="settingOpen" class="space-y-3 border-t border-[#2a2a2a] p-4">
                  <label class="block text-xs text-zinc-500">世界观<textarea v-model="writingForm.world_setting" rows="4" readonly class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-300" /></label>
                  <label class="block text-xs text-zinc-500">人物设定<textarea v-model="writingForm.characters" rows="5" readonly class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-300" /></label>
                  <label class="block text-xs text-zinc-500">类型<input v-model="writingForm.genre" readonly class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-300" /></label>
                  <label class="block text-xs text-zinc-500">目标字数<input v-model.number="writingForm.target_word_count" type="number" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
                  <label class="flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-200"><input v-model="semiAutoMode" type="checkbox" /> 半自动模式：每个节点生成后暂停审阅</label>
                  <label class="block text-xs text-zinc-500">API Key<input v-model="writingForm.apiKey" type="password" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
                  <label class="block text-xs text-zinc-500">LLM API Base URL<input v-model="writingForm.apiBaseUrl" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
                  <label class="block text-xs text-zinc-500">模型选择<input v-model="writingForm.model" class="mt-1 w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></label>
                </div>
              </section>
              <section class="mt-4 rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 shadow-lg shadow-black/20"><h2 class="mb-3 text-sm font-medium text-white">对标拆解引用</h2><input v-model="dissectSourceId" placeholder="可选：拆解素材 ID" class="w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] p-3 text-sm text-zinc-200" /></section>
            </div>
            <div class="mt-auto grid grid-cols-2 gap-2 pt-4"><button class="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-medium text-emerald-950 hover:bg-emerald-400" @click="startWriting">▶ 启动写作</button><button class="rounded-xl bg-amber-500 px-3 py-2 text-sm font-medium text-amber-950 hover:bg-amber-400" @click="pauseWriting">⏸ 暂停</button><button class="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500" @click="resumeWriting">▶ 继续</button><button class="rounded-xl bg-zinc-700 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-600" @click="exportText">📥 导出文本</button></div>
          </div>
        </aside>
        <section class="flex min-w-[400px] flex-1 flex-col bg-[#0f0f0f]">
          <div class="border-b border-[#2a2a2a] bg-[#141414]/80 px-5 py-3"><div v-if="chapters.length" class="flex gap-2 overflow-x-auto pb-1"><button v-for="(chapter, index) in chapters" :key="chapter.title" class="shrink-0 rounded-full border px-4 py-1.5 text-sm" :class="activeChapter === index ? 'border-indigo-500/50 bg-indigo-500/20 text-white' : 'border-[#2a2a2a] bg-[#1a1a1a] text-zinc-400 hover:text-white'" @click="activeChapter = index">{{ chapter.title }}</button></div><p v-else class="text-sm text-zinc-500">尚未开始写作</p></div>
          <div class="flex-1 overflow-y-auto p-6"><textarea v-if="chapters.length" v-model="currentChapterText" class="min-h-full w-full resize-none rounded-2xl border border-[#2a2a2a] bg-[#151515] p-6 font-mono text-[15px] leading-8 text-zinc-200 shadow-2xl shadow-black/20" /><div v-else class="flex h-full items-center justify-center rounded-2xl border border-dashed border-[#3a3a3a] bg-[#151515] text-zinc-500">尚未开始写作，点击左侧“启动写作”后会自动加载持久化章节。</div></div>
          <div class="border-t border-[#2a2a2a] bg-[#141414] px-6 py-3 text-sm text-zinc-400">节点 {{ currentChapter?.nodesDone || 0 }}/{{ currentChapter?.nodesTotal || 0 }}：{{ currentChapter?.nodeLabel || '尚未开始' }}</div>
        </section>
        <aside class="border-l border-[#2a2a2a] bg-[#141414] transition-all duration-150" :class="rightCollapsed ? 'w-12' : 'w-[360px]'">
          <button v-if="rightCollapsed" class="h-full w-12 text-zinc-500 hover:bg-[#1a1a1a] hover:text-white" @click="rightCollapsed = false">‹</button>
          <div v-else class="h-full overflow-y-auto p-4"><div class="mb-4 flex items-center justify-between"><h2 class="text-base font-semibold text-white">监控面板</h2><button class="rounded-lg border border-[#2a2a2a] px-2 text-zinc-500 hover:text-white" @click="rightCollapsed = true">›</button></div><div class="mb-3 grid grid-cols-4 gap-1 rounded-xl bg-[#0f0f0f] p-1 text-xs"><button v-for="tab in rightTabs" :key="tab" class="rounded-lg px-2 py-1.5" :class="activeRightTab === tab ? 'bg-indigo-500 text-white' : 'text-zinc-500 hover:text-zinc-200'" @click="activeRightTab = tab">{{ tab }}</button></div>
            <div v-if="activeRightTab === '监控'" class="space-y-3"><div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 shadow-lg shadow-black/20"><div class="mb-2 flex justify-between text-xs text-zinc-500"><span>进度</span><span>{{ wordPercent }}%</span></div><div class="h-2 rounded-full bg-zinc-800"><div class="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-blue-400" :style="{ width: wordPercent + '%' }"></div></div><div class="mt-3 grid grid-cols-2 gap-2 text-sm text-zinc-300"><span>{{ progress.total_words }}/{{ progress.target_words || writingForm.target_word_count }} 字</span><span>{{ progress.written_chapters }}/{{ progress.total_chapters }} 章 · {{ chapterPercent }}%</span></div></div><div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4"><div class="mb-2 text-sm font-medium text-white">伏笔台账</div><p class="text-sm text-zinc-400">待回收 {{ daemonState.foreshadowing_ledger?.still_open?.length || 0 }} / 已回收 {{ daemonState.foreshadowing_ledger?.closed_hooks?.length || 0 }}</p></div><div class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4"><div class="mb-2 text-sm font-medium text-white">错误</div><p class="text-sm text-zinc-400">{{ daemonState.errors?.join('；') || '暂无错误' }}</p></div></div>
            <div v-else-if="activeRightTab === '审阅'" class="space-y-3"><div v-if="pendingNode" class="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4"><div class="mb-2 text-sm font-medium text-amber-200">半自动审阅：{{ pendingNodeTitle }}</div><textarea v-model="reviewEditContent" rows="10" class="mt-3 w-full rounded-xl border border-amber-500/30 bg-[#0f0f0f] p-3 text-sm leading-7 text-zinc-200" /><textarea v-model="reviewInstructions" rows="3" placeholder="给后续内容或重写使用的修改意见" class="mt-2 w-full rounded-xl border border-amber-500/30 bg-[#0f0f0f] p-3 text-sm text-zinc-200" /><div class="mt-3 grid grid-cols-3 gap-2 text-xs font-medium"><button class="rounded-xl bg-emerald-500 px-3 py-2 text-emerald-950" @click="submitReviewDecision('approve')">通过并同步</button><button class="rounded-xl bg-amber-500 px-3 py-2 text-amber-950" @click="submitReviewDecision('rewrite')">替换/重写</button><button class="rounded-xl bg-red-500 px-3 py-2 text-white" @click="submitReviewDecision('rollback')">回滚节点</button></div></div><div v-else class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm text-zinc-400">当前没有待审阅节点。</div></div>
            <div v-else-if="activeRightTab === '生成逻辑'" class="space-y-3"><div v-for="(item, index) in generationLogic" :key="index" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm leading-7 text-zinc-300">{{ item }}</div><p v-if="!generationLogic.length" class="rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] p-4 text-sm text-zinc-500">等待节点生成逻辑。</p></div>
            <div v-else class="space-y-2"><div v-for="event in latestEvents" :key="event.receivedAt + event.type" class="rounded-lg bg-[#0f0f0f] p-2 text-xs text-zinc-500"><span class="text-zinc-300">{{ event.type }}</span> · {{ event.receivedAt }}</div><p v-if="!latestEvents.length" class="text-xs text-zinc-500">等待 SSE 事件。</p></div>
          </div>
        </aside>
      </section>

      <ConfigPage v-else-if="route === 'config'" :novels="novels" :writing-form="writingForm" @load="loadNovel" @delete="deleteNovel" @test-connection="testConnection" @export-all="exportAllNovels" />

      <DissectPage
        v-else-if="route === 'dissect'"
        v-model:active-tab="activeDissectTab"
        :steps="steps"
        :dissect-book="dissectBook"
        :uploaded-file-name="uploadedFileName"
        :shuang-stats="shuangStats"
        :replacement-rows="replacementRows"
        @file-selected="onFileSelected"
        @run-step="runStep"
      />

      <AboutPage v-else :version="APP_VERSION" />
    </main>

    <NovelWizard
      :open="wizardOpen"
      :loading="wizardLoading"
      :logline="wizardLogline"
      :settings="wizardSettings"
      @close="wizardOpen = false"
      @update:logline="wizardLogline = $event"
      @update:settings="wizardSettings = $event"
      @generate="generateNovelSettings"
      @accept="createNovelFromWizard"
    />
  </div>
</template>
