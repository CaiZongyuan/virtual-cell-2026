# -*- coding: utf-8 -*-
"""Emit the AIAYN-style State (ST) architecture .drawio -- revision 3.

Revision 3 (user feedback 2026-09-17):
- ELEMENTS TOO BIG / file 368 KB: canvas shrunk 1900x2200 -> 1790x1600 and the
  asset is exported at 1.25x instead of 2x (was 3782x4184).
- FONT UNCOMFORTABLE: nothing below 12 model px any more.  body 13 -> 14,
  captions 11 -> 12, legend 10 -> 12.
- LINES AND TEXT TOO CLOSE / OVERLAPPING, three concrete collisions:
  * the vertical legend row sat under the (a) caption and they overlapped;
    the legend is now a single horizontal strip inside the header band.
  * the predict_residual skip loop ran at x=750 and cut straight through the
    dashed border of panels (b) and (c); it now runs at x=660, inside (a).
  * panel (b) carried ~230 px of dead space at the top, so its content sat
    far from its own title.  Panel (b) is now 690 tall (was 950) and every
    vertical gap is >= 20 px.
- panel captions now sit 25-30 px clear of the panel borders.
"""
import sys

OUT = sys.argv[1]

PAL = {
    "attn":  ("#ffe6cc", "#d79b00"),
    "norm":  ("#f8cecc", "#b85450"),
    "ffn":   ("#fff2cc", "#d6b656"),
    "plain": ("#ffffff", "#000000"),
    "io":    ("#f5f5f5", "#666666"),
    "loss":  ("#d5e8d4", "#82b366"),
}

# ---- typography scale: the ONLY place font sizes are written ----------------
F_MAIN = 20   # document title
F_SUB = 13    # document subtitle / legend
F_PANEL = 15  # (a) (b) (c) panel titles
F_BOX = 14    # module boxes
F_BOXS = 13   # minor boxes
F_CAP = 12    # captions and notes
F_RATIO = 14  # V / K / Q labels

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


