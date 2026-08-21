**<font style="color:rgb(31, 31, 31);">【摘要】</font>**<font style="color:rgb(31, 31, 31);">单细胞转录组学为测量跨物种、疾病和其他生物学条件的细胞表型多样性带来了希望。最近，涌现出了用于识别这种变异的基础模型。然而，尽管技术限制降低了单细胞水平的测量精度，但大多数方法仍然将每个细胞进行独立表示。在这里，我们提出了Stack，这是一个在1.49亿个经过统一预处理的人类单细胞上训练的基础模型，它利用表格注意力（tabular attention）机制，根据上下文中的细胞信息来生成每个细胞的表征。与基线模型（无论是零样本、微调过的，还是在目标数据集上从头训练的模型）相比，Stack在零样本设置下的下游任务中提供了实质性的改进。Stack能够从代表任意条件（如化学微扰或不同供体）的无标签细胞中进行上下文学习（in-context learning），并预测这些条件对目标细胞群的影响，而无需针对特定数据进行微调。我们应用Stack生成了Perturb Sapiens，这是第一个人类全生命体微扰细胞图谱，涵盖了28个组织、40种细胞类别和201种微扰。我们使用体外刺激谱验证了Perturb Sapiens的子集。总的来说，Stack提出了一种新的建模框架，在推理阶段，细胞本身充当指导示例，从而解锁了单细胞生物学中通用的上下文学习能力。</font>

# <font style="color:rgb(31, 31, 31);">引言</font>
---

<font style="color:rgb(31, 31, 31);">大规模单细胞RNA测序的出现产生了前所未有的海量细胞数据，目前收集的数据量已超过数亿个细胞，涵盖了各种组织和条件。数据的爆发式增长推动了单细胞基础模型的发展，这些模型利用自监督学习从海量数据集中提取有意义的细胞表征。随后，这些模型被微调并用于各种下游任务，如细胞类型注释、批次整合和微扰效应预测。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">尽管前景广阔，但目前的单细胞基础模型在生物学发现能力方面面临着显著的局限性。当以零样本方式使用时，它们往往无法超越经典方法。即使进行了特定数据集的微调，它们在微扰预测方面也很难比简单的基线模型表现更好。最近的模型在这些能力上显示出了改进；然而，它们仍然需要大量的训练数据以及针对生物学条件和目标任务的监督。这限制了它们在从头（de novo）生物学发现方面的潜力，例如在新的生物学条件中推断微扰效应（例如，仅有观测数据的未见细胞类型），或执行新颖的任务，如预测免疫表型中样本特异性的变异。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">目前大多数单细胞基础模型都受到基本设计选择的制约。首先，它们的预训练目标在单细胞水平上运作，将模型训练为利用基因依赖性的通用“降噪器”，但无法看到群体尺度的变化。其次，基因表达谱固有的嘈杂计数分布需要跨细胞聚合信息，以提高基因表达模式的信噪比。这一见解已被State应用于微扰效应预测，但在单细胞基础模型中仍未得到充分探索。这种聚合对于编码细胞间相互作用或互信息也是必不可少的，否则这些信息将被忽略或错误地归因于基因水平的依赖性。第三，先前的模型主要通过在有限数据上进行特定任务的微调来应用于下游任务，而不是利用基于Transformer的大型模型在推理时执行稳健学习的已知能力。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">为了解决这些局限性并推动细胞基础模型超越其监督训练条件和任务的泛化能力，我们开发了Stack，这是一个自监督框架，通过在细胞集上的新颖架构实现上下文学习。在 scBaseCount（现有的最大的单细胞集合，包含1.89亿个高质量人类细胞）上进行预训练后，Stack引入了几个关键创新。受近期表格深度学习进展的启发，该架构采用了定制的Transformer模块，同时兼顾了细胞间和细胞内的信息流。一种新颖的预训练目标可防止简单的记忆捷径，同时保持单细胞分辨率。其他改进还包括在潜在空间中强制实现线性可识别性以获得更好的泛化能力，以及一个用于提高可扩展性的高效数据加载器。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在预训练之后，Stack 展示了在推理阶段自动利用细胞上下文信息来完善嵌入表示和实现多项下游任务的能力，甚至对于在训练期间从未遇到过的数据集也是如此。通过广泛的评估，我们表明，与各种基线模型（无论是零样本、经过微调的，还是在评估数据集上从头训练的）相比，这种特性使得在零样本细胞分类和整合任务上的性能得到了显著提高。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">除了利用细胞的上下文来增强其嵌入表征外，我们还可以</font>**<font style="color:rgb(31, 31, 31);">通过设计细胞的上下文来影响其状态</font>**<font style="color:rgb(31, 31, 31);">。通过一种新颖的后训练对齐程序，Stack为单细胞基础模型引入了上下文学习（ICL）。</font>**<font style="color:rgb(31, 31, 31);">通过在来自CellxGene的包含5500万个细胞的注释集合和Parse外周血单核细胞（PBMC）微扰数据集上进行后训练，Stack学会在细胞维度上发挥类似于掩码扩散模型（masked diffusion models）的条件生成模型的作用。</font>**<font style="color:rgb(31, 31, 31);">这种对齐实现了“细胞提示（cell prompting）”任务，</font>**<font style="color:rgb(31, 31, 31);">其中Stack接受两个分别被称为提示（prompt）和查询（query）的细胞群，并预测查询细胞群在提示所代表的条件下的表现。</font>**<font style="color:rgb(31, 31, 31);">该框架支持各种通用任务，例如微扰效应预测和特定条件下的细胞谱生成，并同时支持将受微扰的细胞和观测细胞作为提示。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">我们的评估显示，在后训练之后，Stack 可以在完全未见的数据上生成未见过的、特定于上下文或微扰的细胞类型，而无需进行针对特定数据的微调。在微扰效应预测和表达谱生成基准测试中，Stack的零样本性能在31个测试案例中的28个超过了所有评估的强大基线模型。</font>**<font style="color:rgb(31, 31, 31);">我们利用Stack的独特能力创建了第一个人类全生命体受微扰细胞图谱Perturb Sapiens，它涵盖了201种药物和细胞因子微扰下的28个组织和40种细胞类别。Perturb Sapiens 揭示了全生命体不同细胞类型中真实的细胞反应。</font>**<font style="color:rgb(31, 31, 31);">Perturb Sapiens 中特定于细胞类型和组织的微扰效应使用现有的体外细胞因子刺激数据集得到了验证。</font>

# <font style="color:rgb(31, 31, 31);">结果</font>
---

## <font style="color:rgb(31, 31, 31);">Stack 利用细胞上下文学习跨数据集和任务泛化的细胞表征</font>


<font style="color:rgb(31, 31, 31);">Stack 是一种大规模自监督的编码器-解码器模型架构，旨在</font>**<font style="color:rgb(31, 31, 31);">从单细胞数据集合中学习细胞和基因之间的基本依赖关系。</font>**<font style="color:rgb(31, 31, 31);">我们</font>**<font style="color:rgb(31, 31, 31);">在人类 scBaseCount 数据集上对 Stack 进行了预训练，这是目前最大的可用人类单细胞数据集合，经过严格的质量控制后包含 1.89 亿个细胞</font>**<font style="color:rgb(31, 31, 31);">（见方法）。</font>**<font style="color:rgb(31, 31, 31);">训练数据集包含 19,978 个 SRX 样本和 1.49 亿个细胞，剩余的 20% 数据保留用于验证和测试（图 1A，方法）</font>**<font style="color:rgb(31, 31, 31);">。我们</font>**<font style="color:rgb(31, 31, 31);">高质量的训练集比 scGPT 和 Geneformer 的训练集大四倍以上，比 UCE 的训练集大三倍以上</font>**<font style="color:rgb(31, 31, 31);">。为了加速模型训练，我们开发了一个基于 h5py 的高效数据加载器，它为每个单细胞数据样本读取连续的数据块并缓存细胞索引集（图 1A，方法）。该数据加载器实现了高输入管道吞吐量（约 </font>$ 1.6 \times 10^4 $<font style="color:rgb(31, 31, 31);"> 个细胞/秒，比类似模型快 75 倍以上），足以让 GPU 计算饱和，并在单张 H100 GPU 上于 2-3 天内完成预训练。</font>

<font style="color:rgb(31, 31, 31);"></font>

**<font style="color:rgb(31, 31, 31);">Stack 的输入是来自单个实验样本的细胞集合（或称细胞集）</font>**<font style="color:rgb(31, 31, 31);">。我们将每个细胞的上下文定义为其所在集合中的其余细胞。Stack 利用矩形掩码预训练任务，这可以防止模型走简单的插补捷径，并强制保持单细胞级别的分辨率。在一个小批量（mini-batch）中，会对所有细胞随机采样的一组基因进行掩码屏蔽。模型被训练用于重建每个单个细胞的基因表达分布。掩码率从均匀分布中采样以增强特征学习（图 1A）。</font>**<font style="color:rgb(31, 31, 31);">预训练后，Stack 能够为新的单细胞数据集输出细胞级嵌入和基因表达，以零样本的方式为观察性和微扰生物学中的众多应用提供支持</font>**<font style="color:rgb(31, 31, 31);">（图 1A），而无需针对测试数据进行特定的微调。Stack 通过其推理阶段的学习能力获得了强大的零样本能力，这将在后文详细说明。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775211397625-b5429e70-46cd-4a91-a46a-620622ccecc1.png)

> <font style="color:rgb(31, 31, 31);">图 1 | Stack：利用细胞上下文的单细胞基础模型。  
</font><font style="color:rgb(31, 31, 31);">A. Stack 模型概述。</font>**<font style="color:rgb(31, 31, 31);">Stack 将 scBaseCount 的人类单细胞数据作为输入，经过预处理和过滤后，包含来自 19,978 个 SRX 文件的 1.49 亿个细胞。</font>**<font style="color:rgb(31, 31, 31);">每个文件被分成固定大小的连续细胞集作为模型输入。</font>**<font style="color:rgb(31, 31, 31);">在预训练期间，通过在具有可变掩码率的所有细胞中屏蔽随机的基因子集，来对每个输入细胞集进行加噪。</font>**<font style="color:rgb(31, 31, 31);">预训练后，Stack 支持零样本嵌入分析和在设计的提示语指导下广泛的下游任务。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

**<font style="color:rgb(31, 31, 31);">Stack 将每个细胞的潜在状态抽象为标记（token）向量的集合，我们称之为“基因模块标记（gene module tokens）”</font>**<font style="color:rgb(31, 31, 31);">。</font>**<font style="color:rgb(31, 31, 31);">这些标记是通过使用单层感知机将基因表达向量投影到潜在空间来生成的，为每个细胞生成固定数量的标记。这种标记化（tokenization）模块与模型的其余部分一起进行端到端训练，不依赖外部基因语义信息。</font>**<font style="color:rgb(31, 31, 31);">据我们所知，</font>**<font style="color:rgb(31, 31, 31);">Stack 是第一个在基因组（gene-group）级别引入可训练标记化的单细胞基础模型。由于标记的数量（100 个）大大小于数据中的基因数量，模型必须隐式地学习有意义的基因分组以保留生物学信息。</font>**<font style="color:rgb(31, 31, 31);">与基因级别的标记化相比，这也带来了实质性的可扩展性收益。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">Stack 的一项关键创新是一种新的表格 Transformer 模块（tabular transformer block），</font>**<font style="color:rgb(31, 31, 31);">它使细胞集内的细胞内 (intra-cellular) 和细胞间 (inter cellular) 信息流成为可能（图 1B）</font>**<font style="color:rgb(31, 31, 31);">。每个模块堆叠了一个细胞内多头注意力（MHA）层、一个细胞间多头注意力层和一个逐标记的前馈网络（FFN）层。在细胞内 MHA 层中，注意力机制在每个细胞的基因模块标记序列上独立执行。在细胞间 MHA 层中，注意力机制在细胞集上执行，其中“细胞标记”定义为所有基因模块标记的拼接。我们的设计从新兴的表格学习架构（如 TabPFN 和 TabICL）中汲取灵感，并额外考虑了跨细胞的不同基因模块之间的注意力。最终层的基因模块标记被拼接起来形成细胞嵌入，一个逐细胞的多层感知机（MLP）解码器将观察到的基因表达建模为该嵌入的概率函数。除了掩码基因重建目标之外，Stack 还结合了一种分布正则化（distributional regularization），强制将细胞嵌入分解为每个细胞集的常数加上标准正态分布的样本（见方法），这符合非线性潜在变量模型的线性可识别性条件。</font>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775211420064-f0d539c0-4e4a-4d60-9ef0-aecf800605d1.png)

> <font style="color:rgb(31, 31, 31);">图 1 | Stack：利用细胞上下文的单细胞基础模型。</font>
>
> <font style="color:rgb(31, 31, 31);">B. Stack 的预训练。Stack 采用单层多层感知机（MLP）将细胞投影到一组基因模块标记中。这些标记穿过表格注意力架构，该架构沿着基因和细胞维度迭代应用多头注意力（MHA），然后是前馈网络。经过 </font>$ N $<font style="color:rgb(31, 31, 31);"> 个表格注意力模块后，最终的标记被拼接并展平为每个细胞的一维向量（嵌入），解码器将嵌入投影回表达空间（见方法）。</font>
>
> <font style="color:rgb(31, 31, 31);">C. Stack 的推理阶段学习。模型接受单个查询细胞集或提示与查询细胞集的拼接作为输入。Stack 通过表格注意力架构执行上下文学习，并且可以输出以提示为条件的基因表达。</font>
>



**<font style="color:rgb(31, 31, 31);">在预训练期间，该架构捕获了每个细胞与其上下文（细胞集的其余部分）之间的依赖关系，从而能够更好地控制和优化预测的单细胞表达。在后训练程序之后，它还允许使用人工设计的提示细胞集来修改感兴趣的细胞集（查询集），该提示细胞集隐式编码了辅助条件信息以指导最终的模型输出。</font>**<font style="color:rgb(31, 31, 31);">此输出包含每个目标细胞的嵌入和预测的表达值（图 1C）。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">该框架在推理阶段提供了两个主要优势：</font>

1. <font style="color:rgb(31, 31, 31);">预训练期间编码在细胞间注意力层中的细胞集内的细胞依赖关系，可泛化至未见的数据集，从而在不更新模型的情况下提高零样本性能；</font>
2. <font style="color:rgb(31, 31, 31);">它为上下文学习提供了骨干网络，在推理时实现了“细胞提示工程（cell prompt engineering）”。具体而言，可以改变上下文以获得查询细胞的所需结果，例如改变基因表达以匹配新供体或预测微扰的影响。细胞提示可以从任何单细胞观察或微扰数据集中获得，在统一的转录组空间中提供多种条件信号（如疾病状态、遗传/化学微扰、供体变异性、年龄）的高质量表征。</font>

<font style="color:rgb(31, 31, 31);">在提示上下文中模拟查询数据不仅能够泛化到新的生物学上下文（细胞类型、供体等），还能执行训练中未遇到过的新预测任务（如微扰、年龄等）。两者均仅依赖于推理阶段提示提供的信息。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775211431344-d7be9072-396b-42da-a4c7-6e841064f42c.png)

> <font style="color:rgb(31, 31, 31);">图 1 | Stack：利用细胞上下文的单细胞基础模型。  
</font><font style="color:rgb(31, 31, 31);">D. 在不同的 Stack 设置下，唯一细胞数量对验证重建损失的影响。此处展示的所有 Stack 模型均使用相同的训练集和验证集在 scBaseCount 子集上进行训练（见方法）。  
</font><font style="color:rgb(31, 31, 31);">E. 基因本体（GO）生物过程基因集富集分析中调整后 p 值的热图，显示了在完整的人类 scBaseCount 上预训练后，每个 Stack（Large）标记的前 10 个最重要基因（按标记化权重大小排序）。模块和通路名称以及其他绘图详细信息见图 S2。</font>
>



<font style="color:rgb(31, 31, 31);">为了进行模型评估，我们还在包含 7370 万个人类细胞的 CELLxGENE 集合版本、包含 6000 万个细胞的人类 scBaseCount 子集以及完整的 scBaseCount 上训练了 Stack。我们观察到：</font>

+ <font style="color:rgb(31, 31, 31);">在 6900 万到 6.29 亿个参数的 Stack 配置中，各种验证指标都呈现出扩展行为（scaling behavior）（图 S1A）。</font>
+ <font style="color:rgb(31, 31, 31);">增加隐藏层维度会带来验证性能的整体提升。增加网络深度会产生类似的验证损失，但会提高完整 scBaseCount 数据集上其他指标的性能，同时对 scBaseCount 子集表现出混合效应（图 S1B）。</font>
+ <font style="color:rgb(31, 31, 31);">将细胞集大小扩展到 256 可优化验证损失，而在测试值中，验证重建指标在细胞集大小为 128 时达到峰值（图 S1C）。一项消融研究证实，Stack 中的细胞间注意力和潜在空间正则化均可改善验证指标（图 S1D）。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">为了评估包含丰富信息的细胞上下文的影响，我们在通过重复操作以保持总上下文大小不变的情况下，改变了每个细胞集的唯一细胞数。一旦集合中的唯一细胞数超过 32，Stack 的表现就优于没有细胞间注意力的消融模型。较大的 Stack 模型实现了更低的验证损失，并且随着唯一细胞数的增加，收益差距进一步扩大，表明信息聚合能力增强（图 1D）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775213841182-5602ad9c-080d-41b6-bdd7-680b0218179b.png)

> <font style="color:rgb(31, 31, 31);">图 S1 | Stack 模型的扩展（scaling）和消融分析。 A. 在完整人类 scBaseCount (Youngblut 等，2025) 上训练的 Stack 模型在不同模型大小下的验证性能。B. 在 scBaseCount 子集上训练的 Stack 模型在不同模型大小下的验证性能。C. 在完整 scBaseCount 数据集上训练的 Stack (Large) 模型在不同细胞集大小下的验证性能。D. 在 scBaseCount 子集上训练的 Stack (Base) 模型在不同消融设置下的验证性能（w.o. latent reg：仅移除潜在正则化；w.o. cell attn：同时移除潜在正则化和细胞间注意力）。A、B 和 D 中的所有模型都使用 256 的细胞集大小。对于验证损失和平均绝对误差 (MAE)，越小越好；对于皮尔逊 r (Pearson r)，越大越好。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">最后，Stack 标记化产生了高度特异性的基因分组。在每个模块的前 10 个基因（按标记化权重大小排序）中，699 个基因中有 526 个（75.3%）仅出现在一个基因模块标记中，尽管我们没有施加明确的稀疏性目标。基因集富集分析证实了这些标记在功能上是连贯的（图 1E，S2）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775213903478-4631f4af-e9e8-4cba-bfd3-1e5e3d11d9b9.png)

