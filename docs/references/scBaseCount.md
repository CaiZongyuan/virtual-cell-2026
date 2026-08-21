**<font style="color:rgb(31, 31, 31);">【摘要】构建细胞的虚拟模型</font>**<font style="color:rgb(31, 31, 31);">是人工智能与生物学交叉领域的一个新兴前沿，这一发展得益于单细胞RNA测序数据的快速增长。通过汇总来自数百项研究中数百万个细胞的基因表达谱，单细胞图谱为训练由人工智能驱动的细胞模型奠定了基础。然而，依赖于具有预处理计数的数据集限制了这些资源库的规模和多样性，并将下游的模型训练局限于为不同目的而整理的数据。由于比对工具、基因组参考和计数策略选择上的差异，这引入了分析上的变异性。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在此，我们介绍了 </font>**<font style="color:rgb(31, 31, 31);">scBaseCount</font>**<font style="color:rgb(31, 31, 31);">，这是</font>**<font style="color:rgb(31, 31, 31);">一个不断更新的单细胞RNA测序（scRNA-seq）数据库</font>**<font style="color:rgb(31, 31, 31);">，它利用人工智能智能体驱动的分层工作流程来自动化发现、元数据提取和标准化数据处理。通过直接挖掘和处理所有可公开获取的10X Genomics单细胞RNA测序读取数据，</font>**<font style="color:rgb(31, 31, 31);">scBaseCount是目前最大的公共单细胞数据资源库，包含跨越21种生物和72种组织的超过2.3亿个细胞。</font>**<font style="color:rgb(31, 31, 31);">利用包含单细胞和单核测序数据的研究，我们证明了跨数据集的统一处理有助于减轻由不一致的数据处理选择所引入的分析误差（artifacts）。这种标准化的方法为更准确的虚拟细胞模型奠定了基础，并为广泛的生物学和生物医学应用提供了基石。</font>

# <font style="color:rgb(31, 31, 31);">Introduction</font>
---

<font style="color:rgb(31, 31, 31);">精确测量单个细胞转录组状态的能力改变了细胞生物学的研究。通过揭示细胞在跨物种和组织背景下参与各种过程和功能时的异质性状态，单细胞RNA测序揭示了以前通过批量（bulk）方法无法获得的细胞身份和行为的更精细细节。这些发现极大地影响了从发育生物学到癌症研究的各个领域。更重要的是，这些单细胞数据集不断增长的规模推动了构建细胞的计算机（in silico）模型的努力——即旨在捕捉依赖于背景的细胞功能和行为，并预测细胞对扰动反应的人工智能（AI）模型。在许多方面，构建“虚拟细胞”模型已成为人工智能应用于生物学的一个主要前沿。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在过去十年中，整合跨机构和研究实验室单细胞数据集的兴趣显著增长。诸如人类细胞图谱（Human Cell Atlas）和 CZ CELLxGENE 数据集等著名项目，在扩大经过整理的单细胞RNA测序（scRNA-seq）数据集的可用性方面取得了长足进步。这些努力在增进我们对</font>**<font style="color:rgb(31, 31, 31);">细胞身份、分化轨迹和疾病机制的理解方面发挥了重要作用</font>**<font style="color:rgb(31, 31, 31);">，同时也为</font>**<font style="color:rgb(31, 31, 31);">人工智能驱动的细胞状态建模提供了宝贵的训练数据。</font>**<font style="color:rgb(31, 31, 31);">然而，这些计划主要依赖于研究者提供的（贡献的）数据集，而这只是通过美国国立卫生研究院（NIH）托管的序列读取归档库（SRA）——最大的原始单细胞测序数据资源库——可获取的公开数据的一小部分。虽然目前的方法允许进行更深入的、专家级别的数据集整理和注释，但它也限制了可供分析的数据的规模和多样性——特别是对于通常不依赖于细胞标签的AI模型而言。这凸显了对单细胞基因组学数据整理新方法的需求——这种新方法需要以AI模型训练所需的规模运作，并且不受手动数据集注释的限制。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">现有单细胞数据资源库面临的另一个挑战是，由于比对工具、参考基因组和读取计数策略的差异，来自不同来源的数据集的汇总会引入分析上的变异性。在批量转录组测序（bulk RNA-seq）领域，像Recount计划这样的大规模重新分析工作此前已经证明了标准化流程在最小化这些分析批次效应方面的威力。通过对批量RNA测序数据进行统一的重新处理，Recount为研究人员提供了一个生物学变异不受数据处理流程不一致影响的资源。借鉴这些经验教训，我们认识到需要一个用于单细胞基因组学的类似数据资源库——一个跨越广泛物种和组织，同时坚持一致处理标准的资源库。这样的资源应能实现更可靠的跨研究比较，促进荟萃分析（meta-analyses），并更好地支持旨在模拟跨不同生物学背景下细胞行为的AI驱动研究。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在此，我们展示了 </font>**<font style="color:rgb(31, 31, 31);">scBaseCount</font>**<font style="color:rgb(31, 31, 31);">，这是一个代表了迄今为止最大规模重新处理工作的单细胞基因组学数据资源库。随着SRA上出现新数据，这项工作还将继续扩展。scBaseCount是通过利用人工智能驱动的智能体来自动化资源库识别和元数据统一而构建的，从而能够对原始单细胞RNA测序数据进行持续发现、注释和标准化处理。因此，scBaseCount不仅为AI驱动的建模和综合荟萃分析提供了一个协调一致的大规模资源，而且还保持动态更新，与不断扩大的公开可用单细胞数据领域共同成长。</font>

