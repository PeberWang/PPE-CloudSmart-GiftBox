# 课程数据管理功能设计

> 本文档描述按学年分组创建多维表格、文档关联、表单数据收集功能的实现方案。

---

## 一、需求变更

### 1.1 原有架构

```
Wiki 空间 (7624453064019168209)
├── 文档1
├── 文档2
├── 文档3
├── 文档4
├── ... (18 个节点，未分组)
```

### 1.2 期望架构

```
Wiki 空间
├── 大一 (学年节点)
│   ├── 伦理学导论 (课程节点)
│   ├── 宪法学
│   ├── 微观经济学
│   ├── 政治学原理
│   ├── 宏观经济学
│   └── 概率论与数理统计
├── 大二 (学年节点)
│   ├── 世界经济概论
│   ├── 中国经济概论
│   ├── 西方政治思想史
│   ├── 中国政治思想史
│   ├── 比较政治制度
│   ├── 外国经济学说史
│   └── 计量经济学
├── 大三 (学年节点)
│   ├── 中国哲学史
│   ├── 西方哲学史
│   └── 国际关系
└── 大四 (学年节点)
    └── 毕业论文

多维表格 × 4 (每个学年一个)
├── 大一课程表
│   ├── 伦理学导论 (行)
│   │   ├── 课程名称: 伦理学导论
│   │   ├── 授课老师: 李虎老师
│   │   ├── 开课学期: 大一上
│   │   ├── 课程类型: 必修
│   │   ├── 考试形式: 闭卷
│   │   ├── 学习指南: [云文档链接]
│   │   ├── 资料数量: [数字]
│   │   └── 贡献者: [名单]
├── 大二课程表
├── 大三课程表
└── 大四课程表
```

---

## 二、功能模块设计

### 2.1 课程数据收集模块

**目标**：支持根据表单数据动态添加课程到对应学年的多维表格

**输入数据结构**：
```json
{
  "course_name": "自定义课程名称",
  "teacher": "授课老师",
  "semester": "大一上/大一下/...",
  "course_type": "必修/选修",
  "exam": "闭卷/开卷/论文",
  "materials": ["资料1.pdf", "资料2.docx"],
  "experiences": ["学长经验1", "学长经验2"],
  "contributors": ["贡献者1", "贡献者2"]
}
```

**API 端点**：`POST /api/course/add`

**处理逻辑**：
1. 根据课程名称判断属于哪个学年
2. 在对应学年的多维表格中添加记录
3. 为该课程创建学习指南文档
4. 上传资料文件
5. 更新表格中的文档链接和资料数量

### 2.2 表单数据导入模块

**目标**：支持从 Excel 或 CSV 表单导入课程数据

**输入**：表单文件
**输出**：批量添加到对应学年的多维表格

### 2.3 贡献者资料关联模块

**目标**：处理"上传了资料但课程未被提及"的场景

**实现逻辑**：
1. 扫描所有上传到飞书云盘的资料
2. 根据文件名或路径识别所属课程
3. 为未被提及的课程自动创建记录
4. 在贡献者字段中添加"系统识别"

---

## 三、数据库设计

### 3.1 课程数据表结构

```python
# libs/course_db.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class CourseData:
    """课程数据"""
    course_name: str
    teacher: str
    semester: str
    course_type: str  # 必修/选修
    exam: str  # 闭卷/开卷/论文
    year: str  # 大一/大二/大三/大四
    doc_url: Optional[str]  # 学习指南文档链接
    material_urls: List[str]  # 资料文件链接列表
    contributors: List[str]  # 贡献者列表
    material_count: int  # 资料数量
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
```

### 3.2 本地存储

**存储方式**：JSON 文件（`data/courses.json`）

```json
{
  "大一": {
    "courses": [
      {
        "course_name": "伦理学导论",
        "teacher": "李虎老师",
        "semester": "大一上",
        "course_type": "必修",
        "exam": "闭卷",
        "doc_url": "https://...",
        "material_urls": [],
        "contributors": [],
        "material_count": 0,
        "created_at": "2026-05-12T10:00:00Z"
      }
    ]
  },
  "大二": { ... },
  "大三": { ... },
  "大四": { ... }
}
```

---

## 四、API 路由设计

| 功能 | 方法 | 路径 | 说明 |
|------|------|------|
| 添加课程 | POST | `/api/course/add` | 添加单个课程 |
| 批量添加 | POST | `/api/course/batch` | 批量添加课程 |
| 获取所有课程 | GET | `/api/courses` | 获取所有课程 |
| 按学年获取 | GET | `/api/courses/:year` | 获取指定学年的课程 |
| 更新课程 | PUT | `/api/course/:name` | 更新课程信息 |
| 删除课程 | DELETE | `/api/course/:name` | 删除课程 |
| 导入表单 | POST | `/api/courses/import` | 从 Excel 导入 |