> 图 S2 | 在完整人类 scBaseCount 上预训练后，每个 Stack (Large) 标记中前 10 个最重要基因的基因本体 (GO) 生物过程富集分析的调整后 $ p $ 值热图。 基因重要性得分的计算方法是：首先将标记化权重矩阵 W 重塑为 $ \mathbb{R}^{n_{\mathrm{hidden}} \times d_{\mathrm{token}} \times n_{\mathrm{genes}}} $，然后计算每个隐藏模块在标记维度上的平均绝对权重。基于这些重要性得分选出每个模块的前 10 个基因。显示了每个模块排名前 2 的富集通路。行（模块）和列（通路）通过使用欧氏距离的平均连接法进行层次聚类来排序。
>

## <font style="color:rgb(31, 31, 31);">Stack 通过在推理阶段从细胞上下文中学习来生成卓越的嵌入</font>


<font style="color:rgb(31, 31, 31);">为了评估 Stack 嵌入在下游任务中对单个样本的能力（图 2A），我们开发了一个全面的基准测试框架，通过探测（probing）和整合（integration）评估来评估细胞上下文的影响和单细胞水平表征的质量（图 2B-C，方法）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775531991875-2f7a863d-2ad4-4e8f-a0d5-d4c916fc5e20.png)

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775531999922-6147db59-7749-4e9d-bed7-9e898961b68b.png)

> **<font style="color:rgb(31, 31, 31);">图 2 | Stack 嵌入的评估。</font>**<font style="color:rgb(31, 31, 31);">  
</font><font style="color:rgb(31, 31, 31);">A. 在此处呈现的评估中，Stack 作为上下文感知的嵌入模型，处理来自单个样本的查询细胞集。  
</font><font style="color:rgb(31, 31, 31);">B. 探测评估框架的示意图。  
</font><font style="color:rgb(31, 31, 31);">C. 整合评估框架的示意图。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">用于评估的数据集包括：1) 五个观察性样本集合，其中四个代表取自大量供体（38-223 个）的不同组织（肾脏、淋巴结、大脑和肺），以及 Tabula Sapiens 集合；2) 四个大规模微扰数据集，涵盖三种主要的微扰模式（药物：OpenProblems, Tahoe-100M；信号传导：Parse-PBMC 或 Parse；遗传：X-Atlas:Orion 或 Xaira）。LUCA 数据集是 scBaseCount 或 CELLxGENE 训练数据的一部分，而其余评估数据集则不是，因此对应于零样本设置（详见方法）。我们首先通过应用线性和多层感知机（MLP）探测器来评估观察性单细胞数据上的模型嵌入，以预测不同细微程度和分辨率（从疾病和生理状态到细胞类型）的元数据。重要的是，我们的探测方案包含了精心设计的程序，包括平衡的供体细胞数量、供体级别的测试集保留，以及用于正则化超参数优化的组级交叉验证（方法）。这严格测试了模型是否通过自监督学习捕获了能够泛化到保留供体的生物学状态特征。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">我们将 Stack 与一系列在零样本、微调或从头训练设置下生成嵌入的方法进行了比较。这些方法包括高变基因的主成分（PC HVG）、scGPT、UCE、State（State Embedding 或 SE）、TranscriptFormer、在 scBaseCount 子集上预训练并在目标数据集上微调的 scVI（scVI FT），以及在目标数据集上从头训练的 scVI（scVI from scratch）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775532135068-048063e5-cdd9-41ea-ba84-3be837eb2693.png)

> **<font style="color:rgb(31, 31, 31);">图 2 | Stack 嵌入的评估。</font>**
>
> <font style="color:rgb(31, 31, 31);">D. 逐个细胞类型的线性探测结果。探测得分代表平衡准确率（对于分类任务）或皮尔逊 r 值（对于回归任务），该得分首先在所有方法中对每个细胞类型标准化为 [0, 1] 的尺度，然后在所有细胞类型中取平均值。每个数据集的实验数量（等于细胞类型数量）：n = 12, 20, 10, 20。AKI：急性肾损伤。CKD：慢性肾脏病。BCL：B 细胞淋巴瘤。COPD：慢性阻塞性肺疾病。LUAD：肺腺癌。LUSC：肺鳞状细胞癌。NSCLC：非小细胞肺癌。其他类别：肾脏（高血压、糖尿病史），大脑（微小梗死病理、ADNC、Braak 分期、Thal 分期、CERAD 评分、APOE4 状态），淋巴结（LymphoMAP），LUCA（UICC 分期、曾吸烟者）。ADNC：阿尔茨海默病神经病理学改变。UICC：国际抗癌联盟。</font>
>
> <font style="color:rgb(31, 31, 31);">E. 对 4 个微扰图谱中微扰分类的线性探测评估。每个数据集的实验数量（评估的细胞类型）：n = 6, 60（每板 20 个）, 17, 2。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在逐细胞类型的线性探测中，与其他替代方法相比，Stack 在四个观察性数据集的疾病/其他类别上表现出巨大的优势（图 2D，图 S3A）。唯一的例外是对 LUCA 中其他类别的分类，该数据集部分包含在 Stack 和 State（SE）的训练集中，在此任务中 Stack 排名第二，比 State（SE）低 2.2%。为了控制跨细胞类型的信息流，我们构建了一种新的细胞上下文设置，其中每个细胞集中包含的细胞被限制为相同的细胞类型。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632048148-73cda612-8286-4309-801c-2dbe3dfa1e1e.png)

> **图 S3 | 额外的探测评估结果。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">A. 观察性 scRNA-seq 数据上的疾病和生理状态探测性能 (De Boer 等，2021；Li 等，2025；Salcher 等，2022；Gabitto 等，2024)。为每种细胞类型训练一个线性分类器。每个数据集的实验数量：</font>$ \mathtt{n} = 12 $<font style="color:rgb(31, 31, 31);">、20、10、20。完整结果见图 S4。此处展示的所有 Stack 结果均基于一个在完整人类 scBaseCount 上预训练的 (Large) 设置模型。所有面板显示未归一化的原始指标（平衡准确率/皮尔逊 r）的（平均）值。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">尽管优势有所减小，Stack 仍在所有方法中取得了最佳的整体性能（图 S4）。通过打乱细胞顺序来消除这种细胞上下文信息会导致性能显著下降，最终结果与替代方法相似（图 S4）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632108450-6d18360a-cf93-4e66-82ee-1684ca4cb504.png)

> **图 S4 | 使用额外 Stack 设置的逐细胞类型线性探测结果。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">BC：模型在完整的人类 scBaseCount 上训练。CxG：模型在 CELLxGENE 上训练。All Context：Stack 使用默认的按样本分组的数据集，利用每个样本中的所有细胞类型作为上下文。CT Context：Stack 将每个样本按细胞类型分组的细胞作为上下文，为每个组生成一组嵌入，然后将它们拼接形成总嵌入。Full shuffle：评估数据中的细胞顺序被随机打乱，从而有效去除了上下文信息。每个数据集的实验数量：</font>$ \mathtt{n} = 12 $<font style="color:rgb(31, 31, 31);">、10、20、20、6、17、20、20、20、2。</font>
>



<font style="color:rgb(31, 31, 31);">为了排除 Stack 的优势源于信息量更大的细胞类型的简单信息泄漏的可能性，我们进一步评估了在所有方法中表现最佳的整体细胞类型上的探测性能，结果 Stack 的优势依然存在（图 S5）。Stack 嵌入性能与细胞上下文配置之间的关联表明，Stack 的改进源于其从新的细胞上下文中提取信息的能力。</font>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632127166-406b7845-0120-4384-ac28-9a1f5b96623c.png)

> **图 S5 | 每个数据集的线性探测结果，使用每项任务中整体表现最佳的细胞类型。**<font style="color:rgb(31, 31, 31);"> Xaira 的完整结果包含在图 2 中。</font>
>



<font style="color:rgb(31, 31, 31);">在所有四个观察性数据集上进行的 MLP 探测中也观察到了 Stack 类似的优势（图 S3B）。无论是在线性探测还是 MLP 探测中，所有其他先进的基础模型相对于 PC HVG 和在目标数据集上从头训练的 scVI 等基线方法，都没有表现出一致的优势（图 2D、S3、S4）。在细胞类型分类方面，所有方法都表现出高度相似的性能（图 S3C）。性能的微小差异可能是由于细胞类型信号更清晰及其人工注释的性质。</font>**<font style="color:rgb(31, 31, 31);">Stack 具有竞争力的表现表明，上下文感知机制并没有损害 Stack 在单细胞分辨率下的表征能力。</font>**

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632069372-daeb27b2-1e89-444f-8e83-9d351d6623e0.png)

> **图 S3 | 额外的探测评估结果。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">B. 观察性 scRNA-seq 数据上的疾病和生理状态 MLP 探测性能。在数量最多的前 5 种细胞类型上同时训练一个 MLP 分类器。数据集统计见方法部分。</font>
>
> <font style="color:rgb(31, 31, 31);">C. 观察性 scRNA-seq 数据上的细胞类型分类性能。在 Tabula Sapiens 评估中，每个点代表一种组织 (</font>$ \mathrm{n} = 26 $<font style="color:rgb(31, 31, 31);">)。</font>
>



<font style="color:rgb(31, 31, 31);">接下来，我们评估了不同模型在分类化学、信号和遗传微扰方面的性能（图 2E）。Stack 在所有测试的微扰数据集上均优于现有方法，并且是唯一一个始终优于从头训练的 scVI 的模型。值得注意的是，Stack 在区分大规模数据集 Tahoe 和 Parse 中的微扰效应方面显示出实质性的改进，尽管它几乎只在观察性数据上进行训练，但它的表现比最佳的替代方法高出约 100%。在对 Xaira 数据集中的遗传微扰进行分类时，所有方法均显示出较低的绝对性能，这可能是由于测量噪声以及微扰之间基因表达的相似性。</font>**<font style="color:rgb(31, 31, 31);">这些结果表明，聚合上下文信息对于准确预测微妙的生物学状态至关重要。</font>**



<font style="color:rgb(31, 31, 31);">我们还通过 scIB 整合指标评估了观察性数据上不同嵌入对细胞类型保留和供体标签校正的性能。在所有四个观察性数据集中，Stack 排名第一，超过了最佳的替代方案（State (SE)）1.8%（图 S6A）。</font>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632441477-385638db-deb9-4a3f-8214-0726454b9d43.png)

> **图 S6 | Stack 在批次整合上的额外评估结果。** 
>
> D. 不同数量的主成分和 scVI 潜在维度的整合性能比较。基于这些结果，选择了 50 个主成分和 30 个 scVI 潜在维度的结果作为主要的批次整合基准。
>
> E. 数据集标签整合性能比较。由于 BCL 仅涉及单一数据集标签，因此不适用于数据集标签整合评估。替代的基础模型（scGPT、UCE、State (SE) 和 TranscriptFormer）被排除在 Tabula Sapiens 评估之外，因为它们在每种组织的基准测试中性能提升有限。在 B、D 和 E 中，我们将 Stack 应用于整个数据集，而不是一次应用于一个样本。这导致 Stack 的性能出现非常轻微的下降。E 中的数据集整合性能与 A 中显示的供体整合性能非常吻合。
>



<font style="color:rgb(31, 31, 31);">在 Tabula Sapiens 中，Stack 在 25 种组织中的 21 种里优于替代方法（在眼、心、乳腺和子宫中排名第二，在这些组织中从头训练的 scVI 表现最好），展示了跨人类组织的卓越性能（图 2F）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775532167691-f48b5d50-bd64-4405-bda6-9a4639332519.png)

> **<font style="color:rgb(31, 31, 31);">图 2 | Stack 嵌入的评估。</font>**<font style="color:rgb(31, 31, 31);">  
</font><font style="color:rgb(31, 31, 31);">F. Tabula Sapiens 中每个组织的 scIB 评估。此处呈现的所有 Stack 结果均基于在完整人类 scBaseCount 上预训练的（Large）设置模型。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">这种批次整合能力是涌现出来的，因为在训练期间并未对其进行明确的强制要求。扩大 Stack 的训练数据和模型大小均可提升批次整合性能（图 S6B）。UMAP 可视化进一步证实了 Stack 在聚类细粒度细胞状态和整合批次级信息方面的有效性（图 S6C）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632433869-db50a666-f4e4-4a69-b734-50ca277c7a67.png)

> **图 S6 | Stack 在批次整合上的额外评估结果。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">C. 肾脏图谱中 Stack 嵌入的 UMAP 可视化，按数据收集和细粒度细胞类型着色。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在不同模型规模下结果保持相似，并延伸到了数据集标签整合评估（图 S6D-E）。这些结果确立了 Stack 作为一个强大的嵌入模型，它通过利用细胞上下文增强了单细胞数据领域的零样本预测和整合能力。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775632411901-8084b70b-3f50-4731-855b-7adb2580eb68.png)

> **图 S6 | Stack 在批次整合上的额外评估结果。** 
>
> <font style="color:rgb(31, 31, 31);">A. 不同方法在整合供体表达谱和保留细胞类型方面的 scIB 评估 (Luecken 等，2022)。展示的 Stack 结果基于一个在完整人类 scBaseCount 上预训练的 (Large) 设置模型。</font>
>
> <font style="color:rgb(31, 31, 31);">B. 具有不同大小、训练数据和评估数据集的 Stack 的 scIB 批次整合总分。</font>
>

## <font style="color:rgb(31, 31, 31);">Stack 在后训练之后能够利用细胞进行新颖预测任务的上下文学习</font>


**<font style="color:rgb(31, 31, 31);">在预训练期间，Stack 接触到的是来自相同生物学样本（如供体或实验条件）的细胞集，这限制了基础模型在那些“用户为了产生所需细胞状态而主动设计上下文”的任务中的效用。这种局限性类似于为了使预训练的大型语言模型能够遵循用户指令而必须进行监督微调（SFT）和强化学习（RL）一样</font>**<font style="color:rgb(31, 31, 31);">（Wei 等人，2022；Longpre 等人，2023；Ouyang 等人，2022）。</font>

**<font style="color:rgb(31, 31, 31);"></font>**

**<font style="color:rgb(31, 31, 31);">为了教导 Stack 遵循指令，我们定义了一项包含两个细胞群：提示（prompt）</font>****和****<font style="color:rgb(31, 31, 31);">查询（query）的细胞条件化任务。提示细胞指定所需的生物学状态或条件，而查询细胞指定感兴趣的细胞类型。其目标是预测查询细胞的反事实状态，即它们在提示条件下的基因表达谱，涵盖诸如将微扰效应泛化到新细胞类型和跨数据集等任务。</font>**<font style="color:rgb(31, 31, 31);">在这里，</font>**<font style="color:rgb(31, 31, 31);">提示细胞和查询细胞可以来自不同的数据集，包含非重叠的细胞类型，并且它们的注释可能不可用。因此，监督方法不适用于此任务，而具备零样本能力的基础模型则至关重要。Stack 的上下文感知能力使其特别适合这些任务。</font>**

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">我们</font>**<font style="color:rgb(31, 31, 31);">通过自蒸馏开发了一种新颖的后训练方法，以使 Stack 模型适应这项任务。</font>**<font style="color:rgb(31, 31, 31);">这个</font>**<font style="color:rgb(31, 31, 31);">后训练过程与掩码语言扩散模型（Sahoo 等人，2024）密切相关</font>**<font style="color:rgb(31, 31, 31);">，后者的训练目标是在掩码率从 0 到 1 变化的情况下，恢复输入序列中的被掩码标记。在这个过程中，</font>**<font style="color:rgb(31, 31, 31);">来自单个生物学样本的每个细胞集按类型分组并分为两个子集：保持可见的提示细胞，以及被留出的目标细胞（target cells），这类似于掩码扩散模型中的未掩码和被掩码标记。</font>**<font style="color:rgb(31, 31, 31);">在后训练期间，目标细胞会被取自不同生物样本的、类型匹配的查询细胞所替换。然后，以提示细胞为条件，对 Stack 进行后训练以从查询细胞重建被留出的目标细胞。</font>**<font style="color:rgb(31, 31, 31);">通过这个后训练程序，Stack 学会了以提示细胞为条件来预测任何细胞群的反事实状态，从而实现了条件细胞状态生成。</font>**

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">我们使用预训练的 Stack 模型作为教师模型来提取目标细胞的嵌入表征（图 3A）。</font>**<font style="color:rgb(31, 31, 31);">学生 Stack 模型经过优化，用于在嵌入空间和基因表达空间中预测目标细胞的分布，并带有额外的正则化项。教师模型使用学生模型参数的指数移动平均进行更新，使其能够逐步适应新的数据分布，同时保留在预训练期间获得的知识。</font>**<font style="color:rgb(31, 31, 31);">为了计算基因表达空间中的分布匹配以作为训练目标，我们采用了支持重参数化的零膨胀正态分布（zero-inflated normal distribution）近似（见方法）。最后，训练一个多层感知机（MLP）分类器以在嵌入空间中对细胞进行分类，其中较低的得分表明与提示条件具有更大的相似性，因而意味着对生成质量的置信度更高。在推理阶段，该得分会指导一个迭代优化的过程（图 3A，方法）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775532257749-e1b0fa10-d3dd-4099-bbe0-569d1384669f.png)

> **图 3 | 用于上下文细胞提示任务的 Stack 后训练。**<font style="color:rgb(31, 31, 31);">  
</font>**A.**<font style="color:rgb(31, 31, 31);"> Stack 后训练框架示意图。细胞集按细胞类型组织，并分为提示和目标细胞集。在后训练期间，目标细胞被来自不同条件（查询）的类型匹配细胞替换，以作为模型输入。模型学会通过分布对齐和自蒸馏来预测目标细胞的基因表达和嵌入，并由 MLP 分类器指导推理时生成。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

