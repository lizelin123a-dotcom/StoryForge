# StoryForge 更新日志

## 2026-05-05 · v0.4.4

- `build_governed_context` 接入持久化共创资产 `novel_assets` 和已锁定节点 `locked_nodes`，将作者确认过的作品骨架与人工节点作为高优先级上下文。
- 守护进程启动时会加载作品资产与锁定节点；节点生成前会检查同章同序号锁定节点，若存在则直接采用人工锁定内容并发出 `locked_node_applied` 事件，避免 AI 覆盖作者确认内容。
- 保存节点时支持 `sync_chapter`，人工编辑或锁定节点后可按节点草稿重建当前章节正文，并同步章节、字数与 daemon state。
- 共创资产在左侧设定区展示，方便写作时随时查看核心灵感、主角欲望、世界规则、核心矛盾、期待钩子、爽点模型和角色关系。
- 上下文约束新增明确规则：共创资产优先级高于临时生成想法，锁定节点必须承接、不得覆盖、否定或重写。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.4`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.3

- 新增章节人工保存链路：后端 [`POST /api/v1/novel/{novel_id}/chapter`](storyforge/interfaces/api/v1/novel.py) 可保存当前章节正文，前端 [`ChapterEditor`](storyforge/frontend/src/components/ChapterEditor.vue) 增加“保存章节”和未保存标记，人工编辑不再只停留在前端状态。
- 新增节点草稿持久化模型 `node_drafts` 与接口：支持列出、编辑、保存、锁定节点草稿，AI 生成节点和半自动审阅通过的人工修改都会沉淀为节点级记录。
- 创作台中间区新增“节点草稿”侧栏，可查看当前章节节点、编辑节点正文、保存节点、锁定/解锁节点，开始从抽卡式回滚转向节点级人工干预。
- 新增小说资产持久化模型 `novel_assets` 与接口：共创构思中的核心灵感、主角欲望、世界规则、核心矛盾、期待钩子、爽点模型、角色关系会随作品保存，后续写作可复用。
- 删除作品时同步清理章节、节点草稿、共创资产和守护进程状态，避免残留数据污染后续项目。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.3`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.2

- 将新建作品入口从“一句话直出设定”调整为“共创构思”优先：新增 [`CocreationWizard`](storyforge/frontend/src/components/CocreationWizard.vue)，通过对话逐步沉淀核心灵感、主角欲望、世界规则、核心矛盾、期待钩子、爽点模型和角色关系。
- 新增共创后端接口 [`/api/v1/cocreation/turn`](storyforge/interfaces/api/v1/cocreation.py)，AI 只追问、归纳和打补丁，不一次性替作者拍板完整设定；LLM 不可用时使用本地共创追问逻辑。
- 新增当前文本教学检测服务 [`writing_signal_analyzer.py`](storyforge/application/analyst/services/writing_signal_analyzer.py)，检测情绪、钩子、矛盾、爽点、信息差、代入感与角色行动，并关联内置写作知识库给出修改建议。
- 右侧面板新增“检测”页签，编辑正文时可手动或自动检测当前章节文本，服务人工写作过程，不再只服务 AI 生成流程。
- `App.vue` 默认右栏切到“检测”，创作台开始向“AI 生成 + 人工编辑 + 实时教学检测”的共创工作台转型。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.2`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.1

- 将写作教学资料正式内置到程序仓库 [`storyforge/knowledge/writing`](storyforge/knowledge/writing)，包含原 `备份/基础` 与 `备份/资料` 下的 58 份 `.docx` 核心写作资料。
- `writing_knowledge.py` 改为只读取内置知识库，不再依赖 `C:\\Users\\25109\\Desktop\\备份` 等外部本机路径，保证项目在其他终端和机器上也能运行。
- 知识库条目路径改为相对 `storyforge` 包路径，返回 `category`、`title`、`path`、`content`，便于后续知识库页面和检索 API 使用。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.4.1`。
- 验证通过：`python -m compileall -q storyforge`、知识库加载测试与 `npm run build`。

## 2026-05-05 · v0.4.0

- 明确本地规则来源：`C:\\Users\\25109\\Desktop\\备份` 下的资料是写作教学知识库，不再在用户可见文案中称为“普通模板”。
- 新增写作知识库读取服务 [`writing_knowledge.py`](storyforge/infrastructure/knowledge/writing_knowledge.py)，可读取 `备份/基础` 与 `备份/资料` 下的 `.docx` 教学内容，并按开篇、期待感、爽点、结构、角色、冲突、行文等关键词选择片段。
- `context_governance` 在构建节点上下文时注入 `writing_guidance`，让写作四问和节点正文生成能参考核心教学资料。
- LLM 失败时的用户提示改为“切换本地写作教学规则”，节点正文降级输出标记为“本地写作教学规则生成”，避免误解为随意模板。
- 拆分中间章节编辑区，新增 [`ChapterEditor`](storyforge/frontend/src/components/ChapterEditor.vue)，封装章节 tab、正文编辑器、空状态和节点状态条。
- `App.vue` 移除章节编辑区模板，创作台三大区域已拆成 `LeftSettingsPanel`、`ChapterEditor`、`RightMonitorPanel`。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.4.0`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.3.5

- 拆分创作台左侧设定区，新增 [`LeftSettingsPanel`](storyforge/frontend/src/components/LeftSettingsPanel.vue)。
- `LeftSettingsPanel` 封装作品状态、设定区折叠、世界观/人物/类型/目标字数、半自动模式、LLM 配置、对标拆解引用与启动/暂停/继续/导出按钮。
- `App.vue` 移除左侧设定面板大段模板，创作台仅保留页面布局和状态编排，下一步可继续拆分章节编辑区。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.3.5`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.3.4

