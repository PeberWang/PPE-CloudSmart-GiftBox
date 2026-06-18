# -*- coding: utf-8 -*-
"""
初始化 data/db/{学年}.json 课程库（源真相）。

- 以 COURSES_BY_YEAR 花名册为基础，为每门课建立 CourseData 行。
- 为所有 18 门课程注入仿真的高分心得、推荐资料、课程感悟、贡献者，
  模拟飞书表单采集 + SyncService 合并后的完整数据状态。
- 自动为每份资料生成仿真 OSS 下载链接（file_link）。

这是一次性引导脚本；之后 data/db 由人工 / 飞书表单维护。重跑会覆盖 demo 数据。
用法：python scripts/seed_course_db.py
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from config.course_schema import (
    CourseData, Insight, Material, Contributor,
    COURSES_BY_YEAR, WIKI_YEAR_NODES,
)
from config.settings import settings
from libs.data_adapter import write_course_db

SEED_DATE = "2026-06-05"
OSS_BASE = "https://ppe-giftbox.oss-cn-beijing.aliyuncs.com/materials"


def _oss_link(filename: str) -> str:
    """生成仿真 OSS 下载链接。后续切到真实 OSS 时替换为预签名 URL。"""
    safe = filename.replace(" ", "-").replace("（", "").replace("）", "").replace("《", "").replace("》", "")
    return f"{OSS_BASE}/{safe}.pdf"


# 仿真表单采集数据（key = 课程名称）—— 模拟飞书表单提交后经 SyncService 合并的成果
ENRICHMENT = {
    # ── 大一 ──
    "伦理学导论": dict(
        insights=[
            Insight(author="22级小王", grade="22级", score="95", content=(
                "李虎老师的伦理学导论不是一门背诵课。整个学期围绕三大传统展开："
                "亚里士多德的德性伦理（《尼各马可伦理学》）、康德的义务论（《道德形而上学奠基》）、"
                "以及密尔的功利主义（《功利主义》）。老师反复强调'回到原典'，期末大题几乎都是"
                "给一个具体的道德困境，要求你选定一个理论立场把论证走完整。我的经验是：每读完一个"
                "传统就立刻写一篇 800 字的读书札记，用该理论分析一个真实案例（比如电车难题、说谎的"
                "义务），考前把札记串起来就是一份现成的论述模板。死记定义拿不到高分，能把论证讲清楚才行。"
            )),
            Insight(author="23级小李", grade="23级", score="91", content=(
                "平时分占比不低，课堂参与和读书报告都算。建议第一周就把三本原典的中译本借齐，"
                "跟着进度精读对应章节。老师偏好有自己判断、能引用原文的回答，套话和'我认为'式的空谈会被压分。"
            )),
        ],
        materials=[
            Material(name="伦理学导论-三大传统精读笔记", material_type="笔记", contributor="22级小王", grade="22级",
                     recommendation_reason="按德性论/义务论/功利主义分章整理，附原典页码与论证结构图，最适合期末串讲。"),
            Material(name="伦理学导论-期末论述题框架", material_type="复习大纲", contributor="23级小李", grade="23级",
                     recommendation_reason="把历年大题归纳成可套用的'立场—论证—反驳—回应'四段式模板。"),
            Material(name="尼各马可伦理学-精读章节标注版", material_type="阅读材料", contributor="22级小王", grade="22级",
                     recommendation_reason="老师课上重点讲的章节都做了批注，省去通读全书的时间。"),
        ],
        contributors=[
            Contributor(name="22级小王", contribution="系统梳理了三大伦理学传统的论证脉络，贡献精读笔记与原典标注版，奠定了本课文档的主干。"),
            Contributor(name="23级小李", contribution="提炼期末论述题的四段式答题框架，并补充了平时分与课堂偏好的实战经验。"),
        ],
    ),
    "宪法学": dict(
        insights=[
            Insight(author="22级小张", grade="22级", score="90", content=(
                "赵聚军老师的宪法学核心是'规范+案例'双线。每讲一个宪法条文，都会配两个以上真实案例，"
                "期末大题也基本是案例分析。建议准备一份'条文—案例—法理'索引：把宪法每章的核心条文、"
                "课上讲的典型案例、背后的法理争议整理成表。答题时先引条文、再套案例、最后分析法理，"
                "这个三段式老师很认可。不要只背书，老师会考你没讲过的新案例，考的是分析能力。"
                "另外注意：基本权利部分（平等权、自由权、社会权）是绝对重点，占分一半以上。"
            )),
        ],
        materials=[
            Material(name="宪法学-条文·案例·法理对照表", material_type="笔记", contributor="22级小张", grade="22级",
                     recommendation_reason="按章节整理，每条核心条文配2-3个课堂案例和法理分析要点，期末复习一遍过。"),
            Material(name="宪法学-基本权利案例分析模板", material_type="复习大纲", contributor="22级小张", grade="22级",
                     recommendation_reason="针对平等权/自由权/社会权三类大题，提供'条文引用→案例套用→法理分析'的标准答题框架。"),
        ],
        contributors=[
            Contributor(name="22级小张", contribution="建立了条文—案例—法理的三栏对照体系，把'散装'的宪法知识串成了分析框架。"),
        ],
    ),
    "微观经济学": dict(
        insights=[
            Insight(author="23级小刘", grade="23级", score="93", content=(
                "微观经济学的关键在于画图和直觉并重。每学一个模型（供需均衡、消费者选择、完全竞争、"
                "垄断定价），先画图理解横纵轴的经济含义，再用一个日常例子解释（比如用'食堂定价'理解垄断、"
                "用'选课'理解预算约束和效用最大化）。考试计算题不难，但图形分析题（'画图说明税收对福利的影响'）"
                "是大头。建议准备一叠白纸，每章结束后不看笔记把核心图形默画出来并标注所有交点含义，"
                "能做到这一点基本就稳了。数学基础弱的同学别慌，只用到一元微积分和简单导数。"
            )),
        ],
        materials=[
            Material(name="微观经济学-核心图形手册", material_type="笔记", contributor="23级小刘", grade="23级",
                     recommendation_reason="每章核心图形手绘+标注，从供需到博弈论共18张，考前默画一遍就能进考场。"),
            Material(name="微观经济学-课后习题精选与详解", material_type="真题", contributor="23级小刘", grade="23级",
                     recommendation_reason="从教材课后题中筛选最贴近考试风格的30道，附详细画图步骤和计算过程。"),
        ],
        contributors=[
            Contributor(name="23级小刘", contribution="绘制了全套核心图形手册并用日常例子解释每个模型，让'怕数学'的同学也能建立微观直觉。"),
        ],
    ),
    "概率论与数理统计": dict(
        insights=[
            Insight(author="22级小赵", grade="22级", score="88", content=(
                "刘会刚老师讲得很细，但考试比作业难一个台阶。重点在三大分布（正态、t、F）和假设检验流程，"
                "期末至少两道大题是'给一组数据，选方法、做检验、写结论'。建议把每种检验（z检验、t检验、"
                "卡方检验、方差分析）的条件和适用场景整理成一张决策树，考试时先判断'数据长什么样、问什么'"
                "再选检验方法。概率部分古典概型和条件概率是基础，贝叶斯公式一定考一道。"
                "作业要认真做，老师出的作业题和考试风格一致，只是考试数据换了。"
            )),
        ],
        materials=[
            Material(name="概率统计-假设检验决策树", material_type="笔记", contributor="22级小赵", grade="22级",
                     recommendation_reason="一张流程图覆盖所有检验方法的选择逻辑：数据类型→样本数量→检验目标→对应公式。"),
            Material(name="概率统计-历年期末真题分类汇编", material_type="真题", contributor="22级小赵", grade="22级",
                     recommendation_reason="按题型分类（选择/填空/计算/综合），标注每道考察的知识点和常见陷阱。"),
        ],
        contributors=[
            Contributor(name="22级小赵", contribution="整理了假设检验方法选择的决策树和分类真题，让统计推断的选择逻辑变得清晰可见。"),
        ],
    ),
    # ── 大二 ──
    "世界经济概论": dict(
        insights=[
            Insight(author="22级小孙", grade="22级", score="91", content=(
                "雷鸣老师的世界经济概论视野很广，从国际贸易理论到全球金融体系都会涉及。这门课不是"
                "要你记住每一个数据，而是要理解'为什么这个国家在这个时期采取这个政策'。建议把课程分成"
                "三条线索：贸易（比较优势→WTO→区域贸易协定）、金融（金本位→布雷顿森林→浮动汇率）、"
                "发展（进口替代→出口导向→华盛顿共识）。每学一个国家或地区，问自己三个问题：它面临的"
                "核心约束是什么？它选择了什么策略？结果如何？考试以论述为主，老师特别喜欢比较分析题"
                "（如'比较东亚和拉美的工业化路径'），提前准备几组经典比较会很有帮助。"
            )),
        ],
        materials=[
            Material(name="世界经济概论-三条线索复习框架", material_type="复习大纲", contributor="22级小孙", grade="22级",
                     recommendation_reason="按贸易/金融/发展三条主线梳理，每个阶段标注关键事件、核心理论和代表国家。"),
            Material(name="世界经济概论-经典比较分析集", material_type="笔记", contributor="22级小孙", grade="22级",
                     recommendation_reason="整理了6组老师常考的比较（东亚vs拉美、中美vs日德模式等），每组都附关键数据和理论视角。"),
        ],
        contributors=[
            Contributor(name="22级小孙", contribution="将散落的知识点整合为贸易/金融/发展三条主线和6组经典比较，为论述题提供了清晰的答题框架。"),
        ],
    ),
    "西方政治思想史": dict(
        insights=[
            Insight(author="23级小周", grade="23级", score="89", content=(
                "柳建文老师的西方政治思想史从柏拉图一路讲到罗尔斯，时间跨度大、人物多。核心方法是"
                "'一人一问题'：每个思想家不要全面记忆，而是抓住他最核心的那个问题（柏拉图：谁应该统治？"
                "马基雅维利：道德与政治的关系？霍布斯：为什么要国家？洛克：如何限制国家？卢梭：什么是"
                "公意？马克思：阶级与国家的关系？）。期末论述题通常是'比较A和B关于X问题的看法'，"
                "所以你不仅要理解每个思想家，还要能建立跨时代的对话。建议做一个'思想对话表'，横轴"
                "是核心问题（人性论/国家起源/自由观/财产权），纵轴是按时代排列的思想家，每个格子填他的立场。"
            )),
        ],
        materials=[
            Material(name="西方政治思想史-核心问题对照表", material_type="笔记", contributor="23级小周", grade="23级",
                     recommendation_reason="横轴5个核心问题×纵轴12位思想家，一张表搞定比较论述题的素材。"),
            Material(name="西方政治思想史-原典精读摘要", material_type="阅读材料", contributor="23级小周", grade="23级",
                     recommendation_reason="从每位思想家的代表作中摘出最常被引用的3-5段关键原文，附白话解读。"),
        ],
        contributors=[
            Contributor(name="23级小周", contribution="设计了'核心问题×思想家'二维对照表，把思想的传承与断裂变成了可视化的比较框架。"),
        ],
    ),
    "比较政治制度": dict(
        insights=[
            Insight(author="22级小吴", grade="22级", score="92", content=(
                "贾义猛老师的这门课不是简单的'各国政治制度介绍'，而是有明确的分析框架。核心是"
                "理解'制度如何塑造政治结果'：总统制vs议会制、单一制vs联邦制、多数决vs比例代表制，"
                "每一种制度选择都会产生不同的政治激励和行为。建议把每个国家的案例分析结构化："
                "政治文化→制度设计→政党体系→政策产出，这样四步走下来就是一个完整的论述。"
                "老师特别喜欢问'如果某国的选举制度改成另一种会怎样'这种反事实问题，"
                "提前想想英/美/法/德/日之间的制度对比会很有用。期中是一篇比较论文，期末闭卷。"
            )),
        ],
        materials=[
            Material(name="比较政治制度-五国制度对比手册", material_type="笔记", contributor="22级小吴", grade="22级",
                     recommendation_reason="英/美/法/德/日五国的政治文化、制度设计、政党体系、政策产出四栏对比，一目了然。"),
            Material(name="比较政治制度-反事实分析框架", material_type="复习大纲", contributor="22级小吴", grade="22级",
                     recommendation_reason="针对'如果改制度会怎样'类题型，提供制度变量→激励变化→行为变化→结果变化的分析链路。"),
        ],
        contributors=[
            Contributor(name="22级小吴", contribution="构建了五国四维对比体系和反事实分析框架，把'制度比较'从描述提升为有因果逻辑的分析。"),
        ],
    ),
    "中国经济概论": dict(
        insights=[
            Insight(author="22级小陈", grade="22级", score="92", content=(
                "龚关老师特别重视经济史脉络和制度变迁，不能只背结论。复习时我把 1949 年以来分成"
                "计划经济、改革开放起步、社会主义市场经济确立、新常态几个阶段，每个阶段抓住'核心矛盾—"
                "改革举措—效果与代价'三条线。期末大题常考论述，比如'如何理解中国的渐进式（增量）改革'，"
                "答题一定要史实+数据+理论三结合，光讲道理不给史实拿不到高分。课堂上老师补充的史料很关键，"
                "建议逐字记下来，考试里直接用会很出彩。"
            )),
        ],
        materials=[
            Material(name="中国经济概论-课堂笔记（含老师补充史料）", material_type="笔记", contributor="22级小陈", grade="22级",
                     recommendation_reason="完整记录了龚关老师课上补充的史料与数据，是答论述大题的素材库。"),
            Material(name="中国经济概论-分阶段复习大纲", material_type="复习大纲", contributor="22级小陈", grade="22级",
                     recommendation_reason="按改革阶段搭好框架，把零散知识点挂到'核心矛盾—举措—效果'三条线上。"),
            Material(name="《当代中国经济改革》吴敬琏-阅读重点", material_type="阅读材料", contributor="23级小林", grade="23级",
                     recommendation_reason="老师推荐的核心参考书，标出了与课程考点最相关的章节。"),
        ],
        contributors=[
            Contributor(name="22级小陈", contribution="贡献含老师补充史料的完整课堂笔记与分阶段复习大纲，把一门'史料密集'的课讲成了清晰的脉络。"),
            Contributor(name="23级小林", contribution="标注了吴敬琏《当代中国经济改革》中与考点最相关的章节，降低了阅读门槛。"),
        ],
    ),
    "计量经济学": dict(
        insights=[
            Insight(author="22级小周", grade="22级", score="94", content=(
                "计量最忌讳把它学成'公式推导大全'。我的建议是先把 OLS 的几个经典假设的经济含义弄懂"
                "（为什么需要外生性、异方差和自相关到底意味着什么），再去看推导就顺了。这门课有上机和"
                "实证报告，强烈建议 PPE 的同学系统自学 Python，尤其是 pandas 和 statsmodels，"
                "用真实数据跑一遍回归、读懂每个输出系数和 p 值，比做十道证明题更能建立数据分析的直觉。"
                "期末既考概念也考实证，多做经典论文的结果复现，考前你会很从容。"
            )),
        ],
        materials=[
            Material(name="计量经济学-简明教材（Python实现版）", material_type="教材", contributor="22级小周", grade="22级",
                     recommendation_reason="把每个计量模型都配了可运行的 Python/statsmodels 代码，边学边跑，理论和动手同步。"),
            Material(name="计量经济学-Stata与Python实操手册", material_type="笔记", contributor="22级小周", grade="22级",
                     recommendation_reason="同一个回归分别用 Stata 和 Python 实现，方便对照理解输出。"),
            Material(name="计量经济学-历年大作业范例", material_type="真题", contributor="23级小吴", grade="23级",
                     recommendation_reason="附带数据与完整报告，照着走一遍就知道实证报告该怎么写。"),
        ],
        contributors=[
            Contributor(name="22级小王", contribution="提倡 PPE 同学应在计量经济学课程中系统自学 Python（尤其 pandas 包）以培养数据分析直觉。"),
            Contributor(name="22级小周", contribution="贡献 Python 实现版简明教材与 Stata/Python 双语实操手册，把'怕公式'的同学领进了动手实证的门。"),
            Contributor(name="23级小吴", contribution="提供含数据与完整报告的历年大作业范例，为实证报告写作打了样。"),
        ],
    ),
    # ── 大三 ──
    "中国哲学史": dict(
        insights=[
            Insight(author="22级小郑", grade="22级", score="90", content=(
                "中国哲学史从先秦诸子一直到宋明理学，内容浩瀚。我的方法是不求面面俱到，而是抓住"
                "几条核心线索：天人关系（从'天命'到'天理'）、人性论（孟子性善→荀子性恶→告子无善恶→"
                "宋儒'天地之性与气质之性'）、修养工夫（孔子的'仁'、孟子的'尽心'、老子的'无为'、"
                "庄子的'逍遥'、朱子的'格物'、阳明的'致良知'）。每个思想家只要理清他在这些线索上"
                "的立场，就能应对绝大多数题目。建议背诵 30 条左右核心原文（《论语》《孟子》《道德经》"
                "《庄子》内篇的经典段落），考试引原文是加分项。老师以讲授为主，PPT 比较简略，"
                "课堂笔记至关重要。"
            )),
        ],
        materials=[
            Material(name="中国哲学史-思想线索图谱", material_type="笔记", contributor="22级小郑", grade="22级",
                     recommendation_reason="按天人关系/人性论/修养工夫三大线索梳理从先秦到宋明的演变，附核心原文引用。"),
            Material(name="中国哲学史-核心原文背诵30条", material_type="复习大纲", contributor="22级小郑", grade="22级",
                     recommendation_reason="精选考试最常引用的30条原文，每条附白话翻译和适用题目类型。"),
        ],
        contributors=[
            Contributor(name="22级小郑", contribution="整理了三大思想线索的演变图谱和核心原文背诵集，把一门'浩瀚'的课变成了几条可把握的脉络。"),
        ],
    ),
    "国际关系": dict(
        insights=[
            Insight(author="23级小杨", grade="23级", score="91", content=(
                "国际关系理论是这门课的骨架。三大主流范式（现实主义、自由主义、建构主义）必须烂熟于心："
                "现实主义的核心变量是'权力'（国家是唯一行为体，国际体系是无政府状态），自由主义加上了"
                "'制度'和'相互依存'（国际组织、贸易可以降低冲突），建构主义则强调'观念'和'认同'"
                "（规范和身份建构国家利益）。考试论述题通常是'用至少两种理论分析某个国际事件'，"
                "所以你需要对同一事件准备不同理论视角的解读。建议关注近两年的重大国际事件（大国博弈、"
                "区域冲突、气候变化谈判），每种事件都尝试用三种范式各写一段分析。教材之外，推荐读"
                "《国际政治理论》（华尔兹）和《权力与相互依赖》（基欧汉和奈）的核心章节。"
            )),
        ],
        materials=[
            Material(name="国际关系-三大范式对比表", material_type="笔记", contributor="23级小杨", grade="23级",
                     recommendation_reason="从行为体/核心变量/分析层次/核心命题四个维度对比三大理论，附代表人物和经典文献。"),
            Material(name="国际关系-近年重大事件多范式分析", material_type="复习大纲", contributor="23级小杨", grade="23级",
                     recommendation_reason="选取6个近年重大事件，每个事件分别用现实主义/自由主义/建构主义进行分析，直接应对论述题。"),
        ],
        contributors=[
            Contributor(name="23级小杨", contribution="设计了三大范式的系统对比表和6组事件多范式分析，把理论变成了可以实际操练的分析工具。"),
        ],
    ),
    # ── 补全：大一剩余课程 ──
    "政治学原理": dict(
        insights=[
            Insight(author="22级小林", grade="22级", score="91", content=(
                "政治学原理是 PPE 的入门基石课。核心概念链条是：权力→国家→政体→政治参与→政治文化。"
                "每个概念不仅要知道定义，更要理解不同学者对同一概念的不同界定（比如权力：韦伯的'强制'vs"
                "达尔'影响'vs 卢克斯'三维权力观'）。期末以名词解释+简答+论述为主，论述题通常会给你一个"
                "现实政治现象，要求用学过的概念和理论去分析。建议每学完一章，找一个近期的新闻事件，"
                "尝试用本章的概念框架去解释它——这就是考试论述题的训练。教材之外的推荐阅读："
                "《论美国的民主》（托克维尔）前两卷，老师上课会大量引用。"
            )),
        ],
        materials=[
            Material(name="政治学原理-核心概念辨析集", material_type="笔记", contributor="22级小林", grade="22级",
                     recommendation_reason="整理了20组易混淆概念（权力vs权威/国家vs政府/政体vs政权等），每组附不同学者定义对比。"),
            Material(name="政治学原理-时事分析模板", material_type="复习大纲", contributor="22级小林", grade="22级",
                     recommendation_reason="提供'概念定位→理论框架→现象分析→反思局限'四步论述模板，附5个真题演练。"),
        ],
        contributors=[
            Contributor(name="22级小林", contribution="整理了核心概念辨析集和时事分析模板，把'概念'变成了可操作的分析工具。"),
        ],
    ),
    "宏观经济学": dict(
        insights=[
            Insight(author="23级小高", grade="23级", score="87", content=(
                "宏观经济学和微观的思维方式完全不同——微观是'从个体到市场'，宏观是'从总量到政策'。"
                "核心模型是 IS-LM 和 AD-AS，这两个模型搞懂了，80% 的题目就有了解题框架。建议的学习路径："
                "先彻底搞懂 GDP 的三种核算方法（支出法/收入法/生产法）和各自局限，再进入短期波动"
                "（IS-LM 解释财政和货币政策如何影响产出和利率），最后学长期增长（索洛模型）。"
                "老师出题喜欢问'某一政策在短期和长期的效应分别是什么'，所以一定要分清楚短期（价格粘性）"
                "和长期（价格弹性）的假设差异。计算题主要是乘数效应和 IS-LM 均衡求解，不难但步骤多，"
                "平时多练。"
            )),
        ],
        materials=[
            Material(name="宏观经济学-IS-LM与AD-AS模型全解", material_type="笔记", contributor="23级小高", grade="23级",
                     recommendation_reason="从假设→推导→图形→政策含义四个层面彻底拆解两大核心模型，附20道典型计算题详解。"),
            Material(name="宏观经济学-短期vs长期政策效应对比表", material_type="复习大纲", contributor="23级小高", grade="23级",
                     recommendation_reason="财政政策/货币政策/供给侧冲击在短期和长期的不同效应，一张表搞定最常考的论述题。"),
        ],
        contributors=[
            Contributor(name="23级小高", contribution="拆解了 IS-LM 和 AD-AS 两大核心模型的完整学习路径，并整理了短期vs长期的系统对比。"),
        ],
    ),
    # ── 补全：大二剩余课程 ──
    "中国政治思想史": dict(
        insights=[
            Insight(author="22级小马", grade="22级", score="89", content=(
                "孙晓春老师的中国政治思想史从商周一直讲到近代，时间跨度极大。我的方法是'抓大放小'："
                "把课程分成四个大时段——先秦（诸子百家奠定中国政治思想的基本问题域）、汉唐（儒学"
                "意识形态化与道教/佛教的政治思想的互动）、宋明（理学的政治哲学体系）、近代（中西碰撞"
                "下的变革思潮）。每个时段抓住一两个核心命题：先秦是'秩序从何而来'（礼vs法vs道vs无为），"
                "汉唐是'天人感应与君权合法性'，宋明是'天理与人欲、内圣与外王'，近代是'中学与西学"
                "的体用之争'。考试偏好比较题（如'比较孟子和荀子的人性论及其政治意涵'），所以要能跨思想家"
                "建立对话。课堂笔记很重要，老师在课上对原文的解读比教材深得多。"
            )),
        ],
        materials=[
            Material(name="中国政治思想史-四大时段框架", material_type="复习大纲", contributor="22级小马", grade="22级",
                     recommendation_reason="按先秦/汉唐/宋明/近代四段梳理核心命题和代表人物，附每个时段的关键原文摘录。"),
            Material(name="中国政治思想史-经典比较题库", material_type="真题", contributor="22级小马", grade="22级",
                     recommendation_reason="整理了12组高频比较题（孟子vs荀子/朱熹vs王阳明/黄宗羲vs卢梭等），每组附参考答案要点。"),
        ],
        contributors=[
            Contributor(name="22级小马", contribution="建立了四时段框架和12组经典比较题库，把跨越三千年的思想史变成了可把握的演变脉络。"),
        ],
    ),
    "外国经济学说史": dict(
        insights=[
            Insight(author="23级小钱", grade="23级", score="90", content=(
                "蒋雅文老师的外国经济学说史是按'学派'来讲的：重商主义→重农学派→古典学派（斯密、"
                "李嘉图、马尔萨斯）→边际革命（杰文斯、门格尔、瓦尔拉斯）→新古典（马歇尔）→凯恩斯"
                "革命→新古典综合派→新自由主义（哈耶克、弗里德曼）。核心不是记住每个人说了什么，而是"
                "理解每个学派的'核心问题'——他们试图回答什么时代问题？比如斯密回答的是'国家财富从何"
                "而来'（工业革命前夕），凯恩斯回答的是'市场为什么失灵、政府该做什么'（大萧条之后）。"
                "考试以论述为主，典型的题目是'比较古典学派和凯恩斯学派对 X 问题的不同看法'。"
                "建议做个'思想演化时间轴'，标注每个学派的核心问题、关键概念、政策主张和历史背景。"
            )),
        ],
        materials=[
            Material(name="外国经济学说史-学派演化时间轴", material_type="笔记", contributor="23级小钱", grade="23级",
                     recommendation_reason="从重商主义到新自由主义的完整演化图谱，标注每个学派的核心问题/关键概念/政策主张。"),
            Material(name="外国经济学说史-学派对比表", material_type="复习大纲", contributor="23级小钱", grade="23级",
                     recommendation_reason="古典vs凯恩斯vs新古典综合vs新自由主义在价值论/分配论/危机论/政策观四个维度的系统对比。"),
        ],
        contributors=[
            Contributor(name="23级小钱", contribution="构建了学派演化时间轴和四维对比体系，把互不关联的学派串成了一个有逻辑的演化故事。"),
        ],
    ),
    # ── 补全：大三剩余课程 ──
    "西方哲学史": dict(
        insights=[
            Insight(author="22级小韩", grade="22级", score="86", content=(
                "西方哲学史从古希腊到黑格尔，内容极其庞大。我的策略是'抓主干、弃枝叶'：主干就是"
                "形而上学和认识论这两条线的演变——形而上学追问'存在是什么'（从泰勒斯的'水'到柏拉图"
                "的'理念'到亚里士多德的'实体'到黑格尔的'绝对精神'），认识论追问'我们如何知道'"
                "（从柏拉图的'回忆说'到笛卡尔的'我思'到洛克的'白板说'到康德的'先天综合判断'）。"
                "每个哲学家只要搞清楚他在这两条线上的立场，基本就能应对考试。期末通常是一道论述一道"
                "文本分析，文本分析会给一段原文让你解释论证结构。建议精读几段经典原文（笛卡尔《第一"
                "哲学沉思集》的前两个沉思、康德《纯粹理性批判》导言的前几页），理解'论证是怎样展开的'"
                "比记住'结论是什么'更重要。"
            )),
        ],
        materials=[
            Material(name="西方哲学史-形上·认识论双线演化图", material_type="笔记", contributor="22级小韩", grade="22级",
                     recommendation_reason="按形上/认识两条主线标注从古希腊到黑格尔的演变，每个思想家一句话写明他在两条线上的立场。"),
            Material(name="西方哲学史-经典原文论证拆解", material_type="阅读材料", contributor="22级小韩", grade="22级",
                     recommendation_reason="选取6段考试高频原文，逐句拆解论证结构（前提→推理→结论），附常见考题。"),
        ],
        contributors=[
            Contributor(name="22级小韩", contribution="以形上/认识论双线梳理了西方哲学的主干，并拆解了6段经典原文的论证结构，把'玄学'变成了可追踪的逻辑。"),
        ],
    ),
    "比较政治": dict(
        insights=[
            Insight(author="23级小朱", grade="23级", score="88", content=(
                "比较政治是方法导向的课：学的不是某个国家的政治，而是'如何系统地比较不同国家的政治'。"
                "核心方法包括：最相似体系设计（MSSD）、最差异体系设计（MDSD）、定性比较分析（QCA）。"
                "课程围绕几个核心议题展开：民主化（为什么有的国家民主化了而有的没有？）、国家能力"
                "（为什么有的国家能有效征税和提供公共品？）、政治暴力（内战、恐怖主义的根源是什么？）、"
                "福利国家（为什么有的国家福利更慷慨？）。每个议题学 2-3 个理论解释和一个经验案例。"
                "期末以论文为主，选题自由但要求有明确的比较方法和理论对话。建议尽早确定论文选题，"
                "期中就写好文献综述，这样期末压力小很多。"
            )),
        ],
        materials=[
            Material(name="比较政治-核心方法手册", material_type="笔记", contributor="23级小朱", grade="23级",
                     recommendation_reason="系统介绍MSSD/MDSD/QCA/过程追踪四种比较方法，每种附经典研究案例。"),
            Material(name="比较政治-论文写作指南", material_type="复习大纲", contributor="23级小朱", grade="23级",
                     recommendation_reason="从选题→文献综述→理论框架→经验分析→结论的完整论文写作流程，附优秀论文范例点评。"),
        ],
        contributors=[
            Contributor(name="23级小朱", contribution="整理了四种核心比较方法的手册和论文写作全流程指南，帮助同学从'描述'走向'解释'。"),
        ],
    ),
    # ── 补全：大四 ──
    "毕业论文": dict(
        insights=[
            Insight(author="22级小徐", grade="22级", score="95", content=(
                "PPE 毕业论文最关键的三个节点：选题、文献综述、方法设计。选题一定要在三个学科的交叉处找，"
                "纯经济学或纯政治学的题目虽然能做但很难体现 PPE 特色。我的经验是选一个具体的政策问题"
                "（比如'碳税对中国不同收入群体的分配效应'、'社区治理中社会组织的作用机制'），这样既能用"
                "经济学方法做实证，又能用政治学/哲学框架做规范分析。文献综述不要写成'谁说了什么'的流水账，"
                "而要围绕你的研究问题组织成'已有研究回答了什么、没回答什么、你打算填补什么空白'的三段论。"
                "方法上，PPE 论文可以用定量（回归/实验）、定性（案例比较/过程追踪）或混合方法，选你最"
                "擅长的就好。时间管理是关键：大三暑假确定选题和导师，大四上学期完成数据收集和分析，"
                "寒假写出初稿，下学期修改打磨。"
            )),
        ],
        materials=[
            Material(name="PPE毕业论文-选题指南与范例", material_type="笔记", contributor="22级小徐", grade="22级",
                     recommendation_reason="整理了近三年优秀PPE论文选题、核心方法、导师评价要点，帮你在交叉学科处找到好题目。"),
            Material(name="PPE毕业论文-文献综述写作框架", material_type="复习大纲", contributor="22级小徐", grade="22级",
                     recommendation_reason="提供'gap-spotting'文献综述三步法（梳理→批判→定位），附3篇优秀综述范例。"),
            Material(name="PPE毕业论文-时间规划模板", material_type="笔记", contributor="22级小徐", grade="22级",
                     recommendation_reason="从大三暑假到毕业答辩的详细时间线，标注每个阶段的里程碑和常见拖延陷阱。"),
        ],
        contributors=[
            Contributor(name="22级小徐", contribution="贡献了选题指南、文献综述框架和时间规划模板三件套，为 PPE 论文全流程打了样。"),
        ],
    ),
}


def build_year(year: str) -> list:
    rows = []
    for c in COURSES_BY_YEAR.get(year, []):
        course = CourseData(year=year, updated_at=SEED_DATE, **c)
        extra = ENRICHMENT.get(course.name)
        if extra:
            course.insights = extra["insights"]
            course.materials = extra["materials"]
            course.contributors = extra["contributors"]
        # 自动生成仿真 OSS 下载链接
        for m in course.materials:
            m.file_link = _oss_link(m.name)
        rows.append(course.to_dict())
    return rows


def main():
    print(f"course_db_dir: {settings.course_db_dir}")
    total_courses = 0
    total_insights = 0
    total_materials = 0
    for year in WIKI_YEAR_NODES:
        rows = build_year(year)
        write_course_db(settings.course_db_dir, year, rows)
        n = len(rows)
        enriched = sum(1 for r in rows if r["insights"])
        mats = sum(len(r.get("materials", [])) for r in rows)
        total_courses += n; total_insights += enriched; total_materials += mats
        print(f"  {year}  课程={n}  有心得={enriched}  资料={mats}")
    print(f"合计: {total_courses} 门课 → {total_courses} 个独立 JSON + index.json, "
          f"{total_insights} 门含心得, {total_materials} 份资料")
    print("done.")


if __name__ == "__main__":
    main()
