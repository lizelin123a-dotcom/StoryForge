# StoryForge Notebook UI Architecture

本目录承载写作工作台的“活页手稿本”表现组件。目标是避免继续在全局 CSS 末尾叠加覆盖，而是用组件边界、布局契约和设计 token 稳定推进 UI。

## 设计原则

1. 业务状态留在 `App.vue` / `WriterStudio.vue`，notebook 组件只负责表现和事件转发。
2. 每个组件只拥有一块布局责任，避免一个文件同时控制整页所有视觉。
3. 装饰元素必须 `pointer-events: none`，不得遮挡正文、审稿、按钮。
4. 滚动边界清晰：左页、AI 对话、正文、页边批注各自控制内部滚动。
5. 后续接入真实素材时，只替换背景/道具层，不改业务结构。

## 组件清单

- `NotebookSpread.vue`：两页布局、中缝、页签插槽、后台抽屉插槽。
- `NotebookPage.vue`：通用纸页容器。
- `DeskNotesPanel.vue`：案头设定列表与空状态。
- `ReviewPanel.vue`：当前节点审稿、审阅按钮、保存/锁定草稿。
- `EditorChatPanel.vue`：Skill 标签、AI 消息、可应用补丁、输入框。
- `ManuscriptPage.vue`：章节标题、操作按钮、正文 textarea、字数页脚。
- `MarginDiagnosisStack.vue`：页边批注、写作信号、建议卡片。
- `PageTabs.vue`：目录/章节/日志标签。
- `DebugDrawer.vue`：后台札记、高级配置。

## Mitosis 使用判断

当前 StoryForge 是 Vue 单框架应用，且写作页有较多业务状态、SSE 和持久化操作。短期内不直接引入 Mitosis 编译链。我们采用 Mitosis 的组件设计思想：先形成可迁移的组件契约，再用 Vue SFC 稳定实现。

如果以后需要跨框架组件库，可把这些表现组件再迁移为 `.lite.tsx` Mitosis 源，并编译到 Vue/React。

## 下一步视觉重做入口

视觉重做不再追加到 `storybook.css`。等组件拆分稳定后，新建 `notebook-ui.css` 或逐步迁移到 scoped style，以 token 方式重建第一张参考图的材质系统。
