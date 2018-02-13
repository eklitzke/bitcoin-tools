#!/bin/bash

set -eu

FILE=""
declare -i NUMTIMES=3

while getopts ":f:n:" opt; do
  case $opt in
    f)
      FILE="$OPTARG"
      ;;
    n)
      NUMTIMES="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

sep() {
  echo "--------" >> "$FILE"
}

GITREV=$(git -C ~/bitcoin rev-parse HEAD)

if [ -z "$FILE" ]; then
  mkdir -p ~/bench
  FILE="$HOME/bench/${GITREV}.txt"
fi

echo "$GITREV" > "$FILE"
sep
cat ~/.bitcoin/bitcoin.conf >> "$FILE"
sep

for ((i=0; i < "$NUMTIMES"; i++)); do
  date --iso-8601=seconds >> "$FILE"
  { time ./bitcoin/src/bitcoind -reindex-chainstate; } 2>&1 | tee -a "$FILE"
  sep
done