- 拆分创作台右侧监控区，新增 [`RightMonitorPanel`](storyforge/frontend/src/components/RightMonitorPanel.vue)。
- `RightMonitorPanel` 封装监控、半自动审阅、生成逻辑与 SSE 事件四个 tab，并通过 `v-model` 与事件向父组件同步折叠状态、当前 tab、审阅内容和审阅指令。
- `App.vue` 移除右侧监控面板大段模板，创作台结构进一步收敛，为后续拆分左侧设定面板与章节编辑器做准备。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.3.4`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.3.3

- 继续前端页面拆分，新增 [`DissectPage`](storyforge/frontend/src/components/DissectPage.vue)，封装对标拆解页上传、三遍拆解按钮、爽点/节奏/置换表展示。
- `App.vue` 移除对标拆解页大段模板，改为通过 `file-selected`、`run-step` 与 `v-model:active-tab` 连接状态和行为。
- 保持对标拆解现有交互不变，进一步降低主组件体积，为后续拆分创作台做准备。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.3.3`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.3.2

- 继续前端组件化拆分，新增 [`BookcasePage`](storyforge/frontend/src/components/BookcasePage.vue) 与 [`ConfigPage`](storyforge/frontend/src/components/ConfigPage.vue)。
- `App.vue` 移除书架页和配置页的大段模板，改为通过事件连接新建作品、加载作品、删除作品、测试连接与导出作品列表。
- 保持现有书架和配置行为不变，为后续拆分对标拆解页与创作台主界面降低风险。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.3.2`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.3.1

- 前端开始组件化拆分，新增 [`AppSidebar`](storyforge/frontend/src/components/AppSidebar.vue)、[`NoticeToast`](storyforge/frontend/src/components/NoticeToast.vue)、[`NovelWizard`](storyforge/frontend/src/components/NovelWizard.vue)、[`AboutPage`](storyforge/frontend/src/components/AboutPage.vue)。
- 新增共享类型文件 [`types.ts`](storyforge/frontend/src/types.ts)，将路由、章节、步骤、右侧面板 tab 类型从 `App.vue` 中抽出。
- `App.vue` 改为引用侧栏、通知、新建作品向导和关于页组件，降低主文件模板复杂度，为后续拆分书架、创作台和监控面板做准备。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.3.1`。
- 验证通过：`npm run build`。

## 2026-05-05 · v0.3.0

- 清洗并上传 GitHub 干净基线，移除旧 plotsys 历史中的 `.env`、数据库、缓存和构建产物风险。
- 后端写作守护进程改为按 `novel_id` 管理多个 `DaemonOrchestrator`，避免多作品共用单例状态。
- 为守护进程运行态增加基础锁，降低后台写作线程与 API 请求并发读写状态的风险。
- 章节正文通过质量检查后写入 `ChapterModel`，删除作品时同步清理章节记录，作品详情会从章节表回填 `chapter_texts`。
- SQLite 默认数据位置统一为项目根目录 `data/storyforge.db`，并在首次启动时自动从旧位置 `storyforge.db` / `storyforge/storyforge.db` 复制迁移。
- LLM 规划、分幕、章纲、写作四问、节点正文与章末审阅增加本地兜底标记；前端会提示 `llm_fallback_used`，避免静默伪装成正常 LLM 输出。
- 清理公开配置中的真实 API key，`.env.example` 与 `llm_config.json` 不再包含密钥。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml) 与页面 `APP_VERSION` 均提升至 `0.3.0`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.2.0

- 将默认入口改为书架系统：空 hash 自动进入书架，作品卡片统一来自后端 `GET /api/v1/novel/list`。
- 新增作品创建向导：一句话灵感限制 100 字，通过 `POST /api/v1/novel/generate-settings` 调用 LLM 生成设定，并用 `POST /api/v1/novel/create` 保存到 SQLite。
- 创作台改为 `#/edit/<novel_id>`，按当前作品加载设定、目标字数、守护进程状态与持久化章节，未写作时显示“尚未开始写作”。
- 配置页作品列表改为后端数据源，支持点击进入创作台与 `DELETE /api/v1/novel/<id>` 删除作品及关联写作状态。
- 后端注册 novel router，补齐 Novel ORM 字段与 SQLite 轻量迁移，并让书架字数/状态优先读取真实 DaemonState。
- `/api/v1/daemon/status` 支持 `novel_id` 查询参数，DeepSeek 默认 base_url 统一为 `/v1`。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json) 与后端 [`pyproject.toml`](storyforge/pyproject.toml) 均提升至 `0.2.0`。

## 2026-05-05 · v0.1.1

- 建立后续更新规范：更新日志统一写入独立文件 [`CHANGELOG.md`](CHANGELOG.md)，不再写在业务代码文件底部。
- 前端展示版本号改为 [`APP_VERSION`](storyforge/frontend/src/App.vue:38) 常量，避免页面文案与版本元数据不一致。
- 修复/恢复半自动审阅流程：待审阅节点挂起、通过并同步、替换/重写、回滚节点。
- 恢复节点内容同步到中间写作面板。
- 恢复可读的“生成逻辑”展示，避免直接显示原始结构。
- 完成 StoryForge/storyforge 重命名、旧 plotsys localStorage 兼容迁移与相关清理。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json) 与后端 [`pyproject.toml`](storyforge/pyproject.toml) 均提升至 `0.1.1`。
- 验证通过：`python -m compileall storyforge` 与 `npm run build`。