**<font style="color:rgb(31, 31, 31);">在后训练结束后，我们可以将 Stack 作为条件生成模型来模拟新颖的细胞群。在生成过程中，Stack 接收包含拼接的提示数据和查询数据的细胞集。</font>**<font style="color:rgb(31, 31, 31);">Stack 使用 MLP 分类器预测所有查询位置上的基因表达以及它们的得分。在每次迭代中，我们将一部分具有最高置信度的查询细胞的基因表达值替换为模型的预测值。这个过程以迭代的方式进行，并在比例达到零时结束，此时所有查询细胞的基因表达值都被替换为预测值。在整个迭代过程中，输入细胞集中提示数据的比例会逐渐增加，以实现更精细的控制（方法）。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">对于后训练数据，我们整理了一个包含 5500 万个细胞的大型 scRNA-seq 数据集，该集合由一系列大型 CELLxGENE 数据集（</font>$ >50,000 $<font style="color:rgb(31, 31, 31);"> 个细胞，</font>$ >5 $<font style="color:rgb(31, 31, 31);"> 个供体）和 Parse PBMC 10M 数据集组成，后者包含 12 个供体和 90 种细胞因子微扰（图 3B）。这些训练数据侧重于体内（in vivo）细胞类型，特别关注免疫细胞。为了在我们的大型数据集合上进行高效的后训练，我们开发了一个扩展的后训练数据加载器，以最大化感知细胞类型的局部数据分块。我们在涵盖微扰、观察和混合 ICL 任务三个类别的四项下游细胞提示/上下文学习任务中，评估了后训练模型（框 1）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775532330410-4e399f1a-b96d-4641-8917-db6cb368c050.png)

> **图 3 | 用于上下文细胞提示任务的 Stack 后训练。**
>
> **B.**<font style="color:rgb(31, 31, 31);"> 后训练数据概述。训练数据包含来自精心整理的 CELLxGENE 数据集和 Parse PBMC 数据集（12 个供体，90 种微扰）的约 5500 万个细胞。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">我们的评估利用了 cell-eval（Adduri 等人，2025）中提出的关键指标，这些指标可分为伪容积相关性指标（Pearson Delta、DE Spearman LFC）和差异表达（DE）指标（PR AUC、DE 重叠准确率、Spearman 效应量；见方法）。我们还报告了 Jaccard 相似度指标，该指标衡量两个 DE 基因集之间的重叠，并通过它们的并集进行归一化，从而同时对预测的和真实的 DE 基因集大小进行调整（图 S7）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633190949-81cbfa25-4a28-4fdb-95de-09a689d0ba28.png)

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633204158-8ca12e97-3042-40b4-8f21-0975b0661969.png)

> **图 S7 | 细胞提示任务上的额外指标。** 
>
> A. 对 Dong 等人（2023）细胞因子微扰数据集（6 种细胞因子）中跨细胞类型的微扰效应预测评估。
>
> B. 对 OpenProblems 药物微扰数据集 (Luecken 等，2025)（12 种药物）中跨细胞类型的微扰效应预测评估。
>
> C. 跨样本的 T 细胞反应预测评估（7 种细胞因子刺激条件）。
>
> D. 跨五个图谱的供体特异性基因表达生成评估。
>
> E. 跨四个 PBMC 图谱的条件特异性表达生成评估。更多细节见图 3 标题。对于所有分数，数值越高表示性能越好。
>



<font style="color:rgb(31, 31, 31);">当伪容积或 DE 指标不太合适或不适用时，DE 方向匹配和 top-N 处的 DE 精度可作为辅助指标（方法）。对于设置 4（其中目标和查询属于不同的数据集），我们额外评估了 scIB 批次整合指标。可供选择的基线模型包括查询数据本身（输入基线）、提示样本中最近/相同的细胞类型、State（Adduri 等人，2025），以及 Adduri 等人（2025）中确定的两个强大基线模型（PerturbMean/DonorMean，scVI）。对于微扰 ICL 任务，我们采用了一种“合成对照（synthetic control）”方法，即利用提示样本的未受微扰版本来额外预测一个对照图谱，在计算 cell-eval 指标时，该图谱将作为微扰效应预测的参考基准。同样的合成对照程序也应用于最近/相同细胞类型基线和 scVI，从而产生了更强的基线。对于其余任务，Stack 在没有辅助样本的情况下运行，而 DonorMean 和 scVI 基线仍然需要；因此，在这些情况下我们将这些基线称为“预言机（oracle）”。评估数据包括七个在 Stack 预训练或后训练期间从未见过的数据集：1. OpenProblems 药物微扰（Luecken 等，2025），2. 细胞因子刺激（Dong 等，2023），3. 免疫衰老（Wells 等，2025），4. Tabula Sapiens（Consortium* 等，2022），5. 肾脏图谱（De Boer 等，2021），6. 淋巴结 BCL（Li 等，2025），7. 肝脏图谱（Edgar 等，2025）。此外，我们在评估中将 Parse PBMC 数据集（Parse Biosciences，2023）作为提示（而非查询）包括在内。</font>



> ### **框 1. 用于细胞提示的上下文学习（ICL）任务。**
> **• 微扰 ICL（提示是受微扰过的细胞，查询是对照细胞）**
>
> **1. 同一样本中新细胞类型的微扰效应预测：**<font style="color:rgb(31, 31, 31);"> 我们使用随机采样的受微扰细胞类型作为提示，其余细胞类型的对照细胞作为查询。Stack 在查询细胞类型中模拟提示指定的微扰条件（图 3C–E）。  
</font>_示例：给定一个仅 T 细胞受到 IL-6 微扰的 PBMC 样本，我们使用受微扰的 T 细胞作为提示，未受微扰的 B 细胞/单核细胞作为查询，来预测 IL-6 对 B 细胞/单核细胞的影响。_
>
> **2. 新样本中的微扰效应预测：**<font style="color:rgb(31, 31, 31);"> 我们使用单一一种受微扰细胞类型（此处为 T 细胞）作为提示，将不同数据集中另一个供体的对照 T 细胞作为查询。该设置评估模型预测在查询样本中观察到的反应的能力（图 3F）。  
</font>_示例：我们收集了一个新的 PBMC 样本，并想预测 T 细胞如何对 _$ \mathrm{IFN}-\beta $_ 刺激作出反应。我们使用已发表的参考数据集中受 _$ \mathrm{IFN}-\beta $_ 微扰的 T 细胞作为提示，以新样本的对照 T 细胞作为查询。_
>
> **• 观察性 ICL（提示和查询均来自观察性 scRNA-seq 样本的细胞）**
>
> **3. 留出（Hold-out）细胞类型预测：**<font style="color:rgb(31, 31, 31);"> 我们使用来自一个供体的采样细胞类型作为提示，使用同一数据集中另一个供体的非重叠细胞类型作为查询。Stack 预测提示供体中查询细胞类型的表达谱（图 3G）。该设置评估模型捕获观察性数据集中供体特异性表达差异的能力。  
</font>_示例：在一个患者队列中，患者 A 已完成了巨噬细胞和 T 细胞的分析，但由于组织可用性而缺少成纤维细胞。我们使用患者 A 的细胞作为提示，将患者 B 的成纤维细胞作为查询，以插补出患者 A 特异性的成纤维细胞表达。_
>
> **• 混合 ICL（提示和查询来自不同的观察性研究或微扰研究）**
>
> **4. 跨数据集细胞类型生成：**<font style="color:rgb(31, 31, 31);"> 我们使用某一条件下的采样细胞类型作为提示，使用另一数据集中的非重叠细胞类型作为查询，并预测提示样本上下文中的查询细胞类型表达谱（图 3H）。此设置评估模型生成感兴趣的观察性图谱或微扰数据中缺失的细胞类型的能力。  
</font>_示例：使用受药物微扰的 T 细胞和 B 细胞作为提示，独立 scRNA-seq 图谱中的树突状细胞作为查询，我们预测从未被实验微扰过的树突状细胞的微扰反应。_
>

---

<font style="color:rgb(31, 31, 31);">在 Dong 等人（2023）细胞因子刺激数据集的设置 1（跨细胞类型的微扰效应预测）中，Stack 不仅在所有指标上均表现出优势（图 3C，S7），而且如 Pearson Delta 所证明（图 3D），它还能将包括 IL-6 和 </font>$ \mathrm{TNF}-\alpha $<font style="color:rgb(31, 31, 31);"> 在内的细微细胞因子微扰的全局效应泛化到跨细胞类型中。这种整体优势也延伸到了 OpenProblems 药物微扰数据集，该数据集包含在模型预训练或后训练期间未见过的药物条件（图 3E，S7）。在设置 2 中，无论是单一还是组合的细胞因子条件，Stack 在 DE 指标上均优于替代方法（包括观察到的提示 T 细胞微扰效应），但在伪容积指标上表现相似。然而，由于 Parse 和 Dong 等人（2023）在剂量和刺激持续时间上使用了不同的刺激方案，仅凭泛化少数细胞因子（</font>$ \mathrm{TNF}-\alpha $<font style="color:rgb(31, 31, 31);">、IL-6）的微妙效应，会导致所有方法在此处的伪容积和 DE 分数接近于零（图 3F）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775532415685-646a3b5d-92a1-4c01-a4d2-a2c7c757cc6d.png)

> **图 3 | 用于上下文细胞提示任务的 Stack 后训练。**
>
> **C.**<font style="color:rgb(31, 31, 31);"> 对 Dong 等人（2023）细胞因子微扰数据集（6 种细胞因子）中跨细胞类型的微扰效应预测评估。在前四个面板中，每个点代表一个细胞因子条件的平均结果。在最后一个面板中，每个点代表一种细胞类型（B 细胞、髓系细胞、T 细胞）。标题中的百分比代表 Stack 相比最佳非 Stack 基线的平均改进幅度。所有 Stack（零样本）预测都是使用后训练的 Stack（Large）模型通过掩码扩散程序（</font>$ T = 5 $<font style="color:rgb(31, 31, 31);">）生成的。  
</font>**D.**<font style="color:rgb(31, 31, 31);"> Dong 等人（2023）的 Pearson Delta 评估结果（按细胞因子分层）。（续下页）</font>
>
> **E.**<font style="color:rgb(31, 31, 31);"> 对 OpenProblems 药物微扰数据集（Luecken 等人，2025）（12 种药物）中跨细胞类型的微扰效应预测评估。点代表药物条件（前四个面板）或细胞类型（最后一个面板）。  
</font>**F.**<font style="color:rgb(31, 31, 31);"> 跨样本的 T 细胞反应预测评估。Parse PBMC 的每个供体用作提示，而来自（Dong 等人，2023）的供体 a/b 用作查询。每个点代表一个细胞因子条件（7 种单一/组合条件）的平均结果。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在设置 3 中，预言机 DonorMean 在伪容积相关性指标中表现最强，而 Stack 在评估的四个组织中的方向性和 DE 指标上保持领先（图 3G，S7）。值得注意的是，如 scIB 整合和 cell-eval 指标所证明的（图 3H，S7），Stack 在跨数据集生成细胞类型（设置 4）方面表现出了特殊的优势。这种优势可能源于 Stack 预训练期间获得的上下文感知能力，因为在微扰 ICL 任务上从头开始训练的 Stack 表现欠佳（图 S8）印证了这一点。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775541161200-e2923288-0fe5-4b85-8c0c-31901553fbad.png)

> **图 3 | 用于上下文细胞提示任务的 Stack 后训练。**
>
> **G.**<font style="color:rgb(31, 31, 31);"> 跨四个图谱（肾脏：(De Boer 等，2021)；淋巴结：(Li 等，2025)；肝脏：(Edgar 等，2025)；PBMC：(Wells 等，2025)）的供体特异性基因表达生成评估。采样的供体对中非重叠的细胞类型分别作为提示和查询。每个点代表一个评估数据集。  
</font>**H.**<font style="color:rgb(31, 31, 31);"> 跨四个 PBMC 图谱的条件特异性表达生成评估。药物微扰：包含在（Luecken 等人，2025）中所有可用 PBMC 细胞类型表达谱的 15 个条件；衰老：（Wells 等人，2025）中的前 10 个供体；Parse 供体：来自 12 个供体的所有对照 PBS 条件；Parse 微扰：来自供体 1 的前 20 种微扰条件。来自 Tabula Sapiens（Consortium* 等人，2022）的免疫细胞在所有案例中用作查询。每个点代表一个评估案例。对于所有分数，较高的值表示更好的性能。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633292580-d19020ee-0296-40b9-aa8a-9a8a0428d991.png)

> **图 S8 | 从预训练权重进行后训练的 Stack 与从头训练的 Stack 在新细胞类型中的微扰反应预测的比较。** 
>
> A. Dong 等人（2023）数据集上的结果。
>
> B. OpenProblems 药物微扰数据集 (Luecken 等，2025) 上的结果。显示的所有百分比均代表 Stack 相对于从头进行后训练的 Stack 的平均性能提升。
>



<font style="color:rgb(31, 31, 31);">作为一种零样本方法，Stack 在所有 ICL 任务中实现了最强的整体性能，在 31 项评估中的 28 项中排名第一（图 3C-H，S7）。在评估 cell-eval 指标时，“最近/相同细胞类型”的提示细胞成为了一个强大的基线，这在以前的微扰预测研究中尚未得到充分探讨。尽管 State 在提示数据和查询数据上都进行了训练，但在评估的微扰任务中，Stack 在所有指标上均优于 State。这可能是因为 State 旨在用于具有比这里评估的数据量高出几个数量级的监督数据的设置中。Stack 在低数据、跨实验设置中的成功证明了，当监督微调不足时（例如，在询问难以在实验中进行微扰的细胞类型时），它作为基础模型的极高实用性。在跨 ICL 任务中，多步掩码扩散生成程序显示出相对于 Stack 单步预测和其他生成方案的适度优势（图 S9）。Stack 在未见过的提示和查询（Dong 等，2023；Wells 等，2025；Consortium* 等，2022）、新颖微扰（Luecken 等，2025）以及外周血以外的细胞类型和组织（De Boer 等，2021；Li 等，2025；Edgar 等，2025；Sikkema 等，2023）上具备的竞争性能，凸显了我们的方法向先前未遇到的数据集和多样化生物学任务泛化的能力。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633320725-04e81883-bbff-4beb-98d6-afc51936c134.png)

> **图 S9 | Stack 生成过程在细胞提示任务上的评估。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">A. Stack (</font>$ \mathrm{T} = 5 $<font style="color:rgb(31, 31, 31);">) 和 Stack (</font>$ \mathrm{T} = 1 $<font style="color:rgb(31, 31, 31);">) 在 Dong 等人（2023）数据集上跨细胞类型进行微扰效应预测的比较。</font>
>
> <font style="color:rgb(31, 31, 31);">B. Stack (</font>$ \mathrm{T} = 5 $<font style="color:rgb(31, 31, 31);">) 和 Stack (</font>$ \mathrm{T} = 1 $<font style="color:rgb(31, 31, 31);">) 在 OpenProblems 药物微扰数据集 (Luecken 等，2025) 上跨细胞类型进行微扰效应预测的比较。</font>
>
> <font style="color:rgb(31, 31, 31);">C. 跨 Parse PBMC 和 Dong 等人（2023）对个别细胞因子刺激条件的 T 细胞微扰反应预测评估。</font>
>
> <font style="color:rgb(31, 31, 31);">D. 跨五个图谱的供体特异性基因表达生成评估。</font>
>
> <font style="color:rgb(31, 31, 31);">E. 以四个 PBMC 图谱作为提示并以 Tabula Sapiens 作为查询，进行条件特异性表达生成的评估。显示的所有百分比均代表 Stack 生成设置相对于预测设置的平均性能提升。实验数量和分数的定义见图 3 标题。对于所有分数，数值越高表示性能越好。</font>
>

## <font style="color:rgb(31, 31, 31);">Stack 生成了一个虚拟的全生命体微扰图谱</font>


<font style="color:rgb(31, 31, 31);">我们利用 Stack 通过上下文学习（ICL）生成了一个全生命体微扰图谱（Perturb Sapiens），其中使用 Parse 中的 90 种细胞因子微扰和 OpenProblems 中的 111 种药物微扰作为提示（prompt），并将组织平衡后的 Tabula Sapiens 的完整表达谱作为查询（query）（图 4A）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775541294433-b30d02da-6903-4186-a685-0f6ebd641436.png)

> **图 4 | 虚拟全生命体微扰图谱 Perturb Sapiens 的分析。**<font style="color:rgb(31, 31, 31);">  
</font>**A.**<font style="color:rgb(31, 31, 31);"> Perturb Sapiens 概述。我们利用 PBMC 微扰数据集（来自 Parse 的 90 种细胞因子；来自 OpenProblems 的 144 种药物）作为提示，并将 Tabula Sapiens 作为查询（左）。对于每种组织和细胞类型，Perturb Sapiens 包含在药物和细胞因子微扰下模拟的基因表达谱。生成的图谱涵盖 28 种组织和每个微扰条件下的 513,870 个细胞（右）。</font>
>
> **B.**<font style="color:rgb(31, 31, 31);"> 结合细胞因子 ADSF 和 Tabula Sapiens 生成的示例 Perturb Sapiens 的 UMAP 可视化，按组织和细胞类别着色。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">UMAP 可视化展示了 Perturb Sapiens 具有组织特异性和细胞类型特异性表达的单细胞分辨率图谱（图 4B，S10A）。对 MLP 分类器得分的检查表明，不同细胞和组织类型的生成置信度存在差异（图 S10B–C）。在药物和细胞因子微扰示例中，分类器对几种罕见细胞类型（如变移上皮细胞）赋予了低置信度（高对数几率 / logit 值）。我们将后续分析限制在对数几率小于阈值（2.5）的细胞上，这表明其生成置信度较高。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633431064-684ef47c-a6bb-4041-a78f-c0c8b0311e62.png)

> **图 S10 | Perturb Sapiens 的额外分析。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">A. Dactolisib Perturb Sapiens 的 Stack 嵌入的 UMAP 可视化，按组织和细胞类别标签着色。</font>
>
> <font style="color:rgb(31, 31, 31);">B. ADSF Perturb Sapiens 中分类器预测的对数几率 (logit) 值的微小提琴图，按组织和细胞类别分组。</font>
>
> <font style="color:rgb(31, 31, 31);">C. Dactolisib Perturb Sapiens 中分类器预测的对数几率值的微小提琴图，按组织和细胞类别分组。较低的对数几率表示生成置信度较高。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">作为一个代表性示例，我们检查了 Perturb Sapiens 中 IFN-?? 微扰与对照组的影响，以评估模型在提示细胞或与提示相关（免疫）细胞类型中所观察到的效应之外的泛化能力。Stack 生成了具有细胞类型特异性的高度逼真的差异表达图谱（图 4C）。排名前列的差异表达基因（DEG）在提示免疫细胞和生成的免疫细胞之间表现出近乎完美的一致性。值得注意的是，尽管仅使用了 Parse 中的单个供体作为提示，但 Perturb Sapiens 实现了与所有 12 个 Parse 供体的聚合反应更强的一致性，证明了其克服个体实验噪声的能力（图 4C）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775541329116-204b0b1d-093d-4de9-8097-87f9e3ae684d.png)