# <font style="color:rgb(31, 31, 31);">结果</font>
---

## <font style="color:rgb(31, 31, 31);">scBaseCount：一个庞大、多样化且正在积极扩展的单细胞数据资源库</font>


<font style="color:rgb(31, 31, 31);">scBaseCount 是第一个综合性的单细胞数据库，其构建方式是通过直接挖掘序列读取归档库（Sequence Read Archive, SRA）中所有可公开获取的 10X Genomics scRNA-seq 数据，并应用标准化处理流程以改善数据协调性。</font>**<font style="color:rgb(31, 31, 31);">利用人工智能驱动的智能体 SRAgent，我们系统地、持续地识别资源库，统一不同来源的元数据，并促进原始单细胞RNA测序数据的发现、注释和重新处理。</font>**

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">迄今为止，我们的 SRAgent 已识别出63,892个SRA实验（即SRX条目），其中43,587个被标记为10X Genomics 测序文库。结合目前属于 CZ CELLxGENE 的6,059个额外样本，在撰写本文时，我们共识别出49,646个SRX条目。到目前为止，我们已经重新处理了30,387个条目。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">目前，scBaseCount 包含超过2.3亿个细胞，平均每个细胞有7,614个唯一分子标识符（UMI）（图1A）。与CZ CELLxGENE（1.07亿个细胞）和人类细胞图谱（Human Cell Atlas，6500万个细胞）等其他大型单细胞数据资源库相比，在撰写本文时，scBaseCount已经是最大的公开单细胞数据集集合（图S 1A）。scBaseCount 包含来自21种生物和72种组织的数据，与目前最大的资源库CZ CELLxGENE相比，提供了明显更广泛的实验背景（图1B、C和图S1B、C）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775203531578-1276655e-243c-4a50-b568-2a750bd48660.png)

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775203546882-d6006b5e-bd4b-4f5c-9807-68295f729e8a.png)

> **图1 | scBaseCount：最大的跨物种和组织单细胞基因表达公开数据集资源库。**<font style="color:rgb(31, 31, 31);"> (A) 从scBaseCount中随机抽样细胞的UMAP可视化，按组织类型着色。每个面板代表不同的物种：智人（人类；</font>$ N=243,807 $<font style="color:rgb(31, 31, 31);">），小鼠（</font>$ N=249,008 $<font style="color:rgb(31, 31, 31);">），斑马鱼（</font>$ N=501,041 $<font style="color:rgb(31, 31, 31);">），以及黑腹果蝇（</font>$ N=500,877 $<font style="color:rgb(31, 31, 31);">）。(B) scBaseCount与CZ CELLxGENE之间跨物种细胞分布的比较，突显了scBaseCount中更广泛的物种代表性。(C) scBaseCount和CZ CELLxGENE（人类和小鼠）中排名前30的组织（所有哺乳动物）细胞分布的比较，说明了scBaseCount中增加的组织多样性和代表性。(D) 比较scBaseCount中SRAgent自动化的组织注释与CZ CELLxGENE组织标签的混淆矩阵，证明了在大多数情况下的高度一致性。</font>
>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204005985-22c0f8ab-aa15-4cd2-9967-c7f5d31ed519.png)

> **<font style="color:rgb(31, 31, 31);">图S1 | scBaseCount与其他可公开访问的单细胞数据资源库的大小和计数分布比较。</font>**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">(A) 最大的可公开访问单细胞数据资源库中唯一细胞的总数。</font>
>
> <font style="color:rgb(31, 31, 31);">(B-C) 箱线图描绘了scBaseCount（蓝色）和CZ CELLxGENE（红色）排名前30的组织中每个细胞的基因和UMI计数分布。须线表示 </font>$ 1.5 \times IQR $<font style="color:rgb(31, 31, 31);">。对于scBaseCount，数据代表所有哺乳动物；对于CZ CELLxGENE，数据代表人类和小鼠。</font>
>



<font style="color:rgb(31, 31, 31);">除了数据集识别之外，SRAgent还尝试提取每个SRX的关键元数据，包括10X化学试剂版本、细胞与细胞核悬液类型以及相关的疾病和组织。例如，在比较SRAgent的自动化组织注释与CZ CELLxGENE中的注释时，我们发现在大多数情况下，该智能体都能准确提取正确的组织标签（图1D）。这一观察结果与近期证明大型语言模型在细胞类型注释中有效性的研究相一致。虽然细胞状态的人工智能模型在训练期间不依赖于这些标签，但SRAgent执行可靠组织标记的能力增强了人们对其数据整理和注释能力的信心。</font>

## <font style="color:rgb(31, 31, 31);">使用SRAgent自动发现和注释单细胞数据</font>


<font style="color:rgb(31, 31, 31);">为了系统地识别和整合单细胞RNA测序数据集，我们开发了 SRAgent，这是一种利用 LangGraph 围绕大型语言模型（LLMs）和用于查询序列读取归档库（SRA）的专用工具构建的分层智能体工作流程。具体而言，SRAgent采用Re-Act智能体的分层工作流程，异步访问 eSearch、eSummary、eFetch、eLink、NCBI HTML抓取、SRA BigQuery、sra-stat 和 fastq-dump。该工作流程持续挖掘可公开获取的10X Genomics数据集，检索关键元数据（例如生物体、组织、疾病、扰动），并将这些注释存储在关系数据库中（图2A）。这种自动化方法能够快速发现新研究，同时确保元数据整理保持一致且具有可扩展性。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204146407-e5ec6462-9eaf-4c54-b08a-e0003c0f0171.png)

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204151987-adb71633-b5cf-4316-8cba-587afaaae790.png)

