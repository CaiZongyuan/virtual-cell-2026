# VCC26: Exploring the Data III — Sequencing and External Datasets

> **来源**：<https://forrestsheldon.github.io/virtual-cell/posts/2026-09-14-exploring-the-data-iii/> ｜ 站点：forrestsheldon.github.io/virtual-cell
> **作者**：Forrest Sheldon ｜ **发布**：2026-09-14 ｜ **分类**：data exploration / measurement models / perturbation data ｜ **抓取**：2026-09-17
>
> **文件性质：机器转换的阅读副本，不是原文。** 本文件由原网页 HTML 经脚本自动转换为 Markdown，
> 仅用于本地阅读、检索和交叉引用。逐字引用、公式、数值和结论核验**必须回到上方的原文链接**。
> 原文中的图片以绝对 URL 保留引用，未下载到本仓库；若原站改动或下线，图片将不可见。
> 转换过程未做内容改写，但标题层级、表格与公式的渲染可能与原文存在差异。

---

In biology the measurement is part of the experiment. That can be hard to grasp coming from fields where interpreting experiments is more direct and is one of the first things to trip up incoming data scientists and ML researchers.

For biologists the way around this is to put everything in one experiment and then focus on contrasts. That is not an option for applying ML. Getting many different experiments to talk to one another might be *the* primary challenge. The zero-shot nature of the 2026 challenge puts this center-stage: we need to find ways to unify the results of many different cellular measurements into one virtual cell model.

In this post, I am going to talk about sequencing, how we can model it as a sampling process, and what data is out there to make our comparisons.

## From cells to counts: sequencing as sampling

There are many, many ways to go from a plate of cells to a count matrix. I had Claude put together the figure below summarising the possible ways of running each step of a sequencing experiment. Each pill has a hovertext explanation (written by Claude).

Loosely we:

1. **Prepare the cells** — fresh, fixed, or frozen; whole cells or extracted nuclei.
2. **Separate the cells and give each a unique cell barcode** — in droplets, in wells, or through rounds of split-pool labelling.
3. **Capture the mRNA** — bind transcripts through their poly-A tail or with targeted probes.
4. **Convert the mRNA into complementary DNA (cDNA)** by reverse transcription (RT), attaching the cell barcode and a unique molecular identifier (UMI) to each captured molecule. All mRNA from a cell shares the same cell barcode, but each molecule gets a different UMI.
5. **Amplify the cDNA** many times to create enough material to sequence.
6. **Break the cDNA into shorter fragments** and attach sequencing adapters.
7. **Sequence the fragments.**
8. **Post-process** — map each fragment to a gene and cell, then collapse fragments sharing a UMI into a single molecule.

You can spend a moment browsing the figure to get an idea of the variety of approaches to each of these steps.

The measurement pipeline: cells → counts
10x 3′ (Replogle)
10x Flex (VCC)
Parse (Jiang)
Smart-seq (full-length)

1
2
3
4
5
6
7
8
1 · Sample & cell state

fresh

fixed

frozen
nuclei (snRNA)
2 · Compartmentalization & barcoding

GEMs / droplet

split-pool

plate / FACS

microwell
3 · Transcript capture

poly-A (oligo-dT)

probe hyb + ligation

random priming

4 · Conversion to sequenceable molecule

RT → cDNA (± TSO)

ligated probe (no RT)

5 · Amplification

PCR

IVT (linear)
6 · Library prep

fragment + adapters

tagmentation

7 · Sequencing (Illumina)

R1 = barcode+UMI · R2 = cDNA

both mates cDNA

depth = reads / cell — the sampling knob
8 · Quantification

genome / transcriptome align

probe-set match

→ cell calling → UMI collapse → gene × cell count matrix

Sequencing has several more variations than listed here. My brief summary is:

- 3’/5’/full-length designates the part of the transcript that attaches to the UMI-barcode. In 3’/5’, the UMI-barcode is attached to the 3’/5’ end. In 3’ it is at the start, so every cDNA carries the UMI. In 5’ and modern full-length it is at the end, so only completely transcribed cDNA carries the UMI (partials do not). After fragmentation, 3’ and 5’ only keep the fragments that carry the UMI/barcode, while in full-length all fragments are kept. This is why full-length sequencing gives more information about isoforms and splicing but UMI collapse can only be applied to the 5’ end fragments.
- Probe-capture, like 10X Flex, uses paired DNA probes that bind to neighboring target sequences on the mRNA. Rather than capturing any poly-A tail, they target specific sequences allowing researchers to only capture a subset of molecules and not waste sequencing. Probes that bind to target mRNA are fused (ligated) together and the joined probes are then what is sequenced.
- Single-/paired-end sequencing refers to how the kept fragments are read by the sequencer. Single-end gives one read, from the barcoded (Read 1) end of the fragment. Paired-end does a read from each end of the fragment. This is usually a short read for the UMI-barcode and then a long read from the opposite end to read the fragment. Because the barcode and the transcript sit at opposite ends, a 3’/5’ assay needs paired-end reads to recover both — a single read would return only the barcode. Paired reads can give us better alignment and more information about isoforms/splicing but it means we spend more sequencing on each fragment rather than capturing fragments more widely.

What this should convey is that there is a tremendous amount of technical variation in how the count matrix is prepared and any focus on biological variation will have to take separating these technical effects out seriously. This is the core reason why it is so difficult to integrate two datasets together: each one is filtered through a different experimental process that puts the biological variation in each in different coordinates.

## What is a “batch effect,” really?

When you look at two different scRNAseq datasets, the first step is usually to look for evidence of “batch effects” which are features of the experiments that make them difficult to compare. We can decompose this into a few buckets:

- Measurement/sequencing - differences in sequencing depth, gene capture efficiency, the gene panel and many other choices as to how the experiment was run can lead to differences in what the counts represent.
- Cell composition - The experiments contain different mixtures of cell states. This is usually what we want to observe but when combined with measurement differences it means the two are confounded.
- Intangibles - scRNAseq is known for less tangible reasons for variation: operator to operator differences, reagent lots, jamming in the sorter etc. Even in datasets matched across sequencing and cell composition, we can still see differences.

In the next section, we’ll do the best we can to produce a measurement model that separates these effects.

## A measurement model

