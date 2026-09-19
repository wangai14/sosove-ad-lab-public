const REFERENCE_ROLES = [
  { value: "front_full", label: "主视图", placeholder: "@产品主视图", authority: "品类、主颜色、完整外形、比例与主要结构" },
  { value: "front_detail", label: "结构细节", placeholder: "@产品结构细节图", authority: "按键、开口、接口、扣件、标签位置与其他主要结构" },
  { value: "back", label: "背面 / 底部", placeholder: "@产品背面或底部图", authority: "背面、底部、接口、支脚、封口或隐藏结构" },
  { value: "side", label: "侧面", placeholder: "@产品侧面图", authority: "厚度、侧边、侧面轮廓与连接关系" },
  { value: "fabric", label: "材质 / 质地", placeholder: "@产品材质或质地图", authority: "可见纹理、光泽、内容物质地、表面状态与物理表现" },
  { value: "extra", label: "补充参考", placeholder: "@产品补充参考图", authority: "只补充其他图片未覆盖的可观察事实" },
];

const PROMPT_ROLES = {
  overview: {
    title: "整体稳定展示",
    risk: "低风险 · 正侧背轮廓",
    task: "只证明商品类别、完整轮廓、长度和整体比例稳定",
    preferredRefs: ["front_full", "side", "back"],
    actions: [
      "模特在安静背景中自然站立，当前商品完整进入画面，停留让整体轮廓可读",
      "模特缓慢转到侧前方三分之二角度，向前迈半步后停住，展示侧面比例",
      "模特继续完成半圈转身，短暂呈现已确认的背面后回到正面自然站姿",
    ],
    cameras: ["固定全身景，人物居中，镜头不摇摆", "轻微横向跟随，到侧前方构图后停止", "镜头保持全身构图，不追求面部特写"],
    endpoint: "正面稳定定格，当前商品从上缘到下摆完整、清楚、无遮挡",
  },
  detail: {
    title: "关键结构细节",
    risk: "中风险 · 五金与结构",
    task: "只证明一个关键结构区域的形状、数量、位置和比例",
    preferredRefs: ["front_detail", "front_full", "fabric"],
    actions: [
      "模特双手自然垂下，画面停在肩带到腰部区域，让关键结构无遮挡地出现",
      "镜头保持稳定，模特只做一次轻微呼吸和肩部放松，不触摸扣件或口袋",
      "镜头缓慢后退到半身构图，确认细节与整件商品的比例关系",
    ],
    cameras: ["从正面中近景开始，不切到其他部位", "固定近景，不环绕、不变焦", "单次缓慢拉远，在半身景停止"],
    endpoint: "关键结构完整、无遮挡、边缘清楚，数量与位置可核对",
  },
  walking: {
    title: "自然走动与商品物理",
    risk: "中风险 · 动作连续性",
    task: "只证明走动时轮廓、垂落和左右结构保持一致",
    preferredRefs: ["front_full", "side", "back"],
    actions: [
      "模特从三米外自然向镜头走近两步，步幅正常，手臂放松",
      "模特从画面左侧走向右侧，保持正常速度，侧面完整进入画面",
      "模特背对镜头向前走两步后停下，商品下摆和整体轮廓保持稳定",
    ],
    cameras: ["低幅度后退的全身跟拍，结束时停止", "与人物同速横向跟拍，不超越人物", "固定全身景，不推近"],
    endpoint: "模特稳定停住，商品整体结构没有融合、闪烁、复制或变形",
  },
  routine: {
    title: "自然日常动作",
    risk: "中风险 · 手部交互",
    task: "只证明商品在一个普通生活动作中的稳定状态",
    preferredRefs: ["front_full", "front_detail", "side"],
    actions: [
      "模特站在简洁玄关旁，身体朝向门口，商品完整进入画面",
      "模特单手拿起一只无标识帆布包，另一只手不触碰商品结构",
      "模特走到门边自然停住，侧前方展示完整穿着状态",
    ],
    cameras: ["固定中全景，保持商品完整", "轻微向右平移跟随手部动作后停止", "镜头后退半步回到全身景"],
    endpoint: "模特拿包站在门边，商品结构无遮挡，动作已经结束",
  },
  activity: {
    title: "坐下起身活动验证",
    risk: "较高风险 · 关节与褶皱",
    task: "只观察坐下再起身时的活动空间与商品结构连续性，不生成效果宣称",
    preferredRefs: ["front_full", "side"],
    actions: [
      "模特站在无扶手木凳旁，侧前方完整展示商品",
      "模特自然坐下，停顿一秒后双手离开商品，保持肩带和腰部结构清楚",
      "模特平稳起身并站直，轻轻整理姿势后停止，不拉扯面料",
    ],
    cameras: ["固定全身景，不移动", "保持同一机位和焦段，完整记录坐下动作", "同一机位记录起身，结束后停留"],
    endpoint: "模特重新站直，商品恢复自然垂落，关键结构与参考一致",
  },
  lifestyle: {
    title: "通勤生活场景",
    risk: "中风险 · 环境干扰",
    task: "只把商品放进克制的真实日常环境，保持商品仍是画面主体",
    preferredRefs: ["front_full", "side"],
    actions: [
      "模特在选定场景入口自然站立，背景简单，没有人群和可读招牌",
      "模特沿直线正常行走，单手拿无标识小包，商品正面和侧面依次可见",
      "模特在自然光位置停下并转向镜头，保持放松站姿",
    ],
    cameras: ["中全景建立环境，商品仍占画面主要区域", "平稳侧向跟拍，到预定位置停止", "轻微推近到全身景后锁定"],
    endpoint: "模特在干净背景前正面站定，完整商品清楚，环境没有抢夺注意力",
  },
  ending: {
    title: "一镜到底收尾",
    risk: "低风险 · 干净终点",
    task: "只生成一个可用于剪辑结尾的连续动作和干净全身定格",
    preferredRefs: ["front_full", "side"],
    actions: [
      "模特从侧前方进入画面，沿直线自然走两步，随后缓慢转向镜头并停止",
      "模特保持自然表情和放松肩部，在完成转身后静止到视频结束",
      "不要加入新的动作、道具、换装或镜头切换",
    ],
    cameras: ["一个连续的全身跟拍，从侧前方平稳移动到正面", "人物停下时镜头同步停止", "最后保持静止全身构图"],
    endpoint: "正面全身画面稳定停留，商品从上到下完整，留出后期 CTA 安全空间",
    oneTake: true,
  },
};

const GARMENT_PROFILES = {
  universal: {
    id: "universal",
    name: "通用女装",
    garmentSpan: "商品从最上缘到下摆",
    overviewProof: "完整轮廓、长度、正侧背关系",
    detailProof: "当前档案已经确认的关键结构及其数量、位置和比例",
    motionProof: "商品随身体和重力自然运动，已确认结构保持稳定",
    activityProof: "动作发生处出现自然形变，动作结束后按真实重力稳定垂落",
    frontBackRule: "正面结构转到背面时自然离开视野；背面只显示背面参考或文字已确认的结构",
    framing: "商品上下边缘完整可见，不被手、包或画面边缘遮挡",
    exclusions: ["不变成其他服装品类", "不新增未确认的开合、口袋、五金或拼接", "不复制正面结构到背面"],
  },
  knitwear: {
    id: "knitwear",
    name: "针织上衣",
    garmentSpan: "针织上衣从肩部、袖口到下摆",
    overviewProof: "实际领口、衣长、袖型、门襟与正侧背轮廓",
    detailProof: "实际领口、门襟、扣件、口袋、罗纹或织面区域",
    motionProof: "衣身垂落、袖身摆动和针织表面在走动中的稳定表现",
    activityProof: "腋下、肘弯和身体转折处只产生符合动作的临时折线，其他区域保持当前可见织面",
    frontBackRule: "门襟、扣件和前袋在转到背面后自然离开视野；背面不得复制正面结构",
    framing: "领口、两只袖口和下摆同时在画面内，重点结构无遮挡",
    exclusions: ["不改变实际领型、开合与衣长", "不增减扣件、口袋或罗纹", "不把当前织面改成另一种粗细、毛羽或光泽"],
  },
  overalls: {
    id: "overalls",
    name: "背带裤 / 连体裤",
    garmentSpan: "肩带、胸前片、腰胯、裆部到两侧裤脚",
    overviewProof: "一体式连接关系、胸前片比例、腰胯轮廓与直筒或实际裤型",
    detailProof: "肩带、调节扣、胸前片、腰侧连接、口袋或实际五金",
    motionProof: "肩带与连接件稳定，裆部和左右裤腿分别随对应腿部运动",
    activityProof: "坐下起身时肩带、胸前片和腰侧连接保持连续，裤腿不融合",
    frontBackRule: "正面胸前片和前扣转到背面后自然离开视野；背面肩带走向只按背面依据生成",
    framing: "人物从头顶到鞋底完整入镜，肩带到两侧裤脚全部可见",
    exclusions: ["不变成普通长裤、裙装或上下分体", "不增减肩带、胸前片或连接扣件", "左右裤腿与裆部不融合"],
  },
  trousers: {
    id: "trousers",
    name: "长裤",
    garmentSpan: "裤腰、裆部、两侧裤腿到裤脚",
    overviewProof: "腰头高度、臀胯轮廓、实际裤型、裤长与两侧裤脚",
    detailProof: "腰头、门襟、扣件、褶裥、口袋或裤脚等已确认结构",
    motionProof: "裆部清楚，左右裤腿分别随对应腿部运动并保持实际裤型",
    activityProof: "坐下起身时腰头、裆部和裤腿连接连续，站直后恢复自然垂落",
    frontBackRule: "前门襟和前袋转到背面后自然离开视野；后腰与后袋只按背面依据生成",
    framing: "人物从头顶到鞋底完整入镜，裤腰和两侧裤脚都不被裁切",
    exclusions: ["不变成裙装、短裤或连体裤", "不增减腰头、门襟、口袋或褶裥", "左右裤腿与裆部不融合"],
  },
  dress: {
    id: "dress",
    name: "连衣裙 / 半身裙",
    garmentSpan: "商品上缘、腰部到连续裙摆下缘",
    overviewProof: "实际上缘或领口、腰线、裙身轮廓、裙长与连续下摆",
    detailProof: "领口或腰头、开合、褶裥、口袋、拼接和下摆等已确认结构",
    motionProof: "裙摆作为连续结构随步伐和空气自然摆动，不分裂成裤腿",
    activityProof: "坐下起身时腰部与裙摆保持连续，动作结束后按真实重力落下",
    frontBackRule: "正面上缘、腰头、开合或装饰转到背面后自然离开视野；背面只按背面依据生成",
    framing: "人物从头顶到鞋底完整入镜，裙摆下缘全程可见且不被裁切",
    exclusions: ["不分裂成裤腿或变成连体裤", "不改变实际裙长、腰线或连续下摆", "不新增未确认开衩、口袋或拼接"],
  },
  outerwear: {
    id: "outerwear",
    name: "外套",
    garmentSpan: "外套从肩部、两只袖口到下摆",
    overviewProof: "领型、开合、肩线、袖型、衣长与正侧背轮廓",
    detailProof: "领口、门襟、扣件、拉链、口袋、腰带或袖口等已确认结构",
    motionProof: "门襟、衣摆和袖身随走动自然响应，开合状态保持当前设定",
    activityProof: "抬臂或坐下时肩部、袖窿、门襟和下摆连接连续",
    frontBackRule: "前门襟、扣件和前袋转到背面后自然离开视野；背面只按背面依据生成",
    framing: "领口、两只袖口和下摆完整可见，包袋不得遮挡门襟",
    exclusions: ["不改变实际领型、开合或衣长", "不增减扣件、拉链、口袋或腰带", "不把前门襟和前袋复制到背面"],
  },
  top: {
    id: "top",
    name: "普通上衣",
    garmentSpan: "上衣从肩部、两只袖口到下摆",
    overviewProof: "领口、肩线、袖型、衣长和正侧背轮廓",
    detailProof: "领口、门襟、袖口、口袋、褶裥或下摆等已确认结构",
    motionProof: "衣身、袖身和下摆随动作自然响应，已确认结构保持稳定",
    activityProof: "抬臂或坐下时肩部、袖窿与下摆连接连续，动作停止后自然垂落",
    frontBackRule: "正面领口、门襟、口袋或装饰转到背面后自然离开视野；背面只按背面依据生成",
    framing: "领口、两只袖口和下摆完整可见，造型层不遮挡主商品",
    exclusions: ["不改变实际领型、袖型或衣长", "不新增未确认门襟、口袋或装饰", "不复制正面结构到背面"],
  },
};

const PRODUCT_PROFILES = {
  beauty: {
    id: "beauty", name: "美妆个护", subject: "同一件商品与一双干净的成年人的手", operator: "成年人只在手背或商品允许的非敏感区域做克制演示",
    productSpan: "包装、容器、开合件、标签位置与可见内容物", overviewProof: "容器外形、包装比例、颜色和开合关系", detailProof: "刷头、泵头、瓶口、盖体与可见质地", motionProof: "开盖、取用、少量延展与归位的真实顺序", activityProof: "内容物只呈现参考可见的流动、延展或附着状态",
    continuityRule: "容器、盖体、工具和内容物用量前后连续，已取出的内容物不会凭空回到容器", framing: "商品与操作手完整可见，标签和开合结构不被手指遮住",
    exclusions: ["不改变包装、刷头、泵头或盖体结构", "不虚构上脸效果、疗效、成分或即时功效", "不让内容物颜色、稠度或用量跳变"],
    scenes: ["纯净梳妆台", "自然光浴室台面", "简洁旅行收纳台"],
    beats: ["商品直立在纯净台面，包装正面先完整出现", "镜头贴近开合处与标签位置，商品保持静止", "成年人的手稳定开盖或按压一次，结构全过程可见", "只取出少量内容物，在手背做一次短距离延展", "镜头观察可见质地和光泽，停止后保持真实状态", "操作手把工具或盖体按原结构准确归位", "商品与实际附带物整齐并列，边界关系清楚", "商品回到正面干净定格，四周留出后期安全空间"],
  },
  food: {
    id: "food", name: "食品饮料", subject: "同一份商品、原包装与一双干净的成年人的手", operator: "成年人按真实食用顺序开封、倒出或摆盘",
    productSpan: "完整包装、封口、内容物形态、份量关系与盛放容器", overviewProof: "包装外形、规格感、主色与内容物对应关系", detailProof: "封口、配料可见形态、断面、气泡或蒸汽等真实状态", motionProof: "开封、倒出、切开或搅拌的真实物理过程", activityProof: "内容物只呈现参考和档案确认的流动、酥脆、软硬或热气状态",
    continuityRule: "包装开封状态、内容物总量与盛放位置前后连续，倒出或取走后数量只会合理减少", framing: "包装和内容物至少一项完整可见，食品接触面干净，不用手遮住关键形态",
    exclusions: ["不虚构口味、配方、营养、产地或健康功效", "不让内容物凭空增加、回流或变成另一种食品", "不生成不卫生接触、过量飞溅或危险烹饪"],
    scenes: ["干净餐桌", "自然光厨房台面", "简洁早餐场景"],
    beats: ["未开封包装与一份成品并列建立完整外观", "固定近景核对封口、标签位置与内容物表面", "成年人的手沿真实封口一次性开封", "内容物以正常速度倒入干净容器，份量连续", "切开或掰开一个样品，只展示真实可见断面", "完成一次搅拌、冲泡或夹取后立即停住", "包装退到背景，成品进入自然食用场景但不夸张表演", "包装与成品回到整洁终点，画面稳定留白"],
  },
  home: {
    id: "home", name: "家居日用", subject: "同一件家居商品与一双成年人的手", operator: "成年人按真实家务流程摆放、开合、装入或整理",
    productSpan: "商品完整外轮廓、支撑结构、开合件、接缝与实际附带物", overviewProof: "尺寸比例、完整形态与空间占用关系", detailProof: "连接、边缘、把手、卡扣、支脚或收纳分区", motionProof: "摆放、开合、承托或整理过程中的结构稳定", activityProof: "在合理载荷和正常动作下保持当前形态与连接关系",
    continuityRule: "开合状态、内部物品数量与摆放位置前后连续，不凭空增减配件", framing: "商品完整边缘与操作点清楚，不被家具或手臂遮挡",
    exclusions: ["不虚构承重、耐久、抗菌或安全等级", "不增减隔层、支脚、卡扣或配件", "不出现穿模、悬浮或不可能的开合方式"],
    scenes: ["真实家庭使用空间", "纯净收纳角落", "自然光客厅"],
    beats: ["商品单独放在真实空间，先交代完整轮廓和尺度", "固定近景核对边缘、连接件与分区", "成年人的手按真实方向完成一次开合", "放入一件普通无标识物品，展示实际空间关系", "从侧面观察受力点与结构连接，动作结束后停住", "取出物品并恢复初始状态，配件数量保持不变", "镜头拉宽显示商品融入日常空间但仍是主体", "整理后的商品完整定格，环境保持克制"],
  },
  kitchen: {
    id: "kitchen", name: "厨房用品", subject: "同一件厨房用品、少量普通食材与一双成年人的手", operator: "成年人在安全、干净的台面按正确方向握持和使用",
    productSpan: "主体、手柄、开口、刀口或工作面、连接件与实际配件", overviewProof: "完整外形、握持关系和台面尺度", detailProof: "手柄连接、刻度、边缘、盖体、滤网或工作面", motionProof: "握持、开合、倾倒、切分或搅拌的合理动作", activityProof: "正常使用时结构连接与食材状态变化连续",
    continuityRule: "工具、配件与食材数量前后连续，操作方向符合真实结构", framing: "工作端、手柄和食材接触点清楚，危险边缘始终受控",
    exclusions: ["不虚构锋利度、耐热、无毒或烹饪效果", "不出现危险握持、手指靠近刀口或失控飞溅", "不增减盖体、滤网、刀片或连接件"],
    scenes: ["自然光厨房台面", "干净水槽旁", "简洁餐前准备区"],
    beats: ["商品平放在干净台面，完整主体和配件一次出现", "固定近景核对手柄、工作端与连接位置", "成年人的手按正确姿势拿起商品并停顿", "使用少量普通食材完成一次低风险操作", "从侧前方观察工作端和食材接触关系", "操作结束后把商品安全放回台面", "按实际需要完成一次冲洗、擦拭或配件归位", "商品与配件整齐收尾，工作区恢复干净"],
  },
  electronics: {
    id: "electronics", name: "数码电子", subject: "同一套数码商品、实际配件与一双成年人的手", operator: "成年人按真实接口和控件做一次清楚的桌面操作",
    productSpan: "设备主体、充电盒或底座、按键、接口、指示灯、屏幕与实际配件", overviewProof: "整机外形、部件数量、颜色和收纳关系", detailProof: "接口、按键、转轴、触点、扬声器孔或屏幕边框", motionProof: "开合、取放、插接、按键与屏幕交互的正确顺序", activityProof: "指示灯或屏幕状态只按已确认功能变化，部件连接稳定",
    continuityRule: "设备、左右部件、线材和电量状态前后连续，接口方向与收纳位置保持正确", framing: "设备完整或关键操作区清楚，屏幕内容简洁且不生成乱码",
    exclusions: ["不虚构续航、音质、算力、防水或连接性能", "不增减按键、接口、耳机、线材或指示灯", "不让屏幕、灯光、转轴或插头状态无原因跳变"],
    scenes: ["纯净自然光桌面", "真实居家办公桌", "简洁通勤桌面"],
    beats: ["整套设备与实际配件在桌面建立完整外观", "微距扫过接口、按键、转轴或触点后停住", "成年人的手按真实方向打开、取出或拿起设备", "手指只按一次已确认按键或完成一次清楚触控", "连接实际线材或放回底座，接口方向全过程可见", "固定侧前方观察已确认指示灯或屏幕状态", "设备进入一个真实桌面使用动作，其他道具保持从属", "设备与配件按初始数量归位，正面干净定格"],
  },
  appliance: {
    id: "appliance", name: "家用电器", subject: "同一台家电、实际附件与一双成年人的手", operator: "成年人先确认放置与控件，再启动一个已确认的低风险功能",
    productSpan: "整机、底座、门盖、水箱、滤网、出风口、控制区与实际附件", overviewProof: "整机外形、尺寸关系、部件位置和工作朝向", detailProof: "控制区、门盖、滤网、水箱、接口或出风口", motionProof: "开合、装入、按键、工作与关机归位的完整顺序", activityProof: "只展示已确认的灯光、转动、气流、水流或声音状态",
    continuityRule: "整机和可拆部件数量、装配方向与工作状态前后连续，先关机再拆卸或清洁", framing: "整机和操作区清楚，电源、水源与高温部位不被错误操作",
    exclusions: ["不虚构功率、节能、净化、杀菌或效率", "不生成带电拆卸、湿手插电或接触高温等危险动作", "不增减滤网、水箱、门盖、按钮或附件"],
    scenes: ["真实家庭使用空间", "自然光厨房或浴室", "简洁家务区"],
    beats: ["整机在正确使用位置建立完整外观与尺度", "固定近景核对控制区和可拆部件位置", "成年人的手按正确方向装入或关闭一个部件", "只按一次已确认控件启动低风险功能", "固定机位观察已确认的工作状态并保持整机可见", "手部关机并等待工作状态完全停止", "按正确顺序取出一个可拆部件做清洁示意", "部件归位，整机恢复关机状态并干净定格"],
  },
  accessory: {
    id: "accessory", name: "鞋包配饰", subject: "同一件配饰与同一位成年使用者", operator: "成年人按商品类型完成佩戴、开合、背负或步行演示",
    productSpan: "商品完整轮廓、开合件、带体、五金、内部分区、鞋底或实际配件", overviewProof: "完整外形、尺寸比例与佩戴或携带关系", detailProof: "五金、车线、扣件、拉链、带体、鞋底或内部分区", motionProof: "开合、调节、背负、穿脱或正常步行中的结构稳定", activityProof: "与身体接触处和活动连接件按真实重力运动",
    continuityRule: "商品、肩带、鞋带、五金和内装数量前后连续，左右件不互换", framing: "商品主体完整可见，手、衣物与身体不遮住关键结构",
    exclusions: ["不虚构容量、舒适、防水、耐磨或材质成分", "不增减带体、五金、鞋带、拉链或左右件", "不让包体、鞋型或首饰比例随镜头变化"],
    scenes: ["纯净穿搭区", "真实玄关", "克制的通勤环境"],
    beats: ["商品单独完整出现，先交代轮廓与部件数量", "固定近景核对五金、车线、开合或鞋底结构", "成年人按真实方向完成一次开合、穿上或佩戴", "只调节一次带体、扣件或鞋带并停住", "完成一次正常携带或低幅度步行动作", "从侧前方观察轮廓与活动连接件", "回到静止状态，展示商品与造型层边界", "商品正面完整定格，所有部件归位"],
  },
  toy: {
    id: "toy", name: "母婴玩具", subject: "同一件商品与一双成年人的手", operator: "成年人负责组装、开启或演示，儿童只在明确需要时自然陪伴且不承担危险动作",
    productSpan: "主体、部件、连接点、活动结构、包装与实际配件", overviewProof: "完整形态、部件数量、颜色和比例", detailProof: "连接点、按钮、活动件、纹理与边缘", motionProof: "组装、推动、旋转或触发的正确顺序", activityProof: "活动件只按真实连接与已确认功能运动",
    continuityRule: "所有部件数量、装配方向与位置前后连续，小零件不凭空出现或消失", framing: "商品和成人操作手清楚，避免遮挡连接点与活动路径",
    exclusions: ["不虚构适龄、安全、益智、无毒或认证信息", "不生成婴幼儿无人看护、吞咽小件或危险玩法", "不增减零件、按钮、轮子或活动关节"],
    scenes: ["明亮家庭游戏区", "纯净儿童房桌面", "简洁收纳区"],
    beats: ["商品与所有实际配件整齐铺开建立数量关系", "固定近景核对连接点、按钮与边缘", "成年人的手按说明方向完成一步组装", "推动、旋转或触发一次已确认活动结构", "固定侧面观察活动路径到完整停止", "把可拆部件按原数量归位", "商品进入一个有人看护的自然使用场景", "商品完整收尾，配件清点清楚"],
  },
  pet: {
    id: "pet", name: "宠物用品", subject: "同一件宠物商品、一双成年人的手与一只自然状态的宠物", operator: "成年人先完成设置，宠物自主靠近或使用，不强迫摆拍",
    productSpan: "商品主体、开口、卡扣、容器、连接件与实际配件", overviewProof: "完整形态、尺寸比例与宠物使用关系", detailProof: "开口、卡扣、出水口、缝线、连接点或容器", motionProof: "安装、填充、开合或调整后宠物自然使用的过程", activityProof: "商品受力、液体、食物或活动件按真实物理变化",
    continuityRule: "商品、配件、食物或水量前后连续，宠物外观与项圈等保持一致", framing: "商品始终是主体，宠物不被束缚，操作手不遮挡关键结构",
    exclusions: ["不虚构健康、舒缓、训练或安全功效", "不强迫宠物动作、不制造惊吓或不适", "不增减卡扣、容器、牵引结构或配件"],
    scenes: ["安静家庭宠物角", "自然光客厅地面", "安全户外休息区"],
    beats: ["商品单独完整出现，先交代形态和实际配件", "固定近景核对开口、卡扣或连接位置", "成年人的手完成一次安装、填充或尺寸调整", "操作者退开，宠物自主靠近并短暂停留", "宠物自然完成一次低强度使用动作", "从侧前方观察商品受力和连接稳定", "宠物离开后商品保持真实使用状态", "成人整理商品并恢复干净终点"],
  },
  sports: {
    id: "sports", name: "运动户外", subject: "同一件运动户外商品与同一位成年人", operator: "成年人先调节与检查，再完成一次低强度、安全的真实使用动作",
    productSpan: "主体、握持区、带体、锁扣、支撑点、鞋底或实际附件", overviewProof: "完整外形、尺寸比例与正确使用关系", detailProof: "锁扣、带体、支撑、纹路、握把或连接点", motionProof: "调节、穿戴、展开、握持或低强度运动过程", activityProof: "受力点、回弹或活动连接只按真实结构变化",
    continuityRule: "商品、锁扣、带体与附件数量前后连续，调节位置保持一致", framing: "完整商品与关键受力点可见，动作空间安全",
    exclusions: ["不虚构性能、保护、防伤、耐久或专业认证", "不生成高速、极限、危险地形或错误使用", "不增减带体、锁扣、支撑或左右件"],
    scenes: ["安全室内训练区", "平整户外步道", "简洁装备整理区"],
    beats: ["商品在安全场地完整出现，交代外形和使用方向", "固定近景核对锁扣、带体与受力连接", "成年人完成一次正确调节或穿戴", "低强度完成一个完整动作后停稳", "侧前方观察关键受力点和结构响应", "解除受力并让商品恢复自然状态", "商品进入克制的真实户外或训练情境", "商品与附件归位，干净静止收尾"],
  },
  automotive: {
    id: "automotive", name: "汽车用品", subject: "同一件汽车用品、静止车辆与一双成年人的手", operator: "车辆保持熄火静止，成年人按正确位置安装、调节或演示",
    productSpan: "商品主体、安装件、卡扣、线材、接口、支撑面与实际附件", overviewProof: "完整外形、部件数量与车内安装位置关系", detailProof: "卡扣、接口、支架、线材路径、接触面或控制区", motionProof: "安装、锁定、调节、连接与拆卸的正确顺序", activityProof: "固定、转轴或控件只在安全静止状态下演示",
    continuityRule: "车辆、商品、卡扣、线材和安装位置前后连续，车辆全程静止", framing: "商品和安装点清楚，不遮挡驾驶视线或车辆安全控制",
    exclusions: ["不虚构适配车型、安全、防护或性能", "不在行驶中安装、拍摄或操作，不遮挡视线", "不增减卡扣、线材、接口或支架"],
    scenes: ["熄火静止的整洁车内", "安全停车位", "纯净汽车用品展示台"],
    beats: ["商品与实际附件在车外或展示台完整出现", "固定近景核对卡扣、接口与接触面", "车辆熄火静止，成年人把商品对准正确安装位置", "完成一次锁定、插接或角度调节", "侧面观察安装点和线材路径是否清楚", "演示一个已确认控件后立即恢复静止", "按正确顺序拆下或整理多余线材", "商品在安全位置稳定定格，车辆仍保持静止"],
  },
  universal_product: {
    id: "universal_product", name: "其他商品", subject: "同一件商品与一双成年人的手", operator: "成年人只按当前已确认结构完成一个低风险操作",
    productSpan: "商品完整外轮廓、主要结构、开合件、连接处、材质与实际附件", overviewProof: "完整外形、比例、颜色与部件数量", detailProof: "最易漂移的结构、边缘、连接与可见材质", motionProof: "拿起、旋转、开合、放回或当前商品真实允许的动作", activityProof: "商品状态只按当前可见材质、结构与重力变化",
    continuityRule: "商品、可拆部件和附件数量前后连续，操作方向服从已确认结构", framing: "商品完整或目标细节清楚，操作手不遮挡关键边缘",
    exclusions: ["不虚构功能、参数、功效、材质成分或认证", "不新增未确认部件、开口、接口或装饰", "不使用危险、不可能或与商品无关的动作"],
    scenes: ["纯净自然光桌面", "真实家庭使用空间", "简洁商业使用环境"],
    beats: ["商品单独完整出现，建立轮廓、颜色与比例", "固定近景核对最易漂移的结构和边缘", "成年人的手按真实受力点稳定拿起商品", "完成一次已确认的开合、旋转或连接动作", "从侧前方观察厚度、连接和材质状态", "操作结束后把商品准确放回原位", "商品进入一个与用途匹配的克制使用场景", "商品恢复正面完整定格并留出安全空间"],
  },
};

