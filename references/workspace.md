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
| `00 方案/`            | `plan`      | Strategy documents, planning, frameworks |
| `01 题库/`            | `topic`     | Article topic lists, headline lists |
| `02 草稿/`            | `draft`     | Drafts and in-progress writing |
| `03 定稿/`            | `final`     | Finalised documents (filenames carry `_final`) |
| `04 文章/`            | `article`   | Published posts (公众号 / 头条 / 小红书 / 知乎) |
| `05 报告/`            | `report`    | Analysis reports, retrospectives, research |
| `06 规范/`            | `standard`  | Standards and specification documents |
| `07 素材/`            | `asset`     | Images, audio, video, hot-topic feeds |
| `08 数据/`            | `data`      | Platform operations data |
| `09 记录/`            | `record`    | Logs and meeting notes |
| `10 脚本/`            | `script`    | Code and automation scripts |
| `11 日报/`            | `report`    | Daily reports and work summaries |
| `99 其它/`            | `other`     | Files that don't fit any category above |

---

## Sub-directory Structure

| First-level | Second-level | Third-level | Fourth-level |
|-------------|--------------|-------------|--------------|
| `00 方案/`  | `<year>/`    | —           | —            |
| `01 题库/`  | `<year>/`    | `<month>/`  | —            |
| `02 草稿/`  | `<year>/`    | `<month>/`  | —            |
| `03 定稿/`  | `<year>/`    | `<month>/`  | —            |
| `04 文章/`  | `公众号/` `头条/` `小红书/` `知乎/` | `<year>/` | `<month>/` |
| `05 报告/`  | `<year>/`    | `<month>/`  | —            |
| `06 规范/`  | `<year>/`    | —           | —            |
| `07 素材/`  | `配图/` `AI热点/` | `<year>/` | `<month>/` |
| `08 数据/`  | `<year>/`    | `<month>/`  | —            |
| `09 记录/`  | `<year>/`    | `<month>/`  | —            |
| `10 脚本/`  | `<year>/`    | `<month>/`  | —            |
| `11 日报/`  | `<year>/`    | `<month>/`  | —            |
| `99 其它/`  | `<year>/`    | `<month>/`  | —            |

`<year>` format: `2026`  |  `<month>` format: `2026-05`

---

## Notes

- Match on the **first-level directory name only** when resolving type from a file path.
- `04 文章/` has multiple second-level platform sub-directories; type is always `article` regardless of platform.
- `11 日报/` shares type prefix `report` with `05 报告/`; distinguish by directory, not type.
- If a file sits outside any known first-level directory, fall back to `default_type` in `config.json` (`"other"`).
