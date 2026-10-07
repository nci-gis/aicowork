# Backlog — enhancements with trigger conditions

> Nothing here is built before its trigger fires. Each entry says what to build, the trigger that starts it, and notes on how. It was carried over on 2026-10-03 from the first owner's instance. Owner-specific context was removed, and entries already done are listed at the end.

## Open

### Search without scanning (committed index)

- **Trigger**: an instance passes about 300 `.md` files, **or** an agent session needs more than 30 s to find an item with grep, **or** search is needed where Python cannot run.
- **Today**: there is no committed index. An index is derived data: committing it breaks PHILOSOPHY #1 and churns git on every sync. For the instance sizes seen so far, grep plus `INDEX.md` is enough.
- **When it fires**: add `aicowork index --json`, printed on demand to stdout and never persisted or committed.

### A light framework for the viewer (e.g. VanJS)

- **Trigger**: the viewer needs a drag-and-drop board, optimistic UI, or client state several levels deep. Until then: vanilla JavaScript plus vendored ECharts.

### Local semantic search (embeddings)

- **Trigger**: FTS5 returns poor results on at least 3 real searches (record each failure here), **and** the instance holds more than 200 items.

### Dark mode following the OS

- **Trigger**: a user asks for it. It is pure CSS: `style.css` already uses CSS variables, so one `@media (prefers-color-scheme: dark)` block is enough.

### Capture away from the desk (e-mail to inbox, a chat bot)

- **Trigger**: an owner loses real ideas to missing capture three or more times a week (record each one; a feeling does not count).
- **Constraint**: any channel is egress and a new AI surface, so it is decided in `policy.yaml` first.

### Calendar sync (Outlook / Teams)

- **Trigger**: the viewer's calendar drifts from the real one and makes the owner late for, or miss, at least one meeting.
- **Constraint**: depends on the employer's IT policy; check that before starting.

### Restore drill

- **Trigger**: on a schedule, every quarter (the first is due 2026-11). It is insurance, not an enhancement: rebuild an instance from a backup bundle and from the kernel text alone (REBUILD.md).

### A day without its daily log

- **Trigger**: a scheduled ritual reports success again while the file it should write is missing (first seen 2026-10-02; the tasks were not bound to the computer).
- **When it fires**: `doctor` warns when a weekday in the last week has no `06_logs/daily/` file, naming the dates.

## Done

Built entries leave this file; what was built is in `CHANGELOG.md` and the git history (the last list was removed on 2026-10-03, commit "docs(agents): tidy").
