# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

## 本仓库额外使用的标签

| 标签 | 含义 |
| --- | --- |
| `spec` | `to-spec` 产出的规格 issue，描述「要建成什么样」 |
| `tutorial` | 教程写作相关（`docs/lessons/` 下的课文、notebook、配图） |

GitHub 默认已自带 `wontfix`；其余四个（`needs-triage` / `needs-info` / `ready-for-agent` /
`ready-for-human`）需要在首次使用前创建。
