#!/usr/bin/env bash
set -euo pipefail
UNIT="${UNIT:-stratgen}"
LINES="${LINES:-200}"
FMT="${FMT:-short-iso}"   # alternativ: cat
SINCE="${SINCE:--1h}"
PRIO="${PRIO:-all}"       # "all" oder "errors"

if [ "$PRIO" = "errors" ]; then
  sudo journalctl -u "$UNIT" -S "$SINCE" -p warning..emerg -n "$LINES" -f --no-pager -o "$FMT"
else
  sudo journalctl -u "$UNIT" -S "$SINCE" -n "$LINES" -f --no-pager -o "$FMT"
fi
