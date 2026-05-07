# StoryForge

StoryForge is an AI-assisted writing workspace for long-form fiction.

It treats writing as an iterative process: conversation, planning, drafting, reviewing, revising, and finally committing text into the manuscript. Instead of acting as a simple text generation button, StoryForge aims to make AI feel like a persistent editor beside the author.

## Overview

StoryForge is designed around a manuscript-first workflow:

1. Discuss the current chapter with an AI editor.
2. Generate or revise node drafts.
3. Review each draft before it enters the manuscript.
4. Write confirmed content into the chapter.
5. Diagnose the chapter from the margin.
6. Keep worldbuilding and desk notes nearby.

The current UI direction is a calm writing desk: a chat-like AI editor on the left, manuscript writing in the center, and margin notes on the right.

## Features

### AI Editor Chat

- Chat-style AI editor panel.
- Supports ongoing conversation around the current chapter and node.
- Skill tools can be selected from the composer area.
- Keeps the author in a familiar messaging workflow.

### Manuscript Workspace

- Chapter-centered writing area.
- Inline node review before content is written into the manuscript.
- Review actions for writing, rewriting, rollback, locking, and saving node drafts.
- Word count footer for current chapter and full book progress.

### Desk Notes

- Slide-out desk notes drawer.
- Stores worldbuilding, rules, characters, scenes, and other project assets.
- Kept out of the main writing area to avoid distracting from the manuscript.

### Margin Notes

- Side diagnosis panel for the current chapter.
- Displays checks for emotion, hooks, payoff, and conflict.
- Shows expected diagnosis items even before analysis has been run.

### Writing Control

- Start, pause, resume, and save controls.
- Fullscreen writing mode.
- Lightweight fixed toolbar designed to stay outside the main manuscript area.

### Local-first Persistence

- Local application workflow.
- SQLite persistence.
- Suitable for personal writing, prototyping, and iterative product development.

## Screenshots

> TODO: Add screenshots.

```md
![StoryForge Writing Workspace](docs/screenshots/writing-workspace.png)
```

## Tech Stack

### Backend

- Python
- FastAPI
- SQLite
- Pydantic

### Frontend

- Vue 3
- TypeScript
- Vite
- CSS

## Project Structure

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

## Getting Started

### 1. Clone

```bash
git clone https://github.com/lizelin123a-dotcom/StoryForge.git
cd StoryForge
```

### 2. Install backend dependencies

```bash
cd storyforge
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Run

On Windows, you can use:

```bash
start_storyforge.bat
```

Or run backend and frontend manually.

Backend:

```bash
cd storyforge
python run.py
```

Frontend:

```bash
cd storyforge/frontend
npm run dev
```

## Build

### Backend check

```bash
python -m compileall -q storyforge
```

### Frontend build

```bash
cd storyforge/frontend
npm run build
```

## Current Status

StoryForge is in active development.

The latest focus is the writing workspace UI:

- notebook-style writing layout
- AI chat panel
- inline node review
- margin diagnosis cards
- desk notes drawer
- fullscreen writing mode
- cleaner manuscript-first interaction

APIs, UI details, and data models may still change.

## Roadmap

- [ ] Improve chapter and outline navigation.
- [ ] Refine AI skill selection.
- [ ] Add richer manuscript versioning.
- [ ] Improve long-context writing memory.
- [ ] Add export formats.
- [ ] Add screenshot documentation.
- [ ] Polish the desktop writing experience.
- [ ] Improve error recovery and daemon state visibility.

## Design Direction

StoryForge aims for a calm, manuscript-first interface.

The UI avoids noisy fake textures and decorative clutter. The current direction is:

- warm paper-like workspace
- minimal writing surface
- chat-like AI editor
- subtle desk notes
- readable margin diagnosis
- low-friction review before writing into the manuscript

## Development Notes

The writing workspace is componentized under:

```text
storyforge/frontend/src/components/notebook/
```

Key files:

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

The UI layer is intentionally isolated in:

```text
storyforge/frontend/src/notebook-ui.css
```

This keeps the writing workspace easier to iterate without heavily modifying older global style files.

## License

TODO
