# Task spec — morning brief

_Kernel. A host's scheduled prompt for this task is exactly one line:_

> Read `99_system/tasks/morning-brief.md` in the connected folder and follow it.

- **When**: weekdays, before the owner's first meeting (suggested 07:30 local time).
- **Needs the local folder**: yes — this task is **device-bound**. On a host that runs scheduled prompts in the cloud, it only works while the owner's machine is on and connected; if the host suspends it when the machine is absent, restart it by hand.
- **Does**: follow `99_system/skills/morning-brief/SKILL.md`.
- **Writes**: only `06_logs/daily/<today>.md` (and one commit).
- **Idempotent**: yes — the skill stops if today's Plan is already filled, so a double run or a catch-up run changes nothing.
- **If it fails**: nothing is half-written that matters; the owner runs "morning brief" by hand.
