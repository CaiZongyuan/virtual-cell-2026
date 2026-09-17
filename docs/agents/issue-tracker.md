# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues in
`CaiZongyuan/virtual-cell-2026`. Use the `gh` CLI for all operations.

## 本地注意事项（本仓库特有）

**`gh` 必须能读到仓库。** 本仓库通过 UNC 路径访问，Windows 侧 git 会报
`detected dubious ownership`，而 `gh` 内部要跑 git，因此 `gh issue ...` 会直接失败
（报错原文就是 git 的 dubious ownership）。一次性修好：

```bash
git config --global --add safe.directory '%(prefix)///wsl.localhost/Ubuntu24.04/home/caii/projects/virtual-cell-2026'
```

如果哪天换了挂载路径，用 `gh --repo CaiZongyuan/virtual-cell-2026 ...` 显式指定仓库绕开。

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`。多行 body 用 heredoc 或
  `--body-file <path>`；**中文 body 一律走 `--body-file`**（Windows 命令行传中文会被转码成 `?`）。
- **Read an issue**: `gh issue view <number> --comments`，必要时配 `--json` + `jq` 取 labels。
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments`
- **Comment on an issue**: `gh issue comment <number> --body-file <path>`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

## 本仓库的 issue 词汇

除了标准的 triage 标签（见 `triage-labels.md`），本仓库的 issue 分两类：

- **spec issue**：由 `to-spec` 产出，描述「要建成什么样」。带 `spec` 标签。
- **ticket issue**：由 `to-tickets` 产出，是 tracer-bullet 垂直切片，带 `ready-for-agent`。

阻塞关系用 GitHub **原生 issue dependencies**（UI 可见），命令与「blocker 的数据库 id 而非
issue number」这个坑见 `.agents/skills/setup-matt-pocock-skills/issue-tracker-github.md`；
原生依赖不可用时退回 body 顶部的 `Blocked by: #<n>` 一行。

## Pull requests as a triage surface

**PRs as a request surface: no.**

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.
