#!/bin/bash

SRC=$(dirname ${BASH_SOURCE[0]})
SCRIPT="$SRC/cache.stp"

if [ ! -f "$SCRIPT" ]; then
  echo "no script!"
  exit 1
fi

BITCOIND=$(dirname ${BASH_SOURCE[0]})/../bitcoin/src/bitcoind

if [ ! -x "$BITCOIND" ]; then
  echo "no bitcoind!"
  exit 1
fi

stap -c "$BITCOIND -reindex-chainstate" "$SCRIPT" | tee ~/"$(hostname -s)-$(date '+%s').log"
