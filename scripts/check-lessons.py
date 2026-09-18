#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""课程完成度校验 —— 教程的唯一验证接缝。

为什么只有这一个接缝
--------------------
`docs/lessons/README.md` §7 把「一课算完成」写成了 7 条契约。这 7 条里能机械判定的
部分集中在这里一次判定，而不是每课各写一套检查：一处改动就能让全部课同时得到
同一个口径的结论。不能机械判定的部分（论证是否成立、去重是否真的落地、产物是否
可复核）**不假装能自动化**，报告里单列「需人工 review」。

判定的 7 条契约（详见 README §7 与 issue #1）
--------------------------------------------
1. 课文存在，且按对应样板组织（因果单元 8 步 / 模型深潜 8 步）
2. 至少一道可判定的诊断题
3. 至少一份可运行 notebook，且与课文互相引用
4. 可复核产物（仅本机可实操的课强制）
5. 证据分级显式（[S#] / [P#] / 工程假设 / 参赛者自报）
6. 三处同步（课程总表、notebook 映射表、主题权威归属表）
7. 主题去重到位

2026-09-18 改造（issue #14 / spec #13）
--------------------------------------
课程体系从三层 `L<层>-<序号>` 重构为 **8 课连续编号 `DD`**（00–07）。本脚本随之做
三件事，其余判定逻辑保持原样：

1. **课程发现改为目录扫描。** 此前课号表只从 README §3 课程总表解析，新课先于总表
   存在时会被整个跳过。现在 `docs/lessons/` 下的 `DD-*.md` 与历史 `L*-*.md` 都被
   扫描并进统计（「先于索引存在」不再等于「不被检查」）。
2. **三条硬指标**（D3 前三行）对**连续编号课**生效：篇幅上限、正式配图下限、行内
   ASCII 因果链下限。历史层编号课暂不判（它们正在被逐课删除），但会打印原始数值，
   便于删除前对比。
3. **旧课号残留判定改向。** 连续编号课正文里出现 `L\\d-\\d\\d` 视为 STALE（迁移期
   应改用文字指路；改造完成后应指向已存在的新课）。历史课维持原判定。

「第 0X 课」在新体系里是合法写法（它就是新课号），不再误报。

其中 1 的「样板」部分用关键词覆盖做**软判定**（报 WARN，不判 FAIL）：小节标题的措辞
本来就有差异，强行严格匹配会把「写得好但标题不同」判成失败，那是假的准确性。

用法
----
    python3 scripts/check-lessons.py            # 人读报告
    python3 scripts/check-lessons.py --json     # 机器读
    python3 scripts/check-lessons.py --quiet    # 只输出失败项

退出码
------
    0  全部通过（或属于有理由的豁免）
    1  存在**已归票**的缺口（报告里写明归到哪个 issue）
    2  存在**未被跟踪**的缺口 —— 这才是需要立刻处理的状态

不引入测试框架：形态与 `scripts/` 下既有审计脚本一致，只用标准库。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "docs" / "lessons"
NOTEBOOK = ROOT / "notebook"
COURSE_INDEX = LESSONS / "README.md"
NB_INDEX = NOTEBOOK / "README.md"

# 连续编号课（2026-09-18 新体系）与历史层编号课。迁移期内两种并存：
# 连续编号是现状主线，层编号课正在被逐课吸收删除。
COURSE_RE = re.compile(r"^(?:\d\d|L\d-\d\d)$")
CONTINUOUS_RE = re.compile(r"^\d\d$")
# 发现用的文件名模式：`DD-标题.md`（连续编号）与 `L*-标题.md`（历史）。
# 排除 appendix/（附录不进主线编号）与 assets/。
COURSE_FILE_RE = re.compile(r"^(?:(?P<cont>\d\d)|(?P<legacy>L\d-\d\d))-[^/]+\.md$")

# 三条硬指标（spec D3 前三行，以 02 课的实测现状为标尺）。
# 只对**连续编号课**生效；历史课正在被删除，判它没有意义。
LIMIT_LINES = 700
LIMIT_CHARS = 30_000
MIN_FIGURES = 3      # 正文以 ![...](path) 引用 assets 下图片的计数
MIN_ASCII = 8        # ``` 围栏块且语言标注为 text 的计数

# 诊断题的不同写法（各课历史上用过不同标题）
DIAG_RE = re.compile(r"诊断题|理解检查题|自检问题|检查题")

# 样板槽位：即使标题措辞不同，也应能在某个小节标题里找到对应关键词。
# 软判定，只报 WARN。
CAUSAL_SLOTS = {
    "直觉解释": r"直觉|为什么需要|先说清楚|为什么",
    "机制或数学对象": r"机制|数学|对象|概念|原理|是什么",
    "实验或数据流程": r"流程|步骤|流水线|实现|怎样|怎么",
    "失败与噪声": r"噪声|失败|故障|陷阱|常见问题|风险",
    "与 VC2026 的关系": r"VC2026|本赛|比赛|任务",
    "对模型的影响": r"对模型的影响|模型影响|影响",
    "可复现实践": r"可复现|实践|交付|运行|产物",
    "诊断题": r"诊断题|理解检查题|自检问题",
}
MODEL_SLOTS = {
    "它赌什么": r"赌什么|赌注|假设",
    "输入输出契约": r"输入|输出|契约|维度|接口",
    "架构": r"架构|模块|结构|层",
    "训练目标": r"训练|损失|目标|loss",
    "数据": r"数据|语料|语料库|暴露",
    "官方代码怎么跑": r"代码|命令|怎么跑|运行|环境",
    "适配缺口": r"缺口|适配|要改|迁移",
    "诊断题": r"诊断题|理解检查题|自检问题",
}

# 使用模型深潜样板的课。L2-05 是方法论课（统计机制替代生物机制），
# 按 README §2 阶段表走因果单元样板，因此不在本表内。
# 2026-09-18：新课号体系下，05（Stack）与 06（其余路线全景）走模型深潜样板。
# L2-01 已于 2026-09-18 被 02 课吸收删除；02 走模型深潜样板（与 02 正文 §9.1 一致）。
MODEL_SLOT_COURSES = {"02", "L2-02", "L2-03", "L2-04", "L2-06", "05", "06"}

# 证据分级出现的写法
EVIDENCE_TAGS = {
    "[S#] 官方事实": r"\[S\d",
    "[P#] 论文章节": r"\[P\d",
    "工程假设": r"工程假设",
    "参赛者自报": r"参赛者自报",
}

# 已经不在使用的旧编号体系。配图文件名是有意保留的例外，
# 因此只查正文里的「第 N 课 / 第N课」写法，且「原第 N 课」是允许的历史标注。
STALE_RE = re.compile(r"(?<!原)第\s?(0[2-9]|10)\s?课")

# 连续编号课正文里的历史课号提及。迁移期内应使用文字指路（「第 03 课」），
# 不给指向不存在文件的链接；改造完成后这些提及应全部消除。
#
# **例外：资产与图源的既定文件名。** `L2-01-state-architecture.webp`、
# `L2-01-state-architecture-facts.md` 这类名字记录在生成溯源日志里，改名会破坏溯源，
# 是 spec 明确保留的（同 README §9.2 的约定）。因此只在**非路径上下文**里判 STALE：
# 先剔掉行内的 `路径/文件名.ext`、行内代码 `...` 与 Markdown 链接目标，
# 剩下的裸 `L\\d-\\d\\d` 才算真的在说「旧课号」。
STALE_LEGACY_RE = re.compile(r"L\d-\d\d")
_PATHLIKE_RE = re.compile(r"`[^`]*`|\]\([^)]*\)|[\w./-]*L\d-\d\d[\w./-]*\.\w+")


def stale_legacy_hits(text: str) -> list[str]:
    """剔掉资产文件名与代码片段后，正文里还剩哪些裸历史课号。"""
    stripped = _PATHLIKE_RE.sub(" ", text)
    return sorted(set(STALE_LEGACY_RE.findall(stripped)))

NB_WHITELIST = "test.ipynb"

# --------------------------------------------------------------------------
# 豁免：**每条都必须给理由**。不加理由的豁免就是放宽判定。
# --------------------------------------------------------------------------
EXEMPT: dict[tuple[str, str], str] = {
    # ---- 冻结的锚点课 00 / 01 --------------------------------------------
    # 2026-09-18：课号由 L0-00 / L0-01 收敛为 00 / 01（连续编号体系）。
    # 正文一个字都不许动（已发布飞书并被精读），因此下列缺口只能豁免。
    ("00", "DIAG"): "早于完成度契约；已发布飞书并被精读，正文冻结（spec Out of Scope）。",
    ("00", "NB_DECL"): "90/91 号 notebook 是官方 Colab 逐字节固定副本，"
                       "映射表已声明不属于课程序列；本课无教学 notebook 是对的。",
    ("00", "NB_BACKREF"): "同上（正文冻结）。",
    ("00", "ASCII"): "冻结前写的课，早于 D3 的「ASCII ≥ 8」密度契约；"
                     "已有 4 个 ASCII 块。正文不许改动，故不追补。",
    ("01", "NB_DECL"): "notebook/README.md 已声明本课映射 01_vc2026_data.ipynb；"
                       "正文不许改动，缺口在 notebook 侧补齐（原 L0-01 的同一处理）。",
    ("01", "NB_BACKREF"): "正文已发布飞书并冻结，不允许加链接；"
                          "缺口改在 notebook/README.md 侧补齐映射。",
    # ---- 纯阅读课 --------------------------------------------------------
    ("L1-01", "NB_DECL"): "纯阅读课，产物是读者自己的「赌注对照表」（材料 × 赌注 × "
                          "核心假设 × 天花板判据 × 本赛可用性），不存在需要 kernel "
                          "执行的计算。映射表已按豁免登记，理由写在 notebook/README.md。",
    ("L1-01", "NB_BACKREF"): "同上：本课零算力（README 阶段表第 1 阶段），"
                             "没有可回指的动手材料。",
    # ---- 连续编号课的篇幅豁免（2026-09-18） ------------------------------
    # 只豁免 LIMITS（篇幅），不豁免配图与 ASCII 图——那两项是内容密度契约，
    # 冻结不是「不写图」的理由。原始判定照常打印。
    ("01", "LIMITS"): "正文已发布飞书并被精读，按 spec「Out of Scope」冻结不许改动"
                      "（约 1,052 行，早于 D3 的 700 行上限订立）。原始判定照常打印。",
}

# --------------------------------------------------------------------------
# 冻结课的槽位措辞别名。键是 (课号, 槽位名)，值是要补进该槽位正则的额外分支。
# 只在**正文不许改动**的课上使用；能改标题的就直接改标题，不要加别名。
# 每一条都要能指到真实存在的小节，加错了等于放宽判定。
SLOT_ALIAS: dict[tuple[str, str], str] = {
    # 00 / 01 已发布飞书、正文冻结。00 用「先建立生物学直觉」讲机制、
    # 用「当前尚未解决的问题」讲失败与噪声、用「应该学到什么」讲实践。
    # （2026-09-18 课号由 L0-00 / L0-01 收敛为 00 / 01。）
    ("00", "机制或数学对象"): r"|生物学直觉|建立.*直觉|什么是",
    ("00", "失败与噪声"): r"|尚未解决|容易误读|暴露的问题|边界",
    ("00", "对模型的影响"): r"|关键差异|学到什么|工程判断",
    ("00", "可复现实践"): r"|学到什么|学习顺序|建议",
    ("00", "诊断题"): r"|尚未解决",
    # 01 同上（正文冻结，回指改在 notebook/README.md 侧补齐）。
    # 它用 §5.3「显式零值仍然有成本」讲失败、§3.10 讲模型、§7 讲动手。
    ("01", "失败与噪声"): r"|误区|成本|不能混为一谈|缺失什么",
    ("01", "对模型的影响"): r"|模型能|能学到什么|保留了什么",
    ("01", "可复现实践"): r"|审计与可视化|复现脚本|预检|验收标准",
    # L1-01 是纯阅读课，「实验或数据流程」对应的是 §3.3 末尾给出的
    # 本项目消融顺序（无变化 → 均值 → 加性/低秩 → 跨背景 target-effect
    # → 复杂模型），标题写的是「按什么顺序做实验」。
    ("L1-01", "实验或数据流程"): r"|顺序|消融",
    # 02 用「训练目标：为什么不能换成 MSE」讲目标和「它保证什么，不保证什么」
    # 讲边界；「对模型的影响」这一槽位由 §5.5 + §8.1 的失败面覆盖。
    ("02", "对模型的影响"): r"|对模型|要改什么|适配缺口",
}

# 已归票的缺口：真实存在、但由某个 issue 跟踪。不许静默消失。
#
# 2026-09-18：全部清空。#12 把 notebook 映射与互相引用补齐后，原四条
# （NB_DECL / NB_BACKREF / SLOTS）都已实际解决：所有课要么有映射与回指，
# 要么有带理由的 EXEMPT。**这张表为空才是正常状态**；再往里加条目时，
# 必须同时贴上跟踪它的 issue 号，否则就该直接修掉。
# --------------------------------------------------------------------------
KNOWN_GAPS: dict[tuple[str, str], str] = {}

# 尚未写的课：文件缺失是**预期状态**，归到写它的那一票，不算未跟踪失败。
#
# 2026-09-18：#3–#9 七课全部写完，这张「待写」清单已清空。**故意留空而不是
# 删掉循环**：它的作用是让后续新开课时能一行登记「这一票正在写」，同时告诉
# 校验器「文件缺失是预期状态」而不是未跟踪失败。现在任何课的文件缺失都会
# 直接算 FAIL（退出码 2）——因为已经没有课处于待写状态了。
PENDING_COURSES: list[tuple[str, str]] = []
for _num, _ticket in PENDING_COURSES:
    KNOWN_GAPS[(_num, "FILE")] = _ticket

# 附录课（在 README §10 声明，不在 §3 的课程总表里）
EXTRA_COURSES = [
    ("L2-06", "appendix/L2-06-模型卡.md"),
]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def parse_course_table() -> list[dict]:
    """从 README §3 课程总表解析课号 → 文件路径。

    2026-09-18 起本函数只作**补充**：课程主体由 `discover_courses()` 目录扫描得到。
    这里保留的原因有两个——(1) 在索引里被标为〔待写〕而文件已存在的矛盾仍要报出来；
    (2) 索引声明的路径与磁盘实际路径不一致时要能发现。
    索引里出现但磁盘上没有的行，不再**制造**一个课程条目（现实是文件为准），
    但仍会作为索引问题记录。
    """
    text = read(COURSE_INDEX)
    try:
        sec = text.split("## 3. 课程总表", 1)[1].split("\n## ", 1)[0]
    except IndexError:
        sys.exit("找不到 README 的「## 3. 课程总表」小节")

    rows = []
    for line in sec.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not COURSE_RE.match(cells[0]):
            continue
        num, ref = cells[0], cells[1]
        m = re.search(r"\]\(([^)]+)\)", ref) or re.search(r"`([^`]+\.md)`", ref)
        rows.append({"num": num, "path": m.group(1) if m else None,
                     "pending": "待写" in ref, "in_table": True})
    return rows


def discover_courses() -> tuple[list[dict], list[str]]:
    """扫描 `docs/lessons/` 得到全部课程（不含 appendix/）。

    返回 (课程列表, 索引问题列表)。课程条目按课号排序，连续编号在前。
    这样做的理由见模块 docstring 第 1 条：新课先于索引存在时也必须进统计，
    否则新写的课会在「课数」里凭空消失，所有检查形同虚设。
    """
    problems: list[str] = []
    found: dict[str, dict] = {}

    for f in sorted(LESSONS.glob("*.md")):
        if f.name == "README.md":
            continue
        m = COURSE_FILE_RE.match(f.name)
        if not m:
            continue
        num = m.group("cont") or m.group("legacy")
        found[num] = {
            "num": num,
            "path": f.name,
            "pending": False,
            "in_table": False,
            "continuous": bool(m.group("cont")),
        }

    # 用索引里的行补「待写」与「路径不一致」两类信息；不新建课程。
    for row in parse_course_table():
        num = row["num"]
        if num in found:
            found[num]["in_table"] = True
            if row["path"] and row["path"] != found[num]["path"]:
                problems.append("README §3 的 %s 指向 %s，磁盘上是 %s"
                                % (num, row["path"], found[num]["path"]))
            if row["pending"]:
                problems.append("README §3 把 %s 标为〔待写〕，但文件已存在" % num)
            continue
        # 附录课在 appendix/ 子目录里，按声明路径直接确认存在性，不进编号主线。
        if row["path"] and (LESSONS / row["path"]).exists():
            continue
        problems.append("README §3 声明了 %s（%s），磁盘上找不到对应文件"
                        % (num, row["path"] or "无路径"))

    courses = sorted(found.values(),
                     key=lambda c: (not c["continuous"], c["num"]))
    return courses, problems


def parse_notebook_map() -> dict[str, list[str]]:
    """从 notebook/README.md 解析「课程号 → notebook 路径」映射表。

    要求的行格式（任何表格里都行）：首格是课程号，第二格含 notebook 路径。
        | L3-04 | [02：State 模型与迁移](02_state_model_and_transfer.ipynb) | ... |
    """
    if not NB_INDEX.exists():
        return {}
    out: dict[str, list[str]] = {}
    for line in read(NB_INDEX).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not COURSE_RE.match(cells[0]):
            continue
        for m in re.finditer(r"\]\(([^)]+\.ipynb)\)|`([^`]+\.ipynb)`", cells[1]):
            out.setdefault(cells[0], []).append(m.group(1) or m.group(2))
    return out


def headings(text: str) -> list[str]:
    return [h.strip() for h in re.findall(r"^#{2,3}\s+(.+)$", text, re.M)]


def check_course(c: dict, nb_map: dict[str, list[str]]) -> dict:
    num = c["num"]
    res: dict = {"num": num, "path": c["path"], "checks": {}, "notes": []}
    f = (LESSONS / c["path"]) if c["path"] else None

    # ---- 课文存在 & 与索引一致 ------------------------------------------
    exists = bool(f and f.exists())
    res["exists"] = exists
    if not exists:
        res["checks"]["FILE"] = ("FAIL", "索引里指向 %s，文件不存在" % c["path"])
        return res
    if c["pending"]:
        res["checks"]["FILE"] = ("FAIL", "索引标为〔待写〕，但文件已存在（索引未更新）")
    else:
        res["checks"]["FILE"] = ("PASS", None)

    text = read(f)
    hs = headings(text)

    # ---- 诊断题 ---------------------------------------------------------
    hit = [h for h in hs if DIAG_RE.search(h)]
    res["checks"]["DIAG"] = ("PASS", hit[0] if hit else None) if hit else \
        ("FAIL", "没有任何小节标题匹配诊断题（%s）" % DIAG_RE.pattern)

    # ---- notebook 映射与互相引用 ----------------------------------------
    declared = nb_map.get(num, [])
    if declared:
        missing = [p for p in declared if not (NOTEBOOK / p).exists()]
        if missing:
            res["checks"]["NB_EXISTS"] = ("FAIL", "映射表声明的 notebook 不存在：%s"
                                          % ", ".join(missing))
        else:
            res["checks"]["NB_EXISTS"] = ("PASS", ", ".join(declared))
        res["checks"]["NB_DECL"] = ("PASS", ", ".join(declared))
    else:
        res["checks"]["NB_DECL"] = ("FAIL", "notebook/README.md 的映射表未声明本课的 notebook")

    backref = "notebook/" in text
    res["checks"]["NB_BACKREF"] = ("PASS", None) if backref else \
        ("FAIL", "正文里没有任何到 notebook/ 的链接（读者走不到动手材料）")

    # ---- 样板槽位（软判定） ---------------------------------------------
    # 不是所有 L2 课都用模型深潜样板：README §2 阶段表把 L2-05 归为方法论课，
    # 用的是 L1/L3 的因果单元样板（生物机制换成统计机制）。按课号单独指定，
    # 不要用 num.startswith("L2") 一刀切。
    slots = MODEL_SLOTS if num in MODEL_SLOT_COURSES else CAUSAL_SLOTS
    # 冻结课（正文已发布飞书、不许改动）的标题措辞与本样板不同，但它们用
    # 自己的话覆盖了同样的语义。逐槽位补一条「本课实际使用的措辞」，
    # 而不是去改冻结正文的标题——改标题会破坏飞书侧已被精读的版本。
    slots = {k: slots[k] + SLOT_ALIAS.get((num, k), "") for k in slots}
    join = " || ".join(hs)
    missing_slots = [k for k, pat in slots.items() if not re.search(pat, join)]
    if missing_slots:
        res["checks"]["SLOTS"] = ("WARN", "小节标题里没找到：%s（标题措辞可不同，需人工确认语义是否覆盖）"
                                  % "、".join(missing_slots))
    else:
        res["checks"]["SLOTS"] = ("PASS", "%d/%d 槽位" % (len(slots), len(slots)))

    # ---- 证据分级（信息性，不判失败） ------------------------------------
    res["ev"] = {name: len(re.findall(pat, text))
                 for name, pat in EVIDENCE_TAGS.items()}

    # ---- 三条硬指标（spec D3 前三行，只判连续编号课） --------------------
    # 判的是「写够了没有」，不判写作内部实现。数值一律打印出来，
    # 即使 PASS 或 EXEMPT 也照常可见——否则豁免会掩盖真实体量。
    lines = len(text.splitlines())
    chars = len(re.sub(r"\s", "", text))
    figs = len(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text))
    ascii_blocks = len(re.findall(r"^```text\s*$", text, re.M))
    res["metrics"] = {"lines": lines, "chars": chars,
                      "figures": figs, "ascii": ascii_blocks}

    if c.get("continuous"):
        over = []
        if lines > LIMIT_LINES:
            over.append("%d 行 > %d" % (lines, LIMIT_LINES))
        if chars > LIMIT_CHARS:
            over.append("%d 字 > %d" % (chars, LIMIT_CHARS))
        if over:
            res["checks"]["LIMITS"] = ("FAIL", "篇幅超限：" + "；".join(over))
        else:
            res["checks"]["LIMITS"] = ("PASS", "%d 行 / %d 字" % (lines, chars))

        if figs < MIN_FIGURES:
            res["checks"]["FIGURES"] = ("FAIL", "正式配图 %d 张 < %d"
                                        % (figs, MIN_FIGURES))
        else:
            res["checks"]["FIGURES"] = ("PASS", "%d 张正式配图" % figs)

        if ascii_blocks < MIN_ASCII:
            res["checks"]["ASCII"] = ("FAIL", "行内 ASCII 因果链 %d 个 < %d"
                                      % (ascii_blocks, MIN_ASCII))
        else:
            res["checks"]["ASCII"] = ("PASS", "%d 个 ASCII 块" % ascii_blocks)

    # ---- 旧课号残留 ------------------------------------------------------
    # 连续编号课：正文里出现 `L\\d-\\d\\d` 即为 STALE——迁移期应改用文字指路
    # （「第 03 课」），改造完成后应指向真实存在的新课。
    # 历史层编号课：维持原判定（「第 N 课」这种旧写法），它们正在被逐课删除。
    if c.get("continuous"):
        legacy = stale_legacy_hits(text)
        if legacy:
            res["checks"]["STALE"] = ("WARN", "正文里出现历史课号：%s"
                                      % "、".join(legacy))
        else:
            res["checks"]["STALE"] = ("PASS", None)
    else:
        stale = STALE_RE.findall(text)
        if stale:
            res["checks"]["STALE"] = ("WARN", "出现旧编号写法（非「原第 N 课」）：%s"
                                      % "、".join("第 %s 课" % s for s in sorted(set(stale))))
        else:
            res["checks"]["STALE"] = ("PASS", None)
    return res


