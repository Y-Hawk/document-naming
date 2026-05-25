# Step 1 — Type Matching

**Applies to: `create` and `organize`.**

Resolve the correct type prefix for the filename. The AI should actively normalize similar or subsumed types to the standard type listed in `workspace.md`. Only when the type is completely unrecognizable or unrelated to any configured type, keep the original/caller-provided type and continue (no error).

---

## Process

1. Read the workspace config document at the path specified in `config.json` → `workspace_config_path`.
   * **If the config document cannot be read or the path is not configured**, stop and report:
     > `ERROR: workspace config document not found. Please configure "workspace_config_path" in config.json and ensure the file exists.`

2. Look up the target directory in the Directory→Type Mapping table to get the **standard type prefix**.
   * **If the directory is not found in the mapping**, keep the caller-provided/original type and continue (do NOT report an error).

3. Compare the caller-provided/original type against the standard type:
   * **Similar or subsumed** → normalize to the standard type (e.g. `guide`/`plan` → `方案`, `article`/`post` → `文章`, `other`/`misc` → `其它`).
   * **Completely unrelated** (e.g. `音乐`, `xyz123`) → keep original type, continue silently.

4. Use the resolved (or kept original) type for subsequent steps.

---

## Save Path Resolution

### Create

```
save path resolution (create):
  preferred: workspace config → target directory for the resolved type
  fallback: file's first-level parent directory matched against workspace config
  default:   no directory match → keep original type, save to caller-specified path, continue
```

### Organize

```
save path resolution (organize):
  preferred: file's current type matches current directory type → keep file in place, only rename type prefix
  fallback:  file's current type does NOT match current directory → query workspace config to find correct directory → move file there, then rename type prefix
  default:   no matching directory found for the file's type → keep file in place, rename type prefix only, continue silently
```

---

## Type Resolution Chain

```
type resolution:
  preferred: workspace config document → directory-mapped standard type (normalize similar/subsumed types)
  fallback:  file's first-level parent directory matched against workspace config
  default:   no match found → keep original/caller-provided type, do NOT report error, continue processing
```

## Type Normalization Rules

When the caller-provided type is similar to or a subset of a standard type in `workspace.md`, normalize it to the standard type. Examples:

| Caller-provided type | Standard type (workspace.md) | Action |
|---------------------|----------------------------|--------|
| `guide`, `plan`, `strategy` | `方案` | Normalize to `方案` |
| `question`, `topic`, `bank` | `题库` | Normalize to `题库` |
| `draft`, `wip` | `草稿` | Normalize to `草稿` |
| `final`, `published` | `定稿` | Normalize to `定稿` |
| `article`, `post`, `blog` | `文章` | Normalize to `文章` |
| `report`, `analysis` | `报告` | Normalize to `报告` |
| `spec`, `standard` | `规范` | Normalize to `规范` |
| `asset`, `image`, `media` | `素材` | Normalize to `素材` |
| `data`, `metric` | `数据` | Normalize to `数据` |
| `log`, `note`, `meeting` | `记录` | Normalize to `记录` |
| `script`, `code`, `automation` | `脚本` | Normalize to `脚本` |
| `daily`, `summary` | `日报` | Normalize to `日报` |
| `other`, `misc`, `uncategorized` | `其它` | Normalize to `其它` |
| `音乐`, `video_game`, `xyz123` | *(any)* | Keep original, do NOT normalize |
