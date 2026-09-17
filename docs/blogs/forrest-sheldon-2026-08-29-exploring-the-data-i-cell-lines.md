# Exploring the Data I — Cell Lines

> **来源**：<https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/> ｜ 站点：forrestsheldon.github.io/virtual-cell
> **作者**：Forrest Sheldon ｜ **发布**：2026-08-29 ｜ **分类**：data exploration / challenge 2026 ｜ **抓取**：2026-09-17
>
> **文件性质：机器转换的阅读副本，不是原文。** 本文件由原网页 HTML 经脚本自动转换为 Markdown，
> 仅用于本地阅读、检索和交叉引用。逐字引用、公式、数值和结论核验**必须回到上方的原文链接**。
> 原文中的图片以绝对 URL 保留引用，未下载到本仓库；若原站改动或下线，图片将不可见。
> 转换过程未做内容改写，但标题层级、表格与公式的渲染可能与原文存在差异。

---

## Summary

- This year’s Virtual Cell Challenge is zero-shot CRISPRi perturbation prediction across cell lines. The experimental stack is cell-line culture → CRISPRi perturbation → 10x Flex scRNA-seq.
- Continuous cell lines include intrinsically proliferative stem-cell lines (H1 or iPSCs), engineered immortalized lines (RPE1 or HEK293), and cancer-derived lines (HeLa).
- Our first guesses for the VCC validation lines are all cancer lines: A → Jurkat E6.1; B → HeLa; C → CAL-33.
- A negative baseline that just sampled the control cells scored −0.304 overall. Five component scores were near zero, but DE direction fidelity was strongly negative at −1.721.

## This year’s task

This year’s Virtual Cell Challenge asks us to predict the responses to 300 different CRISPRi perturbations across three cell lines, given data on non-targeting (unperturbed) cells in those lines. Instead of just the mean responses we’re asked to predict the distribution of potential response behavior by providing 400 model cells for each perturbation. When the test week opens, we will be given three new cell lines and will have to supply the same type of predictions.

For the first series of posts, I will unpack the technologies behind this and what they mean for modeling.

## The data creation stack

> **Cell-line culture** → **CRISPRi perturbation** → **10x Flex scRNA-seq**

In brief, they take a human cell modified to divide continuously, introduce a molecular system that reduces the transcription of a target gene, and then capture a targeted library of mRNA sequences. In the next three posts, I’m going to go through each of these stages in more detail to try to understand what considerations they contribute to modeling.

Today I’m going to look at cell lines: what they are, the broad ways they arise, and how those differences might affect perturbation outcomes.

## The A, B and C control cells

The competition supplies control cells corresponding to 46 non-targeting guides, with 400 cells per guide across three cell lines. That gives \(400 \times 46 \times 3 = 55{,}200\) cells. A quick QC pass confirms the metrics that Arc published:

![Four box plots compare UMIs, detected genes, mitochondrial count percentage and Good-Turing unseen mass across contexts A, B and C.](https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/figures/qc_panel.png)

Figure 1: QC for control cells in each context.

The only potentially unfamiliar metric is the Good-Turing estimate of unseen mass. If a cell contains (N) total UMIs and (N\_1) genes observed exactly once, then

\[\widehat M\_0 = \frac{N\_1}{N}.\]

This estimates the probability that another UMI sampled under the same process would belong to a gene not yet observed in that cell. I’ll probably write something more about it sometime soon.

A UMAP over 2,000 highly variable genes shows three distinct clusters. The embedding uses 5,000 cells from each context.

![Two UMAP panels show three separated context clusters and their UMI counts. Context B contains a small low-UMI satellite population.](https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/figures/umap.png)

Figure 2: The same UMAP colored by context and by UMI count.

Interestingly, cell line B has a small satellite population that appears to have far lower UMI counts. We can also see this more clearly in a plot of the UMI distribution:

![Density curves of per-cell UMI counts show broadly overlapping distributions and an additional low-count mode for context B.](https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/figures/umi_distribution.png)

