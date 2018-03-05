#!/bin/bash
#
# Sync remote and local logs

set -eu

synchosts() {
  if [ ! -d ~/logs ]; then
    mkdir -p ~/logs
  fi
  if [ ! -d ~/.profiles ]; then
    mkdir -p ~/.profiles
  fi
  for h in "$@"; do
    rsync -avz "$h:logs/" ~/logs/ &
    rsync -avz "$h:.profiles/" ~/.profiles/ &
  done
  wait
}

if [ $# -eq 0 ]; then
  synchosts core leveldb
else
  synchosts "$@"
fi
