# IIT Madras — Web M.Tech in AI

My study home base for the IIT Madras Web M.Tech in AI: hour-by-hour tracking,
course notes, assignments, and book-driven self-projects. Public by design — it
doubles as a portfolio and a discipline signal.

See [`AGENTS.md`](./AGENTS.md) for the full strategy and the rules any AI coding
agent should follow in this repo.

## What's here

| Path | What it holds |
|------|---------------|
| `tracking/` | Daily JSON logs (source of truth) + generated summaries |
| `automation/` | Scripts: validate, summarize, chart, and the logging CLI |
| `trimester1/` | Coursework: Python for DS, Mathematics for DS |
| `projects/` | Book-driven self-projects, one folder each |
| `docs/` | Generated GitHub Pages dashboard (read-only) |

## Tracking — how it works

- One JSON file per day in `tracking/data/`, named `YYYY-MM-DD.json`.
- 18 fixed hourly slots (5 AM–11 PM), each with activity, category, energy (1-5).
- A daily signals block: sleep, mood, top derailer, biggest win, notes.
- **Data is the single source of truth.** Summaries, charts, and the dashboard are
  all generated from it — never hand-edited.

### Log a day (laptop)

```bash
python automation/log_cli.py            # today
python automation/log_cli.py 2025-09-18 # a specific date
```

### Validate

```bash
python automation/validate.py                         # all logs
python automation/validate.py tracking/data/2025-09-18.json
```

## Courses (Trimester 1)

- **Python for Data Science**
- **Mathematics for Data Science**

## License

[MIT](./LICENSE)