Figure 3: UMI-count density for each context. The small low-count mode in context B corresponds to the satellite in [Figure 2](#fig-control-umap).

The small peak in B is the satellite.

## What is a cell line?

Humans generally do not like parting with their cells. At the same time, researchers need a constantly renewing source of cells that behave consistently. Continuous cell lines are designed to meet this need. They keep dividing in a dish, providing a renewable and reasonably consistent experimental system.

Human cells generally have some ability to divide, but for most cells this is limited.[1](#fn1) There are a few ways of getting around this. How you get around it can be thought of as forming the broad cell line categories:

- You can use a cancer cell. Cancer cells often carry changes that support continued proliferation, making them natural candidates for continuous cell lines. It was a cervical cancer sample from Henrietta Lacks that led to the development of the first widely used human cell line, HeLa.[2](#fn2) Cancer cell lines are still widely used and grow robustly, but that same robustness means they have limited relevance to healthy human cells or even to each other. Over time separate populations pick up different mutations and chromosomal abnormalities and drift apart.
- You can use a stem cell (or a tissue cell reprogrammed into an induced pluripotent stem cell).[3](#fn3) Stem cells are intrinsically proliferative which means you don’t have to break the biology of the cell. The H1 cell line from last year’s VCC is a human embryonic stem cell line.[4](#fn4)
- You can take a normal human cell and *immortalize* it by removing its division limits. Every time a cell divides, the repeated DNA sequences at the ends of its chromosomes—its [telomeres](https://en.wikipedia.org/wiki/Telomere)—shorten slightly. Introducing [hTERT](https://en.wikipedia.org/wiki/Telomerase_reverse_transcriptase) increases telomerase activity; telomerase extends the telomeres by adding new repeats. For some cell types that is enough to bypass division limits, while others require additional modifications. RPE1 is an example of an immortalized cell line derived from retinal pigment epithelial cells.[5](#fn5)

Two cells from the same line will have similar genomes (there is always drift with divisions but they will be largely similar) and similar epigenetic states (things like chromatin conformation and methylation marks are somewhat conserved in divisions) but they are not perfectly identical. The longer it has been in use, the more differences we can expect between cells nominally belonging to that line. Similarly, differences in growth conditions and the media that the cells are in will also lead to differences between the state of cells between different labs or experiments. All of these factors add up to a cell context that determines the response to a perturbation.

## Analysis: what might A, B and C be?

Can we make a guess about what cell line these might be from? The Human Protein Atlas (HPA) provides RNA expression profiles for 1,206 cell lines.[6](#fn6) As a simple comparison, for each provided cell line, we use the Spearman rank correlation between the pseudobulked cell line and the HPA cells to order the HPA cell lines by similarity.

![Three vertically stacked dot plots show the top three HPA cell-line correlations for contexts A, B and C. HeLa in B has the largest gap over the runner-up.](https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/figures/hpa_rank_correlations.png)

Figure 4: The three highest HPA profile correlations for each context, calculated over 3,000 HPA-variable genes.

Taking the top nomination for each:

| Context | Current hypothesis | Nested classification |
| --- | --- | --- |
| A | Jurkat E6.1 | cancer-derived → haematopoietic/lymphoid → T-cell acute lymphoblastic leukaemia |
| B | HeLa | cancer-derived → epithelial → cervical carcinoma |
| C | CAL-33 | cancer-derived → epithelial → squamous → oral/head-and-neck carcinoma |

In an upcoming post, I’ll summarize the other datasets that are out there for these lines.

## Submission: the null control-resampling baseline

Our first submission just sets a null expectation: every perturbation has no effect. For each target and context, I sample 400 cells from that context’s controls and relabel them with the target gene (balanced across constructs).

| Metric | Score |
| --- | --- |
| Overall | −0.3037 |
| Perturbation discrimination | −0.0050 |
| Expression accuracy | 0.0000 |
| DE log-fold-change accuracy | −0.0053 |
| DE direction fidelity | −1.7214 |
| DE direction reach | −0.0079 |
| DE significance overlap | −0.0826 |

Most components sit close to the zero baseline with direction fidelity the clear exception. In one of my next posts (maybe 3 out), I will dive into the evaluation metrics to see how they work.

I had also intended to include an artifical knockdown baseline, were we just knockdown the target gene expression, but it turns out that the evaluation metrics always neglect the target gene. We will have to wait for the linear response baseline for something more interesting than the controls.

Thanks for reading!

Back to top

## Footnotes

1. Leonard Hayflick and Paul Moorhead described the finite replicative lifespan of cultured human diploid cells in [“The serial cultivation of human diploid cell strains”](https://pubmed.ncbi.nlm.nih.gov/13905658/) (1961), DOI: [10.1016/0014-4827(61)90192-6](https://doi.org/10.1016/0014-4827(61)90192-6).[↩︎](#fnref1)
2. HeLa was established from cervical cancer cells taken from Henrietta Lacks in 1951 without her knowledge or consent. See the [NIH account of HeLa cells](https://osp.od.nih.gov/hela-cells/) and [Johns Hopkins’ account of Henrietta Lacks’ legacy](https://www.hopkinsmedicine.org/henrietta-lacks).[↩︎](#fnref2)
3. Kazutoshi Takahashi and colleagues reprogrammed adult human fibroblasts into induced pluripotent stem cells using defined factors: [*Cell* 131, 861–872 (2007)](https://pubmed.ncbi.nlm.nih.gov/18035408/), DOI: [10.1016/j.cell.2007.11.019](https://doi.org/10.1016/j.cell.2007.11.019).[↩︎](#fnref3)
4. H1 was one of the human embryonic stem-cell lines reported by James Thomson and colleagues in [*Science* 282, 1145–1147 (1998)](https://pubmed.ncbi.nlm.nih.gov/9804556/), DOI: [10.1126/science.282.5391.1145](https://doi.org/10.1126/science.282.5391.1145).[↩︎](#fnref4)
5. ATCC describes [hTERT RPE-1 (CRL-4000)](https://www.atcc.org/products/crl-4000) as a retinal pigment epithelial line immortalized by expression of hTERT.[↩︎](#fnref5)
6. [Human Protein Atlas downloadable data](https://www.proteinatlas.org/about/download), version 25.1, accessed 28 August 2026. The cell-line RNA table contains 1,206 profiles over 20,162 genes.[↩︎](#fnref6)
