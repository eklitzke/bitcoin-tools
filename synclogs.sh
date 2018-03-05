#!/bin/bash
#
# Sync remote and local logs

set -eu

VERBOSE=0
while getopts ":vx" opt; do
  case $opt in
    v) VERBOSE=1 ;;
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

mkdirs() {
  for d in ~/logs ~/.profiles; do
    if [ ! -d "$d" ]; then
      mkdir "$d"
    fi
  done
}

do_rsync() {
  OPTS=(-az)
  if [ "$VERBOSE" -eq 1 ]; then
    OPTS+=(-v)
  fi
  rsync "${OPTS[@]}" "$@"
}

synchosts() {
  mkdirs
  for h in "$@"; do
    do_rsync "$h:logs/" ~/logs/ &
    do_rsync "$h:.profiles/" ~/.profiles/ &
  done
  wait
}

if [ $# -eq 0 ]; then
  synchosts core leveldb
else
  synchosts "$@"
fi
