# 问题记录与修复日志

## 2026-03-20：GitHub 已更新，但 `bananabox.plus/academy/` 仍然是旧版

### 问题现象

- `jujutsu-sci` 仓库已经有最新提交
- `zijianxcode.github.io/jujutsu-sci/` 能看到新内容
- 但 [bananabox.plus/academy/](https://bananabox.plus/academy/) 仍然显示旧版首页
- 新增页面 `starred.html` 在 academy 子站上最初不可访问

### 影响范围

- `academy/` 子站不会自动跟随学术站源码仓库更新
- 用户容易误以为“GitHub 已更新 = 主站 academy 已更新”
- 首页入口、筛选标签、高星论文页等新功能会出现“GitHub 有、主站没有”的割裂

### 根因判断

根因不是页面生成失败，而是发布链路分成了两段：

1. 学术站源码仓库：
   [zijianxcode/jujutsu-sci](https://github.com/zijianxcode/jujutsu-sci)
2. 个人主页生产站：
   [bananabox.plus/academy/](https://bananabox.plus/academy/)

`academy/` 实际读取的是 `personal-homepage` 仓库中的 `academy/` 镜像目录，并且最终由 CloudBase 发布。  
所以只推 `jujutsu-sci`，不会自动让 `academy/` 变新。

另外，CloudBase CLI 初次发布时还踩到一个配置问题：
- `cloudbaserc.json` 使用了占位符 `{{env.TCB_ENV_ID}}`
- 直接发布会报错：`Env {{env.TCB_ENV_ID}} not exist in your account`
- 需要显式传入真实环境 `homepage-1gthisc4771d43ac`

### 修复动作

1. 先把最新学术站提交推到 `jujutsu-sci`
2. 再把 [学术小龙虾-web](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web) 同步覆盖到 `personal-homepage` 的 `academy/` 子目录
3. 把 `personal-homepage` 的更新提交并推到远端
4. 使用真实环境变量执行 CloudBase 发布：

```bash
cd /tmp/personal-homepage-preview
rm -rf .cloudbase-deploy
mkdir -p .cloudbase-deploy
cp *.html CNAME .cloudbase-deploy/
cp -r Assets projects documents academy .cloudbase-deploy/
TCB_ENV_ID='homepage-1gthisc4771d43ac' \
  npm exec --yes --package @cloudbase/cli@2.12.2 -- \
  tcb hosting deploy .cloudbase-deploy .
```

### 预防措施

- 以后默认按“三段同步规则”执行：
  本地生成 -> GitHub 仓库 -> CloudBase 发布
- 只要目标地址包含 `bananabox.plus/academy/`，就必须检查 `personal-homepage/academy/` 是否已重新同步
- 以后发布 CloudBase 时，不依赖占位符环境名，直接显式传入真实 `TCB_ENV_ID`
- 每次发布前，先确认 `.cloudbase-deploy/academy/` 内已经包含最新文件，例如 `starred.html`

### 验证结果

- `academy/` 首页已出现 `高星论文`
- `academy/` 首页快捷筛选已变为 `周会讨论`、`每日评审`
- [https://bananabox.plus/academy/starred.html](https://bananabox.plus/academy/starred.html) 已可访问
