**（特别注意：本刊双盲评审，投稿上传系统的版本需要隐去作者、单位、基金等信息；初审后寄编辑部的纸稿、以及录用后的修改稿提交时需将信息补全）**

**基于分片区块链的车联网数据共享方案** 题目三号

陈\*^1^ 黄\*鸿^2^ 田\*凡^1^ 作者四号宋体，作者和单位的对应关系标注在作者姓名的右上角

^1^（电子科技大学计算机科学与工程学院 成都 611731）单位小五号，城市若不是省会则写出省份

^2^（处理器芯片全国重点实验室（中国科学院计算技术研究所） 北京 518110）国家、部级、省级实验室注意写依托单位

（chenxiao_hey@std.uestc.edu.cn）小五号，区别于页脚处通信作者的邮箱

上述作者及单位信息在上传系统的[新投稿、待复审稿件中隐去]{.mark}

#### Internet of Vehicles Data Sharing Scheme via Blockchain Sharding Title四号

Chen\*^1^ , Huang \*hong^2^ , Tian Yifan^1^ Name五号

^1^（*School of Computer Science and Engineering*, *University of Electronic Science and Technology of China*, *Chengdu* 611731）

^2^（*State Key Laboratory of Processors(Institute of Computing, Chinese Academy of Sciences) Beijing* 518110）

上述作者及单位信息在上传系统的[新投稿、待复审稿件中隐去]{.mark}

**Abstract** Efficient and secure data sharing is crucial for the profound application of the intelligent Internet of vehicles, where achieving trusted data sharing between mutually untrusting vehicles has become a major focus of current research. With the characteristics of tamper resistance and traceability, blockchain has emerged as a primary approach to support data circulation in the intelligent Internet of vehicles. Existing blockchain-based data-sharing solutions for the Internet of vehicles suffer from low throughput and security vulnerabilities. In this paper, the blockchain sharding approach was introduced, where a machine learning-based sharding algorithm was utilized to partition road side unit (RSU) with geographical proximity into the same shard and iteratively optimize data-sharing loads within individual shards. This algorithm reduces intra-shard communication latency and subsequently improves throughput while balancing the data-sharing loads among different shards. To prevent bribery attacks within a single shard, a reputation-based intra-shard consensus protocol and the supervisor mechanism were proposed. The proposed protocol involves the election of RSUs with high reputation to participate in the intra-shard consensus process and dynamically calculates the latest reputation of RSUs. High-reputation RSUs are designated supervisors and regularly verify the legitimacy of blocks generated in different shards. Performance evaluation and security analysis demonstrate the scheme enhances the efficiency and security of data sharing in the intelligent Internet of vehicles.

Abstract五号，至少200字，否则影响EI索引

**Key words** Internet of vehicles; blockchain sharding; consensus protocol; supervisor mechanism; data sharing

Key words五号，至少5个

摘要 高效安全的数据共享对于智能车联网的深度应用至关重要，在相互不信任的车辆之间实现可信的数据共享成为当前研究的热点。区块链技术以其防篡改、可追溯等特点，成为支撑智能车联网数据共享流通的主要途径之一。现有基于区块链的车联网数据共享方案，存在吞吐量小，安全性低等不足。引入区块链分片方法，提出基于机器学习的分片算法，将地理位置相近的路侧单元（road side unit，RSU）划分到同一分片，并迭代单个分片的数据共享最优负载，降低了片内通信延迟进而提高了吞吐量，平衡了不同分片之间的数据共享负载。为避免单个分片的贿赂攻击，提出了基于声誉的片内共识协议与监督人机制。选举具有高声誉的路侧单元参与片内共识过程，并动态计算路侧单元的最新声誉。设定声誉度高的路侧单元担任监督员，监督员可定期对不同分片产生的区块进行合法性验证。通过性能评估和安全性分析，证明方案有助于提升智能车联网数据共享的高效性和安全性。摘要五号楷体，300字左右

关键词 车联网；分片区块链；共识协议；监督人机制；数据共享 关键词五号楷体，不少于5个

中图法分类号 TP311.13；TP309

正文五号宋体

随着车联网中车辆数量的不断增加，车辆之间数据共享交换的速度和频率越来越高，安全高效的智能车联网数据共享方案已成为研究热点。其中，基于区块链的方案持续涌现，成为车联网数据共享的重要途径。目前，基于区块链的车联网数据共享方案主要有：基于区块链的联邦学习数据共享方案[^\[1-2\]^]{.mark}，使用区块链代替联邦学习中的中心化服务器，提出了面向分布式终端的去中心化数据共享架构与系统。基于新型共识协议的数据共享方案[^\[3-4\]^]{.mark}，针对不断变化的车联网环境，提出适用于不同场景的共识机制。基于区块链访问控制的数据共享方案[^\[5-6\]^]{.mark}，提出新的加密方式实现对区块的细粒度访问控制。以上方法所使用的区块链系统吞吐量较为有限，难以应对未来智能车联网中海量数据共享需求。参考文献全文顺序标引（含图和表）

