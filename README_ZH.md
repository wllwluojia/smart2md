# Any2MD

> 为 Hermes 与 Obsidian 量身打造的文档结构化提取与 Markdown 转换引擎。

Any2MD 是一个强大的文档处理与编排层，旨在将各类复杂格式的文档（PDF、Office 文档等）高质量、结构化地转换为 Markdown 文件。它可以作为命令行工具独立运行，支持单文件转换，也支持**按照源文件夹的树状结构进行原样批量转化**。配合 Hermes 或 Obsidian 使用，知识摄取体验极其丝滑。

---

## ✨ 核心特性

- **📂 完美保持目录结构**：支持对整个文件夹进行批量处理，并在输出端完美复刻源文件夹的树状层级，让你的整套资料库零成本迁移至 Wiki。
- **🔄 万物皆可转**：原生支持 `pdf`, `pptx`, `docx`, `xlsx`, `md`，并能优雅地处理传统旧版 Office 格式 (`ppt`, `doc`, `xls`)。
- **🧠 智能路由与本地优先**：内置智能分配引擎，绝不把所有文件塞给同一个解析器。系统会根据文件类型和本地环境，优先调用最适合的本地专业工具（如 `Docling`、`MinerU`、`PyMuPDF`），保护数据隐私的同时提供极致解析精度。
- **🧬 双轨输出机制**：
  - `*.ext.md`：高可读性的标准 Markdown 文件，完美适配 Hermes 提取、人类阅读和 Obsidian 沉淀。
  - `*.structured.json/md`：保留坐标和底层排版信息的机器可读文件，为更深度的 AI 结构化分析提供“骨骼数据”。
- **⚡ 极简命令行 (CLI)**：提供 `any2md` 核心指令，一行代码完成复杂的文档提取与分发，并附带完善的 `install` 与 `doctor` 环境体检流程。

## 💡 为什么开发这个项目？

在构建个人数字大脑和投喂 AI（如 Hermes）时，我们往往面临各种格式文档“喂不进去”或“喂进去排版乱套”的痛点。市面上虽然有各种解析库，但通常各自为战（有的擅长 PDF，有的擅长 Excel）。

本项目通过一层优雅的**编排路由网关**，将业内最强的多个解析利器（Docling, MinerU, MarkItDown 等）统揽于麾下。你只需要一个简单的入口命令，它就能自动判别文件并分发给最合适的底层解析器，最终吐出干干净净的 Markdown 文件。对于需要批量把杂乱文件夹塞进大模型或知识库的极客玩家来说，这是必不可少的胶水层工具。

## 🚀 快速开始

### 1. 一键安装

只需一行命令，安装脚本会自动为你配置好虚拟环境，并优先复用你机器上已有的核心解析库（如未安装则会自动帮你装好推荐的本地后端）：

```bash
git clone https://github.com/<你的用户名>/Any2MD.git
cd Any2MD
bash install.sh
```

检查环境依赖是否健康：
```bash
./any2md doctor
```

### 2. 丝滑使用

**转换单个文件：**
```bash
./any2md "/path/to/your/document.pdf" "/path/to/output_dir"
```

**按照原目录结构批量转换整个文件夹：**
```bash
./any2md "/path/to/your/knowledge_base_folder" "/path/to/output_dir"
```
（输出目录中会自动生成一模一样的子文件夹层级，并填充转换好的 `.md` 文件）

## ⚙️ 进阶配置与架构

本工具完全由配置文件驱动，你可以自定义不同文件的路由策略（位于 `config/defaults.toml` 中）。

默认的路由策略示例：
- `pdf` -> PyMuPDF 初判 -> 极速模式走 `pymupdf4llm`，标准模式走 `docling`，复杂扫描件走 `mineru`。
- `docx` -> `docling` -> 降级 `markitdown`。
- `pptx` / `xlsx` -> 优先 `mineru` -> 降级 `markitdown`。
- 旧版 `doc/ppt/xls` -> 自动调用 `LibreOffice/textutil` 转换为现代格式后，接入上述工作流。

## 🤝 贡献与许可

本项目旨在为开源社区提供最干净流畅的文档转 Markdown 体验。欢迎提交 Issue 与 Pull Request！

License: [MIT](LICENSE)