> **图 4 | 虚拟全生命体微扰图谱 Perturb Sapiens 的分析。**<font style="color:rgb(31, 31, 31);">  
</font>**C.**<font style="color:rgb(31, 31, 31);"> 比较 IFN-?? Perturb Sapiens 与对照组的 Log2 倍数变化热图。显著差异表达的基因以彩色显示；不显著的基因以灰色显示。</font>
>



<font style="color:rgb(31, 31, 31);">已知的 IFN-</font>$ \gamma $<font style="color:rgb(31, 31, 31);"> 下游靶点在各种免疫和非免疫细胞类型（例如 IFIT3、ISG15、CXCL10、CXCL11、IDO1）中被广泛激活。在非免疫细胞群中，IFN-?? 在基质细胞和收缩细胞群中诱导了 CIITA 的表达，同时广泛抑制了细胞外基质和黏附基因（LUM、FBLN1、LAMA4、ITGA8）；这伴随着与 IFN 驱动的炎症重塑相一致的血管重塑特征（EMCN、ANGPT2、CEACAM1、PLAT）。这些基因要么在 Parse PBMC 数据中没有差异表达，要么在提示供体和聚合表达谱之间表现出不一致的表达趋势。这表明 Stack 成功地泛化到了提示数据之外，以捕获特定于非免疫谱系的免疫调节和重塑反应。Dactolisib 的微扰导致了对干扰素刺激基因（ISG）的全局抑制（图 S11），这与 Dactolisib 作为 PI3K/mTOR 抑制剂的已知作用以及之前的分析相一致。此外，非免疫谱系显示出选择性的重塑，骨架/黏附和压力响应程序受到了调节（例如 TUBA1C、FHL1、LAMA2、NINJ1、MT1X）。</font>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633478761-109e621c-6cb7-4f59-9372-499c28259e8e.png)

> **图 S11 | Dactolisib Perturb Sapiens 与对照组的 Log2 倍数变化热图。** 仅彩色显示显著变化的基因，其余显示为灰色。
>



<font style="color:rgb(31, 31, 31);">虽然 OpenProblems 中的大多数药物微扰仅包含 T 细胞谱系，但正如在 proscillaridin-A 和 ketoconazole（酮康唑）的案例中所观察到的那样，Stack 也在所有细胞类型中生成了高质量的预测（图 S12–S13）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633510508-8db42d14-fb71-42a8-a7c1-a7a88a5ab242.png)

> **图 S12 | Proscillaridin-A Perturb Sapiens 与对照组的 Log2 倍数变化热图。**<font style="color:rgb(31, 31, 31);"> 仅彩色显示显著变化的基因，其余显示为灰色。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">Proscillaridin-A 在免疫和非免疫细胞类型中引发了广泛的促炎性、先天样激活程序。非免疫谱系表现出独特的转录重塑，涉及囊泡运输和膜动态（RAB30、STX3、LYST）以及谱系特异性调节因子（CPEB4、PLAGL1、TSC22D1）。值得注意的是，酮康唑在整个 OpenProblems 数据集中表现出明显的供体特异性效应。Perturb Sapiens 有效地在提示供体中捕获了这些个体化的反应，同时对于未检测到供体特异性差异表达的许多基因，它保持了与批量（bulk）表达模式的一致性（图 S13）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633524101-df908147-2847-4d76-9c29-0c7e0c474a7b.png)

> **图 S13 | 酮康唑 (Ketoconazole) Perturb Sapiens 与对照组的 Log2 倍数变化热图。**<font style="color:rgb(31, 31, 31);"> 仅彩色显示显著变化的基因，其余显示为灰色。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">总体而言，药物微扰条件下的排名前列的差异表达基因（DEG）在提示免疫细胞和生成的免疫细胞之间表现出与细胞因子微扰情况相当的强烈一致性，尽管药物 Perturb Sapiens 产生了额外的阳性结果（即提示免疫细胞也表达了模型预测的非免疫 DEG）。为了进行定量验证，我们将 Perturb Sapiens 免疫细胞与来自相同药物/微扰数据集的生物学重复进行了基准测试，评估了它们捕获提示微扰效应的能力。尽管 Perturb Sapiens 产生的 Pearson Delta 得分较低（可能是由于批次效应），但与生物学重复相比，它实现了卓越的 DE 重叠准确率，并且 Perturb Sapiens 的表现在药物和细胞因子微扰中保持一致（图 S14）。这些发现支持了 Stack 能够对不同微扰生成具有生物学意义的、细胞类型特异性的响应，而无需在查询细胞类型中实际观察到任何微扰。</font>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633551492-526f6287-b872-4527-a79e-d68bc6a58a54.png)

> **图 S14 | Perturb Sapiens 免疫细胞与生物学重复的比较。** 
>
> A. 使用供体 2 作为生物学重复对 Parse 细胞因子微扰的评估。
>
> B. 每种细胞因子（$ \mathrm{n} = 90 $）在 Perturb Sapiens 和生物学重复之间的差异表达 (DE) 重叠准确率散点图。
>
> C. 由于每个供体细胞数量有限，使用剩余的两个供体作为生物学重复对 OpenProblems 药物微扰的评估。
>
> D. 每种药物（$ \mathtt{n} = 111 $）在 Perturb Sapiens 和生物学重复之间的 DE 重叠准确率散点图。
>



<font style="color:rgb(31, 31, 31);">接下来，我们定量评估了 Stack 在生成受微扰的非免疫细胞方面的表现，由于体外上皮细胞因子刺激数据集的普遍存在，我们将重点放在了上皮细胞谱系上。我们使用相同的一套 cell-eval 伪容积和 DE 指标，通过直接预测每种细胞因子或功能相似的细胞因子，评估了模型在单细胞或批量数据中重现五种细胞因子（I 型 IFN、IL-13、IL-</font>$ 1\beta $<font style="color:rgb(31, 31, 31);">、TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);">、IL-17A）效应的能力。Stack 在生成上皮特异性 I 型 IFN 反应方面表现出强大的性能，优于生成的免疫细胞类型以及用作提示的 Parse 免疫细胞（图 4D）。值得注意的是，该模型表现出对气道上皮细胞相对于其他上皮亚型的明显偏好，这与体外实验相一致。与 IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);"> 不同，IL-13 是一种主要影响上皮细胞而对免疫细胞作用较弱的细胞因子。尽管在提示中这种信号有限，Perturb Sapiens 仍展示了与体外气道上皮实验的细胞类型特异性一致性，尽管整体得分较低（图 4E）。如在 IL-</font>$ 1\beta $<font style="color:rgb(31, 31, 31);"> 角质形成细胞刺激实验中所观察到的，这种细胞类型特异性也泛化到了其他组织（图 4F）。</font>



![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775541403731-45ec3d96-1726-4415-9918-5792b70a89ad.png)

> **图 4 | 虚拟全生命体微扰图谱 Perturb Sapiens 的分析。**
>
> **D.**<font style="color:rgb(31, 31, 31);"> 使用来自原代气道上皮细胞的单细胞 IFN-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 刺激数据，评估 Perturb Sapiens 上皮细胞的干扰素-</font>$ \beta $<font style="color:rgb(31, 31, 31);">（IFN-??）效应。  
</font>**E.**<font style="color:rgb(31, 31, 31);"> 使用来自原代气道上皮细胞的单细胞 IL-13 刺激数据，评估 Perturb Sapiens 上皮细胞的白细胞介素-13（IL-13）效应。  
</font>**F.**<font style="color:rgb(31, 31, 31);"> 使用来自原代角质形成细胞的大量（bulk）IL-</font>$ 1\beta $<font style="color:rgb(31, 31, 31);"> 刺激数据，评估 Perturb Sapiens 上皮细胞的白细胞介素-1</font>$ \beta $<font style="color:rgb(31, 31, 31);">（IL-1??）效应。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在所有这三个案例中，Perturb Sapiens 均取得了比提示数据更好的性能，且得分按细胞类型相似度排序。没有进行置信度过滤的评估导致了细胞类型特异性的降低，这证实了该过滤程序的必要性（图 S15）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633581671-8c83756f-a985-4bb9-a110-75e4d06cc1d5.png)

> **图 S15 | 没有分类器引导过滤的 Perturb Sapiens 结果。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">A. 使用原代气道上皮细胞的单细胞 IFN-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 刺激数据，评估 Perturb Sapiens 上皮细胞的干扰素-</font>$ \beta $<font style="color:rgb(31, 31, 31);"> (IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);">) 效应 (Koh 等，2023)。</font>
>
> <font style="color:rgb(31, 31, 31);">B. 使用原代气道上皮细胞的单细胞 IL-13 刺激数据，评估 Perturb Sapiens 上皮细胞的白细胞介素-13 (IL-13) 效应 (Koh 等，2023)。</font>
>
> <font style="color:rgb(31, 31, 31);">C. 使用原代角质形成细胞的大块 IL-1?? 刺激数据，评估 Perturb Sapiens 上皮细胞的白细胞介素-1 </font>$ \beta $<font style="color:rgb(31, 31, 31);"> (</font>$ \mathrm{IL-}1\beta $<font style="color:rgb(31, 31, 31);">) 效应 (Swindell 等，2018)。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">对于 IL-17 和 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);">，Parse 提示数据和生成的数据均显示与上皮反应呈负相关（图 S16），后者在一个独立的 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 上皮刺激数据集中得到了重复验证（表 S1）。</font>

<font style="color:rgb(31, 31, 31);"></font>

> **表 S1 | 对 Perturb Sapiens 肠上皮细胞因子反应相对于体外 TNF-**$ _\alpha $** 大块数据的额外评估 (Saito 等，2021)。** 显著性：$ ^{**} p < 0.01 $ ，$ ^{\ddagger}_{\mathstrut} \mathbin{\stackrel{\ddagger}{\sim}} \frac{\beta}{p} < 0.001 $，n.s. 不显著。
>

| <font style="color:rgb(31, 31, 31);">Pearson Delta</font> | <font style="color:rgb(31, 31, 31);">DE Spearman LFC</font> | <font style="color:rgb(31, 31, 31);">DE 方向匹配</font> | <font style="color:rgb(31, 31, 31);">PR AUC</font> | <font style="color:rgb(31, 31, 31);">DE 重叠准确率</font> |
| :--- | :--- | :--- | :--- | :--- |
| <font style="color:rgb(31, 31, 31);">-0.122</font><font style="color:rgb(31, 31, 31);">*</font><font style="color:rgb(31, 31, 31);">*</font><font style="color:rgb(31, 31, 31);">*</font> | <font style="color:rgb(31, 31, 31);">-0.077</font><font style="color:rgb(31, 31, 31);">*</font><font style="color:rgb(31, 31, 31);">*</font> | <font style="color:rgb(31, 31, 31);">0.434</font> | <font style="color:rgb(31, 31, 31);">0.530</font> | <font style="color:rgb(31, 31, 31);">0.267</font> |




<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在进一步调查后，我们发现尽管在包括金属硫蛋白和细胞黏附分子在内的几个 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 反应基因上存在一致性，但 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 抑制了 Parse T 细胞和 Perturb Sapiens 中参与 NF-</font>$ \mathbf{\sigma}\kappa\mathbf{B} $<font style="color:rgb(31, 31, 31);"> 信号传导和 I 型 ISG 程序的基因表达，而在体外上皮数据集中却诱导了这些特征（表 S2）。</font>



> **表 S2 | 在 Perturb Sapiens、Parse T 细胞和体外 TNF-**$ \alpha $** 数据 (Lee 等，2022) 之间显示一致（上部）和相反（下部）趋势的代表性基因。**
>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633656450-896f7f15-69b7-4eb5-8593-964f9ae8be1f.png)



<font style="color:rgb(31, 31, 31);">这种现象与先前记录的 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 的次级信号传导效应一致。总之，我们的结果表明，Stack 可以利用细胞类型和组织特异性模拟受微扰的非免疫细胞，其与真实数据的对齐程度与微扰的效应大小和特定生物学机制相关。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633596288-27d51a2f-84a8-4b8a-9d81-8d0d1b95bdca.png)

> **图 S16 | Perturb Sapiens 在其他细胞因子上的结果。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">A. 使用原代气道上皮细胞的单细胞 IL-17 刺激数据，评估 Perturb Sapiens 上皮细胞的 IL-17 效应 (Koh 等，2023)。</font>
>
> <font style="color:rgb(31, 31, 31);">B. 使用原代肠上皮细胞的大块 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 刺激数据，评估 Perturb Sapiens 上皮细胞的 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 效应 (Lee 等，2022)。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">最后，我们计算了 Perturb Sapiens 中所有可用条件下微扰效应的对数倍数变化和统计显著性，并按细胞类型和组织进行了分层。该框架能够对微扰反应进行多尺度表征，并提供了一种统一的方法来对药物和细胞因子微扰进行分类。在全局尺度上，预测的微扰相似性按照细胞谱系和组织的接近程度一致地聚类（图 S17）。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633610332-6c3f56e4-16b1-407c-b4d3-b7b9df40478c.png)

> **图 S17 | Perturb Sapiens 的全局特征表征。**<font style="color:rgb(31, 31, 31);"> </font>
>
> <font style="color:rgb(31, 31, 31);">A. Perturb Sapiens 中跨细胞类别的平均微扰相似度。</font>
>
> <font style="color:rgb(31, 31, 31);">B. Perturb Sapiens 中 T 细胞跨代表性组织的平均微扰相似度。值代表使用 Fisher z 变换在各微扰间求平均的斯皮尔曼相关性均值。每个节点显示按相关性排名的前三或前两个边缘。</font>
>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在局部尺度上，我们使用独立成分分析（ICA）分解了每种细胞类型和组织拼接后的微扰效应空间，揭示了多样化的反应模块，这些模块按微扰类型分离，而药物和细胞因子之间没有明显的批次效应（图 S18A-C）。对每个独立成分中贡献最大的基因进行检查后，确定 IFN/炎症信号传导为主要的反应轴，其他模块则反映了压力响应和细胞外基质（ECM）重塑通路（图 S18D-F）。总而言之，Perturb Sapiens 提供了跨细胞类型和组织的微扰效应的全面、多分辨率视图，代表了远超本文所分析范围的极其丰富的资源。</font>

<font style="color:rgb(31, 31, 31);"></font>

![](https://cdn.nlark.com/yuque/0/2026/png/1739170/1775633629338-e8d4a4c4-3b22-4822-9a33-4b1785299b59.png)

> **图 S18 | 代表性细胞类型和组织中由 Perturb Sapiens 药物和细胞因子对数倍数变化 (LFC) 导出的独立成分热图。** A. 肾上皮细胞。B. 肺上皮细胞。C. 肺 T 细胞。D. 肾上皮细胞的因子载荷。E. 肺上皮细胞的因子载荷。F. 肺 T 细胞的因子载荷。所有分析均使用 15 个独立成分数量。
>

# <font style="color:rgb(31, 31, 31);">讨论</font>
---

<font style="color:rgb(31, 31, 31);">随着跨组织、物种和疾病的大规模单细胞转录组学谱图的汇编，基础模型为学习超越实验观察数据的通用生物学原理和模式提供了一个令人兴奋的机会。细胞状态的虚拟图谱可以通过揭示那些在实验中难以探测、但可以从现有数据中学到的关系推断出的细胞状态，从而极大地扩展我们对细胞生物学的理解。然而，要实现这一愿景需要能够跨条件和任务稳健迁移的模型。目前大多数现有的模型存在几个局限性：它们通常无法泛化到以前未见过的条件，其表现并不优于专门在这些数据集上进行过微调的方法，并且如果没有经过明确训练就无法执行新任务。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在这里，我们介绍了 Stack，这是一种单细胞基础模型，它利用每个细胞的细胞上下文信息来创建增强的表征。这种设计使 Stack 能够始终优于在每个评估数据集上从头开始训练的模型，据我们所知，这是现有的任何单细胞基础模型都没有观察到的结果，并突显了 Stack 有效利用预训练期间获得的信息的能力。这种对上下文的依赖还促成了一种新颖的能力：通过设计上下文来设计细胞状态。因为上下文可以通过多种方式定义（例如施加的微扰、疾病状态或新供体），所以 Stack 支持推理阶段学习新任务，包括向新的生物学环境和数据集进行零样本泛化。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">通过这种上下文学习的能力，Stack 实现了一种单细胞建模的新方法，</font>**<font style="color:rgb(31, 31, 31);">只需用细胞进行提示即可生成反事实的细胞状态。</font>**<font style="color:rgb(31, 31, 31);">重要的是，Stack 通过消除对微扰标签、细胞类型编码和测试样本特异性对照的依赖，扩展了现有的微扰建模，从而实现了细胞状态的直接、无标签比较，以解析超越分类注释的上下文依赖性响应。这些结果确立了 Stack 作为一种生成式细胞模型，能够预测跨细胞类型、微扰和新供体的未观察到的基因表达，具有加速治疗和药物发现周期的巨大潜力。作为具体演示，我们应用 Stack 生成了 Perturb Sapiens，这是一个涵盖 28 个组织、40 个细胞类别和 201 种微扰的生物体尺度微扰细胞图谱，我们相信该资源将为整个社区带来广泛的价值。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">尽管 Stack 性能强大且具有新颖的功能，但它也有一些局限性，这也为未来的研究提供了机会。当前的模型完全在人类单细胞数据上进行训练。将此框架扩展到多物种应用需要在标记化过程中进行额外的设计，</font>**<font style="color:rgb(31, 31, 31);">以解决跨物种的基因不对齐问题</font>**<font style="color:rgb(31, 31, 31);">。针对罕见细胞类型和弱微扰效应的模型校准仍有待建立，这标志着未来发展的一个重要领域。正如我们在 TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);"> 案例中所观察到的，信号级联可能会引入时间依赖性或次级微扰效应，这可能会使 Stack 预测的解释变得复杂。最后，由于该模型主要在体内（in vivo）细胞类型（特别是免疫细胞）上进行后训练，更复杂的数据清洗和对齐方案可能会改善模型在体外（in vitro）微扰研究和体内观测数据中的泛化能力。</font>

