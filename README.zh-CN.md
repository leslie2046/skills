# Codex Skills

[English](README.md)

这个仓库用于存放给 Codex 和其他 agent 式编程助手使用的 skills。
当前包含的 skill 是 `gpt-image-2-generator`，它可以帮助 agent 将图片需求整理成结构化提示词，并通过 Azure OpenAI `gpt-image-2` 部署生成或编辑图片。

## 可用 Skill

| Skill | 用途 |
| --- | --- |
| `gpt-image-2-generator` | 使用 Azure OpenAI `gpt-image-2` 生成或编辑图片，包含提示词整理、参数选择、dry run 校验和本地输出保存。 |

## 目录结构

```text
.
+-- gpt-image-2-generator/
|   +-- SKILL.md
|   +-- agents/
|   |   +-- openai.yaml
|   +-- references/
|   |   +-- gpt-image-2.md
|   +-- scripts/
|       +-- generate_image.py
+-- LICENSE
+-- README.md
+-- README.zh-CN.md
```

## 在 Codex 中使用

将 skill 目录复制或链接到你的 Codex skills 目录。常见位置是 `$CODEX_HOME/skills`，Windows 上通常也可以使用 `%USERPROFILE%\.codex\skills`：

```powershell
Copy-Item -Recurse .\gpt-image-2-generator $env:USERPROFILE\.codex\skills\
```

之后可以在 Codex 中按名称调用：

```text
Use $gpt-image-2-generator to generate a product image for a matte black desk lamp.
```

Codex 会读取 `gpt-image-2-generator/SKILL.md`，整理 visual brief，选择合适的 `gpt-image-2` 参数，并在需要实际请求 Azure 时运行辅助脚本。

## Azure 配置

发起真实 API 调用前，需要先在本地配置凭据：

```powershell
$env:AZURE_OPENAI_API_KEY = "<your-api-key>"
$env:AZURE_OPENAI_ENDPOINT = "https://<resource-name>.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-image-2"
```

也可以直接提供完整部署根路径：

```powershell
$env:AZURE_OPENAI_ENDPOINT_ROOT = "https://<resource-name>.openai.azure.com/openai/deployments/gpt-image-2"
```

可选配置：

```powershell
$env:AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
```

不要把真实 Azure endpoint、deployment name 或 API key 提交到仓库。

## 辅助脚本

辅助脚本只依赖 Python 标准库，支持图片生成和图片编辑。

生成图片：

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py generate `
  --prompt "Photoreal product shot of a ceramic mug on a clean studio background" `
  --output .\outputs\mug.png
```

编辑图片：

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py edit `
  --image .\input.png `
  --mask .\mask.png `
  --prompt "Make the object black and white while preserving the background" `
  --output .\outputs\edited.png
```

只校验请求、不实际调用 Azure：

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py generate `
  --endpoint-root "https://example.openai.azure.com/openai/deployments/gpt-image-2" `
  --prompt "Minimal poster for a robotics workshop" `
  --output .\outputs\poster.jpeg `
  --format jpeg `
  --quality medium `
  --dry-run
```

默认参数：

| 参数 | 默认值 |
| --- | --- |
| `size` | `1024x1024` |
| `quality` | `low` |
| `background` | `auto` |
| `format` | `png` |
| `n` | `1` |

脚本会拒绝 `gpt-image-2` 不支持的透明背景，并在发送请求前校验图片尺寸约束。

## Skill 文件说明

- `SKILL.md` 定义 agent 什么时候应该使用该 skill，以及推荐工作流。
- `scripts/generate_image.py` 负责调用 Azure OpenAI Images API。
- `references/gpt-image-2.md` 记录 endpoint、参数约束和图片编辑细节，供 agent 在需要精确行为时查阅。
- `agents/openai.yaml` 提供 OpenAI agent surface 使用的展示元数据。

## 生成文件

生成的图片通常应保存到 `outputs/`。该目录已被 Git 忽略，避免本地生成结果被误提交。

## 许可证

本项目使用 Apache License 2.0。详情见 [LICENSE](LICENSE)。
