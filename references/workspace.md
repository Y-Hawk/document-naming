# Workspace Reference

Source of truth for directory→type mapping used in Step 1 type resolution.

---

## Workspace Root

```
C:/Users/admin.DESKTOP-FETRK5E/Desktop/内容创作专家
```

---

## Directory→Type Mapping

Directories are created on demand; only create a directory when a document belongs there.

| First-level Directory | Type Prefix | Use Case |
|-----------------------|-------------|----------|
| `00 方案/`            | `方案`      | Strategy documents, planning, frameworks |
| `01 题库/`            | `题库`      | Article topic lists, headline lists |
| `02 草稿/`            | `草稿`      | Drafts and in-progress writing |
| `03 定稿/`            | `定稿`      | Finalised documents (filenames carry `_final`) |
| `04 文章/`            | `文章`      | Published posts (公众号 / 头条 / 小红书 / 知乎) |
| `05 报告/`            | `报告`      | Analysis reports, retrospectives, research |
| `06 规范/`            | `规范`      | Standards and specification documents |
| `07 素材/`            | `素材`      | Images, audio, video, hot-topic feeds |
| `08 数据/`            | `数据`      | Platform operations data |
| `09 记录/`            | `记录`      | Logs and meeting notes |
| `10 脚本/`            | `脚本`      | Code and automation scripts |
| `11 日报/`            | `日报`      | Daily reports and work summaries |
| `99 其它/`            | `其它`      | Files that don't fit any category above |

---

## Sub-directory Structure

Only second-level directories are specified. Lower levels are not constrained by this config.

| First-level Directory | Second-level Directory | Applicable Condition |
|-----------------------|------------------------|----------------------|
| `00 方案/`            | *(none — files go directly under first-level)* | Annual strategy and planning documents |
| `01 题库/`            | *(none — files go directly under first-level)* | Topic bank entries |
| `02 草稿/`            | Named by topic or series (e.g. `01 AI的前世今生/`) | Group drafts by topic or series; create sub-dir when ≥ 2 related drafts exist |
| `03 定稿/`            | *(none — files go directly under first-level)* | Finalised documents |
| `04 文章/`            | `公众号/` / `头条/` / `小红书/` / `知乎/` | One sub-dir per publishing platform; required before placing any article file |
| `05 报告/`            | *(none — files go directly under first-level)* | Reports and retrospectives |
| `06 规范/`            | *(none — files go directly under first-level)* | Specification and standard documents |
| `07 素材/`            | `配图/` / `AI热点/` | `配图/` for article illustration assets; `AI热点/` for daily hot-topic news feeds |
| `08 数据/`            | *(none — files go directly under first-level)* | Platform operation data files |
| `09 记录/`            | *(none — files go directly under first-level)* | Logs and meeting notes |
| `10 脚本/`            | *(none — files go directly under first-level)* | Scripts and automation code |
| `11 日报/`            | *(none — files go directly under first-level)* | Daily summary reports |
| `99 其它/`            | *(none — files go directly under first-level)* | Uncategorised files |

---

## Notes

- Match on the **first-level directory name only** when resolving type from a file path.
- `04 文章/` has multiple second-level platform sub-directories; type is always `文章` regardless of platform.
- `11 日报/` has its own type prefix `日报`; distinguish from `05 报告/` by directory.
- If a file sits outside any known first-level directory, **report an error** — do not apply a default type.
- If the workspace config document cannot be read, **report an error** and prompt the user to configure the relevant entries; do not apply any fallback defaults silently.