const PRODUCT_ROLE_BLUEPRINTS = {
  overview: { title: "外观与完整形态", risk: "低风险 · 完整外形", task: "完整外观", proof: "overviewProof", start: 0, cameras: ["固定正面全景", "缓慢侧移到三分之二角度", "固定侧前方全景"] },
  detail: { title: "关键结构与材质", risk: "中风险 · 细节漂移", task: "关键结构", proof: "detailProof", start: 1, cameras: ["受控微距近景", "固定俯拍近景", "缓慢拉远到结构中景"] },
  walking: { title: "真实操作演示", risk: "中风险 · 操作连续性", task: "真实操作流程", proof: "motionProof", start: 2, cameras: ["45度操作中景", "固定侧面操作景", "轻量跟随手部到终点"] },
  routine: { title: "日常使用流程", risk: "中风险 · 状态连续性", task: "日常使用顺序", proof: "motionProof", start: 3, cameras: ["使用者视角中景", "固定台面或空间全景", "从操作点平移到最终状态"] },
  activity: { title: "功能状态证明", risk: "较高风险 · 未确认功效", task: "已确认功能状态", proof: "activityProof", start: 4, cameras: ["固定证据近景", "侧前方状态观察景", "同机位记录停止与恢复"] },
  lifestyle: { title: "真实场景适配", risk: "中风险 · 环境干扰", task: "真实场景关系", proof: "overviewProof", start: 5, cameras: ["环境建立中全景", "平稳横移展示使用关系", "轻推到商品主构图后锁定"] },
  ending: { title: "干净商品收尾", risk: "低风险 · 干净终点", task: "剪辑收尾", proof: "overviewProof", start: 7, cameras: ["固定英雄构图", "极轻微推近后停止", "最终完全静止"] },
};

const CATEGORY_FIELD_SCHEMAS = {
  beauty: {
    title: "美妆个护专用事实",
    note: "只记录可见色号、质地和容器结构；不推断成分、疗效或上脸效果。",
    fields: [
      { key: "shade", label: "色号 / 内容物颜色", hint: "例如：低饱和豆沙红", placeholder: "只写参考图可见颜色" },
      { key: "texture", label: "可见质地", hint: "例如：透明凝露、细腻膏体", placeholder: "不推断配方或功效" },
      { key: "applicator", label: "泵头 / 刷头 / 工具", hint: "例如：斜面绒毛刷头", placeholder: "数量、形状与连接关系" },
      { key: "opening", label: "开合与取用方式", hint: "例如：旋盖后抽出刷杆", placeholder: "只写真实允许的操作顺序" },
    ],
  },
  food: {
    title: "食品饮料专用事实",
    note: "包装、内容物和开封状态必须连续；不推断口味、配方、产地或健康功效。",
    fields: [
      { key: "packaging", label: "包装与规格感", hint: "袋、盒、瓶、杯及数量", placeholder: "例如：一只自立袋，顶部热封" },
      { key: "contents", label: "内容物形态", hint: "颗粒、液体、断面、气泡", placeholder: "只写可见形态与质地" },
      { key: "opening", label: "开封方式", hint: "撕开、旋开、揭膜、拉环", placeholder: "写清方向和一次性状态变化" },
      { key: "serving", label: "盛放 / 食用终点", hint: "杯、碗、盘或原包装", placeholder: "例如：倒入透明玻璃杯后停止" },
    ],
  },
  electronics: {
    title: "数码电子专用事实",
    note: "接口、按键、指示灯和配件数量会进入商品锁；未确认功能保持不展示。",
    fields: [
      { key: "interfaces", label: "接口", hint: "类型、数量与位置", placeholder: "例如：底部一个 USB-C 接口" },
      { key: "controls", label: "按键 / 触控", hint: "数量、形状与操作方向", placeholder: "例如：右侧一枚圆形实体键" },
      { key: "indicators", label: "指示灯 / 屏幕", hint: "位置、颜色与已确认状态", placeholder: "不虚构 UI、连接或电量变化" },
      { key: "accessories", label: "实际配件", hint: "线材、底座、收纳盒等", placeholder: "只填写包装内实际存在的配件" },
    ],
  },
  home: {
    title: "家居日用专用事实", note: "重点记录开合、分区、承托关系和实际附带物，不虚构承重或耐久。",
    fields: [
      { key: "layout", label: "分区 / 空间", hint: "层数、格数、开口", placeholder: "例如：三层、左右各一格" },
      { key: "mechanism", label: "开合 / 连接", hint: "卡扣、铰链、抽拉方向", placeholder: "只写可见结构" },
      { key: "loadBoundary", label: "演示边界", hint: "允许放入的普通物品", placeholder: "不填写未经证实的承重数字" },
      { key: "accessories", label: "实际附带物", hint: "支脚、挂钩、隔板等", placeholder: "写清数量与归属" },
    ],
  },
  kitchen: {
    title: "厨房用品专用事实", note: "操作必须安全、干净且符合真实握持方向；不生成危险接触。",
    fields: [
      { key: "workingEnd", label: "工作端", hint: "刀口、滤网、杯口、搅拌端", placeholder: "写清形状与方向" },
      { key: "handle", label: "握持 / 手柄", hint: "位置、连接和防遮挡点", placeholder: "例如：右侧弧形手柄" },
      { key: "operation", label: "允许操作", hint: "倾倒、切分、搅拌等", placeholder: "只选一个低风险主动作" },
      { key: "cleaning", label: "清洁 / 归位", hint: "冲洗、擦拭或拆装边界", placeholder: "写清关停后的终点" },
    ],
  },
  appliance: {
    title: "家用电器专用事实", note: "只展示已确认控件和工作状态；先关机再拆卸或清洁。",
    fields: [
      { key: "controls", label: "控制区", hint: "按钮、旋钮、屏幕", placeholder: "数量、位置和已确认状态" },
      { key: "detachable", label: "可拆部件", hint: "水箱、滤网、门盖等", placeholder: "数量和装配方向" },
      { key: "workState", label: "工作状态", hint: "已确认灯光、转动、气流或水流", placeholder: "不推断功率或效果" },
      { key: "safetyBoundary", label: "安全边界", hint: "电源、水源、高温区域", placeholder: "例如：关机静止后再取水箱" },
    ],
  },
  accessory: {
    title: "鞋包配饰专用事实", note: "五金、带体、左右件和开合状态需要跨镜头保持一致。",
    fields: [
      { key: "hardware", label: "五金 / 开合", hint: "扣件、拉链、磁吸等", placeholder: "写清数量与位置" },
      { key: "wear", label: "佩戴 / 携带方式", hint: "手提、斜挎、穿着、佩戴", placeholder: "只选商品真实支持的方式" },
      { key: "interior", label: "内部 / 鞋底结构", hint: "有参考时填写", placeholder: "无图写未确认" },
      { key: "pairedParts", label: "左右件 / 附件", hint: "鞋、耳饰、肩带等", placeholder: "写清成对关系和数量" },
    ],
  },
  toy: {
    title: "母婴玩具专用事实", note: "成人负责操作；不推断适龄、认证、安全或益智效果。",
    fields: [
      { key: "parts", label: "零件清单", hint: "数量、颜色与大小关系", placeholder: "只写实际可见零件" },
      { key: "connections", label: "连接方式", hint: "插接、卡扣、磁吸、转轴", placeholder: "写清方向与终点" },
      { key: "movement", label: "活动结构", hint: "推动、旋转或一次触发", placeholder: "只写已确认动作" },
      { key: "adultBoundary", label: "成人操作边界", hint: "看护、组装或收纳", placeholder: "避免儿童危险动作" },
    ],
  },
  pet: {
    title: "宠物用品专用事实", note: "成人先设置，宠物自主靠近；不强迫摆拍或制造不适。",
    fields: [
      { key: "setup", label: "安装 / 调节", hint: "卡扣、尺寸、容器位置", placeholder: "写清成人先完成的动作" },
      { key: "opening", label: "开口 / 接触点", hint: "饮水口、入口、牵引连接", placeholder: "写清商品与宠物接触关系" },
      { key: "interaction", label: "宠物自然动作", hint: "靠近、饮水、躺卧等", placeholder: "只选一个低强度动作" },
      { key: "consumable", label: "食物 / 水量", hint: "如适用，记录起止状态", placeholder: "数量必须连续" },
    ],
  },
  sports: {
    title: "运动户外专用事实", note: "先调节和检查，再做一次低强度安全动作；不虚构保护或性能。",
    fields: [
      { key: "adjustment", label: "调节结构", hint: "带体、锁扣、长度", placeholder: "写清调节位置" },
      { key: "loadPoint", label: "受力点", hint: "握把、支撑、鞋底等", placeholder: "只写可见结构响应" },
      { key: "motion", label: "安全动作", hint: "一个完整低强度动作", placeholder: "不使用极限或危险动作" },
      { key: "accessories", label: "装备附件", hint: "收纳袋、配件、左右件", placeholder: "数量保持连续" },
    ],
  },
  automotive: {
    title: "汽车用品专用事实", note: "车辆保持熄火静止；不在行驶中安装、拍摄或操作。",
    fields: [
      { key: "mount", label: "安装位置", hint: "出风口、座椅、台面等", placeholder: "写清车辆内相对位置" },
      { key: "interfaces", label: "卡扣 / 接口 / 线材", hint: "数量、方向和走线", placeholder: "不增减连接件" },
      { key: "adjustment", label: "允许调节", hint: "角度、长度或锁定", placeholder: "只做一次静止状态演示" },
      { key: "vehicleBoundary", label: "车辆安全边界", hint: "熄火、停车、不遮挡视线", placeholder: "写清禁止区域" },
    ],
  },
  apparel: {
    title: "服饰专用事实", note: "版型、开合、口袋和下摆只服从当前商品；不套用其他服装结构。",
    fields: [
      { key: "neckWaist", label: "领口 / 腰头", hint: "按当前品类填写", placeholder: "形状、位置与层数" },
      { key: "closure", label: "开合 / 扣件", hint: "纽扣、拉链、搭扣等", placeholder: "写清数量与位置" },
      { key: "pockets", label: "口袋 / 拼接", hint: "有则填写，无则未确认", placeholder: "不从正面复制到背面" },
      { key: "hemLength", label: "衣长 / 裤长 / 下摆", hint: "完整穿着轮廓", placeholder: "只写当前可见比例" },
    ],
  },
  universal_product: {
    title: "通用商品专用事实", note: "只记录一个可执行操作和最容易漂移的结构；未知功能不补全。",
    fields: [
      { key: "operation", label: "主要操作", hint: "拿起、旋转、开合或连接", placeholder: "选择一个低风险动作" },
      { key: "movingParts", label: "活动部件", hint: "转轴、盖体、滑轨等", placeholder: "数量、方向和终点" },
      { key: "label", label: "标签 / 文字位置", hint: "只记录位置，不要求生成新文字", placeholder: "例如：正面下方一处标签" },
      { key: "accessories", label: "实际配件", hint: "商品本体以外的附带物", placeholder: "写清数量和归属" },
    ],
  },
};

const PLATFORM_PRESETS = {
  tiktok: { label: "TikTok 竖屏广告", ratio: "9:16", duration: 15, pace: "前置动作钩子，快速进入商品证明", focus: "第一秒出现完整商品和一次可见动作", safeArea: "主体保持在中央安全区；画内不生成字幕，文案与 CTA 留到后期。" },
  facebook: { label: "Facebook / Meta 信息流", ratio: "4:5", duration: 15, pace: "问题或结果先行，随后给出可见证据", focus: "完整商品、关键结构与真实使用按证据顺序出现", safeArea: "为上下界面和后期优惠卡留白；避免未经证实的身体或功效对比。" },
  instagram: { label: "Instagram Reels", ratio: "9:16", duration: 15, pace: "视觉先行，动作简洁，结尾便于自然循环", focus: "商品轮廓、材质变化和干净终点保持统一构图", safeArea: "商品与手部保持在中部区域，避免边缘关键细节和生成画内文字。" },
  amazon: { label: "Amazon 商品视频", ratio: "16:9", duration: 15, pace: "克制、清楚、按功能证据推进", focus: "先完整外观，再结构细节，最后一次真实操作", safeArea: "干净背景和真实比例优先；不生成价格、排名、评价或未确认宣称。" },
  independent: { label: "独立站产品演示", ratio: "16:9", duration: 15, pace: "完整使用流程，给关键细节更多停留", focus: "商品问题、操作过程和稳定终点形成清楚顺序", safeArea: "主体保留多画幅裁切余量；CTA、字幕和品牌排版在后期完成。" },
  custom: { label: "自定义设置", ratio: "", duration: 0, pace: "使用当前手动时长和画幅", focus: "由当前商品事实与提示词任务决定", safeArea: "保持商品与关键操作远离边缘；最终规格按实际投放位置核对。" },
};

const PROMPT_TEMPLATES = {
  universal: {
    id: "universal",
    name: "通用商品安全规则",
    source: "页面通用规则",
    summary: "只保留商品事实优先、镜头降载和基础防跑偏",
    promptRule: "把本条作为非叙事商品展示：只证明主任务，不编造人物剧情；5秒单镜头，10秒最多2镜头；15秒按当前提示词模式执行高还原8镜头或精简稳定3镜头；每镜头一个动作、一个主要视角和一个完成终点；商品事实只来自当前档案与对应参考图，同一批提示词的开场、任务与第一机位必须不同。",
    rules: ["商品事实与模板拍法分层", "每镜头一个动作和一个主要运镜", "自然实拍，文字与音频包装留到后期"],
    modules: ["商品事实", "镜头降载", "基础防跑偏"],
    qualityGate: ["不补全未知结构", "每条只有一个主任务", "字幕与BGM留到后期"],
  },
  adaptive: {
    id: "adaptive",
    name: "新品自适应安全规则",
    source: "V领纯色长袖针织衫_Seedance提示词合集(1).txt · 19套 / 161镜头完整规则重构",
    summary: "保留原模板的完整商品锁、构图、物理、连续性和修复逻辑，并按新品品类动态改写",
    promptRule: "执行完整新品自适应结构：当前商品事实和参考职责是唯一依据；先锁品类边界、颜色、轮廓、正背结构、面料表现与易漂移锚点，再按当前品类生成构图、动作、物理和正背面隔离规则。5秒单镜头，10秒最多2镜头；15秒高还原模式直接生成8个编号镜头，精简稳定模式生成同一场景3个主镜头；每镜头一个主动作、一个主要视角、一个展示目标和一个可核对终点。不得继承模板旧商品、人物、穿搭、地点或功效宣称。",
    rules: ["当前商品事实与参考职责拥有最高优先级", "主视图、背面或底部、侧面和材质分别由对应权威参考控制", "15秒精细版严格保留镜头1—8及各自时间段", "每个镜头包含动作、运镜、展示目标和终点", "按产品品类编译操作、构图与物理约束", "人物、手、宠物、道具和环境为从属层且全程连续", "同一批提示词的钩子、主任务、第一动作和首个机位不重复", "文字、配音、BGM、价格和CTA留到后期"],
    modules: ["参考角色表", "非叙事主任务", "整体人物与场景", "公共商品主锁", "正背面隔离", "构图硬要求", "分镜时间轴", "面料与动作物理", "连续性与道具", "精简负面约束", "失败修复", "后期边界"],
    qualityGate: ["不补全未知背面、底部或结构", "不串入旧商品事实", "每镜头只有一个主动作和一个主要运镜", "每段写明展示目标与终点", "产品优先于人物、环境和风格", "功效、参数与材质成分只用已确认事实", "批次首镜头差异可核对", "画面保持无文字、无设备、无水印", "参考占位符逐字不变"],
  },
};

const SEEDANCE_SKILL_COMPILER = Object.freeze({
  name: "Seedance 2.0 Skill OS",
  version: "6.7.0",
  fashionSkill: "Universal Product Prompt Router",
  profile: "中文通用商品短视频提示词",
  order: ["参考职责", "主体与动作", "运镜与终点", "物理光线", "声音", "商品保持"],
  forbiddenFillers: ["电影感", "高级感", "氛围感", "大片感", "史诗级", "4K", "8K", "顶级品质"],
});

const COUNT_ROLE_MAP = {
  3: ["overview", "detail", "walking"],
  5: ["overview", "detail", "walking", "routine", "ending"],
  7: ["overview", "detail", "walking", "routine", "activity", "lifestyle", "ending"],
};

const DENSE_TIMELINE_RANGES = [
  ["00:00", "00:02"],
  ["00:02", "00:03.5"],
  ["00:03.5", "00:05"],
  ["00:05", "00:07"],
  ["00:07", "00:08.5"],
  ["00:08.5", "00:10"],
  ["00:10", "00:12.5"],
  ["00:12.5", "00:15"],
];

const DIRECT_SHOT_INDEX_MAP = Object.fromEntries(
  ["overview", "detail", "walking", "routine", "activity", "lifestyle", "ending"]
    .map((key) => [key, [0, 1, 2]]),
);