---

## 五、多维表格字段设计

### 5.1 标准字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 课程名称 | Text | 课程名称 |
| 授课老师 | Text | 授课老师 |
| 开课学期 | Select | 大一上/大一下/... |
| 课程类型 | Select | 必修/选修 |
| 考试形式 | Select | 闭卷/开卷/论文 |
| 学习指南 | Url | 云文档链接 |
| 资料数量 | Number | 资料文件数量 |
| 贡献者 | MultiSelect | 多选贡献者 |
| 最后更新 | Datetime | 最后更新时间 |

### 5.2 字段配置

```python
# config/table_fields.py
BITABLE_FIELDS = {
    "大一": [
        {"field_name": "课程名称", "type": 1, "is_primary": True},
        {"field_name": "授课老师", "type": 1},
        {"field_name": "开课学期", "type": 3, "property": {"options": ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "大四上", "大四下"]}},
        {"field_name": "课程类型", "type": 3, "property": {"options": ["必修", "选修"]}},
        {"field_name": "考试形式", "type": 3, "property": {"options": ["闭卷", "开卷", "论文"]}},
        {"field_name": "学习指南", "type": 15, "property": {"content_type": "text"}},
        {"field_name": "资料数量", "type": 2},
        {"field_name": "贡献者", "type": 3, "property": {"options": ["A", "B", "C", "D"]}, "is_multiple": True},
        {"field_name": "最后更新", "type": 5},
    ],
    "大二": [...],  # 类似结构
    "大三": [...],
    "大四": [...]
}
```

---

## 六、实现步骤

### 6.1 Phase 1: 重建 Wiki 结构（清理旧节点）

**目标**：清理现有的 18 个平级节点，重新按学年分组创建

**步骤**：
1. 删除现有的 18 个节点
2. 创建 4 个学年节点
3. 为每门课程创建子节点（共 18 个）
4. 创建 4 个多维表格（每个学年一个）

**API 使用**：
- `DELETE /wiki/v2/spaces/:space_id/nodes/:node_token` - 删除节点
- `POST /wiki/v2/spaces/:space_id/nodes` - 创建学年节点
- `POST /bitable/v1/apps/:app_token/tables` - 创建表格
- `POST /bitable/v1/apps/:app_token/tables/:table_id/fields` - 创建字段

### 6.2 Phase 2: 实现课程数据收集模块

**新增文件**：
- `services/course_data_service.py` - 课程数据管理服务
- `libs/course_db.py` - 课程数据本地存储
- `data/courses.json` - 课程数据文件

**新增 API**：
- `glue/course_api.py` - 课程数据 API 路由

### 6.3 Phase 3: 实现文档关联功能

**修改**：`services/doc_service.py`

**新增功能**：
- 创建文档后返回文档链接
- 更新课程数据中的 `doc_url` 字段
- 支持为已有课程创建文档

### 6.4 Phase 4: 实现资料上传和关联

**修改**：`services/material_service.py`

**新增功能**：
- 上传资料后返回资料链接
- 更新课程数据中的 `material_urls` 和 `material_count`
- 扫描云盘文件识别课程归属

---

## 七、风险与注意事项

### 7.1 API 权限

确保应用已开通以下权限：
- `wiki:space:create` - 创建知识空间
- `wiki:node:create` - 创建知识库节点
- `wiki:node:read` - 读取知识库节点
- `bitable:app:create` - 创建多维表格应用
- `bitable:app:read` - 读取多维表格应用
- `drive:file:upload` - 上传文件

### 7.2 数据一致性

- Wiki 空间结构、多维表格数据、本地 JSON 数据三者需保持一致
- 添加/更新/删除课程时需同步更新所有数据源

### 7.3 错误处理

- 创建多维表格失败时需回滚
- 添加课程记录失败时需记录日志
- 资料上传失败时需提供重试机制

---

## 八、文件清单

### 8.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `services/course_data_service.py` | 课程数据管理服务 |
| `libs/course_db.py` | 课程数据本地存储 |
| `data/courses.json` | 课程数据文件 |
| `glue/course_api.py` | 课程数据 API 路由 |
| `config/table_fields.py` | 多维表格字段配置 |
| `docs/COURSE_DATA_MANAGEMENT_DESIGN.md` | 本设计文档 |

### 8.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `glue/deploy.py` | 添加按学年分组创建表格的逻辑 |
| `services/wiki_service.py` | 支持创建学年节点 |
| `services/table_service.py` | 支持按学年创建表格 |
| `services/doc_service.py` | 添加文档链接返回功能 |
| `services/material_service.py` | 添加资料链接返回功能 |

---

*最后更新：2026-05-12*
