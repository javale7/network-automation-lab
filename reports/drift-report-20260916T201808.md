# Configuration drift report

Generated: 2026-09-16 20:19 UTC

Devices checked: 2 | Lines added: 2 | Lines removed: 0

## Verdict

**DRIFT DETECTED** on r1

## r1 — DRIFT DETECTED (+2/-0)

```diff
--- r1 (baseline)
+++ r1 (current)
@@ -5,3 +5,5 @@
 set 0 name=serial0
 /ip dhcp-client
 add interface=ether1
+/system identity
+set name=r1-lab-demo
```

## r2 — clean, no changes vs baseline.