const DENSE_ROLE_FRAMINGS = {
  overview: ["正面中全景", "侧前方中全景", "正背轮廓中全景"],
  detail: ["关键结构中近景", "关键结构固定特写", "结构比例中景"],
  walking: ["正面走动全身景", "侧向跟拍全身景", "运动终点全身景"],
  routine: ["室内中全景", "拿包动作中景", "门边完整商品景"],
  activity: ["动作前完整商品景", "活动过程完整商品景", "恢复状态完整商品景"],
  lifestyle: ["生活场景中全景", "日常走动全身景", "自然光终点全身景"],
  ending: ["进入画面全身景", "自然转身全身景", "干净终点全身景"],
};

const STORAGE_KEY = "sosove-fashion-prompt-workbench-v1";
const HISTORY_STORAGE_KEY = "sosove-product-prompt-history-v1";
const MAX_HISTORY_VERSIONS = 12;

const state = {
  references: [],
  prompts: [],
  localPrompts: [],
  packText: "",
  directPackText: "",
  product: null,
  commonLock: "",
  repairs: [],
  template: null,
  generation: null,
  generationError: "",
  optimization: null,
  optimizationError: "",
  aiConfig: { hasApiKey: false, baseUrl: "", model: "", apiKeyPreview: "" },
  aiBusy: false,
  aiProbeBusy: false,
  aiProbe: null,
  pendingAnalysis: null,
  categoryDrafts: {},
  activeCategorySchemaKey: "",
  referenceConsistency: null,
  fidelityReport: null,
  history: [],
};

const elements = {
  form: document.querySelector("#product-form"),
  productName: document.querySelector("#product-name"),
  productNameError: document.querySelector("#product-name-error"),
  category: document.querySelector("#category"),
  color: document.querySelector("#color"),
  silhouette: document.querySelector("#silhouette"),
  frontStructure: document.querySelector("#front-structure"),
  backStructure: document.querySelector("#back-structure"),
  material: document.querySelector("#material"),
  stylingBoundary: document.querySelector("#styling-boundary"),
  fragileAnchors: document.querySelector("#fragile-anchors"),
  categoryDetailTitle: document.querySelector("#category-detail-title"),
  categoryDetailNote: document.querySelector("#category-detail-note"),
  categoryDetailGrid: document.querySelector("#category-detail-grid"),
  templatePreset: document.querySelector("#template-preset"),
  templateResolution: document.querySelector("#template-resolution"),
  templateResolutionName: document.querySelector("#template-resolution-name"),
  templateResolutionDetail: document.querySelector("#template-resolution-detail"),
  promptMode: document.querySelector("#prompt-mode"),
  promptModeNote: document.querySelector("#prompt-mode-note"),
  durationModeLabel: document.querySelector("#duration-mode-label"),
  durationDensityNote: document.querySelector("#duration-density-note"),
  duration: document.querySelector("#duration"),
  promptCount: document.querySelector("#prompt-count"),
  ratio: document.querySelector("#ratio"),
  market: document.querySelector("#market"),
  platformPreset: document.querySelector("#platform-preset"),
  platformPresetCard: document.querySelector("#platform-preset-card"),
  platformPresetRatio: document.querySelector("#platform-preset-ratio"),
  platformPresetPace: document.querySelector("#platform-preset-pace"),
  platformPresetFocus: document.querySelector("#platform-preset-focus"),
  platformPresetSafeArea: document.querySelector("#platform-preset-safe-area"),
  generateButton: document.querySelector("#generate-button"),
  referenceInput: document.querySelector("#reference-input"),
  uploadButton: document.querySelector("#upload-button"),
  referenceGrid: document.querySelector("#reference-grid"),
  referenceCount: document.querySelector("#reference-count"),
  referenceConsistencyPanel: document.querySelector("#reference-consistency-panel"),
  referenceConsistencyScore: document.querySelector("#reference-consistency-score"),
  referenceConsistencySummary: document.querySelector("#reference-consistency-summary"),
  referenceConsistencyList: document.querySelector("#reference-consistency-list"),
  referenceConsistencyState: document.querySelector("#reference-consistency-state"),
  outputSummary: document.querySelector("#output-summary"),
  emptyOutput: document.querySelector("#empty-output"),
  outputContent: document.querySelector("#output-content"),
  referenceMapList: document.querySelector("#reference-map-list"),
  commonLock: document.querySelector("#common-lock"),
  promptList: document.querySelector("#prompt-list"),
  qcList: document.querySelector("#qc-list"),
  repairList: document.querySelector("#repair-list"),
  copyDirectAllButton: document.querySelector("#copy-direct-all-button"),
  copyAllButton: document.querySelector("#copy-all-button"),
  downloadButton: document.querySelector("#download-button"),
  loadDemoButton: document.querySelector("#load-demo-button"),
  resetProductButton: document.querySelector("#reset-product-button"),
  emptyDemoButton: document.querySelector("#empty-demo-button"),
  aiBaseUrl: document.querySelector("#ai-config-base-url"),
  aiModel: document.querySelector("#ai-config-model"),
  aiApiKey: document.querySelector("#ai-config-key"),
  aiKeyPreview: document.querySelector("#ai-key-preview"),
  aiModelStatus: document.querySelector("#ai-model-status"),
  endpointWarning: document.querySelector("#endpoint-warning"),
  saveAiConfigButton: document.querySelector("#save-ai-config-button"),
  testAiConfigButton: document.querySelector("#test-ai-config-button"),
  aiConfigTestResult: document.querySelector("#ai-config-test-result"),
  aiConfigTestState: document.querySelector("#ai-config-test-state"),
  aiConfigTestDetail: document.querySelector("#ai-config-test-detail"),
  analyzeProductButton: document.querySelector("#analyze-product-button"),
  aiAnalysisState: document.querySelector("#ai-analysis-state"),
  aiAnalysisDetail: document.querySelector("#ai-analysis-detail"),
  aiReviewPanel: document.querySelector("#ai-review-panel"),
  aiReviewList: document.querySelector("#ai-review-list"),
  applyAiReviewButton: document.querySelector("#apply-ai-review-button"),
  discardAiReviewButton: document.querySelector("#discard-ai-review-button"),
  optimizePromptsButton: document.querySelector("#optimize-prompts-button"),
  aiOptimizeState: document.querySelector("#ai-optimize-state"),
  aiOptimizeDetail: document.querySelector("#ai-optimize-detail"),
  aiOptimizeUsage: document.querySelector("#ai-optimize-usage"),
  fidelityScorePanel: document.querySelector("#fidelity-score-panel"),
  fidelityScoreValue: document.querySelector("#fidelity-score-value"),
  fidelityScoreGrade: document.querySelector("#fidelity-score-grade"),
  fidelityScoreSummary: document.querySelector("#fidelity-score-summary"),
  fidelityDimensions: document.querySelector("#fidelity-dimensions"),
  fidelitySuggestions: document.querySelector("#fidelity-suggestions"),
  versionHistoryCount: document.querySelector("#version-history-count"),
  versionHistoryList: document.querySelector("#version-history-list"),
  historyCompareLeft: document.querySelector("#history-compare-left"),
  historyCompareRight: document.querySelector("#history-compare-right"),
  historyCompareButton: document.querySelector("#history-compare-button"),
  historyCompareResult: document.querySelector("#history-compare-result"),
  toastRegion: document.querySelector("#toast-region"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function clean(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function categorySchemaKey(product = {}) {
  const profile = inferProductProfile(product);
  return isApparelProfile(profile) ? "apparel" : (CATEGORY_FIELD_SCHEMAS[profile.id] ? profile.id : "universal_product");
}

function captureCategoryDetails() {
  const key = state.activeCategorySchemaKey;
  if (!key || !elements.categoryDetailGrid) return {};
  const details = {};
  elements.categoryDetailGrid.querySelectorAll("[data-category-detail]").forEach((input) => {
    const value = clean(input.value);
    if (value) details[input.dataset.categoryDetail] = value;
  });
  state.categoryDrafts[key] = details;
  return details;
}

function collectCategoryDetails() {
  captureCategoryDetails();
  return { ...(state.categoryDrafts[state.activeCategorySchemaKey] || {}) };
}

function renderCategoryFields({ preserve = true, values = null } = {}) {
  if (!elements.categoryDetailGrid) return;
  if (preserve) captureCategoryDetails();
  const product = {
    name: elements.productName.value,
    category: elements.category.value,
    frontStructure: elements.frontStructure.value,
    material: elements.material.value,
    anchors: elements.fragileAnchors.value,
  };
  const key = categorySchemaKey(product);
  const schema = CATEGORY_FIELD_SCHEMAS[key] || CATEGORY_FIELD_SCHEMAS.universal_product;
  state.activeCategorySchemaKey = key;
  if (values && typeof values === "object") state.categoryDrafts[key] = { ...values };
  const current = state.categoryDrafts[key] || {};
  elements.categoryDetailTitle.textContent = schema.title;
  elements.categoryDetailNote.textContent = schema.note;
  elements.categoryDetailGrid.innerHTML = schema.fields.map((field) => `
    <label class="category-detail-field">
      <span>${escapeHtml(field.label)}<small>${escapeHtml(field.hint)}</small></span>
      <input type="text" maxlength="220" data-category-detail="${escapeHtml(field.key)}" value="${escapeHtml(current[field.key] || "")}" placeholder="${escapeHtml(field.placeholder)}">
    </label>
  `).join("");
}

function platformStrategyForSelection() {
  const key = clean(elements.platformPreset?.value) || "custom";
  const preset = PLATFORM_PRESETS[key] || PLATFORM_PRESETS.custom;
  return {
    label: preset.label,
    pace: preset.pace,
    focus: preset.focus,
    safeArea: preset.safeArea,
  };
}

function renderPlatformPreset({ applySettings = false } = {}) {
  if (!elements.platformPreset) return;
  const key = clean(elements.platformPreset.value) || "custom";
  const preset = PLATFORM_PRESETS[key] || PLATFORM_PRESETS.custom;
  if (applySettings && key !== "custom") {
    elements.ratio.value = preset.ratio;
    elements.duration.value = String(preset.duration);
  }
  const ratio = key === "custom" ? clean(elements.ratio.value) : preset.ratio;
  const duration = key === "custom" ? Number(elements.duration.value || 15) : preset.duration;
  elements.platformPresetRatio.textContent = `${ratio} · ${duration} 秒`;
  elements.platformPresetPace.textContent = preset.pace;
  elements.platformPresetFocus.textContent = preset.focus;
  elements.platformPresetSafeArea.textContent = preset.safeArea;
  elements.platformPresetCard.dataset.platform = key;
  renderPromptModeNote();
}

function applyPlatformPreset() {
  renderPlatformPreset({ applySettings: true });
  saveForm();
  const preset = PLATFORM_PRESETS[elements.platformPreset.value] || PLATFORM_PRESETS.custom;
  toast(`${preset.label}预设已应用；可以继续手动调整画幅和时长。`);
}

function isFidelityMode(product = {}) {
  return clean(product.promptMode || elements.promptMode?.value || "fidelity") !== "stable";
}

function expectedDirectShotCount(product = {}) {
  const duration = Number(product.duration || elements.duration?.value || 15);
  if (duration >= 15) return isFidelityMode(product) ? 8 : 3;
  if (duration >= 10) return 2;
  return 1;
}

function renderPromptModeNote() {
  if (!elements.promptMode) return;
  const fidelity = isFidelityMode({ promptMode: elements.promptMode.value });
  if (elements.promptModeNote) {
    elements.promptModeNote.textContent = fidelity
      ? "完整商品锁直接写入每条提示词；15秒使用8镜头，并保留主体连续性、品类物理和自然演示。"
      : "15秒压缩为同一场景3镜头；仅在高还原版执行不全、动作跳过或结构漂移时使用。";
  }
  if (elements.durationModeLabel) elements.durationModeLabel.textContent = fidelity ? "15秒高还原8镜头" : "15秒稳定3镜头";
  if (elements.durationDensityNote) {
    elements.durationDensityNote.textContent = fidelity
      ? "高还原模式直接生成完整8镜头；每条都自动携带核心商品锁，不需要手工拼接。"
      : "稳定模式保留完整核心商品锁，但把15秒动作负载降为同一地点3个主镜头。";
  }
}

function isKnitwearProduct(product = {}) {
  const evidence = [product.name, product.category, product.frontStructure, product.material, product.anchors]
    .map(clean)
    .join(" ");
  return /针织|开衫|毛衣|线衫|罗纹|ribbed|cardigan|knit/i.test(evidence);
}

function inferGarmentProfile(product = {}) {
  const evidence = [product.name, product.category, product.silhouette, product.frontStructure, product.backStructure, product.anchors]
    .map(clean)
    .join(" ");
  if (isKnitwearProduct(product)) return GARMENT_PROFILES.knitwear;
  if (/背带|连体裤|jumpsuit|overall/i.test(evidence)) return GARMENT_PROFILES.overalls;
  if (/连衣裙|半身裙|裙装|裙摆|dress|skirt/i.test(evidence)) return GARMENT_PROFILES.dress;
  if (/长裤|短裤|牛仔裤|阔腿裤|直筒裤|西裤|裤装|trouser|pants|jeans/i.test(evidence)) return GARMENT_PROFILES.trousers;
  if (/外套|大衣|风衣|夹克|西装|coat|jacket|blazer/i.test(evidence)) return GARMENT_PROFILES.outerwear;
  if (/上衣|衬衫|T恤|罩衫|背心|吊带|blouse|shirt|top/i.test(evidence)) return GARMENT_PROFILES.top;
  return GARMENT_PROFILES.universal;
}

function normalizeApparelProfile(profile = GARMENT_PROFILES.universal) {
  return {
    ...profile,
    isApparel: true,
    productSpan: profile.garmentSpan,
    subject: "同一位原创成年模特与同一件服饰商品",
    operator: "模特以自然站立、转身和正常步行展示商品",
    continuityRule: profile.frontBackRule,
    scenes: ["安静的浅色室内", "简洁玄关", "普通住宅街道"],
  };
}

function inferProductProfile(product = {}) {
  const evidence = [product.name, product.category, product.silhouette, product.frontStructure, product.backStructure, product.material, product.anchors]
    .map(clean)
    .join(" ");
  if (/美妆|个护|口红|唇釉|粉底|眼影|睫毛|面霜|精华|乳液|洗护|香水|cosmetic|beauty|lipstick|skincare/i.test(evidence)) return PRODUCT_PROFILES.beauty;
  if (/食品|饮料|零食|咖啡|茶|果汁|燕麦|饼干|面包|糖果|酒|food|drink|snack|beverage/i.test(evidence)) return PRODUCT_PROFILES.food;
  if (/宠物|猫|狗|牵引|猫砂|宠物饮水|pet|cat|dog/i.test(evidence)) return PRODUCT_PROFILES.pet;
  if (/汽车|车载|车内|行车|方向盘|座椅|支架|automotive|car accessory/i.test(evidence)) return PRODUCT_PROFILES.automotive;
  if (/运动|户外|健身|瑜伽|露营|登山|球拍|哑铃|sports|outdoor|fitness|camping/i.test(evidence)) return PRODUCT_PROFILES.sports;
  if (/母婴|玩具|积木|童车|玩偶|拼图|toy|baby|kids/i.test(evidence)) return PRODUCT_PROFILES.toy;
  if (/鞋|包|手袋|背包|首饰|项链|耳环|手表|腰带|shoe|bag|jewelry|accessor/i.test(evidence)) return PRODUCT_PROFILES.accessory;
  if (/家电|风扇|吹风|吸尘|加湿|空气炸|咖啡机|电饭|洗衣|冰箱|appliance|vacuum|dryer/i.test(evidence)) return PRODUCT_PROFILES.appliance;
  if (/数码|电子|耳机|手机|键盘|鼠标|相机|音箱|充电|显示器|蓝牙|digital|electronic|earbud|headphone|keyboard|mouse|camera|bluetooth/i.test(evidence)) return PRODUCT_PROFILES.electronics;
  if (/厨房|锅|刀|杯|餐具|砧板|烘焙|榨汁|kitchen|cookware|utensil/i.test(evidence)) return PRODUCT_PROFILES.kitchen;
  if (/家居|日用|收纳|置物|清洁|床品|灯具|家具|home|storage|organizer|furniture/i.test(evidence)) return PRODUCT_PROFILES.home;
  if (/背带|连体裤|连衣裙|半身裙|裤|外套|大衣|风衣|夹克|上衣|衬衫|T恤|针织|开衫|服装|服饰|衣|裙|jumpsuit|overall|dress|skirt|trouser|pants|coat|jacket|shirt|apparel|fashion/i.test(evidence)) {
    return normalizeApparelProfile(inferGarmentProfile(product));
  }
  return PRODUCT_PROFILES.universal_product;
}

function isApparelProfile(profile = {}) {
  return Boolean(profile.isApparel || GARMENT_PROFILES[profile.id]);
}

function productActorLabel(profile = {}) {
  return profile.subject || "同一件商品与一双成年人的手";
}

function productMaterialLabel(profile = {}) {
  return isApparelProfile(profile) ? "可见面料表现" : "可见材质、质地或工作状态";
}

function recommendedScenesForProfile(profile = {}) {
  return Array.isArray(profile.scenes) && profile.scenes.length
    ? profile.scenes
    : PRODUCT_PROFILES.universal_product.scenes;
}

function resolvePromptTemplate(product = {}) {
  const requested = clean(product.templatePreset || elements.templatePreset?.value || "auto");
  const detectedProfile = inferProductProfile(product);
  const profile = requested === "knitwear"
    ? normalizeApparelProfile(GARMENT_PROFILES.knitwear)
    : requested === "apparel"
      ? normalizeApparelProfile(inferGarmentProfile(product))
      : requested === "hardgoods" || requested === "universal"
        ? PRODUCT_PROFILES.universal_product
        : detectedProfile;
  const id = requested === "universal" ? "universal" : "adaptive";
  const base = PROMPT_TEMPLATES[id] || PROMPT_TEMPLATES.universal;
  const reason = requested === "knitwear"
    ? "已强制使用针织上衣物理安全规则；商品事实仍只读取当前档案，镜头由 AI 重新构思。"
    : requested === "apparel"
      ? `已强制服饰穿着规则，并匹配“${profile.name}”的构图与物理。`
      : requested === "hardgoods"
        ? "已强制硬质商品桌面操作规则；不会加入模特走秀或服装动作。"
    : requested === "universal"
      ? "已选择通用商品安全规则；只使用已确认的低风险操作。"
      : `已自动匹配“${profile.name}”产品路由；将使用该品类专属动作、机位、连续性和失败约束。`;
  return { ...base, requested, reason, profile };
}

function compactTemplate(template) {
  return {
    id: template.id,
    name: template.name,
    source: template.source,
    summary: template.summary,
    promptRule: template.promptRule,
    rules: [...template.rules],
    modules: [...(template.modules || [])],
    qualityGate: [...(template.qualityGate || [])],
    profile: {
      id: template.profile.id,
      name: template.profile.name,
      garmentSpan: template.profile.garmentSpan || template.profile.productSpan,
      productSpan: template.profile.productSpan || template.profile.garmentSpan,
      overviewProof: template.profile.overviewProof,
      detailProof: template.profile.detailProof,
      motionProof: template.profile.motionProof,
      activityProof: template.profile.activityProof,
      frontBackRule: template.profile.frontBackRule,
      continuityRule: template.profile.continuityRule || template.profile.frontBackRule,
      subject: productActorLabel(template.profile),
      operator: template.profile.operator || "成年人完成低风险商品演示",
      framing: template.profile.framing,
      exclusions: [...template.profile.exclusions],
    },
    promptArchitecture: "模式与非叙事任务 → 参考职责 → 整体设定 → 商品锁定 → 构图硬要求 → 时间轴（动作/镜头/展示/段落终点）→ 连续性与物理 → 声音 → 总终点 → 精简负面约束 → 后期边界",
  };
}

function compactCompilerProfile() {
  return {
    name: SEEDANCE_SKILL_COMPILER.name,
    version: SEEDANCE_SKILL_COMPILER.version,
    fashionSkill: SEEDANCE_SKILL_COMPILER.fashionSkill,
    profile: SEEDANCE_SKILL_COMPILER.profile,
    order: [...SEEDANCE_SKILL_COMPILER.order],
  };
}

function renderTemplatePanel() {
  if (!elements.templateResolution) return;
  const template = resolvePromptTemplate({
    name: elements.productName.value,
    category: elements.category.value,
    frontStructure: elements.frontStructure.value,
    material: elements.material.value,
    anchors: elements.fragileAnchors.value,
    templatePreset: elements.templatePreset.value,
  });
  elements.templateResolution.dataset.template = template.id;
  elements.templateResolutionName.textContent = `${template.name} · ${template.profile.name}`;
  elements.templateResolutionDetail.textContent = `${template.reason} 推荐场景：${recommendedScenesForProfile(template.profile).join("、")}。`;
}

function toast(message, tone = "info") {
  const item = document.createElement("div");
  item.className = `toast${tone === "error" ? " is-error" : ""}`;
  item.textContent = message;
  elements.toastRegion.append(item);
  window.setTimeout(() => item.remove(), 3400);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) throw new Error(payload.error || `请求失败：${response.status}`);
  return payload;
}

function isInsecureRemoteEndpoint(value = elements.aiBaseUrl.value) {
  try {
    const url = new URL(value);
    const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
    return url.protocol === "http:" && !localHosts.has(url.hostname);
  } catch {
    return false;
  }
}

function renderEndpointWarning() {
  elements.endpointWarning.hidden = !isInsecureRemoteEndpoint();
}

function renderAiConfigTestResult(item = null, mode = "idle") {
  if (!elements.aiConfigTestResult) return;
  const latency = Number(item?.latencyMs || 0) > 0 ? `${Math.round(Number(item.latencyMs))}ms` : "";
  const status = item?.httpStatus ? `HTTP ${item.httpStatus}` : "";
  let stateName = mode;
  let title = "模型尚未测试";
  let detail = "点击“测试模型连接”会发送一个极短文本请求；不会上传商品图片。";
  if (mode === "testing") {
    title = "正在试调用当前模型";
    detail = "等待节点完成鉴权并返回极短文本，请勿重复点击。";
  } else if (item) {
    stateName = item.ok ? "success" : item.networkOk ? "warning" : "error";
    title = item.ok
      ? "模型可正常调用"
      : item.authOk === false
        ? "API Key 鉴权失败"
        : item.networkOk
          ? "节点已响应，但模型调用失败"
          : "模型节点无法连接";
    const meta = [clean(item.model), latency, status, item.reply ? `回复：${clean(item.reply)}` : ""].filter(Boolean).join(" · ");
    detail = [clean(item.message) || "测试已完成", meta].filter(Boolean).join("｜");
  }
  state.aiProbe = item;
  elements.aiConfigTestResult.dataset.state = stateName;
  elements.aiConfigTestState.textContent = title;
  elements.aiConfigTestDetail.textContent = detail;
  elements.aiConfigTestResult.title = item?.endpoint ? `${item.endpoint}\n${detail}` : detail;
}

function invalidateAiConfigTestResult() {
  if (!state.aiProbe || state.aiProbeBusy) return;
  state.aiProbe = null;
  renderAiConfigTestResult(null, "idle");
  elements.aiConfigTestState.textContent = "配置已修改，请重新测试";
}

function renderAiConfig(config = {}) {
  state.aiConfig = {
    hasApiKey: Boolean(config.hasApiKey),
    baseUrl: clean(config.baseUrl),
    model: clean(config.model),
    apiKeyPreview: clean(config.apiKeyPreview),
  };
  elements.aiBaseUrl.value = state.aiConfig.baseUrl || elements.aiBaseUrl.value;
  elements.aiModel.value = state.aiConfig.model || elements.aiModel.value;
  elements.aiApiKey.value = "";
  elements.aiKeyPreview.textContent = state.aiConfig.hasApiKey
    ? `已保存 ${state.aiConfig.apiKeyPreview || "••••••••"}`
    : "尚未配置";
  const insecure = isInsecureRemoteEndpoint(state.aiConfig.baseUrl);
  elements.aiModelStatus.dataset.state = state.aiConfig.hasApiKey ? (insecure ? "warning" : "ready") : "idle";
  elements.aiModelStatus.lastChild.textContent = state.aiConfig.hasApiKey
    ? `${state.aiConfig.model || "模型已配置"}${insecure ? " · HTTP" : ""}`
    : "未配置模型";
  renderEndpointWarning();
  updateAnalyzeButton();
  updateGenerateButton();
  updateOptimizeButton();
}

async function loadAiConfig() {
  try {
    const result = await requestJson("/api/config");
    renderAiConfig(result.config?.ai || {});
    renderAiConfigTestResult();
  } catch (error) {
    elements.aiModelStatus.dataset.state = "warning";
    elements.aiModelStatus.lastChild.textContent = "配置读取失败";
    elements.aiAnalysisDetail.textContent = error.message || "无法读取模型配置";
  }
}

async function saveAiConfig() {
  const baseUrl = clean(elements.aiBaseUrl.value);
  const model = clean(elements.aiModel.value);
  const apiKey = clean(elements.aiApiKey.value);
  if (!baseUrl || !model) {
    toast("请填写 API 节点和视觉模型。", "error");
    return;
  }
  const original = elements.saveAiConfigButton.innerHTML;
  elements.saveAiConfigButton.disabled = true;
  elements.testAiConfigButton.disabled = true;
  elements.saveAiConfigButton.innerHTML = "<span>保存中</span><small>写入本机后端</small>";
  try {
    const payload = { aiBaseUrl: baseUrl, aiModel: model, aiTemperature: 0.2, aiMaxTokens: 2600 };
    if (apiKey) payload.aiApiKey = apiKey;
    const result = await requestJson("/api/config", { method: "POST", body: JSON.stringify(payload) });
    renderAiConfig(result.config?.ai || {});
    state.aiProbe = null;
    renderAiConfigTestResult();
    elements.aiConfigTestState.textContent = "配置已保存，尚未测试";
    toast("模型配置已保存；尚未发起远端测试。");
  } catch (error) {
    toast(error.message || "模型配置保存失败。", "error");
  } finally {
    elements.saveAiConfigButton.disabled = false;
    elements.testAiConfigButton.disabled = false;
    elements.saveAiConfigButton.innerHTML = original;
  }
}

async function testAiConfig() {
  if (state.aiProbeBusy) return;
  const baseUrl = clean(elements.aiBaseUrl.value);
  const model = clean(elements.aiModel.value);
  const apiKey = clean(elements.aiApiKey.value);
  if (!baseUrl || !model) {
    toast("请先填写 API 节点和模型 ID。", "error");
    return;
  }
  if (!apiKey && !state.aiConfig.hasApiKey) {
    toast("请填写 API Key，或先保存已有 Key。", "error");
    return;
  }
  if (isInsecureRemoteEndpoint(baseUrl) && !window.confirm("当前是明文 HTTP 远端。测试会发送 API Key 和一条极短文本请求，但不会上传商品图片。确认继续吗？")) return;

  state.aiProbeBusy = true;
  const original = elements.testAiConfigButton.innerHTML;
  elements.testAiConfigButton.disabled = true;
  elements.saveAiConfigButton.disabled = true;
  elements.testAiConfigButton.innerHTML = "<span>正在测试</span><small>等待模型响应…</small>";
  renderAiConfigTestResult(null, "testing");
  try {
    const payload = {
      testMode: "invoke",
      aiBaseUrl: baseUrl,
      aiModel: model,
      aiTemperature: 0,
      aiMaxTokens: 128,
    };
    if (apiKey) payload.aiApiKey = apiKey;
    const result = await requestJson("/api/config/test/ai", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const item = result.result?.ai || { ok: false, networkOk: false, message: "服务端没有返回模型检测结果。" };
    renderAiConfigTestResult(item);
    toast(item.message || "模型连接测试完成。", item.ok ? "success" : "error");
  } catch (error) {
    renderAiConfigTestResult({ ok: false, networkOk: false, message: error.message || "模型连接测试失败。" });
    toast(error.message || "模型连接测试失败。", "error");
  } finally {
    state.aiProbeBusy = false;
    elements.testAiConfigButton.disabled = false;
    elements.saveAiConfigButton.disabled = false;
    elements.testAiConfigButton.innerHTML = original;
  }
}

function updateAnalyzeButton() {
  if (!elements.analyzeProductButton) return;
  const ready = state.aiConfig.hasApiKey && state.references.length > 0 && !state.aiBusy;
  elements.analyzeProductButton.disabled = !ready;
  if (state.aiBusy) return;
  if (!state.aiConfig.hasApiKey) {
    elements.aiAnalysisState.textContent = "先保存模型配置";
  } else if (!state.references.length) {
    elements.aiAnalysisState.textContent = "模型已就绪，请上传商品参考图";
  } else {
    elements.aiAnalysisState.textContent = `${state.references.length} 张图片已就绪，可进行一次 AI 识别`;
  }
}

function usageLabel(usage = {}) {
  if (Number.isInteger(usage.total_tokens) && usage.total_tokens >= 0) return `${usage.total_tokens} tokens`;
  return "服务端未返回 Token 用量";
}

function updateGenerateButton() {
  if (!elements.generateButton) return;
  elements.generateButton.disabled = state.aiBusy;
  if (state.aiBusy) {
    elements.generateButton.innerHTML = "<span>AI生成中</span><b>正在消耗 Token</b>";
  } else if (!state.aiConfig.hasApiKey) {
    elements.generateButton.innerHTML = "<span>先保存模型配置</span><b>AI REQUIRED</b>";
  } else {
    elements.generateButton.innerHTML = "<span>AI生成提示词包</span><b>消耗 Token →</b>";
  }
}

function updateOptimizeButton() {
  if (!elements.optimizePromptsButton) return;
  const ready = state.aiConfig.hasApiKey && state.localPrompts.length > 0 && !state.aiBusy;
  elements.optimizePromptsButton.disabled = !ready;
  if (state.aiBusy) return;
  if (!state.localPrompts.length) {
    elements.aiOptimizeState.textContent = "先完成一次 AI 新品生成";
    elements.aiOptimizeDetail.textContent = "主生成已经由 AI 从零编排；此处只用于对现有结果再做一次动作和终点精修。";
    elements.aiOptimizeUsage.textContent = "本次未调用";
    elements.aiOptimizeUsage.dataset.state = "idle";
  } else if (!state.aiConfig.hasApiKey) {
    elements.aiOptimizeState.textContent = "已有提示词，请先保存模型配置";
    elements.aiOptimizeDetail.textContent = "每次 AI 生成都会消耗 Token；复制和下载现有结果不消耗 Token，再次精修需要模型。";
    elements.aiOptimizeUsage.textContent = "未再次调用";
    elements.aiOptimizeUsage.dataset.state = "local";
  } else if (state.optimizationError) {
    elements.aiOptimizeState.textContent = state.optimization
      ? "本次 AI 优化失败，已保留上一次成功版本"
      : "AI 优化失败，已保留上一次 AI 生成结果";
    elements.aiOptimizeDetail.textContent = state.optimizationError;
    elements.aiOptimizeUsage.textContent = "未覆盖现有版本";
    elements.aiOptimizeUsage.dataset.state = "error";
  } else if (state.optimization) {
    elements.aiOptimizeState.textContent = `AI 精修完成 · ${state.optimization.model || state.aiConfig.model}`;
    elements.aiOptimizeDetail.textContent = state.optimization.notes?.length
      ? state.optimization.notes.join("；")
      : "已强化镜头可执行性，同时保留商品锁、参考占位符和后期边界。";
    elements.aiOptimizeUsage.textContent = `本次 ${usageLabel(state.optimization.usage)}`;
    elements.aiOptimizeUsage.dataset.state = "optimized";
  } else {
    elements.aiOptimizeState.textContent = `${state.localPrompts.length} 条 AI 新品提示词已就绪`;
    elements.aiOptimizeDetail.textContent = `可选：再使用 ${state.aiConfig.model || "当前模型"} 精修动作和终点；这会额外消耗一次 Token，不重复发送图片。`;
    elements.aiOptimizeUsage.textContent = state.generation ? `主生成 ${usageLabel(state.generation.usage)}` : "未再次调用";
    elements.aiOptimizeUsage.dataset.state = "local";
  }
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error(`无法读取图片：${file.name}`));
    reader.readAsDataURL(file);
  });
}