区块链分片技术^\[7\]^旨在提高吞吐量以实现区块链系统的可扩展性。它将区块链网络节点分成多个分片（shard），每个分片只需要处理一部分交易数据，多个分片并行执行．主要的分片区块链技术，如Elastico^\[8\]^，RapidChain^\[9\]^，OmniLedger^\[10\]^，ChainSpace^\[11\]^，MVCom^\[12\]^，在提升系统吞吐量的同时，为了保证分片的安全性，采用了多种密码技术将区块链节点随机分配到各个分片中，以抵御敌手对片内节点的贿赂，防止片内恶意节点数量超过单个分片安全阈值。

将区块链验证节点随机地分配到不同分片，在理论上能最大程度的保证分片区块链的安全性，然而难以适配实际的车联网应用环境，原因在于：......因此，亟需适用于实际车联网应用的区块链分片方案，该方案面临以下挑战：

1）现有的分片算法缺乏实现片内节点距离相近与片间负载均衡的能力，仅能够取得这2个要素中单一目标的较优解，无法同时优化2个要素；

2）各个分片内恶意路侧单元的数量未知，当分片内的恶意RSU数量过多时，由恶意RSU主导的共识所产生的区块上链；

3）为保证分片系统安全性，现有方案需要定期对各个分片实行轮换和置乱等节点重新配置，带来了节点额外数据下载开销；且需要维持较大的单个片内节点数量，降低了片内共识过程效率。

针对上述挑战，本文设计了一种基于分片区块链的车联网数据共享方案。主要贡献包括3个方面：

1）提出了一种基于机器学习的分片算法，该算法基于聚类实现片内节点在地理位置上的紧凑分布，借助平衡损失实现分片间在负载上的均匀分布，实现高吞吐量的车联网区块链架构；

2）提出了基于声誉的片内共识协议，通过片内各个RSU参与共识的行为评估其声誉，高于设定的声誉阈值的RSU可参与片内共识，确保高声誉节点主导片内共识，抵御片内恶意RSU数量过多导致的安全问题；

3）提出了监督人机制，选取声誉度较高的节点作为监督人，可以随机、定期验证不同分片节点交易验证的合法性，降低了对片内节点数量较大的要求，对提升分片系统的安全和效率都有重要作用。

## 1 相关工作一级标题小四黑

## 相关工作中也要注意介绍国内的最新进展，建议阅读本刊近2-3年的相关文献，并在实验中与最先进的方法进行对比。

区块链是一种去中心化的分布式账本技术，通过将交易记录按照时间顺序连接成块，并使用密码学方法保证数据的安全性和完整性，实现了可信、不可篡改的数据存储。将区块链技术应用于智能车联网，为车联网提供了去中心化的数据共享方式，减少了单点故障的风险。在提升性能方面，文献\[13\]提出了一种车联网区块链资源管理方案，通过优化RSU和利用车辆的计算资源来提升吞吐量。文献\[14\]设计了一种增强的委托权益证明（delegated proof of stake，DPoS）共识协议，加速了交易确认同时缩短了数据共享时间，有效提升了车联网系统的吞吐量。文献\[15\]提出了一种新型的区块验证方法，每个节点存储自身的交易验证记录，如果之前已验证过发送节点的区块，就简化验证过程，从而提升系统性能。......

......现有的区块链分片方案，一般从分片节点的随机分配以保障安全性^\[8-12\]^、降低跨分片开销以提升吞吐量^\[20-22\]^、分片之间负载均衡以避免热点分片^\[12,23-25\]^、分片安全与效率平衡^\[26-27\]^、智能合约分片^\[28-29\]^等多个方面开展研究。

名词的英文展开用小写，缩写用大写。人名、地名的首字母始终大写。

在分片区块链安全性方面，文献\[9\]利用有限布谷鸟原则以保证不同分片规模的平衡，并使用可验证秘密共享来生成无偏随机性，要求新加入节点解决工作量证明[（proof of work，PoW）]{.mark}难题加入分片协议，从而抵御女巫攻击。......

**2预备知识**

**2.1** 区块链分片二级标题五号黑

将区块链分片协议进行形式化如下。给定一个区块链网络，其中包含![](media/image1.wmf)个节点，每个节点维护全网的一部分交易历史，其中有![](media/image2.wmf)个拜占庭节点。目标是将该区块链网络分割成![](media/image3.wmf)个分片，其中![](media/image4.wmf)，以提高网络的可扩展性和性能．每个分片![](media/image5.wmf)![](media/image6.wmf)包含1组节点，记作![](media/image7.wmf)，![](media/image8.wmf)，且![](media/image9.wmf)，即所有节点被分片覆盖且分片间的节点互不相交。区块链节点之间运行分片协议，输出一个集合![](media/image10.wmf)，其中包含![](media/image11.wmf)个不相交的分片或子集![](media/image12.wmf) ![](media/image13.wmf)．区块![](media/image14.wmf)中的交易![](media/image15.wmf)被定义为![](media/image16.wmf)。......正文中出现的普通变量用斜体，向量、矢量、张量用黑斜体

