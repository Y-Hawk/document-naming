# Workspace Reference

Defines the workspace structure used by the document-naming skill: root path, directory→type mapping, sub-directory layout, and workspace-level configuration values.

---

## Workspace Root

**Resolution priority** (first match wins):

1. Caller-specified directory (highest priority).
2. Fall back to the user's Desktop directory.
3. If Desktop cannot be determined, match a directory from context or system — do NOT report an error.

---

## Directory→Type Mapping

Used by Step 1 to resolve a document's type prefix from its target directory. Directories are created on demand.

| First-level Directory | Type Prefix | Use Case |
|-----------------------|-------------|----------|
| `00 方案/`            | `方案`      | 策略文档、规划、框架 |
| `01 题库/`            | `题库`      | 文章选题、标题列表 |
| `02 草稿/`            | `草稿`      | 草稿和进行中的写作 |
| `03 定稿/`            | `定稿`      | 已定稿文档 |
| `04 文章/`            | `文章`      | 已发布文章（公众号/头条/小红书/知乎） |
| `05 报告/`            | `报告`      | 分析报告、复盘、调研 |
| `06 规范/`            | `规范`      | 标准和规范文档 |
| `07 素材/`            | `素材`      | 配图、音频、视频、热点新闻 |
| `08 数据/`            | `数据`      | 各平台运营数据 |
| `09 记录/`            | `记录`      | 日志和会议记录 |
| `10 脚本/`            | `脚本`      | 代码和自动化脚本 |
| `11 日报/`            | `日报`      | 日报和工作总结 |

**Resolution rules**:
- Match on first-level directory name only.
- `04 文章/` has platform sub-directories; type is always `文章` regardless of platform.
- If a file sits outside any known directory, keep its original type prefix — do NOT error.

---

## Sub-directory Structure

Second-level directory layout. Directories not listed here have no sub-directories — files go directly under them.

| Second-level Directory | Applicable Condition |
|------------------------|----------------------|
| `02 草稿/` → `<topic>/` | Group drafts by topic/series; create when ≥ 2 related drafts exist |
| `03 定稿/` → `<topic>/` | Group finalised documents by topic/series; create when ≥ 2 related docs exist |
| `04 文章/` → `<platform>/` | Group by publishing platform (公众号/头条/小红书/知乎) |
| `07 素材/` → `配图/` | Article illustration assets |
| `07 素材/` → `AI热点/` | Daily AI hot-topic news |

---

## Configuration

Workspace-level values used by the skill at runtime. Read by `naming.py` → `_merge_workspace_config()`.

| Key | Purpose | Default |
|-----|---------|---------|
| `workspace_root` | Absolute path to workspace root. Resolution: caller-specified → Desktop → context/system-matched | — |
| `archive_dir_name` | Sub-directory for archived old versions (Step 3); auto-created | `"history"` |
| `refer_dir_name` | Sub-directory for `.refer`-suffixed reference documents (Step 3); auto-created | `"refer"` |
| `fallback_dir_name` | Directory name when type has no match; placed as `99 <name>/` under workspace root (Step 1); auto-created | `"other"` |

If a required key has no default and cannot be resolved from either source, emit a warning and continue with the nearest safe fallback. Do NOT halt.