function referenceFingerprint() {
  const files = state.references.map((reference) => [
    reference.file?.name || "",
    Number(reference.file?.size || 0),
    Number(reference.file?.lastModified || 0),
    reference.role || "",
  ].join(":"));
  return `${clean(elements.category?.value)}|${files.join("|")}`;
}

function renderReferenceConsistency(report = state.referenceConsistency) {
  if (!elements.referenceConsistencyPanel) return;
  let current = report;
  if (!current && state.references.length === 1) {
    current = { status: "single", score: 100, sameProduct: true, summary: "当前只有一张参考图，将它作为商品身份的唯一权威来源。", conflicts: [], canonicalSources: [] };
  }
  const status = clean(current?.status) || "idle";
  const tone = status === "conflict" ? "conflict" : status === "warning" ? "warning" : ["consistent", "single"].includes(status) ? "pass" : status === "checking" ? "checking" : "idle";
  elements.referenceConsistencyPanel.className = `reference-consistency-panel is-${tone}`;
  elements.referenceConsistencyScore.textContent = Number.isFinite(Number(current?.score)) ? String(Math.round(Number(current.score))) : "—";
  elements.referenceConsistencySummary.textContent = clean(current?.summary) || (
    state.references.length
      ? "参考图发生变化；两张以上图片会在生成前自动检查是否属于同一商品。"
      : "上传两张以上图片后，AI 会在生成前检查是否为同一商品，并标记颜色、结构、接口与配件冲突。"
  );
  const conflicts = Array.isArray(current?.conflicts) ? current.conflicts : [];
  const authorities = Array.isArray(current?.canonicalSources) ? current.canonicalSources : [];
  elements.referenceConsistencyList.innerHTML = [
    ...conflicts.map((item) => `<li><b>${escapeHtml(item.dimension || "参考冲突")}</b>：${escapeHtml(item.detail || "不同图片存在不一致")}</li>`),
    ...authorities.slice(0, 4).map((item) => `<li>${escapeHtml(item.dimension || "当前维度")}以图片 ${Number(item.index) + 1} 为权威：${escapeHtml(item.reason || "该图更清楚")}</li>`),
  ].join("");
  elements.referenceConsistencyState.textContent = {
    conflict: "严重冲突",
    warning: "需要复核",
    consistent: "一致通过",
    single: "单一权威",
    checking: "检查中",
  }[status] || "待检查";
}

function invalidateReferenceConsistency() {
  state.referenceConsistency = null;
  renderReferenceConsistency();
}

async function requestFashionAnalysis(product = collectProduct()) {
  const images = await Promise.all(state.references.map(async (reference) => ({
    name: reference.file.name,
    role: reference.role,
    dataUrl: await fileToDataUrl(reference.file),
  })));
  return requestJson("/api/fashion-prompts/analyze", {
    method: "POST",
    body: JSON.stringify({
      productName: clean(product.name || elements.productName.value),
      category: clean(product.category || elements.category.value),
      categoryDetails: product.categoryDetails || collectCategoryDetails(),
      images,
    }),
  });
}

async function ensureReferenceConsistency(product = collectProduct()) {
  if (state.references.length <= 1) {
    state.referenceConsistency = {
      status: state.references.length ? "single" : "not_provided",
      score: state.references.length ? 100 : 0,
      sameProduct: state.references.length ? true : null,
      summary: state.references.length ? "单张参考图作为当前商品身份的唯一权威来源。" : "当前没有参考图，按纯文本商品事实生成。",
      conflicts: [],
      canonicalSources: [],
      fingerprint: referenceFingerprint(),
    };
    renderReferenceConsistency();
    return state.referenceConsistency;
  }
  const fingerprint = referenceFingerprint();
  if (state.referenceConsistency?.fingerprint === fingerprint) {
    if (state.referenceConsistency.status === "conflict" || state.referenceConsistency.sameProduct === false) {
      throw new Error("参考图存在严重商品冲突，请移除串品图片或重新分配参考角色后再生成。");
    }
    return state.referenceConsistency;
  }
  renderReferenceConsistency({ status: "checking", summary: `正在比较 ${state.references.length} 张参考图的颜色、轮廓、接口、文字位置与配件……` });
  const result = await requestFashionAnalysis(product);
  state.referenceConsistency = {
    ...(result.referenceConsistency || {}),
    fingerprint,
    model: result.model || state.aiConfig.model,
    usage: result.usage || {},
  };
  renderReferenceConsistency();
  if (state.referenceConsistency.status === "conflict" || state.referenceConsistency.sameProduct === false) {
    throw new Error("参考图一致性检查未通过：检测到可能不是同一商品的颜色、结构、接口或配件冲突。");
  }
  return state.referenceConsistency;
}

const AI_ANALYSIS_FIELDS = [
  { key: "suggestedName", label: "商品名称", element: "productName" },
  { key: "category", label: "商品品类", element: "category" },
  { key: "color", label: "主颜色", element: "color" },
  { key: "silhouette", label: "整体版型", element: "silhouette" },
  { key: "frontStructure", label: "正面结构", element: "frontStructure" },
  { key: "backStructure", label: "背面结构", element: "backStructure" },
  { key: "material", label: "可见面料", element: "material" },
  { key: "stylingBoundary", label: "穿搭边界", element: "stylingBoundary" },
  { key: "fragileAnchors", label: "易漂移锚点", element: "fragileAnchors", list: true },
  { key: "categoryDetails", label: "品类专用事实", element: null, details: true },
  { key: "referenceRoles", label: "参考图角色", element: null, roles: true },
];

function analysisFieldValue(analysis, field) {
  if (field.details) {
    if (!analysis.categoryDetails || typeof analysis.categoryDetails !== "object") return "";
    return Object.values(analysis.categoryDetails).map(clean).filter(Boolean).join("；");
  }
  if (field.roles) {
    if (!Array.isArray(analysis.referenceRoles) || !analysis.referenceRoles.length) return "";
    return analysis.referenceRoles.map((item) => {
      const reference = state.references[Number(item.index)];
      const role = roleByValue(item.role);
      return `${reference?.file?.name || `图片${Number(item.index) + 1}`} → ${role.label}`;
    }).join("；");
  }
  const raw = analysis[field.key];
  return field.list && Array.isArray(raw) ? raw.map(clean).filter(Boolean).join("，") : clean(raw);
}

function currentAnalysisFieldValue(field) {
  if (field.details) return Object.values(collectCategoryDetails()).map(clean).filter(Boolean).join("；");
  if (field.roles) {
    return state.references.map((item) => `${item.file.name} → ${roleByValue(item.role).label}`).join("；");
  }
  return clean(elements[field.element]?.value);
}

function discardAiReview({ message = true } = {}) {
  state.pendingAnalysis = null;
  elements.aiReviewPanel.hidden = true;
  elements.aiReviewList.innerHTML = "";
  if (message) {
    elements.aiAnalysisState.textContent = "AI 建议已放弃，保留当前商品档案";
    elements.aiAnalysisDetail.textContent = "可以调整参考图角色后重新识别。";
  }
}

function stageAiAnalysis(analysis) {
  if (!analysis || typeof analysis !== "object") throw new Error("模型没有返回可用的商品档案。");
  state.pendingAnalysis = analysis;
  const rows = AI_ANALYSIS_FIELDS.map((field) => {
    const suggestion = analysisFieldValue(analysis, field);
    if (!suggestion) return "";
    const current = currentAnalysisFieldValue(field) || "尚未填写";
    const shouldCheck = field.key === "category" || current === "尚未填写" || current === "未确认";
    const unchanged = current === suggestion;
    return `
      <label class="ai-review-row${unchanged ? " is-same" : ""}">
        <input type="checkbox" data-ai-review-key="${field.key}"${shouldCheck && !unchanged ? " checked" : ""}${unchanged ? " disabled" : ""}>
        <span class="ai-review-field">${escapeHtml(field.label)}</span>
        <span class="ai-review-current"><small>当前</small>${escapeHtml(current)}</span>
        <span class="ai-review-arrow" aria-hidden="true">→</span>
        <span class="ai-review-suggestion"><small>${unchanged ? "一致" : "AI建议"}</small>${escapeHtml(suggestion)}</span>
      </label>`;
  }).filter(Boolean);
  elements.aiReviewList.innerHTML = rows.join("");
  elements.aiReviewPanel.hidden = false;
  elements.aiAnalysisState.textContent = "识别完成，等待人工确认";
  elements.aiAnalysisDetail.textContent = "AI 尚未改动商品档案；逐项勾选后再应用。";
}

function applyAiAnalysis(analysis, selectedKeys = null) {
  if (!analysis || typeof analysis !== "object") throw new Error("模型没有返回可用的商品档案。");
  const selected = selectedKeys instanceof Set
    ? selectedKeys
    : new Set(AI_ANALYSIS_FIELDS.map((field) => field.key));
  if (selected.has("suggestedName") && analysis.suggestedName) elements.productName.value = clean(analysis.suggestedName);
  const categoryValues = [...elements.category.options].map((option) => option.value);
  if (selected.has("category") && categoryValues.includes(analysis.category)) {
    elements.category.value = analysis.category;
    renderCategoryFields();
  }
  const fieldMap = {
    color: "color",
    silhouette: "silhouette",
    frontStructure: "frontStructure",
    backStructure: "backStructure",
    material: "material",
    stylingBoundary: "stylingBoundary",
  };
  Object.entries(fieldMap).forEach(([analysisKey, elementKey]) => {
    if (!selected.has(analysisKey)) return;
    const value = clean(analysis[analysisKey]);
    if (value) elements[elementKey].value = value;
  });
  if (selected.has("fragileAnchors") && Array.isArray(analysis.fragileAnchors) && analysis.fragileAnchors.length) {
    elements.fragileAnchors.value = analysis.fragileAnchors.map(clean).filter(Boolean).join("，");
  }
  if (selected.has("categoryDetails") && analysis.categoryDetails && typeof analysis.categoryDetails === "object") {
    renderCategoryFields({ preserve: false, values: analysis.categoryDetails });
  }
  if (selected.has("referenceRoles") && Array.isArray(analysis.referenceRoles)) {
    analysis.referenceRoles.forEach((suggestion) => {
      const reference = state.references[Number(suggestion.index)];
      if (reference && REFERENCE_ROLES.some((role) => role.value === suggestion.role)) reference.role = suggestion.role;
    });
  }
  renderReferences();
  renderTemplatePanel();
  saveForm();
  const uncertain = Array.isArray(analysis.uncertainFacts) ? analysis.uncertainFacts.map(clean).filter(Boolean) : [];
  const warnings = Array.isArray(analysis.warnings) ? analysis.warnings.map(clean).filter(Boolean) : [];
  const notes = [...uncertain.map((item) => `待确认：${item}`), ...warnings].slice(0, 5);
  discardAiReview({ message: false });
  elements.aiAnalysisState.textContent = "已应用勾选的 AI 商品事实";
  elements.aiAnalysisDetail.textContent = notes.length
    ? notes.join("；")
    : "识别结果已回填。请人工核对商品边界、背面结构和易漂移锚点。";
}

function applySelectedAiAnalysis() {
  if (!state.pendingAnalysis) return;
  const selected = new Set(
    [...elements.aiReviewList.querySelectorAll("[data-ai-review-key]:checked")]
      .map((input) => input.dataset.aiReviewKey)
      .filter(Boolean),
  );
  if (!selected.size) {
    toast("请至少勾选一项 AI 建议。", "error");
    return;
  }
  const pending = state.pendingAnalysis;
  applyAiAnalysis(pending, selected);
  toast(`已应用 ${selected.size} 项 AI 建议；未勾选内容保持不变。`);
}

async function analyzeProductWithAi() {
  if (!state.references.length || !state.aiConfig.hasApiKey || state.aiBusy) return;
  if (isInsecureRemoteEndpoint() && !window.confirm("当前模型节点使用明文 HTTP。继续后，API Key 与商品图片会通过未加密连接发送到该节点。确认继续识别吗？")) return;
  state.aiBusy = true;
  updateAnalyzeButton();
  updateGenerateButton();
  updateOptimizeButton();
  const original = elements.analyzeProductButton.innerHTML;
  elements.analyzeProductButton.innerHTML = "<span>识别中</span><b>请稍候</b>";
  elements.aiAnalysisState.textContent = `正在使用 ${state.aiConfig.model || "视觉模型"} 分析商品`;
  elements.aiAnalysisDetail.textContent = "只提取可观察事实，并检查多张参考图是否属于同一商品。";
  try {
    const result = await requestFashionAnalysis();
    state.referenceConsistency = {
      ...(result.referenceConsistency || {}),
      fingerprint: referenceFingerprint(),
      model: result.model || state.aiConfig.model,
      usage: result.usage || {},
    };
    renderReferenceConsistency();
    stageAiAnalysis(result.analysis);
    elements.aiAnalysisState.textContent = `识别完成 · ${result.model || state.aiConfig.model} · 等待确认`;
    const tokenText = result.usage?.total_tokens ? ` · ${result.usage.total_tokens} tokens` : "";
    toast(`识别建议已返回${tokenText}，确认后才会写入商品档案。`);
  } catch (error) {
    elements.aiAnalysisState.textContent = "AI 识别失败，原商品档案未被清空";
    elements.aiAnalysisDetail.textContent = error.message || "请检查模型是否支持图片输入。";
    toast(error.message || "AI 识别失败。", "error");
  } finally {
    state.aiBusy = false;
    elements.analyzeProductButton.innerHTML = original;
    updateAnalyzeButton();
    updateGenerateButton();
    updateOptimizeButton();
  }
}

function selectedScenes() {
  return [...document.querySelectorAll('input[name="scene"]:checked')].map((input) => input.value);
}

function collectProduct() {
  const categoryDetails = collectCategoryDetails();
  return {
    name: clean(elements.productName.value),
    category: clean(elements.category.value),
    color: clean(elements.color.value),
    silhouette: clean(elements.silhouette.value),
    frontStructure: clean(elements.frontStructure.value),
    backStructure: clean(elements.backStructure.value),
    material: clean(elements.material.value),
    stylingBoundary: clean(elements.stylingBoundary.value),
    anchors: clean(elements.fragileAnchors.value),
    categoryDetails,
    templatePreset: clean(elements.templatePreset.value) || "auto",
    platformPreset: clean(elements.platformPreset?.value) || "custom",
    platformStrategy: platformStrategyForSelection(),
    promptMode: clean(elements.promptMode.value) || "fidelity",
    duration: Number(elements.duration.value) || 15,
    count: Number(elements.promptCount.value) || 3,
    ratio: clean(elements.ratio.value) || "9:16",
    market: clean(elements.market.value) || "日本日常电商",
    scenes: selectedScenes(),
  };
}

