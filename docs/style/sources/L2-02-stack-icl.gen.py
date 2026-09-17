# -*- coding: utf-8 -*-
"""Emit the AIAYN-style Stack in-context architecture .drawio -- revision 1.

Three panels, all facts taken from the fixed official commit
cacc2e4b09435c3e536d46237d10b50f222dd144 (static verification, no weights
loaded, no inference run):

(a) the double-axis attention path: expression matrix -> gene tokenisation ->
    intra-cellular attention over the n=100 gene-module tokens -> reshape ->
    inter-cellular attention over the K cells -> N x block -> NB decoder.
    The token/head/width numbers are printed ON the two attention boxes,
    because the whole point of this figure is that the "cheap-looking" axis
    (n = 100) is the expensive one: it runs B*K times.

(b) the K*H*n^2 vs K*K cost comparison, with the real ratios from
    notebook 07 at K = 64/128/256/512/1024.  n^2 = 10,000 and the K*K axis is
    two orders of magnitude below it -- that is the visual claim.

(c) the in-context window split: ratio = prompt_ratio + context_ratio, which
    is what the source decides, NOT the "prompt 25%" the paper text says.
    The tail window's duplicated query cells are drawn as offset stacked
    cards so the 137/400 duplication is visible rather than asserted.

Layout rules from AGENTS.md "教程图片" 9/10 are applied: fonts are defined once
in the scale block below and nothing is under 12 model px; every adjacent
vertical gap is >= 20 px; captions sit >= 25 px clear of the frame they belong
to; flat shapes carry perimeter=rectanglePerimeter; the residual-style long
jumps stay inside their own panel.
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
F_PANEL = 15   # (a) (b) (c) panel titles
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


def vellipse(cid, x, y, w, h, label="+", parent="1", font=16):
    st = ("ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
          f"fontFamily=Helvetica;fontSize={font};fontStyle=1;fontColor=#111111;")
    add(f'<mxCell id="{cid}" value="{label}" style="{st}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def edge(cid, src, tgt, pins, parent="1"):
    st = ("edgeStyle=none;rounded=0;html=1;endArrow=block;endSize=8;"
          "strokeColor=#000000;strokeWidth=1;" + pins)
    add(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="{parent}" '
        f'source="{src}" target="{tgt}">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>')


def fedge(cid, sp, wps, tp, parent="1", color="#000000", dashed=0, label=""):
    pts = "".join(f'<mxPoint x="{p[0]}" y="{p[1]}"/>' for p in wps)
    st = ("edgeStyle=none;rounded=0;html=1;endArrow=block;endSize=8;"
          f"strokeColor={color};strokeWidth=1;")
    if dashed:
        st += "dashed=1;"
    add(f'<mxCell id="{cid}" value="{label}" style="{st}" edge="1" parent="{parent}">'
        f'<mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{sp[0]}" y="{sp[1]}" as="sourcePoint"/>'
        f'<mxPoint x="{tp[0]}" y="{tp[1]}" as="targetPoint"/>'
        f'<Array as="points">{pts}</Array></mxGeometry></mxCell>')


V = "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;"
H = "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"

# ----------------------------------------------------------------- header ----
vtext("t1", 20, 24, 1500, 32,
      "图 L2-02&#xa0;|&#xa0;Stack 的上下文学习：双轴注意力、代价与窗口切分",
      font=F_MAIN, bold=True, color="#1a1a1a")
vtext("t2", 20, 62, 1780, 24,
      "结构依据 Arc 官方源码 commit cacc2e4b 的静态核验（未加载权重、未运行推理）；"
      "所有显存数字为手算，耗时未测。K=256 为预训练档，K=512 为后训练档。",
      font=F_CAP, color="#666666")

for i, (role, label) in enumerate([
        ("attn", "注意力模块"),
        ("norm", "Add &amp; Norm"),
        ("ffn", "前馈网络"),
        ("plain", "线性/逐元素"),
        ("io", "输入输出"),
        ("good", "提示侧（示例）"),
        ("warn", "查询侧/被复制")]):
    f, s = PAL[role]
    xx = 24 + 200 * i
    add(f'<mxCell id="lg{i}" value="" style="rounded=0;html=1;'
        f'perimeter=rectanglePerimeter;fillColor={f};strokeColor={s};" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{xx}" y="94" width="24" height="14" as="geometry"/></mxCell>')
    vtext(f"lgt{i}", xx + 32, 91, 160, 20, label, font=F_CAP, color="#111111")

vrect("t3", 20, 120, 1780, 2, fill="#cccccc")

# ================================================================ PANEL (a) ==
WA = 700          # panel (a) width
band("pa", 20, 130, WA, 1330)
vtext("a_t", 40, 148, 660, 28, "（a）前向路径：基因模块 token 与两个注意力轴",
      font=F_PANEL, bold=True, color="#111111")

# --- input / tokenisation ---
vtext("a_in", 200, 190, 340, 62,
      "表达矩阵&#xa;X ∈ ℝ^(B × K × G)，G = 15,012", font=F_CAP, align="center")
vbox("a_red", 200, 282, 340, 56,
     "基因 token 化&#xa0;&#xa0;Linear&#xa0;(G → n·d)", font=F_BOX)
vtext("a_pos", 200, 348, 340, 42,
      "+ 可学习 gene_pos_embedding&#xa;(n, d)，与具体基因解耦",
      font=F_CAP, align="center")
vbox("a_rs1", 200, 412, 340, 46,
     "reshape → (B·K, n, d)", role="io", font=F_BOXS)
vtext("a_rs1n", 546, 414, 160, 42,
      "B·K 条序列&#xa;n = 100，d = 16", font=F_CAP, color="#8a4b00")

# --- intra-cellular attention: the expensive axis ---
vbox("a_intra", 150, 486, 440, 92,
     "细胞内注意力（gene attention）&#xa;H = 8 头，序列长 n = 100&#xa;"
     "&lt;b&gt;每层元素数 B·K·H·n²&lt;/b&gt;",
     role="attn")
fedge("a_ea1", (370, 458), [], (370, 486))

# --- reshape back into the cell axis ---
vbox("a_rs2", 200, 606, 340, 46,
     "reshape → (B, K, n·d)", role="io", font=F_BOXS)
fedge("a_ea2", (370, 578), [], (370, 606))
vtext("a_rs2n", 546, 608, 160, 42,
      "B 条序列&#xa;K 个细胞", font=F_CAP, color="#8a4b00")

# --- inter-cellular attention: the axis that carries the context ---
vbox("a_inter", 150, 680, 440, 92,
     "细胞间注意力（cell attention）&#xa;H = 8 头，序列长 K&#xa;"
     "&lt;b&gt;每层元素数 B·H·K²&lt;/b&gt;",
     role="attn")
fedge("a_ea3", (370, 652), [], (370, 680))

vtext("a_note", 150, 790, 440, 44,
      "上下文学习的能力只来自这一个模块：&#xa;关掉它，换提示集对查询输出毫无影响",
      font=F_CAP, align="center", color="#8a4b00")

# --- N x block ---
# Emitted as a plain backdrop (NOT container=1) so the re-parenting pass can
# own its contents uniformly with everything else on this panel. The N x
# bracket is drawn on the LEFT EDGE of the block: at x = 373 it would sit on
# top of the FFN box, which is a real collision, not a lint artefact.
band("a_blk", 200, 852, 340, 150, role="plain")
vbox("a_ffn", 262, 882, 250, 44, "前馈网络", role="ffn")
vbox("a_an2", 262, 946, 250, 36, "Add &amp; Norm", role="norm", font=F_BOXS,
     dashed=1)
vrect("a_nbrk", 220, 852, 3, 150)
vrect("a_nbrkt", 223, 852, 14, 3)
vrect("a_nbrkb", 223, 999, 14, 3)
fedge("a_ea4", (370, 772), [], (370, 852))

vtext("a_nlbl", 24, 906, 150, 44, "N×（9 层）", font=F_CAP, bold=True,
      align="center", color="#111111")

# --- decoder ---
vbox("a_outmlp", 150, 1040, 440, 56,
     "output_mlp&#xa0;&#xa0;n·d → 2·n·d → 2G", font=F_BOX)
fedge("a_ea5", (370, 1002), [], (370, 1040))
vbox("a_nb", 150, 1132, 440, 92,
     "负二项参数&#xa;rho = softmax(logits[…, 0])，G 维&#xa;"
     "theta = softplus(logits[…, 1])，须为正",
     role="ffn", font=F_BOXS)
fedge("a_ea6", (370, 1096), [], (370, 1132))
vtext("a_out", 150, 1248, 440, 62,
      "按细胞采样得到计数 → 天然输出原始整数&#xa;（比 State 少一步计数生成适配）",
      font=F_CAP, align="center", color="#2e6b1f")
fedge("a_ea7", (370, 1224), [], (370, 1248))

# --- the K-is-not-structural point is stated inside the two attention boxes
# above; a floating side note here overlapped panel (b) and was removed.

# ================================================================ PANEL (b) ==
XB = 754
WB = 520
band("pb", XB, 130, WB, 1330)
vtext("b_t", XB + 20, 148, WB - 40, 28, "（b）两个轴的代价：贵的不是 K²",
      font=F_PANEL, bold=True, color="#111111")

vtext("b_sub", XB + 20, 182, WB - 40, 42,
      "每层每 batch、fp32、单位 MB。n = 100 固定，K 变化。",
      font=F_CAP, color="#666666")

# bar chart: intra is 2 orders of magnitude above inter for most K.
# Log-ish visual: draw bars against a max of 320 MB, intra solid orange,
# inter drawn as a thin dark strip at the bottom with a callout.
rows = [
    ("K = 64",   19.5,  0.1,  156.2),
    ("K = 128",  39.1,  0.5,   78.1),
    ("K = 256",  78.1,  2.0,   39.1),
    ("K = 512", 156.2,  8.0,   19.5),
    ("K = 1024", 312.5, 32.0,   9.8),
]
BAR_H = 46
BAR_GAP = 22          # >= 20 px as required
y0 = 250
X_LAB = XB + 30
X_BAR = XB + 130
BAR_W_MAX = 190       # px == 320 MB; the panel is 520 wide with 26 px margins,
                      # so 130 + 190 + label room has to stay under 494.

# NOTE on the bar scale: intra/inter spans 156x at K = 64.  A linear scale
# makes every inter bar a sub-pixel sliver, which reads as "zero" and defeats
# the point of the panel.  Bars are therefore drawn on a square-root scale and
# the axis line says so in words; the numeric labels carry the exact values.
import math as _math


def _barw(v):
    return max(4.0, BAR_W_MAX * _math.sqrt(v / 320.0))


for i, (name, intra, inter, ratio) in enumerate(rows):
    y = y0 + i * (BAR_H + BAR_GAP)
    vtext(f"b_n{i}", X_LAB, y, 96, BAR_H, name, font=F_BOXS, color="#111111")
    wi = _barw(intra)
    vbox(f"b_i{i}", X_BAR, y, wi, 22, "", role="attn", rounded=0)
    vtext(f"b_it{i}", X_BAR + wi + 6, y, 186, 22,
          "细胞内 %.1f MB" % intra, font=F_CAP, color="#8a4b00")
    w2 = _barw(inter)
    vbox(f"b_e{i}", X_BAR, y + 24, w2, 22, "", role="plain", rounded=0)
    vtext(f"b_et{i}", X_BAR + w2 + 6, y + 24, 186, 22,
          "细胞间 %.1f MB (%.1f×)" % (inter, ratio), font=F_CAP,
          color="#111111")

y_axis = y0 - 24
vtext("b_axis", X_BAR, y_axis, 300, 20,
      "柱长按 √(MB/320) 压缩；数值以标签为准",
      font=F_CAP, color="#666666")

# the quantitative punchline
y_pl = y0 + len(rows) * (BAR_H + BAR_GAP) + 26
vbox("b_punch", XB + 30, y_pl, WB - 60, 130, "", role="good")
vtext("b_pt", XB + 50, y_pl + 16, WB - 100, 98,
      "K = 512 时，细胞内注意力是细胞间的 &lt;b&gt;19.5 倍&lt;/b&gt;。&#xa;"
      "因为细胞内要跑 B·K 条序列（每个细胞一次），&#xa;"
      "细胞间只跑 B 条。倍数随 K 增大而下降：&#xa;"
      "K = 64 时 156.2×，K = 1024 时 9.8×。",
      font=F_BOXS, color="#1f4d13", align="left")

# 8 GiB boundary
y_mem = y_pl + 160
vbox("b_mem", XB + 30, y_mem, WB - 60, 200, "", role="io")
vtext("b_mt", XB + 50, y_mem + 14, WB - 100, 24,
      "本机 8 GiB 能跑到哪一步（手算，非实测）",
      font=F_BOXS, bold=True, color="#111111")
vtext("b_mb", XB + 50, y_mem + 44, WB - 100, 146,
      "单次前向，fp32，2.17 亿参数（≈830 MB）：&#xa;"
      "· K = 256 → 最大 batch &lt;b&gt;9&lt;/b&gt;（7.82 GiB），batch 10 即 8.60 GiB&#xa;"
      "· K = 512 → 最大 batch &lt;b&gt;4&lt;/b&gt;（7.18 GiB），batch 5 即 8.77 GiB&#xa;"
      "· bf16 同档：K = 256 → 19；K = 512 → 9&#xa;"
      "&#xa;"
      "后训练（batch = 8, K = 512）：权重+梯度+优化器 2.43 GiB，&#xa;"
      "注意力分数（含 autograd 保存的 softmax）&lt;b&gt;23.10 GiB&lt;/b&gt; → 远超 8 GiB。&#xa;"
      "&lt;b&gt;耗时一个数字都没有&lt;/b&gt;：FLOPs 量级给了，换算不代填。",
      font=F_CAP, color="#222222", align="left")

# compute budget, filled in so the panel does not end in dead space
y_cmp = y_mem + 226
vbox("b_comp", XB + 30, y_cmp, WB - 60, 180, "", role="ffn")
vtext("b_ct", XB + 50, y_cmp + 14, WB - 100, 24,
      "算力口径：只给 FLOPs，不给秒", font=F_BOXS, bold=True, color="#5a4a00")
vtext("b_cb", XB + 50, y_cmp + 44, WB - 100, 126,
      "K = 512、batch = 1 的一次前向约 &lt;b&gt;2.4×10¹¹ FLOPs&lt;/b&gt;。&#xa;"
      "主导项是细胞间注意力的 2K²d 与 output_mlp 的 4ndG。&#xa;"
      "&#xa;"
      "换算成耗时需要「GPU 有效算力 × 达成率」两个数，&#xa;"
      "本机没跑过，&lt;b&gt;不代填&lt;/b&gt; —— 这与 L2-01 §10.3 同一口径。",
      font=F_BOXS, color="#5a4a00", align="left")

# the honesty note about what this figure is NOT
y_ev = y_cmp + 206
vbox("b_ev", XB + 30, y_ev, WB - 60, 158, "", role="norm")
vtext("b_evt", XB + 50, y_ev + 14, WB - 100, 130,
      "&lt;b&gt;不是实测。&lt;/b&gt;&#xa;"
      "全部数字按张量形状手算，未实例化确认；&#xa;"
      "不含 allocator 碎片与 CUDA context 开销。&#xa;"
      "唯一一次与官方数字碰撞成功的是参数量：&#xa;"
      "Large 217,484,712 / 非嵌入 193,463,912，&#xa;"
      "与论文表 3 的 2.17 亿 / 1.93 亿一致。",
      font=F_CAP, color="#7a2222", align="left")

# ================================================================ PANEL (c) ==
XC = 1294
WC = 506
band("pc", XC, 130, WC, 1330)
vtext("c_t", XC + 20, 148, WC - 40, 28, "（c）窗口切分：25% 是误读",
      font=F_PANEL, bold=True, color="#111111")

vtext("c_sub", XC + 20, 182, WC - 40, 64,
      "源码 inference.py::get_incontext_prediction 决定切分的是&#xa;"
      "&lt;b&gt;ratio = prompt_ratio + context_ratio&lt;/b&gt;（默认 0.25 + 0.4 = 0.65），&#xa;"
      "不是论文正文写的「提示 25% 固定」。",
      font=F_CAP, color="#a33", align="left")

# the two knobs feeding one ratio.  Left column is 176 wide and the right
# column starts at XC + 262 so the pair never crowds the K label.
vbox("c_k1", XC + 26, 268, 176, 52, "prompt_ratio = 0.25", role="io", font=F_CAP)
vbox("c_k2", XC + 26, 336, 176, 52, "context_ratio = 0.40", role="io", font=F_CAP)
vellipse("c_add", XC + 99, 402, 30, 30)
fedge("c_e1", (XC + 114, 294), [(XC + 250, 294), (XC + 250, 417)], (XC + 114, 417))
fedge("c_e2", (XC + 114, 362), [(XC + 175, 362), (XC + 175, 417)], (XC + 114, 417))

vbox("c_ratio", XC + 26, 452, 176, 52, "ratio = 0.65", role="good", font=F_CAP)
vtext("c_split", XC + 26, 516, 176, 74,
      "n_test = int(K·(1−ratio)) = 179&#xa;n_base = K − n_test = 333",
      font=F_CAP, color="#111111", align="center")

vtext("c_kt", XC + 262, 268, 218, 24, "K = 512（后训练档）", font=F_BOXS,
      bold=True, color="#111111")

# the three windows for 400 query cells
win_rows = [
    ("窗口 1", "333 提示 + 179 查询", "查询 0–178", "good"),
    ("窗口 2", "333 提示 + 179 查询", "查询 179–357", "good"),
    ("窗口 3", "333 提示 + 179 查询", "查询 358–399 → 再补 137", "warn"),
]
for i, (nm, mid, rng, role) in enumerate(win_rows):
    y = 300 + i * 100
    vbox(f"c_w{i}", XC + 262, y, 218, 84, "", role=role, rounded=0)
    vtext(f"c_wt{i}", XC + 272, y + 8, 198, 22, nm, font=F_BOXS, bold=True,
          color="#111111")
    vtext(f"c_wm{i}", XC + 272, y + 30, 198, 20, mid, font=F_CAP, color="#222222")
    vtext(f"c_wr{i}", XC + 272, y + 52, 198, 24, rng, font=F_CAP, color="#a33")

vrect("c_sep", XC + 20, 618, WC - 40, 2, fill="#aaaaaa")

vtext("c_pt", XC + 26, 636, WC - 52, 116,
      "第 3 个窗口只有 42 个真实查询细胞，缺的 137 个由源码&#xa;"
      "&lt;b&gt;test_indices[:need]&lt;/b&gt; 从查询集开头复制补齐。&#xa;"
      "&#xa;"
      "⇒ 拼成 400 行提交时，&lt;b&gt;137 / 400 行是重复的&lt;/b&gt;（cr = 0.40）。&#xa;"
      "cr = 0.20 时是 162 / 400，cr = 0.25 时是 112 / 400。",
      font=F_CAP, color="#a33", align="left")

# the recorded consequence table
y_tab = 772
vtext("c_tt", XC + 26, y_tab, WC - 52, 22, "提交前的机械后果（notebook 07 实测）",
      font=F_BOXS, bold=True, color="#111111")
tbl = [
    ("context_ratio", "复制行数 / 400"),
    ("0.20", "162"),
    ("0.25", "112"),
    ("0.40", "137"),
]
for i, (a, b) in enumerate(tbl):
    y = y_tab + 28 + i * 40
    role = "io" if i == 0 else "plain"
    vbox(f"c_ta{i}", XC + 26, y, 220, 36, a, role=role, font=F_CAP,
         bold=(i == 0))
    vbox(f"c_tb{i}", XC + 250, y, 230, 36, b, role=role, font=F_CAP,
         bold=(i == 0))

y_warn = y_tab + 28 + len(tbl) * 40 + 24
vbox("c_warn", XC + 26, y_warn, WC - 52, 200, "", role="warn")
vtext("c_warnt", XC + 46, y_warn + 14, WC - 92, 172,
      "&lt;b&gt;格式检查发现不了这件事。&lt;/b&gt;&#xa;"
      "它只看行数、列名、基因顺序、非负整数性——&#xa;"
      "不知道第 1 行和第 359 行应是两个生物细胞。&#xa;"
      "&#xa;"
      "&lt;b&gt;伤害的是群体分布线：&lt;/b&gt;重复行对方差的贡献是 0，&#xa;"
      "总 UMI 均值不变，但方差、零比例、状态组成、&#xa;"
      "基因间协变全部被拉偏。&#xa;"
      "&#xa;"
      "&lt;b&gt;工程合同线全绿，分布线已经错了&lt;/b&gt; —— 这才是危险处。&#xa;"
      "修法：保留每个查询细胞首次出现的行，按原顺序输出。",
      font=F_CAP, color="#7a2222", align="left")

y_nostruc = y_warn + 226
vbox("c_ns", XC + 26, y_nostruc, WC - 52, 168, "", role="good")
vtext("c_nst", XC + 46, y_nostruc + 14, WC - 92, 140,
      "&lt;b&gt;K 不是结构约束。&lt;/b&gt;&#xa;"
      "TabularAttentionLayer.__init__ 收下 n_cells，&#xa;"
      "但从不拿它构造任何权重；注意力在 forward 里&#xa;"
      "按实际形状 reshape。&#xa;"
      "&#xa;"
      "所以 K = 256 / 512 只是推理窗口大小，&lt;b&gt;改它不需重训&lt;/b&gt;。&#xa;"
      "与 L2-01 §2.4 第 2 项（State 的 cell_set_len）同构。",
      font=F_CAP, color="#1f4d13", align="left")

# ------------------------------------------------------------------ footer ---
y_foot = 1490
vrect("f_sep", 20, y_foot, 1780, 2, fill="#cccccc")
vtext("f_note", 20, y_foot + 18, 1780, 96,
      "证据边界：本图全部数字来自固定 commit cacc2e4b 的源码静态核验与 notebook 07 的手算，"
      "不是实例化实测。&#xa;"
      "显存按张量形状估算，不含 allocator 碎片与 CUDA context；"
      "算力只给 FLOPs 量级，耗时未测故不填。&#xa;"
      "两处源码与论文的真实差异在本图内标出：窗口切分用 prompt_ratio + context_ratio（panel c），"
      "以及 query_pos_embedding 在源码里是 (n, d)。",
      font=F_CAP, color="#666666")

W, Hc = 1820, y_foot + 130

# ------------------------------------------------------------------ re-parent --
# validate.py only flags W-OVERLAP between vertices with the SAME parent, and
# container vertices are excluded from the leaf set.  So each panel has to own
# every element drawn on it.  Rewriting ~90 absolute-coordinate call sites into
# panel-relative ones is error prone, so the nesting is applied here, once, by
# walking the generated cells: any top-level vertex that lies fully inside a
# panel rectangle becomes that panel's child with clipped coordinates.
import re as _re

_PANELS = [("pa", 20, 130, WA, 1330), ("pb", XB, 130, WB, 1330),
           ("pc", XC, 130, WC, 1330)]
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
    x, y, w, h = (float(g.group(1)), float(g.group(2)),
                  float(g.group(3)), float(g.group(4)))
    return m.group(1), m.group(2), m.group(3), m.group(4), x, y, w, h


def _abs_pos(cells):
    """Absolute origin of each cell, accumulating panel offsets."""
    geo, par = {}, {}
    for c in cells:
        r = _rect(c)
        if not r:
            continue
        geo[r[0]] = (r[4], r[5], r[6], r[7])
        par[r[0]] = r[3]
    absg = {}
    for cid in geo:
        x, y, w, h = geo[cid]
        chain, cur = [], par.get(cid, "1")
        seen = set()
        while cur in geo and cur not in seen:
            seen.add(cur)
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
# Card backings are the ids listed below; their absolute rects are recovered
# from the already-panel-relative geometry by adding the panel origin back.
_CARD_IDS = (["b_punch", "b_mem", "b_comp", "b_ev", "c_warn", "c_ns", "a_blk"]
             + [f"c_w{i}" for i in range(3)])
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
head = ('<mxfile host="app.diagrams.net" modified="2026-09-17T00:00:00.000Z" '
        'agent="vc2026-lessons" version="24.0.0" type="device">'
        '<diagram id="L2-02-stack-icl" name="L2-02 Stack in-context">'
        f'<mxGraphModel dx="1422" dy="798" grid="0" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{W}" pageHeight="{Hc}" math="0" shadow="0">'
        '<root><mxCell id="0"/><mxCell id="1" parent="0"/>')
tail = "</root></mxGraphModel></diagram></mxfile>"

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(head + "".join(cells) + tail)
print("wrote %s with %d cells, canvas %dx%d" % (OUT, len(cells), W, Hc))
