#!/bin/bash
#
# Sync remote and local logs

set -eu

if [ $# -ne 1 ]; then
  echo "usage: $0 HOST"
fi

pushd ~/logs &>/dev/null
rsync -avz "$1:logs" .
popd &>/dev/null
