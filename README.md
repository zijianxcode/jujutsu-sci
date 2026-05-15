# 咒术SCI高专

一个由 AI Agent 驱动的学术研究协作系统。**让 Agent 像一位严谨的研究者一样工作**——不只搬运论文信息，而是理解、判断、验证和积累。

线上地址：[zijianxcode.github.io/jujutsu-sci](https://zijianxcode.github.io/jujutsu-sci/) · [bananabox.plus/academy](https://bananabox.plus/academy/)

## 这不是又一个论文管理工具

大多数论文工具解决的是"存在哪里"。这个系统解决的是"怎么读、怎么判断、怎么积累"。

| 传统工具 | 本系统 |
| --- | --- |
| 你手动导入论文元数据 | Agent 自己找、自己读、自己写结构化总结 |
| 标签和文件夹 | 六段式分析：研究什么 / 为什么 / 别人做了什么 / 作者怎么做的 / 发现了什么 / 价值与不足 |
| 引用是文本 | 引用自动溯源 arXiv / CrossRef 验证真实性 |
| 读完就归档 | 每轮调研自动沉淀方法论：有效数据库、关键词配方、搜索策略 |
| 一个人的工具 | 多角色协作：研究员 → 批判者 → 方法论专家 → 评审者 |

## 核心架构

```
采集层    Agent 每日自主检索、筛选、阅读、结构化总结
  ↓        回答："今天该读什么？这篇论文在说什么？"
验证层    引用溯源校验 + 论文结构完整性审查
  ↓        回答："引用的文献真实存在吗？总结写全了吗？"
发布层    源 Markdown → 静态站点生成 → 多端发布
           回答："研究成果如何被看到？"
```

## Agent 研究团队

项目模拟了一个学术团队的完整分工。每个 Agent 有独立的采集方向、判断标准和能力进化档案。

| Agent | 身份 | 学术分工 | 判断标准 |
| --- | --- | --- | --- |
| **悠仁** | 跨领域研究员 | 追踪 AI+X 交叉创新，发现跨域连接 | 跨域洞察力、连接密度、场景覆盖 |
| **野蔷薇** | 批判性研究者 | 发现方法盲点、检验假设、补充被忽视的视角 | 批判深度、替代解释质量、伦理敏感性 |
| **惠** | 方法论专家 | 提炼研究设计、评估方法严谨性、推进写作质量 | 方法适当性、可复现性、理论贡献清晰度 |
| **五条悟** | 首席评审者 | 方向判断、质量把关、资源分配、最终取舍 | 创新性 / 影响力 / 可操作性 / 跨域连接力 / 时间考验力 |
| **全栈工程师** | 工程实现者 | 评估系统可行性、工具链、工程落地路径 | 架构合理性、可部署性、成本效益 |

每个 Agent 的能力进化文档不是"今日工作记录"，而是一个持续成长的学术档案：**读过的论文**形成领域知识图谱，**打星和评分**反映判断力进化，**调研策略章节**沉淀可复用的方法论，**批判与反思**记录学术品味的形成过程。

研究闭环：`悠仁调研 → 野蔷薇批判分析 → 惠方法论整理 → 五条悟最终评审`

## 三项 Agent 能力

### 引用溯源校验

论文总结中的每一个 arXiv ID 和 DOI，都是读者追溯原始文献的唯一桥梁。失效的引用 = 研究链条断裂。

```bash
python3 verify_citations.py           # 扫描所有论文总结，生成验证报告
python3 verify_citations.py --fix     # 验证后自动在文档中追加验证状态
```

通过 arXiv API 和 CrossRef API 批量验证，确保每一篇总结的引用可追溯。

### 论文结构完整性审查

一篇合格的论文总结，应像一篇合格的投稿论文——结构完整、元数据齐全、评分有效。

```bash
python3 sync_from_source.py --check-quality   # 同步时附带完整性审查
python3 check_paper_quality.py --json          # 独立运行，JSON 输出
```

自动检查六段式完整性（模糊匹配，容忍编号变体）、元数据字段、评分有效性。**非阻塞**：有问题打印警告但不中断发布。

### 领域调研方法论沉淀

每一次检索中的发现——哪些数据库产出高、哪些关键词有效、哪些策略值得复用——如果不被记录，下次就得重新试错。Agent 在角色进化文档中追加 `## 领域调研策略` 章节，`sync_from_source.py` 自动提取并聚合到成员页面。把"这次怎么找到的"变成"下次可以怎么找"。

## 快速开始

```bash
# 同步源内容并生成站点
python3 sync_from_source.py

# 附带质量审查
python3 sync_from_source.py --check-quality

# 如果源目录出现散乱的顶层日期目录，先整理
python3 organize_source.py --preview
python3 organize_source.py --apply
```

源内容目录：`学术小龙虾/records/YYYY/MM/DD/slot/<paper-key>/论文总结.md`

### 文件地图

| 文件 | 用途 |
| --- | --- |
| `sync_from_source.py` | 站点生成入口（含完整性审查、策略提取） |
| `verify_citations.py` | 引用溯源校验 |
| `check_paper_quality.py` | 独立完整性检查 |
| `organize_source.py` | 源目录归档整理 |
| `site.css` / `site-index.js` / `site-detail.js` | 样式与交互 |
| `auto_sync_site.sh` | 自动同步 + 推送脚本 |
| `vendor/marked.min.js` / `vendor/purify.min.js` | Markdown 渲染 + XSS 防护 |

### 文档入口

[项目结构](docs/PROJECT_STRUCTURE.md) · [内容同步说明](docs/CONTENT_SYNC.md) · [Hermes 迁移说明](docs/HERMES_MIGRATION.md) · [采集规则](docs/COLLECTION_POLICY.md) · [部署发布](docs/DEPLOYMENT.md) · [版本历史](docs/VERSION_HISTORY.md) · [发包归档](releases/README.md) · [问题日志](docs/ISSUE_LOG.md)

建议新接触先看：项目结构 → 内容同步 → 部署发布

## 维护约定

**核心链路**：`源内容 → 本地生成 → GitHub 推送 → academy 镜像 → 线上验证`。任何一步没走完，都不算完成更新。

**三段同步**：① 本地 `sync_from_source.py` 生成 → ② 推送到 `jujutsu-sci` GitHub Pages → ③ 同步 `personal-homepage/academy/` 并部署 CloudBase。`jujutsu-sci` 更新不等于 `academy` 自动更新。

**源目录规范**：`records/` 是唯一同步入口；`attachments/`、`inbox/`、`legacy-html/` 不参与生成。Hermes 只写源 Markdown，不直接修改 HTML、不提交、不发布。

**其他约束**：页面按正文真实时间倒序，不手动调整顺序。角色链路（悠仁→野蔷薇→惠→五条悟）不可打乱。高星论文从角色能力进化文档自动抽取，不做手工清单。GitHub 推送与生产发布须确认后执行。

**问题记录**：所有异常统一记录到 [问题日志](docs/ISSUE_LOG.md)，写清现象、影响、根因、修复、预防、验证。不让经验留在聊天记录里。

## 当前状态

**v2.1.0** — Agent 研究能力升级版本。

已具备：5 Agent 自主采集 · 引用溯源校验 · 论文结构完整性审查 · 调研方法论自动沉淀 · 763+ 条记录 · GitHub Pages + CloudBase 多端发布

下一步：研究问题自动发现、跨论文主题聚类、Agent 间自动讨论触发