def vellipse(cid, x, y, w, h, parent="1"):
    st = ("ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
          "fontFamily=Helvetica;fontSize=16;fontStyle=1;fontColor=#111111;")
    add(f'<mxCell id="{cid}" value="+" style="{st}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def edge(cid, src, tgt, pins, parent="1"):
    st = ("edgeStyle=none;rounded=0;html=1;endArrow=block;endSize=8;"
          "strokeColor=#000000;strokeWidth=1;" + pins)
    add(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="{parent}" '
        f'source="{src}" target="{tgt}">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>')


def fedge(cid, sp, wps, tp, parent="1"):
    pts = "".join(f'<mxPoint x="{p[0]}" y="{p[1]}"/>' for p in wps)
    st = ("edgeStyle=none;rounded=0;html=1;endArrow=block;endSize=8;"
          "strokeColor=#000000;strokeWidth=1;")
    add(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="{parent}">'
        f'<mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{sp[0]}" y="{sp[1]}" as="sourcePoint"/>'
        f'<mxPoint x="{tp[0]}" y="{tp[1]}" as="targetPoint"/>'
        f'<Array as="points">{pts}</Array></mxGeometry></mxCell>')


V = "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;"

# ----------------------------------------------------------------- header ----
vtext("t1", 20, 24, 1300, 32,
      "图 L2-01&#xa0;|&#xa0;State（ST）架构：把细胞集合当 token 的双向 Transformer",
      font=F_MAIN, bold=True, color="#1a1a1a")
vtext("t2", 20, 62, 1750, 24,
      "结构依据 Arc 官方源码 commit 9bbfe78 的静态核验（本轮未运行训练、未加载权重）；"
      "图中维数为配置读取值，不是实测结果。",
      font=F_CAP, color="#666666")

# legend as a single horizontal strip: it used to be a tall column on the left
# and collided with the (a) caption.
for i, (role, label) in enumerate([
        ("attn", "注意力模块"),
        ("norm", "Add &amp; Norm"),
        ("ffn", "前馈网络"),
        ("plain", "线性/逐元素"),
        ("io", "输入输出"),
        ("loss", "损失(仅训练)")]):
    f, s = PAL[role]
    xx = 24 + 200 * i
    add(f'<mxCell id="lg{i}" value="" style="rounded=0;html=1;'
        f'perimeter=rectanglePerimeter;fillColor={f};strokeColor={s};" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{xx}" y="94" width="24" height="14" as="geometry"/></mxCell>')
    vtext(f"lgt{i}", xx + 32, 91, 158, 20, label, font=F_CAP, color="#111111")

vrect("t3", 20, 120, 1750, 2, fill="#cccccc")

# ================================================================ PANEL (a) ==
vtext("a_t", 20, 130, 520, 28, "（a）ST 前向路径", font=F_PANEL, bold=True,
      color="#111111")
vtext("a_out", 190, 196, 320, 68,
      "扰动后表达预测（G 维）&#xa;ŷ ∈ ℝ^G，G = 18,533&#xa;仍是浮点 log 空间，不是原始计数",
      font=F_CAP, align="center")
vbox("a_relu", 190, 306, 320, 54, "ReLU")
vbox("a_lin_g8g", 190, 384, 320, 54, "Linear&#xa0;&#xa0;G/8 → G")
vbox("a_gelu", 190, 462, 320, 54, "GELU")
vbox("a_lin_gg8", 190, 540, 320, 54, "Linear&#xa0;&#xa0;G → G/8")
vellipse("a_add2", 337, 622, 26, 26)
vbox("a_lin_768g", 190, 676, 320, 54, "Linear&#xa0;&#xa0;768 → G")

vbox("a_blk", 150, 766, 400, 390, "", container=True)
vbox("a_mha", 50, 278, 300, 76,
     "集合自注意力（双向）&#xa;12 heads × head_dim 64",
     role="attn", parent="a_blk")
vbox("a_an1", 50, 208, 300, 48, "Add &amp; Norm", role="norm", parent="a_blk")
vbox("a_ffn", 50, 110, 300, 76,
     "前馈网络 Feed Forward&#xa;hidden 3,072", role="ffn", parent="a_blk")
vbox("a_an2", 50, 20, 300, 48, "Add &amp; Norm", role="norm", parent="a_blk")
vrect("a_nbrk", 113, 766, 3, 390)
vrect("a_nbrkt", 116, 766, 14, 3)
vrect("a_nbrkb", 116, 1153, 14, 3)
vtext("a_nlbl", 20, 936, 90, 46, "N×&#xa;（8 层）", font=F_CAP, bold=True,
      align="center", color="#111111")

vbox("a_lin_g768", 190, 1240, 320, 54, "Linear&#xa0;&#xa0;G → 768")
vellipse("a_add1", 337, 1186, 26, 26)
vbox("a_lin_d768", 20, 1174, 150, 50, "Linear&#xa0;&#xa0;D → 768", font=F_BOXS)
vtext("a_tgt", 14, 1232, 164, 78,
      "靶点特征 eᵗ ∈ ℝ^D&#xa;one-hot 词表 2,024&#xa;或 ESM2 连续向量",
      font=F_CAP, align="center")
vtext("a_in", 190, 1322, 320, 64,
      "对照细胞集合（NTC）&#xa;每个细胞 = 一个 token&#xa;x ∈ ℝ^G，G = 18,533",
      font=F_CAP, align="center")
vtext("a_reslab", 600, 540, 176, 62,
      "残差：加回对照表达 x&#xa;predict_residual = true", font=F_CAP)

edge("ea1", "a_in", "a_lin_g768", V)
edge("ea2", "a_lin_g768", "a_add1", V)
edge("ea3", "a_lin_d768", "a_add1",
     "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;")
edge("ea4", "a_add1", "a_mha", V)
edge("ea5", "a_mha", "a_an1", V)
edge("ea6", "a_an1", "a_ffn", V)
edge("ea7", "a_ffn", "a_an2", V)
edge("ea8", "a_an2", "a_lin_768g", V)
edge("ea9", "a_lin_768g", "a_add2", V)
edge("ea10", "a_add2", "a_lin_gg8", V)
edge("ea11", "a_lin_gg8", "a_gelu", V)
edge("ea12", "a_gelu", "a_lin_g8g", V)
edge("ea13", "a_lin_g8g", "a_relu", V)
edge("ea14", "a_relu", "a_out", V)

# residual skip: previously routed at x=750, i.e. straight through the dashed
# border of panels (b)/(c).  Now it stays inside (a) at x=660.
fedge("ea17", (510, 1354), [(660, 1354), (660, 635)], (363, 635))

vtext("a_cap", 20, 1412, 700, 60,
      "（a）ST 前向路径：官方默认 embed_key=null / output_space=all / predict_residual=true。&#xa;"
      "两处残差：主干前后各一次，第二处是把预测加回对照表达。&#xa;"
      "G→G/8→G 混合层在 G=18,533 时约占 8,587 万参数；8 层主干约 7,551 万（按矩阵形状手算，非实测）。",
      font=F_CAP, color="#555555", valign="top")

# ================================================================ PANEL (b) ==
vbox("bf", 800, 130, 960, 690, "", dashed=1, container=True)
vtext("b_t", 24, 22, 912, 26,
      "（b）集合自注意力：注意力在细胞之间，不在基因之间",
      font=F_PANEL, bold=True, color="#111111", parent="bf")
vtext("b_out", 265, 64, 430, 54,
      "回到残差与 Add &amp; Norm&#xa;（双向，没有因果掩码）",
      font=F_BOXS, align="center", parent="bf")
vbox("b_lin", 295, 142, 370, 54, "Linear&#xa0;&#xa0;768 → 768", parent="bf")
vbox("b_concat", 295, 220, 370, 54, "拼接 Concat（12 个头 → 768）", parent="bf")
vrect("b_bus2", 230, 296, 500, 2, parent="bf")
vbox("b_h1", 145, 320, 170, 92, "缩放点积注意力&#xa;头 1", role="attn",
     font=F_BOXS, parent="bf")
vtext("b_dots", 395, 330, 170, 72, "⋯", font=24, align="center", parent="bf")
vbox("b_h2", 645, 320, 170, 92, "缩放点积注意力&#xa;头 12", role="attn",
     font=F_BOXS, parent="bf")
vrect("b_bus1", 230, 436, 500, 2, parent="bf")
vbox("b_lv", 315, 460, 90, 54, "Linear", font=F_BOXS, parent="bf")
vbox("b_lk", 435, 460, 90, 54, "Linear", font=F_BOXS, parent="bf")
vbox("b_lq", 555, 460, 90, 54, "Linear", font=F_BOXS, parent="bf")
vtext("b_v", 315, 540, 90, 26, "V", font=F_RATIO, align="center", parent="bf")
vtext("b_k", 435, 540, 90, 26, "K", font=F_RATIO, align="center", parent="bf")
vtext("b_q", 555, 540, 90, 26, "Q", font=F_RATIO, align="center", parent="bf")
vtext("b_note", 24, 586, 912, 46,
      "V、K、Q 都来自同一批细胞 token —— 这是自注意力。&#xa;"
      "State 用双向注意力，且不使用旋转位置编码（RoPE）。",
      font=F_CAP, color="#555555", parent="bf", valign="top")
vrect("b_hbt", 825, 318, 36, 3, parent="bf")
vrect("b_hbb", 825, 411, 36, 3, parent="bf")
vrect("b_hbv", 861, 318, 3, 96, parent="bf")
vtext("b_hbl", 872, 336, 70, 56, "h = 12&#xa;个头", font=F_CAP, align="center",
      color="#111111", parent="bf")

edge("eb1", "b_v", "b_lv", V, parent="bf")
edge("eb2", "b_k", "b_lk", V, parent="bf")
edge("eb3", "b_q", "b_lq", V, parent="bf")
edge("eb4", "b_lv", "b_bus1",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.26;entryY=0;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb5", "b_lk", "b_bus1",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb6", "b_lq", "b_bus1",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.74;entryY=0;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb7", "b_bus1", "b_h1",
     "exitX=0;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb8", "b_bus1", "b_h2",
     "exitX=1;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb9", "b_h1", "b_bus2",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0;entryY=1;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb10", "b_h2", "b_bus2",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=1;entryY=1;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb11", "b_bus2", "b_concat",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;",
     parent="bf")
edge("eb12", "b_concat", "b_lin", V, parent="bf")
edge("eb13", "b_lin", "b_out", V, parent="bf")

vtext("b_cap", 800, 846, 960, 48,
      "（b）每个细胞是一个 token，token 之间两两算注意力（cell_set_len = 64）。&#xa;"
      "一个 token 是一条基因表达向量，所以「集合长度 64」指 64 个细胞，不是 64 个基因。",
      font=F_CAP, color="#555555", valign="top")

# ================================================================ PANEL (c) ==
vbox("cf", 800, 906, 960, 610, "", dashed=1, container=True)
vtext("c_t", 24, 22, 912, 26,
      "（c）Energy 距离集合损失：比较两个集合的分布，不要求逐细胞配对",
      font=F_PANEL, bold=True, color="#111111", parent="cf")
vtext("c_note", 24, 56, 912, 50,
      "这是 State 相对普通回归基线的关键差别：损失在集合层面比较分布，&#xa;"
      "模型不必猜「哪个真实细胞对应哪个预测细胞」，两边的集合大小也不必相等。",
      font=F_CAP, color="#555555", parent="cf", valign="top")
vtext("c_out", 225, 112, 510, 28, "对集合整体给出一个标量 → 反向传播",
      font=F_BOXS, align="center", parent="cf")
vbox("c_green", 285, 168, 390, 54, "标量损失（仅训练时存在）", role="loss",
     parent="cf")
vbox("c_energy", 85, 254, 790, 84,
     "Energy 距离（分布级损失）&#xa;2·E‖P−Q‖ − E‖P−P′‖ − E‖Q−Q′‖&#xa;"
     "（标准形式；源码配置 loss=energy）",
     role="loss", font=F_BOXS, parent="cf")
vbox("c_dist", 85, 370, 790, 54, "两两距离 ‖ŷ − x′‖（集合级，不配对）",
     role="io", font=F_BOXS, parent="cf")
vbox("c_setP", 85, 454, 360, 58, "预测集合（模型输出）", role="io", font=F_BOXS,
     parent="cf")
vbox("c_setQ", 515, 454, 360, 58, "真实集合（公共训练数据）", role="io", font=F_BOXS,
     parent="cf")
vtext("c_labP", 85, 540, 360, 46, "预测细胞集合&#xa;{ŷ₁ … ŷ₆₄}", font=F_CAP,
      align="center", parent="cf")
vtext("c_labQ", 515, 540, 360, 46, "真实细胞集合&#xa;{x′₁ … x′₆₄}", font=F_CAP,
      align="center", parent="cf")

edge("ec1", "c_labP", "c_setP", V, parent="cf")
edge("ec2", "c_labQ", "c_setQ", V, parent="cf")
edge("ec3", "c_setP", "c_dist",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.2278;entryY=1;entryDx=0;entryDy=0;",
     parent="cf")
edge("ec4", "c_setQ", "c_dist",
     "exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.7722;entryY=1;entryDx=0;entryDy=0;",
     parent="cf")
edge("ec5", "c_dist", "c_energy", V, parent="cf")
edge("ec6", "c_energy", "c_green", V, parent="cf")
edge("ec7", "c_green", "c_out", V, parent="cf")

vtext("c_cap", 800, 1536, 960, 48,
      "（c）损失类型来自官方配置 loss=energy / distributional_loss=energy。&#xa;"
      "图中画的是标准 Energy 距离的三项结构，用来说明损失比较的是分布；未逐行复刻官方实现。",
      font=F_CAP, color="#555555", valign="top")

# -------------------------------------------------------------- assemble -----
body = "\n        ".join(cells)
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="State-ST-architecture" id="st-arch-1">
    <mxGraphModel dx="2400" dy="1600" grid="0" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="0"
                  pageScale="1" pageWidth="1790" pageHeight="1610"
                  math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {body}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(xml)
print("wrote %s (%d cells, %d bytes)" % (OUT, len(cells), len(xml.encode("utf-8"))))
