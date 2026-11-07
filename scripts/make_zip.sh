#!/usr/bin/env bash
# Build the Moodle submission zip (E-05).
#
# Default name: Grupo7-AlbanoMendes-GustavoCunha-ArthurBastos.zip
# Override by passing a name:  scripts/make_zip.sh OutroNome
#
# The zip contains the code, docs (incl. slides.pptx), tests, scripts, config,
# README.md and AUTHORS.md. It excludes the virtualenv, caches, git, the
# professor's reference materials in Docs/ (capital D), and the zip itself.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

NAME="${1:-Grupo7-AlbanoMendes-GustavoCunha-ArthurBastos}"
OUT="../${NAME}.zip"
rm -f "$OUT"

zip -r "$OUT" . \
  -x '.venv/*' \
  -x '*/__pycache__/*' \
  -x '.pytest_cache/*' \
  -x '*.pyc' \
  -x 'evidencias/*' \
  -x '*.egg-info/*' \
  -x './.git/*' \
  -x 'Docs/*' \
  -x '*.zip' \
  -x '*.~lock.*#'

echo "wrote $OUT"
echo "Contents:"
unzip -l "$OUT"
