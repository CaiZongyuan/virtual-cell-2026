# Preliminaries — who I am and how I'm approaching the competition

> **来源**：<https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-my-approach-to-the-virtual-cell/> ｜ 站点：forrestsheldon.github.io/virtual-cell
> **作者**：Forrest Sheldon ｜ **发布**：2026-08-29 ｜ **分类**：introduction / challenge 2026 ｜ **抓取**：2026-09-17
>
> **文件性质：机器转换的阅读副本，不是原文。** 本文件由原网页 HTML 经脚本自动转换为 Markdown，
> 仅用于本地阅读、检索和交叉引用。逐字引用、公式、数值和结论核验**必须回到上方的原文链接**。
> 原文中的图片以绝对 URL 保留引用，未下载到本仓库；若原站改动或下线，图片将不可见。
> 转换过程未做内容改写，但标题层级、表格与公式的渲染可能与原文存在差异。

---

## whoami

Hi! I’m Forrest and for whatever reason you’ve stumbled onto my Virtual Cell Challenge blog. I made a pivot from physics and neuromorphic computing to biology and cell reprogramming a few years ago. For the last couple of years I’ve been working on analyzing perturbation screens and trying to find reliable ways to nominate cell reprogramming targets. That turns out to be a pretty hard problem and in the process I’m continually learning new things about biology, statistics and machine learning. To keep that process going, I’m joining the Virtual Cell Challenge.

## How I’m approaching the Virtual Cell Challenge

First, I am not alone. My friend Alex and I are a two-person team. As individuals we can’t compete with larger teams on resources, so the goal here is to carefully wade into this year’s challenge and look for novel and cheap ideas that we can try. The best way to learn is not just by doing, but by doing carefully, and writing about the process is a way to ensure that happens. Hopefully in doing that, we’ll kick off some worthwhile conversations with everyone else.

Broadly, I’m organizing my work into four stages:

- Exploring the Data - For the first week or two I’ll be writing about the provided and linked datasets and the methods used to produce them. The material here will be more biology and sequencing heavy but if you want to make a good model, you need to understand your data.
- Baselines - One of the themes of virtual cell modeling so far is that simple baselines are tough to beat. A lot of that debate centers on what you measure and more careful evaluations have shown that deep learning models may have the edge. The point remains though that simple interpretable models can be competitive if they are carefully geared to the problem at hand. I’ll start with simple linear models and examine the evaluation metrics carefully. Looking at these should occupy early September.
- Beyond Linear Models - Can we use the successes and failures of our nice interpretable baselines to develop a family of slightly more advanced models that include machine learning in precisely targeted ways? This should close out September.
- Modern Models - Part of the goal of all of this is to learn about the modern approaches to the virtual cell: transformers, flow matching, optimal transport etc. I’ll spend the last month of the competition writing about and playing with these approaches.

If that sounds interesting, I hope you’ll follow along.

Back to top
