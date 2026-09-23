# Build notes — scenario choice

## Why this scenario

The lab scenario (automated backup + configuration drift audit on MikroTik
RouterOS) was chosen to match the operator profile in the CV and the stated
pivot toward network automation:

- CV: MikroTik MTCNA (2019), multi-year MikroTik/RouterOS field experience
  running an ISP access network (Gandalf Comunicaciones), Cisco CCNP.
- Stated direction: "network automation" with Python and Ansible; currently
  QA Engineer, targeting NetDevOps roles.
- A backup/audit pipeline is the smallest automation project that proves all
  three skills at once: real device interaction (RouterOS API), Ansible
  orchestration, and Python data handling (diff/report).

Alternatives considered: VLAN management and unauthorized-change detection.
Drift audit covers the detection use-case as a subset (any unauthorized change
shows up as drift vs the baseline), so one scenario demonstrates both.

## Lab technology note

The original plan called for containerlab. The build machine's kernel has no
bridge/netfilter support, so Docker networking cannot start there — containerlab
was not viable in that environment. The lab therefore boots the same CHR
images (downloaded from mikrotik.com) directly with QEMU user-mode networking
(`lab/bringup.sh`); SSH/API reachability and the automation flow are identical.
A containerlab topology is still included (`lab/topology.clab.yml`) for anyone
running this on a Docker-capable host.

## Privacy posture

- All automation runs against two emulated RouterOS CHR nodes on a local
  containerlab topology. No production data, no customer data, no real
  credentials anywhere in this repo.
- Lab credentials are a non-secret lab-only default (`admin` / `netlab123`,
  set by `lab/first_boot.py` because fresh RouterOS 7.x forces a password
  change on first login) and are parameterized so real deployments can inject
  their own via Ansible Vault.
