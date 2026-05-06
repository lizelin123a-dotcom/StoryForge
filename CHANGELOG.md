# StoryForge 更新日志

## 版本号规则

StoryForge 使用 `大版本.小功能.修复`：

- 第一位：底层逻辑、主工作流或整体使用方式发生巨大变化时递增。
- 第二位：增加局部小功能时递增。
- 第三位：修改小 bug 或小体验问题时递增。

## 2026-05-05 · v2.0.3

- 根据 Gemini 的视觉建议，将默认书封从“完成的硬皮精装书”调整为更像“线装/活页创作笔记本”的过程型手稿。
- 默认封面加入外露装订线/装订孔效果，弱化皮革精装感，强化“仍在记录和修补”的写作状态。
- 封面标题与书名说明切换到更接近仿真手写的字体栈，降低工业印刷感，增加作者亲手题名的私人感。
- 封面和新书占位加入淡稿纸格、圈阅和划线痕迹，让书架上的作品更像正在使用中的手稿本。
- 调整环境光、书架与页面背景，让书更像摆在木桌/书房暖光下，而不是儿童卡通场景。
- 顶部按钮、侧边栏图标和主操作按钮进一步改为更有纸张/印章/铜色质感的低饱和设计。
- 这是视觉风格修正，按版本号规则递增第三位。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `2.0.3`。
- 验证通过：`npm run build`。

## 2026-05-05 · v2.0.2

- 将书本 UI 从偏儿童卡通的高饱和风格收敛为更接近写实的古典书房/手稿风格。
- 降低书架、封面、按钮和侧边栏的饱和度，减少玩具感与游戏化视觉。
- 默认封面改为低饱和布面/皮革旧书色系，弱化大装饰符号，改用细金线和压纹感。
- 书页、案头设定、审稿区、AI 编辑区和后台札记统一为更克制的纸张质感、小圆角和低对比边框。
- 侧边栏、章节书签和操作按钮改为更沉稳的铜色/木色体系，保持书本隐喻但降低幼稚感。
- 这是视觉风格修正，按版本号规则递增第三位。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `2.0.2`。
- 验证通过：`npm run build`。

## 2026-05-05 · v2.0.1

- 修复书架顶部“把新书放上书架”按钮在右侧被裁切的问题，增加右侧安全留白并允许按钮文本自然换行。
- 优化书架横向布局：书本改为更紧凑的横向陈列，书架区域使用自然横向滚动，减少大面积空洞。
- 默认封面新增 5 套颜色/纹样变体，并让书本上下轻微错落，更接近真实书架陈列。
- 侧边导航去掉主要 emoji 图标，改为统一的 CSS 小图标风格：书架、拆书放大镜、设置齿轮、关于信息。
- 保留并确认“后台札记”调试区设计，作为当前调试/高级配置入口。
- 这是书本 UI 的视觉与排版修复，按版本号规则递增第三位。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `2.0.1`。
- 验证通过：`npm run build`。

## 2026-05-05 · v2.0.0

- 按“书架 → 打开一本书 → 扉页 → 翻页写作 → 页边批注”的创作隐喻重构主 UI，保留现有后端框架和写作接口。
- 首页重建为卡通古朴书架：作品以书本封面陈列在木质书架上，按钮文案改为“把新书放上书架”。
- 新增 [`NewBookPage.vue`](storyforge/frontend/src/components/NewBookPage.vue)：新建书不再使用古板弹窗，而是打开一本空白书，在扉页填写灵感并生成案头设定，确认后“把这本书放上书架”。
- 新增/重建 [`WriterStudio.vue`](storyforge/frontend/src/components/WriterStudio.vue)：打开作品后呈现摊开的书，左页为“案头设定 + 当前审稿 + AI 编辑”，右页为章节正文和页边批注。
- “资产库”统一更名为“案头设定”，更贴近小说作者语境；案头设定默认按上下文收起/展开，已确认内容仍使用原有资产存储。
- 审批环节移动到左页 AI 对话框上方，当前节点草稿可直接编辑、通过、修改后通过或回滚，便于作者边问 AI 边改稿。
- 章节正文放在右页，一章一页；字数信息移到页脚，显示本章字数、全书字数和当前状态，弱化原监控面板。
- 原检测结果改为右页“页边批注”，支持手动“检查本章”，检测摘要、信号、建议以批注卡片贴在当前章节旁边。
- 右侧章节导航改为书本插签式标签，包含目录、章节编号和日志入口；章节切换像翻页。
- 原监控/生成逻辑/事件等调试信息移动到“日志”调试抽屉，不再占据作者主写作界面；拆书工坊保留为设置下方的独立入口，UI 暂沿用旧版。
- 侧边导航重建为小型书房菜单，只保留书架、拆书、设置、关于入口。
- 全局视觉系统调整为“古朴手账书房 + 轻小说编辑部”方向，保留卡通感但不幼稚。
- 按用户版本规则，将此前不彻底的 `2.0.0` 含义修正为本次真正的整体使用逻辑重构；版本号保持 `2.0.0`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v1.1.0

