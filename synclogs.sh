#!/bin/bash
#
# Sync remote and local logs

set -eu

if [ $# -lt 1 ]; then
  echo "usage: $0 HOST..."
fi

pushd ~/logs &>/dev/null
for h in "$@"; do
  rsync -az "$h:logs/" . &
done
popd &>/dev/null
wait
