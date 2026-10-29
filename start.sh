#!/usr/bin/env bash
# Run from any directory; arguments are passed through to the server.
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python="$project_dir/.venv/bin/python"

if [[ ! -x "$python" ]]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo 'Install Python 3.10 or newer, then run this script again.' >&2
        exit 1
    fi
    echo 'Creating Python virtual environment...'
    python3 -m venv "$project_dir/.venv"
fi

if ! "$python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo 'Python 3.10 or newer is required.' >&2
    exit 1
fi

echo 'Checking Python dependencies...'
"$python" -m pip install -r "$project_dir/scout/requirements.txt"
echo 'Starting Scout (Ctrl+C to stop).'
exec "$python" "$project_dir/scout/server.py" --auto-port --open-browser "$@"