> **图2 | scBaseCount中AI驱动的单细胞RNA测序数据整理和标准化处理。**<font style="color:rgb(31, 31, 31);"> </font>
>
> **<font style="color:rgb(31, 31, 31);">(A) SRAgent工作流程</font>**<font style="color:rgb(31, 31, 31);">：一个分层的AI驱动数据处理管道，用于从序列读取归档库（SRA）自动发现数据集和整理元数据。SRAgent系统地查询NCBI工具（如eSearch、eFetch）以识别10X Genomics数据集，检索元数据（如组织类型、文库制备化学试剂），并将结构化注释存储在GCP SQL数据库中。</font>
>
> **<font style="color:rgb(31, 31, 31);">(B) scRecounter处理流程</font>**<font style="color:rgb(31, 31, 31);">：一个基于Nextflow的工作流，用于将原始单细胞测序读取数据处理为基因表达计数矩阵。scRecounter下载测序读取数据并使用STARsolo进行比对，自动检测最佳条形码参数，并生成以h5ad格式存储的协调一致的表达矩阵。过程跟踪通过托管在GCP上的PostgreSQL数据库进行管理。</font>
>
> **<font style="color:rgb(31, 31, 31);">(C) scRecounter使用多种特征注释和多重比对策略来生成各种“细胞×基因”计数表。</font>**<font style="color:rgb(31, 31, 31);">用户可以选择最适合其应用的选项。我们目前在scBaseCount中提供了对所有变体的访问。</font>
>



<font style="color:rgb(31, 31, 31);">SRAgent 部署在GCP Cloud Run上，每个任务使用2个CPU和2 GB内存。为避免超过NCBI API的速率限制，任务每1-5分钟触发一次，每次运行处理3-5个数据集，峰值速率高达每小时300个数据集。SRAgent总共处理了63,892个数据集，其中43,587个被鉴定为10X Genomics测序文库。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">作为本出版物的一部分，我们已将 SRAgent 代码公开。研究界可以访问和利用 SRAgent 来进一步扩大单细胞数据集的发现和整合工作。</font>

## <font style="color:rgb(31, 31, 31);">使用scRecounter进行标准化的数据重新处理</font>


**<font style="color:rgb(31, 31, 31);">为了处理 SRAgent 识别出的 10X Genomics 数据集，我们开发了 scRecounter，这是一个定制的Nextflow处理管道，专为高效和可扩展的单细胞数据重新处理而设计。</font>**<font style="color:rgb(31, 31, 31);">scRecounter 运行在GCP Cloud Run上，任务提交给GCP Batch。为了保持在GCP资源配额限制内，该处理管道每次运行最多处理三个数据集，每三分钟触发一次新的运行。</font>

<font style="color:rgb(31, 31, 31);"></font>

**<font style="color:rgb(31, 31, 31);">由于无法从SRA元数据中可靠地识别特定的10X Genomics化学试剂版本，我们开发了一种简单的算法来实现其自动识别。</font>**<font style="color:rgb(31, 31, 31);">对于每个识别出的数据集，首先通过fastq-dump下载100万个双端读取片段，然后根据有效条形码的数量，利用这些读取片段来确定化学试剂版本和适当的STARsolo参数（10X Genomics细胞条形码版本、UMI长度和链特异性）。随后，使用fasterq-dump下载整个数据集，并使用STARsolo进行比对以生成“细胞×基因”计数表。迄今为止，scRecounter处理管道总共处理了</font>$ 7.7 \times 10^{12} $<font style="color:rgb(31, 31, 31);">条读取数据。</font>

<font style="color:rgb(31, 31, 31);"></font>

**<font style="color:rgb(31, 31, 31);">对于基因注释，我们使用了来自10X Genomics资源库的人类和小鼠参考基因组。</font>**<font style="color:rgb(31, 31, 31);">其他物种的STAR参考序列是使用以下工作流生成的：针对每个物种，选择并下载一个广泛使用的ENSEMBL基因组组装版本。与人类和小鼠的注释一样，我们应用了自定义脚本来过滤每个物种的GTF文件，仅根据其演化支（如哺乳动物、鸟类、真菌）保留相关的生物类型（例如“蛋白质编码（protein-coding）”和“长链非编码RNA（lncRNA）”）。这种过滤确保了只包含可通过单细胞RNA测序测量到的基因，并保持了与10X Genomics注释的一致性。对于STAR参考序列的生成，我们遵循STAR开发者的建议，根据基因组大小调整了genomeSAindexNbases参数（图2B）。这些注释和参考序列均可通过我们的门户网站下载。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在分析单细胞RNA测序数据时，研究人员通常需要在基因模型和计数策略方面做出选择，因为不存在适合所有应用的通用方法。根据具体分析的不同——无论是侧重于标准基因表达定量、可变剪接还是转录动态——不同的基因模型和计数策略可能更为合适。借助 scRecounter，我们的目标是提供一套全面的可能性方案，使研究人员能够为自己的研究选择最合适的方法。为了实现这一目标，scRecounter 提供了多种特征注释策略，包括Gene、Gene-Full、GeneFull_Ex50pAS、GeneFull_ExonOverIntron和Velocyto（参见“方法”部分）。这些模型在处理外显子和内含子区域方面有所不同，允许用户在标准基因计数（GeneFull）、捕获反义转录的扩展注释（GeneFull_Ex50pAS）或专为RNA速率分析设计的基于内含子的定量方法（Velocyto）之间进行选择（图2C）。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">此外，scRecounter在多重比对（multimapping）策略方面非常灵活，该策略决定了如何处理多重比对的读取数据。这些策略包括期望最大化（EM，即以概率方式分配多重比对的读取数据），以及唯一（unique）和均匀（uniform）策略，后者要么仅保留唯一比对的读取数据，要么均匀分配多重比对的读取数据（图2C）。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">通过整合这些多样化的选项，scRecounter确保了scBaseCount保持作为一个多功能资源的地位，能够适应广泛的单细胞RNA测序应用，同时最大程度地减少技术偏差。作为本出版物的一部分，我们也公开了scRecounter的代码。</font>