function saveForm() {
  const product = collectProduct();
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...product, categoryDetailsByRoute: state.categoryDrafts }));
  } catch {
    // The page still works when browser storage is unavailable.
  }
}

function restoreForm() {
  let saved;
  try {
    saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
  } catch {
    return;
  }
  if (!saved || typeof saved !== "object") return;
  const fieldMap = {
    productName: "name",
    category: "category",
    color: "color",
    silhouette: "silhouette",
    frontStructure: "frontStructure",
    backStructure: "backStructure",
    material: "material",
    stylingBoundary: "stylingBoundary",
    fragileAnchors: "anchors",
    platformPreset: "platformPreset",
    templatePreset: "templatePreset",
    promptMode: "promptMode",
    duration: "duration",
    promptCount: "count",
    ratio: "ratio",
    market: "market",
  };
  Object.entries(fieldMap).forEach(([elementKey, savedKey]) => {
    if (saved[savedKey] !== undefined && elements[elementKey]) elements[elementKey].value = saved[savedKey];
  });
  if (Array.isArray(saved.scenes) && saved.scenes.length) {
    document.querySelectorAll('input[name="scene"]').forEach((input) => {
      input.checked = saved.scenes.includes(input.value);
    });
  }
  state.categoryDrafts = saved.categoryDetailsByRoute && typeof saved.categoryDetailsByRoute === "object"
    ? { ...saved.categoryDetailsByRoute }
    : {};
  const restoredSchemaKey = categorySchemaKey(saved);
  if (saved.categoryDetails && typeof saved.categoryDetails === "object") {
    state.categoryDrafts[restoredSchemaKey] = { ...saved.categoryDetails };
  }
  renderCategoryFields({ preserve: false });
  renderPlatformPreset({ applySettings: false });
}

function loadDemo({ generate = true } = {}) {
  discardAiReview({ message: false });
  elements.productName.value = "椭圆充电盒真无线蓝牙耳机";
  elements.category.value = "数码电子";
  elements.color.value = "雾面白色；状态灯为柔和绿色";
  elements.silhouette.value = "圆角椭圆充电盒，两只独立入耳式耳机收纳在盒内";
  elements.frontStructure.value = "翻盖充电盒，正面一枚状态灯，两只耳机左右分槽，耳机各有短柄和触控区";
  elements.backStructure.value = "背部转轴与底部充电接口只按对应参考图生成；无图时保持不可见";
  elements.material.value = "外壳为细腻哑光硬质表面，金属充电触点有轻微反光";
  elements.stylingBoundary.value = "充电线是实际配件；手机、桌面和手不属于商品本体";
  elements.fragileAnchors.value = "耳机数量与左右位置，充电盒转轴，正面状态灯，底部充电接口，耳机短柄比例";
  state.categoryDrafts.electronics = {
    interfaces: "底部一个充电接口",
    controls: "两只耳机各有一处触控区",
    indicators: "充电盒正面一枚柔和绿色状态灯",
    accessories: "两只耳机与一个充电盒；充电线为实际配件",
  };
  renderCategoryFields({ preserve: false, values: state.categoryDrafts.electronics });
  elements.templatePreset.value = "auto";
  elements.platformPreset.value = "tiktok";
  elements.promptMode.value = "fidelity";
  elements.duration.value = "15";
  elements.promptCount.value = "3";
  elements.ratio.value = "9:16";
  elements.market.value = "日本日常电商";
  renderPlatformPreset({ applySettings: true });
  document.querySelectorAll('input[name="scene"]').forEach((input, index) => {
    input.checked = index < 3;
  });
  renderTemplatePanel();
  renderPromptModeNote();
  saveForm();
  if (generate) generatePack();
  else elements.productName.focus();
}

function resetProduct() {
  if (!window.confirm("清空当前商品档案、参考图和生成结果，开始一个新商品？")) return;
  state.references.forEach((reference) => {
    if (reference.url) URL.revokeObjectURL(reference.url);
  });
  state.references = [];
  state.prompts = [];
  state.localPrompts = [];
  state.packText = "";
  state.directPackText = "";
  state.product = null;
  state.commonLock = "";
  state.repairs = [];
  state.template = null;
  state.generation = null;
  state.generationError = "";
  state.optimization = null;
  state.optimizationError = "";
  state.categoryDrafts = {};
  state.activeCategorySchemaKey = "";
  state.referenceConsistency = null;
  state.fidelityReport = null;
  discardAiReview({ message: false });
  elements.form.reset();
  renderTemplatePanel();
  renderCategoryFields({ preserve: false });
  renderPromptModeNote();
  renderPlatformPreset({ applySettings: false });
  renderReferenceConsistency();
  renderFidelityReport();
  elements.productName.removeAttribute("aria-invalid");
  elements.productNameError.hidden = true;
  elements.emptyOutput.hidden = false;
  elements.outputContent.hidden = true;
  elements.outputSummary.textContent = "填写商品档案后生成。基础三条会分别测试整体、细节与真实使用演示。";
  elements.copyAllButton.disabled = true;
  elements.copyDirectAllButton.disabled = true;
  elements.downloadButton.disabled = true;
  updateOptimizeButton();
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Clearing persisted form data is best effort.
  }
  renderReferences();
  elements.productName.focus();
  toast("已建立空白商品档案。");
}

function addReferenceFiles(files) {
  const candidates = [...files].filter((file) => /^image\/(jpeg|png|webp)$/i.test(file.type));
  if (!candidates.length) {
    toast("请选择 JPG、PNG 或 WebP 图片。", "error");
    return;
  }
  discardAiReview({ message: false });
  const openSlots = Math.max(0, 6 - state.references.length);
  candidates.slice(0, openSlots).forEach((file) => {
    const index = state.references.length;
    state.references.push({
      id: `${Date.now()}-${index}-${Math.random().toString(16).slice(2)}`,
      file,
      url: URL.createObjectURL(file),
      role: REFERENCE_ROLES[Math.min(index, REFERENCE_ROLES.length - 1)].value,
    });
  });
  if (candidates.length > openSlots) toast("最多保留 6 张参考图，多余图片未添加。", "error");
  invalidateReferenceConsistency();
  renderReferences();
}

function removeReference(id) {
  discardAiReview({ message: false });
  const target = state.references.find((item) => item.id === id);
  if (target?.url) URL.revokeObjectURL(target.url);
  state.references = state.references.filter((item) => item.id !== id);
  invalidateReferenceConsistency();
  renderReferences();
}

function roleByValue(value) {
  return REFERENCE_ROLES.find((role) => role.value === value) || REFERENCE_ROLES[REFERENCE_ROLES.length - 1];
}

function renderReferences() {
  elements.referenceCount.textContent = `${state.references.length} / 6`;
  elements.referenceGrid.innerHTML = state.references.map((reference) => `
    <article class="reference-card" data-reference-id="${escapeHtml(reference.id)}">
      <img src="${escapeHtml(reference.url)}" alt="${escapeHtml(reference.file.name)} 的本地预览">
      <div class="reference-card-body">
        <div>
          <strong title="${escapeHtml(reference.file.name)}">${escapeHtml(reference.file.name)}</strong>
          <select aria-label="${escapeHtml(reference.file.name)} 的参考角色" data-reference-role>
            ${REFERENCE_ROLES.map((role) => `<option value="${role.value}"${reference.role === role.value ? " selected" : ""}>${role.label}</option>`).join("")}
          </select>
        </div>
        <button type="button" data-remove-reference>移除</button>
      </div>
    </article>
  `).join("");
  updateAnalyzeButton();
}

function referenceAuthorityMap() {
  return state.references.map((reference) => {
    const role = roleByValue(reference.role);
    return { ...role, fileName: reference.file.name, id: reference.id };
  });
}

function isUnknownFact(value) {
  const text = clean(value);
  return !text || /未确认|未知|不清楚|没有.*图|不生成/.test(text);
}

function referenceCoverage(product = {}) {
  const roles = new Set(state.references.map((item) => item.role));
  const hasReferences = state.references.length > 0;
  return {
    hasReferences,
    front: roles.has("front_full") || roles.has("front_detail"),
    detail: roles.has("front_detail"),
    back: roles.has("back"),
    side: roles.has("side"),
    fabric: roles.has("fabric"),
    allowBack: roles.has("back") || (!hasReferences && !isUnknownFact(product.backStructure)),
    allowSideProof: roles.has("side") || !hasReferences,
  };
}

function splitProductFacts(value, limit = 3) {
  return String(value || "")
    .split(/[，,、；;。\n]/)
    .map(clean)
    .filter(Boolean)
    .slice(0, limit);
}

function detailFocusForProduct(product, profile) {
  const anchors = splitProductFacts(product.anchors, 6);
  const structuralAnchor = anchors.find((item) => /接口|按键|开口|封口|转轴|触点|泵头|刷头|卡扣|手柄|支脚|滤网|水箱|带体|连接|领|肩带|胸前片|门襟|扣|拉链|腰头|口袋|袖口|下摆|褶|拼接|开衩/.test(item));
  if (structuralAnchor) return structuralAnchor;
  if (anchors.length) return anchors[0];
  const structures = splitProductFacts(product.frontStructure, 4);
  if (structures.length) return structures[0];
  return profile.detailProof;
}

function buildCommonLock(product, selectedProfile = null) {
  const profile = selectedProfile || inferProductProfile(product);
  const coverage = referenceCoverage(product);
  const categoryFacts = Object.entries(product.categoryDetails || {})
    .map(([key, value]) => `${key}：${clean(value)}`)
    .filter((item) => !item.endsWith("："));
  const facts = [
    `商品是“${product.name}”，类别固定为${product.category}，只把当前商品本体作为主产品`,
    product.color && `颜色：${product.color}`,
    product.silhouette && `外形、规格或轮廓：${product.silhouette}`,
    product.frontStructure && `主要结构：${product.frontStructure}`,
    product.backStructure && `背面、底部或接口：${product.backStructure}`,
    product.material && `${productMaterialLabel(profile)}：${product.material}`,
    product.stylingBoundary && `商品边界：${product.stylingBoundary}`,
    product.anchors && `全程锁定这些易漂移锚点：${product.anchors}`,
    categoryFacts.length && `品类专用事实：${categoryFacts.join("；")}`,
  ].filter(Boolean);

  const exclusions = [
    ...profile.exclusions,
    "不改变已确认的颜色、轮廓、开合、部件、接口、扣件数量和位置",
    "不复制参考图人物的脸、身份、姿势、房间、品牌或水印",
  ];

  const sourceLead = state.references.length
    ? "参考图只控制商品本体，各图按参考角色表分工；每个维度只服从职责对应的权威参考。"
    : "当前没有绑定参考图，以下仅为根据用户已确认文字事实生成的纯文本草案；不得自行补全未确认结构。";
  const coverageRule = coverage.allowBack
    ? (profile.continuityRule || profile.frontBackRule)
    : "当前没有可靠背面或底部依据，只展示主视图与允许的侧前方角度，不补全隐藏结构";
  const platformRule = product.platformStrategy?.focus
    ? `平台创作预设只控制节奏与构图：${product.platformStrategy.focus}；${product.platformStrategy.safeArea || "主体保持在安全区域"}，不得覆盖商品事实。`
    : "平台设置不得覆盖商品事实与参考权威。";
  return `${sourceLead}所有镜头复用完全相同的一件商品，商品事实只允许来自当前档案和职责对应参考。${facts.join("；")}。${coverageRule}。材质、质地、内容物和工作状态只按当前档案与对应参考生成；数量、位置和物理状态跨镜头连续，不闪烁、不换材质、不凭空增减。${platformRule}高风险排除：${[...new Set(exclusions)].slice(0, 5).join("；")}。`;
}

function refsForPrompt(role) {
  const map = referenceAuthorityMap();
  const chosen = [];
  role.preferredRefs.forEach((preferred) => {
    const match = map.find((item) => item.value === preferred);
    if (match && !chosen.some((item) => item.id === match.id)) chosen.push(match);
  });
  if (!chosen.length && map.length) chosen.push(map[0]);
  return chosen.slice(0, 3);
}

function productRoleForProfile(roleKey, profile, product = {}) {
  const base = PROMPT_ROLES[roleKey] || PROMPT_ROLES.overview;
  const blueprint = PRODUCT_ROLE_BLUEPRINTS[roleKey] || PRODUCT_ROLE_BLUEPRINTS.overview;
  const productName = product.name || "当前商品";
  const focus = detailFocusForProduct(product, profile);
  const beats = Array.isArray(profile.beats) && profile.beats.length
    ? profile.beats
    : PRODUCT_PROFILES.universal_product.beats;
  const rotated = beats.map((_, index) => beats[(blueprint.start + index) % beats.length]);
  const taskProof = profile[blueprint.proof] || profile.overviewProof;
  const task = roleKey === "detail"
    ? `只证明“${productName}”的“${focus}”及${profile.detailProof}，不同时承担其他功能或功效宣称`
    : `只用${blueprint.task}证明“${productName}”的${taskProof}，不重复本批其他提示词的开场动作与机位`;
  return {
    ...base,
    key: roleKey,
    profile,
    focus,
    coverage: referenceCoverage(product),
    title: `${profile.name} · ${blueprint.title}`,
    risk: blueprint.risk,
    task,
    actions: rotated.slice(0, 3),
    denseActions: rotated,
    cameras: [...blueprint.cameras],
    proofs: [taskProof, roleKey === "detail" ? focus : profile.motionProof, profile.activityProof],
    endpoint: `“${productName}”完成${blueprint.task}后稳定停留，部件、颜色、结构、材质和易漂移锚点均与当前参考一致`,
  };
}

function roleForTemplate(roleKey, template, product = {}) {
  const base = PROMPT_ROLES[roleKey];
  const profile = template?.profile || inferProductProfile(product);
  if (!isApparelProfile(profile)) return productRoleForProfile(roleKey, profile, product);
  const productName = product.name || "当前商品";
  const focus = detailFocusForProduct(product, profile);
  const upperBodyProfile = ["knitwear", "top", "outerwear"].includes(profile.id);
  const coverage = referenceCoverage(product);
  const sideAction = coverage.allowSideProof
    ? "模特缓慢转到侧面，放松双臂后停住，让侧面轮廓和长度清楚可见"
    : "模特只转到侧前方约30度后停住，不展示参考图未覆盖的完整侧面结构";
  const sideProof = coverage.allowSideProof
    ? `侧面轮廓、长度与${profile.garmentSpan}`
    : "正面与轻微侧前方的轮廓连续性，不补全未知侧面结构";
  const backAction = coverage.allowBack
    ? "模特继续转到背面短暂停留，再回到正面；背面只呈现当前已经确认的结构"
    : "模特从侧前方直接回到正面并停住，不转到参考图未覆盖的背面";
  const backProof = coverage.allowBack
    ? profile.frontBackRule
    : "只核对正面与侧前方；未知背面保持不展示、不补全";
  const adaptive = {
    overview: {
      title: `${profile.name}整体稳定展示`,
      task: `只证明“${productName}”的${profile.overviewProof}，不同时承担细节、剧情或搭配变化`,
      actions: [
        `模特自然站定，${profile.garmentSpan}完整进入画面，保持两秒让正面比例可核对`,
        sideAction,
        backAction,
      ],
      cameras: ["固定稳定构图，人物居中，不推拉", "低幅度横向跟随，到侧前方构图后停止", "保持同一焦段与人物尺度，不追求面部特写"],
      proofs: [profile.overviewProof, sideProof, backProof],
      endpoint: `正面稳定定格，${profile.garmentSpan}完整、清楚、无遮挡，可与权威参考逐项核对`,
    },
    detail: {
      title: `${profile.name}关键结构细节`,
      task: `只证明“${focus}”的实际形状、数量、位置、比例与可见材质，不触摸高风险结构`,
      actions: [
        `模特双手自然离开商品，画面停在“${focus}”所在区域，让结构边缘与数量无遮挡`,
        "模特只做一次轻微呼吸和肩部放松，关键结构保持原位，面料产生极小的自然微动",
        `模特保持不触摸商品，镜头缓慢拉远一级，确认“${focus}”与整件商品的比例关系`,
      ],
      cameras: ["从正面受控近景开始，机位固定", "固定近景，不环绕、不快速变焦、不改变光向", "单次缓慢拉远，在商品结构仍清楚的位置停止"],
      proofs: [focus, profile.detailProof, `关键结构与${profile.garmentSpan}的比例关系`],
      endpoint: `“${focus}”完整、无遮挡、边缘清楚，实际数量、位置和比例可核对`,
    },
    walking: {
      title: `${profile.name}自然走动物理`,
      task: `只观察正常步行时的${profile.motionProof}，不生成舒适、显瘦、抗皱或其他功效宣称`,
      actions: [
        `模特从两米外自然向镜头走近两步，步幅正常、手臂放松，${profile.garmentSpan}保持可见`,
        coverage.allowSideProof
          ? "模特从画面左侧走向右侧，保持正常速度，完整侧面进入画面后停住"
          : "模特沿轻微斜线向侧前方走两步后停住，不转成参考图未覆盖的完整侧面",
        coverage.allowBack
          ? `模特背对镜头向前走两步后停止，背面只呈现已确认结构，${profile.garmentSpan}按真实重力运动`
          : `模特保持侧前方角度回到正面并停止，${profile.garmentSpan}持续可见，不展示未知背面`,
      ],
      cameras: ["低幅度后退跟拍，保持完整商品构图，人物停止时镜头停止", "与人物同速横向跟拍，不超越人物", "固定后方构图，不推近、不环绕"],
      proofs: [profile.motionProof, coverage.allowSideProof ? "侧面轮廓、长度与下摆运动" : sideProof, backProof],
      endpoint: `模特稳定停住，${profile.garmentSpan}与易漂移锚点没有融合、闪烁、复制或变形`,
    },
    routine: {
      title: `${profile.name}日常动作稳定性`,
      task: "只观察商品在一个普通拿包出门动作中的稳定状态，道具不能遮挡或改变商品结构",
      actions: [
        `模特站在简洁入口旁，身体朝向门口，${profile.garmentSpan}完整进入画面`,
        "模特单手拿起一只无标识小包，另一只手自然下垂，不触碰领口、门襟、腰头、扣件、口袋或其他易漂移锚点",
        "模特走到门边自然停住，包保持在身体外侧，侧前方展示完整穿着状态",
      ],
      cameras: ["固定中全景或全身景，保持商品完整", "轻微平移跟随拿包动作，动作结束立即停止", "后退半步恢复完整商品构图后锁定"],
      proofs: [profile.overviewProof, `道具不遮挡${profile.garmentSpan}`, profile.motionProof],
      endpoint: `模特拿包站定，${profile.garmentSpan}无遮挡，道具位置和人物动作都已停止`,
    },
    activity: {
      title: `${profile.name}活动与面料响应`,
      task: `只观察${profile.activityProof}，不把动作演示写成未经证实的商品功效`,
      actions: upperBodyProfile
        ? [
          `模特自然站直，${profile.garmentSpan}完整可见，双手先保持在商品外侧`,
          "模特缓慢抬起双臂到胸前再自然放下，动作连续、幅度克制，不拉扯领口、门襟或下摆",
          "模特恢复自然站姿并保持静止，让商品按真实重力稳定下来",
        ]
        : [
          `模特站在无扶手木凳旁，${profile.garmentSpan}完整可见，双手不触碰商品`,
          "模特自然坐下，停顿一秒后保持手部离开商品，结构只随身体动作自然变化",
          "模特平稳起身并站直，动作结束后保持静止，让商品按真实重力稳定下来",
        ],
      cameras: ["固定完整商品构图，不移动", "保持同一机位、焦段和光向，完整记录动作", "同一机位记录恢复，结束后继续停留"],
      proofs: [profile.overviewProof, profile.activityProof, "动作结束后易漂移锚点仍与参考一致"],
      endpoint: `模特重新站稳，${profile.garmentSpan}自然垂落，已确认结构、颜色与比例保持一致`,
    },
    lifestyle: {
      title: `${profile.name}真实生活场景`,
      task: "只把当前商品放进一个克制的日常环境，商品仍是唯一主角，环境不提供新的商品事实",
      actions: [
        `模特在选定场景入口自然站立，背景简单、没有人群或可读招牌，${profile.garmentSpan}完整可见`,
        "模特沿直线正常行走，单手拿无标识小包，商品正面和侧面依次清楚出现",
        "模特在自然光位置停下并转向镜头，包保持在身体外侧，保持放松站姿",
      ],
      cameras: ["完整商品构图建立少量环境，商品占画面主要区域", "平稳侧向跟拍，到预定位置停止", "轻微推近一级后锁定，仍保持商品完整"],
      proofs: [profile.overviewProof, profile.motionProof, "商品本色、完整轮廓与场景光线分离"],
      endpoint: `模特在干净背景前正面站定，${profile.garmentSpan}完整清楚，环境没有抢夺注意力`,
    },
    ending: {
      title: `${profile.name}一镜到底收尾`,
      task: "只生成一个可用于剪辑结尾的连续进入、转身、停住动作和干净商品定格",
      actions: [
        `模特从侧前方进入画面，沿直线自然走两步，${profile.garmentSpan}始终完整`,
        "模特缓慢转向镜头并停止，完成后保持自然表情和放松肩部直到视频结束",
        `模特保持正面放松站姿，双手自然垂落，${profile.garmentSpan}完整无遮挡，静止到视频结束`,
      ],
      cameras: ["一个连续的完整商品跟拍，从侧前方平稳移动到正面，人物停下时镜头同步停止", "人物停下后保持同一构图", "最后保持静止"],
      proofs: [profile.overviewProof, backProof, "干净正面商品终点与后期安全空间"],
      endpoint: `正面完整商品画面稳定停留，${profile.garmentSpan}清楚，四周留出后期CTA安全空间`,
    },
  }[roleKey] || {};
  return { ...base, profile, focus, coverage, ...adaptive };
}

function buildReferenceClause(role) {
  const refs = refsForPrompt(role);
  if (!refs.length) return "【参考】纯文本模式，所有未确认结构保持不可见，不自行设计。";
  return `【参考】${refs.map((ref) => `${ref.placeholder}仅控制${ref.authority}`).join("；")}。各维度只服从职责对应参考；所有参考均不传递人物身份、脸、姿势、穿搭层、房间、品牌、水印或文字。`;
}

function formatTime(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(/\.0$/, "");
}

function resolveDenseScenes(product = {}, fallbackScene = "安静的浅色室内") {
  const choices = [...new Set([...(product.scenes || []), fallbackScene].map(clean).filter(Boolean))];
  const interior = choices.find((item) => /室内|公寓|玄关|住宅|镜前/.test(item)) || choices[0] || fallbackScene;
  const outdoor = choices.find((item) => item !== interior && /街|店|咖啡|公园|户外/.test(item))
    || choices.find((item) => item !== interior)
    || interior;
  const lifestyle = choices.find((item) => item !== interior && item !== outdoor) || outdoor;
  return { interior, outdoor, lifestyle };
}

