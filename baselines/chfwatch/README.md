# CHF-Watch — transition-warning reference baseline (multimodal_fusion)

A reference baseline for the `multimodal_fusion` task on **BoilingBench-3/4
(NED3-007)**, contributed by Brad Moore (independent researcher) after
correspondence with the NED3 lab (Prof. Han Hu, June 2026). Scope was agreed
in [issue #1](../../issues/1): AE + hydrophone + thermal features on the
standard 5-surface split; `.cine` video deferred; no new datasets.

The full implementation lives in the standalone repo, **pinned**, not
vendored:

- Standalone repo: <https://gitlab.com/moore.brad.m-group/chf-watch>
- Pinned commit: `b86bf0d`
  ("Refresh E17/E20/E22 tables + fig3 with measured CHF; FAR 0.038 -> 0.040 in E20")
- Install: `pip install "git+https://gitlab.com/moore.brad.m-group/chf-watch.git@b86bf0d"`
- Environment: `environment.yaml` in this directory (Python 3.11, PyTorch
  cu128-nightly for Blackwell/sm_120; see the standalone README for the
  wheel gotcha).

## What the baseline is

`ChfWatchDetector` (in `chfwatch.deploy`) combining four established pieces:

1. a **baseline-relative alarm gate** — wall temperature rising >= 5% above
   its first-20%-of-recording baseline, sustained 12 s;
2. **online conformal calibration** (Gibbs-Candès 2021 ACI) for calibrated
   intervals under domain shift;
3. a **Mahalanobis-on-features OOD flag** to mark windows the model has
   never plausibly seen;
4. **quantile-regression directional bands** to surface asymmetric
   (dangerous / false-alarm) prediction errors.

The synthesis class (alarm + interval + direction + OOD) is the deployment
artifact; the standalone repos's `deploy.py` is unit-tested.
The leakage-safe splits: `time_block`, `group_holdout(level=surface|heat_load)`,
`leave_one_group_out` — all disjoint in group keys, asserted by tests.

## Split files

`splits/ned3-007-lso-surface-<surface>.csv` — one file per held-out surface
(5 surfaces, 2 runs each; train = the other 8 runs). Run ids are the archive
folder tokens (`B69`, `B70`, ...) resolved from `MANIFEST_NED3_007_FILES.csv`;
the mapping and file generation are reproducible with
`scripts/make_ned3_007_lso_splits.py`, and all files pass
`scripts/validate_splits.py` (each run is assigned to exactly one split).

Surfaces = `cu_foam_pH0 (B69/B70)`, `cu_foam_pH10 (B83/B84)`,
`cu_foam_pH12 (B81/B82)`, `polished_cu (B78/B79)`, `microchannel (B114/B119)`.

## Metrics

Folds report heat-flux MAE, conformal PICP, surface recall, false-alarm rate
(FAR), and pre-CHF lead time via `scripts/evaluate_chfwatch.py`, which binds
a split file to the pinned standalone repo's E21 (LSO-calibrated) run and
writes a per-fold JSON record. Intended command:

```
python scripts/evaluate_chfwatch.py \
  --split splits/ned3-007-lso-surface-cu_foam_pH0.csv \
  --manifest MANIFEST_NED3_007_FILES.csv \
  --repo ~/chf-watch --data-root <ned3-007 archive> \
  --cache-root <feature cache> --out results/cu_foam_pH0.json
```

Data lives on the dataset's distribution channels (Zenodo / Hugging Face per
the benchmark release notes); this repo carries no raw data.

## Reported numbers (PROVISIONAL)

Taken from the pinned standalone commit `b86bf0d`; treated as provisional
until independently reproduced by benchmark maintainers.

| Surface | recall | median lead (s) | FAR |
|---|---:|---:|---:|
| cu_foam_pH0 | 1.00 | 35.0 | 0.000 |
| cu_foam_pH10 | 1.00 | 35.0 | 0.000 |
| cu_foam_pH12 | 1.00 | 52.5 | 0.000 |
| polished_cu | 1.00 | 177.5 | 0.250 |
| microchannel | 1.00 | 60.0 | 0.000 |

Aggregate across surfaces: **5/5 recall, median 52.5 s lead, mean FAR 0.050**
(E21, LSO-tuned thresholds). E20 with oracle tuning is tighter overall
(median 45 s lead, FAR 0.038). Per-surface detail, thresholds, and
interpretation are in the standalone repo's
`reports/tables/E21_lso_calibrated_detector.md`.

CHF ground truth used for lead-time/labeling is the **published aggregates**
(Dunlap et al. Table 1 and the dataset's measured values); per-run lab data
(Prof. Hu / Hari Pandey's spreadsheet) remains private and is not included.
The `microchannel` surface's CHF is flagged inferred (not in the private
spreadsheet; derived from the setpoint ladder as documented in the standalone
repo).

## Scope, licensing, disclosure

- No raw per-run data is contributed; only split definitions and this
  baseline stub. Code license: MIT. Dataset terms follow BoilingBench /
  NED3 licensing.
- Brad Moore is an independent researcher, not a member of the NED3 lab;
  this repository maintainer invited `bradleymoore1` with a maintain role,
  and substantive contributions go through review.
- This baseline is **not** safety-certified and not reactor-ready.