- 使用前端设计审阅流程优化编辑页布局，重点修复节点草稿/审阅合并后出现的拥挤与视觉重叠问题。
- 中间编辑器改为 `正文编辑区 + 360px 节点工作区` 的稳定网格，章节正文、节点列表、节点编辑器分别拥有独立滚动区域，避免长节点列表挤压审阅编辑框。
- 节点工作区重新分层：顶部说明、节点列表、当前节点编辑/审阅三段式结构；待审状态以提示卡附着在当前节点编辑器上。
- 审阅操作层级调整：主按钮“通过并写入正文”单独占一行，“修改后通过/回滚节点”为次级操作，减少误点和按钮拥挤。
- 右侧监控面板宽度收窄为 360px，标签改为横向滚动，避免五个标签在窄宽度下互相挤压。
- 左侧面板宽度收敛为 340px，并降低资产区最大高度，让底部启动/暂停/继续/导出操作不会被上方内容压住。
- 全局最小宽度提升到 1180px，并补充键盘焦点样式，减少三栏编辑器在窄窗口下互相覆盖。
- 这是一个编辑页布局与可用性的小功能优化，按版本号规则递增第二位。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `1.1.0`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v1.0.1

- 修复重启项目后仍存在待审阅节点，但内存中的守护进程不存在时，点击“通过写入/修改后通过/回滚”返回 `404 daemon is not started` 的问题。
- 审阅接口现在会优先使用运行中的守护进程；如果项目重启导致守护进程丢失，会回退读取持久化的 daemon state，并解析其中的 `manual_review.pending`。
- 对持久化待审节点执行通过/修改后通过时，会保存节点草稿、写入章节正文、更新 `chapter_texts/baseline_texts/progress`，并清空 pending 状态。
- 对持久化待审节点执行回滚时，会清空 pending 状态并保留历史记录，不再要求守护进程必须正在运行。
- 这是重启恢复场景的小修复，按版本号规则递增第三位。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `1.0.1`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v1.0.0

- 版本号校正：此前 `v0.4.9` 与 `v0.4.10` 实际改变了写作主链路，属于底层工作流变化，应提升到 `v1.0.0`，而不是继续递增第三位。
- 确立新的主工作流：AI 生成节点草稿，节点草稿即审阅对象，人工通过后才进入中间正文；全自动写入变成显式开关。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `1.0.0`。

## 2026-05-05 · v0.4.10

- 合并“节点草稿”和“节点审阅”的前端工作面：待审阅节点会自动选中对应节点草稿，用户直接在同一个节点编辑器里修改、通过、修改后通过或回滚。
- 中间右侧节点栏标题改为“节点草稿 / 审阅”，待审阅时显示提示和审阅按钮，避免同一节点内容在节点草稿区和右侧审阅区重复出现两个编辑窗口。
- 右侧“审阅”标签页不再渲染第二个大文本框，只显示当前待审阅节点和说明，引导用户回到统一的节点编辑器完成审阅。
- 审阅提交现在优先读取当前选中节点草稿的内容，而不是读取独立审阅文本框，保证“看到的草稿”就是“通过写入的内容”。
- `node_review_required` 事件会自动切换到对应章节并选中对应节点草稿，但不再强制弹出右侧审阅编辑窗口。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.10`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.9

- 修复原有整章/小说流程与新增节点写作流程双线并行的问题：节点生成先作为 `node_draft_generated` 草稿进入节点池，不再直接追加到中间章节正文。
- 守护进程只有在节点通过审阅后才广播 `node_generated`，前端收到已审阅节点后才追加到章节正文，避免“未审阅内容自动进正文”。
- 写作启动默认进入节点审阅流程，原“半自动模式”反转为“全自动模式”开关；未勾选时常态为逐节点审阅，勾选才跳过审阅直接写入。
- 审阅接口调用补充 `novel_id`，避免多作品/多守护进程情况下审阅请求落到错误实例或最新实例。
- 右侧审阅文案从“半自动审阅”改为“节点审阅”，符合半自动作为默认常态的新工作流。
- 共创资产沉淀 prompt 明确允许并要求修正已有资产：当后续思路改变、否定、扩展或重构前面内容时，AI 会通过 `asset_patch` 覆盖旧字段，而不是只补空字段。
- 左侧 AI 写入资产时会识别是否修改了已有字段，并提示“根据新思路修正作品资产”。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.9`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.8

