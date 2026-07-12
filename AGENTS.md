# Modeskill Repository Rules

本仓库开发 Modelab 私有统一 Skill：`modeskill`。Skill 名和入口 `.agents/skills/modeskill/SKILL.md` 必须保持不变。

## 结构规则

- 所有 Modelab 自建能力在 `modeskill` 内部分模块维护，不得擅自拆成平级 Skill。
- v0.1 只实现 `ui-consistency`，不得为未来模块创建空目录或占位文件。
- `shared` 规则变化后必须检查所有已实现模块。
- `modules.json` 只登记与 Git 仓库同步的模块；本机模块注册和内容只能放在 `.local/modules`。
- 修改 Schema 时同步更新示例和测试；修改行为时更新 CHANGELOG。

## 当前仓库开发边界

- 只修改当前 `modeskill` 仓库根目录。
- 不读取或修改 `../modetools`、Easy、Trans 或其他真实 Modelab 项目。
- 测试真实工作区场景时只使用仓库示例和系统临时目录。
- 不安装依赖或用户级 Skill，不自动 stage、commit 或 push。
- 不提交真实凭据、密码、Token、Cookie、生产 `.env` 或 `.local` 配置。
- 不把本机模块专有说明、输出格式、示例或测试快照复制到受 Git 跟踪目录。

## 质量规则

- 一致性结论必须引用源文件证据，不把偶然值当成全局规范。
- reference 永远只读；target 默认只读。
- Workspace 配置、运行环境权限和当前任务授权必须分别检查。
