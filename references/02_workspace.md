# Workspace Reference

Shared by `document-naming` and `workspace-management`. Defines root path, directory→type mapping, sub-directory layout, and runtime configuration.

---

## Configuration

Required settings in this document. Skills read these values at startup.

| Key                 | Value                                            | Description                                                  |
| ------------------- | ------------------------------------------------ | ------------------------------------------------------------ |
| `workspace_root`    | `""`                                              | Absolute path to the workspace root. Empty = read from config dict instead. |
| `archive_dir_name`  | `"history"`                                      | Sub-directory name for historical file versions.              |
| `refer_dir_name`    | `"refer"`                                        | Sub-directory name for reference file versions.               |
| `fallback_dir_name` | `"other"`                                        | Directory name for files matching no known type. Must be ASCII, no numeric prefix, no spaces. |

### workspace_root — Resolution Priority

First match wins:

1. `workspace_root` from this file (if non-empty).
2. `workspace_root` from config dict (`config.local.json` → `config.json`).
3. User's Desktop directory (AI fallback when all values empty).

---

## Directory→Type Mapping

Resolves a document's type prefix from its first-level directory. Directories are created on demand.

| First-level Directory | Type Prefix | Use Case                             |
| --------------------- | ----------- | ------------------------------------ |
| `00 方案/`             | `方案`       | Strategy docs, plans, frameworks     |
| `02 草稿/`             | `draft`     | Drafts and in-progress writing       |
| `03 定稿/`             | `定稿`       | Finalized drafts (auto `_final`)     |
| `04 文章/`             | `文章`       | Published articles per platform      |
| `05 报告/`             | `报告`       | Analysis reports, reviews, research  |
| `06 规范/`             | `规范`       | Standards, specification docs        |
| `07 素材/`             | `素材`       | Images, audio, video assets         |
| `08 数据/`             | `数据`       | Operational data per platform        |
| `09 记录/`             | `记录`       | Logs, meeting notes                  |
| `10 脚本/`             | `脚本`       | Code, automation scripts             |
| `11 日报/`             | `日报`       | Daily reports, work summaries        |
| `98 意见/`             | `意见`       | Feedback and revision comments       |
| `99 其它/`             | `其它`       | Unclassified files                   |
| `material/`           | `material`  | Resources, assets, trending news     |
| `daily/`              | `daily`     | Daily reports and work summaries     |

- Match on first-level directory only.
- Files outside all known directories keep their original prefix — never error.

---

## Sub-directory Structure

Second-level layout. Unlisted directories have no sub-directories; files go directly under them.

| Parent       | Sub-directory   | Condition                                    |
| ------------ | --------------- | -------------------------------------------- |
| `draft/`     | `<topic>/`      | Group by topic/series; create when ≥ 2 items |
| `material/`  | `illustration/` | Article illustration assets                  |
| `material/`  | `ai-hot/`       | Daily AI hot-topic news                      |
