# Codex Skills

[Chinese](README.zh-CN.md)

This repository contains skills for Codex and other agent-style coding assistants.
The current skill is `gpt-image-2-generator`, which helps an agent turn image
requests into structured prompts and call an Azure OpenAI `gpt-image-2`
deployment for image generation or editing.

## Available Skills

| Skill | Purpose |
| --- | --- |
| `gpt-image-2-generator` | Generate or edit images with Azure OpenAI `gpt-image-2`, including prompt shaping, parameter selection, dry runs, and local output handling. |

## Repository Layout

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

## Use With Codex

Copy or link the skill directory into your Codex skills directory, commonly
`$CODEX_HOME/skills` or `%USERPROFILE%\.codex\skills` on Windows:

```powershell
Copy-Item -Recurse .\gpt-image-2-generator $env:USERPROFILE\.codex\skills\
```

Then ask Codex to use the skill by name:

```text
Use $gpt-image-2-generator to generate a product image for a matte black desk lamp.
```

Codex will read `gpt-image-2-generator/SKILL.md`, build a visual brief, choose
reasonable `gpt-image-2` parameters, and run the helper script when a live Azure
call is needed.

## Azure Configuration

Configure credentials locally before making live API calls:

```powershell
$env:AZURE_OPENAI_API_KEY = "<your-api-key>"
$env:AZURE_OPENAI_ENDPOINT = "https://<resource-name>.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-image-2"
```

Alternatively, provide the full deployment root:

```powershell
$env:AZURE_OPENAI_ENDPOINT_ROOT = "https://<resource-name>.openai.azure.com/openai/deployments/gpt-image-2"
```

Optional:

```powershell
$env:AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
```

Do not commit real Azure endpoints, deployment names, or API keys.

## Helper Script

The helper script uses only the Python standard library and supports both image
generation and image editing.

Generate an image:

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py generate `
  --prompt "Photoreal product shot of a ceramic mug on a clean studio background" `
  --output .\outputs\mug.png
```

Edit an image:

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py edit `
  --image .\input.png `
  --mask .\mask.png `
  --prompt "Make the object black and white while preserving the background" `
  --output .\outputs\edited.png
```

Validate a request without calling Azure:

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py generate `
  --endpoint-root "https://example.openai.azure.com/openai/deployments/gpt-image-2" `
  --prompt "Minimal poster for a robotics workshop" `
  --output .\outputs\poster.jpeg `
  --format jpeg `
  --quality medium `
  --dry-run
```

Default parameters:

| Parameter | Default |
| --- | --- |
| `size` | `1024x1024` |
| `quality` | `low` |
| `background` | `auto` |
| `format` | `png` |
| `n` | `1` |

The script rejects unsupported transparent backgrounds for `gpt-image-2` and
validates image size constraints before sending requests.

## Skill Files

- `SKILL.md` defines when the agent should use the skill and the recommended
  workflow.
- `scripts/generate_image.py` performs the Azure OpenAI Images API calls.
- `references/gpt-image-2.md` contains endpoint details, parameter constraints,
  and editing guidance for the agent to consult when exact behavior matters.
- `agents/openai.yaml` provides display metadata for OpenAI agent surfaces.

## Generated Files

Generated images should usually be written under `outputs/`. That directory is
ignored by Git so local results do not get committed accidentally.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
