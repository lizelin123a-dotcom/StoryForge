<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api, getApiBase, setApiBase, type CharacterSetting, type DaemonState, type GeneratedSettings, type NovelDetail, type NovelSummary, type SseEvent } from './api'
import AboutPage from './components/AboutPage.vue'
import AppSidebar from './components/AppSidebar.vue'
import BookcasePage from './components/BookcasePage.vue'
import ChapterEditor from './components/ChapterEditor.vue'
import CocreationWizard from './components/CocreationWizard.vue'
import ConfigPage from './components/ConfigPage.vue'
import DissectPage from './components/DissectPage.vue'
import LeftSettingsPanel from './components/LeftSettingsPanel.vue'
import NoticeToast from './components/NoticeToast.vue'
import NovelWizard from './components/NovelWizard.vue'
import RightMonitorPanel from './components/RightMonitorPanel.vue'
import type { Chapter, CocreationMessage, CocreationTurn, NodeDraft, RightTab, RouteName, StepState, WritingAnalysis } from './types'
import { useSSE } from './useSSE'

const APP_VERSION = '0.4.6'
const navItems: { key: RouteName; icon: string; label: string }[] = [
  { key: 'bookcase', icon: '📂', label: '书架' },
  { key: 'edit', icon: '✍️', label: '创作台' },
  { key: 'config', icon: '🛠', label: '配置' },
  { key: 'about', icon: 'ℹ️', label: '关于' },
]
const rightTabs: RightTab[] = ['检测', '监控', '审阅', '生成逻辑', '事件']

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
const nodeDrafts = ref<NodeDraft[]>([])
const selectedNodeId = ref('')
const saveLoading = ref(false)
const daemonState = ref<DaemonState>(emptyState())
const { events, status: sseStatus, connect } = useSSE()

const leftCollapsed = ref(false)
const rightCollapsed = ref(false)
const settingOpen = ref(true)
const activeRightTab = ref<RightTab>('检测')
const semiAutoMode = ref(false)
const reviewEditContent = ref('')
const reviewInstructions = ref('')
const generationLogic = ref<string[]>([])
const dissectSourceId = ref('')

