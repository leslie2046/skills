# GPT Image 2 Reference

Use this file only when exact API behavior matters.

## Provider selection

- `--provider auto` tries OpenAI-compatible first when `OPENAI_API_KEY` is set.
- If OpenAI-compatible is not configured or a live request fails, Azure OpenAI is tried when Azure key and endpoint variables are configured.
- `--provider openai` and `--provider azure` force one provider and do not fall back.
- Dry runs show the selected provider and fallback list without requiring an API key for endpoint-shape validation.

## OpenAI-compatible configuration

- base URL defaults to `https://api.openai.com/v1`, or read from:
  - `OPENAI_BASE_URL`
  - `--base-url`
- model defaults to `gpt-image-2`, or read from:
  - `OPENAI_IMAGE_MODEL`
  - `--model`
- auth header uses `Authorization: Bearer $OPENAI_API_KEY`

The bundled script appends the `/images/*` path suffix itself. Set `OPENAI_BASE_URL` to the /v1 root, not to an `/images/*` endpoint.

## Azure deployment configuration

- deployment root is read from `AZURE_OPENAI_ENDPOINT_ROOT`, or built from:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_DEPLOYMENT`
- api version defaults to `2025-04-01-preview`, or read from `AZURE_OPENAI_API_VERSION`
- auth header uses `Authorization: Bearer $AZURE_OPENAI_API_KEY`

The bundled script appends the `/images/*` path suffix itself. Do not commit real Azure endpoints, resource names, deployment names, or keys.

## Endpoints used by the script

- OpenAI-compatible generate:
  - `POST {base-url}/images/generations`
- OpenAI-compatible edit:
  - `POST {base-url}/images/edits`
- Azure generate:
  - `POST {deployment-root}/images/generations?api-version=2025-04-01-preview`
- Azure edit:
  - `POST {deployment-root}/images/edits?api-version=2025-04-01-preview`

## Compatibility note

- Microsoft Learn's Azure image generation guide, updated on `2026-04-17`, shows `GPT-image-2` image edits on:
  - `POST {endpoint}/openai/deployments/{deployment}/images/edits?api-version=2025-04-01-preview`
- The same guide describes `GPT-image-2` as supporting:
  - text-to-image generation
  - image-to-image generation
  - editing with a mask
- Use `2025-04-01-preview` or later for edits on Azure `gpt-image-2` deployments.

## Request mapping

OpenAI-compatible generate request body:

- `model`
- `prompt`
- `size`
- `quality`
- `output_compression`
- `output_format`
- `n`

Azure generate request body:

- `prompt`
- `size`
- `quality`
- `output_compression`
- `output_format`
- `n`

OpenAI-compatible edit multipart form:

- `image[]=@...`
- optional `mask=@...`
- `model=...`
- `prompt=...`

Azure edit multipart form:

- `image=@...`
- optional `mask=@...`
- `prompt=...`

The script mirrors those request shapes.

## Official pages

- Azure image generation guide:
  - `https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/dall-e`
- Azure OpenAI API version lifecycle:
  - `https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle`
- OpenAI image generation guide:
  - `https://developers.openai.com/api/docs/guides/image-generation`

Checked against the official Microsoft Learn and OpenAI developer docs on `2026-06-18`.

## Response shape

The API returns base64 image data in `data[].b64_json`, which the script decodes to files automatically.

## Output controls

- `size`
  - Popular values: `1024x1024`, `1536x1024`, `1024x1536`, `2048x2048`, `2048x1152`, `3840x2160`, `2160x3840`, `auto`
  - Constraints:
    - max edge `<= 3840`
    - both edges must be multiples of `16`
    - aspect ratio must not exceed `3:1`
    - total pixels must be between `655360` and `8294400`
- `quality`
  - `low`, `medium`, `high`, `auto`
  - `low` is the fastest and is a good draft default
- `background`
  - `opaque` or `auto`
  - `transparent` is not supported by `gpt-image-2`
- `output_format`
  - `png`, `jpeg`, `webp`
  - default is `png`
- `output_compression`
  - accepted by the user-provided Azure example
  - range `0-100`
  - usually most relevant for `jpeg` and `webp`
- `n`
  - generate multiple images in one request

## Reference-image and edit workflows

If the user wants generation from reference images, image edits, or masked replacement:

- Use the provider edit endpoint shape used in this skill:
  - OpenAI-compatible: `POST {base-url}/images/edits`
  - Azure: `POST {deployment-root}/images/edits?api-version=2025-04-01-preview`
- The official guides show:
  - editing an existing image
  - using multiple input images as references
  - editing with a mask
- This skill currently implements:
  - one or more `image[]` parts for OpenAI-compatible calls
  - one or more `image` parts for Azure calls
  - optional `mask`
  - prompt-driven edits

## Moderation handling

If the API returns `moderation_blocked`:

- inspect `moderation_details` when available
- keep the end-user explanation generic
- rewrite the prompt in neutral language
- remove abusive, targeted, or graphic phrasing
- treat `input` vs `output` moderation stage as separate cases in logs if needed
