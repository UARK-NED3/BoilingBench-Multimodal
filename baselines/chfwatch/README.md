# CHF-Watch — transition-warning reference baseline (multimodal_fusion)

A reference baseline for the `multimodal_fusion` task on the current
benchmark's multimodal boiling datasets — **BoilingBench-3** (Cu-foam
surfaces) and **BoilingBench-4** (flat-Cu surfaces), which originate from
NED3-002 — contributed by Brad Moore (independent researcher) after
correspondence with the NED3 lab (Prof. Han Hu, June 2026). Scope was
agreed in [issue #1](../../issues/1): AE + hydrophone + thermal features on
the standard 5-surface split; `.cine` video deferred; no new datasets.

> **Dataset identity note (per NED3 maintainers, 2026-06-03):** an earlier
> development-stage archive of this multimodal boiling data was staged in the
> repo under the path `ned3-007_MultimodalBoilingData` (hence the legacy
> `MANIFEST_NED3_007_FILES.csv` used for run resolution). The current
> benchmark no longer includes **NED3-007** — that is a steady-state-only test
> dataset with no regression-grade transients, which is why the benchmark
> replaces it with BoilingBench-3/4. The runs this baseline covers are the
> multimodal boiling runs now distributed as BoilingBench-3/4.

## Task specification

This is a contribution to the repo's existing
[`tasks/multimodal_fusion.md`](../../tasks/multimodal_fusion.md) track —
**transition warning** is already one of its listed targets, so no new task
file or new task terminology is introduced. Following the repo's release
terminology: dataset ids (`BoilingBench-3`, `BoilingBench-4`), run ids as
archive folder tokens (`B69`, `B70`, ...), surfaces as the canonical
`cu_foam_pH0 / cu_foam_pH10 / cu_foam_pH12 / polished_cu / microchannel`
keys, and `splits/lso-surface-<surface>.csv` per fold.

| Surface | Dataset id | Note |
|---|---|---|
| cu_foam_pH0 / pH10 / pH12 | BoilingBench-3 (NED3-002) | Cu-foam family |
| polished_cu | BoilingBench-4 (NED3-002) | flat-Cu family |
| microchannel | BoilingBench-4 (NED3-002) | flat-Cu family; **not named on the BBB-4 card — confirm with maintainers** |

Distribution (current version): Hugging Face
[`hanhuark/BoilingBench-Multimodal`](https://huggingface.co/datasets/hanhuark/BoilingBench-Multimodal)
and Zenodo record
[`10.5281/zenodo.22131859`](https://doi.org/10.5281/zenodo.22131859)
(Lite v0.1.0). BoilingBench-3/4 are also on Dryad,
[`10.5061/dryad.ksn02v7h2`](https://doi.org/10.5061/dryad.ksn02v7h2).
Source citation: Pandey, Li, Dunlap, and Hu, "Unveiling Hysteresis of
Transient Boiling: A Multimodal Perspective," *Appl. Therm. Eng.* 262,
125259 (2025).

The full implementation lives in the standalone repo, **pinned**, not
vendored:

- Standalone repo: <https://gitlab.com/moore.brad.m-group/chf-watch>
- Pinned commit: `b86bf0d`
  ("Refresh E17/E20/E22 tables + fig3 with measured CHF; FAR 0.038 -> 0.040 in E20")
- Install: `pip install "git+https://gitlab.com/moore.brad.m-group/chf-watch.git@b86bf0d"`
- Environment: `environment.yaml` in this directory (Python 3.11, PyTorch
  cu128-nightly for Blackwell/sm_120; see the standalone README for the
  wheel gotcha). A plain-pip mirror is in `requirements.txt`.
- Configs used for the reported runs (standalone repo at `b86bf0d`):
  `configs/surface_heldout.yaml` (group-holdout at `level: surface`) and
  `configs/ned3_multimodal.yaml`; the E21 LSO threshold calibration is
  documented in `reports/tables/E21_lso_calibrated_detector.md`.

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
artifact; the standalone repo's `deploy.py` is unit-tested.
The leakage-safe splits: `time_block`, `group_holdout(level=surface|heat_load)`,
`leave_one_group_out` — all disjoint in group keys, asserted by tests.

> Note: the BoilingBench-3/4 cards record AE as legacy hit/source files with
> no continuous AE waveform export in the current package; the runs resolved
> here carry continuous AE sensor records from the earlier multimodal archive
> staging. Whether the HF/Zenodo revision includes the continuous AE channels
> used for these figures should be confirmed with the maintainers before
> reproduction.

## Split files

`splits/lso-surface-<surface>.csv` — one file per held-out surface (5
surfaces, 2 runs each; train = the other 8 runs). Run ids are the archive
folder tokens (`B69`, `B70`, ...) resolved from the legacy staging manifest
`MANIFEST_NED3_007_FILES.csv` (run->surface mapping is untouched by a
republish: re-run `scripts/make_lso_splits.py` against the current-version
manifest if the maintainers provide one). All files pass
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
  --split splits/lso-surface-cu_foam_pH0.csv \
  --manifest MANIFEST_NED3_007_FILES.csv \
  --repo ~/chf-watch --data-root <BoilingBench-3/4 archive root> \
  --cache-root <feature cache> --out results/cu_foam_pH0.json
```

Data lives on the dataset's distribution channels (Hugging Face / Zenodo /
Dryad per the release notes above); this repo carries no raw data.

## Reported numbers (PROVISIONAL)

Taken from the pinned standalone commit `b86bf0d`; treated as provisional
until independently reproduced by benchmark maintainers on repo-defined
splits of the current BoilingBench-3/4 distribution.

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

## CHF ground truth (evaluation-only label interface)

CHF labels used for lead-time reporting are exposed through the
**evaluation-only label interface**
[`metadata/boilingbench-chf_published_labels.csv`](../../metadata/boilingbench-chf_published_labels.csv):
**published aggregates only** — the steady-state values from Dunlap et al.
(2023, Table 1) and the Pandey-Li-Hu (2024) data paper, with
`value_source == "inferred"` on the `microchannel` surface (not in the
private spreadsheet; derived from the setpoint ladder as documented in the
standalone repo). Per-run lab data (Prof. Hu / Hari Pandey's spreadsheet)
remains **private and is not included**. The adapter exposes this via
`adapter.load_published_chf_labels()` / `adapter.inferred_chf_surfaces()`;
we are happy to follow the lab's lead on the exact interface shape.

## Scope, licensing, disclosure

- No raw per-run data is contributed; only split definitions and this
  baseline stub. Code license: MIT. Dataset terms follow BoilingBench /
  NED3 licensing.
- Brad Moore is an independent researcher, not a member of the NED3 lab;
  this repository's maintainers invited `bradleymoore1` with a maintain role,
  and substantive contributions go through review.
- This baseline is **not** safety-certified and not reactor-ready.