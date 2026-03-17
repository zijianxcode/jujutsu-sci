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

## 发布前建议

正式上线前，建议再补几项：
- 一个更完整的项目简介
- 一个对外可读的首页说明
- 仓库封面图或社交分享图
- 一个更稳定的 logo / favicon 方案