# <font style="color:rgb(31, 31, 31);">方法</font>
---

## <font style="color:rgb(31, 31, 31);">Stack 模型</font>
### <font style="color:rgb(31, 31, 31);">生成过程</font>


<font style="color:rgb(31, 31, 31);">Stack 将细胞 </font>$ k $<font style="color:rgb(31, 31, 31);"> 的状态 </font>$ \mathbf{E}^{(k)} \in \mathbb{R}^{n \times d} $<font style="color:rgb(31, 31, 31);"> 建模为 </font>$ n $<font style="color:rgb(31, 31, 31);"> 个标记（token）向量 </font>$ \mathbf{e}_i^{(k)} \in \mathbb{R}^d $<font style="color:rgb(31, 31, 31);"> 的集合，我们将其称为基因模块标记，因为每个标记代表单细胞中基因变异的一个连贯子集：</font>

<font style="color:rgb(31, 31, 31);"></font>

$ \mathbf{E}^{(k)} = \left[ e_1^{(k)}; e_2^{(k)}; \dots; e_n^{(k)} \right]. \tag{4.1} $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">使用 scVI 模型中考虑的生成过程（Lopez 等人，2018；Gayoso 等人，2022），将展平的状态向量 </font>$ \bar{\mathbf{E}}^{(k)} \in \mathbb{R}^{nd} $<font style="color:rgb(31, 31, 31);"> 与真实基因表达 </font>$ \boldsymbol{x}^{(k)} \in \mathbb{R}^G $<font style="color:rgb(31, 31, 31);"> 关联起来。该生成过程涉及潜在解码变换 </font>$ f $<font style="color:rgb(31, 31, 31);"> 和细胞文库大小标量 </font>$ l^{(k)} \in \mathbb{R} $<font style="color:rgb(31, 31, 31);">。最终的表达计数通过具有均值和离散参数 </font>$ (\boldsymbol{\rho}^{(k)}, \boldsymbol{\theta}^{(k)}) $<font style="color:rgb(31, 31, 31);"> 的负二项（NB）分布来建模：</font>

<font style="color:rgb(31, 31, 31);"></font>

$ \left(\boldsymbol{\rho}^{(k)}, \boldsymbol{\theta}^{(k)}\right) := f \left(\bar{\mathbf{E}}^{(k)}\right) \in \left(\mathbb{R}^G, \mathbb{R}^G\right); \quad \boldsymbol{x}_g^{(k)} \sim \mathrm{NB} \left(l^{(k)} \boldsymbol{\rho}_g^{(k)}, \boldsymbol{\theta}_g^{(k)}\right). \tag{4.2} $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">这种生成过程可以看作是基于 Transformer 的数据建模和 scVI 中考虑的类生物物理模型的混合体。它与这两种策略最普遍的区别总结如下：</font>

+ <font style="color:rgb(31, 31, 31);">Stack 不像 scVI 模型那样考虑低维潜变量；细胞标记的总维度 </font>$ nd \sim 10^3 $<font style="color:rgb(31, 31, 31);">，这与大型语言模型和大规模单细胞自监督学习模型（Cui 等人，2024；Rosen 等人，2023；Adduri 等人，2025）相当。</font>
+ <font style="color:rgb(31, 31, 31);">Stack 不包含像几种经典（单细胞）Transformer 模型（Devlin 等人，2019；He 等人，2022；Rosen 等人，2023；Adduri 等人，2025）中的结构标记（例如 CLS 标记）。对于下游微调或嵌入上的线性探测，所有输出标记的拼接被用作 Stack 模型的嵌入输出。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">该生成过程对应于从细胞状态嵌入到基因表达的模型解码过程，并在细胞之间独立运行。</font>

### <font style="color:rgb(31, 31, 31);">Stack 架构</font>


<font style="color:rgb(31, 31, 31);">在预训练期间，Stack 模型接收一个细胞集 </font>$ \mathbf{X} \in \mathbb{R}^{K \times G} $<font style="color:rgb(31, 31, 31);">，其中 </font>$ K $<font style="color:rgb(31, 31, 31);"> 表示细胞数量，</font>$ G $<font style="color:rgb(31, 31, 31);"> 表示基因总数。细胞集包括来自同一 SRX 实验（针对 scBaseCount（Youngblut 等人，2025））或同一数据集（针对 CELLxGENE（Program 等人，2025），其中数据集中的细胞主要按供体 ID 排序）的连续索引的细胞。每个细胞集的组织结构引入了细胞集内细胞之间的依赖关系，这可作为丰富的辅助信息。Stack 使用以下架构对细胞集 </font>$ \mathbf{X} \in \mathbb{R}^{K \times G} $<font style="color:rgb(31, 31, 31);"> 进行编码：</font>

+ **标记化（Tokenization）：**<font style="color:rgb(31, 31, 31);"> 首先，使用单层感知机将细胞集中的每个细胞 </font>$ \boldsymbol{x}^{(k)} \in \mathbb{R}^G $<font style="color:rgb(31, 31, 31);"> 投影到维度 </font>$ n \times d $<font style="color:rgb(31, 31, 31);">，其中 </font>$ n $<font style="color:rgb(31, 31, 31);"> 是基因模块标记的数量，</font>$ d $<font style="color:rgb(31, 31, 31);"> 表示标记的大小。然后，将基因标记嵌入 </font>$ \mathbf{P} \in \mathbb{R}^{n \times d} $<font style="color:rgb(31, 31, 31);"> 添加到感知机输出中。这为细胞集生成了一个张量 </font>$ \mathbf{Z}_0^{(k)} \in \mathbb{R}^{K \times n \times d} $<font style="color:rgb(31, 31, 31);">。</font>
+ **表格 Transformer 层（Tabular transformer layer）：**<font style="color:rgb(31, 31, 31);"> 这些张量由一组由 </font>$ N_L $<font style="color:rgb(31, 31, 31);"> 个表格 Transformer 层组成的堆叠 </font>$ (\{\mathcal{T}_i\}_{i=1}^{N_L}) $<font style="color:rgb(31, 31, 31);"> 进行处理：</font>



$ \mathbf{Z}_i = \mathcal{T}_i \left(\mathbf{Z}_{i-1}\right), \quad i \in \{1, 2, \dots, N_L - 1\}; \tag{4.3} $

$ \mathbf{E} = \mathcal{T}_{N_L} \left(\mathbf{Z}_{N_L - 1}\right). $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">每层 </font>$ \mathcal{T}_i $<font style="color:rgb(31, 31, 31);"> 在细胞集级别的表征上应用双重注意力机制。在以下描述中，每个注意力模块都是一个标准的多头注意力（MHA）块：输入被投影到多个头中，注意力输出被拼接并投影回来，然后通过残差连接与输入组合，接着是层归一化：</font>

1. **细胞内注意力（Intra-cellular attention）：**<font style="color:rgb(31, 31, 31);"> 一个细胞内 MHA 模块在 </font>$ \mathbf{Z}_i \in \mathbb{R}^{K \times n \times d} $<font style="color:rgb(31, 31, 31);"> 中的每个细胞的 </font>$ n $<font style="color:rgb(31, 31, 31);"> 个标记上独立运作。序列长度为 </font>$ n $<font style="color:rgb(31, 31, 31);">，特征维度为 </font>$ d $<font style="color:rgb(31, 31, 31);">。注意力头数为 </font>$ N_{H_g} $<font style="color:rgb(31, 31, 31);">。</font>
2. **细胞间注意力（Inter-cellular attention）：**<font style="color:rgb(31, 31, 31);"> 一个细胞间 MHA 模块在 </font>$ K $<font style="color:rgb(31, 31, 31);"> 个细胞上运作，其中 </font>$ (n, d) $<font style="color:rgb(31, 31, 31);"> 维度被展平为 </font>$ nd $<font style="color:rgb(31, 31, 31);">。序列长度为 </font>$ K $<font style="color:rgb(31, 31, 31);">，特征维度为 </font>$ nd $<font style="color:rgb(31, 31, 31);">。注意力头数为 </font>$ N_{H_c} $<font style="color:rgb(31, 31, 31);">。</font>
3. **前馈网络（FFN）：**<font style="color:rgb(31, 31, 31);"> 一个按位置操作的 FFN 独立处理每个 </font>$ d $<font style="color:rgb(31, 31, 31);"> 维标记，随后是残差连接和层归一化，产生 </font>$ \mathbf{Z}_i \in \mathbb{R}^{K \times n \times d} $<font style="color:rgb(31, 31, 31);">。</font>
+ **逐细胞解码器（Cell-wise decoder）：**<font style="color:rgb(31, 31, 31);"> 最后，细胞状态嵌入 </font>$ \mathbf{E} \in \mathbb{R}^{K \times n \times d} $<font style="color:rgb(31, 31, 31);"> 被独立解码为 </font>$ \{1, 2, \cdots, K\} $<font style="color:rgb(31, 31, 31);"> 中每个细胞的基因表达空间。解码器 </font>$ f $<font style="color:rgb(31, 31, 31);"> 被实现为一个多层感知机（MLP），它将展平的嵌入 </font>$ \bar{\mathbf{E}}^{(k)} \in \mathbb{R}^{nd} $<font style="color:rgb(31, 31, 31);"> 映射到负二项分布参数 </font>$ (\boldsymbol{\rho}^{(k)}, \boldsymbol{\theta}^{(k)}) \in (\mathbb{R}^G, \mathbb{R}^G) $<font style="color:rgb(31, 31, 31);">，遵循上面描述的生成过程。</font>

### <font style="color:rgb(31, 31, 31);"> 预训练目标</font>


<font style="color:rgb(31, 31, 31);">该模型在一个掩码基因重建任务上进行预训练。对于每个输入细胞集 </font>$ X $<font style="color:rgb(31, 31, 31);">，随机选择一个基因子集 </font>$ \mathcal{M} \subset \{1, 2, \cdots, G\} $<font style="color:rgb(31, 31, 31);">，并且这些基因在所有 </font>$ K $<font style="color:rgb(31, 31, 31);"> 个细胞中的表达值都会被掩码屏蔽。每个小批量（mini-batch）的掩码率从 </font>$ (p_{\mathrm{min}}, p_{\mathrm{max}}) = (0.1, 0.8) $<font style="color:rgb(31, 31, 31);"> 中随机采样。参考 </font>$ \mathrm{R}^2\mathrm{MAE} $<font style="color:rgb(31, 31, 31);">（Dong 等人，2025），这个选择范围旨在涵盖各种强度的基因依赖性。我们采用的 </font>$ p_{\mathrm{max}} $<font style="color:rgb(31, 31, 31);"> (0.8) 高于（Dong 等人，2025）中的设定 (0.5)，因为细胞间信息为隐式去噪带来了额外的信息。预训练目标结合了重建损失和潜在空间正则化项：</font>

<font style="color:rgb(31, 31, 31);"></font>

$ \mathcal{L} = \mathcal{L}_{\text{recon}} + \lambda_{\mathrm{SW}} \mathcal{L}_{\mathrm{SW}}. \tag{4.4} $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">重建损失 </font>$ \mathcal{L}_{\text{recon}} $<font style="color:rgb(31, 31, 31);"> 是预测的 NB 分布下原始计数的负对数似然，它是针对细胞集 </font>$ X $<font style="color:rgb(31, 31, 31);"> 中所有细胞的被掩码基因计算的：</font>

<font style="color:rgb(31, 31, 31);"></font>

$ \mathcal{L}_{\text{recon}} = - \frac{1}{K |\mathcal{M}|} \sum_{k=1}^K \sum_{g \in \mathcal{M}} \log P \left(x_g^{(k)} \mid l^{(k)}, \rho_g^{(k)}, \theta_g^{(k)}\right). \tag{4.5} $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">仅优化重建损失会导致死记硬背（memorization）和性能下降。为了强制进行有意义的预训练，我们加入了一个正则化项 </font>$ \mathcal{L}_{\mathrm{SW}} $<font style="color:rgb(31, 31, 31);">，即最终展平的细胞状态经验分布 </font>$ \{\bar{\mathbf{E}}^{(k)}\}_{k=1}^K $<font style="color:rgb(31, 31, 31);"> 与以批次为中心的多元高斯先验 </font>$ N \left( \frac{1}{K} \sum_{k=1}^K \bar{\mathbf{E}}^{(k)}, \mathbf{I}_{nd} \right) $<font style="color:rgb(31, 31, 31);"> 之间的切片瓦瑟斯坦距离（Sliced Wasserstein distance）。该项强制将嵌入分解为一个中心化高斯分布和一个特定于细胞集的常数向量，这使嵌入分布正则化并强制实现潜因子的线性可识别性（Dong 等人，2024）。线性可识别性结果直接源自 Khemakhem 等人（2020）建立的理论框架。损失项是在随机抽样的细胞集子集内计算的，子集大小从 </font>$ [32, 33, \dots, 128] $<font style="color:rgb(31, 31, 31);"> 中均匀采样。超参数 </font>$ \lambda_{\mathrm{SW}} $<font style="color:rgb(31, 31, 31);">（默认值为 0.01）平衡这两个损失组成部分。</font>

## <font style="color:rgb(31, 31, 31);">后训练</font>


<font style="color:rgb(31, 31, 31);">经过预训练的 Stack 模型通过监督对齐过程进行了针对上下文提示任务的后训练。其目标是赋予模型生成新颖细胞群的能力，结合来自一组查询细胞的细胞类型信息，以及由另一组独立的提示细胞提供的生物学上下文。我们的方法包含四个关键组成部分：(i) 一种新颖的自蒸馏程序；(ii) 一种训练输入构建策略；(iii) 架构修改；以及 (iv) 一个平衡泛化和知识保留的复合损失函数。</font>

### <font style="color:rgb(31, 31, 31);">自蒸馏</font>


<font style="color:rgb(31, 31, 31);">我们在后训练期间引入了自蒸馏程序。一个冻结的教师模型（在没有输入数据掩码的情况下运行）计算包含各个生物样本的细胞集的嵌入和基因表达参数；然后将这些输出用于计算训练目标。教师模型的权重通过正在主动进行后训练的学生模型的指数移动平均（EMA）进行更新。这种方法遵循了在自监督视觉模型（Grill 等人，2020；Oquab 等人，2023；Zhou 等人，2021）中建立的自蒸馏框架。</font>

### <font style="color:rgb(31, 31, 31);">后训练输入的构建</font>


<font style="color:rgb(31, 31, 31);">与预训练不同，后训练过程涉及具有匹配的细胞类型注释的两个生物样本。我们从来自提示样本的一个包含 </font>$ K $<font style="color:rgb(31, 31, 31);"> 个细胞的细胞集 </font>$ \mathbf{\bar{X}} = \{\pmb{x}^{(k)}\}_{k=1}^K $<font style="color:rgb(31, 31, 31);"> 开始。细胞的排列方式使得相同类型的细胞连续出现，并且每个样本的细胞类型顺序是随机的。这个细胞集被分成三个部分：</font>

1. **提示条件细胞**<font style="color:rgb(31, 31, 31);"> </font>$ (\mathbf{X}_{\mathrm{prompt}}^{\mathrm{fixed}}) $<font style="color:rgb(31, 31, 31);">：前 25% 的细胞，原样保留以用作条件上下文。</font>
2. **提示上下文细胞**<font style="color:rgb(31, 31, 31);"> </font>$ (\hat{\mathbf{X}}_{\mathrm{prompt}}^{\mathrm{kept}}) $<font style="color:rgb(31, 31, 31);">：</font>$ K_{\mathrm{kept}} $<font style="color:rgb(31, 31, 31);"> 个细胞，其表达谱是从教师 Stack 模型为相应的原始细胞预测的均值和离散度中采样的。</font>
3. **目标细胞位置**<font style="color:rgb(31, 31, 31);">：剩余的 </font>$ K_{\mathrm{query}} $<font style="color:rgb(31, 31, 31);"> 个位置，其中 </font>$ K_{\mathrm{kept}} + K_{\mathrm{query}} = 0.75K $<font style="color:rgb(31, 31, 31);"> 且比例 </font>$ K_{\mathrm{kept}} / (K_{\mathrm{kept}} + K_{\mathrm{query}}) \sim \mathcal{U}(0,1) $<font style="color:rgb(31, 31, 31);">。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">目标细胞位置被来自不同生物学上下文（例如，不同的供体或微扰条件）的查询细胞 </font>$ (\mathbf{X}_{\mathrm{query}}) $<font style="color:rgb(31, 31, 31);"> 填充。每个查询细胞都在细胞类型上与其替换的目标细胞相匹配。这产生了最终的输入：</font>

<font style="color:rgb(31, 31, 31);"></font>

$ \mathbf{X}_{\text{in}} = \left[ \mathbf{X}_{\text{prompt}}^{\text{fixed}}, \hat{\mathbf{X}}_{\text{prompt}}^{\text{kept}}, \mathbf{X}_{\text{query}} \right]. \tag{4.6} $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">模型的目标是以提示细胞为参考条件，预测目标细胞的基因表达分布。为了确保模型学习到有意义的生物学转变，每个被替换的细胞必须具有与其替换的原始细胞相同的细胞身份（例如，由用户指定的细胞类型或细胞系）。为了解决细胞类型分布不平衡的问题，我们对每个训练样本应用平衡程序：将数量过多的细胞类型下采样至每种类型的平均数量，然后对结果池进行有放回的上采样以恢复原始细胞集大小。对于重复的细胞，只有第一个实例用于计算稍后在 4.2.4 节中详细说明的分布损失项。</font>

<font style="color:rgb(31, 31, 31);"></font>

**表 1 | 后训练输入细胞集 **$ \mathbf{X}_{\mathrm{in}} $** 的组成部分。**