function genericDenseShotPlan(role, product = {}, fallbackScene = "纯净自然光桌面") {
  const profile = role.profile || inferProductProfile(product);
  const actions = role.denseActions || profile.beats || PRODUCT_PROFILES.universal_product.beats;
  const choices = [...new Set([...(product.scenes || []), ...recommendedScenesForProfile(profile), fallbackScene].map(clean).filter(Boolean))];
  const scenes = [...Array(8)].map((_, index) => choices[Math.min(Math.floor(index / 3), choices.length - 1)] || fallbackScene);
  const blueprint = PRODUCT_ROLE_BLUEPRINTS[role.key] || PRODUCT_ROLE_BLUEPRINTS.overview;
  const framingSets = {
    overview: ["完整正面全景", "侧前方完整景", "部件关系中全景"],
    detail: ["结构微距近景", "材质俯拍近景", "结构比例中景"],
    walking: ["操作准备中景", "操作过程侧景", "操作终点中近景"],
    routine: ["使用环境中全景", "手部流程中景", "状态变化近景"],
    activity: ["功能起始近景", "工作状态证据景", "停止恢复中景"],
    lifestyle: ["场景建立中全景", "真实使用关系景", "商品主体中景"],
    ending: ["商品英雄构图", "部件归位中景", "最终静止全景"],
  };
  const framings = framingSets[role.key] || framingSets.overview;
  return [...Array(8)].map((_, index) => ({
    framing: framings[index % framings.length],
    view: index === 0 ? blueprint.cameras[0] : index === 1 ? blueprint.cameras[1] : "自然固定视角",
    scene: scenes[index],
    action: actions[index % actions.length],
    camera: index < 3 ? blueprint.cameras[index] : index === 7 ? "固定完整商品构图，不再增加动作或运镜" : "低幅度稳定移动，动作完成后立即锁定",
    proof: index === 0 ? role.task : role.proofs?.[index % role.proofs.length] || profile.overviewProof,
    endpoint: index === 7 ? role.endpoint : "商品、部件与操作状态清楚，动作完整结束后再切镜",
  }));
}

function denseShotPlan(role, product = {}, fallbackScene = "安静的浅色室内") {
  const profile = role.profile || inferProductProfile(product);
  if (!isApparelProfile(profile)) return genericDenseShotPlan(role, product, fallbackScene);
  const coverage = role.coverage || referenceCoverage(product);
  const focus = role.focus || detailFocusForProduct(product, profile);
  const scenes = resolveDenseScenes(product, fallbackScene);
  const primaryScene = clean(fallbackScene) || scenes.interior;
  const roleFramings = DENSE_ROLE_FRAMINGS[role.key] || DENSE_ROLE_FRAMINGS.overview;
  const firstViews = role.key === "walking"
    ? ["自然跟拍", "自然跟拍", "自然固定视角"]
    : role.key === "routine" || role.key === "lifestyle"
      ? ["自然固定视角", "朋友视角轻量跟拍", "自然固定视角"]
      : ["自然固定视角", "自然固定视角", "自然固定视角"];
  const firstShots = [0, 1, 2].map((index) => ({
    framing: roleFramings[index],
    view: firstViews[index],
    scene: primaryScene,
    action: role.actions[index] || role.actions[0] || role.task,
    camera: role.cameras[index] || role.cameras[0] || "固定完整商品构图",
    proof: role.proofs?.[index] || role.proofs?.[0] || role.task,
    endpoint: "动作完整结束，主体与镜头同时停稳后再切镜",
  }));

  const sideAction = coverage.allowSideProof
    ? `模特继续正常行走半步并缓慢转成侧面，${profile.garmentSpan}保持完整可见，随后停住`
    : `模特只转到侧前方约30度后停住，不展示参考图未覆盖的完整侧面结构，${profile.garmentSpan}持续可见`;
  const sideProof = coverage.allowSideProof
    ? `侧面轮廓、实际长度与${profile.garmentSpan}`
    : "正面与轻微侧前方的轮廓连续性，不补全未知侧面结构";
  const backAction = coverage.allowBack
    ? "模特从侧前方缓慢转到完整背面并停留，正面结构自然离开视野，背面只呈现已确认内容"
    : "模特保持侧前方约30度，不转到未知背面；正面已确认结构仍处于可核对范围";
  const backProof = coverage.allowBack
    ? profile.frontBackRule
    : "未知背面保持不展示、不补全，正面结构不被错误复制";
  const materialProof = product.material
    ? `${focus}及相邻区域的${compactPromptFact(product.material, 120)}`
    : `${focus}及相邻区域的可见材质与结构连接`;

  return [
    ...firstShots,
    {
      framing: "生活场景中全景",
      view: "朋友视角轻量跟拍",
      scene: scenes.outdoor,
      action: `普通直接切换场景；模特从侧前方沿直线自然走两步，手臂放松，${profile.garmentSpan}不被包、手或头发遮挡`,
      camera: "与人物同速低幅度跟拍，不环绕、不突然推拉，人物停止时镜头同步停止",
      proof: profile.motionProof,
      endpoint: "模特走到预定位置并停稳，商品轮廓、颜色和易漂移锚点保持一致",
    },
    {
      framing: "侧面中景",
      view: "自然跟拍",
      scene: scenes.outdoor,
      action: sideAction,
      camera: "平行低幅度跟随到侧面或允许的侧前方构图后锁定，不超越人物",
      proof: sideProof,
      endpoint: "人物在允许角度停住，商品关键边缘完整、无遮挡",
    },
    {
      framing: "关键结构近景",
      view: "自然固定视角",
      scene: scenes.lifestyle,
      action: `模特停在干净背景前，双手离开商品；画面短暂停留在“${focus}”及相邻面料，不触摸、不拉扯、不遮挡`,
      camera: "固定受控近景，不环绕、不改变光向，不过度虚化结构边缘",
      proof: materialProof,
      endpoint: `“${focus}”的形状、数量、位置、比例与相邻材质清楚可核对`,
    },
    {
      framing: coverage.allowBack ? "背面中全景" : "侧前方中全景",
      view: "自然固定视角",
      scene: scenes.lifestyle,
      action: backAction,
      camera: "保持同一焦段与人物尺度，转身完成后固定，不追求面部特写",
      proof: backProof,
      endpoint: coverage.allowBack ? "背面稳定停留，已确认背部结构清楚，正面结构没有复制到背面" : "允许角度稳定停留，不出现任何虚构背面结构",
    },
    {
      framing: "正面全身收尾",
      view: "自然固定视角",
      scene: scenes.interior,
      action: `普通直接切回起始场景；模特回到正面自然站姿，${profile.garmentSpan}完整进入画面，动作结束后保持静止`,
      camera: "固定完整商品构图，人物居中，不再新增运镜、动作、道具或换装",
      proof: profile.overviewProof,
      endpoint: role.endpoint,
    },
  ];
}

function buildDenseTimeline(role, product = {}, scene = "安静的浅色室内") {
  const shots = denseShotPlan(role, product, scene);
  const blocks = DENSE_TIMELINE_RANGES.map(([start, end], index) => {
    const shot = shots[index];
    return [
      `镜头${index + 1}：[${start}—${end}]｜${shot.framing}｜${shot.view}`,
      `画面：在${shot.scene}，${shot.action}。`,
      `镜头：${shot.camera}。`,
      `展示：${shot.proof}。`,
      `段落终点：${shot.endpoint}。`,
    ].join("\n");
  });
  return `【时间轴】\n15秒高密度8镜头，镜头1—8按编号依次硬切；每镜头一个主动作和一个主要视角，动作完整结束后再切镜。\n\n${blocks.join("\n\n")}`;
}

function buildTimeline(role, duration, scene, product = {}) {
  if (duration >= 15) return buildDenseTimeline(role, product, scene);

  if (duration <= 5 || role.oneTake) {
    const combinedAction = duration <= 5 ? role.actions[0] : `${role.actions[0]}；随后${role.actions[1]}`;
    return `【连续动作】0—${duration}秒：在${scene}，${combinedAction}。\n【镜头】${role.cameras[0]}；全程不切镜，不追加第二种运镜。\n【展示】${role.proofs?.[0] || role.task}。\n【段落终点】动作完成，主体、操作者和镜头同时停止并保持到视频结束。`;
  }

  const shotCount = 2;
  const shotLength = duration / shotCount;
  const lines = [];
  for (let index = 0; index < shotCount; index += 1) {
    const start = formatTime(index * shotLength);
    const end = formatTime((index + 1) * shotLength);
    lines.push(`${start}—${end}秒｜动作：在${scene}，${role.actions[index]}。镜头：${role.cameras[index]}。展示：${role.proofs?.[index] || role.task}。段落终点：动作完整结束后再切镜。`);
  }
  return `【时间轴】\n${lines.join("\n")}`;
}

function buildFramingClause(roleKey, profile) {
  if (roleKey === "detail") {
    return "【构图硬性要求】使用受控近景，只让目标结构占据主要画面；结构边缘、数量、连接关系和相邻材质都要可见，不用手遮挡，不用过浅景深虚化关键边缘。";
  }
  if (isApparelProfile(profile)) {
    return `【构图硬性要求】${profile.framing}；动作和跟拍中人物尺度保持稳定，不裁掉商品关键边缘，不用包、头发、手臂或前景遮挡主结构。`;
  }
  return `【构图硬性要求】${profile.framing}；动作和运镜中商品尺度保持稳定，不裁掉完整轮廓或操作点；人物、手、宠物、食材、配件、道具和前景都不得遮挡主结构。`;
}

function buildContinuityClause(product, profile) {
  const boundary = product.stylingBoundary || (isApparelProfile(profile)
    ? "内搭、鞋、包和饰品都是造型层，不属于商品本体"
    : "人物、手、宠物、食材、道具与环境都是展示层，不属于商品本体");
  if (isApparelProfile(profile)) {
    return `【连续性与物理】全片为同一位原创成年模特、同一件商品、同一颜色和同一套造型；${boundary}。${profile.frontBackRule}。${profile.motionProof}。面料只按当前档案的可见表现响应动作和重力；停止动作后保持自然状态，不闪烁、不穿模、不透明度跳变、不换材质。`;
  }
  return `【连续性与物理】全片复用${profile.subject}；${boundary}。${profile.continuityRule}。${profile.motionProof}。材质、内容物、部件和工作状态只按当前档案与对应参考发生可见变化；动作停止后保持真实终点，不闪烁、不穿模、不凭空增减、不换材质。`;
}

function buildNegativeClause(profile, roleKey) {
  const exclusions = [
    ...profile.exclusions,
    "不新增当前档案和权威参考没有确认的结构、颜色、装饰或功能",
    roleKey === "detail" ? "不触摸、拉扯或遮挡目标细节" : "不裁切、遮挡或缩小主商品到不可核对",
  ];
  const subjectFailures = isApparelProfile(profile)
    ? "禁止换脸、身体比例突变、异常手指、衣物穿模、镜像正背面错误、设备或拍摄人员入镜"
    : "禁止异常手指、商品穿模、部件融合、比例跳变、危险操作、设备或拍摄人员入镜";
  return `【负面约束】${[...new Set(exclusions)].slice(0, 5).join("；")}。${subjectFailures}。禁止新增画内字幕、标题、价格、链接、平台UI、品牌水印和乱码。`;
}

function promptSection(prompt, label) {
  const marker = `【${label}】`;
  const startIndex = String(prompt || "").indexOf(marker);
  if (startIndex < 0) return "";
  const contentStart = startIndex + marker.length;
  const nextIndex = String(prompt).indexOf("\n【", contentStart);
  return String(prompt).slice(contentStart, nextIndex < 0 ? undefined : nextIndex).trim();
}

function promptMotionBlock(prompt) {
  const timeline = promptSection(prompt, "时间轴");
  if (timeline) return `【时间轴】\n${timeline}`;
  const labels = ["连续动作", "镜头", "展示", "段落终点"];
  return labels
    .map((label) => {
      const value = promptSection(prompt, label);
      return value ? `【${label}】${value}` : "";
    })
    .filter(Boolean)
    .join("\n");
}

function directShotIndices(roleKey) {
  return DIRECT_SHOT_INDEX_MAP[roleKey] || [0, 1, 2];
}

function denseBlockField(block, label) {
  const prefix = `${label}：`;
  const line = String(block || "").split("\n").find((item) => item.trim().startsWith(prefix));
  return clean(line ? line.trim().slice(prefix.length) : "").replace(/[。；]+$/, "");
}

function compactClauses(value, clauseLimit = 2, charLimit = 80) {
  const clauses = String(value || "")
    .split(/[，,；;。]/)
    .map(clean)
    .filter(Boolean)
    .slice(0, clauseLimit);
  return compactPromptFact(clauses.join("，") || value, charLimit);
}

function compactDirectReference(role, fallback = "") {
  const refs = refsForPrompt(role);
  if (refs.length) {
    const bindings = refs.map((ref) => `${ref.placeholder}锁定${compactFactList(ref.authority, 2, 58)}`);
    return `${bindings.join("；")}。只参考商品本体，不复制图中人物、场景、品牌、水印或文字。`;
  }
  if (fallback) return compactPromptFact(fallback, 150);
  return "纯文本模式，未确认的商品结构保持不可见，不自行补全。";
}

function compactDirectAction(value, charLimit = 105) {
  const withoutRepeatedScene = clean(value).replace(/^在[^，,]{1,48}[，,]\s*/, "");
  return compactPromptFact(withoutRepeatedScene, charLimit);
}

function compactDenseMotionBlock(prompt, role) {
  const timeline = promptSection(prompt, "时间轴");
  if (!timeline || !/镜头\d+：/.test(timeline)) return "";
  const blocks = timeline
    .split(/\n\n(?=镜头\d+：)/)
    .map((block) => block.replace(/^.*?(?=镜头\d+：)/s, "").trim())
    .filter((block) => /^镜头\d+：/.test(block));
  if (blocks.length < 8) return "";
  const ranges = [["0", "5"], ["5", "10"], ["10", "15"]];
  const selected = directShotIndices(role.key);
  const compact = selected.map((sourceIndex, index) => {
    const block = blocks[sourceIndex];
    const action = compactDirectAction(denseBlockField(block, "画面"));
    const camera = compactClauses(denseBlockField(block, "镜头"), 2, 72);
    const endpoint = compactClauses(denseBlockField(block, "段落终点"), 2, 64);
    return `镜头${index + 1}（${ranges[index][0]}—${ranges[index][1]}秒）：${action || role.actions?.[index] || role.task}。${camera || role.cameras?.[index] || "固定稳定构图"}；终点：${endpoint || "人物与镜头同时停稳"}。`;
  });
  return `【三镜头】15秒只生成以下3个主镜头，同一人物、商品、造型和地点；不增加剧情或换场。\n${compact.join("\n")}`;
}

function lightForScene(scene = "") {
  if (/桌面|梳妆|收纳|展示台/.test(scene)) return "窗边柔和侧光扫过商品表面，标签、接口、边缘与材质保持清楚，背景反射克制";
  if (/厨房|餐桌|早餐|水槽/.test(scene)) return "厨房或餐桌侧窗的自然散射光，食品与器具保持真实本色，高光不过曝";
  if (/浴室|家务/.test(scene)) return "空间原有顶灯配合柔和侧窗光，水汽或高光受控，商品结构清楚";
  if (/车内|停车|汽车/.test(scene)) return "车辆静止时的柔和日光从侧窗进入，安装点与商品边缘清楚，不使用闪烁灯光";
  if (/街|店|咖啡|公园|户外/.test(scene)) return "阴天或树荫下的自然散射光，商品本色不被环境色染偏，阴影柔和";
  if (/走廊|玄关|住宅/.test(scene)) return "住宅入口的柔和侧光，光向稳定，墙面反射克制，不使用戏剧性逆光";
  return "窗边柔和自然光从画面侧前方进入，曝光稳定，商品本色与背景色分离";
}

function compactPromptFact(value, limit = 150) {
  const text = clean(value);
  return text.length > limit ? `${text.slice(0, limit).trim()}…` : text;
}

function compactFactList(value, itemLimit = 2, charLimit = 90) {
  const facts = splitProductFacts(value, itemLimit);
  return compactPromptFact(facts.join("、") || value, charLimit);
}

function buildDirectPrompt(role, product, sourcePrompt, scene = "安静的浅色室内") {
  if (isFidelityMode(product)) return String(sourcePrompt || "").trim();
  const reference = compactDirectReference(role, promptSection(sourcePrompt, "参考"));
  const motion = product.duration >= 15
    ? (compactDenseMotionBlock(sourcePrompt, role) || promptMotionBlock(sourcePrompt))
    : promptMotionBlock(sourcePrompt);
  const endpoint = compactClauses(promptSection(sourcePrompt, "终点") || role.endpoint, 2, 100);
  const profile = role.profile || inferProductProfile(product);
  const apparel = isApparelProfile(profile);
  const coverage = role.coverage || referenceCoverage(product);
  const structureFacts = role.key === "detail"
    ? [compactFactList(product.frontStructure, 3, 100), compactFactList(product.material, 2, 70)]
    : role.key === "overview"
      ? [compactFactList(product.frontStructure, 2, 80), coverage.allowBack ? compactFactList(product.backStructure, 1, 60) : ""]
      : [compactFactList(product.material, 2, 70)];
  const facts = [...new Set([
    `商品始终是同一件“${product.name}”，类别固定为${product.category}`,
    product.color && `颜色为${compactPromptFact(product.color, 60)}`,
    product.silhouette && `外形或规格为${compactFactList(product.silhouette, 2, 70)}`,
    ...structureFacts.filter(Boolean),
    product.anchors && `重点锁定${splitProductFacts(product.anchors, 2).join("、")}`,
  ].filter(Boolean))];
  const productLock = promptSection(sourcePrompt, "商品锁定");
  const noBack = coverage.allowBack ? "" : "不展示或补全未知背面、底部或隐藏结构；";
  const subject = apparel
    ? `同一位原创成年模特穿着“${product.name}”`
    : `${profile.subject}展示“${product.name}”`;
  const sound = apparel
    ? "无配乐，仅低环境声、脚步和衣料摩擦；无对白。"
    : "无配乐，仅低环境声和与操作同步的真实接触声；无对白。";
  return [
    `【参考】${reference}`,
    `【主体与动作】${subject}，在${scene}。本条任务：${compactPromptFact(role.task, 120)}。${profile.operator}。画幅${product.ratio}，普通商品记录，正常速度。`,
    productLock && `【核心商品锁】${productLock}`,
    motion,
    `【光线】${lightForScene(scene)}。`,
    `【声音】${sound}`,
    `【保持】${facts.join("；")}；${compactClauses(profile.framing, 2, 90)}；${noBack}${profile.exclusions.slice(0, 2).join("；")}；无文字、水印、拍摄设备或人员。`,
    `【最终状态】${endpoint}`,
  ].filter(Boolean).join("\n");
}

function directPromptBudget(duration, promptMode = "stable") {
  if (promptMode === "fidelity") return 9000;
  if (duration <= 5) return 650;
  if (duration <= 10) return 850;
  return 2600;
}

