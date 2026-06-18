#!/usr/bin/env python3
"""
Generate or edit images with OpenAI-compatible or Azure OpenAI gpt-image-2 APIs.

The script uses only the Python standard library. In auto mode it tries an
OpenAI-compatible /v1 Images API first, then falls back to Azure OpenAI when
Azure credentials and endpoint settings are configured.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from pathlib import Path


DEFAULT_API_VERSION = "2025-04-01-preview"
DEFAULT_DEPLOYMENT = "gpt-image-2"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_IMAGE_MODEL = "gpt-image-2"
MIN_EDIT_API_VERSION = (2025, 4, 1)
OUTPUT_FORMATS = {"png", "jpeg", "webp"}
QUALITY_OPTIONS = {"low", "medium", "high", "auto"}
BACKGROUND_OPTIONS = {"opaque", "auto", "transparent"}
COMMANDS = {"generate", "edit"}
PROVIDER_AUTO = "auto"
PROVIDER_OPENAI = "openai"
PROVIDER_AZURE = "azure"
PROVIDER_OPTIONS = {PROVIDER_AUTO, PROVIDER_OPENAI, PROVIDER_AZURE}
AZURE_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
LEGACY_AZURE_API_KEY_ENV = "AZURE_API_KEY"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_BASE_URL_ENV = "OPENAI_BASE_URL"
OPENAI_IMAGE_MODEL_ENV = "OPENAI_IMAGE_MODEL"
AZURE_ENDPOINT_ROOT_ENV = "AZURE_OPENAI_ENDPOINT_ROOT"
AZURE_ENDPOINT_ENV = "AZURE_OPENAI_ENDPOINT"
AZURE_DEPLOYMENT_ENV = "AZURE_OPENAI_DEPLOYMENT"
AZURE_API_VERSION_ENV = "AZURE_OPENAI_API_VERSION"


def inject_default_command(argv: list[str]) -> list[str]:
    if not argv:
        return ["generate"]
    if argv[0] in COMMANDS:
        return argv
    return ["generate", *argv]


def default_api_version() -> str:
    return os.getenv(AZURE_API_VERSION_ENV, DEFAULT_API_VERSION)


def provider_label(provider: str) -> str:
    if provider == PROVIDER_OPENAI:
        return "OpenAI-compatible"
    if provider == PROVIDER_AZURE:
        return "Azure OpenAI"
    return provider


def resolve_openai_base_url(args: argparse.Namespace) -> str:
    return args.base_url or os.getenv(OPENAI_BASE_URL_ENV, DEFAULT_OPENAI_BASE_URL)


def resolve_openai_model(args: argparse.Namespace) -> str:
    return args.model or os.getenv(OPENAI_IMAGE_MODEL_ENV, DEFAULT_OPENAI_IMAGE_MODEL)


def endpoint_root_from_parts(endpoint: str, deployment: str) -> str:
    return f"{endpoint.rstrip('/')}/openai/deployments/{deployment.strip('/')}"


def resolve_endpoint_root(args: argparse.Namespace) -> str:
    if args.endpoint_root:
        return args.endpoint_root

    endpoint_root = os.getenv(AZURE_ENDPOINT_ROOT_ENV)
    if endpoint_root:
        return endpoint_root

    endpoint = os.getenv(AZURE_ENDPOINT_ENV)
    deployment = args.deployment or os.getenv(AZURE_DEPLOYMENT_ENV) or DEFAULT_DEPLOYMENT
    if endpoint:
        return endpoint_root_from_parts(endpoint, deployment)

    raise ValueError(
        "Azure endpoint is not configured. Set AZURE_OPENAI_ENDPOINT_ROOT, or set "
        "AZURE_OPENAI_ENDPOINT with AZURE_OPENAI_DEPLOYMENT, or pass --endpoint-root."
    )


def has_openai_config(args: argparse.Namespace) -> bool:
    return bool(os.getenv(OPENAI_API_KEY_ENV))


def has_openai_dry_run_config(args: argparse.Namespace) -> bool:
    return bool(
        has_openai_config(args)
        or args.base_url
        or os.getenv(OPENAI_BASE_URL_ENV)
    )


def has_azure_key_config(args: argparse.Namespace) -> bool:
    return bool(
        os.getenv(AZURE_API_KEY_ENV)
        or os.getenv(LEGACY_AZURE_API_KEY_ENV)
    )


def has_azure_endpoint_config(args: argparse.Namespace) -> bool:
    return bool(
        args.endpoint_root
        or os.getenv(AZURE_ENDPOINT_ROOT_ENV)
        or os.getenv(AZURE_ENDPOINT_ENV)
    )


def has_azure_config(args: argparse.Namespace) -> bool:
    return has_azure_key_config(args) and has_azure_endpoint_config(args)


def select_providers(args: argparse.Namespace, for_dry_run: bool = False) -> list[str]:
    if args.provider != PROVIDER_AUTO:
        return [args.provider]

    providers: list[str] = []
    if for_dry_run:
        if has_openai_dry_run_config(args):
            providers.append(PROVIDER_OPENAI)
        if has_azure_endpoint_config(args):
            providers.append(PROVIDER_AZURE)
    else:
        if has_openai_config(args):
            providers.append(PROVIDER_OPENAI)
        if has_azure_config(args):
            providers.append(PROVIDER_AZURE)
    if providers:
        return providers

    if for_dry_run:
        raise ValueError(
            "No image API provider is configured for dry-run. Set OPENAI_BASE_URL "
            "or OPENAI_API_KEY for an OpenAI-compatible /v1 API, or set "
            "AZURE_OPENAI_ENDPOINT_ROOT or AZURE_OPENAI_ENDPOINT."
        )

    raise ValueError(
        "No image API provider is configured. Set OPENAI_API_KEY for an "
        "OpenAI-compatible /v1 API, or set AZURE_OPENAI_API_KEY with "
        "AZURE_OPENAI_ENDPOINT_ROOT or AZURE_OPENAI_ENDPOINT."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate or edit images with OpenAI-compatible or Azure OpenAI "
            "gpt-image-2 APIs."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--provider",
        default=PROVIDER_AUTO,
        choices=sorted(PROVIDER_OPTIONS),
        help="API provider. auto tries OpenAI-compatible first, then Azure OpenAI.",
    )
    common.add_argument(
        "--base-url",
        default=None,
        help=(
            "OpenAI-compatible /v1 base URL. Defaults to OPENAI_BASE_URL "
            "or api.openai.com."
        ),
    )
    common.add_argument(
        "--model",
        default=None,
        help=(
            "OpenAI-compatible image model. Defaults to OPENAI_IMAGE_MODEL "
            "or gpt-image-2."
        ),
    )
    common.add_argument(
        "--endpoint-root",
        default=None,
        help="Azure deployment root without the /images/* suffix.",
    )
    common.add_argument(
        "--deployment",
        help="Azure deployment name used with AZURE_OPENAI_ENDPOINT.",
    )
    common.add_argument(
        "--api-version",
        default=default_api_version(),
        help="Azure OpenAI api-version query parameter.",
    )
    common.add_argument(
        "--api-key",
        help="Override the selected provider API key for this call.",
    )
    common.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds.",
    )
    common.add_argument(
        "--response-json",
        type=Path,
        help="Optional path to save the raw JSON response.",
    )
    common.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the outgoing request summary without calling the API.",
    )

    generate_parser = subparsers.add_parser(
        "generate",
        parents=[common],
        help="Create new images from a prompt.",
    )
    add_prompt_args(generate_parser)
    add_output_args(generate_parser)
    generate_parser.set_defaults(handler=handle_generate)

    edit_parser = subparsers.add_parser(
        "edit",
        parents=[common],
        help="Edit one or more images, optionally with a mask.",
    )
    add_prompt_args(edit_parser)
    add_output_args(edit_parser)
    edit_parser.add_argument(
        "--image",
        action="append",
        type=Path,
        required=True,
        help="Input image path. Repeat to send multiple reference images.",
    )
    edit_parser.add_argument(
        "--mask",
        type=Path,
        help="Optional mask image path.",
    )
    edit_parser.set_defaults(handler=handle_edit)

    return parser


def add_prompt_args(parser: argparse.ArgumentParser) -> None:
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="Prompt text to send to the API.")
    prompt_group.add_argument(
        "--prompt-file",
        type=Path,
        help="Path to a UTF-8 text file containing the prompt.",
    )


def add_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("image"),
        help="Output file path. The proper extension is added automatically.",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        help="Image size such as 1024x1024, 1536x1024, 1024x1536, or auto.",
    )
    parser.add_argument(
        "--quality",
        default="low",
        choices=sorted(QUALITY_OPTIONS),
        help="Rendering quality.",
    )
    parser.add_argument(
        "--background",
        default="auto",
        choices=sorted(BACKGROUND_OPTIONS),
        help="Background handling.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        default="png",
        choices=sorted(OUTPUT_FORMATS),
        help="Output image format.",
    )
    parser.add_argument(
        "--output-compression",
        type=int,
        help="Compression percentage. Useful primarily for jpeg or webp.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of images to return.",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    if argv is None:
        argv = sys.argv[1:]
    argv = inject_default_command(argv)
    return build_parser().parse_args(argv)


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        prompt = args.prompt.strip()
    else:
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError("Prompt must not be empty.")
    return prompt


def parse_size(size: str) -> None:
    if size == "auto":
        return

    parts = size.lower().split("x")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError("Size must look like WIDTHxHEIGHT or be auto.")

    width, height = (int(part) for part in parts)
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive integers.")
    if width > 3840 or height > 3840:
        raise ValueError("Each image edge must be <= 3840.")
    if width % 16 != 0 or height % 16 != 0:
        raise ValueError("Each image edge must be a multiple of 16.")

    long_edge = max(width, height)
    short_edge = min(width, height)
    if long_edge > short_edge * 3:
        raise ValueError("Aspect ratio must not exceed 3:1.")

    pixels = width * height
    if pixels < 655_360 or pixels > 8_294_400:
        raise ValueError("Total pixels must be between 655,360 and 8,294,400.")


def validate_common_args(args: argparse.Namespace) -> None:
    parse_size(args.size)

    if args.background == "transparent":
        raise ValueError("gpt-image-2 does not support transparent backgrounds.")

    if args.n < 1:
        raise ValueError("--n must be >= 1.")

    if args.output_compression is not None and not 0 <= args.output_compression <= 100:
        raise ValueError("--output-compression must be between 0 and 100.")

    if args.command == "edit":
        api_version_date = parse_api_version_date(args.api_version)
        if api_version_date is not None and api_version_date < MIN_EDIT_API_VERSION:
            raise ValueError(
                "Azure image edits for gpt-image-2 require api-version 2025-04-01-preview or later."
            )


def parse_api_version_date(api_version: str) -> tuple[int, int, int] | None:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", api_version)
    if not match:
        return None
    return tuple(int(match.group(index)) for index in range(1, 4))


def normalize_output_path(path: Path, output_format: str) -> Path:
    suffix = f".{output_format}"
    if path.suffix.lower() != suffix:
        path = path.with_suffix(suffix)
    return path


def build_output_paths(base_path: Path, output_format: str, count: int) -> list[Path]:
    resolved = normalize_output_path(base_path, output_format)
    if count == 1:
        return [resolved]

    stem = resolved.stem
    parent = resolved.parent
    suffix = resolved.suffix
    return [parent / f"{stem}-{index}{suffix}" for index in range(1, count + 1)]


def generation_payload(prompt: str, args: argparse.Namespace, provider: str) -> dict:
    payload = {
        "prompt": prompt,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
        "n": args.n,
    }
    if provider == PROVIDER_OPENAI:
        payload["model"] = resolve_openai_model(args)
    if args.background != "auto":
        payload["background"] = args.background
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    return payload


def edit_fields(
    prompt: str,
    args: argparse.Namespace,
    provider: str,
) -> tuple[list[tuple[str, str]], list[tuple[str, Path]]]:
    fields: list[tuple[str, str]] = [("prompt", prompt)]
    image_field = "image[]" if provider == PROVIDER_OPENAI else "image"
    files: list[tuple[str, Path]] = [
        (image_field, image_path)
        for image_path in args.image
    ]

    if provider == PROVIDER_OPENAI:
        fields.append(("model", resolve_openai_model(args)))
    if args.mask is not None:
        files.append(("mask", args.mask))
    if args.size != "1024x1024":
        fields.append(("size", args.size))
    if args.quality != "low":
        fields.append(("quality", args.quality))
    if args.background != "auto":
        fields.append(("background", args.background))
    if args.output_format != "png":
        fields.append(("output_format", args.output_format))
    if args.output_compression is not None:
        fields.append(("output_compression", str(args.output_compression)))
    if args.n != 1:
        fields.append(("n", str(args.n)))
    return fields, files


def build_url(endpoint_root: str, operation: str, api_version: str) -> str:
    return f"{endpoint_root.rstrip('/')}/images/{operation}?api-version={api_version}"


def build_openai_url(base_url: str, operation: str) -> str:
    return f"{base_url.rstrip('/')}/images/{operation}"


def build_provider_url(provider: str, args: argparse.Namespace, operation: str) -> str:
    if provider == PROVIDER_OPENAI:
        return build_openai_url(resolve_openai_base_url(args), operation)
    endpoint_root = resolve_endpoint_root(args)
    return build_url(endpoint_root, operation, args.api_version)


class ProviderRequestError(Exception):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(message)
        self.provider = provider


def json_request(
    provider: str,
    url: str,
    payload: dict,
    api_key: str,
    timeout: int,
) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise ProviderRequestError(
            provider,
            format_http_error(provider, error),
        ) from error
    except urllib.error.URLError as error:
        raise ProviderRequestError(
            provider,
            f"{provider_label(provider)} request failed: {error.reason}",
        ) from error
    except Exception as exc:
        raise ProviderRequestError(
            provider,
            f"{provider_label(provider)} request failed: {exc}",
        ) from exc


def multipart_request(
    provider: str,
    url: str,
    fields: list[tuple[str, str]],
    files: list[tuple[str, Path]],
    api_key: str,
    timeout: int,
) -> dict:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    body = build_multipart_body(boundary, fields, files)
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise ProviderRequestError(
            provider,
            format_http_error(provider, error),
        ) from error
    except urllib.error.URLError as error:
        raise ProviderRequestError(
            provider,
            f"{provider_label(provider)} request failed: {error.reason}",
        ) from error
    except Exception as exc:
        raise ProviderRequestError(
            provider,
            f"{provider_label(provider)} request failed: {exc}",
        ) from exc


def build_multipart_body(
    boundary: str,
    fields: list[tuple[str, str]],
    files: list[tuple[str, Path]],
) -> bytes:
    chunks: list[bytes] = []
    boundary_bytes = boundary.encode("utf-8")

    for name, value in fields:
        chunks.extend(
            [
                b"--" + boundary_bytes + b"\r\n",
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for field_name, file_path in files:
        filename = file_path.name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        file_bytes = file_path.read_bytes()
        chunks.extend(
            [
                b"--" + boundary_bytes + b"\r\n",
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{filename}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                file_bytes,
                b"\r\n",
            ]
        )

    chunks.append(b"--" + boundary_bytes + b"--\r\n")
    return b"".join(chunks)


def save_images(response: dict, output_paths: list[Path]) -> list[Path]:
    data = response.get("data")
    if not isinstance(data, list) or len(data) < len(output_paths):
        raise ValueError("Response did not contain the expected image data.")

    saved_paths: list[Path] = []
    for index, output_path in enumerate(output_paths):
        item = data[index]
        image_base64 = item.get("b64_json") if isinstance(item, dict) else None
        if not image_base64:
            raise ValueError(f"Image {index + 1} did not include b64_json.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(base64.b64decode(image_base64))
        saved_paths.append(output_path)
    return saved_paths


def save_provider_images(
    provider: str,
    response: dict,
    output_paths: list[Path],
) -> list[Path]:
    try:
        return save_images(response, output_paths)
    except ValueError as exc:
        raise ProviderRequestError(
            provider,
            f"{provider_label(provider)} response failed: {exc}",
        ) from exc


def save_response_json(path: Path | None, response: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(response, indent=2), encoding="utf-8")


def moderation_hint(error_payload: dict) -> str | None:
    code = error_payload.get("code")
    details = error_payload.get("moderation_details") or {}
    if code != "moderation_blocked":
        return None

    categories = details.get("categories") or []
    stage = details.get("moderation_stage")
    hint = "The request was blocked by image safety checks. Rewrite it in neutral visual terms."
    if "harassment" in categories:
        hint = "Remove abusive or targeted language and describe the scene neutrally."
    elif stage == "input":
        hint = "Revise the prompt or input content and try again."
    elif stage == "output":
        hint = "The generated result was blocked. Keep the concept but change the phrasing."

    return hint


def format_http_error(provider: str, error: urllib.error.HTTPError) -> str:
    label = provider_label(provider)
    raw = error.read().decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return f"{label} request failed: HTTP {error.code}\n{raw}"

    err = parsed.get("error") if isinstance(parsed, dict) else None
    if not isinstance(err, dict):
        return f"{label} request failed: HTTP {error.code}\n{raw}"

    lines = [f"{label} request failed: {err.get('message', 'unknown error')}"]
    if err.get("code"):
        lines.append(f"code: {err['code']}")
    hint = moderation_hint(err)
    if hint:
        lines.append(hint)
    return "\n".join(lines)


def require_openai_api_key(args: argparse.Namespace) -> str:
    api_key = args.api_key or os.getenv(OPENAI_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            "OpenAI-compatible API key is not set. "
            "Pass --api-key or export OPENAI_API_KEY."
        )
    return api_key


def require_azure_api_key(args: argparse.Namespace) -> str:
    api_key = (
        args.api_key
        or os.getenv(AZURE_API_KEY_ENV)
        or os.getenv(LEGACY_AZURE_API_KEY_ENV)
    )
    if not api_key:
        raise ValueError(
            "Azure API key is not set. Pass --api-key or export AZURE_OPENAI_API_KEY."
        )
    return api_key


def require_provider_api_key(args: argparse.Namespace, provider: str) -> str:
    if provider == PROVIDER_OPENAI:
        return require_openai_api_key(args)
    return require_azure_api_key(args)


def require_files_exist(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise ValueError("Missing input files: " + ", ".join(missing))


def print_saved_paths(saved_paths: list[Path]) -> None:
    for path in saved_paths:
        print(path)


def run_provider_attempts(
    providers: list[str],
    attempt: Callable[[str], list[Path]],
) -> int:
    errors: list[str] = []
    for index, provider in enumerate(providers):
        try:
            saved = attempt(provider)
        except ProviderRequestError as error:
            errors.append(str(error))
            if index + 1 < len(providers):
                next_provider = providers[index + 1]
                print(
                    f"{provider_label(provider)} request failed; "
                    f"falling back to {provider_label(next_provider)}.",
                    file=sys.stderr,
                )
                continue

            for message in errors:
                print(message, file=sys.stderr)
            return 1
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print_saved_paths(saved)
        return 0

    return 1


def build_dry_run_preview(
    provider: str,
    args: argparse.Namespace,
    operation: str,
    content_type: str,
    output_paths: list[Path],
    payload: dict | None = None,
    fields: list[tuple[str, str]] | None = None,
    files: list[tuple[str, Path]] | None = None,
) -> dict:
    preview = {
        "provider": provider,
        "method": "POST",
        "url": build_provider_url(provider, args, operation),
        "headers": {
            "Content-Type": content_type,
            "Authorization": "Bearer ***",
        },
        "output_paths": [str(path) for path in output_paths],
    }
    if payload is not None:
        preview["payload"] = payload
    if fields is not None:
        preview["fields"] = fields
    if files is not None:
        preview["files"] = [
            {"field": field_name, "path": str(path)}
            for field_name, path in files
        ]
    return preview


def handle_generate(args: argparse.Namespace, prompt: str) -> int:
    output_paths = build_output_paths(args.output, args.output_format, args.n)
    try:
        providers = select_providers(args, for_dry_run=args.dry_run)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.dry_run:
        provider = providers[0]
        payload = generation_payload(prompt, args, provider)
        preview = {
            **build_dry_run_preview(
                provider,
                args,
                "generations",
                "application/json",
                output_paths,
                payload=payload,
            ),
            "fallback_providers": providers[1:],
        }
        print(json.dumps(preview, indent=2))
        return 0

    def attempt(provider: str) -> list[Path]:
        payload = generation_payload(prompt, args, provider)
        url = build_provider_url(provider, args, "generations")
        api_key = require_provider_api_key(args, provider)
        response = json_request(provider, url, payload, api_key, args.timeout)
        save_response_json(args.response_json, response)
        return save_provider_images(provider, response, output_paths)

    return run_provider_attempts(providers, attempt)


def handle_edit(args: argparse.Namespace, prompt: str) -> int:
    output_paths = build_output_paths(args.output, args.output_format, args.n)
    try:
        providers = select_providers(args, for_dry_run=args.dry_run)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.dry_run:
        provider = providers[0]
        fields, files = edit_fields(prompt, args, provider)
        preview = {
            **build_dry_run_preview(
                provider,
                args,
                "edits",
                "multipart/form-data",
                output_paths,
                fields=fields,
                files=files,
            ),
            "fallback_providers": providers[1:],
        }
        print(json.dumps(preview, indent=2))
        return 0

    try:
        input_paths = args.image + ([args.mask] if args.mask is not None else [])
        require_files_exist(input_paths)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    def attempt(provider: str) -> list[Path]:
        fields, files = edit_fields(prompt, args, provider)
        url = build_provider_url(provider, args, "edits")
        api_key = require_provider_api_key(args, provider)
        require_files_exist([path for _, path in files])
        response = multipart_request(provider, url, fields, files, api_key, args.timeout)
        save_response_json(args.response_json, response)
        return save_provider_images(provider, response, output_paths)

    return run_provider_attempts(providers, attempt)


def main() -> int:
    try:
        args = parse_args()
        prompt = load_prompt(args)
        validate_common_args(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return args.handler(args, prompt)


if __name__ == "__main__":
    raise SystemExit(main())