| **<font style="color:rgb(31, 31, 31);">组成部分</font>** | **<font style="color:rgb(31, 31, 31);">符号</font>** | **<font style="color:rgb(31, 31, 31);">大小</font>** | **<font style="color:rgb(31, 31, 31);">描述</font>** |
| :--- | :--- | :--- | :--- |
| <font style="color:rgb(31, 31, 31);">提示条件</font> | $ \mathbf{X}_{\text{prompt}}^{\text{fixed}} $ | <font style="color:rgb(31, 31, 31);">0.25K</font> | <font style="color:rgb(31, 31, 31);">来自提示样本的原始细胞</font> |
| <font style="color:rgb(31, 31, 31);">提示上下文</font> | $ \hat{\mathbf{X}}_{\text{prompt}}^{\text{kept}} $ | $ K_{\text{kept}} $ | <font style="color:rgb(31, 31, 31);">从教师预测的分布中采样</font> |
| <font style="color:rgb(31, 31, 31);">查询</font> | $ \mathbf{X}_{\text{query}} $ | $ K_{\text{query}} $ | <font style="color:rgb(31, 31, 31);">来自不同生物学上下文的细胞</font> |


> <font style="color:rgb(31, 31, 31);">注意：</font>$ K_{\text{kept}} + K_{\text{query}} = 0.75K $<font style="color:rgb(31, 31, 31);">；比例 </font>$ K_{\text{kept}} / (K_{\text{kept}} + K_{\text{query}}) \sim \mathcal{U}(0,1) $<font style="color:rgb(31, 31, 31);">。</font>
>

### <font style="color:rgb(31, 31, 31);">架构修改</font>


<font style="color:rgb(31, 31, 31);">我们在模型中引入了两个可学习的模块：一个查询位置嵌入 </font>$ \mathbf{P}_{\mathrm{query}} \in \mathbb{R}^{nd} $<font style="color:rgb(31, 31, 31);"> 和一个 MLP 二分类器 </font>$ f_{\mathrm{CLS}} : \mathbb{R}^{2nd} \to \mathbb{R} $<font style="color:rgb(31, 31, 31);">。在第一个嵌入层，位置嵌入 </font>$ \mathbf{P}_{\mathrm{query}} $<font style="color:rgb(31, 31, 31);"> 被添加到查询细胞的标记表征中。MLP 二分类器 </font>$ f_{\mathrm{CLS}} : \mathbb{R}^{2nd} \to \mathbb{R} $<font style="color:rgb(31, 31, 31);"> 接收平均提示条件嵌入与提示上下文/查询单细胞嵌入的拼接作为输入，并预测该细胞是来自提示（0）还是查询（1）。分类器接收分离（detached）的嵌入作为输入，因此其优化与其他模型权重无关。我们在这些新引入的模块上注册梯度钩子以应用 </font>$ 10\times $<font style="color:rgb(31, 31, 31);"> 的梯度缩放，这有效地提高了它们相对于预训练参数的学习率。此外，在所有 Transformer 层中应用了因果注意力掩码，以防止提示条件细胞关注提示上下文或查询细胞，从而确保信息严格地从提示条件细胞流向其余细胞。</font>

### <font style="color:rgb(31, 31, 31);">后训练目标</font>


<font style="color:rgb(31, 31, 31);">与预训练设置类似，模型接收一个被掩码处理的输入细胞集版本 </font>$ \mathbf{X}_{\mathrm{in}} $<font style="color:rgb(31, 31, 31);">，带有矩形基因掩码，掩码率从 </font>$ \mathcal{U}(0.1, 0.3) $<font style="color:rgb(31, 31, 31);"> 中采样。后训练目标旨在同时预测未见过的目标细胞，并保持在预训练期间学习到的信息：</font>

<font style="color:rgb(31, 31, 31);"></font>

$ \mathcal{L}_{\mathrm{FT}} = \mathcal{L}_{\text{dist}} + \lambda_{\text{recon}} \mathcal{L}_{\text{recon}} + \lambda_{\mathrm{SW}} \mathcal{L}_{\mathrm{SW}} + \lambda_{\mathrm{CLS}} \mathcal{L}_{\mathrm{CLS}}; \quad \mathcal{L}_{\text{dist}} = 0.5 \times \left(\mathcal{L}_{\text{gene}} + \mathcal{L}_{\text{embed}}\right). \tag{4.7} $

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">各组成部分的定义如下：</font>

+ **嵌入对齐损失 **$ \mathcal{L}_{\mathrm{embed}} $<font style="color:rgb(31, 31, 31);">：该项被定义为查询细胞和目标细胞的 Stack 嵌入之间的能量距离。目标细胞的嵌入从教师模型中提取，并在计算损失时进行分离（detached）。要微调的学生模型从输入数据细胞集 </font>$ \mathbf{X}_{\mathrm{in}} $<font style="color:rgb(31, 31, 31);"> 中计算查询细胞的嵌入。</font>
+ **表达对齐损失 **$ \mathcal{L}_{\mathrm{gene}} $<font style="color:rgb(31, 31, 31);">：该项被定义为预测的对数归一化目标基因表达分布与真实分布之间的能量距离。为了使 NB 分布参数的优化变得可行，使用可重参数化的零膨胀正态分布采样器生成预测，该采样器匹配对数归一化 NB 分布的前两个矩。为了解决过度平滑问题，我们使用从提示细胞中计算出的中位数分离过度离散度，为查询细胞估计一个共享的过度离散参数。损失是在每个小批次（mini-batch）的前 1,000 个高变基因（通过皮尔逊残差确定（Lause 等人，2021））上计算的，并像 </font>$ \mathcal{L}_{\mathrm{embed}} $<font style="color:rgb(31, 31, 31);"> 一样按细胞类型进行分层。</font>
+ **分布对齐损失 **$ \mathcal{L}_{\mathrm{dist}} $<font style="color:rgb(31, 31, 31);">：这是主要的对齐目标，定义为嵌入对齐损失 </font>$ \mathcal{L}_{\mathrm{embed}} $<font style="color:rgb(31, 31, 31);"> 和基因表达对齐损失 </font>$ \mathcal{L}_{\mathrm{gene}} $<font style="color:rgb(31, 31, 31);"> 的平均值。</font>
+ **重建损失 **$ \mathcal{L}_{\mathrm{recon}} $<font style="color:rgb(31, 31, 31);">：为了保留模型的掩码重建能力，我们像在预训练中一样，对提示细胞应用标准的掩码基因重建损失。这作为一个辅助任务，使模型正则化并迫使它维持预训练目标。我们使用 </font>$ \lambda_{\mathrm{recon}} = 1 $<font style="color:rgb(31, 31, 31);">。</font>
+ **潜在正则化 **$ \mathcal{L}_{\mathrm{SW}} $<font style="color:rgb(31, 31, 31);">：保留了预训练中的切片瓦瑟斯坦距离目标，并将其应用于批次中所有细胞的嵌入。我们使用 </font>$ \lambda_{\mathrm{SW}} = 0.01 $<font style="color:rgb(31, 31, 31);">。</font>
+ **分类损失 **$ \mathcal{L}_{\mathrm{CLS}} $<font style="color:rgb(31, 31, 31);">：分类损失被定义为 MLP 分类器在区分查询细胞与提示上下文细胞时的二元交叉熵损失（BCE）。我们使用 </font>$ \lambda_{\mathrm{CLS}} = 1 $<font style="color:rgb(31, 31, 31);">。</font>

### <font style="color:rgb(31, 31, 31);">生成过程</font>


<font style="color:rgb(31, 31, 31);">后训练设置非常类似于条件掩码扩散模型，其中提示细胞代表未被掩码的标记，而查询细胞代表模型必须预测的被掩码标记 </font>`<font style="color:rgb(31, 31, 31);">[mask]</font>`<font style="color:rgb(31, 31, 31);">。Stack 的生成式推理有两个关键区别：</font>

1. <font style="color:rgb(31, 31, 31);">查询细胞的基因表达谱被输入到模型中，以便对细胞类型信息进行编码。与 </font>$ \mathbf{P}_{\mathrm{query}} $<font style="color:rgb(31, 31, 31);"> 结合，它起着类似于语言模型中 </font>`<font style="color:rgb(31, 31, 31);">[mask]</font>`<font style="color:rgb(31, 31, 31);"> 标记的位置编码的作用。</font>
2. <font style="color:rgb(31, 31, 31);">掩码语言模型直接从词汇表上的 softmax 概率中获得标记级别的置信度。由于我们的输出空间是连续的，所以我们训练了一个单独的分类器来估计预测置信度，从而在生成过程中指导选择性取消掩码的过程。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在每个生成步骤中，模型接收包含拼接的提示条件细胞、提示上下文细胞和查询细胞的小批次。在这里，提示上下文细胞对应于原始细胞的表达谱。在整个生成过程中，提示条件细胞的比例保持在 25% 不变，而提示上下文细胞的比例从 0.2 线性增加到 0.4。维护一个布尔数组 </font>`<font style="color:rgb(31, 31, 31);">is_mask</font>`<font style="color:rgb(31, 31, 31);"> 以指示每个查询位置是否仍待预测，并且对于查询细胞，它初始化为全部为 </font>`<font style="color:rgb(31, 31, 31);">True</font>`<font style="color:rgb(31, 31, 31);">。每个步骤包括一个预测-更新周期，由线性掩码计划 </font>$ (1 - t/T) $<font style="color:rgb(31, 31, 31);"> 指导：</font>

+ **预测**<font style="color:rgb(31, 31, 31);">：模型执行前向传播，为所有查询细胞生成完整的表达谱。</font>
+ **置信度评分**<font style="color:rgb(31, 31, 31);">：分类器模块评估每个预测的查询细胞，并输出一个对数几率（logit）向量。正值表示细胞更像查询细胞，负值表示细胞更像提示细胞。</font>
+ **选择性取消掩码**<font style="color:rgb(31, 31, 31);">：基于掩码计划，选择一部分 </font>`<font style="color:rgb(31, 31, 31);">is_mask := True</font>`<font style="color:rgb(31, 31, 31);"> 的查询细胞用模型预测值替换。选择具有最低对数几率值的细胞进行替换。</font>
+ **状态更新**<font style="color:rgb(31, 31, 31);">：被替换的细胞的 </font>`<font style="color:rgb(31, 31, 31);">is_mask</font>`<font style="color:rgb(31, 31, 31);"> 值设置为 </font>`<font style="color:rgb(31, 31, 31);">False</font>`<font style="color:rgb(31, 31, 31);">。接下来，所有对数几率值 </font>$ > 0 $<font style="color:rgb(31, 31, 31);"> 的查询细胞（即那些被分类为查询细胞的细胞）会被（重新）设置为 </font>`<font style="color:rgb(31, 31, 31);">is_mask := True</font>`<font style="color:rgb(31, 31, 31);">。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">迭代过程在计划中的掩码率达到零时结束。该步骤的最终输出构成了初始查询细胞集的完整的、生成的表达矩阵。最终的对数几率向量也是用于量化生成质量和解释的输出的一部分。</font>

## <font style="color:rgb(31, 31, 31);">模型实现</font>


<font style="color:rgb(31, 31, 31);">Stack模型在PyTorch中实现，并使用PyTorch Lightning框架进行训练。训练过程包含两个阶段：自监督预训练和用于上下文提示的监督后训练。</font>

### <font style="color:rgb(31, 31, 31);">基础模型</font>


<font style="color:rgb(31, 31, 31);">Stack架构由 </font>$ N_L \in \{6, 9\} $<font style="color:rgb(31, 31, 31);"> 个表格Transformer层组成。每个细胞被标记化（tokenized）为 </font>$ n = 100 $<font style="color:rgb(31, 31, 31);"> 个标记（token），每个标记的维度为 </font>$ d \in \{8, 16, 32\} $<font style="color:rgb(31, 31, 31);">，从而产生总计为 </font>$ nd \in \{800, 1600, 3200\} $<font style="color:rgb(31, 31, 31);"> 的每细胞嵌入维度。Transformer的输入是一个由 </font>$ K = 256 $<font style="color:rgb(31, 31, 31);"> 个被标记化细胞组成的细胞集。每层内的前馈网络使用GELU激活函数。解码器被实现为带有GELU激活的2层MLP。在预训练期间没有应用dropout。扩展研究（scaling study）部分详细说明了不同模型设置的配置。</font>

### <font style="color:rgb(31, 31, 31);">预训练数据</font>


<font style="color:rgb(31, 31, 31);">预训练数据来源于完整的人类scBaseCount、scBaseCount子集或人类CELLxGENE。对于scBaseCount，我们过滤出了检测到300–7,000个基因且至少有700个UMI的细胞。没有对CELLxGENE数据集进行过滤。对于模型训练，通过计算每个scBaseCount数据文件中前1,000个高变基因（HVG）的并集，创建了一个统一的基因列表，总基因数上限为15,012个。使用解析皮尔逊残差（Lause 等人，2021）识别了HVG。数据加载器通过从每个文件中创建 </font>$ K = 256 $<font style="color:rgb(31, 31, 31);"> 个细胞的非重叠、连续的数据块来生成样本。长度短于 </font>$ K $<font style="color:rgb(31, 31, 31);"> 的数据块中的细胞被丢弃。表2总结了预训练数据指标。</font>

<font style="color:rgb(31, 31, 31);"></font>

**表 2 | 本研究中Stack模型训练数据集的概述。**

| **<font style="color:rgb(31, 31, 31);">训练集</font>** | **<font style="color:rgb(31, 31, 31);">训练数据集数量</font>** | **<font style="color:rgb(31, 31, 31);">训练细胞数量</font>** |
| :--- | :--- | :--- |
| <font style="color:rgb(31, 31, 31);">CellXGene ($)</font> | <font style="color:rgb(31, 31, 31);">905</font> | <font style="color:rgb(31, 31, 31);">7370万</font> |
| <font style="color:rgb(31, 31, 31);">scBaseCount 子集 (†)</font> | <font style="color:rgb(31, 31, 31);">9004</font> | <font style="color:rgb(31, 31, 31);">6020万</font> |
| <font style="color:rgb(31, 31, 31);">scBaseCount 完整集 (‡)</font> | <font style="color:rgb(31, 31, 31);">19978</font> | <font style="color:rgb(31, 31, 31);">1.488亿</font> |


### <font style="color:rgb(31, 31, 31);">预训练设置</font>


<font style="color:rgb(31, 31, 31);">Stack的base/large模型使用AdamW优化器预训练了10个epoch，峰值学习率为 </font>$ 1 \times 10^{-4} $<font style="color:rgb(31, 31, 31);">，权重衰减为 </font>$ 3 \times 10^{-3} $<font style="color:rgb(31, 31, 31);">。对于Stack的XLarge和Huge模型，峰值学习率被下调至 </font>$ 3 \times 10^{-5} $<font style="color:rgb(31, 31, 31);"> 以稳定训练。使用了余弦退火学习率计划，并在第一个epoch进行了线性预热。切片瓦瑟斯坦（Sliced Wasserstein）正则化权重 </font>$ \lambda_{\mathrm{SW}} $<font style="color:rgb(31, 31, 31);"> 被设置为0.01。所有实验均在一张具有320GB系统内存的NVIDIA H100 GPU（80GB HBM）上进行，使用bf16混合精度，批大小（batch size）为32，并包含4个训练数据加载工作进程。我们在同等设置下，将数据加载和预训练速度与State Embedding模型进行了基准测试比较。</font>

### <font style="color:rgb(31, 31, 31);">后训练数据</font>


<font style="color:rgb(31, 31, 31);">用于监督对齐的数据集精选自多个公共来源，包括Parse 10M PBMC数据（Parse Biosciences，2023），以及通过程序筛选的CELLxGENE数据库子集（Program 等人，2025）。为了确保适合学习供体特异性效应，对CELLxGENE子集进行了过滤，使其仅包含具有至少五个唯一供体的大规模数据集（大于50,000个细胞）。由于发现CELLxGENE中默认的“cell_type”列并不是最优的，我们实现了一个自动化程序来为每个数据集识别最佳的细胞类型注释列，该程序采用了一种启发式算法，优先考虑作者提供的、中等粒度的标签（例如，‘author_cell_type’、‘ann_coarse’），而不是标准化的本体论或过于详细的亚型。数据集选择程序最终获得了来自189个数据集的4500万个细胞。后训练数据加载器首先基于供体或样本ID，将整理好的数据集划分为训练集、验证集和测试集。每个训练样本包含一个由 </font>$ K = 512 $<font style="color:rgb(31, 31, 31);"> 个细胞组成的细胞集，该细胞集被进一步划分为 </font>$ K_{\mathrm{kept}} = 128 $<font style="color:rgb(31, 31, 31);"> 个提示条件细胞和 </font>$ K_{\mathrm{query}} = 384 $<font style="color:rgb(31, 31, 31);"> 个提示上下文/目标细胞。</font>

### <font style="color:rgb(31, 31, 31);">后训练设置</font>


<font style="color:rgb(31, 31, 31);">模型微调了8个epoch，其初始权重来自在完整人类scBaseCount上预训练的Stack（Large）模型。我们使用AdamW优化器，峰值学习率为 </font>$ 2 \times 10^{-5} $<font style="color:rgb(31, 31, 31);">，权重衰减为 </font>$ 3 \times 10^{-3} $<font style="color:rgb(31, 31, 31);">。应用了具有1个epoch线性预热和最低学习率 </font>$ 5 \times 10^{-6} $<font style="color:rgb(31, 31, 31);"> 的余弦退火学习率计划。对于教师模型的更新，我们采用了衰减率为0.95的指数移动平均（EMA），每500个优化步骤应用一次。训练配置的批大小为8，具有4步梯度累加，从而产生了32的有效批大小。微调实验在具有400GB系统内存的单张NVIDIA H100 GPU（80GB HBM）上进行，使用bf16混合精度。</font>

## <font style="color:rgb(31, 31, 31);">消融与扩展研究</font>


<font style="color:rgb(31, 31, 31);">我们进行了全面的消融（ablation）和扩展（scaling）研究，以评估Stack在不同设置和规模下的性能。下面展示了测试模型的概述。除了XLarge和Huge模型使用 </font>$ N_{H_C} = 20 $<font style="color:rgb(31, 31, 31);"> 之外，所有模型均使用隐藏维度 </font>$ d = 100 $<font style="color:rgb(31, 31, 31);"> 以及注意力头 </font>$ N_{H_C} = N_{H_G} = 8 $<font style="color:rgb(31, 31, 31);">。</font>

<font style="color:rgb(31, 31, 31);"></font>

**表 3 | 扩展研究中测试的模型设置概述。**