function directPromptQuality(prompt, productOrDuration) {
  const text = String(prompt || "");
  const product = typeof productOrDuration === "object"
    ? productOrDuration
    : { duration: Number(productOrDuration) || 15, promptMode: "stable" };
  const duration = Number(product.duration) || 15;
  const fidelity = isFidelityMode(product);
  const orderLabels = (fidelity
    ? ["【参考】", "【整体设定】", "【商品锁定】", "【时间轴】", "【连续性与物理】", "【声音】", "【终点】"]
    : ["【参考】", "【主体与动作】", "【核心商品锁】", duration >= 15 ? "【三镜头】" : "", "【光线】", "【声音】", "【保持】"])
    .filter(Boolean);
  const positions = orderLabels.map((label) => text.indexOf(label));
  const shotIds = [...text.matchAll(/镜头\s*(\d+)\s*(?=[：:（(【】])/g)].map((match) => Number(match[1]));
  return {
    length: Array.from(text).length,
    budget: directPromptBudget(duration, fidelity ? "fidelity" : "stable"),
    shotCount: new Set(shotIds).size,
    fillers: SEEDANCE_SKILL_COMPILER.forbiddenFillers.filter((word) => text.includes(word)),
    ordered: positions.every((position, index) => position >= 0 && (index === 0 || position > positions[index - 1])),
  };
}

function roleForDuration(role, duration) {
  if (duration < 15 || role.key !== "ending") return role;
  return {
    ...role,
    title: `${role.profile.name}干净收尾`,
    task: "只生成进入画面、缓慢转向镜头并停住的干净商品收尾，不加入新卖点、道具或场景",
    oneTake: false,
  };
}

function buildPrompt(roleKey, product, commonLock, index, template) {
  const role = roleForDuration({ key: roleKey, ...roleForTemplate(roleKey, template, product) }, product.duration);
  const scene = product.scenes[index % product.scenes.length] || "安静的浅色室内";
  const hasReferences = state.references.length > 0;
  const apparel = isApparelProfile(role.profile);
  const subjectSetting = apparel
    ? "同一位原创成年模特，健康自然体态，真实肤质，动作只服务于服饰展示"
    : `${role.profile.subject}；${role.profile.operator}；商品始终是画面主角`;
  const captureStyle = apparel
    ? "普通手机或轻量相机生活记录感，正常速度，不使用电影大片、T台、棚拍或奢侈品广告式表演"
    : "普通手机或轻量相机真实商品记录，正常速度，不使用电影大片、悬浮环绕、复杂棚拍或夸张功能表演";
  const sound = apparel
    ? "仅保留与动作同步的轻微环境声、脚步和衣料摩擦，无对白、无旁白、无生成配乐"
    : "仅保留与操作同步的轻微环境声和真实接触声，无对白、无旁白、无生成配乐";
  const prompt = [
    `提示词${index + 1}｜${role.title}｜${product.duration}秒｜${role.risk}`,
    "",
    `【模式】${hasReferences ? "图像参考商品展示；请先在 Seedance 界面把下列占位符替换成系统插入的真实 @ 标签" : "纯文本商品展示草案；未确认结构保持不可见"}。`,
    `【非叙事任务】实用意图：${role.task}。拒绝编造人物欲望、冲突、剧情转折或商品人格化。`,
    `【主任务】${role.task}。商品结构优先于人物、环境和风格。`,
    buildReferenceClause(role),
    `【整体设定】${product.ratio}，${product.market}；${subjectSetting}。场景只使用${scene}，自然光或场景原有灯光，${captureStyle}。`,
    `【商品锁定】${commonLock}`,
    `【模板策略】${template.promptRule}`,
    buildFramingClause(roleKey, role.profile),
    buildTimeline(role, product.duration, scene, product),
    buildContinuityClause(product, role.profile),
    "【画面】自然曝光，商品本色、材质边缘与环境色清楚分离，镜头只做时间轴指定的移动。画面中不出现手机、相机、自拍杆、三脚架、补光灯、麦克风、拍摄人员或设备反射。",
    `【声音】${sound}；不同生成片段的统一音乐在后期添加。`,
    `【终点】${role.endpoint}。`,
    buildNegativeClause(role.profile, roleKey),
    "【后期边界】输出无文字干净画面；字幕、日语配音、BGM、价格、优惠、法律文案和CTA全部留到可编辑剪辑阶段。",
  ].join("\n");
  const promptItem = { ...role, scene, prompt };
  return { ...promptItem, directPrompt: buildDirectPrompt(promptItem, product, prompt, scene) };
}

function buildRepairs(product, selectedProfile = null) {
  const profile = selectedProfile || inferProductProfile(product);
  const repairs = [
    { title: "颜色漂移", text: `追加：商品颜色只以主权威参考和“${product.color || "已确认主颜色"}”为准，环境色不得改变商品本色。` },
    { title: "品类或结构改变", text: `追加：画面中的商品始终是${product.category}；${profile.exclusions[0]}；只保留当前档案和权威参考确认的结构。` },
  ];
  if (isApparelProfile(profile) && ["overalls", "trousers"].includes(profile.id)) {
    repairs.push({ title: "裤腿融合或变成裙装", text: "追加：裆部和左右裤腿在每一帧都清楚分离，左腿只跟随左腿运动，右腿只跟随右腿运动，不形成连续裙摆。" });
  }
  if (/扣|五金|肩带|金属/.test(product.frontStructure + product.anchors + product.name)) {
    repairs.push({ title: "肩带 / 五金变化", text: "追加：固定肩带和扣件的实际数量、位置、尺寸与颜色；本镜头不触摸扣件，使用稳定正面近景。" });
  }
  if (isApparelProfile(profile) && profile.id === "dress") {
    repairs.push({ title: "裙摆分裂", text: "追加：裙摆从腰部到下摆保持一片连续结构，缩小步幅，取消快速转身。" });
  }
  if (isApparelProfile(profile) && ["knitwear", "top", "outerwear"].includes(profile.id)) {
    repairs.push({ title: "正背面复制 / 面料乱纹", text: `追加：${profile.frontBackRule}；固定镜头和光向，面料只保留当前档案确认的表面表现。` });
  }
  if (!isApparelProfile(profile)) {
    repairs.push({ title: "部件或状态跳变", text: `追加：${profile.continuityRule}；只保留一个低风险操作，使用固定机位完整记录开始、变化、结束与停住。` });
  }
  repairs.push({ title: "手部导致商品变形", text: "追加：操作手离开目标结构，不拉扯、不遮挡、不重复触发；改由固定镜头展示该细节。" });
  return repairs.slice(0, 5);
}

function buildQc(product, template, prompts = []) {
  const filledFacts = [product.color, product.silhouette, product.frontStructure, product.backStructure, product.material, product.stylingBoundary].filter(Boolean).length;
  const roles = state.references.map((item) => item.role);
  const duplicateRole = roles.some((role, index) => roles.indexOf(role) !== index);
  const anchors = product.anchors.split(/[，,、；;]/).map(clean).filter(Boolean);
  const coverage = referenceCoverage(product);
  const coverageNotes = [];
  const directMetrics = prompts.map((item) => directPromptQuality(item.directPrompt || item.prompt, product));
  const longestDirect = directMetrics.reduce((longest, item) => Math.max(longest, item.length), 0);
  const modeLabel = isFidelityMode(product) ? "高还原" : "精简稳定";
  const expectedShots = expectedDirectShotCount(product);
  const directBudget = directPromptBudget(product.duration, isFidelityMode(product) ? "fidelity" : "stable");
  const wrongShotCount = directMetrics.some((item) => item.shotCount !== expectedShots);
  const fillerWords = [...new Set(directMetrics.flatMap((item) => item.fillers))];
  if (coverage.hasReferences && !coverage.back) coverageNotes.push("缺背面或底部图，已取消隐藏结构补全");
  if (coverage.hasReferences && !coverage.side) coverageNotes.push("缺侧面图，已把完整侧面证明降级为轻微三分之二角度");
  if (coverage.hasReferences && !coverage.detail) coverageNotes.push("缺结构细节图，细节提示词只作保守近景");
  return [
    { ok: true, text: "本次提示词只读取当前表单，未引用旧商品名称或旧版型结构。" },
    { ok: true, text: `模板已解析为“${template.name} / ${template.profile.name}”；完整规则控制拍法，商品事实仍只读取当前档案。` },
    { ok: true, text: `已启用 ${template.modules?.length || 3} 个模板模块：参考职责、商品锁、构图、分镜、物理、连续性、负面约束与修复分别检查。` },
    { ok: true, text: `${SEEDANCE_SKILL_COMPILER.name} v${SEEDANCE_SKILL_COMPILER.version} 与通用商品路由已共同编译直贴提示词。` },
    { ok: !directMetrics.length || longestDirect <= directBudget, text: !directMetrics.length || longestDirect <= directBudget ? `${modeLabel}提示词长度在当前预算内，最长 ${longestDirect} 字符。` : `最长提示词 ${longestDirect} 字符，超过 ${directBudget} 字符预算；请删除商品档案中的重复描述。` },
    { ok: !wrongShotCount, text: wrongShotCount ? `${modeLabel}提示词应为 ${expectedShots} 个镜头，请重新生成。` : `${modeLabel}模式镜头数量正确：${expectedShots}镜头，每镜头都有动作、主要视角和终点。` },
    { ok: directMetrics.every((item) => item.ordered), text: directMetrics.every((item) => item.ordered) ? `${modeLabel}提示词已按参考、商品锁、时间轴、物理、声音和终点的优先顺序编排。` : "提示词章节顺序异常，请重新生成。" },
    { ok: fillerWords.length === 0, text: fillerWords.length ? `发现空泛质量词：${fillerWords.join("、")}；请删除并改成可见的光线、动作或材质。` : "未使用电影感、高级感、4K等空泛质量词。" },
    { ok: filledFacts >= 4, text: filledFacts >= 4 ? `已确认 ${filledFacts} 组商品事实。` : `只确认了 ${filledFacts} 组商品事实，建议至少补足颜色、外形、主要结构和商品边界。` },
    { ok: state.references.length >= 2, text: state.references.length >= 2 ? `已绑定 ${state.references.length} 张参考图。` : "参考图少于 2 张；可先做纯文本测试，但细节稳定性风险较高。" },
    { ok: !duplicateRole, text: duplicateRole ? "有多张图片承担相同角色；发生冲突时请保留更清楚的一张作为权威来源。" : "每张参考图的主要职责没有重复。" },
    {
      ok: coverage.hasReferences && coverageNotes.length === 0,
      text: !coverage.hasReferences
        ? "当前是纯文本模式；不会把未知背面当作已确认事实。"
        : coverageNotes.length
          ? coverageNotes.join("；") + "。"
          : "参考覆盖范围足以执行当前主视图、结构、侧面和背面 / 底部计划。",
    },
    { ok: anchors.length >= 3, text: anchors.length >= 3 ? `已锁定 ${anchors.length} 个易漂移锚点。` : "易漂移锚点少于 3 项，建议补充最容易变成另一件商品的结构。" },
    { ok: product.scenes.length > 0, text: product.scenes.length ? `场景限制在：${product.scenes.join("、")}。` : "未选择场景，已回退到安静的浅色室内。" },
    { ok: true, text: "画内文字、配音、BGM、价格和 CTA 默认全部留到可编辑后期。" },
  ];
}

function renderReferenceMap() {
  const map = referenceAuthorityMap();
  if (!map.length) {
    elements.referenceMapList.innerHTML = `
      <article class="map-item is-warning"><span>未绑定</span><strong>纯文本草案</strong><small>建议补充商品主视图</small></article>
      <article class="map-item is-warning"><span>待补充</span><strong>@产品结构细节图</strong><small>控制接口、开合、扣件、标签位置或主要结构</small></article>
      <article class="map-item is-warning"><span>待补充</span><strong>@产品背面或底部图</strong><small>没有权威图片就不生成隐藏结构</small></article>`;
    return;
  }
  const counts = map.reduce((result, item) => {
    result[item.value] = (result[item.value] || 0) + 1;
    return result;
  }, {});
  elements.referenceMapList.innerHTML = map.map((item) => `
    <article class="map-item${counts[item.value] > 1 ? " is-warning" : ""}">
      <span>${escapeHtml(item.placeholder)}</span>
      <strong title="${escapeHtml(item.fileName)}">${escapeHtml(item.fileName)}</strong>
      <small>${escapeHtml(item.authority)}${counts[item.value] > 1 ? " · 角色重复" : ""}</small>
    </article>
  `).join("");
}

function renderPrompts(prompts) {
  const fidelity = isFidelityMode(state.product || collectProduct());
  const directLabel = fidelity ? "高还原直贴版" : "精简稳定版";
  const directCopyLabel = fidelity ? "复制高还原版" : "复制稳定版";
  elements.promptList.innerHTML = prompts.map((prompt, index) => `
    <details class="prompt-card"${index === 0 ? " open" : ""}>
      <summary>
        <span class="prompt-index">${String(index + 1).padStart(2, "0")}</span>
        <span class="prompt-title"><strong>${escapeHtml(prompt.title)}</strong><small>${escapeHtml(prompt.risk)} · ${escapeHtml(elements.duration.value)}S</small></span>
        <span class="prompt-summary-actions">
          <button class="copy-prompt-button" type="button" data-prompt-index="${index}" data-prompt-variant="direct">${directCopyLabel}</button>
          <i class="prompt-toggle" aria-hidden="true">＋</i>
        </span>
      </summary>
      <div class="prompt-versions">
        <section class="prompt-version is-direct">
          <header>
            <div><span>DIRECT INPUT</span><strong>${directLabel}</strong></div>
            <button type="button" data-prompt-index="${index}" data-prompt-variant="direct">${directCopyLabel}</button>
          </header>
          <div class="prompt-body prompt-direct-body">${escapeHtml(prompt.directPrompt || prompt.prompt)}</div>
        </section>
        ${fidelity ? "" : `<details class="prompt-version is-inspection">
          <summary>展开检查完整版 <small>商品锁 · 参考职责 · 失败约束</small></summary>
          <div class="inspection-actions"><button type="button" data-prompt-index="${index}" data-prompt-variant="full">复制完整版</button></div>
          <div class="prompt-body">${escapeHtml(prompt.prompt)}</div>
        </details>`}
      </div>
    </details>
  `).join("");
}

function renderQc(qcItems) {
  elements.qcList.innerHTML = qcItems.map((item) => `<li class="${item.ok ? "" : "is-warning"}">${escapeHtml(item.text)}</li>`).join("");
}

function renderRepairs(repairs) {
  elements.repairList.innerHTML = repairs.map((item) => `
    <article class="repair-item"><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.text)}</p></article>
  `).join("");
}

function renderFidelityReport(report = state.fidelityReport) {
  if (!elements.fidelityScoreValue) return;
  state.fidelityReport = report || null;
  if (!report || !Number.isFinite(Number(report.score))) {
    elements.fidelityScoreValue.textContent = "—";
    elements.fidelityScoreGrade.textContent = "等待生成";
    elements.fidelityScoreSummary.textContent = "评分检查提示词是否锁住颜色、轮廓、接口、文字边界、部件数量与位置；它是生成前预测，不代表对实际视频画面的验收。";
    elements.fidelityDimensions.innerHTML = "";
    elements.fidelitySuggestions.innerHTML = "";
    return;
  }
  const score = Math.max(0, Math.min(100, Math.round(Number(report.score))));
  elements.fidelityScoreValue.textContent = String(score);
  elements.fidelityScoreGrade.textContent = clean(report.grade) || (score >= 90 ? "高锁定" : score >= 75 ? "可生成" : score >= 60 ? "需复核" : "高风险");
  elements.fidelityScoreSummary.textContent = clean(report.summary) || "当前分数来自最终提示词的商品事实覆盖检查。";
  const dimensions = Array.isArray(report.dimensions) ? report.dimensions : [];
  elements.fidelityDimensions.innerHTML = dimensions.map((item) => `
    <article class="fidelity-dimension">
      <strong>${escapeHtml(item.label || item.key || "检查项")}</strong>
      <b>${Math.round(Number(item.score || 0))}</b>
      <small>${escapeHtml(item.message || "")}</small>
    </article>
  `).join("");
  const suggestions = Array.isArray(report.suggestions) ? report.suggestions : [];
  elements.fidelitySuggestions.innerHTML = suggestions.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function loadHistoryVersions() {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || "[]");
    state.history = Array.isArray(parsed) ? parsed.filter((item) => item && typeof item === "object" && item.id).slice(0, MAX_HISTORY_VERSIONS) : [];
  } catch {
    state.history = [];
  }
  renderVersionHistory();
}

function persistHistoryVersions() {
  let versions = state.history.slice(0, MAX_HISTORY_VERSIONS);
  while (versions.length) {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(versions));
      state.history = versions;
      return true;
    } catch {
      versions = versions.slice(0, -1);
    }
  }
  try {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
  } catch {
    // Version history is optional; current prompts remain usable.
  }
  state.history = [];
  return false;
}

function historyVersionLabel(version) {
  const date = new Date(version.createdAt || Date.now());
  const time = Number.isNaN(date.getTime()) ? "未知时间" : date.toLocaleString("zh-CN", { hour12: false });
  const kind = version.kind === "optimized" ? "AI精修" : version.kind === "restored" ? "已恢复" : "AI生成";
  return `${kind} · ${time}`;
}

function saveHistorySnapshot(kind = "generated") {
  if (!state.product || !state.prompts.length) return;
  const snapshot = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    createdAt: new Date().toISOString(),
    kind,
    product: JSON.parse(JSON.stringify(state.product)),
    prompts: JSON.parse(JSON.stringify(state.prompts)),
    commonLock: state.commonLock,
    repairs: JSON.parse(JSON.stringify(state.repairs || [])),
    template: state.template ? JSON.parse(JSON.stringify(state.template)) : null,
    generation: state.generation ? JSON.parse(JSON.stringify(state.generation)) : null,
    optimization: state.optimization ? JSON.parse(JSON.stringify(state.optimization)) : null,
    fidelityReport: state.fidelityReport ? JSON.parse(JSON.stringify(state.fidelityReport)) : null,
    referenceConsistency: state.referenceConsistency ? JSON.parse(JSON.stringify(state.referenceConsistency)) : null,
    referenceFiles: referenceAuthorityMap().map((item) => ({ fileName: item.fileName, role: item.label, authority: item.authority })),
    packText: state.packText,
    directPackText: state.directPackText,
  };
  state.history = [snapshot, ...state.history].slice(0, MAX_HISTORY_VERSIONS);
  const saved = persistHistoryVersions();
  renderVersionHistory();
  if (!saved) toast("浏览器存储空间不足，当前结果可用，但本次历史版本未保存。", "error");
}

function renderVersionHistory() {
  if (!elements.versionHistoryList) return;
  elements.versionHistoryCount.textContent = `${state.history.length} / ${MAX_HISTORY_VERSIONS}`;
  if (!state.history.length) {
    elements.versionHistoryList.innerHTML = '<p class="version-history-empty">还没有历史版本。</p>';
  } else {
    elements.versionHistoryList.innerHTML = state.history.map((version) => `
      <article class="history-version-card">
        <strong title="${escapeHtml(version.product?.name || "未命名商品")}">${escapeHtml(version.product?.name || "未命名商品")}</strong>
        <small>${escapeHtml(historyVersionLabel(version))}</small>
        <small>${escapeHtml(version.product?.platformStrategy?.label || "自定义平台")} · ${escapeHtml(version.product?.ratio || "—")} · ${Number(version.product?.duration || 0)}秒 · ${version.prompts?.length || 0}条</small>
        <button type="button" data-history-restore="${escapeHtml(version.id)}">恢复此版本</button>
      </article>
    `).join("");
  }
  const options = state.history.map((version) => `<option value="${escapeHtml(version.id)}">${escapeHtml(version.product?.name || "未命名商品")} · ${escapeHtml(historyVersionLabel(version))}</option>`).join("");
  const previousLeft = elements.historyCompareLeft.value;
  const previousRight = elements.historyCompareRight.value;
  elements.historyCompareLeft.innerHTML = options;
  elements.historyCompareRight.innerHTML = options;
  if (state.history.some((item) => item.id === previousLeft)) elements.historyCompareLeft.value = previousLeft;
  if (state.history.some((item) => item.id === previousRight)) elements.historyCompareRight.value = previousRight;
  if (state.history.length > 1 && !elements.historyCompareRight.value) elements.historyCompareRight.selectedIndex = 1;
  if (state.history.length > 1 && elements.historyCompareLeft.value === elements.historyCompareRight.value) elements.historyCompareRight.selectedIndex = 1;
  elements.historyCompareButton.disabled = state.history.length < 2;
}

function promptDifferenceCount(left = "", right = "") {
  const leftLines = String(left).split("\n");
  const rightLines = String(right).split("\n");
  const length = Math.max(leftLines.length, rightLines.length);
  let changed = 0;
  for (let index = 0; index < length; index += 1) {
    if ((leftLines[index] || "") !== (rightLines[index] || "")) changed += 1;
  }
  return changed;
}

function compareHistoryVersions() {
  const left = state.history.find((item) => item.id === elements.historyCompareLeft.value);
  const right = state.history.find((item) => item.id === elements.historyCompareRight.value);
  if (!left || !right || left.id === right.id) {
    toast("请选择两个不同的历史版本。", "error");
    return;
  }
  const settingPairs = [
    ["平台", left.product?.platformStrategy?.label, right.product?.platformStrategy?.label],
    ["品类", left.product?.category, right.product?.category],
    ["画幅", left.product?.ratio, right.product?.ratio],
    ["时长", `${left.product?.duration || 0}秒`, `${right.product?.duration || 0}秒`],
    ["提示词数", left.prompts?.length, right.prompts?.length],
    ["还原度", left.fidelityReport?.score ?? "未评分", right.fidelityReport?.score ?? "未评分"],
  ];
  const changedSettings = settingPairs.filter(([, a, b]) => String(a ?? "") !== String(b ?? ""));
  const promptCount = Math.max(left.prompts?.length || 0, right.prompts?.length || 0);
  const promptChanges = [...Array(promptCount)].map((_, index) => {
    const leftPrompt = left.prompts?.[index]?.directPrompt || left.prompts?.[index]?.prompt || "";
    const rightPrompt = right.prompts?.[index]?.directPrompt || right.prompts?.[index]?.prompt || "";
    return { index, changed: promptDifferenceCount(leftPrompt, rightPrompt), title: right.prompts?.[index]?.title || left.prompts?.[index]?.title || `提示词 ${index + 1}` };
  });
  elements.historyCompareResult.hidden = false;
  elements.historyCompareResult.innerHTML = `
    <div class="history-diff-grid">
      <article><strong>版本 A</strong><small>${escapeHtml(historyVersionLabel(left))}<br>${escapeHtml(left.product?.name || "未命名商品")}</small></article>
      <article><strong>版本 B</strong><small>${escapeHtml(historyVersionLabel(right))}<br>${escapeHtml(right.product?.name || "未命名商品")}</small></article>
      <article><strong>设置变化</strong><small>${changedSettings.length ? changedSettings.map(([label, a, b]) => `${label}：${a ?? "—"} → ${b ?? "—"}`).join("；") : "平台、品类、画幅、时长和数量一致"}</small></article>
      <article><strong>提示词变化</strong><small>${promptChanges.map((item) => `${item.index + 1}. ${item.title}：${item.changed} 行变化`).join("；")}</small></article>
    </div>`;
}

function applyProductToForm(product = {}) {
  const map = {
    productName: "name", category: "category", color: "color", silhouette: "silhouette",
    frontStructure: "frontStructure", backStructure: "backStructure", material: "material",
    stylingBoundary: "stylingBoundary", fragileAnchors: "anchors", templatePreset: "templatePreset",
    platformPreset: "platformPreset", promptMode: "promptMode", duration: "duration",
    promptCount: "count", ratio: "ratio", market: "market",
  };
  Object.entries(map).forEach(([elementKey, productKey]) => {
    if (elements[elementKey] && product[productKey] !== undefined) elements[elementKey].value = product[productKey];
  });
  state.categoryDrafts = {};
  const key = categorySchemaKey(product);
  state.categoryDrafts[key] = { ...(product.categoryDetails || {}) };
  renderCategoryFields({ preserve: false });
  document.querySelectorAll('input[name="scene"]').forEach((input) => {
    input.checked = Array.isArray(product.scenes) && product.scenes.includes(input.value);
  });
  renderPlatformPreset({ applySettings: false });
  renderTemplatePanel();
  renderPromptModeNote();
}

function restoreHistoryVersion(versionId) {
  const version = state.history.find((item) => item.id === versionId);
  if (!version) return;
  if (!window.confirm(`恢复“${version.product?.name || "未命名商品"}”的这个版本？当前未保存的表单改动会被替换，参考图需要重新上传。`)) return;
  state.references.forEach((reference) => reference.url && URL.revokeObjectURL(reference.url));
  state.references = [];
  applyProductToForm(version.product || {});
  state.product = JSON.parse(JSON.stringify(version.product || {}));
  state.prompts = JSON.parse(JSON.stringify(version.prompts || []));
  state.localPrompts = JSON.parse(JSON.stringify(version.prompts || []));
  state.commonLock = version.commonLock || "";
  state.repairs = JSON.parse(JSON.stringify(version.repairs || []));
  state.template = version.template || resolvePromptTemplate(state.product);
  state.generation = version.generation || null;
  state.optimization = version.optimization || null;
  state.packText = version.packText || buildPackText(state.product, state.commonLock, state.prompts, state.repairs, state.template, state.optimization, state.generation);
  state.directPackText = version.directPackText || buildDirectPackText(state.product, state.prompts, state.optimization, state.generation);
  state.referenceConsistency = null;
  renderReferences();
  renderReferenceConsistency();
  renderReferenceMap();
  elements.commonLock.textContent = state.commonLock;
  renderPrompts(state.prompts);
  renderQc(buildQc(state.product, state.template, state.prompts));
  renderRepairs(state.repairs);
  renderFidelityReport(version.fidelityReport || null);
  elements.emptyOutput.hidden = true;
  elements.outputContent.hidden = false;
  elements.copyDirectAllButton.disabled = false;
  elements.copyAllButton.disabled = false;
  elements.downloadButton.disabled = false;
  elements.outputSummary.textContent = `已恢复 ${historyVersionLabel(version)} · 参考图文件不会存入浏览器，请重新上传并检查一致性。`;
  updateOptimizeButton();
  saveForm();
  toast("历史版本已恢复；请重新上传并绑定当时使用的参考图。", "error");
}

