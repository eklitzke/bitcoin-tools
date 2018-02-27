#!/bin/bash

set -e

# If this is 1, then we filter out background LevelDB compaction work (usually
# what you want, as that happens asynchronously in another thread, and pollutes
# graphs).
NOBGTHREAD=1

# Output destination.
OUTPUT=

# In test mode we just verify that we know how to run flamegraph.pl
TEST=0

while getopts ":bd:o:tx" opt; do
  case $opt in
    b) NOBGTHREAD=0 ;;
    d)
      # You can also just set this in your shell before invoking gensvg.sh
      FLAMEGRAPHDIR="$OPTARG"
      ;;
    o) OUTPUT="$OPTARG" ;;
    t) TEST=1 ;;
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

# have we found the flamegraph installation?
haveflamegraph() {
  test -x "${FLAMEGRAPHDIR}/flamegraph.pl"
}

# try to find a flamegraph installation
findflamegraph() {
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

if [ "$TEST" -eq 1 ]; then
  findflamegraph
  exit $?
fi

if [ -z "$OUTPUT" ]; then
  if [ $# -eq 1 ]; then
    OUTPUT="$1"
  else
    echo "usage: $0 OUTPUT.svg"
    exit 1
  fi
fi

if ! findflamegraph; then
  echo "Failed to find flamegraph.pl, retry with -d /path/to/FlameGraph"
  exit 1
fi

collapse() {
  "${FLAMEGRAPHDIR}/stackcollapse-perf.pl"
}

gensvg() {
  "${FLAMEGRAPHDIR}/flamegraph.pl" > "$OUTPUT"
}

if [ "$NOBGTHREAD" -eq 1 ]; then
  collapse | grep -v BGThreadWrapper | gensvg
else
  collapse | gensvg
fi
