#!/bin/bash
#
# Sync remote and local logs

if [ $# -ne 1 ]; then
  echo "usage: $0 HOST"
fi

pushd ~/logs &>/dev/null
rsync "$1:logs/" .
popd &>/dev/null
