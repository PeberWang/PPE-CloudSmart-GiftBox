# PPE云端智能大礼包

> 南开大学PPE专业课程资料智能管理与分发系统

## 📋 项目简介

PPE云端智能大礼包是一个基于飞书开放平台的知识库自动构建系统，旨在帮助PPE专业学生：
- 📚 系统化管理各学年课程资料
- 📝 智能生成课程学习指南
- 🔗 打通知识库、文档、多维表格的完整链路
- 🤖 利用AI自动提取学长学姐的经验心得

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/PeberWang/PPE-CloudSmart-GiftBox.git
cd PPE-CloudSmart-GiftBox

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```env
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
ZHIPU_API_KEY=your_api_key
```

### 3. 准备数据

将课程资料数据放入 `ppe_giftbox/data/` 目录：
- `materials.json` — 资料元信息
- `experiences.json` — 心得体会

### 4. 一键部署

```bash
# 完整部署（推荐首次使用）
python deploy.py --mode full

# 按模块部署
python deploy.py --mode wiki      # 仅创建知识库
python deploy.py --mode tables    # 仅创建多维表格
python deploy.py --mode docs      # 仅生成文档
python deploy.py --mode link      # 仅关联链接
python deploy.py --mode upload    # 仅上传资料
python deploy.py --mode sync      # 增量同步
python deploy.py --mode cleanup   # 清理空记录
```

## 📁 项目结构

```
PPE-CloudSmart-GiftBox/
├── deploy.py              # 统一部署入口（CLI）
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量模板
├── .editorconfig          # 编辑器配置
│
├── ppe_giftbox/           # 核心应用包
│   ├── __init__.py
│   ├── config.py          # 全局配置（路径解析、API凭据、目录常量）
│   ├── models.py          # 数据模型（Material, Experience, CourseDocument）
│   ├── data/              # 源数据与数据定义
│   │   ├── course_schema.py    # 课程数据、字段定义、常量
│   │   ├── materials.json      # 资料元信息（.gitignore）
│   │   ├── experiences.json    # 心得体会（.gitignore）
│   │   └── report.json         # 报告数据（.gitignore）
│   ├── output/            # 本地输出（.gitignore）
│   │   └── course_docs/
│   └── services/          # 核心服务层（按职责分层）
│       ├── __init__.py
│       ├── orchestrator.py     # 部署编排（流程控制）
│       ├── core/               # 基础服务
│       │   ├── feishu_service.py      # 飞书 API 封装
│       │   ├── llm_service.py         # 智谱 AI 调用
│       │   ├── pipeline.py            # 主流水线
│       │   └── experience_service.py  # 心得体会服务
│       ├── wiki/               # 知识库服务
│       │   └── wiki_builder.py        # 知识库自动构建
│       ├── bitable/            # 多维表格服务
│       │   └── table_service.py       # 多维表格管理（增量更新）
│       ├── docs/               # 文档服务
│       │   ├── doc_generator.py       # 课程文档生成
│       │   └── link_service.py        # 表格↔知识库链接关联
│       ├── materials/          # 资料服务
│       │   ├── material_uploader.py   # 资料批量上传到飞书
│       │   └── upload_service.py      # 资料上传服务
│       └── cleanup/            # 清理服务
│           └── cleanup_service.py     # 部署残留清理
│
├── output/                # 部署产物（运行时生成）
│   ├── wiki_structure.json  # 知识库结构配置（.gitignore）
│   └── bitable_config.json  # 多维表格配置（.gitignore）
│
├── tests/                 # 测试脚本
│   └── test_*.py
│
├── tools/                 # 辅助工具
│   └── read_docs.py
│
├── docs/                  # 文档与规划
│   ├── plan/              # 版本规划文档
│   ├── memorandum/        # 技术备忘录
│   └── support/           # 支撑文档
│
└── log/                   # 运行日志
    └── YYYY-MM-DD-HH.md
```

## 🛠️ 技术架构

### 核心设计原则

- **配置驱动**：所有敏感信息通过 `.env` 环境变量管理，代码中无硬编码凭据
- **服务分层**：按职责划分子模块（core/wiki/bitable/docs/materials/cleanup），通过 orchestrator 编排
- **增量更新**：多维表格支持增量同步，保护用户手动编辑的字段
- **自动重试**：内置网络超时与频率限制的退避重试机制

### 数据流

```
本地数据 (materials.json, experiences.json)
    ↓ UploadService / ExperienceService
飞书知识库 (WikiBuilder → 空间 → 学年节点 → 课程节点)
    ↓ DocGenerator + LLMService
智能课程文档 (飞书云文档)
    ↓ TableService + LinkService
多维表格 (课程列表 ↔ 学习指南链接)
```

### 添加新课程

编辑 `ppe_giftbox/data/course_schema.py` 中的 `COURSES_BY_YEAR` 字典即可。

## ⚠️ 注意事项

1. **飞书权限**：需开通 `wiki:wiki`、`docx:document`、`bitable:app`、`drive:file:upload`
2. **API频率限制**：Docx 块操作约 3次/秒，已内置退避重试
3. **数据安全**：`materials.json`、`wiki_structure.json` 等含敏感路径的文件已在 `.gitignore` 中排除

## 📝 更新日志

### v3.0 (2026-04-20)
- 🏗️ 深度模块化重构：包名 `ppe_demo` → `ppe_giftbox`
- 📦 配置分离：`course_schema.py` 独立存放课程数据与字段定义
- 📂 服务分层：services/ 按职责重组为 core/wiki/bitable/docs/materials/cleanup
- 🎯 部署编排：deploy.py 精简为 CLI 入口，逻辑移入 orchestrator.py
- 📁 部署产物分离：wiki_structure.json、bitable_config.json 移至 output/

### v2.1 (2026-04-20)
- 🔧 项目结构重构：tests/、tools/、docs/ 目录整理
- 📦 添加 `__init__.py`，规范化 Python 包结构
- 🔒 完善 `.gitignore`，排除含敏感路径的数据文件
- 📝 资料上传服务 (material_uploader.py)

### v2.0 (2026-03-30)
- ✨ 重构为飞书云文档架构
- 🔗 打通多维表格与知识库链接
- 📄 文档自动上传到飞书
- 🚀 统一部署入口

### v1.0 (2026-02-28)
- 📚 本地 Markdown 文档生成
- 📝 心得体会管理
- 🎯 AI 智能提取

## 📄 License

MIT License

## 👥 贡献者

- 铭培（产品设计与需求）
- 小劳（技术实现）
- 南开大学PPE专业全体同学（资料贡献）

---

*Made with ❤️ for Nankai PPE*
