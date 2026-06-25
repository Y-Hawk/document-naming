# Document Naming

文档命名、文件生成、版本管理与归档的规范化技能。为内容创作工作空间提供统一命名格式、自动版本递增与旧版本归档能力。

> **English documentation**: [README.en.md](README.en.md)

## 特性

- 📝 **统一命名格式** — `Type_Title_YYYYMMDD_v<major.minor.patch>[_suffix]_Author.ext`，自动清理非法字符与空白
- 🔄 **语义化版本管理** — `major/minor/patch` 三级递增，可选 `.final`（定稿）与 `.refer`（参考）后缀
- 📦 **自动归档** — 修改文档时旧版本自动移入 `history/` 或 `refer/`，零残留
- ⚙️ **配置驱动** — 多来源合并，全部软回退，不会因配置缺失而中断
- 🔧 **技能调用** — 自然语言提示词触发，无需手动执行脚本

## 快速上手

> **铁律**：涉及文档内容的一切操作（新建、修改、调整、优化等），必须先调用此技能。不自行构造文件名，不跳过三步工作流，不区分"大改""小改"。
> 
> **格式强制验证**：只有 `allowed_extensions` 白名单中的文件类型才会被处理，不在白名单中的扩展名即使触发了技能也拒绝执行。

### 方案一：明确信息

用户提供完整参数，技能直接执行：

| 操作    | 提示词模板            | 示例                                   |
| ----- | ---------------- | ------------------------------------ |
| 新建文档  | `新建{类型}文档：{标题}`  | `新建方案文档：内容策略`                        |
| 修改文档  | `修改{文件名}，{递增级别}` | `修改方案_内容策略_..._v1.0.0_Hawk.md，minor` |
| 归档旧版本 | `归档{文件名}`        | `归档方案_内容策略_..._v1.0.0_Hawk.md`       |

递增级别：`major`（重构） / `minor`（增删） / `patch`（修错字）

### 方案二：自然语言（AI 自动判断）

用户只表达意图，AI 自动推断类型与递增级别：

| 操作   | 提示词模板         | 示例               |
| ---- | ------------- | ---------------- |
| 新建文档 | `新建关于{标题}的文档` | `新建关于内容策略的文档`    |
| 修改文档 | `修改{文件名}`     | `修改内容策略文档，重写了一半` |

**类型推断**：从工作空间配置 Directory→Type 映射匹配 → 无匹配则用 `fallback_dir_name`（默认 `other`）

**递增推断**：重写/重构 → `major` · 补充/增删 → `minor` · 改错字/调格式 → `patch`

> 修改文档后归档自动触发，无需单独调用。

---

> **触发词**：新建、创建、生成、修改、调整、编辑、优化、拆分、归档，以及任何涉及文档新建或修改的场景。

## 命名格式

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

示例：`guide_claw-content-strategy_20260407_v1.0.0_Hawk.md`

完整字段定义、回退规则与版本策略 → [references/rules.md](references/rules.md)

## 三步工作流

| 步骤                | 适用操作                | 说明                          | 详细文档                                                            |
| ----------------- | ------------------- | --------------------------- | --------------------------------------------------------------- |
| **Step 1** — 类型匹配 | `create`            | Directory→Type 映射匹配类型前缀     | [step1-type-matching.md](references/step1-type-matching.md)     |
| **Step 2** — 文件生成 | `create` / `modify` | 生成合规文件名并写入                  | [step2-file-generation.md](references/step2-file-generation.md) |
| **Step 3** — 文件归档 | `modify`            | 旧版本移入 `history/` 或 `refer/` | [step3-file-archive.md](references/step3-file-archive.md)       |

## 配置

合并顺序：工作空间配置文件（`enable_workspace_path=true` 且可读） → `config.local.json` → `config.json` → 硬编码默认值。全部软回退。

完整配置键、层级与回退链 → [SKILL.md Configuration 章节](SKILL.md)

### 目录与类型 — 两种配置模式

目录→类型映射（`directory_tree`）支持两种配置方式，读取时优先级：workspace 文件 > config dict。

**模式一：workspace 文件**

在 `references/workspace.md` 中以表格形式定义 Directory→Type Mapping 和 Sub-directory Structure。这里只是参考文档，在格式保持一致的前提下，可更改后存放在任何位置，只需把文件路径配置到`workspace_config_path`且`enable_workspace_path=true`，脚本会自动解析该文件生成 `directory_tree`，优先覆盖 config dict 中的值。

***注意：文档中的配置和目录表格必须保持与该文档格式一致，子目录可不设置。***

**模式二：config dict**

直接在 `config.json` / `config.local.json` 的 `workspace.directory_tree` 字典中配置，格式：

```json
{
  "draft": {"name": "draft", "type": "draft", "sub": {"<topic>": {"name": "<topic>"}}},
  "material": {"name": "material", "type": "material", "sub": {"illustration": {"name": "illustration"}, "ai-hot": {"name": "ai-hot"}}},
  "daily": {"name": "daily", "type": "daily", "sub": {}}
}
```

- `name`：目录名（也作为字典键）
- `type`：文件名类型前缀（Step 1 仅用此列匹配类型）
- `sub`：子目录嵌套字典，`{}` 表示无子目录

> **选择建议**：workspace 文件模式便于人工编辑和阅读；config dict 模式适合自动化或纯 JSON 环境。两种模式可共存——workspace 文件启用时覆盖 config dict 值，关闭时回退到 config dict。

> **配置建议**：可直接在 `config.json` 中填写个人配置值（如作者名、工作空间路径）。若需要将仓库推送至远程（GitHub/Gitee 等），建议将 `config.json` 复制为 `config.local.json`，再将个人配置值移入 `config.local.json`、`config.json` 恢复为空值模板，避免本地配置信息泄露至远程仓库。

## 目录结构

```
document-naming/
├── SKILL.md                      # 技能控制文件
├── config.json                   # 出厂默认配置
├── README.md                     # 中文说明
├── README.en.md                  # 英文说明
├── LICENSE                       # MIT 许可证
├── references/
│   ├── rules.md                  # 命名格式规范
│   ├── step1-type-matching.md    # Step 1 类型匹配
│   ├── step2-file-generation.md  # Step 2 文件生成
│   ├── step3-file-archive.md     # Step 3 文件归档
│   └── workspace.md              # 工作空间配置参考
└── scripts/
    └── naming.py                 # 命名工具脚本
```

> `config.local.json` 和 `scripts/__pycache__/` 被 `.gitignore` 排除，不出现在远程仓库中。

## 贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交修改 (`git commit -m 'Add your feature'`)
4. 推送分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)
