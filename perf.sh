#!/bin/bash
#
# Helper script to run "perf record" against a process.

set -eu

# If this is 1, then we filter out background LevelDB compaction work (usually
# what you want, as that happens asynchronously in another thread, and pollutes
# graphs).
NOBGTHREAD=1

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

while getopts ":b:d:f:F:h:o:p:t:x" opt; do
  case $opt in
    b) NOBGTHREAD=0 ;;
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

# have we found the flamegraph installation?
haveflamegraph() {
  test -x "${FLAMEGRAPHDIR}/flamegraph.pl"
}

# try to find a flamegraph installation
findflamegraph() {
  set +u
  trap 'set -u' RETURN
  if [ -z "$FLAMEGRAPHDIR" ]; then
    FLAMEGRAPHDIR=.
    if haveflamegraph; then
      return
    fi
    FLAMEGRAPHDIR=../FlameGraph
    if haveflamegraph; then
      return
    fi
    return 1
  fi
}

collapse() {
  perf script | "${FLAMEGRAPHDIR}/stackcollapse-perf.pl"
}

gensvg() {
  "${FLAMEGRAPHDIR}/flamegraph.pl" > "$OUTPUT"
}

# cleanup logic if we need to generate an svg
svgcleanup() {
  if [ -n "$(jobs)" ]; then
    kill %1
    wait
  fi

  if [ "$NOBGTHREAD" -eq 1 ]; then
    collapse | grep -v BGThreadWrapper | gensvg
  else
    collapse | gensvg
  fi
}

# run perf record
dorecord() {
  exec perf record "${ARGS[@]}"
}

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
  ARGS+=("$*")
fi

if [ -n "$OUTPUT" ]; then
  if findflamegraph; then
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
