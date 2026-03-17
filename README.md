# 学术小龙虾-web

这个目录是从源目录 `/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/2026sci1/学术小龙虾` 自动拉取内容生成的静态网页项目。

## 重新同步

```bash
python3 sync_from_source.py
```

生成规则：
- 只扫描源目录中的 Markdown 文件
- 忽略 `html/` 子目录
- 按时间目录倒序生成页面
- 成员页来自 `*-能力进化.md`
- 类型页来自 `论文总结.md`、`升级迭代.md`、`日会记录.md`、`团队讨论.md`