| **<font style="color:rgb(31, 31, 31);">模型变体</font>** | **<font style="color:rgb(31, 31, 31);">层数 </font>**$ N_L $ | **<font style="color:rgb(31, 31, 31);">总嵌入维度 </font>**$ nd $ | **<font style="color:rgb(31, 31, 31);">参数量</font>** | **<font style="color:rgb(31, 31, 31);">非嵌入参数量</font>** |
| :--- | :--- | :--- | :--- | :--- |
| <font style="color:rgb(31, 31, 31);">STACK (Base-) †</font> | <font style="color:rgb(31, 31, 31);">3</font> | <font style="color:rgb(31, 31, 31);">800</font> | <font style="color:rgb(31, 31, 31);">6910万</font> | <font style="color:rgb(31, 31, 31);">5700万</font> |
| <font style="color:rgb(31, 31, 31);">STACK (Base) §, †,‡</font> | <font style="color:rgb(31, 31, 31);">6</font> | <font style="color:rgb(31, 31, 31);">800</font> | <font style="color:rgb(31, 31, 31);">7670万</font> | <font style="color:rgb(31, 31, 31);">6470万</font> |
| <font style="color:rgb(31, 31, 31);">STACK (Base+) †</font> | <font style="color:rgb(31, 31, 31);">9</font> | <font style="color:rgb(31, 31, 31);">800</font> | <font style="color:rgb(31, 31, 31);">8440万</font> | <font style="color:rgb(31, 31, 31);">7240万</font> |
| <font style="color:rgb(31, 31, 31);">STACK (Medium) †</font> | <font style="color:rgb(31, 31, 31);">6</font> | <font style="color:rgb(31, 31, 31);">1600</font> | <font style="color:rgb(31, 31, 31);">1.86亿</font> | <font style="color:rgb(31, 31, 31);">1.63亿</font> |
| <font style="color:rgb(31, 31, 31);">STACK (Large) †,‡</font> | <font style="color:rgb(31, 31, 31);">9</font> | <font style="color:rgb(31, 31, 31);">1600</font> | <font style="color:rgb(31, 31, 31);">2.17亿</font> | <font style="color:rgb(31, 31, 31);">1.93亿</font> |
| <font style="color:rgb(31, 31, 31);">STACK (XLarge) ‡</font> | <font style="color:rgb(31, 31, 31);">6</font> | <font style="color:rgb(31, 31, 31);">3200</font> | <font style="color:rgb(31, 31, 31);">5.06亿</font> | <font style="color:rgb(31, 31, 31);">4.59亿</font> |
| <font style="color:rgb(31, 31, 31);">STACK (Huge) ‡</font> | <font style="color:rgb(31, 31, 31);">9</font> | <font style="color:rgb(31, 31, 31);">3200</font> | <font style="color:rgb(31, 31, 31);">6.29亿</font> | <font style="color:rgb(31, 31, 31);">5.82亿</font> |


<font style="color:rgb(31, 31, 31);">我们还评估了Stack (Base) † 的两种消融版本：(i) 没有潜在正则化，以及 (ii) 既没有潜在正则化也没有细胞间注意力。</font>

## <font style="color:rgb(31, 31, 31);">Stack 嵌入的评估</font>
### <font style="color:rgb(31, 31, 31);">探测（Probing）评估</font>


<font style="color:rgb(31, 31, 31);">为了评估学习到的细胞表征中编码的生物学信息，我们实施了一个多层探测框架。所有探测实验均采用基于分组的拆分策略，其中对于观察数据和 PBMC 微扰数据按供体 ID 划分数据集，对于细胞系微扰数据按 50% 样本拆分（按库标签分组）。这确保了在来自完全未见过的供体（或对于细胞系数据集的库拆分）的细胞上对模型进行评估。为了解决测试集中的类别不平衡问题，我们将每个供体的最大贡献限制为：观察数据 2,000 个细胞，Parse 25,000 个细胞，其他微扰数据集每个样本拆分 100,000 个细胞。采用了两种主要的探测方法来评估学习表征的不同方面：</font>

+ **线性探测**<font style="color:rgb(31, 31, 31);">：分类任务采用逻辑回归，连续变量采用岭回归，并在 80% 的供体上进行五折交叉验证训练。此设置对每种细胞类型分别训练单独的模型，从而能够评估细胞类型特异性信息的编码情况。如果总细胞类型数超过 20（或 Tabula Sapiens 中每种组织超过 5 种），所有分析均在数量最多的前 20 种细胞类型上进行。</font>
+ **MLP 探测**<font style="color:rgb(31, 31, 31);">：为了捕获非线性关系，我们实现了一个多层感知机（MLP），包含输入层归一化、具有 128 个单元和 ReLU 激活的隐藏层、0.2 的 dropout 以及特定任务的输出层。模型使用 AdamW 进行优化，学习率为 </font>$ 1 \times 10^{-3} $<font style="color:rgb(31, 31, 31);">，最多训练 80 个 epoch 并使用早停（早停耐心值为 12 个 epoch）。L2 正则化强度通过在 </font>$ \{0, 10^{-5}, 10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}\} $<font style="color:rgb(31, 31, 31);"> 范围内进行网格搜索来选择，该搜索基于按供体 70/15/15 划分训练/验证/测试集计算出的验证损失。模型在每个数据集的 5 个数量最多的细胞类型上一起训练。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在单细胞水平上评估性能。由于测试集限制了每个供体的贡献，当所有供体都超过 2,000 个细胞阈值时，计算出的细胞级准确率指标等于供体级平均指标，并在一些供体细胞数较少时平滑地逼近它。对于分类任务，我们报告平衡准确率。对于回归任务，我们报告皮尔逊相关系数。所有评估均采用固定的随机种子 42 进行。</font>

### <font style="color:rgb(31, 31, 31);">批次整合评估</font>


<font style="color:rgb(31, 31, 31);">我们使用 </font>`<font style="color:rgb(31, 31, 31);">scib-metrics</font>`<font style="color:rgb(31, 31, 31);"> 包（v0.5.5）进行了批次整合评估。为了移除导致基准测试错误的极其罕见的细胞群，分析是在一个子集上进行的，该子集包含数量最多的前 20 种细胞类型，或对于 Tabula Sapiens 包含数量最多的前 5 种细胞类别。如果由此产生的细胞数超过 100,000，则该子集会被随机下采样至此大小。评估围绕两个主要目标构建，每个目标由一套特定的指标评估：</font>

1. **批次校正**<font style="color:rgb(31, 31, 31);">：为了量化技术批次效应的消除，我们测量了 k 最近邻批次效应测试（kBET）、图连通性、主成分回归（PCR）得分、整合局部逆辛普森指数（iLISI）以及适应去批次的轮廓系数（BRAS）（Rautenstrauch 和 Ohler，2025）。</font>
2. **生物学信息守恒**<font style="color:rgb(31, 31, 31);">：为了评估生物信号的保留情况，我们测量了 Leiden 聚类与真实细胞类型标签的归一化互信息（NMI）和调整兰德指数（ARI）、细胞类型标签的轮廓分数以及细胞类型局部逆辛普森指数（cLISI）。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">这些分数被聚合以计算总分，遵循 </font>`<font style="color:rgb(31, 31, 31);">scib-metrics</font>`<font style="color:rgb(31, 31, 31);"> 的默认设置（Luecken 等人，2022）。</font>

### <font style="color:rgb(31, 31, 31);">基线模型</font>


<font style="color:rgb(31, 31, 31);">Stack 嵌入与以下几种方法进行了基准测试比较：</font>

1. **PC HVG**<font style="color:rgb(31, 31, 31);">：我们执行了文库归一化、log1p 转换和 Scanpy 默认的高变基因选择，以识别排名前 2,000 的高变基因。然后将这些基因降维至 800/50 个主成分。前一种设置与 Stack (base) 的维度相匹配，在探测任务中表现出色，而后一种设置更适合整合评估。</font>
2. **scGPT (v0.2.4)**<font style="color:rgb(31, 31, 31);">：我们使用推荐的全人类 scGPT 检查点来生成细胞嵌入。输入数据使用文库大小归一化和 log1p 转换进行预处理，推理批大小为 256。</font>
3. **UCE (commit 8227a65)**<font style="color:rgb(31, 31, 31);">：我们采用了（Rosen 等人，2023）中提供的 33 层模型检查点，批大小为 20 以提取嵌入。该模型直接在未经归一化的原始计数数据上运行。由于 UCE 默认情况下可能会由于预处理跳过极少量的细胞，我们将输出嵌入对齐回原始细胞索引，用零填充缺失的细胞。</font>
4. **State (SE) (state v0.9.27)**<font style="color:rgb(31, 31, 31);">：我们使用 Hugging Face 上的 </font>`<font style="color:rgb(31, 31, 31);">SE-600M</font>`<font style="color:rgb(31, 31, 31);"> 检查点和 </font>`<font style="color:rgb(31, 31, 31);">state emb transform</font>`<font style="color:rgb(31, 31, 31);"> 命令在原始计数数据上推断嵌入。数据加载器吞吐量测量方式如下：</font>`<font style="color:rgb(31, 31, 31);">uv run state emb fit model.batch_size=32 optimizer.gradient_accumulation_steps=256 dataset.num_train_workers=4</font>`<font style="color:rgb(31, 31, 31);">。</font>
5. **TranscriptFormer (v0.6.1)**<font style="color:rgb(31, 31, 31);">：由于其在人类 scRNA-seq 数据评估中的优势，我们使用了（Pearce 等人，2025）中的 </font>`<font style="color:rgb(31, 31, 31);">TF-sapiens</font>`<font style="color:rgb(31, 31, 31);"> 检查点。我们使用提供的 CLI 从原始计数数据推断嵌入。</font>
6. **微调的 scVI (scvi-tools v1.3.1)**<font style="color:rgb(31, 31, 31);">：预训练的 scVI 模型最初在 scBaseCount 子集上训练了 10 个 epoch，具有 2 个隐藏层，每层 2000 个隐藏维度和 800 个潜在维度，或 256 个隐藏维度和 50 个潜在维度。随后，该模型在每个目标数据集上以 </font>$ 5 \times 10^{-4} $<font style="color:rgb(31, 31, 31);"> 的学习率微调额外的 20 个 epoch。微调采用了流式小批次策略：从单个文件中抽取 256 个细胞的样本，并拼接形成 4096 个细胞的训练批次。每个细胞都标记有从其源文件派生的批次 ID。该策略极大地加速了 scVI 在大型单细胞数据集合上的训练。</font>
7. **从头开始训练的 scVI (scvi-tools v1.3.1)**<font style="color:rgb(31, 31, 31);">：模型配置有 2 个隐藏层，每层 2000/128 个隐藏维度和 800/30 个潜在维度，使用 Adam 优化器，以 </font>$ 1 \times 10^{-3} $<font style="color:rgb(31, 31, 31);"> 的学习率和 </font>$ 1 \times 10^{-4} $<font style="color:rgb(31, 31, 31);"> 的权重衰减训练 50 个 epoch。</font>

### <font style="color:rgb(31, 31, 31);">评估数据集</font>


<font style="color:rgb(31, 31, 31);">用于探测和整合评估的五个观察研究从 CELLxGENE 门户（Program 等人，2025）下载（肾脏、BCL、SEAS-AD MTG、LUCA 和 Tabula Sapiens）。微扰数据集从其官方网站下载（Tahoe、Parse、X-Atlas:Orion (Xaira) 和 OpenProblems 竞赛）。我们平衡了 Tabula Sapiens 的组织组成，如果细胞数超过阈值，则将每种组织的细胞数下采样至 20,000。</font>

<font style="color:rgb(31, 31, 31);"></font>

**表 4 | 本研究中使用的主要数据集概述。********* 表示从原始数据集进行了子采样。**

| **<font style="color:rgb(31, 31, 31);">数据集类别</font>** | **<font style="color:rgb(31, 31, 31);">数据集名称</font>** | **<font style="color:rgb(31, 31, 31);">供体数</font>** | **<font style="color:rgb(31, 31, 31);">细胞类型数</font>** | **<font style="color:rgb(31, 31, 31);">条件</font>** |
| :--- | :--- | :--- | :--- | :--- |
| **观察图谱** | <font style="color:rgb(31, 31, 31);">肾脏图谱</font> | <font style="color:rgb(31, 31, 31);">77</font> | <font style="color:rgb(31, 31, 31);">43</font> | <font style="color:rgb(31, 31, 31);">疾病：14 (AKI) / 37 (CKD) / 26 (健康)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">高血压：41 (有) / 36 (无)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">糖尿病史：38 (有) / 38 (无)</font> |
|  | <font style="color:rgb(31, 31, 31);">大脑图谱 (SEAS MTG)</font> | <font style="color:rgb(31, 31, 31);">38</font> | <font style="color:rgb(31, 31, 31);">65</font> | <font style="color:rgb(31, 31, 31);">微梗死病理：34 (0-3) / 2 (4-6) / 2 (7-10)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">ADNC：4 (非AD) / 7 (低) / 9 (中) / 18 (高)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">Braak 分期：2 (0) / 2 (II) / 4 (III) / 8 (IV) / 11 (V) / 11 (VI)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">Thal 分期：4 (0) / 3 (1) / 4 (2) / 7 (3) / 10 (4) / 10 (5)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">CERAD 评分：9 (无) / 5 (稀疏) / 7 (中等) / 17 (频繁)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">APOE4 状态：23 (无) / 15 (有)</font> |
|  | <font style="color:rgb(31, 31, 31);">淋巴结图谱 (BCL)</font> | <font style="color:rgb(31, 31, 31);">223</font> | <font style="color:rgb(31, 31, 31);">21</font> | <font style="color:rgb(31, 31, 31);">疾病：208 (BCL) / 15 (健康)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">LymphoMAP：84 (FMAC) / 76 (LN) / 64 (TEX)</font> |
|  | <font style="color:rgb(31, 31, 31);">肺图谱 (LUCA)</font> | <font style="color:rgb(31, 31, 31);">160</font> | <font style="color:rgb(31, 31, 31);">39</font> | <font style="color:rgb(31, 31, 31);">疾病：18 (COPD) / 75 (LUAD) / 17 (LUSC) / 2 (NSCLC) / 48 (健康)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">UICC 分期：45 (I) / 17 (II) / 7 (III) / 24 (IV) / 66 (非癌症)</font><font style="color:rgb(31, 31, 31);">   </font><font style="color:rgb(31, 31, 31);">曾吸烟者：85 (是) / 75 (否)</font> |
|  | <font style="color:rgb(31, 31, 31);">Tabula Sapiens</font> | <font style="color:rgb(31, 31, 31);">24</font> | <font style="color:rgb(31, 31, 31);">31</font> | <font style="color:rgb(31, 31, 31);">具有 </font><font style="color:rgb(31, 31, 31);">></font><font style="color:rgb(31, 31, 31);">1 个供体的 25 种组织</font> |
| **微扰数据集** | <font style="color:rgb(31, 31, 31);">OpenProblems-PBMC</font> | <font style="color:rgb(31, 31, 31);">3</font> | <font style="color:rgb(31, 31, 31);">6</font> | <font style="color:rgb(31, 31, 31);">147 种条件</font> |
|  | <font style="color:rgb(31, 31, 31);">Tahoe-100M</font> | <font style="color:rgb(31, 31, 31);">-</font> | <font style="color:rgb(31, 31, 31);">40</font><font style="color:rgb(31, 31, 31);">*</font> | <font style="color:rgb(31, 31, 31);">来自 1-3 块板的 250</font><font style="color:rgb(31, 31, 31);">*</font><font style="color:rgb(31, 31, 31);"> 种微扰</font> |
|  | <font style="color:rgb(31, 31, 31);">Parse-PBMC</font> | <font style="color:rgb(31, 31, 31);">12</font> | <font style="color:rgb(31, 31, 31);">17</font> | <font style="color:rgb(31, 31, 31);">90 种微扰</font> |
|  | <font style="color:rgb(31, 31, 31);">X-Atlas:Orion (Xaira)</font> | <font style="color:rgb(31, 31, 31);">-</font> | <font style="color:rgb(31, 31, 31);">2</font> | <font style="color:rgb(31, 31, 31);">每个细胞系前 50</font><font style="color:rgb(31, 31, 31);">*</font><font style="color:rgb(31, 31, 31);"> 种微扰</font> |


## <font style="color:rgb(31, 31, 31);">细胞提示任务评估</font>


<font style="color:rgb(31, 31, 31);">提示评估框架评估了模型在给定提示（prompt）和查询（query）细胞的情况下，通过上下文学习（ICL）生成所需表达谱的能力。我们评估了四种 ICL 设置：</font>

<font style="color:rgb(31, 31, 31);"></font>

**表 5 | Stack 的上下文细胞提示任务概述。**

| **<font style="color:rgb(31, 31, 31);">任务类别</font>** | **<font style="color:rgb(31, 31, 31);">任务名称</font>** | **<font style="color:rgb(31, 31, 31);">提示</font>** | **<font style="color:rgb(31, 31, 31);">查询</font>** | **<font style="color:rgb(31, 31, 31);">同一数据集？</font>** |
| :--- | :--- | :--- | :--- | :--- |
| **微扰 ICL** | <font style="color:rgb(31, 31, 31);">1. 新细胞类型的微扰效应预测</font> | <font style="color:rgb(31, 31, 31);">受微扰细胞（随机类型）</font> | <font style="color:rgb(31, 31, 31);">对照细胞（非重叠类型）</font> | <font style="color:rgb(31, 31, 31);">是</font> |
|  | <font style="color:rgb(31, 31, 31);">2. 新样本的微扰效应预测</font> | <font style="color:rgb(31, 31, 31);">受微扰 T 细胞（供体 A）</font> | <font style="color:rgb(31, 31, 31);">未受微扰 T 细胞（供体 B）</font> | <font style="color:rgb(31, 31, 31);">否</font> |
| **观察性 ICL** | <font style="color:rgb(31, 31, 31);">3. 留出（Hold-out）细胞类型预测</font> | <font style="color:rgb(31, 31, 31);">选定细胞类型（供体 A）</font> | <font style="color:rgb(31, 31, 31);">非重叠类型（供体 B）</font> | <font style="color:rgb(31, 31, 31);">是</font> |
| **混合 ICL** | <font style="color:rgb(31, 31, 31);">4. 跨数据集细胞类型生成</font> | <font style="color:rgb(31, 31, 31);">选定细胞类型（供体/微扰 A）</font> | <font style="color:rgb(31, 31, 31);">非重叠类型（供体 B）</font> | <font style="color:rgb(31, 31, 31);">否</font> |


### <font style="color:rgb(31, 31, 31);">评估数据构建</font>


