#!/usr/bin/env bash
# demo.sh — End-to-end demo of the backup + drift-audit pipeline.
#
# Flow:
#   1. Back up both routers (Ansible -> backups/)
#   2. Snapshot baselines (baselines/)
#   3. Apply one small demo change on r1 (Ansible)
#   4. Back up again
#   5. Run the Python drift audit -> reports/drift-report-<ts>.md
#
# All console output is mirrored into evidence/<timestamp>/ so the run
# is reproducible and auditable.
#
# Prerequisites: lab routers up (./lab/bringup.sh), Ansible + collections
# installed (ansible/requirements.yml), Python 3.
set -uo pipefail

cd "$(dirname "$0")"
export ANSIBLE_CONFIG="$PWD/ansible/ansible.cfg"
TS=$(date +%Y%m%dT%H%M%S)
EVIDENCE="evidence/$TS"
mkdir -p "$EVIDENCE" reports

pass=0; fail=0
step() { echo; echo "==> [$1] $2"; }

step "1/5" "Backing up current configurations..."
if ansible-playbook -i ansible/inventory.yml ansible/backup.yml 2>&1 | tee "$EVIDENCE/01-backup.log"; then
  pass=$((pass+1)); else fail=$((fail+1)); echo "BACKUP FAILED"; fi

step "2/5" "Recording baselines..."
for h in r1 r2; do cp "backups/$h.rsc" "baselines/$h.rsc"; done
echo "baselines written for r1 r2"

step "3/5" "Applying demo change on r1..."
if ansible-playbook -i ansible/inventory.yml ansible/test_change.yml --limit r1 2>&1 | tee "$EVIDENCE/02-test-change.log"; then
  pass=$((pass+1)); else fail=$((fail+1)); echo "TEST CHANGE FAILED"; fi

step "4/5" "Re-backing up after the change..."
if ansible-playbook -i ansible/inventory.yml ansible/backup.yml 2>&1 | tee "$EVIDENCE/03-backup-after-change.log"; then
  pass=$((pass+1)); else fail=$((fail+1)); echo "RE-BACKUP FAILED"; fi

step "5/5" "Running drift audit..."
set +e
python3 scripts/config_diff.py --baselines baselines --current backups \
  --output "reports/drift-report-$TS.md" 2>&1 | tee "$EVIDENCE/04-drift-audit.log"
drift_rc=$?
set -u
cp "reports/drift-report-$TS.md" "$EVIDENCE/drift-report.md"
if [[ $drift_rc -eq 1 ]]; then
  echo "Drift detected as expected (exit 1 = drift found)."
  pass=$((pass+1))
else
  echo "UNEXPECTED: drift audit exit code $drift_rc (expected 1)"
  fail=$((fail+1))
fi

echo
echo "==================================="
echo "Demo finished: $pass steps ok, $fail failed."
echo "Evidence: $EVIDENCE"
echo "==================================="
[[ $fail -eq 0 ]]
