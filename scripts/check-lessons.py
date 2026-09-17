#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""课程完成度校验 —— 教程的唯一验证接缝。

为什么只有这一个接缝
--------------------
`docs/lessons/README.md` §7 把「一课算完成」写成了 7 条契约。这 7 条里能机械判定的
部分集中在这里一次判定，而不是每课各写一套检查：一处改动就能让 15 门课同时得到
同一个口径的结论。不能机械判定的部分（论证是否成立、去重是否真的落地、产物是否
可复核）**不假装能自动化**，报告里单列「需人工 review」。

判定的 7 条契约（详见 README §7 与 issue #1）
--------------------------------------------
1. 课文存在，且按对应样板组织（L1/L3 因果单元 8 步、L2 模型深潜 8 步）
2. 至少一道可判定的诊断题
3. 至少一份可运行 notebook，且与课文互相引用
4. 可复核产物（仅本机可实操的课强制）
5. 证据分级显式（[S#] / [P#] / 工程假设 / 参赛者自报）
6. 三处同步（课程总表、notebook 映射表、主题权威归属表）
7. 主题去重到位

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

COURSE_RE = re.compile(r"^L\d-\d\d$")

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

# 证据分级出现的写法
EVIDENCE_TAGS = {
    "[S#] 官方事实": r"\[S\d",
    "[P#] 论文章节": r"\[P\d",
    "工程假设": r"工程假设",
    "参赛者自报": r"参赛者自报",
}

# 已经不在使用的旧编号体系（2026-08-30）。配图文件名是有意保留的例外，
# 因此只查正文里的「第 N 课 / 第N课」写法，且「原第 N 课」是允许的历史标注。
STALE_RE = re.compile(r"(?<!原)第\s?(0[2-9]|10)\s?课")

NB_WHITELIST = "test.ipynb"

# --------------------------------------------------------------------------
# 豁免：**每条都必须给理由**。不加理由的豁免就是放宽判定。
# --------------------------------------------------------------------------
EXEMPT: dict[tuple[str, str], str] = {
    ("L0-00", "DIAG"): "早于完成度契约；已发布飞书并被精读，正文冻结。",
    ("L0-00", "NB_DECL"): "90/91 号 notebook 是官方 Colab 逐字节固定副本，"
                          "映射表已声明不属于课程序列；本课无教学 notebook 是对的。",
    ("L0-00", "NB_BACKREF"): "同上（正文冻结）。",
    ("L0-01", "NB_BACKREF"): "正文已发布飞书并冻结，不允许改动；"
                             "缺口改在 notebook/README.md 侧补齐映射。",
}

# --------------------------------------------------------------------------
# 已归票的缺口：真实存在、但由某个 issue 跟踪。不许静默消失。
# --------------------------------------------------------------------------
KNOWN_GAPS: dict[tuple[str, str], str] = {
    ("__ALL__", "NB_DECL"): "#12",
    ("__ALL__", "NB_BACKREF"): "#12",
    ("__ALL__", "SLOTS"): "#12",
    ("L1-01", "SLOTS"): "#12",
}

# 尚未写的课：文件缺失是**预期状态**，归到写它的那一票，不算未跟踪失败。
for _num, _ticket in [("L1-02", "#3"), ("L2-01", "#4"), ("L2-02", "#5"),
                      ("L2-03", "#6"), ("L2-04", "#7"), ("L2-05", "#8"),
                      ("L2-06", "#9")]:
    KNOWN_GAPS[(_num, "FILE")] = _ticket

# 附录课（在 README §10 声明，不在 §3 的课程总表里）
EXTRA_COURSES = [
    ("L2-06", "appendix/L2-06-模型卡.md"),
]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def parse_course_table() -> list[dict]:
    """从 README §3 课程总表解析课号 → 文件路径。"""
    text = read(COURSE_INDEX)
    try:
        sec = text.split("## 3. 课程总表", 1)[1].split("\n## ", 1)[0]
    except IndexError:
        sys.exit("找不到 README 的「## 3. 课程总表」小节")

    courses = []
    for line in sec.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not COURSE_RE.match(cells[0]):
            continue
        num, ref = cells[0], cells[1]
        pending = "待写" in ref
        m = re.search(r"\]\(([^)]+)\)", ref) or re.search(r"`([^`]+\.md)`", ref)
        courses.append({
            "num": num,
            "path": m.group(1) if m else None,
            "pending": pending,
            "in_table": True,
        })

    have = {c["num"] for c in courses}
    for num, path in EXTRA_COURSES:
        if num not in have:
            courses.append({"num": num, "path": path, "pending": True,
                            "in_table": False})
    return courses


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
    slots = MODEL_SLOTS if num.startswith("L2") else CAUSAL_SLOTS
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

    # ---- 旧课号残留 ------------------------------------------------------
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

    courses = parse_course_table()
    nb_map = parse_notebook_map()
    results = [check_course(c, nb_map) for c in courses]
    links = check_links()
    nb_problems = check_notebook_index()

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

    rc = 2 if untracked else (1 if tracked or exempted else 0)

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