一致性：对于![](media/image17.wmf)，所有诚实的节点对![](media/image18.wmf)达成一致。

有效性：对于![](media/image17.wmf)和![](media/image19.wmf)，![](media/image20.wmf)。

可扩展性：![](media/image21.wmf)随着网络规模而线性增长。

**2.2** 基于声誉的共识协议

共识协议主要功能是在存在拜占庭节点的情况下，确保诚实节点能够维护一个一致的账本。声誉机制在现代社会中扮演着至关重要的角色。在人们进行决策时，往往会依赖公开的且基于声誉的排名系统来做出选择。将声誉机制与共识协议相结合可以实现以下重要目标：

......

**3基于分片区块链的车联网数据共享方案**

**3.1** 系统模型

本文设计了一个支持分片的车联网区块链架构，由车载单元（on board unit，OBU）、路侧单元和可信机构（trusted authority，TA）组成。系统模型及组件之间的关系如图1所示。

......

![](media/image22.emf)

Fig. 1 System model

图1 系统模型图

中英文图题用小五号。图内容（标目、图例、图注）尽量用中文，除变量、名称缩写外。图的背景颜色若无特殊考虑，尽量去掉，否则影响印刷效果。两个图有联系，不要分图。

OBU之间的通信以及OBU与RSU之间的通信采用IEEE 802.11p^\[36\]^或DSRC^\[37\]^协议，以上协议在数据传输过程中具有低延迟、高稳定的性质。

**3.2** 基于机器学习的分片算法

区块链中，节点数据可以被转化基于属性的表示形式，以便机器学习算法进行分析和应用于分片任务。

定义1．基于机器学习的车联网分片。给定一个由*n*个RSU组成的集合：

![](media/image23.wmf)，

其中*c~i~*代表RSU的2维位置坐标，......．基于机器学习的车联网分片需要通过机器学习模型，最小化以下目标函数：

![](media/image24.wmf)，

其中*v*代表RSU节点，*k*代表分片数，*X~i~*代表第*i*个分片，*μ~i~*代表归属于第*i*个分片的所有RSU的位置均值，![](media/image25.wmf)代表2点之间的欧氏距离。

> 公式用office编辑器或者mathtype录入，尽量避免用高版本编辑器、以及少见的符号，以免审稿和排版时不能方便使用。

**......**

基于Reputation-based SMR协议构建片内共识节点选举函数，确保高声誉的节点参与共识。具体过程如算法2所示：

算法2．片内共识节点选举函数。

输入：分片内RSU的总数*m*，分片内RSU的公钥集合*PK*，分片内RSU的声誉集合*U*，当前轮次数*q*；

输出：高声誉RSU的公钥集合*PK′*。

① 初始化![](media/image26.wmf)；

② ![](media/image27.wmf)；

③ if ![](media/image28.wmf) then

④ ![](media/image29.wmf)；

⑤ else

⑥ ![](media/image30.wmf)；

⑦ end if

算法2中，![](media/image31.wmf)代表任意RSU![](media/image32.wmf)的声誉．![](media/image33.wmf)代表难度系数，控制各个节点被选举的难度。代表所选加密哈希函数的位长。可以看出，RSU声誉越高^①^，越容易超过给定阈值，从而担任共识节点。反之亦然。

2）基于声誉的片内共识协议^①^

![f2b](media/image34.png){width="2.8673611111111112in" height="2.15in"}

Fig.3 Effect of graph convolutional layer numbers on ML-100K

图3 图卷积层数量的影响(ML-100K数据集)

> 图例尽量用不同图案、颜色深浅来区别。图的坐标值应在0.1\~1000内，若在这个范围之外，则标值改成0.1\~1000，在标目位置写 10*^n^*×标目。若数值扩大10倍，则*n*=1；若数值缩小1000倍，则*n*=-3。标目的表示形式为含义/单位。

基于声誉的片内共识协议在由片内共识节点选举函数选举出的高声誉节点中执行提议、转发与投票步骤。

![](media/image36.svg){width="3.316666666666667in" height="2.0572648731408574in"}

Fig. 4 Comparison of load variance between clusters of four algorithms

图4 4种算法的簇间负载方差对比

基于声誉的片内共识协议部署在阿里云实例上。参数如下：

**Table 1 Elastic Compute Service Configuration Parameters**

