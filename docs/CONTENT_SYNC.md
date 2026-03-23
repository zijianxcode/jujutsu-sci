# 内容同步说明

## 同步入口

项目通过下面这条命令，从源目录重新拉取内容并重建页面：

```bash
python3 sync_from_source.py
```

## 同步来源

源目录路径：
`/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/2026sci1/学术小龙虾`

## 同步规则

脚本会：
- 扫描源目录中的 Markdown 文件
- 忽略 `html/` 子目录
- 读取时间目录并按倒序排序
- 优先解析正文中的真实时间信息，再回退到目录时间
- 自动生成首页、主题页、成员页、归档页和 `高星论文` 页

## 三段同步规则

以后只要这个学术站发生改动，默认按三段一起同步：

1. 本地生成：
   在 [学术小龙虾-web](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web) 运行 `python3 sync_from_source.py`。
2. GitHub 同步：
   把本地生成结果提交并推送到 [zijianxcode/jujutsu-sci](https://github.com/zijianxcode/jujutsu-sci)。
3. `academy` 发布同步：
   如果 [bananabox.plus/academy/](https://bananabox.plus/academy/) 也要保持一致，必须把最新静态产物同步到 `personal-homepage` 仓库的 `academy/` 子目录，并完成当前实际生产链路的发布。

补充说明：
- `jujutsu-sci` 是学术站源码仓库。
- `bananabox.plus/academy/` 读取的是 `personal-homepage` 仓库里的 `academy/` 镜像副本。
- 2026-03-23 核查结果显示，`bananabox.plus` 当前使用的是 GitHub Pages 自定义域名，Pages 配置为 `main /`。
- 所以“本地站已经更新”或“jujutsu-sci 已经更新”都不等于 `academy/` 一定更新。
- 默认允许先做本地同步、校验和预览，但 `GitHub 推送` 与 `CloudBase 发布` 都属于需要人工确认的步骤，未经确认不直接执行。
- 如果 CloudBase 仍保留为并行环境，也要单独同步，但不能把它当作 `academy/` 当前唯一生产源。

## 内容识别方式

系统根据文件名识别内容类型：
- `论文总结.md` -> 论文总结
- `升级迭代.md` -> 升级迭代
- `日会记录.md` -> 日会记录
- `团队讨论.md` -> 团队讨论
- `*-能力进化.md` -> 成员页内容

## 时间解析规则

当前同步逻辑会优先尝试识别正文中的这些时间字段：
- `生成时间`
- `更新时间`
- `记录时间`
- `整理时间`
- `时间`
- `日期 + 时间` 组合字段

如果正文里没有可靠时间，再回退到目录名时间，例如：
- `2026-03-18-20`
- `2026-03-18`

这样可以避免首页“最新时间”只跟着目录名走，和正文实际记录时间不一致。

## 主题页生成方式

研究主题页来自 `论文总结.md` 的自动归类，当前会整理出：
- AI
- NLP
- CV
- ML
- HCI
- UX

## 同步后的建议检查项

每次同步完成后，建议检查：
- 首页标题和导览是否正常
- 首页“最新时间”是否符合最新源文件
- 论文总结页是否按时间倒序
- 成员页是否正常刷新
- 研究主题分布与主题页是否一致
- 详情页目录、筛选和阅读区是否正常

## 问题排查流程

如果你发现“内容明明更新了，但网站没变”，按下面顺序排查：
1. 先确认源目录里是否真的有新文件或新时间字段
2. 运行 `python3 sync_from_source.py`
3. 检查生成结果里的 `index.html` 是否已经变化
4. 检查 Git 是否有待提交变更
5. 检查 `jujutsu-sci` 是否已经推到远端
6. 如果目标地址是 `bananabox.plus/academy/`，继续检查 `personal-homepage/academy/` 是否已同步
7. 检查 `personal-homepage` 的 GitHub Pages 构建是否成功
8. 如果 CloudBase 也需要跟进，再检查 CloudBase 是否重新发布
9. 最后再排查浏览器缓存或 CDN 缓存

## 记录要求

以后凡是出现同步异常、排序异常、时间错误、漏页面等问题，都要补记到：
- [问题记录与修复日志](ISSUE_LOG.md)
