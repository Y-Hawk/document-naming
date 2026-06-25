# Document Naming

文档命名、文件生成、版本管理与归档的规范化工具。为内容创作工作空间提供统一的文件命名格式、自动版本递增与旧版本归档能力。

> **English documentation**: [README.en.md](README.en.md)

## 特性

- 📝 **统一命名格式** — `Type_Title_YYYYMMDD_v<major.minor.patch>[_suffix]_Author.ext`，自动清理非法字符与空白
- 🔄 **语义化版本管理** — 支持 `major/minor/patch` 三级递增，可选 `.final`（定稿）与 `.refer`（参考）后缀
- 📦 **自动归档** — 修改文档时旧版本自动移入 `history/` 或 `refer/` 子目录，绝不残留
- ⚙️ **配置驱动** — 双来源合并（技能配置 + 工空间配置），全部软回退，不会因配置缺失而中断
- 🔧 **CLI + Python API** — 纯标准库实现，零外部依赖，Python 3.10+ 即可运行

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/document-naming.git
cd document-naming
```

### 30 秒上手

```bash
# 生成合规文件名
python scripts/naming.py generate "内容策略" md --type guide --author Hawk

# 版本递增
python scripts/naming.py bump "guide_内容策略_20260625_v1.0.0_Hawk.md" minor

# 归档旧版本
python scripts/naming.py archive "guide_内容策略_20260625_v1.0.0_Hawk.md"
```

### Python 调用

```python
from naming import generate_name, bump_version, archive_old_version, parse_filename

# 生成合规文件名（无磁盘 I/O）
result = generate_name("内容策略", "md", file_type="guide", author="Hawk")

# 版本递增
bumped = bump_version("guide_内容策略_20260625_v1.0.0_Hawk.md", "minor")

# 归档旧版本
dest = archive_old_version("guide_内容策略_20260625_v1.0.0_Hawk.md")

# 解析合规文件名
parsed = parse_filename("guide_内容策略_20260625_v1.0.0_Hawk.md")
```

## 命名格式

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

示例：`guide_claw-content-strategy_20260407_v1.0.0_Hawk.md`

### 字段定义

| 字段 | 规则 |
|------|------|
| **Type** | 由 Step 1 解析，可为任意非空字符串。通过工作空间配置的「目录→类型映射」关联到 L1 目录 |
| **Title** | ≤ 30 字符，自动移除 `\/:*?"<>|` 及空白。清理后为空则报错 |
| **Date** | `YYYYMMDD`，始终为当天日期 |
| **Version** | `v<major>.<minor>.<patch>` — 语义化版本。新文档为 `v1.0.0` |
| **Suffix** | 可选 `.final`（定稿/已审批）或 `.refer`（参考/备份） |
| **Author** | 优先级：调用方提供 → `config.json` → `"Unknown"` |
| **Extension** | 优先级：调用方提供 → `config.json` → `.md` |

### 版本策略

| 递增级别 | 适用场景 |
|----------|----------|
| `major` | 主题/内容/框架完全重构 |
| `minor` | 内容增删、改写 |
| `patch` | 格式修正、语法、错字 |

### 版本后缀与归档路由

| 后缀 | 含义 | 归档行为 |
|------|------|----------|
| （无） | 工作进行中 | 移入 `history/` |
| `.final` | 定稿/已审批 | **不移入**，留在原位 |
| `.refer` | 参考/备份 | 移入 `refer/` |

## 工作流

所有涉及文档内容的新建或修改操作，必须先调用此技能。

**铁律**：不自行构造文件名，不跳过三步工作流，不区分"大改""小改"。

### Step 1 — 类型匹配（`create`）

根据工作空间配置的「目录→类型映射」解析文件名前缀：

| 场景 | 行为 |
|------|------|
| 调用方提供类型，且匹配已知类型 | 规范化为匹配的类型 |
| 调用方提供类型，但不匹配任何已知类型 | 保留调用方类型（不报错） |
| 调用方未提供类型 | 使用 `fallback_dir_name`（默认 `"other"`） |

### Step 2 — 文件生成（`create` + `modify`）

**新建**：根据 Step 1 解析的类型生成合规文件名，确定保存路径并写入文件。

保存路径规则：
- **L1**：类型匹配到目录映射 → 使用映射目录；未匹配 → `99 <fallback_dir_name>/`
- **L2**：遵循工作空间配置的子目录结构，不存在则创建

**修改**：
1. 解析现有合规文件名的版本段
2. 按语义化版本递增（`major/minor/patch`）
3. 日期刷新为当天
4. 仅替换版本和日期，标题、类型、作者、扩展名保持不变
5. 新文件写入原目录，旧文件由 Step 3 归档

### Step 3 — 文件归档（`modify`）

