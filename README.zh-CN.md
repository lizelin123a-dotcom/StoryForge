# StoryForge

StoryForge 是一个面向长篇小说创作的 AI 写作工作台。

它把写作视为一个持续迭代的过程：对话、规划、起草、审阅、修改，最后再把确认后的内容写入正文。StoryForge 的目标不是提供一个简单的“生成文本”按钮，而是让 AI 更像一位常驻编辑，陪在作者身边参与真实创作流程。

## 项目概览

StoryForge 围绕“正文优先”的写作流程设计：

1. 和 AI 编辑讨论当前章节。
2. 生成或修改节点草稿。
3. 在草稿写入正文前进行审阅。
4. 将确认后的内容写入章节正文。
5. 在页边批注中检查章节问题。
6. 随时查看案头设定、世界观、人物和规则。

当前界面方向是一个安静的写作工作台：左侧是聊天式 AI 编辑，中间是正文写作区，右侧是页边批注。

## 功能特性

### AI 编辑对话

- 聊天软件式 AI 编辑面板。
- 围绕当前章节和节点持续对话。
- 可通过输入区工具入口选择不同 Skill。
- 让作者在熟悉的聊天体验中推进创作。

### 正文写作区

- 以章节正文为中心的写作界面。
- 节点草稿在写入正文前先审阅。
- 支持写入、改后写入、回滚、锁定、保存节点草稿。
- 底部显示本章字数、全书字数和当前写作状态。

### 案头设定

- 左侧滑出的案头设定抽屉。
- 用于沉淀世界观、规则、人物、场景等项目资料。
- 默认不占据主写作区，避免干扰正文写作。

### 页边批注

- 右侧章节诊断区。
- 支持检查情绪、钩子、爽点、矛盾等维度。
- 即使尚未检测，也会展示待检测项目，让作者知道系统会关注什么。

### 写作控制

- 支持开始、暂停、继续、保存。
- 支持全屏写作模式。
- 轻量固定工具栏放在主写作区之外，尽量不干扰正文。

### 本地优先

- 本地运行。
- SQLite 持久化。
- 适合个人创作、产品原型和持续迭代。

## 截图

> TODO：添加项目截图。

```md
![StoryForge 写作工作台](docs/screenshots/writing-workspace.png)
```

## 技术栈

### 后端

- Python
- FastAPI
- SQLite
- Pydantic

### 前端

- Vue 3
- TypeScript
- Vite
- CSS

## 项目结构

```text
StoryForge/
├── storyforge/
│   ├── application/
│   │   └── daemon/
│   ├── infrastructure/
│   │   └── persistence/
│   ├── interfaces/
│   │   └── api/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── components/notebook/
│   │   │   ├── notebook-ui.css
│   │   │   └── main.ts
│   │   └── package.json
│   ├── requirements.txt
│   └── run.py
├── start_storyforge.bat
├── stop-storyforge.bat
└── README.md
```

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/lizelin123a-dotcom/StoryForge.git
cd StoryForge
```

### 2. 安装后端依赖

```bash
cd storyforge
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动项目

Windows 下可以直接使用：

```bash
start_storyforge.bat
```

也可以手动分别启动后端和前端。

后端：

```bash
cd storyforge
python run.py
```

前端：

```bash
cd storyforge/frontend
npm run dev
```

## 构建与检查

### 后端检查

```bash
python -m compileall -q storyforge
```

### 前端构建

```bash
cd storyforge/frontend
npm run build
```

## 当前状态

StoryForge 仍处于活跃开发阶段。

近期重点是写作工作台 UI：

- 笔记本式写作布局
- AI 聊天面板
- 节点内联审阅
- 页边诊断卡片
- 案头设定抽屉
- 全屏写作模式
- 更干净的正文优先交互

API、UI 细节和数据模型仍可能继续变化。

## Roadmap

- [ ] 优化章节和目录导航。
- [ ] 细化 AI Skill 选择体验。
- [ ] 增加更完整的正文版本管理。
- [ ] 改进长上下文写作记忆。
- [ ] 增加更多导出格式。
- [ ] 补充截图文档。
- [ ] 打磨桌面端写作体验。
- [ ] 改进错误恢复和写作守护进程状态展示。

## 设计方向

StoryForge 追求安静、清晰、以正文为中心的创作界面。

当前 UI 方向避免混乱的伪材质和过度装饰，重点是：

- 温暖的纸面工作区
- 简洁的正文写作面
- 聊天式 AI 编辑
- 轻量案头设定
- 可读的页边诊断
- 写入正文前的低摩擦审阅流程

## 开发说明

写作工作台组件位于：

```text
storyforge/frontend/src/components/notebook/
```

关键文件：

```text
WriterStudio.vue
notebook-ui.css
EditorChatPanel.vue
ManuscriptPage.vue
ReviewPanel.vue
MarginDiagnosisStack.vue
DeskNotesPanel.vue
NotebookSpread.vue
PageTabs.vue
DebugDrawer.vue
```

新的写作工作台视觉层集中在：

```text
storyforge/frontend/src/notebook-ui.css
```

这样可以尽量减少对旧全局样式的干扰，让写作区 UI 更容易继续迭代。

## 许可证

TODO
