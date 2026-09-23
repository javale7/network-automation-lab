# Network Automation Lab — Backup & Config Drift Audit

Automated configuration backup and drift detection for MikroTik RouterOS,
built with Ansible and Python. Every change on the network gets caught —
and proven with an audit trail.

## The problem

In ISP operations, silent config changes are the #1 cause of "it worked
yesterday" outages. Manual backups are forgotten, and nobody notices when a
device's running config no longer matches the approved baseline — until
something breaks at 2am.

## What this does

1. **Backs up** every router's full config on demand (`ansible/backup.yml`).
2. **Snapshots a baseline** of the approved configuration (`baselines/`).
3. **Audits for drift** — a Python script diffs current configs against
   baselines and produces a human-readable report with exit codes a CI
   pipeline can act on (`scripts/config_diff.py`).

Run the full demo with one command:

```bash
./demo.sh
```

It backs up both routers, records baselines, applies a small change on one
router, re-backs up, and runs the audit. A sample report lives in
`reports/drift-report-20260916T201808.md` — the audit correctly flagged the
single changed router (`r1`) while confirming the other (`r2`) was clean.

## The lab

- Two emulated MikroTik CHR routers (RouterOS 7.19.4), booted with QEMU
  (`lab/bringup.sh`); a containerlab topology is included for Docker hosts
  (`lab/topology.clab.yml`).
- Full run logs and reports are stored under `evidence/` and `reports/`,
  so every demo is reproducible.

## Stack

Ansible (community.routeros) · Python 3 · MikroTik RouterOS API · QEMU /
containerlab · Bash

## Skills demonstrated

Device automation over SSH/API, idempotent Ansible playbooks, Python-based
config diffing and reporting, and audit-ready evidence handling — the core
toolkit of a NetDevOps workflow.
