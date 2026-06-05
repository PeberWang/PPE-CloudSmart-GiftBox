# third_party/

此目录用于存放**无法通过 pip 安装的第三方源码**（例如：未发布到 PyPI 的 fork 版本、需要本地修改的内部库等）。

## 使用规则

- **铁律：禁止修改此目录内任何代码**
- 如需定制第三方库功能，在 `libs/` 层封装，不要改 third_party/
- 替换第三方库时，只修改 `libs/` 的适配层，上层零影响

## 当前状态

**本项目所有依赖均通过 pip 安装**（见 `requirements.txt`），本目录暂时为空。

| 优先级 | 安装方式 |
|--------|---------|
| 首选   | `pip install <package>` |
| 兜底   | 将源码放入此目录 |

## 已安装的核心依赖

| 依赖 | 用途 |
|------|------|
| `lark-oapi` | 飞书官方 Python SDK（wiki、bitable、docx、drive、perm） |
| `openai` | LLM 调用（智谱 GLM，兼容 OpenAI 格式） |
| `pydantic-settings` | 配置管理（.env 自动读取 + 类型校验） |
| `tenacity` | 重试逻辑 |
| `jinja2` | LLM 提示词模板渲染 |
| `typer` | CLI 入口 |
