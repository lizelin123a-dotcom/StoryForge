# StoryForge 更新日志

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
