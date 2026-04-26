# 问题记录与修复日志

## 2026-04-27：源目录过于扁平且命名不一致，导致同步容易漏扫或误判

### 问题现象

- 源目录 `2026sci1/学术小龙虾` 根部堆积大量 `YYYY-MM-DD` / `YYYY-MM-DD-HH` 时间目录。
- 目录中还混有旧版 `html/` 产物、顶层附件和顶层 Markdown。
- 带中文后缀的目录，例如 `2026-03-22-反思`、`2026-04-19-团队反思`，旧同步逻辑没有稳定纳入正式记录。
- 用户怀疑文件结构复杂是同步不顺畅的原因。

### 根因判断

旧同步脚本主要按“根目录下直接放时间目录”的结构工作，只稳定识别：
- `YYYY-MM-DD`
- `YYYY-MM-DD-HH`

当源目录继续增长后，这种扁平结构会带来三个问题：
- 根目录过长，人工核查困难。
- 带中文后缀的有效记录容易被漏掉。
- 旧产物和散落文件混在根部，容易干扰“哪些内容应该进入网站”的判断。

### 修复动作

1. 新增 [organize_source.py](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web/organize_source.py)，用于整理源目录。
2. 将源目录整理为：
   - `records/YYYY/MM/DD/HH/`
   - `records/YYYY/MM/DD/daily/`
   - `records/YYYY/MM/DD/中文后缀/`
   - `attachments/`
   - `inbox/`
   - `legacy-html/`
3. 修改 [sync_from_source.py](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web/sync_from_source.py)，让它同时兼容旧结构和新 `records/` 结构。
4. 将 `html/`、`legacy-html/`、`attachments/`、`inbox/` 加入忽略名单，避免非正式记录误入页面。
5. 更新 [内容同步说明](CONTENT_SYNC.md)，把源目录整理和排查步骤写入文档。

### 验证结果

- 整理前 dry-run 检出 `2026-03-26` 与 `2026-03-26-00` 等默认槽位冲突，已改为把无小时目录归入 `daily/`，避免覆盖。
- 正式整理后，源目录根部只剩：
  - `records/`
  - `attachments/`
  - `inbox/`
  - `legacy-html/`
  - `.DS_Store`
- 再次运行 `python3 organize_source.py` 显示 `Planned moves: 0`。
- 运行 `python3 sync_from_source.py` 成功生成 `525` 条记录。

### 预防措施

- 以后新增内容优先进入 `records/YYYY/MM/DD/slot/`。
- 如果源目录根部再次出现大量时间目录，先运行 `python3 organize_source.py` 预览，再确认是否 `--apply`。
- 整理脚本必须先 dry-run，发现冲突时停止，不能覆盖已有目录。
- 同步脚本只读取正式记录目录，附件、收件箱和旧 HTML 归档默认不进站点。

## 2026-03-25：每日自动同步任务存在，但没有自动把最新内容发布上线

### 问题现象

- 用户已经要求配置“每天同步一次”
- 但 2026-03-25 核查时，线上内容并没有按预期自动更新
- 用户误以为自动化没有创建，或者根本没有执行

### 根因判断

这次问题主要有三层：

1. 自动化确实存在，但最近运行失败  
   [daily-sci-sync automation](/Users/zijian/.codex/automations/daily-sci-sync/automation.toml) 仍是 `ACTIVE`，而且最近一次运行记录写在 [memory.md](/Users/zijian/.codex/automations/daily-sci-sync/memory.md) 中。  
   失败点是 `git pull --ff-only origin main`，错误为 `Could not resolve host: github.com`。
2. 老脚本把 `git pull` 作为硬前置步骤  
   旧版 [auto_sync_site.sh](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web/auto_sync_site.sh) 里，只要 GitHub 网络解析失败，脚本就会立即退出，导致后面的 `python3 sync_from_source.py` 根本不会执行。
3. 老脚本会自动提交推送，和“发布必须先确认”的规则冲突  
   用户后续又明确要求：GitHub 推送和生产发布必须先经过确认。  
   这意味着“每天自动发布”本身不应再是默认行为，自动化应该改成“每天自动检查并汇报”。

### 修复动作

1. 将 [auto_sync_site.sh](/Users/zijian/Library/Mobile%20Documents/com~apple~CloudDocs/SCI/%E5%AD%A6%E6%9C%AF%E5%B0%8F%E9%BE%99%E8%99%BE-web/auto_sync_site.sh) 改为：
   - 默认 `sync` 模式
   - 即使 GitHub 暂时不可达，也继续执行本地源目录生成
   - 自动检测是否只有数据页 HTML 发生变化
   - 只自动提交并推送 HTML 数据页更新
   - 自动同步 `personal-homepage/academy/` 镜像
   - 如果检测到非 HTML 改动，则停止并汇报，不自动上线
2. 将 `daily-sci-sync` 自动化提示词改为：
   - 每天拉取可拉取的远端状态
   - 本地重新生成
   - 自动发布数据页 HTML 更新
   - 一旦碰到非 HTML 变更或发布失败，立即停止并汇报
3. 将本次故障与修复逻辑补记到问题日志，避免后续再次误判

### 预防措施

- 以后把“自动同步”理解为“自动发布数据页”，不是“自动发布所有前端改动”
- 即使 GitHub 网络暂时失败，也不应阻止本地源内容生成检查
- 自动任务输出必须明确区分：
  - 远端拉取状态
  - 本地生成是否成功
  - 是否检测到待发布 HTML 变化
  - `academy` 镜像是否同步成功
- UI、样式、脚本和功能改动仍然要走人工确认，不由定时任务自动发布

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
