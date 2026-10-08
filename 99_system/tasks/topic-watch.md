# Task spec — topic watch

_Kernel. A host's scheduled prompt for this task is exactly one line:_

> Read `99_system/tasks/topic-watch.md` in the connected folder and follow it.

- **When**: weekly (suggested Monday 08:00 local time), or when the owner says "watch my topics".
- **Needs the local folder**: yes — **device-bound** (see `morning-brief.md`). It also needs the host's search tool; without one, the task stops and says so.
- **Does**: follow `99_system/skills/topic-watch/SKILL.md` — for each due topic in a project's `watch.md`, one search, one result note.
- **Writes**: one `05_results/YYYY-MM/<date>_<slug>-watch.md` per due topic (`claim: sourced`, `trust: untrusted`), the `last_run` line of that `watch.md`, one INDEX line per result, one commit.
- **Idempotent**: yes — a topic whose result for today exists is skipped; a second run the same day changes nothing.
- **If it fails**: nothing half-written matters — a result note is complete or absent; the owner runs "watch my topics" by hand.
