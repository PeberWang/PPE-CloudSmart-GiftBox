# PPE云端智能大礼包

> 南开大学PPE专业课程资料智能管理与分发系统

## 📋 项目简介

PPE云端智能大礼包是一个基于飞书开放平台的知识库自动构建系统，旨在帮助PPE专业学生：
- 📚 系统化管理各学年课程资料
- 📝 智能生成课程学习指南
- 🔗 打通知识库、文档、多维表格的完整链路
- 🤖 利用AI自动生成学习内容

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
# 飞书应用配置
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx

# 多维表格App Token
BITABLE_APP_TOKEN=cli_xxx

# LLM API配置（OpenAI兼容）
OPENAI_API_KEY=xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# 基础配置
WIKI_SPACE_NAME=PPE CloudSmart Giftbox
MATERIALS_BASE=./materials
```

### 3. 一键部署

```bash
# 完整部署（推荐首次使用）
python deploy.py --mode full

# 按模块部署
python deploy.py --mode wiki                 # 仅创建知识库
python deploy.py --mode tables               # 仅创建多维表格
python deploy.py --mode docs --limit 5       # 仅生成5份文档
python deploy.py --mode link                 # 仅关联文档链接
python deploy.py --mode upload               # 仅上传资料
python deploy.py --mode sync                 # 增量同步
```

## 📁 项目结构

```
PPE-CloudSmart-GiftBox/
├── config/                 # 配置层
│   ├── settings.py        # 配置管理
│   ├── course_schema.py   # 课程数据模型
│   └── table_fields.py    # 表格字段定义
│
├── libs/                  # 适配器层
│   ├── feishu_adapter.py # 飞书API适配器
│   ├── llm_adapter.py     # LLM服务适配器
│   ├── course_db.py       # 课程数据库
│   └── exceptions.py      # 自定义异常
│
├── services/              # 业务服务层
│   ├── wiki_service.py   # 知识库服务
│   ├── table_service.py  # 表格服务
│   ├── doc_service.py    # 文档服务
│   ├── material_service.py # 资料服务
│   └── perm_service.py   # 权限服务
│
├── glue/                  # 编排层
│   ├── deploy.py         # 主部署流程
│   └── pipeline.py       # 子流程定义
│
├── deploy.py              # 统一部署入口
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量模板
│
├── tests/                 # 测试脚本
├── tools/                 # 辅助工具
├── docs/                  # 文档与规划
└── log/                   # 运行日志
```

## 🏗️ 技术架构

### 四层架构设计

```
┌─────────────────────────────────────────┐
│          编排层 (glue)                  │
│   - 主流程控制                          │
│   - 子流程编排                          │
│   - 部署参数管理                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        业务服务层 (services)            │
│   - 知识库服务                          │
│   - 表格服务                            │
│   - 文档服务                            │
│   - 资料服务                            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        适配器层 (libs)                  │
│   - 飞书API适配器                       │
│   - LLM适配器                           │
│   - 课程数据库                          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          配置层 (config)                │
│   - 环境配置                            │
│   - 数据模型                            │
│   - 字段定义                            │
└─────────────────────────────────────────┘
```

### 数据流

```
课程数据 (config/course_schema.py)
    ↓
知识库构建 (wiki_service.py)
    ↓
文档生成 (doc_service.py + llm_adapter.py)
    ↓
多维表格 (table_service.py)
    ↓
文档关联 (link_pipeline)
    ↓
资料上传 (material_service.py)
```

## 📖 功能详解

### 1. 知识库管理

- **按学年分组**：自动创建大一、大二、大三、大四四个节点
- **课程节点**：在每个学年下创建对应的课程节点
- **支持已有空间**：可指定已有的知识空间进行操作

### 2. 多维表格

- **独立表格**：为每个学年创建独立的多维表格
- **字段配置**：包含课程名称、老师、学期、考试形式、学习指南等
- **增量更新**：支持增量更新模式，不覆盖用户手动编辑的内容
- **保护字段**：贡献者、最后更新等字段在增量更新时受保护

### 3. 文档生成

- **学习指南**：自动为每门课程生成学习指南文档
- **LLM驱动**：使用OpenAI兼容API生成个性化的学习内容
- **批量生成**：支持批量生成或限制生成数量

### 4. 资料关联

- **资料上传**：支持PPT、笔记、真题等多种资料类型
- **文件管理**：自动组织文件结构，便于查找
- **批量操作**：支持批量上传和关联

### 5. 文档链接

- **自动关联**：生成文档后自动将链接关联到表格
- **智能匹配**：根据课程名称自动匹配对应的表格记录
- **更新字段**：将文档URL更新到表格的"学习指南"字段

## 🔧 配置说明

### 课程数据配置

在 `config/course_schema.py` 中定义了所有PPE课程信息：

- 按学年分组
- 包含课程名称、授课老师、学期、类型、考试形式
- 支持自定义课程数据

### 环境变量配置

| 变量名 | 说明 | 必填 |
|--------|------|------|
| FEISHU_APP_ID | 飞书应用ID | 是 |
| FEISHU_APP_SECRET | 飞书应用密钥 | 是 |
| BITABLE_APP_TOKEN | 多维表格App Token | 是 |
| OPENAI_API_KEY | OpenAI API密钥 | 是 |
| OPENAI_BASE_URL | OpenAI API基础URL | 否 |
| WIKI_SPACE_NAME | 知识空间名称 | 否 |
| MATERIALS_BASE | 资料基础路径 | 否 |

### 添加新课程

编辑 `config/course_schema.py` 中的 `COURSES_BY_YEAR` 字典即可。

## 🧪 测试

```bash
# 运行文档关联功能测试
python test_doc_link.py

# 查看生成的文档和关联结果
python tools/read_docs.py
```

## 📝 更新日志

### v4.0 (2026-05-12)
- 🏗️ 深度模块化重构：四层架构设计
- 📦 配置分离：config/ 独立存放配置和模型
- 📂 服务分层：services/ 按职责拆分业务服务
- 🔗 文档关联：新增文档链接关联功能
- 🔄 增量更新：支持多维表格增量更新模式

### v3.0 (2026-04-20)
- 🏗️ 模块化重构：包名 `ppe_demo` → `ppe_giftbox`
- 📦 配置分离：`course_schema.py` 独立存放课程数据与字段定义
- 📂 服务分层：services/ 按职责重组为 core/wiki/bitable/docs/materials/cleanup

### v2.0 (2026-03-30)
- ✨ 重构为飞书云文档架构
- 🔗 打通多维表格与知识库链接
- 📄 文档自动上传到飞书
- 🚀 统一部署入口

### v1.0 (2026-02-28)
- 📚 本地 Markdown 文档生成
- 📝 心得体会管理
- 🎯 AI 智能提取

## ⚠️ 注意事项

1. **飞书权限**：需开通 `wiki:wiki`、`docx:document`、`bitable:app`、`drive:file:upload`
2. **API频率限制**：Docx 块操作约 3次/秒，已内置退避重试
3. **数据安全**：`.env` 等含敏感信息的文件已在 `.gitignore` 中排除

## 📄 License

MIT License

## 👥 贡献者

- 铭培（产品设计与需求）
- 小劳（技术实现）
- 南开大学PPE专业全体同学（资料贡献）

---

*Made with ❤️ for Nankai PPE*
