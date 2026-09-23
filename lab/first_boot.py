#!/usr/bin/env python3
"""first_boot.py — One-time provisioning for lab CHR nodes.

Fresh RouterOS 7.x does two things on first SSH login that break automation:
  1. asks "Do you want to see the software license? [Y/n]:"
  2. forces an admin password change ("Change your password / new password>")

This script answers both (declines the license, sets the lab password) so
that later logins — including Ansible's — land straight on the command prompt.

Idempotent: if a login with the lab password already reaches a command
prompt, the node is left untouched.

Lab-only credential. See NOTES.md. Requires: paramiko (pip install paramiko).
Usage: python3 lab/first_boot.py
"""

import re
import sys
import time

import paramiko

LAB_USER = "admin"
LAB_PASS = "netlab123"  # lab-only; never use for real devices
NODES = [("r1", 2222), ("r2", 2223)]
PROMPT_RE = re.compile(rb"\[[^\]]*@.*\] ?> ?$")


def already_provisioned(port):
    """True if we can log in with the lab password and get a prompt."""
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(
            "127.0.0.1", port=port, username=LAB_USER, password=LAB_PASS,
            look_for_keys=False, allow_agent=False, timeout=20,
        )
        ch = c.invoke_shell(width=200, height=50)
        ch.settimeout(5)
        buf = b""
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                chunk = ch.recv(4096)
            except Exception:
                chunk = b""
            if chunk:
                buf += chunk
                for seq, ans in ((b"\x1bZ", b"\x1b/Z"), (b"\x1b[c", b"\x1b[?1;2c"),
                                  (b"\x1b[6n", b"\x1b[200;80R")):
                    while seq in buf:
                        ch.send(ans)
                        buf = buf.replace(seq, b"", 1)
                if PROMPT_RE.search(buf):
                    c.close()
                    return True
            time.sleep(0.3)
        c.close()
    except Exception:
        pass
    return False


def provision(port):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        "127.0.0.1", port=port, username=LAB_USER, password="",
        look_for_keys=False, allow_agent=False, timeout=20,
    )
    ch = c.invoke_shell(width=200, height=50)
    ch.settimeout(5)
    buf = b""
    pw_sent = 0
    deadline = time.time() + 240
    while time.time() < deadline:
        try:
            chunk = ch.recv(8192)
        except Exception:
            chunk = b""
        if chunk:
            buf += chunk
            for seq, ans in ((b"\x1bZ", b"\x1b/Z"), (b"\x1b[c", b"\x1b[?1;2c"),
                              (b"\x1b[6n", b"\x1b[200;80R")):
                while seq in buf:
                    ch.send(ans)
                    buf = buf.replace(seq, b"", 1)
            if b"software license? [Y/n]:" in buf:
                ch.send(b"n")
                buf = b""
                continue
            # "new password>" then "repeat new password>"
            if buf[-60:].rstrip().endswith(b"password>"):
                ch.send(LAB_PASS.encode() + b"\n")
                pw_sent += 1
                buf = b""
                continue
            if pw_sent >= 2 and PROMPT_RE.search(buf):
                c.close()
                return True
        time.sleep(0.3)
    c.close()
    return False


def main():
    rc = 0
    for name, port in NODES:
        if already_provisioned(port):
            print(f"[{name}] already provisioned, skipping")
            continue
        print(f"[{name}] first boot: declining license, setting lab password...")
        if provision(port) and already_provisioned(port):
            print(f"[{name}] provisioned OK")
        else:
            print(f"[{name}] PROVISIONING FAILED")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
