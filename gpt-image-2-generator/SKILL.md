---
name: gpt-image-2-generator
description: Generate and edit images with an Azure OpenAI gpt-image-2 deployment from a visual brief or text requirements. Use when Codex needs to create one or more new images, edit an existing image with or without a mask, adapt requests to the Azure OpenAI Images API, choose image parameters such as size, quality, background, and output format, or run a local helper script against the Azure deployment endpoint.
---

# GPT Image 2 Generator

## Overview

Turn a loose image request into a structured visual brief, choose sane `gpt-image-2` settings, and generate or edit files through the Azure OpenAI Images API. Configure the Azure endpoint and deployment with environment variables so personal resource names and endpoints stay out of the repository.

## Quick Start

- Configure Azure locally before live calls:
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
- Read `references/gpt-image-2.md` when you need the Azure endpoint shape, exact constraints, or edit/reference-image guidance.

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

Use `scripts/generate_image.py` for Azure deployment calls:

- `generate` sends JSON to `/images/generations?api-version=2025-04-01-preview`
- `edit` sends multipart form data to `/images/edits?api-version=2025-04-01-preview`
- Reads the Azure endpoint from `AZURE_OPENAI_ENDPOINT_ROOT`, or builds it from `AZURE_OPENAI_ENDPOINT` plus `AZURE_OPENAI_DEPLOYMENT`
- Uses `AZURE_OPENAI_API_VERSION` when set, otherwise defaults to `2025-04-01-preview`
- Uses `AZURE_OPENAI_API_KEY` by default, with `AZURE_API_KEY` and `OPENAI_API_KEY` as fallbacks
- Never commit real Azure endpoints, deployment names, or API keys
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
  - exact Azure endpoint usage
  - exact size limits or popular resolutions
  - output format/compression tradeoffs
  - reference-image generation or masked edits
  - official limitations or current pricing examples
