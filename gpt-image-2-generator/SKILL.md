---
name: gpt-image-2-generator
description: Generate and edit images with OpenAI-compatible /v1 Images APIs or Azure OpenAI gpt-image-2 deployments from a visual brief or text requirements. Use when Codex needs to create one or more images, edit an image with or without a mask, adapt requests to OpenAI-compatible or Azure OpenAI Images APIs, choose image parameters such as size, quality, background, and output format, or run a local helper script with provider fallback.
---

# GPT Image 2 Generator

## Overview

Turn a loose image request into a structured visual brief, choose sane `gpt-image-2` settings, and generate or edit files through an OpenAI-compatible /v1 Images API first, falling back to Azure OpenAI when Azure is configured. Configure endpoints and credentials with environment variables so personal resource names and keys stay out of the repository.

## Quick Start

- Configure the preferred provider locally before live calls.
  - OpenAI-compatible first:
    - `OPENAI_API_KEY`
    - optional `OPENAI_BASE_URL` for a custom /v1-compatible endpoint
    - optional `OPENAI_IMAGE_MODEL` when not using `gpt-image-2`
  - Azure fallback:
    - `AZURE_OPENAI_API_KEY`
    - `AZURE_OPENAI_ENDPOINT` plus `AZURE_OPENAI_DEPLOYMENT`, or `AZURE_OPENAI_ENDPOINT_ROOT`
    - optional `AZURE_OPENAI_API_VERSION` when not using `2025-04-01-preview`
- Distill the user request into: subject, scene, composition, style, lighting, palette, aspect ratio, text-in-image, and output goal.
- Pick defaults unless the user already specified them:
  - Drafts: `quality=low`
  - Final assets: `quality=medium` or `quality=high`
  - Fast/smaller files: `format=jpeg`
  - Sharper lossless output: `format=png`
  - Leave `size=1024x1024` unless the user clearly wants portrait, landscape, 2K, 4K, or an exact canvas
- Do not request `background=transparent` for `gpt-image-2`.
- Run `scripts/generate_image.py generate` for prompt-only generation.
- Run `scripts/generate_image.py edit` to edit an image or apply a mask.
- Read `references/gpt-image-2.md` when you need the provider endpoint shapes, exact constraints, or edit/reference-image guidance.

## Workflow

### 1. Build the visual brief

- Capture the non-negotiables first: main subject, action, camera/framing, environment, typography, style, and forbidden elements.
- If the request is underspecified, infer reasonable defaults instead of blocking.
- If the user wants text in the image, include the exact text, placement, and tone.

### 2. Write the prompt

- Put the subject and scene in the first sentence.
- Keep hard constraints explicit and short.
- Prefer concrete visual language over abstract art-direction jargon.
- Use exclusions sparingly. Add them only when they prevent a likely failure mode.

### 3. Choose parameters

- `quality=low` for draft exploration or quick variants.
- `quality=medium` for most final-purpose images.
- `quality=high` only when the user needs maximum fidelity and latency/cost are acceptable.
- Default to square if aspect ratio is unspecified.
- Prefer `jpeg` if latency matters. Prefer `png` if clean edges or lossless output matter.
- Use `n > 1` only when the user wants multiple variants.

### 4. Generate

Use the helper script for generation:

```bash
python scripts/generate_image.py generate --prompt "Photoreal product shot of a ceramic mug on a warm beige background" --output outputs/mug.png
```

Use the helper script for editing:

```bash
python scripts/generate_image.py edit --image image_to_edit.png --mask mask.png --prompt "Make this black and white" --output outputs/edited.png
```

For cautious runs, or when credentials may be missing, use:

```bash
python scripts/generate_image.py generate --prompt-file work/brief.txt --output outputs/poster.jpg --format jpeg --quality medium --dry-run
```

### 5. Iterate

- If composition is wrong, rewrite framing and placement language before raising quality.
- If fidelity is the only problem, keep the prompt and raise quality.
- If the model misses required text, shorten the text and make placement explicit.
- If the request is blocked for safety, restate it in neutral, non-targeting terms.

## Parameter Defaults

- `size=1024x1024`
- `quality=low`
- `background=auto`
- `format=png`
- `n=1`

Override those defaults only when the user has a concrete delivery need.

## Helper Script

Use `scripts/generate_image.py` for OpenAI-compatible or Azure deployment calls:

- In `--provider auto` mode, OpenAI-compatible is tried first when `OPENAI_API_KEY` is set.
- If OpenAI-compatible is not configured or the live request fails, Azure is tried when its key and endpoint are configured.
- `--provider openai` sends requests to `{OPENAI_BASE_URL or https://api.openai.com/v1}/images/*`
- `--provider azure` sends requests to `{deployment-root}/images/*?api-version=2025-04-01-preview`
- OpenAI-compatible requests include `model`, from `--model`, `OPENAI_IMAGE_MODEL`, or `gpt-image-2`.
- Reads the Azure endpoint from `AZURE_OPENAI_ENDPOINT_ROOT`, or builds it from `AZURE_OPENAI_ENDPOINT` plus `AZURE_OPENAI_DEPLOYMENT`
- Uses `AZURE_OPENAI_API_VERSION` when set, otherwise defaults to `2025-04-01-preview`
- Uses `OPENAI_API_KEY` for OpenAI-compatible calls
- Uses `AZURE_OPENAI_API_KEY`, with `AZURE_API_KEY` as a legacy fallback, for Azure calls
- Never commit real endpoints, deployment names, model names, or API keys
- Supports `--provider auto|openai|azure`, `--base-url`, and `--model`
- Supports `--prompt` or `--prompt-file`
- Supports `--size`, `--quality`, `--background`, `--format`, `--output-compression`, and `--n`
- Supports repeated `--image` plus optional `--mask` for edits
- Validates documented `gpt-image-2` size constraints locally
- Rejects known-too-old edit API versions before making the request
- Supports `--dry-run` for payload validation without an API call
- Saves one or more decoded images to disk
- Surfaces a clearer message for `moderation_blocked` failures

## When to Read the Reference File

- Read `references/gpt-image-2.md` if the user asks for:
  - exact OpenAI-compatible or Azure endpoint usage
  - exact size limits or popular resolutions
  - output format/compression tradeoffs
  - reference-image generation or masked edits
  - official limitations or current pricing examples
