# -*- coding: utf-8 -*-
"""Emit the L2-03 foundation-model-routes .drawio -- revision 1.

Two panels, all facts taken from either (a) the fixed official scGPT commit
cebd6fae65, read statically (no weights, no inference, no network), or
(b) synthetic NumPy experiments in notebook 08.  Nothing on this figure is an
instance-level measurement of any model.

(a) the interface comparison: how each of the three routes lets "which gene was
    perturbed" reach the model, and what the model outputs.  The point of the
    panel is the bottom row: scGPT carries target identity ONLY through the
    gene's own slot and its expression value, so a target that is zero in NTC
    arrives as (value = 0, flag = 1) -- identical for every such target.

(b) the mechanism that explains "foundation models lose to linear baselines":
    beta_frac = Var(beta) / (Var(beta) + mean_c Var(gamma)) bucketed per target.
    The right-hand curve is B1 / (B1 + perfect-Gamma) from notebook 08 cell 5 --
    the ratio falls from ~1.0 to ~0.15 as the background-specific component
    grows, i.e. the window where a high-capacity model can pay for itself is
    exactly the low-beta_frac end.

Layout rules from AGENTS.md "教程图片" 9/10: font sizes live only in the scale
block below and nothing is under 12 model px; adjacent vertical gaps >= 20 px;
captions sit >= 25 px clear of the frame they belong to; flat shapes carry
perimeter=rectanglePerimeter; the callout jumps stay inside their own panel.
"""
import sys

OUT = sys.argv[1]

PAL = {
    "attn":  ("#ffe6cc", "#d79b00"),
    "norm":  ("#f8cecc", "#b85450"),
    "ffn":   ("#fff2cc", "#d6b656"),
    "plain": ("#ffffff", "#000000"),
    "io":    ("#f5f5f5", "#666666"),
    "warn":  ("#f8cecc", "#b85450"),
    "good":  ("#d5e8d4", "#82b366"),
    "band":  ("#eef3fa", "#a9c3e0"),
}

# ---- typography scale: the ONLY place font sizes are written ----------------
F_MAIN = 20    # document title
F_SUB = 13     # document subtitle / legend
F_PANEL = 15   # (a) (b) panel titles
F_BOX = 14     # module boxes
F_BOXS = 13    # minor boxes / in-box detail lines
F_CAP = 12     # captions and notes

cells = []


def add(s):
    cells.append(s)


