#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <project-slug> [display-name] [ENV_PREFIX]" >&2
  echo "Example: $0 my-calendar 'My Calendar' MY_CALENDAR" >&2
  echo "If ENV_PREFIX is omitted, it is derived from the slug, e.g. my-calendar -> MY_CALENDAR." >&2
}

if [[ $# -lt 1 || $# -gt 3 ]]; then
  usage
  exit 2
fi

slug="$1"
display_name="${2:-$1}"
if [[ $# -ge 3 ]]; then
  env_prefix_base="$3"
else
  env_prefix_base="$(printf '%s' "$slug" | tr '[:lower:]-' '[:upper:]_')"
fi
env_prefix_base="${env_prefix_base%_}"
env_prefix="${env_prefix_base}_"
lower_prefix="$(printf '%s' "$env_prefix_base" | tr '[:upper:]' '[:lower:]')"
python_bin="${PYTHON:-}"

if [[ ! "$slug" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "Project slug must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens." >&2
  exit 2
fi

if [[ ! "$env_prefix_base" =~ ^[A-Z][A-Z0-9_]*$ ]]; then
  echo "ENV_PREFIX must start with an uppercase letter and contain only uppercase letters, numbers, and underscores." >&2
  exit 2
fi

if [[ -z "$python_bin" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  elif command -v python >/dev/null 2>&1; then
    python_bin="python"
  else
    echo "python3 is required to initialize the template." >&2
    exit 1
  fi
fi

"$python_bin" - "$slug" "$display_name" "$env_prefix_base" "$env_prefix" "$lower_prefix" <<'PY'
from pathlib import Path
import sys

slug = sys.argv[1]
display_name = sys.argv[2]
env_prefix_base = sys.argv[3]
env_prefix = sys.argv[4]
lower_prefix = sys.argv[5]

skip_dirs = {
    ".git",
    ".pytest_cache",
    ".terraform",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
}
skip_suffixes = {
    ".pyc",
    ".pyo",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".zip",
    ".gz",
    ".lockb",
}

for path in Path(".").rglob("*"):
    if not path.is_file():
        continue
    if path == Path("scripts/init-project.sh"):
        continue
    if any(part in skip_dirs for part in path.parts):
        continue
    if path.suffix in skip_suffixes:
        continue

    try:
        text = path.read_text()
    except UnicodeDecodeError:
        continue

    original = text
    text = text.replace("FastAPI React AWS Template", display_name)
    text = text.replace("fastapi-react-aws-template", slug)
    text = text.replace("FASTAPI_REACT_AWS_TEMPLATE_", env_prefix)
    text = text.replace("FASTAPI_REACT_AWS_TEMPLATE", env_prefix_base)
    # Backward-compatible replacements for older copies of this template.
    text = text.replace("VoiceCal — Hello World", display_name)
    text = text.replace("VoiceCal Hello World", display_name)
    text = text.replace("hello-world", slug)
    text = text.replace("Hello World", display_name)
    text = text.replace("HELLO_WORLD_", env_prefix)
    text = text.replace("HELLO_WORLD", env_prefix_base)

    # Keep Python package imports as hello_world, but rename the generic Terraform
    # contract variable prefix because it is public template surface.
    if path.parts[:2] == ("infra", "terraform"):
        text = text.replace("hello_world_", f"{lower_prefix}_")

    if text != original:
        path.write_text(text)
PY

echo "Project initialized as ${slug}."
echo "Environment prefix: ${env_prefix}"
echo "Next: copy config/env.example to config/.env and update GitHub variables from infra/bootstrap outputs."