Let’s start translating this to math. The framing below — separating measurement from expression and starting from a Poisson measurement model — follows Sarkar and Stephens.[1](#fn1)

1. **Step 0: Underlying Biology** We begin with a pool of mRNA where each cell possesses \(M\_c\) molecules with abundances \(\pi\_{cg}\) so that \(\sum\_g \pi\_{cg} = 1\) and the number of mRNA from gene \(g\) is \(M\_{cg} = M\_c \pi\_{cg}\). Their values are decided by the distribution of cell states going into the experiment and the preparation the sample undergoes (for example whether the cells are fresh/fixed or whether the nuclei have been extracted).
2. **Step 1: Capture** Each molecule is *captured* (i.e. labelled with a cell barcode and UMI) with a gene specific probability \(e\_g\). This is gene specific because the capture chemistry can depend on things like GC content and length. After this, we are left with a pool of \(U\_{cg}\) molecules that follows \[U\_{cg} \sim \operatorname{Binomial}(M\_{cg}, e\_g) \xrightarrow[\;e\_g \ll 1\;]{} \operatorname{Poisson}(M\_{cg}\, e\_g) = \operatorname{Poisson}(M\_c\, e\_g\, \pi\_{cg}).\] The last step is the usual rare event limit of the binomial distribution.
3. **Step 2: Amplification** Each UMI’d and barcoded molecule \(u\) becomes \(A\_{cgu}\) molecules via a branching process that gives us enough material to sample.
4. **Step 3: Sequencing** In our pool of \(T = \sum\_{cgu} A\_{cgu}\) molecules we sample \(N\) which sets the sequencing depth. We can model this exactly by drawing from an urn without replacement which is distributed as a multivariate hypergeometric RV. If \(N \ll T\) then sampling does not change the distribution of molecules in the pool by that much and we can approximate this as a multinomial sampling process[2](#fn2) where the exact numbers of each molecule, \(A\_{cgu}\), are replaced by their relative abundances \(\frac{A\_{cgu}}{T}\). Finally when \(N\) is large, we can approximate the multinomial by independent Poisson distributions[3](#fn3) where the number of copies \(R\_{cgu}\) sequenced from molecule \(u\) are distributed as \[R\_{cgu} \sim \operatorname{Poisson}\left(\frac{N}{T} A\_{cgu}\right).\] This is just a thinning of the amplified counts by \(r = \frac{N}{T} \ll 1\).
5. **Step 4: UMI Collapse** When we assign counts, we do so as \(Y\_{cg} = \# \{u : \text{at least one copy of molecule } u \text{ was sequenced}\}\). From our distribution for \(R\_{cgu}\) we have \(P(R\_{cgu} > 0) = 1-\exp(-r A\_{cgu}) =: d\_{cgu}\). The next step is a bit more technical and left to an appendix below. The gist is that we can replace \(d\_{cgu}\) by its average value over the amplification distribution \(\bar{d}\_{cg}\). Then by making the same Poissonisation argument for \(U\_{cg}\) we can obtain \[Y\_{cg} \sim \operatorname{Poisson}(\bar{d}\_{cg}\, e\_g\, M\_c\, \pi\_{cg}).\] The average \(\bar{d}\_{cg}\) takes into account biases between cell and gene specific effects. If we assume that these are independent we can write this as a rank one product, \(\bar{d}\_{cg} = \phi\_c \gamma\_g\) which gives us the final form \[Y\_{cg} \sim \operatorname{Poisson}(\phi\_c\, \gamma\_g\, e\_g\, M\_c\, \pi\_{cg}) = \operatorname{Poisson}(s\_c\, f\_g\, \pi\_{cg}), \qquad s\_c = \phi\_c M\_c,\ \ f\_g = \gamma\_g e\_g.\]

This is our final result, which gives us a decomposition into technical effects captured by the cell specific size factor \(s\_c\) and the gene specific \(f\_g\) and biological variation in \(\pi\_{cg}\), the relative abundances of each molecular species in the cell. The model tells us what comparisons are meaningful in a count matrix:

- Comparisons between cells need to be depth corrected to compensate for differences in \(s\_c\).
- Comparisons between genes are confounded by differences in \(f\_g\).
- Depth corrected ratios between cells in the same gene allow \(f\_g\) to cancel and depend on the underlying biology \(\pi\_{cg}\) only.
- Comparisons between experiments must contend with differences in both \(s\_c\) and \(f\_g\). This is the integration problem we will talk about in the next section.

Lastly, the model predicts that if we collect cells in the same state (\(\pi\_{cg}\) constant) at matched depth, counts for each gene should be Poisson distributed which means that the variance is equal to the mean. Overdispersion (when the variance is greater than the mean) is a sign of variation in cell state.[4](#fn4) It should be said that \(\pi\_{cg}\) constant is a very restrictive definition of cell state but it is a start.

## Why integrating two experiments needs overlapping cell states

The integration problem is that, from counts alone an experiment A vs. experiment B difference is explained equally well by differences in \(f\_g\) or differences in \(\pi\_{cg}\). To get around this, integration methods need an ‘anchor’ population of cells that are assumed to have equal \(\pi\_{cg}\).[5](#fn5) This allows us to pin down the ratio \(f\_g^{(A)}/f\_g^{(B)}\) and translate between the two experiments. If two experiments do not have shared cell types/states, then there is not a principled way to do this and most methods just rely on nearest neighbor distance in the confounded space.

## What’s actually out there, and what it lets us compare

Now that we know what we need to do to actually use other datasets, let’s see what’s out there. I had codex search the perturbation databases for CRISPRi datasets and had it summarize what it found below, plus a few more (Orion, Nourreddine, and Zhu) that readers and the Myllia challenge pointed to.[6](#fn6) (LenidKlarov on Discord also pointed out the Orion dataset. If anyone wants to share other datasets to add to the table please do.) The most important external datasets are the ones that overlap the VCC-300 most heavily. The Orion dataset from Xaira Therapeutics covers all 300 perturbations in two lines, HCT116 (a colorectal cancer line) and HEK293T (a transformed embryonic kidney line). Zhu 2026 covers 297 in primary CD4+ T cells — the only primary rather than immortalized context here — and Nourreddine 2024 covers 282 in KOLF2.1J, an induced pluripotent stem cell line and so the closest match to the VCC’s H1. The Replogle 2022 genome wide screen in K562, a cancer cell line from a patient with leukemia, covers 272.

Table 1: Single-gene CRISPRi perturbation coverage across public dataset-contexts.

| Study | Cell line | Tissue | Assay | Perturbations | VCC-300 targets | Perturbed cells | Median cells/pert |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X-Atlas/Orion 2025 | HCT116 | colon (CRC) | 10x Perturb-seq (FiCS) | 18,293 | 300 | 3,243,392 | 150 |
| X-Atlas/Orion 2025 | HEK293T | embryonic kidney | 10x Perturb-seq (FiCS) | 18,311 | 300 | 4,315,461 | 200 |
| Zhu 2026 | primary CD4+ T | blood (T cell) | 10x Perturb-seq | 12,730 | 297 | 21,056,730 | 1,508 |
| Nourreddine 2024 | KOLF2.1J | iPSC | 10x Perturb-seq | 11,687 | 282 | 2,512,462 | 218 |
| Replogle 2022 | K562 | blood (CML) | 10x Perturb-seq | 9,870 | 272 | 1,960,878 | 182 |
| Replogle 2022 | RPE1 | retina | 10x Perturb-seq | 2,393 | 0 | 236,429 | 72 |
| Nadig 2025 | HepG2 | liver | 10x Perturb-seq | 2,393 | 0 | 140,497 | 45 |
| Nadig 2025 | Jurkat | blood (T-ALL) | 10x Perturb-seq | 2,393 | 0 | 250,943 | 83 |
| Jiang 2025 | A549 | lung | Parse Perturb-seq | 218 | 9 | 197,627 | 676 |
| Jiang 2025 | MCF7 | breast | Parse Perturb-seq | 218 | 9 | 249,726 | 859 |
| Jiang 2025 | HT29 | colon | Parse Perturb-seq | 218 | 9 | 340,940 | 1,148 |
| Jiang 2025 | HAP1 | bone marrow | Parse Perturb-seq | 218 | 9 | 261,477 | 884 |
| Jiang 2025 | BxPC3 | pancreas | Parse Perturb-seq | 218 | 9 | 296,666 | 989 |
| Jiang 2025 | K562 | blood (CML) | Parse Perturb-seq | 218 | 9 | 197,771 | 581 |
| McFaline 2024 | A172 | brain (GBM) | sci-Plex-GxE | 522 | 23 | 230,478 | 422 |
| McFaline 2024 | T98G | brain (GBM) | sci-Plex-GxE | 522 | 23 | 207,424 | 379 |
| McFaline 2024 | U87MG | brain (GBM) | sci-Plex-GxE | 522 | 23 | 232,326 | 428 |
| VCC 2025 | H1 | embryonic stem | 10x Flex | 150 | 13 | 183,097 | 1,045 |

## An evaluation ladder we can build ourselves

Using external datasets relies on how well we can build bridges across the technical and biological differences that exist between them. Rather than jumping straight to the hardest comparisons, we can use the available datasets to build up progressively more difficult evaluations by being flexible over which genes and cell lines we compare. The table below gives a ladder of evaluations that we can build up to test our ability to generalize.

Table 2: The evaluation ladder — progressively harder public-data comparisons, ordered by what changes between the data we fit on and the data we predict.

| Rung | Held fixed | Varies | Isolates | Example data |
| --- | --- | --- | --- | --- |
| 1 — same experiment, split | cell line, method, batch | held-out perturbations | sampling / metric ceiling | a dense single context (Orion, Zhu CD4+ T, or Replogle K562; H1) |
| 2 — same cell line, different sequencing | biology (\(\pi\)) | method (\(f\_g\)) | measurement batch effect | K562: Replogle (10x) × Jiang (Parse), 187 shared genes |
| 3 — same sequencing, different cell line | method (\(f\_g\)) | biology (\(\pi\)) | biological transfer | Jiang’s 6 lines; McFaline’s 3 GBM lines; Replogle K562↔︎RPE1; Nadig HepG2↔︎Jurkat; the 10x screens (Orion, Nourreddine, Zhu) across their lines |
| 4 — different sequencing + different cell line | nothing | both | the full problem (≈ VCC zero-shot task) | Replogle K562 → Nadig / McFaline / Jiang non-K562; Nourreddine KOLF2.1J → H1 (pluripotent → pluripotent, the closest analog) |

Alright, that will have to do for this post. For the next, I am going to look at zero-shot baselines and do another that goes into a deeper dive on the phenomenology of perturbation responses.

## Appendix: UMI collapse

From step 5, the counts we attribute to a cell and gene after UMI collapse will be \[Y\_{cg} = \sum\_{u=1}^{U\_{cg}} B\_{cgu}(A\_{cgu})\] where \(B\_{cgu}(A\_{cgu})\) is a Bernoulli random variable that depends on the random amplification \(A\_{cgu}\) and is 1 with probability \(d\_{cgu} = 1-\exp(-r A\_{cgu})\). Dropping subscripts for convenience, we want to calculate \[E\_Y[z^Y] = E\_U[E\_{A|U}[E\_{B|A,U}[z^{\sum\_{u=1}^U B\_u(A\_u)}]]].\] In the above we have used that \(Y\) is a deterministic function of the random variables \(U, A\_u, B\_u\) and we’ve unrolled the expectation into a few steps. Calculating outwards from the innermost expectation, \[E\_{B|A,U}[z^{\sum\_{u=1}^U B\_u(A\_u)}] = \prod\_{u=1}^U (1 + d(A\_u)(z-1))\] where we have used that the Bernoulli random variables are independent. Acting with the next expectation, \[E\_{A|U}[\prod\_{u=1}^U (1 + d(A\_u)(z-1))] = (1 + \bar{d}(z-1))^U, \quad \bar{d} = E\_A[d\_u].\] Finally we take the expectation over \(U\sim \operatorname{Poisson}(\mu)\) in the rare-event/Poisson limit, \[E\_U[(1 + \bar{d}(z-1))^U] = e^{\mu \bar{d}(z-1)}.\] This is a Poisson generating function with parameter \(\mu \bar{d}\). Adding back in all of the subscripts and \(\mu\_{cg} = M\_c e\_g \pi\_{cg}\) we have \[Y\_{cg} \sim \operatorname{Poisson}(\bar{d}\_{cg}\, M\_c\, e\_g\, \pi\_{cg}).\]

Back to top

## Footnotes

1. Abhishek Sarkar and Matthew Stephens (2021), “Separating measurement and expression models clarifies confusion in single-cell RNA sequencing analysis,” *Nature Genetics* 53, 770–777. <https://doi.org/10.1038/s41588-021-00873-4>[↩︎](#fnref1)
2. F. William Townes, Stephanie C. Hicks, Martin J. Aryee and Rafael A. Irizarry (2019), “Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model,” *Genome Biology* 20:295. <https://doi.org/10.1186/s13059-019-1861-6>[↩︎](#fnref2)
3. Which goes by the wonderful name *Poissonisation* <https://mpaldridge.github.io/blog/poissonisation.html>[↩︎](#fnref3)
4. Valentine Svensson (2020), “Droplet scRNA-seq is not zero-inflated,” *Nature Biotechnology* 38, 147–150. <https://doi.org/10.1038/s41587-019-0379-5>[↩︎](#fnref4)
5. Laleh Haghverdi, Aaron T. L. Lun, Michael D. Morgan and John C. Marioni (2018), “Batch effects in single-cell RNA-sequencing data are corrected by matching mutual nearest neighbors,” *Nature Biotechnology* 36, 421–427. <https://doi.org/10.1038/nbt.4091>[↩︎](#fnref5)
6. Sources for the datasets below: Replogle et al. (2022), *Cell*. <https://doi.org/10.1016/j.cell.2022.05.013>; Nadig et al. (2025), *Nature Genetics*, GEO GSE264667, <https://doi.org/10.1038/s41588-025-02169-3>; Jiang et al. (2025), *Nature Cell Biology*, <https://doi.org/10.1038/s41556-025-01622-z>; McFaline-Figueroa et al. (2024), *Cell Genomics*, <https://doi.org/10.1016/j.xgen.2023.100487>; Huang et al. (2025), X-Atlas/Orion, *bioRxiv*, <https://doi.org/10.1101/2025.06.11.659105>; Nourreddine et al. (2026), *Nature Biotechnology*, <https://doi.org/10.1038/s41587-026-03199-w>; Zhu et al. (2026), *bioRxiv*, <https://doi.org/10.64898/2025.12.23.696273>.[↩︎](#fnref6)
