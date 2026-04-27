# 版本历史

本文档记录 `jujutsu-sci` 的版本定位、更新说明和发包归档位置。

## v2.0.0 - Hermes 迁移与 IA 2.0

对应文件：
- `releases/packages/jujutsu-sci-v2.0.0.zip`
- Git 标签：`v2.0.0`

### 版本定位

v2.0.0 是当前学术站点的信息架构升级版本，重点是把 Hermes 采集链路、研究包入口、首页学术视图和详情页阅读体验整理成更稳定的发布基线。

### 主要更新

- 首页收敛为学术协作入口，突出论文追踪、研究方向、成员进展和高星论文。
- 详情页阅读体验升级，改进侧边导航、目录切换、搜索、Obsidian 导出和移动端阅读。
- 增加 IA 迭代和 Hermes 迁移文档，明确内容从采集到生成、发布、镜像的完整链路。
- 更新 `sync_from_source.py` 和测试，适配新的内容生成规则与页面结构。
- 补充 `docs/assets/` 下的页面截图，作为 IA 2.0 和详情页改版的视觉记录。

### 发包差异

相对 v1.0.0：
- 新增 12 个 `docs/assets/` 截图文件。
- 更新 22 个既有文件，覆盖页面产物、样式、详情页脚本、生成脚本、测试与 IA 文档。

### 发布说明

该版本已经适合直接作为静态站点发包留档。若发布到国内访问入口，需要继续按 `docs/DEPLOYMENT.md` 中的 CloudBase 子站链路执行：

`jujutsu-sci` 生成结果 -> `personal-homepage/academy/` 镜像 -> CloudBase 静态托管部署。

## v1.0.0 - GitHub 源同步基线

对应文件：
- `releases/packages/jujutsu-sci-v1.0.0.zip`
- Git 标签：`v1.0.0`

### 版本定位

v1.0.0 是从 GitHub 源同步后整理出的第一个可归档静态站点版本，用于保留早期页面结构、自动同步脚本和基础部署说明。

### 主要更新

- 固化静态页面结构，包括首页、论文、归档、主题、成员、讨论、升级迭代和高星论文。
- 保留 `auto_sync_site.sh`，记录学术站源码仓库与 `personal-homepage/academy/` 镜像之间的同步关系。
- 增加内容同步、部署发布、问题日志和项目结构文档，方便后续维护。
- 提供基础测试，覆盖源内容同步生成的关键行为。

### 发布说明

该版本可用于回滚到早期静态站点形态。由于后续国内访问依赖 CloudBase / `academy` 镜像链路，回滚时不能只替换 `jujutsu-sci`，还需要同步 `personal-homepage/academy/` 并重新发布。

## 校验信息

| 版本 | 文件 | SHA-256 |
| --- | --- | --- |
| v1.0.0 | `releases/packages/jujutsu-sci-v1.0.0.zip` | `0bd49d37b3bcad92b2f3a469dc3bbe8fdc71c1c33eef75e5cf3bc7de69397955` |
| v2.0.0 | `releases/packages/jujutsu-sci-v2.0.0.zip` | `b4988431f573f3cdcdc1e3e444eefc5ba7b8c1b921cc1106fffba23f33cbc1e7` |