function buildPackText(product, commonLock, prompts, repairs, template, optimization = null, generation = null) {
  const map = referenceAuthorityMap();
  const mapText = map.length
    ? map.map((item, index) => `${index + 1}. ${item.placeholder} ← ${item.fileName}：${item.authority}`).join("\n")
    : "未绑定参考图；当前为纯文本草案。";
  const repairText = repairs.map((item) => `- ${item.title}：${item.text}`).join("\n");
  const generationText = generation
    ? `生成方式：AI 根据当前新品档案与参考图从零编排；模型：${generation.model || "已配置模型"}；主生成 ${usageLabel(generation.usage)}。`
    : "生成方式：尚未执行 AI 新品生成。";
  const optimizationText = optimization
    ? `二次精修：已执行；模型：${optimization.model || "已配置模型"}；本次 ${usageLabel(optimization.usage)}。`
    : "二次精修：未执行。复制与下载不消耗 Token。";
  const fidelity = isFidelityMode(product);
  const promptLayers = fidelity
    ? [
      "【高还原 Seedance 直贴版｜完整商品锁 + 8镜头】",
      prompts.map((item) => item.directPrompt || item.prompt).join("\n\n────────────────────────\n\n"),
    ]
    : [
      "【精简稳定版｜实际生成优先使用】",
      prompts.map((item) => item.directPrompt || item.prompt).join("\n\n────────────────────────\n\n"),
      "",
      "【检查完整版｜用于核对和拆分】",
      prompts.map((item) => item.prompt).join("\n\n────────────────────────\n\n"),
    ];
  return [
    `${product.name}_Seedance提示词合集_${optimization ? "AI二次精修版" : "AI生成版"}`,
    "",
    `模式：${fidelity ? "高还原8镜头" : "精简稳定"}；商品参考图 + 已确认商品事实；${product.ratio}；单条 ${product.duration} 秒；共 ${prompts.length} 条。`,
    `提示词编译器：${SEEDANCE_SKILL_COMPILER.name} v${SEEDANCE_SKILL_COMPILER.version} + ${SEEDANCE_SKILL_COMPILER.fashionSkill}。`,
    `AI 导演约束：${SEEDANCE_SKILL_COMPILER.name} v${SEEDANCE_SKILL_COMPILER.version} + ${SEEDANCE_SKILL_COMPILER.fashionSkill}；品类安全规则：${template.profile.name}。`,
    "固定内容只包括输出结构、事实边界和质检规则；镜头动作、机位、场景、光线与终点由 AI 按当前新品重新推导。",
    generationText,
    optimizationText,
    "保守假设：适用于支持图像参考的 Seedance 界面；实际素材标签需在生成界面重新绑定。",
    "",
    "【参考角色表】",
    mapText,
    "",
    "【公共商品锁】",
    commonLock,
    "",
    ...promptLayers,
    "",
    "【失败修复条款】",
    repairText,
    "一次只追加一条匹配条款；同一结构连续两次失败时，拆分镜头或重写，不继续叠加否定词。",
    "",
    "【使用顺序】",
    "先测试完整外形，再测试关键结构，最后测试与当前品类匹配的真实操作；通过后再生成日常流程和生活场景。",
    "占位符不是有效绑定：请在 Seedance 页面上传图片，输入 @ 并选择实际文件，再替换为系统插入的真实标签。",
  ].join("\n");
}

function buildDirectPackText(product, prompts, optimization = null, generation = null) {
  const fidelity = isFidelityMode(product);
  return [
    `${product.name}_Seedance${fidelity ? "高还原8镜头版" : "精简稳定版"}_${optimization ? "AI二次精修" : "AI生成"}`,
    `共 ${prompts.length} 条；${product.ratio}；单条 ${product.duration} 秒。占位符需在 Seedance 中替换为真实 @ 标签。`,
    generation ? `由 ${generation.model || "已配置模型"} 根据当前新品从零生成；主生成 ${usageLabel(generation.usage)}。` : "尚未执行 AI 新品生成。",
    "以下每条都是独立生成单元：每次只复制一条，不能把整包一次粘贴到 Seedance。",
    product.duration >= 15
      ? (fidelity
        ? "每条15秒提示词包含完整核心商品锁和8个编号镜头；如果实际生成出现跳镜或动作遗漏，请切换精简稳定3镜头模式。"
        : "每条15秒提示词保留完整核心商品锁，并把动作负载降为同一地点3个主镜头。")
      : "直贴版遵循一条提示词一个主任务；检查完整版用于核对商品锁与失败约束。",
    "",
    prompts.map((item) => item.directPrompt || item.prompt).join("\n\n────────────────────────\n\n"),
  ].join("\n");
}

function validateProduct(product) {
  if (!product.name) {
    const color = clean(product.color).split(/[，,；;。]/)[0].slice(0, 24);
    const category = clean(product.category) && !["其他女装", "其他商品"].includes(product.category) ? clean(product.category) : "商品新品";
    product.name = `${color}${category}` || "当前商品新品";
    elements.productName.value = product.name;
    elements.productName.setAttribute("aria-invalid", "false");
    elements.productNameError.hidden = true;
    toast(`商品名称未填写，已自动命名为“${product.name}”。`);
  }
  return true;
}

function generateLocalPack() {
  const product = collectProduct();
  if (!validateProduct(product)) return;
  if (!product.scenes.length) product.scenes = ["安静的浅色室内"];
  const template = resolvePromptTemplate(product);
  const commonLock = buildCommonLock(product, template.profile);
  const roleKeys = COUNT_ROLE_MAP[product.count] || COUNT_ROLE_MAP[7];
  const prompts = roleKeys.map((roleKey, index) => buildPrompt(roleKey, product, commonLock, index, template));
  const repairs = buildRepairs(product, template.profile);

  state.product = product;
  state.commonLock = commonLock;
  state.repairs = repairs;
  state.template = template;
  state.localPrompts = prompts.map((item) => ({ ...item }));
  state.prompts = prompts.map((item) => ({ ...item }));
  state.optimization = null;
  state.optimizationError = "";
  state.packText = buildPackText(product, commonLock, state.prompts, repairs, template);
  state.directPackText = buildDirectPackText(product, state.prompts);
  renderReferenceMap();
  elements.commonLock.textContent = commonLock;
  renderPrompts(prompts);
  renderQc(buildQc(product, template, prompts));
  renderRepairs(repairs);
  elements.outputSummary.textContent = `${product.name} · ${prompts.length} 条 · ${isFidelityMode(product) ? "高还原8镜头" : "精简稳定"} / ${template.profile.name} · ${product.duration} 秒 · ${product.ratio}`;
  elements.emptyOutput.hidden = true;
  elements.outputContent.hidden = false;
  elements.copyDirectAllButton.disabled = false;
  elements.copyAllButton.disabled = false;
  elements.downloadButton.disabled = false;
  updateOptimizeButton();
  saveForm();
  toast(`已本地生成 ${prompts.length} 条独立提示词，0 Token。`);
  if (window.innerWidth <= 900) elements.outputContent.scrollIntoView({ behavior: "smooth", block: "start" });
}

function applyAiGeneration(result, product, commonLock, template) {
  const generated = Array.isArray(result?.prompts) ? result.prompts : [];
  const expectedCount = (COUNT_ROLE_MAP[product.count] || COUNT_ROLE_MAP[7]).length;
  if (generated.length !== expectedCount) throw new Error("AI 没有返回完整的提示词集合，请重新生成。");
  const byIndex = new Map(generated.map((item) => [Number(item.index), item]));
  if (byIndex.size !== expectedCount || [...byIndex.values()].some((item) => !clean(item.directPrompt) || !clean(item.inspectionPrompt))) {
    throw new Error("AI 返回的提示词索引或正文不完整，请重新生成。");
  }
  const prompts = [...Array(expectedCount)].map((_, index) => {
    const item = byIndex.get(index);
    return {
      key: clean(item.key),
      title: clean(item.title) || `AI 提示词 ${index + 1}`,
      risk: clean(item.risk) || "AI 动态评估",
      scene: clean(item.scene) || product.scenes[index % product.scenes.length],
      directPrompt: String(item.directPrompt || "").trim(),
      prompt: String(item.inspectionPrompt || "").trim(),
    };
  });
  const repairs = Array.isArray(result.repairs)
    ? result.repairs.map((item) => ({ title: clean(item?.title), text: String(item?.text || "").trim() })).filter((item) => item.title && item.text)
    : [];
  const generation = {
    model: clean(result.model) || state.aiConfig.model,
    usage: result.usage && typeof result.usage === "object" ? result.usage : {},
    notes: Array.isArray(result.notes) ? result.notes.map(clean).filter(Boolean).slice(0, 4) : [],
  };

  state.product = product;
  state.commonLock = commonLock;
  state.repairs = repairs;
  state.template = template;
  state.generation = generation;
  state.generationError = "";
  state.localPrompts = prompts.map((item) => ({ ...item }));
  state.prompts = prompts.map((item) => ({ ...item }));
  state.optimization = null;
  state.optimizationError = "";
  state.packText = buildPackText(product, commonLock, state.prompts, repairs, template, null, generation);
  state.directPackText = buildDirectPackText(product, state.prompts, null, generation);
  renderReferenceMap();
  elements.commonLock.textContent = commonLock;
  renderPrompts(state.prompts);
  renderQc(buildQc(product, template, state.prompts));
  renderRepairs(repairs);
  renderFidelityReport(result.fidelityReport || null);
  elements.outputSummary.textContent = `${product.name} · ${prompts.length} 条 · AI 从零生成 / ${isFidelityMode(product) ? "高还原8镜头" : "精简稳定"} / ${template.profile.name} · ${product.duration} 秒 · ${product.ratio}`;
  elements.emptyOutput.hidden = true;
  elements.outputContent.hidden = false;
  elements.copyDirectAllButton.disabled = false;
  elements.copyAllButton.disabled = false;
  elements.downloadButton.disabled = false;
  saveForm();
  saveHistorySnapshot("generated");
}

async function generatePack() {
  const product = collectProduct();
  if (!validateProduct(product) || state.aiBusy) return;
  if (!state.aiConfig.hasApiKey) {
    toast("主生成现在必须调用 AI，请先在页面顶部保存模型配置。", "error");
    document.querySelector("#ai-model-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    elements.aiBaseUrl.focus();
    return;
  }
  if (!product.scenes.length) product.scenes = ["安静的浅色室内"];
  if (isInsecureRemoteEndpoint() && !window.confirm(
    `当前模型节点使用明文 HTTP。继续后，API Key、当前新品档案${state.references.length ? "和参考图片" : ""}会通过未加密连接发送。多图会先进行一次一致性检查，再生成提示词并消耗 Token，确认继续吗？`,
  )) return;

  if (state.references.length > 1 && state.referenceConsistency?.fingerprint !== referenceFingerprint()) {
    state.aiBusy = true;
    updateAnalyzeButton();
    updateGenerateButton();
    updateOptimizeButton();
    elements.outputSummary.textContent = `正在检查 ${state.references.length} 张参考图是否属于同一商品……`;
    try {
      await ensureReferenceConsistency(product);
    } catch (error) {
      elements.outputSummary.textContent = error.message || "参考图一致性检查失败，请调整图片后重试。";
      toast(elements.outputSummary.textContent, "error");
      return;
    } finally {
      state.aiBusy = false;
      updateAnalyzeButton();
      updateGenerateButton();
      updateOptimizeButton();
    }
  } else {
    try {
      await ensureReferenceConsistency(product);
    } catch (error) {
      elements.outputSummary.textContent = error.message || "参考图一致性检查未通过。";
      toast(elements.outputSummary.textContent, "error");
      return;
    }
  }

  const template = resolvePromptTemplate(product);
  const commonLock = buildCommonLock(product, template.profile);
  const expectedWait = isFidelityMode(product)
    ? (product.count <= 3 ? "通常约3—5分钟" : "通常约6—10分钟")
    : (product.count <= 3 ? "通常约2—3分钟" : "通常约5—8分钟");
  const startedAt = Date.now();
  let progressTimer = null;
  state.aiBusy = true;
  state.generationError = "";
  updateAnalyzeButton();
  updateGenerateButton();
  updateOptimizeButton();
  const renderGenerationProgress = () => {
    const elapsed = Math.floor((Date.now() - startedAt) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = String(elapsed % 60).padStart(2, "0");
    elements.outputSummary.textContent = `AI 正在从零编排 ${product.count} 条提示词 · 已等待 ${minutes}:${seconds} · ${expectedWait}，请不要重复点击或关闭页面。`;
  };
  renderGenerationProgress();
  progressTimer = window.setInterval(renderGenerationProgress, 1000);
  try {
    const images = await Promise.all(state.references.map(async (reference) => ({
      name: reference.file.name,
      role: reference.role,
      dataUrl: await fileToDataUrl(reference.file),
    })));
    const referenceMap = referenceAuthorityMap().map((item) => ({
      placeholder: item.placeholder,
      role: item.label,
      roleKey: item.value,
      authority: item.authority,
      fileName: item.fileName,
    }));
    const result = await requestJson("/api/fashion-prompts/generate", {
      method: "POST",
      body: JSON.stringify({
        product,
        commonLock,
        compiler: compactCompilerProfile(),
        template: compactTemplate(template),
        referenceMap,
        referenceConsistency: state.referenceConsistency,
        images,
      }),
    });
    applyAiGeneration(result, product, commonLock, template);
    toast(`AI 已按当前新品从零生成 ${product.count} 条提示词 · ${usageLabel(result.usage)}`);
    if (window.innerWidth <= 900) elements.outputContent.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    state.generationError = error.message || "AI 新品生成失败，请重试。";
    elements.outputSummary.textContent = state.prompts.length
      ? `本次 AI 生成失败，已保留上一次成功结果：${state.generationError}`
      : `AI 生成失败：${state.generationError}`;
    toast(state.generationError, "error");
  } finally {
    if (progressTimer) window.clearInterval(progressTimer);
    state.aiBusy = false;
    updateAnalyzeButton();
    updateGenerateButton();
    updateOptimizeButton();
  }
}

function applyAiOptimization(result) {
  const optimized = Array.isArray(result?.prompts) ? result.prompts : [];
  if (optimized.length !== state.localPrompts.length) throw new Error("模型没有返回完整的提示词集合，已保留本地版本。");
  const byIndex = new Map(optimized.map((item) => [Number(item.index), String(item.prompt || "").trim()]));
  if (byIndex.size !== state.localPrompts.length || [...byIndex.values()].some((prompt) => !prompt)) {
    throw new Error("模型返回的提示词索引不完整，已保留本地版本。");
  }
  state.prompts = state.localPrompts.map((item, index) => {
    const prompt = byIndex.get(index);
    return { ...item, prompt, directPrompt: buildDirectPrompt(item, state.product, prompt, item.scene) };
  });
  state.optimization = {
    model: clean(result.model) || state.aiConfig.model,
    usage: result.usage && typeof result.usage === "object" ? result.usage : {},
    notes: Array.isArray(result.notes) ? result.notes.map(clean).filter(Boolean).slice(0, 3) : [],
  };
  state.optimizationError = "";
  state.packText = buildPackText(state.product, state.commonLock, state.prompts, state.repairs, state.template, state.optimization, state.generation);
  state.directPackText = buildDirectPackText(state.product, state.prompts, state.optimization, state.generation);
  renderPrompts(state.prompts);
  renderQc(buildQc(state.product, state.template, state.prompts));
  renderFidelityReport(result.fidelityReport || state.fidelityReport);
  elements.outputSummary.textContent = `${state.product.name} · ${state.prompts.length} 条 · AI 从零生成 + 二次精修 / ${isFidelityMode(state.product) ? "高还原8镜头" : "精简稳定"} / ${state.template.profile.name} · ${state.product.duration} 秒 · ${state.product.ratio}`;
  updateOptimizeButton();
  saveHistorySnapshot("optimized");
}

async function optimizePromptsWithAi() {
  if (!state.localPrompts.length || !state.product || !state.aiConfig.hasApiKey || state.aiBusy) return;
  if (isInsecureRemoteEndpoint() && !window.confirm("当前模型节点使用明文 HTTP。继续后，API Key、商品档案和提示词文本会通过未加密连接发送；不会重复上传商品图片。确认继续优化吗？")) return;

  state.aiBusy = true;
  state.optimizationError = "";
  updateAnalyzeButton();
  updateGenerateButton();
  updateOptimizeButton();
  const original = elements.optimizePromptsButton.innerHTML;
  elements.optimizePromptsButton.innerHTML = "<span>AI优化中</span><b>正在消耗 Token</b>";
  elements.aiOptimizeState.textContent = `正在使用 ${state.aiConfig.model || "当前模型"} 精修 ${state.localPrompts.length} 条提示词`;
  elements.aiOptimizeDetail.textContent = "上一次 AI 生成版本会保留到完整结果返回；失败或返回不完整时不会覆盖。";
  elements.aiOptimizeUsage.textContent = "本次调用中";
  elements.aiOptimizeUsage.dataset.state = "busy";

  try {
    const referenceMap = referenceAuthorityMap().map((item) => ({
      placeholder: item.placeholder,
      role: item.label,
      authority: item.authority,
    }));
    const prompts = state.localPrompts.map((item, index) => ({
      index,
      key: item.key,
      title: item.title,
      risk: item.risk,
      prompt: item.prompt,
    }));
    const result = await requestJson("/api/fashion-prompts/optimize", {
      method: "POST",
      body: JSON.stringify({
        product: state.product,
        commonLock: state.commonLock,
        compiler: compactCompilerProfile(),
        template: compactTemplate(state.template),
        referenceMap,
        referenceConsistency: state.referenceConsistency,
        prompts,
      }),
    });
    applyAiOptimization(result);
    toast(`AI 精修完成 · ${usageLabel(result.usage)}`);
  } catch (error) {
    state.optimizationError = error.message || "请稍后重试，或继续使用现有版本。";
    elements.aiOptimizeState.textContent = "AI 优化失败，已保留上一次 AI 生成结果";
    elements.aiOptimizeDetail.textContent = state.optimizationError;
    elements.aiOptimizeUsage.textContent = "未覆盖本地版本";
    elements.aiOptimizeUsage.dataset.state = "error";
    toast(error.message || "AI 优化失败。", "error");
  } finally {
    state.aiBusy = false;
    elements.optimizePromptsButton.innerHTML = original;
    updateAnalyzeButton();
    updateGenerateButton();
    updateOptimizeButton();
  }
}

async function copyText(text, successMessage) {
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const helper = document.createElement("textarea");
      helper.value = text;
      helper.setAttribute("readonly", "");
      helper.style.position = "fixed";
      helper.style.opacity = "0";
      document.body.append(helper);
      helper.select();
      const copied = document.execCommand("copy");
      helper.remove();
      if (!copied) throw new Error("copy failed");
    }
    toast(successMessage);
  } catch {
    toast("浏览器未允许自动复制，请展开提示词后手动选择文本。", "error");
  }
}

function safeFilename(value) {
  return clean(value).replace(/[\\/:*?"<>|]/g, "_").slice(0, 70) || "商品";
}

function downloadPack() {
  if (!state.packText) return;
  const blob = new Blob(["\ufeff", state.packText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${safeFilename(elements.productName.value)}_Seedance提示词合集_${state.optimization ? "AI二次精修版" : "AI生成版"}.txt`;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast("UTF-8 TXT 已下载。");
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  generatePack();
});

elements.form.addEventListener("input", (event) => {
  if (elements.productName.value.trim()) {
    elements.productName.setAttribute("aria-invalid", "false");
    elements.productNameError.hidden = true;
  }
  if (event.target.matches("[data-category-detail]")) captureCategoryDetails();
  renderTemplatePanel();
  renderPromptModeNote();
  saveForm();
});

elements.form.addEventListener("change", (event) => {
  if (event.target === elements.category) {
    renderCategoryFields();
    invalidateReferenceConsistency();
  }
  if (event.target === elements.platformPreset) {
    applyPlatformPreset();
    return;
  }
  if ([elements.ratio, elements.duration].includes(event.target) && elements.platformPreset.value !== "custom") {
    elements.platformPreset.value = "custom";
    renderPlatformPreset({ applySettings: false });
  }
  renderTemplatePanel();
  renderPromptModeNote();
  saveForm();
});

elements.uploadButton.addEventListener("click", () => elements.referenceInput.click());
elements.referenceInput.addEventListener("change", () => {
  addReferenceFiles(elements.referenceInput.files || []);
  elements.referenceInput.value = "";
});

["dragenter", "dragover"].forEach((eventName) => {
  elements.uploadButton.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.uploadButton.classList.add("is-dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  elements.uploadButton.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.uploadButton.classList.remove("is-dragging");
  });
});

elements.uploadButton.addEventListener("drop", (event) => addReferenceFiles(event.dataTransfer?.files || []));

elements.referenceGrid.addEventListener("change", (event) => {
  const select = event.target.closest("[data-reference-role]");
  if (!select) return;
  const card = select.closest("[data-reference-id]");
  const reference = state.references.find((item) => item.id === card?.dataset.referenceId);
  if (reference) {
    reference.role = select.value;
    invalidateReferenceConsistency();
    discardAiReview({ message: false });
  }
});

elements.referenceGrid.addEventListener("click", (event) => {
  const button = event.target.closest("[data-remove-reference]");
  if (!button) return;
  const card = button.closest("[data-reference-id]");
  if (card) removeReference(card.dataset.referenceId);
});

elements.promptList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-prompt-index]");
  if (!button) return;
  event.preventDefault();
  event.stopPropagation();
  const prompt = state.prompts[Number(button.dataset.promptIndex)];
  if (!prompt) return;
  const direct = button.dataset.promptVariant !== "full";
  const directName = isFidelityMode(state.product || {}) ? "高还原 Seedance 版" : "精简稳定版";
  copyText(direct ? (prompt.directPrompt || prompt.prompt) : prompt.prompt, `已复制${direct ? directName : "检查完整版"}：${prompt.title}`);
});

document.addEventListener("click", (event) => {
  const button = event.target.closest('[data-copy-target="common-lock"]');
  if (button) copyText(elements.commonLock.textContent, "公共商品锁已复制。");
});

elements.versionHistoryList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-history-restore]");
  if (button) restoreHistoryVersion(button.dataset.historyRestore);
});

elements.historyCompareButton.addEventListener("click", compareHistoryVersions);

elements.copyDirectAllButton.addEventListener("click", () => copyText(state.directPackText, "Seedance 直贴版提示词包已复制。"));
elements.copyAllButton.addEventListener("click", () => copyText(state.packText, "双版本完整合集已复制。"));
elements.downloadButton.addEventListener("click", downloadPack);
elements.loadDemoButton.addEventListener("click", () => loadDemo({ generate: true }));
elements.resetProductButton.addEventListener("click", resetProduct);
elements.emptyDemoButton.addEventListener("click", () => loadDemo({ generate: true }));
elements.aiBaseUrl.addEventListener("input", renderEndpointWarning);
elements.aiBaseUrl.addEventListener("input", invalidateAiConfigTestResult);
elements.aiModel.addEventListener("input", invalidateAiConfigTestResult);
elements.aiApiKey.addEventListener("input", invalidateAiConfigTestResult);
elements.saveAiConfigButton.addEventListener("click", saveAiConfig);
elements.testAiConfigButton.addEventListener("click", testAiConfig);
elements.analyzeProductButton.addEventListener("click", analyzeProductWithAi);
elements.applyAiReviewButton.addEventListener("click", applySelectedAiAnalysis);
elements.discardAiReviewButton.addEventListener("click", () => discardAiReview({ message: true }));
elements.optimizePromptsButton.addEventListener("click", optimizePromptsWithAi);

restoreForm();
renderTemplatePanel();
renderPromptModeNote();
renderCategoryFields({ preserve: false });
renderPlatformPreset({ applySettings: false });
renderReferences();
renderReferenceConsistency();
renderFidelityReport();
loadHistoryVersions();
loadAiConfig();

window.FashionPromptWorkbench = {
  buildTimeline,
  buildDenseTimeline,
  denseShotPlan,
  buildCommonLock,
  buildRepairs,
  buildDirectPrompt,
  directPromptQuality,
  expectedDirectShotCount,
  isFidelityMode,
  compactDirectReference,
  promptSection,
  referenceCoverage,
  inferGarmentProfile,
  detailFocusForProduct,
  resolvePromptTemplate,
  roleForTemplate,
  collectProduct,
  renderCategoryFields,
  applyPlatformPreset,
  referenceFingerprint,
  ensureReferenceConsistency,
  renderReferenceConsistency,
  renderFidelityReport,
  saveHistorySnapshot,
  compareHistoryVersions,
  restoreHistoryVersion,
  generatePack,
  stageAiAnalysis,
  applyAiAnalysis,
  applyAiOptimization,
  isInsecureRemoteEndpoint,
};
