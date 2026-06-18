# Codex Skills

[Chinese](README.zh-CN.md)

This repository contains skills for Codex and other agent-style coding assistants.
The current skill is `gpt-image-2-generator`, which helps an agent turn image
requests into structured prompts and call an OpenAI-compatible /v1 Images API
or Azure OpenAI `gpt-image-2` deployment for image generation or editing.

## Available Skills

| Skill | Purpose |
| --- | --- |
| `gpt-image-2-generator` | Generate or edit images with OpenAI-compatible /v1 or Azure OpenAI `gpt-image-2` APIs, including prompt shaping, provider fallback, parameter selection, dry runs, and local output handling. |

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
reasonable `gpt-image-2` parameters, and run the helper script when a live API
call is needed.

## Provider Configuration

By default, the helper script tries OpenAI-compatible /v1 first when
`OPENAI_API_KEY` is set. If that provider is not configured or the live request
fails, it falls back to Azure when Azure credentials and endpoint settings are
present.

Configure OpenAI-compatible credentials locally before making live API calls:

```powershell
$env:OPENAI_API_KEY = "<your-api-key>"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
$env:OPENAI_IMAGE_MODEL = "gpt-image-2"
```

`OPENAI_BASE_URL` and `OPENAI_IMAGE_MODEL` are optional. Set `OPENAI_BASE_URL`
to a custom `/v1` root for OpenAI-compatible gateways.

Configure Azure as the fallback provider:

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

Do not commit real endpoints, deployment names, model names, or API keys.

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

Validate an OpenAI-compatible request without calling the API:

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py generate `
  --provider openai `
  --base-url "https://api.example.test/v1" `
  --model "gpt-image-2" `
  --prompt "Minimal poster for a robotics workshop" `
  --output .\outputs\poster.jpeg `
  --format jpeg `
  --quality medium `
  --dry-run
```

Validate an Azure request without calling the API:

```powershell
python .\gpt-image-2-generator\scripts\generate_image.py generate `
  --provider azure `
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
- `scripts/generate_image.py` performs the OpenAI-compatible and Azure OpenAI
  Images API calls.
- `references/gpt-image-2.md` contains endpoint details, parameter constraints,
  and editing guidance for the agent to consult when exact behavior matters.
- `agents/openai.yaml` provides display metadata for OpenAI agent surfaces.

## Generated Files

Generated images should usually be written under `outputs/`. That directory is
ignored by Git so local results do not get committed accidentally.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
