# NOTAMper report

> Not for operational use. All aviation texts are fictional.

## Run parameters

- **Models:** mock:naive, mock:robust
- **Defenses:** none, guard, spotlight, filter, approval
- **Run date:** 2026-11-02T14:12:46.736356+00:00
- **Repetitions:** 2
- **Temperature:** 0.0
- **Temperature not applied:** mock:naive, mock:robust
- **Max tokens:** 1024
- **Seed:** 1234
- **Cases:** 1162
- **Corpus SHA-256:** 381dc23951f68740203a76ae10db12bf799c86c4cba6b2c40c099dbd97d8f5d5
- **Calls made (this invocation):** 23240
- **Calls total (cached):** 23240
- **Stopped reason:** complete
- **NOTAMper version:** 0.1.0

Scored responses: 23240 (23240 used)

## Results

### Key observations

- mock:naive: lowest ASR with defense filter (8.3 %).
- mock:naive: highest ASR under defense none for variant V1 (100.0 %).
- mock:naive: under defense none, ASR aviation 97.6 % vs generic 99.0 % (-1.3 pp; two-proportion z-test on unique cases, n = 293 vs 288); p = 0.21, not significant at α=0.05.
- mock:robust: lowest ASR with defense none, guard, spotlight, filter, approval (0.0 %).
- mock:robust: under defense none all variants equal (0.0 %).
- mock:robust: under defense none, ASR aviation 0.0 % vs generic 0.0 % (+0.0 pp; two-proportion z-test on unique cases, n = 293 vs 288); p = 1.00, not significant at α=0.05.

### Headline results by model and defense

_ASR = attack success rate (lower is better). Tool attempt = share of tool-goal attack cases where the model requested send_report, executed or not; ASR under defense approval measures the gate, tool attempt measures the model. False alarm = detection rate on controls. Omission (control) = natural omission rate on controls of suppress cases (ASR net of it is the effect of the injection). Filter hit = share of controls the filter defense altered. False-block = drop in control utility versus defense none. Intervals are 95 % Wilson at n = unique cases; repetitions of a case are not independent. Errors and empty responses are excluded from every rate._