<font style="color:rgb(31, 31, 31);">在具有细胞类型留出的设置（1、3、4）中，随机抽取了一个供体/条件中存在的广泛细胞类别，并将其作为要预测的目标细胞留出（比例为 0.75）。该供体剩余的未留出细胞类型构成了提示数据，而来自另一个供体/条件的留出细胞类型被用作查询细胞。在跨样本的反应预测（设置 2）中，所有数据均被提取子集为单一细胞类型（T 细胞）。在微扰数据（设置 1-2）中，通常可以获得来自同一提示供体的对照条件。因此，我们额外利用这些细胞作为模型的辅助提示，并将输出用作 cell-eval 基准测试的“合成对照（synthetic control）”。在适当的情况下，这种合成对照方法被应用于 Stack 和其他基线模型。对于观察性提示任务，预言机（oracle）基线额外使用了查询条件中的未留出细胞类型作为辅助数据，而这些数据对 Stack 是不可用的。我们通过下采样至这三组中最小可用细胞数，来使查询细胞、辅助细胞和目标细胞的数量相等。为了解决设置 1 和 3 中的罕见细胞类型问题，我们将查询数据中的每种细胞类型分别上采样至至少 2000 个和 1000 个细胞。</font>

### <font style="color:rgb(31, 31, 31);">基线模型</font>


<font style="color:rgb(31, 31, 31);">Stack 的提示性能与以下几种方法进行了基准测试比较：</font>

1. **原始查询（Original Query）**<font style="color:rgb(31, 31, 31);">：原始查询细胞被用于预测，代表一种未利用提示中任何信息的零变化情景。</font>
2. **提示中最近的细胞类型（Nearest Cell Type in Prompt）**<font style="color:rgb(31, 31, 31);">：该基线计算提示数据中所有细胞类型的伪容积表达谱。对于每个查询细胞，它基于伪容积皮尔逊相关性识别提示中最相似的细胞类型，然后从该匹配细胞类型中无放回地随机抽取一个细胞的表达谱进行分配。一旦一种细胞类型中的所有细胞被用尽，就使用第二接近的细胞类型，依此类推。</font>
3. **提示中相同的细胞类型（Same Cell Type in Prompt）**<font style="color:rgb(31, 31, 31);">：该基线在可能的情况下，通过从提示中无放回地对相同细胞类型的细胞进行采样来分配表达谱。</font>
4. **PerturbMean/DonorMean**<font style="color:rgb(31, 31, 31);">：该方法计算提示上下文和查询上下文之间（每种细胞类型的）表达谱平均差异。这个差异向量是在提示数据和辅助数据之间的未留出细胞类型上计算的，然后被添加到查询细胞的表达谱中。合成对照不适用于此基线，因为它将等同于查询数据。</font>
5. **scVI**<font style="color:rgb(31, 31, 31);">：训练一个带有 30 个潜在维度和 200 个隐藏维度的 2 层 scVI 模型（scvi-tools v1.3.1），在拼接的提示和辅助样本上训练 50 个 epoch，使用数据集来源作为批次键。然后，该模型被用来将查询细胞投影到潜在空间并采样它们的表达谱，人为地将“提示”指定为批次标签。</font>
6. **State**<font style="color:rgb(31, 31, 31);">：State 模型（v0.9.27）使用 </font>$ \mathrm{ST} + \mathrm{SE} $<font style="color:rgb(31, 31, 31);"> 设置进行训练（Adduri 等人，2025），在该设置中，模型预测细胞嵌入并同时将其解码回基因表达空间。模型在提示数据、查询数据和辅助数据上使用最大均值差异（MMD）损失进行训练，使用的基因集是不同随机种子下 cell-eval 基准测试中高变基因的并集。只有查询集中的对照细胞被用于模型训练。所有模型使用的隐藏维度为 328，细胞集长度为 32。模型训练了 60,000 步（批大小为 8，学习率 </font>$ 3 \times 10^{-4} $<font style="color:rgb(31, 31, 31);">）。在基因空间输出上使用了随机基础映射。通过保留细胞上的验证损失来选择最佳检查点。</font>

### <font style="color:rgb(31, 31, 31);">评估指标</font>


<font style="color:rgb(31, 31, 31);">我们使用伪容积相关性和差异表达（DE）指标，对照真实数据评估了生成的表达谱。这两类指标均使用 cell-eval v0.6.6 (Adduri 等人，2025) 及其默认参数来实现，采用 Wilcoxon 秩和检验进行 DE 检测，并使用 Benjamini-Hochberg 校正进行多重检验。所有指标均在通过合并目标数据和查询数据识别出的排名前 2000 的对数归一化高变基因上计算得出。对于设置 4，我们额外使用 scIB 评估了真实表达谱和预测基因表达谱的整合性能，配置与早先的基准测试相同。</font>

+ **伪容积相关性**<font style="color:rgb(31, 31, 31);">：我们通过两个指标衡量方法捕获伪容积级别微扰效应的程度：</font>
    - **Pearson Delta**<font style="color:rgb(31, 31, 31);">：预测的表达变化与观察到的表达变化之间的皮尔逊相关性。对于每种微扰 </font>$ t $<font style="color:rgb(31, 31, 31);">，我们分别计算预测的伪容积 </font>$ (\bar{\Delta}_t) $<font style="color:rgb(31, 31, 31);"> 和真实的伪容积 </font>$ (\Delta_t) $<font style="color:rgb(31, 31, 31);"> 的表达变化 </font>$ \Delta_t = \left| p_t - p_{\mathrm{ctrl}} \right| $<font style="color:rgb(31, 31, 31);">，然后计算：</font>$ \text{Pearson-}\Delta = \mathrm{corr}(\bar{\Delta}_t, \Delta_t) $
    - **DE Spearman LFC**<font style="color:rgb(31, 31, 31);">：预测的与观察到的对数倍数变化之间的斯皮尔曼秩相关性，该指标在真实数据中显著差异表达（DE）的基因集合内计算。</font>
    - **DE 方向匹配（DE direction match）**<font style="color:rgb(31, 31, 31);">：该指标衡量基因表达变化的预测方向（即上调或下调）是否与真实情况相匹配。它仅在预测数据和真实数据中均显著差异表达（DE）的基因集合上计算。得分是这些共享的 DE 基因中变化方向相匹配的比例。在观察性提示任务中，该指标取代了 Pearson Delta。当许多基因被识别为差异表达基因（DEG）时，Pearson Delta 的表现与 DE Spearman LFC 相当，但同时也显示出对批次效应更大的脆弱性。</font>
+ **差异表达准确率**<font style="color:rgb(31, 31, 31);">：最后，我们评估了预测是否捕获了真实数据和输入查询条件之间的差异表达。</font>
    - **PR-AUC**<font style="color:rgb(31, 31, 31);">：精确率-召回率曲线下的面积，使用二元 DE 标签和 </font>$ -\log_{10}(p\text{-values}) $<font style="color:rgb(31, 31, 31);"> 作为得分（基于 sklearn 的 average</font><font style="color:rgb(31, 31, 31);">_</font><font style="color:rgb(31, 31, 31);">precision</font><font style="color:rgb(31, 31, 31);">_</font><font style="color:rgb(31, 31, 31);">score 实现）。</font>
    - **Spearman 效应量（Spearman effect size）**<font style="color:rgb(31, 31, 31);">：为了比较微扰的相对效应量，我们计算了预测和真实之间差异表达基因数量（调整后 p 值 </font><font style="color:rgb(31, 31, 31);"><</font><font style="color:rgb(31, 31, 31);"> 0.05）的斯皮尔曼相关系数。这评估了模型是否准确捕获了不同条件下的相对效应量。我们在每种细胞类型和微扰/供体内对不同随机种子的预测进行了平均，从而得出按每种细胞类型的微扰/供体计算的斯皮尔曼相关性。</font>
    - **DE 重叠准确率（DE Overlap Accuracy）**<font style="color:rgb(31, 31, 31);">：计算真实 DE 绝对对数倍数变化排名前 </font>$ N $<font style="color:rgb(31, 31, 31);"> 的基因与预测 DE 排名前 </font>$ N $<font style="color:rgb(31, 31, 31);"> 的基因之间的重叠，计算公式为 </font>$ |\text{top-}N \text{ true} \cap \text{top-}N \text{ predicted}| / N $<font style="color:rgb(31, 31, 31);">，其中 </font>$ N $<font style="color:rgb(31, 31, 31);"> 是真实的 DE 基因总数。</font>
    - **DE Precision-at-N**<font style="color:rgb(31, 31, 31);">：计算真实 DE 排名前 </font>$ N $<font style="color:rgb(31, 31, 31);"> 的基因与预测 DE 排名前 </font>$ N $<font style="color:rgb(31, 31, 31);"> 的基因之间的重叠，计算公式为 </font>$ |\text{top-}N \text{ true} \cap \text{top-}N \text{ predicted}| / N $<font style="color:rgb(31, 31, 31);">，其中 </font>$ N $<font style="color:rgb(31, 31, 31);"> 是预测的 DE 基因总数。该指标评估了预测 DE 基因列表的保真度，并在设置 2 中取代了 Spearman 效应量相关性，在设置 2 中，由于具有相似效应量的微扰数量有限，基于秩的相关性不可靠。</font>
    - **Jaccard 相似度（Jaccard similarity）**<font style="color:rgb(31, 31, 31);">：对于每种微扰，我们计算预测的 DE 基因集和真实的 DE 基因集之间的 Jaccard 指数，定义为两个集合的交集大小除以并集大小。</font>

### <font style="color:rgb(31, 31, 31);">评估数据集</font>


<font style="color:rgb(31, 31, 31);">用于评估的数据集包括：1. OpenProblems 药物微扰（Luecken 等，2025），2. 细胞因子刺激（Dong 等，2023），3. 免疫衰老（Wells 等，2025），4. Tabula Sapiens（Consortium</font><font style="color:rgb(31, 31, 31);">*</font><font style="color:rgb(31, 31, 31);"> 等，2022），5. 肾脏图谱（De Boer 等，2021），6. 淋巴结 BCL（Li 等，2025），7. 肝脏图谱（Edgar 等，2025），8. Parse 细胞因子微扰数据集（Parse Biosciences，2023）。观察图谱（3-7）下载自 CELLxGENE 门户，细胞因子刺激数据下载自 Dryad（Dong 等，2023）。细胞因子刺激数据（Dong 等，2023）包含 3 个供体，但供体 1 的细胞数量非常有限。因此，我们将数据集取子集以仅包含供体 2 和 3（重新标记为供体 a 和 b），并且仅包括来自急性条件（2 天）的细胞。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">对于设置 1，OpenProblems 数据集在每次测试实验中使用从同一供体（共 3 个供体）中采样的提示和查询。对于设置 2，提示使用来自细胞因子条件（IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);">、IFN-</font>$ \gamma $<font style="color:rgb(31, 31, 31);">、IL-6、TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);">）下 Parse 数据集中一个供体的 T 细胞，而查询使用（Dong 等人，2023）中供体 a 或 b 的对照 T 细胞。真实评估使用了（Dong 等人，2023）中对应的单一和组合条件（IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);">、IFN-</font>$ \gamma $<font style="color:rgb(31, 31, 31);">、IL-6、TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);">、IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);"> + IFN-</font>$ \gamma $<font style="color:rgb(31, 31, 31);">、IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);"> + IL-6、IFN-</font>$ \beta $<font style="color:rgb(31, 31, 31);"> + TNF-</font>$ \alpha $<font style="color:rgb(31, 31, 31);">）。对于组合微扰评估，我们计算了单次微扰 Stack 预测的加权总和。由于 Parse 数据集和 Dong 等人（2023）之间的剂量差异，我们在权重 [0.1, 0.3, 0.5, 0.7, 0.9] 上执行了网格搜索，以确定原始提示 T 细胞中归一化基因表达条件的最佳加权平均值。最佳权重基于 Pearson Delta 选择，随后用于生成组合微扰的 Stack 预测。对于设置 3，提示和查询包含在每个数据集中从不同供体采样的非重叠细胞类型。对于设置 4，提示包括：Parse 对照细胞（PBS 条件），每个提示采样一个供体；Parse 供体 1 细胞，每个提示采样一种微扰；免疫衰老数据集细胞，每个提示一个供体；OpenProblems 细胞，每个提示一种微扰。在此设置中的所有查询均使用来自 Tabula Sapiens 的免疫细胞。在设置 3 和 4 中，我们对每个评估数据集在细胞类别级别进行留出处理，将细胞注释从原作者的注释重新标记，以与 Tabula Sapiens 中为相应组织定义的广泛细胞类别保持一致。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">在细胞类别层面进行留出可以最大程度地减少相似细胞类型之间潜在的信息泄漏。</font>

## <font style="color:rgb(31, 31, 31);">全生命体微扰图谱 Perturb Sapiens</font>


<font style="color:rgb(31, 31, 31);">在分析中，我们将 OpenProblems 药物微扰数据中供体 2 的每个条件和 Parse 细胞因子微扰数据中供体 1 的每个条件用作提示，并将组织平衡版本的 Tabula Sapiens 用作查询。我们使用后训练的 Stack (</font>$ T=5 $<font style="color:rgb(31, 31, 31);">) 执行上下文生成。我们移除了分类器对数几率（logits）大于 2.5 的细胞。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">我们生成了单个细胞因子处理的对数倍数变化热图。对于每种细胞类型，在每个条件下对多达 10,000 个细胞进行了子采样、归一化和对数转换。通过在示例 ADSF Perturb Sapiens 数据集中的皮尔逊残差，将基因取子集为 4,000 个高变基因（Lause 等人，2021）。使用带有 Benjamini-Hochberg 校正的 Wilcoxon 秩和检验执行差异表达分析（DEG：对于 Parse/OpenProblems 分别为 FDR </font><font style="color:rgb(31, 31, 31);"><</font><font style="color:rgb(31, 31, 31);"> 0.05, </font>$ |\log_2\mathrm{FC}| > 0.25/0.5 $<font style="color:rgb(31, 31, 31);">）。为了比较跨药物或细胞因子微扰的 Perturb Sapiens 性能与生物学重复的性能，应用了相同的差异表达流程，其中每个条件被子采样至最多 15,000 个细胞。Cell-eval 评估指标如上所述构建，带有一个修改：显著基因使用与 DEG 流程一致的明确最小对数倍数变化阈值来定义。</font>

<font style="color:rgb(31, 31, 31);"></font>

<font style="color:rgb(31, 31, 31);">对于非免疫细胞的评估，我们从 GEO 数据库下载了四个体外上皮细胞因子微扰数据集（Koh 等，2023；Swindell 等，2018；Lee 等，2022；Saito 等，2021）。所有评估均限制在从示例 ADSF Perturb Sapiens 中识别出的前 4,000 个高变基因。对于前三个数据集，使用 PyDESeq2（v0.5.2）在伪容积（Koh 等，2023）或大块（bulk）RNA-seq 数据（Swindell 等，2018；Lee 等，2022）上计算了对数倍数变化、p 值和调整后的 p 值。对于（Saito 等人，2021），由于存储数据的归一化 TPM 格式，我们执行了供体水平的配对 t 检验以计算对数倍数变化和 p 值，并使用 Benjamini-Hochberg 校正计算调整后的 p 值。Perturb Sapiens 上的差异表达分析是使用 Scanpy 实现的 Wilcoxon 秩和检验执行的。Perturb Sapiens 中的气道和角质形成细胞上皮细胞群是通过从其各自的组织（肺、气管代表气道；皮肤和舌头代表角质形成细胞）中选择被注释为“上皮细胞”的细胞类别构建的。为了确保 Perturb Sapiens 细胞类型之间的公平比较，每个细胞类型群体的上限为最多 15,000 个细胞。我们将体外单细胞数据评估的 LFC 阈值设置为 0.5，大块数据评估的 LFC 阈值设置为 0.25。最后，对于每种药物/细胞因子微扰及其匹配的对照组，我们识别了具有足够细胞计数（</font>$ \geq 1000 $<font style="color:rgb(31, 31, 31);"> 个细胞）的组织-细胞类型组合。然后，我们应用上述相同的差异表达分析流程来计算对数倍数变化和调整后的 p 值。在图 S17 和 S18 中，微扰效应被定义为对数倍数变化，其中不显著的值（调整后的 p </font><font style="color:rgb(31, 31, 31);">></font><font style="color:rgb(31, 31, 31);"> 0.05）设置为零。</font>

<font style="color:rgb(31, 31, 31);"></font>

**数据可用性。**<font style="color:rgb(31, 31, 31);"> 有关访问 scBaseCount 的文档，请访问 </font>[https://github.com/ArcInstitute/arc-virtual-cell-atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas)<font style="color:rgb(31, 31, 31);">。生成的 Perturb Sapiens 数据存放在 Huggingface：</font>[https://huggingface.co/datasets/arcinstitute/Perturb-Sapiens](https://huggingface.co/datasets/arcinstitute/Perturb-Sapiens)<font style="color:rgb(31, 31, 31);">。用于对齐的 CELLxGENE 45M 数据也可在 Huggingface 获取：</font>[https://huggingface.co/arcinstitute/Stack-CellxGene45M](https://huggingface.co/arcinstitute/Stack-CellxGene45M)<font style="color:rgb(31, 31, 31);">。Parse 10M PBMC 数据可在官方网站获取 </font>[https://www.parsebiosciences.com/datasets/10-million-human-pbmcs-in-a-single-experiment/#download](https://www.google.com/search?q=https://www.parsebiosciences.com/datasets/10-million-human-pbmcs-in-a-single-experiment/%23download)<font style="color:rgb(31, 31, 31);">。本项目使用的所有评估数据均可公开获取；有关其他数据集的下载详细信息，请参阅“方法”部分。</font>

**代码和模型可用性。**<font style="color:rgb(31, 31, 31);"> Stack 模型的代码可在 </font>[https://github.com/ArcInstitute/stack](https://github.com/ArcInstitute/stack)<font style="color:rgb(31, 31, 31);"> 获取。模型参数可在 Huggingface 上获取：</font>[https://huggingface.co/arcinstitute/Stack-Large](https://huggingface.co/arcinstitute/Stack-Large)<font style="color:rgb(31, 31, 31);">，</font>[https://huggingface.co/arcinstitute/Stack-Large-Aligned](https://huggingface.co/arcinstitute/Stack-Large-Aligned)<font style="color:rgb(31, 31, 31);">。</font>