- 新增内置编辑 Skill 注册表 [`storyforge/knowledge/editor_skills`](storyforge/knowledge/editor_skills)，首批提供“职业网文编辑”和“情绪钩子设计师”两类专业提示词技能。
- 新增 Skill 读取服务 [`editor_skills.py`](storyforge/infrastructure/knowledge/editor_skills.py)，支持列出和按 ID 注入编辑技能内容，为后续导入蒸馏从业人员 Skill 预留目录和接口。
- 新增接口 `GET /api/v1/cocreation/skills`，前端可读取可用编辑 Skill 列表。
- 左侧 AI 创作对话支持 Skill 选择，已选 Skill 会随 `/api/v1/cocreation/turn` 的 `skill_ids` 传给后端，并注入共创/改稿 prompt。
- Skill 规则在共创服务中高于普通建议优先级，会影响 AI 的判断、追问和 `edit_patch` 生成，让左侧 AI 编辑更专业。
- 前端会记住已选 Skill，首次启动默认启用第一个可用 Skill。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.8`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.7

- 共创/编辑对话后端返回结构新增 `edit_patch`，当作者要求改稿、补写、替换、加强爽点或加钩子时，AI 必须给出可应用到当前节点或章节的修改补丁，而不只停留在建议层。
- `edit_patch` 支持 `target=node|chapter`、`mode=replace|append`、`content`、`reason` 与 `lock_node`，并经过后端归一化，避免前端拿到不可执行补丁。
- 左侧创作对话面板新增“AI 可应用修改”卡片，可一键应用到当前节点或当前章节。
- 前端应用节点补丁时会复用已有节点保存链路，自动持久化并同步章节；若 AI 建议锁定节点，会在应用后锁定。
- 前端应用章节补丁时会复用已有章节保存链路，确保正文修改直接写入数据库与 daemon state。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.7`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.6

- 新增编辑器创作对话持久化模型 `editor_chat_messages`，作品加载时恢复左侧 AI 编辑聊天记录，删除作品时同步清理。
- 新增接口 `GET/POST /api/v1/novel/{novel_id}/editor-chat`，左侧创作对话每轮用户消息与 AI 回复都会保存到数据库。
- 左侧编辑器对话调用共创接口时携带当前写作现场：当前章节正文、当前选中节点、右侧教学检测结果与章节序号，让 AI 能围绕正在写的文本给建议。
- 共创服务 `next_cocreation_turn` 支持 `writing_context`，优先针对当前章节、节点和检测结果回应，并继续归纳可确认的资产补丁。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.6`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

## 2026-05-05 · v0.4.5

- 创作台左侧改为 VSCode 式“创作对话”主面板：写作过程中可持续和 AI 编辑讨论章节推进、人物动机、反转、爽点、钩子等思路。
- 左侧对话接入 `/api/v1/cocreation/turn`，AI 会从对话中归纳 `asset_patch`，并自动调用资产保存接口写入作品资产，减少手动填表式编辑。
- 左侧下半区改为“资产与操作”：展示 AI 已沉淀资产，并保留启动/暂停/继续/导出、半自动模式、目标字数和高级 LLM 配置。
- 创作台布局进一步靠近“左侧 AI 编辑对话 + 中间正文与节点草稿 + 右侧教学检测”的工作台形态。
- 同步版本号：前端 [`package.json`](storyforge/frontend/package.json)、后端 [`pyproject.toml`](storyforge/pyproject.toml)、FastAPI 版本与页面 `APP_VERSION` 均提升至 `0.4.5`。
- 验证通过：`python -m compileall -q storyforge` 与 `npm run build`。

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