const wizardOpen = ref(false)
const wizardLoading = ref(false)
const wizardLogline = ref('')
const wizardSettings = ref<GeneratedSettings | null>(null)
const cocreationOpen = ref(false)
const cocreationLoading = ref(false)
const cocreationInput = ref('')
const cocreationMessages = ref<CocreationMessage[]>([])
const cocreationAssets = ref<Record<string, string>>({})
const cocreationLastTurn = ref<CocreationTurn | null>(null)
const editorChatInput = ref('')
const editorChatMessages = ref<CocreationMessage[]>([])
const editorChatLoading = ref(false)
const editorChatLastTurn = ref<CocreationTurn | null>(null)
const writingAnalysis = ref<WritingAnalysis | null>(null)
const analysisLoading = ref(false)

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
    if (currentChapter.value) {
      currentChapter.value.content = value
      currentChapter.value.dirty = true
    }
  },
})
const currentChapterIndex = computed(() => activeChapter.value + 1)
const currentChapterNodeDrafts = computed(() => nodeDrafts.value.filter((node) => Number(node.chapter_index) === currentChapterIndex.value))
const selectedNode = computed(() => nodeDrafts.value.find((node) => node.id === selectedNodeId.value) || null)
const currentNodeText = computed({
  get: () => selectedNode.value?.content || '',
  set: (value: string) => {
    if (selectedNode.value) selectedNode.value.content = value
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
    nodeDrafts.value = normalizeNodeDrafts(novel.node_drafts || [])
    editorChatMessages.value = normalizeChatMessages(novel.editor_chat_messages || [])
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

function normalizeChatMessages(rows: unknown[]): CocreationMessage[] {
  return rows.filter((row): row is Record<string, unknown> => !!row && typeof row === 'object').map((row): CocreationMessage => ({
    role: String(row.role || 'user') === 'assistant' ? 'assistant' : 'user',
    content: String(row.content || ''),
  })).filter((message) => message.content.trim())
}

function normalizeNodeDrafts(rows: unknown[]): NodeDraft[] {
  return rows.filter((row): row is Record<string, unknown> => !!row && typeof row === 'object').map((row) => ({
    id: String(row.id || `${row.novel_id}:chapter:${row.chapter_index}:node:${row.node_index}`),
    chapter_index: Number(row.chapter_index || 1),
    node_index: Number(row.node_index || 1),
    node_type: String(row.node_type || '节点'),
    content: String(row.content || ''),
    locked: Boolean(row.locked),
    source: String(row.source || 'ai'),
    updated_at: String(row.updated_at || ''),
  }))
}

function syncChaptersFromTexts(texts: string[]) {
  chapters.value = texts.map((text, index) => ({
    title: `第 ${index + 1} 章`,
    content: text || '',
    nodeLabel: '已完成',
    nodesDone: 7,
    nodesTotal: 7,
    dirty: false,
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
    chapters.value[index].dirty = false
    upsertNodeDraft({
      id: `${event.state?.novel_id || selectedNovelId.value}:chapter:${index + 1}:node:${Number(event.data.node_index) || 1}`,
      chapter_index: index + 1,
      node_index: Number(event.data.node_index) || 1,
      node_type: String(event.data.node_type || '节点'),
      content: String(event.data.content || ''),
      locked: false,
      source: 'ai',
    })
    chapters.value[index].nodesDone = Number(event.data.node_index) || chapters.value[index].nodesDone + 1
    chapters.value[index].nodeLabel = String(event.data.node_type || '节点生成')
    activeChapter.value = index
  }
  if (event.data?.generation_logic) generationLogic.value.unshift(String(event.data.generation_logic))
  if (event.type === 'llm_fallback_used') {
    appNotice.value = `LLM 调用失败，已切换本地写作教学规则：${String(event.data?.stage || 'unknown')}`
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

function upsertNodeDraft(node: NodeDraft) {
  const existing = nodeDrafts.value.findIndex((item) => item.id === node.id)
  if (existing >= 0) nodeDrafts.value[existing] = { ...nodeDrafts.value[existing], ...node }
  else nodeDrafts.value.push(node)
  if (!selectedNodeId.value) selectedNodeId.value = node.id
}

async function saveCurrentChapter() {
  if (!selectedNovelId.value || !currentChapter.value) return
  try {
    saveLoading.value = true
    const novel = await api.saveChapter(selectedNovelId.value, { chapter_index: currentChapterIndex.value, title: currentChapter.value.title, content: currentChapterText.value })
    selectedNovel.value = novel
    currentChapter.value.dirty = false
    appNotice.value = '章节已保存。'
  } catch (error) {
    appNotice.value = `章节保存失败：${String(error)}`
  } finally {
    saveLoading.value = false
  }
}

async function saveCurrentNode() {
  if (!selectedNovelId.value || !selectedNode.value) return
  try {
    const saved = await api.saveNode(selectedNovelId.value, { ...selectedNode.value, content: currentNodeText.value, source: 'manual', sync_chapter: true }) as unknown as NodeDraft
    upsertNodeDraft(saved)
    appNotice.value = '节点已保存。'
  } catch (error) {
    appNotice.value = `节点保存失败：${String(error)}`
  }
}

async function toggleNodeLock(node: NodeDraft) {
  if (!selectedNovelId.value) return
  const saved = await api.saveNode(selectedNovelId.value, { ...node, locked: !node.locked, source: node.source || 'manual', sync_chapter: true }) as unknown as NodeDraft
  upsertNodeDraft(saved)
}

function persistConfig() {
  localStorage.setItem('storyforge.apiKey', writingForm.apiKey)
  localStorage.setItem('storyforge.llmApiBaseUrl', writingForm.apiBaseUrl)
  localStorage.setItem('storyforge.model', writingForm.model)
  setApiBase(writingForm.backendApiBaseUrl)
}

function openCocreation() {
  wizardOpen.value = false
  cocreationOpen.value = true
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

async function sendCocreationTurn() {
  const userText = cocreationInput.value.trim() || wizardLogline.value.trim()
  if (!userText) return
  try {
    cocreationLoading.value = true
    persistConfig()
    const userMessage: CocreationMessage = { role: 'user', content: userText }
    cocreationMessages.value.push(userMessage)
    cocreationInput.value = ''
    const turn = await api.cocreationTurn({
      logline: wizardLogline.value,
      messages: cocreationMessages.value,
      assets: cocreationAssets.value,
      api_key: writingForm.apiKey,
      api_base_url: writingForm.apiBaseUrl,
      model: writingForm.model,
    }) as unknown as CocreationTurn
    cocreationLastTurn.value = turn
    cocreationAssets.value = { ...cocreationAssets.value, ...(turn.asset_patch || {}) }
    cocreationMessages.value.push({ role: 'assistant', content: turn.reply })
  } catch (error) {
    appNotice.value = `共创讨论失败：${String(error)}`
  } finally {
    cocreationLoading.value = false
  }
}

async function sendEditorChat() {
  if (!selectedNovel.value || !editorChatInput.value.trim()) return
  try {
    editorChatLoading.value = true
    persistConfig()
    const userMessage: CocreationMessage = { role: 'user', content: editorChatInput.value.trim() }
    editorChatMessages.value.push(userMessage)
    editorChatInput.value = ''
    const turn = await api.cocreationTurn({
      logline: selectedNovel.value.title,
      messages: editorChatMessages.value,
      assets: selectedNovel.value.assets || {},
      writing_context: {
        chapter_index: currentChapterIndex.value,
        chapter_text: currentChapterText.value.slice(-2400),
        selected_node: selectedNode.value,
        writing_analysis: writingAnalysis.value,
      },
      api_key: writingForm.apiKey,
      api_base_url: writingForm.apiBaseUrl,
      model: writingForm.model,
    }) as unknown as CocreationTurn
    editorChatLastTurn.value = turn
    const assistantMessage: CocreationMessage = { role: 'assistant', content: turn.reply }
    editorChatMessages.value.push(assistantMessage)
    await api.appendEditorChat(selectedNovel.value.id, { messages: [userMessage, assistantMessage] })
    if (Object.keys(turn.asset_patch || {}).length) {
      const result = await api.saveAssets(selectedNovel.value.id, { assets: turn.asset_patch })
      selectedNovel.value = { ...selectedNovel.value, assets: result.assets }
      appNotice.value = 'AI 编辑已把本轮确认内容写入作品资产。'
    }
  } catch (error) {
    appNotice.value = `创作对话失败：${String(error)}`
  } finally {
    editorChatLoading.value = false
  }
}

async function createNovelFromCocreation() {
  const assets = cocreationAssets.value
  const data: GeneratedSettings = {
    title: assets['核心灵感']?.slice(0, 18) || wizardLogline.value.slice(0, 18) || '未命名作品',
    world_setting: ['世界规则', '核心矛盾', '期待钩子', '爽点模型'].map((key) => `${key}：${assets[key] || '待补充'}`).join('\n'),
    characters: [{ name: '主角', role: '主角', description: assets['主角欲望'] || '待补充' }, { name: '对手/阻碍方', role: '反派/阻碍', description: assets['核心矛盾'] || '待补充' }, { name: '关系角色', role: '配角', description: assets['角色关系'] || '待补充' }],
    genre: '共创项目',
    target_word_count: Number(writingForm.target_word_count || 120000),
  }
  try {
    const novel = await api.createNovel(data)
    await api.saveAssets(novel.id, { assets })
    cocreationOpen.value = false
    await refreshNovels()
    await loadNovel(novel.id)
  } catch (error) {
    appNotice.value = `创建作品失败：${String(error)}`
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

async function analyzeCurrentText() {
  try {
    analysisLoading.value = true
    writingAnalysis.value = await api.writingSignals({ text: currentChapterText.value }) as unknown as WritingAnalysis
    activeRightTab.value = '检测'
  } catch (error) {
    appNotice.value = `文本检测失败：${String(error)}`
  } finally {
    analysisLoading.value = false
  }
}

let analysisTimer = 0
watch(currentChapterText, () => {
  window.clearTimeout(analysisTimer)
  analysisTimer = window.setTimeout(() => {
    if (currentChapterText.value.trim().length >= 20) void analyzeCurrentText()
  }, 900)
})

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

      <BookcasePage v-if="route === 'bookcase'" :novels="novels" @create="openCocreation" @load="loadNovel" />

      <section v-else-if="route === 'edit'" class="flex h-screen overflow-hidden">
        <LeftSettingsPanel
          v-model:collapsed="leftCollapsed"
          v-model:setting-open="settingOpen"
          v-model:semi-auto-mode="semiAutoMode"
          v-model:dissect-source-id="dissectSourceId"
          v-model:editor-chat-input="editorChatInput"
          :selected-novel="selectedNovel"
          :state-tone="stateTone"
          :state-label="stateLabel"
          :writing-form="writingForm"
          :editor-chat-messages="editorChatMessages"
          :editor-chat-loading="editorChatLoading"
          :editor-chat-last-turn="editorChatLastTurn"
          @send-editor-chat="sendEditorChat"
          @start-writing="startWriting"
          @pause-writing="pauseWriting"
          @resume-writing="resumeWriting"
          @export-text="exportText"
        />
        <ChapterEditor
          v-model:active-chapter="activeChapter"
          v-model:current-chapter-text="currentChapterText"
          v-model:selected-node-id="selectedNodeId"
          v-model:current-node-text="currentNodeText"
          :chapters="chapters"
          :node-drafts="currentChapterNodeDrafts"
          :save-loading="saveLoading"
          @save-chapter="saveCurrentChapter"
          @save-node="saveCurrentNode"
          @toggle-node-lock="toggleNodeLock"
        />
        <RightMonitorPanel
          v-model:collapsed="rightCollapsed"
          v-model:active-tab="activeRightTab"
          v-model:review-edit-content="reviewEditContent"
          v-model:review-instructions="reviewInstructions"
          :tabs="rightTabs"
          :word-percent="wordPercent"
          :chapter-percent="chapterPercent"
          :progress="progress"
          :target-word-count="writingForm.target_word_count"
          :daemon-state="daemonState"
          :pending-node="pendingNode"
          :pending-node-title="pendingNodeTitle"
          :generation-logic="generationLogic"
          :latest-events="latestEvents"
          :writing-analysis="writingAnalysis"
          :analysis-loading="analysisLoading"
          @review-decision="submitReviewDecision"
          @analyze-current-text="analyzeCurrentText"
        />
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

    <CocreationWizard
      :open="cocreationOpen"
      :loading="cocreationLoading"
      :logline="wizardLogline"
      :input="cocreationInput"
      :messages="cocreationMessages"
      :assets="cocreationAssets"
      :last-turn="cocreationLastTurn"
      @close="cocreationOpen = false"
      @update:logline="wizardLogline = $event"
      @update:input="cocreationInput = $event"
      @send="sendCocreationTurn"
      @accept="createNovelFromCocreation"
    />

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
