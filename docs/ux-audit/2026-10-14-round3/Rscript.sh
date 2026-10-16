#!/bin/bash
r_script_dir=${0%/*}
export R_HOME="$(CDPATH= cd -- "$r_script_dir/.." && pwd)"
export R_SHARE_DIR="$R_HOME/share"
export R_INCLUDE_DIR="$R_HOME/include"
export R_DOC_DIR="$R_HOME/doc"
r_arguments=(--no-save --no-restore --no-echo)
expression=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    -e) r_arguments+=(-e "$2"); expression=true; shift 2 ;;
    --*) r_arguments+=("$1"); shift ;;
    *) if $expression; then break; fi
       r_arguments+=("--file=$1"); shift; break ;;
  esac
done
exec "$R_HOME/bin/R" "${r_arguments[@]}" --args "$@"