def check_links() -> list[str]:
    """`docs/lessons/**` 正文里的相对链接是否都指向真实文件。

    范围刻意限定在教程自己的表面（含它到 CONTEXT.md / docs/style 的回指）；
    全仓链接检查是 #10 的事。
    """
    bad = []
    pat = re.compile(r"\]\(([^)#][^)]*)\)")
    for f in sorted(LESSONS.rglob("*.md")):
        for i, line in enumerate(read(f).splitlines(), 1):
            for target in pat.findall(line):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                clean = target.split("#")[0]
                if not clean:
                    continue
                if "<" in clean or ">" in clean:
                    continue
                if not (f.parent / clean).exists():
                    bad.append("%s:%d  %s" % (f.relative_to(ROOT).as_posix(), i, target))
    return bad


def check_notebook_index() -> list[str]:
    """notebook/README.md 里提到的 notebook 是否都存在，以及非课程单元是否声明。"""
    problems = []
    if not NB_INDEX.exists():
        return ["notebook/README.md 不存在"]
    text = read(NB_INDEX)
    for m in re.finditer(r"\]\(([^)]+\.ipynb)\)|`([^`]+\.ipynb)`", text):
        p = m.group(1) or m.group(2)
        if not (NOTEBOOK / p).exists():
            problems.append("notebook/README.md 指向不存在的 %s" % p)
    for ref in ("90_ref_", "91_ref_", NB_WHITELIST):
        if ref not in text:
            problems.append("notebook/README.md 没有声明非课程单元 %s" % ref)
    return problems


def status_for(num: str, check: str) -> str:
    """把原始结果改写成 PASS / EXEMPT / KNOWN_GAP / FAIL。"""
    if (num, check) in EXEMPT or ("__ALL__", check) in EXEMPT:
        return "EXEMPT"
    if (num, check) in KNOWN_GAPS or ("__ALL__", check) in KNOWN_GAPS:
        return "KNOWN_GAP"
    return "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="只输出非 PASS 项")
    args = ap.parse_args()

    courses, index_problems = discover_courses()
    nb_map = parse_notebook_map()
    results = [check_course(c, nb_map) for c in courses]
    links = check_links()
    nb_problems = check_notebook_index() + index_problems

    tally = {"PASS": 0, "EXEMPT": 0, "KNOWN_GAP": 0, "FAIL": 0, "WARN": 0}
    untracked: list[str] = []
    tracked: list[str] = []
    exempted: list[str] = []

    for r in results:
        for check, (st, detail) in list(r["checks"].items()):
            if st == "PASS":
                tally["PASS"] += 1
                continue
            if st == "WARN":
                reason = status_for(r["num"], check)
                if reason == "EXEMPT":
                    tally["EXEMPT"] += 1
                    exempted.append("%s %s — %s" % (r["num"], check, EXEMPT.get((r["num"], check)) or EXEMPT[("__ALL__", check)]))
                elif reason == "KNOWN_GAP":
                    tally["KNOWN_GAP"] += 1
                    tracked.append("%s %s — %s" % (r["num"], check, detail))
                else:
                    tally["WARN"] += 1
                continue
            reason = status_for(r["num"], check)
            if reason == "EXEMPT":
                tally["EXEMPT"] += 1
                exempted.append("%s %s — %s" % (r["num"], check, EXEMPT.get((r["num"], check)) or EXEMPT[("__ALL__", check)]))
            elif reason == "KNOWN_GAP":
                tally["KNOWN_GAP"] += 1
                tracked.append("%s %s — %s" % (r["num"], check, detail))
            else:
                tally["FAIL"] += 1
                untracked.append("%s %s — %s" % (r["num"], check, detail))

    for p in links:
        untracked.append("LINK 断链 — %s" % p)
        tally["FAIL"] += 1
    for p in nb_problems:
        untracked.append("NB_INDEX — %s" % p)
        tally["FAIL"] += 1

    # 退出码语义：
    #   0 = 没有未跟踪失败，也没有待清的归票缺口 → 教程完成
    #   1 = 没有未跟踪失败，但仍有 KNOWN_GAP（真实存在、由 issue 跟踪的缺口）
    #   2 = 存在未跟踪失败（新破的东西）
    # 豁免**不**降低退出码：豁免是「这条契约对本课本来就不适用」的
    # 书面判断，不是待清的欠债。把它算成非零会让「登记豁免」和
    # 「留一个缺口」在退出码上无法区分，等于惩罚诚实登记。
    rc = 2 if untracked else (1 if tracked else 0)

    if args.json:
        print(json.dumps({"tally": tally, "courses": results, "links": links,
                          "notebook_index": nb_problems,
                          "untracked": untracked, "tracked": tracked,
                          "exempt": exempted, "exit": rc},
                         ensure_ascii=False, indent=2))
        return rc

    print("课程完成度校验 — 教程的唯一验证接缝")
    print("文档契约见 docs/lessons/README.md §7；本脚本判定其中可机械化的部分。")
    print("课数 %d ｜ PASS %d ｜ 豁免 %d ｜ 已归票 %d ｜ 未跟踪失败 %d"
          % (len(results), tally["PASS"], tally["EXEMPT"], tally["KNOWN_GAP"],
             tally["FAIL"]))
    print("=" * 78)

    for r in results:
        if not r.get("exists"):
            st = status_for(r["num"], "FILE")
            tag = {"KNOWN_GAP": "待写，已归票", "EXEMPT": "豁免"}.get(st, "未跟踪失败")
            print("\n%s  ✗ 文件缺失（%s）  %s" % (r["num"], tag, r["path"]))
            for c, (cs, d) in r["checks"].items():
                why = status_for(r["num"], c)
                if why == "EXEMPT":
                    cs = "EXEMPT"
                elif why == "KNOWN_GAP":
                    cs = "KNOWN_GAP"
                    d = "%s ｜ 归票 %s" % (d, KNOWN_GAPS.get((r["num"], c))
                                          or KNOWN_GAPS[("__ALL__", c)])
                print("    %-11s %-10s %s" % (c, cs, d))
            continue
        bad = {c: v for c, v in r["checks"].items() if v[0] != "PASS"}
        if args.quiet and not bad:
            continue
        mark = "✓" if not bad else "!"
        print("\n%s %s  %s" % (mark, r["num"], r["path"]))
        ev = r.get("ev", {})
        print("    证据分级：[S#]=%d  [P#]=%d  工程假设=%d  参赛者自报=%d"
              % (ev.get("[S#] 官方事实", 0), ev.get("[P#] 论文章节", 0),
                 ev.get("工程假设", 0), ev.get("参赛者自报", 0)))
        mt = r.get("metrics")
        if mt:
            print("    原始体量：%d 行 / %d 字 / 正式图 %d / ASCII %d"
                  % (mt["lines"], mt["chars"], mt["figures"], mt["ascii"]))
        for c, (st, d) in r["checks"].items():
            if st == "PASS" and args.quiet:
                continue
            # 把原始结果改写成含豁免 / 归票信息的最终状态，避免「显示 FAIL
            # 但其实已豁免」这种自相矛盾的输出。
            if st != "PASS":
                why = status_for(r["num"], c)
                if why == "EXEMPT":
                    st = "EXEMPT"
                    d = (EXEMPT.get((r["num"], c)) or EXEMPT[("__ALL__", c)]) + \
                        (" ｜ 原始判定：" + (d or ""))
                elif why == "KNOWN_GAP":
                    st = "KNOWN_GAP"
                    d = "%s ｜ 归票 %s" % (d or "", KNOWN_GAPS.get((r["num"], c))
                                          or KNOWN_GAPS[("__ALL__", c)])
            print("    %-11s %-10s %s" % (c, st, d or ""))

    if tracked:
        print("\n" + "=" * 78)
        print("已归票的缺口（真实存在，由 issue 跟踪；不因归票就算通过）")
        for t in tracked:
            print("  - %s" % t)

    if exempted:
        print("\n" + "=" * 78)
        print("豁免（每条都带理由；无理由的豁免就是放宽判定）")
        for t in exempted:
            print("  - %s" % t)

    print("\n" + "=" * 78)
    print("需人工 review（脚本不判，别假装它能自动化）")
    print("  - 论证是否成立、机制是否讲透、[P#] 是否被误当已验证结论")
    print("  - 主题去重是否真的落地（权威归属表指定的位置是否只剩回指）")
    print("  - 可复核产物是否真的可复核（数字能不能追到来源与证据等级）")
    print("  - 样板槽位是关键词判定，标题措辞不同但语义覆盖的不算缺失")

    if untracked:
        print("\n" + "=" * 78)
        print("未跟踪的失败（退出码 2）")
        for t in untracked:
            print("  - %s" % t)
    elif tracked:
        print("\n" + "=" * 78)
        print("退出码 1：没有未跟踪的失败，但仍有 %d 个已归票缺口待清。"
              % tally["KNOWN_GAP"])

    print("\n怎么用它验收后续每张 ticket：")
    print("  改完一课跑一次本脚本；该课不得出现 untracked 失败，")
    print("  且原本 PASS 的课不得变红。全绿（退出码 0）是教程完成的标准。")
    return rc


if __name__ == "__main__":
    sys.exit(main())