## <font style="color:rgb(31, 31, 31);">统一的数据重新处理减少了分析混杂因素的影响</font>


<font style="color:rgb(31, 31, 31);">单细胞转录组数据统一处理流程的一个关键优势是，它能够最大限度地减少由分析流程差异引入的技术变异性。为了评估这种效应，我们使用了轮廓评分（silhouette scoring），这是一种量化单个数据点基于给定分类变量聚类效果的指标。轮廓评分的范围从-1到1，较高的值表明细胞在同一类别内更紧密地聚集并且与其他类别分离良好，而较低的值则表明聚类重叠或定义不清。我们应用这种方法来评估各种分类元数据变量如何影响scBaseCount中的基因表达模式。一些因素主要反映生物学变异（例如，组织类型），而其他因素则捕捉了技术和生物学变异的混合（例如，样本悬液类型、文库制备化学试剂或样本ID）。我们的目标是量化基于每个因素的分组在多大程度上塑造了数据集的结构，并促成了观察到的基因表达变异。然而，鉴于数据集过于庞大，我们转而分析了重复抽样的500,000个细胞的子集，并记录了每个子集的轮廓评分。正如预期的那样，在scBaseCount中，文库制备化学试剂和样本悬液类型（单细胞测序与单核测序）等技术因素表现出与组织类型等具有生物学意义的类别相当或更低的轮廓评分（图3A）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204421689-55b1a073-7035-4db5-8a7d-f922feae3600.png)

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204435046-e7f64977-6828-45d6-b027-9d498e379cd6.png)

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204465613-1fa766a4-a94b-4b69-b4fe-988851bbc3f2.png)

> **<font style="color:rgb(31, 31, 31);">图3 | 比较scBaseCount和CZ CELLxGENE中技术和生物学因素对聚类的影响。</font>**
>
> <font style="color:rgb(31, 31, 31);"> </font>**<font style="color:rgb(31, 31, 31);">(A)</font>**<font style="color:rgb(31, 31, 31);"> 针对不同元数据因素，对来自scBaseCount（蓝色）和CZ CELLxGENE（红色）的250,000个细胞的随机子集计算的轮廓评分。较高的评分表明相应因素对数据聚类的影响更大。对于技术因素，评分已相对于每个数据集的平均组织评分进行了归一化。CZ CELLxGENE子集是从20个单独的人类数据集中提取的，分两步下采样至250,000个细胞；而scBaseCount子集是从人类和小鼠的记录中随机抽样的。对生成的对象进行过滤，以保留至少在10个细胞中存在的基因，以及检测到至少30个基因的细胞。在计算轮廓评分（使用scib_metrics包）之前，所有数据集均经过总和归一化、对数转换和PCA处理。这些结果表明，在考虑组织类型的贡献后，与CZ CELLxGENE相比，在scBaseCount中，诸如样本ID、文库制备化学试剂和样本悬液类型等技术因素对聚类的贡献较小，这突显了scBaseCount的统一处理流程如何在保留生物学结构的同时减少了分析的变异性。</font>
>
> **<font style="color:rgb(31, 31, 31);">(B)</font>**<font style="color:rgb(31, 31, 31);"> 对scBaseCount和CZ CELLxGENE中同时包含单细胞和单核数据的共享细胞子集（N = 566,224）进行的主成分分析（PCA）。</font>**<font style="color:rgb(31, 31, 31);">左侧</font>**<font style="color:rgb(31, 31, 31);">：scBaseCount中共享子集的PCA图，按组织类型（顶部）和悬液类型（底部）着色。</font>**<font style="color:rgb(31, 31, 31);">右侧</font>**<font style="color:rgb(31, 31, 31);">：CZ CELLxGENE中同一子集的PCA图，显示单细胞和单核样本在前两个主成分上有更大的分离。</font>
>
> **<font style="color:rgb(31, 31, 31);">(C)</font>**<font style="color:rgb(31, 31, 31);"> 每个数据集中作为组织类型和样本悬液类型（即细胞与细胞核）函数的轮廓评分，证实了样本悬液类型在CZ CELLxGENE中比在scBaseCount中是更强的变异驱动因素，并且组织类型在scBaseCount中得到了更好的保留。</font>
>
> **<font style="color:rgb(31, 31, 31);">(D)</font>**<font style="color:rgb(31, 31, 31);"> 细胞和细胞核在scBaseCount和CZ CELLxGENE的第一个PC（主成分）上的投影分布。正如推土机距离（Earth Mover's Distance, EMD）所测量的，我们观察到在CZ CELLxGENE中细胞和细胞核之间的分离更为明显。</font>
>



