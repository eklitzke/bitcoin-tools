#!/bin/bash
#
# Script to reindex bitcoind, in a format suitable for the exploration Python
# scripts I have here. Somewhat specific to my setup.

set -eu

if [ ! -d ~/logs ]; then
  mkdir ~/logs
fi
OUTFILE="$HOME/logs/$(hostname -s)-$(date '+%s').log"

sep() {
  if [ $# -ne 1 ]; then
    return 1
  fi
  echo "--- $1" >> "$OUTFILE"
}

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
echo

append() {
  echo "$@" >> "$OUTFILE"
}

# increase our fd limits (needed in the leveldb_tweaks branch)
ulimit -Sn "$(ulimit -Hn)"

echo "--- system" > "$OUTFILE"
append "date $(date -u --iso-8601=seconds)"
append "hostname $(hostname -s)"
append "uname $(uname -r)"
append "memtotal:bytes $(grep 'MemTotal.*kB' /proc/meminfo | awk '{print $2*1024}')"
append "fdlimit:count $(ulimit -Sn)"
pushd "$BITCOINDIR" &>/dev/null
append "git:commit $(git rev-parse HEAD)"
append "git:branch $(git rev-parse --abbrev-ref HEAD)"
popd &>/dev/null

sep config
cat ~/.bitcoin/bitcoin.conf >> "$OUTFILE"

wait_for_finish() {
  while true; do
    if tac "$OUTFILE" | head -n 1 | grep -q ^finish; then
      killall bitcoind
      return
    fi
    sleep 10
  done
}


# zero the log file
if [ -f ~/.bitcoin/testnet3/debug.log ]; then
  rm -f ~/.bitcoin/testnet3/debug.log
fi

sep systemtap
stap -c "$BITCOIND -reindex-chainstate" "$SCRIPT" | tee -a "$OUTFILE" &
wait_for_finish &
trap 'kill %1' INT
wait
