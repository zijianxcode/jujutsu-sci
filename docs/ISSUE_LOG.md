# 问题记录与修复日志

## 2026-03-23：定时任务存在，但学术站与 `academy/` 仍然停在 2026-03-20

### 问题现象

- 源目录已经更新到 `2026-03-23`
- 本地生成站与线上 `academy/` 仍显示 `2026-03-20 21:00`
- 用户误以为“已经配置了每日同步，所以应该自动变新”

### 根因判断

这次不同步不是单点问题，而是三层叠加：

1. 每日定时任务确实存在，但执行失败  
   `daily-sci-sync` 自动化已创建并处于 `ACTIVE`，但 2026-03-20 与 2026-03-22 两次运行都在第一步 `git pull --ff-only origin main` 失败，原因是 `Could not resolve host: github.com`。因此后续 `sync_from_source.py`、提交、推送都没有发生。
2. 定时脚本只覆盖了 `jujutsu-sci` 仓库  
   [auto_sync_site.sh](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web/auto_sync_site.sh) 只会：
   - `git pull`
   - `python3 sync_from_source.py`
   - 提交并推送 HTML 到 `jujutsu-sci`
   
   它并不会把内容镜像到 `personal-homepage/academy/`。
3. `academy/` 当前生产链路是 GitHub Pages，而不是 CloudBase 直接出内容  
   2026-03-23 核查结果显示：
   - `bananabox.plus` 的 Pages 配置为 `main /`
   - `https://bananabox.plus/academy/` 响应头 `server: GitHub.com`
   
   这说明当前 `academy/` 想变新，必须：
   - 先同步 `personal-homepage` 仓库里的 `academy/`
   - 再等待 GitHub Pages 构建完成
   
   仅仅跑 `jujutsu-sci` 定时任务，或者仅做 CloudBase 发布，都不足以保证 `academy/` 变新。

### 修复动作

1. 在 [学术小龙虾-web](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web) 重新执行 `python3 sync_from_source.py`
2. 将最新生成内容提交并推送到 [zijianxcode/jujutsu-sci](https://github.com/zijianxcode/jujutsu-sci)，提交 `09872a5`
3. 将最新静态页面同步到 `personal-homepage/academy/`
4. 推送 [zijianxcode/personal-homepage](https://github.com/zijianxcode/personal-homepage) 的 `academy` 更新，提交 `c0eaa10`
5. 等待 GitHub Pages 构建成功后复核 [https://bananabox.plus/academy/](https://bananabox.plus/academy/)

### 验证结果

- `https://zijianxcode.github.io/jujutsu-sci/` 已更新为：
  - `论文总结 63`
  - `成员记录 162`
  - `最新时间 2026-03-23 09:07`
- `https://bananabox.plus/academy/` 已更新为：
  - `论文总结 63`
  - `成员记录 162`
  - `最新时间 2026-03-23 09:07`
- `academy` 首页包含：
  - `高星论文`
  - `周会讨论`
  - `每日评审`

### 预防措施

- 以后不要把“定时任务存在”视为“内容一定已上线”，必须检查执行结果和失败日志
- `jujutsu-sci` 自动任务只代表学术站源码仓库同步，不代表 `academy/` 已同步
- 只要目标是 `bananabox.plus/academy/`，发布检查必须覆盖：
  - `personal-homepage/academy/` 是否已更新
  - GitHub Pages 构建是否成功
  - 线上页面是否已返回最新时间
- 如果继续保留 CloudBase，也只能把它视为并行发布目标，不能默认等同于当前 `academy` 生产源
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
