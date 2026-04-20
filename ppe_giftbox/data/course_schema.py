# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 课程数据与字段定义
从 config.py 分离，包含课程数据、多维表格字段、常量定义
"""

# 资料类型
MATERIAL_TYPES = [
    "PPT",
    "笔记",
    "真题",
    "阅读材料",
    "教材",
    "复习大纲",
    "练习题",
    "其他"
]

# 年级
GRADES = ["22级", "23级", "24级"]

# PPE课程按学年分类
COURSES_BY_YEAR = {
    "大一": [
        {"name": "伦理学导论", "teacher": "李虎老师", "semester": "大一上", "type": "必修", "exam": "闭卷"},
        {"name": "宪法学", "teacher": "赵聚军老师", "semester": "大一上", "type": "必修", "exam": "闭卷"},
        {"name": "微观经济学", "teacher": "", "semester": "大一上", "type": "必修", "exam": "闭卷"},
        {"name": "政治学原理", "teacher": "", "semester": "大一下", "type": "必修", "exam": "闭卷"},
        {"name": "宏观经济学", "teacher": "", "semester": "大一下", "type": "必修", "exam": "闭卷"},
        {"name": "概率论与数理统计", "teacher": "刘会刚老师", "semester": "大一下", "type": "必修", "exam": "闭卷"},
    ],
    "大二": [
        {"name": "世界经济概论", "teacher": "雷鸣老师", "semester": "大二上", "type": "必修", "exam": "开卷"},
        {"name": "中国经济概论", "teacher": "龚关老师", "semester": "大二上", "type": "必修", "exam": "闭卷"},
        {"name": "西方政治思想史", "teacher": "柳建文老师", "semester": "大二上", "type": "必修", "exam": "闭卷"},
        {"name": "中国政治思想史", "teacher": "孙晓春老师", "semester": "大二上", "type": "必修", "exam": "闭卷"},
        {"name": "比较政治制度", "teacher": "贾义猛老师", "semester": "大二上", "type": "必修", "exam": "闭卷"},
        {"name": "外国经济学说史", "teacher": "蒋雅文老师", "semester": "大二下", "type": "必修", "exam": "闭卷"},
        {"name": "计量经济学", "teacher": "", "semester": "大二下", "type": "必修", "exam": "闭卷"},
    ],
    "大三": [
        {"name": "中国哲学史", "teacher": "", "semester": "大三上", "type": "选修", "exam": "闭卷"},
        {"name": "西方哲学史", "teacher": "", "semester": "大三上", "type": "选修", "exam": "闭卷"},
        {"name": "国际关系", "teacher": "", "semester": "大三上", "type": "选修", "exam": "论文"},
        {"name": "比较政治", "teacher": "", "semester": "大三下", "type": "选修", "exam": "论文"},
    ],
    "大四": [
        {"name": "毕业论文", "teacher": "", "semester": "大四上", "type": "必修", "exam": "论文"},
    ],
}

# 知识库配置
WIKI_SPACE_NAME = "Demo PPE CloudSmart Giftbox"
WIKI_YEAR_NODES = ["大一", "大二", "大三", "大四"]

# 多维表格字段定义（学年课程表）
BITABLE_COURSE_FIELDS = [
    ("课程名称", 1),
    ("授课老师", 1),
    ("开课学期", 3),
    ("课程类型", 3),
    ("考试形式", 3),
    ("学习指南", 15),
    ("资料数量", 2),
    ("贡献者", 1),
    ("最后更新", 5),
]

# ── 保护字段：增量更新时不覆盖这些用户手动编辑的字段 ──
PROTECTED_FIELDS = {"贡献者", "最后更新"}
