#!/usr/bin/env bash
# destroy.sh — Stop the emulated routers and (optionally) delete their disks.
# Usage: ./lab/destroy.sh [--wipe]   (--wipe also removes the per-node disks)
set -euo pipefail

RUN_DIR="${RUN_DIR:-/tmp/netlab-qemu}"

for name in r1 r2; do
  pidfile="$RUN_DIR/qemu-$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "[$name] stopping (pid $pid)..."
      kill "$pid"
      for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  fi
done

if [[ "${1:-}" == "--wipe" ]]; then
  rm -f "$RUN_DIR"/r1.vmdk "$RUN_DIR"/r2.vmdk
  echo "Node disks wiped."
fi
echo "Lab stopped."
