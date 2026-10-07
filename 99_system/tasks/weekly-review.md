# Task spec — weekly review

_Kernel. A host's scheduled prompt for this task is exactly one line:_

> Read `99_system/tasks/weekly-review.md` in the connected folder and follow it.

- **When**: Friday afternoon or weekend (suggested Friday 16:00 local time).
- **Needs the local folder**: yes — **device-bound** (see `morning-brief.md` for what that means on cloud-scheduled hosts).
- **Does**: follow `99_system/skills/weekly-review/SKILL.md`.
- **Writes**: only `06_logs/weekly/<YYYY-Www>.md` (and one commit).
- **Idempotent**: yes — a second run only refreshes the Numbers block and never touches judgment sections.
- **If it fails**: the owner runs "weekly review" by hand; the numbers can also come from `aicowork doctor`.
