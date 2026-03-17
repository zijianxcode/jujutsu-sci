# 咒术SCI高专

咒术SCI高专是一个由本地学术资料自动生成的静态网站项目。

它的核心目标是把论文总结、研究主题、成员进展和归档记录整理成清晰的网页入口，方便本地维护，也方便后续发布到 GitHub Pages 等静态平台。

## 文档导航

如果你是第一次接手这个项目，建议按这个顺序看：
- [项目结构](docs/PROJECT_STRUCTURE.md)
- [内容同步说明](docs/CONTENT_SYNC.md)
- [部署发布说明](docs/DEPLOYMENT.md)

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

执行后会自动刷新首页、主题页、成员页和归档页。

## 当前核心文件

- `sync_from_source.py`：整站内容同步与生成入口
- `site.css`：全站样式
- `site-index.js`：首页脚本
- `site-detail.js`：详情页脚本
- `index.html`：网站首页

## 当前仓库状态

这个项目已经：
- 初始化 Git 仓库
- 推送到 GitHub 公开仓库
- 适合继续接入 GitHub Pages 做静态部署
