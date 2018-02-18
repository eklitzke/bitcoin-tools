#!/bin/bash
#
# Script to reindex bitcoind, in a format suitable for the exploration Python
# scripts I have here. Somewhat specific to my setup.

set -eu

if [ ! -d ~/logs ]; then
  mkdir ~/logs
fi
OUTFILE="$HOME/logs/$(hostname -s)-$(date '+%s').log"

sep() { echo "---" >> "$OUTFILE"; }

SCRIPTDIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
SCRIPT="$SCRIPTDIR/cache.stp"

if [ ! -f "$SCRIPT" ]; then
  echo "no cache.stp script!"
  exit 1
fi

BITCOINDIR=$(realpath "$SCRIPTDIR"/../bitcoin)
BITCOIND="$BITCOINDIR/src/bitcoind"

if [ ! -d "$BITCOINDIR" ] || [ ! -x "$BITCOIND" ]; then
  echo "failed to find bitcoind"
  exit 1
fi

echo "sending log output to $OUTFILE"

pushd "$BITCOINDIR" &>/dev/null
git rev-parse HEAD > "$OUTFILE"
sep
popd &>/dev/null

cat ~/.bitcoin/bitcoin.conf >> "$OUTFILE"
sep
stap -c "$BITCOIND -reindex-chainstate" "$SCRIPT" | tee -a "$OUTFILE"
