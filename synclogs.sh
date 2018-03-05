#!/bin/bash
#
# Sync remote and local logs

set -eu

synchosts() {
  pushd ~/logs &>/dev/null
  for h in "$@"; do
    rsync -avz "$h:logs/" . &
  done
  popd &>/dev/null
  wait
}

if [ $# -eq 0 ]; then
  synchosts core leveldb
else
  synchosts "$@"
fi