修改后自动将旧版本文件移入对应子目录：

| 后缀 | 目标目录 | 配置键 | 默认值 |
|------|----------|--------|--------|
| （无） | `<源目录>/history/` | `archive_dir_name` | `history` |
| `.refer` | `<源目录>/refer/` | `refer_dir_name` | `refer` |
| `.final` | **不移入** | — | — |

归档流程：验证源文件 → 路由到目标目录 → 创建目录 → **移动**文件 → 验证源文件已删除

> **关键**：必须使用移动操作（`mv`/`Move-Item`/`shutil.move`），绝不使用复制，避免旧版本残留在主目录。

| 平台 | 正确 | 错误 |
|------|------|------|
| Git Bash | `mv` | ~~`cp`~~ |
| PowerShell | `Move-Item` | ~~`Copy-Item`~~ |
| Python | `shutil.move()` | ~~`shutil.copy()`~~ |

## 配置

运行时配置从两个来源合并，任一来源不可读均不中断执行：

| 来源 | 文件 | 提供的配置项 |
|------|------|-------------|
| **技能配置** | `config.json` | `default_author`、`default_extension`、`default_workspace_root`、`workspace_config_path` |
| **工作空间配置** | `workspace_config_path` 指定的文件 | `workspace_root`、`archive_dir_name`、`refer_dir_name`、`fallback_dir_name`；目录→类型映射 |

回退链（全部软回退）：

| 配置键 | 优先级 |
|--------|--------|
| `workspace_root` | 调用方指定 → Desktop → 上下文/系统匹配目录 |
| `archive_dir_name` | 工作空间配置 → `history` |
| `refer_dir_name` | 工作空间配置 → `refer` |
| `fallback_dir_name` | 工作空间配置 → `other` |
| `default_author` | `config.json` → `Unknown` |
| `default_extension` | `config.json` → `.md` |

### config.json 示例

```json
{
  "default_author": "Hawk",
  "default_extension": "md",
  "default_workspace_root": "C:/Users/admin/Desktop/内容创作专家",
  "workspace_config_path": "C:/Users/admin/.workbuddy/WORKSPACE.md"
}
```

## CLI 参考

```bash
# 生成新文件名
python scripts/naming.py generate <title> <ext> \
    --type <type> --author <author> \
    [--date YYYYMMDD] [--suffix final|refer]

# 版本递增
python scripts/naming.py bump <filename> <major|minor|patch>

# 归档旧版本
python scripts/naming.py archive <file_path>
```

### 输出示例

```bash
# 生成
$ python scripts/naming.py generate "内容策略" md --type guide --author Hawk
{"name":"guide_内容策略_20260625_v1.0.0_Hawk.md","type":"guide","title":"内容策略","date":"20260625","version":"v1.0.0","suffix":"","author":"Hawk","ext":"md"}

# 递增
$ python scripts/naming.py bump "guide_内容策略_20260625_v1.0.0_Hawk.md" minor
{"old_name":"guide_内容策略_20260625_v1.0.0_Hawk.md","new_name":"guide_内容策略_20260625_v1.1.0_Hawk.md","old_version":"v1.0.0","new_version":"v1.1.0"}

# 归档
$ python scripts/naming.py archive "guide_内容策略_20260625_v1.0.0_Hawk.md"
{"archived":".../guide_内容策略_20260625_v1.0.0_Hawk.md","to":".../history/guide_内容策略_20260625_v1.0.0_Hawk.md"}
```

## Python API 参考

| 函数 | 用途 |
|------|------|
| `generate_name(title, ext, file_type, author, date_str, suffix)` | 生成合规文件名（无磁盘 I/O），返回结构化 dict |
| `bump_version(filename, level)` | 版本递增 + 日期刷新，返回新旧文件名与版本 |
| `archive_old_version(file_path)` | 移动旧版本到归档目录，返回目标 Path |
| `parse_filename(filename)` | 解析合规文件名为结构化 dict，不合规返回 None |

## 目录结构

```
document-naming/
├── SKILL.md              # 技能控制文件（触发条件、工作流、配置说明）
├── config.json           # 技能级默认配置
├── README.md             # 中文说明文档
├── README.en.md          # 英文说明文档
├── references/
│   ├── rules.md          # 命名格式规范、字段定义、版本策略
│   ├── step1-type-matching.md   # Step 1 类型匹配规则
│   ├── step2-file-generation.md # Step 2 文件生成规则
│   └── step3-file-archive.md    # Step 3 文件归档规则
└── scripts/
    └── naming.py         # 命名工具（CLI + Python API）
```

## 系统要求

- Python 3.10+（使用 `dict | None` 类型语法）
- 无外部依赖，纯标准库实现

## 贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交修改 (`git commit -m 'Add your feature'`)
4. 推送分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)