<font style="color:rgb(31, 31, 31);">为了进一步说明这一点，我们对CZ CELLxGENE进行了相同的分析，这是最大的公开单细胞RNA测序数据集资源库，由未经过统一处理的预处理数据集组成。我们发现，作为变异的主要生物学来源，组织类型在 scBaseCount中表现出比在CZ CELLxGENE中高得多的轮廓评分。为了评估组织类型所捕获的生物信号之外更多技术因素的贡献，我们将其他因素的轮廓评分相对于组织变量的平均轮廓评分进行了归一化。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在所有技术变量中，CZ CELLxGENE始终表现出比scBaseCount更高的轮廓评分，表明技术变异对其数据集的影响更大。例如，样本ID（在很大程度上等同于scBaseCount中的SRA研究或SRP ID；图S2）在两个数据集中的表现不同：在scBaseCount中，样本ID评分与组织类型相似；而在CZ CELLxGENE中，它们明显更高，这表明针对特定研究的处理引入了更强的批次效应（图3A）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![图S2 | 匹配CZ CELLxGENE集合ID的SRA研究（SRP）数量直方图。 由于在大多数情况下，给定的CZI集合仅关联一个SRP，因此我们选择在图3的数据可视化中将这两个变量视为可比较的。](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775204578482-f188bb2e-050d-429a-9126-c9805d1703b1.png)

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">这种效应对于区分单细胞测序和单核测序的样本悬液类型更为明显。在CZ CELLxGENE中，悬液类型的轮廓评分要高得多。我们认为，这很可能是由于在统计单核数据时，通常同时使用外显子和内含子读取序列（即前体mRNA注释），而单细胞数据通常仅包含外显子读取序列的做法所致。虽然这两种方法本身都没有错，但当整合这两种数据类型时，这种不一致性可能会引入强烈的批次效应。scBaseCount通过保留并报告外显子和内含子的读取计数缓解了这一问题，从而实现了单核和单细胞数据集的更好整合。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">为了进一步检验这种可能性，我们重点关注了表S1中列出的四个共享数据集，它们同时包含单细胞和单核测序数据。我们执行了主成分分析（PCA），并在二维PC空间中对数据集进行了可视化（图3B）。在二维PC空间中，组织类型在scBaseCount中显示出比在CZ CELLxGENE中更高的轮廓评分；反之，样本悬液类型（即细胞与细胞核）在scBaseCount中的评分较低（图3C）。鉴于这两种分析策略在样本制备方面固有的差异，不出所料，PC1主要将单细胞与单核分离开来。然而，我们应进一步强调两个关键观察结果：</font>

1. **<font style="color:rgb(31, 31, 31);">首先</font>**<font style="color:rgb(31, 31, 31);">，与CZ CELLxGENE相比，scBaseCount中由PC1解释的方差有所减少，下降了约4%——从CZ CELLxGENE的15%降至scBaseCount的11%。</font>
2. **<font style="color:rgb(31, 31, 31);">其次</font>**<font style="color:rgb(31, 31, 31);">，正如我们在图3D中所展示的，在CZ CELLxGENE中，细胞和细胞核在PC1上的分离效果比在scBaseCount中更好。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">与scBaseCount中细胞和细胞核之间分离程度降低相一致，对于该数据集的PC1，CZ CELLxGENE的推土机距离（EMD）更高。在这种背景下，较高的EMD表明PC1更强烈地通过技术变异而非有意义的生物学差异来分离基因表达谱，这提示数据处理的选择放大了CZ CELLxGENE中细胞和细胞核之间的差异。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">检查这四个综合数据集的来源出版物，我们发现该子集中的单核数据确实是使用前体mRNA（pre-mRNA）参考进行处理的，而单细胞则是使用标准的外显子参考进行处理的，这是常见的做法（表S1）。在scBaseCount中纠正这一技术误差后，与CZ CELLxGENE相比，前两个主成分上的组织类型分离得更好，这反映在它们各自的轮廓评分中（图3B）。综合来看，这些发现表明，在这一综合数据集的CZ CELLxGENE版本中，超过4%的基因表达变异可归因于数据分析处理的差异，而不是单细胞和单核测序之间的生物学差异。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);"></font>

**<font style="color:rgb(31, 31, 31);">表S1 | 数据集、处理方法和细胞制备技术概述。</font>**

