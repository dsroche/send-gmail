#!/usr/bin/env bash

# Cretes a venv and launch script for send-gmail.py

set -euo pipefail
shopt -s nullglob

srcdir=$(dirname "$(readlink -f "$0")")

venvdir="$srcdir/venv"

if [[ -e $venvdir ]]; then
  echo "venv directory $venvdir already exists"
else
  python3 -m venv "$venvdir"
  "$venvdir/bin/pip" install -r "$srcdir/requirements.txt"
  echo
  echo "venv successfully created in $venvdir"
  echo
fi

launcher="$srcdir/send-gmail"
if [[ -e $launcher ]]; then
  echo "launcher script $launcher already exists"
else
  cat >"$launcher" <<EOF
#!/usr/bin/env bash
"$venvdir/bin/python3" "$srcdir/send-gmail.py" "\$@"
EOF
  chmod +x "$launcher"
  echo
  echo "launcher script created at $launcher"
fi

:
