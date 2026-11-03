# Example run (offline mock models)

`mock:naive` and `mock:robust` are deterministic pipeline stand-ins, not language models. The
numbers here only show what the report looks like; they say nothing about real models.

Reproduce (about 23,000 calls, a few seconds, no keys needed):

```bash
notamper run --models mock:naive,mock:robust --defenses none,guard,spotlight,filter,approval \
  --reps 2 --out results/ex
notamper report results/ex      # then copy report.md, report.html, manifest.json here
```

Only the run timestamps differ between reproductions.
