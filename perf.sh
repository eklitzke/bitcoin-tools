#!/bin/bash
#
# Helper script to run "perf record" against a process.

set -eu

# How often to poll.
FREQUENCY=

# PID to profile.
PID=

# In PID profiling mode, how long to run for.
TIME=60

# If 1, then use DWARF debugging info (almost always what you want)
DWARF=1

# Output file.
OUTPUT=

while getopts ":df:F:ho:p:t:x" opt; do
  case $opt in
    d) DWARF=0 ;;
    f) ;&
    F) FREQUENCY="$OPTARG" ;;
    h) usage; exit ;;
    o) OUTPUT="$OPTARG" ;;
    p) PID="$OPTARG" ;;
    t) TIME="$OPTARG" ;;
    x) set -x ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

shift $((OPTIND - 1))

if [ -z "$PID" ] && [ $# -eq 0 ]; then
  echo "You must pass a pid with -p, or specify a command"
  exit 1
fi

if [ -n "$PID" ] && [ $# -gt 0 ]; then
  echo "Cannot use -p and positional arguments at the same time"
  exit 1
fi

if [ -z "$PID" ] && [ -z "$FREQUENCY" ]; then
  # in command mode, set a default frequency
  FREQUENCY=99
fi

ARGS=(-g)

if [ -n "$FREQUENCY" ]; then
  ARGS+=(-F "$FREQUENCY")
fi

if [ "$DWARF" -eq 1 ]; then
  ARGS+=(--call-graph dwarf)
fi

if [ -n "$PID" ]; then
  ARGS+=(-p "$PID" -- sleep "$TIME")
else
  ARGS+=($*)
fi

gensvg() {
  "$(dirname "${BASH_SOURCE[0]}")/gensvg.sh" "$@"
}

# cleanup logic if we need to generate an svg
svgcleanup() {
  if [ -n "$(jobs)" ]; then
    kill %1
    wait
  fi
  perf script | gensvg -o "$OUTPUT"
}

# run perf record
dorecord() {
  exec perf record "${ARGS[@]}"
}

if [ -n "$OUTPUT" ]; then
  if gensvg -t; then
    dorecord &
    trap svgcleanup EXIT INT
    wait
  else
    echo "Failed to find flamegraph.pl, set FLAMEGRAPHDIR and retry"
    exit 1
  fi
else
  dorecord
fi
