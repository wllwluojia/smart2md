# smart2md

> **专为 AI 知识库优化的智能文档编排引擎。**
> 告别繁琐的解析器配置。smart2md 自动将每份文档路由到最合适的专业后端，输出**结构化、紧凑、高质量的 Markdown**——完美适配 Obsidian、NotebookLM 与 RAG 流水线。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 为什么选择 smart2md？

大多数文档转 Markdown 工具的思路是**选一个解析器，一用到底**。处理简单 Word 文档没问题，但当你把扫描版 PDF、复杂表格型 Excel 和内容密集的 PPT 一起丢进去，效果往往就崩了。

**smart2md 不一样。** 它是一个编排层，而不只是一个转换器。

| | 同类单后端工具 | **smart2md** |
|---|---|---|
| **解析策略** | 一个引擎通吃所有格式 | 按文件类型自动路由到最优专业后端 |
| **输出质量** | 原始文字堆砌 | 结构化、紧凑的 Wiki 级 Markdown |
| **AI 就绪度** | 需要人工清理才能入库 | 归一化 Schema，开箱即用于 RAG 向量化 |
| **数据隐私** | 常依赖云端 API | 本地优先，默认无需任何云端鉴权 |
| **安装体验** | 手动配置繁琐依赖 | 一键 `install.sh` + `doctor.sh` 环境自检 |
| **目录处理** | 只能逐文件处理 | 完美镜像输入文件夹的原始层级结构 |

---

## ✨ 核心优势

### 🧠 智能多后端路由
smart2md 不会盲目地把所有文件推给同一个解析器。其内置路由引擎会读取文件类型和本地环境，将每份文档分发给最合适的专业工具：
- **Docling**（IBM Research）——处理复杂 PDF 与 DOCX
- **MinerU**（OpenDataLab）——处理扫描版 PDF 与 PPTX
- **pymupdf4llm**——PDF 极速提取快速通道
- **MarkItDown**（Microsoft）——可靠的万能兜底

### 📐 结构化、紧凑、高质量输出
简单的文字提取不足以支撑严肃的 AI 流水线。smart2md 的 Normalizer 保证：
- **清晰的标题层级**——无孤立碎片，无重复标题
- **紧凑的表格格式**——标准 Markdown 表格，而非松散的 ASCII 艺术
- **去除重复内容**——页眉、页脚、重复样板文本全部剔除
- **完整的段落结构**——保留句子边界，无断句换行

### 📂 完美镜像目录结构的批量处理
一次性处理整个知识库文件夹。输出端完美复刻源文件夹的**原始层级结构**——不打平、不改名。直接拖进 Obsidian 或 RAG 流水线即可使用。

### 🔒 本地优先，保护数据隐私
所有处理均在本地运行，默认不向任何外部 API 发送文件。非常适合处理敏感企业文档或个人知识库。

### ⚡ 一键安装 + 环境自检
```bash
bash install.sh
./smart2md doctor
```
安装脚本自动检测您机器上已有的工具并复用，`doctor` 命令秒级验证环境是否就绪。

---

## 🚀 快速开始

```bash
git clone https://github.com/wllwluojia/smart2md.git
cd smart2md
bash install.sh
./smart2md doctor
```

**转换单个文件：**
```bash
./smart2md "/path/to/document.pdf" "/path/to/output_dir"
```

**按原目录结构批量转换整个文件夹：**
```bash
./smart2md "/path/to/knowledge_base/" "/path/to/output_dir"
```
（输出目录中将自动生成一模一样的子文件夹层级，并填充转换好的 `.md` 文件）

---

## 📄 支持的输入格式

| 格式 | 扩展名 | 说明 |
|---|---|---|
| PDF | `pdf` | 智能路由：极速 / 标准 / 扫描 OCR 三条通道 |
| PowerPoint | `pptx`, `ppt` | 旧版 `.ppt` 自动转换后接入标准流程 |
| Word | `docx`, `doc` | 旧版 `.doc` 自动转换后接入标准流程 |
| Excel | `xlsx`, `xls` | 旧版 `.xls` 自动转换后接入标准流程 |
| 纯文本 | `txt` | 归一化处理，适配 Wiki 摄取 |
| Markdown | `md` | 直通并进行格式归一化与清理 |

---

## 📦 输出结构

每个处理后的文件会生成一组干净的输出：

```
output_dir/
├── document.pdf.md          ← 可读性强的 Wiki 级 Markdown（主要使用）
├── document.structured.md   ← 含排版元数据的机器可读版本
├── document.structured.json ← AI 流水线的标准结构化 Trace
├── document.mermaid.md      ← 图表提取（适用时）
└── _raw/                    ← 后端原生中间产物
```

**推荐使用方式：**
- 使用 `*.pdf.md` 进行人工阅读、Obsidian 沉淀和 NotebookLM 投喂
- 使用 `*.structured.json` 进行 RAG 向量索引和深度 AI 分析
- 将 `_raw/` 作为调试资产存档

---

## ⚙️ 安装选项

**默认安装（推荐）：**
```bash
bash install.sh
```
安装内容：`docling`、`mineru`、`markitdown`、`PyMuPDF`、`pymupdf4llm`

**轻量安装（仅核心）：**
```bash
bash install.sh --with-backends core
```
安装内容：`markitdown`、`PyMuPDF`

**离线/归档模式：**
```bash
bash install.sh --from-archive /path/to/downloads --with-backends recommended
```

---

## 🔀 默认路由规则

| 输入 | 主要后端 | 降级后端 |
|---|---|---|
| `pdf`（数字版） | `pymupdf4llm`（极速）→ `docling`（标准） | `markitdown` |
| `pdf`（扫描版） | `mineru` | `local-pdf` |
| `docx` | `docling` | `markitdown` |
| `pptx` | `mineru` → `native-pptx` | `markitdown` |
| `xlsx` | `mineru` | `markitdown` |
| `txt` / `md` | `markitdown` | — |

路由规则完全可在 [`config/defaults.toml`](config/defaults.toml) 中自定义。

---

## 💡 为什么开发这个项目？

在构建个人数字大脑和投喂 AI（如 Hermes）时，我们往往面临各种格式文档"喂不进去"或"喂进去排版乱套"的痛点。市面上虽然有各种解析库，但通常各自为战（有的擅长 PDF，有的擅长 Excel）。

本项目通过一层优雅的**编排路由网关**，将业内最强的多个解析利器（Docling、MinerU、MarkItDown 等）统揽于麾下。你只需要一个简单的入口命令，它就能自动判别文件并分发给最合适的底层解析器，最终输出干干净净、结构严谨的 Markdown 文件。

对于需要批量把杂乱文件夹塞进大模型或知识库的极客玩家来说，这是必不可少的胶水层工具。

---

## 🗂️ 项目结构

```
smart2md/
├── README.md
├── README_ZH.md
├── LICENSE
├── install.sh
├── upgrade.sh
├── doctor.sh
├── smart2md              ← CLI 入口
├── config/
│   └── defaults.toml
├── references/
├── scripts/
│   ├── smart2md_cli_main.py
│   └── smart2md_lib/
└── .github/workflows/
```

---

## 🤝 贡献与许可

欢迎提交 Issue 与 Pull Request，共同打造最干净流畅的文档转 Markdown 体验！

本项目采用 [MIT License](LICENSE) 开源协议。