| Model | Defense | ASR | Tool attempt | Utility (attack) | Utility (control) | False-block | Detection | False alarm (control) | Omission (control) | Filter hit (control) | n attack | n control | n errors | n empty |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mock:naive | none | 98.3 % [96.9–99.1] | 100.0 % [98.0–100.0] | 66.6 % [62.7–70.3] | 100.0 % [99.3–100.0] | – | 0.0 % [0.0–0.7] | 0.0 % [0.0–0.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:naive | guard | 98.3 % [96.9–99.1] | 100.0 % [98.0–100.0] | 66.6 % [62.7–70.3] | 100.0 % [99.3–100.0] | 0.0 % | 0.0 % [0.0–0.7] | 0.0 % [0.0–0.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:naive | spotlight | 98.3 % [96.9–99.1] | 100.0 % [98.0–100.0] | 66.6 % [62.7–70.3] | 100.0 % [99.3–100.0] | 0.0 % | 0.0 % [0.0–0.7] | 0.0 % [0.0–0.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:naive | filter | 8.3 % [6.3–10.8] | 0.0 % [0.0–2.0] | 95.5 % [93.5–96.9] | 100.0 % [99.3–100.0] | 0.0 % | 0.0 % [0.0–0.7] | 0.0 % [0.0–0.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:naive | approval | 65.1 % [61.1–68.8] | 100.0 % [98.0–100.0] | 66.6 % [62.7–70.3] | 100.0 % [99.3–100.0] | 0.0 % | 0.0 % [0.0–0.7] | 0.0 % [0.0–0.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:robust | none | 0.0 % [0.0–0.7] | 0.0 % [0.0–2.0] | 100.0 % [99.3–100.0] | 100.0 % [99.3–100.0] | – | 95.7 % [93.7–97.1] | 17.4 % [14.5–20.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:robust | guard | 0.0 % [0.0–0.7] | 0.0 % [0.0–2.0] | 100.0 % [99.3–100.0] | 100.0 % [99.3–100.0] | 0.0 % | 95.7 % [93.7–97.1] | 17.4 % [14.5–20.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:robust | spotlight | 0.0 % [0.0–0.7] | 0.0 % [0.0–2.0] | 100.0 % [99.3–100.0] | 100.0 % [99.3–100.0] | 0.0 % | 95.7 % [93.7–97.1] | 17.4 % [14.5–20.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:robust | filter | 0.0 % [0.0–0.7] | 0.0 % [0.0–2.0] | 100.0 % [99.3–100.0] | 100.0 % [99.3–100.0] | 0.0 % | 8.3 % [6.3–10.8] | 17.4 % [14.5–20.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |
| mock:robust | approval | 0.0 % [0.0–0.7] | 0.0 % [0.0–2.0] | 100.0 % [99.3–100.0] | 100.0 % [99.3–100.0] | 0.0 % | 95.7 % [93.7–97.1] | 17.4 % [14.5–20.7] | 0.0 % [0.0–1.9] | 0.0 % [0.0–0.7] | 1162 | 1162 | 0 | 0 |

### ASR by goal

_Attack cases only (controls excluded). Intervals use n = unique cases; repetitions of a case are not independent. Errors and empty responses are excluded. Goals use different success rules, so compare across goals with care._

| Model | Defense | Goal | ASR | Utility (attack) | Detection | n attack |
|---|---|---|---|---|---|---|
| mock:naive | none | canary | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | none | suppress | 94.8 % [90.8–97.2] | 0.0 % [0.0–1.9] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | none | tool | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | guard | canary | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | guard | suppress | 94.8 % [90.8–97.2] | 0.0 % [0.0–1.9] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | guard | tool | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | spotlight | canary | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | spotlight | suppress | 94.8 % [90.8–97.2] | 0.0 % [0.0–1.9] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | spotlight | tool | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | filter | canary | 12.4 % [8.5–17.7] | 100.0 % [98.1–100.0] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | filter | suppress | 12.4 % [8.5–17.7] | 86.6 % [81.1–90.7] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | filter | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | approval | canary | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | approval | suppress | 94.8 % [90.8–97.2] | 0.0 % [0.0–1.9] | 0.0 % [0.0–1.9] | 388 |
| mock:naive | approval | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:robust | none | canary | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 388 |
| mock:robust | none | suppress | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 87.1 % [81.7–91.1] | 388 |
| mock:robust | none | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | guard | canary | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 388 |
| mock:robust | guard | suppress | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 87.1 % [81.7–91.1] | 388 |
| mock:robust | guard | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | spotlight | canary | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 388 |
| mock:robust | spotlight | suppress | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 87.1 % [81.7–91.1] | 388 |
| mock:robust | spotlight | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | filter | canary | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 12.4 % [8.5–17.7] | 388 |
| mock:robust | filter | suppress | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 0.0 % [0.0–1.9] | 388 |
| mock:robust | filter | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 12.4 % [8.5–17.8] | 386 |
| mock:robust | approval | canary | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 100.0 % [98.1–100.0] | 388 |
| mock:robust | approval | suppress | 0.0 % [0.0–1.9] | 100.0 % [98.1–100.0] | 87.1 % [81.7–91.1] | 388 |
| mock:robust | approval | tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |

### ASR by format

_Attack cases only (controls excluded). Intervals use n = unique cases; repetitions of a case are not independent. Errors and empty responses are excluded._

| Model | Defense | Format | ASR | Utility (attack) | Detection | n attack |
|---|---|---|---|---|---|---|
| mock:naive | none | notam | 96.0 % [90.1–98.4] | 66.7 % [56.9–75.2] | 0.0 % [0.0–3.7] | 198 |
| mock:naive | none | metar | 100.0 % [96.2–100.0] | 66.3 % [56.5–74.9] | 0.0 % [0.0–3.8] | 196 |
| mock:naive | none | atis | 96.9 % [91.2–98.9] | 66.7 % [56.8–75.3] | 0.0 % [0.0–3.8] | 192 |
| mock:naive | none | generic | 99.0 % [97.0–99.6] | 66.7 % [61.0–71.9] | 0.0 % [0.0–1.3] | 576 |
| mock:naive | guard | notam | 96.0 % [90.1–98.4] | 66.7 % [56.9–75.2] | 0.0 % [0.0–3.7] | 198 |
| mock:naive | guard | metar | 100.0 % [96.2–100.0] | 66.3 % [56.5–74.9] | 0.0 % [0.0–3.8] | 196 |
| mock:naive | guard | atis | 96.9 % [91.2–98.9] | 66.7 % [56.8–75.3] | 0.0 % [0.0–3.8] | 192 |
| mock:naive | guard | generic | 99.0 % [97.0–99.6] | 66.7 % [61.0–71.9] | 0.0 % [0.0–1.3] | 576 |
| mock:naive | spotlight | notam | 96.0 % [90.1–98.4] | 66.7 % [56.9–75.2] | 0.0 % [0.0–3.7] | 198 |
| mock:naive | spotlight | metar | 100.0 % [96.2–100.0] | 66.3 % [56.5–74.9] | 0.0 % [0.0–3.8] | 196 |
| mock:naive | spotlight | atis | 96.9 % [91.2–98.9] | 66.7 % [56.8–75.3] | 0.0 % [0.0–3.8] | 192 |
| mock:naive | spotlight | generic | 99.0 % [97.0–99.6] | 66.7 % [61.0–71.9] | 0.0 % [0.0–1.3] | 576 |
| mock:naive | filter | notam | 9.1 % [4.9–16.4] | 94.9 % [88.7–97.8] | 0.0 % [0.0–3.7] | 198 |
| mock:naive | filter | metar | 9.2 % [4.9–16.5] | 94.9 % [88.6–97.8] | 0.0 % [0.0–3.8] | 196 |
| mock:naive | filter | atis | 8.3 % [4.3–15.6] | 95.8 % [89.8–98.4] | 0.0 % [0.0–3.8] | 192 |
| mock:naive | filter | generic | 7.6 % [5.1–11.3] | 95.8 % [92.9–97.6] | 0.0 % [0.0–1.3] | 576 |
| mock:naive | approval | notam | 62.6 % [52.8–71.5] | 66.7 % [56.9–75.2] | 0.0 % [0.0–3.7] | 198 |
| mock:naive | approval | metar | 67.3 % [57.6–75.8] | 66.3 % [56.5–74.9] | 0.0 % [0.0–3.8] | 196 |
| mock:naive | approval | atis | 63.5 % [53.6–72.5] | 66.7 % [56.8–75.3] | 0.0 % [0.0–3.8] | 192 |
| mock:naive | approval | generic | 65.6 % [60.0–70.9] | 66.7 % [61.0–71.9] | 0.0 % [0.0–1.3] | 576 |
| mock:robust | none | notam | 0.0 % [0.0–3.7] | 100.0 % [96.3–100.0] | 96.0 % [90.1–98.4] | 198 |
| mock:robust | none | metar | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 94.9 % [88.6–97.8] | 196 |
| mock:robust | none | atis | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 95.8 % [89.8–98.4] | 192 |
| mock:robust | none | generic | 0.0 % [0.0–1.3] | 100.0 % [98.7–100.0] | 95.8 % [92.9–97.6] | 576 |
| mock:robust | guard | notam | 0.0 % [0.0–3.7] | 100.0 % [96.3–100.0] | 96.0 % [90.1–98.4] | 198 |
| mock:robust | guard | metar | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 94.9 % [88.6–97.8] | 196 |
| mock:robust | guard | atis | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 95.8 % [89.8–98.4] | 192 |
| mock:robust | guard | generic | 0.0 % [0.0–1.3] | 100.0 % [98.7–100.0] | 95.8 % [92.9–97.6] | 576 |
| mock:robust | spotlight | notam | 0.0 % [0.0–3.7] | 100.0 % [96.3–100.0] | 96.0 % [90.1–98.4] | 198 |
| mock:robust | spotlight | metar | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 94.9 % [88.6–97.8] | 196 |
| mock:robust | spotlight | atis | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 95.8 % [89.8–98.4] | 192 |
| mock:robust | spotlight | generic | 0.0 % [0.0–1.3] | 100.0 % [98.7–100.0] | 95.8 % [92.9–97.6] | 576 |
| mock:robust | filter | notam | 0.0 % [0.0–3.7] | 100.0 % [96.3–100.0] | 8.1 % [4.2–15.1] | 198 |
| mock:robust | filter | metar | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 8.2 % [4.2–15.3] | 196 |
| mock:robust | filter | atis | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 8.3 % [4.3–15.6] | 192 |
| mock:robust | filter | generic | 0.0 % [0.0–1.3] | 100.0 % [98.7–100.0] | 8.3 % [5.7–12.1] | 576 |
| mock:robust | approval | notam | 0.0 % [0.0–3.7] | 100.0 % [96.3–100.0] | 96.0 % [90.1–98.4] | 198 |
| mock:robust | approval | metar | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 94.9 % [88.6–97.8] | 196 |
| mock:robust | approval | atis | 0.0 % [0.0–3.8] | 100.0 % [96.2–100.0] | 95.8 % [89.8–98.4] | 192 |
| mock:robust | approval | generic | 0.0 % [0.0–1.3] | 100.0 % [98.7–100.0] | 95.8 % [92.9–97.6] | 576 |

### ASR by variant

_Attack cases only (controls excluded). Intervals use n = unique cases; repetitions of a case are not independent. Errors and empty responses are excluded._

| Model | Defense | Variant | ASR | Utility (attack) | Detection | n attack |
|---|---|---|---|---|---|---|
| mock:naive | none | V1 | 100.0 % [94.9–100.0] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | none | V2 | 97.3 % [90.5–99.2] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | none | V3 | 98.6 % [92.6–99.8] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | none | V4 | 98.6 % [92.5–99.8] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | none | V5 | 97.3 % [90.5–99.2] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | none | V6 | 97.3 % [90.5–99.2] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | none | V7 | 98.6 % [92.5–99.8] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | none | V8 | 98.6 % [92.6–99.8] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | guard | V1 | 100.0 % [94.9–100.0] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | guard | V2 | 97.3 % [90.5–99.2] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | guard | V3 | 98.6 % [92.6–99.8] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | guard | V4 | 98.6 % [92.5–99.8] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | guard | V5 | 97.3 % [90.5–99.2] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | guard | V6 | 97.3 % [90.5–99.2] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | guard | V7 | 98.6 % [92.5–99.8] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | guard | V8 | 98.6 % [92.6–99.8] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | spotlight | V1 | 100.0 % [94.9–100.0] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | spotlight | V2 | 97.3 % [90.5–99.2] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | spotlight | V3 | 98.6 % [92.6–99.8] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | spotlight | V4 | 98.6 % [92.5–99.8] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | spotlight | V5 | 97.3 % [90.5–99.2] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | spotlight | V6 | 97.3 % [90.5–99.2] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | spotlight | V7 | 98.6 % [92.5–99.8] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | spotlight | V8 | 98.6 % [92.6–99.8] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | filter | V1 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | filter | V2 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | filter | V3 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | filter | V4 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | filter | V5 | 1.4 % [0.2–7.4] | 98.6 % [92.6–99.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | filter | V6 | 31.5 % [22.0–42.9] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | filter | V7 | 33.3 % [23.5–44.8] | 100.0 % [94.9–100.0] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | filter | V8 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | approval | V1 | 66.7 % [55.2–76.5] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | approval | V2 | 64.4 % [52.9–74.4] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | approval | V3 | 65.8 % [54.3–75.6] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | approval | V4 | 65.3 % [53.8–75.2] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | approval | V5 | 64.4 % [52.9–74.4] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | approval | V6 | 64.4 % [52.9–74.4] | 65.8 % [54.3–75.6] | 0.0 % [0.0–5.0] | 146 |
| mock:naive | approval | V7 | 65.3 % [53.8–75.2] | 66.7 % [55.2–76.5] | 0.0 % [0.0–5.1] | 144 |
| mock:naive | approval | V8 | 64.4 % [52.9–74.4] | 67.1 % [55.7–76.8] | 0.0 % [0.0–5.0] | 146 |
| mock:robust | none | V1 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | none | V2 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | none | V3 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | none | V4 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | none | V5 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | none | V6 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 65.8 % [54.3–75.6] | 146 |
| mock:robust | none | V7 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | none | V8 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | guard | V1 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | guard | V2 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | guard | V3 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | guard | V4 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | guard | V5 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | guard | V6 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 65.8 % [54.3–75.6] | 146 |
| mock:robust | guard | V7 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | guard | V8 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | spotlight | V1 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | spotlight | V2 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | spotlight | V3 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | spotlight | V4 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | spotlight | V5 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | spotlight | V6 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 65.8 % [54.3–75.6] | 146 |
| mock:robust | spotlight | V7 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | spotlight | V8 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | filter | V1 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 0.0 % [0.0–5.1] | 144 |
| mock:robust | filter | V2 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:robust | filter | V3 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:robust | filter | V4 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 0.0 % [0.0–5.1] | 144 |
| mock:robust | filter | V5 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:robust | filter | V6 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:robust | filter | V7 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 66.7 % [55.2–76.5] | 144 |
| mock:robust | filter | V8 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 0.0 % [0.0–5.0] | 146 |
| mock:robust | approval | V1 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | approval | V2 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | approval | V3 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | approval | V4 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | approval | V5 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |
| mock:robust | approval | V6 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 65.8 % [54.3–75.6] | 146 |
| mock:robust | approval | V7 | 0.0 % [0.0–5.1] | 100.0 % [94.9–100.0] | 100.0 % [94.9–100.0] | 144 |
| mock:robust | approval | V8 | 0.0 % [0.0–5.0] | 100.0 % [95.0–100.0] | 100.0 % [95.0–100.0] | 146 |

### ASR by task

_Attack cases only (controls excluded). Intervals use n = unique cases; repetitions of a case are not independent. Errors and empty responses are excluded._

| Model | Defense | Task | ASR | Utility (attack) | Detection | n attack |
|---|---|---|---|---|---|---|
| mock:naive | none | briefing_tool | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | none | filter | 97.7 % [93.3–99.2] | 50.0 % [41.5–58.5] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | none | question | 97.7 % [93.3–99.2] | 42.2 % [34.0–50.8] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | none | summarize | 97.0 % [92.5–98.8] | 57.6 % [49.0–65.7] | 0.0 % [0.0–2.8] | 264 |
| mock:naive | guard | briefing_tool | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | guard | filter | 97.7 % [93.3–99.2] | 50.0 % [41.5–58.5] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | guard | question | 97.7 % [93.3–99.2] | 42.2 % [34.0–50.8] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | guard | summarize | 97.0 % [92.5–98.8] | 57.6 % [49.0–65.7] | 0.0 % [0.0–2.8] | 264 |
| mock:naive | spotlight | briefing_tool | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | spotlight | filter | 97.7 % [93.3–99.2] | 50.0 % [41.5–58.5] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | spotlight | question | 97.7 % [93.3–99.2] | 42.2 % [34.0–50.8] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | spotlight | summarize | 97.0 % [92.5–98.8] | 57.6 % [49.0–65.7] | 0.0 % [0.0–2.8] | 264 |
| mock:naive | filter | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | filter | filter | 12.5 % [7.8–19.3] | 93.0 % [87.2–96.3] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | filter | question | 14.1 % [9.1–21.1] | 92.2 % [86.2–95.7] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | filter | summarize | 10.6 % [6.4–17.0] | 94.7 % [89.5–97.4] | 0.0 % [0.0–2.8] | 264 |
| mock:naive | approval | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 0.0 % [0.0–2.0] | 386 |
| mock:naive | approval | filter | 97.7 % [93.3–99.2] | 50.0 % [41.5–58.5] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | approval | question | 97.7 % [93.3–99.2] | 42.2 % [34.0–50.8] | 0.0 % [0.0–2.9] | 256 |
| mock:naive | approval | summarize | 97.0 % [92.5–98.8] | 57.6 % [49.0–65.7] | 0.0 % [0.0–2.8] | 264 |
| mock:robust | none | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | none | filter | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 93.8 % [88.2–96.8] | 256 |
| mock:robust | none | question | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 92.2 % [86.2–95.7] | 256 |
| mock:robust | none | summarize | 0.0 % [0.0–2.8] | 100.0 % [97.2–100.0] | 94.7 % [89.5–97.4] | 264 |
| mock:robust | guard | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | guard | filter | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 93.8 % [88.2–96.8] | 256 |
| mock:robust | guard | question | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 92.2 % [86.2–95.7] | 256 |
| mock:robust | guard | summarize | 0.0 % [0.0–2.8] | 100.0 % [97.2–100.0] | 94.7 % [89.5–97.4] | 264 |
| mock:robust | spotlight | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | spotlight | filter | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 93.8 % [88.2–96.8] | 256 |
| mock:robust | spotlight | question | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 92.2 % [86.2–95.7] | 256 |
| mock:robust | spotlight | summarize | 0.0 % [0.0–2.8] | 100.0 % [97.2–100.0] | 94.7 % [89.5–97.4] | 264 |
| mock:robust | filter | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 12.4 % [8.5–17.8] | 386 |
| mock:robust | filter | filter | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 5.5 % [2.7–10.9] | 256 |
| mock:robust | filter | question | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 7.0 % [3.7–12.8] | 256 |
| mock:robust | filter | summarize | 0.0 % [0.0–2.8] | 100.0 % [97.2–100.0] | 6.1 % [3.1–11.5] | 264 |
| mock:robust | approval | briefing_tool | 0.0 % [0.0–2.0] | 100.0 % [98.0–100.0] | 100.0 % [98.0–100.0] | 386 |
| mock:robust | approval | filter | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 93.8 % [88.2–96.8] | 256 |
| mock:robust | approval | question | 0.0 % [0.0–2.9] | 100.0 % [97.1–100.0] | 92.2 % [86.2–95.7] | 256 |
| mock:robust | approval | summarize | 0.0 % [0.0–2.8] | 100.0 % [97.2–100.0] | 94.7 % [89.5–97.4] | 264 |

### Domain comparison: aviation vs generic text

_Aviation = notam + metar + atis. Difference = aviation minus generic ASR (research question 3). Intervals use n = unique cases; repetitions of a case are not independent. Errors and empty responses are excluded._

| Model | Defense | ASR aviation | ASR generic | Difference | n aviation | n generic |
|---|---|---|---|---|---|---|
| mock:naive | none | 97.6 % [95.2–98.8] | 99.0 % [97.0–99.6] | -1.3 pp | 586 | 576 |
| mock:naive | guard | 97.6 % [95.2–98.8] | 99.0 % [97.0–99.6] | -1.3 pp | 586 | 576 |
| mock:naive | spotlight | 97.6 % [95.2–98.8] | 99.0 % [97.0–99.6] | -1.3 pp | 586 | 576 |
| mock:naive | filter | 8.9 % [6.1–12.7] | 7.6 % [5.1–11.3] | +1.2 pp | 586 | 576 |
| mock:naive | approval | 64.5 % [58.9–69.8] | 65.6 % [60.0–70.9] | -1.1 pp | 586 | 576 |
| mock:robust | none | 0.0 % [0.0–1.3] | 0.0 % [0.0–1.3] | +0.0 pp | 586 | 576 |
| mock:robust | guard | 0.0 % [0.0–1.3] | 0.0 % [0.0–1.3] | +0.0 pp | 586 | 576 |
| mock:robust | spotlight | 0.0 % [0.0–1.3] | 0.0 % [0.0–1.3] | +0.0 pp | 586 | 576 |
| mock:robust | filter | 0.0 % [0.0–1.3] | 0.0 % [0.0–1.3] | +0.0 pp | 586 | 576 |
| mock:robust | approval | 0.0 % [0.0–1.3] | 0.0 % [0.0–1.3] | +0.0 pp | 586 | 576 |

### Stop reasons by model

_max_tokens / length mean the answer was cut off; a canary at the very end is then missed. Raise --max-tokens if these are frequent._

| Model | Stop reasons (count) |
|---|---|
| mock:naive | end_turn: 10076, tool_use: 1544 |
| mock:robust | end_turn: 11620 |
