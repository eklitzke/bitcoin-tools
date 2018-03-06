#!/bin/bash
#
# Script to reindex bitcoind, in a format suitable for the exploration Python
# scripts I have here. Somewhat specific to my setup.

set -eu

COMMENT=
while getopts ":m:" opt; do
  case $opt in
    m)
      COMMENT="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

if [ -z "$COMMENT" ];then
  echo "Error: no comment!"
  exit 1
fi

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

BITCOINDIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")"/../bitcoin)
if [ ! -d "$BITCOINDIR" ]; then
  echo "no bitcoindir"
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
append "comment \"$COMMENT\""
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
pushd "${BITCOINDIR}" &>/dev/null
PATH="$PWD/src:$PATH"
stap -I share/systemtap/tapset -c "bitcoind -reindex-chainstate -debug=leveldb" share/systemtap/cache.stp | tee -a "$OUTFILE" &
popd &>/dev/null
wait_for_finish &
trap 'kill %1' INT
wait
