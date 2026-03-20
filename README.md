# 咒术SCI高专

咒术SCI高专是一个由本地学术资料自动生成的静态网站项目。

它的核心目标是把论文总结、研究主题、成员进展和归档记录整理成清晰的网页入口，方便本地维护，也方便后续发布到 GitHub Pages 等静态平台。

## 文档导航

如果你是第一次接手这个项目，建议按这个顺序看：
- [项目结构](docs/PROJECT_STRUCTURE.md)
- [内容同步说明](docs/CONTENT_SYNC.md)
- [部署发布说明](docs/DEPLOYMENT.md)
- [问题记录与修复日志](docs/ISSUE_LOG.md)

## 项目概览

这个项目包含两部分：
- 源内容目录：存放原始 Markdown 记录
- 网页项目目录：存放生成后的 HTML、样式和同步脚本

当前网页项目目录：
`/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/学术小龙虾-web`

源内容目录：
`/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/2026sci1/学术小龙虾`

## 快速使用

当源目录有新内容时，在项目目录运行：

```bash
python3 sync_from_source.py
```

执行后会自动刷新首页、主题页、成员页、归档页和高星论文页。

## 同步发布规则

以后涉及站点更新时，必须按下面这条链路一起同步，不能只更新其中一段：

1. 本地项目同步：
   在 [学术小龙虾-web](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web) 运行 `python3 sync_from_source.py`，确认生成页已经更新。
2. GitHub 仓库同步：
   把本地生成结果提交并推送到 [zijianxcode/jujutsu-sci](https://github.com/zijianxcode/jujutsu-sci)。
3. CloudBase 子站同步：
   如果 `bananabox.plus/academy/` 也要反映这次更新，必须把最新静态产物同步到 `personal-homepage` 仓库的 `academy/` 子目录，并重新发布 CloudBase。

规则说明：
- `https://zijianxcode.github.io/jujutsu-sci/` 和 `https://bananabox.plus/academy/` 不是同一条自动发布链路。
- 推送 `jujutsu-sci` 成功，不代表 `bananabox.plus/academy/` 会自动更新。
- 只要 `academy/` 仍然是镜像子站，就必须把“本地 / GitHub / CloudBase”三段都走完。

## 当前核心文件

- `sync_from_source.py`：整站内容同步与生成入口
- `site.css`：全站样式
- `site-index.js`：首页脚本
- `site-detail.js`：详情页脚本
- `index.html`：网站首页

## 问题记录机制

从现在开始，项目里遇到的错误、bug、同步异常、部署异常，都统一记录到：
- [问题记录与修复日志](docs/ISSUE_LOG.md)

每条记录至少包含：
- 问题现象
- 影响范围
- 根因判断
- 修复动作
- 预防措施
- 验证结果

原则上，问题修复完成后再补文档，不把经验只留在聊天记录里。

## 当前仓库状态

这个项目已经：
- 初始化 Git 仓库
- 推送到 GitHub 公开仓库
- 适合继续接入 GitHub Pages 做静态部署