**表1 云服务器配置参数**

  ---------------- ----------------------
        名称              配置环境

    处理器核心数             32

      内存/GB               256

    本地存储/GB             100

   处理器主频/GHz           3.5

   内网带宽/GBps             25
  ---------------- ----------------------

三线表，表题为中英文，小五号黑体，表的内容尽量用中文，除变量、名称缩写外。

**6结论**

本文提出了一种基于机器学习分片的车联网区块链数据共享方案，每个分片负责存储和管理特定类型的车联网数据，使得设备间的数据共享可以并发执行，提高了数据共享的效率。为了保证分片方案的安全性，本文提出了基于声誉的共识协议和监督人机制，通过片内共识节点选举函数尽可能地保证高声誉的诚实RSU参与并完成共识。监督人机制使节点从共享数据中存储数据并获得验证其他分片数据的能力，进一步有助于以提高系统的安全性。性能评估和安全分析证明，本文方案可以实现安全高效的车联网数据共享。

**作者贡献声明：**陈骁、黄牧鸿负责方案整体设计并撰写论文；田一凡、王岩负责部分算法思路和实验方法；曹晟、张小松提出指导意见并修改论文。

评审阶段作者信息注意隐去

**参 考 文 献**

详细格式要求参照期刊主页下载中心"参考文献规范"，https://crad.ict.ac.cn/ziliaoxiazai

\[1\] Jiang Wenxian, Chen Mengjuan, Tao Jun. Federated learning with blockchain for privacy-preserving data sharing in Internet of vehicles\[J\]. China Communications, 2023, 20(3): 69-85

> 期刊文献要有年、卷、期、起止页码（或编号），期刊名称不缩写。题目的首个单词的首字母大写，其余均小写；期刊名称的实词首字母均大写。

\[2\] Le Junqing, Tan Zhouyong, Zhang Di, et al. Secure and Efficient Federated Learning for Continuous IoV Data Sharing\[J\]. Journal of Computer Research and Development, 2024, 61(9): 2199-2212.（in Chinese）

(乐俊青, 谭州勇, 张迪,等. 面向车联网数据持续共享的安全高效联邦学习\[J\]. 计算机研究与发展, 2024, 61(9): 2199-2212)

> 中文文献用双语

1.  

\[3\] [Diallo E, Dib O, Zhang San, et al]{.mark}. An improved PBFT-based consensus for securing traffic messages in VANETs\[C\] //Proc of the 12th Int Conf on Information and Communication Systems (ICICS). Piscataway, NJ: IEEE, 2021: 126-133注意：老外作者姓前名后缩写，中国人用全拼。作者超过3人，加et al。\[4\] Lee S, Seo S H. Design of a two layered blockchain-based reputation system in vehicular networks\[J\]. IEEE Transactions on Vehicular Technology, 2021, 71(2): 1209-1223

......

\[8\] Luu L, Narayanan V, Zheng Chaodong, et al. A secure sharding protocol for open blockchain[s\[C\]//Proc of the 23rd ACM SIGSAC Conf on Computer and]{.mark} [Communications Security. New York: ACM, 2016: 17-30]{.mark}

会议文献要有论文集名称、出版地、出版社、年、起止页码。注意：出版地是出版社所在的城市，不是会议开会地点。题目的首个单词的首字母大写，其余均小写；会议论文集的实词首字母均大写。

......

> \[13\] Ni Weiquan, Asheralieva A, Maple C, et al. Throughput-efficient blockchain for Internet-of-vehicles\[C/OL\]// Proc of the 64th IEEE Globecom Workshops (GC Wkshps). Piscataway, NJ: IEEE, [2021\[2024-05-07\]. <https://ieeexplore.ieee.org/abstract/document/9681973>]{.mark} 网络文献要有下载日期和链接地址

......

\[41\] Abraham I, Malkhi D, Nayak K, et al. Sync hotstuff: Simple and practical synchronous state machine replication\[C\]// Proc of the 39th IEEE Symp on Security and Privacy (SP). Piscataway, NJ: IEEE, 2020: 106-118

评审阶段作者信息注意隐去

作者介绍小五号，英文在上、中文在下。照片是正面免冠证件照，不要侧脸照，照片背景尽量简单。作者介绍主要包括：姓名、出生年月、学历、职称和研究领域。

![](media/image37.jpeg){width="0.9020833333333333in" height="1.2819444444444446in"}

**Chen X\*,** born in 1998. PhD candidate. His main research interests include blockchain and network security.

**陈\*，**199\*年生。博士研究生。主要研究方向为区块链与网络安全。

![](media/image38.jpeg){width="0.8756692913385826in" height="1.3243219597550306in"}

**Huang \*hong,** born in 1997. PhD candidate. His main research interests include blockchain and network security.

**黄\*鸿，**199\*年生。博士研究生。主要研究方向为区块链与网络安全。
