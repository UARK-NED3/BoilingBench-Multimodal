# CHF-Watch current-data exploratory baseline

This contribution provides a runnable, leakage-safe exploratory baseline for
the public processed **BoilingBench-1** through **BoilingBench-4** exports. It
replaces the earlier five-surface/NED3-007-oriented draft: that scope does not
match the current public release.

## Scope and limits

- Each current dataset contributes one processed run, so evaluation is
  cross-dataset transfer rather than within-dataset cross-validation.
- Inputs are thermal time-series features, hydrophone and microphone
  band-power where available, AE-hit counts, and processed continuous-AE
  band-power where available. BB-1/BB-2 include the continuous-AE product;
  BB-3/BB-4 do not in the current public export.
- The regression target is the release's processed heat-flux time series.
- The release describes that heat flux as a derived analysis product; any
  model using thermal features is therefore predicting a co-derived target,
  not independently validating a physical CHF measurement.
- The `chf_proxy` event is retained only as screening metadata. It is marked
  `not_confirmed` in the source and is never used as a CHF label, a safety
  outcome, or an alarm-performance claim.

This is consequently not a five-surface LSO CHF benchmark and does not
reproduce the historical NED3-007 headline numbers. It is a transparent
current-release baseline that can grow when the benchmark adds more
independent runs and confirmed event labels.

## Reproduce

Download the processed files for BB-1 through BB-4 from the Hugging Face dataset
at revision `e4d977db425e5a283c5f26b13b452a84868a5c5a`, arranged as:

    <data-root>/BB-1/... (common files plus ae_wfs_band_integrated_power.csv)
    <data-root>/BB-2/... (same waveform product)
    <data-root>/BB-3/... (plus microphone when available)
    <data-root>/BB-4/... (plus microphone when available)

Then run:

    pip install numpy pandas scikit-learn
    python scripts/audit_current_data.py --data-root <data-root> \
      --out results/boilingbench_audit.json \
      --markdown results/boilingbench_audit.md
    python scripts/run_boilingbench_ablations.py --data-root <data-root> \
      --out results/boilingbench_ablations.json

The audit records checksums, schemas, timing, modality availability, and event
provenance. The ablation JSON records constant and ridge baselines, eligible
datasets, train-only standardization, modality ablations, and metrics. No raw data, private lab
spreadsheet, or inferred CHF label is included in this repository.

## Relationship to CHF-Watch

The standalone CHF-Watch repository remains a historical NED3-007 research
artifact. Its claims must remain identified with that archive and must not be
represented as BB-3/BB-4 results. This adapter exists to make the current
benchmark evaluation independently reproducible from its public files.
