# 部署发布说明

## 当前状态

项目已经推送到 GitHub 仓库：
[zijianxcode/jujutsu-sci](https://github.com/zijianxcode/jujutsu-sci)

## 当前适合的发布方式

这是一个纯静态项目，最适合以下平台：
- GitHub Pages
- Vercel
- Netlify

## GitHub Pages 推荐方式

如果要用 GitHub Pages，最直接的方式是：
1. 打开 GitHub 仓库设置
2. 进入 `Pages`
3. Source 选择 `Deploy from a branch`
4. Branch 选择 `main`
5. Folder 选择 `/ (root)`

因为当前首页入口就是根目录下的 `index.html`，所以不需要额外打包。

## 后续更新流程

如果网站内容有更新，推荐按这条流程走：
1. 在源目录中更新 Markdown 内容
2. 运行 `python3 sync_from_source.py`
3. 本地检查生成结果
4. 提交 Git 变更
5. 推送到 GitHub
6. 等待 Pages 自动更新

## 线上常见现象

GitHub Pages 更新后，可能出现这些“看起来像没更新”的情况：
- 页面还在构建，几分钟内还没刷新完成
- 浏览器命中了旧缓存
- 仓库已经更新，但站点还没完成部署

遇到这种情况，建议按这个顺序确认：
1. 先看仓库最新提交是否已经推到 `main`
2. 再看网页源码或生成产物是否已经包含新内容
3. 等待 Pages 刷新 1 到 5 分钟
4. 浏览器强制刷新一次

## 发布前建议

正式上线前，建议再补几项：
- 一个更完整的项目简介
- 一个对外可读的首页说明
- 仓库封面图或社交分享图
- 一个更稳定的 logo / favicon 方案

## 记录要求

以后凡是遇到部署延迟、线上页面未刷新、GitHub Pages 异常等问题，也统一记录到：
- [问题记录与修复日志](ISSUE_LOG.md)