def vbox(cid, x, y, w, h, value, role="plain", font=F_BOX, bold=False,
         parent="1", rounded=1, align="center", valign="middle", dashed=0,
         container=False, fontcolor="#111111"):
    f, s = PAL[role]
    # perimeter=rectanglePerimeter is load bearing: the DEFAULT rect perimeter
    # is an octagon built from s=ceil(h/2), which degenerates on flat shapes
    # and makes fractional exitX/entryX snap to an end.
    st = (f"rounded={rounded};whiteSpace=wrap;html=1;perimeter=rectanglePerimeter;"
          f"fillColor={f};strokeColor={s};"
          f"fontFamily=Helvetica;fontSize={font};fontColor={fontcolor};"
          f"align={align};verticalAlign={valign};")
    if bold:
        st += "fontStyle=1;"
    if dashed:
        st += "dashed=1;"
    if container:
        st += "container=1;pointerEvents=0;"
    add(f'<mxCell id="{cid}" value="{value}" style="{st}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def vtext(cid, x, y, w, h, value, font=F_CAP, bold=False, align="left",
          color="#333333", parent="1", valign="middle"):
    st = (f"text;html=1;whiteSpace=wrap;align={align};verticalAlign={valign};"
          f"fontFamily=Helvetica;fontSize={font};fontColor={color};")
    if bold:
        st += "fontStyle=1;"
    add(f'<mxCell id="{cid}" value="{value}" style="{st}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def vrect(cid, x, y, w, h, fill="#000000", parent="1"):
    add(f'<mxCell id="{cid}" value="" style="rounded=0;html=1;'
        f'perimeter=rectanglePerimeter;fillColor={fill};'
        f'strokeColor=none;" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def band(cid, x, y, w, h, role="band"):
    """Panel background container; contents are re-parented in a post-pass."""
    f, s = PAL[role]
    add(f'<mxCell id="{cid}" value="" style="rounded=0;html=1;'
        f'perimeter=rectanglePerimeter;fillColor={f};strokeColor={s};'
        f'dashed=1;container=1;pointerEvents=0;" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def fedge(cid, sp, wps, tp, parent="1", color="#000000", dashed=0, label="",
          arrow=True):
    """Orthogonal/straight connector between two absolute points.

    `arrow=False` drops endArrow entirely.  Use it for anything that is a
    plotted rule or a data curve rather than a directed flow: endArrow=block with
    endSize=8 draws a ~16 px triangle that at this stroke width reads as a blob
    and covers whatever marker the line lands on.
    """
    pts = "".join(f'<mxPoint x="{p[0]}" y="{p[1]}"/>' for p in wps)
    st = "edgeStyle=none;rounded=0;html=1;"
    st += "endArrow=block;endSize=8;" if arrow else "endArrow=none;"
    st += f"strokeColor={color};strokeWidth=1;"
    if dashed:
        st += "dashed=1;"
    add(f'<mxCell id="{cid}" value="{label}" style="{st}" edge="1" parent="{parent}">'
        f'<mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{sp[0]}" y="{sp[1]}" as="sourcePoint"/>'
        f'<mxPoint x="{tp[0]}" y="{tp[1]}" as="targetPoint"/>'
        f'<Array as="points">{pts}</Array></mxGeometry></mxCell>')


W = 1820
Hc = 1560

WA = 880          # panel (a) width
XB = 20 + WA + 40  # 940
WB = W - XB - 20   # 860

# ----------------------------------------------------------------- header ----
vtext("t1", 20, 24, 1500, 32,
      "图 L2-03&#xa0;|&#xa0;三条基础模型路线：靶点如何进入模型，以及算力该往哪儿投",
      font=F_MAIN, bold=True, color="#1a1a1a")
vtext("t2", 20, 62, 1780, 24,
      "scGPT 结构取自官方源码 commit cebd6fae65 的静态核验（未下载权重、未运行推理、未联网）；"
      "(b) 的曲线来自 notebook 08 的合成数据实验，演示机制而非复现任何数据集结论。",
      font=F_CAP, color="#666666")

for i, (role, label) in enumerate([
        ("attn", "条件/扰动通路"),
        ("ffn", "输出与读出"),
        ("io", "输入形状"),
        ("good", "共享分量 β 主导"),
        ("warn", "背景特异 Γ 主导"),
        ("plain", "接口/对比项")]):
    f, s = PAL[role]
    xx = 24 + 200 * i
    add(f'<mxCell id="lg{i}" value="" style="rounded=0;html=1;'
        f'perimeter=rectanglePerimeter;fillColor={f};strokeColor={s};" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{xx}" y="94" width="24" height="14" as="geometry"/></mxCell>')
    vtext(f"lgt{i}", xx + 32, 91, 160, 20, label, font=F_CAP, color="#111111")

vrect("t3", 20, 120, 1780, 2, fill="#cccccc")

# ================================================================ PANEL (a) ==
band("pa", 20, 130, WA, 1400)
vtext("a_t", 40, 150, 840, 28,
      "（a）靶点身份怎样到达模型：三条路线的接口对照",
      font=F_PANEL, bold=True, color="#111111")
vtext("a_s", 40, 182, 840, 24,
      "同一个问题「敲的是哪个基因」，三条路线给了三种完全不同的入口。",
      font=F_CAP, color="#666666")

# ---- row 1: scGPT ----
vtext("a_r1", 40, 224, 200, 24, "scGPT", font=F_BOX, bold=True, color="#8a4b00")
vbox("a_r1a", 40, 254, 250, 78,
     "基因 slot&#xa;（序列中的位置）", role="io", font=F_BOXS)
vbox("a_r1b", 310, 254, 250, 78,
     "表达值&#xa;clamp(max=512)", role="io", font=F_BOXS)
vbox("a_r1c", 580, 254, 280, 78,
     "扰动标记&#xa;Embedding(3, d)", role="attn", font=F_BOXS)
fedge("a_r1e1", (290, 293), [], (310, 293))
fedge("a_r1e2", (560, 293), [], (580, 293))
vtext("a_r1n", 40, 350, 820, 44,
      "相加后进 Transformer。&lt;b&gt;注意：扰动标记只有 3 个取值，它只说「这个基因被敲了」，"
      "不说「被敲的是哪个基因」——靶点身份由 slot 与表达值联合携带。&lt;/b&gt;",
      font=F_CAP, color="#333333")

# ---- row 2: the zero-expression target case ----
vbox("a_r2", 40, 414, 820, 150,
     "&lt;b&gt;关键情形：靶点在该背景的 NTC 中表达为零&lt;/b&gt;&#xa;"
     "三个不同靶点 GENE_A / GENE_B / GENE_C，各自到达模型时都是"
     "&#xa;（表达值 = 0，扰动标记 = 1）——&lt;b&gt;模型看到的是同一个输入&lt;/b&gt;&#xa;"
     "去重后可区分组合数 = 1，而不是 3",
     role="warn", font=F_BOXS)
vtext("a_r2n", 40, 582, 820, 44,
      "这不是容量问题：加大模型或加数据都不会修好它。修法是给靶点一个独立编码"
      "（学靶点嵌入 / 用基因嵌入当靶点向量）。",
      font=F_CAP, color="#8a2b2b")

# ---- row 3: the three routes' interfaces ----
vtext("a_r3", 40, 648, 820, 24,
      "三条路线的接口与输出对照", font=F_BOX, bold=True, color="#111111")

vbox("a_t1h", 40, 682, 258, 46, "scGPT", role="ffn", font=F_BOX)
vbox("a_t2h", 310, 682, 258, 46, "scBaseCount", role="ffn", font=F_BOX)
vbox("a_t3h", 580, 682, 280, 46, "AIDO Cell", role="ffn", font=F_BOX)

vtext("a_t1a", 40, 738, 258, 150,
      "它是模型&#xa;扰动入口：逐基因 3 元标记&#xa;训练监督：&lt;b&gt;对照↔扰动配对&lt;/b&gt;&#xa;"
      "输出：log1p 单点估计&#xa;（pred = coeff·x + bias，无 softmax）",
      font=F_CAP, align="left")
vtext("a_t2a", 310, 738, 258, 150,
      "&lt;b&gt;它不是模型&lt;/b&gt;&#xa;是语料：2.3 亿细胞&#xa;21 物种 / 72 组织&#xa;"
      "扰动字段有，但&lt;b&gt;细胞级标注缺失&lt;/b&gt;&#xa;输出：h5ad 原始计数",
      font=F_CAP, align="left")
vtext("a_t3a", 580, 738, 280, 150,
      "平台 / 世界模型&#xa;把三类留出写进评测：&#xa;见背景未见靶 / 未见背景见靶 / &#xa;"
      "未见背景未见靶&#xa;输出：TPM 聚合谱",
      font=F_CAP, align="left")

vbox("a_r4", 40, 906, 820, 128,
     "&lt;b&gt;共同的阻塞点（与 L2-02 的 Stack 同源）&lt;/b&gt;&#xa;"
     "本赛给新背景的只有 NTC 与靶基因名字——&lt;b&gt;没有该靶点在该背景里的任何扰动真值&lt;/b&gt;。"
     "&#xa;任何「用同背景真实扰动细胞来校准」的做法（scGPT 的配对微调、"
     "Stack 的上下文示例、AIDO Cell 的 held-out 细胞系评测）都必须先回答：这些细胞从哪来。",
     role="warn", font=F_BOXS)

vtext("a_r5", 40, 1050, 820, 44,
      "三条路线都不进入首投主线（本机 8 GiB + 合同缺扰动真值）；"
      "但 AIDO Cell 的三类留出设计可以免费抄进本项目的内部验证协议。",
      font=F_CAP, color="#333333")

# ---- row: the "no total parameter count" card ----
vbox("a_r6", 40, 1114, 820, 168,
     "&lt;b&gt;scGPT 的规模该怎么引用&lt;/b&gt;&#xa;"
     "论文实现细节：嵌入 512、12 个堆叠块、8 个注意力头、前馈 512；"
     "与扰动教程实参一致。&#xa;"
     "结构本体手算 ≈ 2,079 万（不含基因嵌入）；基因嵌入 = 48,292 × 512 ≈ 2,473 万，"
     "&lt;b&gt;单列不并入总数&lt;/b&gt;。&#xa;"
     "所以引用规模时引用「12 层 / 512 维」，不要引用一个来源不明的总参数——"
     "总量由词表主导，而词表随数据版本变化。",
     role="io", font=F_BOXS)

vtext("a_r7", 40, 1300, 820, 44,
      "另有一条源码事实：预训练权重只加载 encoder / value_encoder / transformer_encoder "
      "三个前缀——&lt;b&gt;pert_encoder 不在其中，是随机初始化后从零学的&lt;/b&gt;。",
      font=F_CAP, color="#8a2b2b")
vtext("a_r8", 40, 1348, 820, 44,
      "推论：扰动能力 100% 来自下游那三套 Perturb-seq，0% 来自 3,300 万观察性细胞的预训练。"
      "而本赛缺的正是下游那一步。",
      font=F_CAP, color="#8a2b2b")

vtext("a_cap", 40, 1420, 820, 50,
      "* 三条路线的结构、行号与词表条目数均取自本地固定 commit 的静态核验；"
      "AIDO Cell 与 scBaseCount 的数字来自经机器转换的一手材料，等级低于源码核验。"
      "本图没有任何实测耗时或显存数字。",
      font=F_CAP, color="#777777")

# ================================================================ PANEL (b) ==
# Panel (b) rows are shifted +2 px relative to panel (a) so that the two panels'
# title baselines and their first content blocks land on the same horizontal
# rules; the title block itself keeps panel (a)'s y so the two headings read as
# one band.
band("pb", XB, 130, WB, 1400)
vtext("b_t", XB + 20, 150, WB - 40, 28,
      "（b）算力该往哪儿投：beta_frac 分档与机会窗口",
      font=F_PANEL, bold=True, color="#111111")
vtext("b_s", XB + 20, 182, WB - 40, 24,
      "分解口径转写自 perturbation-decomposition 的 anova.py:3 / 68-72（该仓库无许可证，仅本地阅读）。",
      font=F_CAP, color="#666666")

vbox("b_eq", XB + 20, 224, WB - 40, 74,
     "Δ(c, t, g) = μ + α(c) + &lt;b&gt;β(t, g)&lt;/b&gt; + &lt;b&gt;Γ(c, t, g)&lt;/b&gt; + ε"
     "&#xa;beta_frac(t) = Var(β_t) / [ Var(β_t) + mean_c Var(Γ_c,t) ]",
     role="ffn", font=F_BOXS)
vtext("b_eqn", XB + 20, 314, WB - 40, 48,
      "β 是共享分量（跨背景可迁移），Γ 是背景特异分量（交互）。"
      "B1 全局 target delta 只建模 β——所以 beta_frac 高的靶点，B1 本来就够用。",
      font=F_CAP, color="#333333")

# ---- bucket chart: 40 synthetic targets bucketed by beta_frac ----
BCH_X = XB + 30
BCH_Y = 378
BCH_W = WB - 60
BCH_H = 250
vbox("b_chb", BCH_X, BCH_Y, BCH_W, BCH_H, "", role="plain", rounded=0)

vtext("b_cht", BCH_X + 10, BCH_Y + 8, BCH_W - 20, 22,
      "40 个合成靶点的 beta_frac 分布（notebook 08 单元 4）",
      font=F_BOXS, bold=True, color="#111111")

# stacked horizontal bars for the three buckets, drawn as proportional rects.
# Labels are kept to two short lines each: the segment widths are proportional
# (22 / 9 / 9 of 40), so the 9-target segments are only ~194 px wide and a
# longer label wraps to a third line that the 62 px box then clips.
_BUCKETS = [("β 主导：B1 就够", 22, "good"),
            ("可投，要过地板", 9, "ffn"),
            ("Γ 主导：最值得投", 9, "warn")]
_TOT = sum(b[1] for b in _BUCKETS)
_bx = BCH_X + 16
_by = BCH_Y + 44
# Each bucket is ONE shape: the coloured rect with its label inside, rather than
# a rect plus a text drawn over it.  Drawing them as two overlapping siblings is
# what makes validate.py report W-OVERLAP, and re-parenting the text under the
# rect is what made the label vanish in the render -- a vertex with container=1
# only renders children whose geometry it fully contains AND that carry their own
# container offset, so a plain nested mxCell silently disappears.  A label inside
# the box's own value string has neither problem and needs no nesting at all.
for i, (lab, n, role) in enumerate(_BUCKETS):
    seg_w = max(60, int((BCH_W - 32) * n / _TOT))
    vbox(f"b_bk{i}", _bx, _by, seg_w, 62,
         f"&lt;div style='text-align:left'&gt;{lab}&#xa;&lt;b&gt;{n} 个靶点&lt;/b&gt;&lt;/div&gt;",
         role=role, rounded=0, align="left", font=F_CAP)
    _bx += seg_w
_by += 62 + 22

vtext("b_bkn", BCH_X + 16, _by, BCH_W - 32, 40,
      "阈值 0.70 / 0.50 不是物理常数：要在公开真值面板上同时记录 beta_frac 与 B1 的实测分数，"
      "按分数曲线找拐点。",
      font=F_CAP, color="#666666")

# ---- opportunity window curve ----
C_X = XB + 30
C_Y = 712
C_W = WB - 60
C_H = 380
vbox("b_cvb", C_X, C_Y, C_W, C_H, "", role="plain", rounded=0)
vtext("b_cvt", C_X + 10, C_Y + 8, C_W - 20, 22,
      "机会窗口：B1 分数 / 「完美知道 Γ」的上界（notebook 08 单元 5）",
      font=F_BOXS, bold=True, color="#111111")

# axes.  The left gutter is 84 px: the tick labels ("1.00", "0.00") need ~44 px
# and the rotated axis caption another ~26 px of column, and a narrower gutter
# pushes the tick text into the plotted data.  The x-axis caption lives BELOW
# the "0.00" tick line, outside the axes rect, so it cannot collide with the
# corner tick.
_AX = C_X + 84
_AY = C_Y + C_H - 62
_AW = C_W - 130
_AH = C_H - 150
_PY_TOP_SAFE = _AY - _AH + 24
fedge("b_ax1", (_AX, _AY), [], (_AX, _AY - _AH), color="#333333", arrow=False)
fedge("b_ax2", (_AX, _AY), [], (_AX + _AW, _AY), color="#333333", arrow=False)
vtext("b_ax1l", C_X + 34, _AY - _AH - 10, 46, 20, "1.00", font=F_CAP, align="right")
vtext("b_ax2l", C_X + 34, _AY - 10, 46, 20, "0.00", font=F_CAP, align="right")
vtext("b_axl", C_X + 8, _AY - _AH / 2 - 40, 22, 80,
      "B1 /&#xa;上界", font=F_CAP, align="center", color="#555555")
vtext("b_axxl", C_X + 84, _AY + 8, _AW, 22,
      "背景特异分量 Γ 的强度（对数刻度，0.05 → 3.20）",
      font=F_CAP, align="left", color="#555555")

# the measured points from nb08 cell 5
_PTS = [(0.05, 0.9985), (0.10, 0.9940), (0.20, 0.9764), (0.40, 0.9126),
        (0.80, 0.7305), (1.60, 0.4152), (3.20, 0.1496)]
_LO = 0.05
_HI = 3.20
import math


def _px(v):
    t = (math.log(v) - math.log(_LO)) / (math.log(_HI) - math.log(_LO))
    return int(_AX + 6 + t * (_AW - 12))


def _py(v):
    return int(_AY - 6 - v * (_AH - 12))


_pts_svg = []
for xv, yv in _PTS:
    px, py = _px(xv), _py(yv)
    _pts_svg.append((px, py))

for i, (px, py) in enumerate(_pts_svg):
    add(f'<mxCell id="b_pt{i}" value="" style="ellipse;html=1;'
        f'fillColor=#c0392b;strokeColor=#8a2b2b;" vertex="1" parent="1">'
        f'<mxGeometry x="{px - 5}" y="{py - 5}" width="10" height="10" as="geometry"/></mxCell>')
    if i:
        ppx, ppy = _pts_svg[i - 1]
        fedge(f"b_sg{i}", (ppx, ppy), [], (px, py), color="#c0392b", arrow=False)

# Value labels go in the empty lower-right wedge, not next to their own point:
# the measured curve is monotone decreasing and sits in the upper-left, so the
# area below/right of it is free.  Each label is nudged down-right by 30 px from
# its own vertex so the text never sits on the marker, and the column is capped
# at _ZONE_TOP: everything below that y is reserved for the two zone notes, so
# the two groups occupy disjoint horizontal bands and cannot collide.
_ZONE_TOP = _AY - 78
for i, (xv, yv) in enumerate(_PTS):
    if i % 2 == 0:
        ly = min(max(_AY - 40 - 20 * (i // 2), _PY_TOP_SAFE), _ZONE_TOP - 22)
        vtext(f"b_pl{i}", _px(xv) - 42, ly, 76, 20,
              f"{yv:.3f} @ {xv:.2f}", font=F_CAP, align="center", color="#8a2b2b")

# Zone notes.  b_z1 annotates the flat left end (the curve hugs y = 1.0) and
# b_z2 the falling right end.  Both sit in the band below _ZONE_TOP, which the
# value labels above no longer reach.  b_z2 is pulled left of the last vertex so
# its right-aligned text cannot run under the "0.150 @ 3.20" label, and both
# stop short of the axes rect so nothing is clipped.
vtext("b_z1", _AX + 12, _ZONE_TOP, 290, 44,
      "Γ 很弱 → B1 ≈ 上界&#xa;（β 就是全部）", font=F_CAP, color="#2f6b2f")
vtext("b_z2", _px(1.6) - 216, _ZONE_TOP, 200, 44,
      "Γ 变强 →&#xa;B1 反而下降", font=F_CAP, align="right", color="#8a2b2b")

vbox("b_concl", XB + 30, 1146, WB - 60, 220,
     "&lt;b&gt;这张图就是「基础模型打不过线性基线」的机制&lt;/b&gt;&#xa;&#xa;"
     "B1 已经吃掉了共享分量的大头。一条高容量路线要证明自己不是白花的钱，"
     "就必须证明它的额外收益来自 Γ——而 Γ 恰恰是最稀疏、最容易被噪声淹没的那一项。&#xa;"
     "本赛的用法：先剔除在训练数据上&lt;b&gt;零覆盖&lt;/b&gt;的靶点（只能走 B0），"
     "再把剩余靶点按 beta_frac 分档，把算力集中在中低档。&#xa;"
     "判据仍然是 L1-02 的噪声地板——改动前后分数差不超过地板，就不算改进。",
     role="good", font=F_BOXS)

vtext("b_cap", XB + 30, 1420, WB - 60, 50,
      "* 本面板的分布与曲线全部来自合成数据，演示的是机制，不是任何真实数据集或本赛 300 个靶点的统计。"
      "真实分档必须先在一份有真值的公开面板上跑一次四分量分解。",
      font=F_CAP, color="#777777")

# ============================================================ re-parenting ===
import re as _re

_PANELS = [("pa", 20, 130, WA, 1400), ("pb", XB, 130, WB, 1400)]
_panel_ids = {p[0] for p in _PANELS}

_geo_re = _re.compile(r'<mxGeometry x="(-?[\d.]+)" y="(-?[\d.]+)" '
                      r'width="([\d.]+)" height="([\d.]+)" as="geometry"/>')
# Parent is captured, not pinned to "1": the re-parenting pass runs twice and
# the second pass has to see the panel-relative cells produced by the first.
_cell_re = _re.compile(r'<mxCell id="([^"]+)" value="([^"]*)" style="([^"]*)" '
                       r'vertex="1" parent="([^"]+)">(<mxGeometry[^>]*/>)</mxCell>')


def _rect(c):
    m = _cell_re.match(c)
    if not m:
        return None
    g = _geo_re.search(m.group(5))
    if not g:
        return None
    return (m.group(1), m.group(2), m.group(3), m.group(4),
            float(g.group(1)), float(g.group(2)),
            float(g.group(3)), float(g.group(4)))


def _abs_pos(cells):
    geo = {}
    par = {}
    for c in cells:
        r = _rect(c)
        if not r:
            continue
        geo[r[0]] = (r[4], r[5], r[6], r[7])
        par[r[0]] = r[3]
    absg = {}
    for cid, (x, y, w, h) in geo.items():
        cur = par[cid]
        chain = []
        while cur != "1":
            if cur not in geo:
                break
            chain.append(cur)
            cur = par.get(cur, "1")
        for p in chain:
            x += geo[p][0]
            y += geo[p][1]
        absg[cid] = (x, y, w, h)
    return absg


def _reparent(cells, hosts):
    """Nest every vertex fully inside a host box into that host.

    `hosts` is a list of (id, x, y, w, h) in ABSOLUTE coordinates, ordered most
    specific first: panel backdrops own cards, cards own their label text. Two
    levels are needed because a card backing and the text drawn on it are
    otherwise compared as siblings and reported as an overlap.
    """
    absg = _abs_pos(cells)
    moved = []
    for c in cells:
        r = _rect(c)
        if not r:
            moved.append(c)
            continue
        cid, value, style, par, x, y, w, h = r
        if cid in {hh[0] for hh in hosts}:
            moved.append(c)
            continue
        ax, ay, _, _ = absg[cid]
        for hid, hx, hy, hw, hh in hosts:
            if ax >= hx and ay >= hy and ax + w <= hx + hw and ay + h <= hy + hh:
                geo = (f'<mxGeometry x="{ax - hx:g}" y="{ay - hy:g}" '
                       f'width="{w:g}" height="{h:g}" as="geometry"/>')
                moved.append(f'<mxCell id="{cid}" value="{value}" '
                             f'style="{style}" vertex="1" parent="{hid}">{geo}</mxCell>')
                break
        else:
            moved.append(c)
    return moved


# level 1: panels own everything drawn on them
cells = _reparent(cells, [(pid, px, py, pw, ph)
                          for pid, px, py, pw, ph in _PANELS])

# level 2: the card backings own the label text sitting on top of them.
#
# b_chb (bucket chart frame) and b_cvb (opportunity-window axes frame) MUST be
# here.  Both are plain rectangles whose entire content -- the title, the bucket
# bars, the axis lines, the measured points, the point labels and the zone notes
# -- is drawn on top of them.  validate.py compares sibling vertices, so without
# this level every one of those children is reported as overlapping the frame it
# sits on; that was 37 of the 37 warnings.  The host rectangles themselves are
# skipped by _reparent, so nesting is one level deep only and the children stay
# siblings of each other (their real geometry still gets checked, which is what
# we want).
_CARD_IDS = ["a_r2", "a_r4", "a_r6", "b_eq", "b_concl", "b_chb", "b_cvb"]
_panel_origin = {p[0]: (p[1], p[2]) for p in _PANELS}
_card_hosts = []
for c in cells:
    m = _cell_re.match(c)
    if not m:
        continue
    cid, par = m.group(1), m.group(4)
    if cid not in _CARD_IDS or par not in _panel_origin:
        continue
    g = _geo_re.search(m.group(5))
    if not g:
        continue
    ox, oy = _panel_origin[par]
    _card_hosts.append((cid, float(g.group(1)) + ox, float(g.group(2)) + oy,
                        float(g.group(3)), float(g.group(4))))
cells = _reparent(cells, _card_hosts)

# ------------------------------------------------------------------- emit ----
head = ('<mxfile host="app.diagrams.net" modified="2026-09-18T00:00:00.000Z" '
        'agent="vc2026-lessons" version="24.0.0" type="device">'
        '<diagram id="L2-03-foundation-routes" name="L2-03 foundation model routes">'
        f'<mxGraphModel dx="1422" dy="798" grid="0" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{W}" pageHeight="{Hc}" math="0" shadow="0">'
        '<root><mxCell id="0"/><mxCell id="1" parent="0"/>')
tail = "</root></mxGraphModel></diagram></mxfile>"

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(head + "".join(cells) + tail)
print("wrote %s with %d cells, canvas %dx%d" % (OUT, len(cells), W, Hc))
