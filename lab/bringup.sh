#!/usr/bin/env bash
# bringup.sh — Boot two emulated MikroTik CHR routers with QEMU.
#
# Each router gets user-mode (SLIRP) networking with its SSH and API ports
# forwarded to localhost, so Ansible can reach them without any real network:
#
#   r1:  ssh 127.0.0.1:2222   api 127.0.0.1:8728   console telnet 127.0.0.1:5001
#   r2:  ssh 127.0.0.1:2223   api 127.0.0.1:8729   console telnet 127.0.0.1:5002
#
# Usage: ./lab/bringup.sh [path-to-chr.vmdk]
# The CHR image is a free download from https://mikrotik.com/download
# (Cloud Hosted Router, VMDK format).
set -euo pipefail

LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
IMG="${1:-$LAB_DIR/../images/chr.vmdk}"
RUN_DIR="${RUN_DIR:-/tmp/netlab-qemu}"
SSH_WAIT_SECS="${SSH_WAIT_SECS:-600}"

if [[ ! -f "$IMG" ]]; then
  echo "CHR image not found: $IMG"
  echo "Download the CHR VMDK from https://mikrotik.com/download and pass its path."
  exit 1
fi
command -v qemu-system-x86_64 >/dev/null || { echo "qemu-system-x86_64 not installed"; exit 1; }

mkdir -p "$RUN_DIR"

boot_node() {
  local name=$1 ssh_port=$2 api_port=$3 console_port=$4
  local disk="$RUN_DIR/$name.vmdk"
  if [[ ! -f "$disk" ]]; then
    echo "[$name] preparing disk..."
    cp "$IMG" "$disk"
  fi
  if [[ -f "$RUN_DIR/qemu-$name.pid" ]] && kill -0 "$(cat "$RUN_DIR/qemu-$name.pid")" 2>/dev/null; then
    echo "[$name] already running"
    return
  fi
  echo "[$name] booting..."
  qemu-system-x86_64 \
    -name "$name" \
    -machine q35 -cpu qemu64 -m 512 \
    -drive "file=$disk,format=vmdk,if=virtio" \
    -netdev "user,id=net0,hostfwd=tcp:127.0.0.1:$ssh_port-:22,hostfwd=tcp:127.0.0.1:$api_port-:8728" \
    -device virtio-net-pci,netdev=net0 \
    -display none \
    -serial "telnet:127.0.0.1:$console_port,server,nowait" \
    -pidfile "$RUN_DIR/qemu-$name.pid" \
    -daemonize
}

wait_ssh() {
  local name=$1 ssh_port=$2
  echo "[$name] waiting for SSH on 127.0.0.1:$ssh_port ..."
  local deadline=$((SECONDS + SSH_WAIT_SECS))
  while (( SECONDS < deadline )); do
    if python3 -c "
import socket, sys
s = socket.create_connection(('127.0.0.1', $ssh_port), timeout=5)
banner = s.recv(64)
sys.exit(0 if banner.startswith(b'SSH-') else 1)
" 2>/dev/null; then
      echo "[$name] SSH is up"
      return 0
    fi
    sleep 10
  done
  echo "[$name] ERROR: SSH did not come up within $SSH_WAIT_SECS seconds"
  return 1
}

boot_node r1 2222 8728 5001
boot_node r2 2223 8729 5002
wait_ssh r1 2222
wait_ssh r2 2223

# Fresh RouterOS 7.x forces a license prompt + admin password change on
# first login, which breaks automation. Provision once per fresh disk.
if python3 -c "import paramiko" 2>/dev/null; then
  python3 "$LAB_DIR/first_boot.py"
else
  echo "NOTE: paramiko not installed — skipping first-boot provisioning."
  echo "Install it (pip install paramiko) and run: python3 $LAB_DIR/first_boot.py"
fi
echo "Lab is up. Tear down with ./lab/destroy.sh"
