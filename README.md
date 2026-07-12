# modeskill

Modeskill 是 Modelab 的统一私有 Skill。v0.1 提供跨项目 UI 一致性模块、只读 Workspace 项目发现、Schema、模拟项目、报告验证框架，以及可选本机模块的安全加载机制。

## v0.1 能力边界

- 一个 Workspace root 可以包含多个项目，也可以是包含多个子项目的单一 Git 仓库。
- 自动发现与手动登记项目可以合并，参考项目始终只读。
- 当前项目发现只生成项目清单和基础信息，不是完整 UI 自动扫描器。
- v0.1 不会自动提取全部规范、监测漂移或修改真实项目。
- 自动提取、漂移检测和受控写入属于后续版本。

## 启动设置界面

```bash
python3 .agents/skills/modeskill/configurator/server.py
```

打开 [http://127.0.0.1:8765](http://127.0.0.1:8765)。页面默认使用简体中文，可在右上角切换 English；选择会保存在当前浏览器中。完成后回到启动命令的终端按 `Control+C` 停止服务。

本地服务只接受 `127.0.0.1` 或 `localhost`。浏览器发起的修改请求必须来自同一地址；没有 `Origin` 的请求仅允许来自本机回环地址，用于本地命令行或测试客户端。POST 请求只接受 1 MB 内的 JSON 对象。

操作顺序：

1. 输入 Workspace 名称和允许只读访问的根目录。
2. 设置扫描深度、识别文件、排除目录，必要时手动填写无 marker 项目的相对路径。
3. 点击“重新扫描项目”。
4. 选择主要参考项目、辅助参考项目和目标项目。
5. 验证并保存配置。

Workspace 配置只表达 Modeskill 规则上的读取范围，不会自动授予 Codex 或操作系统权限。参考项目永远只读；目标项目默认只读。“允许单次任务申请写入”只允许用户以后发起申请，不代表当前任务已经授权。

## 模块分发与本机备份

- **与 Git 仓库同步**：模块位于 `.agents/skills/modeskill/`，允许由 Git 跟踪，但设置界面不会自动 commit 或 push。
- **仅保留在本机**：模块位于 `.local/modules/`，由 `.gitignore` 排除，不会上传到 GitHub。

v0.1 只展示和管理已支持的固定策略，不支持自动迁移模块，也不能改变已有 Git 历史。`ui-consistency` 固定与仓库同步；可选的本机模块可在设置界面启用或停用。

本机路径允许使用内部符号链接，但解析后的真实目标必须仍位于对应的仓库、`.local`、模块或 Workspace 配置目录中；任何逃逸到外部的符号链接都会被拒绝。

Workspace 配置位于 `.local/workspaces/`，本机模块位于 `.local/modules/`。它们换电脑或重新 Clone 后不会自动恢复。删除本地 `modeskill` 目录前，请手动备份这两个目录。当前界面提供本机模块路径复制，不提供压缩导出。

## 调用可选本机模块

先在设置界面的“功能模块”区域确认模块已安装并启用，再在 Codex 中使用：

```text
使用 $modeskill，用大白话解释当前项目的技术逻辑。
使用 $modeskill，生成适合求职面试的三句话技术介绍。
```

根 Skill 会从自身真实路径向上定位当前仓库，再读取 `.local/modules/registry.json`。通过用户级软链接调用时也会解析到真实仓库。找不到仓库或模块时会明确提示，不会搜索整个用户目录。

## 验证

```bash
python3 .agents/skills/modeskill/shared/scripts/validate_config.py
python3 .agents/skills/modeskill/ui-consistency/scripts/validate_profile.py
python3 .agents/skills/modeskill/ui-consistency/scripts/validate_report.py
python3 scripts/validate_modeskill.py
python3 -m unittest discover -s tests
```

内置验证器只实现 v0.1 Schema 使用的 Draft 2020-12 关键字子集，并非完整 JSON Schema 实现。Schema 文件本身声明 Draft 2020-12。