| **<font style="color:rgb(31, 31, 31);">数据集</font>** | **<font style="color:rgb(31, 31, 31);">处理方法</font>** | **<font style="color:rgb(31, 31, 31);">细胞制备</font>** | **<font style="color:rgb(31, 31, 31);">出版物链接</font>** |
| --- | --- | --- | --- |
| <font style="color:rgb(31, 31, 31);">成年和胎儿心脏整合单细胞RNA测序</font> | <font style="color:rgb(31, 31, 31);">样本拆分、细胞识别、比对和计数矩阵生成均使用Cell Ranger 6.1版本进行。</font> | <font style="color:rgb(31, 31, 31);">单细胞，单核 (N=26,972)</font> | [<font style="color:rgb(11, 87, 208);">https://www.nature.com/articles/s44161-022-00183-w</font>](https://www.nature.com/articles/s44161-022-00183-w) |
| <font style="color:rgb(31, 31, 31);">人类肺部的空间分辨图谱刻画了与腺体相关的免疫微环境</font> | <font style="color:rgb(31, 31, 31);">两种类型的文库都比对到了基于Ensembl 93的参考序列（10X提供的GRCh38参考序列，3.0.0版本）。对于细胞核样本，根据10X的说明将参考序列更改为了前体mRNA（pre-mRNA）参考序列。</font> | <font style="color:rgb(31, 31, 31);">单细胞/单核 (N=142,492)</font> | [<font style="color:rgb(11, 87, 208);">https://doi.org/10.1038/s41588-022-01243-4</font>](https://doi.org/10.1038/s41588-022-01243-4) |
| <font style="color:rgb(31, 31, 31);">成年人类心脏的细胞</font> | <font style="color:rgb(31, 31, 31);">单细胞样本针对提供的参考序列进行了比对。对于单核样本，根据10X Genomics说明创建了前体mRNA（pre-mRNA）参考序列。</font> | <font style="color:rgb(31, 31, 31);">单细胞/单核 (N=328,595)</font> | [<font style="color:rgb(11, 87, 208);">https://doi.org/10.1038/s41586-020-2797-4</font>](https://doi.org/10.1038/s41586-020-2797-4) |
| <font style="color:rgb(31, 31, 31);">人类骨骼肌衰老图谱</font> | <font style="color:rgb(31, 31, 31);">使用带有人类参考基因组GRCh38-3.0.0的Cell Ranger (3.1.0) 对基因组骨骼肌测序数据进行了比对和定量。细胞核数据集的比对使用了参考基因组的pre-mRNA版本。使用STARsolo (STAR 2.7.3) 的 </font>`<font style="color:rgb(68, 71, 70);">-soloFeatures Gene GeneFull Velocytow</font>`<br/><font style="color:rgb(31, 31, 31);"> 参数来分离已剪接和未剪接的计数，以区分MF片段。</font> | <font style="color:rgb(31, 31, 31);">单细胞，单核 (N=57,581)</font> | [<font style="color:rgb(11, 87, 208);">https://doi.org/10.1038/s43587-024-00613-3</font>](https://doi.org/10.1038/s43587-024-00613-3) |


_<font style="color:rgb(31, 31, 31);">(注：如上表所示，scBaseCount和CZ CELLxGENE中共享的人类单细胞数据集合，同时包含单细胞和单核测序数据。每个数据集中细胞/细胞核的数量在“细胞制备”列中的括号内显示。对于单细胞核，作者使用了前体mRNA参考进行读取比对，而对于单细胞RNA-seq数据集，则使用了默认的CellRanger mRNA比对。这种分析方法选择上的差异导致了单细胞和单核研究的分离。)</font>_

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">除了协调一致外，scBaseCount中统一的数据处理——包括跨样本对外显子和内含子读取序列的一致处理——还支持额外的下游分析（例如RNA速率分析），以更好地模拟转录动态和细胞状态的转换。如上一节所述，scRecounter也提供了来自Velocyto的剪接和未剪接转录本的细胞×基因计数表。</font>

## <font style="color:rgb(31, 31, 31);">scBaseCount的计划扩展</font>


<font style="color:rgb(31, 31, 31);">迄今为止，scBaseCount一直专注于通过SRA可获取的公开10X Genomics数据集，并计划扩展到更多的单细胞基因组学技术和数据源。目前，scBaseCount包含81个集合（包括1800万个细胞），这些集合与CZ CELLxGENE重叠，而后者本身包含超过6000万个10X Genomics细胞。这些数据集中的一部分源自SRA之外的数据源；例如，我们目前正在整合来自NeMO Archive的700万个细胞。然而，获取大量额外细胞的原始数据需要访问受保护的数据集，这个过程无法大规模自动化，而是需要提交手动申请。尽管面临这一挑战，我们已经开始与作者联系以获取访问权限，并且我们预计scBaseCount中的这一差距将逐渐缩小。展望未来，我们还将把scRecounter扩展到10X Genomics数据之外，以支持额外的单细胞基因组平台，从而进一步拓宽scBaseCount的范围。</font>

# <font style="color:rgb(31, 31, 31);">讨论</font>
---

<font style="color:rgb(31, 31, 31);">在本研究中，我们展示了scBaseCount，这是一个不断更新、统一处理的多物种单细胞RNA测序数据资源库，它是通过直接挖掘所有可公开访问的10X Genomics数据集构建而成的。我们的动机源于需要创建一个大型且高质量的资源，用于训练细胞状态和行为的计算模型。现有的单细胞数据库依赖于人工整理的数据集，这限制了它们的规模和多样性，未能充分利用大量公开可用的转录组数据储备。此外，由于这些数据集处理方式的差异，在这些资源库中整合单个数据集仍然是一项重大挑战。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">通过直接系统地挖掘、注释和处理来自SRA的原始单细胞转录组读取数据，scBaseCount被设计成一个统一的大型单细胞数据集资源库，其分析混杂因素被降至最低。受到展示了统一处理的大批量（bulk）RNA测序数据威力的Recount计划的启发，scBaseCount旨在减少跨研究的技术误差，确保AI模型学到的细胞状态表示是基于具有生物学意义的变异。此外，scBaseCount在所代表的物种和组织背景的多样性方面远远超过了其他单细胞数据库，反映了其包含的表型信息的广度。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">scBaseCount是第一个由AI智能体整理的大型生物数据资源库。我们的自动化工作流由SRAgent AI系统和基于Nextflow的处理管道驱动，确保了所有数据集在元数据整理和分析处理上的一致性。这种智能体工作流的优势在于它完全自动化、易于扩展，并且能够在有新数据可用时持续更新。与许多现有资源不同，scBaseCount通过提供包括外显子和内含子计数在内的多种基因计数选项，减少了对数据处理方式的预设与假设。这种灵活性允许研究人员定制他们的分析，同时支持RNA速率等依赖内含子读取来推断细胞状态转换的下游应用。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">尽管有这些优势，但仍有一些未来的发展方向和挑战需要考虑。</font>

+ **<font style="color:rgb(31, 31, 31);">首先</font>**<font style="color:rgb(31, 31, 31);">，虽然我们的智能体工作流实现了元数据提取的自动化，但某些方面（例如细胞类型注释）可能仍需要人类专业知识、社区来源的整理或将单细胞映射到带注释的参考序列上的额外工具。其他细胞级别的注释（如施加的扰动或供体信息）也无法通过源自SRA的元数据获取，必须手动整合。</font>
+ **<font style="color:rgb(31, 31, 31);">其次</font>**<font style="color:rgb(31, 31, 31);">，在当前版本中，我们专注于使用10X Genomics平台创建并在成熟的Illumina测序仪上测序的文库。随着替代的文库制备化学试剂变得更加普遍，以及测序技术不断发展，我们必须调整scBaseCount以保持对新模式的兼容性，包括各种化学试剂、多组学测量和空间转录组学。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">最终，这个统一、持续更新的资源为旨在建立跨健康与疾病细胞行为整合模型的AI驱动工作奠定了基础。通过提供这个目前最大的、且经过统一处理的公开单细胞数据资源库，我们希望降低研究人员进行大规模计算模型训练和综合分析的门槛。</font>

# <font style="color:rgb(31, 31, 31);">数据和代码可用性</font>
---

## <font style="color:rgb(31, 31, 31);">数据可用性</font>


<font style="color:rgb(31, 31, 31);">所有STARsolo计数矩阵均位于Google Cloud Storage，路径为 </font>`<font style="color:rgb(68, 71, 70);">gs://arc-ctc-scBaseCount/2025-02-25</font>`<font style="color:rgb(31, 31, 31);">。有关访问数据的说明文档可在 </font>[<font style="color:rgb(11, 87, 208);">https://github.com/ArcInstitute/arc-virtual-cell-atlas</font>](https://github.com/ArcInstitute/arc-virtual-cell-atlas)<font style="color:rgb(31, 31, 31);"> 找到。</font>

## <font style="color:rgb(31, 31, 31);">代码可用性</font>


<font style="color:rgb(31, 31, 31);">SRAgent和scRecounter的源代码分别在GitHub上开源：</font>[<font style="color:rgb(11, 87, 208);">https://github.com/ArcInstitute/SRAgent</font>](https://github.com/ArcInstitute/SRAgent)<font style="color:rgb(31, 31, 31);"> 和 </font>[<font style="color:rgb(11, 87, 208);">https://github.com/ArcInstitute/scRecounter</font>](https://github.com/ArcInstitute/scRecounter)<font style="color:rgb(31, 31, 31);">。用于数据分析的代码可在 </font>[<font style="color:rgb(11, 87, 208);">https://github.com/ArcInstitute/scBaseCount_analysis</font>](https://github.com/ArcInstitute/scBaseCount_analysis)<font style="color:rgb(31, 31, 31);"> 获取。</font>

# <font style="color:rgb(31, 31, 31);">方法</font>
---

## <font style="color:rgb(31, 31, 31);">10X化学试剂版本的鉴定</font>


<font style="color:rgb(31, 31, 31);">一旦SRAgent预测某个SRX包含10X Genomics单细胞数据，该数据集就会通过scRecounter处理管道，使用一种受Cell Ranger启发的自动检测算法来确定具体的检测化学试剂版本。为此，使用STARsolo处理每个SRX的前100万条读取序列，测试对应于10X 5'、10X 3' v2、10X 3' v3和10X Multiome GEX的条形码集（未包含10X 3' v1）。选择产生最高比例有效细胞条形码的条形码文件。在此阶段移除了有效条形码少于30%的数据集。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">对于被鉴定为10X 3' v2或10X 5'的数据集（它们共享相同的白名单），在反义链上执行了额外的比对。最终的链分配是通过选择具有较高基因比对百分比的链来决定的，前提是其比对百分比至少是对立链的两倍。这种方法复制了Cell Ranger使用的链检测策略，确保了化学试剂版本的准确鉴定。</font>

## <font style="color:rgb(31, 31, 31);">数据处理</font>


<font style="color:rgb(31, 31, 31);">在确定了正确的10X化学试剂版本后，我们在单次STARsolo运行中，使用以下参数将SRX记录内的所有SRR作为一个文库进行比对和计数：</font>

```plain
--soloType CB_UMI_Simple 
--clipAdapterType CellRanger4 
--outFilterScoreMin 30 
--soloCBmatchWLtype 1MM-multi_Nbase_psuedocounts 
--soloCellFilter EmptyDrops_CR 
--soloUMIfiltering MultiGeneUMI_CR 
--soloUMIdedup 1MM_CR 
--soloFeatures Gene GeneFull GeneFull_ExonOverIntron GeneFull_Ex50pAS Velocyto 
--soloMultiMappers EM Uniform 
--outSAMtype None 
--soloBarcodeReadLength 0
```

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">scRecounter利用STARsolo的 </font>`<font style="color:rgb(68, 71, 70);">--soloFeatures</font>`<font style="color:rgb(31, 31, 31);"> 参数，能够生成针对特定分析需求量身定制的各种计数矩阵：</font>

+ **<font style="color:rgb(31, 31, 31);">Gene</font>**<font style="color:rgb(31, 31, 31);">：计算完全比对到注释转录本外显子区域的读取序列，捕获完全剪接的转录本。该过程代表了传统的基因表达分析，并且是早期CellRanger版本中的默认设置。</font>
+ **<font style="color:rgb(31, 31, 31);">GeneFull</font>**<font style="color:rgb(31, 31, 31);">：计算与整个基因位点重叠的读取序列，即包括外显子和内含子区域。这同时捕获了未剪接（初级）和已剪接的转录本，提供了更全面的基因活动视图。</font>
+ **<font style="color:rgb(31, 31, 31);">GeneFull_ExonOverIntron</font>**<font style="color:rgb(31, 31, 31);">：计算与外显子和内含子区域重叠的读取序列，但对外显子重叠赋予更高的优先级。此选项有助于解决比对到重叠基因的读取序列。</font>
+ **<font style="color:rgb(31, 31, 31);">GeneFull_Ex50pAS</font>**<font style="color:rgb(31, 31, 31);">：与上述选项类似，但采用了更复杂的优先级方案，该方案将部分和反义外显子重叠的优先级置于内含子读取序列之上。</font>
+ **<font style="color:rgb(31, 31, 31);">Velocyto</font>**<font style="color:rgb(31, 31, 31);">：遵循相关既定规则，生成用于剪接、未剪接和模糊读取的独立计数矩阵。这支持利用RNA速率分析以推断动态的细胞过程。</font>

## <font style="color:rgb(31, 31, 31);">重新处理CZ CELLxGENE中的数据集</font>


<font style="color:rgb(31, 31, 31);">我们获取了对应于CZ CELLxGENE集合的记录代码，并使用上述方法重新处理了相应的SRX。然后，使用唯一的 </font>`<font style="color:rgb(68, 71, 70);">GeneFullEx50pAS</font>`<font style="color:rgb(31, 31, 31);"> 计数，将每个集合中包含的SRX组装成每个集合一个h5ad对象。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">接着，我们通过匹配细胞条形码，将每个CZ CELLxGENE集合的观测元数据映射到我们重新处理的集合中。具体而言，在每个集合内，细胞条形码遵循 </font>`<font style="color:rgb(68, 71, 70);">[ATCG]-[10x_well_id]</font>`<font style="color:rgb(31, 31, 31);"> 的格式，而我们经STARsolo处理的数据也遵循相同的格式。因此，对于每个集合，我们通过将每个标识符分配给能够最大化相交条形码数量的对应CZ CELLxGENE标识符，从而将该集合CZI版本中的 </font>`<font style="color:rgb(68, 71, 70);">10x_well_ids</font>`<font style="color:rgb(31, 31, 31);"> 映射到我们的数据中。通过使用这种方法，我们成功地将CZ CELLxGENE集合中的元数据映射到scBaseCount中。</font>

## <font style="color:rgb(31, 31, 31);">评估CZ CELLxGENE和scBaseCount中的分析因素</font>


<font style="color:rgb(31, 31, 31);">为了评估悬液类型对数据结构的贡献，我们选择了CZ CELLxGENE和scBaseCount集合之间共享的四个同时包含单细胞和单核数据的人类数据集。我们使用 </font>`<font style="color:rgb(68, 71, 70);">observation_joinid</font>`<font style="color:rgb(31, 31, 31);"> 和 </font>`<font style="color:rgb(68, 71, 70);">cell_type</font>`<font style="color:rgb(31, 31, 31);"> 的组合作为唯一的细胞标识符，在CZ CELLxGENE中识别出匹配的细胞。我们排除了具有少于100个独特基因的细胞，以及在少于40个细胞中观察到的基因。随后对生成的数据集进行了总和归一化（sum-normalized）和对数转换。使用50个主成分（PC）进行主成分分析（PCA），并使用scanpy对前两个主成分进行可视化。使用 </font>`<font style="color:rgb(68, 71, 70);">scib_metrics</font>`<font style="color:rgb(31, 31, 31);"> 包计算轮廓评分。</font>

## <font style="color:rgb(31, 31, 31);">数据集下采样 (Subsampling)</font>


<font style="color:rgb(31, 31, 31);">对于CZ CELLxGENE，每个下采样数据包含来自20个项目的样本，其中所有项目均仅为10X检测，并在CZI元数据中被标记为 </font>`<font style="color:rgb(68, 71, 70);">primary_data</font>`<font style="color:rgb(31, 31, 31);">。每个数据集在合并前均被下采样至原始规模的30%。随后根据需要，将每个样本进一步下采样至250,000个细胞。对于scBaseCount，我们从随机选择的SRX记录中提取 </font>`<font style="color:rgb(68, 71, 70);">GeneFullEx50pAs</font>`<font style="color:rgb(31, 31, 31);"> 计数，并将它们拼接在一起，直到对象达到250,000个细胞。在这两种情况下，子集中一半是小鼠数据，一半是人类数据。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);"></font>

