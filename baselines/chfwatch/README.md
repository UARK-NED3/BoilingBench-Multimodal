# CHF-Watch current-data exploratory baseline

This contribution provides a runnable, leakage-safe exploratory baseline for
the public processed **BoilingBench-3** and **BoilingBench-4** exports. It
replaces the earlier five-surface/NED3-007-oriented draft: that scope does not
match the current public release.

## Scope and limits

- BB-3 and BB-4 each contribute one processed run, so evaluation is strictly
  leave-one-dataset-out: train on BB-3/test on BB-4 and the reverse.
- Inputs are thermal time-series features, hydrophone and microphone
  band-power, and AE-hit counts. Current data cards do not provide continuous
  AE waveforms for these two cases.
- The regression target is the release's processed heat-flux time series.
- The `chf_proxy` event is retained only as screening metadata. It is marked
  `not_confirmed` in the source and is never used as a CHF label, a safety
  outcome, or an alarm-performance claim.

This is consequently not a five-surface LSO CHF benchmark and does not
reproduce the historical NED3-007 headline numbers. It is a transparent
current-release baseline that can grow when the benchmark adds run-level,
confirmed event labels and more independent cases.

## Reproduce

Download the processed files for BB-3 and BB-4 from the Hugging Face dataset
at revision `e4d977db425e5a283c5f26b13b452a84868a5c5a`, arranged as:

    <data-root>/BB-3/thermal_timeseries.npz
    <data-root>/BB-3/ae_hit_parameters_aligned.csv
    <data-root>/BB-3/hydrophone_band_integrated_power.csv
    <data-root>/BB-3/microphone_band_integrated_power.csv
    <data-root>/BB-3/critical_events.csv
    <data-root>/BB-4/... (same files)

Then run:

    pip install numpy pandas scikit-learn
    python scripts/evaluate_chfwatch_current.py --data-root <data-root> --out results/chfwatch_current.json

The JSON records data revision, feature set, split protocol, train-only
standardization, metrics, and marker provenance. No raw data, private lab
spreadsheet, or inferred CHF label is included in this repository.

## Relationship to CHF-Watch

The standalone CHF-Watch repository remains a historical NED3-007 research
artifact. Its claims must remain identified with that archive and must not be
represented as BB-3/BB-4 results. This adapter exists to make the current
benchmark evaluation independently reproducible from its public files.
