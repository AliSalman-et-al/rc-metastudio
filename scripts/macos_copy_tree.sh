# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

copy_tree() {
  local source="$1"
  local destination="$2"
  if [ ! -d "$source" ]; then
    echo "Source directory was not found: $source" >&2
    exit 1
  fi
  rm -rf "$destination"
  mkdir -p "$(dirname "$destination")"
  if command -v rsync >/dev/null 2>&1; then
    mkdir -p "$destination"
    rsync -a --delete "$source"/ "$destination"/
  else
    mkdir -p "$destination"
    (cd "$source" && tar -cf - .) | (cd "$destination" && tar -xf -)
  fi
}
